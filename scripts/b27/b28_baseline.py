"""B28, offline half: the noise floor of the search-usage probe.

B28 asks whether v22's ported BFS instruction moves search usage off its ~2% base rate.
That comparison is one run against a baseline, so it can only rank something if the
between-run spread of the probe on runs that were NOT prompted differently is smaller
than the lift being claimed. Nobody has measured that spread.

This computes it over the five-run corpus, with the cleanest possible control: v10cal and
thuiv1 are the SAME BUILD (B27: probe inert, rank_runs.py p=0.3027), so any difference
between their search rates is noise by construction.

Validation gate first: the probe must reproduce R29 sec.6's 31/1973 = 1.6% before any new
number is read off it.
"""
import re, sys, collections
from corpus import RUNS5, game_files, load_game, game_key

# R29 sec.6's exact list -- reproducing its 31/1973 is the control, so do not "improve" it.
SEARCH = re.compile(
    r"bfs|deque|heapq|itertools\.product|permutations|product\(|def solve|def search|"
    r"def plan|visited=|frontier|queue=\[",
    re.I,
)
CODE = re.compile(r"<parameter=code>(.*?)</parameter>", re.S)
MARK = re.compile(r"^\[[A-Z][A-Z ]+\]$", re.M)

# A transcript is [SYSTEM PROMPT] [USER PROMPT] [THINKING]* [ASSISTANT] [ANALYZER STATUS],
# and `<parameter=code>` appears in BOTH [THINKING] and [ASSISTANT] -- 1,009 blocks against
# 1,432 over the pair. sec.6 says "inside the tool call's <parameter=code>", and only the
# [ASSISTANT] block is a tool call; [THINKING] is code the model drafted and did not run.
# Joining both gives 72/1973 = 3.65% where sec.6 published 31/1973. Which section the probe
# reads is not a detail: it is the difference between measuring what the agent RAN and what
# it CONSIDERED, and prompt pressure is likelier to move the second.


def code_of(turn, section="[ASSISTANT]"):
    bounds = [(m.start(), m.group()) for m in MARK.finditer(turn)]
    out = []
    for m in CODE.finditer(turn):
        cur = None
        for pos, name in bounds:
            if pos < m.start():
                cur = name
            else:
                break
        if section is None or cur == section:
            out.append(m.group(1))
    return "\n".join(out)


def turns_of(run):
    """(game, transcript) for every analysis turn."""
    for f in game_files(run):
        g = game_key(f)
        for e in load_game(f):
            if e.get("type") == "analysis":
                t = e.get("transcript")
                if t:
                    yield g, t


def rate(run):
    """(turns, hits in executed code, turns carrying executed code, hits in drafted-or-executed)"""
    n = hit = ncode = both = 0
    for _, t in turns_of(run):
        n += 1
        c = code_of(t)
        if c:
            ncode += 1
        if SEARCH.search(c):
            hit += 1
        if SEARCH.search(code_of(t, section=None)):
            both += 1
    return n, hit, ncode, both


def fisher(a, b, c, d):
    """two-sided Fisher exact on [[a,b],[c,d]]; scipy-free."""
    from math import comb
    from fractions import Fraction
    n = a + b + c + d
    r1, c1 = a + b, a + c
    obs = comb(r1, a) * comb(n - r1, c1 - a)
    tot = comb(n, c1)
    # exact integer weights -- comparing them as floats overflows at these table sizes
    p = 0
    lo = max(0, c1 - (n - r1))
    hi = min(r1, c1)
    for k in range(lo, hi + 1):
        w = comb(r1, k) * comb(n - r1, c1 - k)
        if w <= obs:
            p += w
    return float(Fraction(p, tot))


def detectable(p0, n0, n1, alpha=0.05, power=0.80, sims=400, seed=20260824):
    """Smallest lift (in percentage points) on top of p0 that a Fisher test between a
    baseline of n0 turns and a new run of n1 turns detects at `power`. Simulated, because
    the counts are tiny and normal approximations lie at p ~ 0.02."""
    import random
    rng = random.Random(seed)
    for lift in range(1, 41):
        p1 = p0 + lift / 100.0
        if p1 >= 1:
            break
        wins = 0
        for _ in range(sims):
            a = sum(1 for _ in range(n0) if rng.random() < p0)
            b = sum(1 for _ in range(n1) if rng.random() < p1)
            if fisher(a, n0 - a, b, n1 - b) < alpha:
                wins += 1
        if wins / sims >= power:
            return lift, wins / sims
    return None, None


if __name__ == "__main__":
    per = {}
    for r in RUNS5:
        per[r] = rate(r)

    print("per-run search-construct rate")
    print(f"{'run':8s} {'turns':>6s} {'w/code':>7s} {'ran':>5s} {'rate':>7s} "
          f"{'+drafted':>9s} {'rate':>7s}")
    for r in RUNS5:
        n, h, nc, b = per[r]
        print(f"{r:8s} {n:6d} {nc:7d} {h:5d} {100*h/n:6.2f}% {b:9d} {100*b/n:6.2f}%")

    # ---- control: R29 sec.6 reported 31/1973 = 1.6% over v10cal+thuiv1 ----
    pn = per["v10cal"][0] + per["thuiv1"][0]
    ph = per["v10cal"][1] + per["thuiv1"][1]
    ok = (pn == 1973 and ph == 31)
    print(f"\nCONTROL  v10cal+thuiv1 = {ph}/{pn} = {100*ph/pn:.2f}%"
          f"   (R29 sec.6: 31/1973 = 1.6%)  match={ok}")
    if not ok:
        print("  instrument does not reproduce the published number -- STOP, read nothing below")
        sys.exit(1)

    # ---- the floor: same build, two runs ----
    n0, h0, _, _ = per["v10cal"]
    n1, h1, _, _ = per["thuiv1"]
    p_same = fisher(h0, n0 - h0, h1, n1 - h1)
    print("\nSAME-BUILD SPREAD  (v10cal vs thuiv1 -- identical build, B27 p=0.3027)")
    print(f"  {h0}/{n0} = {100*h0/n0:.2f}%   vs   {h1}/{n1} = {100*h1/n1:.2f}%"
          f"   Fisher p = {p_same:.4f}   spread = {abs(100*h0/n0 - 100*h1/n1):.2f} pp")

    rates = sorted((100 * per[r][1] / per[r][0], r) for r in RUNS5)
    print(f"\nALL-FIVE SPREAD  {rates[0][0]:.2f}% ({rates[0][1]}) .. "
          f"{rates[-1][0]:.2f}% ({rates[-1][1]})  = {rates[-1][0]-rates[0][0]:.2f} pp")

    # every unprompted pair, so the spread is not read off one lucky pairing
    print("\n  pairwise, all 10 unprompted pairs:")
    worst = (1.0, None)
    for i, a in enumerate(RUNS5):
        for b in RUNS5[i + 1:]:
            na, ha, _, _ = per[a]
            nb, hb, _, _ = per[b]
            p = fisher(ha, na - ha, hb, nb - hb)
            flag = "  <-- separates" if p < 0.05 else ""
            print(f"    {a:7s} vs {b:7s}  {100*ha/na:5.2f}% vs {100*hb/nb:5.2f}%  p={p:.4f}{flag}")
            if p < worst[0]:
                worst = (p, (a, b))

    # ---- what a single v22 run could detect ----
    allh = sum(per[r][1] for r in RUNS5)
    alln = sum(per[r][0] for r in RUNS5)
    p0 = allh / alln
    n_v22 = alln // len(RUNS5)  # a run is ~1/5 of the corpus
    lift, got = detectable(p0, alln, n_v22)
    print(f"\nFLOOR  baseline {allh}/{alln} = {100*p0:.2f}%, v22 assumed ~{n_v22} turns")
    if lift is None:
        print("  no lift up to +40pp reaches 80% power -- the probe cannot rank this run")
    else:
        print(f"  smallest detectable lift at 80% power: +{lift} pp "
              f"(to {100*p0+lift:.1f}%), measured power {got:.2f}")
    print(f"\nWORST unprompted pair: {worst[1]} at p={worst[0]:.4f}")

    # ---- does stratifying by game rescue it? ----
    # sec.6 already showed unstratified (b) is confounded by which games are hard. If the
    # unprompted separations above survive pairing on the game, no stratification saves the
    # B28 design either. Paired sign-flip permutation on the per-game rate difference --
    # the same unit and the same test family sec.1 used.
    import random

    def by_game(run):
        d = collections.defaultdict(lambda: [0, 0])
        for g, t in turns_of(run):
            k = g.split("-")[0]
            d[k][0] += 1
            if SEARCH.search(code_of(t)):
                d[k][1] += 1
        return d

    G = {r: by_game(r) for r in RUNS5}

    def paired(a, b, nperm=100_000, seed=20260824):
        ga, gb = G[a], G[b]
        keys = [k for k in ga if k in gb and (ga[k][0] and gb[k][0])]
        diffs = [100 * ga[k][1] / ga[k][0] - 100 * gb[k][1] / gb[k][0] for k in keys]
        obs = sum(diffs) / len(diffs)
        rng = random.Random(seed)
        ge = 0
        for _ in range(nperm):
            s = sum(d if rng.random() < 0.5 else -d for d in diffs)
            if abs(s / len(diffs)) >= abs(obs) - 1e-12:
                ge += 1
        return len(keys), obs, (ge + 1) / (nperm + 1)

    print("\n  stratified on the GAME (paired sign-flip, 100k perms):")
    surv = 0
    for i, a in enumerate(RUNS5):
        for b in RUNS5[i + 1:]:
            k, obs, p = paired(a, b)
            flag = "  <-- still separates" if p < 0.05 else ""
            if p < 0.05:
                surv += 1
            print(f"    {a:7s} vs {b:7s}  games={k:2d}  mean diff {obs:+5.2f} pp  p={p:.4f}{flag}")
    # A null is only worth reading with its floor beside it (sec.8's lesson). Plant a lift
    # into one arm's per-game rates and measure how often the paired test finds it.
    def strat_floor(base, sims=150, nperm=2000, seed=99):
        gb = G[base]
        keys = [k for k in gb if gb[k][0]]
        rng = random.Random(seed)
        for lift in range(1, 21):
            wins = 0
            for _ in range(sims):
                diffs = []
                for k in keys:
                    n = gb[k][0]
                    p = gb[k][1] / n
                    ha = sum(1 for _ in range(n) if rng.random() < p)
                    hb = sum(1 for _ in range(n) if rng.random() < min(1.0, p + lift / 100))
                    diffs.append(100 * hb / n - 100 * ha / n)
                obs = sum(diffs) / len(diffs)
                ge = sum(
                    1 for _ in range(nperm)
                    if abs(sum(d if rng.random() < 0.5 else -d for d in diffs) / len(diffs))
                    >= abs(obs) - 1e-12
                )
                if (ge + 1) / (nperm + 1) < 0.05:
                    wins += 1
            if wins / sims >= 0.80:
                return lift, wins / sims
        return None, None

    lf, pw = strat_floor("v10cal")
    if lf is None:
        print("\n  STRATIFIED FLOOR: no lift up to +20 pp reaches 80% power")
    else:
        print(f"\n  STRATIFIED FLOOR: +{lf} pp per game at 80% power (measured {pw:.2f})")

    print(f"\n  unprompted pairs separating: {surv}/10 stratified, "
          f"{sum(1 for i,a in enumerate(RUNS5) for b in RUNS5[i+1:] if fisher(per[a][1], per[a][0]-per[a][1], per[b][1], per[b][0]-per[b][1]) < 0.05)}/10 unstratified")
