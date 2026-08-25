# duckv26 cell 12 — B38: the family brake.
#
# WHY (notes/R38-the-agent-locks-onto-one-action-family.md): 1,920 of 2,637 actions
# (73%) fire after a game's LAST level-up, and the tail is not flailing — it is one
# locked action family. vc33 spends 101 clicks walking row=56; tr87 fires a single
# family 226 times in a row. B29's brake cannot see it: it keys on an exact
# (level, board, action) repeat and vc33 never repeats an action exactly
# (col=46, then col=12, then col=50 — three distinct actions, one hypothesis).
# Measured reach of an exact-action brake, R32: 0.49% of decisions.
#
# SEAM: NoopGuard is consulted on BOTH block paths in tool_agent._handle_action —
# the single-action pre-check (~:1779) and the per-action batch loop (~:1858) — and
# each already carries the refusal back to the model as stop_reason/stop_detail,
# which reaches it twice (the sandbox-visible last_action_result, and the next
# turn's summary line). Wrapping the guard therefore adds a second block reason
# with ZERO structural change and no new plumbing. It is also why this is not a
# prompt nudge: the action does not happen, so there is nothing to disobey — the
# failure mode B32 measured at 52% obedience.
#
# RULE: per game, count fires per action FAMILY since the last level-up. A family
# is (MOUSE, row) for clicks and the action name otherwise. At K the family is
# refused until a level-up resets the ledger.
#
# K=20 IS MEASURED, NOT CHOSEN (R38 §3, swept over the clock2x corpus):
#   k=10 -> speaks on 45.5% of decisions, DESTROYS 5 of 30 real level-ups
#   k=15 -> 34.2%, destroys 5 of 30
#   k=20 -> 25.9%, destroys 0 of 30      <- deepest family count at a real level-up is 19
#   k=30 -> 17.0%, destroys 0 of 30
# The margin is ONE, on n=1 run and 30 level-ups. DUCKV26_BRAKE_K overrides it;
# k=25/30 are the documented fallbacks if a wider sweep moves the 19.
import os as _os
import re as _re

import inference.agent.noop_guard as _ng

_K = max(1, int(_os.environ.get("DUCKV26_BRAKE_K", "20")))
_MOUSE_RE = _re.compile(r"^MOUSE\(row=(\d+),\s*col=(\d+)\)")

_orig_is_known_noop = _ng.NoopGuard.is_known_noop
_orig_observe = _ng.NoopGuard.observe


def _family(action_sig):
    """(MOUSE, row) for a click, the bare action name otherwise, or None."""
    s = str(action_sig or "").strip()
    if not s:
        return None
    m = _MOUSE_RE.match(s)
    if m:
        return ("MOUSE_ROW", int(m.group(1)))
    return ("KEY", s.split("(", 1)[0].strip() or s)


def _ledger(self, level):
    """Per-level fire counts. A level-up empties it — that is the whole reset rule."""
    st = getattr(self, "_duckv26", None)
    if st is None or st["level"] != level:
        st = {"level": level, "fires": {}, "braked": 0}
        self._duckv26 = st
    return st


def _is_known_noop(self, level, board_before_sig, action_sig):
    # B29 keeps priority: an exact known no-op is refused for its own reason, and
    # this brake never has to re-derive that case.
    if _orig_is_known_noop(self, level, board_before_sig, action_sig):
        return True
    fam = _family(action_sig)
    if fam is None:
        return False
    st = _ledger(self, level)
    if st["fires"].get(fam, 0) >= _K:
        st["braked"] += 1
        return True
    return False


def _observe(self, *, level, board_before_sig, action_sig, board_changed, animated=False):
    _orig_observe(self, level=level, board_before_sig=board_before_sig,
                  action_sig=action_sig, board_changed=board_changed, animated=animated)
    # Count every EXECUTED action, whether or not it moved the board: the lock this
    # brake exists to break is made of actions that mostly do move something (vc33's
    # clicks repaint a row) and get nowhere. Counting only no-ops would rebuild B29.
    fam = _family(action_sig)
    if fam is None:
        return
    st = _ledger(self, level)
    st["fires"][fam] = st["fires"].get(fam, 0) + 1


_ng.NoopGuard.is_known_noop = _is_known_noop
_ng.NoopGuard.observe = _observe
print(f"duckv26: family brake armed, K={_K}", flush=True)
