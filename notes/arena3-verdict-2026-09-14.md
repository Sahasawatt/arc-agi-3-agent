# ARENA 3 verdict — four axes, two refuted, one serving lever with a KV wall in front of it, and a one-line lever nobody proposed

**2026-09-14.** Four sonnet competitors, one assigned axis each, no contact; one sonnet refuter per proposal, paid to
kill it; judge = the main session, which re-ran every number below. Brief: `scratchpad/ARENA3.md`; artifacts
`scratchpad/arena3/<axis>/{proposal,refutation}.md` with every script. **Scoring rule, fixed before launch:** the
frozen scorer (`eval/oracle_ceiling.py`, 24/24 against the LEDGER) re-scores the control arm
`thui-l1-ctl-full25-r1` (8.6427) under the assumption that every level in the lever's MEASURED population is cleared
at that population's own median spent/human — a ceiling, never a prediction. Cost: 8 agents, **2,073,598 tokens**
(the launch estimate was ~1 M — a 2x miss, recorded), 37.5 min, 280 tool uses, 0 GPU, repo tree untouched.

This is the first arena in the campaign scored on the shipped chassis: the Flash-Next per-level harvest
(`notes/flash-census-harvest-2026-09-14.md`) landed the same day, so "population" and "ceiling" are computed, not
argued. Follows R56/R57 (the peer lineage's arenas 1 and 2).

## Standings after refutation

| axis | lever | ceiling on ctl 8.64 | population | refuter | judge |
|---|---|---|---|---|---|
| **B serving** | `TAAF_VLLM_MAX_NUM_SEQS` 8 -> 16/28 (solver concurrency is 28; vLLM admits 8) | **+6.84** (-> 15.48) | 17 STARVED game-runs, median eff 0.561 | SURVIVES | reproduced; feasibility gated by KV (below) |
| A harness | dwell T=90 + code-computed coverage ledger in the prompt | +0.84 (-> 9.49) | 4 game-runs (behind-frontier AND spent >= 90) | SURVIVES | reproduced; its refuter found a cheaper root cause (below) |
| C draw variance | plateau-triggered per-game wall reallocation | +2.30 (-> 10.94) | 5 | **REFUTED** — DEAD-list item (early-exit / budget return; B36 closed it) | agreed |
| D transfer | L2-live: dwell(T=90) redirect line in the prompt | +0.94 (-> 9.58) | claimed 8 | **REFUTED** — the 8 credited games never reach 90 actions on the stall level in the ctl run; self-consistent ceiling +0.16 / +0.05 | agreed |

Every `file:line` in all four proposals was opened by the refuters and holds (35 of 35). The two refutations are
about population and rules, not about fabricated mechanisms.

## B — the winner on the number, and the judge's own discriminator

The claim: with 25 games in flight and `--max-num-seqs 8`, every analyzer turn queues for a slot, and the per-turn
wall has a ~140 s floor that barely moves with output length (competitor: turns under 800 output chars still take a
median 138 s; wall-vs-chars r = 0.50). The refuter's objection: that does not separate **admission queueing** from
**prefill compute** (prefix caching is OFF in the shipped profile, so every turn re-prefills up to 32,768 tokens at
8,192 per chunk), and the two have opposite remedies.

Judge's independent read, from the fast-v0 d2 events and L4's measured rates: **median wall per analyzer turn
152 s** (p25 129, p75 176; 1,303 turns); ~1,553 harness tokens per turn; at L4's per-request rates (130 tok/s at
c=1, 52.7 at c=8) generation explains **12-29 s of the 152** — a **~125-140 s residual per turn** that is not
generation. Prefill of a ~10 k-token context on this card is seconds, not a hundred; so the magnitude favours
queueing, and the refuter is right that only the bench separates them.

**The wall in front of it, read from vLLM's own server log** (`kout-sa-thui-fast-v0-d2/vllm/vllm-openai-server.log`,
neither competitor nor refuter opened it):

```
Model loading took 81.8 GiB memory
Initial free memory 94.43 GiB, reserved 5.0 GiB memory for KV Cache as specified by kv_cache_memory_bytes config
  and skipped memory profiling
GPU KV cache size: 105,202 tokens, Maximum concurrency for 32,768 tokens per request: 3.21x
```

So the shipped profile holds **105 k KV tokens = 3.2 full-context sequences**, ~10 sequences at a realistic 10 k
context. `max-num-seqs 8` is not an arbitrary cap; it is where the 5 GiB KV runs out. Raising seqs alone will
preempt. What is genuinely available: after weights (81.8) + KV (5.0) + graphs (0.36) there is on the order of
**7 GiB free** of the 94.4, so KV can plausibly go to ~10 GiB (~2x tokens, ~6.4x of 32 k) — and memory profiling
was skipped, so nothing ever measured whether it can. **That is the lever: KV budget and max-num-seqs together, with
preemptions read.** The bench that decides it is the existing `thui-l4` kernel with a concurrency-25 phase and three
new arms; PASS/FAIL pre-registered in its builder.

## The lever nobody proposed: A's refuter found it in A's own trace, and the judge confirmed it in code

`inference/agent/tool_agent.py:1113-1126` — `_update_summarized_knowledge_from_step_summary` erases **world_model,
goal_model, action_model, recent_findings, open_questions, current_plan** whenever the last step summary carries
`level_transition`, `run_complete` **or `game_over`**. `game_over` is set at `framework/solver.py:718` from
`GameState.GAME_OVER`, i.e. a within-level failure, after which `_execute_auto_reset` (`:663`) RESETs the level. So
every time the agent dies inside a level, the harness throws away everything it had written down about that level and
restarts it from prose memory of nothing.

Population, counted from the events (0 GPU): **fast-v0 d2: 32 within-level game-overs, 26 of them on the level the
run died on, in 9 games** (sp80 x7, tu93 x7, bp35 x5, tn36 x4 ...); **a7-v1 d2: 36, 33 on the dying level, in 8
games** (r11l x16, tu93 x8, sp80 x4 ...). Ceiling with the same rule as the arena (dying level cleared at the
Flash-family median eff 0.80): **fast-v0 d2 9.32 -> 12.07 (+2.75, +9 levels); a7-v1 d2 8.23 -> 11.27 (+3.03, +8
levels).** Second on the number, first on cost: the fix is a guard clause — wipe on `level_transition` or
`run_complete`, keep the knowledge on `game_over`. It rides the same graft seam L1 used (cell 9, wrap the imported
method), and its 0-GPU teeth are the same shape.

⚠️ Unproven, and the instrument that cannot see it: whether keeping a wrong world model across a reset helps or
hurts — the knowledge erased might be exactly the hypothesis that killed the level. Only a smoke on the wipe-heavy
games (r11l, tu93, sp80) vs control says, and the L1 smoke already taught what a 3-game single draw can and cannot
resolve (nothing under ~4 public points; only a mechanism-fires + no-regression read).

## What the arena did not do

No ticket closed, no MAP row, no slot spent, no build pushed. The ceilings are ceilings. The judge's ranking is by
reproduced number, then by cost: **B's Phase-1 bench first (~1 GPU-h, no games), the wipe guard second (0 GPU to
build, one 3-game smoke to read).** Both need the owner's OK.

## Addendum, same day — the wipe guard is built (0 GPU)

`thui-wm/build_notebook.py` grafts the guard as one wrapper on the imported `ToolAgent` (cell 9, L1's seam), with
`--control`. Smoke arms `thui-wm-v0` / `thui-wm-ctl` built for tu93 / sp80 / r11l at 1,800 s. `thui-wm/test_wm_graft.py`
executes the notebook's own cell-9 source against a stub whose original really wipes: ALL TEETH PASS (signature by ast,
the upstream wipe condition present verbatim, class-carries-wrapper control, and five cases — game_over alone KEPT with
marker; level_transition, run_complete, and game_over+level_transition WIPED; no flag untouched). Pre-registered read in
the builder docstring. Not pushed.


## Addendum, same day, 18:48 — Bench Phase-1 arms a v2 + s16 ran (1 GPU-h so far): axis B is REFUTED at the serving layer

Same kernel, same three real prompts (21-24k chars), max_tokens 2048, phases c8 (24 req) and c25 (50 req), preemptions read from
`vllm:num_preemptions_total`; `max_num_seqs` confirmed from vLLM's own non-default-args line and `vllm-server-identity.json`.

| arm | seqs | c8 agg tok/s | c8 median req | c25 agg tok/s | c25 median req | acceptance | preemptions |
|---|---|---|---|---|---|---|---|
| a v2 | 8 | 339.1 | 40.9 s | 359.3 | 114.3 s | 0.43 / 0.44 | 0 / 0 |
| s16 | 16 | 328.0 | 40.3 s | 360.9 | 136.6 s | 0.43 / 0.44 | 0 / 0 |

Pre-registered ALIVE = c25 aggregate > 395 tok/s (baseline x 1.10) with preemptions 0. s16: **+0.4%**, NOT ALIVE. The card is
saturated at ~360 tok/s aggregate from concurrency 8 upward; admitting 16 only lengthens every request (114 -> 137 s median at c25).
So the judge's discriminator resolved the refuter's split — the residual IS queueing, not prefill — and at the same time killed the
lever: the queue is a symptom of decode throughput, not of the admission cap, and the +6.84 ceiling assumed throughput that does not
exist. KV was never the binding constraint at 16 (0 preemptions), which also answers the "seqs and KV together" hedge: moving them
together moves nothing. Remaining arms (s28, k10s16) can only confirm saturation and settle the 10 GiB KV fact; neither can revive B.

Standings after this: A (+0.84, harness) survives untested; the wipe guard (smoke PASS, full-25 A/B built, draw planned 09-15) is
the only lever with a live measurement path.

## Correction, same day, 19:55 — the s16/s28 arms never moved the binding knob; KV did all the binding

| arm | seqs | c25 agg tok/s | c25 median req | max `Running` | max `Waiting` | KV usage while waiting | preemptions |
|---|---|---|---|---|---|---|---|
| a v2 | 8 | 359.3 | 114 s | **5** | 20 | 88-93% | 0 |
| s16 | 16 | 360.9 | 137 s | **5** | 20 | 88-94% | 0 |
| s28 | 28 | 356.2 | 122 s | **5** | 20 | 74-93% | 0 |

Read from vLLM's own periodic `Running/Waiting/KV usage` lines in each server log. The addendum above concluded "the card is
saturated"; that inference is withdrawn — the admitted count was 5 in every arm because the 5 GiB KV fills at ~5 sequences of ~8k
tokens, so the three arms measured the same configuration three times. Preemptions stayed 0 because vLLM v1 admits only what fits;
a KV-bound server queues silently. Axis B is therefore **not refuted, and not confirmed**: its live form is "KV budget", exactly the
judge's hedge, and the only arm that tests it is k10s16 (KV 10 GiB, seqs 16) — built, not run. Pre-read for it: `max Running` ≈ 10
and c25 aggregate > 395 with 0 preemptions = ALIVE (ceiling arithmetic reopens with the measured admitted-count ratio); `Running`
still 5, or an OOM at startup = the KV path is closed and B dies for real. Why 5 × ~8k tokens fills a "105,202-token" KV is
unverified (hybrid linear-attention state per sequence is the hypothesis); the arm answers the question without needing the why.

## Addendum, 20:34 — k10s16 OOMs at warmup; Phase-1 closes with axis B alive only in the (5, 10) GiB KV gap

KV 10 GiB reserved fine (210,405 tokens, 6.42x of 32k) and then vLLM died in kernel warmup with 42 MiB free — weights 81.8 + KV 10
leaves ~2.6 GiB, and the Gated-DeltaNet warmup (`chunk_gated_delta_rule_fwd`) needs more. The four pre-registered arms are done:
a v2 359 tok/s at c25 with 5 admitted; s16 and s28 identical because the cap never bound; k10s16 refused to start. What Phase-1
established: the binder is KV, not admission, at this profile; 10 GiB is too much; nothing between 5 and 10 has been tried. One more
15-minute arm (k7s16: KV 7 GiB) is the last cheap probe — if `Running` reaches ~7 and c25 aggregate clears 395 with 0 preemptions,
the lever is real at roughly +40% admitted turns and the ceiling gets recomputed from that ratio; if not, B closes.

## Final addendum, 21:20 — k7s16 OOMs at the first batched prefill; axis B is closed on this card

| arm | KV | seqs | outcome |
|---|---|---|---|
| a v2 | 5 GiB | 8 | 359 tok/s at c25, 5 admitted |
| s16 / s28 | 5 GiB | 16 / 28 | 361 / 356, still 5 admitted — cap never bound |
| k10s16 | 10 GiB | 16 | OOM in kernel warmup (42 MiB free) |
| k7s16 | 7 GiB | 16 | server up, warm request fine, OOM at the first c8 batched prefill (`_short_conv_dilated_prefill_batched`, 248 MiB free) |

Measured per-sequence KV cost: one 8.3k-token request = 12.9% of 147,456 KV tokens ≈ 19k, i.e. 2.3x its length — the hybrid
model's per-sequence state, which is why 105k "tokens" holds five sequences. The headroom the shipped profile leaves (~7 GiB) is
consumed by batched prefill activations, so KV cannot grow without shrinking prefill (`max_num_batched_tokens`), a knob nobody
proposed and whose upside is bounded by ~+40% admitted turns. B is closed: the +6.84 ceiling had no memory to run on. Total Phase-1
cost: 5 arms, ~1.3 GPU-h, 0 slots. Surviving levers: A (+0.84, untested) and the wipe guard (smoke PASS, full-25 draw 09-15).

**Addendum 2026-09-15 01:20 — "B is closed" was scoped to MTP-3 and did not say so. Arm `mtp0k7s16` reopens it.**
The paragraph above measured every arm with `TAAF_VLLM_MTP_TOKENS=3`. B78's full-25 at MTP 0 (4,049 actions vs 3,553 at MTP 3,
LEDGER) and the bench's acceptance of 0.43 said the draft head was buying little; the sixth arm asked what it was costing. At MTP 0
the same 7 GiB holds **263,568 KV tokens** (147,456 at MTP 3): per-sequence KV measured ~10.4k tokens (n=31) against ~19k at MTP 3 —
the draft head was half the per-sequence state, and its activations were the prefill OOM too (no OOM at any phase here). Numbers:
c8 392 tok/s (+16% vs 339), c25 **570 tok/s (+59% vs 359)**, median request at c25 **58.6 s (vs 114.4 s)**, preemptions 0; `max
Running` = 16 = the cap, KV at 67% — the seqs cap binds again with room for ~25. So the memory the +6.84 ceiling "had none of" was
being spent on speculation with a 0.43 acceptance. What this does NOT show: score. It halves the per-request wait at c25 on a
synthetic mix; a full-25 draw at mtp0+k7+s28 (built next, `mtp0k7s28`, seqs = solver concurrency) is the instrument, and it competes
for the same slots as the wipe-guard A/B. The 18:48 and 21:20 readings both stand as written for MTP-3.
