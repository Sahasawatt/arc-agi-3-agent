"""dc22 L1 recipe + L2 fresh characterization.

1. Replay the `bridge` driver (bridge.py, the exact module wired into
   compete.py's play loop) from a fresh reset until obs.levels_completed==1.
   Record the full action trace -> results/dc22-L1-recipe.json.
2. From that L2 root (no L2 actions taken yet), characterize the board:
   movable objects per verb (deepcopy branches, frame diffs), click sweep
   at a coarse lattice, death/revert with a positive control, multi-plane
   check (does dc22 return >1 plane on any action?).
3. Deepcopy fidelity control (g50t_r1.py pattern): deepcopy the env at the
   L2 root, diverge the original by one action, confirm the copy's frame
   is untouched and its own step reproduces what the original would have
   done from the root.

Output: results/dc22-b1-log.json (raw data for the report writer).
"""
import copy
import json
import os
import sys
import time

os.environ.setdefault("PYTHONUTF8", "1")
import numpy as np
import arc_agi

from bridge import Bridge

OUT = {}
T0 = time.time()


def log(msg):
    print("[%6.1fs] %s" % (time.time() - T0, msg), flush=True)


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
info = envs["dc22"]
env = arc.make(info.game_id)

obs = env.reset()
actions = [a for a in env.action_space if not a.is_complex()]
by_value = {a.value: a for a in actions}
values = sorted(by_value)
clicker = next((a for a in env.action_space if a.is_complex()), None)
log("reset ok, values=%s clicker=%s" % (values, clicker))

# ---------- Part 1: replay bridge driver to the L2 root ----------
bridge = Bridge(values)
trace = []
i = 0
MAXI = 400
stuck_reason = None
while i < MAXI:
    frame = np.array(obs.frame)[-1]
    cv = bridge.act(frame, obs.levels_completed)
    if cv is None:
        stuck_reason = "bridge returned None at i=%d lvl=%d" % (i, obs.levels_completed)
        log(stuck_reason)
        break
    i += 1
    if isinstance(cv, tuple):
        clicker.set_data({"x": cv[1], "y": cv[2]})
        obs = env.step(clicker, data={"x": cv[1], "y": cv[2]})
        trace.append({"i": i, "type": "click", "x": cv[1], "y": cv[2]})
    else:
        obs = env.step(by_value[cv])
        trace.append({"i": i, "type": "move", "v": cv})
    if obs is None:
        stuck_reason = "obs None at i=%d" % i
        log(stuck_reason)
        break
    log("i=%d lvl=%d act=%s state=%s" % (i, obs.levels_completed, cv, obs.state))
    if obs.levels_completed >= 1:
        log("REACHED LEVEL 1 at i=%d" % i)
        break

OUT["l1_trace"] = trace
OUT["l1_actions"] = i
OUT["l1_final_levels_completed"] = obs.levels_completed if obs is not None else None
OUT["l1_stuck_reason"] = stuck_reason
OUT["l1_state"] = str(obs.state) if obs is not None else None

if obs is None or obs.levels_completed < 1:
    log("FATAL: did not reach level 1, aborting characterization")
    json.dump(OUT, open("results/dc22-b1-log.json", "w"), indent=2, default=str)
    sys.exit(1)

l2_root_frame = np.array(obs.frame)  # keep ALL planes, not just [-1]
OUT["l2_root_planes"] = int(l2_root_frame.shape[0])
OUT["l2_root_shape"] = list(l2_root_frame.shape)
log("L2 root captured: planes=%d shape=%s" % (l2_root_frame.shape[0], l2_root_frame.shape))

# ---------- Part 2: deepcopy fidelity control (g50t_r1.py pattern) ----------
# Deepcopy the env at the L2 root, diverge the ORIGINAL by one action, and
# confirm the copy is untouched (frame identical to the root) while its own
# independent step reproduces the same transition the original just took.
try:
    env_copy = copy.deepcopy(env)
except Exception as e:
    OUT["deepcopy_error"] = repr(e)
    env_copy = None
    log("deepcopy FAILED: %r" % e)

fidelity = {}
if env_copy is not None:
    root_frame_bytes = np.array(obs.frame).tobytes()
    # take one real action on the ORIGINAL to diverge it
    probe_action = by_value[values[0]]
    obs_after_orig = env.step(probe_action)
    orig_after_bytes = np.array(obs_after_orig.frame).tobytes() if obs_after_orig is not None else None
    # take the SAME action on the independent COPY, starting from its own
    # (untouched) root state
    obs_after_copy = env_copy.step(probe_action)
    copy_after_bytes = np.array(obs_after_copy.frame).tobytes() if obs_after_copy is not None else None
    fidelity["probe_action_value"] = values[0]
    fidelity["orig_after_lvl"] = obs_after_orig.levels_completed if obs_after_orig is not None else None
    fidelity["copy_after_lvl"] = obs_after_copy.levels_completed if obs_after_copy is not None else None
    fidelity["orig_vs_copy_after_identical"] = (orig_after_bytes == copy_after_bytes)
    fidelity["copy_after_matches_root"] = (copy_after_bytes == root_frame_bytes)
    log("fidelity: orig==copy after same action? %s (should be True); copy==root after action? %s (should be False unless action was refused)"
        % (fidelity["orig_vs_copy_after_identical"], fidelity["copy_after_matches_root"]))
    # restore: continue characterizing from a FRESH deepcopy of the true L2 root,
    # re-deepcopied from env_copy's pre-step state is gone now (we stepped it too).
    # So re-derive a clean L2-root copy from the ORIGINAL env by deepcopy-ing env
    # BEFORE we take further probing actions on it -- but we already advanced
    # `env` by one action above. Use env_copy's sibling: deepcopy env_copy is
    # ALSO one action past root. We need a NEW deepcopy taken at the true root,
    # which we no longer have since both env and env_copy have moved.
    # Fix: we captured obs at root before this block; re-derive root env by
    # deepcopy of env_copy is invalid too. Simplest correct fix: this control
    # consumed its own root. Re-establish root explicitly below (Part 2b).
OUT["deepcopy_fidelity"] = fidelity

# ---------- Part 2b: re-establish a clean L2 root for characterization ----------
# `env` advanced by one probe action in Part 2. Deepcopy it is NOT the root.
# Take deepcopies from THIS point on (post-probe) and call this "L2 root+1"
# honestly -- OR replay from scratch to get a truly clean root. Replaying is
# cheap (400 actions max, measured ~i above) and avoids ambiguity.
log("re-replaying bridge driver from scratch for a CLEAN L2 root (previous env consumed by fidelity probe)")
env2 = arc.make(info.game_id)
obs2 = env2.reset()
bridge2 = Bridge(values)
i2 = 0
while i2 < MAXI:
    frame = np.array(obs2.frame)[-1]
    cv = bridge2.act(frame, obs2.levels_completed)
    if cv is None:
        break
    i2 += 1
    if isinstance(cv, tuple):
        clicker.set_data({"x": cv[1], "y": cv[2]})
        obs2 = env2.step(clicker, data={"x": cv[1], "y": cv[2]})
    else:
        obs2 = env2.step(by_value[cv])
    if obs2 is None or obs2.levels_completed >= 1:
        break
log("clean L2 root: i2=%d lvl=%s (should match i=%d lvl=%s from part 1)"
    % (i2, obs2.levels_completed if obs2 is not None else None, i, obs.levels_completed))
OUT["l2_root_replay_actions"] = i2
OUT["l2_root_replay_matches_part1"] = (i2 == i)

if obs2 is None or obs2.levels_completed < 1:
    log("FATAL: clean replay did not reach L2, aborting further characterization")
    json.dump(OUT, open("results/dc22-b1-log.json", "w"), indent=2, default=str)
    sys.exit(1)

root_frame_full = np.array(obs2.frame)
root_bytes = root_frame_full.tobytes()
OUT["l2_root_frame_shape"] = list(root_frame_full.shape)
OUT["l2_root_planes_confirmed"] = int(root_frame_full.shape[0])

# ---------- Part 3: movable objects per verb, via deepcopy branches ----------
# From the CLEAN root (env2/obs2), for each of the 4 movement verbs AND the
# click action, deepcopy env2, take ONE action on the copy, diff the frame
# against root. This never advances env2 itself -- every branch starts fresh.
verb_results = {}
for v in values:
    try:
        branch = copy.deepcopy(env2)
    except Exception as e:
        verb_results[str(v)] = {"error": repr(e)}
        continue
    o = branch.step(by_value[v])
    if o is None:
        verb_results[str(v)] = {"obs_none": True}
        continue
    f = np.array(o.frame)
    changed = int((f[-1] != root_frame_full[-1]).sum()) if f.shape == root_frame_full.shape else None
    verb_results[str(v)] = {
        "levels_completed": o.levels_completed,
        "state": str(o.state),
        "planes": int(f.shape[0]),
        "changed_cells_last_plane": changed,
        "frame_shape": list(f.shape),
        "shape_matches_root": f.shape == root_frame_full.shape,
    }
    log("verb %s -> lvl=%s state=%s planes=%d changed=%s"
        % (v, o.levels_completed, o.state, f.shape[0], changed))
OUT["l2_verb_probe"] = verb_results

# ---------- Part 4: click-then-ACT sweep on a coarse lattice ----------
# dc22's play area / panel split (bridge.split) tells us the board's actual
# extent; sweep a coarse grid over the WHOLE frame (play + panel) since L2's
# layout is unmeasured -- do not assume bridge.split's L1 geometry transfers.
h, w = root_frame_full.shape[-2], root_frame_full.shape[-1]
STEP_X = max(1, w // 10)
STEP_Y = max(1, h // 10)
click_grid = [(x, y) for y in range(0, h, STEP_Y) for x in range(0, w, STEP_X)]
log("click sweep: %d points over frame %dx%d" % (len(click_grid), w, h))
click_results = []
for (cx, cy) in click_grid:
    try:
        branch = copy.deepcopy(env2)
    except Exception as e:
        click_results.append({"x": cx, "y": cy, "error": repr(e)})
        continue
    clicker.set_data({"x": cx, "y": cy})
    o = branch.step(clicker, data={"x": cx, "y": cy})
    if o is None:
        click_results.append({"x": cx, "y": cy, "obs_none": True})
        continue
    f = np.array(o.frame)
    changed = int((f[-1] != root_frame_full[-1]).sum()) if f.shape == root_frame_full.shape else None
    click_results.append({
        "x": cx, "y": cy,
        "levels_completed": o.levels_completed,
        "state": str(o.state),
        "planes": int(f.shape[0]),
        "changed_cells_last_plane": changed,
    })
responsive = [c for c in click_results if c.get("changed_cells_last_plane", 0)]
log("click sweep done: %d/%d points changed something" % (len(responsive), len(click_grid)))
OUT["l2_click_sweep"] = click_results
OUT["l2_click_responsive"] = responsive

# ---------- Part 5: death/revert behaviour, with a positive control ----------
# Positive control: repeat the SAME verb probe twice from independent fresh
# deepcopies -- must agree (sanity on the deepcopy branch mechanism itself).
ctrl_a = copy.deepcopy(env2)
ctrl_b = copy.deepcopy(env2)
oa = ctrl_a.step(by_value[values[0]])
ob = ctrl_b.step(by_value[values[0]])
control_agree = (np.array(oa.frame).tobytes() == np.array(ob.frame).tobytes()) if oa is not None and ob is not None else None
OUT["positive_control_two_fresh_copies_agree"] = control_agree
log("positive control (2 fresh copies, same verb): agree=%s" % control_agree)

# Death/revert: press every verb repeatedly (deepcopy branch, up to 60 presses)
# looking for a GAME_OVER state or a board reset back toward the root.
death_probe = {}
for v in values:
    branch = copy.deepcopy(env2)
    o = obs2
    seen_state = None
    steps_taken = 0
    for k in range(60):
        o = branch.step(by_value[v])
        steps_taken = k + 1
        if o is None:
            seen_state = "OBS_NONE"
            break
        if str(o.state) not in ("GameState.NOT_FINISHED", "NOT_FINISHED"):
            seen_state = str(o.state)
            break
    death_probe[str(v)] = {"steps": steps_taken, "final_state": seen_state}
    log("death probe verb %s: %d steps -> %s" % (v, steps_taken, seen_state))
OUT["l2_death_probe"] = death_probe

json.dump(OUT, open("results/dc22-b1-log.json", "w"), indent=2, default=str)
log("wrote results/dc22-b1-log.json")
print("DONE", flush=True)
