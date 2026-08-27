#!/usr/bin/env python3
"""B26 -- does the agent's uncertainty about WHAT AN ACTION DOES decay over a game?

R32 closed the one-bit version of this question: on *does this action change the board here*
the agent is already right (re-fires a recorded no-op 10.2% against a 52.2% repetition habit).
Its own closing line names what is left:

    "This measures ONE BIT and does not touch R29 section 2 -- the agent's belief about what an
     action *does* (lp85's 'one big loop', cd82 still asking 'do arrows move the piece?' at
     turn 40) is a richer object, is untouched, and remains the load-bearing half."

That richer object is a THEORY OF THE MECHANICS, and the exemplar R29 gives is temporal: still
asking at turn 40. So the measurable form is not "is the belief right" -- there is no ground
truth for a theory -- but:

    does the agent's expressed uncertainty about the mechanics DECAY as a game goes on,
    and does it decay differently in games that clear levels than in games that stall?

Either answer is useful. Decay only in clearing games makes "never learns the mechanics" the
stall mechanism. Flat in both makes the belief not the thing that separates them, and B26's
remaining half stops being load-bearing.

WHAT IS MEASURED
    Text     : the agent's OWN prose only -- the [ASSISTANT] and [THINKING] blocks of each
               analysis transcript. Everything else is sliced out.
    Rate     : mechanic-uncertainty hits per 1,000 characters of that prose.
    Position : each analysis row is placed in a QUARTILE of its own game's turn sequence, so
               games of different lengths are comparable.
    Split    : games that cleared >= 1 level vs games that cleared none.

THE TRAP THIS IS MOSTLY BUILT AROUND
    Every transcript embeds the 14,204-char [SYSTEM PROMPT]. R33 recorded this section trap and
    it still bit R39, whose first probe returned 100% on every column INCLUDING both controls,
    because the prompt contains the very tokens being counted. A rate computed over the whole
    transcript is a measurement of the prompt. C2 below is that trap turned into a control: a
    phrase that exists ONLY in the system prompt must score zero after slicing, while a phrase
    known to occur in assistant prose must not.

CONTROLS (all must pass or the script exits 1 and prints no findings)
    C1  corpus     200 cells, and the analysis-row count printed so a short walk is visible.
    C2  slicing    a system-prompt-only phrase scores 0 in the sliced prose; an assistant-prose
                   phrase scores > 0. Without both halves, "0 hits" cannot be told from "the
                   slice returned nothing".
    C3  prose vol  characters of agent prose per quartile, printed beside every rate. A rate
                   that falls because the agent writes LESS is not a rate that falls.
    C4  negative   a mechanic-neutral frequent word must be flat across quartiles. If it trends,
                   the quartile axis itself is confounded and no other trend can be read.
    C5  positive   selftest only: a marker injected into Q1 alone must be reported as decaying.
                   A pipeline that cannot see a trend that IS there cannot report its absence.

Reproduce:
    python scripts/b27/b26_mechanic_belief.py --selftest   # controls + synthetic, no corpus
    python scripts/b27/b26_mechanic_belief.py              # needs ~/Claude/arc-artifacts/ (0.56 GB)
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from pathlib import Path

ART = Path(os.path.expanduser("~/Claude/arc-artifacts"))
RUNS = ["v10cal", "v18", "v19", "v23", "thuiv1", "thuiv1-1r2", "clock2x", "v25seed"]

# The agent's own voice. [TOOL RESULT] is the environment talking and [SYSTEM PROMPT] /
# [USER PROMPT] are ours, so none of them is evidence about what the agent believes.
OWN = re.compile(r"^\[(ASSISTANT|THINKING)\]$", re.M)
# The `:` branch is load-bearing: the markers that end an [ASSISTANT] block in practice are
# `[TOOL CALL: python]` and `[TOOL RESULT: python]`. A pattern without it does not recognise
# them as boundaries, so the agent's prose silently absorbs the ENVIRONMENT's output and every
# rate below becomes a measurement of tool results. Caught by the selftest, not by reading.
SECTION = re.compile(r"^\[[A-Z][A-Z ]*(?::[^\]\n]*)?\]", re.M)

# Uncertainty ABOUT MECHANICS: a hedge or a question in the same sentence as an action verb.
# Deliberately not a bare hedge list -- "maybe I should try the left column" is uncertainty
# about a plan, not about what an action does.
VERB = r"(?:rotat\w*|translat\w*|mov\w*|shift\w*|toggl\w*|flip\w*|select\w*|place\w*|push\w*|turn\w*|swap\w*|press\w*|click\w*)"
HEDGE = r"(?:maybe|might|unclear|not sure|unsure|unknown|uncertain|hypothesis|assum\w*|guess\w*|test\w+ to see|to see (?:if|whether|what)|let'?s test|try(?:ing)? to (?:see|work out|determine)|still (?:don'?t|do not) know|appears? to|seems? to|possibly|perhaps)"
SENT = re.compile(r"[^.!?\n]*[.!?\n]")

NEUTRAL = re.compile(r"\bthe\b", re.I)          # C4: must be flat
SYS_ONLY = "You are a coding agent solving a grid-based puzzle game"   # C2 positive half
QUARTILES = 4


def own_prose(transcript: str) -> str:
    """Everything the AGENT wrote, and nothing else. Each [ASSISTANT]/[THINKING] block runs to
    the next section marker of any kind."""
    out = []
    for m in OWN.finditer(transcript):
        start = m.end()
        nxt = SECTION.search(transcript, start)
        out.append(transcript[start:nxt.start() if nxt else len(transcript)])
    return "\n".join(out)


def uncertainty_hits(prose: str) -> int:
    """A sentence counts once if it carries an action verb AND (a hedge OR a question mark)."""
    n = 0
    for s in SENT.findall(prose):
        if not re.search(VERB, s, re.I):
            continue
        if "?" in s or re.search(HEDGE, s, re.I):
            n += 1
    return n


def quartile(i: int, total: int) -> int:
    if total <= 1:
        return 0
    return min(QUARTILES - 1, (i * QUARTILES) // total)


def walk_game(path: Path):
    """-> (cleared_any, [(quartile, prose_chars, hits, neutral_hits)])"""
    rows = []
    cleared = False
    for ln in path.open():
        r = json.loads(ln)
        t = r.get("type")
        if t == "action" and r.get("level_completed"):
            cleared = True
        if t == "analysis":
            rows.append(r.get("transcript") or "")
    out = []
    for i, tr in enumerate(rows):
        p = own_prose(tr)
        out.append((quartile(i, len(rows)), len(p), uncertainty_hits(p),
                    len(NEUTRAL.findall(p))))
    return cleared, out


def rates(cells):
    """cells: list of (q, chars, hits, neutral) -> per-quartile rates per 1k chars"""
    agg = [[0, 0, 0] for _ in range(QUARTILES)]     # chars, hits, neutral
    for q, ch, h, nt in cells:
        agg[q][0] += ch
        agg[q][1] += h
        agg[q][2] += nt
    return [
        {"chars": a[0], "hits": a[1],
         "rate": (1000.0 * a[1] / a[0]) if a[0] else None,
         "neutral": (1000.0 * a[2] / a[0]) if a[0] else None}
        for a in agg
    ]


def auc_simple(pos: list[float], neg: list[float]) -> float:
    """Rank AUC, ties at half credit. Same estimator as scripts/b27/b35_identifiability.py."""
    tot = sum(1.0 if a > b else (0.5 if a == b else 0.0) for a in pos for b in neg)
    return tot / (len(pos) * len(neg))


def trend(rs):
    """Q1 -> Q4 change in the uncertainty rate, as a fraction of Q1."""
    a, b = rs[0]["rate"], rs[-1]["rate"]
    if not a or b is None:
        return None
    return (b - a) / a


# ---------------------------------------------------------------- selftest

def selftest() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        print(f"  {'ok  ' if cond else 'FAIL'} {name}")
        ok = ok and cond

    tr = ("[SYSTEM PROMPT]\nYou are a coding agent solving a grid-based puzzle game.\n"
          "Maybe the arrows rotate the piece?\n"
          "[USER PROMPT]\nhere is the frame\n"
          "[THINKING]\nDo the arrows move the piece or rotate it?\n"
          "[ASSISTANT]\nThe arrows rotate the piece, not translate.\n"
          "[TOOL RESULT: python]\nmaybe rotate? unclear\n")
    p = own_prose(tr)
    chk("slice drops the SYSTEM PROMPT", SYS_ONLY not in p)
    chk("slice drops TOOL RESULT", "unclear" not in p)
    chk("slice keeps THINKING", "Do the arrows move" in p)
    chk("slice keeps ASSISTANT", "not translate" in p)

    chk("question about a mechanic counts", uncertainty_hits("Do the arrows move the piece?") == 1)
    chk("hedge about a mechanic counts", uncertainty_hits("Maybe the arrows rotate it.") == 1)
    chk("a confident mechanic claim does NOT count",
        uncertainty_hits("The arrows rotate the piece, not translate.") == 0)
    chk("a hedge with no action verb does NOT count",
        uncertainty_hits("Maybe the answer is in the corner.") == 0)
    chk("a plain question with no action verb does NOT count",
        uncertainty_hits("Which colour is the target?") == 0)

    chk("quartile puts index 0 of 8 in Q1", quartile(0, 8) == 0)
    chk("quartile puts the last index in Q4", quartile(7, 8) == 3)
    chk("quartile of a single-row game is Q1", quartile(0, 1) == 0)

    # C5 positive control: a marker present ONLY in Q1 must be reported as a decay
    cells = [(0, 1000, 10, 100), (1, 1000, 0, 100), (2, 1000, 0, 100), (3, 1000, 0, 100)]
    t = trend(rates(cells))
    chk("C5 pipeline sees a planted Q1-only decay", t is not None and t <= -0.99)
    flat = [(q, 1000, 5, 100) for q in range(4)]
    chk("a flat input reports no trend", abs(trend(rates(flat))) < 1e-9)
    rising = [(0, 1000, 1, 100), (1, 1000, 2, 100), (2, 1000, 3, 100), (3, 1000, 4, 100)]
    chk("a rising input reports a rise", trend(rates(rising)) > 0)

    print("\nSELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--runs", type=int, default=len(RUNS), help="walk only the first N runs")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not ART.is_dir():
        sys.exit(f"corpus not found: {ART}")

    runs = RUNS[:a.runs]
    cleared_cells, stalled_cells, all_cells = [], [], []
    per_game_cleared, per_game_stalled = [], []
    n_files = n_rows = 0
    c2_sys = c2_own = 0

    for run in runs:
        for p in sorted((ART / run / "artifacts").glob("*_events.jsonl")):
            n_files += 1
            cleared, cells = walk_game(p)
            n_rows += len(cells)
            (cleared_cells if cleared else stalled_cells).extend(cells)
            all_cells.extend(cells)
            g = rates(cells)
            row = [q["rate"] for q in g] + [trend(g)]
            (per_game_cleared if cleared else per_game_stalled).append(row)
            if n_files <= 25:                       # C2 sampled over one run's worth
                for ln in p.open():
                    r = json.loads(ln)
                    if r.get("type") != "analysis":
                        continue
                    pr = own_prose(r.get("transcript") or "")
                    c2_sys += pr.count(SYS_ONLY)
                    c2_own += len(re.findall(VERB, pr, re.I))
                    break

    print(f"C1 corpus            : {n_files} game logs over {len(runs)} runs, "
          f"{n_rows} analysis rows")
    assert n_files == 25 * len(runs), f"C1 FAIL: walked {n_files} logs, expected {25*len(runs)}"
    # Scaled to what was walked, so --runs N stays gated instead of tripping on the full-corpus
    # figure. One run carries ~975 rows over its 25 games.
    assert n_rows > 500 * len(runs), f"C1 FAIL: only {n_rows} analysis rows over {len(runs)} run(s)"

    print(f"C2 slicing           : system-prompt-only phrase in sliced prose = {c2_sys} "
          f"(must be 0); action verbs in sliced prose = {c2_own} (must be > 0)")
    assert c2_sys == 0, "C2 FAIL: the system prompt survived the slice -- R33's section trap"
    assert c2_own > 0, "C2 FAIL: the slice returned no agent prose, so 0 hits means nothing"

    ra = rates(all_cells)
    print("C3 prose volume      : chars of agent prose per quartile = "
          + ", ".join(f"Q{i+1} {r['chars']:,}" for i, r in enumerate(ra)))
    print("C4 negative control  : neutral-word rate per 1k chars = "
          + ", ".join(f"Q{i+1} {r['neutral']:.1f}" for i, r in enumerate(ra)))
    nt = [r["neutral"] for r in ra]
    spread = (max(nt) - min(nt)) / min(nt)
    assert spread < 0.20, f"C4 FAIL: the neutral word itself trends by {spread:.0%} across quartiles"
    print(f"                       spread {spread:.1%} (must be < 20%)")
    print("C5 positive control  : proven in --selftest (a planted Q1-only marker is reported as decay)")

    print("\n=== mechanic-uncertainty rate per 1,000 chars of the agent's OWN prose")
    for label, cells in (("ALL games", all_cells),
                         ("games that cleared >=1 level", cleared_cells),
                         ("games that cleared nothing", stalled_cells)):
        rs = rates(cells)
        t = trend(rs)
        print(f"\n  {label}  ({len(cells)} analysis rows)")
        print("     " + "  ".join(f"Q{i+1} {r['rate']:.2f}" if r["rate"] is not None else f"Q{i+1} --"
                                  for i, r in enumerate(rs)))
        print(f"     Q1 -> Q4: {t:+.1%}" if t is not None else "     Q1 -> Q4: undefined")

    # A pooled rate over 200 game logs can be carried by a handful of verbose games. The honest
    # unit is the GAME: one number each, then compare the two populations by rank. AUC needs no
    # distributional assumption and 0.5 is exactly "the two populations are interchangeable".
    print("\n=== per-GAME, so a few verbose games cannot carry the result")
    for label, idx in (("Q1 uncertainty rate", 0), ("Q4 uncertainty rate", 3)):
        cl = [g[idx] for g in per_game_cleared if g[idx] is not None]
        st = [g[idx] for g in per_game_stalled if g[idx] is not None]
        a = auc_simple(cl, st)
        med = lambda v: sorted(v)[len(v) // 2]
        print(f"  {label:<22} cleared n={len(cl):3d} median {med(cl):.2f}  |  "
              f"stalled n={len(st):3d} median {med(st):.2f}  |  AUC {a:.3f}"
              if cl and st else f"  {label}: one population empty")
    cl = [g[4] for g in per_game_cleared if g[4] is not None]
    st = [g[4] for g in per_game_stalled if g[4] is not None]
    if cl and st:
        med = lambda v: sorted(v)[len(v) // 2]
        print(f"  {'Q1->Q4 decay':<22} cleared median {med(cl):+.1%}  |  "
              f"stalled median {med(st):+.1%}  |  AUC {auc_simple(cl, st):.3f}")
    # The bar for those AUCs, measured rather than assumed: shuffle which games are "cleared"
    # and see how far AUC wanders on this sample size alone. Same discipline as R45's C5.
    rnd = random.Random(20260827)
    band = 0.0
    for idx in (0, 3, 4):
        vals = [g[idx] for g in per_game_cleared + per_game_stalled if g[idx] is not None]
        k = sum(1 for g in per_game_cleared if g[idx] is not None)
        for _ in range(200):
            v = vals[:]
            rnd.shuffle(v)
            band = max(band, abs(auc_simple(v[:k], v[k:]) - 0.5))
    print(f"\n  Shuffle null on this sample: max |AUC-0.5| over 600 relabellings = {band:.3f}.")
    print("  AUC 0.500 means the two populations are interchangeable on that quantity;")
    print("  anything inside the band above is a number a meaningless split also produces.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
