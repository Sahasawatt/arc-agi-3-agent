#!/usr/bin/env python3
"""thui-reflect-v0 -- B62 smoke: periodic REFLECTION MEMORY grafted onto duck's own world-model slot.

Design: notes/B62-reflection-memory-design.md. Lever 7 of
arc-agi-pub/notes/deep-research-arc3-sota-now-2026-09-03.md (Reki #2 / forge #3 of Milestone 1
refresh a reflection memory every ~10 steps; never tested inside the duck harness by anyone).

What duck already has: `ToolAgent._summarized_knowledge` -- seven labelled fields the model may
volunteer as assistant-text prefixes, injected into every user prompt, wiped on level transition.
Measured over three full runs (2,472 turns with action > 1): the carried world model is present in
**60-64 %** of turns and EMPTY in the rest. B62 adds ONE extra LLM call every K executed steps
(and right after a level transition) that rewrites those seven fields from the recent transcript,
so the slot is never empty for long and the level-transition wipe is repaired from evidence.
No new prompt surface: the fields land in the same `_summarized_knowledge_lines()` the model already
reads. The reflection call never issues an action and never touches history.

thui-v1-1 byte-for-byte except three cells: cell 0 markdown, cell 12 appended payload
(wrap ToolAgent.analyze -> reflect after the turn), cell 14 smoke filter (tr87 / sk48 / sc25,
900 s/game). `--full` drops the cell-14 filter; `--suffix=-r2` names a second run.

    python3 build_notebook.py [--full] [--suffix=-r2] [--owner=yocybercode]   # owner must match the pushing token (G4)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SRC_NB = REPO / "thuiv1" / "v1-1" / "taaf-thui-v1-1.ipynb"
OWNER = "sahasawatt"

SMOKE_GAMES = ("tr87", "sk48", "sc25")
GAME_CLOCK_S = 900
REFLECT_K = 10            # executed steps between reflections (Reki/forge: ~10)
REFLECT_MAX_TOKENS = 700  # cap on the reflection reply
REFLECT_TIMEOUT_S = 90    # one reflection call may not eat the turn budget
REFLECT_HISTORY = 12      # most recent history messages rendered into the reflection prompt

CELL0_MD_SMOKE = """# thui-reflect-v0 — B62 smoke: reflection memory every 10 steps, into duck's own world-model slot

**Infrastructure smoke, not a scoring run.** `thui-v1-1` byte-for-byte except cells 12 and 14.
Cell 12 wraps the analyzer: after every turn, once ≥ 10 actions have executed since the last
reflection (or a level just completed), ONE extra chat call rewrites the seven world-model fields
duck already injects into each prompt (`World model / Goal model / Action model / Recent findings /
Open questions / Plan / Cross-level notes`) from the recent transcript. The call never issues an
action and never edits history. Cell 14 filters to tr87 / sk48 / sc25 at 900 s each. Numbers are
meaningless and must never be quoted. Design: `notes/B62-reflection-memory-design.md`.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

CELL0_MD_FULL = """# thui-reflect-v1 — B62: reflection memory every 10 steps, full 25 games

`thui-v1-1` byte-for-byte except cell 12: after every turn, once ≥ 10 actions have executed since
the last reflection (or a level just completed), one extra chat call rewrites the seven world-model
fields duck already injects into each prompt from the recent transcript. The call never issues an
action and never edits history. Seed, temperature, clock and games inherited unchanged. Oracle:
paired **levels** vs the same-seed base pair (`thui-v1-1`, `thui-v1-1-r2`), ≥ 2 runs per arm.
Design + record: `notes/B62-reflection-memory-design.md`.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

CELL12_SUFFIX = r'''

# === thui-reflect-v0 (B62): periodic reflection memory into duck's world-model slot ======
# Seam: class-level wrap of ToolAgent.analyze (as B60/B61). AFTER the upstream turn returns,
# if >= K actions executed since the last reflection, or the turn completed a level, run ONE
# tool-free chat call that rewrites self._summarized_knowledge -- the seven fields
# _summarized_knowledge_lines() already injects into every user prompt. Upstream wipes those
# fields inside the same turn that completes a level (tool_agent.py:1584), so a reflection
# placed after the turn survives until the next transition. Never issues an action.
import time as _time
from pathlib import Path as _Path
from inference.agent import tool_agent as _ta

_REFLECT_K = @K@
_REFLECT_MAX_TOKENS = @MAXTOK@
_REFLECT_TIMEOUT_S = @TIMEOUT@
_REFLECT_HISTORY = @HIST@
_REFLECT_FIELDS = ("world_model", "goal_model", "action_model", "recent_findings", "open_questions", "current_plan", "cross_level_notes")
_REFLECT_STATS = {"games": 0, "calls": 0, "ok": 0, "empty": 0, "errors": 0, "wrapper_errors": 0,
                  "skipped_stop": 0, "latency_s": 0.0, "injected_checks": 0, "injected_ok": 0}
_REFLECT_SYSTEM = (
    "You are the memory of a coding agent that is solving a grid-based puzzle game. "
    "Rewrite the agent's working world model from the transcript below. Output ONLY these seven "
    "labelled lines, each a single concise line, evidence-based, no code, no preamble:\n"
    "World model: <what the level contains and how the board responds>\n"
    "Goal model: <what completing the level seems to require>\n"
    "Action model: <what each action does, incl. which do nothing>\n"
    "Recent findings: <newest evidence, with the action/step it came from>\n"
    "Open questions: <what is still unknown>\n"
    "Plan: <the best next steps>\n"
    "Cross-level notes: <ONLY facts likely to hold on later levels: action semantics, HUD vs board, win-condition shape>\n"
    "Keep what the transcript still supports, drop what it contradicts, add what was learned. "
    "Never invent evidence. If a field is unknown write: unknown."
)


def _reflect_game(state_path):
    try:
        return _Path(state_path).stem.split("_")[0][:4]
    except Exception:
        return "????"


def _reflect_render_history(agent):
    lines = []
    for m in list(agent._history_messages)[-_REFLECT_HISTORY:]:
        role = str(m.get("role", "")).strip()
        text = _ta._normalize_message_content(m.get("content"))
        if role == "assistant" and not text:
            calls = m.get("tool_calls") or []
            try:
                text = " ".join(str((c.get("function") or {}).get("arguments", ""))[:400] for c in calls if isinstance(c, dict))
            except Exception:
                text = ""
        if not text:
            continue
        cap = 700 if role == "tool" else 1500
        lines.append(f"[{role}] {text[:cap]}")
    return "\n".join(lines)


def _reflect(agent, state_path, reason):
    game = _reflect_game(state_path)
    _REFLECT_STATS["calls"] += 1
    current = "\n".join(agent._summarized_knowledge_lines()) or "(empty)"
    history = _reflect_render_history(agent) or "(no history captured)"
    user = f"CURRENT WORLD MODEL (may be stale or empty):\n{current}\n\nRECENT TRANSCRIPT (oldest first):\n{history}"
    saved_max = agent._max_output_tokens
    agent._max_output_tokens = _REFLECT_MAX_TOKENS
    t0 = _time.monotonic()
    try:
        result = agent._chat_completion(
            [{"role": "system", "content": _REFLECT_SYSTEM}, {"role": "user", "content": user}],
            tools=None,
            request_timeout_seconds=_REFLECT_TIMEOUT_S,
        )
    except Exception as exc:
        _REFLECT_STATS["errors"] += 1
        print(f"thui-reflect: game={game} reason={reason} call FAILED ({type(exc).__name__}: {str(exc)[:160]})", flush=True)
        return
    finally:
        agent._max_output_tokens = saved_max
    latency = _time.monotonic() - t0
    _REFLECT_STATS["latency_s"] += latency
    try:
        agent._accumulate_usage_tokens(result.usage)
    except Exception:
        pass
    content = _ta._normalize_message_content(result.message.get("content"))
    note = _ta._extract_scientist_note(content)
    filled = {k: v for k, v in note.items() if k in _REFLECT_FIELDS and v and v.strip().lower() != "unknown"}
    if filled:
        for k, v in filled.items():
            agent._summarized_knowledge[k] = v
        _REFLECT_STATS["ok"] += 1
    else:
        _REFLECT_STATS["empty"] += 1
    usage = result.usage if isinstance(result.usage, dict) else {}
    print(f"thui-reflect: game={game} reason={reason} fields={sorted(filled)} latency={latency:.1f}s "
          f"tokens={usage.get('total_tokens', '?')} content_chars={len(content)}", flush=True)


_orig_analyze = _ta.ToolAgent.analyze


def _reflect_analyze(self, state_path, action_count, *args, **kwargs):
    st = self.__dict__.get("_reflect_state")
    if st is None:
        st = self.__dict__["_reflect_state"] = {"since": 0, "pending_check": False}
        _REFLECT_STATS["games"] += 1
        print(f"thui-reflect: new memory for game #{_REFLECT_STATS['games']} ({_reflect_game(state_path)})", flush=True)
    # P2 probe: the turn right after a reflection must carry the fields into the prompt.
    if st["pending_check"]:
        st["pending_check"] = False
        _REFLECT_STATS["injected_checks"] += 1
        n = len(self._summarized_knowledge_lines())
        if n > 0:
            _REFLECT_STATS["injected_ok"] += 1
        print(f"thui-reflect: P2 injected lines={n} game={_reflect_game(state_path)}", flush=True)
    result = _orig_analyze(self, state_path, action_count, *args, **kwargs)
    try:
        summ = self._last_step_summary or {}
        try:
            executed = int(summ.get("executed_count") or 0)
        except (TypeError, ValueError):
            executed = 0
        st["since"] += executed
        transition = bool(summ.get("level_transition"))
        terminal = bool(summ.get("run_complete") or summ.get("game_over"))
        should_stop = kwargs.get("should_stop")
        if (st["since"] >= _REFLECT_K or (transition and st["since"] > 0)) and not terminal:
            if callable(should_stop) and should_stop():
                _REFLECT_STATS["skipped_stop"] += 1
            else:
                _reflect(self, state_path, "level" if transition else "k")
                st["since"] = 0
                st["pending_check"] = True
    except Exception as exc:  # the memory must never break the harness path
        _REFLECT_STATS["wrapper_errors"] += 1
        print(f"thui-reflect: wrapper error (pass-through): {type(exc).__name__}: {exc}", flush=True)
    return result


_ta.ToolAgent.analyze = _reflect_analyze
assert _ta.ToolAgent.analyze is _reflect_analyze, "thui-reflect: analyze wrap did not land"
assert callable(getattr(_ta, "_extract_scientist_note", None)), "thui-reflect: upstream note parser missing"
print(f"thui-reflect-v0: ToolAgent.analyze wrapped (reflect every {_REFLECT_K} executed steps or on level completion; "
      f"max {_REFLECT_MAX_TOKENS} tokens, {_REFLECT_TIMEOUT_S}s timeout; never issues an action)", flush=True)
# ======================================================================================
'''.replace("@K@", str(REFLECT_K)).replace("@MAXTOK@", str(REFLECT_MAX_TOKENS)).replace("@TIMEOUT@", str(REFLECT_TIMEOUT_S)).replace("@HIST@", str(REFLECT_HISTORY))

CELL14_ANCHOR = "    bm.games = _offline_games(competition_env_files)\n"
CELL14_FILTER = (
    "    # thui-reflect-v0 smoke: three games, at the REAL seam.\n"
    "    _SMOKE = " + repr(SMOKE_GAMES) + "\n"
    "    _n0 = len(bm.games)\n"
    "    bm.games = [g for g in bm.games if any(g.env_name.startswith(h) for h in _SMOKE)]\n"
    "    print(f\"thui-reflect-v0: smoke filter {_n0} -> {len(bm.games)} games\", flush=True)\n"
    "    assert len(bm.games) == " + str(len(SMOKE_GAMES)) + ", f\"thui-reflect-v0: expected " + str(len(SMOKE_GAMES)) + " games, got {len(bm.games)}\"\n"
    "    bm.solver.max_runtime_s_per_game = " + str(GAME_CLOCK_S) + ".0\n"
)


def main(full: bool = False, slug_suffix: str = "", owner: str = OWNER) -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 17, f"thui-v1-1 source expected 17 cells, found {len(cells)}"
    before = ["".join(c["source"]) for c in cells]
    slug = ("thui-reflect-v1" if full else "thui-reflect-v0") + slug_suffix
    out_nb = HERE / f"taaf-{slug}.ipynb"

    cells[0]["source"] = (CELL0_MD_FULL if full else CELL0_MD_SMOKE).splitlines(keepends=True)
    c12 = "".join(cells[12]["source"])
    assert "thui-reflect" not in c12, "cell 12 already carries the memory -- double build?"
    assert "@K@" not in CELL12_SUFFIX and "@MAXTOK@" not in CELL12_SUFFIX and "@HIST@" not in CELL12_SUFFIX, "placeholder not substituted"
    cells[12]["source"] = (c12 + CELL12_SUFFIX).splitlines(keepends=True)
    if not full:
        c14 = "".join(cells[14]["source"])
        assert c14.count(CELL14_ANCHOR) == 1, "offline bm.games assignment not found once in cell 14"
        cells[14]["source"] = c14.replace(CELL14_ANCHOR, CELL14_ANCHOR + CELL14_FILTER).splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    expected = [0, 12] if full else [0, 12, 14]
    assert changed == expected, f"cells changed {changed}, expected {expected}"

    import ast
    for i in (12, 14):
        ast.parse("".join(cells[i]["source"]), filename=f"cell{i}")

    out_nb.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads((REPO / "thuiv1" / "v1-1" / "kernel-metadata.json").read_text(encoding="utf-8"))
    meta["id"] = f"{owner}/{slug}"; meta["title"] = slug; meta["code_file"] = out_nb.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"built {out_nb.name}: cells changed {changed}, id {meta['id']}")


if __name__ == "__main__":
    _suf = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--suffix=")), "")
    _own = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), OWNER)
    main(full="--full" in sys.argv, slug_suffix=_suf, owner=_own)
