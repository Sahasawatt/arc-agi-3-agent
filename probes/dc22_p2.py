"""dc22 second pass: what the two panel buttons DO, and whether the room is
still sealed once one has been pressed.

p1 measured: the right panel holds two display boxes, colour 8 at y16-22 and
colour 9 at y33-39; clicking one answers 129/97 cells the first time (it also
clears the 0-borders both boxes wear at reset) and a steady 49/17 every time
after. Nothing else on the board responds, before or after.

E5  press the 8-button four times, printing the PLAY AREA (x0-31) each time --
    a cycle shows up as a board repeating, a toggle as two alternating.
E6  the same for the 9-button.
E7  recon's "the piece's room is sealed" was measured before any button was
    pressed. Press each button, then walk the piece in all four directions and
    report whether it leaves the room.
"""
import sys

import numpy as np

import arc_agi

BTN8, BTN9 = (48, 19), (48, 36)
PLAY = (0, 31)


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def play(g):
    return g[16:54, PLAY[0]:PLAY[1] + 1]


def show(g, label):
    print(f"  {label}")
    for y in range(16, 54):
        line = "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                       for v in g[y, PLAY[0]:PLAY[1] + 1])
        if set(line) != {"4"}:
            print(f"    y{y:2d} {line}")


def piece_at(g, colour=14):
    ys, xs = np.nonzero(g == colour)
    return (int(xs.min()), int(ys.min())) if len(ys) else None


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}


def fresh():
    env = arc.make(envs["dc22"].game_id)
    return env, {a.value: a for a in env.action_space}, None


for btn, label in ((BTN8, "E5: the colour-8 button"), (BTN9, "E6: the colour-9 button")):
    print(f"== {label} ==")
    env, A, _ = fresh()
    obs = env.reset()
    g = grid_of(obs)
    show(g, "reset play area")
    seen = {play(g).tobytes(): "reset"}
    for k in range(4):
        obs = env.step(A[6], data={"x": btn[0], "y": btn[1]})
        g2 = grid_of(obs)
        if g2 is None:
            print(f"  press {k}: DEAD FRAME")
            break
        key = play(g2).tobytes()
        tag = f"   <-- play area equals {seen[key]}" if key in seen else ""
        seen.setdefault(key, f"press {k}")
        print(f"  press {k}: n={int((g != g2).sum())} "
              f"lvl={obs.levels_completed}{tag}")
        if not tag:
            show(g2, f"after press {k}")
        g = g2
    sys.stdout.flush()
    print()

print("== E7: is the room still sealed after a press? ==")
for pre, label in ((None, "no press (control)"), (BTN8, "after the 8-button"),
                   (BTN9, "after the 9-button")):
    env, A, _ = fresh()
    obs = env.reset()
    if pre:
        obs = env.step(A[6], data={"x": pre[0], "y": pre[1]})
    g = grid_of(obs)
    start = piece_at(g)
    moved = {}
    for v in (1, 2, 3, 4):
        env2, A2, _ = fresh()
        obs2 = env2.reset()
        if pre:
            obs2 = env2.step(A2[6], data={"x": pre[0], "y": pre[1]})
        gg = grid_of(obs2)
        for _ in range(6):
            obs2 = env2.step(A2[v])
            g2 = grid_of(obs2)
            if g2 is None:
                break
            gg = g2
        moved[v] = piece_at(gg)
    print(f"  {label}: start={start} after 6x each direction: {moved} "
          f"lvl={obs2.levels_completed}")
    sys.stdout.flush()
