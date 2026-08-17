# ka59 L2 -- driving REDESIGN 4 (the FORCED assignment): BROKE_AT_LEG_3 (CHECK B')

2026-08-17. Verdict: **BROKE_AT_LEG_3 (CHECK B')**. `levels_completed` never left 1. No WIN.
Script: `ka59_s1_forced.py`. Raw logs: `results/ka59-forced-run4.txt` (final, correct run),
`results/ka59-forced-run.txt`/`-run2.txt`/`-run3.txt` (earlier runs of the same script used to
diagnose and fix an instrument bug -- see below; superseded by run4, kept for the audit trail).

## Instrument fact found this session (load-bearing -- changes the leg-1/2 reading)

**The auto-settle press after a MINT click's transient corrupted frame can itself KICK an
unrelated dot, because it is a REAL action chosen only by "does this un-corrupt the frame",
never by "does this disturb something else."** Minting via dot2 (clicking dot2 while standing
in box2) teleports the piece to dot2's canonical cell and leaves one corrupted frame (the
known `ka59_u2.py` transient). The fixed settle order `(1,4,3,2)` tried north and east first
(both failed to produce a valid `piece_xy`) and resolved on **west** -- which, from the
post-teleport landing near `(17-18,44-48)`, walked the piece into **dot0** at `(13,44)/(13,45)`
and kicked it **12 cells west to the wall clamp, landing at `(1,44)/(1,45)`**. This was caught
by comparing dot0's position before MINT (`(13,44)/(13,45)`, matches leg 1's identification)
against right after MINT+settle (`(1,44)/(1,45)`) in an instrumented rerun (`-run2.txt`/
`-run3.txt`); the FIRST attempt (`-run.txt`) used the stale pre-mint `d0_now` value to compute
CHECK A'/B's approach regions and got **0 of 4 kick directions finding a route at all**
(silently targeting empty cells dot0 no longer occupied) -- a pure instrument artifact, not a
game fact. Fixed by re-deriving `d0_now` from the live board immediately after MINT+settle;
`ka59_s1_forced.py` now does this (see its "INSTRUMENT FACT" comment). All results below are
from the corrected run.

## Per-leg table

| leg | action | piece after | phase | extra4 after | levels_completed | result |
|---|---|---|---|---|---|---|
| entry | -- | (37,55) | (1,1) | [] | 1 | -- |
| 1 | compound sweep | (49,49) | (1,1) | [] | 1 | **WORKS** -- dot0 (34,44)/(34,45) -> (13,44)/(13,45); dot2 (44,47..45,48) -> (17,47)/(17,48)/(18,47)/(18,48). Matches every prior session (t1/t2/u1). |
| 2 | walk into box2, MINT click dot2 | (18,48) | (0,0) | [(52,52)] | 1 | **WORKS** -- box2 stand cell (52,52) confirmed reachable (t2/u1 reused live); ticket planted at (52,52); MINT's transient-smear settle fired (v=3), and its side effect kicked dot0 to (1,44)/(1,45) -- see instrument fact above. |
| CHECK A' | dot0-kick-approach region (132 cells, recomputed around dot0's REAL post-settle position) reachable? | (18,48) | (0,0) | [(52,52)] | 1 | **REACHABLE, narrowly** -- 52-node exhaustive BFS (EXHAUSTED), only 3 of 132 approach cells reachable: (2,36), (8,42), (8,44). Positive control PASS (real press landed at (18,50), in reachable set). |
| CHECK B' / leg 3 | chain-kick dot0, all 4 directions from (1,44)/(1,45) | -- | -- | [(52,52)] | 1 | **BROKE** -- south-approach (needed for a NORTH kick) and west-approach both had **NO ROUTE** (their target cells fall outside the 52-node reachable component -- dot0 sits jammed against the absolute west wall, x=1, one column outside the piece's own reachable bbox x=[2,18]). north-approach-press-south DID kick (1 real kick, verified `moved=True`) but drove dot0 further away from the band, to (1,59)/(1,60) -- wrong direction. east-approach-press-west found **zero movement** (kicks=0) after 8 real presses each round (dot0 stayed (1,44)/(1,45) throughout, confirmed via live `dot_cells` reads that are unaffected by the piece's own transient colour-0 corruption on several of those presses). |
| 4 (box0 fill) | NOT RUN | -- | -- | -- | -- | leg 3 broke first |
| 5 (CHECK D', box1) | NOT RUN | -- | -- | -- | -- | leg 3 broke first |
| 6 (box1 from afar) | NOT RUN | -- | -- | -- | -- | leg 3 broke first |
| 7 (CHECK E', box3) | NOT RUN | -- | -- | -- | -- | leg 3 broke first |
| 8 (FINAL click ticket) | NOT RUN | -- | -- | -- | -- | leg 3 broke first; ticket still parked unused in box2 at (52,52) |

## CHECK A' detail

Exhaustive real BFS from the post-mint state: **52 nodes expanded, 52 distinct reachable
positions, EXHAUSTED** (well under the 15,000 cap -- the queue drained, not the cap). Reachable
bbox `x=[2,18] y=[32,60]`. Of the 132-cell union of all 4 kick-approach regions around dot0's
real position (1,44)/(1,45), only `[(2,36),(8,42),(8,44)]` are reachable -- three isolated
corners, one per surviving approach direction (south and west approaches are entirely outside
the reachable set; their region cells run partly off-board since dot0 sits against the wall).
Positive control: a real press from this state landed at (18,50), confirmed inside the
reachable set (**PASS**).

## CHECK B' detail -- all 4 kick directions, real presses

```
south-approach-press-north: NO ROUTE TO APPROACH
north-approach-press-south: moved=True  kicks=1  d0_after=[(1,59),(1,60)]  crossed_band=False
west-approach-press-east:   NO ROUTE TO APPROACH
east-approach-press-west:   moved=False kicks=0   d0_after=[(1,44),(1,45)] crossed_band=False
```

South and west approaches are unreachable at the census level (CHECK A' already showed this --
their region cells are not among the 3 reachable ones). North-approach genuinely kicks dot0 (a
real, verified kick -- `moved=True` on live `dot_cells`), but the only approachable direction
from north drives dot0 **south**, away from the band, to `(1,59)/(1,60)`. East-approach reached
adjacent cells `(8,44)/(8,42)` but 8 real west-presses per round, 6 rounds, produced **zero**
change in dot0's position -- a genuine null read on live colour-5 cells, unaffected by the
piece's own colour-0 corruption on several of those presses (`piece_xy=None` transients did not
prevent reading `dot_cells`, which is a different colour channel).

**The mechanism: dot0 is jammed flush against the absolute west wall (x=1) by the mint-settle's
side kick, one column outside the piece's own reachable bbox (x=[2,18]).** The only kick
direction with both a real approach route AND a real registered kick (north-approach) pushes it
the wrong way; the one direction that would help (south-approach, press north) cannot even be
approached -- its cells are not in the 52-node reachable component at all.

## Census (what IS reachable from the broken state)

52 nodes expanded, 52 distinct positions, EXHAUSTED, bbox `x=[2,18] y=[32,60]`:

- box0 interior cells reachable (any phase): `[(8,42),(8,44)]`
- box1 interior cells reachable (any phase): `[]`
- box3 interior cells reachable (any phase): `[]`

## Verdict

**BROKE_AT_LEG_3 (CHECK B').** Config reached: **zero of {box0,box1,box3} filled**, ticket
parked in box2 at `(52,52)` (unused), piece at `(18,48)` phase `(0,0)`, `levels_completed=1`
throughout. Total real actions: **42**.

This is a genuine negative result, but it breaks **one leg earlier** than the prior session's
`ka59_u1.py` (BROKE_AT_LEG_5, one box filled) -- not because Redesign 4's assignment logic is
wrong, but because **swapping which dot mints (dot2 instead of dot0) exposed a new mint-settle
side effect that the box3-last redesign never triggered**: minting via dot0 (u1.py's leg 2) put
the settle press somewhere that never touched dot2; minting via dot2 (this session's leg 2) put
it somewhere that clipped dot0 and threw it into a wall-jammed corner before the deliberate
chain-kick ever got a turn. The forced assignment itself (dot0 must be the box0-filler because
box1 only succeeds at phase (1,2)) is not refuted by this -- it is simply never reached, because
an earlier, unrelated mechanic (the settle's blind direction choice) spent dot0's favourable
position before leg 3 could use it.

**Per the brief: any check failing closes the ticket-construction across all
measurement-consistent assignments named in breadth-recon.md's "BROKE_AT_LEG_5" tail.** Redesign
4 was stated there as "the last assignment consistent with every measurement." With CHECK B'
failed here, **every dot-role assignment this campaign has been able to derive from the
box1-needs-(1,2) constraint has now been tried and broken** -- box3-last/mint-via-dot0
(`ka59_u1.py`, BROKE_AT_LEG_5, one box filled) and box3-last/mint-via-dot2 (this session,
BROKE_AT_LEG_3, zero boxes filled, but for an incidental instrument reason rather than a
structural one). **LINE_COMPLETE_NO_WIN was not reached in either.** The best config any session
has reached on this game remains y11's: 2 of {box1,box3,box0} filled + piece in box2, via a
different, box3-un-fill route (predating this campaign's box3-last family entirely).

The one thing this session adds beyond the prior negative: **a MINT click's recovery settle is
not neutral** -- it can spend a resource (a dot's favourable position) that the very next leg of
the plan was counting on, and this is now a documented risk for any future MINT-adjacent-to-a-
raw-dot construction on this game.
