# duck-mod commit run — per-game score forensics (public 2.41)

Sources (read-only): `%TEMP%\duckmodout\taaf-duck-mod.log` (1,411 lines, 228.7KB — Kaggle
kernel stdout/stderr, one JSON stream-event per line), `%TEMP%\duckmodout\benchmark.json`
(863KB, the structured per-game `game_runs[]` the log's printed tables are derived from) and
`%TEMP%\duckmodout\summary.txt`. `duckmod-transcripts-20260819.md` (prior forensics, tool-call
level) used as background on the ft09/ar25 lift; not re-derived here. Harness state machine
read from `duck\bundle\src\tufa-arc-agi-framework\src\taaf\game.py` and
`duck\bundle\src\ARC3-Inference\inference\framework\solver.py`. `environment_files/` was not
touched.

## 0. What this run actually is

The log's final periodic diagnostics snapshot (`taaf-duck-mod.log:1321-1363`, `time=8553.0`)
is the commit run's own summary: 25 games, 1 pass, mean score **2.41**, median **0.08**, total
actions **3,481**, total tokens **1,503,782**, `runs: 25 (won: 0)`. `benchmark.json`'s
`game_runs[]` (25 entries, one per game) is the structured source for the same numbers plus
per-level detail the log's printed table doesn't carry: `actions_per_level`,
`base_actions_per_level` (the human baseline the ARC-AGI-3 scoring formula compares against),
`final_wallclock_seconds`, and `state`.

## 1. Per-game table

`ratio` = actions the agent spent on the level where it was still active when the run ended,
divided by that level's human baseline (`base_actions_per_level[i]`) — <1.0 means it hadn't
even used a fair human-equivalent try before the clock cut it off; ≥2.0 means it used at least
double a human's budget on that level and still didn't clear it. `bucket` is defined in §3.
Source: `benchmark.json` → `game_runs[].{actions_per_level,base_actions_per_level,
levels_completed,final_score,final_wallclock_seconds,history}` for every row below.

| game | levels | score | actions | tokens | sec/action | stuck at | level actions | level base | ratio | bucket |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---|
| ar25-0c556536 | 2/8 | 7.73 | 164 | 64,873 | 48.3 | L3 | 81 | 75 | 1.08x | B |
| bp35-0a0ad940 | 1/9 | 0.28 | 230 | 65,266 | 34.4 | L2 | 171 | 48 | 3.56x | C |
| cd82-fb555c5d | 0/6 | 0.00 | 98 | 66,101 | 80.8 | L1 | 98 | 55 | 1.78x | B |
| cn04-2fe56bfb | 0/6 | 0.00 | 99 | 66,465 | 80.0 | L1 | 99 | 29 | 3.41x | C |
| dc22-fdcac232 | 0/6 | 0.00 | 73 | 66,677 | 108.5 | L1 | 73 | 59 | 1.24x | B |
| ft09-0d8bbf25 | 3/6 | 28.57 | 44 | 58,176 | 180.0 | L4 | 2 | 28 | 0.07x | A |
| g50t-5849a774 | 0/7 | 0.00 | 53 | 59,423 | 149.5 | L1 | 53 | 78 | 0.68x | A |
| ka59-38d34dbb | 0/7 | 0.00 | 58 | 68,132 | 137.2 | L1 | 58 | 28 | 2.07x | C |
| lf52-271a04aa | 1/10 | 1.82 | 234 | 65,163 | 33.9 | L2 | 211 | 81 | 2.60x | C |
| lp85-305b61c3 | 1/8 | 2.78 | 59 | 50,041 | 134.3 | L2 | 50 | 38 | 1.32x | B |
| ls20-9607627b | 1/7 | 2.06 | 49 | 55,246 | 161.7 | L2 | 20 | 123 | 0.16x | A |
| m0r0-492f87ba | 0/6 | 0.00 | 418 | 64,989 | 19.0 | L1 | 418 | 30 | 13.93x | C |
| r11l-495a7899 | 1/6 | 4.76 | 58 | 65,662 | 136.6 | L2 | 49 | 33 | 1.48x | B |
| re86-8af5384d | 1/8 | 0.89 | 70 | 58,045 | 113.2 | L2 | 24 | 42 | 0.57x | A |
| s5i5-18d95033 | 1/8 | 0.08 | 206 | 65,716 | 38.5 | L2 | 91 | 89 | 1.02x | B |
| sb26-7fbdac44 | 1/8 | 2.78 | 113 | 65,058 | 70.1 | L2 | 104 | 28 | 3.71x | C |
| sc25-635fd71a | 0/6 | 0.00 | 151 | 66,317 | 52.5 | L1 | 151 | 36 | 4.19x | C |
| sk48-d8078629 | 0/8 | 0.00 | 174 | 65,683 | 45.5 | L1 | 174 | 61 | 2.85x | C |
| sp80-589a99af | 1/6 | 4.76 | 194 | 66,742 | 40.8 | L2 | 175 | 58 | 3.02x | C |
| su15-1944f8ab | 1/9 | 2.22 | 110 | 65,553 | 72.0 | L2 | 91 | 42 | 2.17x | C |
| tn36-ef4dde99 | 0/7 | 0.00 | 182 | 66,163 | 43.5 | L1 | 182 | 32 | 5.69x | C |
| tr87-cd924810 | 0/6 | 0.00 | 240 | 63,734 | 33.0 | L1 | 240 | 54 | 4.44x | C |
| tu93-0768757b | 2/9 | 1.46 | 110 | 60,576 | 72.0 | L3 | 33 | 34 | 0.97x | A |
| vc33-5430563c | 0/7 | 0.00 | 34 | 40,463 | 233.0 | L1 | 34 | 7 | 4.86x | C |
| wa30-ee6fef47 | 0/9 | 0.00 | 260 | 65,527 | 30.5 | L1 | 260 | 71 | 3.66x | C |

## 2. 2.41 cross-check

Sum of the `score` column above = **60.19**; ÷ 25 = **2.4077**, matching the reported mean
2.41 (log line 1329: `mean score: 2.41`) to rounding. Sum of the `actions` column = **3,481**,
matching log line 1331 (`total actions: 3481`) exactly. **Both totals reconcile — the
per-game table fully accounts for the reported score, no games or points are unexplained.**

## 3. Termination: every game timed out, none crashed, none surrendered early

`benchmark.json` — grepped every `"game_id"`/`"state"` pair across all 25 entries: **all 25
read `"state": "gave_up"`**. Zero read `"crashed"`, zero `"cancelled"`, zero `"won"`. Grepped
`"solver_note": "error` across the whole file: **0 hits** — the exception path in
`solver.py:325-330` only sets `state="crashed"` and writes `solver_note=f"error: ..."`
together, so their joint absence confirms no game hit an unhandled exception.

`solver.py`'s `should_stop()` (`:246-261`) only returns `True` for a non-winning game on
`runtime_limit_reached()` (the per-game wall-clock cap) or `max_actions_per_game` (configured
`None` for this run — log line 655 — so it never fires). `_is_run_complete()` (`:143-144`)
requires an engine `WIN` state, which none of the 25 reached. Every game's
`final_wallclock_seconds` (`benchmark.json`, per-row) is **7,921.0–7,955.4s**, tightly
clustered on the configured `max_runtime_s_per_game=7920.0` (log line 655) — i.e. **every
single game ran to its individual 132-minute wall-clock cap and was cut off there**, not
stopped by a lack of actions, a crash, or an explicit give-up decision distinct from the
clock. `concurrency=28 ≥ games=25` (log line 655), so all 25 games ran one wave, in parallel —
this is why the job's own total wallclock (log line 1334, 198,090.1s job-clock ≈ the printed
`duration: 2h 12m 35s` once divided by the concurrent games) lines up with each game
individually spending its full ~7,920s budget rather than queueing behind others.

**This means action count is not a resource the harness was managing directly** — it is
whatever fit inside 7,920s given how long each game's model turns took. Seconds/action ranges
from **19.0s** (m0r0) to **233.0s** (vc33) across otherwise-identical config, a >12x spread.

## 4. Failure buckets, ranked by recoverable points

Bucket assignment is purely the `ratio` column in §1 (actions spent on the level active when
the clock cut the game off, ÷ that level's human baseline) — no other signal was available in
this log/JSON pair (no per-action frame diffs, no tool-call transcripts were re-parsed here;
see prior report for that layer).

### Bucket C — "thrashing": ratio ≥ 2.0x, 14 of 25 games, combined score 11.86

`bp35, cn04, ka59, lf52, m0r0, sb26, sc25, sk48, sp80, su15, tn36, tr87, vc33, wa30`. These
games used **at least double** — up to **13.93x** (m0r0: 418 actions against a 30-action human
baseline for level 1, and 0 progress) — the human action budget on their current level and
still did not clear it. This is **the majority of the run (56% of games)** and contains **9 of
the 10 zero-score games** (`cn04, m0r0, sc25, sk48, tn36, tr87, vc33, wa30`, plus `ka59` —
every zero-score game except `g50t`, which is Bucket A). More time would not obviously fix
this bucket: these games already had more than a fair human-equivalent number of tries and
still failed, which points at a discovery/strategy gap (the model never found the mechanic),
not a resource shortage. This is the largest total point pool in the run (every zero-score
game but one lives here) but the lowest-confidence fix, since the log/JSON pair gives no
visibility into *why* the actions taken didn't work.

### Bucket B — "fair trial, still stuck": 1.0x ≤ ratio < 2.0x, 6 games, combined score 15.36

`ar25, cd82, dc22, lp85, r11l, s5i5`. Used roughly one human-equivalent try (1.02x–1.78x) on
the level they're stuck at and still didn't clear it. Ambiguous signal — could resolve with
either more time or a strategy fix; not separable from this data.

### Bucket A — "clock-limited, not skill-limited": ratio < 1.0x, 5 games, combined score 32.97

`ft09, g50t, ls20, re86, tu93`. Had **not yet used a full human-equivalent try** on their
current level when the 132-minute cap ended the game. This bucket holds **the single best
performer in the entire run** — `ft09` (score 28.57, 3/6 levels) — which cleared levels 1–3 in
**21, 7 and 14 actions against baselines of 43, 12 and 23** (well under 1x each time — the
most action-efficient game of the 25, see §1) and was only **2 actions into level 4 (base 28)**
when the clock stopped it. `tu93` was **33 of a 34-action baseline into level 3** (ratio 0.97x,
essentially at the human pace) when cut off. Both are direct evidence the ceiling was the
wall clock, not the model's ability, in these specific cases. `g50t`, `ls20`, `re86` are
weaker examples of the same shape (low ratio, zero-or-partial score) but their per-action time
(149.5s / 161.7s / 113.2s — 3 of the 5 slowest games in the whole run) means the clock bound
them by way of high latency-per-action rather than by genuinely being close to a level clear;
this data cannot separate "would have solved it with 10 more actions" from "was headed
nowhere, just slowly."

## 5. Top 3 fixes by expected points

1. **Per-action latency, run-wide.** All 25 games hit the *same* 7,920s cap and none crashed
   (§3) — action budget is entirely a function of time-per-model-turn. Seconds/action spans
   19.0–233.0s for no configuration difference between games. Halving latency would
   roughly double the actions available to every game at the same wall-clock cost, which most
   directly helps Bucket A (`ft09`/`tu93` were mid-level, not stuck) and the low-ratio half of
   Bucket B (`ar25` 1.08x, `s5i5` 1.02x) — the games with the clearest evidence they were still
   making forward progress when time ran out. This is the only fix with a mechanism
   (`runtime_limit_reached()`) directly traceable to every game's outcome; it is not proven to
   help Bucket C, whose games already had more tries than a human baseline and still failed.

2. **Bucket C's zero-score members** (`cn04, m0r0, sc25, sk48, tn36, tr87, vc33, wa30, ka59`
   — 9 games, all stuck on level 1 at 2.07x–13.93x baseline). Largest point pool in the run by
   game count (9 of 10 zero-score games) but this table gives no evidence of *why* the level-1
   mechanic wasn't found — only that repeated, above-baseline trying didn't surface it. `m0r0`
   (418 actions, 13.9x baseline, 0 progress) is the single largest action-waste in the run and
   the clearest individual target for whatever root-cause investigation follows this report.

3. **Bucket B's near-baseline stragglers** (`ar25` 1.08x on L3, `s5i5` 1.02x on L2, `dc22`
   1.24x on L1) — closest to the Bucket-A "just needs more room" profile without being as
   clear-cut; a latency fix (item 1) is the most likely lever to move these, but unlike `ft09`/
   `tu93` there's no multi-level track record in this run showing they were converging.
