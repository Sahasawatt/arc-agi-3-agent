# ARC-AGI-3 breadth campaign — standing session brief (rewritten 2026-08-08)

Repo `Desktop\projects\arc-agi-3-agent` · python `./.venv/Scripts/python.exe` (always; never bare `python`).
This brief is meant to be reused. Update the GOAL numbers and the QUEUE after every session; leave the rest.

## GOAL

Clear ≥1 level in EVERY game. Standing: **11/17 games with a level, mean 6.320%**
(ls20 43.629 · re86 41.477 · tu93 5.946 · sp80 4.762 · tr87 4.762 · sk48 2.778 · wa30 2.222 · m0r0 1.526 · cn04 0.233 · ar25 0.095 · cd82 0.008)
← results/sweep-skewer.log (sweep_diff vs sweep-dial.log, control sk48: 16/17 identical to the digit, PASS)

## THE PATTERN THAT WORKS — four games have fallen to it, follow it

1. `probe_found.py <game>` — determinism, step rate, census, board dump, baselines.
2. `probe_acts.py <game> 8` — per-action diffs, guarded against empty frames.
3. Hypothesis probes until the mechanic is MEASURED.
4. **Solve level 1 BY HAND** with a scripted action list, verified forward-only.
5. Only then build a rung, shaped like `cover.py` / `swap.py` / `haul.py` / `maze.py` / `dial.py`,
   and measure its signature with `sigs.py` (every SHIPPED predicate x 17 reset frames)
   BEFORE wiring. Signatures are no longer all disjoint: `cover`'s fires on four games,
   so a contested game is settled by CASCADE ORDER and `sigs.py` checks that.

`bfs_solve.py <game> <depth> <nodes>` searches real engine states with deepcopy nodes.
Validated: sp80 L1 `[4,4,4,5]` in 38 expansions, ls20 L1 in 13 actions, tu93 L1 in 18
← results/bfs-control.txt, bfs-control-ls20.txt, tu93-bfs.txt. **A null means nothing
unless it reports `exhausted=True` AND the depth covers a whole life.** Not rules-legal
(it rewinds, like `play.py`) — use it to learn IF a level is winnable and what the line is.

## GATE

Any change to `compete.py`/`cover.py`/`swap.py`/`haul.py`/`maze.py`/`dial.py`/`skewer.py`/`discover.py`/`gate.py` =
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

Values that must not move ← results/sweep-skewer.log:
- ls20 **7/7** `[23, 45, 99, 178, 292, 209, 526]` · re86 **5/8** `[31, 56, 66, 80, 188]`
- tu93 **2/9** `[31, 14]` · tr87 **1/6** `[28]` · sk48 **1/8** `[24]` · sp80 `[16]`
  · wa30 `[43]` · ar25 `[173]` · cn04 `[131]` · m0r0 `[53]` · cd82 `[1306]`
- pytest **330 passed** — run redirected to a file and READ THE FILE (rtk rewrites pytest).

Recon-only work needs no sweep.

## QUEUE (highest value first)

0. **Port the GENERIC rung machinery into the Kaggle agent — in progress.** `kaggle/`
   holds the submission pipeline: `bundle.py` embeds driver modules (zlib+b64) +
   `adapter.py` (MyAgent per the official starter-kit contract) -> generated
   `kaggle/my_agent.py`, verified through the starter's own harness on all six driver
   games with numbers identical to compete.py (results/kaggle-local*.txt; starter kit =
   github.com/arcprize/ARC-AGI-3-Kaggle-Starter, cloned to scratchpad). What is NOT in
   yet: compete.play's rung machinery (ls20 43.6% + ar25/cn04/m0r0/cd82). Plan: run
   compete.play on a THREAD against an env PROXY whose step()/reset() pipe through the
   framework's choose_action queue — inversion without touching play()'s logic.
   Gotchas already measured: `GameAction(v)` raises on every int (enum .value is a
   property; map `{int(a.value): a for a in GameAction}` like compete does) · local
   play_local SSL-fails on the SECOND game per process (first always works; Kaggle
   gateway unaffected) · slim_framework.py writes cp1252 on Windows — rewrite the
   vendored agents/__init__.py ascii. Submission steps for the human: accept rules ->
   kaggle.json + username in kernel-metadata.json -> `make submit` -> Save & Run All ->
   Submit to Competition.

1. **Next 0-level game.** Remaining: dc22, ka59, sc25, bp35, sb26, g50t — and the walls
   have piled up: dc22 (sealed room, click sequences), ka59 (74-state BFS exhausted),
   sb26 (EVERY channel dead ← breadth-recon §sb26), g50t (search says L1 unwinnable).
   Fresh ground: **sc25** (metronome game, br-sc25-*.txt exist) and **bp35** (2-layer
   frame, A7 does something big at the bottom rows, cover-sig false positive). Run the
   pattern on bp35 first; sc25's election problem is a known repo-wide blocker.
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
