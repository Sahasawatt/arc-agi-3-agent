"""Verify duckv5/taaf-duck-v5.ipynb the way duckv3/duckv4's own builds verified
their notebooks: valid JSON, only cell 12 differs from the duckmod notebook it was
built from, every code cell's Python parses, and the EXACT cell-12 source (as
embedded in the notebook, not the standalone modules) executes cleanly against the
real bundle -- applying duckmod's own patches (hud_mask/TransitionGraph splice) AND
both duckv5 patches (accumulating world model, transition digest + reset banner) in
one exec, matching what a Kaggle kernel actually runs.

Run:
    PYTHONPATH=duck/bundle/src/ARC3-Inference:duck/bundle/src/tufa-arc-agi-framework/src \
        ./.venv/Scripts/python.exe duckv5/verify_notebook.py
"""
import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DUCKMOD_NB = REPO_ROOT / "duckmod" / "taaf-duck-mod.ipynb"
DUCKV5_NB = REPO_ROOT / "duckv5" / "taaf-duck-v5.ipynb"


def main() -> None:
    duckmod = json.loads(DUCKMOD_NB.read_text(encoding="utf-8"))
    duckv5 = json.loads(DUCKV5_NB.read_text(encoding="utf-8"))
    print(f"both notebooks parse as valid JSON, {len(duckv5['cells'])} cells")

    assert len(duckmod["cells"]) == len(duckv5["cells"])
    diffs = [
        c1.get("id")
        for c1, c2 in zip(duckmod["cells"], duckv5["cells"])
        if c1["source"] != c2["source"]
    ]
    assert diffs == ["12"], f"expected only cell 12 to differ, got: {diffs}"
    print(f"only cell 12 differs from duckmod's notebook ({len(duckv5['cells']) - 1}/{len(duckv5['cells'])} identical)")

    for cell in duckv5["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell["source"])
        ast.parse(src)
    print("every code cell's Python parses (ast.parse)")

    cell12 = next(c for c in duckv5["cells"] if c.get("id") == "12")
    cell12_src = "".join(cell12["source"])
    ast.parse(cell12_src)
    print("cell 12 source itself parses (ast.parse)")

    # duckv5's cell 12 must be a strict superset of duckmod's own cell 12 text --
    # proves this is a stacked customization layer, not a silent replacement (the
    # brief's explicit constraint: v5 = duckmod + these three).
    duckmod_cell12 = next(c for c in duckmod["cells"] if c.get("id") == "12")
    duckmod_cell12_src = "".join(duckmod_cell12["source"])
    assert cell12_src.startswith(duckmod_cell12_src.rstrip("\n")), (
        "duckv5's cell 12 must begin with duckmod's own cell 12 verbatim"
    )
    assert "duckv5: accumulating world model" in cell12_src
    print("cell 12 is duckmod's own patch verbatim, plus the duckv5 additions appended")

    # Execute the EXACT embedded cell-12 source (as a Kaggle kernel would) against
    # the real bundle -- applies duckmod's splice AND both duckv5 patches in one exec.
    from inference.agent import tool_agent, python_tool_sandbox
    from inference.agent.runtime_state import Frame, HistoryEntry

    before_bootstrap_len = len(python_tool_sandbox._SANDBOX_BOOTSTRAP)
    before_prompt_len = len(tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM)
    exec(compile(cell12_src, "<cell12>", "exec"), {})
    after_bootstrap_len = len(python_tool_sandbox._SANDBOX_BOOTSTRAP)
    after_prompt_len = len(tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM)

    assert getattr(tool_agent.ToolAgent, "_duckv5_accum_patched", False), "accum patch marker missing"
    assert getattr(tool_agent.ToolAgent, "_duckv5_digest_patched", False), "digest patch marker missing"
    assert after_bootstrap_len > before_bootstrap_len, "duckmod's own sandbox splice must still run"
    assert after_prompt_len > before_prompt_len, "system prompt must grow (duckmod's + duckv5's additions)"
    print(
        f"executed embedded cell-12 source against the real bundle: "
        f"sandbox bootstrap +{after_bootstrap_len - before_bootstrap_len} chars, "
        f"system prompt +{after_prompt_len - before_prompt_len} chars, "
        f"all three patch markers set"
    )

    agent = tool_agent.ToolAgent(model="dummy-model", timeout=30.0)
    assert "hud_mask(history)" in agent._system_prompt, "duckmod's own tool doc must survive"
    assert "PROGRESS DIGEST block is auto-appended" in agent._system_prompt, "duckv5's addendum must be present"
    print("real ToolAgent's system prompt contains both duckmod's and duckv5's additions")

    def grid(mid, w=3):
        return tuple(tuple(mid if (r, c) == (1, 1) else 0 for c in range(w)) for r in range(w))

    history = [
        HistoryEntry(action="", frame=Frame(grid=grid(0), step=0, level=1)),
        HistoryEntry(action="ACTION1", frame=Frame(grid=grid(1), step=1, level=1)),
        HistoryEntry(action="ACTION1", frame=Frame(grid=grid(1), step=2, level=2)),  # level_up
    ]
    user_prompt = agent._build_user_prompt(
        1,
        valid_actions=["ACTION1", "ACTION2"],
        current_frame=history[-1].frame,
        history_entries=history,
        previous_step_summary=None,
    )
    assert "=== PROGRESS DIGEST" in user_prompt, user_prompt
    assert "L1@a0" in user_prompt and "L2@a2" in user_prompt, user_prompt
    print("real ToolAgent's per-turn user prompt contains the duckv5 PROGRESS DIGEST block")

    # exercise the accumulate patch through the real, exec'd module too.
    agent._update_summarized_knowledge_from_assistant("World model:\nfirst finding")
    agent._update_summarized_knowledge_from_assistant("World model:\nsecond finding")
    wm = agent._summarized_knowledge["world_model"]
    assert "first finding" in wm and "second finding" in wm, wm
    print("real ToolAgent's world_model field accumulates across turns via the exec'd cell 12")

    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
