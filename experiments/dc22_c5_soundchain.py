"""dc22 L2 chain c5: c2's resumable path-frontier BFS chain, re-keyed with
the validated sound key from c4 (board_bytes + total_len + nA_count +
nB_count) instead of board_bytes alone.

Everything except the key is c2's machinery, verbatim (called via
`import dc22_c2_l2chain as c2`, not reimplemented): root replay + button
detection (c2.make_root), the 6-action alphabet, the per-process MEASURED
death policy (c2.measure_death_policy), the path-frontier + atomic-
checkpoint resume pattern. Persisted separately at
results/dc22_c5_ckpt.pkl so a c5 run never collides with a live/resumed c2
checkpoint.

WHY THE KEY CHANGES THE STATE SPACE (see results/dc22-c4-hidden-20260817.md):
c3 found c2's board-only key merges genuinely different states (73/100
sampled collision pairs diverged under further play). c4 validated
`board + total_len(exact) + nA_count(exact) + nB_count(exact)` at 0/100
divergence over 3,857 fresh collisions. Because `total_len` is folded in
as an EXACT (not mod) integer, two keys can only collide within the same
BFS layer (bfs_collect / this script's frontier is a strict FIFO deque, so
all length-d paths pop before any length-(d+1) path) -- the effective
per-layer key is `(board, nA, nB)`. c4's sizecheck measured this key
retaining ~1.38-1.39x the distinct states of the old key at a comparable
(2000-node) expansion budget; the real inflation at full-run depth is
unmeasured and may be larger. No depth cap is added here -- c2's run_bfs
had none (only budget_seconds), and the game's own death policy is what
bounds branches; unchanged.

    ./.venv/Scripts/python.exe dc22_c5_soundchain.py --budget-seconds 60 --fresh
    ./.venv/Scripts/python.exe dc22_c5_soundchain.py --budget-seconds 3300        # resume
"""
import argparse
import copy
import os
import pickle
import time
from collections import deque

os.environ.setdefault("PYTHONUTF8", "1")

import dc22_c2_l2chain as c2
from dc22_c4_hidden import key_total_raw_plus_nAnB_raw as l2_key

CKPT_PATH = os.path.join("results", "dc22_c5_ckpt.pkl")
WIN_PATH = os.path.join("results", "dc22-c5-win.txt")
CURVE_EVERY = 2000
HEARTBEAT_S = 60
T0 = time.time()


def log(msg):
    print("[%7.1fs] %s" % (time.time() - T0, msg), flush=True)


def save_checkpoint(state):
    os.makedirs("results", exist_ok=True)
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
    root_env, root_obs, l1_actions, ACTIONS, by_value, clicker = c2.make_root()
    ROOT_ENV = root_env
    ROOT_LVL = root_obs.levels_completed
    root_key = l2_key(root_obs, [])

    death_continues = c2.measure_death_policy(root_env, root_obs, ACTIONS, by_value, clicker, ROOT_LVL)

    def replay(seq):
        e = copy.deepcopy(ROOT_ENV)
        o = root_obs
        for act in seq:
            o = c2.press(e, act, by_value, clicker)
            if o is None:
                return e, None
        return e, o

    ckpt = None if fresh else load_checkpoint()
    if ckpt is not None:
        frontier = deque(ckpt["frontier"])
        seen = ckpt["seen"]
        expanded = ckpt["expanded"]
        deaths = ckpt["deaths"]
        curve = ckpt["curve"]
        win = ckpt["win"]
        ckpt_policy = ckpt.get("death_continues")
        if ckpt_policy != death_continues:
            log("WARNING: this process's fresh death measurement (%s) differs from "
                "the checkpointed policy (%s) -- keeping the CHECKPOINTED policy so "
                "the resumed frontier stays consistent with how it was built"
                % (death_continues, ckpt_policy))
            death_continues = ckpt_policy
        print("RESUMED expanded=%d states=%d frontier=%d deaths=%d death_continues=%s"
              % (expanded, len(seen), len(frontier), deaths, death_continues), flush=True)
    else:
        frontier = deque([[]])
        seen = {root_key}
        expanded = 0
        deaths = 0
        curve = []
        win = None
        print("FRESH START death_continues=%s" % death_continues, flush=True)

    t0 = time.time()
    last_heartbeat = t0

    def checkpoint_now():
        save_checkpoint(dict(
            frontier=list(frontier), seen=seen, expanded=expanded, deaths=deaths,
            curve=curve, win=win, death_continues=death_continues,
        ))

    try:
        while frontier and win is None and time.time() - t0 < budget_seconds:
            now = time.time()
            if now - last_heartbeat >= HEARTBEAT_S:
                elapsed = now - t0
                print("HEARTBEAT expanded=%d states=%d frontier=%d deaths=%d t=%.0fs"
                      % (expanded, len(seen), len(frontier), deaths, elapsed), flush=True)
                last_heartbeat = now

            seq = frontier.popleft()
            node_env, node_obs = replay(seq)
            if node_obs is None:
                # Deterministic engine -> a path we ourselves appended should always
                # replay clean. Defensive only (Principle 5): count and move on
                # rather than crash the whole run on one bad node.
                deaths += 1
                continue

            for act in ACTIONS:
                b2 = copy.deepcopy(node_env)
                o2 = c2.press(b2, act, by_value, clicker)
                if o2 is None:
                    deaths += 1
                    continue
                if o2.levels_completed > ROOT_LVL:
                    win = seq + [act]
                    with open(WIN_PATH, "w") as f:
                        f.write("dc22 L2 chain (c5, sound key) WIN\nseq=%r\nlevels_completed=%s\n"
                                % (win, o2.levels_completed))
                    print("WIN: seq=%r levels_completed=%s" % (win, o2.levels_completed), flush=True)
                    break
                st = str(o2.state)
                if st != "GameState.NOT_FINISHED":
                    if not death_continues:
                        deaths += 1
                        continue
                    # death_continues: fall through, treat as an ordinary real state
                nk = l2_key(o2, seq + [act])
                if nk in seen:
                    continue
                seen.add(nk)
                frontier.append(seq + [act])
            if win is not None:
                break

            expanded += 1
            if expanded % CURVE_EVERY == 0:
                curve.append((expanded, len(seen), len(frontier)))
                checkpoint_now()
                print("CURVE expanded=%d states=%d frontier=%d deaths=%d t=%.0fs CHECKPOINTED"
                      % (expanded, len(seen), len(frontier), deaths, time.time() - t0), flush=True)
    finally:
        checkpoint_now()

    exhausted = not frontier
    win_bool = win is not None
    print("FINAL expanded=%d states=%d frontier=%d deaths=%d exhausted=%s win=%s"
          % (expanded, len(seen), len(frontier), deaths, exhausted, win_bool), flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget-seconds", type=int, default=3300)
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args()
    run_bfs(args.budget_seconds, args.fresh)
