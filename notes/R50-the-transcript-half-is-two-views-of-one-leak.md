# R50 — the transcript separates eventual scorers, under two validations that share one blind spot

**2026-08-27, offline, 0 slots, 0 GPU.** `scripts/b27/b35a_transcript_identifiability.py`, eight
controls, 28 selftest cases, teeth proven by seven mutations. Answers `B35-a`, and the answer is
**no**.

R45 tested five cheap EVENT-LOG features over four early windows and found nothing usable — one of
twenty tests crossed its shuffle-calibrated band, at one k only, which is what chance produces at
that bar. Its limit 2 names what it did not test, rather than assuming it away:

> **Five features, not all features.** A richer detector — the transcript, the board itself — is
> not tested here. What is tested is every cheap behavioural signal the event log carries.

This is that richer detector on the transcript half. Target, windows, exclusion rule and null band
are R45's, unchanged, so the two results are comparable; only the features differ.

**It looked like the first positive of the campaign. It was a leak, and it took a third holdout to
see that.**

## 1. What was measured

| | |
|---|---|
| target | does this game EVER score (`summary.txt` score > 0), per (run, game) |
| window | the **file-order prefix** ending at the K-th action, K ∈ {5, 10, 20, 40} |
| restriction | cells that already levelled up inside the window are excluded — they need no detector |
| features | five, from the agent's OWN prose only: `uncertainty_rate` (R46's detector verbatim), `prose_per_action`, `question_rate`, `type_token_ratio`, `goal_mention_rate` |
| band | **0.043**, from C5's within-run label shuffle |

Corpus: **200 logs, 9,085 analysis rows, 13,176 action rows.** Testable cells after exclusion:
193 / 173 / 137 / 93.

The window is a file-order prefix and **not** an `analysis_step` range, because R49 measured the
per-step shape as `[analysis]* action* [analysis]` — 2,069 of 3,538 acting steps have no analysis
row before their first action. Slicing on `analysis_step` would pull in reasoning written *after*
the window's last action, which can mention the outcome. C3 asserts the prefix.

## 2. The result, and the two readings that were wrong

`uncertainty_rate` lift over the held-out majority predictor:

| k | LORO (hold the RUN out) | LOGO (hold the GAME out) | **BLOCK (hold both out)** |
|---|---|---|---|
| 10 | +0.085 | +0.070 | **+0.075** |
| 20 | +0.057 | +0.051 | **+0.029** |

Under LORO it crosses the band at **k=10 and k=20** — two adjacent windows, which is `B35-a`'s own
pre-fixed criterion. Replaying the whole grid under labels shuffled within each run, 500 times,
one permutation per (run, game) applied to all four windows, **2.8%** of replications satisfy that
criterion. So at that point the result read as a genuine detector at p ≈ 0.03.

Under **BLOCK** it crosses at k=10 only. **The criterion fails, and B35-a is a dead end.**

## 3. Why LORO and LOGO agreeing was worth nothing

The 25 public games repeat across all eight runs, and the label has structure on **both** axes —
`sk48` scores only in `v23`. LORO holds the run out and lets the game stay in training; LOGO holds
the game out and lets the run stay. Each bounds one confound and is blind to the other, so the two
**share an assumption**, and their agreement is one view counted twice.

The corpus says so directly. `prose_per_action` at k=20 lifts **+0.132 under LORO** and
**−0.001 under LOGO** — pure game identification, and LORO cannot see it. That feature is what made
LOGO look like the answer; it is also the proof that a single-axis holdout is not one.

BLOCK trains each cell on the cells whose run **and** game both differ from its own. It is the
holdout that matches what B35 is actually asking: on the hidden 110 the game is one you have never
seen, in a run you have never seen.

## 4. What survives

Nothing, at the criterion. Two features cross at a single window and neither has a neighbour:
`uncertainty_rate` at k=10 (+0.075) and `type_token_ratio` at k=20 (+0.109). R45 refused exactly
this shape and was right to; this note refuses it in code (`adjacent_pass`), not in judgement.

C8's null is **skipped** on this run and says so in the output — the null exists to price a
crossing, there is none to price, and running it would spend ~2 hours (BLOCK is 200 folds per
feature-window). **A control that did not run must never read as a control that passed.**

## 5. Controls

| | |
|---|---|
| C1 | 200 cells asserted exactly |
| C2 | system-prompt phrase scores **0** in the sliced prose, action verbs **333** — the same figure R46 §5 published for its own C2, which is evidence the slicer is literally the same object |
| C3 | the window is a file-order prefix; its action count asserted ≤ k per cell |
| C4 | the leaky `levelled_up_in_window` reaches AUC **0.913** — grades the machinery, not the transcript |
| C5 | shuffled labels reach \|AUC−0.5\| = **0.043**; that value is the band every verdict is read against |
| C6 | median chars of own prose per window: 23,675 / 43,612 / 80,858 / 188,507 — the features are not computed over an empty slice |
| C7 | a crossing must hold at two ADJACENT windows, in code |
| C8 | the criterion's own null, skipped here with the reason printed |

Teeth, each mutation reddening **only** its own cases: `window_prefix` ignoring k · the `SECTION`
regex losing its `:` branch (R46's own defect) · `adjacent_pass` accepting any crossing · AUC
crediting ties · `loro` grading on the training runs · `logo` splitting on the run · **`block`
holding only the game out**.

Two selftest defects were found by their own cases failing on the unmutated file, and both are
worth carrying:

- **`x or default` treats a legitimate `0.0` as missing.** `loro` returns 0.0 for a perfectly
  anti-predictive feature and `auc` returns 0.0 for a perfect inversion; both are measurements.
  Three guards were swallowing them, and the worst read as *"no signal"*.
- **A single threshold EXTRAPOLATES.** The first game-identity fixture was monotone in the label,
  so the held-out game was still placed correctly and LOGO scored 1.000 on it. The fixture had to
  be made non-monotone. The limit that follows is real and is stated in the code: **LOGO refutes
  game-lookup; it does not certify its absence.**

## 6. Limits

1. **8 runs are 8 draws of the same 25 public games.** Identifiability on the hidden 110 is a
   different population; this can only say the mechanism failed where we can look.
2. **Five features, not all features** — R45's own limit, inherited. The BOARD half (`B35-b`) is
   untouched and is now the last offline detection route B35 has.
3. **Expressed prose is not belief**, exactly as in R46 and R49.
4. **The band comes from one shuffle draw per feature**, R45's method, kept for comparability. C8
   is the honest gate and it did not need to run here.

## 7. Reproduce

```bash
python scripts/b27/b35a_transcript_identifiability.py --selftest   # 28 cases, no corpus
python scripts/b27/b35a_transcript_identifiability.py --runs 1     # smoke
python scripts/b27/b35a_transcript_identifiability.py              # needs ~/Claude/arc-artifacts/
```
