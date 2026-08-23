# === duckv21: stop telling the model to think harder on every single turn ===
#
# WHERE THIS CAME FROM (notes/R26-reasoning-effort.md):
# `ataraxian/arc3-qwen38-colab-v29` is published by the team at leaderboard rank 21
# (Ya Xu, hidden 2.37, vs our rank 212 at 1.70). Against the same June-era base we
# hold, their whole diff is SIX files. The load-bearing one adds this hook to
# inference/utils/openai_compat.py, with their own comment:
#
#   # Optional Qwen3.8 reasoning_effort override (xhigh/medium/low) via env.
#   # Empty/absent => leave the model default (xhigh). This is the hook v27/v28
#   # use to dial down over-thinking (see results-v25 r11l/sk48 analysis paralysis).
#
# and their setup env sets:  'LOCAL_ANALYZER_REASONING_EFFORT': 'medium'
#
# VERIFIED AGAINST THE MODEL'S OWN CHAT TEMPLATE, not taken on their word
# (huggingface.co/Qwen/Qwen3.8-27B-FP8/raw/main/chat_template.jinja):
#
#   {%- set resolved_reasoning_effort = reasoning_effort|default('xhigh') %}
#   {%- if resolved_reasoning_effort not in ('xhigh', 'medium', 'low') %}
#   {{- raise_exception('Unexpected reasoning effort ...') }}
#
#   xhigh -> "think carefully through the task, validate key assumptions, consider
#            plausible alternatives"
#   low   -> "keep your thinking brief and focused, moving directly to the conclusion"
#   medium-> no extra instruction at all
#
# So every turn of every run this campaign has ever made carried the xhigh
# instruction, because xhigh is the template default and nothing set the key. That
# matches what we measured independently: games plateau with 30-95 minutes and 24-47
# actions still unspent (LEDGER). Not out of budget — spending it on deliberation.
#
# A wrong value raises inside the template rather than being ignored, so this flag
# cannot fail silently the way MULTIMODAL_GRID_LINES does upstream ('true' vs "1").
#
# WHY A MONKEYPATCH: our anim bundle's openai_compat.py has no such hook (checked:
# `LOCAL_ANALYZER_REASONING_EFFORT` and `reasoning_effort` both absent from it and
# from the newer bundle). And tool_agent.py:45 does
# `from inference.utils.openai_compat import build_chat_payload`, so the name is
# bound in tool_agent's namespace — patching only the source module would be a no-op.
# Both are patched.

import os as _os

_EFFORT = "medium"
_os.environ["LOCAL_ANALYZER_REASONING_EFFORT"] = _EFFORT

from inference.utils import openai_compat as _compat  # noqa: E402
from inference.agent import tool_agent as _tool_agent  # noqa: E402

_ORIGINAL = _compat.build_chat_payload


def _build_chat_payload_with_effort(**kwargs):
    payload = _ORIGINAL(**kwargs)
    effort = _os.environ.get("LOCAL_ANALYZER_REASONING_EFFORT", "").strip()
    if effort and isinstance(payload.get("chat_template_kwargs"), dict):
        payload["chat_template_kwargs"]["reasoning_effort"] = effort
    return payload


_compat.build_chat_payload = _build_chat_payload_with_effort
# tool_agent imported the name directly (tool_agent.py:45), so its binding is the
# one that actually runs.
_tool_agent.build_chat_payload = _build_chat_payload_with_effort

# --- teeth, in-kernel, before a single game starts ---------------------------
# R8's lesson: a patch that silently fails to take reads afterwards as "the idea
# does not help". Prove it fires on a payload shaped like the real one.
_probe = _tool_agent.build_chat_payload(
    provider="vllm",
    model="test",
    messages=[{"role": "user", "content": "x"}],
    max_tokens=None,
    temperature=0.6,
    top_p=0.95,
    top_k=20,
    thinking=True,
)
assert _probe["chat_template_kwargs"]["reasoning_effort"] == _EFFORT, (
    f"duckv21: TEETH FAIL - reasoning_effort missing from the payload: {_probe.get('chat_template_kwargs')}"
)
assert _probe["chat_template_kwargs"]["enable_thinking"] is True, (
    "duckv21: TEETH FAIL - the patch dropped enable_thinking"
)
# And prove the patch is not a no-op: the unpatched original must NOT carry the key.
_before = _ORIGINAL(
    provider="vllm",
    model="test",
    messages=[{"role": "user", "content": "x"}],
    max_tokens=None,
    temperature=0.6,
    top_p=0.95,
    top_k=20,
    thinking=True,
)
assert "reasoning_effort" not in _before.get("chat_template_kwargs", {}), (
    "duckv21: TEETH FAIL - the stock builder already sets reasoning_effort, so this "
    "run measures nothing"
)
assert _tool_agent.build_chat_payload is not _ORIGINAL, "duckv21: tool_agent binding not replaced"

print(f"duckv21: reasoning_effort={_EFFORT} (template default is xhigh); "
      f"patched openai_compat AND tool_agent bindings; teeth OK")
