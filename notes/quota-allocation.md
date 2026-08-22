# How to spend the GPU quota — run allocation design

2026-08-21. Produced by running `question-design` over the allocation problem: 30 GPU-h/week,
a commit run costs ~2h12m, so **~13 questions per week and no more**. Every run is one expensive
question, so the test each must pass is: *does every possible outcome, including "no difference",
change what we do next?*

## What was checked and closed first

- **There is no cheap full-eval mode.** R15 already settled it — a rival's "fast-eval" notebook is
  fast *to screen*, not cheap in GPU-hours, and v19's trick of truncating to 3 games + 1 duplicate
  saves nothing either, because the games run **concurrently** and each still runs to the 7,920s
  cap. 4 games and 25 games cost the same wall clock. (`R15-v19-fasteval.md`:18, 27-31)
- **A short-clock run cannot answer the prefix-cache question.** The decay that v14 exists to test
  runs 63.8% → 23.2% *across the whole run*, and the first 13 minutes still average 63.8%. A
  20-minute probe would not reach the phenomenon it is probing.

## The knobs that do exist

From the v14 notebook itself:

- `cell11` — the documented customization hook, "the safe place" to tweak `bm`, `bm.games`,
  `bm.solver`.
- `cell14` — sets **`bm.n_passes = 1`, hardcoded, AFTER that hook**. This is why `significance.py`
  has shipped with the harness all campaign and never been used: the hook cannot reach the value.
  Patchable, and cell 14 is the same class of seam v10/v14 already patch (cells 6, 8, 12).
- `cell14` — reads `budget = getattr(target, "max_runtime_s", ...)`, so the per-game clock is
  settable from inside the notebook.

**CORRECTION (2026-08-22): the smoke run needs no notebook patch at all.** This note originally
said a short-clock run required patching cell 14. `kaggle kernels push --help` lists exactly three
options — `-p/--path`, `--accelerator`, and:

```
-t TIMEOUT, --timeout TIMEOUT
        Limit the run time of a kernel to the given number of seconds.
        The global maximum time will not be exceeded.
```

So `kernels push -p . -t 900` is the entire smoke mechanism. The claim that cell 14 had to be
patched was never checked against the CLI's own help — and the cost of not checking was real: v14
version 1 spent a full launch to discover an `IndentationError` that a 15-minute smoke would have
surfaced for ~0.1 of a slot.

## The allocation

### 1. Smoke first, on a short clock — `kernels push -p . -t 900`, about 0.1 of a slot

**Every push creates a new kernel version; there is no overwrite.** `kernels push` exposes no
amend/replace flag, so each attempt is permanently numbered. That makes a cheap smoke strictly
better than a careful build: the version number is spent either way, only the GPU time differs.


`v7` died with `ERROR` **twice**, burning two full slots on a build that never ran. A short-clock
run verifies wiring end to end: for v14 the KV flag is applied at vLLM launch and appears in the
server log within minutes, so a 20-minute run confirms `kv_cache_dtype=fp8`, the fire-guard's
`duckv14 injected` line, and that the kernel starts at all.

It does **not** measure score or prefix decay, and must never be read as if it did.

### 2. Then the paired question, on the full clock

R9's finding is the binding constraint on everything below: **a single run cannot rank two
designs.** v10's own band [4.55, 4.71] took two runs. So the real exchange rate is:

> **1 rankable answer = 2 slots.** 13 slots/week = **6 rankable answers per week**, maximum.

Which means breadth is not available. Running 13 different designs once each produces 13 numbers
and zero rankings — the exact mistake R9 was written to prevent.

### 3. Reading order is pre-registered, and this is not optional

v14's outcome space has two independent axes, and one quadrant is a trap:

| | score up | score flat or down |
|---|---|---|
| **hit rate held** | hypothesis confirmed end to end | mechanism is real but was **not costing score** — kills the KV lever, and refutes the link R19 drew from eviction to the scaffolding deaths |
| **hit rate still collapsed** | score moved for some other reason — **confounded, the worst quadrant** | fp8 did not buy retention: either it does not double effective capacity here, or eviction is not capacity-driven |

All four teach something, so the question is well-formed. But the bottom-left quadrant is only
visible if the **vLLM log is read before the score**. Reading the score first makes a confounded
result indistinguishable from a confirmation. Pre-register: *log, then score.*

### 3b. Can the four predictions actually be READ? — three of them could not, as written

Run before paying: `verification-layers` over each of R19's v14 predictions, asking not "is it
true" but "would the artifacts a run returns let us tell".

| # | prediction | verdict | why |
|---|---|---|---|
| P3 | low-vs-high-prefill decode gap (452.5 vs 321.9 tok/s) narrows | **CLEAN** | computed from the `Engine 000: Avg …` lines; v10's own log is the baseline; hundreds of samples per run, so not a lottery |
| P1 | prefix hit rate does not decay to 23% | **needs a stated condition** | see below — the stat is cumulative |
| P2 | `lf52` and `tr87` execute a non-zero number of actions | **NOT a discriminator as written** | `lf52` executed 0 actions in run A and **scored 1.82 in run B**. The marker is already present in both states, so v14 can satisfy it by luck. A marker only discriminates if it appears in exactly one of the two worlds |
| P4 | the `r11l`/`sk48` low-tok/s outliers disappear | **same lottery flaw** | n=1 per game per run, and R9 says per-game outcomes swing between identical-code runs |

**P1's hidden condition, measured from v10's own log.** vLLM's "Prefix cache hit rate" is a
**cumulative average since server start**, not a rolling window — proved by the step-size decay:
mean `|Δ|` per sample is 0.52 over samples 1-100, 0.053 over 300-400, and **0.041** over 690-790,
i.e. it shrinks **12.7×** while n grows **14.8×** — the 1/n signature. (793 samples,
`duckv10out/vllm-openai-server.log`.)

Three consequences:

1. The 63.8% → 23.2% decay is real but **understates** the problem: dragging a large-n lifetime
   mean down to 22.2 requires the *instantaneous* late-run rate to sit well below that.
2. A cumulative endpoint is comparable across runs **only when the runs have similar length and
   request count**. v10 and v14 share 25 games and the same 7,920s cap, so it holds — but it holds
   by coincidence of configuration, and must be asserted at read time, not assumed.
3. A better instrument is free: **de-cumulate**. Differences between consecutive samples recover
   the instantaneous rate, and its trajectory is a sharper signal than the final number.

**Fix P2 and P4 before running.** Replace the per-game markers with population statistics that
have many samples per run:

- instead of "`lf52` executes actions": **the count of game-runs with a >50% dead tail**, and the
  **total fraction of clock spent in stuck-yield tails across all 25 games**. R19 measured both for
  v10 (7 of 18 zero-runs; tails of 51.7-68.3% on the affected games), so the baseline exists.
- instead of "the two low-tok/s outliers disappear": **the spread of per-game tok/s across all 25
  games** (v10: 48 of 50 game-runs at 13.2-13.5, two at 6.42 and 7.30). A distribution moves on
  evidence; two named games move on luck.

### 4. v13 does not earn a slot

`duckv13` (animation-retrieval discipline) sits on the prompt axis, which is **0 for 2** measured
(v9 0.22, v12 3.72). Its outcome space is asymmetric: a win would be genuinely informative — the
axis is not dead — but a loss is the third confirmation of something already established twice.
A question whose "no" branch teaches nothing is half-wasted, and half of two slots is a slot.

Hold it until the harness-level candidates are spent.

## Recommended order

| # | run | clock | slots | question it answers |
|---|---|---|---|---|
| 1 | v14 smoke | ~20 min | ~0.2 | did the flag land, does the kernel start |
| 2-3 | v14 paired | full | 2 | does KV retention change the mechanism, and does that move score |
| 4-5 | v16 paired | full | 2 | does pushing the diff cut the indexing waste, and does that move score |
| — | v13 | — | — | held: losing axis, asymmetric payoff |

That is ~4.2 of 13 weekly slots for two rankable answers plus wiring insurance, leaving room for
whatever those answers open up.

## Open

- **`n_passes` > 1 versus two separate runs.** Same total games and therefore the same quota, but
  multi-pass produces the paired structure `significance.py` expects instead of two loose numbers.
  Worth patching cell 14 for that reason alone — UNVERIFIED whether the harness's own aggregation
  handles n_passes>1 cleanly on this bundle.
- ~~**The exact short-clock value.**~~ **MEASURED** from v10's own logs:

  | milestone | clock | source |
  |---|---|---|
  | kernel start → vLLM launched | ~1m34s | `taaf-duck-v10.log`, `Starting vLLM OpenAI server` at t=93.9s |
  | vLLM process first log line | 16:03:23 | `vllm-openai-server.log:1` |
  | **KV cache allocated** (`kv_cache_dtype` readable) | 16:07:44 | `:1319` — **~5m50s from kernel start** |
  | first request served | 16:08:26 | `:145`, first `Engine 000: Avg …` — **~6m37s** |

  So the v14 flag is verifiable at **under 6 minutes** and "it boots and serves" at **under 7**.
  A **12-minute** smoke is comfortable, not 20 — roughly **0.1 of a slot**, cheaper than the
  earlier estimate and far cheaper than v7's two lost full slots.
