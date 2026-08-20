"""Duck v7 throughput-only customization layer.

This module is stdlib-only because its source is embedded in the Kaggle cell.
"""
import os
import re


_MAX_OUTPUT = 768
_PROMPT_LIMIT = 8000
_BATCHING_LINES = (
    "When confident about a plan or performing a systematic sweep, emit 5-15 "
    "environment actions in one turn to amortize the model call.\n"
    "Single-action turns are appropriate for genuinely uncertain states or "
    "when each result determines the next probe.\n"
    "Batch only actions that remain safe under the current plan, and stop on "
    "game-over or level-completion results."
)


def _tool_names(text):
    """Return code-like names mentioned in backticks, preserving original order."""
    names = []
    for name in re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)", text):
        if name not in names:
            names.append(name)
    return names


def _slim_prompt(original):
    """Deduplicate generic prompt prose while retaining every documented name.

    Lines containing code names are the usage/syntax-bearing surface and are kept
    verbatim. Remaining lines are retained only once and only while the budget
    permits; this is deliberately content-agnostic rather than game-tuned.
    """
    names = _tool_names(original)
    lines = original.splitlines()
    kept = []
    seen = set()
    for line in lines:
        normalized = " ".join(line.split()).casefold()
        required = bool(re.search(r"`[A-Za-z_][A-Za-z0-9_]*", line))
        if required or (normalized and normalized not in seen and len(kept) < 32):
            if normalized:
                seen.add(normalized)
            kept.append(line)
    result = "\n".join(kept).strip()
    # Keep all syntax-bearing lines, but never allow generic filler to crowd them.
    if len(result) >= _PROMPT_LIMIT:
        result = "\n".join(
            line for line in kept if re.search(r"`[A-Za-z_][A-Za-z0-9_]*", line)
        ).strip()
    missing = [name for name in names if name not in result]
    assert not missing, f"v7 prompt slim dropped documented names: {missing}"
    assert len(result) < _PROMPT_LIMIT, len(result)
    return result


def _patch_output_cap(tool_agent):
    # Cell 12 imports tool_agent before this layer runs, so env alone cannot alter
    # its module-level _get_env_int result. Set both surfaces for real harness runs.
    os.environ["LOCAL_ANALYZER_MAX_OUTPUT"] = str(_MAX_OUTPUT)
    tool_agent._LOCAL_ANALYZER_MAX_OUTPUT = _MAX_OUTPUT


def install_patch(tool_agent):
    """Install v7 patches on the already-imported real bundle module."""
    _patch_output_cap(tool_agent)

    original_builder = tool_agent._build_system_prompt

    def build_slim_system_prompt(*, tool_output_tokens):
        original = original_builder(tool_output_tokens=tool_output_tokens)
        return _slim_prompt(original)

    tool_agent._build_system_prompt = build_slim_system_prompt
    original_prompt_builder = tool_agent.ToolAgent._build_user_prompt

    def build_batched_user_prompt(self, *args, **kwargs):
        prompt = original_prompt_builder(self, *args, **kwargs)
        return prompt + "\n\nBatching guidance:\n- " + _BATCHING_LINES.replace("\n", "\n- ")

    tool_agent.ToolAgent._build_user_prompt = build_batched_user_prompt
    tool_agent.ToolAgent._duckv7_throughput_patched = True
    return _MAX_OUTPUT


def _demo():
    class _Agent:
        def __init__(self):
            self.payload = {"model": "x", "messages": [], "max_tokens": _MAX_OUTPUT}

    original = """You are a coding agent.
`python` is the only tool.
Use `current_frame`, `history`, `valid_actions`, and `action`.
Use `TransitionGraph` and `hud_mask` when useful.
`python` may call `action(actions)` more than once.
Repeated guidance: use `python` and `action(actions)`.
"""
    slim = _slim_prompt(original)
    assert _Agent().payload["max_tokens"] == 768
    assert len(slim) < 8000
    assert set(_tool_names(original)).issubset(_tool_names(slim))
    assert all(line in _BATCHING_LINES for line in ("5-15", "Single-action", "stop on"))
    print("duckv7 throughput self-test OK")


if __name__ == "__main__":
    _demo()
