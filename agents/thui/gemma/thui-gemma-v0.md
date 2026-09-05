# thui `gemma v0` — built, quota-blocked, never run

**Line** thui · **family** gemma · **directory** [`thui-gemma/`](../../../thui-gemma) · **ticket** `B64` · **status** built, NOT RUN — ticket open

## The one change

**The model.** Gemma-4-31B-it replaces Qwen3.8-27B-FP8 inside the unchanged duck harness. Nothing in the
harness, prompts, seed (`20260825`), temperature (0.6), yield, upscale or clock moves — the chassis's own
in-kernel teeth still assert all of them.

**Why this candidate**: the model-swap lane is the only lever that ever gained (`B6`, 2.41 → 4.55). The
2026-09-03 research closed Flash-Next (135 GB, does not fit) and gpt-oss-120b (5.1B active = `B25`'s dead
class), leaving one dense multimodal candidate with **zero in-harness evidence** — which is what Reki (#2)
and forge (#3) ran in Milestone 1. Evidence strength: **weak, structural.**

**Two measured blockers are built around, not guessed at**:

- the pinned wheelhouse (vLLM 0.19.0 / transformers 4.57.6) **cannot load Gemma 4** — it needs
  vLLM ≥ 0.19.1 and transformers ≥ 5.5 — so the wheelhouse is swapped to `ko0kip/vllm-0230-offline`
  (vLLM 0.23.0, transformers 5.12.1, torch 2.11.0), installed **by name from its wheels dir** because it
  ships no `requirements.lock`;
- duck's launch flags are Qwen-specific (`qwen3_coder` tool parser, `qwen3` reasoning parser,
  `preserve_thinking`) → `gemma4` / `gemma4`, plus an explicit **32-image prompt limit**, because duck
  keeps prior turns' board images in history, and **online fp8 weights** to restore the KV budget
  (62.6 GB BF16 leaves ~24 GB of KV; fp8 brings the weights to ~31 GB).

Cells 0 / 6 / 8 / 14. **Eleven exact-once rewrites on the rendered setup command**, replayed at build time
against the vendored bundle and `ast.parse`d — so bundle drift fails at build time rather than on the GPU.

## Where it lives

| what | path |
|---|---|
| builder | `thui-gemma/build_notebook.py --base=v3` |
| notebook | `thui-gemma/taaf-thui-gemma-v0.ipynb` |
| kernel | **none** — never pushed |
| design | `notes/B64-gemma-4-31b-duck-agent-design.md` |

## What it scored

**Nothing. It has never run.** `notes/LEDGER-all-runs.md` has no row and should not gain one until it does.

🔴 The push failed 2026-09-03 20:54Z with the CLI's own
`Kernel push error: Maximum weekly GPU quota of 30.00 hours reached.` — the same blocker that held `B61`
and `B62`. Unblock: the weekly reset on `sahasawatt`, or
`python3 thui-gemma/build_notebook.py --owner=yocybercode` plus the gate script from the mac.

## Verdict

**None yet — and the oracle is already written, which is the point of the page.**

- **S0 serving** — the bundle's own `run_vllm_api_smoke_test` passes under vLLM 0.23 + Gemma-4 fp8. Kill on
  sight if the model fails to load, or if fp8 fails and BF16 leaves < 15 GB of KV.
- **S1 tool calls** — fraction of analysis turns ending `Step executed.`, read against Qwen's measured
  **44–57%** (`taaf-duck-v10` 44 · `thui-v3-1` 57 · `thui-v3-2` 54 · `thui-v6-0` 48). **Kill line < 25%**;
  25–40% means read the parse errors before judging.
- **S2 images** — zero `analyzer failed` lines from 4xx on requests carrying `image_url` parts.
- **S3 harness** — COMPLETE, 3 games, no new exception class.

Full-run oracle: paired **levels** against the `thuiv3` pool, ≥ 2 runs per arm, `+1` level in ≥ 6 of 25
games on both draws. **A hidden draw only after that reads** — a model swap is exactly the case the
within-build sd (0.28–0.34) was measured on.

## Read next

- `notes/B64-gemma-4-31b-duck-agent-design.md` — the blocker table, the eleven rewrites, and what is out of scope
- [`../v6/v6-0.md`](../v6/v6-0.md) — the other build whose every structural oracle fired and whose score did not move
