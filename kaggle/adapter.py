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
    """compete.play on a worker thread; this class is only the pipe."""

    MAX_ACTIONS = 2600   # play's own budget is 2000; resets and slack on top

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._req: queue.Queue = queue.Queue()
        self._rep: queue.Queue = queue.Queue()
        self._avail: list[int] = []
        self._pending = False    # a request was answered with an action and
        #                          its resulting frame is owed to the worker
        self._worker = None
        self._dead = False
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
        return latest_frame.state is GameState.WIN

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
            try:
                # ls20's level-6 patrol planner legitimately thinks for
                # minutes on one round -- a 120s timeout here killed the
                # worker mid-level and handed the rest to the random
                # fallback (measured: fps 6.9 -> 1.7 at count ~660, levels
                # 6-7 never played). The timeout is only a backstop against
                # a true hang; Kaggle's own wall clock bounds the run.
                kind, payload = self._req.get(timeout=1800)
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
            self._dead = True     # play returned or timed out: budget spent
        # Fallback keeps the framework loop legal until MAX_ACTIONS.
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            return GameAction.RESET
        return BY_VALUE[random.choice(self._values(latest_frame))]
