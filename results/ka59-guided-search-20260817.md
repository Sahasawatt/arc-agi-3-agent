# ka59 L2 -- guided search over click/kick orderings (2026-08-17)

Verdict: **INCOMPLETE -- one validated mechanic finding, one composed line reached an
INSTRUMENT wall (not a structural negative) at leg D.** `levels_completed` never left 1.
No WIN. Scripts: `ka59_g1_composed_line.py`. Raw logs: `results/ka59-g1-run.txt` (first
attempt, wide dot2-approach band), `results/ka59-g1-run3.txt` (retried with a
narrower/fallback band -- same outcome). Time budget spent on one composition +
one retry; did not reach systematic enumeration of the rest of the space.

## PRIORITY 1 -- VALIDATED: dot1's marker inherits dot1's own kick geometry

On a throwaway branch (19 actions, discarded, not part of the composed line below):
filled box3 with raw dot1 (click from inside box3 -> box3 filled, marker at (55,40));
ejected it via its halo (click (54,39) -> marker lands at piece's pre-click position,
(41,34)/(42,34) -- dot1's own canonical entry cell, by coincidence of the approach
path); approached the ejected marker from the east and pressed west:

```
PRIORITY 1 RESULT: marker MOVED. before=[(41, 34), (42, 34)] after=[(17, 34), (18, 34)]
dx=-24 (multiple of 3)
```

**(17,34)/(18,34) is the EXACT cell the campaign's "known good legs" already recorded
for the RAW dot1 kicked west from this same entry position.** So dot1's marker, kicked
from the identical starting cell and the identical approach side as the raw dot, lands
on the identical cell -- confirming "markers inherit their origin dot's kick geometry"
for a **second** dot (previously measured only for dot2's marker, per the recon tail).
This closes the load-bearing question the mission flagged, though the composed line
below did not end up needing it (it uses dot1 only in its raw, unkicked form).

## Composed line #1 -- design and where it broke

**Re-derivation before driving anything**: y11 (`ka59_y11.py`, prior campaign) already
*proved* dot0's own north-chain works end-to-end (kick dot0 west -> chain-kick dot0
north across the internal band -> click dot0 from inside box0 -> box0 filled AND piece
delivered to box1's entry phase (1,2) -- straight walk into box1, no search needed).
y11's only cost was spending dot1 (kicked, clicked into box3) purely as the vehicle to
cross RIGHT->LEFT before the chain-kick, then later RECYCLING that same marker out of
box3 into box1 -- which is why y11 ended with box3 EMPTIED (2 of 3 filled, not 3).

The idea driven this session: use **dot2** for that RIGHT->LEFT crossing + box3 fill
instead of dot1, leaving dot1 completely untouched and free for the mission's untested
"return-click fill" (click dot1, still at entry, from inside box1 -> box1 filled AND
piece returns to dot1's RIGHT entry cell in one click). If box2's interior really does
span all nine phases (per the x3 finding already on record), the line would not even
need a mint/ticket step -- just walk into box2 directly after returning RIGHT. Planned
8 legs: A) kick dot0 west, B) kick dot2 west, C) box3+click dot2 (fills box3, crosses
piece LEFT), D) chain-kick dot0 north, E) box0+click dot0 (fills box0, delivers piece
to box1's phase), F) walk into box1, G) click dot1 from inside box1 (fills box1,
returns piece RIGHT -- the novel leg), H) walk into box2 directly.

**Legs A, C (mechanically), E-are not reached; G/H never ran.** The line broke at leg D.

## What actually happened, and why leg D's failure is an INSTRUMENT wall, not a proof

Leg A (kick dot0 west, y11's exact recipe) reproduced cleanly: dot0 landed at
`(19,44)/(19,45)`.

Leg B (kick dot2 west) is where the composition went wrong, silently. The approach BFS
that walks the piece toward "east of dot2, then press west" never actually lines the
piece up on dot2's own row (dot2 sits at y=47/48; the approach settled on y=46, one row
off, and 8 further west-presses along y=46 never touched anything -- confirmed by the
per-press dot_cells diff staying empty for all 8 presses, and by the piece's own x
decreasing by exactly 3 every single press with no interruption, i.e. free walking, not
a kick). A retry with a tight y=[47,48] approach band found **no route at all** (0
nodes), and the fallback ladder (`[47,48] -> [46,49] -> [47,47] -> [48,48]`) landed back
on the same wide `[46,49]` band -- same outcome both runs.

Yet the leg-C click (`CLICK(59, 47)`) *did* find a live colour-5 cell and it *did*
successfully fill box3 (`extra4=[(55,40)]` after the click) -- so dot2 was moved by
something. The only candidate is the **approach walk itself**: leg B's approach phase
presses `v=4` (east) five times to reach the kick-staging cell, and that eastward walk
is the most likely point of incidental contact -- consistent with dot2 ending up
**east** of its own entry position (44/45 -> 59) rather than west of it. This is the
same failure class already on record for this game (`results/ka59-forced-assignment-
20260817.md`: "a recovery/settle action is not neutral -- it can spend a dot's
favourable position") extended to an **approach BFS**, not just a settle press: any walk
whose region brushes a dot's cell can kick it, silently, before the script's own
"kick" phase believes it has started.

**Consequence**: dot2 never crossed to LEFT at all (it flew further into RIGHT
territory). The leg-C click therefore delivered the piece to `(60,48)` -- still inside
a small RIGHT-side pocket, not across the moat. Leg D's exhaustive BFS from there found
exactly **69 reachable positions, none of them in box0, box1, or box3's interior** --
a real, exhausted, positive-controlled-pattern census, but of the **wrong state**: the
piece was never on the LEFT side dot0's chain-kick approach needed. This is not a
measurement that the dot0-north-chain-after-a-dot2-crossing is unreachable; it is a
measurement that **the dot2 crossing never happened**, contaminating leg D exactly the
way an unconstrained settle contaminated `ka59_s1_forced.py`'s BROKE_AT_LEG_3 reading
before the clean-settle fix. Per the mission's own anti-goal ("no re-running known walls
without a new reason") this is *not* a wall to log as closed -- it is an untested arm.

## Frontier -- what a clean re-run needs

The fix is the same shape as the clean-settle fix that closed the last session's
contamination: **before any BFS approach walk near a dot, verify via deepcopy that the
approach path does not disturb that dot's (or any other dot's) live cells**, the same
way `step_log`'s settle logic now trials all 4 directions and picks the one that
resolves cleanly. y11's own dot1-approach region (`region(48, 52, 33, 35)`, tight to
D1's exact y-span) apparently avoided this failure mode by being narrow and aligned;
my dot2 region attempts (wide `[46,49]`, tight-but-unreachable `[47,48]`) were not
equivalent. A geometrically tighter, verified-clean approach to dot2's actual row
(`y=47` or `y=48` exactly, not a padded band) is the next thing to try -- not yet run.

If that clean crossing works, legs D onward (chain-kick dot0 north, box0 fill, walk to
box1) are expected to reproduce y11's proven behaviour unchanged, since dot0's own
kicked position and chain-kick recipe are untouched by which dot performs the crossing.
Legs G (return-click fill of dot1 into box1) and H (direct walk to box2) remain
completely UNRUN -- no arm was exercised for either; per the mission's anti-goals,
that is reported as NOT RUN, not as a wall.

## Anti-goals compliance

No static-map reachability was used for any verdict above (all reachability claims come
from either a real exhaustive BFS with a positive control, or a directly observed
`dot_cells`/`extra4` diff). No known wall was re-run blind -- leg D's negative is
reported as instrument-contaminated, not banked as a new wall. No full-game BFS was
run. Legs G and H are explicitly marked NOT RUN.

## Files

- `ka59_g1_composed_line.py` -- the guided-search script (priority-1 check + composed
  line #1, both described above).
- `results/ka59-g1-run.txt`, `results/ka59-g1-run3.txt` -- raw logs (first wide-band
  attempt and the retry with a fallback ladder; both hit the same leg-B contamination).
