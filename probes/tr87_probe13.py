"""tr87: SHAPE match, not exact byte match. probe10 refuted exact cell-equality
(ink=5, both polarities) between each station's own hint icon and its 7
reachable dial states. This tests whether the hint encodes a shape -- same
cell COUNT and same connected pattern up to rotation/reflection -- against
its OWN station's states and, as a bonus, every OTHER station's states too
(in case the hint/station pairing is a permutation, not identity).

Geometry (measured, not re-derived): dial window = g[51:58, x0:x0+5], hint
window = g[40:47, x0:x0+5], both 7 rows with a constant border row top and
bottom (row0, row6) -- crop to the interior 5x5 (rows 1:6) before any
dihedral transform so rotation stays shape-preserving.
"""
import sys
import numpy as np
import arc_agi

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
A = {a.value: a for a in env.action_space}
STATIONS = [15, 22, 29, 36, 43]


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def deck_at(x0, moves_to_station):
    obs = env.reset()
    for _ in range(moves_to_station):
        obs = env.step(A[4])
    g = grid_of(obs)
    d = [(g[51:58, x0:x0 + 5] == 5)[1:6, :]]
    for i in range(6):
        obs = env.step(A[1])
        g = grid_of(obs)
        d.append((g[51:58, x0:x0 + 5] == 5)[1:6, :])
    return d


def dihedral8(mask):
    forms = []
    m = mask
    f = np.fliplr(mask)
    for base in (m, f):
        cur = base
        for _ in range(4):
            forms.append(cur)
            cur = np.rot90(cur)
    return forms


def canon(mask):
    return min(tuple(map(tuple, t.tolist())) for t in dihedral8(mask))


obs = env.reset()
g0 = grid_of(obs)
hints = {}
for x0 in STATIONS:
    m = (g0[40:47, x0:x0 + 5] == 5)[1:6, :]
    hints[x0] = m

print("hint cell counts:", {x0: int(hints[x0].sum()) for x0 in STATIONS})

decks = {}
for st_idx, x0 in enumerate(STATIONS):
    decks[x0] = deck_at(x0, st_idx)

print("deck cell counts (7 states each):")
for x0 in STATIONS:
    print(f"  x={x0}: {[int(s.sum()) for s in decks[x0]]}")

print("\n== exact cell-COUNT coincidences (necessary condition for any shape match, "
      "own station AND cross-station, both polarities) ==")
any_count_hit = False
for hx in STATIONS:
    hc = int(hints[hx].sum())
    hc_inv = 25 - hc
    for dx in STATIONS:
        for i, s in enumerate(decks[dx]):
            sc = int(s.sum())
            if sc == hc:
                print(f"  COUNT MATCH (direct): hint@{hx} ({hc}) == deck@{dx} state{i} ({sc})")
                any_count_hit = True
            if sc == hc_inv:
                print(f"  COUNT MATCH (inverted hint): hint@{hx} inv ({hc_inv}) == deck@{dx} state{i} ({sc})")
                any_count_hit = True
if not any_count_hit:
    print("  none")

print("\n== shape match under 8 dihedral transforms (direct + inverted hint), "
      "own station AND cross-station ==")
any_shape_hit = False
for hx in STATIONS:
    ch = canon(hints[hx])
    ch_inv = canon(~hints[hx])
    for dx in STATIONS:
        for i, s in enumerate(decks[dx]):
            cs = canon(s)
            if cs == ch:
                print(f"  SHAPE MATCH (direct): hint@{hx} == deck@{dx} state{i}")
                any_shape_hit = True
            if cs == ch_inv:
                print(f"  SHAPE MATCH (inverted hint): hint@{hx} == deck@{dx} state{i}")
                any_shape_hit = True
if not any_shape_hit:
    print("  none")

sys.stdout.flush()
