"""thui-bo -- the fast base with a STUCK-GAME BACKOFF grafted into the harness (2026-09-15, from the 7-row Flash census).

Why. All 25 games run concurrently (solver concurrency 28) against ONE vLLM server that admits ~5 sequences at the
shipped 5 GiB KV (bench 2026-09-14: `Running: 5, Waiting: 20` in every arm, per-request median 114-137 s at c25 vs
41 s at c8). So every request from a game that is stuck occupies the same slot a game with momentum needs, and the
run is wall-bound end to end (7/7 Flash rows: 25/25 games `gave_up` at budget_s 7920; timeouts are the clock running
out mid-request, read timeout = remaining budget). Measured on b78-mtp0-full25-r1: bp35 / sp80 / wa30 / ka59 spent
1,075 actions (27% of the run) for 3 levels, 3.4x the run's mean cost per level, while tu93 reached level 5 and had
5 actions left; animfast-b71 shows the same shape at half the action count. Nothing in the harness throttles a game
that has stopped progressing.

What the graft does (cell 9, applied to the IMPORTED module after his serving setup; solver tree on disk untouched):
  ONE wrapper on `ToolAgent.analyze` (one ToolAgent per game, solver.py:1189). It reads the current level from the
  runtime-state file the solver writes right before each analyze (`current_frame.level`, runtime_state.py:88) and
  counts actions since the level last changed. Below THUI_BO_STALE (60) actions it does nothing. At >= 60 it sleeps
  THUI_BO_SLEEP (20 s) x (stale // 60), capped at THUI_BO_MAX_SLEEP (90 s), BEFORE delegating -- releasing the server
  to other games -- and prints `THUI_BO_BACKOFF level=<n> stale=<k> sleep=<s>`. The sleep polls `should_stop` every
  second, so a game whose clock ends mid-nap stops exactly as it would without the graft. The level counter resets on
  a level change only; an in-level death + auto-RESET keeps counting (it is the same level, still stuck). Nothing about
  the model, prompt, actions or knowledge is touched. --control: identical notebook, no wrapper (marker
  THUI_BO_GRAFT control).

Why 60 / 20 / 90: the Flash family's cleared levels cost a median 0.80 x human with human median 32, so 60 actions on
one level is ~2x a normal clear; stalled levels sit at human median 59. A game at 60-119 stale actions goes from ~50 s
to ~70 s per action (throttled 1.4x), at 120-179 to ~90 s, from 270 on to ~140 s -- it never stops, so a late unstick
still counts, and the freed requests are what the other games get. All three are env-overridable for a second arm.

Pre-registered read. THIS LEVER CANNOT BE READ ON A SMOKE: with 3 games there is no queue, so a nap frees nothing. The
smoke (bp35 / sp80 / wa30 at 1,800 s -- the three sinks) proves only (1) THUI_BO_GRAFT ok and >= 1 THUI_BO_BACKOFF in
the treatment log (zero = no game reached 60 actions on one level inside the clock -> VOID), (2) no crash, gave_up
states identical to control, (3) levels >= control on all three (a nap must not lose a level a control clears).
The instrument is a full-25 A/B vs --control, same day: primary = total levels (rank_runs.py, repo rule) and the
action count on the four sink games; secondary = levels on games that were BEHIND the family frontier in the census
(they are the ones a freed slot can move). MDE ~4 public points per single draw (R57/A4); expect the effect in
LEVELS on non-sink games, not in the score of the sinks.

Build:  PYTHONUTF8=1 python thui-bo/build_notebook.py             -> taaf-thui-bo-v0.ipynb  (smoke, treatment)
        PYTHONUTF8=1 python thui-bo/build_notebook.py --control   -> taaf-thui-bo-ctl.ipynb (smoke, no wrapper)
        PYTHONUTF8=1 python thui-bo/build_notebook.py --full           -> taaf-thui-bo-v0-full25-r1.ipynb
        PYTHONUTF8=1 python thui-bo/build_notebook.py --full --control -> taaf-thui-bo-ctl-full25-r1.ipynb
Teeth:  python thui-bo/test_bo_graft.py   (0 GPU: executes the notebook's own cell-9 source against a stub)
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
SLUG = (("thui-bo-ctl-full25-r1" if CONTROL else "thui-bo-v0-full25-r1") if FULL
        else ("thui-bo-ctl" if CONTROL else "thui-bo-v0"))
OUT_NB = HERE / f"taaf-{SLUG}.ipynb"
SMOKE_GAMES = ("bp35-0a0ad940", "sp80-589a99af", "wa30-ee6fef47")   # the three action sinks on b78 (244 / 288 / 296 actions, <=1 level)
SMOKE_CLOCK_S = 1800

sys.path.insert(0, str(FAST))
import build_notebook as fast  # noqa: E402
_spec = importlib.util.spec_from_file_location("thui_l1_builder", L1)
l1 = importlib.util.module_from_spec(_spec)
_argv, sys.argv = sys.argv, sys.argv[:1]   # the L1 builder reads its own flags at import; we only want its constants
_spec.loader.exec_module(l1)
sys.argv = _argv

CELL0_MD = f"""# {SLUG} (Thuitanium / Knowless Crew) — the fast base with a stuck-game backoff

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
- **cell 9** — {"CONTROL arm: the harness module is imported and asserted untouched (no wrapper)." if CONTROL else "one wrapper on the imported harness: `ToolAgent.analyze` sleeps before delegating once a game has spent 60+ actions on one level (20 s per 60, cap 90 s, polling should_stop), so the shared vLLM server's ~5 admission slots go to games still progressing. Model, prompt, actions and knowledge untouched."}
{"- **cell 15** — smoke: " + ", ".join(SMOKE_GAMES) + f" at {SMOKE_CLOCK_S} s each (mechanism + no-regression only; the lever needs the full 25 to read)." if not FULL else "- **cell 15** — all 25 public games, upstream clock (full-25 A/B draw r1)."}

Build script: `thui-bo/build_notebook.py` in our agent repo (asserts exactly those cells changed). Lever from the 7-row Flash census (2026-09-15).
"""

CELL9_COMMON = '''
# ---- thui-bo: stuck-game backoff. The policy is a pure function first, so the teeth drive it in-kernel.
assert "inference" not in sys.modules, "solver imported before the BO graft"
import json as _bo_json, os as _bo_os, time as _bo_time
_BO_STALE = int(_bo_os.environ.get("THUI_BO_STALE", "60"))
_BO_SLEEP = float(_bo_os.environ.get("THUI_BO_SLEEP", "20"))
_BO_MAX = float(_bo_os.environ.get("THUI_BO_MAX_SLEEP", "90"))

def _thui_bo_sleep_for(stale, stale_n=None, step=None, cap=None):
    """Seconds to yield before this analyze: 0 below the staleness threshold, then step x multiples, capped."""
    stale_n = _BO_STALE if stale_n is None else stale_n
    step = _BO_SLEEP if step is None else step
    cap = _BO_MAX if cap is None else cap
    if stale < stale_n:
        return 0.0
    return float(min(cap, step * (stale // stale_n)))

def _thui_bo_level(state_path):
    try:
        return int(_bo_json.loads(Path(state_path).read_text(encoding="utf-8"))["current_frame"]["level"])
    except Exception:
        return None

assert _thui_bo_sleep_for(0) == 0.0 and _thui_bo_sleep_for(59) == 0.0
assert _thui_bo_sleep_for(60) == 20.0 and _thui_bo_sleep_for(119) == 20.0 and _thui_bo_sleep_for(120) == 40.0
assert _thui_bo_sleep_for(300) == 90.0 and _thui_bo_sleep_for(10_000) == 90.0
assert _thui_bo_sleep_for(10, stale_n=5, step=1, cap=1.5) == 1.5
print("thui-bo: policy teeth ok", flush=True)
'''

CELL9_WRAP = '''
import inference.agent.tool_agent as _ta
_orig_bo_analyze = _ta.ToolAgent.analyze

def _thui_bo_analyze(self, state_path, action_num, *args, **kwargs):
    try:
        level = _thui_bo_level(state_path)
        st = getattr(self, "_thui_bo_state", None)
        if st is None or st["level"] != level:
            st = {"level": level, "since": int(action_num)}
            self._thui_bo_state = st
        stale = int(action_num) - st["since"]
        nap = _thui_bo_sleep_for(stale)
        if nap > 0:
            should_stop = kwargs.get("should_stop")
            print(f"THUI_BO_BACKOFF level={level} stale={stale} sleep={nap:.0f}", flush=True)
            end = _bo_time.monotonic() + nap
            while _bo_time.monotonic() < end:
                if should_stop is not None and should_stop():
                    break
                _bo_time.sleep(1.0)
    except Exception as exc:  # never let the graft kill a step
        print(f"thui-bo: wrapper error {exc!r}", flush=True)
    return _orig_bo_analyze(self, state_path, action_num, *args, **kwargs)

_ta.ToolAgent.analyze = _thui_bo_analyze
assert _ta.ToolAgent.analyze is _thui_bo_analyze
print(f"THUI_BO_GRAFT ok agent={Path(_ta.__file__)} stale={_BO_STALE} sleep={_BO_SLEEP} cap={_BO_MAX}", flush=True)
'''

CELL9_CTL = '''
import inference.agent.tool_agent as _ta
assert _ta.ToolAgent.analyze.__name__ == "analyze"
print("THUI_BO_GRAFT control (no wrapper installed)", flush=True)
'''

CELL15_SELECT_SMOKE = (l1.CELL15_SELECT_OLD +
                       f'    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-bo smoke clock\n'
                       f'    print(f"thui-bo: smoke {{len(bm.games)}} games @ {{bm.solver.max_runtime_s_per_game}} s", flush=True)\n')


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
    rep(3, fast.CELL3_OLD, fast.CELL3_NEW.replace("thui-fast", "thui-bo"))
    rep(5, l1.CELL5_ANCHOR, "        _WHEELS,\n")
    cells[5]["source"] = (l1.CELL5_RESOLVER.replace("thui-l1", "thui-bo") + "".join(cells[5]["source"])).splitlines(keepends=True)
    cells[9]["source"] = ("".join(cells[9]["source"]) + CELL9_COMMON + (CELL9_CTL if CONTROL else CELL9_WRAP)).splitlines(keepends=True)
    rep(15, l1.CELL15_MOUNT_OLD, l1.CELL15_MOUNT_NEW.replace("thui-l1", "thui-bo"))
    if not FULL:
        s = "".join(cells[15]["source"])
        m = re.search(r"PUBLIC_GAME_IDS = tuple\(\[\n(?:    \"[a-z0-9]{4}-[0-9a-f]{8}\",?\n){25}\]\)\n", s)
        assert m, "cell 15: the 25-game PUBLIC_GAME_IDS tuple not found"
        for g in SMOKE_GAMES:
            assert f'"{g}"' in m.group(0), f"{g} is not one of the 25 public ids"
        s = s.replace(m.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-bo smoke subset\n")
        assert s.count("!= 25") == 2, s.count("!= 25")
        s = s.replace("!= 25", "!= len(PUBLIC_GAME_IDS)")
        assert s.count(l1.CELL15_EXTRA_OLD) == 1 and s.count(l1.CELL15_SELECT_OLD) == 1
        s = s.replace(l1.CELL15_EXTRA_OLD, l1.CELL15_EXTRA_NEW.replace("thui-l1", "thui-bo")).replace(l1.CELL15_SELECT_OLD, CELL15_SELECT_SMOKE)
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
    assert after[9].count("THUI_BO_GRAFT") == 1 and after[9].count("policy teeth ok") == 1
    assert ("_thui_bo_analyze" in after[9]) == (not CONTROL)
    assert "THUI_L1" not in after[9] and "THUI_WM" not in after[9] and "thui-l1" not in after[5] and "thui-l1" not in after[15]
    assert after[7] == before[7] and after[11] == before[11] and after[13] == before[13]
    assert l1.WHEELS_NESTED not in after[5] and l1.WHEELS_NESTED not in after[15]
    assert ("smoke" in after[15]) == (not FULL)

    # the policy runs here too: the same source the kernel executes, on the same teeth
    exec(CELL9_COMMON.replace('assert "inference" not in sys.modules, "solver imported before the BO graft"\n', ""), {"sys": sys, "Path": Path})

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(SRC_META.read_text(encoding="utf-8")); meta.pop("id_no", None)
    assert meta["model_sources"] == ["keithtyser/qwen3-8-flash-next-nvfp4/PyTorch/radixark-modelopt-fp4/1"]
    assert meta["machine_shape"] == "NvidiaRtxPro6000" and meta["enable_gpu"] is True
    meta["id"] = f"{OWNER}/{SLUG}"; meta["title"] = SLUG; meta["code_file"] = OUT_NB.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}, smoke={not FULL}, control={CONTROL}")


if __name__ == "__main__":
    main()
