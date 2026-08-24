"""What the fixed clock actually buys, and who spent it -- the derived half of B33.

censoring.py asks whether the level-up process was still running when the wall arrived.
This asks the other half: how big the budget is, that it never varies, and which past
runs are evidence about raising it.

Two data sources, deliberately kept apart:

  MEASURED -- summary.txt and benchmark.json of the five downloaded runs. Everything in
  sections 1 and 2 is read off disk.

  TRANSCRIBED -- v14 / v20 / v21 have no artifacts here (only five corpora were pulled),
  so their rows come from notes/LEDGER-all-runs.md by hand and are labelled as such.
  Section 3 marks every transcribed row so a reader knows which figures a re-run checks
  and which it only repeats.

Positive control: section 2 predicts each run's `total tokens` from an INDEPENDENT pair
of fields (`generated tokens/sec` x duration) and fails loudly if the ratio strays. If
that is off, `total tokens` is not the generated count and the tok/action column in
section 3 means something else.
"""
import os, re, glob, statistics, sys

BASE = os.path.expanduser("~/Claude/arc-artifacts")
CAP_S = 7920.0
GAMES = 25

# TRANSCRIBED from notes/LEDGER-all-runs.md -- anim bundle only, so the bundle is not a
# free variable. Mtok is None where the LEDGER does not record it.
#            run        public levels actions  Mtok
LEDGER_ANIM = [
    ("v16",      3.51, 24, 1218, 2.02),
    ("v10out",   4.55, 22, 1285, 1.87),
    ("thui-v1",  3.20, 22, 1493, 2.16),
    ("v18",      3.60, 22, 1576, None),
    ("v10cal",   4.71, 28, 1597, 2.03),
    ("v14",      2.87, 19, 1633, 2.35),
    ("v23",      3.32, 20, 1634, 2.21),
    ("v19",      2.82, 20, 1638, None),
    ("v12",      3.72, 24, 1810, 2.19),
    ("v21",      1.25, 12, 2921, 2.27),
    ("v20",      0.18,  3, 7656, None),
]
ON_DISK = {"v10cal", "v18", "v19", "v23"}   # thui-v1 is on disk as `thuiv1`


def summaries():
    out = {}
    for d in sorted(glob.glob(os.path.join(BASE, "*"))):
        path = os.path.join(d, "summary.txt")
        if not os.path.exists(path):
            continue
        text = open(path).read()

        def grab(pattern, cast=float):
            m = re.search(pattern, text)
            return cast(m.group(1)) if m else None

        dur = re.search(r"duration:\s+(?:(\d+)h )?(\d+)m (\d+)s", text)
        secs = int(dur.group(1) or 0) * 3600 + int(dur.group(2)) * 60 + int(dur.group(3))
        out[os.path.basename(d)] = {
            "games": grab(r"games:\s+(\d+)", int),
            "mean": grab(r"mean score:\s+([\d.]+)"),
            "actions": grab(r"total actions:\s+(\d+)", int),
            "tokens": grab(r"total tokens:\s+(\d+)", int),
            "wall": grab(r"total wallclock:\s+([\d.]+)"),
            "rate": grab(r"generated tokens/sec:\s+([\d.]+)"),
            "job_s": secs,
        }
    return out


def section1(runs):
    print("1. the budget is a constant, and it is spent in full every time  [MEASURED]")
    print("   {:9s} {:>3s} {:>6s} {:>6s} {:>11s} {:>8s} {:>7s}".format(
        "corpus", "gm", "mean", "acts", "wall_s", "s/game", "vs cap"))
    for name, r in runs.items():
        per = r["wall"] / r["games"]
        print("   {:9s} {:3d} {:6.2f} {:6d} {:11.1f} {:8.1f} {:6.1%}".format(
            name, r["games"], r["mean"], r["actions"], r["wall"], per, per / CAP_S))
    print("   cap: max_runtime_s_per_game = {:.0f}. One wave for public-25 (ceil(25/28)=1),".format(CAP_S))
    print("   so the job wallclock is ~one game's clock and the 32,400 s envelope is 24.6% used.")
    print()


def section2(runs):
    print("2. CONTROL -- is `total tokens` the GENERATED count?  [MEASURED]")
    bad = []
    for name, r in runs.items():
        pred = r["rate"] * r["job_s"]
        ratio = pred / r["tokens"]
        print("   {:9s} total={:9d}  rate*duration={:11.0f}  ratio={:.4f}".format(
            name, r["tokens"], pred, ratio))
        if not 0.995 <= ratio <= 1.005:
            bad.append(name)
    if bad:
        sys.exit("CONTROL FAILED for {} -- tok/action below is not reasoning output".format(bad))
    toks = [r["tokens"] for r in runs.values()]
    print("   ratios ~1.000 => tok/action is reasoning OUTPUT per action, not input+output.")
    print("   generated-token budget across builds: {:.2f}M..{:.2f}M, spread {:.1%}".format(
        min(toks) / 1e6, max(toks) / 1e6, max(toks) / min(toks) - 1))
    print("   near-constant because the clock is fixed -- every lever so far only redistributed it.")
    print()


def corr(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den


def check_transcription(runs):
    """The five on-disk runs appear in LEDGER_ANIM too. Verify the hand-typed cells
    against the artifacts before any of section 3 is read -- a transcription error
    would move the correlation and the v14 comparison without looking wrong."""
    alias = {"thui-v1": "thuiv1"}
    checked = mismatch = 0
    for name, pub, lvl, acts, mtok in LEDGER_ANIM:
        key = alias.get(name, name)
        if key not in runs:
            continue
        checked += 1
        disk = runs[key]
        for field, typed, found in (("actions", acts, disk["actions"]),
                                    ("mean", pub, disk["mean"])):
            if abs(typed - found) > (0.005 if field == "mean" else 0):
                print("   MISMATCH {} {}: LEDGER {} vs disk {}".format(name, field, typed, found))
                mismatch += 1
    print("   CONTROL transcription: {} of {} LEDGER rows checked against disk, {} mismatches".format(
        checked, len(LEDGER_ANIM), mismatch))
    if checked < 5:
        sys.exit("only {} rows were checkable -- the control is not discriminating".format(checked))
    if mismatch:
        sys.exit("LEDGER transcription disagrees with the artifacts; fix the table before reading on")
    print()


def section3(runs):
    check_transcription(runs)
    print("3. which runs are evidence about a LONGER clock  [rows marked T = TRANSCRIBED]")
    print("   {:9s} {:>2s} {:>5s} {:>4s} {:>6s} {:>8s} {:>7s}".format(
        "run", "src", "pub", "lvl", "acts", "tok/act", "s/act"))
    clock = CAP_S * GAMES
    for name, pub, lvl, acts, mtok in LEDGER_ANIM:
        on_disk = name in ON_DISK or (name == "thui-v1" and "thuiv1" in runs)
        ta = "{:8.0f}".format(mtok * 1e6 / acts) if mtok else "       -"
        print("   {:9s} {:>2s} {:5.2f} {:4d} {:6d} {} {:7.1f}".format(
            name, "M" if on_disk else "T", pub, lvl, acts, ta, clock / acts))
    A = [r[3] for r in LEDGER_ANIM]
    L = [r[2] for r in LEDGER_ANIM]
    sub = [r for r in LEDGER_ANIM if r[0] not in ("v20", "v21")]
    print()
    print("   corr(actions, levels), all {} anim runs      = {:+.3f}".format(len(LEDGER_ANIM), corr(A, L)))
    print("   the same, dropping v20 and v21 (n={})        = {:+.3f}".format(
        len(sub), corr([r[3] for r in sub], [r[2] for r in sub])))
    print("   => the negative correlation is those two runs, not a law. Both bought actions")
    print("      by degrading reasoning-per-action, so neither is evidence about a longer clock.")
    print()
    base = next(r for r in LEDGER_ANIM if r[0] == "v10out")
    v14 = next(r for r in LEDGER_ANIM if r[0] == "v14")
    b_ta, v_ta = base[4] * 1e6 / base[3], v14[4] * 1e6 / v14[3]
    print("   the one precedent -- v14 (B16) held reasoning-per-action fixed:")
    print("     actions {:+.1%}   tok/action {:+.1%}   levels {:+d}".format(
        v14[3] / base[3] - 1, v_ta / b_ta - 1, v14[2] - base[2]))
    print("   one sample, inside this corpus's noise. It is the whole prior, in both directions.")


if __name__ == "__main__":
    runs = summaries()
    if len(runs) != 5:
        sys.exit("expected 5 downloaded runs under {}, found {}".format(BASE, sorted(runs)))
    section1(runs)
    section2(runs)
    section3(runs)
