"""pool_runs.py — average N same-build run fixtures into one arm.

WHY THIS EXISTS: `bm.n_passes` is hardcoded to 1 in cell 14, *after* the customization hook,
so `significance.py`'s paired structure has never been reachable from a build. Pricing that
(2026-08-26) found the patch is the wrong shape anyway: solver `concurrency` is 28, so 25 games
is one wave and `k` passes is `ceil(25k/28)` waves — `k` passes costs `k` of the ~13 slots a
week, exactly what `k` separate runs cost. Steady-state GPU KV cache is p90 83.6% at 25
concurrent, so a single wave cannot hold 50 games; multi-pass is sequential, never free.

So `k` separate runs pooled here are the SAME arm at the SAME cost, without a new seam in cell
14 and without a 6.7 h kernel that loses three passes when it dies. And it is needed regardless:
the v10 baseline arm is already four separate runs (`v10cal`, `v19`, `thuiv1-1`, `thuiv1-1-r2`).

WHAT IT BUYS: the floor over those six real pairings is 2.96 at k=1 and 2.12 at k=2 — ratio 1.40
against sqrt(2)=1.41 — so `floor(k) = 2.96/sqrt(k)`. Hidden 2.08 (public +0.86..+1.34) needs
k ~ 5. That is a median: the worst of the six pairings needs k ~ 19.

NOT the same question as B35's +4.07. That synthetic has a zero-noise arm, so 19 of its 25 deltas
are exactly 0 and the sign-flip test ignores zeros — its p tracks 2/2^N to within 0.005 across all
eight rows. Combinatorial, and passes cannot move it. This one is a NOISE floor, and they can.

Output is a fixture `rank_runs.py` loads unmodified:

  python eval/pool_runs.py armA.json eval/fixtures/v10cal.json eval/fixtures/v19.json
  python eval/rank_runs.py armA.json armB.json

CONTROLS (`--selftest`, real fixtures, both poles, same invocation) — a failing control prints
no numbers, because a pooling bug is laundered into a confident verdict one command later:
  identity     — pooling ONE run must reproduce it exactly (catches any averaging that scales)
  mean         — the pooled mean must equal the mean of the arms' means
  order        — pool(a,b) must equal pool(b,a)
  ragged       — a game set that differs must be refused, not silently intersected
  not-a-fixture— a file with no `games` key must be refused, not crash on a missing `label`
Each is proven red on a mutation (5 mutations, one control green each).

EXIT CODES, matching rank_runs.py: 0 = ran, 2 = usage, 3 = data error.

LIMITS, stated: equal weight per run, which is what `n_passes` does — a pool of runs on DIFFERENT
per-game clocks is not one arm and this cannot tell. Pooling assumes the runs are same-build;
`rank_runs.py --selftest`'s negative pole is the check for that, and it is not run from here.
"""
from __future__ import annotations

import json
import math
import os
import statistics
import sys

FIELDS = ("score", "levels", "actions")


def load(path: str) -> tuple[str, dict]:
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    if not isinstance(raw, dict) or "games" not in raw:
        raise SystemExit(f"data error: {path} is not a run fixture (no 'games' key)")
    return raw.get("label", path), raw["games"]


def pool(arms: list[tuple[str, dict]]) -> dict:
    """Equal-weight mean per game per field. Ragged game sets are a data error."""
    if not arms:
        raise SystemExit("data error: nothing to pool")
    keys = set(arms[0][1])
    for label, games in arms:
        if set(games) != keys:
            raise SystemExit(f"data error: {label} game set differs by {sorted(set(games) ^ keys)}")
    out = {}
    for k in keys:
        row = {}
        for f in FIELDS:
            vals = [g[k][f] for _, g in arms]
            for v in vals:
                if not isinstance(v, (int, float)) or not math.isfinite(v):
                    raise SystemExit(f"data error: game {k!r} has non-finite {f}: {v!r}")
            row[f] = statistics.mean(vals)
        out[k] = row
    return out


def write(out_path: str, arms: list[tuple[str, dict]], sources: list[str]) -> dict:
    games = pool(arms)
    doc = {"label": "pool(" + "+".join(l for l, _ in arms) + ")", "source": sources, "games": games}
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    return doc


def _mean(games: dict) -> float:
    return sum(v["score"] for v in games.values()) / len(games)


def selftest() -> None:
    fx = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
    a, b = load(os.path.join(fx, "v10cal.json")), load(os.path.join(fx, "v19.json"))
    fails = []

    # identity: a pool of one is that one, field for field
    one = pool([a])
    if any(one[k][f] != a[1][k][f] for k in a[1] for f in FIELDS):
        fails.append("identity: pool of a single run did not reproduce it")

    # mean: pooled mean == mean of the arms' means
    both = pool([a, b])
    want = (_mean(a[1]) + _mean(b[1])) / 2
    if abs(_mean(both) - want) > 1e-9:
        fails.append(f"mean: pooled {_mean(both):.6f} != mean-of-means {want:.6f}")

    # order: pooling is commutative
    if pool([b, a]) != both:
        fails.append("order: pool(a,b) != pool(b,a)")

    # ragged: a differing game set must be refused
    ragged = dict(b[1])
    ragged.pop(sorted(ragged)[0])
    try:
        pool([a, ("ragged", ragged)])
        fails.append("ragged: a differing game set was accepted")
    except SystemExit:
        pass

    # not-a-fixture: no 'games' key must be refused, not crash on a missing 'label'
    try:
        load(os.path.join(fx, "game-totals.json"))
        fails.append("not-a-fixture: a file with no 'games' key was accepted")
    except SystemExit:
        pass

    if fails:
        print("SELFTEST FAIL — no numbers are printed, a pooling bug becomes a verdict downstream:")
        for f in fails:
            print("  " + f)
        raise SystemExit(3)
    print(f"SELFTEST OK: identity, mean, order, ragged, not-a-fixture — 5 controls")
    print(f"  v10cal {_mean(a[1]):.2f} + v19 {_mean(b[1]):.2f} -> pool {_mean(both):.2f}")


def main(argv: list[str]) -> int:
    if len(argv) == 1 and argv[0] == "--selftest":
        selftest()
        return 0
    if len(argv) < 3:
        print(__doc__)
        return 2
    out, sources = argv[0], argv[1:]
    doc = write(out, [load(p) for p in sources], sources)
    print(f"pooled {len(sources)} runs x {len(doc['games'])} games -> {out}   "
          f"mean {_mean(doc['games']):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
