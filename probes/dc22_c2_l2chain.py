"""dc22 L2 chain: c1's board-keyed BFS, made resumable (sp80_s11's path-
frontier + atomic-checkpoint pattern) + a MEASURED death policy.

Root replay, board key, button detection and the 6-action alphabet are all
cited from dc22_c1.py -- reproduced here (not imported) since c1 is a
top-level script, not a module.

WHY PATH-FRONTIER INSTEAD OF ENV-FRONTIER: c1 held one BFS *layer* of
deepcopy(env) nodes at a time (CLAUDE.md's BFS-memory lesson) but a
deepcopy(env) is not picklable, so a layer-frontier cannot checkpoint. This
script stores the frontier as ACTION PATHS (picklable) and replays each one
from a fresh deepcopy(ROOT_ENV) on pop -- the same trade sp80_s11 made
(~20x slower per node at depth ~20, priced in already).

DEATH POLICY (measured, not chosen): c1 observed `reverts_to_root: False`
at the first GAME_OVER (depth 11) but never tested whether the env is
STEPPABLE after death -- it just dropped the branch. measure_death_policy()
below reproduces the identical layer-by-layer board-keyed BFS to reach that
same first death, then presses the dead env again and reads what comes
back. The finding is printed and drives DEATH_CONTINUES for the whole run:
a death that returns to NOT_FINISHED with a real board is an ordinary node
(kept); a death that stays terminal or stops responding is dropped and
counted. Runs once per process invocation, including on resume, because a
process's own env instance is what gets tested -- ponytail: this is a
~50-60s fixed cost paid on every invocation (~8k engine expansions to
reliably reach the depth-11 death); cache the verdict only if this becomes
the bottleneck -- it currently isn't.

    ./.venv/Scripts/python.exe dc22_c2_l2chain.py --budget-seconds 60 --fresh
    ./.venv/Scripts/python.exe dc22_c2_l2chain.py --budget-seconds 3300        # resume
    ./.venv/Scripts/python.exe dc22_c2_l2chain.py --seed-c1 --fresh --budget-seconds 60
"""
import argparse
import copy
import os
import pickle
import time
from collections import deque

os.environ.setdefault("PYTHONUTF8", "1")
import numpy as np
import arc_agi

from bridge import Bridge, components, read

CKPT_PATH = os.path.join("results", "dc22_c2_ckpt.pkl")
C1_CKPT_PATH = os.path.join("results", "dc22_c1_ckpt.pkl")
WIN_PATH = os.path.join("results", "dc22-c2-win.txt")
CURVE_EVERY = 2000
HEARTBEAT_S = 60
DEATH_NODE_CAP = 9000  # >= worst-case 7,962 expansions to complete c1's depth-10 layer
T0 = time.time()


def log(msg):
    print("[%7.1fs] %s" % (time.time() - T0, msg), flush=True)


def last(o):
    return np.array(o.frame)[-1]


def board_bytes(o):
    return last(o).tobytes()


def press(env_obj, act, by_value, clicker):
    """act = ('v', value) or ('c', 'A'/'B', x, y). Cited from dc22_c1.py."""
    if act[0] == "v":
        return env_obj.step(by_value[act[1]])
    _, _, x, y = act
    clicker.set_data({"x": x, "y": y})
    return env_obj.step(clicker, data={"x": x, "y": y})


def make_root():
    """Same L1->L2 replay + button detection as dc22_c1.py Phases 0. Returns
    (root_env, root_obs, l1_actions, ACTIONS, by_value, clicker)."""
    arc = arc_agi.Arcade()
    envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
    env = arc.make(envs["dc22"].game_id)
    obs = env.reset()
    actions = [a for a in env.action_space if not a.is_complex()]
    by_value = {a.value: a for a in actions}
    clicker = next((a for a in env.action_space if a.is_complex()), None)

    bridge = Bridge(sorted(by_value))
    l1_actions = []
    i = 0
    while i < 400:
        frame = last(obs)
        cv = bridge.act(frame, obs.levels_completed)
        if cv is None:
            break
        i += 1
        if isinstance(cv, tuple):
            l1_actions.append(("click", cv[1], cv[2]))
            clicker.set_data({"x": cv[1], "y": cv[2]})
            obs = env.step(clicker, data={"x": cv[1], "y": cv[2]})
        else:
            l1_actions.append(("v", cv))
            obs = env.step(by_value[cv])
        if obs is None or obs.levels_completed >= 1:
            break
    assert obs is not None and obs.levels_completed == 1, "did not reach L2 root"
    log("L2 root at i=%d l1_actions=%d" % (i, len(l1_actions)))

    root_last = last(obs)
    b0 = read(root_last)
    assert b0 is not None, "read() failed at L2 root"
    panel = root_last[:, b0["panel"][0]:b0["panel"][1] + 1]
    wide = panel.shape[1] - 1
    btn = []
    for c in components(panel, b0["nbg"]):
        if c[5] < 20 or c[0] == 0 or c[1] >= wide:
            continue
        x0, x1 = c[0] + b0["panel"][0], c[1] + b0["panel"][0]
        y0, y1 = c[2], c[3]
        at = ((x0 + x1) // 2, (y0 + y1) // 2)
        if at not in [e["at"] for e in btn]:
            btn.append({"at": at, "bbox": (x0, x1, y0, y1), "colour": c[4], "size": c[5]})
    assert len(btn) == 2, "expected exactly 2 buttons, got %r" % (btn,)
    BTN_A, BTN_B = btn[0], btn[1]
    ACT_A = ("c", "A", BTN_A["at"][0], BTN_A["at"][1])
    ACT_B = ("c", "B", BTN_B["at"][0], BTN_B["at"][1])
    ACTIONS = [("v", 1), ("v", 2), ("v", 3), ("v", 4), ACT_A, ACT_B]
    log("buttons: A=%s B=%s" % (BTN_A, BTN_B))
    return env, obs, l1_actions, ACTIONS, by_value, clicker


def measure_death_policy(root_env, root_obs, ACTIONS, by_value, clicker, root_lvl):
    """MEASURE ONCE PER PROCESS. Reach the first GAME_OVER via the identical
    layer-by-layer board-keyed BFS c1 used (same alphabet, same dedup, one
    layer of deepcopy(env) alive at a time), then press the dead env again
    and read what comes back. Prints the finding; returns DEATH_CONTINUES."""
    root_bytes = board_bytes(root_obs)
    visited = {root_bytes}
    frontier = [(copy.deepcopy(root_env), [])]
    total = 0
    dead = None
    while frontier and dead is None and total < DEATH_NODE_CAP:
        next_frontier = []
        for env_node, path in frontier:
            for act in ACTIONS:
                total += 1
                b2 = copy.deepcopy(env_node)
                o2 = press(b2, act, by_value, clicker)
                if o2 is None:
                    continue
                st = str(o2.state)
                if st != "GameState.NOT_FINISHED":
                    dead = (b2, o2, path + [act], st)
                    break
                bb = board_bytes(o2)
                if bb in visited:
                    continue
                visited.add(bb)
                next_frontier.append((b2, path + [act]))
            if dead is not None:
                break
        if dead is not None:
            break
        frontier = next_frontier
    if dead is None:
        log("DEATH MEASUREMENT: no GAME_OVER found within %d expansions -- cannot "
            "measure; defaulting DEATH_CONTINUES=False (conservative drop)" % DEATH_NODE_CAP)
        return False

    b2, o2, path, st = dead
    reverts = board_bytes(o2) == root_bytes
    log("DEATH MEASUREMENT: first %s at depth=%d total_expansions=%d "
        "levels_completed=%s reverts_to_root=%s"
        % (st, len(path), total, o2.levels_completed, reverts))

    o3 = press(b2, ACTIONS[0], by_value, clicker)
    if o3 is None or len(o3.frame) == 0:
        reason = "obs=None" if o3 is None else "obs returned but frame is EMPTY (len=0)"
        log("DEATH MEASUREMENT: post-death step -> %s. Engine does not hand back a "
            "usable frame after %s on this env (no explicit reset() attempted). "
            "FINDING: env terminates." % (reason, st))
        return False

    board_changed = not np.array_equal(last(o3), last(o2))
    log("DEATH MEASUREMENT: post-death step(%r) -> state=%s levels_completed=%s "
        "board_changed_from_death_frame=%s" % (ACTIONS[0], o3.state, o3.levels_completed, board_changed))

    continues = str(o3.state) == "GameState.NOT_FINISHED"
    if continues:
        log("DEATH MEASUREMENT FINDING: play CONTINUES after %s -- env stays "
            "steppable, state returns to NOT_FINISHED with a real (mutated) board. "
            "Policy: treat post-death states as ordinary nodes." % st)
    else:
        log("DEATH MEASUREMENT FINDING: env is steppable but state stays %s (does "
            "not return to NOT_FINISHED) -- not real continued play. "
            "Policy: drop the branch, count as death." % o3.state)
    return continues


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


def seed_from_c1(seen_add_fn, replay_fn, seed_deadline):
    """Import c1's checkpoint FRONTIER (903 depth-19 action paths). c1's own
    ckpt stores only a `visited` COUNT (int), not the hash set, so the
    historical 8,023-state dedup cannot be imported -- only the frontier
    paths. Best-effort: replay each seeded path once to add ITS OWN board to
    `seen`, so the seeded frontier doesn't immediately self-collide; bounded
    by seed_deadline since 903 x 19-step replays is not free."""
    if not os.path.exists(C1_CKPT_PATH):
        log("SEED-C1: %s not found, skipping" % C1_CKPT_PATH)
        return [], 0, 0, False
    with open(C1_CKPT_PATH, "rb") as f:
        c1 = pickle.load(f)
    paths = c1["paths"]
    log("SEED-C1: loaded %d frontier paths from c1 ckpt (depth=%d, c1 visited "
        "count=%d -- COUNT ONLY, not a hash set, so historical dedup is NOT imported)"
        % (len(paths), c1["depth"], c1["visited"]))
    n_hashed = 0
    budget_exceeded = False
    for idx, p in enumerate(paths):
        if time.time() > seed_deadline:
            budget_exceeded = True
            log("SEED-C1: seeding deadline hit after %d/%d paths hashed" % (idx, len(paths)))
            break
        _, o = replay_fn(p)
        if o is not None:
            seen_add_fn(board_bytes(o))
            n_hashed += 1
    return paths, n_hashed, len(paths), budget_exceeded


def run_bfs(budget_seconds, fresh, seed_c1):
    root_env, root_obs, l1_actions, ACTIONS, by_value, clicker = make_root()
    ROOT_ENV = root_env
    ROOT_LVL = root_obs.levels_completed
    root_bytes = board_bytes(root_obs)

    death_continues = measure_death_policy(root_env, root_obs, ACTIONS, by_value, clicker, ROOT_LVL)

    def replay(seq):
        e = copy.deepcopy(ROOT_ENV)
        o = root_obs
        for act in seq:
            o = press(e, act, by_value, clicker)
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
        seen = {root_bytes}
        expanded = 0
        deaths = 0
        curve = []
        win = None
        print("FRESH START death_continues=%s" % death_continues, flush=True)
        if seed_c1:
            seed_deadline = time.time() + 90
            paths, n_hashed, n_total, budget_exceeded = seed_from_c1(seen.add, replay, seed_deadline)
            frontier.extend(paths)
            print("SEED-C1: frontier extended by %d paths, %d/%d hashed into `seen` "
                  "(budget_exceeded=%s)" % (len(paths), n_hashed, n_total, budget_exceeded), flush=True)

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
                o2 = press(b2, act, by_value, clicker)
                if o2 is None:
                    deaths += 1
                    continue
                if o2.levels_completed > ROOT_LVL:
                    win = seq + [act]
                    with open(WIN_PATH, "w") as f:
                        f.write("dc22 L2 chain WIN\nseq=%r\nlevels_completed=%s\n"
                                % (win, o2.levels_completed))
                    print("WIN: seq=%r levels_completed=%s" % (win, o2.levels_completed), flush=True)
                    break
                st = str(o2.state)
                if st != "GameState.NOT_FINISHED":
                    if not death_continues:
                        deaths += 1
                        continue
                    # death_continues: fall through, treat as an ordinary real state
                bb = board_bytes(o2)
                if bb in seen:
                    continue
                seen.add(bb)
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
    ap.add_argument("--seed-c1", action="store_true")
    args = ap.parse_args()
    run_bfs(args.budget_seconds, args.fresh, args.seed_c1)
