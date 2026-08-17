# ka59 L2 -- safe_route harness fix + composed line #1, re-driven (2026-08-17)

**Verdict: BROKE_AT_LEG_4, confirmed independently from TWO different fill
orderings (primary line and its named fallback), both converging on the
IDENTICAL wall.** `levels_completed` never left 1. No WIN. This is a
new measurement (this exact landing cell/fill-state was never censused
before), not a re-run of a known wall.

Scripts: `ka59_g2_safe_route.py` (harness fix + primary line, legs 1-8),
`ka59_g2b_fallback.py` (copy of the primary script with legs 3/3b replaced
by the mission's named fallback: fill box3 via dot1 instead of dot2, cross
by clicking dot2 directly). Raw logs: `results/ka59-g2-run5.txt` (final
primary run), `results/ka59-g2b-run.txt` (fallback run). Earlier numbered
runs (`ka59-g2-run.txt`..`run4.txt`) are the iteration history that found
and fixed two harness bugs before the reported run -- kept for the record,
not part of the verdict.

## THE HARNESS FIX -- `safe_route` -- built and validated

`safe_route(env, obs, is_target, protect, ...)`: a BFS route that forbids
landing on the 8-neighbourhood+footprint of every cell in `protect` (live
dots/loose markers this leg has no business touching) unless the landing
cell is the leg's own declared destination (`is_target`). `guarded_step` /
`safe_walk` / `safe_kick` are the belt-and-braces half: after **every**
press, the full live dot+marker cell set is diffed against before; any cell
that vanished (an object moved off it) that was not the leg's own declared
`target_cells` aborts the leg immediately via `fail()`, printing which
press (by act#) and which cells moved.

**The fix caught something on the very first run** (`ka59-g2-run.txt`):
leg 2's kick-west press moved dot0 from `(19,44)` to `(13,44)` *and* dot2
from its post-approach cell to `(17,47)`-family, in the same press. That
is the **documented, known-fine "compound sweep"** from the mission brief,
not contamination -- but the harness correctly refused to assume that; it
aborted loudly with the exact before/after cell sets, which is what let it
be told apart from real contamination. The fix: declare both dot0's and
dot2's current cells as the kick's legitimate targets for that one press.
This is the harness behaving exactly as specified -- it does not
distinguish "good" surprises from "bad" ones on its own, it just refuses
to proceed silently, and a human (this session) read the diff and decided.

Two more bugs were found and fixed by the SAME instrument before the
composed line could run cleanly, both classification bugs, not harness
bugs: (1) a nearest-old-position heuristic misidentified which swept dot
was dot0 vs dot2 (Euclidean-nearest is the wrong discriminator for a sweep
-- fixed by trusting the mission's own documented fact, dot0 lands at
smaller x); (2) downstream code clicked the (13,44) dot for box3's fill --
which, per the corrected identity, is actually dot0, not dot2 -- silently
consuming the wrong object. Both are `verification-layers`-class findings:
a plausible-looking geographic filter and a plausible-looking distance
heuristic were each wrong in ways that would have produced a confidently
wrong "leg 3 succeeded" without ever tripping a python exception.

## Per-leg table (primary line, `ka59_g2_safe_route.py`, final run)

| Leg | Actions | Piece (final) | Phase | extra4 | lvl | Object-position asserts |
|---|---|---|---|---|---|---|
| 0-entry | 0 | (37,55) | (1,1) | [] | 1 | -- |
| 1: kick dot0 west | 4 | (37,46) | (1,1) | [] | 1 | PASS (3 approach + 1 kick, all guarded) |
| 2: kick dot2 west | 7 | (49,46) | (1,1) | [] | 1 | PASS (6 approach + 1 kick; kick press correctly exempted the documented compound sweep, dot0 (19,44)->(13,44) + dot2 ->(17,47)-family, and nothing else moved) |
| 3: box3 via dot2, cross LEFT | 6 | (18,50) | (0,2) | [(55,40)] | 1 | PASS (4 approach + 1 click + 1 clean settle, dot0 untouched throughout) |
| 3b: south-approach probe | 0 | (18,50) | (0,2) | [(55,40)] | 1 | one-shot fixed-window `safe_route` probe found no path (informational only, non-fatal by design -- see census below) |
| 4: chain-kick dot0 north | 0 | (18,50) | (0,2) | [(55,40)] | 1 | round 0's own dynamically-recomputed approach also found no safe route -- **BROKE_AT_LEG_4** |
| 5-8 | -- | -- | -- | -- | -- | **NOT RUN** (blocked by leg 4) |

Total actions to the break: **17**.

### Census at the break (leg 3b / leg 4, primary line)

Exhaustive real BFS from `(18,50)` phase `(0,2)`, fills = `{box3}` (filled
via dot2): **44 nodes expanded, 44 distinct positions, EXHAUSTED** (well
under the 15,000 cap -- this is the queue actually draining, not a budget
cutoff). Positive control: one real press from this state landed at
`(18,54)`/`(13,38)` (varies by which probe), confirmed inside the
reachable set -- **PASS**, so the BFS instrument itself is trusted.

Of that 44-cell reachable set: **box0 interior reachable (any phase): 2
cells** (`(6,42)`, `(6,44)`) -- none at the phase the fill would need.
**box1 interior reachable: 0 cells. box3 interior (beyond the fill):
0 cells.** Dot0's own dynamically-recomputed south-approach region (the
same shape leg 4's per-round loop uses) is not inside this 44-cell set
either -- confirmed both by the one-shot `safe_route` probe (leg 3b) and
by leg 4's own round-0 attempt failing identically.

**This is a real wall, not an instrument artifact**: exhausted (not
capped), positive-controlled, and reproduced with the belt-and-braces
asserts all PASSing throughout (no contamination confound this time).

## Fallback order (`ka59_g2b_fallback.py`) -- run per the mission's own
## contingency clause, since the check above failed

Legs 1-2 (kick dot0 west, kick dot2 west) are byte-identical to the
primary run (same compound sweep, same landing cells). From there:

| Leg | Actions | Piece (final) | Phase | extra4 | lvl | Object-position asserts |
|---|---|---|---|---|---|---|
| FB3: box3 via **dot1** (no crossing) | 5 | (42,34) | (0,1) | [(55,40)] | 1 | PASS |
| FB3c: cross via clicking dot2 directly | 2 | (18,50) | (0,2) | [(41,34),(42,34),(55,40)] | 1 | PASS |
| 4: chain-kick dot0 north | 0 | (18,50) | (0,2) | (same) | 1 | round 0 found no safe route -- **BROKE_AT_LEG_4, same wall** |
| 5-9 | -- | -- | -- | -- | -- | **NOT RUN** |

Total actions to the break: **18**.

**New mechanic fact, confirmed live**: FB3c clicked dot2's cell `(17,47)`
from the piece standing at `(42,34)` -- **not adjacent, 25+ cells away**
-- and the swap fired anyway, landing the piece at the identical `(18,50)`
phase `(0,2)` cell the primary line's dot2-click produced. **The click
swap does not require proximity to the target**; only the piece's current
context (inside a box or not) determines what happens to the swapped
object. This was an open question in the mission brief's language
("cross by clicking dot2 later from wherever appropriate") and is now
answered: "wherever" is literal.

**The fallback hits the IDENTICAL wall as the primary line** -- same
landing cell, same phase, same 44-node exhausted census, same absence of
box0/box1 reachability. Filling box3 via dot1 instead of dot2 does not
change dot2's own kicked position or the geometry of its crossing click,
so it cannot change where the piece lands after crossing. **This rules
out the wall being an artifact of which dot fills box3** -- it is a
property of the crossing landing cell itself (`(18,50)` phase `(0,2)`)
combined with box3 being filled, independent of ordering.

**Additional cost of the fallback, confirmed structural, not attempted
further**: dot1 is spent on box3 in this ordering, so the mission's
"return-click fill" mechanic for box1 (leg 7 -- click dot1, still at
entry, from inside box1) has no live dot1 left to click. Leg 7 reports
this gap explicitly (`7-box1-fill-BLOCKED` in the leg table) rather than
fabricating a fill. The only candidate left unexamined is recycling
box3's own marker via a halo-eject (the PRIORITY-1 mechanic validated in
the prior session, `results/ka59-guided-search-20260817.md`) -- **not
attempted, time budget**.

## Arm 9 (bonus, pre-park dot1's marker as a box2 ticket)

**NOT RUN.** Per the mission's own framing this arm only matters if leg 8
is reached and fails; leg 8 was never reached in either ordering (both
broke at leg 4), and both orderings hit the identical wall regardless of
how box3 is filled, so the arm would not route around it. Time budget was
also exhausted by the point this became clear.

## Verdict

**BROKE_AT_LEG_4** in both the primary composed line and its named
fallback. The break is a real, exhausted, positive-controlled wall: from
the crossing landing cell `(18,50)` phase `(0,2)` with box3 filled, only
44 positions are reachable, covering 2 of box0's interior cells (wrong
phase) and none of box1's or box3's remaining interior. This falsifies
composed line #1 in **both** orderings the mission specified, for the
same underlying reason -- the crossing via dot2 (whichever object fills
box3) lands the piece in a pocket that cannot reach dot0's own
north-chain approach.

**LINE_COMPLETE_NO_WIN does not apply** -- the line did not complete;
it broke before box0 or box1 were ever filled. Final config at the break
(both orderings): box3 filled, box0/box1 empty, piece stranded in a
44-cell pocket, dot0 sitting at `(13,44)`/`(13,45)` unreachable from
there.

## What a clean re-run needs

The wall is in the **crossing itself**, not in dot0's chain-kick recipe
(which is unmodified from y11's proven form). The dot2-click crossing
(compound-swept or not) reliably lands the piece at `(18,50)`ish --
measured twice now, from two different pre-crossing states (piece
crossing with box3 filled by dot2 directly, and piece crossing separately
after box3 was already filled by dot1). Since the landing cell is what's
walled off from dot0's own position, the next lever is **where the piece
crosses FROM** (a different approach angle/side to the click), or
**recycling box3's marker after a halo-eject** to reach box1 without ever
needing dot0's north-chain -- both untested in this session's time
budget.

## Anti-goals compliance

No static-map reachability was used for any verdict above -- every
reachability claim is either a real exhaustive BFS with a positive
control, or a directly observed `dot_cells`/`extra4` diff via the
belt-and-braces asserts. No known wall was re-run blind: the leg-4 wall
measured here is a **new** census (different landing cell/phase/fill-state
than any prior session's recorded wall), confirmed independently twice.
No unrouted walk near an object was used -- every routed leg went through
`safe_route` (proactive 8-neighbourhood forbidding) and every press went
through `guarded_step` (reactive object-position assert); both mechanisms
fired zero false negatives and one initially-flagged-then-correctly-
reclassified true positive (the documented compound sweep) across both
scripts. No full-game BFS was run -- every exhaustive BFS was scoped to
board positions from the current live state (15,000-node cap, both
exhausted well under it). Arm 9 is explicitly NOT RUN, not silently
skipped.

## Files

- `ka59_g2_safe_route.py` -- harness fix (`safe_route`/`guarded_step`/
  `safe_walk`/`safe_kick`) + primary composed line (legs 1-8).
- `ka59_g2b_fallback.py` -- copy with legs 3/3b replaced by the named
  fallback (box3 via dot1, cross via direct dot2 click).
- `results/ka59-g2-run.txt` .. `run4.txt` -- primary-script iteration
  history (found + fixed the compound-sweep exemption bug and the
  nearest-position misidentification bug).
- `results/ka59-g2-run5.txt` -- primary script's final, reported run.
- `results/ka59-g2b-run.txt` -- fallback script's run.
