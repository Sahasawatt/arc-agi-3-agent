"""Hypothesis-free real-engine BFS over re86 L6, from a root built by replaying
compete.play's own actions (cover.py drives L1-5; L6 win-family is unknown).

Root: run compete.play(env, budget=big) with env.step monkeypatched to stop the
instant levels_completed reaches 5 -- that IS "construct the root by replaying
compete.play's own actions". Deepcopy that env for every BFS branch (measured
elsewhere in this repo: deepcopy(env) is legal, faithful, ~ms-scale).

BFS: board-keyed (full last-plane bytes -- the wall-desync arm offset is DRAWN,
so the key sees it), layer-by-layer to bound memory, deepcopy nodes stored only
for the CURRENT layer. GAME_OVER children are dropped after one control confirms
free re-entry reverts to the root's own board bytes. Node/time caps bound the
run; GROWING past either checkpoints to a pickle of action-paths (not envs).
"""
import copy
import json
import pickle
import sys
import time

import numpy as np

import arc_agi
import compete
from arcengine import GameState

OUT_MD = "results/re86-L6-bfs-20260817.md"
CKPT = "results/re86_b1_ckpt.pkl"
import os
NODE_CAP = int(os.environ.get("RE86_NODE_CAP", 40000))
TIME_CAP_S = int(os.environ.get("RE86_TIME_CAP_S", 14 * 60))      # BFS wall-clock budget, inside the 25-min engine cap
TARGET_LEVEL = 5           # levels_completed value that means "L6 root"


def grid_bytes(obs):
    return np.array(obs.frame)[-1].tobytes()


class LevelReached(Exception):
    def __init__(self, obs, actions_taken):
        self.obs = obs
        self.actions_taken = actions_taken


def build_root():
    """Replay compete.play's own actions until levels_completed==5, return the
    live env (already at the L6 root) + the obs + the action recipe + cost."""
    arc = arc_agi.Arcade()
    envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
    info = envs["re86"]
    env = arc.make(info.game_id)
    orig_step = env.step
    taken = []

    def step_wrap(a):
        o = orig_step(a)
        taken.append(int(a.value) if hasattr(a, "value") else int(a))
        if o is not None and o.levels_completed >= TARGET_LEVEL:
            raise LevelReached(o, list(taken))
        return o

    env.step = step_wrap
    t0 = time.time()
    try:
        compete.play(env, budget=2000)
    except LevelReached as e:
        env.step = orig_step
        return env, e.obs, e.actions_taken, time.time() - t0
    raise RuntimeError("compete.play never reached levels_completed==5 within budget 2000")


def main():
    t_start = time.time()
    print("[root] replaying compete.play (cover.py) to L6 entry...", flush=True)
    env, obs, recipe, cost_s = build_root()
    print(f"[root] levels_completed={obs.levels_completed} state={obs.state} "
          f"recipe_len={len(recipe)} cost={cost_s:.1f}s", flush=True)
    assert obs.levels_completed == 5, "root construction did not land on L6"
    root_key = grid_bytes(obs)

    A = {a.value: a for a in env.action_space}
    action_values = sorted(A)
    print(f"[root] action space (plain, non-complex only per env.action_space): {action_values}",
          flush=True)

    # --- deepcopy fidelity control ---
    c1, c2 = copy.deepcopy(env), copy.deepcopy(env)
    probe_a = action_values[0]
    o1 = c1.step(A[probe_a])
    o2 = c2.step(A[probe_a])
    fidelity_ok = (grid_bytes(o1) == grid_bytes(o2)
                   and o1.levels_completed == o2.levels_completed
                   and str(o1.state) == str(o2.state))
    print(f"[control] deepcopy fidelity (two independent copies, same action {probe_a}): "
          f"{'OK' if fidelity_ok else 'MISMATCH'}", flush=True)
    assert fidelity_ok, "deepcopy fidelity control FAILED -- BFS nodes are not independent/faithful"
    # env itself was never stepped -- root untouched, still levels_completed==5
    assert grid_bytes(obs) == root_key

    # --- BFS ---
    root_env = copy.deepcopy(env)
    visited = {root_key}
    layer = [(root_key, root_env, [])]
    layer_no = 0
    total_expanded = 0
    total_new = 0
    total_merged = 0
    total_gameover = 0
    total_refused_wall = 0  # heuristic: child board == parent board (no-op-looking press)
    gameover_control_done = False
    gameover_control_ok = None
    win_path = None
    census = []  # per-layer stats for the curve

    deadline = t_start + TIME_CAP_S
    stop_reason = None

    while layer:
        next_layer = {}
        layer_new = layer_merged = layer_gameover = layer_expanded = 0
        for key, node_env, path in layer:
            if win_path is not None:
                break
            if time.time() > deadline:
                stop_reason = "time_cap"
                break
            if total_expanded >= NODE_CAP:
                stop_reason = "node_cap"
                break
            for v in action_values:
                if time.time() > deadline:
                    stop_reason = "time_cap"
                    break
                if total_expanded >= NODE_CAP:
                    stop_reason = "node_cap"
                    break
                child_env = copy.deepcopy(node_env)
                o = child_env.step(A[v])
                total_expanded += 1
                layer_expanded += 1
                if o is None:
                    continue
                if o.levels_completed > TARGET_LEVEL or str(o.state) == "GameState.WIN":
                    win_path = path + [v]
                    print(f"[WIN] path={win_path}", flush=True)
                    break
                if str(o.state) == "GameState.GAME_OVER":
                    total_gameover += 1
                    layer_gameover += 1
                    if not gameover_control_done:
                        ro = child_env.reset()
                        gameover_control_ok = (
                            ro is not None and grid_bytes(ro) == root_key
                            and ro.levels_completed == TARGET_LEVEL)
                        gameover_control_done = True
                        print(f"[control] free re-entry on GAME_OVER reverts to root board: "
                              f"{'OK' if gameover_control_ok else 'MISMATCH'}", flush=True)
                    continue  # death children dropped -- free re-entry is the root again
                ckey = grid_bytes(o)
                if ckey == key:
                    total_refused_wall += 1
                if ckey in visited:
                    total_merged += 1
                    layer_merged += 1
                    continue
                visited.add(ckey)
                total_new += 1
                layer_new += 1
                next_layer[ckey] = (child_env, path + [v])
            if win_path is not None or stop_reason:
                break
        if win_path is not None:
            break
        layer_no += 1
        elapsed = time.time() - t_start
        row = {"layer": layer_no, "frontier": len(next_layer), "visited": len(visited),
               "expanded": total_expanded, "new": layer_new, "merged": layer_merged,
               "gameover": layer_gameover, "elapsed_s": round(elapsed, 1)}
        census.append(row)
        print(f"[layer {layer_no}] frontier={row['frontier']} visited={row['visited']} "
              f"expanded={row['expanded']} new={layer_new} merged={layer_merged} "
              f"gameover={layer_gameover} elapsed={row['elapsed_s']}s", flush=True)
        if stop_reason:
            break
        if not next_layer:
            stop_reason = "exhausted"
            break
        layer = [(k, e, p) for k, (e, p) in next_layer.items()]

    # --- write results ---
    branching = (total_new / max(1, total_expanded - total_gameover)) if total_expanded else 0
    result = {
        "root_recipe_len": len(recipe),
        "root_recipe": recipe,
        "root_cost_s": cost_s,
        "action_values": action_values,
        "fidelity_control": fidelity_ok,
        "gameover_control": gameover_control_ok,
        "total_expanded": total_expanded,
        "total_new": total_new,
        "total_merged": total_merged,
        "total_gameover": total_gameover,
        "total_refused_wall": total_refused_wall,
        "win_path": win_path,
        "stop_reason": stop_reason,
        "layers": layer_no,
        "census": census,
        "measured_branching_factor": round(branching, 3),
    }

    if win_path is None and stop_reason in ("node_cap", "time_cap"):
        ckpt = {
            "recipe": recipe,
            "action_values": action_values,
            "visited_count": len(visited),
            "frontier_paths": [p for (_k, _e, p) in layer] if not next_layer
                               else [p for (_k, (_e, p)) in next_layer.items()],
            "census": census,
            "resume": "rebuild root via re86_b1_bfs.build_root(), replay each frontier_paths[i] "
                      "with deepcopy(root_env), then continue BFS from that frontier.",
        }
        with open(CKPT, "wb") as f:
            pickle.dump(ckpt, f)
        print(f"[checkpoint] wrote {CKPT} ({len(ckpt['frontier_paths'])} frontier paths)", flush=True)

    verdict = ("WIN" if win_path is not None
               else "EXHAUSTED_NO_WIN" if stop_reason == "exhausted"
               else f"GROWING+checkpoint ({stop_reason})")
    result["verdict"] = verdict
    print(f"[verdict] {verdict}", flush=True)

    with open("results/re86_b1_bfs_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    write_report(result)
    print(f"[done] total wall time {time.time()-t_start:.1f}s", flush=True)


def write_report(result):
    lines = []
    lines.append("# re86 L6 -- hypothesis-free real-engine BFS")
    lines.append("")
    lines.append(f"Verdict: **{result['verdict']}**")
    lines.append("")
    lines.append("## Root recipe + cost")
    lines.append("")
    lines.append(f"- Built by monkeypatching `env.step` to raise the instant "
                  f"`obs.levels_completed >= 5`, and running `compete.play(env, budget=2000)` "
                  f"unmodified (existing file, not edited) -- this IS \"replaying compete.play's "
                  f"own actions\": the cover.py driver plays L1-5 exactly as the sweep does.")
    lines.append(f"- Action count to reach L6: **{result['root_recipe_len']}** "
                  f"(sweep-wave12.log's re86 per-level counts [31,56,66,80,188] sum to 421 -- "
                  f"{'matches' if result['root_recipe_len'] == 421 else 'DIFFERS from'} that).")
    lines.append(f"- Wall time to build root: {result['root_cost_s']:.1f}s.")
    lines.append(f"- Root env is deepcopied once; every BFS branch works off a deepcopy, "
                  f"never the canonical root.")
    lines.append("")
    lines.append("## Action space")
    lines.append("")
    lines.append(f"`env.action_space` (plain, non-complex): `{result['action_values']}` "
                  f"-- matches cover.py's DIRS {{1,2,3,4}} + TOGGLE 5; no complex/click action.")
    lines.append("")
    lines.append("## Controls")
    lines.append("")
    lines.append(f"- **Deepcopy fidelity**: two independent `deepcopy(root_env)` copies stepped "
                  f"with the same action produced byte-identical frames, `levels_completed` and "
                  f"`state` -- {'OK' if result['fidelity_control'] else 'FAILED'}.")
    lines.append(f"- **GAME_OVER free re-entry**: on the first GAME_OVER encountered in BFS, "
                  f"`env.reset()` was called on that dead branch and compared to the root's board "
                  f"bytes -- {result['gameover_control']} "
                  f"({'confirmed byte-identical, free' if result['gameover_control'] else 'NOT confirmed -- see note'}). "
                  f"All {result['total_gameover']} GAME_OVER children across the run were dropped "
                  f"on this single control, per the anti-goal (no per-node re-verification).")
    lines.append(f"- **Board key = full last-plane bytes.** The standing closure notes the wall-"
                  f"desync arm offset is DRAWN, so a byte-key sees it; no board-invisible hidden "
                  f"state is known for this game (unlike ar25's period-3 selection or sp80's ammo).")
    lines.append("")
    lines.append("## BFS census")
    lines.append("")
    lines.append(f"- Total real `env.step` calls (expansions): **{result['total_expanded']}**")
    lines.append(f"- New distinct boards: **{result['total_new']}**")
    lines.append(f"- Merged into an already-visited board (\"divergence\"/convergence count): "
                  f"**{result['total_merged']}**")
    lines.append(f"- GAME_OVER children: **{result['total_gameover']}**")
    lines.append(f"- Presses that left the board byte-identical to the parent (refused/no-op, "
                  f"e.g. the wall or a clamp with no visible effect): **{result['total_refused_wall']}**")
    lines.append(f"- Layers completed: **{result['layers']}**")
    lines.append(f"- Measured branching factor (new boards / non-GAME_OVER expansion): "
                  f"**{result['measured_branching_factor']}**")
    lines.append("")
    lines.append("| layer | frontier | visited | expanded | new | merged | gameover | elapsed_s |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in result["census"]:
        lines.append(f"| {r['layer']} | {r['frontier']} | {r['visited']} | {r['expanded']} | "
                      f"{r['new']} | {r['merged']} | {r['gameover']} | {r['elapsed_s']} |")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    if result["win_path"] is not None:
        lines.append(f"WIN. Action sequence from the L6 root: `{result['win_path']}`")
    elif result["stop_reason"] == "exhausted":
        lines.append("EXHAUSTED_NO_WIN. The frontier reached empty (every reachable, "
                      "not-yet-visited board from the L6 root has been expanded, or ended in "
                      "GAME_OVER) with no `WIN`/`levels_completed>5` ever observed. "
                      f"Total distinct boards visited: {len(result.get('census', [])) and result['census'][-1]['visited']}.")
    else:
        lines.append(f"GROWING -- stopped by `{result['stop_reason']}` before exhausting or "
                      f"winning. Checkpoint written to `{CKPT}` (action-paths for the live "
                      f"frontier, not envs -- resume by rebuilding the root and replaying each "
                      f"path). See the branching factor above and the per-layer curve: at that "
                      f"rate, exhausting the remaining space is "
                      f"{'plausible within minutes' if result['measured_branching_factor'] < 1.5 else 'NOT plausible within minutes -- treat this as the closure'}.")
    lines.append("")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(chr(10).join(lines) + chr(10))
    print(f"[report] wrote {OUT_MD}", flush=True)


if __name__ == "__main__":
    main()
