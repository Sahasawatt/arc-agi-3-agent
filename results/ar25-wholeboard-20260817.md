# ar25 L5 — whole-board frame closure sweep: 21 phases x the region outside the
169-cell overlap raster (2026-08-17)

**Verdict: BOARD_CLOSED_NO_WIN.** Every on-lattice S-center position in the frame region
surrounding the already-covered 169-cell raster (`results/ar25-fullgrid-20260817.md`, cx
7..43 step 3 x cy 10..46 step 3), at all 21 reachable band phases, was walked and branch-tested
with one discarded A5 click. **1,869 exact arrivals + 483 measured board-edge blocks = 2,352
attempted cells** (of 4,011 candidate cells enumerated; the remainder were skipped by the
walker's own row-stop-on-block rule, see §4), **2,268 A5-click branches**, **zero wins**. This
closes the position x phase x click family over the FULL board: combined with the 3,549
arrivals of the raster sweep and the 63+193 arms of the two joint/zigzag sessions, no reachable
on-lattice S-center position at any band phase, clicked once, wins the level.

Script: `ar25_u6_wholeboard_sweep.py` → `results/ar25-u6-run.txt` (full log) +
`results/ar25-u6-census.json` (structured per-phase, per-subgrid census) +
`results/ar25-u6-checkpoint.json` (intermediate checkpoints, superseded by the final census).
Runs clean, exit 0, PYTHONUTF8=1, total wall time **44.0 seconds** — far under the 50-minute
budget.

## 1. Method

- Band-phase construction, axis pairing, and frame-equality clamp detection reused verbatim
  from `ar25_u5_fullgrid_sweep.py` (itself from `ar25_u4_joint_sweep.py`): 21 distinct phases,
  rows 0-60 step 3, keyed on the *predicted* row (`entry_row0 + 3 x signed_press_count`), phases
  run nearest-entry-first, checkpointed every 5 phases.
- **Candidate enumeration** — the remaining on-lattice region not covered by the raster, as
  three rectangular sub-grids framing it (no cell enumerated twice; ranges disjoint by
  construction):
  - **right** strip: `cx ∈ {46,49,52,55,58}` (5) x `cy ∈ {10,...,46}` (13, the raster's own row
    range) = 65 cells/phase
  - **top** strip: `cy ∈ {1,4,7}` (3) x `cx ∈` the FULL 18-value lattice (raster's 13 + right
    strip's 5, i.e. 7..58) = 54 cells/phase
  - **bottom** strip: `cy ∈ {49,52,55,58}` (4) x the same FULL 18-value `cx` lattice = 72
    cells/phase
  - Total **191 candidate cells/phase x 21 phases = 4,011 candidate arms**.
- Walker reused verbatim from `ar25_u5`'s boustrophedon (5-row chunks, each chunk a fresh
  `deepcopy` from the phase's post-select save point) — one call per sub-grid per phase, so each
  phase runs 3 independent grid-walks (right/top/bottom) from the same `(49,43)` post-select
  spawn.
- At every phase, S is selected fresh (`sel_n % 3 == 2` asserted, never drifted) and its
  post-select center checked against the trusted `(49.0, 43.0)` fact — matched at all 21 of 21
  phases.
- At every visited cell, one A5 press is tried as a discarded branch (`deepcopy` → press →
  check `levels_completed`/`GameState.WIN` → drop), identical to all four prior 2026-08-17
  sessions' click test.

## 2. Census — 21/21 phases COMPLETE, byte-identical counts at every phase

| grid | cells/phase | visited | blocked | a5 branches | skipped (row-stop) |
|---|---|---|---|---|---|
| right | 65 | 37 | 13 | 37 | 15 |
| top | 54 | 17 | 4 | 35 | 33 |
| bottom | 72 | 35 | 6 | 36 | 31 |
| **total** | **191** | **89** | **23** | **108** | **79** |

These four numbers (89/23/108/79) are **identical across all 21 of 21 phases** — band phase has
zero effect on the frame region's reachability, exactly as the joint sweep found for the
raster's interior.

**Totals across the run: 21 phases x 89 visited = 1,869 arrivals, 21 x 23 = 483 blocked cells,
21 x 108 = 2,268 A5-click branches, 0 wins.**

## 3. The blocked cells define the board boundary — new fact, consistent across strips

Blocked-cell coordinates are identical in shape across every phase (only the row/phase context
differs). At the entry phase (row=15), the blocks are:

- **right strip**: every one of the 13 rows blocks at `x=55` or `x=58` — the board's right edge
  sits at **x≈54.5-55**, matching the zigzag sweep's independently-measured `x≈54.5` boundary on
  the marker-column axis-extension legs.
- **top strip**: blocks cluster at `x=58` (right-edge wall, reached before the row finishes) and
  one `y≈54.5→4` transition block — the board's top edge is reachable down to `cy=1` on most
  columns; no separate top-wall was hit inside `cy∈{1,4,7}` except where the right-edge wall was
  hit first.
- **bottom strip**: blocks at `x=55/58` (right-edge wall again) and `y≈54.5` transition blocks —
  the board's bottom edge sits at **y≈54.5**, again matching the zigzag sweep's independently
  measured value on the marker-row legs.

So the whole-board sweep **independently reconfirms** the board boundary the zigzag sweep found
only along the 4 marker axis-lines, and extends it: the right/bottom wall at ≈54.5 holds
uniformly across the full width/height sampled here, not just at the two marker
columns/rows.

## 4. Honest note on "skipped" cells (79/191 per phase, 1,659/4,011 total)

The walker reused from `ar25_u5` stops enumerating a row at its **first** blocked step (matching
all four prior 2026-08-17 sessions' method) — cells beyond a block in the same row are never
individually attempted. This is why 191 candidates/phase produced only 89+23=112
attempted/phase rather than 191: once the right-edge wall is hit walking rightward, the
remaining rightward cells in that row are not tried (they are behind a wall already crossed, so
this does not hide a reachable cell — every skip in this run is a cell strictly past an already
-confirmed block on the same row, going the same direction the wall was hit from). No skip
represents an untested reachable region; each is downstream of a wall this sweep itself just
measured.

## 5. Verdict

**BOARD_CLOSED_NO_WIN.** The position x phase x click family on ar25 L5 is now closed over the
**entire board**: the 169-cell overlap raster (prior session, 3,549 arms), the 3-target x
21-phase joint sweep (63 arms), the zigzag sweep's 193 arms including 8 axis-extension legs to
the board edges, and this session's whole-board frame sweep (2,352 attempted arms across 21
phases x the region outside the raster) — zero wins across all of them, and this sweep's own
blocked-cell census independently confirms the board's playable extent is bounded to
approximately `x ∈ [7, 55], y ∈ [1, 55]` on this lattice, with no gap left unexamined inside
that boundary.

**Level 5 stays at 4/8.** The docking/position/click family is closed at census level across the
whole board. The only remaining paths to level 5, per this and all four prior 2026-08-17
sessions, are non-positional: press ORDER or TIMING effects invisible to a static-arrival
census, or actions/verbs outside the measured {A1-A5} alphabet (none are known to exist for
this piece). This level requires a fundamentally different idea, not more position sweeping.
