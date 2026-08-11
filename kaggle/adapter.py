"""The MyAgent adapter -- everything below the MARK is appended verbatim to
the generated bundle by `kaggle/bundle.py`. The imports here exist only so
this file stands alone for linting; the bundle provides its own.
"""
from __future__ import annotations

import random
from typing import Any

import numpy as np

from arcengine import FrameData, GameAction, GameState
from agents.agent import Agent

import cover
import swap
import haul
import maze
import dial
import skewer

# --- BUNDLE BODY ---

# Cascade order is load-bearing and mirrors `compete.play` / `sigs.py`:
# `dial` before `cover` because cover's signature also fires on tr87
# (the one contested board), everything else is disjoint by measurement
# (`results/sig-sweep.txt`).
DRIVERS = [
    ("dial", dial.signature, dial.Dial),
    ("cover", cover.signature, cover.Cover),
    ("swap", swap.signature, swap.Swap),
    ("haul", haul.signature, haul.Haul),
    ("maze", maze.signature, maze.Maze),
    ("skewer", skewer.signature, skewer.Skewer),
]


# `GameAction(v)` does NOT work: the enum's `.value` is a property over a
# richer `_value_`, so lookup-by-call raises on every int. Map by iteration,
# the same pattern `compete.play` uses.
BY_VALUE = {int(a.value): a for a in GameAction}


def _grid(latest_frame):
    """The last animation layer as int ndarray, or None -- the engine hands
    back empty frames mid-level and at transitions."""
    f = latest_frame.frame
    if not f:
        return None
    g = np.array(f)
    return None if g.ndim < 2 or g.size == 0 else g[-1]


class MyAgent(Agent):
    """Whole-game drivers behind their signatures; random otherwise."""

    MAX_ACTIONS = 2000   # the per-game budget the local sweeps run at

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.driver = None
        self.driver_name = None
        self.sig_checked = False
        random.seed(0x5EED ^ hash(self.game_id) % (1 << 30))

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        return latest_frame.state is GameState.WIN

    def _values(self, latest_frame) -> list[int]:
        """Simple-action values this game offers, RESET excluded."""
        out = []
        for a in latest_frame.available_actions or []:
            v = getattr(a, "value", a)
            v = int(v) if not isinstance(v, int) else v
            if v > 0 and v in BY_VALUE and not BY_VALUE[v].is_complex():
                out.append(v)
        return out or [1, 2, 3, 4]

    def choose_action(
        self, frames: list[FrameData], latest_frame: FrameData
    ) -> GameAction:
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            return GameAction.RESET
        g = _grid(latest_frame)
        # One signature pass, on the first real frame -- the same latch point
        # `compete.play` uses (the reset frame).
        if not self.sig_checked and g is not None:
            self.sig_checked = True
            for name, sig, cls in DRIVERS:
                try:
                    if sig(g):
                        self.driver = cls(self._values(latest_frame))
                        self.driver_name = name
                        break
                except Exception:
                    continue
        v = None
        if self.driver is not None and g is not None:
            try:
                v = self.driver.act(g, latest_frame.levels_completed)
            except Exception:
                v = None   # a driver crash must never kill the run
        if v is None:
            v = random.choice(self._values(latest_frame))
        action = BY_VALUE[int(v)]
        action.reasoning = f"{self.driver_name or 'random'}: {v}"
        return action
