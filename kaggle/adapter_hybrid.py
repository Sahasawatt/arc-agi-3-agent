"""The HYBRID MyAgent -- everything below the MARK is appended verbatim to the
hybrid bundle by `kaggle/bundle_hybrid.py`.  The imports here exist only so
this file lints standalone; the bundle provides its own.

Why this file exists, in one measurement.  Our submissions score **0.11 (v1),
0.10 (v7), 0.01 (v8)** while the competition's own published baseline --
StochasticGoose, Tufa Labs, shipped as a `%%writefile` cell in the starter
kit's reference notebook -- sits at **~1.56**.  The gap is not tuning.  The
sample learns ONLINE, per game, which of ACTION1-5 *and which of the 4,096
click coordinates* change the frame; a uniform random click on a click-driven
game is worth ~nothing, and a learned coordinate head is not.

So the hybrid inverts which agent is the default: the sample plays every game,
and `compete.play` -- the repo's real agent, with the fourteen measured
whole-game drivers behind it -- takes over ONLY where a driver signature
claims the reset frame.  Everywhere else the sample plays unmolested.

The honest caveat, stated because it decides whether this is worth submitting:
**on the 110 HIDDEN games the drivers claim close to nothing** (v1 without them
scored 0.11 and v7 with fourteen scored 0.10), so this hybrid's expected score
is close to the sample's own.  It is a better score, not a better agent, and
the difference matters when deciding what to submit.

One design choice is genuinely unmeasurable from here and is left as a knob.
The sample's `is_done` is WIN or **8 hours, per game** -- with `MAX_ACTIONS`
infinite it will happily spend the whole run on the games it reaches and never
visit the rest, and it scores 1.56 doing exactly that.  Our adapter instead
gives every game GAME_SECONDS and drains the run at RUN_SECONDS, sized so all
110 get a turn.  Which is better cannot be settled without submissions we do
not have (quota is 1/day), so: the per-game clock is kept (coverage is the
thing our structure is for), and `GAME_SECONDS` is the one number to move if a
future run suggests the sample needs longer to learn a single board.
"""
from __future__ import annotations

import queue
import random
import threading
import time
from typing import Any

import numpy as np

from arcengine import FrameData, GameAction, GameState

import compete
import cover, swap, haul, maze, dial, skewer, tape, bridge, sorter
import ferry, claw, mirror, twin, roller

# the bundle defines this from the extracted sample module
GooseAgent = object

# --- BUNDLE BODY ---

# `GameAction(v)` does NOT work: the enum's `.value` is a property over a
# richer `_value_`, so lookup-by-value raises on every int. Map by iteration,
# the same pattern `compete.play` itself uses.
BY_VALUE = {int(a.value): a for a in GameAction}

SIGNATURES = (cover.signature, swap.signature, haul.signature, maze.signature,
              dial.signature, skewer.signature, tape.signature,
              bridge.signature, sorter.signature, ferry.signature,
              claw.signature, mirror.signature, twin.signature,
              roller.signature)


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


class MyAgent(GooseAgent):
    """The sample agent, with `compete.play` pre-empting it on claimed games.

    Inheriting rather than composing is deliberate: two `Agent` instances for
    one game would each register their own recorder and frame history, and the
    thing we want is one agent whose ACTION SOURCE switches.  So this class is
    the sample, plus the worker/proxy pipe from `kaggle/adapter.py`, and its
    `choose_action` answers from `play` while `play` owns the game and
    delegates to `super()` -- the sample -- the moment it does not.

    Note what is NOT here: v8's bandit mop-up.  It was measured harmful (its
    only change from v7 was giving itself three times more clock, and the
    score fell 0.10 -> 0.01), and in this design the sample IS the fallback,
    which is the whole point.
    """

    MAX_ACTIONS = 200_000          # the real bounds are the clocks below
    PLAY_SECONDS = 180             # compete.play's slice on a CLAIMED game
    GAME_SECONDS = 240             # then is_done ends the game -- see the
    #                                module docstring: this is the knob that
    #                                trades coverage of all 110 games against
    #                                the sample's time to learn one board
    RUN_SECONDS = 8 * 3600 - 300   # global drain, same envelope as the sample
    _REPLY_TIMEOUT = 60            # worker's wait for its OWN reply -- normal
    #                                round-trip is well under a second; this
    #                                only bounds the abandoned-worker case
    #                                where nothing will ever answer again
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
        self._dead = False       # play is finished with this game
        self._t0 = None          # first choose_action call, this game's clock
        self._claimed = None     # does any driver signature claim this game?
        self._handed_over = False
        if MyAgent._run_start is None:
            MyAgent._run_start = time.time()

    # -- worker side ------------------------------------------------------
    def _exchange(self, msg):
        self._req.put(msg)
        # Normal round-trip (worker asks -> next choose_action delivers) is
        # sub-second. A reply that never comes means the framework loop has
        # already ended and nothing will ever service `self._req` again --
        # `is_done`'s delivery below covers the game's real last reply, but
        # `compete.play` doesn't know to stop there and asks for one more
        # (see adapter_hybrid.py's fix notes); this timeout is what actually
        # bounds that case instead of blocking forever.
        try:
            return self._rep.get(timeout=self._REPLY_TIMEOUT)
        except queue.Empty:
            raise TimeoutError(
                "adapter_hybrid: no reply -- framework loop has ended")

    def _run(self):
        try:
            compete.play(_Proxy(self))
        except Exception as e:      # a crash must never take the run down
            print(f"[hybrid] play() died: {type(e).__name__}: {e}")
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
            # choose_action) would otherwise never be sent. Deliver it here,
            # unconditionally, before the short-circuit -- root cause fix.
            self._rep.put(_Obs(latest_frame))
            self._pending = False
        return done

    def cleanup(self, *args: Any, **kwargs: Any) -> None:
        """Called by `Agent.main()` unconditionally after the loop exits --
        including the MAX_ACTIONS-cutoff path, which can end the loop without
        `is_done()` ever returning True. Backstop-deliver any still-pending
        reply (using the last frame the loop actually saw) so an abandoned
        worker isn't left holding the bag purely on that path, then give the
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
                print(f"[hybrid] {self.game_id}: worker thread still alive "
                      f"after cleanup join (times out on its own in "
                      f"{self._REPLY_TIMEOUT}s)")

    def _claims(self, latest_frame) -> bool:
        try:
            f = np.array(latest_frame.frame)
            g = f[-1] if f.ndim >= 2 and f.size else None
        except Exception:
            return False
        if g is None:
            return False
        try:
            return any(s_(g) for s_ in SIGNATURES)
        except Exception:
            return False    # fail to the SAMPLE, which is the better default

    def choose_action(
        self, frames: list[FrameData], latest_frame: FrameData
    ) -> GameAction:
        if self._t0 is None:
            self._t0 = time.time()
        if latest_frame.available_actions:
            self._avail = [int(getattr(a, "value", a))
                           for a in latest_frame.available_actions]
        if self._claimed is None:
            self._claimed = self._claims(latest_frame)
            print(f"[hybrid] {self.game_id}: driver claim = {self._claimed}")

        if self._claimed and not self._dead:
            if self._worker is None:
                self._worker = threading.Thread(target=self._run, daemon=True)
                self._worker.start()
            if self._pending:
                self._rep.put(_Obs(latest_frame))
                self._pending = False
            # The get timeout shrinks with the slice, so one long planner
            # round (ls20's patrol thinks for minutes) cannot overrun it; on
            # expiry the worker is parked mid-block (daemon thread, never
            # joined) and the sample takes the rest of the game clock.
            left = self.PLAY_SECONDS - (time.time() - self._t0)
            if left > 0:
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
            self._dead = True     # play returned, crashed, or ran out of slice

        if not self._handed_over:
            self._handed_over = True
            # The sample credits a frame change to the action IT last chose.
            # Handing it a board that `play` has been moving would book one
            # false observation, so clear its last-action memory at the seam.
            for attr in ("prev_frame", "prev_action_idx"):
                if hasattr(self, attr):
                    setattr(self, attr, None)
        return super().choose_action(frames, latest_frame)
