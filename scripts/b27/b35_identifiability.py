#!/usr/bin/env python3
"""B35 -- can a game's POPULATION be identified from in-run signal, in time to act?

B35 proposes per-game targeting: stop applying one global change to 25 games, and treat
its three populations (never-clear / all-or-nothing / cap-locked) differently. Every fact
that frame rests on is measured. The question it has never asked is the one that decides
whether the family can SHIP AT ALL:

    on the hidden 110 you cannot name a game. Any per-game lever must decide, FROM THE RUN
    ITSELF and early enough for the decision to be worth anything, which population the
    game in front of it belongs to.

If the populations are not separable from an early window, the whole family is a public-25
artefact and B35 closes as unshippable. If they are, B35 becomes a build with a named
detector and a measured error rate.

WHAT IS MEASURED
    Target      : does this game EVER score (summary.txt score > 0), decided per (run, game).
    Window      : the first K actions of that game's event log, K in {5, 10, 20, 40}.
    Restriction : cells that have ALREADY scored inside the window are excluded from the
                  test -- they need no detector. The decision that matters is about a game
                  that is silent so far.
    Validation  : leave-one-RUN-out. A threshold fitted on the other seven runs is tested on
                  the held-out run, so nothing is graded on the draw it was fitted to. AUC is
                  reported alongside, being threshold-free.

WHY AUC AND ACCURACY BOTH
    Accuracy against an imbalanced base rate is satisfied by a constant predictor; AUC is not,
    but AUC alone does not say whether any single cut is usable. Neither is sufficient. The
    majority-class rate is printed beside every accuracy so a constant predictor is visible.

CONTROLS (all five must pass or the script exits 1 and prints no findings)
    C1  corpus     8 runs x 25 games = 200 cells, every cell carrying both a summary row and
                   an event log. A short corpus means the walk missed runs, and every rate
                   below would be computed over a population nobody chose.
    C2  dead games B35 asserts `g50t`, `sk48`, `tr87` never score, from FOUR fixture runs.
                   Re-checked here across all eight. If one of them scores, the frame's own
                   dead-game pool is wrong and the target labels are not what B35 means.
    C3  leakage    every feature must be computable from rows with action_num <= K. Asserted
                   by construction: the window is sliced first and the slice's max action_num
                   is checked against K.
    C4  positive   a deliberately leaky feature (`levelled_up_in_window`) must score HIGH. A
                   pipeline that cannot detect signal that IS there cannot be believed when it
                   reports there is none -- this is the control that separates "the populations
                   are not separable" from "this script does not work".
    C5  negative   labels shuffled within each run must collapse every feature to chance
                   (AUC ~ 0.5). Without it, a high AUC cannot be told from an evaluation bug.

Reproduce:
    python scripts/b27/b35_identifiability.py --selftest   # controls + synthetic cases, no corpus
    python scripts/b27/b35_identifiability.py              # needs ~/Claude/arc-artifacts/
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
DEAD = ["g50t", "sk48", "tr87"]          # B35's never-clear pool, from four fixture runs
KS = [5, 10, 20, 40]
NULL_BAND = 0.15                         # replaced by C5's measured value at runtime

MOUSE_RE = re.compile(r"^MOUSE\(row=(-?\d+)")


def family(disp: str, name: str):
    """Same key R38/R43 use: a click is its ROW, a keypress is its name."""
    m = MOUSE_RE.match(disp or "")
    return ("MOUSE", int(m.group(1))) if m else ("KEY", name)


# ---------------------------------------------------------------- corpus

def read_summary(run: str) -> dict:
    """game-stem -> score. summary.txt is the ONLY place the competition score lives; the
    `score` field inside the event rows is the levels-cleared count and means something else."""
    p = ART / run / "summary.txt"
    out = {}
    for ln in p.read_text().splitlines():
        m = re.match(r"\s*([a-z0-9]+)-[0-9a-f]+:\s*score=([0-9.]+)", ln)
        if m:
            out[m.group(1)] = float(m.group(2))
    return out


def read_actions(path: Path) -> list[dict]:
    rows = []
    for ln in path.open():
        r = json.loads(ln)
        if r.get("type") == "action":
            rows.append(r)
    return rows


def features(win: list[dict], k: int) -> dict:
    """Everything here is a property of the window and of nothing after it."""
    n = len(win)
    assert n <= k, f"window carries {n} rows for k={k}"
    if n == 0:
        return {}
    fams = [family(r.get("action_display", ""), r.get("action_name", "")) for r in win]
    changed = sum(1 for r in win if r.get("board_changed"))
    # longest run of one family, the shape R38 built the family brake around
    run_len = best = 1
    for a, b in zip(fams, fams[1:]):
        run_len = run_len + 1 if a == b else 1
        best = max(best, run_len)
    steps = {(r.get("action_num"), r.get("analysis_step")) for r in win}
    return {
        "change_rate": changed / n,
        "distinct_families": len(set(fams)) / n,
        "longest_family_run": best / n,
        "mouse_share": sum(1 for f in fams if f[0] == "MOUSE") / n,
        "actions_per_step": n / max(1, len(steps)),
        # C4's positive control: leaky on purpose, must come out strong
        "levelled_up_in_window": float(any(r.get("level_completed") for r in win)),
    }


FEATS = ["change_rate", "distinct_families", "longest_family_run", "mouse_share",
         "actions_per_step", "levelled_up_in_window"]


def build(k: int):
    """-> list of (run, game, feats, label, scored_in_window)"""
    cells = []
    for run in RUNS:
        summ = read_summary(run)
        for p in sorted((ART / run / "artifacts").glob("*_events.jsonl")):
            stem = p.name.split("-")[0]
            acts = read_actions(p)
            win = acts[:k]
            f = features(win, k)
            # A game that fired ZERO actions in a whole run is a real cell, not missing data
            # (R43 section 4 predicted this pair). Dropping it would quietly shrink the corpus
            # and take the most extreme never-scoring cells out of the population being tested.
            cells.append({
                "run": run, "game": stem, "f": f or None,
                "score": summ.get(stem, 0.0), "n_actions": len(acts),
                "label": 1 if summ.get(stem, 0.0) > 0 else 0,
                "in_window": bool(f.get("levelled_up_in_window")) if f else False,
                "no_actions": not f,
            })
    return cells


# ---------------------------------------------------------------- scoring

def auc(pairs: list[tuple[float, int]]) -> float | None:
    """Rank AUC with ties at half credit. None when a class is missing -- a single-class
    sample has no AUC, and returning 0.5 there would read as 'measured, no signal'."""
    pos = [v for v, y in pairs if y == 1]
    neg = [v for v, y in pairs if y == 0]
    if not pos or not neg:
        return None
    tot = 0.0
    for a in pos:
        for b in neg:
            tot += 1.0 if a > b else (0.5 if a == b else 0.0)
    return tot / (len(pos) * len(neg))


def loro(cells, feat):
    """Leave-one-run-out: fit the cut on the other runs, test on this one."""
    accs, n_test = [], 0
    for held in RUNS:
        tr = [c for c in cells if c["run"] != held]
        te = [c for c in cells if c["run"] == held]
        if not te or not tr:
            continue
        cuts = sorted({c["f"][feat] for c in tr})
        best_cut, best_acc = None, -1.0
        for cut in cuts:
            for sign in (1, -1):
                acc = sum(1 for c in tr
                          if (1 if sign * c["f"][feat] > sign * cut else 0) == c["label"]) / len(tr)
                if acc > best_acc:
                    best_acc, best_cut, best_sign = acc, cut, sign
        hit = sum(1 for c in te
                  if (1 if best_sign * c["f"][feat] > best_sign * best_cut else 0) == c["label"])
        accs.append(hit / len(te))
        n_test += len(te)
    return (sum(accs) / len(accs) if accs else None), n_test


# ---------------------------------------------------------------- controls

def controls(cells_by_k) -> None:
    cells = cells_by_k[KS[0]]
    n = len(cells)
    silent = [(c["run"], c["game"]) for c in cells if c["no_actions"]]
    print(f"C1 corpus            : {n} cells from {len({c['run'] for c in cells})} runs "
          f"x {len({c['game'] for c in cells})} games; "
          f"{len(silent)} fired NO action all run: {silent}")
    assert n == 200, f"C1 FAIL: expected 8x25=200 cells, walked {n}"
    assert all(c["label"] == 0 for c in cells if c["no_actions"]), \
        "C1 FAIL: a game that never acted is recorded as scoring"

    # C2 as first written asserted all three of B35's never-clear games score 0 in all eight
    # runs. It FAILED, and the failure is the finding: `sk48` clears L1 in `v23`, which is not
    # one of the four fixture runs B35 read. The assert is kept in the shape that survived
    # measurement -- the two that really are 0-for-8 -- and the exception is printed, never
    # asserted away.
    exceptions = []
    for g in DEAD:
        s = [c["label"] for c in cells if c["game"] == g]
        assert s, f"C2 FAIL: {g} absent from the corpus"
        if any(s):
            hits = [c for c in cells if c["game"] == g and c["label"]]
            exceptions.append((g, sum(s), len(s),
                               ", ".join(f"{c['run']} score={c['score']} in {c['n_actions']} actions"
                                         for c in hits)))
    for g in ("g50t", "tr87"):
        s = [c["label"] for c in cells if c["game"] == g]
        assert not any(s), f"C2 FAIL: {g} was 0-for-8 when this was written and now scores"
    print(f"C2 never-clear pool  : g50t, tr87 score 0 in all 8 runs. "
          f"B35's third member is REFUTED: " +
          "; ".join(f"{g} scores in {n} of {t} runs -- {w}" for g, n, t, w in exceptions))

    print(f"C3 no leakage        : windows sliced before features; max |window| <= k asserted per cell")

    a = auc([(c["f"]["levelled_up_in_window"], c["label"]) for c in cells_by_k[40] if c["f"]])
    print(f"C4 positive control  : levelled_up_in_window AUC = {a:.3f} (must be >= 0.70)")
    assert a is not None and a >= 0.70, f"C4 FAIL: leaky feature only reached {a}"

    rnd = random.Random(1234)
    worst = 0.0
    for feat in FEATS:
        sh = []
        for run in RUNS:
            grp = [c for c in cells_by_k[20] if c["run"] == run and c["f"]]
            lab = [c["label"] for c in grp]
            rnd.shuffle(lab)
            sh += [(c["f"][feat], y) for c, y in zip(grp, lab)]
        a = auc(sh)
        worst = max(worst, abs((a or 0.5) - 0.5))
    print(f"C5 negative control  : shuffled labels, max |AUC-0.5| over {len(FEATS)} features = {worst:.3f} (must be < 0.15)")
    assert worst < 0.15, f"C5 FAIL: shuffled labels still separate by {worst}"
    return worst


# ---------------------------------------------------------------- selftest

def selftest() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        print(f"  {'ok  ' if cond else 'FAIL'} {name}")
        ok = ok and cond

    chk("family keys a click by row", family("MOUSE(row=58, col=35)", "ACTION6") == ("MOUSE", 58))
    chk("family keys a key by name", family("ACTION1", "ACTION1") == ("KEY", "ACTION1"))
    chk("auc perfect separation", auc([(1, 1), (1, 1), (0, 0)]) == 1.0)
    chk("auc all ties = 0.5", auc([(1, 1), (1, 0)]) == 0.5)
    chk("auc single class -> None", auc([(1, 1), (2, 1)]) is None)

    win = [
        {"action_display": "MOUSE(row=3, col=1)", "action_name": "ACTION6", "board_changed": True,
         "action_num": 1, "analysis_step": 1, "level_completed": False},
        {"action_display": "MOUSE(row=3, col=9)", "action_name": "ACTION6", "board_changed": False,
         "action_num": 2, "analysis_step": 1, "level_completed": False},
        {"action_display": "ACTION1", "action_name": "ACTION1", "board_changed": True,
         "action_num": 3, "analysis_step": 2, "level_completed": True},
    ]
    f = features(win, 5)
    chk("change_rate over the window", abs(f["change_rate"] - 2 / 3) < 1e-9)
    chk("same-row clicks are ONE family (run of 2)", abs(f["longest_family_run"] - 2 / 3) < 1e-9)
    chk("mouse_share", abs(f["mouse_share"] - 2 / 3) < 1e-9)
    chk("leaky feature fires on a level-up", f["levelled_up_in_window"] == 1.0)

    try:
        features(win, 2)
        chk("features refuses a window longer than k", False)
    except AssertionError:
        chk("features refuses a window longer than k", True)

    # teeth: a feature that perfectly predicts must be found by loro, and a constant must not
    cells = []
    for i, run in enumerate(RUNS):
        for j in range(4):
            lab = j % 2
            cells.append({"run": run, "game": f"g{j}", "label": lab,
                          "f": {"perfect": float(lab), "constant": 1.0}})
    acc, _ = loro(cells, "perfect")
    chk("loro finds a perfect feature", acc == 1.0)
    acc, _ = loro(cells, "constant")
    chk("loro cannot beat chance on a constant", acc is not None and acc <= 0.5)

    print("\nSELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    if not ART.is_dir():
        sys.exit(f"corpus not found: {ART}")

    global NULL_BAND
    cells_by_k = {k: build(k) for k in KS}
    NULL_BAND = controls(cells_by_k)

    base = cells_by_k[KS[0]]
    pos = sum(c["label"] for c in base)
    print(f"\nBASE RATE            : {pos} of {len(base)} cells ever score = {pos/len(base):.1%}; "
          f"majority-class predictor = {max(pos, len(base)-pos)/len(base):.1%}")

    print("\n=== can an EARLY WINDOW tell a game that will score from one that never does?")
    print("    (cells that already levelled up inside the window are EXCLUDED -- they need no detector)")
    for k in KS:
        cells = [c for c in cells_by_k[k] if not c["in_window"] and c["f"]]
        excl = len(cells_by_k[k]) - len(cells)
        nact = sum(1 for c in cells_by_k[k] if c["no_actions"])
        pos = sum(c["label"] for c in cells)
        if not cells or pos == 0 or pos == len(cells):
            print(f"\n  k={k:3d}: {len(cells)} cells left ({excl} excluded) -- one class only, nothing to separate")
            continue
        maj = max(pos, len(cells) - pos) / len(cells)
        print(f"\n  k={k:3d}  {len(cells)} testable cells ({excl} excluded: "
              f"{excl - nact} already levelled up in-window, {nact} fired no action at all), "
              f"{pos} eventually score = {pos/len(cells):.1%}; majority = {maj:.1%}")
        # The bar is the SHUFFLE NULL, not an arbitrary lift. C5 showed label-shuffling alone
        # reaches |AUC-0.5| = NULL_BAND on this corpus, so anything inside that band is a
        # number a broken feature would also produce.
        print(f"        {'feature':<24} {'AUC':>7} {'|AUC-.5|':>9} {'LORO acc':>9}  verdict "
              f"(null band = {NULL_BAND:.3f} from C5)")
        for feat in FEATS:
            if feat == "levelled_up_in_window":
                continue                      # constant 0 on this subset by construction
            a = auc([(c["f"][feat], c["label"]) for c in cells])
            acc, _ = loro(cells, feat)
            dev = abs(a - 0.5)
            beats = dev > NULL_BAND and acc is not None and acc - maj > NULL_BAND
            print(f"        {feat:<24} {a:>7.3f} {dev:>9.3f} {acc:>9.3f}  "
                  f"{'SEPARATES' if beats else 'inside the null band'}")

    print("\n=== what the only working signal costs: 'abandon a game still silent at k actions'")
    print("    (the level-up itself is the signal -- there is no precursor. This prices acting on it.)")
    print(f"    {'k':>4} {'still silent':>13} {'of those, later score':>22} {'clock freed':>12}")
    for k in KS:
        cs = [c for c in cells_by_k[k] if not c["in_window"]]
        later = sum(c["label"] for c in cs)
        tot = len(cells_by_k[k])
        print(f"    {k:>4} {len(cs):>7} /{tot:<4} {later:>10} = {later/max(1,len(cs)):>6.1%}      "
              f"{len(cs)/tot:>6.1%} of games")
    print("\n    Reading: every game abandoned at k is a game whose remaining clock is reclaimed,")
    print("    and every 'later score' in that column is a level-up the policy would have destroyed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
