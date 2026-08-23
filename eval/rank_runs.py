"""rank_runs.py — can these two runs actually be told apart, given this campaign's noise?

WHY THIS EXISTS (LEDGER CORRECTION 3): the same build produced 4.71 / 4.55 / 2.82 public,
and the same parquet drew 1.70 / 1.32 hidden. Four of the eight "closed" directions were
closed on a mean gap smaller than that spread. A bare mean comparison is how that happened.

WHAT IT DOES: paired per-game comparison over the 25 public games, with a two-sided
sign-flip permutation test on the per-game deltas. Under H0 (same build, noise only) each
game's delta is symmetric in sign, so permuting signs gives the null distribution of the
mean — no external noise model needed, heavy tails handled by construction. 25 paired
observations have far more power than two means: identical builds flip 7 of 25 games
between scoring and zero with swings up to ±27 that cancel in the mean.

VERDICT RULE (stated, not implied): p < 0.05 on the score-mean test => DISTINGUISHABLE,
with the direction of the mean; otherwise NOT-DISTINGUISHABLE. Levels and sign counts are
reported alongside because depth is the axis that matters (R24/R25).

CONTROLS (verification-layers: both poles, same invocation, real artifacts):
  --selftest runs
    negative: v10cal vs v19  — same build, inert graft => must be NOT-DISTINGUISHABLE
    positive: v10cal vs v20  — dense vs MoE, 4.71 vs 0.18 => must be DISTINGUISHABLE
  A harness that cannot pass both poles is a broken instrument, not a strict one.

EXIT CODES: 0 = ran (verdict is in stdout, never in the exit code — a crash must not be
readable as a verdict), 2 = usage, 3 = data error.

LIMITS, stated: n=25 games; exchangeability under H0 is the assumption; the hidden set is
OOD vs public (R22), so NOT-DISTINGUISHABLE here says nothing about hidden, and even a
public DISTINGUISHABLE only predicts hidden direction, not size. Hidden n=2 spread is 0.38.

Usage:
  python eval/rank_runs.py eval/fixtures/v10cal.json <candidate benchmark.json>
  python eval/rank_runs.py --selftest
"""
from __future__ import annotations

import json
import random
import sys

ALPHA = 0.05
PERMS = 20000
SEED = 0  # fixed: a measurement that re-randomises between runs is one sample of a distribution


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    if "games" in raw:  # fixture shape
        return {"label": raw.get("label", path), "games": raw["games"]}
    # full benchmark.json shape
    games: dict = {}
    for r in raw["game_runs"]:
        g = r["game_id"].split("-")[0]
        if g in games:
            raise SystemExit(f"data error: duplicate game prefix {g!r} in {path}")
        a = r.get("actions_per_level")
        acts = (
            sum(a.values()) if isinstance(a, dict)
            else sum(x[1] if isinstance(x, (list, tuple)) else x for x in (a or []))
        )
        games[g] = {"score": r["final_score"], "levels": r["levels_completed"], "actions": acts}
    return {"label": raw.get("label", path), "games": games}


def perm_test(deltas: list[float], perms: int = PERMS) -> float:
    obs = abs(sum(deltas) / len(deltas))
    rng = random.Random(SEED)
    hits = 0
    for _ in range(perms):
        m = sum(d if rng.random() < 0.5 else -d for d in deltas) / len(deltas)
        if abs(m) >= obs - 1e-12:
            hits += 1
    return hits / perms


def compare(a: dict, b: dict) -> dict:
    ga, gb = a["games"], b["games"]
    if set(ga) != set(gb):
        raise SystemExit(f"data error: game sets differ: {sorted(set(ga) ^ set(gb))}")
    if len(ga) < 10:
        raise SystemExit(f"data error: only {len(ga)} paired games — nothing to test")
    keys = sorted(ga)
    d_score = [gb[k]["score"] - ga[k]["score"] for k in keys]
    d_level = [gb[k]["levels"] - ga[k]["levels"] for k in keys]
    p = perm_test(d_score)
    pos = sum(1 for d in d_score if d > 0)
    neg = sum(1 for d in d_score if d < 0)
    flips = sum(
        1 for k in keys if (ga[k]["score"] > 0) != (gb[k]["score"] > 0)
    )
    mean_a = sum(ga[k]["score"] for k in keys) / len(keys)
    mean_b = sum(gb[k]["score"] for k in keys) / len(keys)
    verdict = (
        ("BETTER" if sum(d_score) > 0 else "WORSE") if p < ALPHA else "NOT-DISTINGUISHABLE"
    )
    return {
        "a": a["label"], "b": b["label"], "games": len(keys),
        "mean_a": round(mean_a, 2), "mean_b": round(mean_b, 2),
        "mean_delta": round(sum(d_score) / len(keys), 2),
        "levels_a": sum(ga[k]["levels"] for k in keys),
        "levels_b": sum(gb[k]["levels"] for k in keys),
        "games_up": pos, "games_down": neg, "scoring_flips": flips,
        "p_score": round(p, 4), "alpha": ALPHA, "verdict": verdict,
        "level_delta_sum": sum(d_level),
    }


def report(r: dict) -> None:
    print(f"{r['a']}  ->  {r['b']}   ({r['games']} paired games)")
    print(f"  mean {r['mean_a']} -> {r['mean_b']}  (delta {r['mean_delta']:+})   "
          f"levels {r['levels_a']} -> {r['levels_b']} ({r['level_delta_sum']:+})")
    print(f"  per-game: {r['games_up']} up / {r['games_down']} down / "
          f"{r['scoring_flips']} flipped scoring<->zero")
    print(f"  sign-flip permutation p = {r['p_score']}  (alpha {r['alpha']})")
    print(f"  VERDICT: {r['verdict']}")
    print("  caveat: public-only; the hidden set is OOD (R22) and its own n=2 spread is 0.38")


def selftest() -> None:
    import os
    fx = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
    v10 = load(os.path.join(fx, "v10cal.json"))
    v19 = load(os.path.join(fx, "v19.json"))
    v20 = load(os.path.join(fx, "v20.json"))

    neg = compare(v10, v19)   # same build, inert graft — the instrument must NOT separate it
    pos = compare(v10, v20)   # dense vs MoE, 26x apart — the instrument MUST separate it
    print("== negative control (same build, must NOT distinguish) ==")
    report(neg)
    print("\n== positive control (26x apart, MUST distinguish) ==")
    report(pos)

    ok_neg = neg["verdict"] == "NOT-DISTINGUISHABLE"
    ok_pos = pos["verdict"] in ("BETTER", "WORSE")
    if not (ok_neg and ok_pos):
        print("\nSELFTEST FAIL: the instrument cannot pass both poles — do not use its verdicts")
        raise SystemExit(3)
    print("\nSELFTEST OK: both poles behave; verdicts are usable")


def main(argv: list[str]) -> int:
    if len(argv) == 1 and argv[0] == "--selftest":
        selftest()
        return 0
    if len(argv) != 2:
        print(__doc__)
        return 2
    report(compare(load(argv[0]), load(argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
