"""thui-dg -- hard DEATH guard on the anim harness: the search-strategy lever, built as a REFUSAL instead of a prompt line.

Why (2026-09-15). Four smokes (wm, db v0, db v1, m0) taught one rule: in-prompt facts about deaths and budgets do not move this
model's policy -- told "MOUSE(row=33, col=21) ended the game, do not repeat", it clicked it twice more (thui-db v1). The anim bundle
already contains the one mechanism on this harness that DID change behaviour: `inference/agent/noop_guard.py` ("Experiment 1 only
*mentioned* known no-ops ... ~12% no-op repeats remained. This module instead lets the harness actively block re-executing an action
already proven to have no effect in the exact same board state, before it ever reaches the environment."). This graft applies the
same pattern to deaths: a (level, board_before, action) combo that ended the game is BLOCKED before execution the next time the model
asks for it from that exact board. The model's plan continues with its next action; no prompt text is added.

What it cannot do, stated: budget deaths (tn36 61 actions/life, sp80 30/45 actions, sp80 L2 5 SPACE) are not (state, action)
combos -- the N-th action kills whatever it is -- so the guard does not touch them. It targets repeat-fatal: ctl smoke 12 repeats
(bp35 L2 MOUSE(33,21) x3, sp80 L1 SPACE x3 / DOWN x2 ...), and the census read of 27 % of all deaths as exact repeats.

Graft (cell 9, after the anim import, before any game): `_ThuiDeathGuard(NoopGuard)` -- observe() files a death into `fatal` instead
of the no-op table; is_known_noop() answers True for a known-fatal key, so the agent's existing block path fires (marker THUI_DG_BLOCK).
The death signal reaches the guard through one wrapper on `ToolAgent._compact_action_result` (called on every executed payload
immediately before observe() in both the single and the batch path): an executed payload with game_over sets `pending_game_over` =
its action_display; observe() consumes it once and only when the action matches. `tool_agent.NoopGuard` is rebound to the subclass
so both construction sites (init and _ensure_session) build it. --control: identical notebook, no wrapper (THUI_DG_GRAFT control).

Pre-registered read (smoke bp35 / sp80 / tn36 at 1,800 s, v0 vs --control, same hour; oracle thui-db/repeat_fatal_read.py):
  1. Mechanism: THUI_DG_GRAFT ok; >= 1 THUI_DG_RECORD AND >= 1 THUI_DG_BLOCK in v0. Zero BLOCK = no exact-state repeat was asked for
     inside 1,800 s -> VOID for the lever (the smoke measured nothing), not a FAIL.
  2. Repeat-fatal (oracle, non-budget) in v0 < control. It is what the guard removes by construction where the board matched; any
     remaining repeats are from a different board_before (the oracle keys on level+action only -- report both numbers).
  3. Levels >= control on all three (a 3-game draw can only read no-regression; control draws 1 vs 2 already differ 2-vs-0 on tn36,
     so read rule 3 against BOTH db controls, kout-sa-thui-db-ctl and -ctl-r2, before calling a FAIL).
  4. PASS buys a full-25 pair on the anim base (2.4 GPU-h per draw). Nothing here is a submission.

Build:  PYTHONUTF8=1 python thui-dg/build_notebook.py               -> taaf-thui-dg-v0.ipynb        (smoke, graft)
        PYTHONUTF8=1 python thui-dg/build_notebook.py --control     -> taaf-thui-dg-ctl.ipynb       (smoke, no wrapper)
        PYTHONUTF8=1 python thui-dg/build_notebook.py --full        -> taaf-thui-dg-v0-full25-r1.ipynb
        PYTHONUTF8=1 python thui-dg/build_notebook.py --full --control -> taaf-thui-dg-ctl-full25-r1.ipynb
Teeth:  python thui-dg/test_dg_graft.py   (0 GPU: executes the notebook's cell-9 graft against the bundle's REAL noop_guard.py)
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
SLUG = (("thui-dg-ctl-full25-r1" if CONTROL else "thui-dg-v0-full25-r1") if FULL else ("thui-dg-ctl" if CONTROL else "thui-dg-v0"))
OUT_NB = HERE / f"taaf-{SLUG}.ipynb"
ANIM_DS = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
B71_CELLS = (1, 3, 5, 7, 9, 11, 15)
SMOKE_GAMES = ("bp35-0a0ad940", "sp80-589a99af", "tn36-ef4dde99")   # the three death games of the frontier-5 diagnosis
SMOKE_CLOCK_S = 1800

_spec = importlib.util.spec_from_file_location("thui_l1_builder", L1)
l1 = importlib.util.module_from_spec(_spec)
_argv, sys.argv = sys.argv, sys.argv[:1]
_spec.loader.exec_module(l1)
sys.argv = _argv

CELL0_MD = f"""# {SLUG} (Thuitanium / Knowless Crew) -- hard death guard on the animation-awareness duck harness

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
- **cell 9 (tail)** -- {"CONTROL arm: no wrapper; the imported harness is asserted untouched." if CONTROL else "`_ThuiDeathGuard(NoopGuard)`: the bundle's hard no-op guard extended to remember `(level, board_before, action)` combos that reached GAME_OVER and block them before execution; the signal arrives via one wrapper on `ToolAgent._compact_action_result`. No prompt text is added."}
{"- **cell 15** -- smoke: " + ", ".join(SMOKE_GAMES) + f" at {SMOKE_CLOCK_S} s each." if not FULL else "- **cell 15** -- all 25 public games, upstream clock."}

Build script: `thui-dg/build_notebook.py` in our agent repo (asserts exactly those cells changed). 2026-09-15.
"""

CELL9_DG = '''
# ---- thui-dg: hard DEATH guard -- the bundle's Known-Noop-Guard pattern applied to game_over (block, do not tell).
from inference.agent.noop_guard import NoopGuard as _thui_dg_base, normalize_action_signature as _thui_dg_norm


class _ThuiDeathGuard(_thui_dg_base):
    """NoopGuard that also remembers (level, board_before_sig, action) combos that ended the game and blocks them."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fatal = {}
        self.pending_game_over = None   # action_display of the executed action that reported game_over; consumed by observe()
        self.records = 0
        self.blocks = 0

    def observe(self, *, level, board_before_sig, action_sig, board_changed, animated=False):
        pending, self.pending_game_over = self.pending_game_over, None
        sig = _thui_dg_norm(action_sig)
        if pending is not None and sig and _thui_dg_norm(pending) == sig:
            try:
                key = (int(level), str(board_before_sig), sig)
            except (TypeError, ValueError):
                return None
            self.fatal[key] = self.fatal.get(key, 0) + 1
            self.records += 1
            print(f"THUI_DG_RECORD level={key[0]} action={sig} n={self.fatal[key]} records={self.records}", flush=True)
            return None   # a death is not a no-op: never let the base guard file it as one
        return super().observe(level=level, board_before_sig=board_before_sig, action_sig=action_sig,
                               board_changed=board_changed, animated=animated)

    def is_known_noop(self, level, board_sig, action_sig):
        try:
            key = (int(level), str(board_sig), _thui_dg_norm(action_sig))
        except (TypeError, ValueError):
            key = None
        if key is not None and key in self.fatal:
            self.blocks += 1
            print(f"THUI_DG_BLOCK level={key[0]} action={key[2]} deaths={self.fatal[key]} blocks={self.blocks}", flush=True)
            return True
        return super().is_known_noop(level, board_sig, action_sig)


_thui_dg_orig_compact = _ta.ToolAgent._compact_action_result


def _thui_dg_compact(self, payload):
    out = _thui_dg_orig_compact(self, payload)
    try:
        guard = getattr(self, "_noop_guard", None)
        if (isinstance(guard, _ThuiDeathGuard) and isinstance(payload, dict)
                and payload.get("executed") and payload.get("game_over")):
            guard.pending_game_over = str(payload.get("action_display") or payload.get("action_name") or "")
    except Exception as exc:   # never let the graft kill a step
        print(f"thui-dg: compact wrapper error {exc!r}", flush=True)
    return out


_ta.ToolAgent._compact_action_result = _thui_dg_compact
_ta.NoopGuard = _ThuiDeathGuard
assert _ta.NoopGuard is _ThuiDeathGuard and _ta.ToolAgent._compact_action_result is _thui_dg_compact
assert _ta._HARD_NOOP_GUARD_ENABLED is True, "the bundle's hard no-op guard is off; the death guard rides on it"
print("THUI_DG_GRAFT ok", flush=True)
'''

CELL9_CTL = '''
# ---- thui-dg CONTROL: no wrapper; the harness is asserted untouched.
assert _ta.ToolAgent._compact_action_result.__name__ == "_compact_action_result" and _ta.NoopGuard.__name__ == "NoopGuard"
print("THUI_DG_GRAFT control (no wrapper installed)", flush=True)
'''

CELL15_SELECT_SMOKE = (l1.CELL15_SELECT_OLD +
                       f'    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-dg smoke clock\n'
                       f'    print(f"thui-dg: smoke {{len(bm.games)}} games @ {{bm.solver.max_runtime_s_per_game}} s", flush=True)\n')


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
        s = b[i].replace("thui-animfast", "thui-dg").replace("THUI_ANIMFAST_GRAFT", "THUI_ANIM_GRAFT")
        if i == 9:
            s += "\nimport inference.agent.tool_agent as _ta\nassert _ta is _tool_agent\n" + (CELL9_CTL if CONTROL else CELL9_DG)
        cells[i]["source"] = s.splitlines(keepends=True)
        cells[i].pop("attachments", None)
    if not FULL:
        s = "".join(cells[15]["source"])
        m = re.search(r"PUBLIC_GAME_IDS = tuple\(\[\n(?:    \"[a-z0-9]{4}-[0-9a-f]{8}\",?\n){25}\]\)\n", s)
        assert m, "cell 15: the 25-game PUBLIC_GAME_IDS tuple not found"
        for g in SMOKE_GAMES:
            assert f'"{g}"' in m.group(0), f"{g} is not one of the 25 public ids"
        s = s.replace(m.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-dg smoke subset\n")
        assert s.count("!= 25") == 2
        s = s.replace("!= 25", "!= len(PUBLIC_GAME_IDS)")
        assert s.count(l1.CELL15_EXTRA_OLD) == 1 and s.count(l1.CELL15_SELECT_OLD) == 1
        s = s.replace(l1.CELL15_EXTRA_OLD, l1.CELL15_EXTRA_NEW.replace("thui-l1", "thui-dg")).replace(l1.CELL15_SELECT_OLD, CELL15_SELECT_SMOKE)
        cells[15]["source"] = s.splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (x, y) in enumerate(zip(before, after)) if x != y]
    assert changed == [0, 1, 3, 5, 7, 9, 11, 15], f"cells changed {changed}"
    for i, c in enumerate(cells):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]), filename=f"cell{i}")
    assert "animfast" not in json.dumps(after[1:])
    assert after[9].count("THUI_DG_GRAFT") == 1 and ("_ThuiDeathGuard" in after[9]) == (not CONTROL)
    assert after[9].index("THUI_ANIM_GRAFT ok") < after[9].index("THUI_DG_GRAFT"), "death guard must be installed after the anim import"
    assert 'bm.label == "anim-20260807-anim"' in after[11] and "hard_noop_guard" in after[11]
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
