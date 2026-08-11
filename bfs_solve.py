"""Breadth-first search over REAL engine states, for any replay-deterministic game.

    ./.venv/Scripts/python.exe bfs_solve.py <game> [depth] [max_nodes] [clock_rows]

Nodes are `copy.deepcopy(env)` -- measured to be a true fork, by the control that
asks whether the PARENT moved after the copy stepped (`results/deepcopy-check.txt`;
the weaker "does the copy advance" test passes even on shared state). The visited
key is (whole frame, actions taken): the action count stands in for every clock and
counter that is a function of it, and dropping it is how the sp80 search returned a
false null (`sp80-p9.txt` vs `sp80-p11.txt` -- there the missing term was ammo).

Validated on two levels whose answers are known: sp80 level 1 -> [4,4,4,5] in 38
expansions, ls20 level 1 -> a 13-action win, shorter than the human baseline of 22
(`results/bfs-control.txt`, `bfs-control-ls20.txt`).

NOT rules-legal -- it rewinds, like `play.py`. Use it to learn whether a level is
winnable at all and what the line looks like, then build a forward-only rung.
"""

import copy
import hashlib
import sys
import time
from collections import Counter, deque

# bp35's own game code recurses past the default 1000 frames (a flood-fill
# shaped routine died 987 levels deep under an ordinary step); deepcopy of a
# big env graph gets deep too. One knob covers both.
sys.setrecursionlimit(20000)

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def solve(game, depth=60, max_nodes=60000, clock_rows=(), report=2000):
    arc = arc_agi.Arcade()
    envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
    env = arc.make(envs[game].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    g0 = grid_of(obs)

    def bkey(g):
        if not clock_rows:
            return hashlib.md5(g.tobytes()).hexdigest()
        m = g.copy()
        for r in clock_rows:
            m[r, :] = 0
        return hashlib.md5(m.tobytes()).hexdigest()

    seen = {(bkey(g0), 0)}
    frontier = deque([([], env)])
    expanded, t0, win, deaths, deepest = 0, time.time(), None, 0, 0
    # An action the engine answers with None every time it is tried is dead
    # for the whole run -- bp35's (and cn04's) complex action raises KeyError
    # inside the game and each attempt logs a full traceback; without this
    # latch the log drowns and every expansion pays the exception.
    nones = Counter()
    while frontier and expanded < max_nodes and win is None:
        seq, node = frontier.popleft()
        deepest = max(deepest, len(seq))
        if len(seq) >= depth:
            continue
        for a in sorted(A):
            if nones[a] >= 25:
                continue
            child = copy.deepcopy(node)
            o = child.step(A[a])
            if o is None:
                nones[a] += 1
                continue
            nones[a] = 0
            if o.levels_completed > 0 or str(o.state).endswith("WIN"):
                win = seq + [a]
                break
            if not str(o.state).endswith("NOT_FINISHED"):
                deaths += 1
                continue
            cg = grid_of(o)
            if cg is None:
                continue
            k = (bkey(cg), len(seq) + 1)
            if k in seen:
                continue
            seen.add(k)
            frontier.append((seq + [a], child))
        expanded += 1
        if report and expanded % report == 0:
            print(f"  expanded={expanded} frontier={len(frontier)} states={len(seen)} "
                  f"depth~{len(seq)} deaths={deaths} t={time.time() - t0:.0f}s",
                  flush=True)
    return {"win": win, "expanded": expanded, "states": len(seen), "deaths": deaths,
            "deepest": deepest, "exhausted": not frontier, "secs": time.time() - t0}


if __name__ == "__main__":
    game = sys.argv[1] if len(sys.argv) > 1 else "sp80"
    depth = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    nodes = int(sys.argv[3]) if len(sys.argv) > 3 else 60000
    rows = tuple(int(r) for r in sys.argv[4].split(",")) if len(sys.argv) > 4 else ()
    r = solve(game, depth, nodes, rows)
    print(f"\n{game}: win={r['win']}")
    print(f"  len={len(r['win']) if r['win'] else None} expanded={r['expanded']} "
          f"states={r['states']} deaths={r['deaths']} deepest={r['deepest']} "
          f"exhausted={r['exhausted']} t={r['secs']:.0f}s")
    if r["win"] is None:
        print("  NOTE: 'no win' means nothing unless `exhausted` is True AND the depth "
              "covers a life. Otherwise the search simply ran out.")
