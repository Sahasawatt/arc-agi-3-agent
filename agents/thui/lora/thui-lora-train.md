# thui `lora train` — the offline SFT kernel, and a fifteen-push ladder

**Line** thui · **family** lora · **directory** [`thui-lora/train/`](../../../thui-lora/train) · **ticket** none — the LoRA arm · **status** ran, produced the adapters

## The one change

Not a harness build at all: a **standalone kernel** running `train_lora.py` from the
`sahasawatt/thui-lora-train-v1` dataset, fine-tuning a LoRA adapter on our own winning turns. It plays no
games and produces no score — its output is the adapter that [`e1`](thui-lora-e1.md) evaluates.

## Where it lives

| what | path |
|---|---|
| notebook | `thui-lora/train/taaf-thui-lora-train.ipynb` |
| metadata | `thui-lora/train/kernel-metadata.json` |
| kernel | `sahasawatt/thui-lora-train` |

## What it scored

**Nothing — it is a trainer.** No ledger row, and it should not gain one.

## Verdict

**It works, and what it left behind is the ladder**, learned across **15 pushes** and recorded in the
commit that added the family (`e598cbe`):

- `transformers` **5.16.1** (`qwen3_5`);
- **FP8-as-shipped is un-trainable** — the hub Triton op has no autograd — so the weights are
  **dequantized to bf16 at load**;
- `MAX_LEN` 4096 + `expandable_segments` against OOM;
- **left-truncate the prompt** so no response is ever dropped — 1331/1331 encoded.

⚠️ A missing `layer_types` silently targeted all 64 layers; the builder now asserts `_lt` rather than
guessing target layers.

## Read next

- [`thui-lora-e1.md`](thui-lora-e1.md) — what the adapters scored on the held-out games
- [`thui-lora-v0.md`](thui-lora-v0.md) — the serving smoke that made the arm possible at all
