# R40 — six turns in ten end without moving the game, and one game spent 108 of them without firing a single action

Measured 2026-08-25, offline, 0 slots, from the `clock-2x-v1` and `taaf-duck-v25` artifacts
already on disk. Found while asking a different question: why three samples of one build score
4.71, 3.69 and 2.82.

## 1. The number

Every `analysis` turn whose transcript carries `turn_time_budget`:

| run | turns ending in a yield | rate |
|---|---|---|
| `clock2x` | 1,150 of 1,858 | **61.9%** |
| `v25` | 668 of 1,105 | **60.5%** |

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
| `v25` **ft09** | **107 / 108 = 99%** | **0 action rows**, ends `NOT_FINISHED`, `run_status=playing` |
| `v25` **bp35** | 72 / 74 = 97% | 1 action in the whole game |
| `clock2x` ft09 | 43 / 65 = 66% | 73 actions, 4 levels, 47.62 |
| median game, either run | ~55-65% | plays normally |

**`ft09` in v25 never fired an action at all.** 108 analysis turns, every one of them a tool
call the harness dispatched and then cut before it could reach the environment. That is not
"played and lost" — the game was never entered.

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
