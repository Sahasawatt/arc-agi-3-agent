"""Verify both duckv5 patches against the REAL duck bundle source tree.

Run:
    PYTHONPATH=duck/bundle/src/ARC3-Inference:duck/bundle/src/tufa-arc-agi-framework/src \
        ./.venv/Scripts/python.exe duckv5/verify_against_bundle.py

Imports the real `inference.agent.tool_agent` module, applies both `install_patch`
functions, and exercises them against real `ToolAgent`/`Frame`/`HistoryEntry` objects --
proves the patches compile, import, and compose cleanly against the actual bundle types,
not just the test doubles in each module's own `_demo()`. No network, no model call, no
sandbox subprocess -- everything patched here is a pure function of its arguments.
"""
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import duckv5_digest  # noqa: E402
import duckv5_worldmodel_accum  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def _check_worldmodel_accum() -> None:
    src = (REPO_ROOT / "duckv5" / "duckv5_worldmodel_accum.py").read_text(encoding="utf-8")
    ast.parse(src)
    print("duckv5_worldmodel_accum.py parses clean (ast.parse)")

    from inference.agent import tool_agent

    assert hasattr(tool_agent.ToolAgent, "_update_summarized_knowledge_from_assistant"), (
        "patch target must exist"
    )
    assert callable(tool_agent._extract_scientist_note), "the extractor this patch calls must exist"
    print(
        "patch target ToolAgent._update_summarized_knowledge_from_assistant + "
        "_extract_scientist_note exist (patch-target existence)"
    )

    agent = tool_agent.ToolAgent(model="dummy-model", timeout=30.0)

    # BEFORE patching: reproduces R7 sec5 -- plain overwrite, no accumulation.
    agent._update_summarized_knowledge_from_assistant("World model:\nturn one finding")
    agent._update_summarized_knowledge_from_assistant("World model:\nturn two finding")
    before_wm = agent._summarized_knowledge["world_model"]
    assert "turn one finding" not in before_wm, (
        "negative control: before the patch the real harness must actually overwrite, "
        "or this whole check proves nothing"
    )
    assert before_wm == "turn two finding"
    print(f"BEFORE patch: world_model = {before_wm!r} (overwritten, reproduces R7 sec5)")

    duckv5_worldmodel_accum.install_patch(tool_agent)
    assert getattr(tool_agent.ToolAgent, duckv5_worldmodel_accum._PATCH_MARKER, False)

    agent2 = tool_agent.ToolAgent(model="dummy-model", timeout=30.0)
    agent2._update_summarized_knowledge_from_assistant("World model:\nturn one finding")
    agent2._update_summarized_knowledge_from_assistant("World model:\nturn two finding")
    after_wm = agent2._summarized_knowledge["world_model"]
    assert "turn one finding" in after_wm, "AFTER patch: earlier turns must survive (accumulation)"
    assert "turn two finding" in after_wm
    print(f"AFTER patch: world_model accumulates both turns ({len(after_wm)} chars)")

    # idempotency against the real class
    duckv5_worldmodel_accum.install_patch(tool_agent)
    agent3 = tool_agent.ToolAgent(model="dummy-model", timeout=30.0)
    agent3._update_summarized_knowledge_from_assistant("World model:\nsolo finding")
    assert agent3._summarized_knowledge["world_model"].count("solo finding") == 1
    print("install_patch is idempotent against the real tool_agent module")

    # negative control: a module whose ToolAgent lacks the target method fails loudly.
    class _BrokenToolAgent:
        pass

    class _BrokenModule:
        ToolAgent = _BrokenToolAgent

    try:
        duckv5_worldmodel_accum.install_patch(_BrokenModule())
        raise AssertionError("expected AttributeError: ToolAgent missing the target method")
    except AttributeError:
        pass
    print("negative control: a ToolAgent missing the target method fails loudly")

    # restore: the REAL module must still behave correctly after the negative control
    # above ran against an unrelated fake module.
    agent4 = tool_agent.ToolAgent(model="dummy-model", timeout=30.0)
    agent4._update_summarized_knowledge_from_assistant("World model:\npost-failure finding")
    assert "post-failure finding" in agent4._summarized_knowledge["world_model"]
    print("restore: the real tool_agent.ToolAgent still patches/behaves correctly")


def _check_digest() -> None:
    src = (REPO_ROOT / "duckv5" / "duckv5_digest.py").read_text(encoding="utf-8")
    ast.parse(src)
    print("duckv5_digest.py parses clean (ast.parse)")

    from inference.agent import tool_agent
    from inference.agent.runtime_state import Frame, HistoryEntry

    assert hasattr(tool_agent.ToolAgent, "_build_user_prompt"), "patch target must exist"
    print("patch target ToolAgent._build_user_prompt exists (patch-target existence)")

    def grid(mid):
        return ((0, 0, 0), (0, mid, 0), (0, 0, 0))

    history = [
        HistoryEntry(action="", frame=Frame(grid=grid(0), step=0, level=1)),
        HistoryEntry(action="ACTION1", frame=Frame(grid=grid(1), step=1, level=1)),
        HistoryEntry(action="ACTION1", frame=Frame(grid=grid(1), step=2, level=1)),
    ]

    # BEFORE patching: no digest block in the prompt.
    agent = tool_agent.ToolAgent(model="dummy-model", timeout=30.0)
    before_prompt = agent._build_user_prompt(
        1,
        valid_actions=["ACTION1", "ACTION2"],
        current_frame=history[-1].frame,
        history_entries=history,
        previous_step_summary=None,
    )
    assert "PROGRESS DIGEST" not in before_prompt
    print("BEFORE patch: no PROGRESS DIGEST block in the user prompt")

    duckv5_digest.install_patch(tool_agent)
    assert getattr(tool_agent.ToolAgent, duckv5_digest._PATCH_MARKER, False)

    agent2 = tool_agent.ToolAgent(model="dummy-model", timeout=30.0)
    after_prompt = agent2._build_user_prompt(
        1,
        valid_actions=["ACTION1", "ACTION2"],
        current_frame=history[-1].frame,
        history_entries=history,
        previous_step_summary=None,
    )
    assert "=== PROGRESS DIGEST" in after_prompt, after_prompt
    assert "ACTION1: 2/1/1" in after_prompt, after_prompt
    assert "=== END DIGEST ===" in after_prompt, after_prompt
    print("AFTER patch: real ToolAgent's user prompt contains a well-formed PROGRESS DIGEST block")
    print("--- tail of user prompt ---")
    print(after_prompt[after_prompt.index("=== PROGRESS DIGEST") :])
    print("--- end ---")

    # per-instance isolation: a second ToolAgent starts with its own fresh digest.
    agent3 = tool_agent.ToolAgent(model="dummy-model", timeout=30.0)
    assert not hasattr(agent3, "_duckv5_digest")
    prompt3 = agent3._build_user_prompt(
        0,
        valid_actions=["ACTION1"],
        current_frame=history[0].frame,
        history_entries=history[:1],
        previous_step_summary=None,
    )
    assert "actions so far: 0" in prompt3, prompt3
    assert agent2._duckv5_digest is not agent3._duckv5_digest
    print("two ToolAgent instances hold independent TransitionDigest state (no cross-game leak)")

    # idempotency
    duckv5_digest.install_patch(tool_agent)
    print("install_patch is idempotent against the real tool_agent module")

    # negative control
    class _BrokenToolAgent:
        pass

    class _BrokenModule:
        ToolAgent = _BrokenToolAgent

    try:
        duckv5_digest.install_patch(_BrokenModule())
        raise AssertionError("expected AttributeError: ToolAgent missing _build_user_prompt")
    except AttributeError:
        pass
    print("negative control: a ToolAgent missing _build_user_prompt fails loudly")

    # restore: real module still works after the negative control ran elsewhere.
    agent4 = tool_agent.ToolAgent(model="dummy-model", timeout=30.0)
    prompt4 = agent4._build_user_prompt(
        0,
        valid_actions=["ACTION1"],
        current_frame=history[0].frame,
        history_entries=history[:1],
        previous_step_summary=None,
    )
    assert "=== PROGRESS DIGEST" in prompt4
    print("restore: the real tool_agent.ToolAgent still patches/behaves correctly")


def main() -> None:
    _check_worldmodel_accum()
    _check_digest()
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
