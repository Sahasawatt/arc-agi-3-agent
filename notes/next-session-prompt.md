# ARC-AGI-3 breadth campaign — session brief (written 2026-08-06, after the sp80 night)

Repo: `Desktop\projects\arc-agi-3-agent` · python = `./.venv/Scripts/python.exe` ← author's decision (venv path, standing)

## GOAL

Clear ≥1 level in EVERY game. Standing: **6/17 games with a level, mean 5.116%**
(ls20 43.629 · re86 41.477 · m0r0 1.526 · cn04 0.233 · ar25 0.095 · cd82 0.008)
← results/sweep-cover2.log. **sp80 L1 is a KNOWN CLEAR offline** (`[4,4,4,5]`,
4 actions ← results/sp80-p6.txt) — not yet in the agent, so not yet on the board.

## GATE

Any code change to `compete.py`/`cover.py`/`discover.py`/`gate.py` = full 17-game sweep
before commit, per-game, no game loses a level ← CLAUDE.md §How a change is accepted:

```bash
./.venv/Scripts/python.exe compete.py > results/sweep-<name>.log 2>&1
```

← runs ~90 min ← the 2026-08-06 session's two sweeps

Values that must not move:
- ls20 **7/7** 43.629% `[23, 45, 99, 178, 292, 209, 526]` ← results/sweep-cover2.log
- re86 **5/8** 41.477% `[31, 56, 66, 80, 188]` ← results/sweep-cover2.log
- ar25 `[173]` · cn04 `[131]` · m0r0 `[53]` · cd82 `[1306]` ← results/sweep-cover2.log
- pytest: 219 passed, run as `./.venv/Scripts/python.exe -m pytest -q > file 2>&1` and READ THE FILE ← file-redirect rule ← CLAUDE.md §Running it (rtk trap)

Recon-only work (probes, board dumps, doc updates) needs no sweep ← CLAUDE.md §How a change is accepted.

## READ FIRST

`results/breadth-recon.md` §"sp80 OPENS" to end of file (written 2026-08-06
session 3): the sp80 mechanic, both transfer maps, and the closed/open list.
That file is the state of record; this brief only points.

## FIRST TASK

**Wire a sp80 discovery rung into the agent** so the known L1 clear lands on the
scorecard (6/17 → 7/17). The rung must DISCOVER legally, not replay the recipe:

- Mechanic (all measured ← results/breadth-recon.md §sp80): 1=up 2=down 3=left
  4=right step 4 · ACTION5 = control transfer, 5-shot magazine per life, 5th
  press = GAME_OVER · budget L1 = 30 actions (bar y0, ~2.13 cells/action) ·
  L1 win = fire with the 20-wide block at x-left=24 (any y — 9-position column
  ← results/sp80-p6.txt) · signature at reset: colour-9 20x4 block + colour-14
  full bar row + two colour-11 castles (census ← results/sp80-det.txt).
- Shape that fits the budgets: walk the home row, fire at ≤4 x-alignments per
  life (5th shot kills), GAME_OVER restarts the life for free at the same
  board. 12 x-positions / 4 shots ≈ 3 lives ≈ scoring cost, acceptable vs 0.
- Gate on a signature no other game shows at reset (re86's `cover.py` gating
  pattern ← cover.py) — candidate: exactly one 20x4 colour-9 blob + full
  colour-14 row 0 + colour-1 band y60-63.
- UNKNOWN — whether the same rung should also fire on sp80 L2+ (L2 is a
  measured wall ← below); after L1 falls, answering None hands the level to
  the generic rungs, which is the cover.py convention.
- Code change ⇒ full sweep + pytest + ask-before-commit.

Queue after it (do not start a second before the first is written up):
re86 L6 · cn04 L2 trigger · walls-during-planning (ar25) — dead lists below.

## DEAD LIST — measured refuted, do not re-derive:

sp80 (all 2026-08-06 session 3 ← results/breadth-recon.md §sp80, run files named there):
- L2 win within one life: NONE — BFS over the real engine, exhaustive: 39,328
  states, (board, ammo) key, depth 44 on the 45-action budget ← results/sp80-p11.txt
- L2 win clock-gated at stack-aligned candidates: NONE ← results/sp80-p15.txt
- L2 board varying with the L1 exit recipe: NO (byte-identical, 3 recipes) ← results/sp80-p16.txt
- Transfer legality clock- or route-dependence: NONE (position-pure) ← results/sp80-p14.txt
- Transfer rule closed forms REFUTED against the p12+p13 maps: Manhattan /
  Chebyshev / Euclidean radii, sum-diagonals, every 45° corner ray, all single
  half-planes and all cones over corner pairs (coefficients −3..3) ← results/sp80-fit.txt
- L2 transfer chain: 80-body ↔ block-2 ONLY; block-1 is NEVER a target, even
  fully overlapped ← results/sp80-p12.txt, sp80-p13.txt (full maps)
- 8-blocks are pass-through scenery: no push, no collect ← results/sp80-p5.txt
- ACTION6 (click) is a no-op on every object centre tried ← results/sp80-p2.txt
- probe.py crashes on sp80's GAME_OVER empty frame — it never probed ACTION6;
  guard every frame read (`cover.grid_of` pattern) ← results/sp80-probe8.txt tail

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

re86 general:
- "collection"/"consumption" readings taken while a shape sits on the thing are OCCLUSION until re-read from afar — this lied three separate times ← results/breadth-recon.md §session 2. Same trap re-confirmed on sp80 (blob detector loses an overlapped body) ← results/sp80-p5.txt

## INSTRUMENTS

- `probe.py <game> <n>` — per-action diff from reset ← probe.py (⚠️ unguarded frame reads, dies on sp80 GAME_OVER)
- `probe_re86.py` / `probe_sp80.py` — determinism + step-rate + census pattern
- sp80 probe family `sp80_p*.py` → `results/sp80-p*.txt` — maps, BFS, fitters; p11 = the deepcopy-BFS harness, reusable for any deterministic game
- **`copy.deepcopy(env)` is legal, faithful, ~2-3ms** ← results/sp80-p10.txt — O(1) BFS nodes; `env.reset()` costs ~10ms and dominates naive sweeps
- sp80 steps at **80,469/s** (19× re86) ← results/sp80-det.txt
- reset-with-zero-actions-after-a-transition = full GAME reset — usable as a TOOL to re-enter level 1 in-process ← results/sp80-p6.txt
- `probe_cn04.py` `live_at_level(game, level)` — live-env shim for process-random games ← probe_cn04.py docstring
- `cover.py re86 <n>` run directly = offline whole-game harness ← cover.py `__main__`
- `ARC_ACCT=out.jsonl` on compete.py = per-action rung accounting ← CLAUDE.md §Running it

## FREE vs COSTED:

- Offline probes and scripted runs: FREE — no scorecard impact ← CLAUDE.md session rules
- In-game action budgets are real: sp80 L1 = 30 actions & 5 shots/life · L2 = 45 ← results/sp80-p1.txt, sp80-p10.txt; re86 ~100/level ← results/breadth-recon.md §re86 FALLS
- Full sweep: ~90 min wall-clock — run in background, poll the log

## STOP

Per game: **3 hypothesis probes** that come back inert → write the findings into
`results/breadth-recon.md` (what was measured, run files named) and move to the next
queue item. ← author's decision; closed re86-L6, cn04-L2, and now sp80-L2 cleanly.
Session end: if code changed, sweep + pytest + ask-before-commit; if recon-only,
commit the doc + artifacts (ask first). Never leave findings only in the chat.

## TRAPS (this machine):

- `rtk` rewrites pytest AND grep output — a failing run prints "No tests collected" exit 0; `command grep -q` exits 0 on zero matches. Redirect to a file and read the file; gate control flow on awk/python, never a grep exit ← CLAUDE.md §Running it + ~/.claude/RTK.md
- Background bash starts at `Desktop` and resets cwd on restart — `cd` into the repo in every backgrounded command ← ~/.claude memory (background_bash_cwd_reset)
- The engine returns EMPTY frames mid-level AND on GAME_OVER/level-up transitions — guard every `np.array(obs.frame)` (`cover.grid_of` is the pattern) ← cover.py grid_of docstring + results/sp80-probe8.txt
- Windows console is cp1252 — non-ASCII `print()` crashes; keep probe output ASCII ← ~/.claude memory (windows_console_cp1252_thai)

## RULES

- NEVER read/grep/list `environment_files/` — it is the answer key ← CLAUDE.md §The one rule
- NEVER `git add -A`; stage by name, commit with `git commit -- <paths>` ← CLAUDE.md §Git + memory (arc_agi3_competition)
- Ask before every commit ← CLAUDE.md §Git
- One change at a time; a claim needs the run that produced it, named ← CLAUDE.md §How a change is accepted
