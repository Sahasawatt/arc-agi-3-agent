# R45 — per-game targeting cannot ship, because the level-up is the only signal there is

**2026-08-27, offline, 0 slots, 0 GPU.** `scripts/b27/b35_identifiability.py`, five controls,
one of which **failed on first run and the failure is a finding**.

B35 proposes per-game targeting: stop applying one global change to 25 games, and treat its
three populations differently. Every fact that frame rests on has been measured — the totals
(sum 183), the cap-bound share (55%), the variance concentration (six games carry 90.8%). The
question it never asked is the one that decides whether the family can ship at all:

> On the hidden 110 you cannot name a game. Any per-game lever must decide, **from the run
> itself and early enough for the decision to be worth anything**, which population the game in
> front of it belongs to.

Measured across **8 runs × 25 games = 200 cells**. The answer is no, and the shape of the no is
sharper than the no.

## 1. C2 failed, and B35's never-clear pool is two games, not three

B35 and B36 both name **`g50t`, `sk48`, `tr87`** as the games that never score — *"6.6h of every
run returning 0.00"* — derived from **four** fixture runs. Across all eight:

| game | v10cal | v18 | v19 | v23 | thuiv1 | thuiv1-1r2 | clock2x | v25seed |
|---|---|---|---|---|---|---|---|---|
| `g50t` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| **`sk48`** | 0.00 | 0.00 | 0.00 | **2.78** | 0.00 | 0.00 | 0.00 | 0.00 |
| `tr87` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

**`sk48` clears L1 in `v23` — score 2.78, in 20 actions.** `v23` is not one of the four fixture
runs, which is the entire reason nobody saw it. It is not a marathon clear either: 20 actions is
the cheap end of the corpus, so the game is not *hard*, it is *rare*.

This is the universally-quantified-claim failure in its ordinary form. Three games were read off
a four-run sample, the claim was written as a property of the games, and it travelled into two
tickets and the workspace `CLAUDE.md` as a given. **The dead-game pool is `g50t` and `tr87`.**
Anything that prices reallocation off "three games × 7,920 s = 6.6 h" is over by a third.

⚠️ The assert is kept in the shape that survived measurement — `g50t` and `tr87` are 0-for-8 —
and `sk48` is **printed**, not asserted away. A control that is edited until it passes is not a
control.

## 2. Two cells fired no action at all

`thuiv1-1r2/tr87` and `v25seed/ft09` have **zero `action` rows for the whole run**. R43 §4
predicted exactly this pair from the other direction (*"`tr87` and `ft09` each fire zero actions
in 1 of 8 runs"*). They are real cells with label 0, not missing data — the first draft of the
walk dropped them silently and C1 caught the corpus at 198.

## 3. Nothing in an early window predicts whether a game will ever score

Target: does this game ever score (`summary.txt` score > 0). Window: the first *k* actions.
Cells that have **already** levelled up inside the window are excluded — they need no detector.
Validated **leave-one-run-out**, so no threshold is graded on the draw that fitted it.

The bar is the **shuffle null**, not an arbitrary lift: C5 shuffles labels within each run and
reaches |AUC−0.5| = **0.068** on this corpus, so anything inside that band is a number a broken
feature would also produce.

| k | testable cells | later score | majority | best feature by AUC | \|AUC−0.5\| | its LORO acc |
|---|---|---|---|---|---|---|
| 5 | 194 | 63.4% | 63.4% | `mouse_share` 0.663 | 0.163 | 0.619 — **below** majority |
| 10 | 174 | 59.2% | 59.2% | `change_rate` 0.593 | 0.093 | 0.594 — **+0.2 pp** |
| 20 | 138 | 48.6% | 51.4% | `change_rate` 0.582 | 0.082 | 0.588 — +7.4 pp, **the one crossing** |
| 40 | 93 | 23.7% | 76.3% | `distinct_families` 0.329 | 0.171 | 0.777 — **+1.4 pp** |

**One of twenty (5 features × 4 windows) crossed the band, at one k only, and does not hold at
any neighbouring k** — `change_rate` is 0.016 at k=5 and its lift is +0.2 pp at k=10 and inside
the band at k=40. At a bar calibrated on shuffled labels, one crossing in twenty is what chance
produces.

The two features that look strongest **by AUC alone** are the clearest case for why AUC alone
is not enough here: `mouse_share` at k=5 deviates 0.163 and its best single threshold scores
**below** the majority-class predictor, and `distinct_families` at k=40 deviates 0.171 for a lift
of **+1.4 pp** against a 6.8 pp null band. An AUC that no single cut converts into a decision is
not a detector.

Controls: **C4** (a deliberately leaky feature, `levelled_up_in_window`) reaches AUC **0.913**, so
the pipeline finds signal when signal is there. Without it, "no feature separates" would be
indistinguishable from "this script does not work".

## 4. The level-up IS the signal, and here is what acting on it costs

The excluded column is the finding. By **k = 40, 105 of 200 cells have already levelled up
inside the window** — a game announces it is alive by scoring, and there is no precursor.

So the only usable in-run signal is lagging, and the only policy it supports is *abandon a game
that is still silent at k*:

| k | still silent | of those, later score | share of games freed |
|---|---|---|---|
| 5 | 196 / 200 | 123 = **62.8%** | 98.0% |
| 10 | 176 / 200 | 103 = **58.5%** | 88.0% |
| 20 | 140 / 200 | 67 = **47.9%** | 70.0% |
| 40 | 95 / 200 | 22 = **23.2%** | 47.5% |

Every row is a trade with no good side. At the most patient cut measured, abandoning silent games
frees the remaining clock of **47.5%** of games and destroys **22 level-ups** — 23.2% of what it
cuts. And the receiving side is not strong either: **B34 doubled a game's clock for +2 levels
across 25 games at p = 0.2761**, so the clock this policy reclaims goes to games that have already
been measured not to convert it.

Both halves of the reallocation trade now have numbers, and they point the same way.

## 5. What this settles and what it does not

**Settles** — per-game targeting cannot ship *by detection*. The populations B35 names are real
in the artifacts and are not recoverable from behaviour before the outcome arrives, which is the
one thing a hidden-set lever would need.

**Does not settle** — B35's frame is not *wrong*. Six games really do carry 90.8% of the variance
and five really are cap-locked. What is refuted is the route: you cannot get there with an
in-run classifier. A per-game lever keyed on something other than behaviour (a game's own
`levels=<cleared>/<TOTAL>` line, available at runtime) is untouched by this and is a different
proposal.

**Limits, stated rather than discovered later**:

1. **8 runs are 8 draws of the same 25 public games.** Identifiability on the hidden 110 is a
   different population and this cannot speak to it. It can only say the mechanism failed where
   we can look.
2. **Five features, not all features.** A richer detector — the transcript, the board itself —
   is not tested here. What is tested is every cheap behavioural signal the event log carries.
3. **The abandon table is measured on runs where nothing was abandoned.** The 22 late scorers
   scored under a full clock; it does not follow they would have scored under a shortened one,
   and it does not follow they would not.
4. **`sk48`'s single clear is n=1.** It refutes *never*, which is all it is used for here.

## 6. Reproduce

```bash
python scripts/b27/b35_identifiability.py --selftest   # 12 cases, no corpus
python scripts/b27/b35_identifiability.py              # needs ~/Claude/arc-artifacts/
```
