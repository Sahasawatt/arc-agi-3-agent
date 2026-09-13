r"""arm_oracle_gap.py -- how much depth the DRAW decides, measured inside one declared build.

WHY THIS EXISTS: `per_level_census.py` reports "stalls BEHIND the game's own frontier: 255 (60%)
<- draw variance" and a best-ever oracle of 47 levels against a best single run of 30. Both
numbers are computed over the 17-run FAMILY, which is a set of DIFFERENT builds held to be
in-band -- so the gap it reports mixes run-to-run variance with whatever the levers did. This
script recomputes the same quantity inside the arms declared in `eval/fixtures/arms.json`, where
membership is "same build, lever proven inert or absent", so the remaining spread is the draw.

WHAT IT DOES: per arm, per game, max levels over the arm's runs (the oracle), against the best
single run's total; plus E[oracle] by subset size k, exact over all C(n,k) subsets, so the curve
is not a simulation.

READ THE RESULT AS A BOUND, NOT A PLAN. The oracle is what per-game best-of-k WOULD give, and
whether anything buys it is UNSETTLED -- see notes/R53 for the correction that opened it:
  * `bm.n_passes = k` plays every game k times (`_game_run_count` = game_count * n_passes).
    Whether the passes are averaged or the best is taken is NOT KNOWABLE FROM THIS REPO: the
    scorer is not vendored (zero hits for RHAE / human_baseline_actions under localrig/, no
    aggregation of scores across passes anywhere in framework/run.py), and the "equal weight per
    run, which is what n_passes does" in pool_runs.py's LIMITS is a docstring, not a measurement.
    On the AVERAGING branch the oracle is unreachable and the k=1 column is what k passes buy.
    On the BEST-OF branch this gap is purchasable directly.
  * The literal `bm.n_passes = 1` is at CELL 15 of the live Flash-Next chassis (18 cells) and at
    cell 14 of thuiv3 (17 cells) -- the "cell 14" in the docstrings is off by one against the
    chassis now running. The customization hook is cell 12, so a HOOK cannot set it; patching the
    cell can, which is what this campaign does routinely to cells 6/8/12, and has never been tried
    for this one.
  * pinning the sampler (`LOCAL_ANALYZER_SEED`, MAP B37) removes the spread without moving the
    distribution -- it lands on one draw, and four of them here are 20, 23, 25, 28.
So the gap is a statement about where capability is ALREADY latent. The lever that collects it is
either a cell-15 patch (if best-of) or in-run recovery after a stall (if averaging); neither is
measured here.

CONTROLS (both poles plus a closure, same invocation):
  positive: the FAMILY list from per_level_census.py must reproduce that script's published
            oracle 47 / best single 30. The expected values come from the repo, not from me.
  negative: a one-member arm must report gap 0 -- an oracle over one run IS that run.
  closure:  at k = n there is exactly one subset, so E[oracle] must equal the oracle exactly.
A harness that cannot pass all three is a broken instrument, not a strict one.

EXIT CODES: 0 = ran (the numbers are in stdout), 3 = data error or a failed control.

    python eval/arm_oracle_gap.py
"""

from __future__ import annotations

import itertools
import json
import pathlib
import statistics
import sys

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"

# per_level_census.py's FAMILY, verbatim -- the positive control's population.
FAMILY = ["v10cal", "v14", "v16", "v18", "v19", "v22", "v23", "v24", "v25", "v26",
          "thui-v1-0", "thui-v1-1", "thui-v1-1-r2", "thui-v2-0", "thui-v3-0", "thui-v4-0",
          "clock2x"]
FAMILY_PUBLISHED = {"oracle": 47, "best_single": 30}

# arms.json names fixtures; the census keys the same runs differently. Declared, never guessed:
# an unmapped member is skipped loudly rather than silently dropped from an arm.
FIXTURE_TO_CENSUS = {
    "v10cal": "v10cal",
    "v19": "v19",
    "thuiv1-1": "thui-v1-1",
    "thuiv1-1-r2": "thui-v1-1-r2",
    "thuiv3-0": "thui-v3-0",
}


def load() -> tuple[dict, dict]:
    runs = json.loads((FIX / "per-level-census.json").read_text(encoding="utf-8"))["runs"]
    arms = json.loads((FIX / "arms.json").read_text(encoding="utf-8"))["arms"]
    return runs, arms


def levels(runs: dict, run: str, game: str) -> int:
    v = runs[run][game]["levels"]
    if not isinstance(v, int) or v < 0:
        raise ValueError(f"{run}/{game}: levels is {v!r}, not a count")
    return v


def oracle_gap(runs: dict, members: list[str]) -> dict:
    """Per-game max over members, against the best single member."""
    games = sorted(set(runs[members[0]]))
    for m in members:
        if sorted(set(runs[m])) != games:
            raise ValueError(f"{m} does not cover the same games as {members[0]}")
    totals = {m: sum(levels(runs, m, g) for g in games) for m in members}
    oracle = sum(max(levels(runs, m, g) for m in members) for g in games)
    disagree = [
        (g, [levels(runs, m, g) for m in members])
        for g in games
        if len({levels(runs, m, g) for m in members}) > 1
    ]
    curve = {}
    for k in range(1, len(members) + 1):
        subsets = list(itertools.combinations(members, k))
        vals = [sum(max(levels(runs, m, g) for m in c) for g in games) for c in subsets]
        curve[k] = {"mean": statistics.mean(vals), "min": min(vals), "max": max(vals),
                    "subsets": len(subsets)}
    return {"games": len(games), "totals": totals, "oracle": oracle,
            "best_single": max(totals.values()), "disagree": disagree, "curve": curve}


def controls(runs: dict) -> list[str]:
    failures = []

    present = [r for r in FAMILY if r in runs]
    if len(present) != len(FAMILY):
        failures.append(f"positive control unrunnable: census lacks {set(FAMILY) - set(present)}")
    else:
        fam = oracle_gap(runs, present)
        for key, want in FAMILY_PUBLISHED.items():
            if fam[key] != want:
                failures.append(
                    f"positive control: FAMILY {key} = {fam[key]}, per_level_census.py published {want}")

    solo = oracle_gap(runs, [FAMILY[0]])
    if solo["oracle"] != solo["best_single"]:
        failures.append("negative control: a one-run arm reported a non-zero gap")

    arm = oracle_gap(runs, [FAMILY[0], FAMILY[1]])
    if arm["curve"][2]["subsets"] != 1 or arm["curve"][2]["mean"] != arm["oracle"]:
        failures.append("closure control: E[oracle] at k=n did not equal the oracle")

    return failures


def main() -> int:
    try:
        runs, arms = load()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"data error: {exc}")
        return 3

    failed = controls(runs)
    if failed:
        for f in failed:
            print(f"CONTROL FAILED -- {f}")
        print("refusing to print arm numbers from an instrument that cannot pass its own controls")
        return 3
    print(f"controls OK: FAMILY reproduces oracle {FAMILY_PUBLISHED['oracle']} / "
          f"best single {FAMILY_PUBLISHED['best_single']}, one-run gap 0, k=n closure exact")

    for name, spec in sorted(arms.items()):
        declared = sorted(spec["members"])
        mapped, skipped = [], []
        for m in declared:
            key = FIXTURE_TO_CENSUS.get(m)
            (mapped if key and key in runs else skipped).append(m)
        print(f"\n== arm {name} ({spec['rule']}) ==")
        if skipped:
            print(f"  not in the census fixture, excluded: {', '.join(skipped)}")
        if len(mapped) < 2:
            print(f"  {len(mapped)} member(s) banked here -- needs 2 to separate draw from build")
            continue

        r = oracle_gap(runs, [FIXTURE_TO_CENSUS[m] for m in mapped])
        gap = r["oracle"] - r["best_single"]
        pct = 100.0 * gap / r["best_single"] if r["best_single"] else float("nan")
        print(f"  members measured: {', '.join(mapped)}  ({r['games']} games)")
        print("  per-run total levels: " + ", ".join(f"{k} {v}" for k, v in r["totals"].items()))
        print(f"  best single {r['best_single']}   oracle {r['oracle']}   "
              f"gap +{gap} (+{pct:.0f}%)")
        print(f"  games whose depth DISAGREES across the arm: {len(r['disagree'])}/{r['games']}")
        for g, vals in r["disagree"]:
            print(f"    {g} {vals}")
        print("  E[oracle] by k (exact over every subset):")
        for k, c in r["curve"].items():
            print(f"    k={k}  mean {c['mean']:.2f}  min {c['min']}  max {c['max']}  "
                  f"({c['subsets']} subset{'s' if c['subsets'] > 1 else ''})")

    print("\nThe gap is a BOUND on what per-game best-of-k would give, not a plan. Whether "
          "n_passes averages the draws or takes the best is NOT knowable from this repo (the "
          "scorer is not vendored), so the gap is purchasable on one of those branches and not "
          "the other; `bm.n_passes = 1` is a literal at cell 15 of the live chassis, after the "
          "cell-12 hook -- a hook cannot set it, a cell patch can. See notes/R53.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
