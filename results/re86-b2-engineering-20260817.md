# re86 b2 -- L6 chain engineering (persistence only, no semantic change)

New file: `re86_b2_l6chain.py`. Reuses `re86_b1_bfs.build_root`/`grid_bytes`/`TARGET_LEVEL`
directly (`import re86_b1_bfs as b1`) -- root builder, board key (last-plane bytes),
action set `[1..5]`, WIN test and GAME_OVER handling are byte-identical to b1, unedited.

## Diff vs b1 -- persistence only

| | b1 (`re86_b1_bfs.py`) | b2 (`re86_b2_l6chain.py`) |
|---|---|---|
| Frontier storage | `(key, deepcopy(env), path)` tuples, envs held in memory | `path` only (action list from root); env rebuilt by replay |
| Node expansion | expand directly off the stored `child_env` | `replay(path)`: `deepcopy(ROOT_ENV)` + step through `path`, then expand |
| `visited` | in-memory `set`, dropped at process exit (only `len()` saved) | in-memory `set`, checkpointed whole, byte-for-byte |
| Checkpoint trigger | once, only when the run stops (`node_cap`/`time_cap`) | every 2,000 expansions **and** on exit (`try/finally`), atomic (`tmp`+`os.replace`) |
| Checkpoint payload | `frontier_paths` (paths only, no keys, no visited set) | full resumable state: `layer`, `next_layer` (ckey->path), `visited`, all counters, `census`, `win_path`, gameover-control flags |
| Resume | **none** -- explicitly flagged as missing | `load_checkpoint()`; `RESUMED expanded=N frontier=N` |
| Seed from b1 | n/a | `--seed-b1`: loads `results/re86_b1_ckpt.pkl`'s `frontier_paths` as the initial layer (`layer_no` set to `len(b1_census)`); b1's `visited` set is **not present** in its checkpoint (only `visited_count`), so it cannot be carried -- b2 starts `visited={root_key}` only and re-derives dedup lazily as each seeded path is popped and replayed |
| Stop condition | `NODE_CAP` (40,000) or `TIME_CAP_S` (14 min) | `--budget-seconds` only (default 3300), no node cap |
| Budget scope | one process = one run, no chaining | per-invocation; chain by re-running without `--fresh` |
| Loop shape | nested `for key,env,path in layer: for v in action_values:` | flattened `while True:` state machine (layer-drain / expand-node / advance-layer), same layer semantics, restartable mid-layer |

Board key, action set, GAME_OVER control (`env.reset()` after first GAME_OVER, compared to
`root_key`), deepcopy-fidelity control, and layer-by-layer census reporting are all reused
verbatim from b1's logic (re-typed against the imported helpers, not re-derived).

## Smoke test outputs (foreground, all three ran)

**(a) `--budget-seconds 60 --fresh`** (`results/re86-b2-smoke-a.txt`):
```
[root] levels_completed=5 recipe_len=421 cost=16.6s
[control] deepcopy fidelity: OK
FRESH START
[layer 0] frontier=5 visited=6 expanded=5 ...
...
[layer 7] frontier=2408 visited=4741 expanded=11665 ...
  CHECKPOINT expanded=20000 visited=8060 frontier=4060
FINAL expanded=20805 states=8298 frontier=4136 deaths=0 exhausted=False win=False
[done] stop_reason=budget total wall time 82.4s
```
Layer-by-layer frontier/visited/expanded counts through layer 7 are identical to b1's own
first-run census (b1: layer7 frontier=2408 visited=4741 expanded=11665 -- confirms the
persistence swap changed nothing about the search itself). Checkpoint file written
(`results/re86_b2_ckpt.pkl`, 32.6MB after ~20.8k expansions -- the `visited` set dominates
size; note this scales linearly and is worth watching over a full 3300s run).

**(b) resume (no `--fresh`), `--budget-seconds 30`** (`results/re86-b2-smoke-b.txt`):
```
RESUMED expanded=20805 frontier=4136
  CHECKPOINT expanded=22000 visited=8611 frontier=4210
[layer 8] frontier=4327 visited=9068 expanded=23700 ...
FINAL expanded=28125 states=10184 frontier=4557 deaths=0 exhausted=False win=False
[done] stop_reason=budget total wall time 49.9s
```
`RESUMED expanded=20805 frontier=4136` matches (a)'s FINAL line exactly -- resume continues
from the correct point, not from scratch. Root is rebuilt (~17-30s, expected: build_root()
is a full ~421-action replay every process start) then the layer-8 boundary is crossed
cleanly. This checkpoint (expanded=28125) was left in place as the live
`results/re86_b2_ckpt.pkl` for the main thread's chain run.

**(c) `--fresh --seed-b1`, `--budget-seconds 30`** (`results/re86-b2-smoke-c.txt`):
```
FRESH START seeded_from_b1 paths=6414 layer_no=12
  CHECKPOINT expanded=4000 visited=2354 frontier=7167
FINAL expanded=4873 states=2908 frontier=7371 deaths=0 exhausted=False win=False
```
Confirms `--seed-b1` loads all 6,414 of b1's frontier paths into the initial layer
(`layer_no=12`, matching `len(b1_ckpt['census'])`) and the run proceeds without error --
new checkpointing, heartbeat and layer-advance logic all exercised on seeded data. This
run's checkpoint was **not** kept (it would have overwritten (b)'s further-progressed
state); (b)'s checkpoint was restored as the live one afterward
(`results/re86_b2_ckpt.pkl`: expanded=28125, visited=10184, layer_no=9, frontier=4557,
verified by re-loading the pickle).

## Chain command for the main thread

Resume the live checkpoint (currently at expanded=28125, layer 9) with the full budget:

```bash
PYTHONUTF8=1 ./.venv/Scripts/python.exe re86_b2_l6chain.py --budget-seconds 3300
```

Re-run the identical command (no `--fresh`) to keep chaining across invocations until
`FINAL ... exhausted=True` or `win=True`. On win, the sequence is printed
(`WIN seq=[...]`) and written to `results/re86-b2-win.txt`.

To instead start over seeded from b1's exhausted-frontier snapshot instead of continuing
b2's own progress: `--budget-seconds 3300 --fresh --seed-b1` (one-time; drop both flags on
every subsequent chain call after that).

## Not done (anti-goals, honored)

No semantic change to root/key/actions. No long run launched -- longest single invocation
above was 60s wall (excluding ~17-30s root rebuild). Nothing backgrounded.
