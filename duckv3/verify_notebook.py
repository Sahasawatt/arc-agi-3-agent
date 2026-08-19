"""Verify duckv3/taaf-duck-v3.ipynb the way duckmod's own build verified
taaf-duck-mod.ipynb: valid JSON, only cell 12 differs from the duckmod
notebook it was built from, every code cell's Python parses, and the exact
cell-12 source (as embedded in the notebook, not the standalone module)
executes cleanly against the real bundle and reaches
`tool_agent._build_system_prompt`.

Run:
    PYTHONPATH=duck/bundle/src/ARC3-Inference:duck/bundle/src/tufa-arc-agi-framework/src \
        python duckv3/verify_notebook.py
"""
import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DUCKMOD_NB = REPO_ROOT / "duckmod" / "taaf-duck-mod.ipynb"
DUCKV3_NB = REPO_ROOT / "duckv3" / "taaf-duck-v3.ipynb"


def main() -> None:
    duckmod = json.loads(DUCKMOD_NB.read_text(encoding="utf-8"))
    duckv3 = json.loads(DUCKV3_NB.read_text(encoding="utf-8"))
    print(f"both notebooks parse as valid JSON, {len(duckv3['cells'])} cells")

    assert len(duckmod["cells"]) == len(duckv3["cells"])
    diffs = [
        c1.get("id")
        for c1, c2 in zip(duckmod["cells"], duckv3["cells"])
        if c1["source"] != c2["source"]
    ]
    assert diffs == ["12"], f"expected only cell 12 to differ, got: {diffs}"
    print(f"only cell 12 differs from duckmod's notebook ({len(duckv3['cells']) - 1}/{len(duckv3['cells'])} identical)")

    for cell in duckv3["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell["source"])
        ast.parse(src)
    print("every code cell's Python parses (ast.parse)")

    cell12 = next(c for c in duckv3["cells"] if c.get("id") == "12")
    cell12_src = "".join(cell12["source"])
    ast.parse(cell12_src)
    print("cell 12 source itself parses (ast.parse)")

    # Execute the EXACT embedded cell-12 source (as a Kaggle kernel would)
    # against the real bundle.
    from inference.agent import tool_agent
    from inference.agent.runtime_state import Frame, HistoryEntry

    ns = {"tool_agent": tool_agent}
    before_len = len(tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM)
    exec(compile(cell12_src, "<cell12>", "exec"), ns)
    after_len = len(tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM)
    assert getattr(tool_agent.ToolAgent, "_duckv3_patched", False)
    assert after_len > before_len
    print(f"executed embedded cell-12 source against the real bundle: system prompt +{after_len - before_len} chars")

    agent = tool_agent.ToolAgent(model="dummy-model", timeout=30.0)
    assert "OBSERVATION block" in agent._system_prompt, "system prompt addition not present"
    print("real ToolAgent's system prompt contains the duckv3 OBSERVATION paragraph")

    grid = ((9, 0, 0), (0, 1, 0), (0, 0, 0))
    history = [HistoryEntry(action="", frame=Frame(grid=grid, step=0, level=1))]
    user_prompt = agent._build_user_prompt(
        0,
        valid_actions=["ACTION1", "ACTION2"],
        current_frame=history[0].frame,
        history_entries=history,
        previous_step_summary=None,
    )
    assert "HUD cells (auto-masked):" in user_prompt
    print("real ToolAgent's per-turn user prompt contains the duckv3 OBSERVATION block")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
