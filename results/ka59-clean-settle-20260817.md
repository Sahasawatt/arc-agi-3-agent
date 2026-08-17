# ka59 L2 -- attempt 5: Redesign 4 with a dot-avoiding settle: BROKE_AT_LEG_3 (CHECK B'), UNCONTAMINATED -- family CLOSED

2026-08-17. Verdict: **BROKE_AT_LEG_3 (CHECK B'), FAMILY_CLOSED**. `levels_completed` never left 1.
No WIN. Script: `ka59_s4_clean_settle.py`. Raw log: `results/ka59-clean-settle-run.txt`.

This is attempt 5 -- Redesign 4 (breadth-recon.md's "BROKE_AT_LEG_5 ... dot ASSIGNMENT is now
forced" spec) UNCHANGED, with **THE ONE CHANGE**: the MINT-recovery settle press is now chosen
so it does not touch/kick ANY dot, instead of being picked only by "does this un-corrupt the
frame" (the bug that contaminated the prior session's `ka59_s1_forced.py` run -- it walked the
settle into dot0 and kicked it 12 cells to the wall before CHECK B' ever got a real turn; see
`results/ka59-forced-assignment-20260817.md`).

## THE ONE CHANGE -- verified working

At the MINT-click settle (action #10-11), the fix trialed all 4 directions via `deepcopy` (free,
no real action spent) before committing one for real:

```
settle-trial v=1 resolved=False dots_disturbed=False
settle-trial v=4 resolved=False dots_disturbed=False
settle-trial v=3 resolved=True  dots_disturbed=True   dots_before=[(13,44),(13,45),(41,34),(42,34)]
                                                        dots_after=[(1,44),(1,45),(41,34),(42,34)]
settle-trial v=2 resolved=True  dots_disturbed=False
settle choice: v=2 (CLEAN -- resolves AND touches no dot)
```

v=3 (west) is exactly the direction the old fixed-order settle (`1,4,3,2`) would have picked
first among the resolving ones in the OLD script's priority -- and it is the one that kicks dot0
to the wall, reproducing the prior session's accident inside this session's own trial data. The
new logic instead picked **v=2**, which resolves the corruption AND leaves every dot untouched.

Post-commit verification (real action #11): `SETTLE-CHECK: every dot unchanged from pre-settle:
True before=[(13,44),(13,45),(41,34),(42,34)] after=[(13,44),(13,45),(41,34),(42,34)]` -- the
`assert settle_clean` in `step_log()` passed (no AssertionError raised; script continued).

**Leg-2 payoff assertion** (per the brief, "assert dot0 still at its sweep landing"):

```
ASSERT (THE ONE CHANGE): dot0 after MINT+settle: [(13, 44), (13, 45)] -- sweep landing was
[(13, 44), (13, 45)] -- UNCHANGED=True
```

Dot0 is confirmed to still be at its leg-1 sweep landing before CHECK A'/B' ever run -- this
session's negative result is not contaminated the way the prior session's was.

## Per-leg table

| leg | action | piece after | phase | extra4 after | levels_completed | dot0 position | result |
|---|---|---|---|---|---|---|---|
| entry | -- | (37,55) | (1,1) | [] | 1 | (34,44)/(34,45) | -- |
| 1 | compound sweep | (49,49) | (1,1) | [] | 1 | (13,44)/(13,45) | **WORKS** -- dot0 -> (13,44)/(13,45); dot2 -> (17,47)/(17,48)/(18,47)/(18,48); dot1 untouched (41,34)/(42,34). Matches every prior session. |
| 2 | walk into box2, MINT click dot2 | (18,50) | (0,2) | [(52,52)] | 1 | (13,44)/(13,45) **UNCHANGED** | **WORKS, cleanly** -- ticket planted at (52,52); dot-avoiding settle picked v=2, verified+asserted dot0 unchanged from sweep landing. |
| CHECK A' | dot0-kick-approach region (132 cells) reachable? | (18,50) | (0,2) | [(52,52)] | 1 | (13,44)/(13,45) | **REACHABLE, narrowly** -- 44-node exhaustive BFS (EXHAUSTED), 4 of 132 approach cells reachable: (12,36),(14,36) [north-approach], (6,42),(6,44) [west-approach]. South- and east-approach regions: 0 reachable cells. Positive control PASS (real press landed at (18,54), in reachable set). |
| CHECK B' / leg 3 | chain-kick dot0, all 4 directions | -- | -- | [(52,52)] | 1 | see below | **BROKE** -- only north- and west-approach have routes (matches CHECK A'); both produce a real, verified kick, but neither crosses the band. |
| 4 (box0 fill) | NOT RUN | -- | -- | -- | -- | -- | leg 3 broke first |
| 5 (CHECK D', box1) | NOT RUN | -- | -- | -- | -- | -- | leg 3 broke first |
| 6 (box1 from afar) | NOT RUN | -- | -- | -- | -- | -- | leg 3 broke first |
| 7 (CHECK E', box3) | NOT RUN | -- | -- | -- | -- | -- | leg 3 broke first |
| 8 (FINAL click ticket) | NOT RUN | -- | -- | -- | -- | -- | leg 3 broke first; ticket still parked unused in box2 at (52,52) |

## CHECK A' detail

Exhaustive real BFS from the post-mint, dot0-verified-unmoved state: **44 nodes expanded, 44
distinct reachable positions, EXHAUSTED** (well under the 15,000 cap). Reachable bbox
`x=[2,18] y=[32,60]`. Of the 132-cell union of all 4 kick-approach regions around dot0's real
(unchanged) position (13,44)/(13,45), only `[(12,36),(14,36),(6,42),(6,44)]` are reachable --
2 cells in the north-approach region, 2 in the west-approach region; south- and east-approach
regions are entirely unreachable. Positive control: a real press from this state landed at
(18,54), confirmed inside the reachable set (**PASS**).

## CHECK B' detail -- all 4 kick directions, real presses

```
south-approach-press-north: NO ROUTE TO APPROACH
north-approach-press-south: moved=True  kicks=1  d0_after=[(13,59),(13,60)]  crossed_band=False
west-approach-press-east:   moved=True  kicks=1  d0_after=[(31,44),(31,45)]  crossed_band=False
east-approach-press-west:   NO ROUTE TO APPROACH
```

South- and east-approach are unreachable at the census level (CHECK A' already showed this --
their region cells are not among the 4 reachable ones; "NO ROUTE" here is a bounded-BFS
confirmation of that exhaustive-BFS finding, not a separate failure -- consistent with the
ANTI-GOALS clause "an arm not run = NOT RUN": no real kick presses were attempted in either of
those two directions because no route to their approach cells exists at all).

The two directions that DO have a route both produce a real, verified kick (live `dot_cells`
reads, unaffected by the piece's own transient colour-0 corruption on some of the intervening
presses):

- **north-approach-press-south** pushes dot0 south, from y=44/45 to y=59/60 -- away from the
  band (y=24-29), the wrong direction.
- **west-approach-press-east** pushes dot0 east, from x=13 to x=31, at the same y (44/45) --
  purely horizontal, does not touch the band's y-range at all.

Neither of the two reachable kick directions can drive dot0 north past the band. No arm was
run more than once per state (the north- and west-approach trials are independent, each starting
fresh from the same post-CHECK-A' state).

## Census (what IS reachable from the broken state)

Same 44-node exhaustive BFS as CHECK A' (the state is unchanged -- neither kick trial crossed
the band, so `cur_e`/`cur_o` never advanced past the post-mint-settle state):

- box0 interior cells reachable (any phase): `[(6,42),(6,44)]`
- box1 interior cells reachable (any phase): `[]`
- box3 interior cells reachable (any phase): `[]`

## Verdict: BROKE_AT_LEG_3 (CHECK B'), FAMILY_CLOSED

**Config reached**: zero of {box0,box1,box3} filled, ticket parked in box2 at `(52,52)` (unused),
piece at `(18,50)` phase `(0,2)`, `levels_completed=1` throughout. **Total real actions: 52.**
LINE_COMPLETE_NO_WIN was NOT reached (no box got filled at all in this line).

**This is the genuine, uncontaminated result the prior session's `BROKE_AT_LEG_3` reading was
reaching for and missed.** With dot0 verified to still be at its sweep landing before CHECK
A'/B' ran, this session establishes for real -- not by accident of an unconstrained settle --
that dot0's kick-approach region from the post-mint-via-dot2 state offers only two directions
with a route, and neither one can push dot0 north past the internal band.

**Per the brief: this closes the box3-last / box1-needs-(1,2)-forced-assignment family
(Redesign 4).** Both dot-role assignments consistent with the box1-only-succeeds-at-(1,2)
constraint have now been tried, for real:

- box3-last / mint-via-dot0 (`ka59_u1.py`, prior campaign): **BROKE_AT_LEG_5** -- box0 filled,
  box1 unreachable at phase (1,2) after that.
- box3-last / mint-via-dot2 (this family, two attempts): first attempt (`ka59_s1_forced.py`)
  broke at CHECK B' but was **contaminated** by an unconstrained settle spending dot0's sweep
  position; this session (`ka59_s4_clean_settle.py`), with that contamination fixed, **also
  breaks at CHECK B'** -- for a genuinely structural reason (only 2 of 4 kick approaches are
  reachable, and neither crosses the band), not an instrument accident.

**Every dot-role assignment this campaign has been able to derive from the box1-needs-(1,2)
constraint has now been tried and broken, cleanly.** The best config any session has reached on
this game remains y11's: 2 of {box1,box3,box0} filled + piece in box2, via a different,
box3-un-fill route that predates this campaign's box3-last family entirely.

The instrument lesson from this session: **a settle chosen to avoid disturbing every currently-
live dot is achievable at zero real-action cost** (4 deepcopy trials, one real commit) and is
now the general behaviour of `step_log()`'s settle handling for any future MINT-adjacent
construction on this game.
