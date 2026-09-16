# thui-m0 (MTP-0 / KV 7 GiB / seqs 20 chassis) full-25 draw r1 — verdict (2026-09-15)

`sahasawatt/thui-m0-s20-full25-r1`, output `kout-sa-thui-m0-s20-full25-r1/`, ran 15:33–17:58 local (wall 8,491 s). Pre-registered read in
`thui-m0/build_notebook.py`, applied in order. The paired control arm (`--control`) was NOT run; comparators are the same-day
shipped-profile draws already banked.

## 1. Mechanism — delivered, gate half-met
- `THUI_M0_ARM name=s20` printed; vLLM was started with `--kv-cache-memory-bytes 7516192768 --max-num-seqs 20` and no speculative
  config (`speculative_config=None` in the engine banner). No OOM, no traceback, 0 preemption lines. (The `GPU KV cache size:` banner
  line is absent from the Kaggle log stream in this vLLM build — the start command and `speculative_config=None` are the evidence.)
- `thui-m0/turns_read.py`: **turns/game median 70** (60–90; shipped 52, 48–54) → +35 %; **wall/turn median 107 s** (shipped 159 s;
  gate said < 100 s). Actions **5,722** — the most any Thuitanium draw has ever taken (shipped pool 3,100–4,049).
- Reading: the queue did shrink and the harness used the room (more turns, many more actions). The gate's `< 100 s` clause missed by
  7 s; the turns clause passed. Not VOID — the chassis delivered roughly 1.5× turns, not the 2× the bench's 722 tok/s suggested,
  because the per-turn floor is now the model's own generation + the harness's 60 s turn budget, not the queue.

## 2. Score — lower, not distinguishable
| baseline | mean | levels | actions | delta | p (sign-flip) | verdict |
|---|---|---|---|---|---|---|
| wm-ctl-full25-r1 (shipped, 09-15) | 8.32 | 36 | 3,517 | **−2.70** | 0.102 | NOT-DISTINGUISHABLE |
| wm-v0-full25-r1 (shipped + wipe guard, 09-15) | 7.44 | 39 | 3,100 | −1.82 | 0.104 | NOT-DISTINGUISHABLE |
| fast-b78-mtp0 (Watchara, MTP-0 at KV 5 / seqs 8) | 6.96 | 40 | 4,049 | −1.34 | 0.264 | NOT-DISTINGUISHABLE |
| **m0-s20** | **5.62** | **39** | **5,722** | | | |

Levels 39 = exactly wm-v0's 39, one above ctl's 36 (inside the pool's 36–40). Score fell because RHAE is
`(human_actions / ai_actions)^2` per level: the same 39 levels were bought with 63 % more actions than ctl, so every scoring level
pays. The three MTP-0 rows line up: b78 (4,049 actions, 6.96) → m0-s20 (5,722, 5.62) — more room, more actions, same levels, less score.

## 3. Verdict — DEAD for score (rule 4), with the gate caveat stated
More turns did not become more levels; they became more actions on the same levels. The tail is the search, not the queue — the
same conclusion the frontier-5 diagnosis reached from the other side (corr(actions, levels) = 0.08). A second draw could move
5.62 by ±1.5 (pool sd) and would not change the shape: 39 levels at 5.7k actions is not a path to 8.21.

What it does NOT say: nothing about hidden; nothing about MTP-0 *with an action-frugal harness* — a harness that stops acting when
it has nothing new to try would keep the turn gain without paying the action tax. That is the search-strategy lever, unbuilt.

Cost: 1 kernel, 2.36 GPU-h, 0 slots. Nothing submitted. Harvested into `eval/fixtures/per-level-census.json` as its own run key
(not added to the FLASH list — different serving profile; b78-mtp0 sits there by the owner's earlier call, so folding m0 in is the
owner's call too).
