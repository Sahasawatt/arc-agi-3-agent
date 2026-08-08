"""tr87: characterise ACTION1-4 precisely, isolating the piece (colour 0) from
the budget-bar burn (y63) and from the crate room (y51-57) noise.

Usage: ./.venv/Scripts/python.exe tr87_probe3.py
"""
import sys
import numpy as np
import arc_agi

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
A = {a.value: a for a in env.action_space}


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece_box(g):
    ys, xs = np.nonzero(g == 0)
    if not len(xs):
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def room_state(g):
    """crate-room cells (y51-57) as a tuple, excludes the piece/bar entirely."""
    return tuple(g[51:58, 14:52].ravel().tolist())


print("== walk ACTION4 x8 from reset, report piece box + room-changed + lvl ==")
obs = env.reset()
g = grid_of(obs)
print("reset piece box:", piece_box(g), "room hash cells:", len(room_state(g)))
prev_room = room_state(g)
for i in range(8):
    obs = env.step(A[4])
    g = grid_of(obs)
    box = piece_box(g)
    cur_room = room_state(g)
    changed = sum(1 for a, b in zip(prev_room, cur_room) if a != b)
    print(f"  press{i}: piece={box} room_cells_changed={changed} "
          f"lvl={obs.levels_completed} state={str(obs.state).split('.')[-1]}")
    prev_room = cur_room

print("\n== walk ACTION3 x8 from reset (opposite dir hypothesis) ==")
obs = env.reset()
g = grid_of(obs)
print("reset piece box:", piece_box(g))
for i in range(8):
    obs = env.step(A[3])
    g = grid_of(obs)
    box = piece_box(g)
    print(f"  press{i}: piece={box} lvl={obs.levels_completed}")

print("\n== ACTION1 x4 then ACTION2 x4 from reset (piece parked at reset column) ==")
obs = env.reset()
g = grid_of(obs)
prev_room = room_state(g)
print("reset room snapshot (7x38):")
snap = g[51:58, 14:52]
for row in snap:
    print("  " + "".join(str(int(v)) if v < 10 else chr(87 + int(v)) for v in row))
for i in range(4):
    obs = env.step(A[1])
    g = grid_of(obs)
    cur_room = room_state(g)
    changed = [(idx) for idx, (a, b) in enumerate(zip(prev_room, cur_room)) if a != b]
    print(f"  ACTION1 press{i}: room_cells_changed={len(changed)} piece={piece_box(g)} "
          f"lvl={obs.levels_completed}")
    prev_room = cur_room
for i in range(4):
    obs = env.step(A[2])
    g = grid_of(obs)
    cur_room = room_state(g)
    changed = sum(1 for a, b in zip(prev_room, cur_room) if a != b)
    print(f"  ACTION2 press{i}: room_cells_changed={changed} piece={piece_box(g)} "
          f"lvl={obs.levels_completed}")
    prev_room = cur_room
print("room snapshot after ACTION1x4+ACTION2x4:")
g = grid_of(obs)
snap = g[51:58, 14:52]
for row in snap:
    print("  " + "".join(str(int(v)) if v < 10 else chr(87 + int(v)) for v in row))

sys.stdout.flush()
