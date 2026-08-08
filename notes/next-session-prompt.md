# ARC-AGI-3 breadth campaign — standing session brief (rewritten 2026-08-08)

Repo `Desktop\projects\arc-agi-3-agent` · python `./.venv/Scripts/python.exe` (always; never bare `python`).
This brief is meant to be reused. Update the GOAL numbers and the QUEUE after every session; leave the rest.

## GOAL

Clear ≥1 level in EVERY game. Standing: **8/17 games with a level, mean 5.527%**
(ls20 43.629 · re86 41.477 · wa30 2.222 · sp80 4.762 · m0r0 1.526 · cn04 0.233 · ar25 0.095 · cd82 0.008)
← results/sweep-haul.log

## THE PATTERN THAT WORKS — four games have fallen to it, follow it

1. `probe_found.py <game>` — determinism, step rate, census, board dump, baselines.
2. `probe_acts.py <game> 8` — per-action diffs, guarded against empty frames.
3. Hypothesis probes until the mechanic is MEASURED.
4. **Solve level 1 BY HAND** with a scripted action list, verified forward-only.
5. Only then build a rung, shaped like `cover.py` / `swap.py` / `haul.py`.

`bfs_solve.py <game> <depth> <nodes>` searches real engine states with deepcopy nodes.
Validated: sp80 L1 `[4,4,4,5]` in 38 expansions, ls20 L1 in 13 actions, tu93 L1 in 18
← results/bfs-control.txt, bfs-control-ls20.txt, tu93-bfs.txt. **A null means nothing
unless it reports `exhausted=True` AND the depth covers a whole life.** Not rules-legal
(it rewinds, like `play.py`) — use it to learn IF a level is winnable and what the line is.

## GATE

Any change to `compete.py`/`cover.py`/`swap.py`/`haul.py`/`discover.py`/`gate.py` =
full 17-game sweep before commit, per-game, no game loses a level ← CLAUDE.md.

```bash
./.venv/Scripts/python.exe compete.py > results/sweep-<name>.log 2>&1
```
~90 min. Compare with the parser, never by eye and never with `diff` (rewritten here):
```bash
./.venv/Scripts/python.exe sweep_diff.py <before.log> <after.log> <game-expected-to-change>
```
The third argument is the positive control — it refuses to report "identical" until it has
SEEN a difference in the game the change was aimed at. Hardcoding it worked for exactly one
comparison and then fired on the next.

Values that must not move ← results/sweep-haul.log:
- ls20 **7/7** `[23, 45, 99, 178, 292, 209, 526]` · re86 **5/8** `[31, 56, 66, 80, 188]`
- sp80 `[16]` · wa30 `[43]` · ar25 `[173]` · cn04 `[131]` · m0r0 `[53]` · cd82 `[1306]`
- pytest **255 passed** — run redirected to a file and READ THE FILE (rtk rewrites pytest).

Recon-only work needs no sweep.

## QUEUE (highest value first)

1. **Wire tu93 — the rung is BUILT and verified; wiring is all that is left.**
   `maze.py` clears **2 levels, [31, 14] actions** driven by its own harness, verified
   in the main thread ← results/tu93-maze.txt. `test_maze.py` is 30 tests with a proved
   teeth mutation ← results/teeth-mut1.txt. **`maze.signature()` was run for real against
   all 17 reset frames and fires on tu93 alone** — do not trust the multi-True rows in
   results/maze-sig.txt, those are the exploratory candidate table, not the final
   predicate. Wiring is three edits in `compete.py` copying the `haul` pattern, then the
   full sweep, then ask before commit.
   It stops at level 3, and the blocker is named: the only route to that goal passes a
   cell patrolled by a MOVING colour-8 hazard, and the driver has no phase model — it
   blacklists a square only after dying there ← results/tu93-death.txt. Same class of
   mechanic ls20's levels 6-7 needed, so treat it as its own project, not a bug.
   ⚠️ Also measured on the way: **tu93's GAME_OVER is NOT budget exhaustion** — it fires
   with 60 of 64 bar cells left, on collision with that moving body
   ← results/tu93-budget-trace.txt.

   (superseded) the hand line, still valid: 18 actions vs baseline 19
   `[4,2,2,4,1,4,2,2,3,3,2,4,4,2,4,1,4,2]` ← results/tu93-verify.txt, re-verified in the
   main thread. Plain maze: notched 3x3 piece, 6px lattice, four fixed directions, walls,
   a colour-14 goal block, budget row at y63. ⚠️ The repo's GENERIC maze machinery scores
   zero here, on a game whose mechanic is four directions and a goal square — so what fails
   is upstream of routing, most likely piece identification, because the colour-4 notch
   rotates to whichever side the piece last moved and the body is not rigid.
2. **Wire tr87** — level 1 solved, 28 actions vs baseline 54
   `[1,1,1,1,1,4,1,1,1,1,1,4,1,1,1,4,1,1,1,1,1,1,4,1,1,1,1,1]` ← results/tr87-solution.txt.
   Five-station combination lock: ACTION1/2 dial the station under the clamp (period 7,
   2 is 1's inverse), ACTION3/4 slide the clamp between five fixed x-stations (15, 22, 29,
   36, 43). Win = all five at their target phase AT ONCE (15→5, 22→5, 29→3, 36→6, 43→5),
   checked continuously. Targets are read from the top y4-28 region: six (icon, block)
   pairs, icon names the station, block names the phase.
3. **Next 0-level game.** Remaining: dc22, ka59, sc25, bp35, sk48, sb26, g50t. Prefer ones
   with no complex action; the click-driven ones are a different problem.
4. g50t's open contradiction ← results/breadth-recon.md §g50t · re86 L6 · cn04 L2 trigger ·
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
