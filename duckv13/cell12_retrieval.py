# duckv13: v10 (anim bundle + Qwen3.8, uncapped) + animation-retrieval discipline.
#
# R18 measured the defect: 669 animation() requests in one run, 582 served, with
# pathological loops (sb26 405, tn36 137, sp80 41) while the strong animation games used
# 3-10. Two of the three loopers scored zero: frames were retrieved instead of actions
# being taken. The feature is useful; iterating over frame numbers blindly is not.
import inference.agent.tool_agent as tool_agent

_RETRIEVAL_TEXT = (
    "\n- Animation retrieval is for ONE question: what did that action actually do?"
    "\n  Read the compact summary first. Call `animation()` at most ONCE per animated"
    "\n  action, and only when the summary leaves a transient you cannot explain."
    "\n  NEVER iterate over frame indices in a loop, and never re-retrieve frames you"
    "\n  have already seen - the timeline does not change. If two retrievals in a row"
    "\n  taught you nothing new, take an environment action instead: the game answers"
    "\n  faster than the replay does."
)

assert isinstance(getattr(tool_agent, "PYTHON_ADDENDUM", None), str), (
    "duckv13: tool_agent.PYTHON_ADDENDUM missing or not a str - patch point moved"
)
assert "Animation retrieval is for ONE question" not in tool_agent.PYTHON_ADDENDUM, (
    "duckv13: already patched"
)
tool_agent.PYTHON_ADDENDUM = tool_agent.PYTHON_ADDENDUM + _RETRIEVAL_TEXT
print(f"duckv13: retrieval-discipline addendum +{len(_RETRIEVAL_TEXT)} chars, output UNCAPPED")
