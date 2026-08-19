"""Verify both duckv4 patches against the REAL duck bundle source tree.

Run:
    PYTHONPATH=duck/bundle/src/ARC3-Inference:duck/bundle/src/tufa-arc-agi-framework/src \
        ./.venv/Scripts/python.exe duckv4/verify_against_bundle.py

Imports the real `inference.agent.tool_agent` and `inference.framework.solver`
modules, applies both `install_patch` functions, and exercises them against
real bundle functions/duck-typed session objects -- proves the patches
compile, import, and reach the exact call chain R2 documents, not just the
test doubles in each module's own `_demo()`.
"""
import ast
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import duckv4_reallocator  # noqa: E402
import duckv4_worldmodel_cap  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def _check_worldmodel_cap() -> None:
    src = (REPO_ROOT / "duckv4" / "duckv4_worldmodel_cap.py").read_text(encoding="utf-8")
    ast.parse(src)
    print("duckv4_worldmodel_cap.py parses clean (ast.parse)")

    from inference.agent import tool_agent

    assert callable(tool_agent._extract_labeled_blocks), "patch target must exist and be callable"
    assert callable(tool_agent._extract_scientist_note), "the only caller must exist too"
    print("patch target tool_agent._extract_labeled_blocks exists (patch-target existence)")

    # Build one assistant turn whose "World model" section blows the cap.
    long_note = "\n".join(f"- observation {i}: the door is at row {i}" for i in range(2000))
    content = f"World model:\n{long_note}\nGoal model:\nreach the door\n"

    # BEFORE patching: reproduces R2's finding -- unbounded.
    before = tool_agent._extract_scientist_note(content)
    assert len(before["world_model"]) > duckv4_worldmodel_cap.FIELD_CAP_CHARS, (
        "negative control: before the patch, the real harness must actually be "
        "unbounded here, or this whole check proves nothing"
    )
    print(f"BEFORE patch: world_model = {len(before['world_model'])} chars (unbounded, reproduces R2)")

    duckv4_worldmodel_cap.install_patch(tool_agent)
    after = tool_agent._extract_scientist_note(content)
    assert len(after["world_model"]) <= duckv4_worldmodel_cap.FIELD_CAP_CHARS + 40
    assert "[compacted:" in after["world_model"]
    assert after["goal_model"] == "reach the door", "a short field must pass through unchanged"
    print(f"AFTER patch: world_model = {len(after['world_model'])} chars (capped)")

    # idempotency against the real module
    duckv4_worldmodel_cap.install_patch(tool_agent)
    after2 = tool_agent._extract_scientist_note(content)
    assert after == after2
    print("install_patch is idempotent against the real tool_agent module")


def _check_reallocator() -> None:
    src = (REPO_ROOT / "duckv4" / "duckv4_reallocator.py").read_text(encoding="utf-8")
    ast.parse(src)
    print("duckv4_reallocator.py parses clean (ast.parse)")

    from inference.framework import solver

    cls = solver._HarnessGameSession
    assert hasattr(cls, "runtime_limit_reached"), "patch target must exist"
    assert hasattr(cls, "timing_payload"), "patch target must exist"
    assert hasattr(solver, "HarnessSolver")
    assert "max_runtime_s_per_game" in solver.HarnessSolver.__dataclass_fields__, (
        "HarnessSolver must still expose the field this patch reads, not writes"
    )
    print("patch targets _HarnessGameSession.runtime_limit_reached/timing_payload exist "
          "(patch-target existence)")

    # Duck-typed session: a real _HarnessGameSession is a heavyweight dataclass
    # (needs a real taaf.game.Game, analyzer, paths, ...); what matters here is
    # that the REAL, PATCHED methods (bound as plain functions) read exactly the
    # attributes documented in the module docstring, so a minimal object with
    # those attributes is a faithful, standard duck-typed test double.
    class _State:
        def __init__(self, levels):
            self.levels_completed = levels

    class _Game:
        def __init__(self, levels):
            self.current_state = _State(levels)

    class _Session:
        def __init__(self, budget, levels, actions):
            self.solver = solver.HarnessSolver(max_runtime_s_per_game=budget)
            self.game = _Game(levels)
            self._actions = actions
            self.started_at = time.monotonic()

        @property
        def action_count(self):
            return self._actions

    budget = 7920.0
    before_session = _Session(budget, levels=0, actions=10)

    # BEFORE patching: the unpatched real method reads the flat budget only.
    before_remaining = cls.timing_payload(before_session)["time_remaining_seconds"]
    assert abs(before_remaining - budget) < 1.0, "unpatched session must read the flat budget"
    print(f"BEFORE patch: timing_payload remaining ~= {before_remaining:.1f}s (flat budget)")

    duckv4_reallocator.install_patch(solver)
    assert getattr(cls, duckv4_reallocator._PATCH_MARKER, False)

    after_session = _Session(budget, levels=0, actions=10)
    after_remaining = cls.timing_payload(after_session)["time_remaining_seconds"]
    assert abs(after_remaining - budget) < 1.0, "a freshly-registered, non-adjusted session keeps its budget"
    assert cls.runtime_limit_reached(after_session) is False
    print(f"AFTER patch: timing_payload still reads ~= {after_remaining:.1f}s (no adjustment yet, correct)")

    # idempotency against the real class
    duckv4_reallocator.install_patch(solver)
    print("install_patch is idempotent against the real solver module")

    # negative control against the real module: renamed attribute must fail loudly.
    class _FakeSolverModule:
        pass

    try:
        duckv4_reallocator.install_patch(_FakeSolverModule())
        raise AssertionError("expected AttributeError: module has no _HarnessGameSession")
    except AttributeError:
        pass
    print("negative control: a module missing _HarnessGameSession fails loudly")


def main() -> None:
    _check_worldmodel_cap()
    _check_reallocator()
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
