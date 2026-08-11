"""bp35 seventh pass: THE CLICK, which has never been fired on this game.

`KeyError: 'x'` from ACTION6 is what a complex action answers when no
coordinates were set (`compete.py:1965` sets them via `set_data`), so every
earlier reading of "the click raises here, retire it" was measuring an
un-aimed press. This aims it.

One click per FRESH episode so no two readings share a board, over the
objects visible at reset, plus the same sweep after event #1 (where the
tape has put a 4-block group directly above the piece's chamber -- the
thing that blocks a second climb).

Controls in the same invocation: a click on the outer background (nothing
there) and a click repeated at one target that already answered, so a zero
is distinguishable from a broken call.
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece_x(g):
    ys, xs = np.nonzero((g == 9) | (g == 11))
    return int(xs.min()) if len(xs) else None


def flood_top(g):
    ys, _ = np.nonzero(g[:63] == 15)
    return int(ys.min()) if len(ys) else None


def click(env, A, x, y):
    """The local wrapper builds ActionInput from its OWN `data` kwarg
    (local_wrapper.py:234) and never reads the action's set_data -- which is
    why every click in this repo has arrived un-aimed and answered
    KeyError 'x' (compete.py:1965 sets it the ignored way)."""
    return env.step(A[6], data={"x": x, "y": y})


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

RESET_TARGETS = [
    (15, 3, "e-block, left column top"),
    (45, 3, "box interior, right column top"),
    (33, 15, "e-block, right column y13-17"),
    (45, 15, "e-block directly over the chute"),
    (33, 24, "big box interior above the chute"),
    (45, 33, "the chute itself"),
    (21, 39, "the piece"),
    (45, 50, "chamber floor, under the chute"),
    (2, 2, "outer background (control: expect nothing)"),
]

for pre, label, targets in [
    ([], "RESET", RESET_TARGETS),
    ([4] * 4, "AFTER EVENT #1 (piece x=44)",
     [(45, 33, "the 4-block group now above the ceiling"),
      (33, 33, "same group, left end"),
      (45, 50, "the chute now BELOW the piece"),
      (45, 39, "the piece"),
      (2, 2, "outer background (control)")]),
]:
    print(f"== click sweep, {label} ==")
    for x, y, what in targets:
        env = arc.make(envs["bp35"].game_id)
        A = {a.value: a for a in env.action_space}
        obs = env.reset()
        for v in pre:
            obs = env.step(A[v])
        g = grid_of(obs)
        try:
            obs = click(env, A, x, y)
        except Exception as exc:                      # noqa: BLE001
            print(f"  ({x:2d},{y:2d}) {what}: RAISED {type(exc).__name__}: {exc}")
            continue
        g2 = grid_of(obs)
        if g2 is None:
            print(f"  ({x:2d},{y:2d}) {what}: EMPTY FRAME "
                  f"state={str(obs.state).split('.')[-1]}")
            continue
        n = int((g != g2).sum())
        ys, xs = np.nonzero(g != g2)
        where = (f" at y{ys.min()}-{ys.max()} x{xs.min()}-{xs.max()}"
                 if n else "")
        print(f"  ({x:2d},{y:2d}) {what}: n={n:5d} x={piece_x(g2)} "
              f"flood={flood_top(g2)} lvl={obs.levels_completed} "
              f"st={str(obs.state).split('.')[-1]}{where}")
        sys.stdout.flush()
    print()

# control: repeat one target twice in one episode -- a second identical answer
# proves the call is live rather than the first having been a fluke.
print("== control: the same click twice in one episode ==")
env = arc.make(envs["bp35"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g = grid_of(obs)
for k in range(2):
    obs = click(env, A, 45, 33)
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  press {k}: EMPTY FRAME")
        break
    print(f"  press {k}: n={int((g != g2).sum()):5d} x={piece_x(g2)} "
          f"flood={flood_top(g2)} st={str(obs.state).split('.')[-1]}")
    g = g2
