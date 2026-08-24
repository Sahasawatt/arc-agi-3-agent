# R28 — the output-token distribution, and the question it turned out not to answer

Measured 2026-08-23 from `yocybercode/thui-v1-0` (v10 + the cell-12 usage probe), the first
run to carry `thuiv1/request_usage_probe.py`. **1,291 rows, 25 per-game `*_usage.jsonl`
files, 0 unparseable.** The probe installed against the real `inference.agent.tool_agent`
and recorded real values — that had never been shown before.

## The probe's own question: where can an output cap sit?

`duckv9` capped `LOCAL_ANALYZER_MAX_OUTPUT` at 768 and scored **0.22**, with `finish_reason`
`length` 704 against `tool_calls` 68 — the cap truncated the tool call that carries the
action. The probe exists to place a cap that trims the tail without repeating that.

This run, uncapped:

| `finish_reason` | n |
|---|---|
| `tool_calls` | 1,246 |
| `__exception__:ReadTimeout` | 32 |
| `stop` | 13 |
| **`length`** | **0** |

`completion_tokens` over the 1,259 requests that returned:

| p50 | p75 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|
| 1,376 | 2,538 | 4,716 | 6,111 | 8,586 | 11,262 |

**Answer: there is no cap worth placing.**

| cap | requests truncated | output tokens saved | % of all output |
|---|---|---|---|
| 2,048 | 428 | 847,994 | 34.4% |
| 4,096 | 159 | 318,137 | 12.9% |
| 8,192 | 19 | 24,173 | **0.98%** |
| 12,288 | 0 | 0 | **0%** |

The reason is structural, not a threshold to tune: **the distribution has no fat tail.** The
top 18.4% of requests hold 50% of the output and the top 44.6% hold 80%. There is no small
set of runaway requests to trim, so every cap that saves meaningfully is cutting the body of
the distribution — which is `duckv9`'s mechanism, at a smaller radius.

Two corrections to what was assumed when the probe was written:

- the probe's own docstring says *"91% of requests want more than 768 tokens"*. Measured:
  **68.4%**.
- `stop` responses — the model finishing without emitting a tool call, i.e. a turn that
  produced no action — are **4x larger** than `tool_calls` (median 5,804 vs 1,352). 13 of
  them, 70,103 output tokens for zero actions. Small, and the one class a cap would help;
  a cap cannot select on `finish_reason`.

## What the data says the constraint actually is

**Every game hit the per-game wall clock.** `final_wallclock_seconds` across all 25 games:
min **7,920**, median **7,921**, max 7,955, against `max_runtime_s_per_game = 7920.0` in the
solver config. All 25 are within 60 s of the cap; none is under 90% of it.

So `state: gave_up` — recorded for all 25, exactly as `v19` reported — is the label the
harness assigns when the per-game clock expires. It is not the agent giving up, and no game
in this run ran out of anything except time.

That makes the score a **throughput** number, and the economics are input-side:

```
input  26,311,101      output 2,461,226      ratio 10.7 : 1
prompt median 22,274 = 68% of ANALYZER_CONTEXT_WINDOW (32,768) before the model writes a token
request median wall 103 s   p95 483 s   concurrency achieved 24.8 (cap 28)
a game gets 7,955 s; at the median that is ~78 requests. Observed: 51.6.
```

13.4 output tok/s per request x 24.8 concurrent ~ 332 tok/s, against the 271.28 tok/s the
run reported. The GPU is saturated. **Prefill dominates**, so the only lever the data
supports for buying more actions per game is prompt size — not output.

## What is NOT a lever, stated so it is not tried

**Lowering `analyzer_timeout` (900 s).** 32 requests died on it, 3.45 h of 54.9 h
request-wall (6.3%), spread across 23 of 25 games rather than clustered. That reads like
free time to reclaim, and it is the trap this repo already has a case for: p95 request wall
is **483 s**, so 900 s is only ~1.9x the slowest honest request. A liveness timeout must
dwarf the slowest legitimate unit; at 1.9x it is already close to scheduled killing, and
lowering it converts healthy long requests into lost turns with a graceful-looking result.

## Instrument notes

- `final_uncached_input_tokens` and `final_generated_tokens` are **0 for all 25 games** in
  `benchmark.json`. The probe is the only place this run's token counts exist.
- `summary.txt` reports `total tokens: 2,158,107`; the probe's output sum is **2,461,226**,
  14% apart. Two different quantities, unreconciled — do not mix them in one column.
- The probe cost nothing in score: public **3.20**, inside the `[2.82, 4.71]` band, levels 22
  equal to v10out. See the ledger row.
