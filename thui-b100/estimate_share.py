"""Pre-registration input: under the revised keep rule, what share of the REASONING sent in a request's history window
would be stripped, on requests made after the first level clear? Window = the last W assistant turns (W bracketed,
because the real window is set by a 32k-token estimate that also counts image parts). Turn level + clearing flag come
from the "Current state ... level L" markers exactly as the graft reads them.
"""
import glob, re, sys, statistics as st
S = sys.argv[1]
TOK = re.compile(r"\[MODEL RESPONSE META\]\n(?:.*?\n)*?reasoning_chars: (\d+)|Current state: step \d+, level (\d+)")
out = {}
for W in (8, 12, 20, 30):
    elig = tot = reqs = 0
    shares = []
    for p in glob.glob(f"{S}/kout-*/transcripts/*.txt"):
        t = open(p, encoding="utf-8", errors="replace").read()
        turns, level = [], None   # (level, reasoning_chars)
        for m in TOK.finditer(t):
            if m.group(2):
                level = int(m.group(2))
            elif level is not None:
                turns.append([level, int(m.group(1)), False])
        for i in range(1, len(turns)):   # clearing = last turn before a level increase
            if turns[i][0] > turns[i - 1][0]:
                turns[i - 1][2] = True
        for i, (lv, rc, _) in enumerate(turns):
            if lv < 2:
                continue
            win = turns[max(0, i - W):i]
            e = sum(r for l, r, c in win if l != lv and not c)
            a = sum(r for l, r, c in win)
            if a:
                elig += e; tot += a; reqs += 1; shares.append(e / a)
    out[W] = (reqs, elig / tot, st.median(shares), sum(s > 0 for s in shares) / len(shares))
for W, (n, share, med, frac) in out.items():
    print(f"W={W:2d}: post-clear requests {n}, eligible reasoning share {share:.3f} (median per request {med:.3f}), "
          f"requests with anything to strip {frac:.2f}")
