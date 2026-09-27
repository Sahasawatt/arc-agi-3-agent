# thui-b103 OneBoard — pre-registered 2026-09-27, before any GPU run

Base: `thui-a5-mtp0k7s28-full25-r1` (B81), full clock (7,920 s), all 25 public games. Treatment: one cell-9 graft
only. Every `analyze()` call appends a user message carrying the current board as a base64 PNG
(`ToolAgent._build_user_message`, anim bundle `tool_agent.py:1377`), and the persistent history keeps those messages,
so each request re-sends every older board still inside the window. The estimator `_estimate_tokens`
(`tool_agent.py:611`) json-dumps the whole payload, so an image is charged `len(base64)/3` and pushes text history out
under `_trim_messages_for_context` (`:2056`). The arm wraps that trim: every user message except the newest
image-bearing one loses its image parts (text kept, the `Current grid image:` pointer removed). The control carries
the SAME wrapper with the flag off: it passes the history through unchanged and prints the same counters. Changed
cells must be exactly `[0, 9]` on both.

Source of the idea: agentfix F1 in the public notebook `scottlegrand/taaf-flashnext-sheetu12b-0922`, whose author
reports a median of 8 obsolete boards per request, ~26% of the budget. **Neither figure is re-derived here** — the
control arm's counters are what measure it on our chassis. Only the first half of F1 is carried: the author also
replaced the image token charge with a flat cost; this build does not, so the ONE remaining image is still
over-charged. That is deliberate (one change) and it bounds the effect from below.

0-GPU evidence already in hand: `test_b103_graft.py` against the real anim-bundle `ToolAgent` — 15 checks green,
including *under a budget that forces eviction, the arm keeps 18 history messages where the original keeps 6*
(synthetic sizes: 6,000-char base64 per board). Teeth: five graft mutations (no strip · pointer kept · newest board
stripped too · wrapper unwired · original trim handed the unstripped list) each turn the suite red; graft restored
byte-identical (`cmp`) after the round.

## VALID / VOID (plumbing, per arm)

VALID only if `THUI_B103_GRAFT ok oneboard=<True|False>` appears once and the last `THUI_B103_STATS` line shows
`trims >= 1000` and `images_seen >= 1`. On the arm `images_dropped >= 1`; on the control `images_dropped == 0`.
Anything else is VOID and nothing below is read. The STATS line prints every 200 trims, so the last one undercounts
by < 200 trims; ratios, not totals, are what is read.

## Mechanism bar (read before any score)

From the control's last STATS line: `obsolete = (images_seen − trims) / trims` (boards per trim beyond the current one).
- **MECHANISM-DEAD** if the control's `obsolete < 1.0` — the history does not carry old boards on this chassis, the
  premise is false, and the arm's score is not read as evidence about this lever.
- Otherwise read the arm's `est_tokens_after / est_tokens_before`; the mechanism **fires** if it is `<= 0.85`.

## Outcome bar (one matched pair; power UNMEASURED)

Both arms pushed together, same notebook source except the flag. Per-game levels through `eval/rank_runs.py`
(arm vs control, `--single-baseline` with this file named as the reason).
- **KILL:** arm total levels `<=` control total levels.
- **PROMOTE to a second pair:** arm total levels `>=` control `+ 3` (the B81 pair-to-pair level spread is not banked
  here; +3 is chosen as a floor, not derived — say so when reading).
- **INCONCLUSIVE:** anything between. No hidden submission on INCONCLUSIVE.
- **PASS** only after the second pair: pooled `rank_runs.py` BETTER at p < 0.05 over both pairs.

Secondary, descriptive only, never a verdict: `history_messages:` per request from the transcripts (arm median
should exceed control's if the freed budget is used), actions, tokens per action, hidden score if submitted.

## Known confounds, carried

- The model may USE old boards (compare two frames by eye). Dropping them can cost that. The bar measures the net.
- Freed budget refills with OLDER text turns, not new information; B92 showed stored reasoning is load-bearing, B100
  showed selective removal was killed — so the sign of "more old text" is not known in advance.
- Tufa's own write-up (kaggle discussion 717133) reports that more frames in context did not help small models; that
  is consistent with this lever and says nothing about its size.
