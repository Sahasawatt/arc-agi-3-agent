"""Teeth for the thui-dg death guard (0 GPU). Executes the built notebook's cell-9 graft source against the anim bundle's REAL
noop_guard.py (scratchpad/anim-bundle, the dataset the kernel mounts) and a stub ToolAgent, then drives the exact call sequence the
real tool_agent.py performs (compact -> observe -> is_known_noop).

    python thui-dg/test_dg_graft.py

Seam checks on the REAL tool_agent.py of the bundle: `_compact_action_result` defined once and called before `.observe(` in both
action paths; `NoopGuard()` constructed at 2 sites by module name; `_HARD_NOOP_GUARD_ENABLED` defaults True.
Cases: death recorded + blocked in the exact state; other state not blocked; death not filed as a no-op; base no-op behaviour intact;
pending consumed once; MOUSE sig normalisation; control notebook has no wrapper.
"""
import importlib.util
import io
import json
import sys
import types
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parent.parent / "anim-bundle" / "src" / "ARC3-Inference" / "inference"
NB = HERE / "taaf-thui-dg-v0.ipynb"
NB_CTL = HERE / "taaf-thui-dg-ctl.ipynb"


def cell9_tail(path):
    cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
    s = "".join(cells[9]["source"])
    return s[s.index("import inference.agent.tool_agent as _ta"):]


def make_stub_modules():
    spec = importlib.util.spec_from_file_location("inference.agent.noop_guard", BUNDLE / "agent" / "noop_guard.py")
    ng = importlib.util.module_from_spec(spec); spec.loader.exec_module(ng)
    inference = types.ModuleType("inference"); agent = types.ModuleType("inference.agent")
    ta = types.ModuleType("inference.agent.tool_agent")
    ta.NoopGuard = ng.NoopGuard
    ta._HARD_NOOP_GUARD_ENABLED = True

    class ToolAgent:
        def __init__(self):
            self._noop_guard = ta.NoopGuard()   # resolved by NAME at call time, like the real init / _ensure_session

        def _compact_action_result(self, payload):
            return {"executed": bool(payload.get("executed")), "game_over": bool(payload.get("game_over")),
                    "board_changed": bool(payload.get("board_changed")), "action_display": payload.get("action_display")}
    ta.ToolAgent = ToolAgent
    for name, mod in (("inference", inference), ("inference.agent", agent), ("inference.agent.tool_agent", ta), ("inference.agent.noop_guard", ng)):
        sys.modules[name] = mod
    return ta, ng


def main():
    fails = []
    src = (BUNDLE / "agent" / "tool_agent.py").read_text(encoding="utf-8")
    # seams on the real bundle
    if src.count("def _compact_action_result(self, payload") != 1: fails.append("seam: _compact_action_result def count")
    if src.count("NoopGuard() if self._hard_noop_guard_enabled else None") != 2: fails.append("seam: NoopGuard() construction sites")
    if src.count(".is_known_noop(") != 2 or src.count("self._noop_guard.observe(") != 2: fails.append("seam: guard call sites")
    if 'ARC3_HARD_NOOP_GUARD", True' not in src: fails.append("seam: hard guard default")
    single = src[src.index("if len(normalized_actions) == 1:"):src.index("# Batch of >1 actions")]
    batch = src[src.index("# Batch of >1 actions"):]
    for name, seg in (("single", single), ("batch", batch)):
        if not (seg.index("_compact_action_result(raw_payload)") < seg.index("self._noop_guard.observe(")):
            fails.append(f"seam order ({name}): compact must precede observe")

    ta, ng = make_stub_modules()
    graft = cell9_tail(NB)
    out = io.StringIO()
    with redirect_stdout(out):
        exec(graft, {"_tool_agent": ta})
    if "THUI_DG_GRAFT ok" not in out.getvalue(): fails.append("graft did not print ok")
    if ta.NoopGuard.__name__ != "_ThuiDeathGuard": fails.append("NoopGuard not rebound")

    ag = ta.ToolAgent()
    g = ag._noop_guard
    if type(g).__name__ != "_ThuiDeathGuard": fails.append("agent guard is not the death guard (construction by name failed)")
    click = "MOUSE(row=33, col=21)"

    def death(sig, state, level=2, changed=True):
        ag._compact_action_result({"executed": True, "game_over": True, "board_changed": changed, "action_display": sig})
        g.observe(level=level, board_before_sig=state, action_sig=sig, board_changed=changed)

    try:
      with redirect_stdout(io.StringIO()):
          # 1. death recorded and blocked in the exact state
          death(click, "S")
          if not g.is_known_noop(2, "S", click): fails.append("case1: fatal not blocked")
          if g.records != 1 or g.blocks != 1: fails.append(f"case1: counters {g.records}/{g.blocks}")
          # 2. other state / other level / other action not blocked
          if g.is_known_noop(2, "T", click): fails.append("case2: blocked in a different state")
          if g.is_known_noop(3, "S", click): fails.append("case2: blocked on a different level")
          if g.is_known_noop(2, "S", "UP"): fails.append("case2: blocked a different action")
          # 3. death not filed as a no-op in the base table
          if ng.NoopGuard.is_known_noop(g, 2, "S", click): fails.append("case3: death filed as no-op")
          # 4. base behaviour intact: executed no-op is recorded and blocked; a changing action is not
          ag._compact_action_result({"executed": True, "game_over": False, "board_changed": False, "action_display": "DOWN"})
          g.observe(level=2, board_before_sig="S", action_sig="DOWN", board_changed=False)
          if not g.is_known_noop(2, "S", "DOWN"): fails.append("case4: base no-op not blocked")
          ag._compact_action_result({"executed": True, "game_over": False, "board_changed": True, "action_display": "LEFT"})
          g.observe(level=2, board_before_sig="S", action_sig="LEFT", board_changed=True)
          if g.is_known_noop(2, "S", "LEFT"): fails.append("case4: changing action blocked")
          # 5. pending consumed once and only by the matching action
          ag._compact_action_result({"executed": True, "game_over": True, "board_changed": True, "action_display": "RIGHT"})
          g.observe(level=2, board_before_sig="U", action_sig="UP", board_changed=True)     # mismatch: dropped, not filed
          if (2, "U", "UP") in g.fatal or (2, "U", "RIGHT") in g.fatal: fails.append("case5: mismatched pending filed")
          if g.pending_game_over is not None: fails.append("case5: pending not consumed")
          g.observe(level=2, board_before_sig="V", action_sig="RIGHT", board_changed=True)
          if (2, "V", "RIGHT") in g.fatal: fails.append("case5: stale pending filed later")
          # 6. non-executed / non-death payloads never set pending
          ag._compact_action_result({"executed": False, "game_over": True, "action_display": "SPACE"})
          if g.pending_game_over is not None: fails.append("case6: non-executed payload set pending")
          # 7. signature normalisation (whitespace) matches the bundle's own
          death("MOUSE(row=5,  col=7)", "W")
          if not g.is_known_noop(2, "W", "MOUSE(row=5, col=7)"): fails.append("case7: sig normalisation")
          # 8. base eviction bound untouched: fatal dict is separate from _levels
          if g._levels.get(2, {}).get("S", {}).get(click) is not None: fails.append("case8: fatal leaked into _levels")
          # 9. a second death on the same key counts up, still blocks
          death(click, "S")
          if g.fatal[(2, "S", click)] != 2: fails.append("case9: repeat death count")
    except Exception as exc:   # a crashed case is a red case, never a skipped one
        fails.append(f"case crashed: {type(exc).__name__}: {exc}")

    # 10. control notebook: no wrapper
    if NB_CTL.exists():
        ctl = cell9_tail(NB_CTL)
        if "_ThuiDeathGuard" in ctl or "THUI_DG_GRAFT control" not in ctl: fails.append("case10: control has a wrapper")
        ta2, _ = make_stub_modules()
        with redirect_stdout(io.StringIO()):
            exec(ctl, {"_tool_agent": ta2})
        if ta2.NoopGuard.__name__ != "NoopGuard": fails.append("case10: control rebound NoopGuard")
    else:
        fails.append("control notebook not built")

    for f in fails:
        print("FAIL", f)
    print("ALL TEETH PASS" if not fails else f"{len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
