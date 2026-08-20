"""bp35 fifth pass. Three questions, each with its own fresh episode and a
positive control in the same invocation:

E1  A3 vs A7 -- are they the same action? Same displacement from the same
    state, then compare the WHOLE grid, not the piece x.
E2  The trigger law. Per-action trace (x before/after, cells changed, tower
    hash, flood top) across a shuttle -- p4 logged only the events and its
    five-silent-then-five-firing pattern contradicts "every x44 arrival
    fires".
E3  Does the return leg's ACTION decide the climb? Same position (x44 after
    a bounce off the right wall), reached by A3 in one episode and by A7 in
    another; the tower is the readout.

Control in E1/E3: the two arms are byte-compared, so "identical" is a
measurement and not an absence of output.
"""
import hashlib
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece_x(g):
    ys, xs = np.nonzero((g == 9) | (g == 11))
    return int(xs.min()) if len(xs) else None


def tower_hash(g):
    return hashlib.md5(g[:37].tobytes()).hexdigest()[:8]


def flood_top(g):
    """Topmost row holding any colour 15, ignoring the y63 counter row."""
    ys, _ = np.nonzero(g[:63] == 15)
    return int(ys.min()) if len(ys) else None


def bands(g):
    """Per 6-row band: what each column holds. B=box(10) NN=blocks(14) .=empty"""
    out = []
    for y0 in range(0, 60, 6):
        band = g[y0:y0 + 6]
        codes = []
        for x0, x1 in ((13, 30), (31, 53)):
            sub = band[:, x0:x1 + 1]
            n10, n14 = int((sub == 10).sum()), int((sub == 14).sum())
            codes.append(f"{n14}e" if n14 > 20 else "B" if n10 > 60
                         else "b" if n10 > 10 else ".")
        out.append(codes[0] + "/" + codes[1])
    return " ".join(out)


def fresh():
    env = arc.make(envs["bp35"].game_id)
    A = {a.value: a for a in env.action_space}
    return env, A, env.reset()


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

# ---------------------------------------------------------------- E1
print("== E1: A3 vs A7 from the same state (A4 once, then the left action) ==")
arms = {}
for act in (3, 7):
    env, A, obs = fresh()
    obs = env.step(A[4])
    mid = grid_of(obs)
    obs = env.step(A[act])
    g = grid_of(obs)
    arms[act] = g
    print(f"  A{act}: x {piece_x(mid)} -> {piece_x(g)}  "
          f"changed={int((mid != g).sum())}  tower={tower_hash(g)}")
same = np.array_equal(arms[3], arms[7])
diff = int((arms[3] != arms[7]).sum())
print(f"  IDENTICAL={same} differing_cells={diff}")
if not same:
    ys, xs = np.nonzero(arms[3] != arms[7])
    print(f"  differ at y{ys.min()}-{ys.max()} x{xs.min()}-{xs.max()}")
# control: two grids that MUST differ (reset vs post-move) read as different
env, A, obs = fresh()
ctl = grid_of(obs)
print(f"  control (reset vs moved) differing_cells="
      f"{int((ctl != arms[3]).sum())} (expect > 0)")
sys.stdout.flush()

# ---------------------------------------------------------------- E2
print("\n== E2: per-action trace of a shuttle (what actually fires) ==")
env, A, obs = fresh()
g = grid_of(obs)
plan = [4] * 5 + [3, 4] * 12
for i, v in enumerate(plan):
    xb = piece_x(g)
    tb = tower_hash(g)
    obs = env.step(A[v])
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  i={i:2d} A{v}: EMPTY FRAME")
        break
    n = int((g != g2).sum())
    t2 = tower_hash(g2)
    print(f"  i={i:2d} A{v} x {xb}->{piece_x(g2)} n={n:5d} "
          f"tower={'MOVED' if t2 != tb else '.    '} flood_top={flood_top(g2)} "
          f"st={str(obs.state).split('.')[-1]}")
    if t2 != tb:
        print(f"        bands: {bands(g2)}")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END lvl={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]}")
        break
    sys.stdout.flush()

# ---------------------------------------------------------------- E3
print("\n== E3: return to x44 by A3 vs by A7 (tower is the readout) ==")
arms = {}
for act in (3, 7):
    env, A, obs = fresh()
    for _ in range(4):          # 20 -> 44, fires event #1
        obs = env.step(A[4])
    g1 = grid_of(obs)
    obs = env.step(A[4])        # 44 -> 50 (right wall)
    g2 = grid_of(obs)
    obs = env.step(A[act])      # back to 44
    g3 = grid_of(obs)
    arms[act] = g3
    print(f"  via A{act}: x {piece_x(g1)}->{piece_x(g2)}->{piece_x(g3)}  "
          f"n(step back)={int((g2 != g3).sum())}  "
          f"tower {tower_hash(g1)} -> {tower_hash(g3)} "
          f"({'MOVED' if tower_hash(g1) != tower_hash(g3) else 'same'})  "
          f"flood_top={flood_top(g3)}")
    print(f"        bands: {bands(g3)}")
print(f"  arms identical={np.array_equal(arms[3], arms[7])} "
      f"differing_cells={int((arms[3] != arms[7]).sum())}")
