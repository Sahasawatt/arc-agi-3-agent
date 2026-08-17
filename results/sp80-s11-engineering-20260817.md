# sp80_s11.py — multi_match resolver + checkpointing, engineering notes (2026-08-17)

## Task

Two blockers stood between the sp80_s10.py L3 search (72,684 expanded, 192,247 states,
frontier 118,643, 8-14h realistic total) and a long overnight run being worth anything:

1. `transfer_multi_match` (3,730 events at 72k expanded, **2,254 with the driver id NOT
   among the matches**) resolved by an unproven tie-break heuristic. Any exhaustion
   verdict from the existing search is void until this is fixed.
2. No checkpointing — s9/s10 restart from the L3 root every invocation.

`sp80_s11.py` (copy of s9/s10's transition logic as its base) fixes both.

## Multi-match: why it happens, and why position alone can't resolve it

Instrumented a real search (throwaway script, output kept at
`results/sp80-s11-dbg1.txt`, script itself deleted per the task's no-test-file
naming/ scope rule) to capture an actual multi-match event instead of guessing. First
one found, at BFS depth 4:

```
pos (stored): {0: (8, 20), 1: (8, 32), 2: (40, 28), 3: (40, 28)}
dp (new driver pos): (40, 28)
matches: [2, 3]
```

Ids 2 and 3 are BOTH stored at `(40, 28)` in the same state — not a bug in the
dict, a real board fact: the driven body (id 2, root position `(36, 40)`) walked onto
the exact cell occupied by the stationary id 3 (root position `(40, 28)`) — this is
the "grab block2 inside castle0's zone" mechanic the recon already named. **Position
cannot disambiguate this**: whichever of {2, 3} is "really" driving now, the OTHER one
is standing on that same cell and therefore fully occluded (colour-9 draws on top),
so a check of "is the other candidate's position still independently visible as its
own colour-8 blob" fails for BOTH candidates — that check is necessary but was proven
insufficient with a live measurement (first cut of the resolver: 26/26 multi-match
events in a 60s run all fell through to "0 survivors", see below).

## The fix: SIZE is a second, independent invariant, and it separates the tie

Each of the four bodies is a fixed physical rectangle. Colour (8 vs 9) is a role
flag that flips when control transfers; **width/height do not change**. Measured at
the L3 root (`swap.blocks`, colours 8/9 only):

| id | root pos | size (w×h) | cells |
|---|---|---|---|
| 0 | (8,20)  | 16×4 | 64 |
| 1 | (8,32)  | 24×4 | 96 |
| 2 | (36,40) | 24×4 | 96 (driver at root) |
| 3 | (40,28) | 20×4 | 80 |

In the captured collision, the freshly-detected new-driver blob had size **24×4 =
96 cells** — matching id 2's known size, not id 3's (80). Size resolves it exactly,
with no dependence on whether the OTHER candidate is currently occluded (it doesn't
need to see anyone else — it only reads the one blob that is guaranteed unoccluded,
the current driver's own).

**Resolver, in `resolve_multi_match()` (`sp80_s11.py`), tried in order:**

1. **SIZE** — keep candidates whose *known* (bootstrap-measured, never re-read
   because it is a game-lifetime constant) size equals the freshly-detected new-driver
   blob's size. If exactly one survives, done.
2. **FRAME RE-READ** — fallback for a size tie (two candidates share a known size):
   re-read the current frame's colour-8 blobs; keep candidates whose *other three*
   stored positions are all independently visible right now (non-driven bodies
   provably never move, so if a candidate is correct, nobody else can have vanished).
   Necessary but not sufficient alone, per the measurement above — it's the second
   pass, not the first.
3. **Neither narrows to 1** → the state is genuinely ambiguous from this one frame.
   **Fork**: push one frontier branch per surviving candidate (or, if size AND frame
   both leave 0 survivors — a true position collision the re-read cannot break — fork
   all original raw matches). No guess is ever made; `full_key()` already
   disambiguates each forked branch since it includes `driver_id`, so no key collision.

Cost: `resolve_multi_match` only runs on multi-match expansions — measured at 5.1%
of expanded nodes in the prior 72k-node run, so the O(board-pixels) frame re-read
(tier 2) is affordable, and tier 1 (size compare) is O(1).

## Before/after measurement

First cut of the resolver used ONLY the frame-re-read check (tier 2 above, no size
tier). A 60s fresh run + 60s resumed run (120s total, 1,363 expanded) hit 26
multi-match events — **all 26 resolved to 0 survivors and were force-forked.**
Every single one was the position-collision case above; tier 2 alone never resolves
it. Investigated with the throwaway debug script (`sp80-s11-dbg1.txt`), found the
size differs, added tier 1. Re-ran the identical smoke sequence:

- Fresh 60s: 2 multi-match events, **2/2 resolved_exact, 0 forked**.
- Resumed 60s: 24 more multi-match events, **24/24 resolved_exact, 0 forked**.
- Extended 200s run (resumed again): still climbing multi_match count, **0 forked
  through at least the first ~2,700 expansions** (see smoke ladder below — this run
  was still in flight when this section was written; final counts are appended below
  once it completes).

So in every case observed so far, size alone breaks the tie. The frame-re-read tier
and the fork path both exist and are exercised by the code (unit-testable via the
resolver function directly), but have not yet been observed to fire on a real
multi-match on this game — meaning either the size tier is sufficient in practice, or
a genuine size-tie / true-ambiguity case is rarer than the ~5% multi-match rate and
just hasn't come up in the smoke-scale runs. **This is flagged, not hidden**: if a
future long run reports `forked_survivors` or `forked_forced` > 0, that is the
fallback tiers doing real work, not a bug.

## Positive control

`sp80_s11.py --control` replays `swap.L2_LINE` (the known 7-action L2 win) through
the exact same `bodies()` / `driver_blob()` / `transfer_targets()` functions the BFS
uses (not a separate/simplified path). Output (`results/sp80-s11-control.txt`):

```
CONTROL: L1 reached via RECIPE1
CONTROL: L2 entry bodies={0: (8, 16), 1: (20, 36), 2: (28, 24)} sizes={0: (12, 4), 1: (20, 4), 2: (12, 4)} driver=1
CONTROL: step 0 (4) plain move, driver 1 -> (24, 36)
CONTROL: step 1 (4) plain move, driver 1 -> (28, 36)
CONTROL: step 2 (('click', 13, 17, (13, 17, 13, 17))) transfer, reason=None candidates=[0]
CONTROL: step 3 (4) plain move, driver 0 -> (12, 16)
CONTROL: step 4 (4) plain move, driver 0 -> (16, 16)
CONTROL: step 5 (4) plain move, driver 0 -> (20, 16)
CONTROL: step 6 (5) -> levels_completed=2, WIN
CONTROL PASS
```

Note L2's own 3-body state has ids 0 and 2 sharing size (12,4) — a real size tie —
but the one transfer on this line (step 2, the click) has `reason=None`, meaning `dp`
matched exactly one stored position with no ambiguity at all, so the tiered resolver
was not exercised by this particular known-win line beyond the trivial single-match
path. Exit code 0.

## Checkpointing

Pickled to `results/sp80_s11_ckpt.pkl` every 2,000 expansions (matches
`CURVE_EVERY`, same cadence as the existing growth-curve print) and once more in a
`finally` block on any exit (budget, exhaustion, win, or exception) — atomic write
(`.tmp` + `os.replace`). Contents: the path-only frontier (paths/ammo/pos/driver_id,
no envs — same design as s9/s10, ~hundreds of bytes/node), the `seen` key set, and
every counter needed to resume the growth curve and the multi-match breakdown without
re-deriving them. `--fresh` ignores an existing checkpoint and starts over;
omitting it resumes if the file is present.

## Smoke ladder results

**(a) fresh, 60s budget:**
```
FRESH START
== transfer_multi_match resolution breakdown ==
count=2 resolved_exact=2 forked_survivors(2+)=0 forked_forced(0 survivors)=0 total_extra_branches_forked=0
FINAL expanded=705 states=2860 frontier=2155 multi_match=2 forked=0 exhausted=False win=False
```
Checkpoint file confirmed present (`results/sp80_s11_ckpt.pkl`, 223,914 bytes).

**(b) resume, no --fresh, 60s budget:**
```
RESUMED expanded=705 states=2860 frontier=2155 multi_match=2 forked=0
== transfer_multi_match resolution breakdown ==
count=24 resolved_exact=24 forked_survivors(2+)=0 forked_forced(0 survivors)=0 total_extra_branches_forked=0
FINAL expanded=1403 states=5307 frontier=3904 multi_match=24 forked=0 exhausted=False win=False
```
`expanded` continued from 705 (not reset), confirming resume works.

**(c) extended 200s run (resumed again), cross-validating the growth curve:**
```
RESUMED expanded=1403 states=5307 frontier=3904 multi_match=24 forked=0
  CURVE expanded=2000 states=7355 frontier=5355 d_states/2000=7354 d_frontier/2000=5354 anomalies=28 multi_match=28 forked=0 avg_replay_ms/node=13.45 t=52s CHECKPOINTED
HEARTBEAT expanded=2088 states=7653 frontier=5565 rate=34.78/s multi_match=29 forked=0 t=60s
HEARTBEAT expanded=2741 states=9755 frontier=7014 rate=22.83/s multi_match=32 forked=0 t=120s
```
At `expanded=2000`, states=7,355 and frontier=5,355 — **byte-identical to the
historical env-frontier run's own numbers at the same expanded count**
(`7,355/5,355` in the 2026-08-16 breadth-recon table), which cross-validates that
this round's changes (resolver rewrite) did not alter which states are reached,
exactly the same cross-validation the s9 round did for its own path-frontier vs
env-frontier switch. Heartbeat fires on schedule (60s, 120s, 180s).

Completed (200s budget, exit 0):
```
RESUMED expanded=1403 states=5307 frontier=3904 multi_match=24 forked=0
  CURVE expanded=2000 states=7355 frontier=5355 ... t=52s CHECKPOINTED
HEARTBEAT expanded=2088 ... t=60s
HEARTBEAT expanded=2741 ... t=120s
HEARTBEAT expanded=3386 ... t=180s
== transfer_multi_match resolution breakdown ==
count=55 resolved_exact=55 forked_survivors(2+)=0 forked_forced(0 survivors)=0 total_extra_branches_forked=0
FINAL expanded=3624 states=12375 frontier=8751 multi_match=55 forked=0 exhausted=False win=False
```
**55/55 multi-match events resolved exactly by the size tier alone across four
chained invocations (fresh + 3 resumes, 1,403 + 2,221 = 3,624 total expanded).
Zero forks fired at this scale.**

**(control) positive control:** PASS, exit 0 (see above).

## Command for the main thread's long run

```bash
PYTHONUTF8=1 ./.venv/Scripts/python.exe sp80_s11.py --budget-seconds 3300 --fresh > results/sp80-s11-run1.txt 2>&1
```
then, chained, drop `--fresh` for every subsequent invocation to resume from
`results/sp80_s11_ckpt.pkl`:
```bash
PYTHONUTF8=1 ./.venv/Scripts/python.exe sp80_s11.py --budget-seconds 3300 >> results/sp80-s11-run1.txt 2>&1
```
Repeat until `exhausted=True` or `win=True` in the printed `FINAL` line, or until
the recon's priced 8-14h estimate has been spent. Each invocation is independent and
safe to interrupt (checkpoint is current as of its last 2,000-expansion boundary or
its own exit, whichever is more recent).

## What is NOT claimed

- The frame-re-read fallback tier and the fork path are implemented, reachable by
  code inspection (`resolve_multi_match()`'s size-tie and 0-survivor branches), but
  were **never observed firing** across the full smoke ladder — 55/55 multi-match
  events over 3,624 expanded resolved on the size tier alone, `forked=0` throughout.
  This is only confirmed at smoke scale (3,624 of the ~300,000-500,000 expected total
  expansions, ~1%). It remains possible that a size-tie or genuine collision (two
  bodies sharing both position and size, e.g. ids 1 and 2 which are both 24×4 at
  root) appears later in the search and exercises the fallback tiers for the first
  time. If the long run reports `forked_survivors` or `forked_forced` > 0, that is
  the fallback doing its job, not a bug — and worth flagging to whoever reads the
  final report, since it is new evidence about the game, not an artifact.
- This round did not re-verify `transfer_no_match` or `driver_blob_count` at scale
  (s9/s10's 72k-node run already confirmed 0 `transfer_no_match` and 0
  `driver_blob_count` with the FIRE fix in place, and this round's transition code
  for those two anomaly classes is otherwise unchanged) — only `transfer_multi_match`
  was in scope for this task and is what the resolver rewrite targets.
