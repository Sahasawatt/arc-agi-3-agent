# R37 — the score is a step function of LEVELS, and 77% of scoring cells cannot be moved by any efficiency lever

2026-08-25. Offline, 0 slots, 0 submissions. Instrument: `eval/score_shape.py`, five controls
gating it, every one proven red on a mutation, exit 0.

Numbered **R37** deliberately, and the three colliding pairs were renumbered in the same change:
`R29-grid-lines` → R34, `R28-usage-distribution` → R35, `R30-untried-ledger` → R36. It reads only `eval/fixtures/*.json`, so unlike everything under
`scripts/b27/` it runs on any checkout — no `~/Claude/arc-artifacts/` corpus needed.

## The answer

LEDGER's standing explanation of the campaign is *"the column that actually explains the score
is actions per level"*, measured across five builds. Within a game it does not hold, and the
reason is in this repo's own `scoring.py`:

```
level_score = min((baseline / actions_in_that_level) ** 2 * 100, 115)
game_score  = min( sum(level_score * level_no) / sum(1..total),     # raw efficiency
                   100 * sum(levels done)      / sum(1..total) )    # completion cap
```

When the completion cap binds, **the score is a function of the level count alone** and no
number of actions saved can move it. Over the four runs with per-game fixtures:

| | cells |
|---|---|
| **CAP-BOUND** — actions irrelevant | **27** |
| raw-bound — efficiency actually paid | **8** |
| unknown — game has no cap anchor | 17 |

**27 of the 35 decided cells = 77%.** Two runs of the same game with the same level count differ
in score by a median of **2.16%** while differing in actions by **32.9%**; with different level
counts the median score difference is **100%**.

## What it costs the efficiency axis

Give every game with a known total its cap for free — i.e. play the levels it already clears
perfectly, clearing not one extra:

| run | public | if every known game hit its cap |
|---|---|---|
| v10cal | 4.71 | **5.44** (+0.73) |
| v18 | 3.60 | 3.76 (+0.16) |
| v19 | 2.82 | **2.82 (+0.00)** |
| v20 | 0.18 | 0.25 (+0.07) |

**v19's headroom is exactly zero** — every game it scored in is already at its cap, so that run
extracted all the efficiency its level count permits and still scored 2.82.

`5.44` is computed from 14 of 25 games; B20's efficiency ceiling, derived independently, is
**5.80 public**. Two different routes to the same wall, 6% apart, with 11 games still excluded
from this one. The axis is closed by arithmetic, not by opinion.

Against that, one more level in a 6-level game pays **+9.52** to that game — and the *entire*
efficiency headroom of the campaign's best run is worth about two such levels, collected across
every game at once.

## Why eleven modifications produced zero rankable results

Two measurements compose, and together they are a proof rather than bad luck:

1. **77% of scoring cells are unreachable by an efficiency lever**, and every lever measured so
   far — KV fp8 (B16), upscale (B23/B31), brevity (B12), `reasoning_effort` (B31), grid lines
   (B31), the untried-ledger nudge (B32) — acts on efficiency or on behaviour, never on the cap.
2. **Payoff and noise are concentrated in the same handful of games.** Across the three runs
   `rank_runs.py` reads as NOT-DISTINGUISHABLE:

   | game | sd | share of all per-game variance |
   |---|---|---|
   | re86 | 11.09 | **35.2%** |
   | ft09 | 9.90 | **28.1%** |
   | dc22 | 6.73 | 13.0% |
   | lp85 | 5.71 | 9.3% |
   | sc25 | 3.24 | 3.0% |
   | cd82 | 2.76 | 2.2% |

   **Six games carry 90.8%** of it. Six others have sd **0.00**. Four games supply 50% of the
   total score and they are not the same four in any two runs (ft09 22.97→0.00, dc22 14.29→0.00,
   re86 0.12→27.14).

A global change applied uniformly to 25 games, whose payoff is reachable in 23% of cells and
whose signal must exceed the noise of six all-or-nothing games, cannot separate on a paired
per-game test. That is what every one of the eleven runs measured.

## Method, and the assumption it rests on

The fixtures carry `score`, `levels`, `actions` per game — not the game's total level count.
That total is DERIVED from cells where the cap binds exactly: it is the `n` with
`sum(1..n) == 100 * sum(1..cleared) / score`. Fourteen games resolve; the other eleven have no
cap-bound cell and are reported **UNKNOWN**, never folded into either bucket.

**The assumption is that levels are cleared contiguously from 1**, so `sum(done) == sum(1..cleared)`.
CONTROL 4 fails the run if any cell scores *above* its derived cap, which is what a non-contiguous
clear would produce. None does.

Derived totals: `ar25` 8 · `cd82` 6 · `cn04` 6 · `dc22` 6 · `ft09` 6 · `ka59` 7 · `lf52` 10 ·
`lp85` 8 · `r11l` 6 · `s5i5` 8 · `sb26` 8 · `sc25` 6 · `su15` 9 · `wa30` 9 = **103 levels over 14
games**. LEDGER puts the 25 games at **183**, leaving 80 for the other eleven (mean 7.3) — the
closure holds with room, and no game's derived total contradicts a level it has been seen to clear.

## What is NOT established

- **Eleven games are unresolved**, and they include `re86` — the single largest contributor to
  variance (35.2%) — plus `vc33`, `tu93`, `sp80`, `ls20`, `m0r0`, `tn36`, `bp35`, `g50t`, `sk48`,
  `tr87`. Whether `re86` is a deep game worth chasing or a shallow one that swings is **unknown**
  from these fixtures. Resolving it needs a run in which it is cap-bound, or the level counts from
  another source.
- **n = 4 runs.** The volatility table is three runs (`v10cal`, `v18`, `v19`); `v20` is a different
  model and is excluded from it. Six games at sd 0.00 over three samples is not "never varies".
- **This does not refute B20.** B20 already found the completion cap and ceilinged efficiency at
  5.80. What is new is the per-cell share (77%) and the reason the eleven modifications could not
  rank: B20 bounded the axis, this bounds the *reachable surface* of every lever on it.
- **It does not say the cap-bound games are unwinnable** — only that the way to score in them is
  another level, never a cheaper one.
- **`actions` in the fixtures is per GAME, not per level.** The formula's denominator is per level,
  so no efficiency figure here is computed from actions; the classification is by cap identity
  alone. That is why it can be done at all without the corpus.

## Controls

All five are evaluated on every run and the numbers are gated on all of them passing. **Each was
proven red on a mutation**, with mean-preserving mutations where needed — an earlier cut exited at
the first failure, and CONTROL 1 then masked every other control (three different mutations all
reported as CONTROL 1).

1. **Loader reproduces LEDGER's published means** — 4.71 / 3.60 / 2.82 / 0.18.
2. **The cap identity resolves and the resolver is not vacuous** — `100/36 = 2.7778` (which is
   `sb26`'s score exactly) resolves; a non-triangular 37 does not.
3. **Cross-run agreement** — no game's derived total may differ between its own runs. 0 conflicts.
4. **Teeth on the contiguous-clear assumption** — no cell may score above its cap.
5. **Closure** — derived totals must leave at least one level for each unresolved game, and no
   derived total may be below a level count that game has actually cleared.

Teeth, run on a scratch copy so the shared working tree is never mutated:

| mutation | controls that went red |
|---|---|
| shift a run's mean off the published value | `[1]` |
| two runs imply different totals for `lf52` (mean held) | `[3, 4]` |
| a cell scores above its own cap (mean held) | `[4]` |
| a derived total below the levels cleared there | `[1, 5]` |
| unmutated baseline, and after restore | `[]`, exit 0 |

## The clock binds on half the board, and only half

Added 2026-08-25, same instrument (`Q_C`). The fixtures hold a natural A/B that nobody had read:
the same game, played by runs that got through different numbers of actions. If the 7,920s wall
were the binding constraint, the run that spent more actions on a game should clear more of its
levels.

Counting pairs where the action counts differ by at least 15%:

| | pairs | |
|---|---|---|
| more actions -> **more** levels | **26** | 41% |
| more actions -> **fewer** levels | 5 | 8% |
| actions moved, **levels did not** | **33** | **52%** |

Per game:

- **TIME-limited (12)** -- `ar25` `bp35` `cd82` `dc22` `ft09` `ka59` `lp85` `r11l` `re86` `sc25`
  `tn36` `wa30`. The clearest are `re86` (123 actions -> 1 level, 339 -> 4, 276 -> 3) and `ft09`
  (62 -> 3, 43 -> 1, 11 -> 0).
- **FLAT (8)** -- `g50t` `lf52` `s5i5` `sb26` `sk48` `sp80` `tr87` `vc33`. `sb26` played 41 against
  **111** actions (2.7x) for the same single level all three times; `tr87` played 40 against **259**
  (6.5x) for zero every time.
- **INVERTED (2)** -- `cn04`, and `m0r0`, which cleared a level in 40 actions and **none in 133**.

**The direction of causation is not settled for the 12**, and that has to be said plainly: clearing
a level lets a game keep playing, so actions can rise *because* levels were cleared rather than the
other way round. The two readings are indistinguishable in this data.

**The FLAT and INVERTED games carry no such confound**, and they are the half that matters for a
decision: their action counts moved by 2-6x while their level counts did not move at all. Whatever
binds there, it is not the clock. That is **10 of 25 games** where extra time provably buys nothing.

Not fragile: at gap thresholds 0.00 / 0.05 / 0.10 / 0.15 / 0.25 / 0.40 the agree count exceeds the
disagree count every time, flat stays the plurality at 47-53%, and the TIME-limited group holds at
10-12 games.

**What it does to B34 and B36.** B34 asks whether the level-up rate continues past the wall, and
this answers it in advance for **at least 10 of the 25 games: no**. It also enlarges B36 -- the
reallocation candidate was written around the 3 games that never score (6.6h per run); the pool is
really those 3 plus 5 more FLAT games plus 2 INVERTED ones, where the agent measurably plays itself
*backwards* with the extra clock.

## Where the run-to-run randomness comes from

Not measured as an experiment -- read out of the harness, and recorded here because every number
above is a statement about variance and nothing in the campaign had named its source.

`localrig/ARC3-Inference/inference/agent/tool_agent.py`:

```
_LOCAL_ANALYZER_TEMPERATURE = _get_env_float("LOCAL_ANALYZER_TEMPERATURE", 0.6)
_LOCAL_ANALYZER_TOP_P       = _get_env_float("LOCAL_ANALYZER_TOP_P", 0.95)
_LOCAL_ANALYZER_TOP_K       = _get_env_int("LOCAL_ANALYZER_TOP_K", 20)
_LOCAL_ANALYZER_SEED        = _get_env_int("LOCAL_ANALYZER_SEED", -1)
```

and in `inference/utils/openai_compat.py`, `build_chat_payload` ends with

```
if seed is not None and seed >= 0:
    payload["seed"] = seed
```

so the default **-1 means no seed is sent at all** and vLLM picks its own. Every run of this
campaign sampled at temperature 0.6 with no seed.

**No builder has ever set either knob** -- 0 occurrences of `LOCAL_ANALYZER_TEMPERATURE` and
`LOCAL_ANALYZER_SEED` across every `duckv*/` builder and `clock2x/`. `MAP.md` and
`LEDGER-all-runs.md` return **0 hits** for `temperature`, `seed` and `sampling`. The band that has
gated every decision in this campaign has never had its mechanism written down.

This does not say pinning them would work: greedy decoding is a different agent, batched vLLM is
not bit-reproducible across differing batch compositions even at a fixed seed, and the wall-clock
cut lands in a different place regardless. It says the knobs exist, cost nothing to set, and have
never been tried. Filed as **B37**.

## Reproduce

```bash
python eval/score_shape.py
python eval/score_shape.py --json
```

Reads `eval/fixtures/*.json` only. Zero GPU slots, zero submissions, no model calls, no corpus.
