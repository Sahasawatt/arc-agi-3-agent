"""dc22 L2 characterization, round 2 -- fixes dc22_b1.py's plane-count bug
(root frame at L2 entry carries 2 planes, a normal press's frame carries 1,
so a full-array shape compare silently reported every diff as None) and
replaces the coarse click LATTICE with a component-centered click sweep
(bridge.py's own `components()`/`split()` machinery), since dc22_b1's
6px-step lattice can walk straight past a 1x1 button the way L1's buttons
at (48,19)/(48,36) would have been missed by anything coarser than "hit
the exact cell".

Also: multi-plane check across a handful of real presses (not just the
level-transition frame), and a movable-object census by diffing f[-1]
against root[-1] per verb / per click target.
"""
import copy
import json
import time

import numpy as np
import arc_agi

from bridge import Bridge, components, split

T0 = time.time()


def log(msg):
    print("[%6.1fs] %s" % (time.time() - T0, msg), flush=True)


def last(frame_obj):
    return np.array(frame_obj)[-1]


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
info = envs["dc22"]
env = arc.make(info.game_id)
obs = env.reset()
actions = [a for a in env.action_space if not a.is_complex()]
by_value = {a.value: a for a in actions}
values = sorted(by_value)
clicker = next((a for a in env.action_space if a.is_complex()), None)

# replay the known-good L1 recipe via the bridge driver to reach the L2 root
bridge = Bridge(values)
i = 0
while i < 400:
    frame = last(obs.frame)
    cv = bridge.act(frame, obs.levels_completed)
    if cv is None:
        break
    i += 1
    if isinstance(cv, tuple):
        clicker.set_data({"x": cv[1], "y": cv[2]})
        obs = env.step(clicker, data={"x": cv[1], "y": cv[2]})
    else:
        obs = env.step(by_value[cv])
    if obs is None or obs.levels_completed >= 1:
        break
log("L2 root at i=%d lvl=%s" % (i, obs.levels_completed))
assert obs.levels_completed == 1, "did not reach L2 root"

root_full = np.array(obs.frame)
root_last = last(obs.frame)
OUT = {"l1_actions": i, "l2_root_planes": int(root_full.shape[0])}

# ---------- multi-plane check across REAL presses (not just entry) ----------
plane_counts = {"entry": int(root_full.shape[0])}
for v in values:
    b = copy.deepcopy(env)
    o = b.step(by_value[v])
    plane_counts["verb_%s" % v] = int(np.array(o.frame).shape[0]) if o is not None else None
b = copy.deepcopy(env)
clicker.set_data({"x": 32, "y": 32})
o = b.step(clicker, data={"x": 32, "y": 32})
plane_counts["click_center"] = int(np.array(o.frame).shape[0]) if o is not None else None
OUT["plane_counts"] = plane_counts
log("plane counts: %s" % plane_counts)

# ---------- board geometry at L2 (do not assume L1's split/twins transfer) ----------
geom = {}
s = split(root_last)
geom["split"] = None if s is None else {"play": s[0], "panel": s[1], "pbg": s[2], "nbg": s[3]}
log("split() at L2 root: %s" % geom["split"])
comps_all = components(root_last, int(np.bincount(root_last.flatten()).argmax()))
geom["n_components_whole_frame"] = len(comps_all)
geom["component_sizes"] = sorted({c[5] for c in comps_all})
OUT["geometry"] = geom
log("whole-frame components at L2 root: n=%d sizes=%s" % (len(comps_all), geom["component_sizes"]))

# ---------- movable objects per verb: diff f[-1] vs root[-1], last plane only ----------
verb_probe = {}
for v in values:
    b = copy.deepcopy(env)
    o = b.step(by_value[v])
    if o is None:
        verb_probe[str(v)] = {"obs_none": True}
        continue
    f = last(o.frame)
    changed = int((f != root_last).sum()) if f.shape == root_last.shape else "SHAPE_MISMATCH:%s" % (f.shape,)
    verb_probe[str(v)] = {
        "levels_completed": o.levels_completed,
        "state": str(o.state),
        "changed_cells": changed,
    }
    log("verb %s -> changed=%s lvl=%s state=%s" % (v, changed, o.levels_completed, o.state))
OUT["verb_probe"] = verb_probe

# ---------- component-centered click sweep (targeted, not a coarse lattice) ----------
# Click the CENTRE of every distinct non-background component in the L2 root
# frame -- this is exactly how bridge.py finds its own buttons, so it is the
# right instrument to re-run at L2 rather than trusting a lattice to land on
# a 1-cell target.
bg = int(np.bincount(root_last.flatten()).argmax())
targets = components(root_last, bg)
click_results = []
for (x0, x1, y0, y1, col, size) in targets:
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    b = copy.deepcopy(env)
    clicker.set_data({"x": cx, "y": cy})
    o = b.step(clicker, data={"x": cx, "y": cy})
    if o is None:
        click_results.append({"x": cx, "y": cy, "colour": col, "size": size, "obs_none": True})
        continue
    f = last(o.frame)
    changed = int((f != root_last).sum()) if f.shape == root_last.shape else "SHAPE_MISMATCH:%s" % (f.shape,)
    click_results.append({
        "x": cx, "y": cy, "colour": col, "size": size,
        "levels_completed": o.levels_completed, "state": str(o.state),
        "changed_cells": changed,
    })
responsive = [c for c in click_results
              if isinstance(c.get("changed_cells"), int) and c["changed_cells"] > 0]
OUT["click_targets_total"] = len(click_results)
OUT["click_results"] = click_results
OUT["click_responsive"] = responsive
log("component-centered click sweep: %d targets, %d responsive"
    % (len(click_results), len(responsive)))
for r in responsive:
    log("  RESPONSIVE click (%d,%d) colour=%d size=%d changed=%d"
        % (r["x"], r["y"], r["colour"], r["size"], r["changed_cells"]))

# ---------- death/revert with a positive control ----------
# Positive control: two independent fresh deepcopies pressing the same verb
# must agree byte-for-byte (sanity on the deepcopy branch mechanism).
ca, cb = copy.deepcopy(env), copy.deepcopy(env)
oa = ca.step(by_value[values[0]])
obb = cb.step(by_value[values[0]])
ctrl_agree = (np.array(oa.frame).tobytes() == np.array(obb.frame).tobytes()) if oa is not None and obb is not None else None
OUT["positive_control_agree"] = ctrl_agree
log("positive control (2 fresh copies, same verb): agree=%s" % ctrl_agree)

death_probe = {}
for v in values:
    b = copy.deepcopy(env)
    o = None
    final_state, steps = None, 0
    for k in range(80):
        o = b.step(by_value[v])
        steps = k + 1
        if o is None:
            final_state = "OBS_NONE"
            break
        st = str(o.state)
        if st not in ("GameState.NOT_FINISHED",):
            final_state = st
            break
    death_probe[str(v)] = {"steps": steps, "final_state": final_state,
                            "last_levels_completed": o.levels_completed if o is not None else None}
    log("death probe verb %s x80: steps=%d final=%s lvl=%s"
        % (v, steps, final_state, death_probe[str(v)]["last_levels_completed"]))
OUT["death_probe"] = death_probe

json.dump(OUT, open("results/dc22-b2-log.json", "w"), indent=2, default=str)
log("wrote results/dc22-b2-log.json")
print("DONE", flush=True)
