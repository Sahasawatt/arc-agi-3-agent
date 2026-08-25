# R40 — three turns in ten end without moving the game, and one game never left its first step

⚠️ **CORRECTED 2026-08-25, hours after this note was first pushed.** Its headline said SIX in ten,
from counting raw `analysis` rows. A row is not a turn: the log writes a record per retry, so a
stalled step is recorded many times. The unit is `(action_num, analysis_step)`, and on that unit
the rate is **30.5% / 30.2%**, not 61.9% / 60.5%. The correction was not found by re-reading this
note — the `dev.knowlesscrew.studio/arc-agi/replay` viewer states the trap in its own methods
section (*"A turn is not an event... reading those as think-only turns counts each turn twice and
inflates the idle rate several-fold"*), and that page was read AFTER this was committed. §8 records
what survived.

Measured 2026-08-25, offline, 0 slots, from the `clock-2x-v1` and `taaf-duck-v25` artifacts
already on disk. Found while asking a different question: why three samples of one build score
4.71, 3.69 and 2.82.

## 1. The number

Every `analysis` turn whose transcript carries `turn_time_budget`:

| run | steps ending in a yield | rate | (raw rows, the WRONG unit) |
|---|---|---|---|
| `clock2x` | 291 of 953 | **30.5%** | ~~1,150 of 1,858 = 61.9%~~ |
| `v25` | 177 of 586 | **30.2%** | ~~668 of 1,105 = 60.5%~~ |

**The unit is `(action_num, analysis_step)`.** Counting `analysis` rows double-counts every step
the harness retried, and the inflation is worst exactly where the finding is: `ft09` in v25 is
**108 rows over 1 step**, `bp35` **74 rows over 3**.

The `[ANALYZER STATUS]` block on such a turn reads:

```
message: Yielded control to solver: turn_time_budget.
step_executed: False
yield_seconds: 60.0
```

and its `[MODEL RESPONSE META]` reads `finish_reason: tool_calls`, `tool_call_count: 1`. **The
model is not failing to answer.** It calls the tool, the harness dispatches it, and then the
60-second turn budget expires before anything reaches the game.

## 2. Where the 60 comes from — not from the code

`tool_agent.py` defaults it to **off**:

```
_LOCAL_ANALYZER_YIELD_SECONDS = _get_env_float("LOCAL_ANALYZER_YIELD_SECONDS", 0.0)
self._yield_seconds = None if _LOCAL_ANALYZER_YIELD_SECONDS <= 0 else float(...)
```

The bundle's own `setup_commands.json` ships `'LOCAL_ANALYZER_YIELD_SECONDS': '60'`, and every
run of this campaign inherits it. ⚠️ **`R2-levers.md` records this lever as "default 0
(disabled)"** — true of the code and false of every run we have ever done. Same shape as the
`MULTIMODAL_GRID_LINES` case in R34, where the author's config armed `'true'` against a `== "1"`
reader: **the lever table's "current" column has to come from a run's `taaf_setup_env.json`, not
from the source.**

## 3. What a yield does NOT cost

Stated because the obvious reading is wrong and it is the one that would justify a build:

- `LOCAL_ANALYZER_TOOL_STEPS: 0` does **not** disable the sub-turn loop —
  `self._tool_steps = None if _LOCAL_ANALYZER_TOOL_STEPS <= 0 else ...`, so 0 means
  **unbounded**, and the loop at `:2167` runs.
- A yield taken on the last tool call of a turn leaves `preserve_history = True` (`:2139`;
  it is only cleared at `:2351/:2356` when a yield lands mid-batch). **The tool result stays in
  `messages`**, so the next turn resumes with the work in context.

So 61.9% is not 61.9% of the run thrown away. It is the rate at which a turn ends **without
moving the game**, with its reasoning carried forward. Reading it as waste would be the same
error R39's first probe made — a big number that measures something other than what it looks
like.

## 4. Where it does become pathological

Per game, the same measurement:

| run / game | yield rate | outcome |
|---|---|---|
| `v25` **ft09** | **1 / 1 step = 100%** | **0 action rows**, ends `NOT_FINISHED` — and every one of its 108 records is `(action_num=0, analysis_step=1)` |
| `v25` **bp35** | 2 / 3 steps = 67% | 1 action in the whole game |
| `clock2x` ft09 | 10 / 30 steps = 33% | 73 actions, 4 levels, 47.62 |
| median game, either run | ~30% | plays normally |

**`ft09` in v25 never fired an action at all, and it never advanced past its FIRST step.** All
108 of its records carry `(action_num=0, analysis_step=1)`: one step, dispatched and cut, over
and over, for the whole game. That is worse than this note first said — not 108 turns of failed
progress but zero turns of any progress.

⚠️ **And it is the single most expensive cell in the corpus.** `ft09` is what `v10cal` scores
**22.97** on, its best game. Against `v25`, `ft09` alone is **+22.97 points = 0.92 public of the
1.02 gap — 90% of it.** The next five games together overshoot the gap (they cancel), which is
the R37 picture at run scale: a handful of games carry everything.

## 5. What this does not settle

1. **Why ft09 yielded 99% in v25 and 66% in clock2x is not separable from one run.** The two
   runs' `taaf_setup_env.json` differ in **exactly one key** (`LOCAL_ANALYZER_SEED`), so config
   is ruled out — but the duckmod leak also lengthened v25's system prompt by **+1,835 chars
   (+12.9%)** (R39/B37), and sampling noise alone remains a live explanation. Three candidates,
   one observation.
2. **Nobody has measured what a longer `yield_seconds` buys.** It is a genuine lever, it has
   never been varied, and this note does not propose a value — B34 just spent a run proving that
   more clock at the GAME level bought +2 levels, and the turn level is a different axis but the
   prior is not encouraging.
3. **The rate may be correct behaviour.** Yielding returns control to the solver, which is what
   lets 28 games share a GPU; a run with no yields at all is not obviously better. What is
   clearly wrong is a game reaching 99%.

## 6. Why this matters for B38

B38 proposes a brake that fires when a family of actions repeats too often since the last
level-up. **A game that fires no actions at all is invisible to it** — `ft09` in v25 would
present as a game with zero repeats and a perfectly clean ledger. Any per-game targeting design
(B35's frame) needs the yield rate beside the action count, or it will read a stalled game as a
well-behaved one.

## 7. Reproduce

```bash
kaggle kernels output yocybercode/clock-2x-v1 -p <dir1>
kaggle kernels output sahasawatt/taaf-duck-v25  -p <dir2>
```

Count `analysis` rows whose `transcript` contains `turn_time_budget`, against all `analysis`
rows, per game. The config claim is `taaf_setup_env.json` in each run's output; the code default
is `tool_agent.py`'s `_get_env_float("LOCAL_ANALYZER_YIELD_SECONDS", 0.0)` in the vendored
bundle at `duck/bundle/src/` (untracked reference).

## 8. What the correction changed, and what survived

Corrected the same day, after reading the replay viewer's own methods note. What was wrong:

- **The headline rate.** 61.9% / 60.5% counted raw `analysis` rows. On `(action_num,
  analysis_step)` it is **30.5% / 30.2%** — still high, half of what was published.
- **"108 turns".** They are 108 records of ONE step.

What survived unchanged:

- `yield_seconds = 60` comes from the bundle's `setup_commands.json`, while the code defaults to
  `0.0`, so **§2's correction to `R2-levers.md` stands** — and it is the more transferable half.
- **`ft09` in v25 fired zero actions and ended `NOT_FINISHED`.** That is an action-count fact,
  independent of how turns are counted, and the step-level reading makes it sharper.
- **`ft09` is 0.92 public of the 1.02 gap.** A score arithmetic fact, untouched.
- §3's point that a yield is not waste (`TOOL_STEPS: 0` is unbounded, `preserve_history` stays
  True) — untouched, and it is why the corrected 30% still does not justify a build on its own.
- §6's consequence for B38 — a zero-action game is invisible to a repeat-based brake — untouched.

⚠️ **The lesson is not "count carefully".** The trap was already written down, in the methods
section of a page in this workspace, by the peer who hit it first and measured a headline **3.6×
too high**. It was read hours after this note was committed. A denominator drawn from a log's
rows rather than from its own step identifiers is worth a second look BEFORE publishing, and
someone else's methods note is the cheapest place to find that you are about to repeat their
error.
