#!/usr/bin/env python3
"""thui-compact-v0 -- B65 smoke: COMPACTION of the history block duck drops, instead of losing it.

Design: notes/B65-compaction-of-dropped-history-design.md. duck loses history at the 30-turn window
(_PERSISTENT_HISTORY_ASSISTANT_TURNS, tool_agent.py:151, applied in _persistent_history_messages
:1653 after every turn from analyze's finally :2017), not at the token budget: on thui-v3-1 the budget
binds on 0.2% of requests while the window drops 22.2 turns per game. B62 rewrote the seven
world-model slots from turns still INSIDE the window and read p = 0.9978. B65 summarises what is being
DELETED, when it is deleted, into a memento that is folded into the first surviving user message on
every request -- the shape Codex CLI ships (codex-rs/core/compact.rs: summary + verbatim recent tail;
templates/compact/prompt.md: a six-line memento) plus the carry-forward rule its template lacks
(openai/codex#14347).

Seam: class-level wrap of ToolAgent._persistent_history_messages. The wrap diffs the assistant turns
that went in against the ones that came out; the dropped ones go into a per-game buffer. When the
buffer holds >= K dropped turns (or a level just completed with a non-empty buffer) ONE tool-free chat
call (thinking OFF on this thread only -- the B62 v1 lesson) rewrites the memento from (previous
memento + the buffered turns). The memento is folded into the first user message of the returned
history as an extra text part with a marker prefix, stripped and re-folded on every call so it is
never counted as a turn and never dropped as "oldest". The seven slots are untouched (not B62 stacked).

thui-v3-0 (the B48 chassis) byte-for-byte except three cells: cell 0 markdown, cell 12 appended payload,
cell 14 smoke filter (tr87 / sk48 / sc25, 900 s/game). The SMOKE build also shrinks the window to 8
turns and K to 4 so the trigger can fire inside 900 s (a 900 s game rarely reaches 30 turns); the full
build keeps 30 / 10. `--full` drops the cell-14 filter and the shrink; `--suffix=-r2` names a second run.

    python3 build_notebook.py [--full] [--suffix=-r2] [--owner=yocybercode] [--base=v3|v1]   # owner must match the pushing token (G4)
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BASE = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--base=")), "v3")
SRC_NB = {"v3": REPO / "thuiv3" / "taaf-thui-v3-0.ipynb", "v1": REPO / "thuiv1" / "v1-1" / "taaf-thui-v1-1.ipynb"}[BASE]
META_SRC = {"v3": REPO / "thuiv3" / "kernel-metadata.json", "v1": REPO / "thuiv1" / "v1-1" / "kernel-metadata.json"}[BASE]
OWNER = "sahasawatt"

SMOKE_GAMES = ("tr87", "sk48", "sc25")
GAME_CLOCK_S = 900
FULL = "--full" in sys.argv
WINDOW_TURNS = 30 if FULL else 8      # _PERSISTENT_HISTORY_ASSISTANT_TURNS; 8 in the smoke so the trigger can fire inside 900 s
COMPACT_K = 10 if FULL else 4         # dropped turns per memento call (~2 fires per game at the base's 22.2 drops)
COMPACT_MAX_TOKENS = 600
COMPACT_TIMEOUT_S = 90
COMPACT_TURN_CHARS = 600              # per dropped turn, rendered
COMPACT_BLOCK_CHARS = 6000            # whole buffered block, rendered
MEMENTO_MAX_CHARS = 1600              # ~530 estimator-tokens of every request, 1.7% of the 31,744 budget

CELL0_MD_SMOKE = """# thui-compact-v0 — B65 smoke: compaction of the history block duck drops (3 games, window 8, K 4)

**Infrastructure smoke, not a scoring run.** `thui-v3-0` (the B48 chassis: thui-v1-1 + yield 180, the standing-best build) byte-for-byte except cells 12 and 14.
Cell 12 wraps `ToolAgent._persistent_history_messages`: the assistant turns the 30-turn window (**8 in this smoke**)
discards are buffered, and every **4** (10 in the full build) dropped turns ONE extra tool-free chat call — thinking off
on this thread only — rewrites a MEMENTO from the previous memento plus the dropped turns. The memento is folded into
the first surviving user message on every request. The seven world-model slots are untouched. Cell 14 filters to
tr87 / sk48 / sc25 at 900 s each. Numbers are meaningless and must never be quoted.
Design: `notes/B65-compaction-of-dropped-history-design.md`.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

CELL0_MD_FULL = """# thui-compact-v1 — B65: compaction of the history block duck drops, full 25 games

`thui-v3-0` (the B48 chassis: thui-v1-1 + yield 180, the standing-best build) byte-for-byte except cell 12: the assistant
turns the 30-turn window discards are buffered, and every 10 dropped turns ONE extra tool-free chat call — thinking off
on this thread only — rewrites a MEMENTO from the previous memento plus the dropped turns (Codex CLI's compaction shape
plus the carry-forward rule its template lacks). The memento is folded into the first surviving user message on every
request; the seven world-model slots are untouched. Seed, temperature, clock, window and games inherited unchanged.
Oracle: paired **levels** vs the B48 build's public pool (`eval/fixtures/thuiv3-pool.json`), B35 floor on both draws.
Design + record: `notes/B65-compaction-of-dropped-history-design.md`.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

CELL12_SUFFIX = r'''

# === thui-compact-v0 (B65): compaction of the history block duck drops ==================
# Seam: class-level wrap of ToolAgent._persistent_history_messages (called from analyze's
# finally after every turn, tool_agent.py:2017). Diff the assistant turns in against the ones
# out -> the dropped block -> per-game buffer -> every K dropped turns ONE tool-free chat call
# rewrites a MEMENTO (previous memento + dropped turns), folded into the first user message of
# the returned history as a marked text part. Never issues an action, never edits the slots.
import re as _re
import time as _time
from pathlib import Path as _Path
from inference.agent import tool_agent as _ta
import threading as _threading


class _CompactThinkFlag:
    """Per-THREAD thinking override (the B62 v1 lesson: the 25 games are threads of one process and
    tool_agent.py:1297 reads the module global at call time, so a global flip poisons every game)."""

    def __init__(self, default):
        self.default = bool(default)
        self.local = _threading.local()

    def __bool__(self):
        v = getattr(self.local, "v", None)
        return self.default if v is None else bool(v)


_COMPACT_THINK = _CompactThinkFlag(_ta._LOCAL_ANALYZER_ENABLE_THINKING)
assert _COMPACT_THINK.default is True, "thui-compact: harness thinking is not ON by default"
_ta._LOCAL_ANALYZER_ENABLE_THINKING = _COMPACT_THINK

_COMPACT_WINDOW = @WINDOW@
_COMPACT_K = @K@
_COMPACT_MAX_TOKENS = @MAXTOK@
_COMPACT_TIMEOUT_S = @TIMEOUT@
_COMPACT_TURN_CHARS = @TURNCHARS@
_COMPACT_BLOCK_CHARS = @BLOCKCHARS@
_MEMENTO_MAX_CHARS = @MEMCHARS@
_MEMENTO_MAX_ERRORS = 2   # consecutive failed memento calls before compaction stops for this game
_MEMENTO_MARK = "MEMENTO (turns older than the window; carried forward):"
_COMPACT_STATS = {"games": 0, "fires": 0, "ok": 0, "empty": 0, "errors": 0, "wrapper_errors": 0,
                  "skipped_stop": 0, "dropped_turns": 0, "latency_s": 0.0, "landed_checks": 0, "landed_ok": 0,
                  "labels": 0, "cites": 0, "disabled_games": 0}
_MEMENTO_LABELS = ("Rules:", "Unknown:", "No-op/harmful:", "Hypotheses:", "Plan:")
_COMPACT_SYSTEM = (
    "You are the memory of an agent playing a grid puzzle game. The turns below are about to be deleted from its "
    "context. Rewrite its memento.\n"
    "Keep every entry of the previous memento unless this transcript contradicts it. Then add what these turns "
    "established about this level's rules, and what is still unknown. Every claim names the action or step number "
    "that established it; if you cannot name one, drop the claim. Never invent evidence.\n"
    "Output exactly these labelled lines, in this order:\n"
    "Rules: <at most 4, each ending with the step it came from, like (step 12)>\n"
    "Unknown: <at most 3>\n"
    "No-op/harmful: <each action proven to do nothing or to hurt, with the situation it was tried in and (step N); at most 6>\n"
    "Hypotheses: <at most 2, each one decisive test away>\n"
    "Plan: <repeat any Plan: line from the transcript verbatim; otherwise the best next step>\n"
    "Under 120 words total. No preamble, no code."
)

# window shrink (smoke only): the module global is read at call time in _persistent_history_messages
assert isinstance(_ta._PERSISTENT_HISTORY_ASSISTANT_TURNS, int), "thui-compact: window constant not where measured"
_ta._PERSISTENT_HISTORY_ASSISTANT_TURNS = _COMPACT_WINDOW


def _compact_game(agent, state_path=None):
    """Four-letter game id for the log lines. From the STATE PATH's stem (`sk48-d8078629_p0_state.json` ->
    `sk48`), never from `_session_runtime_dir`: on Kaggle every game's state file sits flat in one
    `artifacts/` dir, so the dir's basename read `arti` for all three smoke games (thui-compact-v0,
    2026-09-05) and the per-game oracle was unreadable. The id is remembered on the buffer at the
    first analyze() so the memento/P2 lines, which only hold the agent, read the same value."""
    try:
        if state_path is not None:
            return _Path(str(state_path)).stem.split("_")[0][:4]
        st = agent.__dict__.get("_compact_state") or {}
        return st.get("game") or "????"
    except Exception:
        return "????"


def _compact_text(m):
    """Text of one message: content text, or tool-call arguments for an assistant tool call. Images never."""
    text = _ta._normalize_message_content(m.get("content"))
    if not text and str(m.get("role", "")) == "assistant":
        calls = m.get("tool_calls") or []
        try:
            text = " ".join(str((c.get("function") or {}).get("arguments", ""))[:400] for c in calls if isinstance(c, dict))
        except Exception:
            text = ""
    return text or ""


def _compact_strip(history):
    """Remove the memento part from the first user message (a copy), so it is never counted or dropped."""
    out = list(history)
    for i, m in enumerate(out):
        if str(m.get("role", "")) != "user":
            continue
        c = m.get("content")
        if isinstance(c, list) and c and isinstance(c[0], dict) and str(c[0].get("text", "")).startswith(_MEMENTO_MARK):
            mm = dict(m)
            mm["content"] = c[1:]
            out[i] = mm
        elif isinstance(c, str) and c.startswith(_MEMENTO_MARK):
            mm = dict(m)
            mm["content"] = c.split("\n\n", 1)[1] if "\n\n" in c else ""
            out[i] = mm
        break
    return out


def _compact_fold(history, memento):
    """Fold the memento into the first user message (a copy) as a leading marked text part."""
    if not memento:
        return history
    out = list(history)
    for i, m in enumerate(out):
        if str(m.get("role", "")) != "user":
            continue
        mm = dict(m)
        c = m.get("content")
        part = {"type": "text", "text": _MEMENTO_MARK + "\n" + memento}
        if isinstance(c, list):
            mm["content"] = [part, *c]
        else:
            mm["content"] = part["text"] + "\n\n" + (c or "")
        out[i] = mm
        break
    return out


def _compact_dropped(before, after):
    """Messages present in `before` (history only) and absent from `after`, by identity; rendered as lines."""
    kept = {id(m) for m in after}
    lines = []
    n_assistant = 0
    for m in before:
        if id(m) in kept:
            continue
        role = str(m.get("role", "")).strip()
        text = _compact_text(m)
        if role == "assistant":
            n_assistant += 1
        if not text:
            continue
        cap = _COMPACT_TURN_CHARS if role == "assistant" else 400
        lines.append(f"[{role}] {text[:cap]}")
    return n_assistant, lines


def _compact_memento(agent, reason):
    game = _compact_game(agent)
    st = agent.__dict__["_compact_state"]
    _COMPACT_STATS["fires"] += 1
    block = "\n".join(st["buffer"])[-_COMPACT_BLOCK_CHARS:]
    user = f"PREVIOUS MEMENTO:\n{st['memento'] or '(none yet)'}\n\nTURNS ABOUT TO BE DELETED (oldest first):\n{block}"
    saved_max = agent._max_output_tokens
    agent._max_output_tokens = _COMPACT_MAX_TOKENS
    _COMPACT_THINK.local.v = False   # this THREAD only
    t0 = _time.monotonic()
    try:
        result = agent._chat_completion(
            [{"role": "system", "content": _COMPACT_SYSTEM}, {"role": "user", "content": user}],
            tools=None,
            request_timeout_seconds=_COMPACT_TIMEOUT_S,
        )
    except Exception as exc:
        _COMPACT_STATS["errors"] += 1
        _COMPACT_STATS["latency_s"] += _time.monotonic() - t0   # a stalled endpoint must reach the latency oracle
        st["errors"] = st.get("errors", 0) + 1
        st["buffer"] = []          # the block is lost either way; retrying it costs the game clock, not the memory
        if st["errors"] >= _MEMENTO_MAX_ERRORS:
            st["disabled"] = True
            _COMPACT_STATS["disabled_games"] += 1
        print(f"thui-compact: game={game} reason={reason} call FAILED ({type(exc).__name__}: {str(exc)[:160]}) "
              f"consecutive={st['errors']} disabled={bool(st.get('disabled'))}", flush=True)
        return
    finally:
        agent._max_output_tokens = saved_max
        _COMPACT_THINK.local.v = None
    latency = _time.monotonic() - t0
    _COMPACT_STATS["latency_s"] += latency
    try:
        agent._accumulate_usage_tokens(result.usage)
    except Exception:
        pass
    content = _ta._normalize_message_content(result.message.get("content")).strip()
    if not content:
        try:
            content = _ta._extract_reasoning_text(result.message).strip()
        except Exception:
            content = ""
    n_buf = sum(1 for l in st["buffer"] if l.startswith("[assistant]"))
    st["buffer"] = []
    st["errors"] = 0
    if content:
        st["memento"] = content[:_MEMENTO_MAX_CHARS]
        _COMPACT_STATS["ok"] += 1
    else:
        _COMPACT_STATS["empty"] += 1
    st["pending_check"] = True
    usage = result.usage if isinstance(result.usage, dict) else {}
    labels = [lab for lab in _MEMENTO_LABELS if lab in st["memento"]]
    cites = len(_re.findall(r"\bstep\s*\d+", st["memento"], _re.I))
    _COMPACT_STATS["labels"] += len(labels)
    _COMPACT_STATS["cites"] += cites
    print(f"thui-compact: game={game} reason={reason} dropped_turns={n_buf} latency={latency:.1f}s "
          f"tokens={usage.get('total_tokens', '?')} completion={usage.get('completion_tokens', '?')} "
          f"memento_chars={len(st['memento'])} labels={len(labels)}/{len(_MEMENTO_LABELS)} cites={cites} "
          f"missing={[l.rstrip(':') for l in _MEMENTO_LABELS if l not in labels]}", flush=True)


_orig_persist = _ta.ToolAgent._persistent_history_messages
_orig_analyze = _ta.ToolAgent.analyze


def _compact_analyze(self, state_path, action_count, *args, **kwargs):
    st = self.__dict__.get("_compact_state")
    if st is None:
        st = self.__dict__["_compact_state"] = {"buffer": [], "memento": "", "pending_check": False,
                                                 "seen_summ": None, "should_stop": None,
                                                 "game": _compact_game(self, state_path)}
        _COMPACT_STATS["games"] += 1
        print(f"thui-compact: new buffer for game #{_COMPACT_STATS['games']} ({st['game']})", flush=True)
    st["should_stop"] = kwargs.get("should_stop")
    # P2 probe: after a fire, the history the NEXT request is built from must carry the memento.
    if st["pending_check"]:
        st["pending_check"] = False
        _COMPACT_STATS["landed_checks"] += 1
        h = self._history_messages or []
        landed = False
        for m in h:
            if str(m.get("role", "")) == "user":
                c = m.get("content")
                landed = (isinstance(c, list) and bool(c) and isinstance(c[0], dict) and str(c[0].get("text", "")).startswith(_MEMENTO_MARK)) \
                    or (isinstance(c, str) and c.startswith(_MEMENTO_MARK))
                break
        if landed:
            _COMPACT_STATS["landed_ok"] += 1
        print(f"thui-compact: P2 landed={landed} history={len(h)} game={_compact_game(self)}", flush=True)
    return _orig_analyze(self, state_path, action_count, *args, **kwargs)


def _compact_persist(self, messages, *args, **kwargs):
    st = self.__dict__.get("_compact_state")
    try:
        before = _compact_strip(list(messages[1:])) if messages else []
        clean = [messages[0], *before] if messages else messages
    except Exception as exc:
        _COMPACT_STATS["wrapper_errors"] += 1
        print(f"thui-compact: wrapper error (strip, pass-through): {type(exc).__name__}: {exc}", flush=True)
        return _orig_persist(self, messages, *args, **kwargs)
    out = _orig_persist(self, clean, *args, **kwargs)
    if st is None:
        return out
    try:
        n_dropped, lines = _compact_dropped(before, out)
        if lines:
            st["buffer"].extend(lines)
        _COMPACT_STATS["dropped_turns"] += n_dropped
        summ = self._last_step_summary or {}
        if summ is st.get("seen_summ"):
            summ = {}
        else:
            st["seen_summ"] = summ
        transition = bool(summ.get("level_transition"))
        terminal = bool(summ.get("run_complete") or summ.get("game_over"))
        n_buf_turns = sum(1 for l in st["buffer"] if l.startswith("[assistant]"))
        if st.get("disabled"):
            st["buffer"] = []
        elif st["buffer"] and not terminal and (n_buf_turns >= _COMPACT_K or transition):
            should_stop = st.get("should_stop")
            if callable(should_stop) and should_stop():
                _COMPACT_STATS["skipped_stop"] += 1
            else:
                _compact_memento(self, "level" if transition else "k")
        return _compact_fold(out, st["memento"])
    except Exception as exc:  # the memory must never break the harness path
        _COMPACT_STATS["wrapper_errors"] += 1
        print(f"thui-compact: wrapper error (pass-through): {type(exc).__name__}: {exc}", flush=True)
        return out


_ta.ToolAgent._persistent_history_messages = _compact_persist
_ta.ToolAgent.analyze = _compact_analyze
assert _ta.ToolAgent._persistent_history_messages is _compact_persist, "thui-compact: history wrap did not land"
assert _ta.ToolAgent.analyze is _compact_analyze, "thui-compact: analyze wrap did not land"
assert _ta._LOCAL_ANALYZER_ENABLE_THINKING is _COMPACT_THINK, "thui-compact: thread-local thinking flag not installed"
assert _ta._PERSISTENT_HISTORY_ASSISTANT_TURNS == _COMPACT_WINDOW, "thui-compact: window shrink did not land"

# teeth 1: the flag is thread-local (worker False, main True)
_seen = {}


def _compact_flag_probe():
    _COMPACT_THINK.local.v = False
    _seen["worker"] = bool(_ta._LOCAL_ANALYZER_ENABLE_THINKING)


_t = _threading.Thread(target=_compact_flag_probe)
_t.start()
_t.join()
assert _seen.get("worker") is False and bool(_ta._LOCAL_ANALYZER_ENABLE_THINKING) is True, "thui-compact: thinking flag is not thread-local"

# teeth 2: the diff/strip/fold helpers on synthetic messages -- a dropped assistant turn is detected, the
# memento is folded once and stripped clean, and a message that survives is never reported as dropped.
_u1 = {"role": "user", "content": [{"type": "text", "text": "board A"}]}
_a1 = {"role": "assistant", "content": "", "tool_calls": [{"function": {"arguments": "{\"code\": \"action(['UP'])\"}"}}]}
_t1 = {"role": "tool", "content": "Step executed."}
_u2 = {"role": "user", "content": [{"type": "text", "text": "board B"}]}
_a2 = {"role": "assistant", "content": "I think LEFT next."}
_n, _lines = _compact_dropped([_u1, _a1, _t1, _u2, _a2], [_u2, _a2])
assert _n == 1 and len(_lines) == 3 and _lines[1].startswith("[assistant] {\"code\""), (_n, _lines)
assert _compact_dropped([_u2, _a2], [_u2, _a2]) == (0, []), "thui-compact: a surviving turn reported as dropped"
_folded = _compact_fold([_u2, _a2], "line one")
assert _folded[0]["content"][0]["text"].startswith(_MEMENTO_MARK) and _folded[0]["content"][1]["text"] == "board B"
assert _u2["content"][0]["text"] == "board B", "thui-compact: fold mutated the original message"
_stripped = _compact_strip(_folded)
assert _stripped[0]["content"] == _u2["content"] and _stripped[1] is _a2, "thui-compact: strip did not restore the message"
assert _compact_fold(_compact_strip(_folded), "line two")[0]["content"][0]["text"].endswith("line two"), "thui-compact: re-fold failed"
for _lab in _MEMENTO_LABELS:
    assert _lab in _COMPACT_SYSTEM, f"thui-compact: label {_lab} is counted but not asked for in the prompt"
assert _COMPACT_SYSTEM.count("names the action or step number") == 1, "thui-compact: the step-id requirement is missing from the prompt"
assert _COMPACT_SYSTEM.count("(step") >= 2, "thui-compact: the step id is not part of the output FORMAT (an instruction alone was ignored in the 8B lint)"
assert _MEMENTO_MAX_ERRORS >= 1, "thui-compact: the breaker must allow at least one attempt"
# teeth 3: the game label comes from the state path's stem, not the runtime dir (Kaggle: flat artifacts/ -> "arti")
assert _compact_game(None, "/kaggle/working/artifacts/sk48-d8078629_p0_state.json") == "sk48", "thui-compact: game label not from the state path"
class _CompactFakeAgent:
    _session_runtime_dir = _Path("/kaggle/working/artifacts")
_fa = _CompactFakeAgent()
assert _compact_game(_fa) == "????", "thui-compact: label fell back to the runtime dir"
_fa.__dict__["_compact_state"] = {"game": "tr87"}
assert _compact_game(_fa) == "tr87", "thui-compact: label not read from the buffer"
print(f"thui-compact-v0: wraps landed; window={_COMPACT_WINDOW} K={_COMPACT_K} cap={_COMPACT_MAX_TOKENS} timeout={_COMPACT_TIMEOUT_S}s; "
      f"thinking flag thread-local (worker False, main True); diff/fold/strip teeth ok; {len(_MEMENTO_LABELS)} memento labels asked for and counted", flush=True)
# ======================================================================================
'''.replace("@WINDOW@", str(WINDOW_TURNS)).replace("@K@", str(COMPACT_K)).replace("@MAXTOK@", str(COMPACT_MAX_TOKENS)) \
   .replace("@TIMEOUT@", str(COMPACT_TIMEOUT_S)).replace("@TURNCHARS@", str(COMPACT_TURN_CHARS)) \
   .replace("@BLOCKCHARS@", str(COMPACT_BLOCK_CHARS)).replace("@MEMCHARS@", str(MEMENTO_MAX_CHARS))

CELL14_ANCHOR = "    bm.games = _offline_games(competition_env_files)\n"
CELL14_FILTER = (
    "    # thui-compact-v0 smoke: three games, at the REAL seam.\n"
    "    _SMOKE = " + repr(SMOKE_GAMES) + "\n"
    "    _n0 = len(bm.games)\n"
    "    bm.games = [g for g in bm.games if any(g.env_name.startswith(h) for h in _SMOKE)]\n"
    "    print(f\"thui-compact-v0: smoke filter {_n0} -> {len(bm.games)} games\", flush=True)\n"
    "    assert len(bm.games) == " + str(len(SMOKE_GAMES)) + ", f\"thui-compact-v0: expected " + str(len(SMOKE_GAMES)) + " games, got {len(bm.games)}\"\n"
    "    bm.solver.max_runtime_s_per_game = " + str(GAME_CLOCK_S) + ".0\n"
)


def main(full: bool = False, slug_suffix: str = "", owner: str = OWNER) -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 17, f"{SRC_NB.name}: expected 17 cells, found {len(cells)}"
    if BASE == "v3":
        _c8 = "".join(cells[8]["source"])
        assert _c8.count("'LOCAL_ANALYZER_YIELD_SECONDS': '180'") == 2, "base v3: yield-180 injection/assert not found twice in cell 8"
    print(f"base = {BASE} ({SRC_NB.relative_to(REPO)}); window={WINDOW_TURNS} K={COMPACT_K}", flush=True)
    before = ["".join(c["source"]) for c in cells]
    slug = ("thui-compact-v1" if full else "thui-compact-v0") + slug_suffix
    out_nb = HERE / f"taaf-{slug}.ipynb"

    cells[0]["source"] = (CELL0_MD_FULL if full else CELL0_MD_SMOKE).splitlines(keepends=True)
    c12 = "".join(cells[12]["source"])
    assert "thui-compact" not in c12, "cell 12 already carries the memento -- double build?"
    for ph in ("@WINDOW@", "@K@", "@MAXTOK@", "@TIMEOUT@", "@TURNCHARS@", "@BLOCKCHARS@", "@MEMCHARS@"):
        assert ph not in CELL12_SUFFIX, f"placeholder not substituted: {ph}"
    assert (f"_COMPACT_WINDOW = {30 if full else 8}\n") in CELL12_SUFFIX, "window constant not rendered for this build"
    cells[12]["source"] = (c12 + CELL12_SUFFIX).splitlines(keepends=True)
    if not full:
        c14 = "".join(cells[14]["source"])
        assert c14.count(CELL14_ANCHOR) == 1, "offline bm.games assignment not found once in cell 14"
        cells[14]["source"] = c14.replace(CELL14_ANCHOR, CELL14_ANCHOR + CELL14_FILTER).splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    expected = [0, 12] if full else [0, 12, 14]
    assert changed == expected, f"cells changed {changed}, expected {expected}"
    for i in (12, 14):
        ast.parse("".join(cells[i]["source"]), filename=f"cell{i}")

    out_nb.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(META_SRC.read_text(encoding="utf-8"))
    meta["id"] = f"{owner}/{slug}"; meta["title"] = slug; meta["code_file"] = out_nb.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"built {out_nb.name}: cells changed {changed}, id {meta['id']}")


if __name__ == "__main__":
    _suf = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--suffix=")), "")
    _own = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), OWNER)
    main(full=FULL, slug_suffix=_suf, owner=_own)
