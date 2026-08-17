# ar25 L5 — joint (band phase x S dock position) sweep (2026-08-17)

**Verdict: JOINT_SWEPT_NO_WIN.** All 21 reachable band phases x all 3 candidate dock targets
(marker1, marker2, zigzag interior center) = **63 arms**, every arm S arrived exact-center at
its target, every arm's terminal state was branch-tested with one A5 click. Zero wins across
63 arrivals and 63 A5-click branches. This closes the gap the two prior 2026-08-17 sessions
(`results/ar25-goal-directed-20260817.md`, `results/ar25-zigzag-sweep-20260817.md`) and the
2026-08-16 recon entry (`results/breadth-recon.md`, "the last gap is closed... 441 x 289 joint
interior... only 2 points... sampled") left open: the band-phase axis of the joint space, swept
against the specific docking-family targets rather than as a random 2-point sample.

Script: `ar25_u4_joint_sweep.py` → `results/ar25-u4-run.txt` (full log) +
`results/ar25-u4-result.json` (structured census). Runs clean, exit 0, PYTHONUTF8=1, total
wall time **6.0 seconds**.

## 1. Method note: two clamp-detection bugs found and fixed before the real sweep ran

The first version keyed band phases on a colour-10 connected-component reader (`band_row()`,
adapted from `ar25_r1.py`'s `components()`), and detected "clamped" as *"this reading equals
the last one."* That version found only **12 distinct phases** (rows 15–48) and reported the
UP direction dead after 1 press. A diagnostic (`ar25_u4_diag.py`) proved this reading, not the
band, was what stopped: `band_row()` legitimately returns **None** once the band's cells
4-connect with the tall static colour-10 column (measured: `up0` through `up4` all show one
322-cell component spanning the whole board, and `down11` through `down13` show the same
signature) — but raw consecutive frames in that exact stretch are **provably not
byte-identical** (`np.array_equal` False at every step checked), i.e. the band keeps moving
after the component reader goes blind.

Fixed by decoupling the two jobs: **blocked-press detection now uses full-frame byte equality**
(HUD ticks at row/col 63 excluded) — the same "a blocked press changes nothing" law
`CLAUDE.md` already documents for this repo — and the **phase key uses the predicted row**
(`entry_row0 + 3 x signed_press_count`), trusted from the CONTEXT's own measured "3px/press"
fact rather than re-derived from a reader now known to be blind in part of the range.
`band_row()`'s component-based observation is still recorded per phase for cross-check
wherever it resolves (it agrees with the prediction at every phase where it isn't None).

## 2. Phase census — 21/21 phases reached, matching the CONTEXT's "21 phases" fact exactly

| phase | row0 predicted | row0 observed (component reader) | presses from entry |
|---|---|---|---|
| 0  | 0  | None (merged/undetectable) | -5 |
| 1  | 3  | None (merged/undetectable) | -4 |
| 2  | 6  | None (merged/undetectable) | -3 |
| 3  | 9  | None (merged/undetectable) | -2 |
| 4  | 12 | None (merged/undetectable) | -1 |
| 5  | 15 | 15 (entry) | 0 |
| 6  | 18 | 18 | 1 |
| 7  | 21 | 21 | 2 |
| 8  | 24 | 24 | 3 |
| 9  | 27 | 27 | 4 |
| 10 | 30 | 30 | 5 |
| 11 | 33 | 33 | 6 |
| 12 | 36 | 36 | 7 |
| 13 | 39 | 39 | 8 |
| 14 | 42 | 42 | 9 |
| 15 | 45 | 45 | 10 |
| 16 | 48 | 48 | 11 |
| 17 | 51 | None (merged/undetectable) | 12 |
| 18 | 54 | None (merged/undetectable) | 13 |
| 19 | 57 | None (merged/undetectable) | 14 |
| 20 | 60 | None (merged/undetectable) | 15 |

Entry (n=0) sits at phase index 5 of 21 (row 15), i.e. 5 phases up and 15 phases down from
entry, spanning rows 0–62 in 3-row steps — a clean 21-phase, full board-height range, exactly
matching the trusted CONTEXT fact ("21 phases") with no shortfall. **UP direction clamps at 5
presses (row 0, board top), DOWN clamps at 15 presses (row 60, board bottom).** Both clamps
verified as true zero-frame-change blocks (`ar25-u4-run.txt` lines 10–11), not reader blindness
— the component reader (`band_row()`) is blind for phases 0–4 and 17–20 (band 4-connects with
the static left column there) but the frame-equality detector that gates phase construction
does not depend on it.

## 3. Dock outcomes per phase — 63/63 arms, zero blocks, zero wins

Every one of the 21 phases x 3 docks (marker1 `(37,16)`, marker2 `(13,40)`, zigzag interior
center `(25,28)`) walked S to an exact-center arrival (`status=ARRIVED` in
`results/ar25-u4-result.json`, tolerance ±2px, budget 20 presses per arm, all arms well inside
budget). **Zero `BLOCKED_BOTH_AXES`, zero `OBS_NONE`, zero `GAME_OVER`, zero `BUDGET_EXCEEDED`
across all 63 arms.** S's position immediately after selection (A5 x2) was **identical across
all 21 phases** — `(49.0, 43.0)` in every case — confirming the goal-directed session's ARM3
finding directly: moving the band before selecting S does not move S's spawn point, and the
docking geometry is unaffected by band phase.

## 4. A5-click branch — 63/63 tested, zero wins

At every one of the 63 arm terminals (all of them arrivals), one A5 press was tried as a
discarded branch (`copy.deepcopy(env)` → press → check `levels_completed`/`GameState.WIN` →
drop). `a5_branch_count=63`, zero wins. `sel_n` bookkeeping was asserted (`sel_n % 3 == 2`)
before every arm's walk, and never drifted — every arm re-selects fresh from its own
band-phase save point (2 clean A5 presses, no residual state carried between arms).

## 5. Verdict

**JOINT_SWEPT_NO_WIN.** The full 21-phase band range (verified against the trusted CONTEXT fact,
not merely assumed) crossed with the 3 docking-family targets (matching the two 2026-08-17
prior sessions' target set) is now exhaustively tested at the arrival level: 21 x 3 = 63 arms,
63 exact-center arrivals, 63 A5-click branches, zero blocks, zero wins. This narrows, without
closing outright, the honest gap the 2026-08-16 recon entry named ("only 2 points of the 441 x
289 joint interior were sampled") — this sweep adds a full, structured band-phase axis against
the specific docking hypothesis (not a random 2-point sample of the much larger full W x S grid,
which remains untouched). What is **not** covered by this sweep, named rather than glossed:
S's position was only tested at 3 fixed docking targets per phase, not swept across its whole
reachable rectangle at each of the 21 phases (that would be the still-larger 21 x 289 grid); and
no win condition outside the docking family (bbox/axis-exact overlap with the colour-11 zigzag)
was tested here.

Level 5 stays at **4/8**.
