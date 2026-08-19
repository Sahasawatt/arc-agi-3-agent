"""Verify duckv3_observer's patch against the REAL duck bundle source tree.

Run:
    PYTHONPATH=duck/bundle/src/ARC3-Inference:duck/bundle/src/tufa-arc-agi-framework/src \
        python duckv3/verify_against_bundle.py

Imports the real `inference.agent.tool_agent` module, applies
`duckv3_observer.install_patch`, and calls the patched
`ToolAgent._build_user_prompt` with real `Frame`/`HistoryEntry` objects from
`inference.agent.runtime_state` -- proves the patch compiles, imports, and
composes cleanly against the actual bundle types, not just the test doubles
in `duckv3_observer._demo()`. No network, no model call, no sandbox
subprocess -- `_build_user_prompt` is a pure function of its arguments.
"""
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import duckv3_observer  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    src = (REPO_ROOT / "duckv3" / "duckv3_observer.py").read_text(encoding="utf-8")
    ast.parse(src)
    print("duckv3_observer.py parses clean (ast.parse)")

    from inference.agent import tool_agent
    from inference.agent.runtime_state import Frame, HistoryEntry

    assert not getattr(tool_agent.ToolAgent, "_duckv3_patched", False)
    duckv3_observer.install_patch(tool_agent)
    assert getattr(tool_agent.ToolAgent, "_duckv3_patched", False)
    print("install_patch applied to the real tool_agent.ToolAgent")

    # idempotency: re-applying must not double-wrap.
    duckv3_observer.install_patch(tool_agent)
    print("install_patch is idempotent (second call no-ops)")

    # Build a tiny real ToolAgent instance without touching the network --
    # __init__ only sets fields, no HTTP call happens until analyze()/chat.
    agent = tool_agent.ToolAgent(model="dummy-model", timeout=30.0)

    def grid(clock, mid):
        return ((clock, 0, 0), (0, mid, 0), (0, 0, 0))

    history = [
        HistoryEntry(action="", frame=Frame(grid=grid(9, 1), step=0, level=1)),
        HistoryEntry(action="ACTION1", frame=Frame(grid=grid(0, 1), step=1, level=1)),
        HistoryEntry(action="ACTION2", frame=Frame(grid=grid(9, 1), step=2, level=1)),
        HistoryEntry(action="ACTION3", frame=Frame(grid=grid(0, 2), step=3, level=1)),
    ]
    current = history[-1].frame
    prompt = agent._build_user_prompt(
        0,
        valid_actions=["ACTION1", "ACTION2", "ACTION3", "ACTION4"],
        current_frame=current,
        history_entries=history,
        previous_step_summary=None,
    )
    assert "HUD cells (auto-masked):" in prompt, prompt
    assert "state:" in prompt, prompt
    assert "untried here:" in prompt, prompt
    assert "last action:" in prompt, prompt
    print("patched _build_user_prompt on a real ToolAgent instance:")
    print("--- tail of user prompt ---")
    print(prompt[prompt.index("HUD cells"):])
    print("--- end ---")

    # per-instance isolation: a second ToolAgent must start with its own
    # fresh GameObservation, not share state with the first (the concurrent-
    # games requirement).
    agent2 = tool_agent.ToolAgent(model="dummy-model", timeout=30.0)
    assert not hasattr(agent2, "_duckv3_observation")
    prompt2 = agent2._build_user_prompt(
        0,
        valid_actions=["ACTION1"],
        current_frame=current,
        history_entries=history[:1],
        previous_step_summary=None,
    )
    assert "state: NOVEL" in prompt2, prompt2
    assert agent._duckv3_observation is not agent2._duckv3_observation
    print("two ToolAgent instances hold independent GameObservation state (no cross-game leak)")

    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
