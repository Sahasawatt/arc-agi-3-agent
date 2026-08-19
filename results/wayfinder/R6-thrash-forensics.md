# R6 — thrash forensics on the 9 zero-score Bucket-C games

Read-only transcript forensics, per R1-forensics.md's bucket table. Sources: 9 transcripts at
`%TEMP%\duckmodout\transcripts\<game>_p0.txt` (`cn04-2fe56bfb`, `m0r0-492f87ba`, `sc25-635fd71a`,
`sk48-d8078629`, `tn36-ef4dde99`, `tr87-cd924810`, `vc33-5430563c`, `wa30-ee6fef47`,
`ka59-38d34dbb`), each sampled beginning/middle/end by 9 parallel sonnet subagents (this repo's
own hand-built driver/game-mechanic notes in `CLAUDE.md` were handed to each agent as reference,
never `environment_files/`). `environment_files/` was not touched. Every claim below traces to a
turn/line citation the subagent verified against the actual file; a handful of items are flagged
`(inferred)` where the transcript is suggestive but not conclusive — see each game's opacity note.

The agent under study is the **duck-mod LLM agent** (Qwen 27B in a Python-REPL loop, prompted
with `hud_mask(history)` and `TransitionGraph()` helpers) — a completely different system from
this repo's own hand-built per-game drivers. All 9 games in this report were stuck on **level 1**
for the entire run (ratio 2.07x–13.93x of the human baseline, 0 score, 0 levels cleared).

## 1. Per-game findings

### ka59 (58 actions, 2.07x baseline, 51 turns)
- **Controls**: partial. Correctly learned LEFT/RIGHT/UP/DOWN move one of two "rings," and
  separately discovered (turn 29/action 48) that a MOUSE click swaps the two rings' center
  colors. Direction magnitude and "blocked" conditions kept flip-flopping turn to turn.
  Never approximated the real ferry-swap mechanic (piece teleports to a clicked dot, dot lands
  on the piece's old square) — every click landed on an existing ring or the frame border, never
  a distinct empty cell.
- **Win condition**: wrong_hypothesis, never converged (line 15289-15290, final turn: "So
  neither ring's center matches the frame's content.")
- **World model at cutoff**: stale — the harness's persisted "world model" field is written
  **once** (turn 2, line 1105) and is byte-identical at turn 6, turn 20, and turn 38 (lines 2405,
  7738, 14845), even though the model's own in-turn reasoning kept evolving and contradicting it.
- **Action loop**: yes — same MOUSE coordinates reused turns 7/19, 10/11/29, 28/32/35, with no
  persistent record of what was tried. Not self-aware (voices "this is confusing" repeatedly,
  never "I am repeating myself"). At actions 57-58 it moved its own correctly-placed ring back
  OUT of the target frame while trying to "block" it — active regression.
- **REPL usage**: computation (segmentation/boundary math, transitions[] tracing every turn) but
  none of it persists — the same coordinate arithmetic, including manual column-counting, is
  redone from scratch each turn.
- **Failure mode**: frozen world-model field + per-turn from-scratch re-derivation → hypotheses
  formed, tested, and silently discarded instead of accumulating.
- Opacity: clear. Confidence: high.

### cn04 (99 actions, 3.41x baseline, 63 turns)
- **Controls**: partial. UP/DOWN/LEFT/RIGHT (3-cell moves) nailed by turn 2. SPACE (a
  rotation+reposition action, matching the reference's "rotator") wasn't even tried until action
  32 — a third of the whole budget spent on pure directional movement first. Once tried, SPACE
  was correctly recognized as *not* a direction within 1-2 presses, but its exact transform was
  re-derived from eyeballed coordinates every turn (never logged), producing self-contradictory
  readings late (turn 57, line 18114: two different SPACE presses landing on positions the model
  itself flags as inconsistent). MOUSE was in the action list every turn but **never once
  actually invoked** — 63/63 mentions are boilerplate, 0 real calls.
- **Win condition**: wrong_hypothesis through several theories ("move to green container" →
  "collect red footprint pattern" → "align piece's hole with green container's hole"); the last,
  closest theory was still unvalidated at cutoff.
- **World model at cutoff**: the harness's persisted world-model slot is **empty every single
  turn, 1 through 58** (content_chars:0 throughout) — worse than ka59's "frozen at turn 2," this
  one was never populated at all. Live reasoning (uncaptured [THINKING] channel) was reasonable
  and used moment-to-moment, but nothing accumulated structurally; continuity came only from a
  bounded rolling context window (15-47 messages, never the full history).
- **Action loop**: yes, two shapes — a full 4x-SPACE rotation cycle that returns to the start
  orientation (self-recognized at turn 52), and — separately — a **silent mid-run GAME_OVER at
  action ~75** that reset the board to the exact turn-1 layout while the step counter kept
  climbing, erasing ~75 of 99 burned actions. The model took a full turn to even recognize the
  reset had happened (turn 44, line 14298: "I'm confused").
- **REPL usage**: mixed/light computation, never structured search; `TransitionGraph()` — 0
  real instantiations anywhere in the file despite being offered every turn.
- **Failure mode**: discover-then-thrash-then-reset — slow control discovery, unlogged rotation
  transform causing self-contradiction, then a silent GAME_OVER erased most progress with ~24
  actions left to redo it before wall-clock ran out too.
- Opacity: partially_opaque (GAME_OVER trigger cause is the model's own unverified guess, not
  established). Confidence: high.

### sk48 (174 actions, 2.85x baseline, 86 turns)
- **Controls**: partial, and arrived very late. UP/DOWN quantized ±6-row jumps figured out at
  action 77 (less than halfway). The core mechanic — moving while "connected" to a block drags
  it — was only discovered on the **second-to-last recorded action (175 of 175)**, one action
  before cutoff.
- **Win condition**: wrong_hypothesis, two incompatible theories ("collect blocks in
  red→green→blue order" then, 160+ actions later, "rearrange blocks into a row matching a panel
  icon order"), neither ever confirmed by score.
- **World model at cutoff**: stale — only **3** `[ASSISTANT]` world-model blocks exist in the
  entire 86-turn transcript (all within the first 4 actions); the harness's persisted field is
  byte-identical from action 4 through action 175, still reading a plan the model's live
  reasoning had abandoned two goal-theories ago.
- **Action loop**: yes — align/overshoot/correct cycles, a burst of 10 consecutive no-op DOWN
  presses at a boundary, late-game drag/undo of the same block. **Self-aware** — explicit "I keep
  going back and forth" (line 6419), "I've been going back and forth" (line 6655), "moving the
  blue block around but not making progress" (line 23654) — but never escapes via the provided
  anti-loop tooling.
- **REPL usage**: mixed — one genuine self-diagnosis-and-fix moment (caught its own
  segmentation filter picking up a static HUD-panel duplicate of the player sprite, rewrote the
  filter), but mostly single positional print-and-act probes; `TransitionGraph`/`hud_mask` never
  called.
- **Failure mode**: scaffold context freeze (world model pinned to a turn-4 plan for 171 straight
  actions) compounding a genuinely hard-to-read mechanic (connect-and-drag) that only surfaced at
  the very end of the budget.
- Also noted: `ACTION7` is listed in `valid_actions` every turn but errors
  `"Unknown action at index 1"` when called (line 2844-2866) — a harness/environment mismatch
  independent of the model's reasoning.
- Opacity: clear. Confidence: high.

### sc25 (151 actions, 4.19x baseline, 75 turns)
- **Controls**: partial, never stabilized — a track-block pair and grid-cell MOUSE clicks were
  both engaged with, but re-described 3+ mutually inconsistent ways over the run; a 14,366-char
  reasoning turn (turn 42) tries and fails to reconcile a claimed color cycle.
- **Win condition**: wrong_hypothesis — 5+ falsified goal theories, ending on one that is
  **actively self-contradictory**: driving track blocks to the left end as the target, 90 turns
  after discovering (turn 24, line 7114) that reaching the left end **causes GAME_OVER**.
- **World model at cutoff**: garbage — final turn asserts "Game still over" one line after its
  own printed tool output shows `game_over: False`.
- **Action loop**: yes, severe — the identical 4-cell MOUSE click batch repeated **11+ times**
  across roughly a third of the run (turns ~37-57), each time narrated as a fresh attempt. Not
  self-aware of the aggregate pattern, though it notices individual failed attempts in isolation.
- **REPL usage**: mixed, degrading — real diffing early, devolving into unproductive manual
  bookkeeping and, in the back third, little more than a vehicle for re-emitting the same click
  batch.
- **Confirmed trap** (this repo's own documented sc25 hazard): the **action-index-1-absorbed**
  bug fired cleanly twice — the very first action of the run (turn 1, a MOUSE click) returns
  `board_changed: false` and the model permanently concludes that click target is inert (turn 2,
  line 843); the same thing happens again on the first action after the second GAME_OVER
  (turn 59/60, lines 20159-20361). The model never once reasons about multi-frame animation or
  "first action of a life" as a concept anywhere in its own text.
- **Failure mode**: goal-hypothesis thrashing on a toggle-grid/move-counter puzzle, compounded by
  falling into the action-index-1-absorption trap at both observed life starts, and never using
  anti-loop tooling to permanently retire a disproven hypothesis.
- Opacity: partially_opaque (one 5-click batch's individual absorption status is unrecoverable
  from the transcript). Confidence: high.

### tn36 (182 actions, 5.69x baseline, 57 turns)
- **Controls**: correct — MOUSE-click toggling of independent horizontal/vertical bar segments
  on 5 buttons, discovered by action 2-3 and used consistently and correctly the entire run. The
  cleanest controls-model result of all 9 games.
- **Win condition**: wrong_hypothesis — 10+ mutually contradictory guesses at which
  buttons/bars two yellow "template" shapes encode, each falsified by no score change, with no
  narrowing over the run (turn 47, line 16211: "I've now tried: 29+ button combinations... None
  of these have worked").
- **World model at cutoff**: stale, and actively wrong — the final carried belief states
  "Clicking on the blue player restarts the game" as fact, contradicting its own earlier,
  correctly-tested finding (turn 7) that the click did nothing (the belief is a coincidental
  artifact of timing with the real GAME_OVER trigger, below).
- **Action loop**: yes, a hypothesis-thrash rather than literal repeats — 40+ distinct manual
  button-combination guesses, no programmatic search ever written. **Self-aware and explicit**
  ("That's 9 out of 32 possible combinations... I still have 23 more to try," "I've now tried
  47+ actions and nothing has worked") but never changes method in response.
- **REPL usage**: mixed — real state-inspection code (segmentation diffs, per-button color
  extraction) but the actual combinatorial search over button states is done by hand, one guess
  per turn, despite the system prompt explicitly recommending exhaustive/BFS search for exactly
  this shape of problem.
- **The load-bearing finding**: a shrinking HUD-classified bar (correctly identified per the
  system prompt's own "don't mistake an edge bar for gameplay" warning) turned out to be a
  **hard per-life action budget** — `GAME_OVER` fired at actions ~61 and ~123 (62 apart, matching
  the bar's initial 61-pixel width), each time wiping all button-state progress and restarting
  the level. The model only explicitly diagnosed this *after* the second reset (~action 125 of
  183) and never adjusted its exploration pace to respect it.
- **Failure mode**: correctly following the prompt's own HUD-classification advice backfired —
  it stopped the model from ever testing the bar as a life/action-budget signal, costing two full
  resets, on top of un-narrowed manual hypothesis churn on a 5-button/10-bar (≥32-state) puzzle.
- Opacity: clear. Confidence: high.

### tr87 (240 actions, 4.44x baseline, 44 turns)
- **Controls**: partial. Cursor move (LEFT/RIGHT) and symbol-cycle (UP/DOWN) correctly
  identified by turn 3 — fast and right. But which of 5 dial positions are "locked" vs editable
  **oscillated three times**: "locked" at action 20 → refuted at action 136 ("I was wrong
  earlier") → re-asserted "locked" at action 199 → refuted again near cutoff — never reconciled,
  each time with no reference back to the prior contradiction.
- **Win condition**: absent — every matching hypothesis (bottom row vs. top-panel symbols, in
  various orderings/subsets) was self-flagged as inconsistent; a 49-combination brute-force
  search was launched but its stop condition **omitted `game_over`** (contradicting the system
  prompt's own explicit instruction to check it) and the search never produced a verdict.
- **World model at cutoff**: stale — final turn re-derives cycle data already partially gathered
  (and partly retracted) ~100 actions earlier, presented as new, with no reference to the earlier
  contradiction.
- **Action loop**: yes — the same 5 cursor positions' cycles re-explored from scratch at least
  twice (once pre-reset, once post-reset, no memory carried across). Not self-aware of the loop
  as a loop (voices confusion, never "I've seen this before"). Confirmed: **every** occurrence of
  `TransitionGraph(`/`hud_mask(` in the file is inside boilerplate, zero real calls.
- **REPL usage**: mixed — hash-based object tracking and one real (buggy) combinatorial search
  exist, plus a genuine self-diagnosed bug (its own cycle-detection code conflated "position not
  yet probed" with "locked") — but the model then **talked itself back out of its own correct
  diagnosis** one paragraph later, reverting to the wrong belief.
- A GAME_OVER/reset around action ~128 queued an action that executed *after* the reset, landing
  the cursor somewhere unexpected — the model spent multiple turns (lines 5910-8069) confused
  about this alone.
- **Failure mode**: unstable, thrice-oscillating belief about which controls are even editable,
  never reconciled across a mid-run reset, plus a brute-force search whose stop condition ignored
  the documented termination signal.
- Opacity: clear. Confidence: high.

### vc33 (34 actions, 4.86x baseline, 27 turns — full transcript read)
- **Controls**: partial but **stable and correct as far as it goes** — the only game where a
  correctly-identified controls model held with zero contradictions the whole run: exactly two
  interactive objects (two blue 4x4 blocks) drive a 4-state ladder (A→B→C→D forward/reverse);
  everything else (fills, bars, other blocks) confirmed inert by turn ~18 and never revisited
  incorrectly.
- **Win condition**: wrong_hypothesis — 6 distinct theories tried and refuted (reach state D,
  fill the board gray, timer-run-out, specific click sequence, positional sub-effects on the
  blocks), all falsified by `level_completed` staying False across all 34 actions.
- **World model at cutoff**: **reasonable_and_used** — the one clearly positive case among the
  9: the mechanics portion of its model is accurate and actively drives each next probe; the
  goal-model portion is honestly flagged "Unknown" rather than fabricated.
- **Action loop**: yes but bounded (only 2 real controls exist, so re-visiting them isn't
  necessarily wasteful) — from action ~18 on it is re-deriving an already-confirmed model rather
  than finding new information. **Self-aware**, explicit "I'm stuck. Let me think about this
  differently" (line 6963) and "I'm really stuck" (line 7022).
- **REPL usage**: mixed — real diffing/bookkeeping code throughout; anti-loop tooling never
  called (same as every other game); no BFS/search code despite the recommendation.
- **Open question, explicitly flagged by the subagent**: whether this is a genuine failure or a
  ratio-inflation artifact of a tiny (7-action) human baseline is **not fully resolvable** — the
  model did substantive, correct negative-evidence-gathering (both state extremes ruled out,
  every other object individually confirmed inert), which argues for genuine difficulty rather
  than "any behavior overshoots a trivial baseline." But the transcript cuts off on an HTTP
  timeout, not a verdict, so a later-discovered mechanic outside the tested space can't be ruled
  out from this file alone.
- **Failure mode**: exhaustive-but-incomplete probing of a small confirmed state space — the
  "what is interactive" sub-problem was solved correctly and durably, but no trigger for
  `level_completed` was ever found within it.
- Opacity: clear. Confidence: medium (explicitly lower — see open question above).

### wa30 (260 actions, 3.66x baseline, 64 turns)
- **Controls**: partial. Directional movement nailed in ~2 turns; SPACE produced two apparently
  real state changes early and was narrated as "collecting" a box into a "white strip that
  follows the player" — but the model **never recognized this white strip as its own piece's
  body** (exactly the occlusion trap the reference predicted), instead treating it as a separate
  beam/HUD object. Built and discarded collect/place/toggle theories for SPACE, at one point
  concluding (turn 29, line 8853) that "no box has been collected yet," contradicting its own
  turn-14 claim.
- **Win condition**: wrong_hypothesis throughout ("collect all boxes" → "deposit into a
  center-bar slot" → "arrange boxes" → "consume the entire center bar by moving through it"),
  never articulating anything close to the real carry/drop-into-frame mechanic.
- **World model at cutoff**: garbage — the persisted world-model field is written once at turn
  1 and is **byte-identical ~30 turns and ~185 actions later** (turn 31); only 1
  `[ASSISTANT]` block exists in the whole 64-turn file, and `content_chars: 0` in 112 of 113
  recorded model turns.
- **Action loop**: yes, two shapes — (1) large blind navigation batches
  (`action(['RIGHT']*13)`, `['UP']*28)`, etc.) sent without per-step verification, based on a
  repeatedly-wrong pixels-per-move estimate, producing a bouncing trajectory across all four
  board edges; (2) a late-game box-color swap cycle (moving through the same box pair repeatedly
  just flips their colors back and forth with zero net progress) that the model **does**
  correctly recognize as non-productive near the end (line 17481-17483). Self-aware
  ("I've been moving in circles," line 8318) but doesn't correct method.
- **REPL usage**: mixed, weighted toward pure action emission — genuine per-turn segmentation
  inspection, but no BFS/search code anywhere in the file and, as with every other game, zero
  real `TransitionGraph`/`hud_mask` calls.
- **Inferred (medium confidence)**: a shrinking HUD-classified pink bar (64px → 63 → 59 → ...)
  is consistent with a per-life action budget exhausted around action ~200, matching a
  `GAME_OVER` that resets the board to the exact turn-1 layout — but the model itself
  misattributes the reset to "colliding with a box" (turn 32, line 9391), not to the timer, so
  this game may share tn36/tr87/m0r0/sc25/cn04's silent-reset pattern without ever correctly
  diagnosing it.
- **Failure mode**: occlusion-driven misdiagnosis of its own piece body prevented ever forming a
  stable grab/carry/drop model; combined with blind unverified action bursts and (likely) a
  silent life-reset that erased ~200 actions of progress.
- Opacity: partially_opaque (GAME_OVER cause is inferred, not confirmed in-transcript).
  Confidence: medium.

### m0r0 (418 actions, 13.93x baseline — worst thrash in the whole 25-game run, 48 turns)
- **Controls**: partial, and **discovered correctly multiple times, then abandoned**. Turn 4
  (action 6) correctly identifies non-mirrored joint movement matching the reference's twin-piece
  hint exactly ("RIGHT: moves left square right and right square left (converging)..."). Turns
  17-19 correctly re-derive independent per-piece movement onto different rows. Then, at turn 31
  (action 353), the model **explicitly discards its own correct hypothesis**: "the blue squares
  are not independent entities... this is getting too complicated. Let me just focus on
  increasing the timer" — reverting to a wrong single-shapeshifting-object model right before
  giving up on controls entirely.
- **Win condition**: wrong_hypothesis, and this is the game's worst and most distinctive
  finding — the model correctly identified a border-pixel "timer" bar's value (~128) as the
  **GAME_OVER (loss) trigger** at turn 25 (confirmed by an actual GAME_OVER at that value), then
  by turns 33-34 was **actively driving toward that same number as a target**: "Current timer:
  98. Target: 128... Let me batch more cycles efficiently" — deliberately chasing its own
  previously self-identified loss condition for the rest of the run.
- **World model at cutoff**: garbage — the final active belief is this unresolved
  self-contradiction (128 = known loss threshold, being pursued as a goal), and the run's last
  tool call times out mid-execution, 30s in, with zero printed output, still chasing it.
- **Action loop**: yes, and this is where most of the 418 actions actually went — **not**
  turn-by-turn play but ~6 large, largely unsupervised `for i in range(N): action([...])` loops
  inside single Python calls (sizes 132, 43, 40, 30, 26, and three of 20), together accounting
  for **roughly 72% of all 418 actions**. Two of these ran the action counter straight into
  GAME_OVER (once via a 30s tool-timeout mid-loop, once via a pointless RIGHT/LEFT cancel-out
  loop). The model notices timeouts *after the fact* ("The code timed out after executing 131
  actions, and the game is now over") but writes the identical unbounded-loop shape again in its
  very last turn.
- **REPL usage**: mixed — real segmentation parsing and one genuine timer-increment
  pattern-mining pass (30-element diff list, turn 34) — but a large majority of the raw action
  count came from blind loops with little/no per-iteration inspection; `hud_mask()` (built
  specifically for exactly this HUD-vs-timer confusion) and `TransitionGraph()` were never called
  once in 48 turns.
- Two separate GAME_OVER events (~action 153, ~action 305) each forced full rediscovery of the
  reset board — a large hidden contributor to the 13.93x blowout beyond the loop/timeout waste
  alone. A ~30-minute, 5-attempt stall (turn 20, action counter frozen at 199) is pure wall-clock
  waste layered on top of the action-count waste.
- **Failure mode**: misidentified its own known loss-condition timer as the win-condition target
  (the exact HUD-vs-gameplay trap the harness's `hud_mask()` tool exists to prevent, and never
  used), repeatedly abandoned a correct twin-piece controls model as "too complicated," and
  issued unbounded action loops with no per-iteration feedback — two of which self-inflicted
  GAME_OVER.
- Opacity: clear. Confidence: high.

## 2. Cross-game failure-mode clustering

Four named modes, each with the games it's confirmed or inferred in (a game can belong to more
than one — these are compounding, not exclusive):

### Mode 1 — Scaffold state amnesia (world-model field frozen or empty)
**Confirmed**: ka59 (frozen at turn 2, byte-identical for 36 more turns), cn04 (empty every
single turn, 1-58), sk48 (frozen at turn 4 for 171 actions), tr87 (content_chars:0 on all 58
`[MODEL RESPONSE META]` blocks; the mandatory "revised world model" instruction is silently
ignored throughout), wa30 (frozen at turn 1 for ~185 actions, content_chars:0 in 112/113 turns).
**Probable, same signature** (contradictory turn-to-turn conclusions consistent with the same
root cause, though the subagent didn't measure content_chars explicitly): sc25, tn36, m0r0.
**Exception**: vc33 — the one game where the persisted model stayed accurate and was actively
used; notably also the shortest run (34 actions), so amnesia had the least time to compound.

**8 of 9 games show this signature.** The mechanism is consistent across every report that
measured it: the harness asks the model to prefix its response with `World model:`/`Plan:` text
that gets captured and re-injected next turn, but the model stops emitting it after the first
few turns (often after 1) — real reasoning keeps happening in the uncaptured `[THINKING]`
channel, but nothing feeds it back structurally, so each turn re-derives (and often
re-contradicts) facts already established earlier in the same run.

### Mode 2 — Anti-loop tooling present in every prompt, used in none
**Confirmed in all 9/9 games, with an exhaustive full-file grep in every report**: zero real
`TransitionGraph()` instantiations, zero `.record()`/`.untried()`/`.path_to_nearest_untried()`
calls, and (outside sc25's action-index-1 case, discussed under Mode 3) minimal/no real
`hud_mask(history)` calls anywhere in any of the 9 transcripts — every match for these tokens in
every file is inside the boilerplate system prompt repeated each turn. This matches and extends
the prior transcript report (`duckmod-transcripts-20260819.md`): 0 `TransitionGraph()` calls and
2 `hud_mask()` calls across all 25 games, now confirmed as 0/0 specifically within the 9
worst-thrashing games. Every game in this report exhibits some form of action-loop or
hypothesis-repetition (§1), and the tool that exists specifically to prevent it went unused in
every case.

### Mode 3 — Silent GAME_OVER / life-reset erasing progress mid-run
**Confirmed**: cn04 (1 reset, ~action 75, erased ~75/99 actions, model needed a full turn to
notice), m0r0 (2 resets, ~actions 153 and 305), tn36 (2 resets, ~actions 61 and 123, each wiping
all button-state progress), tr87 (1 reset, ~action 128, with a queued action executing
post-reset), sc25 (2 resets, ~actions 55 and 148 — see also Mode 4 below).
**Inferred, medium confidence**: wa30 (~action 200, model misattributed the cause).
**Not observed**: ka59, sk48, vc33 (no GAME_OVER surfaced in these transcripts).

**6 of 9 confirmed, 7 of 9 with the inferred case.** In every confirmed instance the model either
took multiple turns to recognize the reset happened at all, or (tn36) recognized it only after
the *second* occurrence, having already burned a full life-budget's worth of actions on the
first.

### Mode 4 — HUD/timer-vs-gameplay misread
Three distinct flavors, none overlapping in mechanism but all in this family:
- **m0r0** (worst case): correctly identified the loss-condition timer value, then *deliberately
  drove toward it as a win target* for the rest of the run.
- **tn36**: *correctly* HUD-classified a shrinking bar per the system prompt's own warning — and
  that correct classification is exactly what stopped it from ever testing the bar as a hard
  life/action budget, costing two full resets.
- **sc25**: the documented action-index-1-absorption bug (this repo's own prior finding) fired
  cleanly twice — the model reads a genuinely no-op first action of a life as proof an
  interaction is dead, and never once reasons about multi-frame animation as a concept.

**3 of 9**, but m0r0 is the single worst game in the entire 25-game run (13.93x baseline) and
sc25's trap is independently confirmed and documented — both disproportionately valuable to fix
despite the smaller game count.

### (Secondary, lower game-count) Occlusion / own-body misidentification
wa30 (clear — its own trailing piece-body mistaken for a separate collector beam), cn04 (partial
— static red pads misread as a dynamic "appearing footprint" mechanic due to piece occlusion),
m0r0 (partial — the twin-piece confusion has an occlusion-adjacent flavor). Folded into the
lever ranking below rather than given its own numbered mode, since only wa30 shows it cleanly.

### Unbounded/blind action bursts (cuts across Mode 2 and Mode 3)
Not a fully independent mode — it's the *mechanism* by which Modes 2 and 3 do the most damage in
the worst-offending games. Clearest in m0r0 (~72% of its 418 actions came from six large,
under-inspected `for` loops, two of which self-inflicted GAME_OVER) and tr87 (a 49-combination
brute force whose stop condition omitted the `game_over` check the system prompt explicitly
told it to use). Present to a lesser degree in wa30 (large directional batches) and sc25
(repeated batch clicks).

## 3. v5 lever candidates, ranked by plausible game count unstuck

1. **Auto-persist state instead of relying on the model to re-emit it.** Either (a) capture and
   feed back the model's actual per-turn reasoning/findings automatically (not just the
   optional `World model:`-prefixed text it stops writing), or (b) force the harness to reject
   an empty/unchanged world-model field and require a non-trivial diff before accepting the next
   action. Targets **Mode 1 (8/9 games)** — the largest, most consistent single defect found,
   and the one every subagent flagged as load-bearing for the contradictions in Mode 1 games'
   controls/win-condition churn.

2. **Make the anti-loop bookkeeping automatic, not model-invoked.** Auto-record
   `(state_key, action, next_state_key)` inside the harness's own `action()` call, so
   `.untried()`/`.path_to_nearest_untried()` become free reads instead of requiring the model to
   remember `.record()` after every action. This repo's own prior report already recommended
   this after finding 0/2 real calls across all 25 games; this report confirms 0/0 specifically
   in the 9 worst games, i.e. the fix targets exactly the population where it would matter most.
   Targets **Mode 2 (9/9 games)** — every game shows some form of loop or hypothesis-repetition
   the tool exists to prevent.

3. **Force-inject an unmissable "STATE WAS RESET" message immediately after any GAME_OVER**,
   naming what was lost (e.g. "your last N actions of board-state progress are gone, back to the
   level-1 starting layout"), rather than relying on the model to notice via board diffing.
   Targets **Mode 3 (6-7/9 games)** and directly prevents wasted turns like cn04's full-turn
   confusion or tn36's failure to adjust pacing after its first reset.

4. **Harness-level hard stop on any `game_over`/`done`/`level_completed`/`run_complete` signal
   inside a batched action loop**, not a prompt reminder — tr87's own stop condition omitted
   `game_over` despite being told to check it, and m0r0's blind bursts (up to 132 actions per
   call) ran unchecked. Pair with a required per-N-iteration print/inspection inside any loop the
   model writes. Targets the **unbounded-burst mechanism** most visibly in m0r0 (72% of its
   action budget) and tr87, and would reduce wasted-budget tails across the others.

5. **Explicitly warn that a shrinking edge-bar value observed at a GAME_OVER is a FAILURE
   threshold, never a target to approach**, and that "HUD-classified" does not mean
   "consequence-free" — a bar can simultaneously be decorative *and* a hard life/action budget.
   Targets **Mode 4 (3/9 games)**, but m0r0 (the single worst game in the whole run) is one of
   them, and this is the most surgical, cheapest-to-word fix of the five.

## 4. Honesty notes

- No game in this sample was rated `too_opaque_to_classify`; opacity ranged clear→partially
  opaque, with confidence high in 6/9, medium in 3/9 (vc33, sc25's single-batch-absorption
  question, wa30's inferred GAME_OVER cause).
- **vc33 remains genuinely ambiguous**: its subagent explicitly could not rule out that the real
  win condition lies outside the state space the model exhaustively (and correctly) tested —
  this transcript alone cannot distinguish "real thrash" from "trivial baseline inflated by a
  harder-than-7-action level," though the model's behavior reads as substantive, not confused.
- Every "inferred" claim above (wa30's GAME_OVER cause, the 3 "probable" Mode-1 games) is
  labeled as such in §1/§2 and should not be read with the same weight as the confirmed cases.
- This report does not propose or validate a fix — per its own anti-goals, it characterizes only
  what the 9 transcripts show is missing.
