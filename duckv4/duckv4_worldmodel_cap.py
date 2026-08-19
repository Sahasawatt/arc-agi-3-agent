"""World-model field cap for the ARC-AGI-3 duck harness (duckv4, lever a).

Patches `tool_agent._extract_labeled_blocks` -- the parser that turns an
assistant turn's labeled sections (World model:, Goal model:, Action model:,
Recent findings:, Open questions:, Plan:, Cross-level notes:, plus the
Hypothesis/History check/Next test aliases) into the dict merged into
`ToolAgent._summarized_knowledge` and re-injected VERBATIM into every
subsequent turn's prompt (`_summarized_knowledge_lines`,
tool_agent.py:1128-1146). R2's own finding: this call site passes
`max_chars=None` -- unbounded -- so a long block written once is paid on
every following turn for the rest of a level
(results/wayfinder/R2-levers.md, "World-model field length" row, ranked #1
lever by leverage-per-cost: "the single biggest uncapped, silently-
compounding prompt-bloat surface in the harness").

Same-module patch, not a from-import copy: `_extract_labeled_blocks` and its
only caller `_extract_scientist_note` both live directly in tool_agent.py,
so `_extract_scientist_note`'s call resolves the bare name against
`tool_agent.__dict__` at CALL time -- replacing the module attribute is
enough. Same mechanism duckmod's own build report documents for its splice
anchors and R5 documents for `_LOCAL_ANALYZER_SEED`; verified against the
real bundle in verify_against_bundle.py, not just asserted here.

Truncation, not LLM self-compression: an LLM call to compress a field would
add its own latency to the SAME per-action-latency problem this lever exists
to fix (R1: 19-233s/action across 25 otherwise-identical games is the
harness's #1 measured failure -- every one of 25 games hit the same flat
clock with none crashing or winning). Deterministic tail-keep (keep the
newest text, drop the oldest) with a "[compacted: N chars dropped]" marker,
per the brief's stated fallback design.
"""
from __future__ import annotations

# ponytail: flat cap for all 7 fields, not measured per-field -- R2 doesn't
# cite per-field token/char sizes for this harness (only the mechanism, not
# a distribution). 6000 chars (~1.5-2k tokens by the harness's own len/3
# estimator, tool_agent.py:462-467) sits mid the brief's suggested 4-8k
# conservative range. Narrow per-field once a real run's transcripts show
# one field dominating the growth.
FIELD_CAP_CHARS = 6000

_PATCH_MARKER = "_duckv4_capped"


def _compact(text: str, cap: int = FIELD_CAP_CHARS) -> str:
    """Tail-keep a field: drop the oldest (leading) text, keep the newest
    (trailing) `cap` chars, and say how much was dropped. Never raises on
    empty/short input."""
    if not text or len(text) <= cap:
        return text
    dropped = len(text) - cap
    return f"[compacted: {dropped} chars dropped] {text[-cap:]}"


def install_patch(tool_agent_module) -> None:
    """Wrap tool_agent_module._extract_labeled_blocks so every label's
    extracted text is capped before it reaches _extract_scientist_note (and
    from there, ToolAgent._summarized_knowledge -- see module docstring).
    Idempotent: a second call no-ops rather than double-wrapping."""
    if getattr(tool_agent_module, _PATCH_MARKER, False):
        return
    original = tool_agent_module._extract_labeled_blocks

    def _capped(content, labels):
        raw = original(content, labels)
        return {label: _compact(text) for label, text in raw.items()}

    setattr(tool_agent_module, _PATCH_MARKER, True)
    tool_agent_module._extract_labeled_blocks = _capped


def _demo() -> None:
    # --- _compact in isolation ---
    short = "a short finding"
    assert _compact(short) == short, "under-cap text must pass through unchanged"

    exact = "x" * FIELD_CAP_CHARS
    assert _compact(exact) == exact, "exactly-at-cap text must not be marked"

    long_text = ("old-" * 100) + "NEWEST-TAIL-" + ("y" * (FIELD_CAP_CHARS - 20))
    capped = _compact(long_text, cap=FIELD_CAP_CHARS)
    assert capped.startswith("[compacted: "), capped[:40]
    assert "chars dropped]" in capped
    assert capped.endswith(long_text[-FIELD_CAP_CHARS:]), "must keep the TAIL, not the head"
    assert "old-old-old" not in capped, "the dropped (oldest) prefix must be gone"
    assert len(capped) <= FIELD_CAP_CHARS + 40, "marker overhead must stay small"

    assert _compact("") == "", "empty field must not crash or grow a marker"

    # --- install_patch against a fake tool_agent-shaped module ---
    class _FakeModule:
        @staticmethod
        def _extract_labeled_blocks(content, labels):
            # Minimal stand-in for the real parser: one short field, one
            # field that would blow the cap if left unbounded.
            return {
                "World model": "y" * (FIELD_CAP_CHARS * 3),
                "Goal model": "reach the door",
            }

    mod = _FakeModule()
    original_fn = mod._extract_labeled_blocks

    install_patch(mod)
    out = mod._extract_labeled_blocks("irrelevant content", ["World model", "Goal model"])
    assert len(out["World model"]) <= FIELD_CAP_CHARS + 40, "patched call must cap the long field"
    assert "[compacted:" in out["World model"]
    assert out["Goal model"] == "reach the door", "a short field must pass through unchanged"

    # idempotency: patching twice must not double-wrap (same output twice)
    install_patch(mod)
    out2 = mod._extract_labeled_blocks("irrelevant content", ["World model", "Goal model"])
    assert out == out2, "re-applying install_patch must not change behavior"
    assert mod._extract_labeled_blocks is not original_fn

    # negative control: prove the assertion above is not vacuous -- pointing
    # at a module that lacks the attribute must fail loudly, not silently.
    class _WrongModule:
        pass

    try:
        install_patch(_WrongModule())
        raise AssertionError("expected AttributeError on a module missing _extract_labeled_blocks")
    except AttributeError:
        pass  # expected: proves install_patch actually reads the real attribute name

    print("duckv4_worldmodel_cap self-test OK")


if __name__ == "__main__":
    _demo()
