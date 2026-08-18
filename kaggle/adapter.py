"""The MyAgent adapter -- everything below the MARK is appended verbatim to
the generated bundle by `kaggle/bundle.py`. The imports here exist only so
this file stands alone for linting; the bundle provides its own.

The whole point: `compete.play` is the repo's real agent -- the rung
machinery that cleared ls20 7/7 plus the six whole-game drivers, all behind
one function that DRIVES an environment (step/reset). The Kaggle framework
inverts control: it calls `choose_action` once per move. Rather than rewrite
seven hundred measured lines as a state machine, `play` runs unchanged on a
worker thread against a PROXY environment whose `reset`/`step` block on a
queue; `choose_action` answers the queue. The logic that was swept seventeen
games clean is byte-identical in the notebook.
"""
from __future__ import annotations

import queue
import random
import threading
import time
from typing import Any

import numpy as np

from arcengine import FrameData, GameAction, GameState
from agents.agent import Agent

import compete

# --- BUNDLE BODY ---

# `GameAction(v)` does NOT work: the enum's `.value` is a property over a
# richer `_value_`, so lookup-by-value raises on every int. Map by iteration,
# the same pattern `compete.play` itself uses.
BY_VALUE = {int(a.value): a for a in GameAction}


class _Act:
    """What `play` sees in `env.action_space`: value, is_complex, set_data."""

    def __init__(self, value):
        self.value = int(value)
        self.data = None

    def is_complex(self):
        return BY_VALUE[self.value].is_complex()

    def set_data(self, d):
        self.data = dict(d)
        return self


class _Obs:
    """What `play` reads off a frame: .frame, .levels_completed, .state."""

    __slots__ = ("frame", "levels_completed", "state")

    def __init__(self, fd):
        self.frame = fd.frame
        self.levels_completed = fd.levels_completed
        self.state = fd.state


class _Proxy:
    """The environment `play` drives. Every call crosses to the framework
    thread through the agent's two queues and blocks until the resulting
    frame comes back."""

    def __init__(self, agent):
        self._agent = agent
        self._space = None

    @property
    def action_space(self):
        # Read by `play` right after its first reset(), by which point the
        # first real frame has arrived and named the game's actions.
        if self._space is None:
            avail = self._agent._avail or [1, 2, 3, 4]
            self._space = [_Act(v) for v in avail]
        return self._space

    def reset(self):
        return self._agent._exchange(("reset", None))

    def step(self, action, data=None):
        # `play` passes click coordinates the local wrapper's way (a `data`
        # kwarg) as well as the framework's way (`set_data` on the action);
        # this side needs them on the action, so fold the kwarg in.
        if data:
            action.set_data(data)
        return self._agent._exchange(("step", action))


class MyAgent(Agent):
    """compete.play on a worker thread; this class is only the pipe.

    Budgeted by CLOCKS, not by actions -- the first submission scored 0.11
    against a baseline cluster at ~1.56 (the official sample), and the
    sample's shape explains the gap: it sets MAX_ACTIONS = inf, bounds the
    whole run with an 8-hour is_done clock, and spends thousands of cheap
    actions per game, while this adapter capped itself at 2,600 actions of
    slow thinking.  So: `play` gets a wall-time slice per game, a cheap
    random mop-up gets the remainder (it can afford thousands of engine
    steps), a per-game clock ends the game, and a global clock drains
    whatever remains as time runs out.  Sized for the hidden set: 110 games
    x GAME_SECONDS ~ 7.3h inside the sample's own 8h envelope.

    HOW MUCH of that clock the mop-up should get is now MEASURED, and the
    answer inverts what v8 assumed.  Scores: v1 = 0.11, v7 = 0.10, v8 = 0.01.
    v8's only behavioural change was handing the mop-up roughly three times
    more clock (a 60s `play` slice on games no driver signature claims, versus
    v7's 180s) and making its bandit state-aware -- and it scored TEN TIMES
    WORSE.

    ⚠️ CORRECTED 2026-08-16: the sentence that used to sit here -- "so the mop-up
    is actively harmful relative to `compete.play`" -- was an INFERENCE FROM ONE
    SCORE presented as a measurement, and it is now refuted.  Measured with
    `kaggle_yield_probe.py` (a shadow-module patch of `compete.py` printing wall
    clock at every level-up; the file on disk is untouched, so it costs no sweep)
    on **ls20**, the only local game the GENERIC rungs clear with no driver and
    therefore the honest proxy for the hidden 110: levels land at 0.8s, 2.4s,
    6.4s, 16.1s and 47.8s -- **five of seven inside sixty seconds** -- and levels
    6 and 7 were still unreached when the probe was killed at 900s.  With
    GAME_SECONDS = 240 those two are unreachable under every variant, so v8's 60s
    slice, v7's 180s and v9-lite's 240s all score ls20 at FIVE.  **The slice is
    worth zero levels here**, and a ten-fold score drop cannot come from a change
    that costs nothing on the one game we can measure it on.

    So the cause of v8's 0.01 is UNKNOWN, and both stated explanations are dead:
    a proportional loss cannot produce 10x.  The shape that fits is a run that
    did not finish or a worker that died silently -- this repo has a recorded
    case of exactly that ("a 120s timeout killed the worker and the silent 5/7
    that resulted had no error anywhere"), and the same day this note was written
    the committed bundle was found to be embedding a STALE mirror.py.  A
    module/bundle mismatch produces per-game crashes, a random fallback, and no
    error at all.  v9-lite reverting v8's two additions is therefore a TEST as
    much as a fix: if it returns to ~0.10 the cause was inside v8 without our
    having to name it; if it stays at 0.01 the difference lies elsewhere.

    The claim-gated short slice is
    withdrawn: `play` owns the whole game clock on every game, claimed or not,
    and the mop-up exists only to keep the framework loop legal after `play`
    returns or dies.  Its bandit is back to v7's per-action global prior; the
    per-(frame-hash, action) table went with the hypothesis that motivated it."""

    MAX_ACTIONS = 200_000          # the real bounds are the clocks below
    GAME_SECONDS = 240             # play, then is_done ends the game
    PLAY_SECONDS = GAME_SECONDS    # play owns the clock -- see the docstring
    RUN_SECONDS = 8 * 3600 - 300   # global drain, same envelope as the sample
    _REPLY_TIMEOUT = 60            # worker's wait for its OWN reply -- normal
    #                                round-trip is well under a second; this
    #                                only bounds the abandoned-worker case
    #                                where nothing will ever answer again
    #                                (see adapter_hybrid.py's fix notes --
    #                                same mechanism, same remedy, this
    #                                adapter has no `_claimed` gate so it
    #                                applies to every game, not just some)
    _JOIN_TIMEOUT = 2.0            # cleanup()'s bounded join, purely for the
    #                                "did it actually die" log line
    _run_start = None              # stamped once by the first game's agent

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._req: queue.Queue = queue.Queue()
        self._rep: queue.Queue = queue.Queue()
        self._avail: list[int] = []
        self._pending = False    # a request was answered with an action and
        #                          its resulting frame is owed to the worker
        self._worker = None
        self._dead = False
        self._t0 = None          # first choose_action call, this game's clock
        self._stats = {}         # global bandit prior: value -> [tries, changes]
        self._last = None        # (value, frame bytes) of the last pick
        if MyAgent._run_start is None:
            MyAgent._run_start = time.time()
        random.seed(0xA5C ^ hash(self.game_id) % (1 << 30))

    # -- worker side ------------------------------------------------------
    def _exchange(self, msg):
        self._req.put(msg)
        # Normal round-trip (worker asks -> next choose_action delivers) is
        # sub-second. A reply that never comes means the framework loop has
        # already ended and nothing will ever service `self._req` again --
        # `is_done`'s delivery below covers the game's real last reply, but
        # `compete.play` doesn't know to stop there and asks for one more;
        # this timeout is what actually bounds that case instead of
        # blocking forever.
        try:
            return self._rep.get(timeout=self._REPLY_TIMEOUT)
        except queue.Empty:
            raise TimeoutError(
                "adapter: no reply -- framework loop has ended")

    def _run(self):
        try:
            compete.play(_Proxy(self))
        except Exception as e:      # a crash must never take the run down
            print(f"[bundle] play() died: {type(e).__name__}: {e}")
        finally:
            self._req.put(("done", None))

    # -- framework side ---------------------------------------------------
    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        done = latest_frame.state is GameState.WIN
        if not done:
            now = time.time()
            if (MyAgent._run_start is not None
                    and now - MyAgent._run_start > self.RUN_SECONDS):
                done = True
            elif self._t0 is not None and now - self._t0 > self.GAME_SECONDS:
                done = True
        if done and self._pending:
            # `Agent.main()` checks `is_done()` BEFORE calling `choose_action`
            # again, so once this returns True the reply this game's worker
            # is blocked on (delivered, normally, at the top of the NEXT
            # choose_action) would otherwise never be sent -- every claimed
            # or unclaimed game alike, since this adapter always starts the
            # worker. Deliver it here, unconditionally, before the
            # short-circuit -- root cause fix.
            self._rep.put(_Obs(latest_frame))
            self._pending = False
        return done

    def cleanup(self, *args: Any, **kwargs: Any) -> None:
        """Called by `Agent.main()` unconditionally after the loop exits --
        including the MAX_ACTIONS-cutoff path, which can end the loop without
        `is_done()` ever returning True. Backstop-deliver any still-pending
        reply (using the last frame the loop actually saw), then give the
        thread a short bounded join and log if it's still alive -- it will
        still die on its own via `_exchange`'s timeout, but this makes a
        leaked thread observable in the Kaggle log instead of silent."""
        super().cleanup(*args, **kwargs)
        if self._pending and self.frames:
            self._rep.put(_Obs(self.frames[-1]))
            self._pending = False
        if self._worker is not None:
            self._worker.join(timeout=self._JOIN_TIMEOUT)
            if self._worker.is_alive():
                print(f"[bundle] {self.game_id}: worker thread still alive "
                      f"after cleanup join (times out on its own in "
                      f"{self._REPLY_TIMEOUT}s)")

    def _values(self, latest_frame) -> list[int]:
        out = []
        for a in latest_frame.available_actions or []:
            v = int(getattr(a, "value", a))
            if v > 0 and v in BY_VALUE and not BY_VALUE[v].is_complex():
                out.append(v)
        return out or [1, 2, 3, 4]

    def choose_action(
        self, frames: list[FrameData], latest_frame: FrameData
    ) -> GameAction:
        if self._t0 is None:
            self._t0 = time.time()
        if latest_frame.available_actions:
            self._avail = [int(getattr(a, "value", a))
                           for a in latest_frame.available_actions]
        if self._worker is None:
            self._worker = threading.Thread(target=self._run, daemon=True)
            self._worker.start()
        if self._pending:
            self._rep.put(_Obs(latest_frame))
            self._pending = False
        if not self._dead:
            # play's slice is PLAY_SECONDS of wall time, which is the WHOLE
            # game clock: v8 shortened it to 60s on games no driver signature
            # claimed, handing the difference to the mop-up, and scored 0.01
            # against v7's 0.10.  The get timeout shrinks with the slice, so
            # one long planner round (ls20's patrol thinks for minutes) cannot
            # overrun it; on expiry the worker is parked mid-block (daemon
            # thread, never joined) and the mop-up keeps the loop legal for
            # whatever is left.
            left = self.PLAY_SECONDS - (time.time() - self._t0)
            if left <= 0:
                self._dead = True
            else:
                try:
                    kind, payload = self._req.get(timeout=left)
                except queue.Empty:
                    kind = "done"
                if kind == "reset":
                    self._pending = True
                    return GameAction.RESET
                if kind == "step":
                    self._pending = True
                    ga = BY_VALUE[payload.value]
                    if ga.is_complex():
                        ga.set_data(payload.data or {"x": 32, "y": 32})
                    return ga
                self._dead = True     # play returned or timed out
        # Mop-up keeps the framework loop legal after `play` returns or its
        # slice expires -- nothing more.  It is v7's plain per-action bandit,
        # weight (changes+1)/(tries+2); the per-(frame-hash, action) table is
        # gone with the hypothesis that motivated it (see the class docstring:
        # v8 gave this code more clock and the score fell from 0.10 to 0.01).
        # The click, where the game has one, is a candidate (value 0) aiming
        # at a random cell.
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            self._last = None
            return GameAction.RESET
        fb = np.asarray(latest_frame.frame, dtype=np.int8).tobytes() \
            if latest_frame.frame else b""
        if self._last is not None:
            v0, fb0 = self._last
            st = self._stats.setdefault(v0, [0, 0])
            st[0] += 1
            st[1] += fb != fb0
        cands = self._values(latest_frame)
        if any(int(getattr(a, "value", a)) == 6
               for a in latest_frame.available_actions or []):
            cands = cands + [0]
        w = []
        for v in cands:
            src = self._stats.get(v, [0, 0])
            w.append((src[1] + 1) / (src[0] + 2))
        pick = random.choices(cands, weights=w)[0]
        self._last = (pick, fb)
        if pick == 0:
            ga = BY_VALUE[6]
            ga.set_data({"x": random.randrange(64), "y": random.randrange(64)})
            return ga
        return BY_VALUE[pick]
