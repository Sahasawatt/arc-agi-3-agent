# v17 "simulate before you act" — killed before it was built

2026-08-22. Design and three offline measurements, no GPU spent.

## The idea

Actions are quadratically expensive and thinking is free, and the model holds a full Python REPL
with `current_frame.grid` in it. The system prompt even recommends the move — *"write a small
scorer or search over candidate sequences, execute"*. So: build a transition model from the
`(state, action, next_state)` triples the harness already records, let the model **search** on it,
and spend actions only on a verified path.

Measured first, because the whole design rests on one assumption nobody had checked: **that a
transition model learned from observed history predicts well enough to plan on.**

## What the model actually does today

Across all 25 games of v10cal, code turns containing any search/simulation construct
(`def solve/search/plan/simulate`, `deque`, `heapq`, `itertools.permutations/product`, `best_score`,
`def step(`, `def apply_`):

```
19 of 935 code turns = 2.0%
even ft09, the corpus best, is 1 of 41
```

The sandbox is used as a microscope, not a solver. That part of the diagnosis stands.

## The three measurements that killed it

Train on the first half of each game's transitions, test on the second, 23 games with ≥12 pairs.

| tier | question | result |
|---|---|---|
| 1 | will this action change the board? | learner **97.0%** vs majority baseline **96.9%** — n=799 |
| 2 | how many cells will change? | **24.6%** exact — n=749 |
| 3 | does the same (board, action) recur, and repeat? | **20 of 1,597 pairs = 1.3%**; of those, same outcome **7**, different **13** |

**Tier 1 is a control failure, not a finding.** The learner adds 0.1 points over "always say yes",
because 97% of actions change the board. Without the baseline in the same run this would have read
as a strong result.

**Tier 3 is what kills the design, and it does so independently of determinism.** The agent is
almost never in a state it has seen before — 1.3% — so a model learned from history has essentially
no coverage at the moment a plan would need it. Whether the remaining 13-of-20 disagreements mean
the environment is stochastic or that the visible grid omits hidden state does not matter: the
observable state does not determine the outcome, and there is not enough repetition to memoise.

**UNVERIFIED / limits.** n=20 for tier 3 is small, and the whole test treats the 64×64 grid as the
state, which is an assumption doing real work — a better state encoding might repeat more often.
The 1.3% coverage figure stands regardless of that assumption; the determinism split does not.

## Where this leaves the delivery question

The three delivery options drafted for v17 (auto-run each turn and push results; force `search()`
before `action()` is accepted; leave it pull-based and nudge when stuck) are all moot — there is
nothing worth delivering. Recorded because the reasoning is reusable:

- **auto-run is structurally broken**: a search needs a GOAL, and the harness does not know the
  goal — discovering it is the model's whole task.
- **forcing it is the v9 shape**: putting a gate on the path the action travels is exactly what
  scored 0.22, and early in a game the transition model is empty so `search()` returns nothing.
- **pull + nudge was the survivor**: the nudge machinery exists (`_animation_hint_line`, firing at
  turns 6/12/18/24) and is provably obeyed — `sk48` was nudged 7 times and called `animation()`
  after every one. That the animation feature did not help is a fact about the feature, not the
  channel.

## Tally for the day

Six directions closed. Two cost a GPU slot each; four cost nothing.

| closed by a run | closed by measurement alone |
|---|---|
| v14 KV fp8 — 2.87 | v15 stop-on-surprise — batch path already guarded, "surprise" undefinable |
| v16 push-the-diff — 3.51 | plateau-stop — actions on uncleared levels enter no denominator |
| | reset-and-retry — `apl` matches raw event counts, RESET refunds nothing |
| | v17 search — this file |
