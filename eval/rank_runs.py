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
  --selftest says nothing about malformed INPUT: it loads three known-clean fixtures and
  checks only the verdict labels. Non-finite scores are refused in load() instead, because
  a NaN there is laundered into a confident "WORSE" rather than a crash (see _finite).

THE BASELINE IS A CHOICE (MAP B57): four runs of the v10 build are banked, and which one is
passed as the baseline moves the p-value by 1.7x-7.1x — clock2x reads 0.2761 against v10cal and
0.0828 against v19. Nothing in this script's output ever recorded that a choice was available,
so B34 was closed on one of six numbers with no artifact naming the other five. A single run of
a multi-run arm is now REFUSED (exit 4) with the pooling command printed, or accepted with
--single-baseline REASON, which is printed into the report. Membership is declared in
eval/fixtures/arms.json and is never inferred from a p-value: almost every run of this campaign
is NOT-DISTINGUISHABLE from v10cal, so "reads the same" is not evidence of "same build".

EXIT CODES: 0 = ran (verdict is in stdout, never in the exit code — a crash must not be
readable as a verdict), 2 = usage, 3 = data error, 4 = unpooled member of a multi-run arm.

LIMITS, stated: n=25 games; exchangeability under H0 is the assumption; the hidden set is
OOD vs public (R22), so NOT-DISTINGUISHABLE here says nothing about hidden, and even a
public DISTINGUISHABLE only predicts hidden direction, not size. Hidden n=2 spread is 0.38.

Usage:
  python eval/pool_runs.py POOLED_ARM.json eval/fixtures/thuiv1-1.json \
      eval/fixtures/thuiv1-1-r2.json eval/fixtures/v10cal.json eval/fixtures/v19.json
  python eval/rank_runs.py POOLED_ARM.json CANDIDATE.json
  python eval/rank_runs.py --selftest
"""
from __future__ import annotations

import json
import math
import os
import random
import re
import sys

ALPHA = 0.05
PERMS = 20000
SEED = 0  # fixed: a measurement that re-randomises between runs is one sample of a distribution

ARMS_FILE = "arms.json"
# Shape, never a word list. A guard's own remediation line is the exact string an operator
# pastes back, and a placeholder check built from English keywords was defeated on this machine
# by a non-English argument that was long enough to pass the length floor.
_PLACEHOLDER = re.compile(r"<[^>]*>|\{\{|PASTE_|\bTODO\b", re.IGNORECASE)


def _fixtures_dir() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def load_arms(path: str | None = None) -> dict:
    """{arm name: sorted member labels}. Raises; the caller reports blindness rather than hiding it."""
    with open(path or os.path.join(_fixtures_dir(), ARMS_FILE), encoding="utf-8") as fh:
        raw = json.load(fh)
    return {name: sorted(spec["members"]) for name, spec in raw["arms"].items()}


def arm_of(label: str, arms: dict):
    """The arm this label is ONE unpooled run of, or None.

    A pooled fixture needs no special case: pool_runs.py labels its output ``pool(a+b)``, which is
    never a member label, so exact membership already excludes it. An explicit startswith("pool(")
    branch was written here first and removed -- its control could not be made to fail, and a check
    that cannot fail is not a check.
    """
    for name, members in arms.items():
        if label in members:
            return name, members
    return None


def check_reason(reason: str):
    """None if usable, else why not."""
    r = reason.strip()
    if len(r) < 12:
        return "--single-baseline needs a sentence, not a token"
    if _PLACEHOLDER.search(r):
        return "--single-baseline was handed the placeholder, not a reason"
    return None


def refusal(hits: list, argv: list) -> str:
    """hits: [(path, label, arm, members)]. Every command printed here is runnable as printed."""
    out = [f"REFUSED: {lab!r} ({pth}) is ONE run of the {arm!r} arm, which has "
           f"{len(mem)} banked runs: {', '.join(mem)}"
           for pth, lab, arm, mem in hits]
    _, _, _, members = hits[0]
    other = argv[1] if hits[0][0] == argv[0] else argv[0]
    srcs = " ".join(os.path.join("eval", "fixtures", m + ".json") for m in members)
    out += [
        "",
        "  Which one is picked moves the p-value by 1.7x-7.1x, and nothing in the output would",
        "  record that a choice was available. Pool the arm first -- 0 GPU, 0 submission slots:",
        f"    python eval/pool_runs.py POOLED_ARM.json {srcs}",
        f"    python eval/rank_runs.py POOLED_ARM.json {other}",
    ]
    if len(hits) > 1:
        out.append("  (both sides are arm members; repeat for the other one)")
    out += [
        "",
        "  Or state why this one run is the right baseline here. The reason is printed into the",
        "  report, which is the artifact B57 says has never existed:",
        "    --single-baseline PASTE_YOUR_REASON_HERE",
    ]
    return "\n".join(out)


def _finite(games: dict, path: str) -> dict:
    """A non-finite score is a DATA ERROR, never a verdict.

    One NaN poisons ``sum(d_score)``; inside ``perm_test`` every ``abs(m) >= obs - 1e-12`` is
    then a NaN comparison and therefore False, so ``hits`` stays 0 and ``p`` is exactly 0.0;
    ``compare`` reads ``p < ALPHA`` as True and ``sum(d_score) > 0`` as False, and returns a
    confident "WORSE". ``json.load`` accepts a bare unquoted ``NaN`` by default, so it arrives
    silently, and ``--selftest`` cannot see it: it loads three known-clean fixtures and only
    checks the verdict labels. Refuse it here, while it is still a data error (exit 3).
    """
    for g, d in games.items():
        for k in ("score", "levels"):
            v = d.get(k)
            if not isinstance(v, (int, float)) or not math.isfinite(v):
                raise SystemExit(f"data error: {path} game {g!r} has non-finite {k}: {v!r}")
    return games


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    if "games" in raw:  # fixture shape
        return {"label": raw.get("label", path), "games": _finite(raw["games"], path)}
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
    return {"label": raw.get("label", path), "games": _finite(games, path)}


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
    if r.get("arm_check_blind"):
        print(f"  ARM CHECK BLIND: {r['arm_check_blind']} — this verdict is UNGUARDED by B57")
    if r.get("single_baseline"):
        print(f"  SINGLE-BASELINE (not pooled), reason given: {r['single_baseline']}")
    print("  caveat: public-only; the hidden set is OOD (R22) and its own n=2 spread is 0.38")


def selftest() -> None:
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

    fails = []
    if neg["verdict"] != "NOT-DISTINGUISHABLE":
        fails.append("negative pole: same build was separated")
    if pos["verdict"] not in ("BETTER", "WORSE"):
        fails.append("positive pole: 26x apart was not separated")

    # --- B57 guard controls. A manifest that matched everything, or nothing, would pass a
    # one-pole check; each side is asserted here in the same invocation.
    try:
        arms = load_arms()                                # a missing manifest reddens here
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"\nSELFTEST FAIL: the B57 arm manifest is unreadable ({exc}) — the guard cannot "
              f"fire, and a guard that cannot fire is not a strict one")
        raise SystemExit(3)
    if not arm_of("v10cal", arms) or len(arm_of("v10cal", arms)[1]) < 2:
        fails.append("guard-positive: v10cal does not resolve to an arm of 2 or more")
    if arm_of("v20", arms) is not None:
        fails.append("guard-negative: v20 (its own build) was claimed by an arm")
    ghosts = [m for ms in arms.values() for m in ms
              if not os.path.exists(os.path.join(fx, m + ".json"))]
    if ghosts:
        fails.append(f"guard-ghost: declared members with no banked fixture: {ghosts}")
    if not check_reason("<one sentence: why this run>"):
        fails.append("guard-reason: the placeholder was accepted as a reason")
    if check_reason("v19 is the only banked run on this per-game clock"):
        fails.append("guard-reason: a real reason was rejected")

    if fails:
        print("\nSELFTEST FAIL — do not use its verdicts:")
        for f in fails:
            print("  " + f)
        raise SystemExit(3)
    print("\nSELFTEST OK: both poles behave, and the B57 arm guard has teeth "
          "(positive, negative, ghost, reason x2) — 6 controls")


def main(argv: list[str]) -> int:
    if len(argv) == 1 and argv[0] == "--selftest":
        selftest()
        return 0
    reason = None
    if "--single-baseline" in argv:
        i = argv.index("--single-baseline")
        if i + 1 >= len(argv):
            print("usage: --single-baseline needs a reason argument")
            return 2
        reason = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
        bad = check_reason(reason)
        if bad:
            print(bad)
            return 2
    if len(argv) != 2:
        print(__doc__)
        return 2

    a, b = load(argv[0]), load(argv[1])
    try:
        arms = load_arms()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        arms = None
        blind = str(exc)
        print(f"ARM CHECK DID NOT RUN ({exc}) — the B57 single-baseline guard is BLIND for this "
              f"run; a gate cannot report its own skip, so this line is the report")
    hits = []
    for path, doc in ((argv[0], a), (argv[1], b)):
        found = arm_of(doc["label"], arms) if arms else None
        if found:
            hits.append((path, doc["label"], found[0], found[1]))
    if hits and reason is None:
        print(refusal(hits, argv))
        return 4

    r = compare(a, b)
    if arms is None:
        r["arm_check_blind"] = blind
    if reason is not None:
        r["single_baseline"] = reason
    report(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
