"""Depth-aware per-game time reallocation for the ARC-AGI-3 duck harness
(duckv4, lever b).

R1 forensics: every one of 25 games in the measured commit run hit the SAME
flat `max_runtime_s_per_game` clock (solver.py:213-217) and none crashed or
won -- action budget is entirely a function of per-action latency against a
flat per-game deadline (results/wayfinder/R1-forensics.md Sec 3). ft09, the
run's best game (score 28.57, 3/6 levels), was 2 actions into level 4 when
its OWN clock cut it off (Bucket A, "clock-limited, not skill-limited",
Sec 4). Meanwhile 14 of 25 games were "thrashing" (>=2x a human's action
budget on their CURRENT level, still 0 progress, Bucket C) and burn the
same flat clock for no return.

R2's own top-5 list does not include this lever standalone (SS(h): "no
scoring-aware behaviour found ... a scheduling change ... is structural"),
and flags `concurrency`/`max_runtime_s_per_game` as LOAD-BEARING for the 9h
envelope: their product across `ceil(games/concurrency)` waves is the
*entire* enforcement mechanism, because the soft-deadline graceful-drain
path is dead code on `TRUE_SUBMISSION` (R2, opening finding). So this module
changes NEITHER constant. Instead it gives each `_HarnessGameSession` an
EFFECTIVE deadline, `solver.max_runtime_s_per_game + delta`, where every
`delta` is drawn from a shared pool that can only ever be negative-or-zero
in total: extension is funded exclusively by harvested slack from thrashing
games, capped per-game and capped system-wide. See BudgetReallocator's
docstring for the exact invariant and why it holds regardless of the
concurrency/wave regime the real 110-hidden-game run uses (a regime this
repo cannot execute or observe locally -- see the build report's risk list).
"""
from __future__ import annotations

import threading
import time
import weakref

REALLOC_INTERVAL_S = 120.0        # throttle: re-evaluate at most this often
THRASH_ACTION_FLOOR = 150         # actions burned at 0 levels before "thrashing"
                                   # (R1 Sec 4: zero-level games ranged 34-418
                                   # actions; 150 sits above the low outliers
                                   # cd82/dc22/vc33/g50t/ka59 -- Bucket B/ambiguous
                                   # -- and below the clear Bucket C thrashers)
SHRINK_STEP_S = 300.0             # seconds trimmed off a thrashing game per tick
MIN_BUDGET_FRACTION = 0.5         # a thrashing game's deadline floor, as a
                                   # fraction of ITS OWN original budget
EXTEND_STEP_S = 300.0             # seconds granted to a leveling game per tick
MAX_EXTENSION_PER_GAME_S = 600.0  # hard per-game ceiling on total extension, ever
TOTAL_POOL_CAP_S = 600.0          # hard system-wide ceiling on cumulative seconds
                                   # granted, ever -- conservative against R2's
                                   # measured ~720s of slack (31680s 4-wave
                                   # arithmetic vs a ~9h/32400s budget); NOT
                                   # re-derived against the real 110-game/9h
                                   # envelope, see build report risk list

_PATCH_MARKER = "_duckv4_realloc_patched"


def _levels_completed(session) -> int:
    try:
        return int(session.game.current_state.levels_completed)
    except Exception:
        return 0  # ponytail: mid-transition/odd state reads as "no progress yet",
                   # never crashes the reallocation tick (Principle 5: failure-aware)


def _action_count(session) -> int:
    try:
        return int(session.action_count)
    except Exception:
        return 0


class BudgetReallocator:
    """One instance per run (module-level singleton via install_patch).
    Thread-safe: sessions run one-per-thread on a ThreadPoolExecutor
    (solver.py:884-887) and can all call in at once.

    Invariant, enforced by construction and asserted in the self-test below:
    at any point in time, `sum(all session deltas) <= 0` -- extension is only
    ever paid for out of a pool that shrink harvests, so the aggregate of all
    effective deadlines can never exceed the aggregate of the original static
    ones. Additionally no single session's delta can ever exceed
    `+MAX_EXTENSION_PER_GAME_S` or go below `-(1-MIN_BUDGET_FRACTION)*base`,
    and the cumulative seconds ever granted across the whole run is capped at
    `TOTAL_POOL_CAP_S` regardless of how many games level up.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # Start the throttle window at construction time, not 0.0 -- otherwise
        # the very first call (arbitrary, platform-dependent monotonic clock
        # reference) would almost always fire an immediate tick.
        self._last_tick = time.monotonic()
        self._pool = 0.0            # harvested, unspent slack (seconds), always >= 0
        self._total_granted = 0.0   # cumulative seconds ever granted, monotonic
        # _HarnessGameSession is UNHASHABLE (dataclass with eq=True, not frozen),
        # so it cannot key a WeakKeyDictionary -- that crashed every game in the
        # v1 kernel run ("TypeError: unhashable type: '_HarnessGameSession'").
        # Key by id() with a strong ref instead: one entry per game per run,
        # process-lifetime, so the strong ref leaks nothing that matters.
        self._sessions = {}  # id(session) -> (session, entry)

    def _entry(self, session):
        rec = self._sessions.get(id(session))
        if rec is None:
            base = float(session.solver.max_runtime_s_per_game or 0.0)
            entry = {"delta": 0.0, "last_levels": _levels_completed(session), "base": base}
            self._sessions[id(session)] = (session, entry)
            return entry
        return rec[1]

    def effective_deadline(self, session) -> float:
        base = float(session.solver.max_runtime_s_per_game)
        with self._lock:
            entry = self._entry(session)
            self._tick_locked()
            return base + entry["delta"]

    def _tick_locked(self) -> None:
        now = time.monotonic()
        if now - self._last_tick < REALLOC_INTERVAL_S:
            return
        self._last_tick = now

        snapshot = []
        for session, entry in list(self._sessions.values()):
            levels = _levels_completed(session)
            actions = _action_count(session)
            leveled = levels > entry["last_levels"]
            thrashing = levels == 0 and actions >= THRASH_ACTION_FLOOR
            snapshot.append((entry, leveled, thrashing))
            entry["last_levels"] = levels

        # 1) harvest slack from thrashing sessions into the shared pool first,
        #    so any grant below is always funded by an actual shrink.
        for entry, _leveled, thrashing in snapshot:
            if not thrashing or entry["base"] <= 0:
                continue
            floor = -entry["base"] * (1.0 - MIN_BUDGET_FRACTION)
            room = entry["delta"] - floor
            step = min(SHRINK_STEP_S, max(0.0, room))
            if step > 0:
                entry["delta"] -= step
                self._pool += step

        # 2) grant pool to sessions that just leveled up, capped per-game and
        #    system-wide -- never spends more than the pool holds.
        for entry, leveled, _thrashing in snapshot:
            if not leveled:
                continue
            if self._pool <= 0 or self._total_granted >= TOTAL_POOL_CAP_S:
                continue
            cap_room = MAX_EXTENSION_PER_GAME_S - entry["delta"]
            global_room = TOTAL_POOL_CAP_S - self._total_granted
            step = min(EXTEND_STEP_S, self._pool, max(0.0, cap_room), max(0.0, global_room))
            if step > 0:
                entry["delta"] += step
                self._pool -= step
                self._total_granted += step

    def total_delta(self) -> float:
        """Sum of every tracked session's delta -- must always be <= 0."""
        return sum(entry["delta"] for _s, entry in self._sessions.values())


def install_patch(solver_module) -> None:
    """Replace `_HarnessGameSession.runtime_limit_reached`/`timing_payload`
    so both consult a shared BudgetReallocator's effective deadline instead
    of the flat `solver.max_runtime_s_per_game`. `request_timeout_seconds`
    (solver.py:227-244) calls `self.timing_payload()` for its own remaining-
    time candidate, so patching `timing_payload` alone is enough to make the
    per-LLM-call timeout clamp respect the adjusted deadline too -- it is not
    patched separately. Idempotent."""
    cls = solver_module._HarnessGameSession
    if getattr(cls, _PATCH_MARKER, False):
        return

    reallocator = BudgetReallocator()

    def _patched_runtime_limit_reached(self):
        if self.solver.max_runtime_s_per_game is None:
            return False
        deadline = reallocator.effective_deadline(self)
        return (time.monotonic() - self.started_at) >= deadline

    def _patched_timing_payload(self):
        elapsed = max(0.0, time.monotonic() - self.started_at)
        if self.solver.max_runtime_s_per_game is None:
            remaining = None
        else:
            deadline = reallocator.effective_deadline(self)
            remaining = max(0.0, deadline - elapsed)
        return {"run_elapsed_seconds": elapsed, "time_remaining_seconds": remaining}

    setattr(cls, _PATCH_MARKER, True)
    cls.runtime_limit_reached = _patched_runtime_limit_reached
    cls.timing_payload = _patched_timing_payload
    cls._duckv4_reallocator = reallocator


def _demo() -> None:
    class _FakeState:
        def __init__(self, levels):
            self.levels_completed = levels

    class _FakeGame:
        def __init__(self, levels):
            self.current_state = _FakeState(levels)

    class _FakeSolver:
        def __init__(self, budget):
            self.max_runtime_s_per_game = budget

    class _FakeSession:
        # UNHASHABLE on purpose, matching the real _HarnessGameSession (a
        # dataclass with eq=True): the v1 kernel run crashed all 25 games on
        # exactly this property, and a hashable fake let it ship. This fake is
        # the regression teeth -- any future session-as-dict-key code dies here.
        __hash__ = None

        def __init__(self, budget, levels, actions):
            self.solver = _FakeSolver(budget)
            self.game = _FakeGame(levels)
            self._actions = actions
            self.started_at = time.monotonic()

        def __eq__(self, other):
            return self is other

        @property
        def action_count(self):
            return self._actions

    budget = 7920.0
    realloc = BudgetReallocator()

    leveling = _FakeSession(budget, levels=3, actions=44)    # ft09-shaped: making progress
    thrashing = _FakeSession(budget, levels=0, actions=418)  # m0r0-shaped: thrashing
    fair = _FakeSession(budget, levels=1, actions=59)        # untouched control

    for s in (leveling, thrashing, fair):
        realloc.effective_deadline(s)  # register + seed last_levels, no tick yet (throttled)

    assert realloc.effective_deadline(leveling) == budget, "no tick has run yet"

    # force a tick past the throttle, and simulate leveling's level-up
    realloc._last_tick = 0.0
    leveling.game.current_state.levels_completed = 4
    realloc.effective_deadline(leveling)  # this call's _tick_locked does the work

    d_level = realloc.effective_deadline(leveling) - budget
    d_thrash = realloc.effective_deadline(thrashing) - budget
    d_fair = realloc.effective_deadline(fair) - budget

    assert d_level > 0, f"a game that just leveled up should be granted extra time, got {d_level}"
    assert d_thrash < 0, f"a thrashing game should be shrunk, got {d_thrash}"
    assert d_fair == 0, f"an untouched fair game must keep its original budget, got {d_fair}"
    assert realloc.total_delta() <= 1e-9, f"total budget must never increase, got {realloc.total_delta()}"
    assert d_thrash >= -budget * (1.0 - MIN_BUDGET_FRACTION) - 1e-9, "shrink must respect its floor"

    # drive many ticks to prove the hard caps actually bind, with several
    # thrashing games funding one repeat leveler.
    realloc2 = BudgetReallocator()
    leveler = _FakeSession(budget, levels=1, actions=10)
    thrashers = [_FakeSession(budget, levels=0, actions=1000) for _ in range(5)]
    for s in [leveler] + thrashers:
        realloc2.effective_deadline(s)

    for tick in range(10):
        realloc2._last_tick = 0.0
        leveler.game.current_state.levels_completed += 1  # "levels up" every tick
        realloc2.effective_deadline(leveler)
        assert realloc2.total_delta() <= 1e-9, f"tick {tick}: total budget increased"

    d_leveler = realloc2.effective_deadline(leveler) - budget
    assert d_leveler <= MAX_EXTENSION_PER_GAME_S + 1e-9, f"per-game cap breached: {d_leveler}"
    assert realloc2._total_granted <= TOTAL_POOL_CAP_S + 1e-9, "system-wide pool cap breached"
    for t in thrashers:
        d_t = realloc2.effective_deadline(t) - budget
        assert d_t >= -budget * (1.0 - MIN_BUDGET_FRACTION) - 1e-9, f"thrash floor breached: {d_t}"

    # a session whose game state raises must not crash a tick (Principle 5)
    class _BrokenGame:
        @property
        def current_state(self):
            raise RuntimeError("mid-transition, no state yet")

    class _BrokenSession:
        def __init__(self, budget):
            self.solver = _FakeSolver(budget)
            self.game = _BrokenGame()
            self.started_at = time.monotonic()

        @property
        def action_count(self):
            raise RuntimeError("no action count yet either")

    broken = _BrokenSession(budget)
    realloc3 = BudgetReallocator()
    realloc3.effective_deadline(broken)
    realloc3._last_tick = 0.0
    realloc3.effective_deadline(broken)  # must not raise
    assert realloc3.effective_deadline(broken) == budget, "a broken session must not drift"

    # negative control: install_patch reads `solver_module._HarnessGameSession`
    # before touching anything -- a module missing that attribute (the shape
    # an upstream rename would take) must fail loudly, not silently no-op.
    class _ModuleMissingSession:
        pass

    try:
        install_patch(_ModuleMissingSession())
        raise AssertionError("expected AttributeError: module has no _HarnessGameSession")
    except AttributeError:
        pass  # expected: proves install_patch actually reads the real attribute name

    print("duckv4_reallocator self-test OK")


if __name__ == "__main__":
    _demo()
