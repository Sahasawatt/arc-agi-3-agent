# B69 — the duck solver on a faster serving stack (`thui-fast-v0`)

Opened 2026-09-07, offline, 0 slots, 0 GPU. Build: `thui-fast/build_notebook.py`.

## The claim this build tests

The score this campaign can reach on the duck harness is bounded by **throughput**, not by the
solver: v10cal spends ~124 s per action and gets ~64 actions per game inside the 7,920 s wall
(LEDGER; B40/B45 measured the two waste pools); `clock2x` bought +2 levels by doubling the wall and
can never ship. A serving stack that produces more actions in the SAME wall is `clock2x` in the
form the rules allow.

One public kernel already does this on this exact harness. `keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp`
= Tufa's June duck bundle (`ARC3-Inference aa69123`; `solver.py` and `framework/kaggle.py` are
byte-identical to our anim bundle's — diffed 2026-09-07, 0 lines) with only the serving replaced:

| | ours (Qwen3.8-27B-FP8, vLLM 0.19 wheelhouse) | his |
|---|---|---|
| model | dense 27B, FP8 | `RadixArk/Qwen3.8-Flash-Next-NVFP4` — MoE ~180B total, 512 experts / top-10, NVFP4 experts, 1 MTP layer (135 GB, Kaggle model asset) |
| serving | vLLM 0.19, default scheduler | pinned vLLM image (CUDA 13, 7.9 GB of docker layers as a dataset), **MTP-3 speculative decoding**, async scheduling, chunked prefill, CUDA graphs 32, 8 seqs, prefix caching OFF, KV 5 GiB explicit, PLE CPU-offload patch, owned-server watchdog |
| budget | 7,920 s / game, concurrency 28 | identical (cell 13 asserts it) |
| public 25 (latest log) | v10 band **4.55–4.71**, thui-v1-1 **5.24**, actions 1,285–1,697 | **6.76**, 36 levels, 19/25 scoring, **3,695 actions** (148/game), gen tokens 1.88 M, wall 8,587 s |

Read from his kernel's own `[finished]` lines (`scratchpad/peer_log_stats.py`), not from a claim.
n = 1. Same-build spread on this harness is 0.4–0.5 public, so 6.76 ranks only after a second draw
— but it sits **above every same-wall number this campaign has produced**, and the axis it moves on
(serving) is the one axis never measured on Qwen3.8 here. B6 (the model swap) remains the only lever
that ever moved the score; this is the model lane again, with the throughput lane riding on it.

⚠️ The MoE class was "refuted" by v20 (Qwen3.6-35B-**A3B**, 0.18). That was a 3B-active model; this
one routes 10 of 512 experts on a 180B base. The refutation does not transfer — a different class,
not a rerun.

## What `thui-fast-v0` is

His notebook, cell for cell, vendored as `thui-fast/upstream-keithtyser-duck-qwen3-8-flash-next-nvfp4-mtp.ipynb`
(sha256 `72d6f351…`), with three cells changed and asserted by the builder:

- **cell 0** — our identity first (G2), crediting Keith Tyser (serving), Tufa Labs (duck), RadixArk (weights).
- **cell 1** — Tufa's header reworded in the third person; the submit gate's two hard markers
  (`Tufa Labs ARC3 submission`, `our milestone-winning`) are never legitimate under our slug. Logo
  attachment dropped.
- **cell 3** — `TAAF_MINIMAL_DIAGNOSTICS` = `1` only under `KAGGLE_IS_COMPETITION_RERUN`, so a public
  run writes the per-game `usage` / `events` / transcript sidecars every instrument in `eval/` reads.
  His run had diagnostics off; ours costs whatever the periodic HTML writes cost (anim runs finish
  inside the wall with them on).

Metadata = his (`dataset_sources` ×2, `model_sources` = his model asset, `NvidiaRtxPro6000`) under
`sahasawatt/thui-fast-v0`. Gate pre-checks on the built notebook: `scan_branding` None,
`scan_markdown` [] (upstream controls: non-None / 2 hits).

## Pre-registered read (write before the number is known)

1. **Serving landed** — vLLM log shows `modelopt_fp4`, `speculative-config {"method":"mtp",…3}`,
   `Application startup`, and `PUBLIC25_VLLM_PROFILE name=kv5-bf16-mtp3-c8-cg32`. Watchdog restarts = 0.
   If it does not land, the run measures nothing and the LEDGER row says so.
2. **Throughput** — actions ≥ 2,500 over 25 games (his 3,695; ours 1,285–1,697). Below 2,500 the
   mechanism did not transfer and the score is uninterpretable as a serving result.
3. **Score** — `rank_runs.py` vs `thuiv3-pool` (n=4) paired sign-flip; the B35 floor (+1 level in ≥ 6 of
   25). A single draw inside [4.55, 6.40] is NOT a verdict; two draws pooled is the bar.
4. **Cost** — wall ≤ 8,700 s (his 8,587 s; the notebook budget is 32,400 s, a hidden rerun is
   4 waves × 7,920 s ≈ 31,680 s + startup — the same margin he ships with).

## Not in this build

- The anim-awareness bundle (`jakobbrggen/taaf-kaggle-source-anim-20260807-anim`, our v10 line) is
  NOT here — his bundle is the June duck. Combining anim + Flash-Next is the next build IF this one
  lands; it needs his `serving_setup.py` grafted into our bundle's `setup_commands.json`.
- No breaker, no prompt change, no clock change. One variable.

## Cost and gates

~2.4 h of GPU on `sahasawatt` (quota reset day unknown; the push is the probe). Push =
`python scripts/kaggle_push_kernel.py repos/arc-agi-3-agent/thui-fast` from `arc-agi-pub`.
Submission, if ever: G1–G6 as usual; the hidden shrink for this stack is unmeasured.

## Draw 1 record (sahasawatt/thui-fast-v0 version 1, 2026-09-07 06:27–08:49Z, wall 8,517 s)

Read against the pre-registered read above, from the kernel's own log + `benchmark.json`:

1. **Serving landed** — `PUBLIC25_VLLM_PROFILE name=kv5-bf16-mtp3-c8-cg32` at 4.9 s, `MODEL_IDENTITY_ONLY files=419
   bytes=135253622894` at 114 s, games under way by ~7 min; watchdog restarts 0. One teardown error AFTER the score
   (`serving_teardown.py`: "vLLM teardown did not reach the bounded terminal gate") — cosmetic, the kernel is COMPLETE.
2. **Throughput** — **3,925 actions** (157 / game) ≥ 2,500. `Read timed out` ×24 = one per game at the wall, the base
   class. Mechanism transferred.
3. **Score** — public **8.07 / 36 levels / 20 of 25 scoring** (`PUBLIC25_AUDIT runs=25 actions=3925`). The highest
   public number this campaign has produced, at the same 7,920 s wall (clock2x's 6.40 needed 2×). Per game:
   ft09 4, tr87 4, lp85 3, vc33 3, re86 3, tu93 2, cd82 2, su15 2, ar25 2, eleven games at 1, zero on sc25 / sk48 /
   bp35 / sp80 / g50t.
   `rank_runs.py` vs `thuiv3-pool` (n=4): **+3.68 mean, +11.75 levels, 14 up / 9 down, p = 0.0587** →
   NOT-DISTINGUISHABLE by the stated rule (α 0.05), the closest any single draw has come. vs `v10-pool`: +3.79,
   +12.0 levels, p = 0.1029. **B35 floor met exactly: 6 of 25 games at ≥ pool mean + 1 level** (cd82, ft09, re86,
   su15, tr87, vc33), 2 games at −1 (sc25, sp80). Fixture banked: `eval/fixtures/thui-fast-v0.json`.
4. **Cost** — wall 8,517 s ≤ 8,700 s.

Two run-time facts for the base: this run drew the NESTED `/kaggle/input/competitions/…` layout (his cell 5 hardcodes
it; the two sibling kernels pushed the same hour drew the FLAT layout and died at 6.5 s), and diagnostics-on cost
nothing visible (his run 8,587 s with them off). Draw 2 (`--over`, version 2) is queued behind gemma-v1 / act-v1 —
the pooled n=2 verdict is the bar, not this number.

## Draw 2 record (sahasawatt/thui-fast-v0 version 2, 2026-09-07 09:23–11:35Z, wall 8,699 s) — and the pooled verdict

Same notebook re-pushed with `--over` (version 2). Read against the pre-registered read:

1. **Serving landed** — `PUBLIC25_VLLM_PROFILE name=kv5-bf16-mtp3-c8-cg32` at 5.8 s, `MODEL_IDENTITY_ONLY files=419
   bytes=135253622894` at 170 s, MTP speculative warning present (`num_speculative_tokens > 1`), watchdog restarts 0.
   The same post-score teardown RuntimeError as draw 1 — cosmetic, kernel COMPLETE.
2. **Throughput** — **3,553 actions** (142 / game) ≥ 2,500; 1.91 M generated tokens. `Read timed out` one per game
   at the wall, as in draw 1.
3. **Score** — public **9.32 / 41 levels / 21 of 25 scoring**. Per game: lp85 5, tr87 4, ft09 3, sc25 3, tu93 3,
   vc33 3, ar25 2, dc22 2, ka59 2, re86 2, s5i5 2, ten games at 1, zero on g50t / sk48 / sp80 / tn36.
   Draw 2 alone vs `thuiv3-pool`: +4.93, +16.75 levels, 18 up / 5 down, p = 0.017. B35 floor **8 of 25** at
   ≥ pool mean + 1 (dc22, ka59, lp85, s5i5, sc25, tr87, tu93, vc33), 1 at −1 (sp80).
   Fixture banked: `eval/fixtures/thui-fast-v0-d2.json`.
4. **Cost** — wall 8,699 s, one second under the 8,700 s gate. The margin is gone; a hidden rerun at 4 waves is
   where this bites, and it is his margin as much as ours.

**Same-build control**: draw 1 vs draw 2 — +1.25 mean, +5 levels, 10 up / 7 down, **p = 0.5364**,
NOT-DISTINGUISHABLE — the two draws read as one build, which is what pooling them requires.

**Pooled verdict (the pre-registered bar)**: `pool_runs.py` over the two draws → `eval/fixtures/thui-fast-pool.json`,
mean **8.69 / 38.5 levels**. `rank_runs.py` `thuiv3-pool` (n=4, 4.39 / 24.25) → `thui-fast-pool` (n=2):
**+4.30 mean, +14.25 levels, 17 up / 6 down, 2 flipped, p = 0.002 → DISTINGUISHABLE, BETTER.** vs `v10-pool`:
+4.42, +14.5 levels, p = 0.0193, BETTER. **The first lever of this campaign to clear the stated rule against the
chassis arm** — eleven prompt-side levers and the model swap to Gemma all sat inside the band or below it.
Membership declared in `eval/fixtures/arms.json` (`fast`, two members).

What it does and does not say. It says the serving stack (Flash-Next NVFP4 ~180B MoE + MTP-3 speculative decoding)
converts the same 7,920 s wall into 2.2–2.4× the actions and that those actions buy levels the 27B chassis does not
reach — on the public set. It does not say anything about hidden (R22: OOD, and this stack's shrink is unmeasured), and
it is not the anim bundle. Next build per §Not in this build: **anim + Flash-Next** (our solver on his serving), which
is the first arm that could be submitted as ours rather than as his kernel under our slug.
