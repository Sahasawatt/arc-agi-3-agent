# B64 — Gemma-4-31B-it as the duck agent: the one model-swap candidate with the right shape

**Design ticket, 2026-09-03.** From `arc-agi-pub/notes/deep-research-arc3-model-swap-2026-09-03.md`
(wf_76d8b5a0-27b): no open-weight model has evidence of beating Qwen3.8-27B-FP8 inside duck; of the
candidates that fit one 96 GB card, Gemma-4-31B-it is the only one whose *shape* matches what won here —
dense (B25's small-active-MoE kill does not apply), multimodal (the 4x board image is a first-class
input), 62.6 GB BF16 on Kaggle Models, and it is what Reki (#2) and forge (#3) ran in Milestone 1.
Evidence strength: **weak, structural** — nobody has run it inside duck, anywhere.
Status: design → serving smoke (in-kernel, before any game) → 3-game smoke → decide.

Proposed MAP row:

> | B64 | build | **Model swap to Gemma-4-31B-it inside the unchanged duck harness.** The model-swap lane is the only lever that ever gained (B6, 2.41 → 4.55); the 2026-09-03 research closed Flash-Next (135 GB, does not fit) and gpt-oss-120b (5.1B active = B25's dead class), leaving one dense multimodal candidate with zero in-harness evidence. Two measured blockers are part of the build: the pinned wheelhouse cannot load Gemma 4 (vLLM 0.19.0 / transformers 4.57.6; needs >= 0.19.1 / >= 5.5) and the vLLM flags are Qwen-specific. Oracle unchanged: paired levels vs the same-seed base pair. | open |

## Blockers measured before writing a line ($0)

| fact | source |
|---|---|
| Gemma 4 support landed in vLLM **0.19.0** (2026-04-02) but the PyPI 0.19.0 pins `transformers<5` while Gemma 4 needs `>= 5.5`; the recipe's minimum is **0.19.1** | vllm-project/vllm#39216; recipes.vllm.ai/Google/gemma-4-31B-it |
| our wheelhouse `driessmit1/arc3-vllm-h100-wheelhouse-v3`: `vllm-0.19.0`, `transformers-4.57.6`, `torch-2.10.0`, flashinfer 0.6.6 | `kaggle datasets files` |
| `ko0kip/vllm-0230-offline` (192 files, used by the public Gemma-4-31B reflection agent): `vllm-0.23.0`, `transformers-5.12.1`, `torch-2.11.0`, `triton-3.6.0`, no flashinfer, **no `requirements.lock`** — wheels under `vllm_0230_offline/wheels/` | `kaggle datasets files` |
| Kaggle model `google/gemma-4/transformers/gemma-4-31b-it/1`: 21 files, **62.6 GB** BF16; mounts under `/kaggle/input/models/...`, which the bundle's dataset resolver never probes | `kaggle models instances versions files` |
| duck's launch flags are Qwen-specific: `--tool-call-parser qwen3_coder`, `--reasoning-parser qwen3`, `--default-chat-template-kwargs {"preserve_thinking": true}` | `framework/kaggle.py:326-333`, rendered into `setup_commands.json` |
| vLLM ships `gemma4` tool-call and reasoning parsers; the recipe recommends `--enable-auto-tool-choice --reasoning-parser gemma4 --tool-call-parser gemma4 --limit-mm-per-prompt {"image": 4, ...}`; thinking per request via `chat_template_kwargs.enable_thinking`, which duck already sends | vLLM docs + recipe |
| duck keeps up to 30 assistant turns of history and every user turn carries a board image, so one prompt can hold far more than 4 images (Qwen runs: MM cache hit 93–95 %) | `tool_agent.py:151`, `_build_user_message`, vLLM logs |

## Seam (builder `thui-gemma/build_notebook.py`, four cells)

- **cell 6** — `DATASET_SOURCES` = bundle + `ko0kip/vllm-0230-offline` (Qwen snapshot and the old wheelhouse dropped); the model mount is asserted to exist (and to carry `config.json`) and mapped as `google/gemma-4-31b-it` into `TAAF_KAGGLE_INPUT_PATHS`, the map the bundle's resolver reads first.
- **cell 8** — eleven string rewrites on the rendered setup command, applied after thui-v1-1's own chain, each asserted in-kernel to hit **exactly once**: model owner / slug / served name → `google/gemma-4-31b-it`; wheelhouse owner / slug → ko0kip; stamp text; the installer's `requirements.lock` read → install `vllm==0.23.0 transformers==5.12.1` by name from the wheels dir; `qwen3_coder` → `gemma4`; `qwen3` → `gemma4`; `preserve_thinking` → `--limit-mm-per-prompt {"image": 32}` + `--quantization fp8`. The builder replays the whole chain against the vendored `setup_commands.json` and `ast.parse`s the rewritten setup script, so bundle drift fails at build time, not on the GPU.
- **cell 14** — the usual 3-game filter.
- kernel metadata: `dataset_sources` = bundle + wheels, `model_sources` = the Gemma model.

Nothing in the harness, prompts, seed (20260825), temperature (0.6), yield, upscale or clock changes —
thui-v1-1's own in-kernel teeth still assert all of them.

**Why online FP8 weights.** 62.6 GB BF16 leaves ~24 GB of KV at 0.9 utilisation for 28 concurrent
games — Qwen-27B-FP8 (27 GB weights) already runs KV at 83–87 % of ~60 GB. `--quantization fp8`
(dynamic, dense-safe) brings the weights to ~31 GB and restores the KV budget. It is a numerics change
on top of the model change; the serving smoke reads it, and BF16 is the fallback if fp8 fails to load.

## Smoke oracle (thui-gemma-v0: tr87 / sk48 / sc25, 900 s each)

- **S0 serving** — the bundle's own `run_vllm_api_smoke_test` ("2 + 2") passes under vLLM 0.23 + Gemma-4 fp8; `vllm-openai-server.log` shows the model loaded, weight memory, KV blocks. Kill on sight: the model fails to load, or fp8 fails and BF16 leaves < 15 GB of KV.
- **S1 tool calls** — fraction of analysis turns ending `Step executed.` over the three games, read against the same fraction in the Qwen sidecars (measured below). Below half of Qwen's rate = the `gemma4` parser is not reading duck's tool schema; try the vLLM example `--chat-template` for Gemma 4 before killing.
- **S2 images** — zero `analyzer failed` lines caused by 4xx on requests carrying `image_url` parts (the MM limit or the modality path). Any such error = raise the limit or strip history images, then re-smoke.
- **S3 harness** — run COMPLETE, 3 games, no new exception class from the python sandbox or the wrapper (the harness code is unchanged, so anything new is the model's output shape).
- Report: generation tok/s, prefix-cache hit, KV usage max, mean turn latency against thui-v1-1's log, tool-call parse rate.

## Full-run oracle (thui-gemma-v1)

Paired **levels** vs the same-seed base pair (`thui-v1-1` 28 / `thui-v1-1-r2`), >= 2 runs per arm,
`eval/pool_runs.py` → `eval/rank_runs.py`. Kill: Δ < +1 level in >= 6 games (B35 floor) on both draws.
A hidden draw only after that reads — a model swap is exactly the case the within-build sd (0.28–0.34)
was measured on.

## Not in scope

- Gemma-specific prompt edits, reflection memory (B62) or any second variable — one swap, one arm.
- `--kv-cache-dtype fp8` — the ko0kip wheels carry no flashinfer; fp8 KV on the default attention backend is a second unknown. Try only if S0 shows KV as the binding constraint.
- Building our own wheelhouse — ko0kip's set is a working, public, pinned one; if its layout changes, the builder's exactly-once asserts fail at build time.

## Status

- 2026-09-03: builder + smoke notebook built (cells 0/6/8/14; every rewrite anchor hit once against the vendored bundle; rewritten setup script parses). GPU quota on `sahasawatt` exhausted (same as B61/B62) — push record below.

### S1 baseline, measured on the Qwen sidecars (the number the smoke is read against)

| run | analysis turns | `Step executed.` | `Yielded control` (180 s yield re-enters) | no status |
|---|---|---|---|---|
| taaf-duck-v10 | 974 | 44 % | 52 % | 4 % |
| thui-v3-1 (yocybercode) | 770 | 57 % | 39 % | 4 % |
| thui-v3-2 (yocybercode) | 774 | 54 % | 42 % | 4 % |
| thui-v6-0 | 778 | 48 % | 47 % | 6 % |

Qwen executes a step on 44–57 % of turns. S1 kill line for Gemma: **< 25 %** (under half of the worst
Qwen run) = the tool-call path is not working; 25–40 % = read the parse errors before judging.

### Push record

- 2026-09-03 20:54Z raw `kaggle kernels push -p thui-gemma` → `Kernel push error: Maximum weekly GPU
  quota of 30.00 hours reached.` Same blocker as B61/B62. Unblock: weekly reset on `sahasawatt`, or
  `python3 thui-gemma/build_notebook.py --owner=yocybercode` + the gate script from the mac. The queue
  behind the reset is now B61 (45 min) → B62 (45 min) → B64 (S0 alone may need ~20 min of model load).

## Rebased 2026-09-04 onto the B48 chassis

Builder default is now `--base=v3` = `thuiv3/taaf-thui-v3-0.ipynb` (thui-v1-1 + yield 180: the build that drew the standing best 2.03 and holds the campaign's only 4-run public pool). The cell-12/14 seams are identical in that chassis (anchors asserted once; cell 8 asserted to carry the yield-180 injection twice). **Baseline for the paired read is the `thuiv3` arm** declared in `eval/fixtures/arms.json` (thuiv3-0 4.01 / thuiv3-0-r2 4.52 / thuiv3-1 5.17 / thuiv3-2 3.85; the three new fixtures banked from each run's `benchmark.json`, means reproducing the LEDGER), pooled as `eval/fixtures/thuiv3-pool.json`. Read: `python3 eval/rank_runs.py eval/fixtures/thuiv3-pool.json <candidate-pool>.json`, +1 level in >= 6 of 25 games on both candidate draws. `--base=v1` keeps the thui-v1-1 chassis for a control build only.
