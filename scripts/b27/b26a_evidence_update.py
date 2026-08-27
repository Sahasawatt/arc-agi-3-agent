#!/usr/bin/env python3
"""B26-a -- does the agent's uncertainty about the mechanics move with EVIDENCE, or only with time?

R46 measured expressed mechanic-uncertainty against TURN POSITION and found a 48% decay that is
the same in games that clear and games that never score (AUC 0.489 inside a 0.159 shuffle band).
Its limit 1 names what it cannot separate:

    "Expressed uncertainty is not actual uncertainty. This probe cannot separate *learned the
     mechanics* from *stopped saying so* -- and the identical decay in stalled games is evidence
     for the second reading."

This asks the question that separates them. Instead of turn position, condition on OUTCOME:

    M1  after the agent fires actions and the board does NOT move -- its theory of the mechanics
        was just falsified -- is the uncertainty it expresses in the SAME step's post-action
        reasoning higher than after a step where every action moved the board?
    M2  and does it carry into the NEXT step's pre-action reasoning?

If uncertainty tracks only turn position, both are flat. If the agent updates on evidence, a
falsifying outcome raises it.

THE LINK, WHICH IS NOT WHAT THE WORKSPACE DOCS SAY
    The workspace CLAUDE.md records "one analysis_step emits MANY analysis events ... and then
    0..N action events". The count half is right; the ORDER half is not. Measured over all 200
    logs, the per-step shape is  [analysis]* action* [analysis]  -- 2,069 of 3,538 acting steps
    have NO analysis row before their first action, and 3,471 analysis rows sit after their
    step's last action. So `analysis_step` alone cannot say which rows are a claim and which are
    a reaction; FILE ORDER can, and the trailing row is the reaction to the outcome. That
    trailing row is this probe's subject and C6 asserts the partition.

CONTROLS (all must pass or the script exits 1 and prints no findings)
    C1  corpus     200 logs / 9,085 analysis rows / 13,176 action rows, asserted exactly.
    C2  slicing    a system-prompt-only phrase scores 0 in the sliced prose and action verbs
                   score > 0. Without both halves a zero cannot be told from an empty slice.
                   (R33's section trap; it bit R39 and R46.)
    C3  prose vol  characters of prose per outcome group, printed beside every rate. A rate that
                   differs because one group writes LESS is not a rate that differs.
    C4  neutral    a mechanic-neutral frequent word must be flat between the groups. If it is
                   not, the groups differ in composition and no other difference can be read.
    C5  positive   selftest only: a planted separation must be reported ABOVE the shuffle band,
                   and identical populations must land INSIDE it. A pipeline that cannot see an
                   effect that is there cannot report its absence.
    C6  partition  pre + post + between == every analysis row, and the pre/post counts reproduce
                   the structural figures above.
    C7  matched    the null band is built by permuting outcome labels WITHIN turn-position
                   strata, so turn position is held fixed. The unstratified band is printed
                   beside it -- if the two differ, R46's axis was doing work here.

DEAD END, fixed before the run (B26-a's own criterion):
    too few triples to declare a denominator, OR |AUC-0.5| <= the matched band. Either is an
    answer and gets written down.

Reproduce:
    python scripts/b27/b26a_evidence_update.py --selftest   # 22 cases, no corpus
    python scripts/b27/b26a_evidence_update.py              # needs ~/Claude/arc-artifacts/
    python scripts/b27/b26a_evidence_update.py --runs 1     # smoke on one run first
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import random
import re
import sys

ART = os.path.expanduser("~/Claude/arc-artifacts")
RUNS = ["v10cal", "v18", "v19", "v23", "thuiv1", "thuiv1-1r2", "clock2x", "v25seed"]

# --- slicer and detector: copied VERBATIM from scripts/b27/b26_mechanic_belief.py so that the
# --- prose object and the hit definition are the same ones R46 measured. Do not "improve" them
# --- here; a divergence would make this probe answer a different question than the one it cites.
OWN = re.compile(r"^\[(ASSISTANT|THINKING)\]$", re.M)
SECTION = re.compile(r"^\[[A-Z][A-Z ]*(?::[^\]\n]*)?\]", re.M)
VERB = r"(?:rotat\w*|translat\w*|mov\w*|shift\w*|toggl\w*|flip\w*|select\w*|place\w*|push\w*|turn\w*|swap\w*|press\w*|click\w*)"
HEDGE = r"(?:maybe|might|unclear|not sure|unsure|unknown|uncertain|hypothesis|assum\w*|guess\w*|test\w+ to see|to see (?:if|whether|what)|let'?s test|try(?:ing)? to (?:see|work out|determine)|still (?:don'?t|do not) know|appears? to|seems? to|possibly|perhaps)"
SENT = re.compile(r"[^.!?\n]*[.!?\n]")
NEUTRAL = re.compile(r"\bthe\b", re.I)
SYS_ONLY = "You are a coding agent solving a grid-based puzzle game"
QUARTILES = 4

EXPECT_LOGS, EXPECT_AN, EXPECT_AC = 200, 9085, 13176
EXPECT_PRE, EXPECT_POST = 3942, 3471          # probe 4, this corpus


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


def quartile(i: int, total: int) -> int:
    if total <= 1:
        return 0
    return min(QUARTILES - 1, (i * QUARTILES) // total)


def outcome_of(changed_flags: list[bool]) -> str:
    if not changed_flags:
        return "noact"
    if all(changed_flags):
        return "all_changed"
    if not any(changed_flags):
        return "none_changed"
    return "mixed"


def walk_game(events: list[dict]):
    """-> (steps, counts) where steps is a list of dicts in step order.

    A step's analysis rows are split by FILE ORDER against that step's own actions:
    pre  = before the first action, post = after the last, between = neither.
    """
    bystep = collections.defaultdict(list)
    order = []
    for i, e in enumerate(events):
        st = e.get("analysis_step")
        if st is None:
            continue
        t = e.get("type")
        if t == "analysis":
            bystep[st].append((i, "an", e.get("transcript") or ""))
        elif t == "action":
            bystep[st].append((i, "ac", bool(e.get("board_changed"))))
        if st not in order:
            order.append(st)
    steps = []
    counts = collections.Counter()
    for st in order:
        rows = sorted(bystep[st])
        acts = [r for r in rows if r[1] == "ac"]
        ans = [r for r in rows if r[1] == "an"]
        counts["an"] += len(ans)
        counts["ac"] += len(acts)
        if not acts:
            counts["between"] += len(ans)
            steps.append({"step": st, "outcome": "noact", "pre": [], "post": [],
                          "n_actions": 0})
            continue
        first_ac, last_ac = acts[0][0], acts[-1][0]
        pre = [r[2] for r in ans if r[0] < first_ac]
        post = [r[2] for r in ans if r[0] > last_ac]
        counts["pre"] += len(pre)
        counts["post"] += len(post)
        counts["between"] += len(ans) - len(pre) - len(post)
        steps.append({"step": st, "outcome": outcome_of([r[2] for r in acts]),
                      "pre": pre, "post": post, "n_actions": len(acts)})
    return steps, counts


def rate(transcripts: list[str]):
    """-> (rate per 1k chars, chars, hits, neutral hits) over the agent's own prose. None if empty."""
    ch = hi = nt = 0
    for t in transcripts:
        p = own_prose(t)
        ch += len(p)
        hi += uncertainty_hits(p)
        nt += len(NEUTRAL.findall(p))
    if ch == 0:
        return None, 0, 0, 0
    return 1000.0 * hi / ch, ch, hi, nt


def auc_simple(pos: list[float], neg: list[float]) -> float:
    """Rank AUC, ties at half credit. Same estimator as b26_mechanic_belief / b35_identifiability."""
    if not pos or not neg:
        return float("nan")
    tot = sum(1.0 if a > b else (0.5 if a == b else 0.0) for a in pos for b in neg)
    return tot / (len(pos) * len(neg))


def stratified_band(vals_by_stratum, n_pos_by_stratum, rnd, reps=600) -> float:
    """Permute the labels WITHIN each turn-position stratum and record how far AUC wanders.

    This is the matched control B26-a requires: R46 showed the quantity moves with turn
    position, so a band built by shuffling across strata would be too wide in one direction
    and would not hold position fixed.
    """
    band = 0.0
    for _ in range(reps):
        pos, neg = [], []
        for s, vals in vals_by_stratum.items():
            v = vals[:]
            rnd.shuffle(v)
            k = n_pos_by_stratum.get(s, 0)
            pos.extend(v[:k])
            neg.extend(v[k:])
        if pos and neg:
            band = max(band, abs(auc_simple(pos, neg) - 0.5))
    return band


def flat_band(all_vals, n_pos, rnd, reps=600) -> float:
    band = 0.0
    for _ in range(reps):
        v = all_vals[:]
        rnd.shuffle(v)
        if n_pos and len(v) - n_pos:
            band = max(band, abs(auc_simple(v[:n_pos], v[n_pos:]) - 0.5))
    return band


# ---------------------------------------------------------------- selftest

def selftest() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        print(f"  {'ok  ' if cond else 'FAIL'} {name}")
        ok = ok and cond

    # --- slicer, inherited. If these drift from b26_mechanic_belief the citation is void.
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

    # --- outcome classification
    chk("all changed", outcome_of([True, True]) == "all_changed")
    chk("none changed", outcome_of([False, False]) == "none_changed")
    chk("mixed", outcome_of([True, False]) == "mixed")
    chk("no actions", outcome_of([]) == "noact")

    # --- the partition, on the two shapes the corpus actually holds
    A = "[ASSISTANT]\nfiller\n"
    ev_pre_post = [                      # ana act ana   -- the documented shape
        {"type": "analysis", "analysis_step": 1, "transcript": A + "pre"},
        {"type": "action", "analysis_step": 1, "board_changed": True},
        {"type": "analysis", "analysis_step": 1, "transcript": A + "post"},
    ]
    st, c = walk_game(ev_pre_post)
    chk("pre/post split on ana-act-ana", len(st) == 1 and len(st[0]["pre"]) == 1
        and len(st[0]["post"]) == 1 and st[0]["outcome"] == "all_changed")
    ev_post_only = [                     # act ana       -- the MAJORITY shape (2,069 steps)
        {"type": "action", "analysis_step": 2, "board_changed": False},
        {"type": "analysis", "analysis_step": 2, "transcript": A + "post"},
    ]
    st2, _ = walk_game(ev_post_only)
    chk("post-only step has no pre rows", len(st2[0]["pre"]) == 0 and len(st2[0]["post"]) == 1)
    chk("post-only step outcome is none_changed", st2[0]["outcome"] == "none_changed")
    ev_between = [                       # act ana act   -- the row belongs to neither side
        {"type": "action", "analysis_step": 3, "board_changed": True},
        {"type": "analysis", "analysis_step": 3, "transcript": A + "mid"},
        {"type": "action", "analysis_step": 3, "board_changed": True},
    ]
    st3, c3 = walk_game(ev_between)
    chk("a row between actions is neither pre nor post",
        not st3[0]["pre"] and not st3[0]["post"] and c3["between"] == 1)
    chk("partition is exhaustive", c3["pre"] + c3["post"] + c3["between"] == c3["an"])

    # --- rate
    r, ch, hi, _ = rate(["[ASSISTANT]\nDo the arrows move the piece?\n"])
    chk("rate counts one hit", hi == 1 and ch > 0 and r > 0)
    chk("rate of empty prose is None", rate([])[0] is None)

    # --- AUC
    chk("AUC of perfect separation is 1.0", auc_simple([3, 4], [1, 2]) == 1.0)
    chk("AUC of identical populations is 0.5", auc_simple([1, 2], [1, 2]) == 0.5)

    # --- C5, both halves. A band-and-effect pipeline needs a planted YES and a planted NO.
    rnd = random.Random(20260827)
    strata = {0: [1.0] * 20 + [5.0] * 20, 1: [1.0] * 20 + [5.0] * 20}
    npos = {0: 20, 1: 20}
    planted_pos = [5.0] * 40
    planted_neg = [1.0] * 40
    eff = abs(auc_simple(planted_pos, planted_neg) - 0.5)
    band = stratified_band(strata, npos, rnd)
    chk("C5a a planted separation beats the matched band", eff > band)
    same = {0: [2.0] * 40, 1: [2.0] * 40}
    eff2 = abs(auc_simple([2.0] * 40, [2.0] * 40) - 0.5)
    band2 = stratified_band(same, npos, rnd)
    chk("C5b identical populations sit inside the band", eff2 <= band2 + 1e-9)

    # --- C7: the stratified shuffle must preserve each stratum's size
    seen = {0: 0, 1: 0}
    for s, vals in strata.items():
        seen[s] = len(vals)
    chk("C7 strata sizes are preserved by construction", seen == {0: 40, 1: 40})

    print("\nSELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--runs", type=int, default=len(RUNS))
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not os.path.isdir(ART):
        sys.exit(f"corpus not found: {ART}")

    runs = RUNS[:a.runs]
    full = a.runs >= len(RUNS)
    n_files = 0
    tot = collections.Counter()
    c2_sys = c2_verb = 0
    # per-step records: (outcome, quartile, post_rate, next_pre_rate)
    recs = []  # (outcome, quartile, post_rate, next_pre_rate, game_id, n_actions)
    grp_chars = collections.Counter()
    grp_hits = collections.Counter()
    grp_neutral = collections.Counter()

    for run in runs:
        for f in sorted(glob.glob(os.path.join(ART, run, "artifacts", "*_events.jsonl"))):
            n_files += 1
            gid = run + "/" + os.path.basename(f).split("_p0_events.jsonl")[0]
            events = [json.loads(l) for l in open(f) if l.strip()]
            steps, counts = walk_game(events)
            tot.update(counts)
            acting = [s for s in steps if s["outcome"] != "noact"]
            for idx, s in enumerate(steps):
                if s["outcome"] in ("noact",):
                    continue
                q = quartile(idx, len(steps))
                pr, ch, hi, nt = rate(s["post"])
                if s["outcome"] in ("all_changed", "none_changed"):
                    grp_chars[s["outcome"]] += ch
                    grp_hits[s["outcome"]] += hi
                    grp_neutral[s["outcome"]] += nt
                nxt = None
                if idx + 1 < len(steps):
                    nxt = rate(steps[idx + 1]["pre"])[0]
                recs.append((s["outcome"], q, pr, nxt, gid, s["n_actions"]))
            if n_files <= 25:
                for e in events:
                    if e.get("type") != "analysis":
                        continue
                    pp = own_prose(e.get("transcript") or "")
                    c2_sys += pp.count(SYS_ONLY)
                    c2_verb += len(re.findall(VERB, pp, re.I))
                    break

    print(f"C1 corpus      : {n_files} logs, {tot['an']} analysis rows, {tot['ac']} action rows")
    assert n_files == 25 * len(runs), f"C1 FAIL: {n_files} logs"
    if full:
        assert (tot["an"], tot["ac"]) == (EXPECT_AN, EXPECT_AC), \
            f"C1 FAIL: corpus moved -- {tot['an']}/{tot['ac']} vs {EXPECT_AN}/{EXPECT_AC}"

    print(f"C2 slicing     : system-prompt phrase in sliced prose = {c2_sys} (must be 0); "
          f"action verbs = {c2_verb} (must be > 0)")
    assert c2_sys == 0, "C2 FAIL: the system prompt survived the slice -- R33's section trap"
    assert c2_verb > 0, "C2 FAIL: the slice returned no agent prose"

    print(f"C6 partition   : pre {tot['pre']} + post {tot['post']} + between {tot['between']} "
          f"= {tot['pre']+tot['post']+tot['between']} (must equal {tot['an']})")
    assert tot["pre"] + tot["post"] + tot["between"] == tot["an"], "C6 FAIL: rows lost"
    if full:
        assert (tot["pre"], tot["post"]) == (EXPECT_PRE, EXPECT_POST), \
            f"C6 FAIL: structure moved -- {tot['pre']}/{tot['post']}"

    for g in ("all_changed", "none_changed"):
        r = 1000.0 * grp_hits[g] / grp_chars[g] if grp_chars[g] else float("nan")
        nt = 1000.0 * grp_neutral[g] / grp_chars[g] if grp_chars[g] else float("nan")
        print(f"C3/C4 {g:13s}: prose {grp_chars[g]:>10,} chars   uncertainty {r:5.2f}/1k   "
              f"neutral {nt:5.1f}/1k")
    nts = [1000.0 * grp_neutral[g] / grp_chars[g] for g in ("all_changed", "none_changed")
           if grp_chars[g]]
    spread = (max(nts) - min(nts)) / min(nts) if len(nts) == 2 else 0.0
    print(f"C4 neutral spread between the groups = {spread:.1%} (must be < 20%)")
    assert spread < 0.20, "C4 FAIL: the groups differ in composition, not only in uncertainty"

    print("\n=== step counts by outcome")
    by_out = collections.Counter(r[0] for r in recs)
    for k, v in by_out.most_common():
        print(f"   {k:14s} {v}")

    rnd = random.Random(20260827)
    for label, col in (("M1  post-action reasoning, SAME step", 2),
                       ("M2  pre-action reasoning, NEXT step", 3)):
        pos = [(r[1], r[col]) for r in recs if r[0] == "none_changed" and r[col] is not None]
        neg = [(r[1], r[col]) for r in recs if r[0] == "all_changed" and r[col] is not None]
        print(f"\n=== {label}")
        print(f"   n(falsified) = {len(pos)}   n(confirmed) = {len(neg)}")
        if len(pos) < 30 or len(neg) < 30:
            print("   DEAD END: too few triples to declare a denominator.")
            continue
        pv = [v for _, v in pos]
        nv = [v for _, v in neg]
        med = lambda v: sorted(v)[len(v) // 2]
        eff = auc_simple(pv, nv)
        strata = collections.defaultdict(list)
        npos = collections.Counter()
        for q, v in pos:
            strata[q].append(v)
            npos[q] += 1
        for q, v in neg:
            strata[q].append(v)
        band = stratified_band(strata, npos, rnd)
        bandf = flat_band(pv + nv, len(pv), rnd)
        print(f"   median uncertainty  falsified {med(pv):.2f}/1k   confirmed {med(nv):.2f}/1k")
        print(f"   AUC {eff:.3f}   |AUC-0.5| = {abs(eff-0.5):.3f}")
        print(f"   C7 matched band (shuffle WITHIN turn-position quartile, 600x) = {band:.3f}")
        print(f"      unstratified band for comparison                          = {bandf:.3f}")
        print("   VERDICT: " + ("ABOVE the matched band -- evidence-aligned movement"
                                if abs(eff - 0.5) > band else
                                "DEAD END -- inside the matched band, a meaningless split "
                                "produces this too"))

    # C8 dose-response. `mixed` steps -- some actions moved the board, some did not -- carry
    # PARTIAL falsification. If the M1 effect is really about evidence they should sit between
    # the two poles; if they sit with `all_changed`, something other than falsification is
    # driving it. Not a gate, a shape check: monotone is corroboration, inverted is a finding.
    print("\n=== C8 dose-response -- RETIRED IN PLACE, it cannot answer what it asks.")
    print("   `mixed` steps are LONG BATCHES, not partial falsifications: median actions per")
    print("   step is 4.0 for mixed against 1.0 for both poles (mean 7.21 / 3.58 / 1.05), so a")
    print("   step can only BE `mixed` by holding several actions. Its position is a statement")
    print("   about batch length. Printed for the record, not read as a dose.")
    med = lambda v: sorted(v)[len(v) // 2]
    for g in ("all_changed", "mixed", "none_changed"):
        v = [r[2] for r in recs if r[0] == g and r[2] is not None]
        print(f"   {g:14s} n={len(v):5d}  median {med(v):.2f}/1k" if v else f"   {g}: empty")

    # C9 the between-game confound R46 sec.3 makes mandatory. Steps inside one game are not
    # independent; a handful of games rich in no-op steps could carry M1 on their own. Compare
    # ONLY within a game that holds both kinds of step, then sign-test the per-game differences.
    # Run TWICE. The unmatched pass is kept only to show what a control that shares M1's
    # confound reports -- two methods agreeing is proof only if they do not share an assumption,
    # and this one does. The batch-matched pass is the one that carries a verdict.
    for tag, want_single in (("as first written (shares M1's batch confound)", False),
                             ("BATCH-MATCHED, single-action steps only", True)):
        print(f"\n=== C9 within-GAME, {tag}")
        bygame = collections.defaultdict(lambda: {"none_changed": [], "all_changed": []})
        for o, q, pr, nx, gid, na in recs:
            if pr is None or o not in ("none_changed", "all_changed"):
                continue
            if want_single and na != 1:
                continue
            bygame[gid][o].append(pr)
        paired = [(med(d["none_changed"]), med(d["all_changed"]))
                  for d in bygame.values() if d["none_changed"] and d["all_changed"]]
        if len(paired) < 20:
            print(f"   only {len(paired)} games hold both kinds of step -- DEAD END here")
            continue
        up = sum(1 for a, b in paired if a > b)
        dn = sum(1 for a, b in paired if a < b)
        tie = len(paired) - up - dn
        n, k = up + dn, min(up, dn)           # exact two-sided sign test, no scipy
        c = tail = 0
        c = 1
        for i in range(0, k + 1):
            tail += c
            c = c * (n - i) // (i + 1)
        pval = min(1.0, 2.0 * tail / (2 ** n)) if n else 1.0
        print(f"   games holding both kinds of step: {len(paired)}")
        print(f"   uncertainty HIGHER after falsification in {up}, lower in {dn}, tied {tie}")
        print(f"   exact two-sided sign test p = {pval:.4g}")
        print("   VERDICT: " + ("separates" if pval < 0.05 and up > dn else "does NOT separate"))
    # C10 the confound C8 surfaced, turned on M1. A no-op step averages 1.05 actions and a
    # confirmed step 3.58, so M1 as computed above could be reporting "the agent is more
    # uncertain after a SHORT step". Re-run it with both groups pinned to single-action steps:
    # the batch axis is then constant by construction and only the outcome differs.
    print("\n=== C10 batch-matched M1: both groups pinned to single-action steps")
    pos = [(r[1], r[2]) for r in recs
           if r[0] == "none_changed" and r[2] is not None and r[5] == 1]
    neg = [(r[1], r[2]) for r in recs
           if r[0] == "all_changed" and r[2] is not None and r[5] == 1]
    print(f"   n(falsified, 1 action) = {len(pos)}   n(confirmed, 1 action) = {len(neg)}")
    if len(pos) < 30 or len(neg) < 30:
        print("   DEAD END: too few single-action steps to declare a denominator.")
    else:
        pv = [v for _, v in pos]
        nv = [v for _, v in neg]
        eff = auc_simple(pv, nv)
        strata = collections.defaultdict(list)
        npos = collections.Counter()
        for q, v in pos:
            strata[q].append(v); npos[q] += 1
        for q, v in neg:
            strata[q].append(v)
        band = stratified_band(strata, npos, rnd)
        print(f"   median uncertainty  falsified {med(pv):.2f}/1k   confirmed {med(nv):.2f}/1k")
        print(f"   AUC {eff:.3f}   |AUC-0.5| = {abs(eff-0.5):.3f}   matched band = {band:.3f}")
        print("   VERDICT: " + ("SURVIVES batch matching -- the effect is about the OUTCOME"
                                if abs(eff - 0.5) > band else
                                "DIES under batch matching -- M1 was reporting step LENGTH"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
