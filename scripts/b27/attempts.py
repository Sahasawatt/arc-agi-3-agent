"""Level-attempt layer, reconstructed. R29's scripts/b27/ is not in the repo.

Attribution rule: `level_completed` rides the event for the level the run is ENTERING,
so a naive read marks level 1 uncleared in every run. An attempt at level L is cleared
iff the run ever reached a level > L. Validated below against every per-pair number R29
published (lp85 27v8, ar25 29v4, cn04 29v11, dc22 31v15) plus 237 attempts / 115 pairs.
"""
import collections
from corpus import RUNS5, game_files, load_game, game_key

def attempts_for(run):
    out = {}
    maxlvl = collections.defaultdict(int)
    for f in game_files(run):
        g = game_key(f)
        for e in load_game(f):
            lvl = e.get("level")
            if lvl is None:
                continue
            maxlvl[g] = max(maxlvl[g], lvl)
            a = out.setdefault((g, lvl), {"turns": [], "n_actions": 0})
            if e.get("type") == "analysis":
                t = e.get("transcript")
                if t:
                    a["turns"].append(t)
            elif e.get("type") == "action":
                a["n_actions"] += 1
    for (g, lvl), a in out.items():
        a["cleared"] = maxlvl[g] > lvl
    return out

def load_all():
    return {r: attempts_for(r) for r in RUNS5}

def pairs(ALL):
    bykey = collections.defaultdict(dict)
    for r, v in ALL.items():
        for k, a in v.items():
            bykey[k][r] = a
    out = []
    for k, runs in bykey.items():
        s = [(r, a) for r, a in runs.items() if not a["cleared"]]
        c = [(r, a) for r, a in runs.items() if a["cleared"]]
        for sr, sa in s:
            for cr, ca in c:
                out.append((k, sr, sa, cr, ca))
    return out

if __name__ == "__main__":
    ALL = load_all()
    total = sum(len(v) for v in ALL.values())
    cl = sum(1 for v in ALL.values() for a in v.values() if a["cleared"])
    P = pairs(ALL)
    print(f"level-attempts = {total}  (R29: 237)  match={total==237}   cleared={cl} stuck={total-cl}")
    print(f"stuck/cleared pairs = {len(P)}  (R29: 115)  match={len(P)==115}")
    print()
    print("R29 §1 named pairs — control (stuck turns vs turns to clear):")
    want = {"lp85": (27, 8), "ar25": (29, 4), "cn04": (29, 11), "dc22": (31, 15)}
    for k, sr, sa, cr, ca in P:
        pre = k[0][:4]
        if pre in want and (len(sa["turns"]), len(ca["turns"])) == want[pre]:
            print(f"   {pre} L{k[1]}  stuck {sr}={len(sa['turns'])}  cleared {cr}={len(ca['turns'])}"
                  f"   R29 says {want[pre]}  MATCH")
    print()
    ge = sum(1 for k, sr, sa, cr, ca in P if len(sa["turns"]) >= len(ca["turns"]))
    print(f"§1 restated: stuck turns >= cleared turns in {ge} of {len(P)}"
          f" = {100*ge/len(P):.1f}%   (R29: 97 of 115 = 84.3%)  match={ge==97}")
