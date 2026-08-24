"""bp35 L2 replay-BFS with chain mechanics (2026-08-17, checkpoint/resume,
sp80_s11 shape).

bp35_b1.py/bp35_b2.py ran the first real replay-BFS over bp35 L2 (deepcopy is
impossible on this game -- it recurses infinitely -- so every node is a
replayed action PATH, never a held env). Their checkpoints wrote COUNTS ONLY
("frontier paths are not serialized, so this is not resumable, only
informative" -- bp35_b2.py). This script is the same search made resumable:
the frontier (action paths) and visited (board-key set) are both pickled,
atomically, so a chain of short invocations accumulates one search instead of
each one restarting from the L2 root.

VIRGIN-RESET DISCIPLINE (the b3 rule, results/bp35-b3-determinism-20260817.md):
bp35_b1.py's BFS began on a SHARED env that had already lived through ~30
characterization replays + a real death/reset before the search started;
bp35_b2.py's began after exactly one confirmation replay. b1 then dropped 91
dead children by node 4000, b2 dropped ZERO through node 24,243 -- same
method, same root, same death-classification code (b3's static diff found
them functionally identical). b3's (c) leg -- 20 paths spanning depth 5-40,
replayed 3x each from a fresh env.reset()+ROOT_RECIPE, full frame+state+
levels_completed compared -- found ZERO divergence anywhere, including at the
two paths that die. That does not prove b1's 91 deaths were wrong; it proves
the ENGINE itself replays byte-identically from a virgin reset when nothing
else has touched the env first. So the rule this script follows: ONE search
env, root confirmed exactly ONCE per process (env.reset()+ROOT_RECIPE -- this
is also what makes every later bare env.reset() scope to the CURRENT LEVEL
per CLAUDE.md's documented reset trap, instead of a full game reset back to
level 1), and NOTHING else ever touches that env -- no probes, no
characterization side-arms, no second env for a control. Session-history
contamination is the only mechanism b3 could pin the 91-vs-0 gap on; this
script refuses to reintroduce it.

Note on the mechanism, honestly: b3's own 3x-replay grid tested full replay
(ROOT_RECIPE+path every call, b1's style), not b2's bare env.reset()-then-
relative-path shortcut specifically. This script uses b2's shortcut anyway
(named explicitly in the task brief, and it is ~5x cheaper per node than
replaying the 20-action root every time -- b2 measured 24,542 nodes/510s vs
b1's ~0.09-0.12s/node). The two are not proven identical; what IS shared and
IS proven is "one search env, one root confirmation, no side-arms after
that." Flagged, not resolved.

SAME key/alphabet/death policy as bp35_b2.py: board-bytes key (last frame
plane via `grid()`), action alphabet = plain [3,4,7] + click on every block
in the piece's current ceiling band or beside it (`candidate_clicks()`,
tape.py's piece_box/room_rows/blocks -- the 7 fixed click targets measured at
the L2 root are what this alphabet reduces to there, not a hardcoded list). A
death (obs is None, grid extraction failure, or GameState.GAME_OVER) is
dropped, not chained -- consistent with the closure's board-reverts-on-death
finding (results/bp35-L2-bfs-20260817.md Controls).

DIVERGENCE COUNTER (`divergence_checked`): counts DEDUP HITS -- a popped
node's board key already present in `visited`. This is NOT a soundness proof
by itself. CLAUDE.md's 2026-08-16 entries (ar25 L5, sp80 L3) show a MERGING
key can report zero divergence while silently dropping real states because
the collision happens before successors are ever computed -- exactly the
shape of this counter. A collision-divergence sample (replay a handful of
same-key pops from independent paths, byte-compare the boards and their
candidate-click sets) is still owed before any EXHAUSTED verdict from this
key is trusted. Not done here -- b3's 20-path/3x grid is partial cover
(0/20 diverged) but is not a sample of THIS run's actual collisions.

CHECKPOINTING: pickled every 2,000 expansions AND on exit (normal or
exceptional, via `finally`) to results/bp35_b4_ckpt.pkl, atomic write
(tmp + os.replace). --fresh ignores any existing checkpoint. --budget-seconds
bounds THIS invocation's engine time only (not cumulative) -- chain
invocations without --fresh to keep going.

    PYTHONUTF8=1 ./.venv/Scripts/python.exe bp35_b4_l2chain.py --budget-seconds 60 --fresh
    PYTHONUTF8=1 ./.venv/Scripts/python.exe bp35_b4_l2chain.py --budget-seconds 3300
"""
import argparse
import os
import pickle
import time
from collections import deque

import numpy as np

import arc_agi
import tape
from arcengine.enums import GameState

CKPT_PATH = os.path.join("results", "bp35_b4_ckpt.pkl")
WIN_TXT_PATH = os.path.join("results", "bp35-b4-win.txt")
CURVE_EVERY = 2000
HEARTBEAT_S = 60

ROOT_RECIPE = (
    [("m", 4)] * 4
    + [("c", 45, 33)]
    + [("c", 15, 39), ("c", 21, 39), ("c", 27, 39)]
    + [("m", 3)] * 5
    + [("c", 15, 33)]
    + [("m", 4)] * 3
    + [("c", 33, 35)]
    + [("m", 3)] * 2
)
assert len(ROOT_RECIPE) == 20
PLAIN = [3, 4, 7]


def grid(o):
    if o is None:
        return None
    f = np.array(o.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def candidate_clicks(g):
    box = tape.piece_box(g)
    if box is None:
        return []
    x0, x1, py0, py1 = box
    top, bot = tape.room_rows(g, box)
    above = tape.blocks(g, 0, top - 1)
    beside = tape.blocks(g, py0, py1)
    seen = {}
    for b in above + beside:
        cx, cy = (b[0] + b[1]) // 2, (b[2] + b[3]) // 2
        seen[(cx, cy)] = b
    return sorted(seen.keys())


def save_checkpoint(state):
    os.makedirs(os.path.dirname(CKPT_PATH), exist_ok=True)
    tmp = CKPT_PATH + ".tmp"
    with open(tmp, "wb") as f:
        pickle.dump(state, f)
    os.replace(tmp, CKPT_PATH)


def load_checkpoint():
    if not os.path.exists(CKPT_PATH):
        return None
    with open(CKPT_PATH, "rb") as f:
        return pickle.load(f)


def run_bfs(budget_seconds, fresh):
    env = arc_agi.Arcade().make("bp35")
    A = {a.value: a for a in env.action_space}
    plain_space = sorted(a.value for a in env.action_space if not a.is_complex())
    click_verb = [a.value for a in env.action_space if a.is_complex()]
    assert plain_space == [3, 4, 7] and click_verb == [6], \
        f"action space changed -- refusing to assume the rest: {plain_space} {click_verb}"

    def do(step):
        if step[0] == "m":
            return env.step(A[step[1]])
        return env.step(A[6], data={"x": step[1], "y": step[2]})

    def replay(path):
        # VIRGIN-RESET DISCIPLINE: env.reset() on the ONE search env, then
        # `path` alone -- see module docstring for why bare reset scopes to
        # L2 entry here (a real action was taken since the last transition,
        # by the one root-confirmation call below) and why nothing else may
        # ever touch this env.
        o = env.reset()
        for s in path:
            o = do(s)
            if o is None:
                return None
        return o

    print("=== root confirmation (once -- no characterization side-arms "
          "on the search env) ===", flush=True)
    obs0 = replay(list(ROOT_RECIPE))
    assert obs0 is not None and obs0.levels_completed == 1, \
        f"L2 root did not confirm (obs={obs0})"
    print(f"L2 root confirmed, levels_completed={obs0.levels_completed}", flush=True)

    ckpt = None if fresh else load_checkpoint()
    if ckpt is not None:
        frontier = deque(ckpt["frontier"])
        visited = ckpt["visited"]
        expanded = ckpt["expanded"]
        deaths_dropped = ckpt["deaths_dropped"]
        divergence_checked = ckpt["divergence_checked"]
        win = ckpt["win"]
        elapsed_prior = ckpt["elapsed_prior"]
        print(f"RESUMED expanded={expanded} states={len(visited)} "
              f"frontier={len(frontier)} deaths={deaths_dropped} "
              f"divergence={divergence_checked} elapsed_prior={elapsed_prior:.1f}s",
              flush=True)
    else:
        frontier = deque([()])
        visited = set()
        expanded = 0
        deaths_dropped = 0
        divergence_checked = 0
        win = None
        elapsed_prior = 0.0
        print("FRESH START", flush=True)

    t0 = time.time()
    last_heartbeat = t0

    def checkpoint_now():
        save_checkpoint(dict(
            frontier=list(frontier), visited=visited, expanded=expanded,
            deaths_dropped=deaths_dropped, divergence_checked=divergence_checked,
            win=win, elapsed_prior=elapsed_prior + (time.time() - t0),
        ))

    try:
        while frontier and win is None and time.time() - t0 < budget_seconds:
            now = time.time()
            if now - last_heartbeat >= HEARTBEAT_S:
                run_elapsed = now - t0
                rate = expanded / max(1e-9, run_elapsed)
                print(f"HEARTBEAT expanded={expanded} states={len(visited)} "
                      f"frontier={len(frontier)} deaths={deaths_dropped} "
                      f"divergence={divergence_checked} rate={rate:.2f}/s "
                      f"t={run_elapsed:.0f}s", flush=True)
                last_heartbeat = now

            path = frontier.popleft()
            obs = replay(list(path))
            expanded += 1

            if obs is None:
                deaths_dropped += 1
            elif obs.levels_completed and obs.levels_completed > 1:
                win = path
                print(f"\n*** WIN at depth {len(path)} ***", flush=True)
                break
            else:
                g = grid(obs)
                if g is None or obs.state == GameState.GAME_OVER:
                    deaths_dropped += 1
                else:
                    key = g.tobytes()
                    if key in visited:
                        # dedup-hit count, not a soundness proof -- see
                        # module docstring
                        divergence_checked += 1
                    else:
                        visited.add(key)
                        for v in PLAIN:
                            frontier.append(path + (("m", v),))
                        for (cx, cy) in candidate_clicks(g):
                            frontier.append(path + (("c", cx, cy),))

            if expanded % CURVE_EVERY == 0:
                checkpoint_now()
                print(f"  CKPT expanded={expanded} states={len(visited)} "
                      f"frontier={len(frontier)} deaths={deaths_dropped} "
                      f"divergence={divergence_checked} "
                      f"t={time.time() - t0:.0f}s CHECKPOINTED", flush=True)
    finally:
        checkpoint_now()

    exhausted = (not frontier) and win is None
    win_bool = win is not None
    total_elapsed = elapsed_prior + (time.time() - t0)

    if win is not None:
        full = list(ROOT_RECIPE) + list(win)
        print(f"\nWIN sequence ({len(full)} actions):", flush=True)
        for i, s in enumerate(full):
            print(f"  {i+1}: {s}", flush=True)
        with open(WIN_TXT_PATH, "w") as f:
            f.write(f"bp35 L2 win, {len(full)} actions\n")
            for i, s in enumerate(full):
                f.write(f"{i+1}: {s}\n")
        print(f"win sequence written to {WIN_TXT_PATH}", flush=True)

    print(f"\nFINAL expanded={expanded} states={len(visited)} "
          f"frontier={len(frontier)} deaths={deaths_dropped} "
          f"exhausted={exhausted} win={win_bool}", flush=True)
    print(f"total_elapsed={total_elapsed:.1f}s "
          f"(this_invocation={time.time() - t0:.1f}s)", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget-seconds", type=int, default=3300)
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args()
    run_bfs(args.budget_seconds, args.fresh)
