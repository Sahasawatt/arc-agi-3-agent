# ar25 L5 — goal-directed session (2026-08-17)

**Verdict: PREDICATE_FOUND_NOT_REACHED.** The win predicate induced from levels 1-4 (a
colour-5-family piece docks on a colour-11 target, gated by a one-way-door precondition) was
translated to level 5 and driven directly — piece walked to exact-center overlap on both
candidate colour-11 targets, under three different band-phase preconditions — with zero wins.
This independently reconfirms, by live drive rather than by citation, the prior campaign's
exhaustive closure of this level (335k+ click arms, BFS to 66,325 keys, mirror-decouple test).
No new win. One genuinely new fact: this session's own live probe found the L5 action-to-axis
mapping is the *opposite* pairing from what an earlier note recorded (see below) — a correction,
not a lead.

Scripts: `ar25_u1.py` (induction, board diffs) → `results/ar25-u1.txt`; `ar25_u2.py` (direct
drives) → `results/ar25-u2.txt`. Both run clean, exit 0, PYTHONUTF8=1.

## 1. Induced win predicate per level, with board-diff evidence

One continuous replay of `L1_LINE + L2_LINE + L3_LINE + L4_LINE` (`ar25_u1.py`), diffing the
frame immediately before the winning action against the frame at it. All four transitions
landed at the documented action indices (14, 39, 79, 108 — cumulative 109), matching every
prior session's replay exactly:

- **L1 (0→1) at action i=14, action=3 (left):** colour 4 (the mirror sprite, by the module's
  own mechanic doc) and colour 11 (the static target) both change in the same action; this
  matches the docstring's already-sourced claim (`results/ar25-q1..q7.txt`) — *mirror docks on
  the colour-11 target, one axis exact suffices*. Not re-derived pixel-by-pixel here (see
  ANTI-GOALS); reproduced only to confirm the action index and that colour 4/colour 11 are the
  moving/static pair.
- **L2 (1→2) at action i=39, action=2 (down):** colour 4 goes to **zero** (69→0) — the mark/step
  cycle's last untoggle — while colour 11 jumps 103→298. Consistent with the module's own
  comment: a mark/step/untoggle cycle walks the piece to the dock.
- **L3 (2→3) at action i=79, action=3:** colour 4 drops 106→18 and colour 11 rises 85→280 —
  two pegs (colour 5, not tracked as a separate count here since colour 5 doesn't change at
  this transition) land on their SIZE-matched colour-11 rectangles, exactly as `mirror.py`'s own
  comment states: peg A on (42,53,33,44) 12x12, peg B on (42,47,9,20) 6x12, piston parked
  rows 27-29 (precondition, set 7 presses before the first peg click).
- **L4 (3→4) at action i=108, action=4:** colour 4 drops 99→0, colour 5 96→88 (settles to its
  L5-entry shape), colour 11 110→271, colour 12 26→0. Same abstract shape as L3: a wall-row
  precondition (six DOWN presses, set before the first piston click) gates two piston docks.

**Induced predicate, abstracted across all four (different) machines:** *a movable colour-5
piece — sometimes rendered as colour 4 in flight/collision — docks bbox-exact or one-axis-exact
onto a static colour-11 target; the docking machinery itself is a NEW ruleset every level, but
the precondition pattern repeats: a control surface (piston row, wall row) must be set BEFORE
the first piece-selecting click, because selecting a piece is a one-way door.*

## 2. Translation to L5

`ar25_u1.py`'s L5-entry component census (`results/ar25-u1.txt`, tail):

- colour 5 (piece, S): 1 non-HUD component, **88 cells, bbox x42-56 y36-50** (15x15 box, ~39%
  fill) — matches every prior session's identification.
- colour 11 (candidate target): 4 components — a **189-cell zigzag**, bbox x12-38 y15-41,
  with two small **9-cell (3x3) corner markers** sitting at its ends: `(36-38,15-17)` and
  `(12-14,39-41)`. (Plus a 64-cell HUD column at x=63, excluded.) These two corner markers are
  the natural candidate dock points — the same shape-role as L3's small size-matched rectangles.
- colour 10 (band/wall complex): 3 components including a static 192-cell left block and two
  ~fragmented segments at rows 15-17 (the band's current phase, split by the zigzag drawn over
  it — not investigated further, out of scope for this session).

**Translated predicate:** S (88 cells, 15x15 bbox) should dock bbox-exact or axis-exact onto one
of the two 9-cell colour-11 corner markers of the zigzag.

## 3. One-way-door check

L3/L4's lesson is that the control surface (piston row / wall row) must be set **before** the
first piece-selecting click. On L5 the analogous surface is the **band phase** — A5 runs the
documented period-3 cycle (`n%3==0` drives the band, `==1` nothing, `==2` drives S), so at
L5 entry (n=0) the band is already the *active* driven object, and moving it further before
selecting S is exactly "setting a control surface before the first click."

`ar25_u2.py` ARM 3 drove the band 3, 7, and 14 presses (roughly 1/7, 1/3, 2/3 of its 21-phase
range) with plain DOWN presses **before** the two A5 selects, then repeated the marker-1 walk.
All three preconditions converged to the **identical final board** (`bbox=(30,44,9,23,88)` in
all three arms) — i.e. **the band presses had no visible effect on S's approach to the target**
under this drive. This is a narrower, live-re-confirmation of the campaign's earlier
(441-combination) finding that no band phase produces a win; it does not by itself rule out a
band phase this session didn't sample, but it found no analogue of L3/L4's one-way-door effect
in the three phases tried.

## 4. Direct drives — action + outcome

`ar25_u2.py`, five arms, `levels_completed` read after every action:

| arm | precondition | target | outcome |
|---|---|---|---|
| ARM1 | none (entry band phase) | marker1 (37,16) | 13 presses, **S center lands exactly on (37,16)**, bbox (30,44,9,23) — `levels_completed=4`, `state=NOT_FINISHED`. NOT RUN: WIN. |
| ARM2 | none | marker2 (13,40) | 13 presses, center lands on (13,40) area, bbox (6,20,33,47) — `levels_completed=4`. NOT WIN. |
| ARM3a | band +3 DOWN presses first | marker1 | 13 presses after precondition, identical final bbox to ARM1 — `levels_completed=4`. NOT WIN. |
| ARM3b | band +7 DOWN presses first | marker1 | identical outcome — `levels_completed=4`. NOT WIN. |
| ARM3c | band +14 DOWN presses first | marker1 | identical outcome — `levels_completed=4`. NOT WIN. |

Every arm's action budget was ≤17 real presses (2 selects + ≤14 walk + ≤14 precondition),
far under the ~127/life real-move budget, so no arm was budget-constrained.

**Correction found while building the walker (a genuinely new, small fact):** the first version
of the walker used the axis pairing recorded in `results/breadth-recon.md`'s L5 directional
probe (A1/A2 = x-axis, A3/A4 = y-axis) and produced a piece that overshot into a wall on one
axis while never moving the other — the walk was going nowhere. Re-measured directly from the
raw bbox deltas (`results/ar25-u2.txt`, first run, before the fix): **A1 = up (dy -3), A2 =
down (dy +3), A3 = left (dx -3), A4 = right (dx +3)** — the opposite pairing from the earlier
note. Once corrected, S reaches an exact-center overlap with each target in 13 presses (4 on
one axis, 9 on the other — matching the |dx|=12, |dy|=27 distances at 3px/press). This
contradicts an existing repo note and should replace it, but it changes no verdict: with either
pairing the reachable set is identical (only the *route* to a given cell differs), so it does
not reopen any of the exhausted searches.

## 5. Why no mirror-decouple arm was run

`results/breadth-recon.md`'s "2026-08-16 — ar25 L5: MIRROR NOT FOUND" section already ran this
exact test: colour 4 (the L1-4 mirror sprite) is entirely absent from the L5 board at entry and
throughout a 16-press held-against-wall probe; level 4 (where pistons demonstrably move) shows
no lockstep companion for the selected piston either — only the selected piece itself displaces.
A 30-press decoupling walk found no second component ever tracking a matched or offset
displacement. Per ANTI-GOALS ("no re-measuring settled facts"), this was treated as closed and
not repeated; it is the reason step 5 of the brief (mirror lockstep-break test) was not run this
session — the object it would decouple does not exist on this board.

## 6. What this session adds and doesn't

**New:** live re-confirmation (not citation) that the induced L1-4 predicate, translated
literally to L5's two most plausible dock points, does not win — with exact-center arrival
proven by direct measurement, not by trusting the prior campaign's summary. A genuine
axis-mapping correction to a repo note, found and fixed in the course of building the walker.
Three band-phase preconditions tried explicitly as one-way-door candidates, converging
identically (no analogue of L3/L4's precondition effect found in the sampled phases).

**Not new / explicitly not attempted:** re-deriving the band-clamp, A5-alias, or sel_phase-cycle
facts (per ANTI-GOALS, trusted from the recon); a full 21-phase x N-target grid (the existing
441-combination overlap sweep already covers this more thoroughly than three samples could);
BFS or any exhaustive enumeration (explicitly retired, RETIRED with 66,325 keys and a growing
frontier); the mirror-decouple test (object does not exist on this board, already measured).

**Untested and worth naming, not run this session for lack of time:** whether S can be driven
onto the zigzag's *interior* (the 189-cell body, not just its two 9-cell corners) as an
axis-exact rather than bbox-exact dock (S's height 15 vs the zigzag's diagonal extent might
share ONE axis exactly at some intermediate cell, the way L1's mirror dock only needed one axis)
— the two corner markers were chosen as the obvious size-matched candidates by analogy to L3,
but L1's predicate was axis-exact, not size-matched, and that geometry was not swept here.

## Bottom line

Level 5 stays at **4/8**. No arm run this session reached `GameState.WIN` or
`levels_completed >= 5`. The induced-predicate approach was executed as specified — predicate
derived from board diffs, translated, one-way-doors checked, candidate goal driven directly,
mirror-decouple skipped only because it was already disproven — and it did not find a win.
