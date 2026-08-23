# What actually stops us — five causes eliminated by measurement

2026-08-23. R20's open-questions list ended with: *"ไม่มี source ไหน (และเราเองก็ยังไม่วัด)
แยกว่า plateau มาจาก exploration strategy, perception misread, หรือ genuine reasoning depth"*.
This closes that, from artifacts already on disk — no GPU, no quota, no new run.

Instrument: `artifacts/*_events.jsonl` from the v18 (1,576 actions) and v19 (1,638 actions)
full runs, 25 games each, plus `benchmark.json` for per-game score.

## Eliminated

| # | candidate cause | measurement | verdict |
|---|---|---|---|
| 1 | doesn't understand what actions do | `board_changed == False` on **5.3%** (v18) / **5.9%** (v19) of actions | not it — 94% of actions move the board |
| 2 | hypothesis lock-in, brute-forcing one wrong mechanic | median longest run of the same action = **5**; worst case 24 | not it — `recovery.py` cites SPACE×71; nothing near that here |
| 3 | knows it is lost | carried `Goal model` line reads Unknown/empty on **7 of 104** rendered turns (6.7%) | not it — the agent believes it knows the goal |
| 4 | out of time or actions | plateaued games stop with 30-95 min and 24-47 actions left (measured earlier, LEDGER) | not it |
| 5 | doesn't explore the click space | 457 MOUSE actions over **222 distinct cells of 4096**, 8 of 25 games never click — **and the top-scoring game (`re86`, 16.10, 3 levels) clicks ZERO times** while the widest clicker (`su15`, 44 cells) scores 2.22 | not it — clicking does not correlate with scoring either way |

⚠️ Two caveats that keep these honest:
- #1 is measured with `hard_noop_guard=True` active, which already blocks re-pressing an
  action proven inert in the same board state. 5% is the first-try rate, not the rate the
  model would produce unguarded.
- #3 rests on 104 rendered turns out of 1,062 analysis events — the `Goal model` line is
  only carried when the agent wrote one. Small sample.

## What is left

The agent moves the board, understands its controls, does not repeat itself, believes it
knows the goal, has time and actions in hand, and — where clicking matters — clicking is not
what separates the games it wins from the ones it does not. **What remains is finding the
sequence that clears the level.**

This is elimination, not direct evidence. But five plausible mechanical causes are now ruled
out with numbers, and the campaign's own record agrees: every lever aimed at the mechanical
causes (throughput, state delivery, image resolution, brevity, retry) moved the score by less
than the build's own noise (LEDGER CORRECTION 3).

**The strategic reading, stated plainly:** if the remaining bottleneck is the model's ability
to reason out a level's solution, then it is a property of Qwen3.8-27B, and R22's finding
lands squarely on it — every strong published result on this benchmark (Symbolica 4.52
levels/game, arc-skill RHAE 100, Continual Harness 20.54%) was measured on Claude Opus 4.6/5
or Gemini 3.1 Pro. Nobody has shown any harness mechanism carrying an open-weight 27B to that
range. Hidden 2.57 for top-5 may not be reachable on this model regardless of harness work.

That is a claim about where to spend the remaining quota, not a reason to stop: the two
things that would test it are (a) a harness change with a mechanism that does not depend on
model strength — banking was that, and it turned out unreachable until a game is won outright
— and (b) checking whether a stronger model can run inside Kaggle's constraints at all, which
R20 already answered negatively for MoE and which has not been re-asked since.

## The one number that reframes everything

**0 games won, ever. 20 of 183 levels cleared in v19; 28 of 183 in v10cal.**

Every game in every run ends `gave_up`. The campaign has been optimising the score of games
it never finishes — which is why the completion-cap term dominates, why banking was
unreachable, and why depth is the only axis with room left.


## Follow-up the same hour: option (b) is open after all

The section above lists two things worth testing, the second being *"checking whether a
stronger model can run inside Kaggle's constraints at all, which R20 already answered
negatively for MoE"*. Re-asked, and **R20's answer was wrong**.

R20 searched Kaggle **datasets** and found only GGUF and ollama blob splits of
Qwen3.6-35B-A3B. Kaggle has a second, separate registry — **Models** — and our own
`kernel-metadata.json` has carried an empty `"model_sources": []` since the first notebook.

`michaelpoluektov/qwen3-6-35b-a3b-fp8` mirrors `Qwen/Qwen3.6-35B-A3B-FP8`:

```
37,493,015,668 bytes   status READY   created 2026-06-02
config.json (37 KB) · generation_config.json · chat_template.jinja · layers-N.safetensors
```

That is the loadable HF layout, not a quantised container. So a MoE — 35B total, ~3B active
— is available to this competition and has never been tried.

**The trade is known and half-measured**: Qwen3.6 is one generation behind the Qwen3.8 we
run, and that exact swap was worth **+37%** on this harness (duck-mod 2.41 → v8out 3.31 on
the old bundle). No Qwen3.8 MoE mirror exists on either registry — searched both.

⚠️ The lesson is the one this file already turns on: **an absence found by a search is a
claim about where you searched.** R20 said "not on Kaggle" and meant "not in the datasets
index", and I repeated it into the LEDGER as a closed direction.

⚠️ Unverified before any run: whether the vLLM build in this container
(0.19.0, which reported `Qwen3_5ForConditionalGeneration` for our current model) supports the
Qwen3.6 MoE architecture, and what `model_sources` mounts look like from inside the kernel —
the bundle's setup script resolves a *dataset* path today.
