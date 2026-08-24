# R31 — the transition model is learnable; R29 §9's instrument threw the click away

2026-08-24. Answers **B26**'s sharpened question offline, 0 slots, and **unblocks B29**.
Instrument: `scripts/b27/b26_statekey.py`, five controls gating it, all passing, exit 0.

## The answer

B26, as R29 §9 sharpened it, asks *"is a transition model learnable from what the agent is
shown"*. §9 answered no. **The answer is yes, and §9's no was its own key.**

Given the same level, the same observed board and the same action **as the agent issues and
sees it**, the harness's own `board_changed` flag reproduces:

| population | repeats | board reproduced | flag reproduced | majority-class null |
|---|---|---|---|---|
| all | 324 | 74.1% | **98.1%** | 89.8% |
| keyboard actions | 311 | 74.9% | **100.0%** | 89.7% |
| clicks | 13 | 53.8% | 53.8% | — |

The residual is **6 misses, all clicks, all in one game (`s5i5`)**. Every other game with
more than two repeats reproduces its flag at 100.0%, including `cn04` on 259 of them.

§9's headline was **58.7% board / 77.8% flag**, from which it concluded that *"a verifier
keyed on the rendered board cannot abort on a prediction miss, because the prediction is
wrong ~4 times in 10."* Under the corrected key the prediction is wrong **0.2 times in 10**,
and never once on a keyboard action.

## What one field did

§9 keyed the action on **`action_name`** — `ACTION1`…`ACTION6`, `RESET`. Every mouse click is
`ACTION6` no matter where it landed, and the corpus holds **662 distinct (game, click cell)
pairs**. So a click at `(58,35)` and a click at `(29,22)` fired from the same board were
recorded as the same `(state, action)` and then compared to each other. Of §9's 446 repeats,
**135 were clicks — and 122 of those were different actions wearing one symbol.**

`action_display` carries the cell: `MOUSE(row=58, col=35)`.

**This is not a shrinkage argument, and the bijection is what proves it.** `action_name` and
`action_display` are in bijection for keyboard actions (0 collisions in either direction over
5,664 events), so the swap cannot touch them — and it does not:

```
kbd-only,   name key    repeats=311  board 74.9%  flag 100.0%
kbd-only, display key   repeats=311  board 74.9%  flag 100.0%     <- identical
mouse-only,   name key  repeats=135  board 21.5%  flag  26.7%
mouse-only, display key repeats= 13  board 53.8%  flag  53.8%     <- the fiction drains out
```

§9's per-game table reads the same way once the click column is put beside it. Every game it
reported as failing to reproduce has repeats that are **100% clicks** — `s5i5` 28/28,
`sb26` 26/26, `ft09` 18/18, `dc22` 14/14, `lp85` 12/12, `su15` 12/12, `sc25` 8/8, `vc33` 7/7.
Both games it reported at 100% — `ls20`, `tu93` — have **zero**. `cn04`, which §9 called the
best-behaved and correctly noted was propping the aggregate up, has **1 of 260**.

So §9's "this is a per-game property, not a blanket statement that the environment is random"
was right about the shape and wrong about the property: the per-game variable is not how
deterministic the game is, it is **how much of its play is clicking**.

## The agent was never the one missing the coordinates

The distinction that matters for B26 is whether the confound lives in the offline instrument
or in what the agent is shown. It is the instrument. The agent's own sandbox renders a
transition **with the cell in it** — from a `v10cal`/`sb26` tool result, verbatim:

```
ActionTransitionView(action='MOUSE(row=58, col=35)', before_frame=AsciiFrameView(level=1,
  step=0, shape=64x64), after_frame=AsciiFrameView(level=1, step=1, shape=64x64))
```

and its user turn reads `Executed actions: MOUSE(row=38, col=15).` The agent issues clicks as
`action([{'action': 'MOUSE', 'row': 4, 'col': 7}])` and reads them back the same way. Nothing
about the agent's view has to change for a verifier to key on this.

## Reliable is not the same as available — and this is what still bounds B29

A prediction that holds 98.1% of the time is worth nothing on a decision where no prediction
exists. Measured over the same 7,938 decisions:

- **9.0%** are taken from a board this run had seen before.
- Of those, **91% have exactly one** recorded action from that board (638 of 711); two or
  more is 73 decisions, 0.9% of the run.
- Exact `(level, board, action)` repeats are **324/7,938 = 4.1%**.

Per game the revisit rate is 0.0%–13.8% with one outlier — `cn04` at 47.5% — and five games
(`lf52`, `tn36`, `r11l`, `tr87`, `bp35`) are at 0.0–0.5%.

**This is B19's coverage argument** (*"exact `(state, action)` repeats are 20 of 1,597 = 1.3%
so a learned model has almost no coverage"*), recomputed on the five-run corpus at 4.1%, and
**it is untouched by the key fix.** It was always the stronger of the two objections; §9's
reliability objection was standing in front of it.

## What this changes for B29

B29 is two mechanisms sharing a sentence, and they now separate:

- *"abort on first prediction miss"* — **viable**. The premise §9 refuted holds. Built as
  specified the gate fires on ~2% of correct repeats corpus-wide and 0% on keyboard actions,
  not the ~50% §9 computed. As a **safety brake** it costs almost nothing and is buildable.
- *"draft k candidate short plans, check each against `history`'s recorded transitions,
  execute only the best-verified one"* — **weak, and not for the reason §9 gave**. A verifier
  can speak on 9% of decisions, and on 91% of those it knows one action out of the ~6
  available. Ranking *k candidate plans* needs coverage of a sequence; the single-step rate is
  already the optimistic bound.

So the shape B29 should take is a brake, not a selector. That is a design consequence, not a
measurement, and it is the maintainer's call.

## What is NOT established

- **`cn04` reproduces its flag 100% and its board only 70.7%**, on 259 of the 324 repeats —
  four fifths of the population. The outcome is right and the pixels differ. §9 measured the
  same shape (median 1 cell, mean 24.4, max 320) and declined to name where they sit; nothing
  here improves on that. Any board-exact verifier still has to handle it.
- **`s5i5`'s 6 misses are unexplained.** One game, 7 click repeats, 14.3%. It is the whole
  residual, so it is also the whole remaining case for genuine non-determinism, and n=7.
- **The animation gap survives, smaller**: 72.0% (neither side animated, n=271) against 84.9%
  (both, n=53). §9's 01/10 flip cases, which it reported collapsing to 6.2%/8.3%, do not exist
  under the corrected key — they were clicks.
- **This says nothing about whether the agent's beliefs are right.** It says the ground truth
  a verifier would check them against is stable. R29 §2 — where a goal is stated it is usually
  correct, what is wrong is what the agent believes an action does — is untouched, and remains
  the load-bearing half.
- **324 repeats is a small population and `cn04` is 80% of it.** Excluding `cn04`: 65 repeats,
  board 87.7%, flag 90.8% — the flag drop is entirely `s5i5`'s 6.

## Controls

All five gate the run and it exits 1 before printing any new number if one fails.

1. **Reproduces R29 §9 exactly** — 446 / 58.7% / 77.8% under `action_name`, so the loader is
   theirs and the delta is the key, not the corpus.
2. **`action_name` ↔ `action_display` bijective on keyboard** — 0 collisions both directions,
   so the swap is surgical.
3. **`board_ascii` ↔ the numeric `board` bijective** — 16 colours ↔ 16 characters, 64×64 both,
   6,468 = 6,468 distinct keys, 0 collisions either way. This was the first alternative
   explanation checked and it is dead: §9's key is not lossy, so its number could not have
   come from two different boards colliding.
4. **Positive controls bite** — dropping the ACTION gives 37.1% board / 52.6% flag; dropping
   the BOARD gives 0.6% board. ⚠️ **Dropping `level` is NOT a control**: measured vacuous, it
   scores identically, because the 64×64 board hash already determines the level. A control
   that cannot fail is a constant.
5. **Null baseline** — the majority-class predictor ("always changed") scores 89.8% corpus-wide
   and 89.7% on keyboard. 98.1% and 100.0% are the numbers that had to beat those, and the
   keyboard result is 311/311 against a baseline that misses 32.

## Reproduce

```bash
python3 scripts/b27/b26_statekey.py
```

Reads `~/Claude/arc-artifacts/{v10cal,thuiv1,v18,v19,v23}` through `scripts/b27/corpus.py`,
the same loader R29 used. Zero GPU slots, zero submissions, no model calls.
