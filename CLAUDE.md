# arc-agi-3-agent — working rules

An agent for ARC Prize 2026 (ARC-AGI-3). `README.md` is the findings log and is written to be
read by a stranger; this file is the operating manual for changing the code.

## The one rule that is not negotiable

**Never read, grep, list or derive anything from `environment_files/`.** It is the source code
of the 25 public games — the answer key — and nothing derived from it generalises to the 110
hidden games that are actually scored. Every fact about a game must come from frames the
engine returned. `.gitignore` covers it; **never `git add -A`** anyway (the SDK writes into
that directory, and it has leaked into a staging area before).

## Running it

```bash
uv run python compete.py            # all 17 playable environments, writes results/compete.json
uv run python compete.py ls20       # one game, ~30-90s
uv run python -m pytest -q          # the suite
```

⚠️ `rtk` is on PATH and rewrites pytest's output — a run with failures has been reported as
`No tests collected` with **exit code 0**. Redirect to a file and read the file.

## How a change is accepted here

This repo is a measurement log that happens to contain code. The bar for any change:

1. **A full 17-game sweep before and after.** Per-game, not just the mean — the mean hides a
   game losing a level while another gains actions.
2. **No game loses a level.** Eight rules that were correct on paper have each cost a
   different game its own and been reverted; they are written up in `README.md` because the
   measurement is worth more than the code was. Add yours to that list rather than deleting
   the entry.
3. **One change at a time.** Two at once and a revert tells you nothing.
4. **A claim needs the run that produced it.** "It should help" is not a result. If a number
   is in a commit message, a README, or a report, it came from a run you can name.

## Traps that have already cost a session

- **`env.reset()` with zero actions taken since the last transition performs a full GAME
  reset**, back to level 1 — it only scopes to the current level once a real action has been
  taken. Probes that reset immediately are measuring level 1 while reporting level 4.
- **A blocked move IS charged budget** (measured 20/20, with 20 walked presses as a control).
  An earlier README claimed the opposite; what actually shows a refusal is that the piece's
  position does not change.
- **Track ids are reused across a level boundary.** Numbering carries on at a boundary so the
  old model's body ids are never handed out again, but it deliberately restarts on a level
  *reset*, where the same board yields the same ids and that is the right answer.
- **A model rebuilt on a new board knows less than the one it replaces.** Its `dirs`,
  `blocking` and `parts` all come back thin or empty, and it replaces a good model anyway.
  `build_model(prior=...)` exists for this; `test_compete.py` guards all three.
- **`hash()` of bytes is randomised per process.** Anything keyed on it makes every run a
  different experiment — pass the raw bytes.
- **`plates()` reads the whole frame, not the play area.** `ls20` draws its indicator across
  the row where the HUD starts.
- **A learned map of the board can remove routes that exist.** `ls20` level 4 has floor cells
  that carry the piece somewhere else, keyed on the cell a press *aims at* (not the source or
  the action). Six of them learned by accident cut the reachable board from 67 squares to 57
  and hid both glyph-changers. Any such map is used when it finds a way and ignored when it
  does not — and a cell is only believed once it has been **deliberately re-probed**, because
  waiting to trip over it twice never happens: a redirect drops the plan and the next route
  goes elsewhere.

- **A plate the piece is standing on is obscured, not read.** The piece is 5x5 and a goal
  box can be 7x7, so walking in garbles the glyph and then hides it. Read fresh, that looks
  like a display changing under the square the piece is on — which is exactly how a changer
  is recognised, so the square in front of the door gets recorded as one. `Gate.observe`
  ignores any plate under the footprint and keeps its last reading from off it; a plate that
  vanishes while the piece is elsewhere is a refill that has been taken, and is forgotten.
- **The clock's rate belongs to the LEVEL, so measure it over this level's steps only.** The
  same 84-cell bar spends 2 cells an action on `ls20` level 1 and 4 on level 2. A window that
  still holds the previous level's steps reads the most common fall off the wrong board, and
  because `full` is the largest reading ever taken, one bad reading at the boundary stands
  for the whole level — level 5 believed a life was 40 actions long instead of 21.
- **`walked` means an object moved by exactly the action's displacement**, so on a floor that
  carries the piece it is False for every carried step. Guarding changer-credit on it means
  no changer is ever credited on such a board. What the guard is actually for is not
  crediting a death, and a death is what puts the clock UP — ask that instead.
- **Cost a route the way the router walks it.** `stage` costed its legs with plain `bfs` and
  `_after`, so on a carrying board every distance it compared was fiction, and it predicted
  endpoints off the board and costed plans against them.

## What the scoring actually rewards

`min((baseline_actions / actions_taken)² × 100, 115)` per level, averaged **weighted by level
number**, and the game total is additionally capped by which levels were completed. Two
consequences worth holding on to:

- **Fast enough beats optimal.** Anything at or under 1.15× the human baseline scores the
  same 115, so shaving actions below that threshold buys nothing.
- **Depth is everything.** Level 1 of a 7-level game is 1/28 of the weight; level 7 is 7/28.
  Exploration is charged at exactly the same rate as play — there is no free discovery phase.

`scoring.py` implements this offline; `docs/competition-rules.md` records the rules with
sources, including a retraction of the "5× human median" action cap that is not a rule.

## Layout, in dependency order

`perception` (frame → objects, HUD, glyph bitmaps) → `identity` (cross-frame tracking) →
`discover` (movement model by acting) → `plan` (BFS routing) / `gate` (locks and the squares
that change them) / `signals` (counters, clock, refills) → `compete` (the rules-legal play
loop). `play.py` is the older rewinding searcher and is **not** rules-legal — its numbers are
upper bounds from a dev mode the competition does not offer.

## Git

Branch `master`, remote `Sahasawatt/arc-agi-3-agent` (public, MIT-0 — the competition requires
open source for prize eligibility). **Ask before every commit**, and stage files by name.
