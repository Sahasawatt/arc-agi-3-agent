#!/usr/bin/env python3
"""B35-a -- do early TRANSCRIPT features separate eventual scorers from games that never score?

R45 tested five cheap EVENT-LOG features over four early windows and found nothing usable: one
of twenty tests crossed its shuffle-calibrated band, at one k only, which is what chance produces
at that bar. Its limit 2 names what it did not test, and says so rather than assuming it away:

    "Five features, not all features. A richer detector -- the transcript, the board itself --
     is not tested here. What is tested is every cheap behavioural signal the event log carries."

This is that richer detector on the transcript half. Target, windows, exclusion rule, validation
and null band are R45's, unchanged, so the two results are comparable; only the FEATURES differ.

WHAT IS MEASURED
    Target      : does this game EVER score (summary.txt score > 0), per (run, game).
    Window      : the file-order prefix ending at the K-th action, K in {5, 10, 20, 40}. The
                  agent's own prose in that prefix is the feature source.
    Restriction : cells that have ALREADY levelled up inside the window are excluded -- they
                  need no detector.
    Validation  : leave-one-RUN-AND-GAME-out (`block`) is the GATE. LORO and LOGO are printed
                  beside it and neither is read as a verdict.
                  LORO holds out a draw; the 25 public games repeat across all eight runs, so
                  a game the detector has never seen is never tested and a threshold can be
                  reading WHICH GAME this is. On the hidden 110 the games are new -- that is
                  B35's whole premise -- so only LOGO answers the question being asked. This
                  is not hypothetical: `prose_per_action` at k=20 lifts +0.132 under LORO and
                  -0.001 under LOGO, i.e. it was game identification and nothing else.

WHY THE WINDOW IS A FILE-ORDER PREFIX AND NOT AN `analysis_step` RANGE
    R49 measured the per-step shape as `[analysis]* action* [analysis]`: 2,069 of 3,538 acting
    steps have NO analysis row before their first action. So `analysis_step <= s` does not mean
    "before the actions of step s", and slicing on it would pull in reasoning written AFTER the
    window's last action -- reasoning that can mention the outcome. A file-order prefix cannot.
    C3 asserts it.

DEAD END, fixed before the run (B35-a's own criterion, implemented in code below and not left
to prose): leave-one-run-out accuracy must beat the held-out majority predictor by more than the
within-run label-shuffle null AT TWO ADJACENT WINDOWS. A one-window spike is a dead end -- that
is exactly what R45 saw and correctly refused.

CONTROLS (all must pass or the script exits 1 and prints no findings)
    C1  corpus     8 runs x 25 games = 200 cells, asserted exactly.
    C2  slicing    a system-prompt-only phrase scores 0 in the sliced prose and action verbs
                   score > 0. R33's section trap, which bit R39 and R46; without both halves a
                   zero cannot be told from an empty slice.
    C3  leakage    the window is a file-order prefix ending at the K-th action; the prefix's
                   action count is asserted <= K, and no event after the cut is read.
    C4  positive   the leaky `levelled_up_in_window` must reach AUC >= 0.70. This grades the
                   LORO/AUC MACHINERY, not the transcript.
    C5  negative   labels shuffled within each run must collapse every feature to chance; the
                   measured value becomes the band every verdict is read against.
    C6  volume     characters of own prose per window, printed. A rate over near-zero prose is
                   not a rate, and at k=5 the median is ~23k chars, so this is a check not a
                   formality.
    C7  adjacency  a feature is reported as crossing only if it clears the band at two
                   ADJACENT k. Printed either way, so a single-window crossing is visible as
                   the near-miss it is rather than absent.
    C8  the criterion's OWN null, and the gate the verdict actually reads. C5's band comes from
                   ONE shuffle draw per feature -- R45's method, kept for comparability, and too
                   thin to price a rule about two adjacent windows. C8 replays the WHOLE grid
                   under labels shuffled within each run, with one permutation per (run, game)
                   applied to all four windows so adjacency keeps its real dependence structure,
                   and reports how often chance alone satisfies C7. If shuffled labels satisfy
                   it often, a real crossing is not evidence.

Reproduce:
    python scripts/b27/b35a_transcript_identifiability.py --selftest   # no corpus
    python scripts/b27/b35a_transcript_identifiability.py              # ~/Claude/arc-artifacts/
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import re
import sys

ART = os.path.expanduser("~/Claude/arc-artifacts")
RUNS = ["v10cal", "v18", "v19", "v23", "thuiv1", "thuiv1-1r2", "clock2x", "v25seed"]
KS = [5, 10, 20, 40]

# --- slicer + mechanic-uncertainty detector: copied VERBATIM from b26_mechanic_belief.py, so
# --- `uncertainty_rate` here is the same quantity R46 and R49 measured, not a lookalike.
OWN = re.compile(r"^\[(ASSISTANT|THINKING)\]$", re.M)
SECTION = re.compile(r"^\[[A-Z][A-Z ]*(?::[^\]\n]*)?\]", re.M)
VERB = r"(?:rotat\w*|translat\w*|mov\w*|shift\w*|toggl\w*|flip\w*|select\w*|place\w*|push\w*|turn\w*|swap\w*|press\w*|click\w*)"
HEDGE = r"(?:maybe|might|unclear|not sure|unsure|unknown|uncertain|hypothesis|assum\w*|guess\w*|test\w+ to see|to see (?:if|whether|what)|let'?s test|try(?:ing)? to (?:see|work out|determine)|still (?:don'?t|do not) know|appears? to|seems? to|possibly|perhaps)"
SENT = re.compile(r"[^.!?\n]*[.!?\n]")
SYS_ONLY = "You are a coding agent solving a grid-based puzzle game"

WORD = re.compile(r"[a-z]{2,}")
GOAL = re.compile(r"\b(goal|target|objective|win condition|to win|solve the level|complete the level)\b", re.I)

FEATS = ["uncertainty_rate", "prose_per_action", "question_rate",
         "type_token_ratio", "goal_mention_rate"]
LEAKY = "levelled_up_in_window"


def own_prose(transcript: str) -> str:
    out = []
    for m in OWN.finditer(transcript):
        start = m.end()
        nxt = SECTION.search(transcript, start)
        out.append(transcript[start:nxt.start() if nxt else len(transcript)])
    return "\n".join(out)


def uncertainty_hits(prose: str) -> int:
    n = 0
    for s in SENT.findall(prose):
        if not re.search(VERB, s, re.I):
            continue
        if "?" in s or re.search(HEDGE, s, re.I):
            n += 1
    return n


def window_prefix(events: list[dict], k: int) -> tuple[list[dict], int]:
    """The file-order prefix ending at the K-th action. -> (prefix, n_actions_in_prefix).

    Strictly causal by construction: nothing after the K-th action is in the slice, so no
    feature computed from it can see an outcome the detector would not have at decision time.
    """
    n = 0
    for i, e in enumerate(events):
        if e.get("type") == "action":
            n += 1
            if n == k:
                return events[:i + 1], n
    return events, n


def features(prefix: list[dict], n_actions: int) -> dict | None:
    """Everything here is a property of the agent's own prose inside the prefix."""
    prose = "\n".join(own_prose(e.get("transcript") or "")
                      for e in prefix if e.get("type") == "analysis")
    ch = len(prose)
    if ch == 0 or n_actions == 0:
        return None
    words = WORD.findall(prose.lower())
    return {
        "uncertainty_rate": 1000.0 * uncertainty_hits(prose) / ch,
        "prose_per_action": ch / n_actions,
        "question_rate": 1000.0 * prose.count("?") / ch,
        "type_token_ratio": (len(set(words)) / len(words)) if words else 0.0,
        "goal_mention_rate": 1000.0 * len(GOAL.findall(prose)) / ch,
        LEAKY: float(any(e.get("level_completed") for e in prefix
                         if e.get("type") == "action")),
        "_chars": float(ch),
    }


def read_summary(run: str) -> dict:
    """summary.txt is the ONLY place the competition score lives; the `score` field inside the
    event rows is the levels-cleared count and means something else (workspace CLAUDE.md)."""
    out = {}
    p = os.path.join(ART, run, "summary.txt")
    for ln in open(p):
        m = re.match(r"\s*([a-z0-9]+)-[0-9a-f]+:\s*score=([0-9.]+)", ln)
        if m:
            out[m.group(1)] = float(m.group(2))
    return out


def build(k: int):
    cells = []
    for run in RUNS:
        summ = read_summary(run)
        for p in sorted(glob.glob(os.path.join(ART, run, "artifacts", "*_events.jsonl"))):
            stem = os.path.basename(p).split("-")[0]
            events = [json.loads(l) for l in open(p) if l.strip()]
            prefix, nact = window_prefix(events, k)
            assert nact <= k, f"C3 FAIL: prefix carries {nact} actions for k={k}"
            f = features(prefix, nact)
            cells.append({
                "run": run, "game": stem, "f": f,
                "score": summ.get(stem, 0.0),
                "label": 1 if summ.get(stem, 0.0) > 0 else 0,
                "in_window": bool(f[LEAKY]) if f else False,
                "no_prose": f is None,
            })
    return cells


def auc(pairs):
    """Rank AUC, ties at half credit. None when a class is missing -- a single-class sample has
    no AUC, and returning 0.5 there would read as 'measured, no signal'."""
    pos = [v for v, y in pairs if y == 1]
    neg = [v for v, y in pairs if y == 0]
    if not pos or not neg:
        return None
    tot = sum(1.0 if a > b else (0.5 if a == b else 0.0) for a in pos for b in neg)
    return tot / (len(pos) * len(neg))


def _folds(cells, feat, key):
    """Fit the single best cut+sign on everything outside one group, test on that group."""
    accs = []
    for held in sorted({c[key] for c in cells}):
        tr = [c for c in cells if c[key] != held]
        te = [c for c in cells if c[key] == held]
        if not te or not tr:
            continue
        best_acc, best_cut, best_sign = -1.0, None, 1
        for cut in sorted({c["f"][feat] for c in tr}):
            for sign in (1, -1):
                acc = sum(1 for c in tr
                          if (1 if sign * c["f"][feat] > sign * cut else 0) == c["label"]) / len(tr)
                if acc > best_acc:
                    best_acc, best_cut, best_sign = acc, cut, sign
        hit = sum(1 for c in te
                  if (1 if best_sign * c["f"][feat] > best_sign * best_cut else 0) == c["label"])
        accs.append(hit / len(te))
    return (sum(accs) / len(accs)) if accs else None


def loro(cells, feat):
    """Leave-one-RUN-out. Printed for comparability with R45; NOT the gate."""
    return _folds(cells, feat, "run")


def logo(cells, feat):
    """Leave-one-GAME-out. The held-out game appears in no training fold."""
    return _folds(cells, feat, "game")


def block(cells, feat):
    """Leave-one-RUN-AND-one-GAME-out. THE GATE.

    LORO holds the run out, LOGO holds the game out, and the label has structure on BOTH axes
    (`sk48` scores only in `v23`), so neither alone bounds the confound. Here the training set
    for a cell excludes every cell of that cell's run AND every cell of its game, so the fitted
    cut has seen neither. Two validations agreeing is proof only when they do not share an
    assumption; these two do, and this is what separates them.
    """
    accs = []
    for c0 in cells:
        tr = [c for c in cells if c["run"] != c0["run"] and c["game"] != c0["game"]]
        if not tr or len({c["label"] for c in tr}) < 2:
            continue
        best_acc, best_cut, best_sign = -1.0, None, 1
        for cut in sorted({c["f"][feat] for c in tr}):
            for sg in (1, -1):
                a = sum(1 for c in tr
                        if (1 if sg*c["f"][feat] > sg*cut else 0) == c["label"]) / len(tr)
                if a > best_acc:
                    best_acc, best_cut, best_sign = a, cut, sg
        accs.append(1.0 if (1 if best_sign*c0["f"][feat] > best_sign*best_cut else 0)
                    == c0["label"] else 0.0)
    return (sum(accs) / len(accs)) if accs else None


# ---------------------------------------------------------------- selftest

def selftest() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        print(f"  {'ok  ' if cond else 'FAIL'} {name}")
        ok = ok and cond

    tr = ("[SYSTEM PROMPT]\nYou are a coding agent solving a grid-based puzzle game.\n"
          "[THINKING]\nDo the arrows move the piece?\n"
          "[ASSISTANT]\nThe goal is the red square.\n"
          "[TOOL RESULT: python]\nmaybe rotate? unclear\n")
    p = own_prose(tr)
    chk("slice drops the SYSTEM PROMPT", SYS_ONLY not in p)
    chk("slice drops TOOL RESULT", "unclear" not in p)
    chk("slice keeps THINKING", "Do the arrows move" in p)
    chk("slice keeps ASSISTANT", "red square" in p)
    chk("uncertainty detector unchanged from R46",
        uncertainty_hits("Do the arrows move the piece?") == 1
        and uncertainty_hits("Maybe the answer is in the corner.") == 0)

    # window is a FILE-ORDER prefix ending at the K-th action
    ev = [{"type": "analysis", "transcript": "[ASSISTANT]\na\n"},
          {"type": "action", "level_completed": False},
          {"type": "analysis", "transcript": "[ASSISTANT]\nb\n"},
          {"type": "action", "level_completed": True},
          {"type": "analysis", "transcript": "[ASSISTANT]\nAFTER\n"},
          {"type": "action", "level_completed": False}]
    pre, n = window_prefix(ev, 2)
    chk("prefix stops at the K-th action", n == 2 and len(pre) == 4)
    txt = "".join(e.get("transcript", "") for e in pre)
    chk("C3 nothing after the cut is in the slice", "AFTER" not in txt)
    pre1, n1 = window_prefix(ev, 99)
    chk("a short game yields its whole log", n1 == 3 and len(pre1) == len(ev))
    f = features(pre, n)
    chk("leaky feature fires on an in-window level-up", f[LEAKY] == 1.0)
    f0 = features(*window_prefix(ev, 1))
    chk("leaky feature is 0 before the level-up", f0[LEAKY] == 0.0)
    chk("no prose -> None", features([{"type": "action"}], 1) is None)
    chk("zero actions -> None",
        features([{"type": "analysis", "transcript": "[ASSISTANT]\nx\n"}], 0) is None)

    g = features(*window_prefix(
        [{"type": "analysis", "transcript": "[ASSISTANT]\nThe goal is here. Is it? yes\n"},
         {"type": "action", "level_completed": False}], 1))
    chk("goal mention counted", g["goal_mention_rate"] > 0)
    chk("question rate counted", g["question_rate"] > 0)
    chk("type_token_ratio in (0,1]", 0 < g["type_token_ratio"] <= 1)

    chk("auc perfect separation", auc([(1, 1), (1, 1), (0, 0)]) == 1.0)
    chk("auc all ties = 0.5", auc([(1, 1), (1, 0)]) == 0.5)
    chk("auc single class -> None", auc([(1, 1), (2, 1)]) is None)

    cells = []
    for run in RUNS:
        for j in range(4):
            lab = j % 2
            cells.append({"run": run, "game": f"g{j}", "label": lab,
                          "f": {"perfect": float(lab), "constant": 1.0}})
    chk("loro finds a perfect feature", loro(cells, "perfect") == 1.0)
    _c = loro(cells, "constant")
    chk("loro cannot beat chance on a constant", _c is not None and _c <= 0.5)

    # The case that proves loro grades the HELD-OUT run. Without it, replacing the test set
    # with the training set is INVISIBLE -- measured: the `perfect`/`constant` pair above gives
    # the identical answer either way, so it cannot see the one property that makes this
    # validation worth anything. Here the feature is perfectly predictive INSIDE each run and
    # its sign flips between runs, so a cut fitted on the others is exactly wrong on the one
    # held out: LORO scores 0.000, grading on the training runs scores 0.571.
    runsign = []
    for i, run in enumerate(RUNS):
        for j in range(4):
            lab = j % 2
            runsign.append({"run": run, "game": f"g{j}", "label": lab,
                            "f": {"runsign": float(lab if i % 2 == 0 else 1 - lab)}})
    _r = loro(runsign, "runsign")
    chk("loro grades the HELD-OUT run, not the training runs",
        _r is not None and _r <= 0.10)

    # logo must hold the GAME out, not the run. Four games, features 1..4, labels 1,0,0,1 --
    # NON-MONOTONE on purpose, and that is the whole trick: a game's label cannot be guessed
    # from where its value sits, so a fold that has never seen the game cannot place it. LORO
    # scores 0.750 (every training fold contains the held-out game) and LOGO 0.250.
    # ⚠️ The limit this fixture also demonstrates: a game-identity feature that IS monotone in
    # the label extrapolates, LOGO scores 1.000 on it, and LOGO cannot see it. So LOGO refutes
    # game-lookup; it does not certify its absence.
    gid = []
    for run in RUNS:
        for j, lab in enumerate([1, 0, 0, 1]):
            gid.append({"run": run, "game": f"g{j}", "label": lab,
                        "f": {"gameonly": float(j + 1)}})
    _lr, _lg = loro(gid, "gameonly"), logo(gid, "gameonly")
    chk("loro keeps a game-identity feature alive (0.750)", _lr == 0.75)
    chk("logo holds the GAME out, so the same feature collapses",
        _lg is not None and _lg <= 0.30)
    # `block` must collapse on BOTH fixtures -- it subsumes each single-axis holdout.
    # ⚠️ These toy fixtures cannot show the case that matters, where LORO and LOGO BOTH pass and
    # block does not: that needs signal present only when a cell's own run AND its own game are
    # in training, which a single threshold over four values cannot express. The real corpus
    # supplies it (`uncertainty_rate` at k=20: LORO +0.057, LOGO +0.051, block +0.029), and that
    # is the whole reason this gate exists rather than either single-axis one.
    _bl_g = block(gid, "gameonly")
    chk("block holds the GAME out (collapses a game-identity feature)",
        _bl_g is not None and _bl_g <= 0.30)
    _bl_r = block(runsign, "runsign")
    chk("block holds the RUN out (collapses a run-specific feature)",
        _bl_r is not None and _bl_r <= 0.10)

    # C7 the dead-end criterion itself, as code
    chk("C7 two adjacent crossings separate",
        adjacent_pass({5: True, 10: True, 20: False, 40: False}, KS))
    chk("C7 a one-window spike does NOT",
        not adjacent_pass({5: False, 10: True, 20: False, 40: False}, KS))
    chk("C7 two NON-adjacent crossings do NOT",
        not adjacent_pass({5: True, 10: False, 20: True, 40: False}, KS))

    print("\nSELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def adjacent_pass(flags: dict, ks: list) -> bool:
    """B35-a's dead-end criterion: crossings at two ADJACENT windows, nothing less."""
    return any(flags.get(a) and flags.get(b) for a, b in zip(ks, ks[1:]))


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--reps", type=int, default=500,
                    help="C8 replications; leave-one-game-out makes each one ~1.7s")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not os.path.isdir(ART):
        sys.exit(f"corpus not found: {ART}")

    by_k = {k: build(k) for k in KS}
    base = by_k[KS[0]]
    print(f"C1 corpus            : {len(base)} cells from {len({c['run'] for c in base})} runs "
          f"x {len({c['game'] for c in base})} games; "
          f"{sum(1 for c in base if c['no_prose'])} with no agent prose in the k=5 window")
    assert len(base) == 200, f"C1 FAIL: walked {len(base)} cells"

    c2_sys = c2_verb = 0
    for run in RUNS[:1]:
        for p in sorted(glob.glob(os.path.join(ART, run, "artifacts", "*_events.jsonl"))):
            for ln in open(p):
                e = json.loads(ln)
                if e.get("type") != "analysis":
                    continue
                pr = own_prose(e.get("transcript") or "")
                c2_sys += pr.count(SYS_ONLY)
                c2_verb += len(re.findall(VERB, pr, re.I))
                break
    print(f"C2 slicing           : system-prompt phrase in sliced prose = {c2_sys} (must be 0); "
          f"action verbs = {c2_verb} (must be > 0)")
    assert c2_sys == 0, "C2 FAIL: the system prompt survived the slice -- R33's section trap"
    assert c2_verb > 0, "C2 FAIL: the slice returned no agent prose"
    print("C3 no leakage        : window is a file-order prefix ending at the K-th action; "
          "prefix action count asserted <= k per cell")

    a4 = auc([(c["f"][LEAKY], c["label"]) for c in by_k[40] if c["f"]])
    print(f"C4 positive control  : {LEAKY} AUC = {a4:.3f} (must be >= 0.70) "
          f"-- grades the MACHINERY, not the transcript")
    assert a4 is not None and a4 >= 0.70, f"C4 FAIL: leaky feature only reached {a4}"

    rnd = random.Random(1234)
    band = 0.0
    for feat in FEATS:
        sh = []
        for run in RUNS:
            grp = [c for c in by_k[20] if c["run"] == run and c["f"]]
            lab = [c["label"] for c in grp]
            rnd.shuffle(lab)
            sh += [(c["f"][feat], y) for c, y in zip(grp, lab)]
        _a = auc(sh)
        assert _a is not None, "C5 FAIL: a shuffled fold had one class only"
        band = max(band, abs(_a - 0.5))
    print(f"C5 negative control  : shuffled labels, max |AUC-0.5| over {len(FEATS)} features "
          f"= {band:.3f} (must be < 0.15) -- this IS the bar below")
    assert band < 0.15, f"C5 FAIL: shuffled labels still separate by {band}"

    print("C6 prose volume      : median chars of own prose per window = " + ", ".join(
        f"k={k} {sorted(c['f']['_chars'] for c in by_k[k] if c['f'])[len([1 for c in by_k[k] if c['f']])//2]:,.0f}"
        for k in KS))

    pos = sum(c["label"] for c in base)
    print(f"\nBASE RATE            : {pos} of {len(base)} cells ever score = {pos/len(base):.1%}; "
          f"majority-class predictor = {max(pos, len(base)-pos)/len(base):.1%}")

    print("\n=== do early TRANSCRIPT features separate eventual scorers from never-scorers?")
    print("    (cells that already levelled up inside the window are EXCLUDED -- they need no detector)")
    crossings = {f: {} for f in FEATS}
    for k in KS:
        cells = [c for c in by_k[k] if not c["in_window"] and c["f"]]
        excl = len(by_k[k]) - len(cells)
        p = sum(c["label"] for c in cells)
        if not cells or p == 0 or p == len(cells):
            print(f"\n  k={k:3d}: {len(cells)} cells ({excl} excluded) -- one class only, nothing to separate")
            for f in FEATS:
                crossings[f][k] = False
            continue
        maj = max(p, len(cells) - p) / len(cells)
        print(f"\n  k={k:3d}  {len(cells)} testable cells ({excl} excluded), "
              f"{p} eventually score = {p/len(cells):.1%}; majority = {maj:.1%}")
        print(f"        {'feature':<22} {'AUC':>7} {'LORO':>6} {'lift':>7} {'LOGO':>6} "
              f"{'lift':>7} {'BLOCK':>6} {'lift':>7}  verdict (gate = BLOCK, band = {band:.3f})")
        for feat in FEATS:
            av = auc([(c["f"][feat], c["label"]) for c in cells])
            a_run = loro(cells, feat)
            a_game = logo(cells, feat)
            a_blk = block(cells, feat)
            dev = abs(av - 0.5)
            l_run = (a_run - maj) if a_run is not None else float("nan")
            l_game = (a_game - maj) if a_game is not None else float("nan")
            l_blk = (a_blk - maj) if a_blk is not None else float("nan")
            crossed = (dev > band) and (a_blk is not None and l_blk > band)
            crossings[feat][k] = crossed
            print(f"        {feat:<22} {av:>7.3f} {a_run:>6.3f} {l_run:>+7.3f} "
                  f"{a_game:>6.3f} {l_game:>+7.3f} {a_blk:>6.3f} {l_blk:>+7.3f}  "
                  f"{'crosses' if crossed else 'inside the band'}")

    print("\n=== C7 a crossing must hold at TWO ADJACENT windows")
    print("    (R45 saw one crossing in twenty at one k and correctly refused it; this is that")
    print("     refusal written as code rather than as a judgement call)")
    observed = {}
    for feat in FEATS:
        ks_hit = [k for k in KS if crossings[feat].get(k)]
        observed[feat] = adjacent_pass(crossings[feat], KS)
        print(f"    {feat:<22} crosses at {str(ks_hit) if ks_hit else '[]':<18} "
              f"{'two adjacent' if observed[feat] else 'no'}")
    any_obs = any(observed.values())

    # C8 -- the criterion's own null. Everything above is read against C5's band, which is one
    # shuffle draw per feature. That is R45's method and it prices a SINGLE crossing; it says
    # nothing about how often chance produces TWO ADJACENT ones, which is what C7 asks. So
    # replay the whole grid under shuffled labels and count.
    if not any_obs:
        # Nothing crossed at two adjacent windows, so there is nothing for a null to reject.
        # C8 exists to price an observed crossing; running it here would spend ~2 hours (the
        # block holdout is 200 folds per feature-window, ~8x leave-one-game-out) to answer a
        # question nobody asked. Skipped, and SAID so -- a control that did not run must never
        # read as a control that passed.
        print("\n=== C8 the criterion's own null: SKIPPED, nothing crossed at two adjacent")
        print("    windows. The null prices a crossing; there is none to price. This is a skip,")
        print("    not a pass.")
        print("\nVERDICT: DEAD END -- no transcript feature clears the band at two adjacent")
        print("         windows under the run-AND-game holdout.")
        return 0

    reps = a.reps
    print(f"\n=== C8 the criterion's own null: {reps} replications with labels shuffled "
          f"within each run")
    print("    (one permutation per (run, game), applied to ALL FOUR windows, so a shuffled")
    print("     replication has the same cross-window dependence the real data does)")
    truth = {(c["run"], c["game"]): c["label"] for c in base}
    rnd2 = random.Random(20260827)
    hits_any = 0
    hits_feat = {f: 0 for f in FEATS}
    for _ in range(reps):
        perm = {}
        for run in RUNS:
            games = sorted({g for (r, g) in truth if r == run})
            labs = [truth[(run, g)] for g in games]
            rnd2.shuffle(labs)
            perm.update({(run, g): y for g, y in zip(games, labs)})
        cr = {f: {} for f in FEATS}
        for k in KS:
            cs = [c for c in by_k[k] if not c["in_window"] and c["f"]]
            lab = [perm[(c["run"], c["game"])] for c in cs]
            pp = sum(lab)
            if not cs or pp == 0 or pp == len(cs):
                for f in FEATS:
                    cr[f][k] = False
                continue
            mj = max(pp, len(cs) - pp) / len(cs)
            shadow = [{**c, "label": y} for c, y in zip(cs, lab)]
            for f in FEATS:
                av = auc([(c["f"][f], c["label"]) for c in shadow])
                ac = block(shadow, f)         # the same gate the observed grid is read against
                cr[f][k] = (av is not None and abs(av - 0.5) > band
                            and ac is not None and ac - mj > band)
        for f in FEATS:
            if adjacent_pass(cr[f], KS):
                hits_feat[f] += 1
        if any(adjacent_pass(cr[f], KS) for f in FEATS):
            hits_any += 1
    print(f"    ANY feature satisfies C7 under shuffled labels: {hits_any}/{reps} "
          f"= {hits_any/reps:.1%}")
    for f in FEATS:
        print(f"      {f:<22} {hits_feat[f]:>4}/{reps} = {hits_feat[f]/reps:>6.1%}")

    p_any = hits_any / reps
    print("\nVERDICT: ", end="")
    if not any_obs:
        print("DEAD END -- no transcript feature clears the band at two adjacent windows.")
    elif p_any >= 0.05:
        print(f"DEAD END -- a feature does cross at two adjacent windows, but shuffled labels\n"
              f"         satisfy the same criterion {p_any:.1%} of the time, so the crossing is\n"
              f"         what chance produces at this bar. Same shape as R45's one-in-twenty.")
    else:
        print(f"SEPARATES -- and shuffled labels reach the same criterion only {p_any:.1%} of\n"
              f"         the time, so it is not what chance produces at this bar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
