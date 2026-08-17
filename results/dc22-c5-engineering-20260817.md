# dc22 L2 -- c5 sound-key chain engineering

`dc22_c5_soundchain.py` = `dc22_c2_l2chain.py`'s resumable path-frontier BFS chain,
re-keyed with c4's validated sound key. Nothing reimplemented: `import dc22_c2_l2chain
as c2` reuses `c2.make_root`, `c2.press`, `c2.measure_death_policy` verbatim; `from
dc22_c4_hidden import key_total_raw_plus_nAnB_raw as l2_key` reuses the key verbatim.

## 1. Diff vs c2

**Only the key changes.** Everywhere c2's `run_bfs` computed `board_bytes(o2)` and
compared/inserted it into `seen`, c5 computes `l2_key(o2, seq + [act])` instead. Root
seeding is `seen = {root_key}` where `root_key = l2_key(root_obs, [])` (path=[] for the
root, matching c4's key contract: "`path` = the action list *including* the action that
produced `obs`" -- for the root no action has been taken).

Everything else is copied structurally identical, with two renames only (own file, own
constants, so a c5 run never collides with a live/resumed c2 checkpoint):

| | c2 | c5 |
|---|---|---|
| key | `board_bytes(o2)` (board only) | `key_total_raw_plus_nAnB_raw(o2, path)` (board + len + nA + nB), imported from `dc22_c4_hidden` |
| checkpoint | `results/dc22_c2_ckpt.pkl` | `results/dc22_c5_ckpt.pkl` |
| win file | `results/dc22-c2-win.txt` | `results/dc22-c5-win.txt` |
| root/alphabet/death-policy/persistence pattern | `c2.make_root` / 6-action alphabet / `c2.measure_death_policy` / atomic checkpoint | same functions, called via `c2.<name>(...)`, not reimplemented |
| depth cap | none in `run_bfs` (only `budget_seconds`) | none added -- per the brief, c2 had none so c5 adds none; the game's death policy is what bounds branches |
| `--seed-c1` | present (seeds frontier from c1's board-keyed checkpoint) | **dropped** -- c1's `seen` was hashed with board-only bytes; splicing those into a `(board,len,nA,nB)`-keyed `seen` would be a different-shaped dedup than the rest of the run and was never asked for. Not in c4's handoff either. |

No semantic change beyond the key: same 6-action alphabet, same per-process MEASURED
death policy (re-run every invocation including resume, same as c2, and both smoke runs
below independently re-measured it and got the same verdict as the checkpointed one).

## 2. State-space note (per c4 §4)

`total_len` is folded into the key as an **exact** integer, and `frontier` is a strict
FIFO deque (`popleft`/`append`), so two keys can only ever collide within the same BFS
layer -- the effective per-layer key is `(board, nA, nB)`. c4's sizecheck measured this
key retaining **1.38-1.39x** the distinct states of the old board-only key at a
comparable 2000-node expansion budget; the true inflation at full-run depth was not
separately measured by c4 and may differ. No depth cap was added (matches c2).

## 3. Smoke (foreground, both runs)

Both used the identical env fingerprint each c2 smoke run used (root at `i=25
l1_actions=25`, same button coords, same first-death depth=11 / total_expansions=7644 /
`reverts_to_root=False` / env terminates post-death -> `death_continues=False`).

### (a) `--budget-seconds 60 --fresh`

```
[    3.8s] L2 root at i=25 l1_actions=25
[    3.8s] buttons: A={'at': (52, 22), ...} B={'at': (52, 40), ...}
[  107.2s] DEATH MEASUREMENT: first GameState.GAME_OVER at depth=11 total_expansions=7644 levels_completed=1 reverts_to_root=False
[  107.2s] DEATH MEASUREMENT: post-death step -> obs returned but frame is EMPTY (len=0). FINDING: env terminates.
FRESH START death_continues=False
FINAL expanded=607 states=1134 frontier=527 deaths=0 exhausted=False win=False
DONE
```

Checkpoint written: `results/dc22_c5_ckpt.pkl` (4.5M).

**states/expanded ratio vs c2's noted:** c2's own 60s fresh smoke
(`results/dc22-c2-smoke-a.log`) is `expanded=509 states=757` -> ratio **1.487**. c5's is
`expanded=607 states=1134` -> ratio **1.868**, i.e. **1.256x** c2's ratio -- same
direction and same order of magnitude as c4's 1.38-1.39x sizecheck figure (not identical:
different budget shape -- c5's window includes the ~107s death-measurement re-run inside
its own process startup, and 607/509 expanded nodes is a much smaller sample than c4's
2000-expansion sizecheck runs).

### (b) resume (`--budget-seconds 60`, no `--fresh`)

```
[    3.6s] L2 root at i=25 l1_actions=25
[    3.6s] buttons: A={'at': (52, 22), ...} B={'at': (52, 40), ...}
[  106.9s] DEATH MEASUREMENT: first GameState.GAME_OVER at depth=11 total_expansions=7644 levels_completed=1 reverts_to_root=False
[  106.9s] DEATH MEASUREMENT: post-death step -> obs returned but frame is EMPTY (len=0). FINDING: env terminates.
RESUMED expanded=607 states=1134 frontier=527 deaths=0 death_continues=False
FINAL expanded=1185 states=2060 frontier=875 deaths=0 exhausted=False win=False
DONE
```

**Resume continues exactly**: `RESUMED expanded=607 states=1134 frontier=527` is a
byte-for-byte match to run (a)'s `FINAL expanded=607 states=1134 frontier=527` -- the
atomic checkpoint round-trips the frontier deque and `seen` set intact, and the fresh
per-process death re-measurement agreed with the checkpointed policy (no WARNING line
fired).

## 4. Chain command (not launched -- main thread owns the long run)

```bash
./.venv/Scripts/python.exe dc22_c5_soundchain.py --budget-seconds 3300
```

(repeat without `--fresh` to keep resuming; `results/dc22_c5_ckpt.pkl` already holds
`expanded=1185 states=2060 frontier=875` from the smoke runs above, so the next
invocation resumes from there, not from scratch).

## Anti-goals compliance

- No `environment_files/` read.
- Key re-implemented: **no** -- imported from `dc22_c4_hidden.key_total_raw_plus_nAnB_raw`.
- Semantic changes beyond the key: **none.**
- No long run launched.
- No backgrounding left unresolved: both smoke commands exceeded the harness's
  foreground timeout and were auto-moved to background; both were watched to completion
  (`grep`-polled for the `DONE` sentinel) and their full output captured to
  `results/dc22-c5-smoke-a.log` / `results/dc22-c5-smoke-b.log` before this report was
  written.
