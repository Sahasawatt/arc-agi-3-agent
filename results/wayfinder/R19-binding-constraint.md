# R19 — What actually binds v10 (two read-only fan-out lanes, 2026-08-21)

Written after duckv10 drew hidden **1.70** (public band [4.55, 4.71]). Question asked:
**find a lever bigger than prompt tuning**, because every prompt-level change we ever ran LOST
(v12 brevity 3.72 < 4.71; v9 hard 768-token cap 0.22) while every winner was a substrate swap
(model: v8 +37%; bundle: v10 +42%).

Two agents, read-only, over both v10 runs (`duckv10out` = run A, `duckv10cal` = run B) plus the
v8/v12 contrasts. Cited numbers are theirs; the synthesis in section 3 is mine and is labelled.

---

## 1. Lane A — binding constraint per game

**Verdict: 0 of 18 zero-score game-runs is throughput-bound. The split is capability vs scaffolding,
roughly half and half.**

Wallclock discriminates nothing: **all 50 game-runs hit the 7,920s cap within 0.7s** (four run-B
games ran 22-52s *over*). No game finished early, so "give it more clock" has no game to point at.

| class | count | who |
|---|---|---|
| **SCAFFOLDING** | 7/18 | `lf52`-A, `tr87`-A, `g50t`-A, `g50t`-B, `tn36`-A, `tn36`-B, `r11l`-B |
| **CAPABILITY** | 7/18 | `cd82`-A, `cn04`-A, `cn04`-B, `dc22`-A, `sk48`-A, `sk48`-B, `m0r0`-A |
| ambiguous | 4/18 | `ka59`-A, `bp35`-B, `sp80`-A, `tr87`-B |

### The scaffolding mechanism — new, not in R16-R18

A turn that overruns `LOCAL_ANALYZER_YIELD_SECONDS=60` yields
(`"Yielded control to solver: turn_time_budget"`, `"step_executed": false`) and **has no escalation
path**. It retries the same action and yields again. Worst cases:

- **`lf52`-A: 0 of 72 attempts ever executed a step.** 71 `turn_time_budget` yields, the 72nd a
  `request_error ... Read timed out`. `solver_note tokens=105,326` — the entire clock spent, not one
  environment action taken. (`duckv10out/artifacts/lf52-271a04aa_p0_events.jsonl:2,73`)
- **`tr87`-A: 0 of 55 attempts executed.** 104,454 tokens, zero actions.
- **`g50t`**: last real action at 46% (A) / 32% (B) of the clock; the remaining **53.5% / 68.3%** is
  consecutive stuck yields on one action number, ending in a read-timeout.
- **`tn36`**: tail gap **51.8%** (A) and **51.7%** (B) — near-identical across independent runs,
  which argues structural rather than stochastic.
- Read-timeouts observed against the local vLLM endpoint at **900.0 / 652.9 / 513.4 / 320.8 /
  122.6 s**.

WARNING: yields alone are NOT diagnostic — they fire 4-71 times in **all 50** game-runs including
the dataset's top scorer (`ft09`-A, 13 yields, 47.62). What is diagnostic is a 100%-yield game or a
tail gap over 50%.

### The capability cases

Full token budget spent, action count at or near baseline, **~0% of generated tokens unattributed
to a recorded action**, ordinary single cutoff. `cn04`-A used **exactly** its 29-action L1 baseline.
`sk48` and `cn04` are dead in both runs — the cleanest "model does not solve this" pair.

---

## 2. Lane B — inference throughput

**Verdict: not memory- or queue-bound; compute-bound, and prefill is eating decode.**

- KV-cache usage max **85.5%**, **0 preemptions** in 793 samples over 2h12m. Waiting > 0 in only
  6/793 samples, all in the first 90s. Running pinned 25/25 for **87.4%** of the run.
- Aggregate generation **median 338.4 tok/s** (range 268-704). Per-request **13.57 tok/s** —
  about 1.5x better than R10's v5/mod figure of ~9, so v10 already improved here.
- **correlation(prompt tok/s, gen tok/s) = -0.75.** Near-pure-decode intervals average
  **452.5 tok/s**; heavy-prefill intervals average **321.9 tok/s** — a **29% decode tax** whenever
  prefill competes for the same GPU step.
- **Prefix cache hit rate decays 63.8% to 23.2%** across the run, decode falling with it
  (392 to 311-341 tok/s).

### The number the log prints about itself

```
16:07:44 [kv_cache_utils.py:1319] GPU KV cache size: 199,136 tokens
16:07:44 [kv_cache_utils.py:1324] Maximum concurrency for 65,536 tokens per request: 11.32x
```

We run **25** games against a cache sized for **11.32** full-length contexts — oversubscribed
**2.2x**. vLLM states this about itself, unprompted. Weights take 28.51 GiB of a 96 GB card;
`Available KV cache memory: 48.8 GiB`.

### CORRECTION to lane B — `num_gpu_blocks_override=512` is NOT a cap

Lane B reported the override as pinning KV to 48.8 GiB and made "find where 512 comes from, then
raise it" a headline lever. Checked against the raw log, that is wrong, and the correction kills
that lever while leaving the oversubscription finding untouched:

```
16:07:03 [kv_cache_utils.py:829]      Overriding num_gpu_blocks=0 with num_gpu_blocks_override=512
16:07:03 [gpu_model_runner.py:5876]   Profiling CUDA graph memory: PIECEWISE=51 (largest=512), FULL=51 (largest=512)
16:07:44 [gpu_worker.py:436]          Available KV cache memory: 48.8 GiB
16:07:44 [kv_cache_utils.py:1319]     GPU KV cache size: 199,136 tokens
```

The override fires at **16:07:03** inside the CUDA-graph memory profiling path — the very next line
is that pass's own `largest=512` capture size. The real KV allocation happens **41 seconds later**
at 16:07:44 and is derived from available memory. Arithmetic settles it: `199,136 / 512 = 388.9`,
not an integer, so the final cache is not 512 blocks of anything. The 512 is a profiling-phase
placeholder, not a run-time ceiling.

Consequence: **do not go looking for where 512 is set** (lane B's top UNVERIFIED item), and drop
"raise the block override" from the lever list. It caps nothing. The 2.2x oversubscription stands
on the `11.32x` line alone, which is independent of it.

This is the standard delegated-recon failure: a correct inventory of log lines, assembled into a
causal claim the lines do not support. Co-occurrence in one grep is evidence about the query.

Config confirmed: vLLM **0.19.0**, TP=1 (single GPU), `--max-model-len 65536`,
`--enable-prefix-caching` ON, **`kv_cache_dtype=auto`** (i.e. NOT fp8), CUDA graphs on,
`speculative_config=None`, chunked prefill on at 8192.

### Killed by lane B

preemption/thrashing (0 events) · request queueing (Waiting about 0) · tensor parallel (one GPU) ·
cheaper quantization (checkpoint is already FP8, nothing else is mounted offline) ·
`enforce_eager` (graphs already on).

### Killed by lane A

**Reducing concurrency** — there is no starvation to fix. And **efficiency tuning on cleared
levels**: **28 of 50 completed levels already scored the 115 cap** (actions at or under 0.9325x
baseline), so squeezing them buys exactly zero. All remaining upside is in clearing NEW levels.

---

## 3. Synthesis — MY HYPOTHESIS, not established by either lane

Both lanes may be describing **one mechanism**. Neither agent had the other's data.

```
KV 199,136 tok / 25 games = about 7,965 tok per game   (but max-model-len is 65,536)
  -> history outgrows its cache share -> prefix blocks evicted
  -> every turn re-prefills the whole context
  -> turn cannot finish inside the 60s yield budget -> yield -> retry -> re-prefill ...
  -> the 100%-yield death spiral lane A found
```

Eviction of prefix blocks causes **no preemption** — free blocks are silently reused — which is
exactly why lane B saw hit-rate collapse at a flat 79.4% usage with 0 preemptions, and read it as
"KV is not binding". It is not binding for *admission*; it may well be binding for *retention*.

**Corroboration lane B flagged as UNVERIFIED without connecting it:** the two game-runs with
anomalously low generation rates — **`r11l`-B at 6.42 tok/s** and **`sk48`-B at 7.30 tok/s** against
the other 48 runs' 13.2-13.5 — are both in the stuck/scaffolding cluster. A game paying full
re-prefill every turn produces exactly that signature: GPU time goes to prefill, not generation.

**If the hypothesis holds, one change fixes both findings**: the 29% decode tax *and* the 7
scaffolding-dead game-runs.

### Falsifiable prediction

Raise effective KV capacity with **`--kv-cache-dtype fp8`** (about 2x tokens per byte, taking the
stated 11.32x concurrency capacity to roughly 22.6x, i.e. finally covering the 25 games we run) and
**nothing else changed**. A secondary knob is `gpu_memory_utilization`, currently the 0.9 default
against weights 28.5 + KV 48.8 + graphs 0.95 = about 78 GiB of 96 — real but modest headroom.
(The block-override route is dead; see the CORRECTION in section 2.) Then:

1. prefix-cache hit rate should NOT decay to 23% by the end of the run;
2. `lf52` and `tr87` should execute a non-zero number of actions;
3. the low-vs-high-prefill gap (452.5 vs 321.9 tok/s) should narrow;
4. the `r11l`/`sk48`-class low tok/s outliers should disappear.

If hit rate still collapses, the hypothesis is refuted and the scaffolding deaths need the
independent fix below.

### Independent fallback (lane A's own recommendation)

Count consecutive `turn_time_budget` yields on the **same** action number; past a threshold (about
5-8, against the observed 7-16) force a shorter completion for that retry only, or restart the turn
with a trimmed context. This is a **per-retry** cap — R17 already killed a *global* output cap, and
v9 proved why (0.22).

---

## 4. Where this leaves the model lever

Kaggle dataset survey done the same day (offline-mountable, must fit 96 GB):

| candidate | size | note |
|---|---|---|
| Qwen3.8-27B-FP8 dense | 25.3 GB | **what we run — newest in the dense line** |
| Qwen3.6-35B-A3B FP8 | 30.7 GB | MoE, 35B total / **3B active** |
| Qwen3.5-35B-A3B FP8 | 30.7 GB | MoE, older generation |
| Nemotron Cascade 2 30B A3B FP8 | 26.8 GB | MoE, different family |
| llama3-70B FP8 | 59 GB | NO — TRT-LLM engine for H100/GH200, not a vLLM layout, 2024 |

The dense line is **exhausted** — we already hold the newest. MoE is the only remaining model move,
and it is a trade: A3B generates far faster but costs a generation of quality (no 3.8-generation
A3B exists on Kaggle; whether one exists at all is **UNVERIFIED** from here). Measured price of
going back a generation, on the old bundle: 3.6 dense 2.41 vs 3.8 dense about 3.09 — roughly **-28%**.

**Lane A changes the read on this.** 7/18 zeros are capability — a stronger model would help those,
and a weaker-but-faster one would not. Since throughput is NOT what kills any game (0/18), the MoE
trade now looks **wrong**: it pays 28% of quality for speed nobody is starved of.

---

## 5. Recommendation

**Order: KV retention, then yield escalation, then model.**

1. **KV capacity experiment** (section 3 prediction) — one flag, `--kv-cache-dtype fp8`. Costs one
   commit run. Fixes two findings if the hypothesis holds, and refutes it cheaply if not. No
   prerequisite hunt is needed; the `512` blocker turned out not to be one (section 2 CORRECTION).
2. **Yield escalation guard** (section 3 fallback). Independent of 1; targets 7/18 zero game-runs
   directly. Pair it in the same run only if the two changes can be told apart afterwards —
   otherwise run them separately, because R9 says single runs already struggle to rank designs.
3. **MoE model swap** — deprioritised by lane A's evidence. Revisit only if 1 and 2 land and the
   remaining gap is still capability-shaped.

Still UNVERIFIED and worth carrying: whether more budget would flip ANY capability-classified game
(no controlled long-budget run exists); the exact mechanism of the 900s read-timeouts (rambling
generation vs a request that never started); and whether v10's public 4.55 repeats at all (R9).

**Context for sizing any of this:** the top-5 bar is hidden 2.57. At v10's measured shrink of
2.68-2.77x, that needs public **6.9-7.1** against our 4.55-4.71 — a **+47% to +56%** gap.
