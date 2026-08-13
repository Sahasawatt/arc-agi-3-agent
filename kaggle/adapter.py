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
    x GAME_SECONDS ~ 7.3h inside the sample's own 8h envelope."""

    MAX_ACTIONS = 200_000          # the real bounds are the clocks below
    PLAY_SECONDS = 180             # compete.play's thinking slice per game
    GAME_SECONDS = 240             # play + random mop-up, then is_done
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
            # play's slice is PLAY_SECONDS of wall time.  The get timeout
            # shrinks with it, so one long planner round (ls20's patrol
            # thinks for minutes) cannot overrun the slice; on expiry the
            # worker is parked mid-block (daemon thread, never joined) and
            # the cheap random mop-up spends the rest of the game clock.
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
        # Random mop-up keeps the framework loop legal until the game clock
        # ends the game (is_done); it affords thousands of engine steps.
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            return GameAction.RESET
        return BY_VALUE[random.choice(self._values(latest_frame))]
