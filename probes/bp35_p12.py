"""bp35 tenth pass: the action matrix at S, and what a block click actually does.

At S (A4 x4 then click(45,33)) the piece's chamber is x31-53 y37-53, the
chute stub sits BELOW it at x43-47 y54-60, and everything above y36 on the
piece's side is background. All 15 block clicks were local and opened no
climb (p11). So the question is which (action, position) pair still fires
anything at all -- asked exhaustively rather than by recipe.

E15  every action in {3,4,7} from every reachable piece x, one fresh
     episode per pair, n + tape shift + level.
E16  one block click, printed as rows before and after, so "n=26" stops
     being a number and becomes a mechanic.
"""
import sys

import numpy as np

import arc_agi

S_PLAN = [("move", 4)] * 4 + [("click", 45, 33)]


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece_x(g):
    ys, xs = np.nonzero((g == 9) | (g == 11))
    return int(xs.min()) if len(xs) else None


def rows(g, y0, y1, x0=13, x1=53):
    return [f"y{y:2d} " + "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                                  for v in g[y, x0:x1 + 1])
            for y in range(y0, y1 + 1)]


def shift(a, b):
    best = (None, 0.0)
    for dy in range(-36, 37, 6):
        rr = [y for y in range(max(0, -dy), min(63, 63 - dy))]
        if len(rr) < 20:
            continue
        frac = float((a[rr, 13:54] == b[[y + dy for y in rr], 13:54]).mean())
        if frac > best[1]:
            best = (dy, frac)
    return best


def to_state(env, A):
    obs = env.reset()
    for s in S_PLAN:
        obs = (env.step(A[s[1]]) if s[0] == "move"
               else env.step(A[6], data={"x": s[1], "y": s[2]}))
    return obs


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}


def fresh_S():
    env = arc.make(envs["bp35"].game_id)
    A = {a.value: a for a in env.action_space}
    return env, A, to_state(env, A)


print("== E15: every action from every reachable x at S ==")
# how far does the chamber run? walk each way first, from S.
for act, name in ((3, "left"), (4, "right")):
    env, A, obs = fresh_S()
    g = grid_of(obs)
    xs = [piece_x(g)]
    for _ in range(6):
        obs = env.step(A[act])
        g = grid_of(obs)
        if g is None:
            break
        xs.append(piece_x(g))
    print(f"  walk {name}: {xs}")
sys.stdout.flush()

REACH = [0, 1, 2, 3]        # how many A3 steps left of S's x before acting
for back in REACH:
    for act in (3, 4, 7):
        env, A, obs = fresh_S()
        g = grid_of(obs)
        ok = True
        for _ in range(back):
            obs = env.step(A[3])
            g = grid_of(obs)
            if g is None:
                ok = False
                break
        if not ok:
            print(f"  back={back}: setup died")
            continue
        xb = piece_x(g)
        obs = env.step(A[act])
        g2 = grid_of(obs)
        if g2 is None:
            print(f"  x={xb} A{act}: DEAD FRAME")
            continue
        n = int((g != g2).sum())
        dy = shift(g, g2)[0] if n > 200 else 0
        print(f"  x={xb} A{act}: n={n:5d} x->{piece_x(g2)} tape dy={dy:+3d} "
              f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}"
              f"{'   <== FIRES' if n > 200 else ''}")
        sys.stdout.flush()

print("\n== E16: one block click, rows before and after ==")
env, A, obs = fresh_S()
g = grid_of(obs)
obs = env.step(A[6], data={"x": 21, "y": 39})
g2 = grid_of(obs)
print(f"  click(21,39): n={int((g != g2).sum())}")
for a, b in zip(rows(g, 36, 48), rows(g2, 36, 48)):
    flag = "  <<" if a != b else ""
    print(f"  {a}   |   {b}{flag}")
