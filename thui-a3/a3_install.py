# ---- thui-a3 install (after the teeth) ----
import inspect as _a3_inspect
assert "run_sandboxed_python(" in _a3_inspect.getsource(_a3_orig_run_python_tool), "the tool no longer calls the module-level sandbox"
assert "def _build_user_prompt" in _a3_inspect.getsource(_a3_ta.ToolAgent)
_a3_ta.ToolAgent._run_python_tool = _a3_run_python_tool
_a3_ta.run_sandboxed_python = _a3_sandbox
_a3_ta.ToolAgent._build_user_prompt = _a3_build_user_prompt
assert _a3_ta.ToolAgent._run_python_tool is _a3_run_python_tool and _a3_ta.run_sandboxed_python is _a3_sandbox
assert _a3_ta.ToolAgent._build_user_prompt is _a3_build_user_prompt
print(f"THUI_A3_GRAFT ok tool_agent={_a3_ta.__file__} max_src={_A3_MAX_SRC_CHARS}", flush=True)
