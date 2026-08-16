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
    WORSE.  So the mop-up is actively harmful relative to `compete.play`, not
    a cheap way to spend leftover time, and the claim-gated short slice is
    withdrawn: `play` owns the whole game clock on every game, claimed or not,
    and the mop-up exists only to keep the framework loop legal after `play`
    returns or dies.  Its bandit is back to v7's per-action global prior; the
    per-(frame-hash, action) table went with the hypothesis that motivated it."""

    MAX_ACTIONS = 200_000          # the real bounds are the clocks below
    GAME_SECONDS = 240             # play, then is_done ends the game
    PLAY_SECONDS = GAME_SECONDS    # play owns the clock -- see the docstring
    RUN_SECONDS = 8 * 3600 - 300   # global drain, same envelope as the sample
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
        return self._rep.get()

    def _run(self):
        try:
            compete.play(_Proxy(self))
        except Exception as e:      # a crash must never take the run down
            print(f"[bundle] play() died: {type(e).__name__}: {e}")
        finally:
            self._req.put(("done", None))

    # -- framework side ---------------------------------------------------
    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        if latest_frame.state is GameState.WIN:
            return True
        now = time.time()
        if (MyAgent._run_start is not None
                and now - MyAgent._run_start > self.RUN_SECONDS):
            return True
        return self._t0 is not None and now - self._t0 > self.GAME_SECONDS

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
