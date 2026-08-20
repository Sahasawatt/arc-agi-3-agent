"""tu93 probe 1: locate piece(9)/marker(4)/goal(14) cells at reset, then walk
action4 repeatedly to see how far it goes, then retest 1/2/3 from the new spot.
Guards every read like probe_acts.py (grid_of never indexes an empty frame).
"""
import sys
import numpy as np
import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def cells(g, color):
    ys, xs = np.nonzero(g == color)
    return sorted(zip(ys.tolist(), xs.tolist()))


def report(label, g):
    print(f"-- {label} --")
    for c in (9, 4, 14):
        cs = cells(g, c)
        if cs:
            ys = [p[0] for p in cs]
            xs = [p[1] for p in cs]
            print(f"  color{c}: n={len(cs)} y[{min(ys)}-{max(ys)}] x[{min(xs)}-{max(xs)}] cells={cs}")
        else:
            print(f"  color{c}: n=0")


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tu93"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
g = grid_of(obs)
report("reset", g)

print("\n== walk action4 up to 20x ==")
prev = g
for i in range(20):
    obs = env.step(A[4])
    cur = grid_of(obs)
    state = "obs=None" if obs is None else str(obs.state).split(".")[-1]
    lvl = "" if obs is None else obs.levels_completed
    if cur is None:
        print(f"  {i}: empty frame state={state}")
        break
    changed = int(np.count_nonzero(cur != prev))
    print(f"  {i}: changed_cells(excl budget)={changed} state={state} lvl={lvl}")
    if changed == 0 and i > 0:
        print("  -- no change, stop walking action4 --")
        prev = cur
        break
    prev = cur
report("after action4 walk", prev)

print("\n== retry action1/2/3 from here, 5x each ==")
for act in (1, 2, 3):
    print(f" action{act}:")
    local_prev = prev
    for i in range(5):
        obs = env.step(A[act])
        cur = grid_of(obs)
        if cur is None:
            print(f"   {i}: empty frame")
            break
        ys, xs = np.nonzero(cur != local_prev)
        # exclude the budget row y=63
        mask = ys != 63
        ys2, xs2 = ys[mask], xs[mask]
        print(f"   {i}: non-budget changed cells={len(xs2)}")
        local_prev = cur
    prev = local_prev
report("after retry block", prev)
sys.stdout.flush()
