"""Drive ls20 level 6 from the measured model: patrolling changers, period-8, press on overlap.

    uv run python l6drive.py <prefix-file> <door>     # door = A | B

Everything here is MEASURED, not assumed (results/l6-circuits.txt):
- three patrollers advance one lattice step per PIECE MOVE (a refused press freezes all),
  each on a period-8 track;
- a press is the piece's 5x5 footprint overlapping a patroller's cells AFTER the move;
- the ink cluster steps the panel ink along 12 -> 9 -> 14 -> 8 -> 12; the y=41 cross turns
  the shape a quarter CW; the y=11 cross walks the shape along an alphabet whose watched
  edges end on door A's glyph.

BFS over (position, phase, ink, shape) emits an action list, then executes it in the real
game, checking the panel against the prediction after every action. Divergence = the model
is wrong; completion answers whether entering a door with a matching panel ends the level.
"""

import sys

import numpy as np

import arc_agi
from arcengine import GameState
from gate import plates, turned
from perception import components

PREFIX = [int(a) for a in open(sys.argv[1]).read().strip().split(",")]
DOOR = sys.argv[2] if len(sys.argv) > 2 else "A"
EXTRA = [int(a) for a in sys.argv[3].split(",")] if len(sys.argv) > 3 else []

DIRS = {1: (0, -5), 2: (0, 5), 3: (-5, 0), 4: (5, 0)}
CARRY = {(49, 20): (39, 20), (49, 5): (49, 25)}   # aim -> landing, measured

# Patroller tracks: anchor per phase (phase = piece moves since the prefix state, mod 8),
# with cell offsets from the anchor. Measured in results/l6-circuits.txt.
INK_ANCHOR = [(25, 31), (20, 31), (20, 26), (20, 21), (25, 21), (30, 21), (30, 26), (30, 31)]
INK_CELLS = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (2, 2)]
C1_ANCHOR = [(15, 11), (20, 11), (25, 11), (30, 11), (35, 11), (30, 11), (25, 11), (20, 11)]
C1_CELLS = [(0, 0), (1, 1), (2, 1), (1, 2)]
C2_ANCHOR = [(35, 41), (30, 41), (25, 41), (20, 41), (15, 41), (20, 41), (25, 41), (30, 41)]
C2_CELLS = [(1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (1, 2)]

INK_CYCLE = [12, 9, 14, 8]
# The y=11 cross's alphabet, watched edge by edge; unknown ground is unplannable.
ALPHABET = {"#.#/.##/##.": "#../###/#..", "#../###/#..": "###/#../###",
            "###/#../###": ".#./#.#/.##", ".#./#.#/.##": ".#./###/#..",
            ".#./###/#..": "#.#/..#/###"}

ASK = {"A": (9, "#.#/..#/###"), "B": (8, "#.#/##./.##")}
DOOR_GOAL = {"A": (54, 50), "B": (54, 35)}
# Optional 4th arg "ink:shape" overrides the panel the plan aims for at the goal — the
# instrument for asking WHICH half a door actually checks.
if len(sys.argv) > 4:
    ink_s, shape_s = sys.argv[4].split(":")
    ASK[DOOR] = (int(ink_s), shape_s)

arc = arc_agi.Arcade()
env = arc.make("ls20")
obs = env.reset()
space = {a.value: a for a in env.action_space}
for a in PREFIX:
    obs = env.step(space[a])
    if np.array(obs.frame).size == 0 or obs.state == GameState.GAME_OVER:
        obs = env.reset()

grid = np.array(obs.frame)[-1]


def walkable(x, y):
    """Only the wall colour blocks. The piece stands overlapping a door's FRAME — measured,
    (54, 30) covers door B's top frame row and the agent stood there — so colour 5 is not
    solid; what the engine refuses is entering an unmatched door's inside, handled below."""
    if x < 0 or y < 5 or x > 59 or y > 55:
        return False
    box = grid[y:y + 5, x:x + 5]
    return box.size == 25 and not (box == 4).any()


# Which inside-positions the BFS may not transit. Door B is a PASSAGE — measured: the
# piece walked (54,30) -> (54,35) -> (54,40) -> (54,45) — so when the target is door A,
# B is left open to route through, and whether B checks its glyph on the way is exactly
# what the run will show.
INSIDE = {(54, 50)} if (len(sys.argv) > 2 and sys.argv[2] == "A") else {(54, 35), (54, 50)}


def cells(anchor, offs):
    return {(anchor[0] + dx, anchor[1] + dy) for dx, dy in offs}


def overlap(pos, cs):
    return any(pos[0] <= cx < pos[0] + 5 and pos[1] <= cy < pos[1] + 5 for cx, cy in cs)


def step_shape(shape, phase, pos):
    """(ink_delta, new shape, ok) after landing on `pos` at `phase`."""
    ink_d, ok = 0, True
    if overlap(pos, cells(INK_ANCHOR[phase], INK_CELLS)):
        ink_d += 1
    if overlap(pos, cells(C2_ANCHOR[phase], C2_CELLS)):
        orbit = turned(shape)
        if orbit:
            shape = orbit[1]
        else:
            ok = False
    if overlap(pos, cells(C1_ANCHOR[phase], C1_CELLS)):
        if shape in ALPHABET:
            shape = ALPHABET[shape]
        else:
            ok = False
    return ink_d, shape, ok


REFILL = {(9, 5): 0, (39, 5): 1, (9, 45): 2}   # pickup position -> refill index
FULL = 42                                       # moves a tank buys at 2 units an action


def plan(start, ink0, shape0, want_ink, want_shape, goal, t0=0, fuel0=FULL, used0=0):
    """Action list to stand on `goal` with the panel reading the ask, or None.

    BFS over (position, phase, ink, shape, refills-used), carrying fuel as a value to
    maximise per state rather than a state dimension — a route is only pruned when an
    earlier visit reached the same state with at least as much in the tank. Stepping on
    a refill's pickup square refills, once each. `want_ink is None` means any panel.
    """
    from collections import deque
    seen = {(start, t0, ink0, shape0, used0): (fuel0, None)}
    q = deque([(start, t0, ink0, shape0, used0)])
    while q:
        node = q.popleft()
        pos, t, ink, shape, used = node
        fuel = seen[node][0]
        if fuel <= 0:
            continue
        for a, (dx, dy) in DIRS.items():
            aim = (pos[0] + dx, pos[1] + dy)
            nxt = CARRY.get(aim, aim)
            # A door is entered only as the goal, with the panel right — routing THROUGH
            # one would be refused by the engine on a mismatch the plan never checked.
            if nxt in INSIDE and nxt != goal:
                continue
            if not walkable(*nxt):
                continue
            t2 = (t + 1) % 8
            ink_d, shape2, ok = step_shape(shape, t2, nxt)
            if not ok:
                continue
            ink2 = INK_CYCLE[(INK_CYCLE.index(ink) + ink_d) % 4]
            if nxt == goal and want_ink is not None \
                    and not (ink2 == want_ink and shape2 == want_shape):
                continue          # only enter the door with the panel right
            used2, fuel2 = used, fuel - 1
            r = REFILL.get(nxt)
            if r is not None and not used & (1 << r):
                used2, fuel2 = used | (1 << r), FULL
            key = (nxt, t2, ink2, shape2, used2)
            if key in seen and seen[key][0] >= fuel2:
                continue
            seen[key] = (fuel2, (node, a))
            if nxt == goal:
                acts, cur = [], key
                while seen[cur][1]:
                    cur, act = seen[cur][1]
                    acts.append(act)
                return acts[::-1], (fuel2, used2)
            q.append(key)
    return None


def panel(frame):
    for box, (ink, ic) in plates(frame).items():
        if box[0] < 15:            # the indicator lives bottom-left
            return (ink, ic)
    return None


def piece(frame):
    """Largest colour-12 component in the PLAY AREA. The panel draws its glyph at 2x in
    the current ink, so when the ink is 12 the biggest 12-component on the frame is the
    panel, not the piece — it lives below row 50 and is excluded by position."""
    g = np.array(frame)[-1]
    best = max((c for c in components(g, 12) if c[2] < 50 or c[0] > 15),
               key=lambda c: c[4])
    return (int(best[0]), int(best[2]))


start = piece(obs.frame)
ink0, shape0 = panel(obs.frame)
print("start at %s panel=(%s, %s)" % (start, ink0, shape0))


def doors_now(frame):
    return {"%d,%d" % (b[0], b[2]): v for b, v in plates(frame).items() if b[0] > 40}


def run(acts, pos, t, ink, shape, fuel, used):
    """Execute, checking every step against the model. Stops on a real divergence —
    every action after one is aimed from a square the piece is not on."""
    global obs
    for i, a in enumerate(acts, start=1):
        obs = env.step(space[a])
        if np.array(obs.frame).size == 0:
            print("%3d act%d GAME OVER" % (i, a))
            return None
        aim = (pos[0] + DIRS[a][0], pos[1] + DIRS[a][1])
        pos = CARRY.get(aim, aim)
        t = (t + 1) % 8
        ink_d, shape, _ = step_shape(shape, t, pos)
        ink = INK_CYCLE[(INK_CYCLE.index(ink) + ink_d) % 4]
        fuel -= 1
        r = REFILL.get(pos)
        if r is not None and not used & (1 << r):
            used, fuel = used | (1 << r), FULL
        got_pos = piece(obs.frame)
        got_panel = panel(obs.frame)
        mark = "OK " if got_pos == pos and got_panel == (ink, shape) else "DIVERGED"
        print("%3d act%d lvl=%d pos=%s pred=%s panel=%s pred=(%s, %s) fuel=%d %s doors=%s"
              % (i, a, obs.levels_completed, got_pos, pos, got_panel, ink, shape, fuel,
                 mark, doors_now(obs.frame)))
        if got_pos != pos:
            print("stopping: the board disagrees, the rest of the plan is fiction")
            return None
        if obs.levels_completed > 5:
            print("LEVEL 6 COMPLETE at action %d of this drive" % i)
            return None
    return pos, t, ink, shape, fuel, used


if DOOR == "AB":
    # Leg 1: enter door B wearing what it asks. Leg 2: from inside, go set the panel to
    # door A's ask and come back THROUGH B — which is the hypothesis under test: does a
    # door, once passed while matched, stay open?
    got = plan(start, ink0, shape0, *ASK["B"], DOOR_GOAL["B"])
    if not got:
        print("NO PLAN leg1")
        sys.exit(1)
    acts, _ = got
    print("leg1: %d acts: %s" % (len(acts), ",".join(map(str, acts))))
    state = run(acts, start, 0, ink0, shape0, FULL, 0)
    if state:
        pos, t, ink, shape, fuel, used = state
        INSIDE.clear()
        got2 = plan(pos, ink, shape, *ASK["A"], DOOR_GOAL["A"], t0=t,
                    fuel0=fuel, used0=used)
        if not got2:
            print("NO PLAN leg2 (fuel=%d used=%d)" % (fuel, used))
            sys.exit(1)
        acts2, _ = got2
        print("leg2: %d acts: %s" % (len(acts2), ",".join(map(str, acts2))))
        run(acts2, pos, t, ink, shape, fuel, used)
else:
    want_ink, want_shape = ASK[DOOR]
    print("-> door %s wants (%s, %s)" % (DOOR, want_ink, want_shape))
    got = plan(start, ink0, shape0, want_ink, want_shape, DOOR_GOAL[DOOR])
    if not got:
        print("NO PLAN")
        sys.exit(1)
    acts, _ = got
    print("plan: %d actions: %s" % (len(acts), ",".join(map(str, acts))))
    run(acts + EXTRA, start, 0, ink0, shape0, FULL, 0)
