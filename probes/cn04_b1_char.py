"""cn04 L2 BFS session, script 1: reach the L2 root, deepcopy-fidelity control,
and action-space characterization (plain verbs ACTION1-7, plus a few clicks).

Writes results/cn04-b1-char.txt. flush=True throughout (long-running discipline).
"""
import copy
import time
import numpy as np
import arc_agi
from arcengine import GameAction

T0 = time.time()
out = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.append(s)


L1_LINE = [GameAction.ACTION5] * 3 + [GameAction.ACTION2] * 7 + [GameAction.ACTION4] * 4

arc = arc_agi.Arcade()
env = arc.make("cn04")


def reach_l2():
    o = env.reset()
    if o.levels_completed >= 1:
        return o
    last = o
    for act in L1_LINE:
        last = env.step(act)
        assert last is not None, "died mid L1 replay"
    assert last.levels_completed >= 1, f"L1 line failed to win: lvl={last.levels_completed}"
    return last


def g_of(o):
    return np.array(o.frame)[-1]


def census(g):
    c = {}
    for col in np.unique(g):
        c[int(col)] = int((g == col).sum())
    return c


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


def centroid(comp):
    ys = [c[0] for c in comp]
    xs = [c[1] for c in comp]
    return int(round(sum(ys) / len(ys))), int(round(sum(xs) / len(xs)))


# --- 1. reach root, record baseline ---
o0 = reach_l2()
g0 = g_of(o0)
log(f"[{time.time()-T0:.1f}s] L2 ROOT reached: levels_completed={o0.levels_completed} state={o0.state}")
log(f"root census: {sorted(census(g0).items())}")
np.save("results/cn04-b-root.npy", g0)

# --- 2. deepcopy fidelity control ---
log("\n=== deepcopy fidelity control ===")
copyA = copy.deepcopy(env)
copyB = copy.deepcopy(env)
oa = copyA.step(GameAction.ACTION2)
ob = copyB.step(GameAction.ACTION2)
ga, gb = g_of(oa), g_of(ob)
same_step = bool((ga == gb).all())
log(f"two independent deepcopies stepped with identical action (ACTION2): frames identical = {same_step}")

# original env must be untouched by stepping the copies
o_check = env.step(GameAction.ACTION1)  # step the ORIGINAL differently
g_orig_after = g_of(o_check)
# copyA/copyB should not reflect this action, and their own state should not have changed
oa2_frame = g_of(oa)
diverged_from_orig = bool((oa2_frame != g_orig_after).any())
log(f"original env stepped independently (ACTION1) after copies were taken and stepped: "
    f"original diverges from copyA's post-ACTION2 frame = {diverged_from_orig} (expected True)")

# re-derive root fresh (env mutated above) and re-copy to confirm copy-of-copy also fidelity-safe
o0b = reach_l2()
g0b = g_of(o0b)
root_reproducible = bool((g0b == g0).all())
log(f"root re-derived via reach_l2() again (fresh replay of L1_LINE): byte-identical to first root = {root_reproducible}")

copyC = copy.deepcopy(env)
copyD = copy.deepcopy(copyC)
oc = copyC.step(GameAction.ACTION4)
od = copyD.step(GameAction.ACTION4)
copy_of_copy_ok = bool((g_of(oc) == g_of(od)).all())
log(f"copy-of-a-copy, same action: identical = {copy_of_copy_ok}")

# --- 3. characterize plain verbs ACTION1-7 from a fresh root each time ---
log("\n=== plain verb characterization (each from a FRESH root copy) ===")
ACTIONS_BY_INT = {int(a.value): a for a in GameAction}
for a in range(1, 8):
    act = ACTIONS_BY_INT[a]
    reach_l2()
    fresh = copy.deepcopy(env)
    o1 = fresh.step(act)
    if o1 is None:
        log(f"ACTION{a}: obs=None (died)")
        continue
    g1 = g_of(o1)
    diff = int((g1 != g0).sum())
    lvl = o1.levels_completed
    log(f"ACTION{a}: state={o1.state} lvl={lvl} changed_cells={diff}")
    if diff > 0 and diff < 40:
        # show exactly which colours moved, cheap enough to be useful
        cb, ca = census(g0), census(g1)
        deltas = {c: (cb.get(c, 0), ca.get(c, 0)) for c in set(cb) | set(ca) if cb.get(c, 0) != ca.get(c, 0)}
        log(f"    census delta: {deltas}")

# --- 4. click characterization: click centroid of each shape colour present ---
log("\n=== click characterization (ACTION6 at each shape's centroid, fresh root each time) ===")
SHAPE_COLOURS = (0, 9, 11, 14)
for colour in SHAPE_COLOURS:
    reach_l2()
    fresh = copy.deepcopy(env)
    g_now = g_of(fresh.reset()) if False else g0  # root frame already known
    comps = blobs(g0, colour, min_size=5)
    if not comps:
        log(f"colour {colour}: no blob >=5 cells at root, skipping")
        continue
    comps.sort(key=len, reverse=True)
    cy, cx = centroid(comps[0])
    oc = fresh.step(GameAction.ACTION6, data={"x": cx, "y": cy})
    if oc is None:
        log(f"click colour{colour} centroid (y={cy},x={cx}): obs=None (died)")
        continue
    gc = g_of(oc)
    diff = int((gc != g0).sum())
    cb, ca = census(g0), census(gc)
    deltas = {c: (cb.get(c, 0), ca.get(c, 0)) for c in set(cb) | set(ca) if cb.get(c, 0) != ca.get(c, 0)}
    log(f"click colour{colour} centroid (y={cy},x={cx}): lvl={oc.levels_completed} changed_cells={diff} delta={deltas}")

log(f"\n[{time.time()-T0:.1f}s] DONE")
with open("results/cn04-b1-char.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
print("wrote results/cn04-b1-char.txt")
