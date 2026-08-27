# R47 — R44 at n=2: the gate IS the knob, every mechanistic prediction lands, and the score does not move

**2026-08-27, offline, 0 slots, 0 GPU.** Corpus is **two** runs' `*_usage.jsonl`:
`thui-v1-1-r2` at `LOCAL_ANALYZER_YIELD_SECONDS = 60` (1,306 requests / 1,070 `analyze()` calls)
and `thui-v3-0` at **180** (1,200 requests / **719** calls), 25 games each.

R44 closed on *"n = 1 run. No other run carries the probe."* `thui-v3-0` is the second, and it is
**not a repeat** — it moved the knob R44 was about. So the pair is not two samples of one quantity;
it is one mechanism observed at two settings of its own gate, which is the only shape that can
answer R44 §6.

⚠️ **The instrument's control comes first.** `scripts/b27/r44_turn_budget.py --selftest` re-derives
R44 from the same corpus and refuses to run otherwise: **15 checks, all reproduced** — 1,306 / 1,070
/ 186, gate 100.0%, CONTROL A 91.0%, CONTROL B 5.9%, 12.7 tok/s, R² 0.9835, medians 1,368 and
22,349, 30 `None`, §6's 266 vs 186, the full `req_in_turn` depth map, plus a negative control (the
gate must *fail* at an absurd 1 s budget: 0/186). A parser that groups turns slightly differently
produces a plausible table on the new run and nothing catches it — the failure mode here is a number
in the right units, not a crash.

## 1. The bound is the knob — measured by intervention, not inferred from a code read

R44 §3 established the gate from `tool_agent.py` plus a correlation at one setting. That cannot
separate *"the gate is `YIELD_SECONDS`"* from *"turns happen to be short."* Moving the knob can.

| run | gate 60 s | gate 180 s |
|---|---|---|
| `v1-1-r2` (Y=60) | **186/186 = 100.0%** ← own | 186/186 = 100.0% |
| `v3-0` (Y=180) | **96/297 = 32.3%** | **297/297 = 100.0%** ← own |

⚠️ **`v1-1-r2`'s 100% at 180 s is arithmetic, not evidence** — every turn under 60 s is under 180 s.
The load-bearing cell is `v3-0` breaking the 60 s bound on **two thirds** of its multi-request turns
while holding the 180 s one without a single violation across 297 turns.

And the bound sits flush against the knob in both runs:

| run | n | max `cum(but last)` | as % of its Y | p95 | median |
|---|---|---|---|---|---|
| `v1-1-r2` | 186 | **59.4 s** | 99.1% | 58.3 s | 31.7 s |
| `v3-0` | 297 | **178.8 s** | 99.4% | 171.0 s | 101.0 s |

## 2. Every mechanistic prediction landed

R44 predicted that raising the budget buys **fewer, deeper** turns inside the same per-game wall.

| | Y=60 | Y=180 |
|---|---|---|
| `analyze()` calls | 1,070 | **719** |
| requests per call | 1.22 | **1.67** |
| turns reaching iteration 2 | 186 | **297** |
| deepest `req_in_turn` | 5 | **6** |
| CONTROL A — 1-request turns whose sole request blew the gate | 91.0% | **62.6%** |
| requests exceeding the budget | 70.5% | **29.9%** |
| median completion ÷ what the budget buys | **1.74×** | **0.60×** |

The last row is the inversion R44 named: at 60 s the model's ordinary reasoning was 1.74× the whole
turn budget; at 180 s the budget is the larger of the two. The lever did exactly what it was built
to do.

## 3. And it bought nothing measurable

`eval/rank_runs.py`, `--selftest` clearing both poles in the same session first:

| baseline | mean | levels | p |
|---|---|---|---|
| `thui-v1-1` 5.24 (its own base) | → 4.01 | 25 → 23 | **0.5370** |
| `thui-v1-1-r2` 4.33 (same base, run 2) | → 4.01 | 23 → **23** | **0.8145** |
| `v10cal` 4.71 | → 4.01 | 28 → 23 | **0.4759** |

All NOT-DISTINGUISHABLE, and 4.01 sits inside the same-build band `[2.82, 5.24]`.
**NOT MEASURABLE, never "no worse"** — at p = 0.54 the −1.23 and a 0 do not separate.

This is the `B34` shape at a second lever: **mechanism confirmed, size at or below the noise.**
Three members of the more-reasoning-per-decision family now read that way — `B25` (MoE), `B34`
(double the clock), `B48` (triple the turn budget).

## 4. 🔴 §6's refusal was right, and the second point makes it worse

R44 refused to build a headroom curve from first-request times because it over-predicted by 43% at
the one value where it could be checked. At the second value it over-predicts by **53%**:

| | predicted | observed | over |
|---|---|---|---|
| turns reaching iteration 2 at Y=60 | 266 | 186 | 43% |
| turns reaching iteration 2 at Y=180 | 455 | 297 | **53%** |

and the cause is the same one, stable across both settings: of the turns the rule wrongly expects to
continue, **95%** (Y=60) and **96%** (Y=180) ended on `tool_calls` — they finished because the agent
did the thing it is supposed to do. **The inflation grows with the budget**, so the curve is not
merely an upper bound, it is a loosening one. Anyone pricing a further increase from first-request
times will over-state it by more than R44's 43%.

## 5. The decode fit doubles as a cross-run control

| | Y=60 | Y=180 |
|---|---|---|
| tok/s | 12.7 | 13.6 |
| R² | 0.9835 | 0.9803 |
| median prompt tokens | 22,349 | 22,349 |

Decode rate is a property of the machine, not of the knob, and it holds to **7%** across two runs a
day apart with an identical median prompt. That is what says the two corpora are commensurable —
without it, every delta in §1–§2 could have been a different serving configuration.

## 6. Not known

1. **This is n=2 runs, not n=2 samples of one setting.** The two differ *by the knob*, so nothing
   here estimates the same-setting spread — and B37 already showed one build's two runs land 0.91
   apart. §3's three p-values are the only noise control available, and they are the weak kind.
2. **`__exception__` rows went 30 → 38** (2.3% → 3.2%). R44 flagged the `ReadTimeout` cluster as
   uninvestigated; it still is, and it is now slightly larger.
3. **Actions per `analyze()` call reads 1.18 → 1.95** — but that ratio crosses two sources
   (`summary.txt` actions over usage-file calls), and R44 §7 established the usage `action` field
   cannot give a per-turn action rate on its own. Treat it as suggestive, not measured.
4. **Why the extra depth converts to nothing** is untouched. The agent deliberates longer per
   decision and clears the same levels; whether the added iterations are redundant, or productive
   but on the wrong sub-goal, needs the transcripts and not the usage rows.

## 7. Reproduce

```bash
python3 scripts/b27/r44_turn_budget.py --selftest
python3 scripts/b27/r44_turn_budget.py \
    "v1-1-r2=60=$HOME/Claude/arc-artifacts/thuiv1-1r2" \
    "v3-0=180=<arc-agi-pub>/notes/runs/thui-v3-0"
```
