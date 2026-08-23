# The bottleneck was the harness, and someone already wrote the layer

2026-08-22. Triggered by the user's read: *"ปัญหาน่าจะคือ harness เราเพราะ model notebook
ตันเหมือนกับคนอื่น"*. It is correct, and the evidence is stronger than the guess.

## Where we actually stand

Downloaded the full public leaderboard (2,476 teams, 2026-08-22 23:39 UTC).

- We are **`Thuitanium`, rank 212, score 1.70, 9 submissions**.
- **Six other teams hold exactly 1.70.** The earliest, `yuki16`, got there on **2026-08-17**
  — four days before us, while we spent 17 runs and closed seven directions.
- The top of the board: `cstl` **3.57**, **Tufa Labs — the authors of the harness we run —
  3.04**, then a dense cluster of 11 teams between **2.43 and 2.76**.
- **`wking edewd` scored 2.70 with THREE submissions.** `rellik13` scored 2.53 with nine,
  the same number we used. Effort is not the variable.

⚠️ A statistical test of whether the repeated scores exceed chance was run and **does not
support a conclusion**: the null model was uniform over the value grid observed (circular),
and its two readings disagree — max multiplicity 17 beats the 95th percentile of 13, while
the count of values shared by 5+ teams (65) is *below* the null median (70). Nothing above
depends on it.

## What the teams above us are running

`thtennant/taaf-kaggle-source-share-fork` — **1,275 downloads**, the most-used fork on the
board. It is built on the same June-era bundle we have at `duck/bundle` (`aa69123`), and
against that base it changes **zero bytes**. What it adds is a new package:

```
src/taaf-grafts/taaf_grafts/   18 modules, 6,524 lines
```

| module | lines | what it does |
|---|---|---|
| `recovery.py` | 810 | un-sticks a stalled session (death spiral, lock-in, level wall) |
| `agent_ext.py` | 568 | ToolAgent subclass that surfaces wasted actions |
| `clickmap.py` | 517 | tells the agent *what it clicked on*, not just that it clicked |
| `goalkeep.py` | 508 | stops the harness erasing what the agent worked out |
| `hudmask.py` | 474 | segments the status band out of `board_changed` |
| `schema_helpers.py` | 469 | preloaded grid-analysis helpers in the sandbox |
| `transfer_solver.py` | 435 | cross-clone replay + scout scheduler |
| `searchmap.py` | 421 | goal inference from the STRUCTURE of the action space |
| `composite.py` | 415 | the single cell-12 entry point, all flags default OFF |
| `family_store.py` | 354 | process-global cross-clone store |
| `banking_solver.py` | 329 | win-then-replay banking |
| `schema_void.py` | 325 | surprise-abort on mixed commit batches |
| `shortcircuit_solver.py` | 294 | no-op overshoot trimmer |
| `retry_guard.py` | 233 | bounded retry + vLLM health probe |
| `trace_utils.py` | 121 | per-level prefix pruning |
| `solver_base.py` | 78 | the session seam every graft hangs off |

`composite.py`'s own docstring records an all-flags-off byte-identity gate it calls **"the
1.15-floor guarantee"** — the author measured stock at 1.15.

## Two of our own conclusions were wrong, and the fork says why

**1. The plateau has a mechanical cause we never found.** `recovery.py`'s docstring, from
forensics of a v8-era run:

> *One-level-deeper wall (sk48): level 0 cleared, then level 1 stalled to the wall; **the
> vendor level-transition wipe discards every mechanic learned**.*

The harness **erases the agent's knowledge at every level transition**. That single fact
explains the shape we measured all campaign and could not account for: top games clearing
2-3 levels then stalling with 30-95 minutes and 24-47 actions still available. They were
not out of budget — they were restarted from zero, repeatedly. It also explains why v14
(more capacity) and v16 (more state pushed per turn) both failed: neither carries anything
ACROSS a level boundary.

**2. v15 was abandoned for a reason that is false.** `notes/v15-stop-on-surprise.md` says
the batch path "was already guarded". `schema_void.py` reads the same code and is precise
about what the guard covers:

> *Duck commits multi-action batches through `step_env` and the vendored loop
> (`solver.py:588-661`) runs them to the end no matter what the world answers mid-batch; it
> breaks only on level/win/game-over/invalid.*

So a MIXED batch whose premise dies mid-way ("press A to open, then walk the corridor that
never opened") burns its entire tail, and every burned action feeds the quadratic penalty.
Our "already guarded" reading was true of four specific cases and false of the one that
costs score.

## banking — the scoring exploit we analysed our way past

We spent a day deriving the two-cap formula and concluded the efficiency axis ceilings at
5.80 public because the agent must explore to win. `banking_solver.py` separates the two:

1. win normally — exploration can cost whatever it costs
2. a scorecard's score is the **MAX over its plays** (`arc_agi.scorecard.EnvironmentScoreList.score`)
3. RESET issued in the WIN state performs a full reset even under `ONLY_RESET_LEVELS=true`,
   and a full reset opens a **NEW play on the SAME card**
4. prune the winning trace per level (drop actions that changed neither the frame nor
   `levels_completed`; a RESET voids everything since the level started)
5. replay the pruned trace on the fresh play — far fewer actions, so `(baseline/actions)^2`
   jumps
6. every replayed action is verified against the recorded state; the first divergence
   aborts, and aborting is **free** because the recorded win still owns the card max

`transfer_solver.py` then extends it across games, on a claim about the hidden set that R20
listed as unanswerable: that the **110 competition runs are the 25 games cloned round-robin**.
The first clone to clear a level publishes its pruned sequence; later clones of the same
family replay it and skip straight to the deepest solved level.

## Compatibility with our anim bundle — checked, not assumed

The fork targets the June bundle; v10 runs the anim bundle (`9158303`), which is what took
us from 3.31 to 4.71 public. Whether the grafts survive that base was verified two ways:

| check | result |
|---|---|
| every `inference.*` symbol the grafts import | **11 of 11 present** in anim and in the newer bundle |
| `_HarnessGameSession` method set | anim is a **superset** — 27 methods vs the fork base's 24, none missing |
| signatures of the 4 base methods the grafts override (`step_env`, `play`, `_finish_if_needed`, `_execute_auto_reset`) | **0 mismatches** |
| `from_solver` | defined by the grafts themselves, not the harness |
| `_LOCAL_ANALYZER_CONTEXT_WINDOW` | in `tool_agent.py` in both bundles, same count |
| engine version pinning | none in any bundle — `arc_agi`/`arcengine` come from the competition package on PYTHONPATH, i.e. identical for everyone |

⚠️ One probe artifact worth recording: the symbol sweep reported `ToolAgent  # lazy: needs
LLM env` as MISSING. That is my regex capturing an inline comment as part of the symbol
name — the real `ToolAgent` is present. A missing-symbol result from a sweep is a claim
about the pattern before it is a claim about the code.

## ⚠️ CORRECTION 2 (2026-08-23) — the fork's author is 102 ranks BELOW us

This file treats `thtennant`'s 6,524-line graft stack as evidence of what teams above us
do, on the strength of 1,275 downloads. The leaderboard CSV settles it:

| publisher | rank | hidden |
|---|---|---|
| ataraxian ("Ya Xu") | **21** | 2.37 |
| sonpham | 38 | 2.21 |
| **us (Thuitanium)** | **212** | **1.70** |
| **thtennant — this fork** | **314** | **1.46** |
| yousefturk (FluidMind) | 1381 | 0.23 |

R22's `attribution` lens had already stated the rule — *popularity is not evidence that a
scoring team uses it* — and this file half-believed the fork anyway.

**What rank 21 actually ships is six changed files against the same base**, one of which
is a `reasoning_effort` env hook set to `medium`; see `notes/R26-reasoning-effort.md`.
The two artifacts that read as most impressive (this fork, and FluidMind's writeup, which
diagnoses our harness precisely) are the two that score worst.

The mechanisms catalogued below are still real code and still worth reading. What does not
survive is the inference that they are what the leaders are doing.

## What is still UNVERIFIED

- **What this fork actually scores.** 1,275 downloads says people use it, not that anyone in
  the top 13 does. No submission on the board is attributable to it from public data.
- ~~**The clone claim.**~~ **REFUTED same day — see R22.** `transfer_solver` asserts 110 runs =
  25 games cloned round-robin. The ARC-AGI-3 technical report (arxiv.org/html/2603.24621v1,
  Table 1) states the opposite: **Public Demo 25 / Semi-Private 55 / Fully Private 55 = 135
  environments that do NOT overlap**, with the private sets deliberately out-of-distribution
  ("limited overlap with the mechanics found in the public environments"). DataCamp reports the
  same structure independently. `transfer_solver` degrades to a no-op when the clone fingerprint
  misses, so running it costs nothing — but it should not be counted as a lever, and the
  fork author's premise for it appears to be wrong.

  **This is the more important consequence:** if the hidden set is OOD by construction, then
  every graft that tunes to a *specific card's quirk* (parts of recovery, banking's per-card
  replay) carries transfer risk, while a **mechanic-agnostic** fix — not erasing the agent's
  own state — does not. That is an argument for doing the wipe fix FIRST, independent of how
  much the grafts are worth. It may also be the missing half of our 2.72x public→hidden shrink,
  which we have been treating as an unexplained constant.
- **Whether the grafts RUN on anim.** Symbol and signature compatibility is necessary, not
  sufficient — behaviour inside the overridden methods can still differ.
- The `1.15-floor` figure is the fork author's measurement of stock, not ours.
- ~~Whether the level-transition wipe still behaves that way in the anim bundle.~~ **CONFIRMED
  from our own source**, `inference/agent/tool_agent.py:1347-1356` — see the quote above.

## ⚠️ CORRECTION (same day, from the v18 full run) — the wipe is real and its effect is not

The section above reads the wipe as *the* explanation for the plateau. **Measured, it is not.**
Instrumented from the v18 full run's own `artifacts/*_events.jsonl` (1,062 analysis events,
22 level transitions across 15 of 25 games — a count that matches `benchmark.json` exactly, so
the probe is calibrated):

| carried-world-model block | non-empty knowledge fields, mean |
|---|---|
| ordinary analysis turn (n=550) | **2.10** |
| the first turn AFTER a level transition (n=15) | **1.87** |

Not empty. `re86` right after a transition still holds four fields (World model, Goal model,
Action model, Plan). The assignment at `tool_agent.py:1347-1356` does execute — but the agent
rewrites those keys on the very next assistant turn through
`_update_summarized_knowledge_from_assistant`, so the net loss is ~11%, not a reset to zero.

**What IS measured and unexplained:** `Cross-level notes` — the one key the wipe deliberately
spares — is **never written, in any game, in either run**. The prompt lists it among six other
optional prefixes ("Helpful optional prefixes are ...") and never says it is the only one that
survives, so the model has no reason to prefer it. That is a real gap, but it is a small one:
the six wiped keys are being refilled anyway.

Three probes were wrong before this one, and each was caught by a control rather than by
re-reading the code:
1. counting the knowledge keys in `transcripts/` gave 134 hits for `Cross-level notes:` —
   all of them the prompt's own list of prefixes echoed back, none written by the model.
2. counting inside `[ASSISTANT]` blocks gave **0** written knowledge lines of any kind, which
   the rendered "Working world model carried" blocks (82 of 82 non-empty) immediately refuted.
3. searching `prompts/*.log` for a level transition found **0 in 25 games** — those logs hold
   only ~2 turns per game (control: `You are a coding agent` appears 50 times across 25 files),
   so they cannot see mid-game events at all.

The rule that keeps surviving: a count over a log is a claim about what the log RECORDS before
it is a claim about what the system DID.

## Two independent measurements of what this class of bug costs (added from R22)

Neither is our harness, and neither is the same mechanism — but both are "the harness throws
away what the agent worked out", and both were measured rather than argued:

- **OpenAI**, on their own ARC-AGI-3 runs: the official harness discarded private reasoning
  after every action and deleted old history past 175,000 chars. Retaining reasoning and
  compacting instead took their public score from **13.3% to 38.3%** — nearly 3x — while
  *reducing* output tokens 6x. (openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/)
- **Princeton's "Continual Harness"** deliberately does not wipe at level-up / game-over /
  stagnation; a "Refiner" re-reads the raw trajectory and consolidates it into memory and
  skills. **20.54%** against baselines of 5.2% and 12.30%.
  (sethkarten.substack.com/p/continual-harness-an-efficient-self)

The port that needs no internet: at `tool_agent.py:1347-1356`, instead of assigning `""` to the
six knowledge keys, **distil them first and carry the distillate forward** — retain-then-summarise
rather than discard.
