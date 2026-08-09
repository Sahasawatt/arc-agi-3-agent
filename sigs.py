"""Every SHIPPED whole-game-driver signature, run against every playable
game's reset frame in one invocation.

    ./.venv/Scripts/python.exe sigs.py

This is the check CLAUDE.md asks for before another driver is wired, and it
carries its own controls: each driver must fire on exactly the game it was
built for, and no game may be claimed by two.

Why it exists rather than the per-driver `*_sig.py` scripts: those print a
CANDIDATE table and the candidate predicates chosen from it, which is the right
way to pick a signature and the wrong way to verify one. `maze_sig.py`'s two
candidates each fire on five games; `maze.signature`, the function actually
wired into the loop, is neither of them.
"""

import sys

import numpy as np

import arc_agi
from compete import PLAYABLE
from cover import signature as cover_sig
from swap import signature as swap_sig
from haul import signature as haul_sig
from maze import signature as maze_sig
from dial import signature as dial_sig

SIGS = {"cover": cover_sig, "swap": swap_sig, "haul": haul_sig,
        "maze": maze_sig, "dial": dial_sig}
OWNER = {"swap": "sp80", "haul": "wa30", "maze": "tu93", "dial": "tr87"}
# `cover` predates this script and is the loose one -- it fires on four games,
# and the sweep is what shows it only ever ENGAGES re86 (a driver handed a board
# it cannot read answers None on its first round). So it is not checked for
# exclusivity; what is checked instead is that wherever two signatures claim the
# same game, the driver built for it is asked FIRST. That order is the wiring in
# `compete.play`, and this list must be kept equal to it.
CASCADE = ["dial", "cover", "swap", "haul", "maze"]


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
hits, fired = {}, {}
print("game    " + "  ".join(f"{k:6s}" for k in SIGS))
for name in PLAYABLE:
    g = grid_of(arc.make(envs[name].game_id).reset())
    if g is None:
        print(f"{name}  EMPTY FRAME AT RESET")
        continue
    row = {k: bool(f(g)) for k, f in SIGS.items()}
    hits[name] = row
    for k, v in row.items():
        if v:
            fired.setdefault(k, []).append(name)
    print(f"{name:6s}  " + "  ".join(f"{str(row[k]):6s}" for k in SIGS), flush=True)

print("\nfired:", {k: fired.get(k, []) for k in SIGS})
wrong = {k: fired.get(k, []) for k, g in OWNER.items() if fired.get(k) != [g]}
print("drivers not firing on exactly their own game:", wrong)

owner_of = {g: k for k, g in OWNER.items()}
misordered = {}
for name, row in hits.items():
    claim = [k for k in CASCADE if row.get(k)]
    if len(claim) > 1:
        want = owner_of.get(name)
        print(f"contested: {name} claimed by {claim}; asked first = {claim[0]}"
              + (f", built for it = {want}" if want else ", built for by none"))
        if want and claim[0] != want:
            misordered[name] = (claim[0], want)
print("contested games where the wrong driver is asked first:", misordered)
ok = not wrong and not misordered
print("VERDICT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
