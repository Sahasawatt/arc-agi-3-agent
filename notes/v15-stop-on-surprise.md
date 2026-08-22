# v15 design — stop-on-surprise batch execution

Status: **ABANDONED, 2026-08-21, same day it was drafted.** Two readings below turned out to be
wrong, and the second one kills the design rather than adjusting it. Kept in full, with the
corrections inline, because the negative result is the useful part: it stops a commit run being
spent on this.

## VERDICT FIRST

1. **The premise was false.** "The batch path runs unguarded" came from reading one line
   (`tool_agent.py:1774`) in isolation. The batch path is already walked action-by-action with
   the no-op guard consulted on every one, the board signature refreshed after every one, and two
   working mid-batch breaks. Nothing needed building there.
2. **The remaining idea has no harness-visible definition.** A "surprise" is a mismatch against
   the model's *expectation*, and the harness never sees an expectation. Every substitute
   condition either never fires or fires on the wrong games.
3. **And the cost argument runs the wrong way.** A batch cap does not save actions when the model
   is right — it re-issues them. It only saves actions when the model changes its mind after an
   intermediate observation. What it always spends is **turns**, and R19 lane A measured that all
   50 game-runs consume their full 7,920s clock. So a global cap trades saved actions on games
   that guess wrong against lost actions on games that guess right — and **28 of 50 completed
   levels already score the 115 cap**, i.e. the efficient games are exactly the ones that would
   pay.

Original draft follows, corrected in place.

## Why this and not a prompt

R19's transcript lane found the one failure shared by the corpus best and worst trajectories:
**committing to a large batch of actions on an unverified state-transition model.** `ft09`
(47.62, the best score in the corpus) ends at level 5 firing a **35-click blind batch** on an
assumption it never checked — *"Cycle assumed p → M → green (as in prior levels)"* —
`level_completed: False`, run over.

The prompt-shaped version of this fix is the axis that has lost every time it was measured
(v12 brevity 3.72 against v10's 4.71; v9's hard cap 0.22). So the fix has to live in the
harness, where it does not depend on the model choosing to comply.

## The seam

`inference/agent/tool_agent.py` in the anim bundle
(`jakobbrggen/taaf-kaggle-source-anim-20260807-anim`):

- ~~**Line 1774: `if len(normalized_actions) == 1:`** — the existing hard no-op guard applies
  **only to single actions**. The batch path runs unguarded.~~ **WRONG — corrected by reading
  lines 1842-1887.** That line is a fast path for the single-action case, nothing more. The batch
  path (1853-1887) already:
  - walks the batch **one action at a time**, deliberately, so the guard can block individual
    no-ops inside it — the code says so in its own comment at 1842-1849;
  - consults `is_known_noop` before **every** action (1855-1861);
  - calls `observe()` after every executed action with `board_changed` and `animated`
    (1873-1880);
  - **refreshes the board signature and level after every action** (1881-1884);
  - and already **breaks mid-batch** on two conditions: an action that did not execute
    (1869-1871), and a terminal result (1885-1887).
- The refusal payload the single-action guard returns carries `executed: False`,
  `requested_count`, `executed_count`, `stopped_early: True`, `stop_reason: "known_noop"`, and a
  human-readable `stop_detail` (lines 1782-1800); `_aggregate_action_batch_result` (1889+)
  assembles the same shape for the batch case.

So the transport was never missing. **The mid-batch stop machinery is complete and working.**
What is missing is a stop *condition* — and that is where the design dies, not where it starts.

## Why no stop condition exists

`ft09`'s 35-click batch would have tripped neither existing break: each click almost certainly
reported `executed: True` and `board_changed: True`. What was wrong was *which colour came next*
— a claim about the model's own state-transition assumption. The harness has no access to that
assumption, so it cannot detect its violation.

Substitutes considered and rejected:

- **Effect-class change** (stop when `board_changed` / `animated` flips mid-batch) — does not fire
  on `ft09`, whose clicks all changed the board. Fires constantly on games whose mechanic
  legitimately alternates.
- **Exact board-signature match** — `board_signature` is an exact hash and every action changes
  the board, so a strict reading never fires inside a batch at all.
- **Batch-size cap while a level is new** — has the cost problem in the VERDICT above, and
  `ft09` was **49 steps in** when it fired the fatal batch (its own turn header reads
  `Current state: step 49, level 5`), so "new level" would not have caught it either.
- **An `expect=` argument the model passes to `action(...)`** — puts the expectation back in
  reach, but only if the model chooses to use it. That is the prompt axis, which is 0-for-2
  measured (v9 0.22, v12 3.72).

## One thing worth keeping from this dig

The system prompt **actively invites the fatal behaviour**:

> `action(...)` accepts an ordered list of one or more actions. Once your code has selected a
> reliable sequence, it is often useful to batch it.

Nothing forces "reliable" to have been established. This is a prompt-level observation about a
prompt-level cause, so acting on it means the losing axis again — but it does explain why the
behaviour shows up in the best trajectory as readily as the worst: the harness asked for it.

`inference/agent/noop_guard.py` is the precedent for the whole shape: a small, bounded,
per-level memory keyed on `(level, board_signature_before, action_signature)`, consulted before
an action reaches the environment, with `observe()` recording outcomes and explicitly
*un-recording* one when later evidence contradicts it (lines 67-76).

## The rule

Execute a batch action-by-action as now, but **stop at the first action whose observed
transition contradicts what the same action signature produced from a similar state earlier in
this level**, and return `stop_reason: "unverified_transition"` with a `stop_detail` naming the
action, the expected result, and the observed one.

Properties that make this worth trying where a prompt is not:

- It does not reduce generated tokens, cap output, or ask the model to be brief — all measured
  dead (v9, v12, R17).
- It costs the model nothing when its transition model is correct: a batch whose actions all
  behave as before runs to completion untouched.
- It converts a wasted 35-action commitment into 1-2 actions plus an observation, which under
  `min((baseline/actions)^2 * 100, 115)` is worth more than the batch was ever going to be.
- The reuse of `stop_detail` means the model is *told* what surprised the harness, which is the
  disconfirming evidence R19 found it explains away when it has to notice on its own.

## Open, before any of this is built

- **What counts as "a similar state"?** `board_signature` is an exact-match hash, so a strict
  reading almost never fires inside a batch (every action changes the board). The condition
  probably has to be keyed on the *action signature* and its *effect class* (changed / unchanged
  / animated), not on an exact board hash. UNRESOLVED — this is the crux and it decides whether
  the guard fires usefully or never at all.
- **False stops are the risk.** A game whose mechanic legitimately alternates would trip this on
  every second action. The `noop_guard` precedent handles the mirror-image problem by dropping a
  recorded entry once evidence contradicts it; something similar is needed here, or the guard
  becomes the new `lf52`.
- **Adoption.** R8 recorded that duckmod's patches against the June-era tree had **zero
  adoption** on the current bundle. Any patch must be verified to actually take effect in the
  running kernel — the same class of check `duckv14` now enforces with its post-loop
  `assert _kv_injected`.
- **It cannot share a run with v14.** R9 says single runs already struggle to rank designs; two
  changes in one run cannot be told apart afterwards.

## Where it sits in the queue

Behind `duckv14` (one flag, tests the R19 KV hypothesis, already built and both-ways verified)
and behind whatever the first post-quota run is spent on. `duckv13` (animation-retrieval
discipline, prompt-level) is also built and unrun, and is on the losing axis — prefer these two.
