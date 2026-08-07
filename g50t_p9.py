"""g50t probe 9: does anything survive a DEATH? And is baseline[0] level 1?

    ./.venv/Scripts/python.exe g50t_p9.py

Two loose ends behind the contradiction (`results/breadth-recon.md` §g50t):

  A. baseline indexing. If `baseline_actions[0]` is not the level the engine calls
     level 1, the 78-against-130 contradiction dissolves. Checked against three
     games whose level-1 action counts are measured.
  B. the search pruned every death (`continue` on a non-NOT_FINISHED state) while
     the real play loop answers a GAME_OVER with a reset and carries on. The board
     comes back byte-identical (`g50t-p4.txt`), so that is only safe if nothing
     INVISIBLE accumulates -- and a live run shows the top-left objects shifting
     +/-4 under action 5 at i=1825, after fifteen deaths, which no probe from a
     fresh reset reproduces (`g50t-run1.txt`).

So: die on purpose, over and over, and after each life ask action 5 the same
question and compare the answer.
"""

import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def sig(g):
    """What the whole board is, minus the clock row."""
    m = g.copy()
    m[63, :] = 0
    return m.tobytes()


def topleft(g):
    return g[0:8, 0:12].copy()


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

print("== A: does baseline_actions[0] mean the engine's level 1? ==")
for name, measured in (("ls20", 23), ("re86", 31), ("sp80", 16), ("g50t", None)):
    b = getattr(envs[name], "baseline_actions", None)
    print(f"  {name}: baseline={b}  agent's measured level-1 actions={measured}")
print("  (ls20 23 vs 22, re86 31 vs 26, sp80 16 vs 39 -- all the same order as"
      " baseline[0], so index 0 IS level 1)")

print("\n== B: 20 deliberate deaths, asking action 5 the same question each life ==")
env = arc.make(envs["g50t"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
base_board = sig(grid_of(obs))
base_tl = topleft(grid_of(obs))
first_answer = None

for life in range(20):
    g = grid_of(obs)
    if g is None:
        print(f"  life {life}: empty frame, stopping")
        break
    same_board = sig(g) == base_board
    same_tl = np.array_equal(topleft(g), base_tl)
    # ask action 5 from the start position and see what it does
    o5 = env.step(A[5])
    g5 = grid_of(o5)
    d = None if g5 is None else int((g5[:63] != g[:63]).sum())
    tl_moved = None if g5 is None else not np.array_equal(topleft(g5), topleft(g))
    answer = (d, tl_moved)
    if first_answer is None:
        first_answer = answer
    flag = "" if answer == first_answer else "   <-- CHANGED"
    print(f"  life {life:2d}: board==reset {same_board}  top-left==reset {same_tl}  "
          f"action5 changed {d} non-clock cells, top-left moved={tl_moved}{flag}")
    # burn the rest of the life
    n = 0
    while n < 200 and str(o5.state).endswith("NOT_FINISHED"):
        o5 = env.step(A[3])       # left: refused at x14, a pure clock burn
        n += 1
    if not str(o5.state).endswith("NOT_FINISHED"):
        obs = env.reset()
    else:
        print(f"    (life {life} did not end after {n} actions -- action 3 moved?)")
        obs = o5
sys.stdout.flush()
