"""Public full25 runs truncated at the short clock: levels/game by t<=T, per-game token rate, start spread.
0 GPU, reads benchmark.json only. usage: python clock_match.py [T_s]"""
import glob, json, sys
from datetime import datetime
T = float(sys.argv[1]) if len(sys.argv) > 1 else 1800.0


def per_run(path):
    b = json.load(open(path, encoding="utf-8"))
    runs = b["game_runs"]
    starts = sorted(datetime.fromisoformat(g["started_at"]) for g in runs if g.get("started_at"))
    spread = (starts[-1] - starts[0]).total_seconds() if starts else None
    at_t = end = 0
    rates = []
    for g in runs:
        h, apl = g["history"], g["actions_per_level"]
        k = 0
        for n in apl[: g["levels_completed"]]:
            k += n
            if h[k - 1]["wallclock_seconds"] <= T:
                at_t += 1
        end += g["levels_completed"]
        if h:
            rates.append(sum(a["generated_tokens"] for a in h) / max(1e-9, h[-1]["wallclock_seconds"]))
    rates.sort()
    return len(runs), at_t, end, spread, rates[len(rates) // 2] if rates else 0


paths = sorted(glob.glob("kout*/benchmark.json"))
print(f"T={T:.0f}s   run | games | levels/game by T | levels/game at end | start spread s | median tok/s per game")
for p in paths:
    try:
        n, at_t, end, spread, rate = per_run(p)
    except Exception as e:                      # older layouts without history
        print(f"  skip {p}: {type(e).__name__}"); continue
    if n not in (3, 25):
        continue
    print(f"  {p.split('/')[0].split(chr(92))[0]:44s} {n:3d}  {at_t / n:5.2f}  {end / n:5.2f}  {spread}  {rate:6.1f}")
