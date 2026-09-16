"""thui-af -- ACTION FLOOR on the anim harness: when the model stops acting, the harness commits one exploratory action itself.

Why (2026-09-15). On the anim base the stalled games are under-acted, not over-died: anim-r2 tn36 = 36 analysis turns, 46 actions,
0 deaths, L1 in 2.2 h; 19 of its 35 turn ends were `Yielded control to solver: turn_time_budget` (180 s of python inspection +
thinking, no `action(...)` call), 16 executed. sp80 17/36 turn ends without an action, bp35 15/33. Every prompt-side lever on this
model priced NULL (wm, db v0/v1); the two mechanisms that did change behaviour are harness-side (the bundle's hard no-op guard;
the June milestone 2nd place's numpy click heuristic used as a FALLBACK when the model does not act -- arcprize.org milestone-1 post).

What the graft does (cell 9 tail, after the anim import): ONE wrapper on `ToolAgent.analyze`. After the original returns, if the turn
ended with no executed action (yield or plain no-action) the per-game stall counter goes up; once it reaches THUI_AF_STALL_TURNS (2)
on the same level, the wrapper calls the solver's own `step_env` with ONE action -- a MOUSE click on a rare-colour cell the floor has
not used on this level (background = the modal colour), else a random non-mouse valid action, never RESET -- and prints
`THUI_AF_FLOOR`. An executed model action resets the counter; a level change resets counter, cap and used cells; at most
THUI_AF_MAX_PER_LEVEL (40) floor actions per level; nothing fires when `should_stop()` is true. The model sees the outcome at its next
(retry) turn through the runtime state (frame + history) exactly like its own actions; no prompt text is added. Seed 20260915.
--control: identical notebook, no wrapper (THUI_AF_GRAFT control).

Stated costs: a floor action is an action -- if the level is cleared later it is charged by RHAE like any other (that is what the
per-level cap bounds); on a level never cleared it costs nothing. The history shows the floor's action as an action, so the model
may read it as its own; v0 accepts that.

Pre-registered read (smoke bp35 / sp80 / tn36 at 1,800 s, v0 vs --control):
  1. Mechanism: THUI_AF_GRAFT ok; >= 3 THUI_AF_FLOOR executed=True across the three games. Fewer = the stall pattern did not recur
     inside 1,800 s -> VOID (measured nothing), not FAIL.
  2. Levels >= control on all three (rule of every smoke here; read against both db controls' spread before calling FAIL).
  3. Secondary, descriptive only: actions per game and the no-action-turn fraction on the three games (thui-m0/turns_read.py + the
     transcript `step_executed:` counts) -- the lever's own mechanism, not a score.
  4. PASS buys a full-25 pair on the anim base (2.4 GPU-h per draw). Nothing here is a submission.

Build:  PYTHONUTF8=1 python thui-af/build_notebook.py               -> taaf-thui-af-v0.ipynb        (smoke, graft)
        PYTHONUTF8=1 python thui-af/build_notebook.py --control     -> taaf-thui-af-ctl.ipynb       (smoke, no wrapper)
        PYTHONUTF8=1 python thui-af/build_notebook.py --full [--control]  -> taaf-thui-af-{v0,ctl}-full25-r1.ipynb
Teeth:  python thui-af/test_af_graft.py   (0 GPU: executes the notebook's cell-9 graft against the bundle's REAL runtime_state.py)
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
SLUG = (("thui-af-ctl-full25-r1" if CONTROL else "thui-af-v0-full25-r1") if FULL else ("thui-af-ctl" if CONTROL else "thui-af-v0"))
OUT_NB = HERE / f"taaf-{SLUG}.ipynb"
ANIM_DS = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
B71_CELLS = (1, 3, 5, 7, 9, 11, 15)
SMOKE_GAMES = ("bp35-0a0ad940", "sp80-589a99af", "tn36-ef4dde99")
SMOKE_CLOCK_S = 1800

_spec = importlib.util.spec_from_file_location("thui_l1_builder", L1)
l1 = importlib.util.module_from_spec(_spec)
_argv, sys.argv = sys.argv, sys.argv[:1]
_spec.loader.exec_module(l1)
sys.argv = _argv

CELL0_MD = f"""# {SLUG} (Thuitanium / Knowless Crew) -- action floor on the animation-awareness duck harness

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
- **cell 9 (tail)** -- {"CONTROL arm: no wrapper; the imported harness is asserted untouched." if CONTROL else "one wrapper on `ToolAgent.analyze`: after 2 consecutive turn ends with no executed action on the same level, the harness commits one exploratory action through the solver's own `step_env` (a MOUSE click on a rare-colour cell not used before on this level, else a random non-mouse valid action; cap 40 per level). No prompt text is added."}
{"- **cell 15** -- smoke: " + ", ".join(SMOKE_GAMES) + f" at {SMOKE_CLOCK_S} s each." if not FULL else "- **cell 15** -- all 25 public games, upstream clock."}

Build script: `thui-af/build_notebook.py` in our agent repo (asserts exactly those cells changed). 2026-09-15.
"""

CELL9_AF = '''
# ---- thui-af: ACTION FLOOR -- after K turn ends with no executed action on one level, the harness commits one exploratory action.
import random as _thui_af_random
from inference.agent.runtime_state import load_runtime_state as _thui_af_load
from inference.agent.action_names import to_model_actions as _thui_af_model_actions

THUI_AF_STALL_TURNS = 2       # consecutive no-action turn ends before the floor fires
THUI_AF_MAX_PER_LEVEL = 40    # cap per level: every floor action is charged by RHAE if the level is cleared later
THUI_AF_SEED = 20260915


def _thui_af_pick(frame, valid_actions, used, rng):
    """One exploratory action: MOUSE on a rare-colour cell the floor has not used on this level, else a random non-mouse action."""
    names = [a for a in _thui_af_model_actions(valid_actions or []) if a != "RESET"]
    if "MOUSE" in names and frame is not None and frame.grid:
        counts = {}
        for row in frame.grid:
            for v in row:
                counts[v] = counts.get(v, 0) + 1
        background = max(counts, key=counts.get)
        cells = [(r, c) for r, row in enumerate(frame.grid) for c, v in enumerate(row) if v != background and (r, c) not in used]
        if cells:
            r, c = rng.choice(cells)
            used.add((r, c))
            return {"action": "MOUSE", "row": r, "col": c}
    others = [a for a in names if a != "MOUSE"]
    if others:
        return {"action": rng.choice(others)}
    return None


_thui_af_orig_analyze = _ta.ToolAgent.analyze


def _thui_af_analyze(self, state_path, action_num, *args, **kwargs):
    result = _thui_af_orig_analyze(self, state_path, action_num, *args, **kwargs)
    try:
        st = self.__dict__.setdefault("_thui_af", {"level": None, "stall": 0, "n": 0, "used": set(),
                                                    "rng": _thui_af_random.Random(THUI_AF_SEED), "fired": 0})
        if result is None or getattr(result, "retryable_failure", False):
            return result
        frame, _history = _thui_af_load(state_path) if state_path.exists() else (None, [])
        level = frame.level if frame is not None else None
        if level != st["level"]:
            st.update(level=level, stall=0, n=0, used=set())
        if getattr(result, "step_executed", False):
            st["stall"] = 0
            return result
        st["stall"] += 1
        step_env = kwargs.get("step_env")
        should_stop = kwargs.get("should_stop")
        if st["stall"] < THUI_AF_STALL_TURNS or st["n"] >= THUI_AF_MAX_PER_LEVEL or step_env is None:
            return result
        if should_stop is not None and should_stop():
            return result
        action = _thui_af_pick(frame, kwargs.get("valid_actions"), st["used"], st["rng"])
        if action is None:
            return result
        payload = step_env({"actions": [action]})
        executed = isinstance(payload, dict) and bool(payload.get("executed"))
        if executed:
            st["n"] += 1
            st["fired"] += 1
        changed = payload.get("board_changed") if isinstance(payload, dict) else None
        print(f"THUI_AF_FLOOR level={level} stall={st['stall']} action={action} executed={executed} changed={changed} "
              f"n_level={st['n']} fired={st['fired']}", flush=True)
    except Exception as exc:   # never let the graft kill a turn
        print(f"thui-af: wrapper error {exc!r}", flush=True)
    return result


_ta.ToolAgent.analyze = _thui_af_analyze
assert _ta.ToolAgent.analyze is _thui_af_analyze
print("THUI_AF_GRAFT ok", flush=True)
'''

CELL9_CTL = '''
# ---- thui-af CONTROL: no wrapper; the harness is asserted untouched.
assert _ta.ToolAgent.analyze.__name__ == "analyze"
print("THUI_AF_GRAFT control (no wrapper installed)", flush=True)
'''

CELL15_SELECT_SMOKE = (l1.CELL15_SELECT_OLD +
                       f'    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-af smoke clock\n'
                       f'    print(f"thui-af: smoke {{len(bm.games)}} games @ {{bm.solver.max_runtime_s_per_game}} s", flush=True)\n')


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
        s = b[i].replace("thui-animfast", "thui-af").replace("THUI_ANIMFAST_GRAFT", "THUI_ANIM_GRAFT")
        if i == 9:
            s += "\nimport inference.agent.tool_agent as _ta\nassert _ta is _tool_agent\n" + (CELL9_CTL if CONTROL else CELL9_AF)
        cells[i]["source"] = s.splitlines(keepends=True)
        cells[i].pop("attachments", None)
    if not FULL:
        s = "".join(cells[15]["source"])
        m = re.search(r"PUBLIC_GAME_IDS = tuple\(\[\n(?:    \"[a-z0-9]{4}-[0-9a-f]{8}\",?\n){25}\]\)\n", s)
        assert m, "cell 15: the 25-game PUBLIC_GAME_IDS tuple not found"
        for g in SMOKE_GAMES:
            assert f'"{g}"' in m.group(0), f"{g} is not one of the 25 public ids"
        s = s.replace(m.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-af smoke subset\n")
        assert s.count("!= 25") == 2
        s = s.replace("!= 25", "!= len(PUBLIC_GAME_IDS)")
        assert s.count(l1.CELL15_EXTRA_OLD) == 1 and s.count(l1.CELL15_SELECT_OLD) == 1
        s = s.replace(l1.CELL15_EXTRA_OLD, l1.CELL15_EXTRA_NEW.replace("thui-l1", "thui-af")).replace(l1.CELL15_SELECT_OLD, CELL15_SELECT_SMOKE)
        cells[15]["source"] = s.splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (x, y) in enumerate(zip(before, after)) if x != y]
    assert changed == [0, 1, 3, 5, 7, 9, 11, 15], f"cells changed {changed}"
    for i, c in enumerate(cells):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]), filename=f"cell{i}")
    assert "animfast" not in json.dumps(after[1:])
    assert after[9].count("THUI_AF_GRAFT") == 1 and ("_thui_af_analyze" in after[9]) == (not CONTROL)
    assert after[9].index("THUI_ANIM_GRAFT ok") < after[9].index("THUI_AF_GRAFT"), "floor must be installed after the anim import"
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
