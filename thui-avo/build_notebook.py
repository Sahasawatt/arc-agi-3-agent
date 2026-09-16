#!/usr/bin/env python3
"""thui-avo-v0 -- the AVO arm: Tufa's 08-31 bundle, run as they ship it.

WHY THIS ARM EXISTS. Every optimisation axis inside the duck harness is closed by
measurement (MAP B8..B58), and at the live bar the shrink arithmetic needs public ~12 --
unreachable by any closed axis. The one externally-evidenced mean-mover left is the
upstream's own AVO agent: `jakobbrggen/taaf-kaggle-source` (branch `experiment/avo`,
git_status clean @ 49720d3) ships `deploy_target.pkl` with **avo_agent=True**, i.e. the
bundle IS Tufa's AVO Kaggle run, published as they run it. AvoAgent subclasses ToolAgent
with durable memory + inspect/plan/implement/evaluate + a stagnation supervisor
(notes/tufa-current-vs-fork-2026-09-01.md). Precedent: duck-v10's own 2.41 -> 4.55 came
from adopting a newer upstream bundle and DELETING fork patches -- this build repeats
that move on the next bundle.

WHAT THE BUILD IS. thui-v1-1 byte-for-byte except:
  cell 0  markdown (attribution, what this run is)
  cell 6  DATASET_SOURCES[0]: taaf-kaggle-source-anim-20260807-anim -> taaf-kaggle-source
  cell 8  the v10-exactness upscale tooth is RELAXED to a print (see below)
Everything else inherits: the seed pin and the wheelhouse.

⚠️ THE LIVE DATASET MOVES UNDER YOU. v0's first push died on the inherited tooth
`'MULTIMODAL_UPSCALE': '4'` even though the locally-diffed copy carried '4' -- because
`taaf-kaggle-source` had been re-versioned since that diff: the mounted LATEST is branch
`experiment/avo-v2` @ 74ff3df ("pin the kaggle-avo arm to the control run's model"),
which sets MULTIMODAL_UPSCALE '8' + MULTIMODAL_GRID_LINES '1' AND natively pins
`jakobbrggen/qwen3-8-27b-fp8-hf-snapshot` / `SERVED_MODEL_NAME = 'Qwen/Qwen3.8-27B-FP8'`
-- the exact model our fork used to swap in by hand. Consequences:
  * the three model .replace() calls in cell 8 now find nothing and no-op, which is
    CORRECT (their asserts test the negative and still hold);
  * the seed-pin anchor and temperature 0.6 survive verbatim (verified on the live
    bytes, count 1 each);
  * the upscale pin is upstream's own v2 setting paired with their vision handling, so
    for an as-shipped arm it must not be pinned back to 4 -- the builder swaps that
    assert for a print of the value actually in force.
Makefile pins unchanged live-vs-0831; avo package still imports only the bundle's own
`inference` package -- the wheelhouse suffices.

WHAT A FAILURE LOOKS LIKE. The chassis is proven; the new variable is the whole bundle.
If it dies it dies in setup/serve (first ~15 min), which is cheap. A completed run is a
25-game public number to rank against v10cal with eval/rank_runs.py -- and per B37/B58,
ONE run ranks nothing inside the same-build band; only outside [2.82, 5.24] does a single
draw speak.

    python3 build_notebook.py    # writes taaf-thui-avo-v0.ipynb + kernel-metadata.json

v1 (2026-09-06, --v1): the same bundle plus ONE cell-12 wrap on AvoAgent.analyze -- two breakers
for two failures the 09-05 full run (yocybercode/thui-avo-v0) showed in its own transcripts:
  * m0r0 made 189 tool calls in 93 turns and never once called action() -- the supervisor wrote
    30 STAGNATION/HARD-REDIRECT paragraphs and the model ignored every one; 7,907 s, 0 actions.
    Breaker A: after K consecutive analyze() calls with step_executed False (K=4 on a game with
    no level yet, 12 otherwise), execute ONE simple action through the session's own step_env
    (the B60 seam), round-robin over the valid non-MOUSE actions, capped per game. A paragraph
    is advice; an executed action is the only thing that changes the prompt.
  * ls20 reached level 2, hit the exploit deadline, and replayed the same ~43-action BFS plan
    that ends in GAME_OVER 28 times (1,227 actions on a 123-action level). Breaker B: two
    GAME_OVERs inside exploit mode switch exploit mode off for that game (game_budget_s=None,
    which is how AvoAgent.in_exploit_mode reads False) and record the failure in memory.
Nothing else moves: prompts, memory, supervisor, chassis, seed all as v0. Cells changed 0/6/8/12.
The build defaults OWNER to sahasawatt (this box's token; pushed on the weekly quota reset).

    python3 build_notebook.py --v1 [--owner=sahasawatt]   # writes taaf-thui-avo-v1.ipynb
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SRC_NB = REPO / "thuiv1" / "v1-1" / "taaf-thui-v1-1.ipynb"
V1 = "--v1" in sys.argv
OWNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), "sahasawatt")
SLUG = "thui-avo-v1" if V1 else "thui-avo-v0"
OUT_NB = HERE / f"taaf-{SLUG}.ipynb"

OLD_BUNDLE = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
NEW_BUNDLE = "jakobbrggen/taaf-kaggle-source"

# The inherited v10-exactness tooth, verbatim from thui-v1-1's cell 8. For the AVO arm
# upstream's own value must stand (avo-v2 ships upscale 8 + grid lines 1), so the assert
# becomes a report of what is in force.
UPSCALE_TOOTH = (
    '    assert "\'MULTIMODAL_UPSCALE\': \'4\'" in command, (\n'
    '        "thui-v1-1 TEETH FAIL: upscale must stay 4 (v10 exact, B23 measured in-noise)"\n'
    '    )\n'
)
UPSCALE_REPORT = (
    "    _ups = re.search(r\"'MULTIMODAL_UPSCALE': '([^']*)'\", command)\n"
    "    print(f\"thui-avo-v0: upstream MULTIMODAL_UPSCALE={_ups.group(1) if _ups else 'ABSENT'} \"\n"
    "          \"(as shipped -- deliberately not pinned to 4)\", flush=True)\n"
)

CELL0_MD = """# thui-avo-v0 (Thuitanium / Knowless Crew) — the upstream AVO bundle, unmodified, on the thui chassis

**This kernel swaps ONE thing against `thui-v1-1`: the source bundle.**
`jakobbrggen/taaf-kaggle-source` (branch `experiment/avo`) ships `avo_agent=True` in its
own `deploy_target.pkl`, so the run executes Tufa's AVO agent — durable memory,
inspect/plan/implement/evaluate, stagnation supervisor — exactly as they publish it.
Sampler seed and the Qwen3.8-27B-FP8 model swap are inherited from `thui-v1-1` unchanged.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""


CELL0_MD_V1 = """# thui-avo-v1 (Thuitanium / Knowless Crew) — the AVO bundle plus two breakers on its loop

`thui-avo-v0` (Tufa's AVO agent as shipped) plus ONE cell-12 wrap on `AvoAgent.analyze`, written
from the 09-05 full run's own transcripts: **(A)** a game that makes K analyze() calls in a row
without executing an action gets ONE simple action executed through the session's `step_env`
(m0r0 made 189 tool calls in 93 turns and never called `action()`; the supervisor's 30 paragraphs
changed nothing); **(B)** two GAME_OVERs inside exploit mode switch exploit mode off for that game
(ls20 replayed one dying plan 28 times, 1,227 actions on level 2). Prompts, memory, supervisor,
chassis and seed are v0's, unchanged.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — their AVO agent from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

# Appended to cell 12 (after thui-v1-1's usage probe). Runs after the bundle is importable and
# before bm.run builds the per-game AvoAgent, so the class-level wrap lands on every game.
CELL12_SUFFIX = r'''
# ======================================================================================
# thui-avo-v1: two breakers on the AVO loop (2026-09-06). Read notes/B-avo-… for the transcripts.
import inference.avo.agent as _avo
from pathlib import Path as _V1Path

_V1_DEAD_TURNS_NO_LEVEL = 4    # consecutive analyze() calls with step_executed False, game has cleared nothing
_V1_DEAD_TURNS_SCORING = 12    # same, once the game has cleared a level (three full AVO cycles; B60's lesson)
_V1_FORCED_CAP = 25            # forced actions per game, so a dead game cannot become a random walk
_V1_EXPLOIT_GAMEOVERS = 2      # GAME_OVERs inside exploit mode before exploit mode is switched off
_V1_SIMPLE = ("UP", "DOWN", "LEFT", "RIGHT", "SPACE")   # never MOUSE (needs coordinates), never RESET
_V1_STATS = {"games": 0, "dead_turns": 0, "forced": 0, "forced_executed": 0, "exploit_off": 0, "wrapper_errors": 0}
_orig_avo_analyze = _avo.AvoAgent.analyze


def _v1_game(state_path):
    try:
        return _V1Path(str(state_path)).stem.split("_")[0][:4]   # the #127 rule: the runtime dir is flat on Kaggle
    except Exception:
        return "????"


def _v1_state(agent):
    st = agent.__dict__.get("_v1_state")
    if st is None:
        st = agent.__dict__["_v1_state"] = {"dead": 0, "forced": 0, "gameovers": 0, "exploit_off": False}
        _V1_STATS["games"] += 1
    return st


def _v1_pick(valid_actions, n):
    names = [str(getattr(a, "name", a)).upper() for a in (valid_actions or [])]
    cand = [a for a in names if a in _V1_SIMPLE]
    return cand[n % len(cand)] if cand else None


def _v1_after_turn(agent, result, state_path, valid_actions, step_env):
    """The breakers. Pure function of the turn's result and the agent's own bookkeeping; drivable by teeth."""
    st = _v1_state(agent)
    gid = _v1_game(state_path)
    executed = bool(getattr(result, "step_executed", False))
    summ = agent._last_step_summary or {}
    # A: dead-game breaker
    if executed:
        st["dead"] = 0
    else:
        st["dead"] += 1
        _V1_STATS["dead_turns"] += 1
    best_level = int(getattr(getattr(agent, "supervisor", None), "best_level", 0) or 0)
    k = _V1_DEAD_TURNS_SCORING if best_level > 0 else _V1_DEAD_TURNS_NO_LEVEL
    if st["dead"] >= k and st["forced"] < _V1_FORCED_CAP and step_env is not None:
        act = _v1_pick(valid_actions, st["forced"])
        if act is not None:
            payload = step_env({"actions": [act]})
            ok = isinstance(payload, dict) and bool(payload.get("executed"))
            st["forced"] += 1
            st["dead"] = 0
            _V1_STATS["forced"] += 1
            _V1_STATS["forced_executed"] += int(ok)
            print(f"thui-avo-v1: game={gid} forced #{st['forced']} act={act} after {k} dead turns executed={ok} "
                  f"changed={payload.get('board_changed') if isinstance(payload, dict) else None} "
                  f"level_completed={payload.get('level_completed') if isinstance(payload, dict) else None}", flush=True)
    # B: exploit-replay breaker (only a turn that executed can carry a fresh game_over; the summary persists)
    if executed and bool(getattr(agent, "in_exploit_mode", False)) and bool(summ.get("game_over")):
        st["gameovers"] += 1
        if st["gameovers"] >= _V1_EXPLOIT_GAMEOVERS and not st["exploit_off"]:
            st["exploit_off"] = True
            agent.game_budget_s = None          # AvoAgent.in_exploit_mode reads False from here on
            _V1_STATS["exploit_off"] += 1
            try:
                agent.memory.record_failure(f"exploit-mode replay ended the game {st['gameovers']} times; that sequence is not a solution")
            except Exception:
                pass
            print(f"thui-avo-v1: game={gid} exploit mode OFF after {st['gameovers']} game-overs (phases resume)", flush=True)
    return st


def _v1_analyze(self, state_path, action_count, *args, valid_actions=None, step_env=None, **kwargs):
    result = _orig_avo_analyze(self, state_path, action_count, *args, valid_actions=valid_actions, step_env=step_env, **kwargs)
    if result is None or getattr(result, "retryable_failure", False):
        return result
    try:
        _v1_after_turn(self, result, state_path, valid_actions, step_env)
    except Exception as exc:   # the breakers must never break the harness path
        _V1_STATS["wrapper_errors"] += 1
        print(f"thui-avo-v1: wrapper error {type(exc).__name__}: {str(exc)[:160]}", flush=True)
    return result


_avo.AvoAgent.analyze = _v1_analyze
assert _avo.AvoAgent.analyze is _v1_analyze, "thui-avo-v1: analyze wrap did not land"

# teeth: drive the breakers on a fake agent with a stub step_env, before any game runs
class _V1Fake:
    def __init__(self):
        self._last_step_summary = None
        self.game_budget_s = 7920.0
        self.in_exploit_mode = False
        self.supervisor = type("S", (), {"best_level": 0})()
        self.memory = type("M", (), {"failures": [], "record_failure": lambda s, t: s.failures.append(t)})()
_calls = []
def _stub_step_env(arguments):
    _calls.append(arguments); return {"executed": True, "board_changed": True, "level_completed": False}
_R = type("R", (), {"step_executed": False, "retryable_failure": False})
_fa = _V1Fake(); _sp = "/kaggle/working/artifacts/m0r0-492f87ba_p0_tool_runtime_state.json"
for _i in range(_V1_DEAD_TURNS_NO_LEVEL - 1):
    _v1_after_turn(_fa, _R(), _sp, ["UP", "DOWN", "MOUSE"], _stub_step_env)
assert _calls == [], "thui-avo-v1 TEETH: forced before the threshold"
_v1_after_turn(_fa, _R(), _sp, ["UP", "DOWN", "MOUSE"], _stub_step_env)
assert _calls == [{"actions": ["UP"]}], f"thui-avo-v1 TEETH: forced action wrong: {_calls}"
assert _fa.__dict__["_v1_state"]["dead"] == 0 and _V1_STATS["forced"] == 1
_v1_after_turn(_fa, type("R", (), {"step_executed": True, "retryable_failure": False})(), _sp, ["UP"], _stub_step_env)
assert _fa.__dict__["_v1_state"]["dead"] == 0, "thui-avo-v1 TEETH: an executed turn must reset the dead counter"
_fa.supervisor.best_level = 1
for _i in range(_V1_DEAD_TURNS_NO_LEVEL):
    _v1_after_turn(_fa, _R(), _sp, ["UP"], _stub_step_env)
assert len(_calls) == 1, "thui-avo-v1 TEETH: a scoring game must use the 12-turn threshold, not 4"
_fb = _V1Fake(); _fb.in_exploit_mode = True; _fb._last_step_summary = {"game_over": True, "executed_count": 3}
_Rx = type("R", (), {"step_executed": True, "retryable_failure": False})
_v1_after_turn(_fb, _Rx(), _sp, ["UP"], _stub_step_env)
assert _fb.game_budget_s == 7920.0, "thui-avo-v1 TEETH: exploit switched off after ONE game-over"
_v1_after_turn(_fb, _Rx(), _sp, ["UP"], _stub_step_env)
assert _fb.game_budget_s is None and _fb.memory.failures and _V1_STATS["exploit_off"] == 1, "thui-avo-v1 TEETH: exploit not switched off after two"
_v1_after_turn(_fb, _R(), _sp, ["UP"], _stub_step_env)   # a non-executed turn cannot re-count the stale game_over
assert _fb.__dict__["_v1_state"]["gameovers"] == 2, "thui-avo-v1 TEETH: stale game_over re-counted on a no-action turn"
assert _v1_game(_sp) == "m0r0" and _v1_pick(["MOUSE"], 0) is None
for _k in _V1_STATS: _V1_STATS[_k] = 0
del _fa, _fb, _calls, _R, _Rx, _sp
print(f"thui-avo-v1: AvoAgent.analyze wrapped; breakers A (dead turns {_V1_DEAD_TURNS_NO_LEVEL}/{_V1_DEAD_TURNS_SCORING}, cap {_V1_FORCED_CAP}) "
      f"and B (exploit off after {_V1_EXPLOIT_GAMEOVERS} game-overs); teeth ok", flush=True)
# ======================================================================================
'''


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 17, f"thui-v1-1 source expected 17 cells, found {len(cells)}"

    before = ["".join(c["source"]) for c in cells]

    cells[0]["source"] = (CELL0_MD_V1 if V1 else CELL0_MD).splitlines(keepends=True)
    if V1:
        c12 = "".join(cells[12]["source"])
        assert "thui-avo-v1" not in c12, "cell 12 already carries the v1 payload -- double build?"
        cells[12]["source"] = (c12 + CELL12_SUFFIX).splitlines(keepends=True)

    c6 = "".join(cells[6]["source"])
    assert c6.count(f'"{OLD_BUNDLE}"') == 1, "bundle slug not found exactly once in cell 6"
    assert NEW_BUNDLE + '"' not in c6, "cell 6 already carries the new bundle -- double build?"
    cells[6]["source"] = c6.replace(f'"{OLD_BUNDLE}"', f'"{NEW_BUNDLE}"').splitlines(keepends=True)

    c8 = "".join(cells[8]["source"])
    assert c8.count(UPSCALE_TOOTH) == 1, "upscale tooth not found verbatim in cell 8 -- source moved"
    c8 = c8.replace(UPSCALE_TOOTH, UPSCALE_REPORT)
    if "\nimport re\n" not in c8 and not c8.startswith("import re\n"):
        c8 = "import re\n" + c8
    cells[8]["source"] = c8.splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    expected = [0, 6, 8, 12] if V1 else [0, 6, 8]
    assert changed == expected, f"cells changed {changed}, expected {expected}"

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads((REPO / "thuiv1" / "v1-1" / "kernel-metadata.json").read_text(encoding="utf-8"))
    meta["id"] = f"{OWNER}/{SLUG}"
    meta["title"] = SLUG
    meta["code_file"] = OUT_NB.name
    srcs = [NEW_BUNDLE if s == OLD_BUNDLE else s for s in meta["dataset_sources"]]
    assert NEW_BUNDLE in srcs and OLD_BUNDLE not in srcs, "metadata source swap failed"
    meta["dataset_sources"] = srcs
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}")
    print(f"dataset_sources: {srcs}")
    print("push with: python3 scripts/kaggle_push_kernel.py repos/arc-agi-3-agent/thui-avo  (from arc-agi-pub)")


if __name__ == "__main__":
    main()
