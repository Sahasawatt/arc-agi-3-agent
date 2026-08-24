# R35 — the output-token distribution, and the question it turned out not to answer

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

**Answer: there is no cap worth placing** — and the axis was already closed. **B8** recorded
*"duckv9 = 0.22 — the output cap truncates tool calls. R10's cap lever REFUTED"*, and **B12**
closed the cut-reasoning axis in both its forms. What this distribution adds is not the
verdict but its **shape**: the axis was closed by one failed run, and it is now closed
structurally. That still has live value, because **B5 is `open` on the map and its item (a)
is `hard output cap LOCAL_ANALYZER_MAX_OUTPUT ~768`** — the same 768 that produced 0.22.

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

## The clock — CONFIRMATION of R1, not a finding

⚠️ **This section originally read as a discovery. It is not one.** `R1-forensics.md`
established it on 2026-08-19 — *"ALL 25 games cut by the 7,920s per-game wall clock (zero
crashes/surrenders)"* — and R7 restated it as *"binding stop = wall clock only (token
hypothesis refuted)"*. What follows is a fourth independent measurement of a known fact,
which is worth having and is worth nothing as news.

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
run reported. The GPU is saturated and **prefill dominates**.

⚠️ **Do not read that as "slim the prompt to buy actions".** An earlier draft of this note
did, and the map refutes it twice by measurement:

- **B16** — v14 bought capacity and spent it the wrong way: actions 1,285 -> 1,633, levels
  22 -> 19. *"Throughput axis closed."*
- **B25** — v20 fired **7,656 actions (4.7x v10)** and cleared **3 levels against 28**.
  *"throughput was not the bottleneck, reasoning-per-decision is."*
- **B20** — the scorer's second cap, `completion_cap = 100*sum(done levels)/W`, already binds
  on 7 of 25 games and locks 41% of the score; the whole efficiency axis ceilings at **5.80
  public (~2.1 hidden)**, below what top-5 needs. *"Depth is the only axis left."*

So the input-side economics here are a **cost measurement**, not a lever recommendation.
More actions per game is a quantity this campaign has twice bought and twice failed to
convert. Prompt work is only worth a slot if it changes what the model *decides* — which is
what B26/B27/B28 are about, and what v22's ported addendum is a live test of.

## What is NOT a lever, stated so it is not tried

**Lowering `analyzer_timeout` (900 s).** 32 requests died on it, 3.45 h of 54.9 h
request-wall (6.3%), spread across 23 of 25 games rather than clustered. That reads like
free time to reclaim, and it is the trap this repo already has a case for: p95 request wall
is **483 s**, so 900 s is only ~1.9x the slowest honest request. A liveness timeout must
dwarf the slowest legitimate unit; at 1.9x it is already close to scheduled killing, and
lowering it converts healthy long requests into lost turns with a graceful-looking result.

## Where the prompt budget goes — B5(b) is aimed at 20% of it

`B5(b)` on the map reads *"slim the 14.5k-char system prompt (dedupe the 6 addenda, target
<8k)"*. The probe records `prompt_tokens` per request, so the split between the static
preamble and accumulated history is measurable, and it had not been measured.

**Every game's first request is 4,410-4,430 prompt tokens.** All 25, a 20-token spread — that
is the static floor: system prompt + tool schemas + the first board.

| | tokens |
|---|---|
| first request (static floor) | **4,420** median, range 4,410-4,430 |
| median across all requests | 22,274 |
| last request of a game | 24,650 median |
| max seen | 29,686 (window is 32,768) |
| growth per action | **+192** median, per-game slope +51 to +800 |

So the static part is **20%** of the median prompt and ~18% of the last one; the other ~17,900
tokens are accumulated history. Halving the preamble — B5(b)'s target — removes roughly
**2,200 tokens from 22,274, about 10% of the prompt**, and prompt runs 10.7:1 against output,
so ~9% of total tokens.

⚠️ **This is not an argument for compacting history instead.** Both are throughput levers and
the throughput axis is closed by B16 and B25 — capacity has twice converted into more actions
and fewer levels. The finding is narrower and only that: **if prompt-size work is ever done,
B5(b) as written targets the smaller fifth**, and the number to beat is history growth at +192
tokens per action, not the preamble.

Also visible: several games reach 26-29k against a 32,768 window, so retention is running near
the ceiling by the end of a game. What the harness does at that ceiling is not measured here.

## Instrument notes

- `final_uncached_input_tokens` and `final_generated_tokens` are **0 for all 25 games** in
  `benchmark.json`. The probe is the only place this run's token counts exist.
- `summary.txt` reports `total tokens: 2,158,107`; the probe's output sum is **2,461,226**,
  14% apart. Two different quantities, unreconciled — do not mix them in one column.
- The probe cost nothing in score: public **3.20**, inside the `[2.82, 4.71]` band, levels 22
  equal to v10out. `rank_runs.py` on this run's `benchmark.json` confirms it against both
  in-band neighbours: vs **v10cal** delta -1.51 **p=0.3027**, vs **v19** delta +0.38
  **p=0.7579**, NOT-DISTINGUISHABLE both ways. Four samples of v10 now span 1.89, so a
  rerun of this build is the one action that provably teaches nothing.
