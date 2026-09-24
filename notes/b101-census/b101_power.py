"""Can ONE full-clock B101 pair be read? Power of the team's paired per-game sign-flip permutation test (rank_runs.py
logic: two-sided, mean of per-game score deltas, p < 0.05) using the 4 same-build a10-ctl runs as the noise model.
Effect model: in the ARM run, each game that had a death after non-empty slots (b101_census lane) gains +1 level with
probability q; the gained level scores s = 0.8 (a typical L2 clear) at index levels_completed+1, weight (k+1)/(n(n+1)/2).

usage: run from a directory holding the downloaded outputs of the four same-build B81 controls
  kaggle kernels output yocybercode/thui-a10-ctl-full25-rN -p kout-yo-thui-a10-ctl-full25-rN   (N = 1, 2, 3, 5)
  python <this dir>/b101_power.py          # needs b101_census.py beside it; 0 GPU, ~minutes"""
import itertools, json, os, random, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b101_census import census
RUNS = ["kout-yo-thui-a10-ctl-full25-r1", "kout-yo-thui-a10-ctl-full25-r2", "kout-yo-thui-a10-ctl-full25-r3",
        "kout-yo-thui-a10-ctl-full25-r5"]
rng = random.Random(20260924)


def load(run):
    return {g["game_id"][:13]: (g["final_score"], g["levels_completed"],  # final_score is already percent per game
                                g["number_of_levels"]) for g in json.load(open(os.path.join(run, "benchmark.json"), encoding="utf-8"))["game_runs"]}


def p_signflip(deltas, n_perm=4000):
    obs = abs(st.mean(deltas)); hits = 0
    for _ in range(n_perm):
        if abs(st.mean(d if rng.random() < 0.5 else -d for d in deltas)) >= obs - 1e-12:
            hits += 1
    return (hits + 1) / (n_perm + 1)


data = {r: load(r) for r in RUNS}
elig = {r: {d[0] for d in census(r)[0] if d[3]} for r in RUNS}
games = sorted(data[RUNS[0]])
print("per-run total score:", {r[-2:]: round(sum(v[0] for v in data[r].values()) / 25, 2) for r in RUNS},
      "| eligible games per run:", {r[-2:]: len(elig[r]) for r in RUNS})
# null: every ordered pair of distinct same-build runs
null_p = [p_signflip([data[b][g][0] - data[a][g][0] for g in games]) for a, b in itertools.permutations(RUNS, 2)]
print("NULL (12 ordered same-build pairs): p-values", sorted(round(p, 3) for p in null_p),
      "| false positives:", sum(p < 0.05 for p in null_p))
for q in (0.3, 0.6, 1.0):
    hits = 0; trials = 0; lv_gain = []
    for a, b in itertools.permutations(RUNS, 2):
        for _ in range(25):
            arm = {}; gain = 0
            for g in games:
                s, k, n = data[b][g]
                if g in elig[b] and k < n and rng.random() < q:
                    s += 100.0 * 0.8 * (k + 1) / (n * (n + 1) / 2); gain += 1
                arm[g] = s
            lv_gain.append(gain)
            p = p_signflip([arm[g] - data[a][g][0] for g in games], 1000)
            hits += p < 0.05 and st.mean(arm[g] - data[a][g][0] for g in games) > 0; trials += 1
    print(f"q={q}: injected +levels per run mean {st.mean(lv_gain):.1f} | power (p<0.05, arm better) {hits}/{trials} = {hits/trials:.2f}")

# --- levels-based variant of the same test, and pooling k arm runs (bootstrapped from the 4 controls) vs the rest
print("\nLEVELS test (per-game levels deltas, same sign-flip):")
null_l = [p_signflip([data[b][g][1] - data[a][g][1] for g in games]) for a, b in itertools.permutations(RUNS, 2)]
print("  NULL p-values", sorted(round(p, 3) for p in null_l), "| false positives:", sum(p < 0.05 for p in null_l))
for q in (0.3, 0.6, 1.0):
    hits = trials = 0
    for a, b in itertools.permutations(RUNS, 2):
        for _ in range(25):
            arm = {g: data[b][g][1] + (1 if (g in elig[b] and data[b][g][1] < data[b][g][2] and rng.random() < q) else 0) for g in games}
            d = [arm[g] - data[a][g][1] for g in games]
            hits += p_signflip(d, 1000) < 0.05 and st.mean(d) > 0; trials += 1
    print(f"  q={q}: power {hits}/{trials} = {hits/trials:.2f}")
print("\nPOOLED score test: mean of k arm runs vs mean of the other controls (arms drawn from controls + effect):")
for k in (2, 3):
    for q in (0.3, 0.6):
        hits = trials = 0
        for _ in range(120):
            arm_src = rng.sample(RUNS, k); ctl = [r for r in RUNS if r not in arm_src] or RUNS
            arm_mean = {g: 0.0 for g in games}
            for r in arm_src:
                for g in games:
                    s, lv, n = data[r][g]
                    if g in elig[r] and lv < n and rng.random() < q:
                        s += 100.0 * 0.8 * (lv + 1) / (n * (n + 1) / 2)
                    arm_mean[g] += s / k
            ctl_mean = {g: st.mean(data[r][g][0] for r in ctl) for g in games}
            d = [arm_mean[g] - ctl_mean[g] for g in games]
            hits += p_signflip(d, 1000) < 0.05 and st.mean(d) > 0; trials += 1
        print(f"  k={k} arm runs vs {4-k} controls, q={q}: power {hits}/{trials} = {hits/trials:.2f}")
