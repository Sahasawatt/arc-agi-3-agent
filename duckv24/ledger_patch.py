# duckv24 — B32: the untried-ledger nudge.
#
# WHY (notes/R28-goal-model-audit.md): 4/5 stuck levels held a wrong or never-formed
# goal model, and 3/5 of the CLEARS trace to a probe taken before the theory was
# finished (ft09's clearer clicked a square at step 4; its stuck run theorized for
# 24 turns and never clicked anything). This patch makes the harness COUNT what has
# never been tried on the current level and say so, through the same hint channel
# the animation nudge uses — the one channel measured obeyed (sk48: 7/7).
#
# SEAM: ToolAgent._animation_hint_line(self, previous_step_summary, current_level)
# is called exactly once per analysis turn inside _build_user_prompt (tool_agent.py
# ~1448), receives the executed-action summary, and its return value is appended to
# the user prompt. Wrapping it adds the ledger line with zero structural change.
# Action strings come from solver._format_action_display: "MOUSE(row=R, col=C)" for
# clicks, bare model action names otherwise.
#
# CADENCE: fires at analysis turns 8, 16, 24, ... on the SAME level, only while
# something valid remains untried. Same family as the animation hint (periodic,
# stuck-gated), NOT the v16 every-turn info push that measured in-band-worse.
import re as _re

import inference.agent.tool_agent as _ta

_orig_animation_hint_line = _ta.ToolAgent._animation_hint_line

_LEDGER_FIRE_EVERY = 8
_MOUSE_RE = _re.compile(r"MOUSE\(row=(\d+),\s*col=(\d+)\)")


def _ledger_state(self):
    st = getattr(self, "_duckv24_ledger", None)
    if st is None:
        st = {"level": None, "turns": 0, "tried": set(), "cells": set()}
        self._duckv24_ledger = st
    return st


def _ledger_hint_line(self, previous_step_summary, current_level):
    base = _orig_animation_hint_line(self, previous_step_summary, current_level)
    st = _ledger_state(self)
    if st["level"] != current_level:
        st["level"] = current_level
        st["turns"] = 0
        st["tried"] = set()
        st["cells"] = set()
    st["turns"] += 1
    for raw in (previous_step_summary or {}).get("executed_actions") or []:
        s = str(raw)
        typ = s.split("(", 1)[0].strip()
        if typ:
            st["tried"].add(typ)
        m = _MOUSE_RE.search(s)
        if m:
            st["cells"].add((int(m.group(1)), int(m.group(2))))

    valid = [str(v).strip() for v in (getattr(self, "_current_valid_actions", None) or []) if str(v).strip()]
    untried = sorted(v for v in valid if v.split("(", 1)[0] not in st["tried"])
    if not untried or st["turns"] < _LEDGER_FIRE_EVERY or st["turns"] % _LEDGER_FIRE_EVERY:
        return base

    tried_txt = ", ".join(sorted(st["tried"])) if st["tried"] else "none"
    note = (
        f"Probe ledger for this level: {st['turns']} analysis turns so far; "
        f"actions tried: {tried_txt}; NEVER tried: {', '.join(untried)}"
    )
    if "MOUSE" in valid:
        note += f"; distinct cells clicked: {len(st['cells'])}"
    note += (
        ". One cheap probe of an untried action, followed by reading the diff, "
        "often reveals the mechanic faster than more analysis of the current theory."
    )
    return f"{base}\n{note}" if base else note


def apply():
    _ta.ToolAgent._animation_hint_line = _ledger_hint_line
    return "duckv24: untried-ledger nudge armed on ToolAgent._animation_hint_line"


# ---- teeth: drive the wrapper directly with a fake self; no harness needed ----
def _teeth():
    class _Fake:
        _current_valid_actions = ["UP", "DOWN", "MOUSE", "SPACE"]

        def _base(self, summary, level):
            return ""

    fake = _Fake()
    # bind the original to a stub returning "" so only the ledger logic is under test
    global _orig_animation_hint_line
    saved = _orig_animation_hint_line
    _orig_animation_hint_line = _Fake._base
    try:
        out = []
        for turn in range(1, 17):
            summary = {"executed_actions": ["UP"] if turn > 1 else []}
            out.append(_ledger_hint_line(fake, summary, 1))
        # turns 1-7: silent; turn 8: fires naming untried DOWN/MOUSE/SPACE; turn 9-15 silent; 16 fires
        if any(out[:7]):
            raise AssertionError("duckv24 TEETH FAIL: ledger fired before the cadence floor")
        if not out[7] or "NEVER tried: DOWN, MOUSE, SPACE" not in out[7]:
            raise AssertionError(f"duckv24 TEETH FAIL: turn-8 line wrong: {out[7]!r}")
        if "distinct cells clicked: 0" not in out[7]:
            raise AssertionError("duckv24 TEETH FAIL: mouse cell count missing while MOUSE is valid")
        if any(out[8:15]):
            raise AssertionError("duckv24 TEETH FAIL: fired between cadence points")
        if not out[15]:
            raise AssertionError("duckv24 TEETH FAIL: turn-16 repeat missing")

        # level transition resets the ledger
        first = _ledger_hint_line(fake, {"executed_actions": ["SPACE"]}, 2)
        if first:
            raise AssertionError("duckv24 TEETH FAIL: ledger did not reset on level change")
        st = fake._duckv24_ledger
        if st["level"] != 2 or st["turns"] != 1 or st["tried"] != {"SPACE"}:
            raise AssertionError(f"duckv24 TEETH FAIL: reset state wrong: {st}")

        # mouse cells accumulate and everything-tried silences the nudge
        fake2 = _Fake()
        for turn in range(1, 9):
            _ledger_hint_line(
                fake2,
                {"executed_actions": ["MOUSE(row=3, col=7)", "UP", "DOWN", "SPACE"]},
                1,
            )
        if fake2._duckv24_ledger["cells"] != {(3, 7)}:
            raise AssertionError("duckv24 TEETH FAIL: mouse cell not parsed")
        # all four types tried -> untried empty -> no fire even at cadence
        out8 = _ledger_hint_line(fake2, {"executed_actions": []}, 1)  # turn 9 -> not cadence anyway
        for turn in range(10, 17):
            out8 = _ledger_hint_line(fake2, {"executed_actions": []}, 1)
        if out8:
            raise AssertionError("duckv24 TEETH FAIL: fired with nothing untried")
    finally:
        _orig_animation_hint_line = saved


_teeth()
