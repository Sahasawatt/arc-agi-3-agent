# thui `lora v0` — the serving smoke, which scores nothing on purpose

**Line** thui · **family** lora · **directory** [`thui-lora/`](../../../thui-lora) · **ticket** none — the LoRA arm, cited by `B60` · **status** smoked, arm closed null

## The one change

`--enable-lora --lora-modules smoke=<dir>` on the vLLM launch, plus a **dummy adapter generated
in-kernel** from the model's own `config.json`: rank-8, `A` small-random, **`B` all zeros**,
`q_proj`/`v_proj` only. `B = 0` makes the adapter the mathematical identity, so nothing can fail for
behaviour reasons — **the serving chain is the only thing under test**.

**The one risk it exists to retire**: nothing in this campaign had ever run vLLM 0.19 + Qwen3.8-27B-**FP8**
+ a LoRA adapter together, and FP8-base + LoRA is a pairing that has genuinely broken in some vLLM
versions. Everything else about LoRA can be built offline; this pairing can only be proven on the kernel
GPU.

⚠️ **Where the injection lands**, learned by the builder's own first failure: the vLLM serve invocation
lives inside the `command` **string** cell 8 loads from the source dataset's `setup_commands.json` at
runtime — not in the cell source. So the flag injection is one more anchored `.replace()` chained where
the seed pin already chains, and the teeth assert on `command` **after** the replaces ran.

## Where it lives

| what | path |
|---|---|
| builder | `thui-lora/build_notebook.py` |
| notebook | `thui-lora/taaf-thui-lora-v0.ipynb` |
| kernel | `sahasawatt/thui-lora-v0` |

## What it scored

**Nothing, and it must not be scored.** 3 games on a capped clock; the summary is meaningless and must
not enter any ledger.

| oracle | result |
|---|---|
| **P1** server lists base **and** `smoke` in `/v1/models` | **PASS** |
| **P2** a chat completion addressed to `smoke` answers 200 with content | **PASS** |
| **P3** the agent plays through the same server with the adapter mounted | **PASS** |

## Verdict

**The serving risk is retired.** FP8 base + LoRA adapter serves on this stack, and the harness's request
path is undisturbed.

⚠️ **The smoke that retired that risk ran the PRE-fix notebook.** A `review-fanout` later found the
cell-12 `bm.games[:3]` slice was **inert** — cell 14 reassigns `bm.games` on both branches — so `v0` as
first built played all 25 offline games at 900 s each while printing *"3 games"*. The slice and clock now
inject after `bm.games = _offline_games(...)` with `assert len(bm.games) == 3`, at the same seam
`eval/build_notebook.py` already used. **P1 and P2 fire before any game and P3's conclusion holds over
more games than intended, so it was not re-run.**

## Read next

- `notes/B60-exploration-prior-design.md` — the held-out means that closed this arm null (2.45 / 3.69
  against base draws 4.61 / 6.35), and the *gain where the base is dead, loss where it is alive* signature
- commit `e598cbe` — the trainer's 15-push ladder and `thui-lora-e1`'s per-game direction; neither the
  trainer nor the eval has a page here
