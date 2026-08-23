# The flag we never knew existed — and the first verified attribution of this campaign

2026-08-23. Every run this campaign has made instructed Qwen3.8 to *"think carefully
through the task, validate key assumptions, consider plausible alternatives"* on every
single turn. Nobody chose that; it is the chat template's default.

## How it was found

Searching Kaggle datasets for large models turned up two tiny artifacts that kept
reappearing — 43 KB with 708 downloads, and a 44 KB "colab-v29". Neither is weights.
Both are competitors' work. Cross-referenced against the leaderboard CSV:

| publisher | rank | hidden | subs | what they published |
|---|---|---|---|---|
| **ataraxian / "Ya Xu"** | **21** | **2.37** | 18 | `arc3-qwen38-colab-v29` — a TAAF bundle fork |
| sonpham | 38 | 2.21 | 25 | `sonpham-org/arc-3` — 11 graft modules |
| **thtennant** | **314** | **1.46** | 32 | the 6,524-line, 1,275-download fork of R21 |
| **yousefturk (FluidMind)** | **1381** | **0.23** | 2 | the most convincing writeup of the four |
| us (Thuitanium) | 212 | 1.70 | 9 | — |

**The two artifacts I found most impressive are the two that score worst.** R21 treated
thtennant's 18-module graft stack as evidence of what teams above us do; its author is
**102 ranks below us**. R22's `attribution` lens had already warned in as many words that
1,275 downloads is popularity and not evidence — and I still half-believed it.

FluidMind's writeup diagnoses our exact harness as failure mode #3 (*"Duck Harness REPL —
world model is chat text, not an assay-gated executable kiln"*), proposes an architecture
that reads as clearly correct, and scores **0.23**.

## What rank 21 actually changed

Diffed against the **same June-era base** we hold at `duck/bundle` — not against our anim
bundle, which produced a misleading 30-file diff dominated by features their base predates:

```
DIFFERENT vs same-era base (6):
  setup_commands.json
  configs/inference.json
  inference/agent/prompts.py
  inference/agent/tool_agent.py
  inference/framework/kaggle.py
  inference/utils/openai_compat.py
ONLY in theirs: 0
```

**Six files.** `kaggle.py` is just the Qwen3.8 default (we do that in cell 8). `prompts.py`
trims the system prompt and adds a per-level "what I already tried" checklist. And
`openai_compat.py` adds this, with their own comment:

```python
# Optional Qwen3.8 reasoning_effort override (xhigh/medium/low) via env.
# Empty/absent => leave the model default (xhigh). This is the hook v27/v28
# use to dial down over-thinking (see results-v25 r11l/sk48 analysis paralysis).
reasoning_effort = os.environ.get("LOCAL_ANALYZER_REASONING_EFFORT", "").strip()
if reasoning_effort:
    chat_template_kwargs["reasoning_effort"] = reasoning_effort
```

Their setup env sets `'LOCAL_ANALYZER_REASONING_EFFORT': 'medium'`.

They name the failure **"analysis paralysis"** and cite `r11l` and `sk48`. In our own runs
`sk48` scored **0.00 in both v18 and v19**.

## Verified against the model, not against their claim

`huggingface.co/Qwen/Qwen3.8-27B-FP8/raw/main/chat_template.jinja`:

```jinja
{%- set resolved_reasoning_effort = reasoning_effort|default('xhigh') %}
{%- if resolved_reasoning_effort not in ('xhigh', 'medium', 'low') %}
{{- raise_exception('Unexpected reasoning effort ' ~ reasoning_effort ~ '.') }}
```

| value | what the template appends |
|---|---|
| **xhigh** (default) | "think carefully through the task, validate key assumptions, consider plausible alternatives" |
| medium | nothing |
| low | "keep your thinking brief and focused, moving directly to the conclusion" |

A wrong value raises inside the template, so unlike upstream's `MULTIMODAL_GRID_LINES`
(set to `'true'` while the reader tests `== "1"`) this flag cannot fail silently.

Neither our anim bundle nor the newer one has the hook — `reasoning_effort` appears in
neither `openai_compat.py`. v21 monkeypatches it in **two** places, because
`tool_agent.py:45` does `from inference.utils.openai_compat import build_chat_payload`,
so the binding that runs lives in `tool_agent`'s namespace.

## Why this is worth a slot even though it contradicts R24

R24 concluded **by elimination** that the bottleneck is the model's capability to find a
level's solution. This says the opposite: the model is *instructed* to over-deliberate.

Both fit the same measurements — games plateau holding 30-95 minutes and 24-47 unspent
actions, with mechanics, lock-in, goal-confusion, budget and click-exploration all ruled
out. "Cannot solve it" and "is told to deliberate at maximum on every turn" are
indistinguishable from the outside.

They are not indistinguishable from the inside. v20 cut *capability* (MoE, ~3B active) and
collapsed to **0.18**. v21 cuts the *instruction to deliberate* and keeps the model. If
R24 is right, v21 lands in the [2.82, 4.71] same-build spread or below. If this is right,
it lands above 4.71.

## UNVERIFIED

- **Their 2.37 is not attributable to this one flag.** Six files changed, and the prompt
  trim plus the tried-checklist may carry it. v21 isolates the flag alone; that is a
  deliberate choice to keep the run rankable (R9), not a claim about which file matters.
- Their bundle is a **Colab** variant (Chinese comments, `WHEELHOUSE_DIR`/`MODEL_DIR` env
  instead of Kaggle mounts). The submitted Kaggle version is not public; what is public is
  the lineage of their experiment, and the flag value they were running with at v29.
- `medium` versus `low` is untested. They chose medium. Nothing here says medium is the
  best of the three.


## RESULT (same day) — measured, and the hypothesis is dead on our stack

v21 ran the flag alone: **1.25 public, p=0.0052 WORSE** (`eval/rank_runs.py`, outside the
same-build noise). The mechanism did exactly what it promised — tok/action 1271→776 (−39%),
actions 1597→2921 (+83%) — and levels halved, 28→12.

So the "analysis paralysis" reading does not transfer to our stack: cutting deliberation
freed throughput and the throughput bought attempts, not depth — the same shape as v20 at
lower magnitude. With v20 this closes the axis in both directions: less thinking per
decision, however achieved, costs levels. Whatever carries the rank-21 team's 2.37, it is
not this flag in isolation — the trimmed prompt and the per-level tried-checklist remain
unmeasured.
