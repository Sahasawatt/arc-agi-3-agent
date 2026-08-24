"""Per-request usage probe for the duck harness — the cell-12 payload.

WHY THIS EXISTS, and why it is not `save_request_logs=True`.

The harness already has a per-request logger. `HarnessSolver.save_request_logs`
(`solver.py:885`) flows to `ToolAgent` (`solver.py:1350`) and gates two
`_append_request_snapshot` calls (`tool_agent.py:2195` and `:2208`). Setting
`bm.solver.save_request_logs = True` in cell 14 works — the analyzer is built per game
inside `bm.run()` (`solver.py:1339 _make_analyzer`), so the flag is read after cell 12
and after cell 14's assignments.

It records the wrong thing for the question in front of us. `_append_request_snapshot`
(`tool_agent.py:929-965`) writes `messages` + `tools` + `finish_reason` + `analysis_step`
+ `action` + `request_index_within_turn`. It does **not** write `usage`, even though the
caller holds it — `result.usage` is passed to `_accumulate_usage_tokens` on the line
between the two snapshot calls (`:2207`) and then dropped. And it writes the full message
list on BOTH the request and the response event, so the response row costs ~60-90 KB to
carry one string. At 1,201 requests × 2 events that is roughly 150-215 MB to obtain 1,201
values of `finish_reason`.

The open question is where to place an output-token cap. `duckv9` capped at 768 and scored
0.22 (`finish_reason` `length` 704 against `tool_calls` 68 — the cap truncated the tool call
carrying the action). `duckv10` runs uncapped at a mean 2,211 output tokens per request. So
we know 91% of requests want more than 768 tokens and nothing about the shape above it.
Placing a safe cap needs the **distribution**, which means `completion_tokens` per request.
That is what this file records, at about 200 bytes per request instead of 150 KB.

⚠️ ANSWERED — and the 91% above is the PRIOR this probe was built to test, not a result.
Measured, the share is **68.4%**. The whole paragraph is left standing on purpose: it is the
reason the probe exists, and overwriting an assumption with its answer deletes the record of
what was assumed. Read `notes/R28-usage-distribution.md` for what the run actually found —
§"Two corrections to what was assumed when the probe was written" (`:50-51`) carries this
correction in the author's own words, and the section above it kills the cap idea
structurally: the distribution has **no fat tail**, so every cap that saves meaningfully cuts
the body. A cap at 8,192 saves 0.98% of output; at 12,288 it saves nothing at all.

WHAT IT RECORDS — one JSONL row per request, written next to the run's other artifacts
using the harness's own path convention (`<game>_usage.jsonl`):

    game, action, req_in_turn, wall_s, prompt_tokens, completion_tokens, total_tokens,
    finish_reason

`req_in_turn` is maintained here rather than read from the harness, because the counter the
harness keeps (`turn_count`) is a local in `analyze()`.

WHAT IT ANSWERS

  - the output-token distribution, hence a cap that trims the tail without truncating
    the median (`duckv9`'s failure mode);
  - requests per turn, and how that moves if `LOCAL_ANALYZER_YIELD_SECONDS` changes —
    the tie-breaker for whether raising the yield budget buys anything at all;
  - measured per-request wall time per game, against the 164 s the vLLM log implies.

CONSTRAINTS

  - stdlib only, no project imports beyond `inference.agent.tool_agent`, no top-level side
    effects — `install()` must be called explicitly. The notebook build step embeds this
    file's source into cell 12 and appends the `install(...)` call, the way duckmod splices
    `duck_tools.py`.
  - **fail-open, always.** This is instrument code riding on a run that costs a GPU slot.
    Every hook swallows its own exceptions and the probe disables itself rather than
    letting a logging bug end a game.
  - bounded: `MAX_ROWS_PER_GAME` caps output so a pathological loop cannot fill the disk.
"""

import json
import time

MAX_ROWS_PER_GAME = 2000

_state = {"installed": False, "orig_analyze": None, "orig_chat": None, "disabled": False}


def _usage_path(tool_agent, state_path):
    """Per-game JSONL path, using the harness's own artifact-location convention.

    Falls back to a sibling of the state file if the private resolver is not where we
    expect it — a bundle refresh may move it, and a moved resolver must not end a run.
    """
    try:
        return tool_agent._resolve_named_run_artifact(
            state_path, default_name="request_usage.jsonl", per_game_suffix="_usage.jsonl"
        )
    except Exception:
        return state_path.parent / (state_path.stem + "_usage.jsonl")


def _as_int(value):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return None


def install(tool_agent, *, max_rows=MAX_ROWS_PER_GAME):
    """Wrap ToolAgent.analyze and ToolAgent._chat_completion. Idempotent.

    `tool_agent` is the module (or any object exposing `ToolAgent`), passed in rather than
    imported so this file is testable against a stub without the harness installed.
    """
    if _state["installed"]:
        return False
    agent_cls = tool_agent.ToolAgent
    orig_analyze = agent_cls.analyze
    orig_chat = agent_cls._chat_completion

    def analyze(self, state_path, action_num, *args, **kwargs):
        # Establishes the per-turn context the _chat_completion wrapper stamps onto rows.
        # A turn is one analyze() call; requests within it are numbered from 1.
        try:
            self._probe_path = _usage_path(tool_agent, state_path)
            self._probe_action = action_num
            self._probe_req = 0
        except Exception:
            self._probe_path = None
        return orig_analyze(self, state_path, action_num, *args, **kwargs)

    def _chat_completion(self, messages, **kwargs):
        started = time.monotonic()
        try:
            result = orig_chat(self, messages, **kwargs)
        except Exception as exc:
            _record(self, started, None, type(exc).__name__, max_rows)
            raise
        _record(self, started, result, None, max_rows)
        return result

    agent_cls.analyze = analyze
    agent_cls._chat_completion = _chat_completion
    _state.update(installed=True, orig_analyze=orig_analyze, orig_chat=orig_chat)
    return True


def _record(agent, started, result, exception_name, max_rows):
    """Append one row. Never raises; on any failure the probe turns itself off."""
    if _state["disabled"]:
        return
    try:
        path = getattr(agent, "_probe_path", None)
        if path is None:
            return
        count = getattr(agent, "_probe_rows", 0)
        if count >= max_rows:
            return
        agent._probe_rows = count + 1
        agent._probe_req = getattr(agent, "_probe_req", 0) + 1

        usage = getattr(result, "usage", None) if result is not None else None
        usage = usage if isinstance(usage, dict) else {}
        row = {
            "game": path.stem[: -len("_usage")] if path.stem.endswith("_usage") else path.stem,
            "action": getattr(agent, "_probe_action", None),
            "req_in_turn": agent._probe_req,
            "wall_s": round(time.monotonic() - started, 3),
            "prompt_tokens": _as_int(usage.get("prompt_tokens")),
            "completion_tokens": _as_int(usage.get("completion_tokens")),
            "total_tokens": _as_int(usage.get("total_tokens")),
            "finish_reason": (
                "__exception__:" + exception_name
                if exception_name
                else str(getattr(result, "finish_reason", "") or "")
            ),
        }
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=True))
            handle.write("\n")
    except Exception:
        # One broken write must not cost a game. Stop trying, keep playing.
        _state["disabled"] = True


def uninstall(tool_agent):
    """Restore the original methods. Exists for the tests, not for the notebook."""
    if not _state["installed"]:
        return False
    tool_agent.ToolAgent.analyze = _state["orig_analyze"]
    tool_agent.ToolAgent._chat_completion = _state["orig_chat"]
    _state.update(installed=False, orig_analyze=None, orig_chat=None, disabled=False)
    return True
