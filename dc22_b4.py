"""Diagnose why `bridge`'s generic driver stalls 13 actions into L2 (dc22_b3:
LEVEL UP at i=25, `bridge returned None` at i=38, after re-probing the 4
movement directions and clicking both large-effect components once each).
Dump bridge.read() (play/panel split, twins) at the L2 root and after each
button press, plus route()/frontier() results, to see whether the stall is
"twins misidentified" or "route genuinely absent from every reachable tile".
"""
import copy
import time

import numpy as np
import arc_agi

from bridge import Bridge, read, route, components

T0 = time.time()


def log(msg):
    print("[%6.1fs] %s" % (time.time() - T0, msg), flush=True)


def last(o):
    return np.array(o.frame)[-1]


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["dc22"].game_id)
obs = env.reset()
actions = [a for a in env.action_space if not a.is_complex()]
by_value = {a.value: a for a in actions}
values = sorted(by_value)
clicker = next((a for a in env.action_space if a.is_complex()), None)

bridge = Bridge(values)
i = 0
while i < 400:
    frame = last(obs)
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
log("L2 root i=%d lvl=%s" % (i, obs.levels_completed))

root = last(obs)
b = read(root)
log("read() at L2 root: play=%s panel=%s pbg=%s nbg=%s" % (b["play"], b["panel"], b["pbg"], b["nbg"]))
log("twins: %s" % (b["twins"],))
here = {t[4]: (t[0], t[2]) for t in b["twins"]}
log("twin positions by colour: %s" % here)

# which twin is the piece? probe motion directly (independent branches)
for v in values:
    br = copy.deepcopy(env)
    o = br.step(by_value[v])
    if o is None:
        continue
    f2 = last(o)
    b2 = read(f2)
    if b2 is None:
        log("verb %s: read() failed post-move" % v)
        continue
    here2 = {t[4]: (t[0], t[2]) for t in b2["twins"]}
    moved = [c for c, p in here2.items() if c in here and here[c] != p]
    log("verb %s -> twins now %s moved=%s" % (v, here2, moved))

# button components in panel, as bridge.buttons would compute them
panel = root[:, b["panel"][0]:b["panel"][1] + 1]
wide = panel.shape[1] - 1
btn = []
for c in components(panel, b["nbg"]):
    if c[5] < 20 or c[0] == 0 or c[1] >= wide:
        continue
    at = ((c[0] + c[1]) // 2 + b["panel"][0], (c[2] + c[3]) // 2)
    if at not in btn:
        btn.append(at)
log("bridge-style buttons detected: %s" % btn)

# route from each twin position to the other, on the ROOT board
tw_positions = list(here.values())
if len(tw_positions) == 2:
    p0, p1 = tw_positions
    path01 = route(root, b, p0, p1)
    log("route(twin0->twin1) at root: %s" % (path01,))

# press each detected button ONCE (independent branches from root), then
# re-read geometry + try the route again
for (bx, by) in btn:
    br = copy.deepcopy(env)
    clicker.set_data({"x": bx, "y": by})
    o = br.step(clicker, data={"x": bx, "y": by})
    if o is None:
        log("button (%d,%d): obs None" % (bx, by))
        continue
    f2 = last(o)
    b2 = read(f2)
    if b2 is None:
        log("button (%d,%d): read() failed after press" % (bx, by))
        continue
    here2 = {t[4]: (t[0], t[2]) for t in b2["twins"]}
    log("button (%d,%d) -> twins now %s" % (bx, by, here2))
    if len(here2) == 2:
        p0, p1 = list(here2.values())
        p2 = route(f2, b2, p0, p1)
        log("  route(twin0->twin1) after this button: %s" % (p2,))

# press BOTH buttons together (sequential on one branch) and re-check
br = copy.deepcopy(env)
for (bx, by) in btn:
    clicker.set_data({"x": bx, "y": by})
    o = br.step(clicker, data={"x": bx, "y": by})
if o is not None:
    f2 = last(o)
    b2 = read(f2)
    if b2 is not None:
        here2 = {t[4]: (t[0], t[2]) for t in b2["twins"]}
        log("BOTH buttons pressed -> twins now %s" % here2)
        if len(here2) == 2:
            p0, p1 = list(here2.values())
            p2 = route(f2, b2, p0, p1)
            log("  route(twin0->twin1) after both buttons: %s" % (p2,))
    else:
        log("BOTH buttons pressed -> read() failed")

print("DONE", flush=True)
