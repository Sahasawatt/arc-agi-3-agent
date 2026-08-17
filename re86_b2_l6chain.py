"""re86 b2 L6 chain: re86_b1_bfs's hypothesis-free real-engine layer-BFS, with
persistence swapped from a deepcopy-env frontier (no resume loader existed)
to an ACTION-PATH frontier that checkpoints and resumes across process
invocations. Root builder, board key, action set and GAME_OVER handling are
UNCHANGED from b1 -- reused directly via `import re86_b1_bfs as b1`. Only
what gets stored, and how a run survives a restart, changed.

Layer BFS is kept (b1's structure): a `layer` (paths still to expand this
layer) drains into a `next_layer` (dict ckey->path, dedups convergent
children) exactly as b1 does; census rows are written per completed layer.
What differs: frontier entries are PATHS, not (key, env, path) -- keys are
computed lazily by replaying from a single root env, and `visited` is a
plain set of board-key bytes checkpointed alongside the frontier.

CHAIN:
  ./.venv/Scripts/python.exe re86_b2_l6chain.py --budget-seconds 60 --fresh [--seed-b1]
  ./.venv/Scripts/python.exe re86_b2_l6chain.py --budget-seconds 3300        # resume, repeat
"""
import argparse
import copy
import os
import pickle
import sys
import time
from collections import deque

import re86_b1_bfs as b1

CKPT = os.path.join("results", "re86_b2_ckpt.pkl")
B1_CKPT = os.path.join("results", "re86_b1_ckpt.pkl")
WIN_FILE = os.path.join("results", "re86-b2-win.txt")
CURVE_EVERY = 2000
HEARTBEAT_S = 60


def save_checkpoint(state):
    os.makedirs(os.path.dirname(CKPT), exist_ok=True)
    tmp = CKPT + ".tmp"
    with open(tmp, "wb") as f:
        pickle.dump(state, f)
    os.replace(tmp, CKPT)


def load_checkpoint():
    if not os.path.exists(CKPT):
        return None
    with open(CKPT, "rb") as f:
        return pickle.load(f)


def load_b1_frontier():
    if not os.path.exists(B1_CKPT):
        return None
    with open(B1_CKPT, "rb") as f:
        return pickle.load(f)


def run(budget_seconds, fresh, seed_b1):
    t_start = time.time()
    print("[root] replaying compete.play (cover.py) to L6 entry...", flush=True)
    env, root_obs, recipe, cost_s = b1.build_root()
    print(f"[root] levels_completed={root_obs.levels_completed} recipe_len={len(recipe)} "
          f"cost={cost_s:.1f}s", flush=True)
    assert root_obs.levels_completed == 5, "root construction did not land on L6"
    root_key = b1.grid_bytes(root_obs)

    A = {a.value: a for a in env.action_space}
    action_values = sorted(A)
    print(f"[root] action space: {action_values}", flush=True)

    # deepcopy fidelity control -- same as b1
    c1, c2 = copy.deepcopy(env), copy.deepcopy(env)
    probe_a = action_values[0]
    o1, o2 = c1.step(A[probe_a]), c2.step(A[probe_a])
    fidelity_ok = (b1.grid_bytes(o1) == b1.grid_bytes(o2)
                   and o1.levels_completed == o2.levels_completed
                   and str(o1.state) == str(o2.state))
    print(f"[control] deepcopy fidelity: {'OK' if fidelity_ok else 'MISMATCH'}", flush=True)
    assert fidelity_ok, "deepcopy fidelity control FAILED"
    assert b1.grid_bytes(root_obs) == root_key

    ROOT_ENV = copy.deepcopy(env)

    def replay(path):
        e = copy.deepcopy(ROOT_ENV)
        o = root_obs
        for v in path:
            o = e.step(A[v])
        return e, o

    ckpt = None if fresh else load_checkpoint()
    if ckpt is not None:
        layer = deque(ckpt["layer"])
        next_layer = ckpt["next_layer"]
        visited = ckpt["visited"]
        layer_no = ckpt["layer_no"]
        total_expanded = ckpt["total_expanded"]
        total_new = ckpt["total_new"]
        total_merged = ckpt["total_merged"]
        total_gameover = ckpt["total_gameover"]
        total_refused_wall = ckpt["total_refused_wall"]
        layer_new = ckpt["layer_new"]
        layer_merged = ckpt["layer_merged"]
        layer_gameover = ckpt["layer_gameover"]
        layer_expanded = ckpt["layer_expanded"]
        census = ckpt["census"]
        win_path = ckpt["win_path"]
        gameover_control_done = ckpt["gameover_control_done"]
        gameover_control_ok = ckpt["gameover_control_ok"]
        print(f"RESUMED expanded={total_expanded} frontier={len(layer) + len(next_layer)}",
              flush=True)
    else:
        seeded_note = ""
        if seed_b1:
            b1ckpt = load_b1_frontier()
            if b1ckpt is None:
                print(f"[seed-b1] {B1_CKPT} not found -- falling back to plain root start",
                      flush=True)
                layer = deque([[]])
                layer_no = 0
            else:
                layer = deque(b1ckpt["frontier_paths"])
                layer_no = len(b1ckpt.get("census", []))
                seeded_note = f" seeded_from_b1 paths={len(layer)} layer_no={layer_no}"
        else:
            layer = deque([[]])
            layer_no = 0
        next_layer = {}
        visited = {root_key}
        total_expanded = total_new = total_merged = total_gameover = total_refused_wall = 0
        layer_new = layer_merged = layer_gameover = layer_expanded = 0
        census = []
        win_path = None
        gameover_control_done = False
        gameover_control_ok = None
        print(f"FRESH START{seeded_note}", flush=True)

    def checkpoint_now():
        save_checkpoint(dict(
            layer=list(layer), next_layer=next_layer, visited=visited, layer_no=layer_no,
            total_expanded=total_expanded, total_new=total_new, total_merged=total_merged,
            total_gameover=total_gameover, total_refused_wall=total_refused_wall,
            layer_new=layer_new, layer_merged=layer_merged, layer_gameover=layer_gameover,
            layer_expanded=layer_expanded, census=census, win_path=win_path,
            gameover_control_done=gameover_control_done, gameover_control_ok=gameover_control_ok,
        ))

    run_t0 = time.time()
    last_heartbeat = run_t0
    stop_reason = None

    try:
        while True:
            if win_path is not None:
                stop_reason = "win"
                break

            if not layer:
                elapsed = time.time() - t_start
                row = {"layer": layer_no, "frontier": len(next_layer), "visited": len(visited),
                       "expanded": total_expanded, "new": layer_new, "merged": layer_merged,
                       "gameover": layer_gameover, "elapsed_s": round(elapsed, 1)}
                census.append(row)
                print(f"[layer {layer_no}] frontier={row['frontier']} visited={row['visited']} "
                      f"expanded={row['expanded']} new={layer_new} merged={layer_merged} "
                      f"gameover={layer_gameover} elapsed={row['elapsed_s']}s", flush=True)
                if not next_layer:
                    stop_reason = "exhausted"
                    break
                layer_no += 1
                layer = deque(next_layer.values())
                next_layer = {}
                layer_new = layer_merged = layer_gameover = layer_expanded = 0
                continue

            if time.time() - run_t0 > budget_seconds:
                stop_reason = "budget"
                break

            now = time.time()
            if now - last_heartbeat >= HEARTBEAT_S:
                elapsed = now - run_t0
                rate = total_expanded / max(1e-9, elapsed)
                print(f"HEARTBEAT expanded={total_expanded} visited={len(visited)} "
                      f"frontier={len(layer) + len(next_layer)} rate={rate:.2f}/s "
                      f"layer={layer_no} t={elapsed:.0f}s", flush=True)
                last_heartbeat = now

            path = layer.popleft()
            node_env, node_obs = replay(path)
            node_key = b1.grid_bytes(node_obs)
            visited.add(node_key)

            for v in action_values:
                if time.time() - run_t0 > budget_seconds:
                    stop_reason = "budget"
                    break
                child_env = copy.deepcopy(node_env)
                o = child_env.step(A[v])
                total_expanded += 1
                layer_expanded += 1
                if o is None:
                    continue
                if o.levels_completed > b1.TARGET_LEVEL or str(o.state) == "GameState.WIN":
                    win_path = path + [v]
                    print(f"[WIN] path={win_path}", flush=True)
                    break
                if str(o.state) == "GameState.GAME_OVER":
                    total_gameover += 1
                    layer_gameover += 1
                    if not gameover_control_done:
                        ro = child_env.reset()
                        gameover_control_ok = (
                            ro is not None and b1.grid_bytes(ro) == root_key
                            and ro.levels_completed == b1.TARGET_LEVEL)
                        gameover_control_done = True
                        print(f"[control] free re-entry on GAME_OVER reverts to root board: "
                              f"{'OK' if gameover_control_ok else 'MISMATCH'}", flush=True)
                    continue
                ckey = b1.grid_bytes(o)
                if ckey == node_key:
                    total_refused_wall += 1
                if ckey in visited:
                    total_merged += 1
                    layer_merged += 1
                    continue
                visited.add(ckey)
                total_new += 1
                layer_new += 1
                next_layer[ckey] = path + [v]

                if total_expanded % CURVE_EVERY == 0:
                    checkpoint_now()
                    print(f"  CHECKPOINT expanded={total_expanded} visited={len(visited)} "
                          f"frontier={len(layer) + len(next_layer)}", flush=True)
            if win_path is not None:
                stop_reason = "win"
                break
    finally:
        checkpoint_now()

    frontier_remaining = len(layer) + len(next_layer)
    exhausted = (stop_reason == "exhausted")
    win = win_path is not None

    if win:
        with open(WIN_FILE, "w", encoding="utf-8") as f:
            f.write(f"WIN path={win_path}\n")
        print(f"WIN seq={win_path}", flush=True)
        print(f"[win-file] wrote {WIN_FILE}", flush=True)

    print(f"FINAL expanded={total_expanded} states={len(visited)} frontier={frontier_remaining} "
          f"deaths={total_gameover} exhausted={exhausted} win={win}", flush=True)
    print(f"[done] stop_reason={stop_reason} total wall time {time.time()-t_start:.1f}s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget-seconds", type=int, default=3300)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--seed-b1", action="store_true")
    args = ap.parse_args()
    run(args.budget_seconds, args.fresh, args.seed_b1)
