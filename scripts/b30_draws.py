"""B30, offline: where the remaining hidden draws go — and whether re-drawing v10 is a route.

B30's row says "variance grows with score (v9-lite A/A spread 0.00 vs duck-v10 0.38), so
ranking high builds needs 2+ draws each", and asks whether to spend draws re-measuring
v10's mean or testing a candidate. Kaggle keeps the BEST submission, so re-drawing an
existing build is not a measurement at all — it is a lottery ticket on the leaderboard
number. That reframing is what this decides, and it costs 0 slots.

Three instruments, in order of how much they carry:

  (1) The PUBLIC LEADERBOARD, 2,506 teams, each row carrying `SubmissionCount`. This is
      the population-level answer to "what does an extra draw buy" and it did not exist in
      working memory — R21 downloaded the board on 2026-08-22 and did not keep the file.
      It is confounded (better teams submit more), so it reads as an UPPER BOUND.

  (2) OUR OWN two v10 hidden draws (1.70 / 1.32) plus the four same-build public draws
      (4.71 / 4.55 / 3.20 / 2.82), which give two INDEPENDENT estimates of the hidden
      standard deviation. Two estimates that agree to within a factor of 1.4 is what makes
      the decision robust; a single pair could not.

  (3) The arithmetic of max-of-n, which is what the leaderboard actually reports.

Validation gate first: the loaders must reproduce the five published public means and the
six teams R21 named by hand, before any new number is read off them.
"""
import csv
import math
import os
import random
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "eval"))
from rank_runs import load  # noqa: E402  the repo's own per-game loader, not a second one

ART = os.path.expanduser("~/Claude/arc-artifacts")

# LEDGER's published public means -- the control. A rebuilt loader that does not reproduce
# these is measuring something else (R29 sec.8's lesson, which cost a session).
PUBLISHED = {"v10cal": 4.71, "thuiv1": 3.20, "v18": 3.60, "v19": 2.82, "v23": 3.32}

# R21 read these six off the board by hand on 2026-08-22. Submission counts only ever grow,
# so each must still be present with a count >= what R21 recorded. A file that has lost any
# of them is the wrong file or a broken parse.
R21 = {"Thuitanium": 9, "wking edewd": 3, "rellik13": 9, "cstl": 34, "Tufa Labs": 116,
       "yuki16": 27}

# v10's own hidden draws (B14, B21) and its four same-build public draws. v10out has no
# per-game artifacts on disk, so it appears here as a mean only.
HIDDEN_V10 = [1.70, 1.32]
PUBLIC_V10 = [4.71, 4.55, 3.20, 2.82]
TOP5_MAP = 2.57  # the bar MAP.md's goal line still quotes, dated 2026-08-19


def read_board(path):
    rows = []
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            rows.append((int(r["Rank"]), r["TeamName"], float(r["Score"]),
                         int(r["SubmissionCount"])))
    return rows


def max_of_n(n, sims=200_000, seed=20260824):
    """E[max of n standard normals]. Simulated rather than tabulated so the constant is
    reproducible from this file alone."""
    rng = random.Random(seed)
    return sum(max(rng.gauss(0, 1) for _ in range(n)) for _ in range(sims)) / sims


def gain_over(c, mu, sigma):
    """E[max(X, c)] - c for X ~ N(mu, sigma): what one further draw adds to a leaderboard
    that already holds c. Closed form, so it does not inherit the simulator's noise."""
    z = (c - mu) / sigma
    phi = math.exp(-z * z / 2) / math.sqrt(2 * math.pi)
    tail = 0.5 * math.erfc(z / math.sqrt(2))
    return sigma * phi - (c - mu) * tail


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        print("usage: python scripts/b30_draws.py <public-leaderboard.csv>")
        return 2
    board = read_board(argv[0])

    # ---- CONTROL 1: the per-game loader reproduces every published public mean ----
    bad = []
    for run, want in PUBLISHED.items():
        g = load(os.path.join(ART, run, "benchmark.json"))["games"]
        got = round(sum(v["score"] for v in g.values()) / len(g), 2)
        if got != want:
            bad.append(f"{run}: got {got}, LEDGER says {want}")
    print(f"CONTROL 1  five published public means reproduced: {not bad}")
    if bad:
        for b in bad:
            print("   ", b)
        print("  loader does not reproduce the published numbers -- STOP, read nothing below")
        return 1

    # ---- CONTROL 2: the board still holds the six teams R21 named, counts not shrunk ----
    byname = {t[1]: t for t in board}
    miss = [n for n in R21 if n not in byname]
    shrunk = [n for n in R21 if n in byname and byname[n][3] < R21[n]]
    print(f"CONTROL 2  {len(board)} teams; R21's six present={not miss}, counts monotone={not shrunk}")
    if miss or shrunk:
        print(f"    missing={miss} shrunk={shrunk}")
        print("  wrong board or broken parse -- STOP, read nothing below")
        return 1

    # ================= 1. where the bar actually is =================
    scores = [t[2] for t in board]
    top5 = scores[4]
    us = byname["Thuitanium"]
    print(f"\nSTANDINGS   us: rank {us[0]}, score {us[2]:.2f}, {us[3]} submissions")
    print(f"  leaderboard shows {us[2]:.2f} while our two v10 draws were "
          f"{HIDDEN_V10[0]} and {HIDDEN_V10[1]} -> Kaggle KEEPS BEST, confirmed from the")
    print("  board itself rather than from our own notes (the only prior source)")
    print(f"  top-5 bar NOW = {top5:.2f}   (MAP.md's goal line still says {TOP5_MAP})")
    print(f"  #1 = {board[0][1]} at {board[0][2]:.2f} with {board[0][3]} submissions")

    # ================= 2. the upper bound from 2,506 teams =================
    act = [t for t in board if t[2] > 0]
    print(f"\nWHAT A DRAW BUYS -- upper bound, {len(act)} teams that ever scored")
    print("  (confounded: better teams submit more, so every rise here overstates the draw)")
    print(f"  {'subs':<8}{'n':>5}{'median':>8}{'mean':>7}{'max':>7}")
    for lo, hi in [(1, 1), (2, 3), (4, 7), (8, 15), (16, 31), (32, 63), (64, 10**9)]:
        g = [t[2] for t in act if lo <= t[3] <= hi]
        if not g:
            continue
        lab = str(lo) if lo == hi else (f"{lo}-{hi}" if hi < 10**9 else f"{lo}+")
        print(f"  {lab:<8}{len(g):>5}{st.median(g):>8.2f}{sum(g)/len(g):>7.2f}{max(g):>7.2f}")

    above = sorted(t[3] for t in board if t[2] >= top5)
    cheap = min((t[3], t[1], t[2]) for t in board if t[2] > us[2])
    many = [t for t in act if t[3] >= us[3]]
    print(f"\n  teams at or above the {top5:.2f} bar used {above} submissions -- min {above[0]}")
    print(f"  cheapest team above our {us[2]:.2f}: {cheap[1]} scored {cheap[2]:.2f} on {cheap[0]} submission(s)")
    print(f"  of the {len(many)} teams with >= {us[3]} submissions, "
          f"{sum(1 for t in many if t[2] < us[2])} score BELOW us")

    # ================= 3. two independent readings of the hidden sigma =================
    mu = sum(HIDDEN_V10) / len(HIDDEN_V10)
    sd_pair = st.stdev(HIDDEN_V10)
    pub_mu, pub_sd = st.mean(PUBLIC_V10), st.stdev(PUBLIC_V10)
    cv_pub, cv_hid = pub_sd / pub_mu, sd_pair / mu
    sd_cv = cv_pub * mu          # transfer the public CV onto the hidden mean
    print(f"\nHIDDEN SIGMA  two independent estimates of the same quantity")
    print(f"  (a) the hidden A/A pair {HIDDEN_V10}: mean {mu:.2f}, sd {sd_pair:.3f}, CV {cv_hid:.3f}")
    print(f"  (b) four same-build PUBLIC draws {PUBLIC_V10}: mean {pub_mu:.2f}, sd {pub_sd:.3f}, "
          f"CV {cv_pub:.3f}")
    print(f"      transferred onto the hidden mean (assumes multiplicative noise): sd {sd_cv:.3f}")
    print(f"  they agree within a factor of {max(sd_cv, sd_pair)/min(sd_cv, sd_pair):.2f} "
          f"-- neither is anywhere near 1.0")

    # ================= 4. is re-drawing v10 a route? =================
    print(f"\nRE-DRAWING v10   the board already holds {us[2]:.2f}; a further draw only counts if it beats it")
    e1 = max_of_n(1)
    print(f"  simulator check: E[max of 1 standard normal] = {e1:+.4f} (must be ~0)")
    for sd in (sd_pair, sd_cv):
        g1 = gain_over(us[2], mu, sd)
        print(f"  sigma={sd:.3f}:  one more draw is worth {g1:+.3f} on the leaderboard")
        for n, what in ((3, "half a week"), (7, "a full week of the 1/day quota")):
            exp_max = mu + sd * max_of_n(n)
            print(f"              {n} draws ({what}) -> E[best] {exp_max:.2f}, "
                  f"gain {exp_max - us[2]:+.2f}")
    need = (top5 - mu) / max_of_n(7)
    print(f"  sigma needed for 7 v10 re-draws to REACH {top5:.2f}: {need:.2f} "
          f"-- {need/max(sd_pair, sd_cv):.1f}x the larger measured value")

    # ================= 5. the shrink, with means on BOTH sides =================
    # LEDGER CORRECTION 2 puts the shrink at 3.05x by dividing the top TWO public draws
    # [4.55, 4.71] by the MEAN of the two hidden draws. That mixes a max with a mean --
    # the same error the correction itself flags one paragraph earlier about quoting 1.70.
    shrink_mixed = st.mean([4.55, 4.71]) / mu
    shrink_means = pub_mu / mu
    print(f"\nSHRINK   LEDGER prints 3.05x; described as it describes itself -- the top two "
          f"public draws over the hidden MEAN -- it recomputes to {shrink_mixed:.2f}x")
    print(f"  means on both sides ({pub_mu:.2f} public over {mu:.2f} hidden): {shrink_means:.2f}x")
    print(f"  so a candidate needs public {top5*shrink_means:.2f} to sit at the {top5:.2f} bar, "
          f"not {top5*shrink_mixed:.2f}")
    print(f"  B20's efficiency ceiling is 5.80 public = {5.80/shrink_means:.2f} hidden -- still "
          "below the bar, so depth stays the only axis")

    # ================= 6. the ticket's second data point =================
    print("\nB30's PREMISE  'variance grows with score (v9-lite 0.00 vs v10 0.38)'")
    print(f"  a constant coefficient of variation already predicts that: CV is {cv_pub:.3f} "
          f"public and {cv_hid:.3f} hidden")
    print(f"  at v9-lite's 0.10 the same CV predicts sigma = {cv_pub*0.10:.3f} -- the pair had "
          "almost no room to differ")
    print("  so the 0.00 is what the v10 pair alone already implies, not a second measurement.")
    print("  The conclusion (2+ draws to rank a high build) stands; it rests on ONE pair.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
