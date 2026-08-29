# R51 — the agent's context window is half what the server serves, and two smaller checks

2026-08-29, offline, 0 slots, 0 GPU. Three checks from the lever-research sweep (7-agent
workflow, 85 candidates -> 34 survivors), each run against banked artifacts or the live
`sahasawatt/taaf-duck-v10` output (the one kernel whose real run is still its latest version).

## 1. The window (the finding that matters)

Every run of this campaign echoes, in its own setup:

```
VLLM_MAX_MODEL_LEN      = 65536      <- what the server accepts
ANALYZER_CONTEXT_WINDOW = 32768      <- what the agent uses
```

`32768` is `tool_agent.py`'s own default (`_get_env_int("LOCAL_ANALYZER_CONTEXT_WINDOW", 32768)`),
copied into the setup script — nobody chose it for the 27B. Downstream, every one of the 935
ANALYZER STATUS blocks in `duck-v10`'s transcripts prints the same derived budget:

```
context_budget_tokens: 31744        (32768 - 512 reply reserve - 512 margin)
```

And the trim is ACTIVE, not theoretical: across the six probe-carrying runs (7,147 usage rows),
`prompt_tokens` sits at **median ~22k, p90 ~25k, max 30.9k** — pressed against the budget in
steady state, with `history_messages` flat at median 18 / max 36 while games run 40–80 turns:
old evidence falls off the back every turn.

**The candidate build is one environment variable and zero code**: `thui-v6-0` = `thui-v1-1` +
`LOCAL_ANALYZER_CONTEXT_WINDOW=49152`.

⚠️ **CORRECTED before any build — this section first said 65536, and that value is UNSAFE.**
`max_model_len` bounds prompt **plus completion**, not the prompt alone. At a 65,536 window the
prompt budget is 64,512, and the completion tail measured over **9,147 requests** across the six
probe runs is p95 **5,148** / p99 **8,325** / max **11,989** — so 64,512 + p99 = **72,837**, past
the server's 65,536 ceiling. The largest prompt+completion ever observed is 39,382, comfortably
inside today's limits precisely because the prompt is capped at 31,744.

Sizing it properly: budget + worst observed completion ≤ 65,536 ⇒ budget ≤ 53,547 ⇒ window
≤ 54,571. **49,152** takes it with room: prompt budget **48,128** (+51.6% over today), and
48,128 + the 11,989 worst case = 60,117, still **5.4k under** the ceiling. Retainable history rises
~1.5×, not 2.9×.

The harness does carry a context-length error path (`_is_context_length_error`), so an oversized
window would likely degrade rather than crash — which is exactly why the arithmetic has to be done
up front: a silently degrading run looks like a normal one.

⚠️ Honest priors, stated before any build:
- This is NOT v16 (dead): v16 *injected* extra state into every turn; this stops *discarding*
  history that already exists. Different mechanism, same risk class.
- thui-v3-0 gave the model 3× thinking time per turn and bought nothing — "more context" and
  "more time" are cousins, and one is already dead.
- Long-context degradation on a 27B is real; retained history may be noise, not signal.
- A single public run cannot rank it (B35). The structural oracle is cheap though:
  `history_messages` should rise by roughly half and `prompt_tokens` should climb toward 48,128;
  if they do not move, the knob did not deliver, same shape as P1 discipline everywhere else.
  ⚠️ A second reading belongs in the same pass: `prompt+completion` must stay under 65,536 on
  every request. The worst case observed today is 39,382; at the new budget it would be 60,117.

## 2. RESET does not lose the level (closes the full_reset question)

All six RESETs in `duck-v10`'s event streams keep the level, including the two discriminating
cases where the game was PAST level 1:

```
re86 L1->L1 (action 101)   sp80 L1->L1 (31)    tr87 L1->L1 (129, 258)
tu93 L2->L2 (30)           tu93 L3->L3 (47)
```

n=6, two above L1. The "stall retries might full-reset the game" candidate is closed — the retry
path keeps progress.

## 3. ACTION7 is offered and has never been used once

Action vocabulary across `duck-v10`'s 1,597 actions: ACTION6/MOUSE 465 · UP 377 · RIGHT 257 ·
LEFT 230 · DOWN 193 · SPACE 69 · RESET 6 · **ACTION7: 0**. Yet the transcripts advertise ACTION7
in **six games — `ar25 bp35 lf52 sb26 sk48 su15` — three of which are named walls** (bp35, sb26,
sk48, per B52). An affordance the sticky games expose and the model has never touched.

⚠️ Not proposed as a prompt nudge: that is B32's lane (52% obedience, induced ≠ better). Recorded
as a fact for any harness-level design that enumerates candidate actions.

## Method

Events + transcripts: `kernels_output("sahasawatt/taaf-duck-v10", file_pattern=...)` — the
`yocybercode/` kernels' outputs are stubbed by the retitle versions, so `duck-v10` is the one
27B run whose artifacts remain fetchable. ⚠️ The `file_pattern` regex must be SUFFIX-anchored
(`.*_events\.jsonl` works); a grouped prefix pattern (`(tr87|cd82).*`) silently matches nothing.
Window/budget numbers cross-read from three independent layers: the setup echo in the banked
driver logs, the ANALYZER STATUS lines in transcripts (935/935 identical), and the usage rows'
`prompt_tokens` distribution.
