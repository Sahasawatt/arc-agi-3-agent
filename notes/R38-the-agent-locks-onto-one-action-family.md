# R38 — 73% of every action fires after the last level-up, and a quarter of them come from one locked action family

Measured 2026-08-25, offline, 0 slots, from the `clock-2x-v1` artifacts already on disk
(`kernels output yocybercode/clock-2x-v1`, 25 games × `*_events.jsonl`). One run, so every
count here is n=1 and says so.

This is the **candidate draft B35 asked for**: stop applying one global change to 25 games.
It is not a build yet — the last section lists what must be true before it becomes one.

## 1. The four populations, from run data rather than from intuition

B35 proposed three. There are four, and the one it did not name is the interesting one.
Classified over the four same-family runs (`clock2x`, `v10cal`, `v18`, `v19` — `v20` is a
different model and is excluded):

| population | n | games | what it means |
|---|---|---|---|
| **STABLE** | 6 | `lf52 s5i5 sb26 sp80 su15 vc33` | **the same level count in EVERY run** — the wall is deterministic, not luck |
| ALL-OR-NOTHING | 11 | `bp35 cd82 cn04 dc22 ft09 ka59 ls20 m0r0 r11l tn36 wa30` | scores in some runs, zero in others — where both the points and the noise live |
| varies | 5 | `ar25 lp85 re86 sc25 tu93` | scores every run, different depth |
| NEVER | 3 | `g50t sk48 tr87` | zero levels in all four runs |

**STABLE is worth more than every efficiency lever combined.** One extra level in each of
those six pays **+39.43 points = +1.58 public**, against the total efficiency headroom measured
the same day of **+1.09**. And unlike the headroom it is not a lottery: those six games return
the identical level count run after run, so whatever blocks them blocks them reproducibly.

⚠️ **`clock2x` already refuted the obvious explanation.** Doubling the clock gave `sp80`
45 → **157** actions and `vc33` 36 → **137**; neither gained a level. It is not time, and it is
not action budget.

## 2. What the stuck games actually do

Reading the event stream of the clock2x run:

| game | actions after the LAST level-up | what the tail is made of |
|---|---|---|
| `vc33` | **123 of 137 = 90%** | every MOUSE action at `row=56` — 101 clicks along one row |
| `sb26` | 64 of 72 = 89% | MOUSE at `row=22` and `row=36` |
| `sp80` | 112 of 157 = 71% | `RIGHT`/`UP`/`LEFT`/`SPACE` cycling |
| `tr87` | 319 of 319 = 100% | one family fired **226 times in a row** |

Across all 25 games: **1,920 of 2,637 actions (73%) fire after the game's last level-up.**

The shape is not random flailing. The agent commits to one hypothesis and enumerates inside
it — a fixed row, a fixed key set — for dozens to hundreds of actions. That matches R29/B27's
finding that the goal is usually right and the **transition model** is what is wrong: it keeps
acting as though this family of actions is the one that matters.

## 3. The candidate — a brake at the FAMILY level, not the action level

**Rule.** Track, per game, how many times each *action family* has fired since the last
level-up. A family is `(MOUSE, row)` for clicks and `(KEY, name)` for everything else. When a
family reaches **k = 20**, remove it from the action set offered for the next decision until a
level-up resets the ledger.

Why a family and not an action: B29's brake keys on an exact `(level, board, action)` repeat,
and R32 priced it at **0.49% of decisions, 7.8 per run**. `vc33` never repeats an action
exactly — it clicks `row=56, col=46`, then `col=12`, then `col=50`. Every one of those is a
distinct action and the same hypothesis.

### Reach and cost, swept on real data

| k | speaks on | real level-ups it would have destroyed |
|---|---|---|
| 10 | 45.5% | **5 of 30** |
| 15 | 34.2% | **5 of 30** |
| **20** | **25.9%** | **0 of 30** |
| 25 | 20.4% | 0 of 30 |
| 30 | 17.0% | 0 of 30 |
| 60 | 9.7% | 0 of 30 |

**k=20 speaks on 26% of all decisions and destroys none of the 30 level-ups the run produced**
— 50× the reach of the B29 brake R32 measured at 0.49%.

⚠️ **The margin is one.** The deepest a family had fired at the moment of a real level-up is
**19** (`lp85` L3→L4; `re86` and `cd82` and `tn36` sit at 16-17). k=20 clears that by a single
count, on **one run and 30 level-ups**. That is the number most likely to be wrong here, and
the sweep above is exactly why k=25 or k=30 are the fallbacks — they cost 5.5 and 8.9 points of
reach and buy real margin.

## 4. Why this is none of the four things already closed

- **Not B36 / clock2x (time).** No budget moves. The same game gets the same clock; only the
  action set offered at a stuck decision changes. clock2x proved more time is not the missing
  ingredient, which is what makes a non-time lever the next thing to try rather than a guess.
- **Not B32 (untried-ledger nudge).** That spoke through the hint channel and the 27B treated it
  as overrulable advice: **obedience 52%**, with `sb26` ignoring `ACTION7` seven times and
  `tr87` ignoring arrows for 72 turns. A brake is structural — the action is not in the set, so
  there is nothing to disobey. R6's Mode-2 law ("offered tools used ZERO times 9/9") points the
  same way: this agent does not do bookkeeping it is *asked* to do.
- **Not B29 (exact-action brake).** Same idea one level of abstraction up, and the abstraction is
  the whole difference: 0.49% → 25.9%.
- **Not B31/v21 (thinking dial).** No model setting changes. The agent reasons exactly as it does
  today, with a smaller menu at the moments it has demonstrably stopped making progress.

## 5. What is NOT known, stated before anyone builds it

1. **n = 1 run.** Every number here is from `clock-2x-v1`. The other runs' artifacts live in
   `~/Claude/arc-artifacts/` on the Mac and were not read. Re-running §3's sweep across all five
   runs is free, changes no code, and is the first thing to do.
2. **A removed action is not a better action.** This measures that the brake can fire without
   killing known level-ups. It does **not** show the agent then does something useful — B32's
   whole lesson is that induced behaviour ≠ score. The brake could simply move the lock to the
   next family.
3. **`tr87` and `ls20` dominate the reach** (239 and 140 of 682 suppressions at k=20). Two games
   of 25, exactly as R32 found for the B29 brake (32 of 39 in `ls20`). The 25.9% is not spread
   evenly and the headline overstates what a typical game sees.
4. **Where the brake is enforced is unwritten.** The action set reaches the model through the
   prompt; whether removal happens there or at the harness's action-validation layer decides
   whether this is a prompt change (weak, per B32) or a structural gate (the point). This is the
   design question to answer first.
5. **STABLE was measured across runs; the harness sees one run.** The brake's trigger is
   within-run (`k` fires since the last level-up) and needs no population label, which is what
   keeps it from overfitting the public 25 — but it also means it cannot target STABLE
   *specifically*. It fires wherever a lock appears.

## 6. Reproduce

Requires the clock2x artifacts:

```bash
kaggle kernels output yocybercode/clock-2x-v1 -p <dir>
```

Then the population table is `eval/score_shape.py` plus `eval/fixtures/*.json`; §2 and §3 read
`<dir>/artifacts/*_events.jsonl` directly — `type == "action"` rows carry `level` and
`action_display`, which is everything the sweep needs.
