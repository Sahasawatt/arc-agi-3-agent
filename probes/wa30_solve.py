"""wa30 level 1, by hand: carry all three boxes into the 12x4 frame.

    ./.venv/Scripts/python.exe wa30_solve.py

The mechanic, measured (`results/wa30-p2.txt`, `p3`, `p4`, `p5`): action 5 beside
a box GRABS it (its ring takes the piece's edge colour and the pair moves as one),
a second press DROPS it where it stands, and a box dropped over the 12x4 colour-9
frame at (28,28)-(39,31) SLOTS IN -- its ring joins the frame's row and 8 cells of
the frame's colour-2 inner are consumed for good, still gone when read from afar.

The inner is 10x2 = 20 cells and the three boxes cover 6 + 8 + 6 of it, so the
arithmetic says three boxes fill it exactly. This drives that.

  box at (32,36) -> the middle slot (32,28)
  box at (16,28) -> the left slot   (28,28)
  box at (44,24) -> the right slot  (36,28)
"""

import sys

import numpy as np

import arc_agi

CH = "0123456789abcdef"


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def held(g):
    ys, xs = np.nonzero((g == 14) | (g == 0))
    if not len(xs):
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()),
            int(((g == 14) | (g == 0)).sum()))


def slots_left(g):
    """Cells of the frame's colour-2 inner still empty."""
    return int((g == 2).sum())


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["wa30"].game_id)
A = {a.value: a for a in env.action_space}
NAME = {1: "up", 2: "down", 3: "left", 4: "right", 5: "act5"}

PLAN = (
    # --- box at (32,36) into the middle slot ---
    [1, 1, 5, 1, 1, 5]
    # --- box at (16,28) into the left slot. The last move before a grab must FACE
    #     the box: action 5 acts along the heading, and the heading is whichever
    #     way the piece last walked. Arriving at (16,32) sideways refuses the grab
    #     (`results/wa30-solve.txt` step 10, first attempt), so drop a row, go
    #     west, and come UP into it.
    + [2, 3, 3, 3, 3, 1, 5, 4, 4, 4, 5]
    # --- box at (44,24) into the right slot ---
    + [4, 4, 4, 4, 1, 5, 3, 3, 2, 5]
)

obs = env.reset()
g = grid_of(obs)
print(f"reset: piece={held(g)} empty slot cells={slots_left(g)}")
for i, a in enumerate(PLAN):
    obs = env.step(A[a])
    g = grid_of(obs)
    if g is None:
        print(f"  {i:2d} {NAME[a]:5s}: empty frame state={obs.state}")
        break
    print(f"  {i:2d} {NAME[a]:5s}: carried={held(g)} slots={slots_left(g)} "
          f"lvl={obs.levels_completed} state={str(obs.state).split('.')[-1]}")
    if obs.levels_completed > 0:
        print(f"\n  *** LEVEL 1 CLEARED in {i + 1} actions ***")
        break
    if not str(obs.state).endswith("NOT_FINISHED"):
        break

print("\nfinal board (rows with content):")
bg = int(np.bincount(g.ravel()).argmax()) if g is not None else 1
if g is not None:
    for y in range(64):
        row = "".join(CH[int(v) & 0xF] for v in g[y])
        if set(row) - {CH[bg & 0xF]}:
            print(f"  y={y:2d} {row}")
sys.stdout.flush()
