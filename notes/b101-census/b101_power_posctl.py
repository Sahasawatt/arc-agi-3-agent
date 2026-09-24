"""Positive control for b101_power.py: the same sign-flip test must detect a LARGE effect (+1 level at s = 0.8 on
EVERY game that can still gain a level), else a power of 0 says nothing. Same cwd as b101_power.py."""
import itertools, os, statistics as st, sys
sys.argv = ["x"]
_here = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(_here, "b101_power.py"), encoding="utf-8").read().split('print("per-run total score:"')[0], globals())   # same dir, so b101_power.py's own __file__ lookup resolves here too
hits = trials = 0; mean_d = []
for a, b in itertools.permutations(RUNS, 2):
    for _ in range(10):
        arm = {}
        for g in games:
            s, k, n = data[b][g]
            if k < n:
                s += 100.0 * 0.8 * (k + 1) / (n * (n + 1) / 2)
            arm[g] = s
        d = [arm[g] - data[a][g][0] for g in games]; mean_d.append(st.mean(d))
        hits += p_signflip(d, 1000) < 0.05 and st.mean(d) > 0; trials += 1
print(f"POSITIVE CONTROL (+1 level on all 25 games): mean score delta {st.mean(mean_d):.2f}, power {hits}/{trials} = {hits/trials:.2f}")
sd = [st.pstdev([data[r][g][0] for r in RUNS]) for g in games]
print("per-game score sd across the 4 same-build runs: median", round(st.median(sd), 2), "max", round(max(sd), 2),
      "| games with sd > 5:", sum(x > 5 for x in sd))
