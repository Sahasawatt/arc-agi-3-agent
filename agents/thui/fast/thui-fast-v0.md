# thui `fast v0` — public 8.07 / 9.32, pooled p = 0.002 BETTER; the duck solver on Keith Tyser's Flash-Next serving stack

## The one change

Nothing in the solver. `sahasawatt/thui-fast-v0` is Keith Tyser's public kernel
[`duck-qwen3-8-flash-next-nvfp4-mtp`](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp)
run cell for cell on our slug — Tufa's June duck bundle (`ARC3-Inference aa69123`, no anim awareness) with the
model serving replaced: `RadixArk/Qwen3.8-Flash-Next-NVFP4` (~180B MoE, 512 experts / top-10, NVFP4 experts,
1 MTP layer; his 135 GB Kaggle model asset) on a pinned vLLM image with **3-token MTP speculative decoding**,
async scheduling, chunked prefill, CUDA graphs, prefix caching off, KV 5 GiB, a PLE CPU-offload patch and a
server watchdog. Budget 7,920 s / game, concurrency 28 — identical to every run in the LEDGER.

Our three edits, asserted by `thui-fast/build_notebook.py` against the vendored upstream copy: cell 0 (our
identity first, crediting him / Tufa / RadixArk), cell 1 (Tufa's header in the third person — the submit gate's
hard markers), cell 3 (full diagnostics on a public run). Design + pre-registered read: `notes/B69-flash-next-serving-design.md`.

## Where it lives

- Builder / notebook / metadata: `thui-fast/` (`upstream-*.ipynb` = his notebook, sha256 `72d6f351…`).
- Kernel: `sahasawatt/thui-fast-v0` — version 1 = draw 1 (2026-09-07 06:27–08:49Z), version 2 = draw 2 (09:23–11:35Z).
- Fixtures: `eval/fixtures/thui-fast-v0.json` (draw 1), `thui-fast-v0-d2.json` (draw 2), `thui-fast-pool.json` (the pooled arm); membership in `arms.json` → `fast`.
- His datasets: `keithtyser/duck-qwen38-nvfp4-mtp-vllm-smoke-v1` (source bundle + `serving_setup.py`),
  `keithtyser/qwen38-flash-next-vllm-nvfp4-runtime-v1` (vLLM image layers), model asset
  `keithtyser/qwen3-8-flash-next-nvfp4/PyTorch/radixark-modelopt-fp4/1`.

## What it scored

| draw | public | levels | scoring | actions | gen tok | wall |
|---|---|---|---|---|---|---|
| 1 (v1) | **8.07** | **36** | 20 / 25 | **3,925** (157 / game) | 1.90 M | 8,517 s |
| 2 (v2) | **9.32** | **41** | 21 / 25 | **3,553** (142 / game) | 1.91 M | 8,699 s  — submitted 2026-09-07 17:10Z as `56081325`, hidden pending |
| pooled | **8.69** | **38.5** | — | 3,739 | — | — |
| his own latest log | 6.76 | 36 | 19 / 25 | 3,695 | 1.88 M | 8,587 s |

Per game (draw 1): ft09 4, tr87 4, lp85 3, vc33 3, re86 3, tu93 2, cd82 2, su15 2, ar25 2; m0r0 ka59 cn04 r11l
s5i5 wa30 tn36 sb26 dc22 lf52 ls20 at 1; sc25 sk48 bp35 sp80 g50t at 0.

`rank_runs.py` vs `thuiv3-pool` (n=4): **+3.68 mean, +11.75 levels, 14 up / 9 down, p = 0.0587** —
NOT-DISTINGUISHABLE at α 0.05, the closest any single draw of this campaign has come. vs `v10-pool`: +3.79,
+12.0 levels, p = 0.1029. **B35 floor met exactly**: 6 of 25 games at ≥ pool mean + 1 level (cd82, ft09, re86,
su15, tr87, vc33); 2 games at −1 (sc25, sp80).

## Verdict

**DISTINGUISHABLE, BETTER — the first lever of the campaign to clear the stated rule against the chassis arm.**
Two draws pooled (`pool_runs.py`, 8.69 / 38.5 levels) vs `thuiv3-pool` (n=4, 4.39 / 24.25): **+4.30 mean,
+14.25 levels, 17 up / 6 down, p = 0.002**; vs `v10-pool` +4.42, p = 0.0193. Draw 1 alone was p = 0.0587, draw 2
alone p = 0.017, and the two draws are one build (d1 vs d2 p = 0.5364). B35 floor 6/25 then 8/25. Mechanism verified
in both logs (profile landed, model identity 419 files, MTP-3 on, 2.2–2.4× our action count).

What it is not: not the anim bundle (his base is the June duck — **anim + Flash-Next is the next build**), not a
hidden number (the shrink for this stack is unmeasured; a submission is the owner's call and shares the daily slot),
and not a lever we authored — every score here rides on Keith Tyser's serving work and Tufa's solver, credited in
cell 0. Cost note: draw 2's wall was 8,699 s against an 8,700 s gate; the margin his stack ships with is one second.

Two infrastructure facts worth carrying: draw 1 drew Kaggle's NESTED `/kaggle/input/competitions/…` layout,
which his cell 5 hardcodes — the two sibling kernels pushed the same hour drew the FLAT layout and died at 6.5 s
(the `solo/` trap; fixed in `thui-gemma` / `thui-act`, still latent here and in every `thuiv3` arm); and
`serving_teardown.py` raised "did not reach the bounded terminal gate" after the score in both draws — cosmetic,
kernel COMPLETE.

## Read next

- `notes/B69-flash-next-serving-design.md` — the claim, the serving diff table, the pre-registered read, the draw-1 record
- `notes/LEDGER-all-runs.md` — where 8.07 sits against every other run
