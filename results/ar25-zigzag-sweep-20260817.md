# ar25 L5 — zigzag position sweep (2026-08-17)

**Verdict: SWEPT_NO_WIN.** S was walked across every reachable lattice position whose 15x15
bbox overlaps the colour-11 zigzag's bbox (169/169 cells, full raster), plus 8 axis-exact
extension legs out to the board edges on both marker columns/rows, plus a band+10 variant
resweep of the 10 most central overlap cells. `levels_completed` was read after every real
press and after a discarded A5-click-alias branch at every one of 193 visited positions.
Zero wins. This is a live, direct-measurement close of the region the goal-directed session
(`results/ar25-goal-directed-20260817.md`) flagged as untested ("whether S can be driven onto
the zigzag's interior... as an axis-exact rather than bbox-exact dock").

Script: `ar25_u3_zigzag_sweep.py` → `results/ar25-u3-sweep-run.txt` (full log) +
`results/ar25-u3-result.json` (structured census). Runs clean, exit 0, PYTHONUTF8=1.
Total wall time **6.7 seconds** — far under the 50-minute budget; this game's engine steps
are near-instant locally, which is itself worth noting for future session time-budgeting on
this game (an operational observation, not a campaign fact).

## 1. Setup (reused, not re-measured)

- L5 entry reached via `mirror.Mirror`'s proven L1-L4 line (`get_to_l5()`, same bootstrap as
  `ar25_u2.py`).
- S selected with exactly 2 presses of A5 (`sel_n=2`, asserted `sel_n % 3 == 2` before every
  arrow batch — verified once at setup and once independently in the phase-3 band+10 branch;
  never drifted during the sweep because every raster chunk re-branches from a single frozen
  save point (`ROOT_SEL_ENV`, a `deepcopy` taken right after those 2 presses) rather than
  continuing to press A5 mid-sweep).
- Axis pairing reused verbatim from `ar25_u2.py`: A1=up(dy-3), A2=down(dy+3), A3=left(dx-3),
  A4=right(dx+3).
- Entry S bbox: `(42, 56, 36, 50, 88)`, center `(49, 43)` — matches the prior session exactly.

## 2. Phase 1 — main raster (overlap region), 169/169 cells, COMPLETE

Overlap region computed from the zigzag bbox (x12-38, y15-41) plus S's half-width/half-height
(7,7): `cx ∈ [5,45]`, `cy ∈ [8,48]`. On the 3px lattice anchored at the entry center (49,43),
the reachable positions inside that region are exactly:

- `cx_list` (13 values): 7,10,13,16,19,22,25,28,31,34,37,40,43
- `cy_list` (13 values): 10,13,16,19,22,25,28,31,34,37,40,43,46

**13 x 13 = 169 cells**, walked as a 3-chunk boustrophedon (5+5+3 rows, each chunk a fresh
`deepcopy` of `ROOT_SEL_ENV` to stay well under the ~127-real-press life budget — actual
per-chunk press counts were far smaller than that ceiling; no game-over, no life exhaustion,
no blocked cell inside the region at all). All 169 cells reached; `levels_completed` checked
after every arrival and after a discarded A5-click branch at each. Zero wins, zero blocks.

## 3. Marker / zigzag-edge lattice-parity check (new fact this session)

Checked exact on-lattice reachability (mod-3 congruence to the entry center) before sweeping:

| point | value | exact-reachable |
|---|---|---|
| marker1 center | (37,16) | x=True, y=True |
| marker2 center | (13,40) | x=True, y=True |
| zigzag bbox x0 | 12 | **False** |
| zigzag bbox x1 | 38 | **False** |
| zigzag bbox y0 | 15 | **False** |
| zigzag bbox y1 | 41 | **False** |

Both marker centers are exactly on this lattice (consistent with the prior session's
exact-center dock at 13 presses). The zigzag's own outer bbox edges (12, 38, 15, 41) are
**not** — they are off by 1-2px from any reachable S-center coordinate given this entry
parity, so a literal axis-exact match of S's center against those specific pixel values is
structurally impossible from this entry; the raster already samples the nearest reachable
cells (10/13 and 37/40, 13/16 and 40/43) on both sides.

## 4. Phase 2 — axis-exact extension beyond the overlap region, 8/8 legs run

For each of the 2 marker columns (x=37, x=13) and 2 marker rows (y=16, y=40), walked the
orthogonal axis beyond the raster's covered range, in both directions, to the board edge:

| leg | direction | outcome |
|---|---|---|
| marker1-col (x=37) | y below 8 | walked to y=7, **BLOCKED at (37, y=1 target)** — board edge |
| marker1-col (x=37) | y above 48 | walked to y≈54.5, **BLOCKED heading y=58** — board edge |
| marker2-col (x=13) | y below 8 | BLOCKED at (13, y=7) — board edge |
| marker2-col (x=13) | y above 48 | BLOCKED at (13, y≈54.5) — board edge |
| marker1-row (y=16) | x below 5 | BLOCKED at (x=7, 16) — board edge |
| marker1-row (y=16) | x above 45 | BLOCKED at (x≈54.5, 16) — board edge |
| marker2-row (y=40) | x below 5 | BLOCKED at (x=7, 40) — board edge |
| marker2-row (y=40) | x above 45 | BLOCKED at (x≈54.5, 40) — board edge |

All 8 legs ran to completion (status `DONE`); every block is the **board boundary**, not the
zigzag body — no wall was found anywhere between the raster region and the board edge on
these 4 axis lines. Zero wins. (The non-integer `54.5` centers at the far extension edge are
a measured bbox-parity artifact of partial HUD/edge clipping, not a new object — noted, not
investigated further, out of scope.)

## 5. Phase 3 — band+10 variant, 10/10 central positions, DONE

Band driven +10 presses (A2, n%3==0 phase) before the 2 A5 selects, then the 10 geometrically
most-central overlap-region cells re-visited: `(19,25) (22,25) (25,25) (28,25) (31,25) (19,28)
(22,28) (25,28) (28,28) (31,28)`. All reached, zero wins — consistent with the goal-directed
session's ARM3 finding (band phase had no visible effect), now also checked at multiple
interior positions rather than only at the two marker docks.

## 6. A5-click-alias arm bookkeeping

At **every** visited position across all 3 phases (193 total position-visits, 183 of them
distinct `(cx,cy)` cells — some cells revisited across phases/directions), one A5 press was
tried as a **discarded branch**: `copy.deepcopy(env)` → single A5 press → check
`levels_completed`/`GameState.WIN` → branch dropped. This never touched the main sweep's
`sel_n`, so the "arrows drive S" phase was never disturbed by the click tests. Zero wins from
any of the 193 branch presses.

## 7. Census summary

- Visited-position count: **183 distinct cells** (169 from the full raster + up to 8 marker
  axis-extension endpoints + phase-3 revisits of already-covered cells under a different band
  phase, which do not add new coordinates).
- Visited bbox coordinate range: x ∈ [7, 54.5], y ∈ [10, 54.5].
- Blocked cells: **8**, all board-edge walls on the 4 axis-extension legs; **zero** blocked
  cells inside the raster's overlap region itself.
- A5-click branch tests: **193**, zero wins.
- Total real presses: small enough that no chunk approached the ~127/life budget; no
  game-over, no life exhaustion anywhere in the run.

## Bottom line

Level 5 stays at **4/8**. The region the prior session flagged as untested — S driven onto
the zigzag's body/edges as an axis-exact (not just bbox-exact) dock, across and around the
full zigzag — is now swept exhaustively-in-region: 169/169 raster cells, all 4 marker
axis-lines walked out to the board edge, a band-phase variant, and an A5-click alias at every
stop. No win anywhere. The zigzag's own bbox edges are additionally now known to be
**off-lattice** from this entry (mod-3 parity mismatch) — a genuinely new fact, not previously
recorded — which rules out literal-pixel axis-exact matches against those 4 specific
coordinates by construction, independent of any further sweeping.
