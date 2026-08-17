# sp80 s13 engineering — a recovering driver reader for L4 (2026-08-17)

`sp80_s13.py` is `sp80_s12.py` with one addition: `driver_blob_recover()`, called only when
`driver_blob()` finds colour-9 blob count != 1, so the three sites that used to `continue`
(silently dropping the child) now attempt a measured recovery first. Root construction,
`resolve_multi_match`/`transfer_targets`, checkpoint shape, budget handling, heartbeat and the
FINAL/DONE lines are otherwise byte-for-byte s12. Nothing is ever silently dropped: every
recovery attempt increments its own counter (`driver_recovered_size` / `driver_recovered_split`
/ `driver_forked` / `driver_dropped_hard`), reported in every HEARTBEAT/CURVE line and the FINAL
line.

## Why s12 was stopped

`driver_blob_count` anomalies fired 56,477 times over ~43k expansions of the long run
(`results/sp80-s12-run1.txt`) — a counter that stayed ZERO across L3's entire 229,506-expansion
run. All three call sites in s12 handled `dp is None` with `continue`: the child was dropped,
never entering `seen`, never entering the frontier. A search dropping >1 edge per node explores
a subgraph; any negative it reports is void.

## The measured anomaly taxonomy

`--diagnose` drives independent short random trajectories from the L4 root (fresh
`copy.deepcopy` of the root env per trial, length 1-35, random mix of moves/fires/clicks) and
classifies every `driver_blob()` count != 1 event through `driver_blob_recover()`. Three
independent samples, different seeds and depths:

| sample | seed | max_len | trials | anomalies found | count histogram | tag histogram |
|---|---|---|---|---|---|---|
| 1 | 0 | 12 | 60 | 20 | `{2: 20}` | `{'fork': 20}` |
| 2 | 42 | 20 | 48 | 60 | `{2: 60}` | `{'fork': 60}` |
| 3 | 777 | 35 | 49 | 40 | `{2: 40}` | `{'fork': 40}` |

**120/120 anomalies, across all three samples, are the identical event**, reproduced and
confirmed by direct inspection (not inferred from the counts alone):

```
$ click (8,29) from the L4 root (driver was body 1, the (15,3)-tier body at (17,17)):
before: [(9,17,17,15,3), (8,38,17,15,3), (8,44,32,12,3), (8,38,41,12,3), (8,20,29,9,3), (8,8,29,9,3)]
after:  [(8,38,17,15,3), (8,17,17,15,3), (8,44,32,12,3), (8,38,41,12,3), (9,20,29,9,3), (9,8,29,9,3)]
```

Clicking body 0 (the (9,3)-tier body at (8,29)) correctly demotes the old driver (17,17 -> colour
8) but **promotes BOTH members of the (9,3) size-tier pair** — (8,29) *and* (20,29) — to colour 9
simultaneously. Control clicks on every other body confirm this is specific to this one pair, not
a general transfer artifact:

```
click (38,41) [12,3-tier body4] -> colour9 count=1 (clean)
click (44,32) [12,3-tier body5] -> colour9 count=1 (clean)
click (38,17) [15,3-tier body3] -> colour9 count=1 (clean)
```

And it is not gated on *click* specifically — a FIRE from an unrelated position lands on the same
pair:

```
seq=[2,4,3,4,2,4,5] (six moves walking the driver 17,17 -> 23,23, then FIRE)
step 6 action 5 -> colour9 blobs: [(20,29,9,3), (8,29,9,3)]   (driver was NOT at either position)
```

**Classification against the spec's three hypotheses:**

- **SPLIT** (2+ blobs whose union bbox ~= driver size, occlusion cutting one blob): refuted. The
  two blobs are never adjacent — x-spans `[8,17)` and `[20,29)`, a 3-cell gap — so their union
  bbox is `(21,3)`, which never equals any of the three known driver sizes `(15,3)/(12,3)/(9,3)`.
  Not observed once in 120 samples.
- **MERGED** ("one blob larger than driver size"): refuted in the literal sense (there is no
  single larger blob — `swap.blocks()` only emits solid rectangles, and a genuinely non-rectangular
  covered region is dropped before `driver_blob()` ever sees it, not enlarged). What actually
  happens is a **real merge at the body level**: the fixed (9,3)-size pair (bodies at root
  positions (8,29) and (20,29)) *both* wear colour 9 after any control-transfer event (click or
  fire) that is not aimed at one of the other four bodies. This reads as a genuine in-game
  twin/paired-body mechanic for this one specific pair, not an occlusion artifact — measured, not
  guessed; the two other size tiers ((15,3), (12,3)) never exhibit it.
- **MISSING** (0 blobs): **never observed** — 0 of 120 anomalies had count 0. `swap.blocks()`'s
  solidity requirement (`len(blob) == w*h`) means a genuinely occluded, non-rectangular colour-9
  remainder is possible in principle, but no trajectory sampled (three seeds, depths to 35, 149
  total trials) ever produced one.

`recover_tag` was `'fork'` in all 120 cases (both candidate blobs pass through: neither matches
the *other* tiers' known size, so tier (a) exact-size never fires when the true driver is one of
the other four bodies; and when the driver itself is body 0 or 2, BOTH blobs match its known size,
so `len(exact) == 1` still fails and falls through the same path). `driver_dropped_hard` and
`driver_recovered_split` were 0 in every sample.

## Recovery design (`driver_blob_recover`)

Tiers, in order, mapped to the taxonomy above:

1. **(a) exact-size match** — filter candidate colour-9 blobs to those matching the driver's
   known `(w,h)` (fixed per body id, from the root `sizes` dict); if exactly one survives, use it.
   Never fired in the diagnostic sample (both blobs share the anomalous pair's size whenever the
   pair is itself involved), but it is the correctness-preserving first check and costs nothing
   when it doesn't fire.
2. **(b) SPLIT: union-bbox match** — if the exact-size tier leaves >1 or 0, compute the union bbox
   of ALL candidate blobs; if it equals the driver's known size, treat it as one occluded/split
   body and recover at the union's top-left corner. Never fired in the sample (the twin pair's
   union bbox never matches any known driver size), but this is the direct, measured answer to a
   true SPLIT should one occur deeper in the search than 149 trials reached.
3. **(c) MISSING (0 blobs)** — `dropped_hard` immediately. No occlusion-shrink recovery was
   implemented because none was measured: `swap.blocks()` drops a non-rectangular colour-9 remnant
   before `driver_blob_recover()` ever receives it, so there is no partial-blob signal in `blobs`
   to recover from at this layer. This is the honest answer per the anti-goals ("no silent
   drops" does not mean "never a drop" — it means every drop is counted and attributed, which
   `dropped_hard` does).
4. **(d) genuinely ambiguous, <=3 candidates -> FORK** — one branch per candidate position (own
   blob size, not a forced size). This is the tier that fires for the measured twin-pair merge:
   both `(8,29)` and `(20,29)` are added to the frontier as separate children with the same
   `driver_id`, letting the search's own dedup (`seen`) and eventual transfer/size-tier resolution
   downstream sort out which one is real, exactly like s11/s12's existing multi-match fork
   philosophy for `transfer_targets`.
5. **(e) >3 candidates -> dropped_hard**, bounded so a pathological frame can never explode the
   frontier. Never fired in the sample (max observed count was 2).

At the fire/click call sites, each recovered candidate `(pos, size)` is fed through the *existing,
unmodified* `transfer_targets()` (per spec: no resolver-logic change beyond the driver reader), so
size-tier/frame-re-read disambiguation still applies per candidate before it becomes a frontier
entry.

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

Exit code 0. The known L3 win line never touches the recovering reader (as expected — L3's own
`driver_blob_count` counter was zero across its whole run), confirming s13 has not perturbed the
already-proven resolver path.

### (b) `--diagnose` — see taxonomy above

Full raw output: `results/sp80-s13-diagnose.txt` (sample 1, seed 0, 20 anomalies). Samples 2/3
(seeds 42, 777) reproduced with the same 100%-fork, 0-split, 0-missing shape and are summarized
in the taxonomy table above.

### (c) 120s fresh run — driver_dropped_hard=0, recovery counters positive

```
L4 root: 6 tracked bodies: [(9, 17, 17, 15, 3), (8, 38, 17, 15, 3), (8, 44, 32, 12, 3), (8, 38, 41, 12, 3), (8, 20, 29, 9, 3), (8, 8, 29, 9, 3)]
root pos0: {0: (8, 29), 1: (17, 17), 2: (20, 29), 3: (38, 17), 4: (38, 41), 5: (44, 32)} sizes: {0: (9, 3), 1: (15, 3), 2: (9, 3), 3: (15, 3), 4: (12, 3), 5: (12, 3)} driver0: 1
FRESH START
HEARTBEAT expanded=495 states=2823 frontier=2328 rate=8.24/s multi_match=2 forked=2 recovered_size=0 recovered_split=0 driver_forked=1494 driver_dropped_hard=0 t=60s

== state-space size ==
states visited: 5639
expanded=1000 anomalies=3535 anomaly_reasons={'driver_blob_count': 3049, 'transfer_no_match': 482, 'transfer_multi_match': 4} exhausted=False t=120s

== per-driver-identity fire coverage ==
ids ever seen as driver: [0, 1, 2, 3, 4, 5] (root driver id = 1)

== driver-reader recovery breakdown ==
driver_recovered_size=0 driver_recovered_split=0 driver_forked=3049 driver_dropped_hard=0

FINAL expanded=1000 states=5639 frontier=4639 multi_match=4 forked=4 exhausted=False win=False driver_recovered_size=0 driver_recovered_split=0 driver_forked=3049 driver_dropped_hard=0
DONE
```

`driver_forked` (3,049) equals `anomaly_reasons['driver_blob_count']` (3,049) exactly:
**every single driver_blob_count anomaly in this run was recovered, zero dropped_hard.** This
matches the diagnostic taxonomy — production-scale confirmation, not just the small sample.

Also notable: `ids ever seen as driver: [0, 1, 2, 3, 4, 5]` — **all six**, including ids 0 and 2
(the twin (9,3) pair), which s12's smoke run flagged as an open, UNVERIFIED question ("ids 0/2
never drove in 803 expansions"). s13 answers it structurally: 0 and 2 never drove in s12 because
every path leading to them was the exact anomaly s12 dropped. Full raw output:
`results/sp80-s13-smoke-fresh.txt`.

### (d) resume — PASS

```
RESUMED expanded=1000 states=5639 frontier=4639 multi_match=4 forked=4
...
FINAL expanded=1244 states=6791 frontier=5547 ... driver_forked=3743 driver_dropped_hard=0
DONE
```

`RESUMED expanded=1000 states=5639 frontier=4639` matches run (c)'s FINAL exactly, then
`expanded` climbs to 1244 in the next 30s slice — the checkpoint round-trips (now including the
four new recovery counters) and the search continues from where it left off. Full raw output:
`results/sp80-s13-resume.txt`.

## What is UNVERIFIED

- Whether a true SPLIT or MISSING anomaly ever occurs at greater search depth than the 149
  diagnostic trials sampled (max length 35, three seeds). The recovery tiers for both are
  implemented and will fire if either shape appears, each with its own counter
  (`driver_recovered_split`, and `dropped_hard` distinguishing an unrecoverable MISSING/oversized
  case from the measured fork path) — but their correctness on an actual SPLIT/MISSING frame is
  unverified because none was observed to test against.
- Whether the twin-pair merge is itself a genuine, intentional in-game mechanic (two bodies under
  simultaneous shared control) versus a rendering artifact of the transfer animation. Not
  resolvable without reading environment_files (out of scope, and forbidden) — the FORK recovery
  is deliberately agnostic to which explanation is true, since it explores both candidate
  positions rather than assuming one.
- Whether forking doubles frontier growth materially over a long run (no long run was launched,
  per the anti-goals). The 120s smoke shows `driver_forked` roughly 3x `expanded` at this depth
  (each expansion touches this pair often, since it is reachable via many click/fire combinations
  at shallow depth) — worth watching in the HEARTBEAT/CURVE lines during the real run.

## Chain command (not run — main thread owns the long run)

Same shape as s12's launch (12 x 3300s cap chained, stop early on `exhausted=True` or `win=True`
in the FINAL line):

```bash
PYTHONUTF8=1 ./.venv/Scripts/python.exe sp80_s13.py --budget-seconds 3300 --fresh \
  > results/sp80-s13-run1.txt 2>&1
# then, repeated (resume -- no --fresh -- until FINAL shows exhausted=True or win=True):
PYTHONUTF8=1 ./.venv/Scripts/python.exe sp80_s13.py --budget-seconds 3300 \
  >> results/sp80-s13-run1.txt 2>&1
```

Watch `driver_dropped_hard` in every HEARTBEAT/CURVE/FINAL line — it should stay at or near zero
per the measured taxonomy; a sustained nonzero rate at scale would mean a fourth anomaly shape
exists that the 149-trial diagnostic sample never reached, and the fork/split/size design would
need re-measuring against it before the run is trusted.
