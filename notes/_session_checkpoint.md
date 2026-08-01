# Session checkpoint — 2026-07-30, cutting level 6

Pushed so far: `b4dc827` on master (level 6 cleared at 1187, plus the level-7 first look).

## Level-6 cost work, measured in order

| change | ls20 | note |
|---|---|---|
| baseline (pushed) | 6/7 [.., 1187] **23.006%** | stage1 483 of 1187, 12 deaths |
| **#1 generalized learn mode** (LANDED, uncommitted) | 6/7 [.., 292, **844**] **23.528%** | route_moving(learn=True): walk known edges to press an UNKNOWN one; the old route_learn could only teach the edge out of the current value |
| #2 moving-fuel fallback | **5/7 22.446%** REVERTED | replacing the square-changer rungs with "refuel instead" LOSES level 6; probe rung took the freed rounds (40 → 329) and bought nothing. Those trips walk the corridors, which is where presses happen. Written into CLAUDE.md |
| #3 clear mover histories on death | measuring | deaths reset the patrollers, so pre/post entries contradict at the same phase and every period is lost (verified: period loss at the exact action a life ended). Edges kept — a starve does not restart the tracker |

`route_learn` is now dead code (superseded by learn mode) — remove it if #3 lands and the
suite stays green.

## Where the score is

per-level now: 91.5, 115, 54.4, 22.3, 11.0 (l5 292), 5.2 (l6 844) — cap 75.0 at 6 of 7.
l6 at 400 → game 27.4% · 300 → 31.2% · 221 (1.15x) → 38.6%. Level 5 at 150 would add ~5.
So both deep levels are worth more than level 7 until they are cheap.

## Next

1. Read #3's number. If ls20 < 844 and nothing else moves: keep, then re-sweep
   cd82/m0r0/ar25 before committing.
2. Then the remaining level-6 tuition: 3 gameovers + 6 starves per run, each restarting
   the choreography. Ideas not yet tried: plan the door trip only from a full tank
   (MARGIN-style slack for a moving trip), and let a trip cross an already-`opened` door
   without re-checking (it does now, but `opened` clears on death — the panel resets
   anyway, so that is honest).
3. Level 7 diagnosis (results/l7-first-look.md): no plates, no patrollers, a colour-8
   HUD counter and a big colour-12 glyph — the lock mechanism is unknown.
