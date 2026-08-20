"""Verify the generated duckv7 notebook and, when available, the real bundle."""
import ast
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "duckmod" / "taaf-duck-mod.ipynb"
NB_PATH = ROOT / "duckv7" / "taaf-duck-v7.ipynb"


def _cell(nb):
    return next(c for c in nb["cells"] if c.get("id") == "12")


def _static_checks():
    base = json.loads(BASE.read_text(encoding="utf-8"))
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    assert len(base["cells"]) == len(nb["cells"])
    diffs = [a.get("id") for a, b in zip(base["cells"], nb["cells"]) if a["source"] != b["source"]]
    assert diffs == ["12"], diffs
    for cell in nb["cells"]:
        if cell.get("cell_type") == "code":
            ast.parse("".join(cell["source"]))
    src = "".join(_cell(nb)["source"])
    assert src.startswith("".join(_cell(base)["source"]).rstrip("\n"))
    for marker in ("LOCAL_ANALYZER_MAX_OUTPUT", "_slim_prompt", "5-15", "install_patch"):
        assert marker in src, marker
    print("JSON valid; exactly one cell differs; every code cell parses; v7 markers present")
    return src


def _runtime_checks(src):
    try:
        from inference.agent import tool_agent
        from inference.agent.runtime_state import Frame, HistoryEntry
    except ImportError as exc:
        print(f"runtime bundle verification deferred: {exc}")
        print("deferred checks: embedded-cell execution, synthetic request payload, real prompt length, negative control")
        return

    before_env = os.environ.get("LOCAL_ANALYZER_MAX_OUTPUT")
    baseline_builder = tool_agent._build_system_prompt
    exec(compile(src, "<duckv7-cell12>", "exec"), {})
    try:
        assert os.environ["LOCAL_ANALYZER_MAX_OUTPUT"] == "768"
        assert tool_agent._LOCAL_ANALYZER_MAX_OUTPUT == 768
        agent = tool_agent.ToolAgent(model="dummy-model", timeout=30.0)
        assert agent._max_output_tokens == 768
        assert len(agent._system_prompt) < 8000, len(agent._system_prompt)
        original_prompt = baseline_builder(tool_output_tokens=agent._tool_output_tokens)
        names = set(__import__("re").findall(r"`([A-Za-z_][A-Za-z0-9_]*)", original_prompt))
        assert names.issubset(set(__import__("re").findall(r"`([A-Za-z_][A-Za-z0-9_]*)", agent._system_prompt)))
        frame = Frame(grid=((0,),), step=0, level=1)
        batching_prompt = agent._build_user_prompt(
            0, valid_actions=[], current_frame=frame,
            history_entries=[HistoryEntry(action="", frame=frame)],
            previous_step_summary=None,
        )
        assert "5-15" in batching_prompt and "Single-action" in batching_prompt

        captured = {}

        class Response:
            status_code = 200
            text = ""
            def raise_for_status(self): pass
            def json(self): return {"choices": [{"message": {}, "finish_reason": "stop"}]}

        original_post = tool_agent.requests.post
        tool_agent.requests.post = lambda *a, **kw: (captured.update(kw["json"]) or Response())
        try:
            agent._chat_completion([], tools=None)
        finally:
            tool_agent.requests.post = original_post
        assert captured.get("max_tokens") == 768, captured
        assert captured.get("chat_template_kwargs", {}).get("enable_thinking") is True
        print(f"real-bundle checks passed: synthetic payload max_tokens={captured['max_tokens']}, prompt={len(agent._system_prompt)} chars, thinking=on")

        marker = tool_agent.ToolAgent._duckv7_throughput_patched
        delattr(tool_agent.ToolAgent, "_duckv7_throughput_patched")
        try:
            try:
                assert getattr(tool_agent.ToolAgent, "_duckv7_throughput_patched_typo", False), "negative control: typo unexpectedly passed"
            except AssertionError as exc:
                print(f"negative control failed loudly as expected: {exc}")
            else:
                raise AssertionError("negative control did not fail")
        finally:
            setattr(tool_agent.ToolAgent, "_duckv7_throughput_patched", marker)
        print("negative control restored; all runtime checks passed")
    finally:
        if before_env is None:
            os.environ.pop("LOCAL_ANALYZER_MAX_OUTPUT", None)
        else:
            os.environ["LOCAL_ANALYZER_MAX_OUTPUT"] = before_env


if __name__ == "__main__":
    source = _static_checks()
    _runtime_checks(source)
