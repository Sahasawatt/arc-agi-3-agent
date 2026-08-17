"""cn04 L2 BFS session, script 2: exhaustive/checkpointed real-engine BFS from the
L2 root over the full boundable action alphabet (plain verbs + object-select clicks
+ pad clicks), board-keyed, layer-by-layer to bound memory (CLAUDE.md: a BFS whose
FRONTIER holds deepcopy(env) nodes is memory-bound before it is time-bound -- keep
envs only for the layer being expanded, emit the next layer, drop this one).

WIN check: obs.levels_completed >= 2 after every single press -- that is the only
oracle used; no geometric/interlock model is consulted anywhere in this file.

Writes results/cn04-b2-bfs.txt (progress, appended-as-you-go) and
results/cn04-b2-win.txt (only if a win is found: the full action path).
flush=True throughout; hard wall-clock deadline + node cap + per-layer cap.
"""
import copy
import hashlib
import time
import numpy as np
import arc_agi
from arcengine import GameAction

T0 = time.time()
DEADLINE_S = 8 * 60           # hard wall-clock cap on the search phase itself
MAX_DEPTH = 45
MAX_LAYER = 6000              # per-layer node cap (memory bound)
MAX_TOTAL = 150000            # total expansion cap

VERBS = [1, 2, 3, 4, 5, 7]    # ACTION6 bare (no data) proven to kill the env (b1 script); excluded
ACTIONS_BY_INT = {int(a.value): a for a in GameAction}

out_lines = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out_lines.append(s)
    with open("results/cn04-b2-bfs.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")


L1_LINE = [GameAction.ACTION5] * 3 + [GameAction.ACTION2] * 7 + [GameAction.ACTION4] * 4


def reach_l2(env):
    o = env.reset()
    if o.levels_completed >= 1:
        return o
    last = o
    for act in L1_LINE:
        last = env.step(act)
        assert last is not None, "died mid L1 replay"
    assert last.levels_completed >= 1
    return last


def g_of(o):
    return np.array(o.frame)[-1]


def board_key(g):
    return hashlib.blake2b(g.tobytes(), digest_size=16).digest()


def blobs(g, colour, min_size=1):
    ys, xs = np.where(g == colour)
    cells = set(zip(ys.tolist(), xs.tolist()))
    seen, out_b = set(), []
    for cell in cells:
        if cell in seen:
            continue
        stack, comp = [cell], []
        seen.add(cell)
        while stack:
            cy, cx = stack.pop()
            comp.append((cy, cx))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (cy + dy, cx + dx)
                if nb in cells and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        if len(comp) >= min_size:
            out_b.append(comp)
    return out_b


SELECT_COLOURS = (0, 9, 11, 14, 15)   # shape colours + the "selected" highlight colour
PAD_COLOUR = 8


def click_targets(g):
    """One representative CELL (never a computed centroid -- concave blobs put the
    centroid off the shape, measured in b1_char.py) per connected blob of the select
    colours plus every pad blob. Returns list of (label, x, y)."""
    targets = []
    for colour in SELECT_COLOURS:
        comps = blobs(g, colour, min_size=5)
        comps.sort(key=len, reverse=True)
        for i, comp in enumerate(comps):
            cy, cx = comp[len(comp) // 2]
            targets.append((f"sel{colour}.{i}", int(cx), int(cy)))
    pad_comps = blobs(g, PAD_COLOUR, min_size=5)
    for i, comp in enumerate(pad_comps):
        cy, cx = comp[len(comp) // 2]
        targets.append((f"pad{i}", int(cx), int(cy)))
    return targets


def candidate_actions(g):
    acts = [("verb", v) for v in VERBS]
    for label, x, y in click_targets(g):
        acts.append(("click", x, y, label))
    return acts


def apply_action(env, act):
    if act[0] == "verb":
        return env.step(ACTIONS_BY_INT[act[1]])
    _, x, y, _label = act
    return env.step(GameAction.ACTION6, data={"x": x, "y": y})


def action_repr(act):
    return act[1] if act[0] == "verb" else ("click", act[3], act[1], act[2])


# --- build root ---
arc = arc_agi.Arcade()
root_env = arc.make("cn04")
o0 = reach_l2(root_env)
g0 = g_of(o0)
root_key = board_key(g0)
log(f"[{time.time()-T0:.1f}s] L2 root: lvl={o0.levels_completed} state={o0.state} key={root_key.hex()[:12]}")
n_targets0 = len(click_targets(g0))
log(f"root click-target count: {n_targets0} (branching = {len(VERBS)} verbs + {n_targets0} clicks = {len(VERBS)+n_targets0})")

visited = {root_key}
layer = [(copy.deepcopy(root_env), o0, [])]   # (env, obs, path-of-action_repr)
total_expanded = 0
depth = 0
win_path = None
verdict = None
truncated_layers = []
divergence_events = 0   # count of (state, action) pairs whose result is a NEW state

while layer:
    elapsed = time.time() - T0
    if elapsed > DEADLINE_S:
        verdict = "DEADLINE"
        log(f"[{elapsed:.1f}s] DEADLINE hit at depth {depth}, frontier size {len(layer)} -- stopping")
        break
    if total_expanded > MAX_TOTAL:
        verdict = "MAX_TOTAL"
        log(f"[{elapsed:.1f}s] MAX_TOTAL ({MAX_TOTAL}) hit at depth {depth} -- stopping")
        break
    if depth > MAX_DEPTH:
        verdict = "MAX_DEPTH"
        log(f"[{elapsed:.1f}s] MAX_DEPTH ({MAX_DEPTH}) hit -- stopping")
        break

    if len(layer) > MAX_LAYER:
        truncated_layers.append((depth, len(layer)))
        log(f"[{elapsed:.1f}s] depth {depth}: layer size {len(layer)} > MAX_LAYER {MAX_LAYER} -- TRUNCATING to first {MAX_LAYER} (coverage partial from here)")
        layer = layer[:MAX_LAYER]

    next_layer = []
    layer_new = 0
    layer_dead = 0
    layer_refused_or_dup = 0

    for env, obs, path in layer:
        if total_expanded > MAX_TOTAL or (time.time() - T0) > DEADLINE_S:
            break   # mid-layer safety cut, checked below via verdict=None -> caps re-checked next outer iter
        g_cur = g_of(obs)
        for act in candidate_actions(g_cur):
            total_expanded += 1
            cand_env = copy.deepcopy(env)
            o2 = apply_action(cand_env, act)
            if o2 is None:
                layer_dead += 1
                continue
            if o2.levels_completed >= 2:
                win_path = path + [action_repr(act)]
                log(f"\n*** WIN at depth {depth+1}: path={win_path} ***\n")
                verdict = "WIN"
                break
            g2 = g_of(o2)
            k2 = board_key(g2)
            if k2 in visited:
                layer_refused_or_dup += 1
                continue
            visited.add(k2)
            layer_new += 1
            next_layer.append((cand_env, o2, path + [action_repr(act)]))
        if verdict == "WIN":
            break
    if verdict == "WIN":
        break

    log(f"[{time.time()-T0:.1f}s] depth {depth} -> {depth+1}: expanded {len(layer)} nodes, "
        f"{layer_new} new states, {layer_refused_or_dup} dup/no-op, {layer_dead} dead-on-click, "
        f"total_expanded={total_expanded}, visited={len(visited)}")

    depth += 1
    layer = next_layer

if verdict is None:
    verdict = "EXHAUSTED_NO_WIN"
    log(f"[{time.time()-T0:.1f}s] frontier EMPTY at depth {depth} -- EXHAUSTED, no win found")

log(f"\n=== FINAL: verdict={verdict} depth_reached={depth} total_expanded={total_expanded} "
    f"visited_states={len(visited)} truncated_layers={truncated_layers} elapsed={time.time()-T0:.1f}s ===")

if win_path is not None:
    with open("results/cn04-b2-win.txt", "w", encoding="utf-8") as f:
        f.write(f"WIN path ({len(win_path)} actions): {win_path}\n")
    print("WIN -- wrote results/cn04-b2-win.txt")

with open("results/cn04-b2-bfs.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines) + "\n")
print("wrote results/cn04-b2-bfs.txt")
