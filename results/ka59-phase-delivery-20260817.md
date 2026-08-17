# ka59 L2 — arbitrary phase delivery: measured, then hit the resource wall it was meant to escape

2026-08-17. No arm ever reported `levels_completed > 1`. Every run stayed at
`levels_completed=1, state=NOT_FINISHED`. No WIN.

Scripts: `ka59_z1.py` (arm 1), `ka59_z2.py` (arm 2/3 drive attempt),
`ka59_z3.py` (diagnostic — exhaustive BFS from the drive's dead end),
`ka59_z4.py` (diagnostic — can dot2 be kicked to a different phase). Raw
logs: `results/ka59-z1.txt` .. `results/ka59-z4.txt`.

## Arm 1 — MEASURE THE MINT: **WORKS**

Procedure (breadth-recon.md:5772-5775's untested arm): walk to a
deliberately chosen cell (not wherever an auto-route happens to leave the
piece), click a dot, verify the new marker lands exactly on the piece's old
cell; then click that marker and verify the piece is delivered exactly
there, at that cell's phase.

Exact action line (`ka59_z1.py`, from L2 entry `piece=(37,55)`
`dot0=[(34,44),(34,45)]` `dot1=[(41,34),(42,34)]`
`dot2=[(44,47),(44,48),(45,47),(45,48)]`):

| act | tag | move | piece after | phase | extra4 after | levels_completed |
|---|---|---|---|---|---|---|
| 1-6 | walk to box2 | v=1,4,4,4,4,4 | (52,52) | (1,1) | [] | 1 |
| 7 | click dot2 from box2 | CLICK(44,47) | (44,48) | (2,0) | **[(52,52)]** | 1 |
| 8 | click the minted marker | CLICK(52,52) | (52,52) | (1,1) | [(44,47),(44,48),(45,47),(45,48)] | 1 |

**Measurement 1a** (mint lands at the chosen cell): the deliberately chosen
stand cell was `(52,52)` (box2's interior, phase (1,1), picked before any
click). After clicking dot2 from there, `extra4` gained exactly one new
cell: `(52,52)` — **MATCH**, verdict **WORKS**.

**Measurement 1b** (later click delivers to that cell, at that phase): from
`(44,48)`, clicking the minted marker at `(52,52)` landed the piece at
`(52,52)` exactly, phase `(1,1)` exactly matching the chosen cell's phase
— **MATCH**, verdict **WORKS**.

**ARM 1 VERDICT: WORKS.** Arbitrary phase delivery is real: standing on a
chosen cell before clicking mints a marker there, and later clicking that
marker delivers the piece to that exact cell (and phase), independent of
which dot or marker triggered the mint. This confirms the mechanism
everything downstream was going to spend.

## Arm 2/3 (combined) — matched pairing / "any three boxes + piece in box2"

Run as one drive, not two, because arm 1's own result (and the earlier
y9 finding, breadth-recon.md:5531-5545) makes them observationally
identical: markers carry **no identity tag**, so "dot0's marker
specifically in box1" is not a pixel-distinguishable state from "any marker
in box1." Both goals collapse onto the same target board state: box1,
box3, box0 filled and the piece standing inside box2.

**Design** (`ka59_z2.py`): spend arm 1's mechanism to plant a "return
ticket" — walk to box2 (free, spawn's own phase (1,1)), click dot2 there to
mint a persistent marker inside box2 itself. Then run y11's proven line
(kick dot0 west, kick dot1 west, fill box3 with dot1, chain-kick dot0
north, fill box0 with dot0 landing phase (1,2), walk into box1) and, from
inside box1, click box2's own recycled marker — which should fill box1
*and* deliver the piece straight into box2, without spending box3's fill
the way y11 had to.

**Exact action line and where it broke** (`ka59_z2.py`):

| act | tag | move | piece after | phase | extra4 after |
|---|---|---|---|---|---|
| 1-6 | walk to box2 | v=1,4,4,4,4,4 | (52,52) | (1,1) | [] |
| 7 | click dot2 from box2 (MINT) | CLICK(44,47) | (44,48) | (2,0) | [(52,52)] |
| — | approach dot0 for kick | bfs_route(region 35-39,42-46) | — | — | **NO ROUTE — script exits** |

**Diagnosis** (`ka59_z3.py`, the authoritative instrument this game's own
history requires — an exhaustive real BFS that targets nothing and drains
the queue, run from the exact post-mint state, cap 8000): **60 nodes
expanded, 60 distinct reachable positions, EXHAUSTED** (queue drained,
not a cap hit). Reachable bbox `x=[32,60] y=[32,60]`. dot0's cells: **not
reachable**. dot1's cells: **not reachable**. box2's own cell `(52,52)`:
**not reachable**. Dot2's own canonical delivery phase, `(2,0)`, is an
isolated ~60-cell pocket that cannot even walk back to box2, let alone to
either remaining dot.

**Attempted fix** (`ka59_z4.py`): can dot2 be *kicked* to relocate its
delivery phase away from `(2,0)`? Approached from four sides and pressed
into it. Three of four kicks succeeded (relocated dot2's footprint to
three different board regions); one (`from-east-press-west`) found no
route. In every successful kick, the landing footprint's phase set was
**exactly the same** as the pre-kick footprint's phase set — `{(2,2),
(2,0), (0,2), (0,0)}` or a superset including `(0,1),(2,1)` — never
gaining `(1,1)`. This is kicks-preserve-phase (already established for
dot0/dot1) now confirmed for dot2 specifically, closing the gap flagged in
`notes/next-session-prompt.md:374`. **dot2's delivery phase is locked at
`(2,0)` by identity, independent of where it is kicked.**

**ARM 2/3 VERDICT: REFUTED**, with mechanism, not merely NOT_FINISHED. The
drive did not complete (routing failure at action 8), and the diagnosis
shows *why* no reordering of this drive can fix it: box2 needs phase
`(1,1)`; the only three raw resources (dot0, dot1, dot2) have fixed
delivery phases `(1,2)`, `(0,1)`, `(2,0)` — **none is `(1,1)`**; the only
measured `(1,1)`-phase object reachable after crossing into the LEFT
regions is box3's own fill-cell (used by y11, prior session, to reach box2
at the cost of un-filling box3 — the already-measured 2-filled result);
and dot2, the one untouched resource, cannot be kicked into supplying
`(1,1)` because kicking never changes a dot's phase, only its position.
Arbitrary phase delivery (arm 1) is real, but every *object* available to
trigger it on this board still carries a fixed phase, so "choose the
phase" only works for objects already sitting where you need them — it
does not manufacture a new phase from nothing.

y11's own already-measured result stands as the best config reached under
this model: 2 of {box1,box3,box0} filled (box0 via dot0, box1 via box3's
recycled marker) + piece inside box2, `levels_completed` never left 1
(prior session, `results/ka59-y11.txt` — not re-run here per the
anti-goal against re-deriving settled results).

## Arm 3 (the simpler never-achieved config) — same target, same verdict

"Any three boxes filled + piece inside box2" and the matched pairing are
the same board state under an identity-less marker model (see above), so
arm 2's drive and diagnosis **is** the arm-3 attempt. No separate line was
run. Verdict: **REFUTED**, same mechanism as arm 2/3 above.

## Arm 4 — enumerate remaining untried combinations

**"Four boxes filled" (box1, box3, box0, box2 all simultaneously filled):
NOT RUN — deduced impossible from a measured resource law, not executed.**
Reasoning, stated explicitly as a deduction so it is not mistaken for a
live result: exactly three raw markers exist (dot0, dot1, dot2). Every
fill is either (a) a *new* mint from a raw dot — three of these exist,
giving a hard ceiling of three simultaneous independently-sourced fills —
or (b) a *recycle* of an already-placed marker, which by the swap mechanic
(arm 1, and Q1/Q3 in breadth-recon.md:5480-5520) moves a marker from one
cell to another and puts the piece where the marker used to be — this
conserves the fill count, it never increases it, and if the piece's
destination is itself one of the "filled" boxes, the fill count can
*decrease* (the box the piece lands in shows colour 0, not 4). No
sequence of raw mints and recycles can therefore produce more than three
simultaneously filled boxes with three dots. This matches the recon's own
flagged concern (breadth-recon.md:5574): "if the win wants four filled
boxes against three objects that is an impossibility worth stating."

No other combination was run — time budget reached before further arms
could be driven live.

## Summary

| arm | verdict | how established |
|---|---|---|
| 1: measure the mint | **WORKS** | live drive, both measurements exact matches |
| 2/3: matched pairing / 3 filled + piece in box2 | **REFUTED** (with mechanism) | live drive to a dead end + exhaustive-BFS diagnostic + kick-invariance diagnostic |
| 4: four boxes filled | **NOT RUN** — deduced impossible | resource-count argument, not executed |

`levels_completed` never exceeded 1 in any script this session. The
arbitrary-phase-delivery mechanism from breadth-recon.md:5772-5775 is now
fully measured and real, but it does not reopen the win: it lets you place
a marker's *phase* wherever you are standing, not wherever you need the
*next* click to deliver to, and the three dots' delivery phases remain
fixed by identity no matter how they are kicked. ka59 L2's fill-model
closure (breadth-recon.md's "the same place re86 L6 reached") stands,
now with the one previously-untested arm closed by measurement rather
than left open.
