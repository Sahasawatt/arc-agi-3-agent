# duckv12: v10 (anim bundle + Qwen3.8, uncapped) + prompt-level brevity.
# Diagnosis R16: 90.2% of generated characters are reasoning. Remedy must not be a token
# cap (R17: no thinking-only knob; a total cap truncated tool calls and collapsed v9), so
# ask for shorter deliberation in the system prompt instead.
import inference.agent.tool_agent as tool_agent

_BREVITY_TEXT = (
    "\n- Keep deliberation SHORT. Aim for under ~300 words of reasoning per turn: state the"
    "\n  hypothesis you are testing and the action that tests it, then act. The environment"
    "\n  answers questions faster than analysis does, and every game ends on a wall clock"
    "\n  that reasoning shares with acting. Never shorten the tool call itself."
)

assert isinstance(getattr(tool_agent, "PYTHON_ADDENDUM", None), str), (
    "duckv12: tool_agent.PYTHON_ADDENDUM missing or not a str - patch point moved"
)
assert "Keep deliberation SHORT" not in tool_agent.PYTHON_ADDENDUM, "duckv12: already patched"
tool_agent.PYTHON_ADDENDUM = tool_agent.PYTHON_ADDENDUM + _BREVITY_TEXT
print(f"duckv12: anim bundle + Qwen3.8 + brevity +{len(_BREVITY_TEXT)} chars, output UNCAPPED")
