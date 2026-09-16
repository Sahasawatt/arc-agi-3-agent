"""thui-l1 -- the fast base (B69) with NO-IMPACT DETECTION grafted into the harness (B80 lever L1).

Why (2026-09-10, B80). sonpham-org/arc-3 measured +55% levels at equal action budget on the Tufa harness by refusing to count an
action whose only board change is the deterministic HUD / moves-counter band. Our own events (thui-fast-v0 v2 and thui-a7-v1 v2)
carry 6.2% such actions, in 8 of 25 games, piled on the levels those games never cleared (tn36 47 on its uncleared L1, vc33 22 on
L4, bp35 24 on its last level). The harness reports them as `board_changed=True`, so the model reads a dead click as an effect and
builds a hypothesis on it; the prompt already asks it to "verify that it affected gameplay objects rather than only HUD elements",
i.e. the harness knows the class and leaves the work to the model.

What the graft does (cell 9, applied to the IMPORTED modules after his serving setup, solver tree on disk untouched):
  1. `_HarnessGameSession._execute_action` wrapper -- per game, learn the HUD band online: rows touched by >= 90% of the
     board-changing actions once >= 20 have been seen, at most 4 rows (the census rule, eval/no_impact_census.py). RESET and
     level-completing actions are excluded from learning (they redraw the board). When a band exists and an action's changed
     rows all lie inside it: payload["board_changed"] = False, payload["no_impact"] = True, payload["hud_rows"] = band, and a
     log line THUI_L1_NOIMPACT game=<id> action=<n> rows=<rows>.
  2. `ToolAgent._compact_action_result` wrapper -- carries no_impact / hud_rows into the result the model's python sees.
  3. `ToolAgent._summarize_step_sequence` wrapper -- counts no-impact actions in the sequence (no_impact_count, hud_rows).
  4. `ToolAgent._describe_last_outcome` wrapper -- appends "N of these actions changed only the counter strip (rows R) and had no
     impact on gameplay objects." to the next user prompt.
  The frames themselves are NOT masked: the model can still read the counter (tn36 budgets by it); only the harness's verdict
  on "did this action do anything" changes. Teeth: a synthetic sequence drives the band learner (row 0 every action + a random
  row) and must yield band {0}; a sequence touching 6 rows every action must yield no band; the four attributes must be the
  wrappers. Marker: THUI_L1_GRAFT ok.
  --control: identical notebook with the wrappers NOT installed (marker THUI_L1_GRAFT control) -- the concurrency-matched baseline.

Pre-registered read (smoke: tn36 / vc33 / bp35 at 1,800 s, 3-way, treatment vs --control; both mounts resolved):
  1. THUI_L1_GRAFT ok; on tn36 the log carries >= 1 THUI_L1_NOIMPACT (the census saw 47 on the full run; the band needs 20 changing
     actions first). Zero on all three = the learner never armed inside 1,800 s -> the run measured nothing (VOID, fix, rerun).
  2. PASS = levels on the three games >= the control's on every game AND the control's no-impact share (offline census over its
     events) >= 5% (the precondition held in this draw too); the lever's claim is stronger if tn36 or vc33 clears a level the control
     does not. FAIL = any game below the control (the counter was information the model needed) -> close L1.
  3. Cost: ~40 min per arm; 0 slots.
Full (`--full`, thui-l1-v1, 25 games): two draws pooled vs the `fast` pool (arms.json), B35 floor vs the same pool, wall <= 8,700 s.

Build:  PYTHONUTF8=1 python thui-l1/build_notebook.py             -> taaf-thui-l1-v0.ipynb  (smoke, treatment)
        PYTHONUTF8=1 python thui-l1/build_notebook.py --control   -> taaf-thui-l1-ctl.ipynb (smoke, no wrappers)
        PYTHONUTF8=1 python thui-l1/build_notebook.py --full      -> taaf-thui-l1-v1.ipynb  (25 games)
Push:   python scripts/kaggle_push_kernel.py <this dir>   (from arc-agi-pub; token = sahasawatt; rebuild the variant first)
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAST = HERE.parent / "thui-fast"
SRC_NB = FAST / "upstream-keithtyser-duck-qwen3-8-flash-next-nvfp4-mtp.ipynb"
SRC_META = FAST / "upstream-kernel-metadata.json"
OWNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), "sahasawatt")
FULL = "--full" in sys.argv
CONTROL = "--control" in sys.argv
assert not (FULL and CONTROL)
SLUG = "thui-l1-v1" if FULL else ("thui-l1-ctl" if CONTROL else "thui-l1-v0")
OUT_NB = HERE / f"taaf-{SLUG}.ipynb"
SMOKE_GAMES = ("tn36-ef4dde99", "vc33-5430563c", "bp35-0a0ad940")   # the three HUD games whose no-impact actions sit on the level they never cleared
SMOKE_CLOCK_S = 1800
HUD_FRAC, HUD_MIN, HUD_MAX_ROWS = 0.9, 20, 4
COMP = "arc-prize-2026-arc-agi-3"
WHEELS_NESTED = "/kaggle/input/competitions/" + COMP + "/arc_agi_3_wheels"

sys.path.insert(0, str(FAST))
import build_notebook as fast  # noqa: E402

CELL0_MD = f"""# {SLUG} (Thuitanium / Knowless Crew) — the fast base with no-impact detection in the harness

**This is a Knowless Crew / Thuitanium fork, and the solver is not ours.** Same two upstreams as `thui-fast-v0`, executed as they ship:

- **Serving**: Keith Tyser's [Duck Qwen3.8 Flash Next NVFP4 MTP](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp)
  — his pinned `RadixArk/Qwen3.8-Flash-Next-NVFP4` asset, offline vLLM runtime, NVFP4 PLE patch, MTP-3 profile, watchdog.
- **Solver**: the Tufa Labs duck harness (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
  Michal Tesnar, Stefano Viel) — his source bundle, unmodified on disk.
- **Weights**: RadixArk's NVFP4 quantisation of Qwen/Qwen3.8-Flash-Next (Qwen licence terms apply).
- **Idea credit**: no-impact detection is Son Pham's measured lever on this harness (sonpham-org/arc-3); our implementation.

⚠️ Every score quoted by any upstream is theirs.

## What we changed

- **cell 0 / 1** — this header; Tufa's header reworded in the third person.
- **cell 3** — full diagnostics on an interactive public run, minimal in a real rerun.
- **cell 5 / 15** — the competition mount resolved (Kaggle serves two layouts).
- **cell 9** — {"CONTROL arm: the harness modules are imported and asserted untouched (no wrappers)." if CONTROL else "four wrappers on the imported harness: an action whose only board change lies in the game's own counter strip (rows touched by ≥ 90 % of board-changing actions, learned online) is reported as `board_changed=False` / `no_impact=True`, and the next prompt says so. Frames are not masked."}
{"- **cell 15** — smoke: " + ", ".join(SMOKE_GAMES) + f" at {SMOKE_CLOCK_S} s each." if not FULL else ""}

Build script: `thui-l1/build_notebook.py` in our agent repo (asserts exactly those cells changed). Ticket B80 / lever L1.
"""

CELL5_ANCHOR = '        "' + WHEELS_NESTED + '",\n'
CELL5_RESOLVER = """# thui-l1: resolve the competition mount instead of assuming its layout (Kaggle serves either
# /kaggle/input/competitions/<comp> or /kaggle/input/<comp>, varying between runs).
_COMP_CANDIDATES = ["/kaggle/input/competitions/__COMP__", "/kaggle/input/__COMP__"]
_COMP_DIR = next((_p for _p in _COMP_CANDIDATES if os.path.isdir(_p)), None)
assert _COMP_DIR is not None, "thui-l1: no competition mount found; /kaggle/input holds " + repr(
    sorted(os.listdir("/kaggle/input")) if os.path.isdir("/kaggle/input") else "MISSING")
_WHEELS = os.path.join(_COMP_DIR, "arc_agi_3_wheels")
assert os.path.isdir(_WHEELS), "thui-l1: resolved wheels dir is not a directory: " + _WHEELS
print("thui-l1: competition mount = " + _COMP_DIR, flush=True)
""".replace("__COMP__", COMP)

# The band learner is a pure function so the teeth can drive it with synthetic sequences in-kernel.
CELL9_COMMON = f'''
# ---- thui-l1 (B80 / L1): no-impact detection. Pure band learner first (teeth drive it), then the wrappers.
assert "inference" not in sys.modules, "solver imported before the L1 graft"
_THUI_HUD_FRAC, _THUI_HUD_MIN, _THUI_HUD_MAX_ROWS = {HUD_FRAC}, {HUD_MIN}, {HUD_MAX_ROWS}

def _thui_hud_update(st, changed_rows, learn=True):
    """st: per-game dict(n, rows, band). Returns True when changed_rows is non-empty and lies inside the current band."""
    if not changed_rows:
        return False
    if learn:
        st["n"] += 1
        for r in changed_rows:
            st["rows"][r] = st["rows"].get(r, 0) + 1
        if st["n"] >= _THUI_HUD_MIN:
            band = {{r for r, k in st["rows"].items() if k / st["n"] >= _THUI_HUD_FRAC}}
            st["band"] = band if 0 < len(band) <= _THUI_HUD_MAX_ROWS else None
    band = st.get("band")
    return bool(band) and changed_rows <= band

def _thui_hud_new():
    return {{"n": 0, "rows": {{}}, "band": None, "noimp": 0}}

# teeth 1: row 0 ticks every action, plus a wandering row -> band {{0}}; the 25th action touching only row 0 is no-impact
_st = _thui_hud_new()
for _i in range(24):
    _thui_hud_update(_st, {{0, 10 + (_i % 7)}})
assert _st["band"] == {{0}}, _st
assert _thui_hud_update(_st, {{0}}) is True and _thui_hud_update(_st, {{0, 5}}) is False
# teeth 2: a playfield that redraws 6 rows every action -> no band, nothing is ever no-impact
_st = _thui_hud_new()
for _i in range(30):
    assert _thui_hud_update(_st, set(range(6))) is False
assert _st["band"] is None, _st
# teeth 3: below the minimum count nothing is classified even if every action touches row 0 only
_st = _thui_hud_new()
assert all(_thui_hud_update(_st, {{0}}) is False for _i in range(_THUI_HUD_MIN - 1))
print("thui-l1: band learner teeth ok", flush=True)
'''

CELL9_WRAP = '''
import inference.framework.solver as _sol
import inference.agent.tool_agent as _ta
_orig_exec = _sol._HarnessGameSession._execute_action
_orig_compact = _ta.ToolAgent._compact_action_result
_orig_summ = _ta.ToolAgent._summarize_step_sequence
_orig_desc = _ta.ToolAgent._describe_last_outcome

def _thui_exec(self, action, **kw):
    prev = _sol._grid_from_state(self.game.current_state)
    payload = _orig_exec(self, action, **kw)
    try:
        if not payload.get("executed", True):
            return payload
        new = _sol._grid_from_state(self.game.current_state)
        changed = {r for r in range(min(len(prev), len(new))) if prev[r] != new[r]} if prev and new else set()
        st = self.__dict__.setdefault("_thui_hud", _thui_hud_new())
        learn = action.id.name != "RESET" and not payload.get("level_completed")
        if learn and _thui_hud_update(st, changed):
            st["noimp"] += 1
            payload["board_changed"] = False
            payload["no_impact"] = True
            payload["hud_rows"] = sorted(st["band"])
            gid = self.game.game_run.game_id if getattr(self.game, "game_run", None) else "?"
            print(f"THUI_L1_NOIMPACT game={gid} action={payload.get('action_num')} rows={sorted(changed)} band={sorted(st['band'])}", flush=True)
    except Exception as exc:  # never let the graft kill a step
        print(f"thui-l1: wrapper error {exc!r}", flush=True)
    return payload

def _thui_compact(self, payload):
    compact = _orig_compact(self, payload)
    if payload.get("no_impact"):
        compact["no_impact"] = True
        compact["hud_rows"] = payload.get("hud_rows")
    return compact

def _thui_summ(self, action_results):
    summary = _orig_summ(self, action_results)
    if summary is not None:
        hits = [item for item in action_results if item.get("executed") and item.get("no_impact")]
        summary["no_impact_count"] = len(hits)
        if hits:
            summary["hud_rows"] = hits[-1].get("hud_rows")
    return summary

def _thui_desc(self, summary):
    text = _orig_desc(self, summary)
    if summary and summary.get("no_impact_count"):
        text += (f" {summary['no_impact_count']} of these actions changed only the game's counter strip (rows {summary.get('hud_rows')}) "
                 "and had NO impact on gameplay objects; do not read them as effects.")
    return text

_sol._HarnessGameSession._execute_action = _thui_exec
_ta.ToolAgent._compact_action_result = _thui_compact
_ta.ToolAgent._summarize_step_sequence = _thui_summ
_ta.ToolAgent._describe_last_outcome = _thui_desc
assert _sol._HarnessGameSession._execute_action is _thui_exec and _ta.ToolAgent._describe_last_outcome is _thui_desc
print(f"THUI_L1_GRAFT ok frac={_THUI_HUD_FRAC} min={_THUI_HUD_MIN} max_rows={_THUI_HUD_MAX_ROWS} solver={Path(_sol.__file__)}", flush=True)
'''

CELL9_CTL = '''
import inference.framework.solver as _sol
import inference.agent.tool_agent as _ta
assert _sol._HarnessGameSession._execute_action.__name__ == "_execute_action"
assert _ta.ToolAgent._describe_last_outcome.__name__ == "_describe_last_outcome"
print("THUI_L1_GRAFT control (no wrappers installed)", flush=True)
'''

CELL15_MOUNT_OLD = 'competition_env_files = str(Path("' + WHEELS_NESTED + '").parent / "environment_files")'
CELL15_MOUNT_NEW = 'competition_env_files = str(Path(_COMP_DIR) / "environment_files")   # thui-l1: resolved in cell 5'
CELL15_EXTRA_OLD = '    if missing or extra:\n'
CELL15_EXTRA_NEW = '    if missing or (extra and len(PUBLIC_GAME_IDS) == 25):   # thui-l1 smoke: a subset leaves extras by design\n'
CELL15_SELECT_OLD = '    bm.games = [offline_by_id[game_id] for game_id in PUBLIC_GAME_IDS]\n'
CELL15_SELECT_SMOKE = (CELL15_SELECT_OLD +
                       f'    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-l1 smoke clock\n'
                       f'    print(f"thui-l1: smoke {{len(bm.games)}} games @ {{bm.solver.max_runtime_s_per_game}} s", flush=True)\n')


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
    rep(3, fast.CELL3_OLD, fast.CELL3_NEW.replace("thui-fast", "thui-l1"))
    rep(5, CELL5_ANCHOR, "        _WHEELS,\n")
    cells[5]["source"] = (CELL5_RESOLVER + "".join(cells[5]["source"])).splitlines(keepends=True)
    cells[9]["source"] = ("".join(cells[9]["source"]) + CELL9_COMMON + (CELL9_CTL if CONTROL else CELL9_WRAP)).splitlines(keepends=True)
    rep(15, CELL15_MOUNT_OLD, CELL15_MOUNT_NEW)
    if not FULL:
        s = "".join(cells[15]["source"])
        m = re.search(r"PUBLIC_GAME_IDS = tuple\(\[\n(?:    \"[a-z0-9]{4}-[0-9a-f]{8}\",?\n){25}\]\)\n", s)
        assert m, "cell 15: the 25-game PUBLIC_GAME_IDS tuple not found"
        for g in SMOKE_GAMES:
            assert f'"{g}"' in m.group(0), f"{g} is not one of the 25 public ids"
        s = s.replace(m.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-l1 smoke subset\n")
        assert s.count("!= 25") == 2, s.count("!= 25")
        s = s.replace("!= 25", "!= len(PUBLIC_GAME_IDS)")
        assert s.count(CELL15_EXTRA_OLD) == 1 and s.count(CELL15_SELECT_OLD) == 1
        s = s.replace(CELL15_EXTRA_OLD, CELL15_EXTRA_NEW).replace(CELL15_SELECT_OLD, CELL15_SELECT_SMOKE)
        cells[15]["source"] = s.splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert changed == [0, 1, 3, 5, 9, 15], f"cells changed {changed}"
    assert "attachments" not in cells[1] and "tufa_labs.png" not in json.dumps(nb)
    for i, c in enumerate(cells):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]), filename=f"cell{i}")
    assert after[0].startswith(f"# {SLUG} (Thuitanium / Knowless Crew)")
    assert after[0].index("Thuitanium") < min(after[0].index("Tufa Labs"), after[0].index("Keith Tyser"))
    for bad in ("Tufa Labs ARC3 submission", "our milestone-winning", "attachment:"):
        assert bad not in after[1]
    assert after[9].count("THUI_L1_GRAFT") == 1 and after[9].count("band learner teeth ok") == 1
    assert ("_thui_exec" in after[9]) == (not CONTROL)
    assert after[7] == before[7] and after[11] == before[11]
    assert WHEELS_NESTED not in after[5] and WHEELS_NESTED not in after[15]
    assert ("smoke" in after[15]) == (not FULL)

    # the band learner runs here too: the same source the kernel executes, on the same teeth
    ns = {"sys": sys}
    exec(CELL9_COMMON.replace('assert "inference" not in sys.modules, "solver imported before the L1 graft"\n', ""), ns)

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(SRC_META.read_text(encoding="utf-8")); meta.pop("id_no", None)
    assert meta["model_sources"] == ["keithtyser/qwen3-8-flash-next-nvfp4/PyTorch/radixark-modelopt-fp4/1"]
    assert meta["machine_shape"] == "NvidiaRtxPro6000" and meta["enable_gpu"] is True
    meta["id"] = f"{OWNER}/{SLUG}"; meta["title"] = SLUG; meta["code_file"] = OUT_NB.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}, smoke={not FULL}, control={CONTROL}")


if __name__ == "__main__":
    main()
