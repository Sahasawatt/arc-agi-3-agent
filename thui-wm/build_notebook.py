"""thui-wm -- the fast base with the WORLD-MODEL WIPE GUARD grafted into the harness (ARENA 3, 2026-09-14).

Why. `inference/agent/tool_agent.py:1113-1126` (`_update_summarized_knowledge_from_step_summary`) erases the six
summarized-knowledge fields -- world_model, goal_model, action_model, recent_findings, open_questions, current_plan --
whenever the last step summary carries `level_transition`, `run_complete` OR `game_over`. `game_over` is set at
`framework/solver.py:718` from `GameState.GAME_OVER`, i.e. a within-level death, after which `_execute_auto_reset`
(`solver.py:663`) RESETs the same level. So every in-level death throws away everything the agent had written down
about the level it is about to replay. Found by ARENA 3's refuter of axis A inside A's own mechanism trace; verified
in code by the judge. Population from our own events: fast-v0 d2 **26 such wipes on the level the run died on, in 9
games** (sp80 x7, tu93 x7, bp35 x5, tn36 x4); a7-v1 d2 **33 in 8 games** (r11l x16, tu93 x8, sp80 x4). Ceiling with
the arena's rule (dying level cleared at the Flash-family median eff 0.80): +2.75 / +3.03 public.

What the graft does (cell 9, applied to the IMPORTED module after his serving setup; solver tree on disk untouched):
  ONE wrapper on `ToolAgent._update_summarized_knowledge_from_step_summary`: when the summary has `game_over` and
  NOT `level_transition` and NOT `run_complete`, the wipe is skipped and a line `THUI_WM_KEPT level=<n> span=<s>` is
  printed; every other case calls the original unchanged. The prompt still tells the model "reached GAME_OVER" /
  "The game is over." (tool_agent.py:1092, :1209) -- only the erasure is removed. Design choice, stated: ALL six
  fields are kept, including current_plan; if the smoke FAILS the variant to try next is keep-world/goal/action,
  wipe plan. --control: identical notebook, no wrapper (marker THUI_WM_GRAFT control).

Pre-registered read (smoke: tu93 / sp80 / r11l at 1,800 s, 3-way, treatment vs --control):
  1. THUI_WM_GRAFT ok; >= 1 THUI_WM_KEPT in the treatment log. Zero = no in-level death happened inside 1,800 s on
     three games chosen for having the most -> the run measured nothing (VOID, not a result).
  2. Levels >= control on all three games = the lever did not regress where it fired (the ONLY thing a 3-game single
     draw can read -- the L1 smoke measured that it cannot resolve anything under ~4 public points). Any game below
     control = FAIL: a kept-but-wrong model is worse than a blank one on that game.
  3. Cost ~40 min per arm, 0 slots. A PASS buys a full-25 A/B (2.4 GPU-h per draw, pooled n=2 vs the fast pool), not
     a submission.

Build:  PYTHONUTF8=1 python thui-wm/build_notebook.py             -> taaf-thui-wm-v0.ipynb  (smoke, treatment)
        PYTHONUTF8=1 python thui-wm/build_notebook.py --control   -> taaf-thui-wm-ctl.ipynb (smoke, no wrapper)
        PYTHONUTF8=1 python thui-wm/build_notebook.py --full           -> taaf-thui-wm-v0-full25-r1.ipynb  (25 games, treatment)
        PYTHONUTF8=1 python thui-wm/build_notebook.py --full --control -> taaf-thui-wm-ctl-full25-r1.ipynb (25 games, no wrapper)

Pre-registered read for the full-25 A/B (written 2026-09-14 after the smoke PASSED: v0 4/3/0 vs ctl 1/3/0 on r11l/tu93/sp80,
36 THUI_WM_KEPT, control marker present):
  1. Compare ONLY via eval/rank_runs.py (repo rule); harvest both into the per-level census with flash_census_harvest.py.
  2. Primary: v0-full25-r1 vs ctl-full25-r1, same-day draws, 25 paired games. Secondary: each vs the fast pool.
  3. Mechanism check first: >= 1 THUI_WM_KEPT in v0 on >= 5 games, else the draw is VOID for the lever (not a FAIL).
  4. One draw each cannot separate under ~4 public points (R57/A4 MDE, L1 full-25 p=0.369 taught this); a PASS here means
     "v0 >= ctl AND levels gained on the wipe-heavy games (r11l/tu93/sp80/bp35/tn36)"; anything else = pool draw 2 or drop.
Teeth:  python thui-wm/test_wm_graft.py   (0 GPU: executes the notebook's own cell-9 source against a stub)
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
L1 = HERE.parent / "thui-l1" / "build_notebook.py"
SRC_NB = FAST / "upstream-keithtyser-duck-qwen3-8-flash-next-nvfp4-mtp.ipynb"
SRC_META = FAST / "upstream-kernel-metadata.json"
OWNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), "sahasawatt")
FULL = "--full" in sys.argv
CONTROL = "--control" in sys.argv
# full-25 A/B keeps the smoke's graft version in the name (v0), one slug per arm, r1 = first draw
SLUG = (("thui-wm-ctl-full25-r1" if CONTROL else "thui-wm-v0-full25-r1") if FULL
        else ("thui-wm-ctl" if CONTROL else "thui-wm-v0"))
OUT_NB = HERE / f"taaf-{SLUG}.ipynb"
SMOKE_GAMES = ("tu93-0768757b", "sp80-589a99af", "r11l-495a7899")   # the three with the most in-level deaths on both runs
SMOKE_CLOCK_S = 1800

# reuse the fast base's header cells and the L1 builder's mount/smoke constants verbatim (both are the shipped chassis)
sys.path.insert(0, str(FAST))
import build_notebook as fast  # noqa: E402
_spec = importlib.util.spec_from_file_location("thui_l1_builder", L1)
l1 = importlib.util.module_from_spec(_spec)
_argv, sys.argv = sys.argv, sys.argv[:1]   # the L1 builder reads its own flags at import; we only want its constants
_spec.loader.exec_module(l1)
sys.argv = _argv

CELL0_MD = f"""# {SLUG} (Thuitanium / Knowless Crew) — the fast base with the world-model wipe guard

**This is a Knowless Crew / Thuitanium fork, and the solver is not ours.** Same two upstreams as `thui-fast-v0`, executed as they ship:

- **Serving**: Keith Tyser's [Duck Qwen3.8 Flash Next NVFP4 MTP](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp)
  — his pinned `RadixArk/Qwen3.8-Flash-Next-NVFP4` asset, offline vLLM runtime, NVFP4 PLE patch, MTP-3 profile, watchdog.
- **Solver**: the Tufa Labs duck harness (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
  Michal Tesnar, Stefano Viel) — his source bundle, unmodified on disk.
- **Weights**: RadixArk's NVFP4 quantisation of Qwen/Qwen3.8-Flash-Next (Qwen licence terms apply).

⚠️ Every score quoted by any upstream is theirs.

## What we changed

- **cell 0 / 1** — this header; Tufa's header reworded in the third person.
- **cell 3** — full diagnostics on an interactive public run, minimal in a real rerun.
- **cell 5 / 15** — the competition mount resolved (Kaggle serves two layouts).
- **cell 9** — {"CONTROL arm: the harness module is imported and asserted untouched (no wrapper)." if CONTROL else "one wrapper on the imported harness: `ToolAgent._update_summarized_knowledge_from_step_summary` keeps the six summarized-knowledge fields across an in-level `game_over` (the harness erases them before the auto-RESET replays the same level); level transitions and run completion wipe exactly as upstream does."}
{"- **cell 15** — smoke: " + ", ".join(SMOKE_GAMES) + f" at {SMOKE_CLOCK_S} s each." if not FULL else "- **cell 15** — all 25 public games, upstream clock (full-25 A/B draw r1)."}

Build script: `thui-wm/build_notebook.py` in our agent repo (asserts exactly those cells changed). ARENA 3 lever (2026-09-14).
"""

CELL9_COMMON = '''
# ---- thui-wm (ARENA 3): world-model wipe guard. The guard is a pure function first, so the teeth drive it in-kernel.
assert "inference" not in sys.modules, "solver imported before the WM graft"

def _thui_wm_should_keep(summary):
    """True when the summary is an in-level death and nothing else: keep the knowledge, the level is about to replay."""
    if not summary:
        return False
    return bool(summary.get("game_over")) and not summary.get("level_transition") and not summary.get("run_complete")

assert _thui_wm_should_keep({"game_over": True}) is True
assert _thui_wm_should_keep({"game_over": True, "level_transition": True}) is False
assert _thui_wm_should_keep({"level_transition": True}) is False
assert _thui_wm_should_keep({"run_complete": True}) is False
assert _thui_wm_should_keep(None) is False and _thui_wm_should_keep({}) is False
print("thui-wm: guard teeth ok", flush=True)
'''

CELL9_WRAP = '''
import inference.agent.tool_agent as _ta
_orig_wm_update = _ta.ToolAgent._update_summarized_knowledge_from_step_summary

def _thui_wm_update(self):
    summary = getattr(self, "_last_step_summary", None)
    try:
        if _thui_wm_should_keep(summary):
            kept = sum(len(str(v or "")) for v in getattr(self, "_summarized_knowledge", {}).values())
            print(f"THUI_WM_KEPT level={summary.get('level')} span={summary.get('action_span')} kept_chars={kept}", flush=True)
            return None
    except Exception as exc:  # never let the graft kill a step
        print(f"thui-wm: wrapper error {exc!r}", flush=True)
    return _orig_wm_update(self)

_ta.ToolAgent._update_summarized_knowledge_from_step_summary = _thui_wm_update
assert _ta.ToolAgent._update_summarized_knowledge_from_step_summary is _thui_wm_update
print(f"THUI_WM_GRAFT ok agent={Path(_ta.__file__)}", flush=True)
'''

CELL9_CTL = '''
import inference.agent.tool_agent as _ta
assert _ta.ToolAgent._update_summarized_knowledge_from_step_summary.__name__ == "_update_summarized_knowledge_from_step_summary"
print("THUI_WM_GRAFT control (no wrapper installed)", flush=True)
'''

CELL15_SELECT_SMOKE = (l1.CELL15_SELECT_OLD +
                       f'    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-wm smoke clock\n'
                       f'    print(f"thui-wm: smoke {{len(bm.games)}} games @ {{bm.solver.max_runtime_s_per_game}} s", flush=True)\n')


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 18, f"{SRC_NB.name}: expected 18 cells, found {len(cells)}"
    before = ["".join(c["source"]) for c in cells]
    assert before[0].startswith("## About this fork") and before[1].startswith("# Tufa Labs ARC3 submission")

    def rep(i: int, old: str, new: str) -> None:
        s = "".join(cells[i]["source"])
        assert s.count(old) == 1, f"cell {i}: anchor not found exactly once ({s.count(old)}): {old[:70]!r}"
        cells[i]["source"] = s.replace(old, new).splitlines(keepends=True)

    cells[0]["cell_type"] = "markdown"; cells[0]["source"] = CELL0_MD.splitlines(keepends=True)
    cells[1]["source"] = fast.CELL1_MD.splitlines(keepends=True); cells[1].pop("attachments", None)
    rep(3, fast.CELL3_OLD, fast.CELL3_NEW.replace("thui-fast", "thui-wm"))
    rep(5, l1.CELL5_ANCHOR, "        _WHEELS,\n")
    cells[5]["source"] = (l1.CELL5_RESOLVER.replace("thui-l1", "thui-wm") + "".join(cells[5]["source"])).splitlines(keepends=True)
    cells[9]["source"] = ("".join(cells[9]["source"]) + CELL9_COMMON + (CELL9_CTL if CONTROL else CELL9_WRAP)).splitlines(keepends=True)
    rep(15, l1.CELL15_MOUNT_OLD, l1.CELL15_MOUNT_NEW.replace("thui-l1", "thui-wm"))
    if not FULL:
        s = "".join(cells[15]["source"])
        m = re.search(r"PUBLIC_GAME_IDS = tuple\(\[\n(?:    \"[a-z0-9]{4}-[0-9a-f]{8}\",?\n){25}\]\)\n", s)
        assert m, "cell 15: the 25-game PUBLIC_GAME_IDS tuple not found"
        for g in SMOKE_GAMES:
            assert f'"{g}"' in m.group(0), f"{g} is not one of the 25 public ids"
        s = s.replace(m.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-wm smoke subset\n")
        assert s.count("!= 25") == 2, s.count("!= 25")
        s = s.replace("!= 25", "!= len(PUBLIC_GAME_IDS)")
        assert s.count(l1.CELL15_EXTRA_OLD) == 1 and s.count(l1.CELL15_SELECT_OLD) == 1
        s = s.replace(l1.CELL15_EXTRA_OLD, l1.CELL15_EXTRA_NEW.replace("thui-l1", "thui-wm")).replace(l1.CELL15_SELECT_OLD, CELL15_SELECT_SMOKE)
        cells[15]["source"] = s.splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert changed == [0, 1, 3, 5, 9, 15], f"cells changed {changed}"
    assert "attachments" not in cells[1] and "tufa_labs.png" not in json.dumps(nb)
    for i, c in enumerate(cells):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]), filename=f"cell{i}")
    assert after[0].startswith(f"# {SLUG} (Thuitanium / Knowless Crew)")
    for bad in ("Tufa Labs ARC3 submission", "our milestone-winning", "attachment:"):
        assert bad not in after[1]
    assert after[9].count("THUI_WM_GRAFT") == 1 and after[9].count("guard teeth ok") == 1
    assert ("_thui_wm_update" in after[9]) == (not CONTROL)
    assert "THUI_L1" not in after[9] and "thui-l1" not in after[5] and "thui-l1" not in after[15]
    assert after[7] == before[7] and after[11] == before[11] and after[13] == before[13]
    assert l1.WHEELS_NESTED not in after[5] and l1.WHEELS_NESTED not in after[15]
    assert ("smoke" in after[15]) == (not FULL)

    # the guard runs here too: the same source the kernel executes, on the same teeth
    exec(CELL9_COMMON.replace('assert "inference" not in sys.modules, "solver imported before the WM graft"\n', ""), {"sys": sys})

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(SRC_META.read_text(encoding="utf-8")); meta.pop("id_no", None)
    assert meta["model_sources"] == ["keithtyser/qwen3-8-flash-next-nvfp4/PyTorch/radixark-modelopt-fp4/1"]
    assert meta["machine_shape"] == "NvidiaRtxPro6000" and meta["enable_gpu"] is True
    meta["id"] = f"{OWNER}/{SLUG}"; meta["title"] = SLUG; meta["code_file"] = OUT_NB.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}, smoke={not FULL}, control={CONTROL}")


if __name__ == "__main__":
    main()
