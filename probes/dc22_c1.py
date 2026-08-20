"""dc22 L2 ratchet cycle-detect + board-keyed BFS.

Picks up exactly where results/dc22-L2-bfs-20260817.md's b-series left off:
both panel buttons are multi-state ratchets (>=7 states measured, no repeat
in 6-7 presses), not L1's binary toggle, and the shipped `bridge.py` driver
cannot represent that. This script:

  1. Reaches the L2 root via the same `bridge` replay used by dc22_b1..b4.py.
  2. Cycle-detects each button on its own continuous deepcopy branch (up to
     CYCLE_CAP presses), recording the true period (first repeated board)
     and each transition's diff bounding box.
  3. Cross-effect check: does pressing A change the board region at B's own
     button, and vice versa (read directly off each state's bbox content).
  4. A bounded (state-A x state-B) grid: press A x times then B y times from
     the root (x, y in 0..GRID_CAP-1), then branch each of the 4 arrows once
     from that combo and record whether the piece moved and how many cells
     changed -- the direct answer to "does movement depend on button state".
  5. A board-keyed BFS over the real engine (4 arrows + click-A + click-B),
     layer-by-layer so only one layer's worth of deepcopy(env) nodes is ever
     alive at once (CLAUDE.md's BFS-frontier memory lesson), bounded by a
     wall-clock deadline and a node cap; checkpoints to
     results/dc22_c1_ckpt.pkl if neither exhausted nor won by the deadline.

Output: results/dc22-c1-log.json (raw data for the report).
"""
import copy
import json
import os
import pickle
import time

os.environ.setdefault("PYTHONUTF8", "1")
import numpy as np
import arc_agi

from bridge import Bridge, components, read

T0 = time.time()
OUT = {}


def log(msg):
    print("[%7.1fs] %s" % (time.time() - T0, msg), flush=True)


def last(o):
    return np.array(o.frame)[-1]


def bbox_diff(a, b):
    d = np.argwhere(a != b)
    if d.size == 0:
        return None
    ys, xs = d[:, 0], d[:, 1]
    return {
        "x0": int(xs.min()), "x1": int(xs.max()),
        "y0": int(ys.min()), "y1": int(ys.max()),
        "n": int(d.shape[0]),
        "colours_before": sorted({int(v) for v in a[ys, xs]}),
        "colours_after": sorted({int(v) for v in b[ys, xs]}),
    }


def region(board, bbox):
    x0, x1, y0, y1 = bbox
    return board[y0:y1 + 1, x0:x1 + 1]


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["dc22"].game_id)
obs = env.reset()
actions = [a for a in env.action_space if not a.is_complex()]
by_value = {a.value: a for a in actions}
values = sorted(by_value)
clicker = next((a for a in env.action_space if a.is_complex()), None)

# ---------- Phase 0: reach the L2 root, recording the exact L1 recipe ----------
bridge = Bridge(values)
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
log("L2 root at i=%d lvl=%s l1_actions=%d" % (i, obs.levels_completed, len(l1_actions)))
assert obs.levels_completed == 1, "did not reach L2 root"
OUT["l1_actions"] = l1_actions
ROOT_LVL = obs.levels_completed

root_env = env
root_last = last(obs)
b0 = read(root_last)
assert b0 is not None, "read() failed at L2 root"
OUT["root_read"] = {"play": b0["play"], "panel": b0["panel"], "pbg": b0["pbg"], "nbg": b0["nbg"]}

# button detection -- identical filter to bridge.Bridge.act's own scan
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
OUT["buttons"] = btn
log("buttons: A=%s B=%s" % (BTN_A, BTN_B))


def press(env_obj, act):
    """act = ('v', value) or ('c', 'A'/'B', x, y). Returns obs or None."""
    if act[0] == "v":
        return env_obj.step(by_value[act[1]])
    _, _, x, y = act
    clicker.set_data({"x": x, "y": y})
    return env_obj.step(clicker, data={"x": x, "y": y})


ACT_A = ("c", "A", BTN_A["at"][0], BTN_A["at"][1])
ACT_B = ("c", "B", BTN_B["at"][0], BTN_B["at"][1])

# ---------- Phase 1: cycle-detect each button on its own continuous branch ----------
CYCLE_CAP = 40


def cycle_detect(root_board, act, label, cap=CYCLE_CAP):
    br = copy.deepcopy(root_env)
    states = [root_board.copy()]
    diffs = []
    period, repeat_of = None, None
    for k in range(cap):
        o = press(br, act)
        if o is None:
            log("%s press %d -> obs None" % (label, k + 1))
            break
        cur = last(o)
        diffs.append(bbox_diff(states[-1], cur))
        cur_bytes = cur.tobytes()
        prior_bytes = [s.tobytes() for s in states]
        if cur_bytes in prior_bytes:
            period = (k + 1) - prior_bytes.index(cur_bytes)
            repeat_of = prior_bytes.index(cur_bytes)
            states.append(cur)
            log("%s press %d -> REPEATS state %d, period=%d" % (label, k + 1, repeat_of, period))
            break
        states.append(cur)
    log("%s: %d presses, %d distinct states seen, period=%s repeat_of=%s"
        % (label, len(diffs), len(states), period, repeat_of))
    return {
        "label": label, "n_presses": len(diffs), "n_states_seen": len(states),
        "period": period, "repeat_of": repeat_of, "diffs": diffs, "states": states,
    }


cyc_a = cycle_detect(root_last, ACT_A, "A")
cyc_b = cycle_detect(root_last, ACT_B, "B")
OUT["cycle_a"] = {k: v for k, v in cyc_a.items() if k != "states"}
OUT["cycle_b"] = {k: v for k, v in cyc_b.items() if k != "states"}

# ---------- Phase 2: cross-effect -- does A's press change B's own button
# region (and vice versa), read directly off each state, not inferred ----------
cross = {"a_changes_b_region": [], "b_changes_a_region": []}
for idx in range(1, len(cyc_a["states"])):
    prev_b = region(cyc_a["states"][idx - 1], BTN_B["bbox"])
    cur_b = region(cyc_a["states"][idx], BTN_B["bbox"])
    cross["a_changes_b_region"].append(bool(not np.array_equal(prev_b, cur_b)))
for idx in range(1, len(cyc_b["states"])):
    prev_a = region(cyc_b["states"][idx - 1], BTN_A["bbox"])
    cur_a = region(cyc_b["states"][idx], BTN_A["bbox"])
    cross["b_changes_a_region"].append(bool(not np.array_equal(prev_a, cur_a)))
OUT["cross_effects"] = cross
log("cross-effects: A changes B's own region in %d/%d presses; B changes A's own region in %d/%d presses"
    % (sum(cross["a_changes_b_region"]), len(cross["a_changes_b_region"]),
       sum(cross["b_changes_a_region"]), len(cross["b_changes_a_region"])))

# ---------- Phase 3: bounded (A-state x B-state) grid, arrow-per-state ----------
GRID_CAP = 8
GRID_DEADLINE = time.time() + 8 * 60
grid = []
grid_aborted_early = False
for x in range(GRID_CAP):
    if time.time() > GRID_DEADLINE:
        grid_aborted_early = True
        log("grid phase deadline hit at x=%d, stopping early" % x)
        break
    for y in range(GRID_CAP):
        br = copy.deepcopy(root_env)
        o = None
        for _ in range(x):
            o = press(br, ACT_A)
        for _ in range(y):
            o = press(br, ACT_B)
        if o is None:
            grid.append({"x": x, "y": y, "obs_none": True})
            continue
        combo_board = last(o)
        rd = read(combo_board)
        piece_here_before = None
        if rd is not None:
            piece_here_before = {t[4]: (t[0], t[2]) for t in rd["twins"]}
        arrow_results = {}
        for v in values:
            ab = copy.deepcopy(br)
            ao = press(ab, ("v", v))
            if ao is None:
                arrow_results[str(v)] = {"obs_none": True}
                continue
            af = last(ao)
            d = bbox_diff(combo_board, af)
            moved = None
            if rd is not None:
                rd2 = read(af)
                if rd2 is not None:
                    here2 = {t[4]: (t[0], t[2]) for t in rd2["twins"]}
                    moved = [c for c, p in here2.items()
                             if c in piece_here_before and piece_here_before[c] != p]
            arrow_results[str(v)] = {
                "changed_cells": 0 if d is None else d["n"],
                "levels_completed": ao.levels_completed,
                "moved_colours": moved,
            }
        grid.append({
            "x": x, "y": y,
            "levels_completed": o.levels_completed,
            "arrow_results": arrow_results,
        })
OUT["grid_cap"] = GRID_CAP
OUT["grid_aborted_early"] = grid_aborted_early
OUT["grid"] = grid
log("grid: %d combos recorded (cap=%d, aborted_early=%s)" % (len(grid), GRID_CAP, grid_aborted_early))

# ---------- Phase 4: board-keyed BFS, layer-by-layer ----------
ACTIONS = [("v", 1), ("v", 2), ("v", 3), ("v", 4), ACT_A, ACT_B]
ACTIONS_JSON = [list(a) for a in ACTIONS]


def board_bytes(o):
    return last(o).tobytes()


root_bytes = root_last.tobytes()
visited = {root_bytes}
frontier = [(copy.deepcopy(root_env), [])]
depth = 0
total_expansions = 0
divergence = {"new": 0, "repeat": 0, "dead": 0}
death_seen = False
death_control = None
depth_curve = [len(frontier)]
win_path = None
verdict = None
BFS_NODE_CAP = 40000
BFS_DEADLINE = time.time() + 18 * 60

while frontier:
    if time.time() > BFS_DEADLINE or total_expansions > BFS_NODE_CAP:
        verdict = "GROWING"
        log("BFS deadline/cap hit: depth=%d total_expansions=%d visited=%d frontier=%d"
            % (depth, total_expansions, len(visited), len(frontier)))
        break
    next_frontier = []
    for env_node, path in frontier:
        for act in ACTIONS:
            total_expansions += 1
            b2 = copy.deepcopy(env_node)
            o2 = press(b2, act)
            if o2 is None:
                divergence["dead"] += 1
                continue
            st = str(o2.state)
            if o2.levels_completed > ROOT_LVL:
                win_path = path + [act]
                log("WIN at depth=%d total_expansions=%d act=%s" % (depth + 1, total_expansions, act))
                break
            if st != "GameState.NOT_FINISHED":
                divergence["dead"] += 1
                if not death_seen:
                    death_seen = True
                    death_control = {
                        "state": st, "depth": depth + 1,
                        "reverts_to_root": bool(board_bytes(o2) == root_bytes),
                    }
                    log("first non-NOT_FINISHED state seen: %s (reverts_to_root=%s)"
                        % (st, death_control["reverts_to_root"]))
                continue
            bb = board_bytes(o2)
            if bb in visited:
                divergence["repeat"] += 1
                continue
            visited.add(bb)
            divergence["new"] += 1
            next_frontier.append((b2, path + [act]))
        if win_path:
            break
    if win_path:
        break
    frontier = next_frontier
    depth += 1
    depth_curve.append(len(frontier))
    log("BFS depth=%d frontier=%d visited=%d total_expansions=%d divergence=%s"
        % (depth, len(frontier), len(visited), total_expansions, divergence))
    if not frontier:
        verdict = "EXHAUSTED"
        log("BFS exhausted: depth=%d visited=%d total_expansions=%d" % (depth, len(visited), total_expansions))

if win_path is not None:
    verdict = "WIN"

OUT["bfs"] = {
    "actions": ACTIONS_JSON,
    "verdict": verdict,
    "depth": depth,
    "total_expansions": total_expansions,
    "visited": len(visited),
    "divergence": divergence,
    "death_seen": death_seen,
    "death_control": death_control,
    "depth_curve": depth_curve,
    "win_path": [list(a) for a in win_path] if win_path else None,
}
log("BFS done: verdict=%s depth=%d visited=%d expansions=%d" % (verdict, depth, len(visited), total_expansions))

if verdict == "GROWING":
    ckpt = {
        "l1_actions": l1_actions,
        "paths": [path for _, path in frontier],
        "depth": depth,
        "visited": len(visited),
        "total_expansions": total_expansions,
        "depth_curve": depth_curve,
        "buttons": btn,
    }
    with open("results/dc22_c1_ckpt.pkl", "wb") as f:
        pickle.dump(ckpt, f)
    log("checkpoint written: results/dc22_c1_ckpt.pkl (%d frontier paths)" % len(ckpt["paths"]))

json.dump(OUT, open("results/dc22-c1-log.json", "w"), indent=2, default=str)
log("wrote results/dc22-c1-log.json")
print("DONE verdict=%s" % verdict, flush=True)
