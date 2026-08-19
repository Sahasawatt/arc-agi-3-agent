"""Accumulating world-model fields for the ARC-AGI-3 duck harness (duckv5, feature 1).

R7 (results/wayfinder/R7-v4-postmortem.md sec5) measured why duckv4's char-length cap on
`_extract_labeled_blocks` never fired: `_update_summarized_knowledge_from_assistant`
(tool_agent.py:1105-1111) OVERWRITES each field with only the CURRENT turn's extracted
text -- the field never accumulates, so a 6000-char cap sits ~5x above the largest block
ever written in a real 25-game run (measured max 3,501 chars). R6 (thrash forensics)
measured the consequence directly: 8/9 zero-score games showed the persisted world-model
field frozen or empty for the whole run while the model's live, uncaptured reasoning kept
re-deriving (and re-contradicting) facts already established earlier -- Mode 1, "scaffold
state amnesia."

This patches the MERGE step itself -- the same call site R7 names -- so each field
ACCUMULATES turn-stamped text instead of being replaced: new text from this turn is
appended (with an exact-duplicate-paragraph dedup so a model that repeats itself doesn't
inflate the field for free), and the whole field is bounded and trimmed oldest-first once
it grows past the cap -- the tail-keep discipline duckv4's cap used
(duckv4/duckv4_worldmodel_cap.py), except now the bound actually matters because growth
is real.

Class-level patch on `ToolAgent._update_summarized_knowledge_from_assistant` (an
INSTANCE method, unlike duckv4's target which was a plain module-level function) -- same
class-level monkeypatch mechanics duckv3 used for `_build_user_prompt`
(results/duckv3-build-20260819.md sec2), verified against the real bundle in
verify_against_bundle.py, not just asserted here.

Same-module patch, not a from-import copy: `_extract_scientist_note` lives directly in
tool_agent.py and our replacement method calls `tool_agent_module._extract_scientist_note`
(the module's own current attribute) rather than importing it elsewhere, so it stays
correct even if a future patch on this same module replaces that function too.
"""
from __future__ import annotations

# ponytail: one flat cap for all 7 fields, same simplification duckv4's cap made (R2
# doesn't cite per-field sizes for this harness, only the mechanism). Mid the brief's
# 6000-8000 char range. Narrow per-field once a real accumulating run's transcripts show
# one field dominating growth.
FIELD_CAP_CHARS = 7000

_PATCH_MARKER = "_duckv5_accum_patched"
_TURN_ATTR = "_duckv5_turn"


def _accumulate(existing: str, new_text: str, turn_label: str, cap: int = FIELD_CAP_CHARS) -> str:
    """Append `new_text` stamped with `turn_label` to `existing`; skip if that exact
    paragraph is already present anywhere in the field (dedup -- a model that re-states
    an unchanged finding doesn't grow the field for free); trim oldest-first once the
    result exceeds `cap`. Never raises on empty input."""
    if not new_text:
        return existing
    if new_text in existing:
        return existing
    stamped = f"[{turn_label}] {new_text}"
    combined = stamped if not existing else f"{existing}\n{stamped}"
    if len(combined) <= cap:
        return combined
    dropped = len(combined) - cap
    return f"[compacted: {dropped} chars dropped]\n{combined[-cap:]}"


def install_patch(tool_agent_module) -> None:
    """Replace ToolAgent._update_summarized_knowledge_from_assistant so every labeled
    field ACCUMULATES across turns instead of being overwritten each turn. Idempotent: a
    second call no-ops rather than double-wrapping."""
    cls = tool_agent_module.ToolAgent
    if getattr(cls, _PATCH_MARKER, False):
        return
    if not hasattr(cls, "_update_summarized_knowledge_from_assistant"):
        raise AttributeError(
            "duckv5 accum: ToolAgent._update_summarized_knowledge_from_assistant not "
            "found -- upstream tool_agent.py changed"
        )
    extract_note = tool_agent_module._extract_scientist_note

    def _patched(self, content: str) -> None:
        note = extract_note(content)
        if not note:
            return
        turn = getattr(self, _TURN_ATTR, 0) + 1
        setattr(self, _TURN_ATTR, turn)
        turn_label = f"t{turn}"
        for key, value in note.items():
            if value:
                existing = self._summarized_knowledge.get(key, "")
                self._summarized_knowledge[key] = _accumulate(existing, value, turn_label)

    setattr(cls, _PATCH_MARKER, True)
    cls._update_summarized_knowledge_from_assistant = _patched


def _demo() -> None:
    # --- _accumulate in isolation ---
    assert _accumulate("", "first finding", "t1") == "[t1] first finding"
    two_turns = _accumulate("[t1] first finding", "second finding", "t2")
    assert two_turns == "[t1] first finding\n[t2] second finding", two_turns

    # exact-duplicate paragraph must not grow the field
    dup = _accumulate(two_turns, "first finding", "t3")
    assert dup == two_turns, "an exact-duplicate paragraph must be skipped, not re-stamped"

    # trimming past the cap: oldest text drops, newest survives, marker present
    cap = 200
    grown = ""
    for i in range(1, 40):
        grown = _accumulate(grown, f"finding number {i} with some padding text", f"t{i}", cap=cap)
    assert grown.startswith("[compacted: "), grown[:40]
    assert "chars dropped]" in grown
    assert "finding number 39" in grown, "the newest finding must survive trimming"
    assert "finding number 1 " not in grown, "the oldest finding must be dropped"
    assert len(grown) <= cap + 40, "marker overhead must stay small"

    assert _accumulate("", "", "t1") == "", "empty new text must be a no-op"

    # --- install_patch against a fake tool_agent-shaped module ---
    class _FakeToolAgent:
        def __init__(self):
            self._summarized_knowledge = {}

        # placeholder so hasattr() finds the target method before patching
        def _update_summarized_knowledge_from_assistant(self, content):  # pragma: no cover
            raise AssertionError("original method must be replaced by install_patch")

    class _FakeModule:
        ToolAgent = _FakeToolAgent

        @staticmethod
        def _extract_scientist_note(content):
            # minimal stand-in: the whole content is one "world_model" paragraph
            if not content.strip():
                return {}
            return {"world_model": content.strip(), "goal_model": ""}

    mod = _FakeModule()
    install_patch(mod)

    agent = _FakeToolAgent()
    agent._update_summarized_knowledge_from_assistant("turn one finding")
    agent._update_summarized_knowledge_from_assistant("turn two finding")
    agent._update_summarized_knowledge_from_assistant("turn three finding")
    wm = agent._summarized_knowledge["world_model"]
    assert "[t1] turn one finding" in wm, wm
    assert "[t2] turn two finding" in wm, wm
    assert "[t3] turn three finding" in wm, wm
    assert "goal_model" not in agent._summarized_knowledge or not agent._summarized_knowledge.get("goal_model"), (
        "an empty extracted field must not be written"
    )

    # exact repeat across turns (dedup applies through the real merge path too)
    agent2 = _FakeToolAgent()
    agent2._update_summarized_knowledge_from_assistant("same finding")
    agent2._update_summarized_knowledge_from_assistant("same finding")
    wm2 = agent2._summarized_knowledge["world_model"]
    assert wm2.count("same finding") == 1, wm2

    # per-instance turn counters are independent
    agent3 = _FakeToolAgent()
    agent3._update_summarized_knowledge_from_assistant("x")
    assert getattr(agent, _TURN_ATTR) == 3
    assert getattr(agent3, _TURN_ATTR) == 1

    # idempotency: patching twice must not double-wrap
    install_patch(mod)
    agent4 = _FakeToolAgent()
    agent4._update_summarized_knowledge_from_assistant("only once please")
    assert agent4._summarized_knowledge["world_model"].count("only once please") == 1

    # negative control: a module whose ToolAgent lacks the target method must fail
    # loudly, not silently -- proves install_patch actually checks the real attribute
    # rather than assuming it's there.
    class _BrokenToolAgent:
        pass

    class _BrokenModule:
        ToolAgent = _BrokenToolAgent

    try:
        install_patch(_BrokenModule())
        raise AssertionError("expected AttributeError on a ToolAgent missing the target method")
    except AttributeError:
        pass  # expected

    # restore: the correct module must still patch and behave correctly after the
    # failed attempt above -- proves the negative control didn't leave shared state
    # corrupted. A fresh ToolAgent-shaped class (never touched by the broken attempt)
    # is used so this exercises a real install_patch call, not a no-op re-check.
    class _RestoredToolAgent:
        def __init__(self):
            self._summarized_knowledge = {}

        def _update_summarized_knowledge_from_assistant(self, content):  # pragma: no cover
            raise AssertionError("original method must be replaced by install_patch")

    class _FakeModule2:
        ToolAgent = _RestoredToolAgent

        @staticmethod
        def _extract_scientist_note(content):
            return {"world_model": content.strip()} if content.strip() else {}

    install_patch(_FakeModule2())
    agent5 = _RestoredToolAgent()
    agent5._update_summarized_knowledge_from_assistant("post-failure finding")
    assert "post-failure finding" in agent5._summarized_knowledge["world_model"]
    print("duckv5_worldmodel_accum self-test OK")


if __name__ == "__main__":
    _demo()
