# v16 — push the diff instead of making the model compute it

Status: **DESIGN, not built.** 2026-08-21, found in the same loop that abandoned v15
(`notes/v15-stop-on-surprise.md`). This is the strongest lever the R19 revision produced, and it
is the only one so far that is harness-level, push-based, and aimed at a measured waste.

## The waste

R19's transcript lane measured the model misreading **its own tool output** — `before_frame` /
`history` indexing confusion **8+ times in `sk48`, 6+ in `cn04`**, each costing a full turn
(`sk48`:2054-2320, 3242-3270). It reads the *board* correctly; what it gets wrong is the
arithmetic of comparing two frames.

## Why prose already failed at this

The system prompt is **not** vague about it. It is unusually careful:

- `prompts.py:54` — "Each `history[i].frame` is the frame after `history[i].action`"
- `prompts.py:55` — "when `history` is non-empty, `history[-1].frame` is the same latest/post-action
  board as `current_frame`. **It is not the previous board**"
- `prompts.py:90` — "For the most recent change, compare `previous_frame` to `current_frame`, or
  `last_transition.before_frame` to `last_transition.after_frame`"

Line 55 exists *because* someone already hit this and tried to fix it with words. The confusion
still happens 8+ times per game. That is another datapoint for the pattern this campaign keeps
re-learning: **prose does not bind behaviour** (v9 0.22, v12 3.72, and now this).

## The gap

Two facts, both read from the bundle source:

1. **The sandbox gives the model no diff tool.** The globals injected into the model's Python
   (`python_tool_sandbox.py`:341-354) are exactly: `current_frame`, `latest_frame`, `history`,
   `transitions`, `last_transition`, `previous_frame`, `last_action_frame`, `last_action`,
   `valid_actions`, `last_action_result` — plus `action()` and `animation()`. **There is no
   `diff()`.** The prompt instructs a comparison the runtime provides no helper for, so the model
   hand-rolls index arithmetic on every single turn.

2. **The harness already computes diffs — it just does not ship them for ordinary actions.**
   `_compact_action_result` (`tool_agent.py`:1653-1691) returns `board_changed` as a **bare
   bool**. But at 1688-1690, when the action produced an animation and animation-awareness is on,
   it attaches a full `animation` dict carrying per-frame `changed` and `bbox`. So the machinery
   to compute and deliver a compact change summary exists and is **wired only to the animated
   path** — which is the minority of actions.

## The change

Attach a compact changed-cell summary to **every** action result, next to `board_changed`, in the
same shape the animation timeline already uses — so the model meets one representation, not two.

### The parts already exist and are already generic

`inference/utils/animation.py` carries three helpers that are **not animation-specific** despite
living there — each takes plain grids or cell lists:

- `_diff_cells(before, after)` (:143) → `list[(row, col, before_value, after_value)]`
- `_bbox_text(cells)` (:156) → the bounding box as text
- `_format_changes(cells, budget)` (:162) → changed cells **grouped by colour transition, one
  compact line each**, and past the budget a `"... N further changed cells omitted"` line (:175)

So the "will a diff eat the context?" question this note originally left open **is already
answered in the code**: `_format_changes` takes a budget and degrades gracefully. Reuse it rather
than inventing a cap.

### Wiring point — NOT `_compact_action_result`

Corrected after checking: `_compact_action_result` (`tool_agent.py`:1653) never sees a grid. It
reads `board_changed` as a value the environment already computed (:1661), so the diff cannot be
built there.

The **call sites** do have both grids, because they already load them to keep the no-op guard's
signature current:

- `:1737` — `board_signature(current_frame.grid)` before the action, i.e. the *before* grid is in
  scope;
- `:1881-1884` — `load_runtime_state(state_path)` returns `refreshed_frame`, and
  `board_signature(refreshed_frame.grid)` is taken from it, i.e. the *after* grid is in scope.

Both the single-action path and the per-action step of the batch loop pass through this. Build the
summary there and attach it to `sub_compact` / `compact_payload` before they are returned. No new
state loading, no extra environment work — the frames are already in hand for another reason.

### CORRECTION — `last_action_result` is PULL, not push

The first draft of this note claimed attaching the summary to `last_action_result` made it push.
**It does not.** Measured against a real transcript: a `[TOOL RESULT: python]` block contains
**only the stdout of the model's own code**. `last_action_result` is a Python object living in
the sandbox globals (`python_tool_sandbox.py`:354) and reaches the model's context **only if the
model prints it**. Attaching a field there has exactly the weakness that sank `animation()` in
`cn04`, which called it **zero** times.

### The real push channel, and it is already proven to work

`_build_user_prompt` (`tool_agent.py`:1391-1460) composes the user message the harness sends
**every turn**, from `previous_step_summary`:

```
1423  "The code executed N actions in the previous sequence."
1430  "Executed actions: ..."
1438  "You are still on the same level."
1441  describe_animation(previous_step_summary.get("animation"))   <- a diff, pushed, unasked
1448  self._animation_hint_line(...)                                <- the stuck nudge
```

Two things follow. First, **the harness already pushes a change description unasked — but only
for animated actions** (1441-1443). Second, this channel demonstrably reaches the model: the
hint at 1448 is the nudge R19 measured firing **7 times in `sk48` with the model responding to
every one**. Whatever else is true, text delivered here is read.

So v16 is: attach the diff to the compact payload at the call site where both grids are in scope,
then render it as a line in `_build_user_prompt` beside `describe_animation` — a
`describe_changes(...)` sibling. Two edits, mirroring a pattern already in the file, on a channel
with evidence of delivery.

Why this is worth a run where v15 was not:

- **Push on a proven channel** (above), not a helper the model has to choose to call.
- **It removes work rather than adding rules.** No cap, no refusal, no budget — the failure mode
  is a turn spent on arithmetic, and the fix is to have already done the arithmetic.
- **It does not touch the losing axis.** Generated tokens are unchanged; nothing is shortened,
  capped, or discouraged.
- **It reuses proven code** rather than inventing a condition, which is precisely where v15 died.

## Open before building

- ~~**Size.**~~ **Answered** — `_format_changes(cells, budget)` already bounds it and emits an
  explicit omission line. Pick the budget; do not build a cap.
- **Adoption must be asserted, not assumed.** R8 recorded duckmod's patches achieving **zero
  adoption** against the current tree. Any patch needs the `duckv14` discipline: a hard failure
  if it did not take effect, so a v10-shaped result cannot be misread as "this lever does not
  work".
- **It cannot share a run with v14.** R9 — single runs already struggle to rank designs.
- **Context cost is now a per-turn LINE, not a payload field.** With the corrected push channel
  the addition is one rendered line in the user message, sized by the `_format_changes` budget we
  pick — the same footprint `describe_animation` already occupies. The earlier framing of this
  question (how much bigger does `last_action_result` get) is void along with the pull design.
  Still worth doing before building: render a sample line from a real v10 frame pair and read its
  length, rather than assuming the budget default is sane. NOT YET MEASURED.
- **`board_changed == False` is not "nothing happened."** `prompts.py`:67 warns that an animation
  key with `board_changed == False` still means the action did something. A diff attached to a
  no-change action would be empty and could reinforce exactly the wrong reading — so on
  `board_changed == False` with an animation present, the summary must defer to the animation
  timeline rather than report "0 cells changed".

## Predictions, falsifiable

If built and run alone against v10:

1. `sk48`'s `before_frame`/`history` confusion count drops from 8+ toward 0 — checkable by
   grepping the new run's transcript for the same contradiction language.
2. Turn count spent on state re-derivation falls, so actions-per-turn rises.
3. If R19's revision is right that this is 6-8 wasted turns per game, the games nearest a level
   boundary gain first — score moves before any new game starts scoring.

If the confusion language persists at the same rate, the finding is refuted and the waste is not
the indexing arithmetic.
