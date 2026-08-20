# PROGRESS DIGEST Audit — duck-v5

## Executive verdict

**Digest bookkeeping is mechanically correct, but adoption is weak and its `changed` signal is semantically noisy.**

Across 15 beginning/middle/end spot-checks, every digest satisfied:

- `tried = changed + noop` for each action.
- Sum of per-action `tried` counts equaled `actions so far`.
- The last-five list agreed with the preceding action sequence and level/reset outcome.
- Level milestones agreed with the reported current level.

No obviously wrong count was found. However, `changed` means only that some unmasked board content changed; the model sometimes found the relevant game object stationary and suspected a timer or other incidental change. This makes correct bookkeeping misleading for strategy selection.

Explicit digest use was concentrated in three losing/low-scoring games:

| Game | Score | Explicit model references |
|---|---:|---:|
| `ft09` | 16.98 | 0 |
| `re86` | 16.67 | 0 |
| `m0r0` | 0.00 | 5 model turns |
| `tr87` | 0.00 | 2 model turns |
| `dc22` | 1.66 | 3 model turns |
| **Total** |  | **10 model turns** |

The two best runs never explicitly referenced the digest. In weaker runs, the model used it mostly reactively—diagnosing noops or resets after long batches—not as an exploration-control mechanism.

The five sampled reset banners were all genuine game resets: **0/5 sampled false positives**. The reset detector appears accurate on this sample, although the high aggregate firing rate reflects agents repeatedly exhausting fixed action budgets.

The accumulating world model is useful early but poorly curated. Some games develop helpful turn-stamped mechanics; others retain long, contradictory hypothesis histories, stop accumulating entirely, or preserve only the initial observation.

---

## 1. Correctness

### Method

Three digest snapshots were selected per game: the first nonzero snapshot, a middle snapshot, and the final snapshot. Counts were checked against surrounding action summaries, structured results, level transitions, and reset records.

### `ft09-0d8bbf25_p0.txt`

| Snapshot | Evidence | Judgment |
|---|---|---|
| Beginning | At approximately line 1,325, the digest reports one `MOUSE`, `1/0/1`, and `MOUSE:noop` as the only recent action. | Correct. |
| Middle | At approximately lines 5,822–5,828, it reports 19 mouse actions, split `19/14/5`; the five recent outcomes contain three changes and two noops. The arithmetic and ordering reconcile. | Correct. |
| End | The preceding prompt says seven mouse actions were executed and that the run advanced to level 4; the digest records `L4@a82`, `MOUSE: 82/77/5`, and ends in `MOUSE:level_up` at approximately lines 13,986–14,012. | Correct. |

No wrong number was found. Milestones also form a plausible sequence: `L1@a0`, `L2@a31`, `L3@a52`, `L4@a82` (approximately lines 14,007–14,011).

### `re86-8af5384d_p0.txt`

| Snapshot | Evidence | Judgment |
|---|---|---|
| Beginning | One `RIGHT` produced a changed board; the next digest says `RIGHT: 1/1/0` and `RIGHT:changed` at approximately lines 601–607. | Correct. |
| Middle | On entry to level 3, the digest reports `L3@a71`; counts total 71 and the last action is `LEFT:level_up` at approximately lines 6,147–6,159. | Correct. |
| End | At step 152, counts total 151: `18+44+27+11+51=151`; all have zero noops, and the last five are two `DOWN` then three `RIGHT`, matching the latest sequence at approximately lines 12,887–12,897. | Correct. |

The earlier level milestones `L2@a31` and `L3@a71` also agree with the later `L4@a136` record (approximately lines 12,888–12,896).

### `m0r0-492f87ba_p0.txt`

| Snapshot | Evidence | Judgment |
|---|---|---|
| Beginning | The first `RIGHT` has `board_changed: true` in the structured result at approximately lines 380–389; the next digest says `RIGHT: 1/1/0`, `RIGHT:changed` at approximately lines 557–563. | Correct. |
| Middle | At action 270, the per-action tried counts total 270 and each split reconciles; the last five are `UP:changed`, `UP:noop`, `SPACE:noop`, `MOUSE:changed`, `MOUSE:noop` at approximately lines 7,492–7,505. | Correct. |
| End | At approximately lines 15,273–15,285, tried counts total 608 and changed/noop splits all reconcile. The last five end in `RESET:reset`, matching the immediately preceding reset banner at approximately line 14,961. | Correct. |

The representation `RESET: 4/0/4` while the recent label is `RESET:reset` is internally deliberate: resets occupy the non-changed bucket, but receive a more informative display label. It is not a count error.

### `tr87-cd924810_p0.txt`

| Snapshot | Evidence | Judgment |
|---|---|---|
| Beginning | The first nonzero digest records `RIGHT: 1/1/0` and `RIGHT:changed` at approximately lines 968–974. | Correct. |
| Middle | At approximately lines 4,854–4,863, `26+8+14+47=95`; every action is changed and the last-five list contains one `UP` followed by four `LEFT`s. | Correct. |
| End | The prompt reports a 24-action preceding batch; the final digest reaches 339 total actions, with per-action counts totaling 339 and a matching changed-only last five at approximately lines 10,603–10,631. | Correct. |

The two resets are also included in the total as `RESET: 2/0/2` (approximately lines 10,624–10,630).

### `dc22-fdcac232_p0.txt`

| Snapshot | Evidence | Judgment |
|---|---|---|
| Beginning | The first mouse click is classified changed; the digest records `MOUSE: 1/1/0` and `MOUSE:changed` at approximately lines 938–945. | Correct. |
| Middle | At action 38, tried counts total 38, all changed/noop splits reconcile, and the last five contain three changed mouse actions followed by two changed ups at approximately lines 8,291–8,302. | Correct. |
| End | The preceding sequence is `RIGHT, RIGHT, RIGHT`; the final digest ends with three `RIGHT:changed` entries. Counts total 113 and record `L2@a100` at approximately lines 15,936–15,964. | Correct. |

### Correctness conclusion

**15/15 sampled blocks passed; no obvious numerical or ordering error was found.**

There is nevertheless an important semantic defect. In `dc22`, the model observes that a green block did not move even though the digest calls the fourth `RIGHT` changed, and speculates that the timer changed instead (approximately lines 10,450–10,458). Thus:

> The digest correctly mirrors `board_changed`, but `board_changed` is not reliably equivalent to “gameplay state changed.”

That distinction matters more than raw arithmetic correctness.

---

## 2. Adoption

An “explicit reference” was counted once per model turn when reasoning quoted a digest count, cited its last-five sequence, discussed a digest `noop`, or used a reset entry to change its interpretation. Repeated sentences within one reasoning response count as one reference.

### `ft09`: 0 references

The model itself records many action effects as “noop” in its accumulated world model—e.g. source-grid clicks and corner clicks around lines 6,692–6,707—but does not attribute these facts to the digest or quote digest counts/last-five content.

The high-scoring run therefore appears to rely on direct observations and its world model, not on the digest.

### `re86`: 0 references

No visible reasoning explicitly quotes the digest, its counts, its last-five sequence, or a digest noop. The model progresses through levels without visible digest-driven strategy changes.

### `m0r0`: 5 references

1. It reconstructs the next batch from the displayed recent sequence—“Last 5 actions: MOUSE, RIGHT, MOUSE, LEFT, MOUSE”—at approximately lines 11,798–11,840.
2. After a 63-action timeout, it quotes the exact five outcomes and investigates why both mouse clicks were classified noop at approximately lines 12,121–12,249.
3. It uses `RESET:reset` to conclude that the game returned to its initial state at approximately line 12,838.
4. It again quotes `MOUSE:changed, RIGHT:changed, MOUSE:noop, LEFT:changed, MOUSE:noop` while diagnosing bad click coordinates at approximately lines 13,738–13,746.
5. It uses two recent mouse noops to justify continuing an “alternating” click pattern at approximately line 14,504.

Adoption did not consistently improve decisions. The model became confused about digest arithmetic—“48 MOUSE actions, 29 changed, 19 noop,” followed by incorrect comparisons against other totals—around line 12,274. It also treated digest noops as evidence for several competing explanations instead of checking transition-local gameplay diffs.

### `tr87`: 2 references

1. It cites `actions so far: 129` and `RESET:reset` to infer a return to the initial state at approximately line 7,237.
2. It later cites 258 cumulative actions and the reset notice to infer an action/step limit at approximately lines 8,190–8,192.

These references are useful, but only after the agent has already hit the limit.

### `dc22`: 3 references

1. It cites three `MOUSE:changed` results while investigating what actually changed at approximately line 3,428.
2. It quotes the recent `RIGHT` outcomes—including an intervening noop—and notices that the fourth “changed” result does not match green-block movement at approximately lines 10,450–10,458.
3. It cites an `UP:noop` result after seeing the green block remain stationary at approximately lines 10,720–10,721.

This is the strongest example of meaningful digest use, but also exposes the coarse `changed` classification.

### Adoption conclusion

Explicit use is **low and skewed toward failure recovery**:

- 0 references in both high-scoring games.
- 10 explicit-reference turns total across 206 digest-bearing prompts.
- Most references occur after long batches, timeouts, unexplained noops, or resets.
- No sampled run visibly says, in effect, “this action now has a high noop rate, so stop trying it.”
- The digest is functioning more as a postmortem cue than an online exploration controller.

---

## 3. Reset banner

Five harness-generated banners were sampled: all four in `m0r0` and the first in `tr87`.

| Occurrence | Evidence | Judgment |
|---|---|---|
| `m0r0`, action 152 | Banner says 152 actions were lost; digest ends `RESET:reset`. The model reports that its BFS executed 112 actions, caused game over, and that the two blue squares returned to their original positions (approximately lines 3,569–3,623). | **True reset** |
| `m0r0`, action 304 | Banner appears at step 305 after another 152-action interval; digest ends `UP:noop, RESET:reset`. The model observes the blue squares back at the bottom in their original positions (approximately lines 8,927–8,966). | **True reset** |
| `m0r0`, action 456 | Banner again reports exactly 152 actions lost; digest ends `SPACE:noop, RESET:reset`. The model sees the original two-square layout and a refilled timer, then restarts from the initial strategy (approximately lines 12,803–12,848). | **True reset** |
| `m0r0`, action 608 | Fourth exact 152-action interval; digest ends `LEFT:noop, RESET:reset`. The model reports the timer refilled and squares returned to starting positions after draining the timer to zero (approximately lines 14,961–15,009). | **True reset** |
| `tr87`, action 129 | Banner reports 129 actions lost and digest ends `RESET:reset`. The model explicitly says “GAME OVER! The level reset” and begins reconstructing the initial symbol state (approximately lines 6,377–6,410). | **True reset** |

**Sampled false-positive rate: 0/5 = 0%.**

These are not animation frames returning temporarily to a similar picture. Each occurrence combines:

- A fixed-length action-budget boundary: 152 in `m0r0`, 129 in `tr87`.
- A synthetic `RESET:reset` transition.
- The level remaining `1→1`.
- Model-observed restoration of initial object positions or timer state.

The high banner volume is therefore more plausibly caused by repeated action-budget exhaustion than detector instability.

---

## 4. World-model quality

### What works

Turn stamps are present and preserve useful discoveries in some runs.

- In `ft09`, entries `[t4]` through `[t21]` record tested interactions, target-cell toggling, rejected source patterns, and planned combination patterns (approximately lines 6,692–6,735).
- In `m0r0`, `[t14]` through `[t25]` preserve reset state, chamber geometry, square containment, opposite horizontal motion, no-op actions, and candidate goals (approximately lines 7,472–7,485).
- In `tr87`, `[t2]` through `[t7]` compactly capture board layout, cursor motion, and the effect of `UP/DOWN` on pink symbols (approximately lines 5,277–5,290).

These fields clearly survive across turns and can save rediscovery.

### What fails

#### 1. Append-only history preserves superseded beliefs

`ft09` carries mutually superseded goals simultaneously:

- “Click on the correct source grid”;
- “match the bottom-left source”;
- then evidence that all three source patterns failed;
- followed by many obsolete plans to retry those same hypotheses.

These appear together in one mid-game prompt at approximately lines 6,690–6,735. The field is a chronological diary, not a current world model.

#### 2. It grows into prompt clutter

The same `ft09` block contains at least 21 world-model entries and roughly 15 plan entries by action 26 (approximately lines 6,690–6,735). Much of that material is already invalidated. Deduplication does not solve semantic redundancy when differently worded entries express obsolete versions of the same hypothesis.

#### 3. Accumulation is inconsistent between games

On entering level 3 in `re86`, the prompt contains only `end of world model`—no carried entries—despite 71 prior actions and two level transitions (approximately lines 6,550–6,577). Useful cross-level discoveries therefore did not survive into a later level.

Likewise, `dc22` still carries only its initial `[t1]` board description and first inspection plan at step 54, despite dozens of actions (approximately lines 10,390–10,410). The extractor evidently depends too heavily on recognized textual prefixes or suitable visible model content.

#### 4. Unverified interpretations become durable facts

In `m0r0`, “MOUSE causes invisible board changes,” “full figure map,” and several changing goal hypotheses are all retained together (approximately lines 7,476–7,485). Later reasoning shows that some apparent mouse changes were timer effects or clicks at the wrong coordinate (approximately lines 13,427–13,446). The world model does not distinguish observation from inference or confidence.

### World-model conclusion

The world-model mechanism is **partially useful but not reliable enough as v6’s primary memory**:

- Turn stamps: working.
- Cross-turn persistence: working in some games.
- Deduplication: insufficient.
- Contradiction handling: absent.
- Extraction/adoption consistency: poor.
- Mid-game signal-to-noise: ranges from useful compact mechanics (`tr87`) to stale hypothesis logs (`ft09`) to nearly empty (`re86`, `dc22`).

---

## 5. Verdict and top three v6 improvements

### Verdict

| Feature | Verdict |
|---|---|
| Digest arithmetic | **Pass** — 15/15 sampled snapshots correct |
| Last-five ordering | **Pass** |
| Level/reset milestones | **Pass** |
| `changed` semantics | **Needs revision** |
| Model adoption | **Low and mostly reactive** |
| Reset precision | **Pass on sample** — 0/5 false positives |
| World-model accumulation | **Mixed; not production-quality memory** |

The feature should remain in v6, but not unchanged. The core counters are trustworthy; the main weaknesses are classification granularity, lack of decision-oriented presentation, and uncurated memory.

### Improvement 1 — Split `changed` into gameplay, HUD-only, and unknown

Replace the binary outcome with something like:

- `gameplay_changed`
- `hud_only`
- `noop`
- `level_up`
- `reset`
- `uncertain`

Grounding:

- `dc22` shows a `RIGHT:changed` while the relevant green block remains stationary; the model suspects only the timer changed (approximately lines 10,450–10,458).
- `m0r0` repeatedly interprets mouse `changed/noop` results as timer behavior and becomes confused about whether clicks worked (approximately lines 12,220–12,249).

Use gameplay-object diffs after subtracting `hud_mask(history)`. If masking is not reliable yet, label the result `unknown_changed` instead of asserting useful progress.

### Improvement 2 — Turn the digest into an intervention, not a ledger

Add concise derived warnings when repetition becomes decision-relevant, for example:

- `MOUSE: 12/20 noops in current state family — stop blind retrying`
- `same 4-action cycle repeated 8× with no level progress`
- `96 actions since last level-up; reset threshold previously observed at 152`
- `last sequence duplicates a previously failed sequence`

Grounding:

- `m0r0` reached 608 actions and four genuine resets while repeatedly draining the same timer and executing the same click/move cycle (approximately lines 12,803–12,848 and 14,961–15,009).
- `tr87` inferred the action cap only after resets at 129 and 258 actions (approximately lines 7,237 and 8,190–8,192).
- The best two games made zero explicit digest references, indicating the raw ledger does not naturally invite strategic use.

The prompt should explicitly require the model to acknowledge a warning before issuing another substantially similar batch.

### Improvement 3 — Replace append-only world-model accumulation with a typed, revised state

Maintain a compact schema with replacement semantics:

- `observed mechanics`
- `current state`
- `confirmed goal constraints`
- `rejected hypotheses`
- `open questions`
- `next discriminating test`
- `cross-level rules`
- confidence and `last_verified_turn` per item

New evidence should update or retire prior entries rather than append another paragraph. Reset should clear current-position fields but preserve confirmed mechanics and rejected hypotheses.

Grounding:

- `ft09` retains obsolete and contradictory goal/plan versions together by action 26 (approximately lines 6,690–6,735).
- `m0r0` promotes uncertain interpretations such as “invisible board changes” into durable memory (approximately lines 7,476–7,485).
- `re86` enters level 3 with an empty carried model (approximately lines 6,550–6,577).
- `dc22` still has only `[t1]` at step 54 (approximately lines 10,390–10,410).

The v6 harness should derive this structure from transition evidence where possible, rather than depending solely on whether the model emitted a recognized prose prefix.

---

## Claims, confidence, and remaining questions

### Claims

- **Digest counters and last-five lists are mechanically correct in the sample — High confidence.** Fifteen beginning/middle/end snapshots passed, with no arithmetic or ordering mismatch.
- **The binary `changed` label is too coarse for gameplay reasoning — High confidence.** Directly demonstrated in `dc22` and repeatedly problematic in `m0r0`.
- **Visible model adoption is low and reactive — High confidence.** Ten explicit-reference turns, with none in the two strongest runs.
- **Sampled reset banners are real — High confidence.** All five coincide with fixed action-budget boundaries, reset transitions, and restored initial state.
- **World-model persistence is useful but inconsistent and poorly curated — High confidence.** Strong examples of both useful stamped mechanics and stale/empty accumulation occur across the five files.

### Open questions

- Whether reset precision remains 100% outside `m0r0` and `tr87`; this audit sampled five required occurrences, not all 594 reported banners.
- Whether `board_changed` already applies `hud_mask` consistently or whether some other animation/state channel produces the misleading changes.
- Why world-model accumulation disappears in `re86` and remains at `[t1]` in `dc22`: extractor-prefix failure, cap behavior, or missing visible model content cannot be distinguished from transcripts alone.

### Working answer

**Proceed with PROGRESS DIGEST in v6 only after refining outcome classification and turning repeated/no-progress statistics into explicit strategy warnings. Keep reset detection as-is pending a broader random sample. Replace the accumulating prose world model with a typed, contradiction-aware state rather than building additional behavior on the current append-only field.**