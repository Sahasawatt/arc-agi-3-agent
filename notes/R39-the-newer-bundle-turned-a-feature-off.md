# R39 — the newer bundle ships its own A/B results in the source, and one of them says we are paying for a feature its author switched off

Measured 2026-08-25, offline, 0 slots. Sources: the three bundles left in a previous session's
scratchpad (`bundlecmp/{anim,new,fork}`, still on disk), the `clock-2x-v1` artifacts, and a live
Kaggle dataset search. No run, no GPU, no submission.

Written because the "harness ล่าสุด" question turned out to have an answer nobody had looked
for: **the newer upstream bundle is not a pile of new features, it is a pile of DECISIONS, and
they are written into the code as comments.**

## 1. What actually differs

`anim` (the bundle every build of this campaign pins) vs `new` (post-anim upstream):
**75 files each, identical file set, 14 files differ in content.**

| file | Δ bytes |
|---|---|
| `framework/solver.py` | **+5,700** |
| `agent/vision_context.py` | +2,206 |
| `utils/animation.py` | +595 |
| `framework/kaggle.py` | +367 |
| `agent/prompts.py` | **−1,038** |
| `agent/tool_agent.py` | **−1,052** |
| 8 more | Makefile, preamble, setup_commands, 2 pkl, git_status, bundle.json, a shell script |

⚠️ **v23 ported ONE of those fourteen** (the grid-line renderer out of `vision_context.py`) and
came back 3.32, p=0.4061 NOT-DISTINGUISHABLE. That result is about grid lines. **"The newer
bundle does not rank" has never been tested**, and this note does not test it either.

## 2. `solver.py` +5,700 is not scheduling — it is flag plumbing, and the flags carry verdicts

Four new symbols, all about configuration: `_env_flag`, `_write_effective_flags`,
`effective_flags`, `effective_animation_retrieval`. Nothing in the action loop, the clock, or
the concurrency path changed shape.

What is worth reading is the prose upstream attached to them:

> **`animation_retrieval`** (default `False` in `new`) — "It works and the model reaches for it
> unprompted in 64% of calls, but **across Experiments 3 and 4 it bought no score**, so we do not
> pay for it by default."

> **`animation_awareness`** (default `True`) — "+3.3% tokens, no measurable harm, and the
> `worth_inspecting` threshold it carries is **the one transferable result of the series**."

> **the frame cache** — "the most informative retrieval of the whole first Kaggle A/B **died in
> the sandbox's 30s budget** building this at retrieval time instead."

> **`effective_flags.json`** — "**Not one of the 28 run folders on disk records which flags were
> active** — the arm of an A/B is recoverable only from the folder name, which is how Experiment
> 4 got audited from a pickle."

That last one is a problem this campaign has too, and the fix upstream shipped is 40 lines.

## 3. The finding: our bundle has the retrieval, with no switch

| | `anim` (ours) | `new` |
|---|---|---|
| `animation()` sandbox global | present | present |
| `animation_retrieval` flag | **ABSENT** | present, **default OFF** |
| `worth_inspecting` | **ABSENT** (0 files) | present (4 files) |
| frame-diff precomputed at append time | no | yes |

So the feature upstream measured across two experiments, found worthless, and switched off is
**permanently on in every run this campaign has ever done**, and the one result they call
transferable is **absent from our bundle entirely**.

## 4. How often our own runs use it — measured, after the first probe failed

Upstream's 64% is upstream's number on upstream's runs. Ours, over the `clock-2x-v1`
transcripts (1,858 analysis turns, 25 games):

```
animation() EXECUTED     in 176 turns =  9.5%
animation() only DRAFTED in 217 turns = 11.7%
action()    EXECUTED     in 621 turns = 33.4%   <- positive control
system-prompt phrase leaking into ASSISTANT: 0  <- negative control
```

⚠️ **The first version of this probe returned 100.0% for every column including both controls**
— R33's trap arriving again. `transcript` is the whole exchange; its `[SYSTEM PROMPT]` block is
14,204 chars and contains both `animation(` and `action(`. An all-100% result with the control
also at 100% is a broken instrument, never a finding. Splitting on the section markers fixes it,
and separating `[ASSISTANT]` (executed) from `[THINKING]` (drafted) matters exactly as it did in
R33 — drafted **exceeds** executed, 11.7% against 9.5%.

⚠️ **The 33.4% control first read as too low to trust.** It is correct: one `analysis` turn is
one tool-agent call containing several sub-turns, and a turn that only inspects the frame issues
no action at all. 2,637 actions over 621 action-issuing turns is 4.2 per turn, which is the
batch shape the harness allows. A control that surprises you is a thing to explain before the
finding beside it is quoted, not after.

**Usage is wildly uneven per game.** `sb26` executes it in 46 of 96 turns (48%), `tn36` 25,
`sp80` 15, `su15` 15 — while `ar25`, `bp35`, `cn04`, `dc22`, `ft09`, `m0r0`, `re86`, `tr87`,
`vc33`, `wa30` execute it **0 times across their combined 745 turns**. Ten of 25 games never
touch it.

## 5. `prompts.py` −1,038 is compression, not a lever

Seven long bullets about animation semantics collapse into two, same content, plus the new
`worth_inspecting` field. **This is not v12's "ask for brevity"** — that told the MODEL to be
brief and measured 3.72, below band. This is the context itself getting shorter.

## 6. Model — there is nothing better to switch to

`new` makes the model env-overridable (`ARC3_MODEL_DATASET_SOURCE`, `ARC3_SERVED_MODEL_NAME`),
which is cleaner than what we do: `duckv25/` cell 8 rewrites the setup-command strings
`vrfai-qwen3-6-27b-fp8-hf-snapshot` → `qwen3-8-27b-fp8-hf-snapshot` and `Qwen3.6-27B-FP8` →
`Qwen3.8-27B-FP8`, with two asserts that the rewrite landed. Same effect, uglier.

But a knob is not a candidate. Kaggle dataset search, run 2026-08-25:

| ref | what it is |
|---|---|
| `driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot` | 3.6 — the bundle default, **older than ours** |
| `an0sss/qwen3-8-27b-abliberated` | 3.8 abliberated, 44 GB, **0 downloads** — a refusal-removed variant, not a reasoning upgrade |
| `an0sss/qwen3-6-27b-abliberated` | 3.6 variant |

**LEDGER's "a better dense model = exhausted" still holds as of today**, and the other direction
is closed with a number: v20 (MoE, ~3B active) = **0.18, p=0.0001 WORSE**.

## 7. What this suggests, and what it does not

**The cheap move is not adopting the bundle — it is porting the switch**, the same shape as
v23's grid-line port. Gating the append at `solver.py:860` (`animation_history.append`) is
enough: an empty history makes `animation_record()` return `None` and `animation()` return `{}`.

⚠️ **That alone reproduces a bug upstream documents**: "that is how the Experiment 4 control arm
ended up still advertising `animation()` while the handler was off." The prompt has to lose the
advertisement in the same change, or the model spends turns calling a dead tool. **Two edits,
not one** — and the second one is the reason the first is not free.

**What is NOT known:**

1. **Nobody has measured what retrieval COSTS us.** 9.5% of turns execute it; the token bill for
   those turns was not measured here, and `thui-v1`'s per-request `*_usage.jsonl` — the artifact
   that could answer it — is on the Mac, not in the clock2x output.
2. **Upstream's "bought no score" is upstream's measurement on upstream's runs.** A strong prior,
   not our data.
3. **Removing a feature is a behaviour change, so it needs a public run to rank** — exactly like
   every other candidate, under B30. "It is a removal" does not exempt it.
4. `worth_inspecting` may be worth more than the removal, and porting it is the larger job: it
   appears in four files including `utils/animation.py`.
5. **Ten of 25 games never execute `animation()` at all**, so whatever the removal is worth, it
   is worth nothing in those ten — which is the same per-game unevenness B35 is about.

## 8. Reproduce

`bundlecmp/` is in a previous session's scratchpad, not in this repo — it holds `anim/`, `new/`,
`fork/` plus the three source zips. The file comparison is `filecmp.cmp(shallow=False)` over
both trees. The usage figures come from `<game>_events.jsonl` rows with `type == "analysis"`,
splitting `transcript` on `^\[([A-Z ]+)\]` and counting only the `ASSISTANT` block — counting the
whole string returns 100% for everything, including the controls.
