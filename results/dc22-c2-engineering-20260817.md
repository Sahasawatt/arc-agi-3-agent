dc22 L2 chain — `dc22_c2_l2chain.py` turns `dc22_c1.py`'s one-shot
layer-frontier BFS (checkpointed but not resumable, dead branches dropped
after one un-tested measurement) into a resumable path-frontier BFS with a
death policy that is measured, not assumed. All three required smokes ran
foreground and pass; the long run was **not** launched.

## Diff vs c1

| | c1 (`dc22_c1.py`) | c2 (`dc22_c2_l2chain.py`) |
|---|---|---|
| Root replay, board key, button detect, 6-action alphabet | original | reproduced verbatim (cited, not imported — c1 is a script, not a module) |
| Frontier storage | one BFS **layer** of `deepcopy(env)` nodes at a time (memory-safe per CLAUDE.md, but a `deepcopy(env)` is not picklable) | **action paths** (sp80_s11 pattern) — picklable, replayed from a fresh `deepcopy(ROOT_ENV)` on pop. Trade: ~O(depth) replay cost per expand instead of O(1); priced into sp80_s11 already at "~20x slower at depth ~20" and accepted here for the same reason (resumability requires something you can pickle) |
| Checkpoint | written once, only if verdict==GROWING, no resume driver | atomic (`tmp`+`os.replace`) every 2,000 expansions **and** in a `finally:` on exit/interrupt; loaded automatically unless `--fresh` |
| `--seed-c1` | n/a | new: imports c1's 903 frontier paths (see §Seed-c1 below) |
| Death handling | first `GAME_OVER` measured once (`reverts_to_root: False`), then **all** dead branches dropped without further testing | measures **once per process invocation** (including on resume) whether the dead env is still steppable, prints the finding, and drives a global `death_continues` flag that decides whether a `GAME_OVER` child is dropped or kept as an ordinary node |
| Run boundedness | single deadline (18 min) + node cap (40,000), no heartbeat | `--budget-seconds` (default 3300) bounds this invocation only; `HEARTBEAT_S=60`; curve checkpointed every 2,000 expansions |

## The measured death finding

c1 only asked "does the board revert to the L2 entry frame" (no — it's a
distinct terminal frame) and then dropped every dead branch without asking
what a further `step()` on it does. This script asks that directly, every
process, by reproducing c1's exact layer-by-layer board-keyed BFS to the
identical first `GAME_OVER` (same alphabet, same dedup, deterministic
engine — landed at the same `depth=11`, `total_expansions=7644` in all
three runs below) and then pressing the dead env once more.

**Finding, measured 3/3 times (verbatim log excerpt):**

```
DEATH MEASUREMENT: first GameState.GAME_OVER at depth=11 total_expansions=7644
  levels_completed=1 reverts_to_root=False
DEATH MEASUREMENT: post-death step -> obs returned but frame is EMPTY (len=0).
  Engine does not hand back a usable frame after GameState.GAME_OVER on this
  env (no explicit reset() attempted). FINDING: env terminates.
```

The obs is **not `None`** (a case the code explicitly checks and handles
separately) — it is a real object whose `.frame` is an empty list, which
crashed a naive `np.array(o.frame)[-1]` on the first run (`IndexError:
index -1 is out of bounds for axis 0 with size 0`, `results/dc22-c2-smoke-a.log`
first attempt). That is a third outcome distinct from both "play continues"
and "obs is None," and it matches the pattern already on record for sp80 in
`CLAUDE.md` ("without that `reset()` it stays GAME_OVER and hands back
empty frames forever"). No explicit `env.reset()` was tried here (out of
scope — the instruction was to measure whether play continues on its own,
not to build a revert mechanism), so the honest finding is **"env
terminates"** and `death_continues = False`: `GAME_OVER` children are
dropped and counted in `deaths`, exactly as c1 did — now confirmed by
measurement instead of assumed by inheritance from c1's code shape.

This also means the `death_continues=True` branch of the main loop (treat
the post-death node as an ordinary, kept, dedup'd state) is currently
**dead code on this game** — left in per the task spec ("if play continues:
treat as ordinary nodes... do not silently choose") so the policy is a
real fork driven by the measurement, not a hardcoded drop with a docstring
promise.

Cost: reproducing the depth-11 death is ~7,644 expansions, ~120s per
invocation (`ponytail:` this is a fixed per-process tax, paid again on
every resume — cache the verdict across resumes only if this cost becomes
the bottleneck; it currently isn't, since the BFS proper is far more
expensive at any real budget).

## Smoke outputs (foreground, verbatim tails)

**(a) 60s `--fresh`** — `results/dc22-c2-smoke-a.log`:
```
[    3.1s] L2 root at i=25 l1_actions=25
[    3.1s] buttons: A={'at': (52, 22), ...} B={'at': (52, 40), ...}
[  122.6s] DEATH MEASUREMENT: first GameState.GAME_OVER at depth=11 total_expansions=7644 ...
[  122.6s] DEATH MEASUREMENT: post-death step -> obs returned but frame is EMPTY (len=0). ... FINDING: env terminates.
FRESH START death_continues=False
FINAL expanded=509 states=757 frontier=248 deaths=0 exhausted=False win=False
DONE
```
(`deaths=0` here is expected, not a bug: 509 nodes popped is still short of
the ~956 needed to fully clear c1's depth-0..9 layers, so this short window
never reached the depth where `GAME_OVER` first appears.)

**(b) resume (no `--fresh`, 20s)** — `results/dc22-c2-smoke-b.log`:
```
[  124.4s] DEATH MEASUREMENT: ... FINDING: env terminates.
RESUMED expanded=509 states=757 frontier=248 deaths=0 death_continues=False
FINAL expanded=654 states=947 frontier=293 deaths=0 exhausted=False win=False
DONE
```
`RESUMED` picked up exactly where (a) left off (`expanded=509` matches (a)'s
`FINAL`), then advanced to `expanded=654`. Resume verified.

**(c) `--seed-c1 --fresh` (20s)** — `results/dc22-c2-smoke-c.log`:
```
[  123.4s] DEATH MEASUREMENT: ... FINDING: env terminates.
FRESH START death_continues=False
[  123.4s] SEED-C1: loaded 903 frontier paths from c1 ckpt (depth=19, c1 visited
  count=8023 -- COUNT ONLY, not a hash set, so historical dedup is NOT imported)
SEED-C1: frontier extended by 903 paths, 903/903 hashed into `seen` (budget_exceeded=False)
FINAL expanded=151 states=1224 frontier=1073 deaths=0 exhausted=False win=False
DONE
```
All 903 c1 paths loaded and hashed into `seen` well inside the 90s seeding
deadline (cheap — implemented in full, not just smoke-scoped). One
documented limitation: c1's own checkpoint stores `visited` as an **int
count** (8,023), not the hash set, so the 8,023 historically-visited boards
cannot be imported — only the 903 frontier-tip paths. A resumed/seeded
search can therefore re-derive (and re-discard as `repeat`) states c1 had
already ruled out; this is a correctness-preserving inefficiency, not a
soundness gap (the `seen` set only ever suppresses re-expansion, never
mis-classifies a state).

## Chain command

```bash
PYTHONUTF8=1 ./.venv/Scripts/python.exe dc22_c2_l2chain.py --budget-seconds 3300
```
(no `--fresh` → resumes `results/dc22_c2_ckpt.pkl`, currently holding smoke
(c)'s state: `expanded=151 states=1224 frontier=1073`, since (c) ran last
and each smoke's checkpoint overwrites the previous one by design.)

## Anti-goals compliance

- No `environment_files/` read.
- No semantic changes beyond the death policy, which was measured (not
  chosen) and matches c1's own prior behaviour (drop) once tested.
- No long run launched; all three invocations above ran with explicit short
  `--budget-seconds` and completed foreground.
- `--seed-c1`'s inability to import c1's `visited` **set** (only its count
  was ever saved) is stated plainly above, not silently worked around.
