# ka59 L2 -- crossing-table-derived plan + drive (2026-08-17)

**Verdict: LINE_COMPLETE_PARTIAL.** All three of {box0, box1, box3} filled
**simultaneously** for the first time in this repo's ka59 history (`ka59_g3f_drive.py`,
`results/ka59-g3f-run.txt`) -- but the piece ends stranded in an isolated
component, not inside box2. `levels_completed` never left 1. No WIN.
Three independent, positive-controlled exhaustive-BFS measurements
(`g3d`, `g3f`, `g3g`) converge on a structural reason this exact recipe
cannot also deliver the piece into box2 -- reported below, not asserted.

Scripts (all reuse the `safe_route`/`guarded_step`/`safe_kick`/`exhaustive`
harness verbatim from `ka59_g2_safe_route.py`, per the mission brief):
`ka59_g3_crossing_table.py` (Phase 1 survey, 9 rows), `ka59_g3b_chain_followup.py`
(follow-up probe), `ka59_g3c_drive.py`/`ka59_g3d_drive.py`/`ka59_g3e_drive.py`/
`ka59_g3f_drive.py` (Phase 3 drive iterations), `ka59_g3g_probe.py` (final
structural check). Raw logs: `results/ka59-g3-run.txt`, `ka59-g3b-run.txt`,
`ka59-g3c-run.txt`, `ka59-g3d-run.txt`, `ka59-g3e-run.txt`, `ka59-g3f-run.txt`,
`ka59-g3g-run.txt`.

## Phase 1: the crossing table

Full table: `results/ka59-crossing-table-20260817.md` (9 rows: {dot0,dot1,dot2}
x {entry, west-kicked, chain-north-attempt}, each on a fresh deepcopy from
level-2 entry, each with an exhaustive real-BFS census + positive control).

**What it confirmed live** (matches the recon's MODEL CORRECTION exactly):
dot0 west-kick -> `(19,44)` phase `(1,2)`; dot1 west-kick -> `(18,34)` phase
`(0,1)`; dot2 west-kick -> `(18,50)` phase `(0,2)` (byte-identical to `g2`'s
independently-measured wall). Every one of the three west-kicked landings
can reach **box0's interior at its own delivery phase** directly (no
band-crossing needed -- box0 sits in the same south-of-band region all
three west-kicks land in): dot0->`[(7,44),(10,44)]`, dot1->`[(6,43),(6,46)]`,
dot2->`[(6,44)]`. None of the nine rows' generic single-round chain-north
probe advanced (0 rounds in all three cases) -- **not because no chain
exists**, but because a chain-kick attempted BEFORE the piece has crossed
the moat is asking to walk a west-side region from the east side, which is
categorically unreachable (confirmed both by exhaustion and by the
follow-up below).

**Follow-up finding (`ka59_g3b_chain_followup.py`):** even after ALSO
kicking dot1 west first (removing it as a hypothesised corridor-blocker,
matching `y11`'s own proven order), dot0's chain-north still found no
approach route with 0 rounds completed. Re-reading `ka59_y11.py` line by
line settled it: **its chain-kick happens AFTER a crossing click** (stand
in box3, click dot1), not before. Kicking never moves the piece across the
moat; only a click does. This was the missing precondition, confirmed by
successfully reproducing the chain in the drive below once sequenced after
a real crossing.

## Phase 2: the plan, derived from the table + `y11`/`t2` ground truth

Re-reading `ka59_y11.py` (its own recorded run, `breadth-recon.md:5615-5665`)
established the resource picture: 3 dots, dot0's phase set (1,2)/(1,0)
matches box1's own centre phase exactly (dot0 is box1's key, via west-kick +
post-crossing chain-north); dot1's west-kick + click-from-inside-box3 both
crosses the piece and fills box3; dot2 is untouched in every prior
successful line. `y11` itself reached 2-of-3 filled + piece in box2 by
recycling box3's OWN marker into box1 -- which **empties box3**, so it can
never be 3-of-3. `ka59_t2.py` additionally proved **box2 is reachable
directly from spawn** (phase (1,1), same 129-node east-side region, no
crossing needed), which is what makes a "mint" (park a marker in box2 early,
recycle it later from the last unfilled box to deliver the piece there)
resource-plausible: 3 dots exactly cover {mint, box0, box3} and the final
recycle-click delivers the piece into box2 while filling the last box (box1)
for free -- exactly the untested configuration `breadth-recon.md:5658-5660`
names ("three fills and the piece inside box2, simultaneously, at the end,
remains untested").

## Phase 3: the drive

| Attempt | What it tried | Result |
|---|---|---|
| `g3c` | mint via dot2 FIRST (before any kicks) | **BROKE_AT_LEG_2**: from dot2's entry landing `(44,48)` phase `(2,0)`, no safe route to dot0's approach region at all |
| `g3d` | both kicks first, THEN mint via dot2 | **BROKE_AT_LEG_4**: same `(44,48)`/`(2,0)` landing (kicking dot0/dot1 first doesn't change dot2's OWN unkicked position) -- exhaustive census: **88 nodes, EXHAUSTED**, does not reach box3 |
| `g3e` | drop the mint; swap y11's step-G object from box3's marker to dot2 (click dot2 from inside box1 instead) | full line ran to leg 4 (chain-kick) then hit a **harness bug**: the kick's `target_cells` named only dot0's reference cell, not its full 2-cell footprint, so the kick's OWN second cell "vanishing" tripped a false-positive safe-route violation |
| `g3f` | g3e + bugfix (target_cells = dot0's full footprint) | **RAN CLEAN END TO END.** See below. |
| `g3g` | quick probe: does minting via dot1 (not dot2) avoid stranding? | No -- dot1's mint-landing `(42,34)` phase `(0,1)` is a **79-node exhausted** component that reaches box3 but **not** dot0's approach region, box0, or box1 |

### `g3f`'s line (the reported result)

kick dot0 west -> kick dot1 west -> walk to box3, click dot1 (crosses +
fills box3) -> chain-kick dot0 north (**this time it worked**, landing
`(19,20)/(19,21)`, matching the recon's known chain landing exactly, now
that it correctly runs post-crossing) -> walk to box0, click dot0 (fills
box0, piece -> `(19,20)` phase `(1,2)`, exact match) -> walk to box1 ->
click dot2 (untouched, still at its entry cell) from inside box1.

**Result: box0 filled, box1 filled, box3 filled -- ALL THREE simultaneously,
first time this configuration has ever been reached in this repo's history**
(prior best was `y11`'s 2-of-3, because its recipe structurally empties one
box to fill another). Piece ends at `(44,48)` phase `(2,0)` -- dot2's own
canonical cell -- **not** inside box2. 43 total actions, `levels_completed`
stayed 1 throughout, confirmed by reading it after every single action
(never just at the end).

### Why it can't (yet) also land in box2 -- three converging measurements, not one guess

1. **`g3d`**: dot2's raw canonical landing `(44,48)`/`(2,0)` is an exhausted
   88-node component with **zero** overlap with box3's interior, regardless
   of whether the kicks happened before or after.
2. **`g3f`**: the same 88-node component (re-measured independently at the
   end of the full drive, fills = {box0,box1,box3}) has **zero** overlap
   with box2's interior either (`box2 interior reachable (any phase): []`).
3. **`g3g`**: substituting dot1 for the mint instead of dot2 does not help
   -- dot1's own canonical landing `(42,34)`/`(0,1)` is a *different*
   79-node exhausted component that reaches box3 but **not** dot0's
   approach region, so it breaks the box0/box1 half of the line instead.

**The structural read:** dot0 and dot1 are each required, by their own
measured phase sets, for one specific half of the line (dot0 -> box1's
(1,2) key; dot1 -> the box3 crossing). Whichever of the three dots is
"free" to spend on the mint (or on the final box1-fill, as in `g3f`) is
therefore always dot2 -- and dot2's own canonical cell, in every position
measured across this session (entry `(44,48)`/`(2,0)`, west-kicked
`(18,50)`/`(0,2)` from the crossing table), is an isolated, exhausted
component disconnected from box2, box3, and dot0's approach region alike.
**No reordering fixes this**, because the disconnection is a property of
dot2's landing cell's phase-component, not of when the click happens.

This is reported as a **measured wall on the specific 3-dot resource
assignment tested**, not as a proof that no line exists: an object
positioned so its OWN canonical cell already sits inside box2 (rather than
a marker planted there via a sacrificial click) has not been found or
ruled out, and was out of this session's time budget.

## Anti-goals compliance

No static-map reachability was used for any verdict -- every reachability
claim is a real exhaustive BFS with a positive control (Phase 1's `census()`
helper, reused for every row and every drive-break), or a directly observed
`extra4`/`dot_cells` diff via the belt-and-braces asserts inherited from
`ka59_g2_safe_route.py`. No known wall was re-run blind: `g3f`'s 3-simultaneous-
fill configuration is new (never reached before in this repo), and its final
stranding census is a fresh measurement, not an assumption. Every routed leg
went through `safe_route` (proactive forbidding) and `guarded_step` (reactive
assert); the one violation caught (`g3e`) was a genuine bug in this
session's OWN code (an incomplete `target_cells` list), diagnosed from the
assert's own printed diff and fixed before the reported run. No full-game
BFS was run -- every exhaustive BFS was scoped to board positions from the
current live state (15,000-node cap; all censuses in this session exhausted
well under it, largest was 129 nodes in `t2.py`'s prior-session reference).

## Files

- `ka59_g3_crossing_table.py` / `results/ka59-crossing-table-20260817.md` /
  `results/ka59-g3-run.txt` -- Phase 1 survey.
- `ka59_g3b_chain_followup.py` / `results/ka59-g3b-run.txt` -- chain
  precondition follow-up.
- `ka59_g3c_drive.py` .. `ka59_g3g_probe.py` / `results/ka59-g3c-run.txt` ..
  `ka59-g3g-run.txt` -- Phase 3 drive iterations (see table above).
