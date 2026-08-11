# ARC-AGI-3 breadth campaign — standing session brief (rewritten 2026-08-08)

Repo `Desktop\projects\arc-agi-3-agent` · python `./.venv/Scripts/python.exe` (always; never bare `python`).
This brief is meant to be reused. Update the GOAL numbers and the QUEUE after every session; leave the rest.

## GOAL

Clear ≥1 level in EVERY game. Standing: **12/17 games with a level, mean 6.451%**
(ls20 43.629 · re86 41.477 · tu93 5.946 · sp80 4.762 · tr87 4.762 · sk48 2.778 · bp35 2.222 · wa30 2.222 · m0r0 1.526 · cn04 0.233 · ar25 0.095 · cd82 0.008)
← results/sweep-tape.log (sweep_diff vs sweep-click-aimed.log, control bp35: 16/17 identical to the digit, PASS)

## THE PATTERN THAT WORKS — five games have fallen to it, follow it

1. `probe_found.py <game>` — determinism, step rate, census, board dump, baselines.
2. `probe_acts.py <game> 8` — per-action diffs, guarded against empty frames.
3. Hypothesis probes until the mechanic is MEASURED.
4. **Solve level 1 BY HAND** with a scripted action list, verified forward-only.
5. Only then build a rung, shaped like `cover.py` / `swap.py` / `haul.py` / `maze.py` /
   `dial.py` / `skewer.py` / `tape.py`,
   and measure its signature with `sigs.py` (every SHIPPED predicate x 17 reset frames)
   BEFORE wiring. Signatures are no longer all disjoint: `cover`'s fires on four games,
   so a contested game is settled by CASCADE ORDER and `sigs.py` checks that.

`bfs_solve.py <game> <depth> <nodes> [clock_rows]` searches real engine states with
deepcopy nodes; an action the engine answers None 25x in a row is retired for the run
(bp35/cn04's click answered KeyError while the coordinates were being attached the way
the local wrapper ignores -- see QUEUE 1; the latch is still right, since a click can be
answered with None for other reasons). ⚠️ **bp35 cannot be BFS'd at all**: its own
game code recurses infinitely on a deepcopied env (RecursionError persists at limit
20000 -- deepcopy likely breaks an object-identity invariant, e.g. a visited set). The
instrument is dead there, not the game; bp35 needs forward-only hand probes
(`bp35_p1.py` started: the 9/11 piece slides on A3/A4, a 1141-cell global event fires
under the x43-47 chute, A7 is context-dependent).
Validated: sp80 L1 `[4,4,4,5]` in 38 expansions, ls20 L1 in 13 actions, tu93 L1 in 18
← results/bfs-control.txt, bfs-control-ls20.txt, tu93-bfs.txt. **A null means nothing
unless it reports `exhausted=True` AND the depth covers a whole life.** Not rules-legal
(it rewinds, like `play.py`) — use it to learn IF a level is winnable and what the line is.

## GATE

Any change to `compete.py`/`cover.py`/`swap.py`/`haul.py`/`maze.py`/`dial.py`/`skewer.py`/
`tape.py`/`discover.py`/`gate.py` =
full 17-game sweep before commit, per-game, no game loses a level ← CLAUDE.md.

```bash
./.venv/Scripts/python.exe compete.py > results/sweep-<name>.log 2>&1
```
~100 min (bp35's level 2 alone spends 2,202 actions). Compare with the parser, never by eye and never with `diff` (rewritten here):
```bash
./.venv/Scripts/python.exe sweep_diff.py <before.log> <after.log> <game-expected-to-change>
```
The third argument is the positive control — it refuses to report "identical" until it has
SEEN a difference in the game the change was aimed at. Hardcoding it worked for exactly one
comparison and then fired on the next.

Values that must not move ← results/sweep-tape.log:
- ls20 **7/7** `[23, 45, 99, 178, 292, 209, 526]` · re86 **5/8** `[31, 56, 66, 80, 188]`
- tu93 **2/9** `[31, 14]` · tr87 **1/6** `[28]` · sk48 **1/8** `[24]` · sp80 `[16]`
  · wa30 `[43]` · ar25 `[173]` · cn04 `[131]` · m0r0 `[53]` · cd82 `[1306]` · bp35 `[20]`
- pytest **330 passed** — run redirected to a file and READ THE FILE (rtk rewrites pytest).

Recon-only work needs no sweep.

## QUEUE (highest value first)

0. **Kaggle submission — READY, needs the human.** The FULL agent (compete.play,
   rungs + all seven drivers) runs unchanged on a worker thread behind a queue-backed
   proxy env: `kaggle/adapter.py` + `kaggle/bundle.py` -> generated `kaggle/my_agent.py`
   (rebuild after ANY module change). Verified through the official starter kit's own
   harness: **ls20 7/7 WIN 43.59%**, per-level transitions identical to the local sweep
   ← results/kaggle-ls20-v2.txt; driver games identical ← results/kaggle-local*.txt.
   Starter kit = github.com/arcprize/ARC-AGI-3-Kaggle-Starter (clone fresh; scratchpad
   copy dies with the session). Human steps: accept rules → username into
   notebooks/kernel-metadata.json + kaggle.json → copy kaggle/my_agent.py to
   agent/my_agent.py → `make submit` → Save & Run All → Submit to Competition.
   Traps already paid for: `GameAction(v)` raises on every int (map {int(a.value): a})
   · exec'd modules must enter sys.modules BEFORE exec (dataclasses) · the adapter's
   per-round timeout must dwarf the slowest planning round — ls20 L6 thinks for MINUTES
   on one round; a 120s timeout killed the worker and the silent 5/7 that resulted had
   no error anywhere (tell: acct file truncated at the 32KB OS buffer = never closed,
   + fallback resets every ~130 actions). Local-only: play_local SSL-fails on the
   SECOND game per process; slim_framework.py writes cp1252 on Windows.
   ⚠️ Pipe is ~20x slower per action than raw local (framework validate+log) — before
   submitting for real, estimate 110-game rerun wall clock; MAX_ACTIONS=2600 may need
   trimming.

1. **DONE 2026-08-11 — the click is aimed now, and it is INERT.** Fix in `compete.py`
   (both ways) + `kaggle/adapter.py`'s proxy `step(action, data=None)`; sweep
   `results/sweep-click-aimed.log` is identical to `sweep-skewer.log` in all 17 games,
   mean 6.320% (`sweep_diff.py`'s control fails on purpose — nothing differs), pytest 330.
   **Next lever, its own gated change:** `poke-click` picks the SMALLEST unprobed object
   first; dc22's only two responding targets are 40 and 47 cells, so the rung never
   reaches them. Order by response, or sweep large objects too. Rebuild the Kaggle bundle
   before any submission — `kaggle/adapter.py` changed. The original finding, kept because
   the reasoning is what generalises:
   `compete.py:1965` set the
   coordinates with `clicker.set_data({...})`; the local wrapper reads only its own `data`
   kwarg (`local_wrapper.py:234`), so every click ever made arrived empty and cn04/bp35
   answered `KeyError: 'x'` — the crash CLAUDE.md filed as cn04's own bug. Measured both
   ways, same coordinates ← results/click-probe.txt. Aimed, dc22 has exactly two live
   targets of 35 components ((48,19) n=129, (48,36) n=97 ← results/dc22-click.txt) and
   bp35's whole second verb appears. The fix is `env.step(clicker, data={...})` plus
   widening `kaggle/adapter.py:83`'s proxy `step(self, action)` (or the bundle breaks on
   the first click), then the full 17-game sweep — cn04 is the positive control for
   `sweep_diff.py` (its clicker stops being retired) and its 1/6 `[131]` is what to watch.

2. **bp35 LEVEL 1: SHIPPED. `tape.py` is the seventh driver; bp35 is 1/9 [20], 2.222%,
   and the sweep is clean — 16/17 identical to the digit, mean 6.320% -> 6.451%
   (results/sweep-tape.log). What is left there is LEVEL 2, which nobody has seen and
   which currently swallows 2,202 actions of `wander`.** The driver
   rediscovers the line from the frame — `1/9 levels actions=[20]`, score 2.222%, the hand
   line's own count ← results/tape-try2.txt, results/smoke-bp35-tape.txt. `sigs.py` PASSES
   with it (fires on bp35 alone; cascade `dial → tape → cover → …`, because cover's loose
   signature claims bp35 too) ← results/sig-sweep-tape.txt. pytest 330. It is the first
   driver that drives with CLICKS, so it is built only where a complex action exists and
   dropped if the clicker is retired. ⚠️ bp35 now takes ~10 minutes per run: its level 2
   swallows 2,202 actions of `wander`, so the whole sweep is ~100 min, not ~90. Level 2 is
   unseen and is the next bp35 question. Below is the hand line's own write-up:
   20 actions against a baseline
   of 21, forward-only, two identical runs ← results/bp35-solution.txt (the full line and
   the mechanic behind every step), bp35-p17.txt/bp35-p17b.txt. The win is **walking onto
   a colour-7 object**; it lives in the room the THIRD ride reaches, which is why fourteen
   probes never saw it. Verbs: a click turns a block into floor; a click on the block over
   the piece's own columns rides one room up; A7 at a shaft column rides down; the flood
   is an action timer (8 + ~8 per ride). Next per the repo's own pattern: a `bp35` driver
   shaped like `cover`/`swap`/`haul`/`maze`/`dial`/`skewer`, its signature measured by
   `sigs.py` over all 17 reset frames BEFORE wiring, cascade order re-checked, then the
   gated sweep. Level 2 is unseen.

3. **Next 0-level game.** Remaining: dc22, ka59, sc25, sb26, g50t — and the walls
   have piled up: dc22 (sealed room, click sequences), ka59 (74-state BFS exhausted),
   sb26 (EVERY channel dead ← breadth-recon §sb26), g50t (search says L1 unwinnable).
   Fresh ground: **sc25** (metronome game, br-sc25-*.txt exist; its election problem is a
   known repo-wide blocker). bp35 has left this list — see item 2. What its fall is worth
   to the others: the click verb now works everywhere (item 1), and a reachability claim
   expired TWICE in one session on the same board, both times because it had been measured
   before something was cleared.
2. **sk48 level 2 — the rearrange puzzle.** `skewer.py` clears L1 (1/8 `[24]`); level 2
   has four blocks in ONE row, recipe [8,12,9,14] vs forced row order 14,9,12,8 —
   ploughing through threads all four and does NOT win ← breadth-recon §sk48. Find the
   reorder mechanic (unload? re-pierce partial? push out the far side?). `bfs_solve` from
   a cleared-L1 process is the cheap instrument (deepcopy after the L1 line, then search).
3. **tr87 level 2 — same family, different geometry.** `dial.py` clears level 1 in 28
   actions and correctly declines level 2 ← results/tr87-l2.txt: SEVEN stations rather
   than five, and the hint band sits on its OWN lattice offset (band x18-45 against
   stations at x8,15,...,50), so a hint no longer names a station by POSITION -- which is
   the assumption level 1's reading rests on. Its top region also loses the (icon, block)
   tiles the level-1 combination is read from. Find what names a station there before
   writing any code; the driver's reading is otherwise geometry-free and should transfer.
4. **tu93 level 3 — a MOVING hazard, its own project.** The driver is wired and clears
   2/9 `[31, 14]` (5.946%, ← results/sweep-dial.log). It stops at level 3 because the only
   route to that goal passes a cell patrolled by a moving colour-8 body, and `maze.py` has
   no phase model — it blacklists a square only after dying there ← results/tu93-death.txt.
   Same class of mechanic ls20's levels 6-7 needed (`gate.mover_period` / `route_moving`
   are the built precedent). ⚠️ **tu93's GAME_OVER is NOT budget exhaustion** — it fires
   with 60 of 64 bar cells left, on collision ← results/tu93-budget-trace.txt.
5. g50t's open contradiction ← results/breadth-recon.md §g50t · re86 L6 · cn04 L2 trigger ·
   ar25 walls-during-planning.

## TRAPS — each has cost this repo a real session, most of them twice

- **An action that looks like a no-op usually says something about the STARTING POSITION.**
  g50t: only 2 of 5 actions move anything at reset (piece in a corner). tu93: three actions
  look dead and one looks like a one-shot; from a moved position they are four ordinary
  directions. g50t's action 5 is a RECALL and read as "no change" for eight presses because
  the piece was already at its destination. Always retry from somewhere else.
- **A reading taken while the piece stands on something is OCCLUSION.** Four games now.
  Step away and re-read before believing a count changed.
- **The piece is often not a solid block.** g50t's is a ring with a hole; wa30's carries a
  one-row edge naming its HEADING that moves to whichever side it walked; tu93's has a
  rotating notch. Reading a piece by its body colour reports a position that shifts when it
  turns, and measuring displacement from one colour reads the step minus one.
- **A detector that works at reset can stop working once the board changes.** wa30's frame
  became undetectable the moment the first crate slotted in; swap.py's clock is a band only
  while it is full. A signature function and a per-round tracker are not the same instrument.
- **A byte-identical run after a code change proves the change never executed.**
- **A signature you were told was measured may never have been.** The brief said
  `maze.signature()` had been run against all 17 reset frames; no run file held it, and
  what existed was a CANDIDATE table whose two predicates each fire on five games. Run
  `sigs.py` (every shipped predicate x 17 frames, own controls) before wiring anything.
- **Driver signatures are no longer disjoint, so CASCADE ORDER is load-bearing.**
  `cover`'s fires on ar25, re86, bp35 AND tr87 while only ever engaging re86 -- a driver
  handed a board it cannot read answers None on its first round. `dial` is asked before
  it; `sigs.py` fails if a contested game has the wrong driver first.
- **Put a positive control in the SAME invocation as any probe.** A probe that "ran" is not
  a probe that "measured".
- **Something measured but never COMPARED against anything is where the answer hides.**
  tr87's key sat in a region a whole session had dumped and never matched to anything.
- `rtk` rewrites grep, diff and pytest output. Never gate control flow on a grep exit code.
- Windows console is cp1252 — keep probe output ASCII or set `PYTHONUTF8=1`.
- Background bash starts at `Desktop` — `cd` into the repo in every backgrounded command.
- The engine returns EMPTY frames mid-level and at transitions — guard every frame read.
- ⚠️ Running `compete.py <one-game>` OVERWRITES `results/compete.json`, which holds the
  17-game sweep. It is tracked; `git checkout --` it afterwards.
- ⚠️ A backtick inside `git commit -m "…"` is command substitution: the word is executed and
  silently deleted from the message. Write the message to a file and use `-F`.

## RULES

- NEVER read/grep/list `environment_files/` — the answer key ← CLAUDE.md §The one rule.
- NEVER `git add -A`; stage by name, `git commit -F <file> -- <paths>`.
- Ask before every commit.
- One change at a time; a claim needs the run that produced it, named.
- Delegated agent results are INTENT, not fact — re-verify the artifact in the main thread
  (re-run a claimed solution forward-only; check the file set with git, not the summary).
