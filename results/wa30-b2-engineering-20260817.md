# wa30_b2_l3chain.py — engineering writeup (2026-08-17)

`wa30_b1_l3bfs.py`'s real-engine L3 BFS converted to the `sp80_s11.py` path-frontier +
checkpoint/resume + budget shape. No search semantics changed.

## What changed vs b1

| Aspect | b1 | b2 |
|---|---|---|
| Frontier | `deque` of `(deepcopy(env) node, path, depth, key)` — holds a live env clone per queued state | `deque` of `(path, key)` — action list only, env reconstructed on pop via `replay()` |
| Memory ceiling | RAM wall (~12k such nodes hit 6.3GB on the analogous sp80 search); capped `MAX_NODES=6,000` as a safety valve | none needed — a path frontier of the same size is a list of small int-tuples, not env clones |
| Resume | none — `--budget-seconds`-style run always starts fresh; checkpoint (`results/wa30_b1_ckpt.pkl`) was write-only, no loader | `load_checkpoint()`/`save_checkpoint()` (atomic tmp+`os.replace`, s11 pattern); `--fresh` skips it, its absence resumes |
| Checkpoint cadence | ad hoc (only near budget exhaustion or when growing past 50% of budget) | every `CURVE_EVERY=2000` expansions + always in a `finally:` block on exit |
| Run length | fixed `BUDGET_S=280` constant, plus a hardcoded `ENGINE_CAP_S=8*60` overall safety cap | `--budget-seconds` CLI arg (default 3300, matching s11) bounding the BFS loop only; `ENGINE_CAP_S` dropped — it existed as a safety net sized for b1's short one-shot 280s run and would truncate a legitimate 3300s chained run, so keeping it would have been a regression, not a port |
| Observability | periodic `...expanded=` print every 250 nodes, no time-based heartbeat | `HEARTBEAT_S=60` wall-clock heartbeat (s11 pattern) |
| Output | free-form `VERDICT:` prose | machine-readable `FINAL expanded=N states=N frontier=N deaths=N divergence=N exhausted=bool win=bool` line, plus (on win) a `WIN: seq=[...]` line and `results/wa30-b2-win.txt` |

**Unchanged from b1** (cited/reused, not rewritten): the L3 root recipe (drive `Haul` from a
fresh reset to `levels_completed==2`, `MAX_DRIVE=400`), the deepcopy-fidelity control, the
death-reverts-to-root control, the action set `{1,2,3,4,5}` (`env.action_space`, asserted no
complex actions), the board key (`grid(obs).tobytes()`), `DEPTH_CAP=100`, and GAME_OVER
handling (counted as a death, node dropped, never enqueued). `make_root()` in b2 is b1's
phases 1–3 verbatim, wrapped as a function so it runs once per invocation (fresh or resumed)
— cheap (~15s wall, 113 actions this run) relative to a 3300s budget, and reconstructing it
every run means the checkpoint never needs to serialize an env or a `ROOT` object, only
action-path frontier entries and board-byte keys, both trivially picklable.

Root recipe is deterministic: byte-identical 113-action recipe across the fresh and resumed
smoke runs below (Haul's drive from a fresh reset has no randomness this game exercises).

## Smoke test (a): `--budget-seconds 45 --fresh`

```
wa30 verbs: plain=[1, 2, 3, 4, 5] complex=[]
root reset: level=0, board (64, 64)
drive finished: i=113 actions, levels_completed=2, recipe len=113
CONTROL deepcopy fidelity: PASS
L3 root recipe replay VERIFIED fresh.
CONTROL death-reverts (try=100): PASS
BFS action set: [1, 2, 3, 4, 5]
FRESH START

nodes expanded : 982
distinct boards: 1737
frontier left  : 755
deaths         : 0
elapsed        : 45.1s of 45s budget
divergence (same board+action giving different results): 0 cases

FINAL expanded=982 states=1737 frontier=755 deaths=0 divergence=0 exhausted=False win=False
DONE
```

Checkpoint written: `results/wa30_b2_ckpt.pkl` (19.3MB), verified by unpickling — `expanded=982
frontier=755 seen=1737 deaths=0`, matching the FINAL line exactly.

## Smoke test (b): rerun without `--fresh`

```
wa30 verbs: plain=[1, 2, 3, 4, 5] complex=[]
root reset: level=0, board (64, 64)
drive finished: i=113 actions, levels_completed=2, recipe len=113
CONTROL deepcopy fidelity: PASS
L3 root recipe replay VERIFIED fresh.
CONTROL death-reverts (try=100): PASS
BFS action set: [1, 2, 3, 4, 5]
RESUMED expanded=982 states=1737 frontier=755 deaths=0 divergence=0

nodes expanded : 1607
distinct boards: 2989
frontier left  : 1382
deaths         : 0
elapsed        : 30.1s of 30s budget
divergence (same board+action giving different results): 0 cases

FINAL expanded=1607 states=2989 frontier=1382 deaths=0 divergence=0 exhausted=False win=False
DONE
```

`RESUMED expanded=982` matches the checkpoint from run (a) exactly; `expanded` continued
growing (982 → 1607), confirming the frontier/seen state carried over correctly. Root
recipe (113 actions) is byte-identical between the two runs.

## Chain command (main thread owns the actual long run)

```bash
./.venv/Scripts/python.exe wa30_b2_l3chain.py --budget-seconds 3300 --fresh   # first invocation
./.venv/Scripts/python.exe wa30_b2_l3chain.py --budget-seconds 3300          # every subsequent resume (no --fresh)
```

Each invocation pays `make_root()`'s ~15s construction cost once, then resumes the frontier
from `results/wa30_b2_ckpt.pkl`. Growth rate observed in the smoke runs: ~625 states/45s in
run (a), ~1252 states/30s in run (b) — both well within the depth-100, RAM-safe path-frontier
regime b1's growing-but-uncapped search was heading toward before it hit the node-storage
ceiling.
