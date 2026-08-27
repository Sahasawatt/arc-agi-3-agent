r"""B52 -- why games pass and why they fail, from the per-level field nobody had parsed.

Every game's [finished] line carries  per-level=SPENT/HUMAN,...  -- actions this run spent on each
level against that game's own human baseline. Cleared levels come first, then the level the game
died on, then 0/H for levels never reached. Nine runs of prose never read it.

READS THE BANKED FIXTURE, NOT THE API -- eval/fixtures/per-level-census.json. On 2026-08-28 the
cell-0 retitle push (#81) created save-only versions of every yocybercode/ kernel, and
kernels_logs() takes no version argument, so those seven runs' real logs now serve an 800-char
nbconvert stub. The fixture was built from logs fetched 2026-08-27/28, before, with the
LEDGER-actions control passing 21/21 at build time. It is the surviving copy.

Classification of a game-run that did not win (none ever has):
  ZERO     0 actions all run                            (B40's population)
  STARVED  died with SPENT < HUMAN on the dying level   (the wall arrived first)
  STUCK    died with SPENT >= HUMAN                     (had the budget, did not solve)

WARNING -- STARVED is the shape of the corpse, not the cause of death. Both causal tests are on
the LEDGER: clock2x DOUBLED the wall for +2 levels, and solo sk48 got 1.31x its human count and
stayed 0/8. Budget converts to levels only where reasoning already works (solo lp85 cleared L1 at
9/17, then starved at L2 5/38). And SPENT counts EXECUTED actions only -- B40's no-action turns
(~30% of turns) and B45's abandoned generation spend clock without appearing here.

    python eval/per_level_census.py          # no network, no slot
"""
import collections
import json
import pathlib
import statistics as st

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "per-level-census.json"

# The in-band family: every anim/v10-derived run at the normal or doubled clock. Excluded:
# v20 (MoE swap, 0.18) and v21 (reasoning_effort, 1.25) are refuted regimes; the two solo runs
# give ONE game the whole clock.
FAMILY = ["v10cal", "v14", "v16", "v18", "v19", "v22", "v23", "v24", "v25", "v26",
          "thui-v1-0", "thui-v1-1", "thui-v1-1-r2", "thui-v2-0", "thui-v3-0", "thui-v4-0",
          "clock2x"]


def main():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))["runs"]
    recs = {}
    for run in FAMILY:
        byg = data[run]
        assert len(byg) == 25, (run, len(byg))
        for g, d in byg.items():
            assert len(d["per_level"]) == d["total"], (run, g)
            assert sum(p[0] for p in d["per_level"]) == d["actions"], (run, g)
        recs[run] = byg
    games = sorted(recs["v10cal"])
    n = len(FAMILY) * 25

    cls = collections.Counter()
    cleared, stalled = [], []
    per_game = {g: {"lv": [], "cls": collections.Counter()} for g in games}
    for run in FAMILY:
        for g, d in recs[run].items():
            lv, tot, act, pairs = d["levels"], d["total"], d["actions"], d["per_level"]
            cleared += [tuple(p) for p in pairs[:lv]]
            if lv < tot:
                sp, hu = pairs[lv]
                stalled.append((sp, hu))
                c = "ZERO" if act == 0 else ("STARVED" if sp < hu else "STUCK")
            else:
                c = "WON"
            cls[c] += 1
            per_game[g]["lv"].append(lv)
            per_game[g]["cls"][c] += 1
    assert sum(cls.values()) == n

    print(f"family: {len(FAMILY)} runs x 25 games = {n} game-runs, {len(cleared)} levels cleared")
    for k, v in cls.most_common():
        print(f"  {k:8s} {v:>4}  ({100.0 * v / n:.1f}%)")

    rc = sorted(s / h for s, h in cleared)
    print(f"\ncleared levels: spent/human median {st.median(rc):.2f} "
          f"(p25 {rc[len(rc)//4]:.2f}, p75 {rc[3*len(rc)//4]:.2f}); "
          f"human baseline median {st.median(sorted(h for _, h in cleared))}")
    print(f"stalled levels: human baseline median {st.median(sorted(h for _, h in stalled))}")

    # frontier cut: a stall is either at a level some sibling run cleared (draw variance), or at
    # the game's all-time deepest -- a level NO family run has ever cleared.
    best = {g: max(recs[r][g]["levels"] for r in FAMILY) for g in games}
    frontier = sum(1 for r in FAMILY for g in games
                   if recs[r][g]["levels"] < recs[r][g]["total"]
                   and recs[r][g]["levels"] >= best[g])
    behind = sum(cls[k] for k in ("STARVED", "STUCK", "ZERO")) - frontier
    print(f"\nstalls BEHIND the game's own frontier (a sibling run cleared that level): "
          f"{behind} ({100.0 * behind / (frontier + behind):.0f}%)  <- draw variance")
    print(f"stalls AT the frontier (no family run ever cleared it):                  "
          f"{frontier} ({100.0 * frontier / (frontier + behind):.0f}%)")
    print(f"best-ever oracle (sum of each game's deepest): {sum(best.values())} levels "
          f"vs best single run "
          f"{max(sum(recs[r][g]['levels'] for g in games) for r in FAMILY)}")

    print(f"\n{'game':6s} {'lv min/med/max':>14} {'classes':>28}")
    for g in sorted(games, key=lambda g: -st.median(per_game[g]["lv"])):
        d = per_game[g]
        print(f"{g:6s} {min(d['lv']):>5}/{int(st.median(d['lv']))}/{max(d['lv']):<4} "
              f"{', '.join(f'{k}:{v}' for k, v in d['cls'].most_common()):>32}")


if __name__ == "__main__":
    main()
