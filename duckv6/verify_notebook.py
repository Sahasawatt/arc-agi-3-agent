"""Static and, when the ARC bundle is installed, runtime verification for v6."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    base = json.loads((ROOT / "duckmod/taaf-duck-mod.ipynb").read_text())
    nb = json.loads((ROOT / "duckv6/taaf-duck-v6.ipynb").read_text())
    assert len(base["cells"]) == len(nb["cells"])
    diffs = [a.get("id") for a, b in zip(base["cells"], nb["cells"]) if a["source"] != b["source"]]
    assert diffs == ["12"], diffs
    for cell in nb["cells"]:
        if cell.get("cell_type") == "code": ast.parse("".join(cell["source"]))
    src = "".join(next(c for c in nb["cells"] if c.get("id") == "12")["source"])
    assert all(marker in src for marker in ("_duckv6_digest_patched", "_duckv5_accum_patched", "HudSemantics", "render_hint"))
    print("JSON valid; exactly one cell differs; every code cell parses; v6 markers and HUD wiring present")
    try:
        from inference.agent import tool_agent, python_tool_sandbox
        from inference.agent.runtime_state import Frame, HistoryEntry
    except ImportError as exc:
        print(f"runtime bundle verification deferred: {exc}")
        return
    before = len(tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM)
    exec(compile(src, "<duckv6-cell12>", "exec"), {})
    assert getattr(tool_agent.ToolAgent, "_duckv5_accum_patched", False)
    assert getattr(tool_agent.ToolAgent, "_duckv6_digest_patched", False)
    assert len(tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM) > before
    agent = tool_agent.ToolAgent(model="dummy-model", timeout=30.0)
    def grid(v): return ((v, 0, 0), (0, 0, 0), (0, 0, 0))
    history = [HistoryEntry(action="", frame=Frame(grid=grid(0), step=0, level=1))]
    history += [HistoryEntry(action="A", frame=Frame(grid=grid(0), step=i, level=1)) for i in range(1, 14)]
    prompt = agent._build_user_prompt(1, valid_actions=["A"], current_frame=history[-1].frame, history_entries=history, previous_step_summary=None)
    assert "=== PROGRESS DIGEST" in prompt and "ADVISORY" in prompt
    digest = agent._duckv6_digest
    hud_key = ("row", 0, 2)
    digest.hud._histories[hud_key] = [(8 - i, True, i) for i in range(8)]
    digest.hud._diverged = {hud_key}
    hud_prompt = agent._build_user_prompt(1, valid_actions=["A"], current_frame=history[-1].frame, history_entries=history, previous_step_summary=None)
    assert "=== HUD SEMANTICS" in hud_prompt, hud_prompt
    agent._update_summarized_knowledge_from_assistant("World model:\nfirst")
    agent._update_summarized_knowledge_from_assistant("World model:\nsecond")
    assert "first" in agent._summarized_knowledge["world_model"] and "second" in agent._summarized_knowledge["world_model"]
    original = tool_agent.ToolAgent._duckv6_digest_patched
    delattr(tool_agent.ToolAgent, "_duckv6_digest_patched")
    try:
        try:
            assert getattr(tool_agent.ToolAgent, "_duckv6_digset_patched", False), (
                "negative control: wrong attribute name unexpectedly passed"
            )
        except AssertionError as exc:
            print(f"negative control failed loudly as expected: {exc}")
        else:
            raise AssertionError("negative control did not fail")
    finally:
        setattr(tool_agent.ToolAgent, "_duckv6_digest_patched", original)
    print("runtime embedded-cell checks passed: markers, digest/warning prompt, world-model accumulation, negative control restored")


if __name__ == "__main__": main()
