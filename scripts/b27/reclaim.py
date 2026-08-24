"""reclaim.py -- how much per-game clock could be MOVED, and what it would cost in levels.

THE QUESTION (MAP B35 / notes/R37-the-cap-decides-most-cells.md): every game gets the same
7,920s wall (B33: all 125 run-games end there). Three of the public 25 never score in any run
and consume 6.6h of every run returning 0.00, and B33 already found most cleared games plateau
at 27-59% of their clock and keep playing. R37 then showed the score is cap-bound in 77% of
decided cells, so the only thing that pays is another LEVEL -- which makes the clock the
resource worth reallocating.

Unlike B34's clock-2x this spends no extra budget: it moves time between games rather than
adding it, so it can actually ship. What it needs before it can be built is the number this
script measures -- WHEN a game earns its first level, and what a give-up rule would cost.

WHAT IT ADDS to plateau.py, whose records() and fire() it reuses unchanged:
  Q_A  time-to-FIRST-level: the distribution a "never-scored, give up" threshold must clear.
  Q_B  for each threshold, seconds reclaimed vs level-ups destroyed -- both halves, because a
       rule that reclaims time by killing the levels it was meant to buy is not a saving.

⚠️ THE TWO TRIGGERS ARE NOT THE SAME RULE and are reported separately:
  never-scored  -- give up on a game with ZERO level-ups after a fraction of its clock.
  plateaued     -- give up after k consecutive actions with no level-up (plateau.fire's rule),
                   which can fire on a game that has already scored.

EXIT CODES: 0 = ran (controls passed), 1 = a control failed, 2 = corpus missing.

Usage (from scripts/b27/, the corpus loader is a sibling import):
    python reclaim.py
    python reclaim.py --selftest     # no corpus needed; proves the arithmetic on fixtures
"""

import statistics
import sys

FRACTIONS = (0.25, 0.40, 0.50, 0.60, 0.75)
WALL_S = 7920.0  # B33: per-game cap; every run-game on record ends within 98-100% of it


def q(values, p):
    ordered = sorted(values)
    return ordered[int(p * (len(ordered) - 1))]


# ---------------------------------------------------------------- measurements


def first_level(rows):
    """Q_A -- where the FIRST level-up lands, as a fraction of the game's own actions."""
    cleared = [r for r in rows if r["ups"]]
    never = [r for r in rows if not r["ups"]]
    fracs = [r["ups"][0] / r["final"] for r in cleared if r["final"]]
    return {
        "n": len(rows),
        "cleared": len(cleared),
        "never": len(never),
        "fracs": fracs,
        "never_actions": sum(r["final"] for r in never),
        "all_actions": sum(r["final"] for r in rows),
    }


def reclaim_never(rows, frac):
    """Q_B(never-scored) -- give up on a game still at zero level-ups at `frac` of its actions.

    Returns (games hit, actions reclaimed, level-ups destroyed). A level-up destroyed is one
    that the real run earned AFTER the cut point -- the whole cost of the rule.
    """
    hit = acts = lost = 0
    for r in rows:
        cut = frac * r["final"]
        if r["ups"] and r["ups"][0] <= cut:
            continue  # had already scored by the cut; the rule never fires
        hit += 1
        acts += r["final"] - cut
        lost += sum(1 for u in r["ups"] if u > cut)
    return hit, acts, lost


def reclaim_plateau(rows, k, fire):
    """Q_B(plateaued) -- plateau.fire's rule, priced. Reuses plateau's own implementation."""
    hit = acts = lost = 0
    for r in rows:
        at, later = fire(r, k)
        if at is None:
            continue
        hit += 1
        acts += r["final"] - at
        lost += sum(1 for u in r["ups"] if u > at)
    return hit, acts, lost


# ---------------------------------------------------------------- self-test


def _fixture():
    """Synthetic run-games whose answers are known by construction."""
    def row(ups, final):
        return {"run": "fx", "game": "g%d" % final, "ups": ups, "final": final,
                "last": ups[-1] if ups else None, "levels": len(ups),
                "actions": [{"action_num": i, "level_completed": i in ups}
                            for i in range(1, final + 1)]}
    return [
        row([], 100),          # never scores
        row([10], 100),        # early single level
        row([90], 100),        # LATE single level -- any early give-up destroys it
        row([10, 20, 30], 100),
    ]


def _selftest():
    rows = _fixture()
    bad = []

    a = first_level(rows)
    if (a["n"], a["cleared"], a["never"]) != (4, 3, 1):
        bad.append("first_level counts %s" % [a["n"], a["cleared"], a["never"]])
    if sorted(a["fracs"]) != [0.1, 0.1, 0.9]:
        bad.append("first-level fractions %s" % sorted(a["fracs"]))
    if a["never_actions"] != 100:
        bad.append("never_actions %s" % a["never_actions"])

    # at 25%: the never-scorer and the late-scorer are both still at zero -> both cut.
    hit, acts, lost = reclaim_never(rows, 0.25)
    if (hit, acts, lost) != (2, 150.0, 1):
        bad.append("reclaim_never(.25) = %s, expected (2, 150.0, 1)" % [hit, acts, lost])
    # the ONE lost level is the late-scorer's -- the whole point of reporting both halves.

    # at 95%: nothing is still at zero except the never-scorer, and it loses nothing.
    hit, acts, lost = reclaim_never(rows, 0.95)
    if (hit, lost) != (1, 0):
        bad.append("reclaim_never(.95) = %s, expected hit=1 lost=0" % [hit, lost])

    # plateau rule with a stub fire(). Fires at 20, NOT at 50: with every fixture row 100
    # actions long, a cut at the midpoint makes `final - at` and `at` numerically equal, so
    # a rule that prices the wrong side of the cut passes. Measured -- that exact mutation
    # went undetected at 50 and is caught at 20.
    hit, acts, lost = reclaim_plateau(rows, 10, lambda r, k: (20, None))
    if (hit, acts, lost) != (4, 320, 2):
        bad.append("reclaim_plateau = %s, expected (4, 320, 2)" % [hit, acts, lost])

    # TEETH: a mutated fixture must move the answer, or the assertions above are vacuous.
    mutated = _fixture()
    mutated[2]["ups"] = [10]          # the late-scorer now scores early
    mutated[2]["actions"][9]["level_completed"] = True
    h2, _, l2 = reclaim_never(mutated, 0.25)
    if (h2, l2) != (1, 0):
        bad.append("teeth: mutated fixture gave %s, expected (1, 0)" % [h2, l2])
    if (h2, l2) == (hit, lost):
        bad.append("teeth: mutation did not change the verdict -- assertions are vacuous")

    for line in bad:
        print("SELFTEST FAILED: %s" % line)
    if bad:
        return 1
    print("SELFTEST OK -- counts, both give-up rules, and a teeth mutation that moves the answer")
    return 0


# ---------------------------------------------------------------- main


def main():
    if "--selftest" in sys.argv[1:]:
        raise SystemExit(_selftest())

    try:
        from plateau import records, fire, controls
    except ImportError as exc:
        print("run this from scripts/b27/ (sibling import): %s" % exc)
        raise SystemExit(2)

    try:
        rows = list(records())
    except (OSError, ValueError) as exc:
        print("corpus unreadable (~/Claude/arc-artifacts): %s" % exc)
        raise SystemExit(2)

    # ---- CONTROL: plateau's own published counts, before any new number is read ----
    _, total_games, total_turns, pair_turns = controls()
    ok = (total_games == 125 and total_turns == 5052 and pair_turns == 1973)
    print("CONTROL  run-games=%d (125) turns=%d (5,052) pair=%d (1,973): %s"
          % (total_games, total_turns, pair_turns, "OK" if ok else "FAILED"))
    if not ok:
        print("loader disagrees with R29/plateau; no numbers printed.")
        raise SystemExit(1)
    if len(rows) != total_games:
        print("CONTROL FAILED: records() yielded %d rows for %d run-games" % (len(rows), total_games))
        raise SystemExit(1)
    print()

    a = first_level(rows)
    print("Q_A  WHEN DOES A GAME EARN ITS FIRST LEVEL?  (fraction of that game's own actions)")
    print("  run-games %d | cleared >=1 level %d | never cleared %d (%.1f%%)"
          % (a["n"], a["cleared"], a["never"], 100 * a["never"] / a["n"]))
    if a["fracs"]:
        f = a["fracs"]
        print("  first level-up at: min %.3f  p10 %.3f  p25 %.3f  median %.3f  p75 %.3f  p90 %.3f  max %.3f"
              % (min(f), q(f, .10), q(f, .25), statistics.median(f), q(f, .75), q(f, .90), max(f)))
        for thr in FRACTIONS:
            late = sum(1 for x in f if x > thr)
            print("    scored FIRST level after %.0f%% of its actions: %d of %d cleared games (%.1f%%)"
                  % (100 * thr, late, len(f), 100 * late / len(f)))
    print("  never-cleared games hold %d of %d actions = %.1f%% of the corpus"
          % (a["never_actions"], a["all_actions"], 100 * a["never_actions"] / a["all_actions"]))
    print()

    print("Q_B  PRICING BOTH GIVE-UP RULES  (seconds assume the %.0fs per-game wall)" % WALL_S)
    print("  rule            param   games hit   actions reclaimed   est. hours/run   LEVEL-UPS LOST")
    for thr in FRACTIONS:
        hit, acts, lost = reclaim_never(rows, thr)
        hours = acts / a["all_actions"] * (len(rows) * WALL_S) / 3600
        print("  never-scored    %.0f%%   %9d   %17.0f   %14.2f   %d"
              % (100 * thr, hit, acts, hours, lost))
    for k in (10, 20, 30, 40, 60):
        hit, acts, lost = reclaim_plateau(rows, k, fire)
        hours = acts / a["all_actions"] * (len(rows) * WALL_S) / 3600
        print("  plateaued       k=%-3d %9d   %17.0f   %14.2f   %d" % (k, hit, acts, hours, lost))
    print()
    print("READ IT AS A PAIR. A rule whose LEVEL-UPS LOST is non-zero is buying clock with the")
    print("exact currency the clock was going to be spent on; the reclaimed hours only pay if")
    print("the games receiving them convert time into levels, which is B34's open question.")


if __name__ == "__main__":
    main()
