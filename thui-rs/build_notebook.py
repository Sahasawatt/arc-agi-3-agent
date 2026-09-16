"""thui-rs -- RESTART-AT-STALL on the anim harness: after K analysis turns without a level change, the agent forgets and re-draws.

Why (2026-09-16, notes/think-score-levers-2026-09-16.md). Six full-25 runs' events: a cleared level takes median 10 analysis turns
from level start (p75 17, 84 % within 20); the final stalled level burns median 32. Of stalled levels that burned > 20 turns
(101 of 150), 69 % were cleared by a sibling draw of the same build, and median 18 turns remained after the 20th -- P(clear <= 18 |
clearable) = 0.80. The family's per-game best is 62-66 levels against the best single run's 44: that gap is draw variance, and a
fresh context at the stalled level is a second draw of that level inside the same run. No MAP row tried it: wm KEPT knowledge across
deaths (NULL), B65 kept MORE history, B62 rewrote the world model; forgetting is the untested pole. Levels are deterministic; what
varies between draws is the sampling and the history, and both are reset here.

What the graft does (cell 9 tail, after the anim import): ONE wrapper on `ToolAgent.analyze`, BEFORE delegating (the prompt is
built inside analyze from these fields). It reads the current level from the runtime state the solver writes before each call and
counts DISTINCT `analysis_step` values seen at that level (retries of one step after a yield count once). At THUI_RS_STALL_TURNS (20)
turns without a level change it clears `_history_messages`, resets `_summarized_knowledge` to `_empty_world_model()`, drops
`_last_step_summary` / `_last_action_result`, bumps the module sampling seed `_LOCAL_ANALYZER_SEED` (passed per request), prints
`THUI_RS_RESTART level= turns= n= seed=`, and restarts the turn count; at most THUI_RS_MAX_PER_LEVEL (2) restarts per level; a level
change resets everything. The no-op guard (mechanical knowledge) is kept. Nothing is added to any prompt; no action is taken for the
model. --control: identical notebook, no wrapper (THUI_RS_GRAFT control).

Pre-registered read (smoke sb26 / g50t / wa30 / ka59 at 1,800 s -- the four games where 5-6 of 6 sibling runs cleared the level this
build stalls on, and where 3-4-way concurrency yields 30-60 turns; v0 vs --control same hour):
  1. Mechanism: THUI_RS_GRAFT ok; >= 4 THUI_RS_RESTART across the four games. Fewer = the stall did not reach 20 turns -> VOID.
  2. The causal read (thui-rs/restart_read.py on both output dirs): v0's levels cleared AFTER a restart vs the CONTROL's levels
     cleared after the point where the rule WOULD have restarted (the reader replays the rule on any run) -- the control number is the
     stale context's own late-clear rate, e.g. af-ctl bp35 L1 / tn36 L2 cleared past turn 20 with no restart. v0 > ctl on that count
     in >= 2 games AND levels >= control = PASS -> full-25 pair on the anim base.
  2b. Full-width caveat, stated before the smoke: at 25-way the anim base gets ~35 turns/game, so the rule fires in ~10 of 25 games
     (restart_read on anim-r2: 10 would-fire, at turns 20-38) and leaves <= 15 turns for the fresh context; the +9 upper bound in the
     ledger came from 52-turn June-duck runs. Expected at full width: +2..4 levels/run; a K=15 variant is the next rung if PASS.
  3. Levels < control on any game with restarts = FAIL (forgetting cost more than the re-draw bought on that game).
  4. Nothing here is a submission; hidden draws of identical code spread 1.96-4.33 (wuliao0), so no single hidden draw ranks a build.

Build:  PYTHONUTF8=1 python thui-rs/build_notebook.py               -> taaf-thui-rs-v0.ipynb        (smoke, graft)
        PYTHONUTF8=1 python thui-rs/build_notebook.py --control     -> taaf-thui-rs-ctl.ipynb       (smoke, no wrapper)
        PYTHONUTF8=1 python thui-rs/build_notebook.py --full [--control]  -> taaf-thui-rs-{v0,ctl}-full25-r1.ipynb
Teeth:  python thui-rs/test_rs_graft.py   (0 GPU: executes the notebook's cell-9 graft against the bundle's REAL runtime_state.py)
Push:   python scripts/kaggle_push_kernel.py <this dir>   (from arc-agi-pub; rebuild the variant first -- code_file is shared)
"""
from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAST = HERE.parent / "thui-fast"
ANIM = HERE.parent / "thui-anim"
L1 = HERE.parent / "thui-l1" / "build_notebook.py"
SRC_NB = FAST / "upstream-keithtyser-duck-qwen3-8-flash-next-nvfp4-mtp.ipynb"
B71_NB = ANIM / "upstream-yocybercode-thui-animfast-b71-full25-r1.ipynb"
B71_META = ANIM / "upstream-yocybercode-kernel-metadata.json"
OWNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), "sahasawatt")
FULL = "--full" in sys.argv
CONTROL = "--control" in sys.argv
SLUG = (("thui-rs-ctl-full25-r1" if CONTROL else "thui-rs-v0-full25-r1") if FULL else ("thui-rs-ctl" if CONTROL else "thui-rs-v0"))
OUT_NB = HERE / f"taaf-{SLUG}.ipynb"
ANIM_DS = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
B71_CELLS = (1, 3, 5, 7, 9, 11, 15)
SMOKE_GAMES = ("sb26-7fbdac44", "g50t-5849a774", "wa30-ee6fef47", "ka59-38d34dbb")   # sibling-cleared 6/6, 5/5, 5/5, 5/5
SMOKE_CLOCK_S = 1800

_spec = importlib.util.spec_from_file_location("thui_l1_builder", L1)
l1 = importlib.util.module_from_spec(_spec)
_argv, sys.argv = sys.argv, sys.argv[:1]
_spec.loader.exec_module(l1)
sys.argv = _argv

CELL0_MD = f"""# {SLUG} (Thuitanium / Knowless Crew) -- restart-at-stall on the animation-awareness duck harness

**This is a Knowless Crew / Thuitanium fork.** Three upstreams, and what is ours is the graft:

- **Serving** -- Keith Tyser's [Duck Qwen3.8 Flash Next NVFP4 MTP](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp):
  the pinned `RadixArk/Qwen3.8-Flash-Next-NVFP4` checkpoint, his offline vLLM runtime, NVFP4 PLE patch, MTP-3 profile and watchdog.
- **Solver** -- the Tufa Labs duck harness (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit, Michal Tesnar, Stefano Viel)
  on Jakob Bruggen's `feature/animation-awareness` branch (`{ANIM_DS}`), executed unmodified on disk.
- **Weights** -- RadixArk's NVFP4 quantisation of Qwen/Qwen3.8-Flash-Next (Qwen licence terms apply).

Every score quoted by any upstream is theirs.

## What we changed (the graft)

- **cell 0 / 1** -- this header; Tufa's original header reworded in the third person.
- **cell 3** -- full diagnostics on an interactive public run, minimal in a real rerun.
- **cell 5 / 15** -- the competition mount resolved instead of hardcoded.
- **cell 7 / 9 / 11** -- the anim bundle mounted as the solver (as in `thui-anim-full25-r2`), thui-v3 knobs seed 20260825 / yield 180.
- **cell 9 (tail)** -- {"CONTROL arm: no wrapper; the imported harness is asserted untouched." if CONTROL else "one wrapper on `ToolAgent.analyze`: after 20 analysis turns without a level change the agent's history and world model are reset and the sampling seed bumped (at most 2 restarts per level), so the stalled level gets a fresh draw inside the same run. No prompt text, no action taken for the model."}
{"- **cell 15** -- smoke: " + ", ".join(SMOKE_GAMES) + f" at {SMOKE_CLOCK_S} s each." if not FULL else "- **cell 15** -- all 25 public games, upstream clock."}

Build script: `thui-rs/build_notebook.py` in our agent repo (asserts exactly those cells changed). 2026-09-16.
"""

CELL9_RS = '''
# ---- thui-rs: RESTART-AT-STALL -- after K analysis turns without a level change, forget and re-draw (before the prompt is built).
from inference.agent.runtime_state import load_runtime_state as _thui_rs_load

THUI_RS_STALL_TURNS = 20      # cleared levels take median 10 turns, 84 % <= 20; the stalled level burns median 32
THUI_RS_MAX_PER_LEVEL = 2     # restarts per level

_thui_rs_orig_analyze = _ta.ToolAgent.analyze


def _thui_rs_analyze(self, state_path, action_num, *args, **kwargs):
    try:
        st = self.__dict__.setdefault("_thui_rs", {"level": None, "steps": set(), "restarts": 0, "total": 0})
        frame, _history = _thui_rs_load(state_path) if state_path.exists() else (None, [])
        level = frame.level if frame is not None else None
        if level != st["level"]:
            st.update(level=level, steps=set(), restarts=0)
        step = kwargs.get("analysis_step")
        if step is not None:
            st["steps"].add(step)
        if len(st["steps"]) >= THUI_RS_STALL_TURNS and st["restarts"] < THUI_RS_MAX_PER_LEVEL:
            self._history_messages = []
            self._summarized_knowledge = _ta._empty_world_model()
            self._last_step_summary = None
            self._last_action_result = None
            _ta._LOCAL_ANALYZER_SEED = int(_ta._LOCAL_ANALYZER_SEED) + 1
            st["restarts"] += 1
            st["total"] += 1
            turns = len(st["steps"])
            st["steps"] = {step} if step is not None else set()   # this turn is turn 1 of the fresh context
            print(f"THUI_RS_RESTART level={level} turns={turns} n={st['restarts']} total={st['total']} "
                  f"seed={_ta._LOCAL_ANALYZER_SEED}", flush=True)
    except Exception as exc:   # never let the graft kill a turn
        print(f"thui-rs: wrapper error {exc!r}", flush=True)
    return _thui_rs_orig_analyze(self, state_path, action_num, *args, **kwargs)


_ta.ToolAgent.analyze = _thui_rs_analyze
assert _ta.ToolAgent.analyze is _thui_rs_analyze
assert callable(_ta._empty_world_model) and isinstance(_ta._LOCAL_ANALYZER_SEED, int)
print("THUI_RS_GRAFT ok", flush=True)
'''

CELL9_CTL = '''
# ---- thui-rs CONTROL: no wrapper; the harness is asserted untouched.
assert _ta.ToolAgent.analyze.__name__ == "analyze"
print("THUI_RS_GRAFT control (no wrapper installed)", flush=True)
'''

CELL15_SELECT_SMOKE = (l1.CELL15_SELECT_OLD +
                       f'    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-rs smoke clock\n'
                       f'    print(f"thui-rs: smoke {{len(bm.games)}} games @ {{bm.solver.max_runtime_s_per_game}} s", flush=True)\n')


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    b71 = json.loads(B71_NB.read_text(encoding="utf-8"))["cells"]
    assert len(cells) == 18 and len(b71) == 18
    before = ["".join(c["source"]) for c in cells]
    b = ["".join(c["source"]) for c in b71]
    for i in range(18):
        if i not in (0,) + B71_CELLS:
            assert b[i] == before[i], f"b71 cell {i} differs from Keith's upstream"
    assert b[7].count(ANIM_DS) == 1 and "import inference.agent.tool_agent as _tool_agent" in b[9] and "ANIM_BUNDLE_DIR" in b[11]

    cells[0]["cell_type"] = "markdown"; cells[0]["source"] = CELL0_MD.splitlines(keepends=True)
    for i in B71_CELLS:
        s = b[i].replace("thui-animfast", "thui-rs").replace("THUI_ANIMFAST_GRAFT", "THUI_ANIM_GRAFT")
        if i == 9:
            s += "\nimport inference.agent.tool_agent as _ta\nassert _ta is _tool_agent\n" + (CELL9_CTL if CONTROL else CELL9_RS)
        cells[i]["source"] = s.splitlines(keepends=True)
        cells[i].pop("attachments", None)
    if not FULL:
        s = "".join(cells[15]["source"])
        m = re.search(r"PUBLIC_GAME_IDS = tuple\(\[\n(?:    \"[a-z0-9]{4}-[0-9a-f]{8}\",?\n){25}\]\)\n", s)
        assert m, "cell 15: the 25-game PUBLIC_GAME_IDS tuple not found"
        for g in SMOKE_GAMES:
            assert f'"{g}"' in m.group(0), f"{g} is not one of the 25 public ids"
        s = s.replace(m.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-rs smoke subset\n")
        assert s.count("!= 25") == 2
        s = s.replace("!= 25", "!= len(PUBLIC_GAME_IDS)")
        assert s.count(l1.CELL15_EXTRA_OLD) == 1 and s.count(l1.CELL15_SELECT_OLD) == 1
        s = s.replace(l1.CELL15_EXTRA_OLD, l1.CELL15_EXTRA_NEW.replace("thui-l1", "thui-rs")).replace(l1.CELL15_SELECT_OLD, CELL15_SELECT_SMOKE)
        cells[15]["source"] = s.splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (x, y) in enumerate(zip(before, after)) if x != y]
    assert changed == [0, 1, 3, 5, 7, 9, 11, 15], f"cells changed {changed}"
    for i, c in enumerate(cells):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]), filename=f"cell{i}")
    assert "animfast" not in json.dumps(after[1:])
    assert after[9].count("THUI_RS_GRAFT") == 1 and ("_thui_rs_analyze" in after[9]) == (not CONTROL)
    assert after[9].index("THUI_ANIM_GRAFT ok") < after[9].index("THUI_RS_GRAFT"), "restart must be installed after the anim import"
    assert 'bm.label == "anim-20260807-anim"' in after[11]
    assert "bm.solver.max_runtime_s_per_game = 7920.0" in after[13]
    assert ("smoke" in after[15]) == (not FULL) and "thui-l1" not in after[15]

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(B71_META.read_text(encoding="utf-8")); meta.pop("id_no", None)
    assert meta["dataset_sources"][-1] == ANIM_DS and meta["machine_shape"] == "NvidiaRtxPro6000" and meta["enable_gpu"] is True
    meta["id"] = f"{OWNER}/{SLUG}"; meta["title"] = SLUG; meta["code_file"] = OUT_NB.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}, smoke={not FULL}, control={CONTROL}")


if __name__ == "__main__":
    main()
