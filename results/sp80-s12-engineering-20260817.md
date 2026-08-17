# sp80 s12 engineering — s11's BFS + resolver retargeted at L4 (2026-08-17)

`sp80_s12.py` is `sp80_s11.py` mechanically adapted: root construction extended one level
(RECIPE1 + `swap.L2_LINE` + `swap.L3_LINE`), checkpoint path bumped to
`results/sp80_s12_ckpt.pkl`, positive control replays `L3_LINE` instead of `L2_LINE`, win
threshold `levels_completed > 3` instead of `> 2`. The resolver (`resolve_multi_match` /
`transfer_targets`, size tier → frame re-read → fork) is **byte-for-byte unchanged** — see
"L4 body model" below for why that held.

## L4 entry body model — re-derived, not assumed

Probed directly (fresh env, RECIPE1 → L2_LINE → L3_LINE, `assert levels_completed == 3`,
then read `bodies()` off the resulting frame):

```
bodies: [(9, 17, 17, 15, 3), (8, 38, 17, 15, 3), (8, 44, 32, 12, 3),
         (8, 38, 41, 12, 3), (8, 20, 29, 9, 3), (8, 8, 29, 9, 3)]
count: 6
driver (colour 9) count: 1
```

**6 tracked bodies, not L3's 4.** Sizes come in three tiers, each tied exactly twice:

| size (w,h) | bodies |
|---|---|
| (15, 3) | driver (17,17) · (38,17) |
| (12, 3) | (44,32) · (38,41) |
| (9, 3) | (20,29) · (8,29) |

This is **worse** for the size-tier resolver than L3 was: L3's four bodies were 96/96/80/64
cells — one tied pair among four, so size alone resolved most collisions outright. At L4
**every single size is duplicated** (each tier has exactly 2 members), so whenever a
multi-match's two candidates happen to be the tied pair sharing a size, `size_hits` comes
back with 2 members and the resolver falls straight through to the frame re-read / fork
path instead of resolving on size alone. This is a **workload shift onto the fallback
tiers**, not a case the two invariants can't handle — the FRAME re-read (do the *other*
stored bodies still show as their own colour-8 rectangle) is still a clean, correctness-
preserving test regardless of how many bodies share a size, and FORK is still the correct
answer when both invariants leave more than one survivor. No resolver-logic change was
required or made; `resolve_multi_match`/`transfer_targets` are copied unmodified from s11.

## What changed vs s11 (exhaustive list)

- `CKPT_PATH` → `results/sp80_s12_ckpt.pkl`.
- `make_root()`: plays `RECIPE1` + `swap.L2_LINE` + `swap.L3_LINE` (factored into a shared
  `_play_click_line` helper used by both `make_root` and `positive_control`), asserts
  `levels_completed == 3` instead of `== 2`.
- `positive_control()`: replays `swap.L3_LINE` from the L3 entry (reached via RECIPE1 +
  L2_LINE) through the same resolver, asserting `levels_completed >= 3` for the win instead
  of `>= 2`. Everything else (per-step transfer logging, fork warnings, the final
  "exhausted without win" assert) is identical in shape.
- `run_bfs()`: win condition `levels_completed > 3` instead of `> 2` (both the arrow-move
  and fire branches); log line says "L4 root" instead of "L3 root". Frontier structure,
  checkpointing cadence (every 2,000 expansions, atomic pickle), heartbeat (60s), budget
  handling, and the FINAL/DONE lines are untouched.
- Docstring updated with the L4 body-model finding above; no other file touched.

Everything else — `bodies()`, `driver_blob()`, `full_key()`, `resolve_multi_match()`,
`transfer_targets()`, `save_checkpoint()`/`load_checkpoint()`, the frontier/replay loop, the
growth-curve table, the multi-match breakdown printout — is copied verbatim.

## Smoke ladder

### (a) `--control` — PASS

```
CONTROL: L1 reached via RECIPE1
CONTROL: L2 reached via L2_LINE
CONTROL: L3 entry bodies={0: (8, 20), 1: (8, 32), 2: (36, 40), 3: (40, 28)} sizes={0: (16, 4), 1: (24, 4), 2: (24, 4), 3: (20, 4)} driver=2
CONTROL: step 0 (4) plain move, driver 2 -> (40, 40)
CONTROL: step 1 (('click', 8, 20, (8, 20, 8, 20))) transfer, reason=None candidates=[0]
CONTROL: step 2 (4) plain move, driver 0 -> (12, 20)
CONTROL: step 3 (('click', 8, 32, (8, 32, 8, 32))) transfer, reason=None candidates=[1]
CONTROL: step 4 (3) plain move, driver 1 -> (4, 32)
CONTROL: step 5 (3) plain move, driver 1 -> (0, 32)
CONTROL: step 6 (('click', 40, 28, (40, 28, 40, 28))) transfer, reason=None candidates=[3]
CONTROL: step 7 (3) plain move, driver 3 -> (36, 28)
CONTROL: step 8 (3) plain move, driver 3 -> (32, 28)
CONTROL: step 9 (5) -> levels_completed=3, WIN
CONTROL PASS
```

Exit code 0. Confirms the resolver replays the known L3 win cleanly (all three transfers
`reason=None`, single-candidate — the L3 board's own bodies don't collide on this
particular line) before the BFS is ever trusted on the new L4 root.

### (b) `--budget-seconds 60 --fresh` — checkpoint appears, FINAL prints, expanded > 0

```
L4 root: 6 tracked bodies: [(9, 17, 17, 15, 3), (8, 38, 17, 15, 3), (8, 44, 32, 12, 3), (8, 38, 41, 12, 3), (8, 20, 29, 9, 3), (8, 8, 29, 9, 3)]
root pos0: {0: (8, 29), 1: (17, 17), 2: (20, 29), 3: (38, 17), 4: (38, 41), 5: (44, 32)} sizes: {0: (9, 3), 1: (15, 3), 2: (9, 3), 3: (15, 3), 4: (12, 3), 5: (12, 3)} driver0: 1
FRESH START

== throughput (this invocation) ==
expanded_this_run=541 elapsed=60s replay_time_total=7s replay_share=12.0%

== state-space size ==
states visited: 2350
expanded=541 anomalies=1091 anomaly_reasons={'driver_blob_count': 1091, 'transfer_no_match': 0, 'transfer_multi_match': 0} exhausted=False t=60s

== per-driver-identity fire coverage ==
ids ever seen as driver: [1, 3, 4, 5] (root driver id = 1)
fire attempts tabulated by who-was-driving: {0: 0, 1: 135, 2: 0, 3: 136, 4: 136, 5: 134}

== transfer_multi_match resolution breakdown ==
count=0 resolved_exact=0 forked_survivors(2+)=0 forked_forced(0 survivors)=0 total_extra_branches_forked=0

NO WIN: t=60s exhausted=False

FINAL expanded=541 states=2350 frontier=1809 multi_match=0 forked=0 exhausted=False win=False
DONE
```

`results/sp80_s12_ckpt.pkl` confirmed on disk after the run (222.0K — written by the
`finally: checkpoint_now()` path since 541 expansions never crossed the 2,000-expansion
CURVE_EVERY checkpoint trigger). No `transfer_multi_match` events yet at this scale (0 of
541 expansions) — unlike L3, which hit its first multi-match early; expected to appear as
expansion count grows, since it's gated on the driver landing exactly on another body's
stored position, not on expansion count alone. `driver_blob_count` anomalies (1,091) are
the "not exactly one colour-9 blob this frame" escape hatch, unchanged mechanism from s11 —
higher raw count here is consistent with more bodies on the board giving more chances for a
transient multi/zero-blob frame, not a resolver defect (these expansions are simply
dropped, same as in s11).

### (c) rerun without `--fresh` — RESUMED, expanded continues

```
L4 root: 6 tracked bodies: [(9, 17, 17, 15, 3), (8, 38, 17, 15, 3), (8, 44, 32, 12, 3), (8, 38, 41, 12, 3), (8, 20, 29, 9, 3), (8, 8, 29, 9, 3)]
root pos0: {0: (8, 29), 1: (17, 17), 2: (20, 29), 3: (38, 17), 4: (38, 41), 5: (44, 32)} sizes: {0: (9, 3), 1: (15, 3), 2: (9, 3), 3: (15, 3), 4: (12, 3), 5: (12, 3)} driver0: 1
RESUMED expanded=541 states=2350 frontier=1809 multi_match=0 forked=0

== throughput (this invocation) ==
expanded_this_run=803 elapsed=30s replay_time_total=12s replay_share=38.6%

== state-space size ==
states visited: 3329
expanded=803 anomalies=1620 anomaly_reasons={'driver_blob_count': 1620, 'transfer_no_match': 0, 'transfer_multi_match': 0} exhausted=False t=30s

== per-driver-identity fire coverage ==
ids ever seen as driver: [1, 3, 4, 5] (root driver id = 1)
fire attempts tabulated by who-was-driving: {0: 0, 1: 200, 2: 0, 3: 202, 4: 200, 5: 200}

FINAL expanded=803 states=3329 frontier=2526 multi_match=0 forked=0 exhausted=False win=False
DONE
```

`RESUMED expanded=541 ... frontier=1809` matches run (b)'s FINAL exactly, then `expanded`
climbs to 803 (541 + 262 more in this 30s slice) — confirms the checkpoint round-trips and
the search continues from where it left off rather than restarting.

All three ladder rungs pass; the harness is verified live on the L4 root before any long
run is launched.

## Open observation (not a code change)

Ids 0 and 2 (the (9,3)-size pair at (8,29)/(20,29)) never appear as driver in either smoke
run (`ids ever seen as driver: [1, 3, 4, 5]`) and never fire. At only ~800 expansions this
is far too small a sample to read as structural — L3's own driver-id coverage only evened
out over tens of thousands of expansions — flagging it as UNVERIFIED rather than concluding
anything.

## Chain command (not run — main thread owns the long run)

Same shape as s11's launch (12 × 3300s cap chained, stop early on `exhausted=True` or
`win=True` in the FINAL line):

```bash
PYTHONUTF8=1 ./.venv/Scripts/python.exe sp80_s12.py --budget-seconds 3300 --fresh \
  > results/sp80-s12-run1.txt 2>&1
# then, repeated (resume — no --fresh — until FINAL shows exhausted=True or win=True):
PYTHONUTF8=1 ./.venv/Scripts/python.exe sp80_s12.py --budget-seconds 3300 \
  >> results/sp80-s12-run1.txt 2>&1
```

Watch `multi_match`/`forked` in each FINAL/HEARTBEAT line — per the body-model finding
above, `forked` firing here is expected to be more likely than at L3 (1 fork in 13,058
multi-match events there), since every size tier is tied rather than just one pair.
