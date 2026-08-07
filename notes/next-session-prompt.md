# ARC-AGI-3 breadth campaign — session brief (written 2026-08-08, after sp80 landed)

Repo: `Desktop\projects\arc-agi-3-agent` · python = `./.venv/Scripts/python.exe` ← author's decision (venv path, standing)

## GOAL

Clear ≥1 level in EVERY game. Standing: **7/17 games with a level, mean 5.396%**
(ls20 43.629 · re86 41.477 · sp80 4.762 · m0r0 1.526 · cn04 0.233 · ar25 0.095 · cd82 0.008)
← results/sweep-swap.log

## GATE

Any code change to `compete.py`/`cover.py`/`swap.py`/`discover.py`/`gate.py` = full 17-game
sweep before commit, per-game, no game loses a level ← CLAUDE.md §How a change is accepted:

```bash
./.venv/Scripts/python.exe compete.py > results/sweep-<name>.log 2>&1
```

← runs ~90 min ← the 2026-08-07 session's two sweeps

Compare the logs with the parser, never by eye and never with `diff` (rewritten on this
machine, ~/.claude/RTK.md — it has its own output shape and no `<`/`>` markers):

```bash
./.venv/Scripts/python.exe sweep_diff.py results/sweep-swap.log results/sweep-<name>.log
```

It asserts a positive control (sp80 must differ between the two named baselines) before
believing any "identical", so a blind parser cannot report a clean sweep ← sweep_diff.py

Values that must not move:
- ls20 **7/7** 43.629% `[23, 45, 99, 178, 292, 209, 526]` ← results/sweep-swap.log
- re86 **5/8** 41.477% `[31, 56, 66, 80, 188]` ← results/sweep-swap.log
- sp80 **1/6** 4.762% `[16]` ← results/sweep-swap.log (NEW this session)
- ar25 `[173]` · cn04 `[131]` · m0r0 `[53]` · cd82 `[1306]` ← results/sweep-swap.log
- pytest: **240 passed**, run as `./.venv/Scripts/python.exe -m pytest -q > file 2>&1` and READ THE FILE ← results/pytest-d1-green.txt; file-redirect rule ← CLAUDE.md §Running it (rtk trap)

Recon-only work (probes, board dumps, doc updates) needs no sweep ← CLAUDE.md §How a change is accepted.

## READ FIRST

`results/breadth-recon.md` §"sp80 OPENS" to end of file — the sp80 mechanic, both transfer
maps, the closed/open list, the sweep verdict and the D1 defect. That file is the state of
record; this brief only points.

## FIRST TASK

**Resolve g50t's open contradiction** ← results/breadth-recon.md §g50t (read it first; the
mechanic, the search and its two controls are all written up there).

The state: a controlled exhaustive engine-BFS says **no sequence of ≤130 actions from the
reset board completes level 1**, the clock allows 128, a death restores the board exactly
(census delta {}), and the human baseline for that level is **78**. One of those is false
and it is **not the search** — the harness returns sp80's known `[4,4,4,5]` in 38
expansions ← results/bfs-control.txt, and `deepcopy` is a true fork on both games with a
positive control ← results/deepcopy-check.txt.

Three candidates, none measured yet — each is one probe:

1. **The recall's y behaviour was never read.** Action 5 moves the piece to x=14
   (measured, `results/g50t-p8.txt`); nobody asked what it does to y, or whether it
   ignores walls. A teleport that ignores walls is a routing primitive the BFS already
   explored, but its own model of it may be wrong.
2. **Something enables the top-left indicator.** A live run shows it shifting ±4 under
   action 5 at i=1825 (`results/g50t-run1.txt`) and no probe from reset reproduces it.
   Find what turns it on — that is a state the BFS's visited key does not contain, which
   is exactly the shape of the sp80 null (there the missing key was the magazine).
3. **The hold-to-open gate may have a second holder.** Standing on the snake's head opens
   the maze and stepping off closes it; a single piece cannot hold and pass. Ask the board
   what else can sit on it.

UNKNOWN — whether `baseline_actions[0]` for g50t indexes the level the engine calls level 1.
Cheap check: compare another game's baseline against a level whose action count is known
(sp80 L1 baseline 39 vs the measured 16-action clear; ls20 L1 baseline 22 vs 23).

**Do not spend the session on the router fix until that is settled** — but note it is
already diagnosed and independent: discovery learns `block=[0, 8]` and colour 8 IS the gate;
with 8 as wall the goal box is unreachable (11 positions), with 8 as floor it is reachable
(20 positions, (44,50)) ← results/g50t-p2.txt. `classify_colours` earned that label honestly
— the move into (14,38) really is refused, 25 times, with 8 the only unexplained colour —
so the fix is not "drop 8", it is a shape for **a colour that blocks except while its head
is held**. Any change there is a `discover.py` change and the full gate applies.

Queue after it (do not start a second before the first is written up): `wa30` (same shape as
g50t and sp80) · re86 L6 · cn04 L2 trigger · walls-during-planning (ar25).

## DEAD LIST — measured refuted, do not re-derive:

sp80 (2026-08-06/07 ← results/breadth-recon.md §sp80, run files named there):
- L2 win within one life: NONE — BFS over the real engine, exhaustive: 39,328 states,
  `(board, ammo)` key, depth 44 on the 45-action budget ← results/sp80-p11.txt
- L2 win clock-gated at stack-aligned candidates: NONE ← results/sp80-p15.txt
- L2 board varying with the L1 exit recipe: NO (byte-identical, 3 recipes) ← results/sp80-p16.txt
- Transfer legality clock- or route-dependence: NONE (position-pure) ← results/sp80-p14.txt
- Transfer rule closed forms REFUTED against the p12+p13 maps: Manhattan / Chebyshev /
  Euclidean radii, sum-diagonals, every 45° corner ray, all single half-planes and all cones
  over corner pairs (coefficients −3..3) ← results/sp80-fit.txt
- L2 transfer chain: 80-body ↔ block-2 ONLY; block-1 is NEVER a target, even fully
  overlapped ← results/sp80-p12.txt, sp80-p13.txt
- 8-blocks are pass-through scenery: no push, no collect ← results/sp80-p5.txt
- ACTION6 (click) is a no-op on every object centre tried ← results/sp80-p2.txt

re86 L6, all one probe each:
- colour-1 cells are WALLS (arm overlap = refusal); the ring's hole is geometrically SEALED to both shapes ← results/re86-l6p2.txt, re86-l6p4.txt
- covering a same-colour PAIR does not consume it ← results/re86-l6p3.txt
- covering a whole quad with mixed coats (plus-9 + square-11) does not consume ← results/re86-l6p6.txt
- centre CAN stand on a box inner (step 3 jumps the ring) — inert ← results/re86-l6p7b.txt
- no swatch exists on the board; the ring is the only unexplained object ← results/re86-l6p1.txt

cn04 L2:
- bodies do NOT collide — the piece passes through every shape; the historical 1,600-round refusal was the board edge ← results/cn04-l2c2.txt
- pad adjacency above/coincide/below the unique Δ-mate (b-shape): all inert ← results/cn04-l2d2.txt
- rotator at dock, carry-after-dock, hammer-through: inert ← results/cn04-l2h.txt, cn04-l2e2.txt, cn04-l2i.txt
- single-pad tour of all 12 pads, up-exit into the top strip: inert ← results/cn04-l2g.txt, cn04-l2j.txt
- the colour-4 strip is a CLOCK (~1 cell per 3-4 actions, persists across level resets), not a door ← results/cn04-l2j.txt
- the dock DOES register (8-census 108 -> 72 while docked) — the trigger is what's missing, not the dock ← results/cn04-l2f.txt

ar25 family:
- player-election fix alone loses ar25; walk caps (emission-counted, arrival-counted, board-change) each lose a different game; NO landable fix exists — next lever is walls learned DURING planning, nothing else ← CLAUDE.md §Traps first entry + results/breadth-recon.md §night 2

Occlusion, the repo's oldest trap, has now lied on three different games:
- re86 "collection"/"consumption" read while a shape sits on the thing ← results/breadth-recon.md §session 2
- cn04's own body hiding a socket pad on the approach ← results/br-cn04-dk3.txt
- sp80's blob reader losing an overlapped body ← results/sp80-p5.txt
Read from AFAR, or keep the reading taken from off it.

## INSTRUMENTS

- `probe.py <game> <n>` — per-action diff from reset ← probe.py (⚠️ unguarded frame reads, dies on a GAME_OVER empty frame)
- `probe_re86.py` / `probe_sp80.py` — determinism + step-rate + census + board dump; copy for a new game
- `sp80_p*.py` → `results/sp80-p*.txt` — maps, BFS, fitters; **p11 is the deepcopy-BFS harness**, reusable on any replay-deterministic game
- `sweep_diff.py` — per-game sweep comparison with its own positive control
- `cover.py <game> <n>` / `swap.py <game> <n>` run directly = offline whole-game harnesses, print per-level actions
- **`copy.deepcopy(env)` is legal, faithful, ~2-3ms** ← results/sp80-p10.txt — O(1) BFS nodes; `env.reset()` costs ~10ms and dominates naive sweeps
- reset-with-zero-actions-after-a-transition = full GAME reset — usable as a TOOL to re-enter level 1 in-process ← results/sp80-p6.txt
- `probe_cn04.py` `live_at_level(game, level)` — live-env shim for process-random games
- `ARC_ACCT=out.jsonl` on compete.py = per-action rung accounting ← CLAUDE.md §Running it

## FREE vs COSTED:

- Offline probes and scripted runs: FREE — no scorecard impact ← CLAUDE.md session rules
- In-game action budgets are real: sp80 L1 = 30 actions & 5 shots/life · L2 = 45 ← results/sp80-p1.txt, sp80-p10.txt; re86 ~100/level ← results/breadth-recon.md §re86 FALLS
- Full sweep: ~90 min wall-clock — run in background, poll the log

## STOP

Per game: **3 hypothesis probes** that come back inert → write the findings into
`results/breadth-recon.md` (what was measured, run files named) and move to the next
queue item. ← author's decision; closed re86-L6, cn04-L2 and sp80-L2 cleanly.
Session end: if code changed, sweep + pytest + ask-before-commit; if recon-only,
commit the doc + artifacts (ask first). Never leave findings only in the chat.

## TRAPS (this machine):

- `rtk` rewrites pytest AND grep AND diff output — a failing run prints "No tests collected" exit 0; `command grep -q` exits 0 on zero matches; `diff` prints its own shape with no `<`/`>`. Redirect to a file and read the file; gate control flow on awk/python, never a grep exit ← CLAUDE.md §Running it + ~/.claude/RTK.md
- Background bash starts at `Desktop` and resets cwd on restart — `cd` into the repo in every backgrounded command ← ~/.claude memory (background_bash_cwd_reset)
- The engine returns EMPTY frames mid-level AND on GAME_OVER/level-up transitions — guard every `np.array(obs.frame)` (`cover.grid_of` is the pattern) ← cover.py grid_of docstring + results/sp80-probe8.txt
- **GAME_OVER is terminal at the engine**: without an `env.reset()` it stays GAME_OVER and hands back empty frames forever. `compete.play` does call it and carries on, charging the death exactly one action ← results/sp80-p17.txt + compete.py:1965-1972
- Windows console is cp1252 — non-ASCII `print()` crashes; keep probe output ASCII, or `PYTHONUTF8=1` ← ~/.claude memory (windows_console_cp1252_thai)
- **A probe that ran is not a probe that measured.** sp80's D1 probe answered "mapping intact" while testing nothing — the driver fired that round instead of walking, and its own first line said so. Put a positive control in the same invocation, and never write the assertion as an `or` chain that can accept the bug ← results/sp80-d1.txt

## RULES

- NEVER read/grep/list `environment_files/` — it is the answer key ← CLAUDE.md §The one rule
- NEVER `git add -A`; stage by name, commit with `git commit -- <paths>` ← CLAUDE.md §Git + memory (arc_agi3_competition)
- Ask before every commit ← CLAUDE.md §Git
- One change at a time; a claim needs the run that produced it, named ← CLAUDE.md §How a change is accepted
