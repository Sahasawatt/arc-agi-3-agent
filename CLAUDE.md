# arc-agi-3-agent — working rules

An agent for ARC Prize 2026 (ARC-AGI-3). `README.md` is the findings log and is written to be
read by a stranger; this file is the operating manual for changing the code.

## Which line is ACTIVE (issue #5 — read this before anything below)

This repo holds TWO submission lines and everything below this section documents the
RETIRED one:

- **Active: the Duck harness line** (`duckv*/`). Base = duckv10 (anim bundle +
  Qwen3.8-27B-FP8, uncapped); every version patches notebook cells 6/8/12 only. The
  full run history with scores and why each landed there is `notes/LEDGER-all-runs.md`;
  decision tickets are `notes/wayfinder/MAP.md`; two runs are compared with
  `eval/rank_runs.py` (never by bare means — the same build spans public [2.82, 4.71]),
  and several runs of one build are averaged into one arm by `eval/pool_runs.py` first
  (`k` pooled runs are the arm `bm.n_passes = k` would build, at the same GPU cost).
  Submissions go from `Desktop/ARC-AGI-3-Kaggle-Starter` with `-k sahasawatt/taaf-duck-vNN`.
- **Retired: the algorithmic line** (root drivers + `kaggle/bundle.py`, hidden 0.11).
  Kept for reference; its per-game search chains live in `experiments/`. Do not extend it
  without reopening the decision in `notes/wayfinder/MAP.md`.

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
ARC_ACCT=out.jsonl uv run python compete.py ls20   # + action accounting, one line per action
```

`ARC_ACCT` writes, per executed action, which rung of `choose` emitted it (`{"i","lvl","src"}`)
plus event lines (`slid` / `chg` / `silentdeath` / `gameover`). Its invariants are its
verification: the per-level line counts must sum to the reported per-level actions, and two
runs must be byte-identical. This is how "where do level 4's 178 actions go" is answered
with a table instead of a theory — tune from it, never from a hunch.

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

- **An exhaustion proof inherits every scoping assumption of its root and its dropped children —
  and the cheapest refuter is an agent that does not know the level is "closed".** g50t L1 was
  "PROVEN unwinnable" by a single-life BFS (1,854 boards, frontier 0, GAME_OVER children dropped
  after one measured revert); a domain-blind online graph agent cleared it on its first eval by
  playing THROUGH resets — multi-life states the proof never enumerated. Fifth false exhaustion of
  the campaign; before banking any exhaustion, enumerate what the root and the drop policy exclude
  (lives, planes, hidden counters), and let a cheap generic agent take one swing at every "closed"
  level. 2026-08-18.

- **A fork policy is a HYPOTHESIS about ambiguity — measure whether the ambiguity is real before
  paying exponential rent on it.** sp80 L4's s13 reader forked ≤3 branches per twin-merge reading
  and reached 1.6M states (driver_forked ~2.6/expansion — the counter was the tell); one diagnostic
  session (sp80_s14) showed the transition is DETERMINISTIC (arrows move both twins in lockstep,
  fire resolves it), so every fork was inflation and the state set was polluted by wrong-model
  branches. Fork only after the dc22-style test: byte-identical states reached by different routes
  actually behaving differently. 2026-08-18.
- **Killing a chained background run child-first does nothing — the wrapper loop respawns it, and a
  `tasklist | tail` verification can show you only the survivors you expected to see.** The chain
  wrappers survived a Claude Code process restart, respawned 20GB of killed pythons within minutes,
  and the tail-truncated process list read as "all dead". Kill the wrapper bash tree FIRST, then
  the pythons, and verify with the FULL process list + a free-RAM number, never a tail. 2026-08-18.

- **sp80 L4 renders TWO colour-9 bodies at once (twin-merge after a control transfer), and an
  anomaly counter nothing gates on is a silent prune.** s12's one-driver reader dropped 56,477
  flagged children in 43k expansions — the search ran, checkpointed, and reported plausible numbers
  over a SUBGRAPH; the only tell was `driver_blob_count` climbing while every drop site said
  `continue`. Diagnosis (149 trajectories, 3 seeds): 120/120 anomalies were the same real game
  state — the (9,3) body pair both colour 9 — not occlusion. Fix shape: recover-or-FORK, never
  drop, and assert `forked == anomaly_count, dropped_hard == 0` in the FINAL line (`experiments/sp80_s13.py`).
  Corollary for every tracker here: a counter that can fire without changing control flow is a
  logging statement wearing a guard's name. 2026-08-17.

- **"Responds to the most actions" elects the wrong player on a board with a metronome —
  and NO landable fix exists yet (three designs measured dead).** sc25's faller wins the
  vote and the run wanders unplanned; but ar25's baseline level DEPENDS on its own
  metronome mis-winning early (blocked planning → novelty wander → walls learned), so the
  election fix alone loses ar25 (1,942/2,000 actions pacing two inert candidates on a
  wall-less map). Emission-counted walk cap: broke ls20 7/7→3/7. Arrival-counted: broke
  cd82+cn04 — their WINNING lines revisit one object 22 and 162 times vs ar25's 61, no
  separating threshold. Board-change discriminator: cd82's productive grind happens on a
  byte-identical frame — observationally equivalent to sterile pacing. Full account in
  `breadth-recon.md` §night 2; next lever = walls learned DURING planning. 2026-08-05.
- **CORRECTED (2026-08-11): the `KeyError: 'x'` is OURS, not cn04's.** The entry below
  read the crash as the game's own bug for three months. `compete.py:1965` attaches the
  coordinates with `clicker.set_data({...})` and the local wrapper never looks at the
  action object — it builds `ActionInput(id=action, data=data or {})` from its own `data`
  kwarg (`local_wrapper.py:234`), so every click this agent has ever made arrived with
  `data={}` and a game that reads `data['x']` answered KeyError. Measured both ways in one
  invocation, same coordinates: cn04 and bp35 DIE on `set_data` and are alive on
  `step(action, data={...})`; dc22 tolerates the empty dict and so clicked somewhere
  nobody chose (`results/click-probe.txt`). Consequences already measured: dc22's "63
  single clicks all answer zero changed cells" was 63 un-aimed clicks — aimed, exactly two
  of its 35 components respond, n=129 and n=97 (`results/dc22-click.txt`); bp35's whole
  second verb is the click (`results/breadth-recon.md` §bp35 fifth pass). **Fixed** —
  `compete.py` now sends the coordinates both ways and `kaggle/adapter.py`'s proxy `step`
  accepts the kwarg (without that the bundle breaks on the first click). The fix is
  measured **INERT on the sweep**: all 17 games identical to the digit, mean 6.320%
  (`results/sweep-click-aimed.log`, and `sweep_diff.py`'s positive control fails on
  purpose because nothing differs). It executes — dc22's own run emits 41 poke-clicks and
  survives — but `poke-click` picks the SMALLEST unprobed object first and dc22's two live
  targets are 40 and 47 cells, so the rung never reaches them. That ordering is the next
  lever, and it is its own gated change.
- **cn04's complex action kills the RUN when the click is malformed** (673/2,000 actions
  died mid-run). Guard in the play loop: a click answered with `obs=None` retires the
  clicker for the run, level-resets, plays on with the keyboard. Keep the guard — a click
  can still be answered with None — but it is a safety net, not evidence about the game.
- **One scattering action vetoes four clean directions.** re86's action 5 ((2,17), (±11,0)…)
  got a most_common direction anyway; that junk vector killed `coherent` (no inverse) and
  dragged `infer_step`'s gcd 3→1. `infer_dirs` now drops any action with ≥3 samples and no
  dominant vector (<0.6, the cn04 rotator-scatter law moved upstream); it lands in the
  extras/rotator path instead. Both fixes: canary cn04 [131] + ls20 7/7 intact.
- **re86's bottom row is a 100-ACTION-PER-LEVEL BUDGET, and a shape's own cells cannot be
  read off its colour.** The colour-15 row fills at `round(0.64 n)` of 64 cells and the game
  ends at 64; it refills on level-up, and a blocked move and the toggle both cost. Two
  unexplained deaths in an earlier session were this and a centre standing on a frame cell.
  Reading the shape: probe ONE DIRECTION PER AXIS and take what MOVES (a shape shifted along
  an arm hides that arm in its own trail -- one axis read a 52-cell plus as 32), never a
  colour mask (level 3 gives three shapes one colour, level 4 pairs a shape colour with a
  different box colour), and symmetrise, because an arm hanging off the board edge is
  measured SHORT. A group = all boxes of one COLOUR and consumes only under shapes WEARING
  it; swatches recolour on ANY CELL contact (not the centre -- routes must dodge each swatch
  dilated by the shape's own offsets, own-colour exempt); a box whose ring is under an arm
  is INVISIBLE to the ring detector (accumulate across frames, drop only on all-background);
  levels consume in WAVES. `cover.py`, `results/re86-*.txt`.
- **`env.reset()` with zero actions taken since the last transition performs a full GAME
  reset**, back to level 1 — it only scopes to the current level once a real action has been
  taken. Probes that reset immediately are measuring level 1 while reporting level 4.
- **A blocked move IS charged budget** (measured 20/20, with 20 walked presses as a control).
  An earlier README claimed the opposite; what actually shows a refusal is that the piece's
  position does not change.
  **NARROWED 2026-08-16: that is true of the MARKER and false of the rendered body.** On `re86`,
  a press refused by the level-6 WALL desyncs the shape's drawn arm from its own tracked marker
  by the attempted, denied displacement — marker frozen at (30,15), arm's row walking
  18 → 21 → 24 → 27 over five refused DOWNs — and the offset survives toggling to the other
  shape and back. It is cleared only by `reset()`, is capped at the shape's natural reach (one
  lattice step short of the wall), and is specific to colliding with the wall OBJECT: the
  board-edge clamp gives a normal non-accumulating shift. So inferring "refused" from the marker
  is sound, and inferring "nothing changed" from the FRAME is not — a diff taken across a refusal
  shows cells moving for a press that was denied (`results/re86-r5.txt`).
- **Track ids are reused across a level boundary.** Numbering carries on at a boundary so the
  old model's body ids are never handed out again, but it deliberately restarts on a level
  *reset*, where the same board yields the same ids and that is the right answer.
- **A model rebuilt on a new board knows less than the one it replaces.** Its `dirs`,
  `blocking` and `parts` all come back thin or empty, and it replaces a good model anyway.
  `build_model(prior=...)` exists for this; `test_compete.py` guards all three.
- **`hash()` of bytes is randomised per process.** Anything keyed on it makes every run a
  different experiment — pass the raw bytes.
- **A static colour-based walk map OVERCOUNTS reachability — it is a hypothesis generator, never an
  oracle** (2026-08-16, ka59 L2). The phase-pure component model built from "same background colour
  implies walkable" was right about phase-purity, right that box1 needs phase (1,2), and right about
  the region structure at level entry — and **wrong about reachability on a board that had been
  played**. It reported the piece and a box2 cell in the same component while the real router failed
  at 3,000 / 6,000 / 12,000 nodes. The dispositive instrument was **an exhaustive real BFS that
  targets nothing and just drains the queue**: it exhausted at **88 reachable cells against a 15,000
  cap**, with box2 inside the reachable region's bounding box and not among its cells. Likely
  mechanism, unproven: `ferry.find_cell()` calls the piece *"one cell, or a tight cluster"*, so if it
  effectively occupies more than one cell a landing needs more than one clear cell, and a point-model
  admits landings the engine refuses. **Verify any reachability claim with an exhaustive real search
  before acting on it; when a static model and a real router disagree, the model loses.**
- **ka59: FILLING A BOX IS REVERSIBLE, and a placed marker is a REUSABLE object** (2026-08-16).
  A dot clicked while the piece stands **inside a box** lands in that box wearing the boxes' own
  colour 4 — and it stays a swappable object: clicking its **3x3 halo** ejects it (the box cell goes
  colour 4 → colour 1, back to floor) and the marker lands on the piece's old cell, from where it can
  be clicked into a **different** box. Measured end to end: box3 filled with dot2 → ejected → walked
  to box2 → clicked → the same object now fills box2. **So "3 dots, one click each" is NOT the
  resource count** — that arithmetic ruled out a whole class of line and it is wrong.
  ⚠️ Narrow it exactly: a dot clicked onto **open floor** IS consumed (a second click on the vacated
  cell does nothing, and it reads as plain floor). *Same verb, opposite outcome, gated on where the
  piece stood.* And the reason this hid for months: **colour 4 is the box FRAMES' colour — 88
  permanent cells from level-2 entry** — so any raw colour-4 count reads frame pixels. Always
  subtract the entry baseline (`extra4 = colour4_now − colour4_at_entry`). No probe before this one
  tracked colour 4 at all.
- **A divergence check placed DOWNSTREAM of a dedup cannot detect a key that merges states —
  zero divergence under a merging key is the merge working, not evidence of soundness.** Measured
  2026-08-16 on two different games in one day. ar25 level 5: a board-derived key could not
  represent a **board-invisible selection state** (A5 has a period-3 cycle — `n mod 3 == 0` arrows
  drive the band, `== 1` arrows are inert, `== 2` arrows drive the piece), the `seen`-set collision
  dropped the node **before its successors were ever computed**, and the search reported
  `EXHAUSTED at 21 states, 0 divergence` — retracted. sp80 level 3: an offset re-key omitting three
  bodies' absolute positions reported **full exhaustion at depth 7 on a level whose win it was
  standing on**. In both cases every other control passed (deepcopy fidelity, death-reverts,
  mask-keeps-signal, keys-vs-raw-boards). **A search cannot audit its own state function from the
  inside.** The two things that have ever caught it: a **positive control on a win already
  possessed** (re-derive a known line blind, before trusting any null), and an outside challenge to
  a number that matches another number for no reason.
- **A BFS whose FRONTIER holds `deepcopy(env)` nodes is memory-bound long before it is
  time-bound, and it dies without producing a result.** Measured 2026-08-16 on sp80 level 3:
  **6.3 GB RSS at 12,000 nodes expanded**, with the frontier's own growth curve projecting a peak
  near 36,700 — i.e. **~20 GB before exhaustion**, on a 32 GB box also running other searches. The
  run does not finish; it dies partway having produced only its checkpoints, and it can swap the
  machine on the way. Deepcopy nodes are legal, faithful and ~3 ms, so they are right for
  *expansion* — they are wrong for *storage*. **Hold the frontier as ACTION PATHS and replay from
  the root when a node is popped** (at depth ~20 that is ~60 ms against ~3 ms, a ~20x slowdown that
  must be priced into any wall-clock estimate), or run **layer-by-layer**, keeping envs only for the
  layer being expanded and emitting the next layer as paths — memory then bounds to one layer and
  each node is replayed once rather than once per pop. `bfs_solve.py` and every ad-hoc probe in this
  repo store envs; check before launching anything expected to exceed a few thousand nodes.
- **EIGHT of the seventeen games answer some action with a MULTI-PLANE frame, and every reader
  here takes `np.array(obs.frame)[-1]`** (`framestack.py` → `results/framestack.txt`, 2026-08-16).
  sb26 returns **42 planes** on its run action, sp80 **22** on its fire, sc25 **22 on every one of
  its four verbs**, cd82 15, tu93 8, g50t 7, bp35 5, sk48 2; the other nine are single-plane
  throughout. Reading the last plane is **sound for play** — sb26 is cleared 8/8 through those 42
  planes, and wins come from `levels_completed`, never from a frame. It is a **keyhole for
  discovery**: any probe that pressed once and concluded "that action did nothing" measured the end
  of an animation. On sc25 the first press of any verb animates through `9 → 18 → 27 → 36` changed
  cells and **snaps back to entry**, so `f[-1]` is 0 and the press reads as a no-op — which is how a
  board-keyed BFS "exhausted" that game's keyboard graph at **one node** (`sc25_r1.py`, verdict
  void, kept as a worked example). Before concluding an action is inert on any game in the list,
  read every plane.
  **The sc25 rule, narrowed 2026-08-16: action-index 1 of every LIFE is absorbed — verb or click,
  it makes no difference — and everything from index 2 onward commits normally.** (An earlier
  reading of the same evidence said the trigger was "the board equals the entry frame"; the two are
  observationally identical until you press a verb at index 1 and then click a real target at index
  2, which commits.) **So every sc25 probe must open each life with a throwaway warmup press before
  its first real action.** `sc25_q16.py`'s 480-state closure survives only because it happens to do
  exactly that after each of its resets — accidentally, for an unrelated reason — which is why its
  historical run shows zero `MISMATCH` across 13 rebuilds. A new probe gets no such protection.
  **Absorption is sc25-ONLY** — measured across all seventeen games, every plain verb, pressed twice
  from a fresh reset (`absorb_r1.py` → `results/absorb-r1.txt`): sixteen commit on the first action,
  sc25 alone does not, and it absorbs after a death too (press-1 diff 0, press-2 diff 8). So no
  driver anywhere else is off by one.
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
- **"Never stood on" is permanent for a square the piece can never stand on.** The explorer
  hunts squares nobody has occupied; the inside of a shut goal box is walkable in every
  colour it is painted, so it is picked, walked to, pressed into, refused, and picked again
  — 598 of `ls20` level 5's planning rounds went to one such square. A press the piece did
  not move for is the evidence, and it expires when a display changes, which is exactly when
  a door can open.
- **Find the rung that emitted the action before theorising about it.** Four fixes aimed at
  a livelock from its symptoms were all measured neutral; tagging every `return` in `choose`
  and counting them found the real one in a single run.
- **The warm-up is a worst case, not a price.** Waiting a fixed 24 actions before the model
  is trusted costs `ls20` level 1 sixteen of the thirty-nine it spends on a goal box seven
  steps away. Planning can start as soon as the controls are *coherent* — four displacements
  on two perpendicular axes, opposite in pairs. Not sooner: `ar25` answers ACTION3 with right
  and ACTION4 with left, so a model built from a couple of presses can hold a sign backwards
  and lose the level outright. The convention cannot simply be assumed either — measured over
  nine games, the axis is right 8 times of 9 and the full mapping 7, and every game has its
  own step size.
- **A board marks what it does to the piece; read it instead of walking into it.** `ls20`
  draws a bar one cell thick and one step long beside every carrying cell, and the piece
  entering one is thrown away from the bar until something blocks it — all eight of level 5's
  cells come out of that rule exactly, before the first step. Filed as a first sighting rather
  than as the map: believed outright it costs level 4, because some marker-shaped object on
  those boards is not a carry.
- **A quarter turn states its whole cycle in one press.** Every shape change on `ls20` levels
  1, 2 and 3 is exactly a rotation (7 of 7 on level 2), so one observation gives four states
  and their order. Walked instead, the same cycle costs an entry per edge — and a life is 21
  actions.
- **A glyph match is exact, and the escape hatch that said otherwise is gone.** `matched`
  used to let a rejected display state un-reject every glyph the old lossy comparison might
  have confused it with — reasonable while collapsing runs of identical rows mapped
  `#.#/#.#/###` onto `#.#/###`, and wrong now that the normal form divides by the scale the
  glyph is drawn at. With it, the piece walks into a shut door wearing a glyph that plainly
  does not match.
- **The board says where the controls are, and using that is a separate problem from reading
  it.** Terrain is painted in one colour and so is most of what there is to walk onto; every
  changer on `ls20` is four or five colours packed into a block the size of the piece.
  Scanned on the piece's own lattice and measured against the board's background colour —
  not against `passable`, which grows until it contains the changer's own colours — that
  reads both of level 3's changers exactly and two of level 5's three, from one frame.
  Driving the walk with it costs level 4 (3 of 7), offering it as a guessed changer costs
  levels 3 and 4 (2 of 7), and a third wiring — reordering the discovery candidates so the
  many-coloured blocks go first, before any display has moved — is measured exactly inert
  (every per-level count identical), so none of it is in the code. A fourth wiring
  (2026-08-05) — ordering the blind never-stood sweep to prefer squares whose footprint
  reaches a many-coloured block, which only reorders a walk already being taken — costs
  level 5 fifty-eight actions (292 → 350, 43.629% → 42.871%, `ug-run94.txt`): the
  geographic nearest-first order beat the signed order on the exact board the signature
  names, because the sweep's order is part of the trajectory that finds everything else
  too. The reading is sound; all four cheap wirings are now measured dead, and any fifth
  attempt has to price in that ORDERING ITSELF is load-bearing on these boards.
- **A press executed inside a committed plan books nothing.** The standing-on-the-changer
  rungs call `gate.cycled()` per entry, and that counter is what forgets a changer that has
  stopped paying — the loop-breaker on a board with a wrong guess in the table. Baking the
  off/on pairs into a staged trip bypasses it: `ls20` level 4 looped on one such square for
  864 actions across 102 trips (98% dead within three actions) and lost the level, at every
  widening tried — whole trips and first-leg-with-presses both. A truncated stage commit
  ends at the first hop's route; the entries stay with the rungs that book them. Two fixes
  that were *not* the cause, both measured inert on the same loop (every count identical):
  filtering stage's routes against `refused`, and gating the commit on the legs being known.
  The whole-trip gate that holds is `known` AND a leg needing two or more entries — `known`
  alone re-costs level 3 its 55 actions through single-entry trips, `known` plus an
  interleaved-half requirement never fires (level 5's ink is one leg), and a stood-on check
  is vacuous because a watched edge implies the square was stood on.
- **The piece covers what it stands on, so two far-apart frames cannot tell a moving
  object from a static one the piece visited.** Level 6's crosses were read as patrolling
  from two frames 500 actions apart; they are static, and the "trail" of thirteen changer
  squares is the set of footprint-overlap positions — all real. A collider-attribution
  model built on the patrol reading measured empty (no mover ever detected), and its
  discriminator needed three exclusions (zero shift, lockstep shift, own colours) just to
  stop reading the piece's churn-renamed body parts as movers — the naive version cost
  levels 3-5 in one run. Level 6's real shape: changers IN the corridors, walking is
  pressing, `locked` reads 0 because the panel never holds still — the planner it needs is
  phase-counting BFS (see README), triggered by the corridor signature, never by `locked`.
- **CORRECTION (2026-07-30, measured per-move): level 6's changers DO patrol.** The
  "static crosses" verdict above was the second wrong reading, not the correction. Tracked
  one position per piece-move (`results/l6-circuits.txt`), three small objects walk
  deterministic period-8 tracks, advance exactly one lattice step per PIECE MOVE, and
  freeze while a press is refused. A press is the footprint overlapping a patroller AFTER
  the move — that model predicted every position and panel value of a 23-action scripted
  drive (`results/l6-driveB.txt`, `l6drive.py`). The collider-attribution failure above
  stands (its discriminator was wrong, and it cost levels 3-5); its conclusion does not.
  The full measured model — patrol tracks, ink alphabet `12→9→14→8→12` closing at level 6,
  door B a checked PASSAGE with door A behind it, death resetting the panel to
  `(14, ##./.##/#.#)` (which is what poisoned `Gate.legacy` with a phantom `12→14`) — is
  written up in `results/l6-model.md`. What a "corridor signature" was groping for is
  patrollers; `gate.track`/`mover_period`/`route_moving` are the measured replacements.
- **On a patrolled board the square-changer rungs are not idle — they are how presses
  get watched.** Their trips go to `gate.changers`, which on such a board are
  footprint-overlap positions rather than places, and they took 317 of level 6's 844
  actions; replacing them with "top the tank up instead" reads like removing pure waste
  and **loses level 6 outright** (5/7, 22.446%). The freed rounds went to the
  confirm-probe rung (40 → 329 actions) and bought nothing, because what a stuck round
  is short of is a watched EDGE, not fuel — and walking the corridors for a fictional
  destination still walks the corridors, which is where the presses are. Cutting the
  cost has to come from teaching the alphabet faster, not from stopping the walking.
- **Three traps from building the patrol planner, each measured before it was found.**
  (1) `Gate.observe` reuses `h` as a half index, so code later in the method that thinks
  `h` is the footprint height gets 0 or 1 — the mover crediting silently tested a 5x1
  footprint and every patroller lost its credit until the condition was print-traced.
  (2) The piece's own parts churn track ids past the `model.body` filter; a piece pacing
  back and forth earns its own fragments a patrol period and a press credit, and that
  phantom patroller glued to the piece blocks every BFS transition (the search explored
  ONE state). Exclude movers by footprint overlap, not by id. (3) On a ±step lattice, a
  patroller whose lap is aligned to the piece's own lattice can only ever share a
  square's parity, never its tick — a test board built that way proves the planner
  "broken" when the geometry makes the press physically impossible. Real patrollers sit
  off-lattice; test fixtures must too.
- **The HUD's colour-8 counter is LIVES REMAINING, four cells each, on every level.**
  Starved deliberately three times over: `8: 12` → `8: 8` → `8: 4` → GAME OVER → back to
  `8: 12` (`results/l7-lives.txt`), and it reads 12 at the start of levels 2, 4, 6 and 7,
  so it is the game's counter and not one level's. A life is 22 actions at 4 units of an
  84-unit bar. This matters because **the three deaths are not alike**: the first two put
  the panel back, the third is a game over that also clears `movers`, `mover_edges` and
  `mover_p` — the patrol model and the alphabet. `ls20` reaches one twice per run and the
  agent has never known which death it was about to take.
- **Keeping the alphabet across a game over LOSES level 6** (5/7, 22.419%). It reads like
  free money — the edges are the expensive half, the board is the same one, and the
  tracker reissues the same ids in the same order, which is the repo's own stated reason
  for restarting the numbering there. Measured, edges filed under the old ids plan presses
  that do not happen, and a wrong edge costs more than an absent one. Only `movers`'
  histories are safe to keep-or-drop cheaply; the edges must go with them.
- **`ls20` level 7's frame is a 40x40 WINDOW around the piece, not the board.** Terrain is
  destroyed behind the piece and created ahead of it as it walks, reversibly and with no
  hysteresis — and comparing consecutive frames at every shift, the best match is
  **dx=0, dy=0 at 94-95%**, so the world is not scrolling: what moves is the colour-5
  region, and the non-5 extent is `piece ± (-18, +21)` in both axes, clipped by the screen
  and the world's own walls. Every reader here treats the frame as the whole board, so the
  fog reads as wall, the piece looks boxed in by something that recedes as it walks, and
  every planning round sees a different board — **776 of level 7's 793 actions are `cand`**,
  which is what a board that will not hold still looks like from inside. Because the
  coordinates are fixed the windows STITCH: the fix is to remember every non-5 cell at the
  coordinates it was seen at and treat colour 5 as *unknown* rather than as wall — gated on
  the colour-5 region moving with the piece, because on levels 1-6 colour 5 IS the border.
  Stitched, the level **has a door**: `plates` on the composite finds `(28-34, 49-55)`
  asking `(8, #.#/##./.##)` — door B's exact ask on level 6 — which no window from the
  start can reach, so "no plates at all" was measuring the window and not the level. Built
  into the agent it works (world 1,165 → 2,839 cells, the plate visible in 777 of 789
  rounds), and **it is in the repo now**. The indicator is the unframed colour-12 L glyph at
  x3-8 y55-59, and **a plate does not need a box around it** — `plates` now also admits a
  shape standing ALONE against ONE background colour that reaches the frame's own edge (a
  shape on the floor is a thing to walk to; a shape in the void is a sign). That reads it as
  `(3-8, 55-60) ink=12 .#./.#./###`, and level 7 stops wandering: `cand` collapses from 853
  actions to 44 while `probe` (231), `stage1` (68), `moving-learn` (40), `turn-fuel` (26)
  and `cycle-last` (16) all start firing — the whole lock machinery, including the patrol
  planner. It costs `cd82` 179 actions (1,034 → 1,213, no level lost) and restricting the
  rule to shapes on the void does not recover them — measured, byte-identical.
  What took two attempts is the LATCH. Keying on colour 5 trading terrain both ways is an
  `ls20` fact dressed as a general one, and costs `cd82`, `m0r0` and `ar25` their only
  level each — measured on one sighting AND on three consecutive — with 1,981 of 2,000
  actions then spent wandering a board painted from the memory of a board redrawn under
  them. The question that separates them is not how MUCH changed but WHERE: the fog is
  everything outside a box around the piece, so the fog SET translates by exactly the
  piece's displacement while the content stays in world coordinates, and a board that
  merely redraws has no reason to agree with the piece's own step. Shift the candidate
  colour's mask by that step and ask whether it predicts the next frame better than leaving
  it put; over colours that reach the frame's edge, latched on two steps running. Measured:
  no game loses a level, levels 1-6 identical to the action, fires only on level 7 — where
  `near-fuel` goes 0 → 280 actions because the agent can finally see refills it is not
  standing next to. It buys **no points yet**, and it is the only route to any.
  **Both halves the level looked to lack were behind the window.** Using the stitched map
  as a stability oracle — a cell that comes back DIFFERENT while not under the piece is the
  board acting, not the window moving — level 7 has a PATROLLER (16 cells at x55-57, a
  five-cell cross of colours 0+1 at y=12/17/22/27/32, the same object as level 6's cross-2;
  "nothing patrols" came from an 18-action probe at the start, where the window reaches x40)
  and an INDICATOR (the colour-12 L glyph at x3-8 y55-60 turns a QUARTER TURN per press,
  four states and back — `turned()` already handles that, but `plates()` cannot see it
  because nothing frames it). Route to the patroller from a standing start, inside one life:
  `1,1,4,4,2,4,2,4,2,4` (the last is a carry) then `4,4,4`, then `1` up x54. Open: the door
  asks `(8, #.#/##./.##)` and the indicator normalises to `.#./###` and its rotations — the
  inks and the shapes both differ, so either a second display is still in the fog or that
  plate is not the lock — and it is NOT: driven to (29,45) and the frame dumped from there,
  x29-34 y50-55 reads colour 5 on the LIVE board with floor either side, so it is a HOLE
  with the colour-8 glyph floating in it, and the refusal measured there is the void, not a
  lock. `plates` saw a plate because on the stitched composite the unexplored interior was
  5 and its ring was 5 as well — **the fog framed itself**, which is a hazard the stitching
  creates and nothing yet guards. The glyph is the level's ask drawn as a picture. The same
  frame shows a **multi-coloured block at x11-12 y41-43 (colours 14, 8, 12)** — four or five
  colours in a piece-sized block is this game's signature for a changer, and standing on it
  at (9,40) **changes the indicator's INK, 12 -> 9, shape untouched** (`hud`'s `12: 6`
  becomes `9: 6`). So level 7 has both halves: the x55 patroller turns the SHAPE a quarter,
  this block walks the INK — along `12 -> 9 -> 14 -> 8 -> 12`, which `Gate.legacy` has held
  since level 3, so three presses reach the ask's ink with nothing new to learn. The SHAPE half is
  the colour-0 object beside it at x20-22 y41-43: from (19,40) the indicator goes
  `.#./.#./###` → `#.#/#.#/###`, five cells to seven, so it walks an ALPHABET rather than
  turning — and it is phase-dependent, so it is a patroller too. **Level 7 is fully
  accounted for and is level 6's machine with the parts further apart than one window.**
  What the agent still lacks is `movers`, which reads 0 for the whole
  level, so `route_moving` never runs. Two causes. **The stitch painted GHOSTS** — it
  remembered moving cells too, so a patroller out of view stayed drawn where it was last
  seen and the tracker followed a copy standing still; 25-61 objects tracked with full
  histories and not one period. Fixed: a cell that comes back DIFFERENT is marked dirty and
  never painted from memory (`withp` 0 → 1-3, every game unchanged). **The rest is
  IDENTITY**: a patroller is out of view most of the time and the tracker issues a new id
  every re-entry, so no id accumulates three laps and `_adopt` cannot help because it needs
  a period first. Keying on a SIGNATURE instead of an id — colour and size, and only where
  unambiguous in the frame — was measured and **costs level 5 a hundred actions and level 6
  eighteen** (40.503% → 36.884%): a signature unique in one frame and not the next flips the
  key back and forth and splits the history it meant to join. What DOES hold is patience —
  `identity.update`'s `max_missed` is 2, so a track dies two frames after the piece walks
  away from it, and on a windowed board out of view is not gone. Raising it to 200 while
  `windowed` takes level 7's `moving-learn` from 40 actions to **90** and its `probe` from
  673 to 317, with every game unchanged. Still not enough to clear it.
- **Learn mode may run on mute patrollers alone ONLY on a windowed board.** The guard
  `if not movers: return None` deadlocks level 7 — 1,034 of its 1,816 refusals had one to
  three period-carrying, never-watched patrollers on the board, and nothing ever presses
  one on purpose, so nothing ever becomes ready. Ungated, letting learn through **costs
  ls20 levels 5 AND 6** (4/7, 20.489%) — measured twice, once with `period` degenerating
  to 1 and once with the mute periods folded into the LCM correctly, identical to the
  digit: on a board with a ready mover coming, a learn trip to a mute one pre-empts the
  rungs that win the level. Gated on `gate.windowed` (set by the fog latch, which levels
  1-6 never trip) it is clean — every game unchanged, and level 7's `moving-learn` rises
  90 → 139. Level 7 still does not fall: 31 deaths in one run and 15 presses, so the trips
  are being planned and starved. The next axis is fuel-awareness of those learn trips, not
  more of them.
- **On a windowed board the refill detector UNLEARNS its refill colour.** `refills()`
  demands `seen_with > seen_without`, and on a board whose frame slides, the ring drops off
  the window's edge on nearly every walk — each exit counts against it, so after the first
  pickup the ratio tips and the tank goes back to empty: measured at `tank=[]` in **384 of
  level 7's 415** planning rounds, every learn trip planned with no fuel to weave. The
  trace now drops, on windowed boards only, `gone` entries whose square is FOG in the raw
  frame (slid out of view, not vanished) and `new` entries whose square was fog a step ago
  (slid in, not appeared) — `tank=[11]` goes 31 → 172 rounds and `fuels>0` 31 → 112, every
  game unchanged. The remaining decay was OCCLUSION — the piece walking past a ring hides
  it for a step with the clock flat, and each of those counted against the colour
  (with=58 vs without=68 by run's end, `ARC_RFDBG` since removed). A second windowed-only
  filter drops `gone` under the piece's own footprint when no draining colour rose (a
  pickup rises, so pickups still count): `tank=[11]` 172 → **196 of 345**, `fuels>0` → 118.
  Level 7 still does not fall — the remaining empty-tank rounds are early-level (before the
  first pickup ever happens) plus post-death windows, and the deaths themselves are what
  starve the learning. Measured next session: the trips DO weave now — `moving-learn` 139
  → 383 actions, presses 15 → 23, deaths 31 → 28 — and the post-death half of the decay is
  gone too: a refill colour is a property of the LEVEL, so `tank_colours` LATCHES it on the
  Gate once earned (windowed boards only; the Gate dies at the level boundary, so nothing
  leaks to the next board, and everywhere else `refills()`'s withdraw-on-doubt still guards
  against a false pickup). Deaths 28 → 22, presses → 31, `probe` 627 → 516, all four games
  unchanged to the digit. Full model: `results/l7-model.md`, probe `probe7.py`.
- **On level 7 a press is never credited to the thing pressed — and the square machinery
  already holds what the mover machinery cannot.** Traced per press (`ARC_CRDBG`): the
  shape changer by x20-22 sits at the SAME box in every sighting, so `mover_period` can
  never earn it a period (a cycle needs two distinct positions), `mover_at` answers None,
  and its `hist` is one tick stale at the press because the piece covers it — 8 of 8
  presses uncredited, `withh=0` in all 1,302 no-ready-mover refusals. The x55-57 patroller
  has a period but its press PHASE is exactly the occluded one, so it goes uncredited too.
  Meanwhile the ink block's fragments flicker size under the footprint's edge, which
  reads as "two positions" and earns a GHOST period — level 7's only mover credits (3 in
  one run, all to that fragment). But the walked presses (18 of 23) land in
  `gate.changers`/`gate.cycles` under their SQUARE — (9,40) ink, (19,40) shape — because
  both of level 7's changers are effectively square-pressable; what keeps that knowledge
  idle is the moving rung swallowing every round (30+ junk tracks keep `gate.movers`
  non-empty). Read back from a run (`ARC_L6=... ARC_L6LVL=6`), the squares hold the whole
  lock: the full ink ring `12→9→14→8→12` under (9,40), a growing shape alphabet under
  (19,40), and the x54 quarter-turn. The rung REORDER is in (windowed boards
  only, three edits in `choose`): the learn trip is stashed instead of returned, the probe
  rung yields whenever `turns_for` knows a square for a wrong half, and the stashed learn
  trip returns after `cycle-last`. Presses 31 → 68, `stage1` 13 → 276, `probe` 516 → 73,
  every other game and level unchanged to the digit — and the square records survive a
  game over, which wipes `mover_edges` twice a run. Level 7 still 6/7; deaths 24.
- **Level 7 is SOLVED by hand — a 71-action line completes it** (`results/l7-solution.txt`,
  run `results/l7-solve.txt`, full write-up in `results/l7-model.md` §SOLVED). The shape
  ring at (19,40) is six states and closed WITHOUT the ask; the exact ask is ring state
  `##./.##/#.#` + TWO quarter turns of the x55 patroller, and the door is the hole,
  entered by `down` from (29,45) once the panel is exactly `(8, #.#/##./.##)`. Load-
  bearing mechanics: presses at both (9,40)/(19,40) are one per RE-ENTRY (not phase-
  dependent — that earlier reading was re-entry semantics); the x55 patroller presses by
  CHASE (piece following it down its y12↔32 lap overlaps every tick, three presses in
  three actions — step off to the x49 column to stop at two); three refills are woven in
  ((14,45), (39,5) on a life's last action, (55-57,51-53)) and two carries used
  ((34,20)→(39,40), (39,35)→(29,30)). The agent still plays 6/7: no planner can compose
  square presses + phase-timed patroller presses + refills in one plan.
- **The composition IS plannable now — the wall is in-run DISCOVERY, one layer at a
  time** (all windowed-gated, every sweep clean, ls20 6/7 40.503% throughout; a first
  ungated version of the credit fix cost level 6 fifty actions — 209 → 259 — before it
  was gated). What was built, and what each unlock measured: `route_moving` folds the
  recorded SQUARE changers into its BFS (press per arrival), lets a marked door whose
  interior is unwalkable void be a goal (the hole — `footprints_touching` filters
  walkable, so its inside was never a gate), and runs with no ready mover when squares
  exist (1,198 rounds died on that guard with halves credited to period-less churned
  ids). The mover credit takes an age-1 sighting inflated a step when the pressed thing
  is covered. Trip marks are not refuted while every display is under fog (`raw5`), so a
  staged east leg can run open-loop. `moving-learn` jumps the square rungs when ANY
  wrong half is `exhausted` (`all` never fires — the ink half is always fixable), and
  before the learn trip a `fog-explore` rung walks to the nearest never-stood position
  bordering colour 5 — the unexplored set IS the fog on a windowed board (before it:
  598 learn-trip actions pressed west ghost fragments while the east stayed unseen).
  Where it stands, measured per run: fog-explore 346-514 actions, east-of-x44 only 22,
  (54,*) never pressed in-run — the east is reachable ONLY through the (34,20) carry,
  which `slides` cannot hypothesise (a +5,+20 warp, not a marked throw) and no route
  can aim at before it is walked once. `l7f.jsonl`
  analysis pattern: per-action rows carry `now`+`chg`, plan rows carry rung+cycles.
- **The discovery cascade, continued (2026-08-01, all windowed-gated, every sweep clean,
  ls20 still 6/7 40.503%).** Landed in order, each unlocking the next measurement:
  `fog-poke` presses the never-poked direction wherever the ROUTABLE map dead-ends
  (`gate.poked`, one action each) — that is what finally teaches the (34,20)→(39,40)
  carry (`redirects` now learns it in-run, slid 8 → 29-33); `fog-fuel` weaves a refill
  when the nearest frontier is beyond the tank (east is 20+ actions out on a 21-action
  life); `observe` keeps icons whose box is UNDER THE FOG (a display that slid out of
  view is not gone — dropping it blanked `state()` and made `exhausted` read
  closed-graph where it should read blind), which immediately exposed two more:
  a colour-5 "plate" (the fog framing itself) kept forever as a display — windowed
  boards now refuse ink-5 plates outright and purge kept ones — and the exhausted-yield
  keyed on `locked[0]`, which is often the refill-ring plate rather than the door
  (`ARC_YDBG` prints the per-round wrong/exhausted/path view that caught both).
  In-run state after all of it: ink ring, shape ring AND the x54 quarter squares all
  recorded live ((54,10..30) with presses at each), carry learned, deaths 31 → 18.
  Exploration-vs-press was then settled the same way the reorder settled probe-vs-stage:
  the yield fires only when `learning_path` is ALSO None (while an unwatched edge is
  reachable, the square rungs keep the round), and **the composition is verified
  plannable offline** — hand a Gate the full six-edge ring plus one x54 rotator and
  `path_for` returns `[((19,40),5), ((54,30),2)]`, the hand solution's exact press plan.
  The best stable state ends at: chg 150/run, stage1 290, deaths 22, still 6/7, ring
  incomplete in-run because presses spread across deaths and the x54 phase no-ops.
- **The union drift is FIXED — a display's off-pixels are state, not fog, and the fix
  is scoped to boxes that have CHANGED** (2026-08-01, sweep clean, every count of all
  four games identical). What three suppressor placements could never catch: the
  garble happens on the PRESS TICK with the box fully in view — paint-back has no
  notion of a window, so a glyph pixel that turned off (non-5 → 5, invisible to the
  dirty test) was repainted from memory in the same frame the press changed the rest
  (reproduced raw-vs-composite, `results/ug-repro.txt`; a box "re-entering reading
  range" is simply not when it happens, which is why the suppressor was byte-identical
  — it keyed on ticks that never coincide). The fix: `stitch(boxes=gate.displays)`
  records in-window 5s inside those boxes as KNOWN 5s, so painting them back is a
  no-op forever; `known`/`dirty` untouched, nothing outside the boxes changes. Two
  refinements are load-bearing: (1) scoping to `icons | displays` FLICKERS — the
  door's static ask-picture is partially fogged from positions the ±18/+21 test calls
  readable (its (32,53) pixel is visible at dx=13 and fogged at dx=18: the window is
  wall-clipped, not square), and recording those as OFF minted 85 phantom edges in one
  run; a STATIC plate is exactly what the paint-back stabilises. (2) A box that
  changes changes its INK before its shape, so it is in `displays` before the first
  union pixel can exist. Measured on level 7: junk shape-edges 85 → 0, `desperate`
  113 → 0, `cand` 182 → 55, deaths 22 → 11 — and the shape ring now assembles CLEAN,
  4 of 6 edges in one run. Still 6/7: the panel parks on `#.#/#.#/###`, a state with
  no outgoing edge in `cycles`, and nothing presses (19,40) again for 800 ticks —
  the next wall is the planner's, not perception's.
- **A transition reported against a stale reading can be a FOLD, and the test for it is
  ENTRIES of the pressed square, not the reading's age** (2026-08-01, the session after
  the one above; all sweeps clean, every game identical). Chain of measurements, each
  breaking the previous repair: (1) a death's panel reset folded into the next booked
  edge gave the ink square a phantom SHAPE edge that CLOSED the ring graph two real
  edges short — `exhausted` then read closed-graph and stopped pressing. A tick-age
  guard has an equality hole (a death on a blocked action leaves `ticks` flat), so the
  guard is `gate._fresh`, boxes read fresh THIS LIFE, cleared at both death sites in
  `compete`. (2) `exhausted` itself now also demands the graph be CLOSED (every seen
  state has an outgoing edge) — a state with none is a walk stopped mid-cycle, blind,
  not exhausted. (3) A walk-through press surfacing squares later folded TWO presses
  into one edge (`#.#/#.#/### -> .#./##./.##`, the `.##` state worn unread between) —
  requiring the old reading be age-1 rejects those but ALSO rejects every bounce whose
  off-square is a wall-clipped blind spot (2 booked edges over 80 bounces); the correct
  discriminator is **arrivals of the pressed square since the display's last fresh
  reading: one is one press however stale, two is a fold** (`_arrivals`/`_foldsafe` in
  `gate.observe`, windowed-gated). (4) On a windowed board a DISPLAY unreadable by
  `plates` is kept in `icons` even where the ±18/+21 geometry says readable — the
  window is wall-clipped, and dropping it emptied `state()` and blinded the lock
  machinery for most rounds (`cand` owned the level). (5) The ring changer is
  phase-gated: continuous oscillation walks the whole six-state ring one state per two
  MOVES with zero no-ops (`results/l7-hashpress.txt`), including changes landing on the
  step-OFF move — "press per re-entry" undercounts it, and a single bounce that no-ops
  is not a dead changer. `cycle-on-turn` commits three bounces while a wrong half is
  unplannable-but-open. Net state after all of it: cycles are finally CLEAN (4 real
  ring edges, zero junk, correct changer attribution) but the ring still does not
  close in-run — the two edges out of `#.#/#.#/###` and `.##/#.#/.#.` need a bounce
  session that persists at the changer, and the fuel rungs (`turn-fuel`/`near-fuel`)
  own those rounds instead. The remaining wall is round-ownership economics, not
  perception.
- **`refuel()` chose off the rarity shortlist, and a refill is rarely rare — the
  widening `stage`'s fuel has had all along.** Measured shape: twenty consecutive
  level-7 lives ran `stage1(4) → near-fuel(10) → turn-fuel(14) → cand(13) →
  desperate(2) → death`, the whole life walking between the far northern rings that
  survived `cands`' ranking while the ring three steps from the shape changer was
  cut — dying at (9,40) with `left=1`, zero presses, every time. Widened to every
  refill seen (sweep clean, deaths 23 → 20), the loop is gone; what replaces it in
  the late game is a `stage1`/`wander` single-action thrash — a plan issued and
  dropped every other action — which is the open thread (`ug-acct12.jsonl` /
  `l7-gate9.jsonl`, a=1950+). One reading of it was refuted (filtering ring-"doors"
  out of `locked` = byte-identical, reverted as inert), and the plan-drop log
  (`ARC_PDBG`) settled it with a zero: the plans were not dropped, they were SHORT —
  stage aiming fuel hops at rings **already eaten this life**. Rings respawn with
  the life but are spent within one, and nothing knew that. `gate.spent` (pickup
  positions per life, cleared on death, windowed-gated) now excludes them from
  `refuel`'s pool and `stage`'s fuel list — thrash gone, deaths 19, chg 52,
  `desperate` 93 → 52, `stage2` back. Sweep clean. A fuel TARGET is state that
  expires with the life, like a phase; the pool it is drawn from is state that
  survives it, like a period.
- **The ring's last two edges travel through a channel the fold guard rightly
  refuses, and the bounce cannot reach them because the lattice is bipartite**
  (`ARC_FDBG`, 15 refusals in a full run tell the whole story — see l7-model.md).
  The `#.#/#.#/###` press fires on WALK-THROUGHS (both missing edges consumed in
  one 2-arrival gap, `.##` worn unread between) and no-ops on bounces: the
  response is phase-gated, every closed walk on a 4-connected lattice is even, so
  a bounce session samples only half the phases and one born on the wrong parity
  no-ops until `cycled` hands off. A CARRY breaks the parity — that is why the
  walk-through presses. Six of a run's deaths happen wearing `#.#`: shape is the
  life's last errand. **RESOLVED (2026-08-03): the law is even-phase gating, and
  parity-walk + quarter-trip are in.** Press-from-`#.#`-class fires only on an
  even patroller phase; arrivals carry odd moves-since-death (bipartite lattice,
  death resets the lap); the flip is an odd-displacement carry — and the stored
  redirect offset is measured from the AIM cell, so odd carry = EVEN offset,
  which every confirmed redirect is. `parity-walk`/`parity-fuel` (parked-class
  trigger) unlock the ring full-circle in-run (`#.#` pressed 28x, chg 52 → 156);
  `quarter-trip`/`quarter-fuel` walk into the x55 lap (gate.lapmem — six target
  filters were each measured wrong before aiming true: fragments, death-churn,
  the piece's own column ghost vs `stood`, the invisible-wall unstood trap, the
  PIECE's lattice offset x≡4 mod 5, and avoid=refused) and now climb x54 through
  the patroller both directions — in the budget's last twenty actions. Sweep
  clean throughout. The RETURN leg is built (same day): `quarter-home` walks back
  to the changers when every display is unreadable, gated on `gate.qt_out` (set
  only by a real outbound leg — a 1-step wall-refused "trip" must not latch it);
  `ask_q` scans EVERY locked target (locked[0] is usually the ring plate, the
  ARC_YDBG lesson again); a lapmem-empty trip bootstraps to the carry landing
  FARTHEST from the changers (nearest goes north and learns nothing); trip
  routes carry persistent walls (tried minus sure — `refused` expires on display
  changes); the x54 lap-overlap squares are seeded as VIRTUAL ROTATORS in
  `gate.rotates` so `path_for` composes ring + quarters and STAGE — the only
  machinery that weaves multiple refills — owns the choreography (stage1 285 →
  368); and the trip tail CHASES along the lap axis away from home, which is
  what first sights the east refill ring into `seen`/tank. All sweep clean.
  The deaths-mid-trip theory then measured FALSE — all seventeen deaths are
  west, during ring work. The real chain (2026-08-04): rotator squares were
  invisible to `route_moving`'s press set (they lived in `rotates` alone) —
  folding them in dropped 1,680 "bfs exhausted" refusals to live plans, the
  `moving` rung went 0 → 188 actions, and the agent now walks to (29,45) twelve
  times a run wearing an unturned panel. The quarters themselves still never
  fire: the x54 entries are phase-dependent, the phase is UNKNOWABLE from the
  west within a life, so pressing must be counted reactively at execution — the
  chase rung + live overlap counter exist, x55 tracks now carry halves and
  measured periods (p=10), lapmem is line-clean, and the chase's TRIGGER is the
  one wrong piece: it keys on `qt_out` (set only by quarter-trip) while the
  east traversals belong to `moving`. The interceptor then landed and CLOSED
  THE LOOP (2026-08-04, all swept clean): play-loop plan-drop so the chase gets
  rounds, lap-span filters (it once chased the east ring's flicker — same
  column, wrong end), column-first steering (a whole chase ridden at x49, one
  column short of overlap), LEAD-the-target (equal speeds never close; aim two
  ticks ahead — the hand recipe), the occlusion-aware hit counter (the overlap
  that IS the press is the sighting perception loses — project forward), and
  live-validated demand (a standing demand paid itself at the wrong panel). One
  run's tail now executes the ENTIRE hand choreography: (8, ##./.##/#.#) rides
  the (34,20) carry at a=1925, two hits pay at a=1935/1942, the piece walks to
  (29,45)... and `down` refuses with the budget dying at 2,000. Last two walls:
  hit-count FIDELITY (a projected-box overlap is a count, not a confirmed
  press — read the panel between chase and door) and the CLOCK (the sequence
  first aligns at a~1900/2000 — fire the far-stone bootstrap in the first half;
  the ring is drivable from ~a900 and lapmem only needs one east sighting).
  ⚠️ Trap, measured: THE TRAJECTORY IS ENV-DEPENDENT — a run with
  ARC_RMDBG+ARC_L6 diverges from one without (chase 10 vs 0 on identical
  code); iterate under ONE fixed env set, never compare across sets. Levers ranked in l7-model.md; two more byte-identical
  hypotheses (ring-doors in `locked`, blind-spot bounce off-squares) are written
  up there as refuted — check before re-deriving either.
- **`ls20` level 7 FALLS (7/7, 43.629%) once the shape errand stops being routed to
  the INK square — and the bug was in the tie-break, not in any of the machinery.**
  Everything the level needs had been built and measured working on its own; what it
  waited on was a half nothing was pressing. `gate.changers` read
  `{(9,40): {0,1}, (19,40): {1}}` in **452 of 507 planning rounds** — a stale reading
  folded onto one of the ink square's entries credits it with the SHAPE half as well
  (the fold family, landing in `changers`, where `_foldsafe` does not reach) — and
  `changer_for` sorts the HALVES blind-first correctly but then takes the first square
  in **insertion order** claiming the winner. The ink square is learned first every
  life, so the phantom won every time: (9,40) arrived at **126 times to (19,40)'s 10**,
  120 of 127 display changes ink, `wander` spending all 90 of its rounds standing on
  it, 66 of 123 refusals there, and `changer_for` answering (9,40) in **424 of ~470**
  decisions — 68 of them with the SHAPE as the only wrong half (`ARC_TWDBG`). The
  shape ring therefore stalls at three edges, which is also the whole reason the
  X-sequencing latch measured inert: replayed offline against the run's own gate
  dumps the scan is correct, and `None` was the right answer for a table that cannot
  reach the ask. `Gate._square_for(h)` now picks, **on windowed boards only**, the
  square with the most WATCHED EDGES for that half — a phantom carries one, a real
  changer carries its cycle; ties keep insertion order and non-windowed boards are
  unchanged, so levels 1-6 and cd82/m0r0/ar25 come back identical to the digit while
  level 7 completes in 526 of its 2,000 actions. Two lessons worth more than the code:
  a claim about reachability EXPIRES with the equilibrium it was measured in (the
  "step-chain reaches `##./.##/#.#`" premise came from an 8-edge run and was false of
  the 3-edge one), and **a gate dump is a replayable oracle** — the scan was cleared
  of suspicion offline, in seconds, without spending a single live run.
- **The "six-state closed ring" was sampling HALF the changer's response — the
  shape graph is the ring x rotation composite, and the ask is IN it** (2026-08-02,
  sweep clean). `changer_for` now prefers the blind half on windowed boards
  (shape errands moved to the life's start), and the first run booked 8 shape
  edges: the ring 4 plus a chain of quarter-TURNED ring states — `.#./###/#..` is
  the exact CW quarter of `.#./##./.##`, and `#.#/.##/##.` is the ask minus one
  quarter, the hand solution's act-52 state. Some (19,40) presses STEP the ring,
  others TURN the glyph, phase-dependent. The ask may be reachable from (19,40)
  alone — no x55 chase, no (54,*) rotators. Missing: an edge INTO the ask (none
  booked), edges out of `###/#../###` and `#.#/#.#/###`. Next: let the square
  rungs keep exploring those two states' presses; the composition machinery is
  already downstream.
- **An engine refusal the frame does not show must be CONSUMED by the router, not
  merely remembered.** Fifty consecutive turn-walk legs died on their first step
  at (19,15)→(19,20) — the x19 gap is an unmarked wall, `refused` was fed on
  every blocked step and expired correctly on display changes, and no route ever
  read it. `bfs(avoid=...)` now exists (a refused square is not walked THROUGH
  but may be a GOAL — a door press aims at a square that refuses) and the
  turn-walk leg passes `refused`; sweep clean, (19,20)-drops 58 → 6, deaths 16,
  the refusal frontier moved south one wall at a time. Extending `avoid` into
  `routed()` — every walk route — **loses cd82 its only level (0/6)**: that level
  walks into squares that refused before any display exists, and with no display
  the refusal never expires — the m0r0 "stop walking to refused targets"
  measurement again, in a new place. Reverted, sweep restores. The turn-walk
  `avoid` stays because that rung only runs when something is `locked`, which
  requires a display, which is the expiry working — any future extension (stage
  legs) must carry the same display-exists guard. (Also a `verification-layers`
  case: the "zero drops in the endgame" reading came from a run BEFORE
  blind-half-first; the stored conclusion expired with the equilibrium it was
  measured on.)
- **A patroller nobody has watched is INVISIBLE to the planner, not unknown to it.**
  `route_moving` builds its patroller list from movers with a period **and a known half**;
  one with no half contributes nothing to `presses`, so walking over it is not modelled as
  a press and no plan can go and find out what it does. Measured: **183 of the 189** rounds
  level 6's learn planner gave up on had two to seven of them on the board, all carrying
  period 8 — the search was right that nothing it could see was unknown, and what it could
  see was not all of them. In learn mode they ARE the unknown press (read each against its
  own period, so the LCM does not have to cover them; same fuel guard, because a press the
  piece starves on teaches nothing). **570 → 285, 24.85% → 32.144%**, levels 1-5 identical
  to the action (`results/sweep-mute.log`). `stage1` 209 → **3**, `moving-learn` 82 → 154,
  deaths 6 → **1**. The lesson generalises past this board: when a search reports "nothing
  left to learn", ask what it is unable to represent before asking what it cannot afford.
- **Preferring to learn the half the DOOR wants is exactly inert.** The learn search
  returns the NEAREST unwatched press and will as happily walk off to learn a half that is
  already right, so a strict pass over the wanted halves before the general one reads like
  free direction. Every per-level count came back identical: the panel differs from a
  door's ask in **both** halves nearly all the time on this board, so the wanted set is
  every half and the strict pass IS the general one. A preference only steers where the
  thing preferred is sometimes a minority.
- **Identity is the LAP, and a track that churns strands the alphabet under the old id.**
  A patroller is invisible exactly when it is pressed — the piece covers it — so the id
  churns on the tick that matters. Level 6's 285-action run makes 85 presses, gains 51
  edges and ends holding **122 edges under 26 keys for three patrollers**, the gains
  arriving in six-action bursts six times over: the same six edges, relearned. Keeping
  edges across a GAME OVER lost the level (ids land on whatever comes next); within a life
  the lap is evidence — two objects on **two** of the same squares of a deterministic
  circuit are one object, two rather than one because a single shared square is a crossing.
  On earning a period a track inherits the halves and edges of the circuit it matches,
  copied not aliased so no reader changes, and a wrong adoption is refutable like any wrong
  edge. **285 → 265, 32.144% → 33.668%** (`results/sweep-adopt.log`).
  Then **265 → 209, 33.668% → 40.503%** by fixing two words of it: adoption was asked only
  on the reading that EARNS a period — never on the commoner one that inherits it, so a
  board that kills the piece adopted nothing for three laps after every death — and it
  compared a SNAPSHOT of the circuit taken at that instant, which holds whatever few phases
  had been sighted by then and never improved. Ask on every reading, accumulate the lap
  (a death moves a patroller back ALONG its track, not off it, so the union is across lives
  while `mover_at` stays within one). Watch the wrong number and you miss it: keys go only
  24 → 22, while the edges SPREAD, 151 → 221.
  Then **265 → 209, 33.668% → 40.503%** by fixing two words of it: adoption was asked only
  on the reading that EARNS a period — never on the commoner one that inherits it, so a
  board that kills the piece adopted nothing for three laps after every death — and it
  compared a SNAPSHOT of the circuit taken at that instant, which holds whatever few phases
  had been sighted by then and never improved. Ask on every reading, accumulate the lap
  (a death moves a patroller back ALONG its track, not off it, so the union is across lives
  while `mover_at` stays within one). Watch the wrong number and you will miss it: keys only
  go 24 → 22, while the edges SPREAD, 151 → 221.
- **A period belongs to the OBJECT and a phase belongs to the LIFE.** A death puts every
  patroller back at the start of its lap, so pre-death entries contradict post-death ones
  at the same phase and `mover_period` returns None for the three laps they take to age
  out — and while it is lost the LEARN planner is out too, so nothing teaches an edge
  deliberately and the alphabet is only picked up by walking. Clearing the histories there
  lost the level (5/7, 22.419%) because a period re-read off a handful of post-respawn
  frames can be wrong. Remembering the period and re-using it is not the same act: it is
  **checked** against this life's frames and never read off them, so they can refute it
  and can never invent one — and the phase map is built from this life's sightings alone,
  an unseen phase answering None exactly as the occluded stretch of a lap already does.
  **844 → 570, 23.528% → 24.85%**, levels 1-5 identical to the action
  (`results/sweep-phase.log`). Deaths 9 → 6, `stage1` 317 → 209.
- **`ARC_RMDBG`'s refusals were not attributed to a level, and reading them as one level's
  cost is how a number gets invented.** `route_moving` is called on every board with a
  tracked object and correctly refuses wherever nothing patrols, so its 588 `no ready
  movers` lines look like level 6's and are mostly levels 2-5. The lines carry `lvl=` now.
  Level 6's own split, measured: **723 refusals — 555 `bfs exhausted`, 168 no-ready-movers**,
  so the search failing is 77% of it and the periods are no longer the binding constraint.
  Both readings of the 555 tried so far are refuted: not fuel (no plan at a tank of 200),
  and not a phase map thinned by reading phases off one life — at the moment those searches
  give up the maps are **full for 83%** of the movers involved (`results/l6-fill.log`).
  189 of the 555 are the LEARN planner giving up — and asking each of those rounds what an
  INFINITE tank would do says the opposite of what that looked like: in **159 of the 189**
  it finds no unknown press either, so there is genuinely **nothing left to learn within
  reach**, at any tank size. Only 30 are affordability. So "make the learn trip affordable"
  is not the lever; what those rounds are short of is a panel VALUE they can get to. The
  derivation that followed — that the reachable set is CLOSED, so a death's reset to
  `(14, ##./.##/#.#)` is the only move that crosses the frontier — was written down as a
  hypothesis and is **refuted by the panel trace** (`ARC_L6`, 24 distinct states over the
  level): the level's five deepest shapes are first seen at a=1039, 1040, 1041, 1042, 1043
  — five consecutive actions, so five PRESSES, ending on door A's own glyph — and the
  deaths are at 679, 760, 837, 916, 993 and 1098. A death is not what opens the alphabet.
  What a death does introduce is exactly one state, `(14, ##./.##/#.#)` at the first one.
  So "nothing left to learn within reach" is a LOCAL condition of the piece's position,
  phase and panel value, not a permanent closure — the level walks the alphabet in a burst
  when it finally stands where it can, and what costs the ~400 actions is getting there.
- **A stuck round on the patrolled board is never short of FUEL, and the accounting that
  says otherwise is reading a tank size that is wrong.** Level 6's planner is handed a
  median of 19 actions of a 42-action tank against a 72-action recipe, five of its ten
  lives end with the square-changer rungs draining a full tank and starving, and not one
  of its 844 actions goes to a refuel rung — every arrow points at thirst. Asked per
  round instead of inferred — *would this door have a plan at a tank of 200?* — the
  answer is no in **121 of 121** rounds where both patrol planners came back empty
  (`results/l6-fueldbg3.log`), so a refuel rung gated on it never fires and the sweep is
  byte-identical. The earlier "the freed rounds bought nothing because what they are
  short of is an EDGE" was an inference from a lost level; this is the same conclusion
  measured directly, and it retires fuel as a lever on this board. Two things fell out
  of asking: `full` itself reads **21 in 72 of those 121 rounds** on a board whose tank
  is 42 — `drain` takes the most common fall over the last 20 steps and that flips 2↔4
  within the level — so any lever keyed on the tank is reading a number that is wrong
  most of the time; and a hypothesis about a resource is settled by handing the search an
  absurd amount of it, which costs one run and no code.
- **Routing walks around the recorded changer squares is inert — measured three times.**
  On stage hops, and again on probe/sweep walks (with the fallback kept), every per-level
  count came back identical: the shortest paths do not cross the *recorded entry squares*.
  The unmeant [chg] events mid-walk come from NEIGHBOURING positions whose 5x5 footprint
  overlaps the same cluster, which the entry-square set cannot name — an avoid set built
  from entry squares is the wrong shape for the thing being avoided. Widening it to a
  footprint neighbourhood is untried and risks sealing corridors.
- **The ink alphabet is a property of the game; the squares that write it are not.**
  `ls20` runs the same `12 -> 9 -> 14 -> 8` on levels 3 and 5, so ink transitions (ints)
  carry across levels in `Gate.legacy` — consulted only for a square already seen to move
  that half on this board, dropped by the phantom-edge refutation if a game disagrees with
  itself. Shapes must NOT carry: level 5 alone has two shape-changers walking two
  different graphs. Worth 306 -> 292 on level 5.
- **A blind probe budgeted one way is a death, and a death resets the panel the probes
  serve.** Twelve of fourteen lives lost in one accounted run ended `probe → desperate`;
  level 6 spent 65% of 1,708 actions in the probe rung and still did not fall (which also
  measured out doubling BUDGET — the block is structural). A blind probe now has to afford
  the walk back to a known refill. Only the blind ones: demanding it of targeted probes too
  costs level 3 twenty-six actions, spent by the rungs that fill the gap when a short,
  useful probe is refused.
- **On a carrying floor, a repeat-count cannot tell a livelock from an honest walk.** Every
  legitimate walk across such a board is dropped and re-planned several times (a carry moves
  the piece, the plan is rebuilt), so "the same goal planned N times without the display
  moving" is true of the door walk that WINS the level as well as of the loop that loses it
  — benching goals on that count was measured three ways and cost level 4 all three times.
  The discriminator would have to be progress (the route to the goal getting shorter across
  replans), not repetition. Related and also open: `slid` drops the plan on every carried
  step including the shortcuts the plan itself routed through (285 drops, 902 planned
  actions in one level-5 run), but both narrow keep-fixes turned level 4's cheap two-square
  bounces into thirty-step circuits — the bounce and the circuit are the same livelock at
  different plan lengths, and the cure has to attack the livelock, not the plan-dropping.
  Progress-based benching (route stops shortening) and teaching-aware benching (map stopped
  growing) were also measured and also cost level 4: what gets benched there is the goal box
  itself, and the walk that looks like a livelock toward it IS the discovery walk that finds
  the level's changer. No local signal separates the two — the next lever is structural:
  either model deaths inside the order search (make the display-reset a cost it can weigh),
  or execute a staged multi-leg plan as a unit instead of committing one leg and rediscovering
  the rest.

- **A wander round on a click game may click — but only once the walk is measured DEAD,
  and dead means fifty still rounds, not eight.** The `poke-click` rung (slice 1 of click
  support, `results/breadth-recon.md`) clicks the smallest unprobed object instead of
  pacing, keeps a box→cells-changed ledger, and re-clicks the loudest responder. Three
  gates were measured to find the safe one: ungated, ar25 and m0r0 each lose their only
  level and cd82 pays 593 actions (`sweep-click1.log`) — wander rounds are part of how a
  walk game's model gets built; frozen-8 still loses m0r0, whose 53-action solve presses
  into refused squares on purpose; planless-8 still loses it too. The discriminator is
  DURATION: dc22 parks over a thousand rounds at one square, so fifty consecutive
  planless still rounds fires there and can never fire inside m0r0's level. Sweep 2
  (`sweep-click2.log`): all 17 games identical to the digit, mean 2.662%. Two invariants
  are load-bearing: click rounds never enter `records` (a click that moves the piece
  would mint a None direction in `infer_dirs` and break every `dirs.get(value)` guard),
  and the trace row stays (the clock ticked). dc22 itself still needs click SEQUENCES —
  63 single clicks all eventually answer zero changed cells.

- **cn04 falls to the DOCK rung (1/6, 131 actions) — and every one of its nine measured
  iterations was a repo trap wearing a new coat.** The game: a crane claw with two red
  pads, a socket with the matching pair, and action 5 a quarter-turn rotator. A rotator
  is detectable because its "displacement" SCATTERS ((3,0)x2, (-3,3)x2, (0,-3)x1 over
  six presses) where a real direction repeats one vector — `infer_dirs` most_common
  hands it a duplicate of a real direction, so test consistency, not the model's word
  (`extras` in the play loop). The rung: identify the piece's marker blobs by MOTION
  (press the rotator once; what moved is yours), record the target constellation ONCE,
  then rotate until the tip pattern (offsets from centroid, sorted) matches and walk
  the single remaining vector. What each failed iteration taught, in order: greedy
  sum-of-nearest parks at a wrong local minimum (231 rounds, two tips courting one
  target); any window anchored on the piece's box lies (the crane's CABLE is the
  piece's own colour — the box stretches to y=0 after a rotation); a refused step gets
  chosen forever without `refused`; `model.parts` thins after cn04's 26 game-overs a
  run, so read the marker colour off the board (4-80 cells, ≥2 blobs); a colour that
  spins twice around without matching goes dead, or the rung courts terrain forever;
  independent nearest-blob tip binding collapses both tips onto one blob (bind 1:1,
  without replacement); and the finale — the piece's own body OCCLUDES a socket pad on
  the approach (`br-cn04-dk3.txt` line 6), which is the plates trap again, and the fix
  is the same law: keep the reading taken from off it (`dk["tgts"]`, stored at identify
  time, never re-read). The identity-starvation hypothesis was REFUTED before any of
  this was found: ARC_IDDBG measured player-in-shifts at 1,942 of 1,969 rounds, so the
  gate dump + one instrumented run beat four blind reruns. Two follow-ups from level 2,
  both measured (`sweep-spun.log` clean, every game identical, mean 2.676%): a rotator
  is a property of the GAME — `records` resets at the level boundary and took the
  scatter evidence with it, so the dock rung measured ZERO rounds on level 2 while its
  level-1 recipe sat ready; `spun` latches the verdict for the game's lifetime, the
  same law as `Gate.legacy`. And a colour whose blobs never move under the rotator is
  scenery — level 2 spent 1,858 rounds re-ref'ing colour 9's three static marks, a
  livelock the spins dead-switch could never reach (it only counts once tips exist);
  three silent identify-presses now kill the colour. Level 2 (recon'd through the
  in-run `ARC_FRAMED` frame dump — offline sims DESYNC on the empty frames the engine
  returns mid-run) is a JIGSAW of four pad-wearing shapes, and it taught two more
  measured rules: the marker cap is 200 cells, not 80 (twelve 3x3 pads = 108 cells,
  and the tighter cap left the rung with no candidate at all), and a matched pad pair
  the walk cannot REACH is a WRONG pair — the piece pressed one refused step for
  1,600 rounds (`br-cn04-l2d.txt`, move frozen at (3,-1.5)); five stalled rounds now
  veto the pair and the next match gets its turn. With all of it in, the rung walks
  the white piece clean across the board to ADJACENT — where the overlap model runs
  out: the level completes on shape INTERLOCK, not pad overlap, and |move|<1 never
  comes true for two solid shapes. Boundary-interlock matching is the next mechanic;
  the rotator + motion-identify + veto machinery all reuses. cn04 stays 1/6 [131]
  through every level-2 change (`br-cn04-l2c/d/e.txt`).

- **sp80's fifth shot MASKS the win, so a sweep that trusts its own fires books a false
  negative at exactly the answer.** The game hands the arrows to a different body on
  action 5 (`sp80-p8.txt`), and level 1 ends from one column of positions — all 108
  reachable positions fired, the nine wins are exactly x-left 24 (`sp80-p6.txt`). But the
  fifth press of action 5 in one life is a GAME_OVER, and the identical position that
  levels up on a fresh magazine dies silently as shot five (`sp80-p18.txt` A against its
  own control B). A sweep marking every fired position tested therefore crosses off the
  one that answers the level and can never return to it. `swap.py` counts shots, LEARNS
  the magazine size from the first death rather than assuming it, spends the last shot of
  a life deliberately as a one-action reset and puts that position back. The reset is
  cheap because `compete.play` answers GAME_OVER with a level reset and carries on
  (compete.py:1965-1972) — but the engine itself does NOT: without that `reset()` it stays
  GAME_OVER and hands back empty frames forever (`sp80-p17.txt`).
- **A signature function and a per-round tracker are not the same instrument even when
  they read the same feature.** `swap`'s life detector first re-read the band structure
  every round to spot the clock refilling. The clock is a full-width BAND only while it is
  FULL: one burnt cell makes its row mixed, the colour drops out of the reading on the very
  first action, the refill is never seen, and the magazine size stays unlearned for the
  whole run (`results/sp80-swap1.txt`, `mag=None`). The watched colours are latched from
  the level's first frame and counted whole thereafter (`sp80-swap2.txt`, `mag=4`).
- **A death is a RIGID TRANSLATION, so a frame pair that straddles one teaches the
  movement model a lie.** `swap` reads the arrow mapping from the driven body's own
  displacement between two frames. When a life ends on the clock the last action was a
  direction, and the block coming back to the level's start looks exactly like a move:
  measured, the arrow just pressed had its vector overwritten with a SIGN FLIP,
  `(0, 4) -> (0, -4)`, against an honest-answer control on the same setup that stayed
  clean (`results/sp80-d1.txt`), and a corrupt stride collapses the sweep's target set
  from 192 positions to 32. Ask whether the board was just put back BEFORE reading
  anything off the pair. The first probe written for this answered "mapping intact" and
  was measuring nothing — the driver FIRED that round instead of walking, which its own
  first line said (`emitted 5`); a positive control in the same invocation is what made
  the second run mean anything, and the first control was worthless besides because its
  assertion carried an `or` escape hatch that accepted the corruption it was testing for.
- **sp80 level 2 is a measured wall, not an unsearched one.** Exhaustive BFS over the real
  engine — 39,328 states, `(board, ammo)` as the visited key, depth 44 against the
  45-action budget, `deepcopy(env)` nodes — finds no win within one life
  (`results/sp80-p11.txt`). Transfer legality is position-pure (same position, different
  clocks and routes, same answer — `sp80-p14.txt`), the win is not clock-gated at the
  stack-aligned candidates (`sp80-p15.txt`), and the level-2 board is byte-identical for
  three different level-1 exit recipes (`sp80-p16.txt`). Two instrument lessons came free:
  `copy.deepcopy(env)` is legal, faithful and ~3ms (`sp80-p10.txt`), and an earlier null
  from the same search was the INSTRUMENT twice over — a depth cap below the budget, and
  fires-used missing from the visited key, because ammo is real hidden state.

- **wa30 is a CARRY puzzle, and its rung cost nine bugs of which almost all are one
  family: a reading taken from a PART of a thing, taken while something was standing on
  it, or taken with a detector that only works at reset.** The game: one action grabs the
  crate the piece is FACING (the heading is whichever way it last walked -- arriving
  beside a crate sideways refuses, which killed the first hand solve), a second press
  drops it, and a crate dropped over the frame slots in and consumes the frame interior
  beneath it for good; the level ends when that interior empties. What the rung got
  wrong, each with the run that showed it (`results/wa30-haul*.txt`): the displacement
  read from ONE COLOUR, when the piece's body is a 4x3 that swaps ends on a turn and so
  translates by the step MINUS ONE on any heading change; the piece found by
  flood-filling non-background, so a carried crate touching the frame swallowed the
  frame; the frame RE-DETECTED each round, when the first slotted crate stops its
  interior being one colour and `crates()` loses it entirely; its free slots read LIVE,
  when the piece covers what it stands on (the free count oscillated 20 -> 14 -> 12 ->
  14 -> 6 with nothing dropped); a refused probe not counted as ATTEMPTED, so a piece
  that starts under a crate presses UP forever; and finally a route that walked straight
  THROUGH crates. That last one is why fixing the eighth bug changed nothing -- a
  byte-identical run after a code change means the change never mattered, and reading
  the trace again with the filtering PRINTED rather than assumed showed the plan was
  right and the walk was not. 2026-08-08.

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

**Measured 2026-08-25 (`notes/R37-the-cap-decides-most-cells.md`): the cap is not an edge case,
it is the usual case.** `score = 100 * sum(done)/sum(1..total)` exactly wherever it binds, and no
action saved can move those cells. Two runs of one game at the same level count differ in score by
a median **2.16%** while differing in actions by **32.9%**; at different level counts, **100%**.
So "depth is everything" is stronger than it reads: for most game-runs depth is the ONLY thing,
and a lever that acts on efficiency or on behaviour is working on the remainder.

⚠️ **The SHARE in R37 was 77% (27 of 35) and it is now 55% (38 of 69)** -- not a correction of
that measurement but a consequence of resolving what it could not: R37 could only classify a cell
whose game had a derivable total, and 11 games had none, so 17 cells sat UNKNOWN and were excluded
from its denominator. The clock2x run's `summary.txt` prints `levels=<cleared>/<TOTAL>` per game,
settling all 25 at once (sum **183**, which is the figure CONTROL 5 had been assuming), and the
newly-decided cells are disproportionately raw-bound. Both readings are of the same world; the
77% describes the subset that could be anchored from fixtures alone.

`eval/score_shape.py` computes this from `eval/fixtures/*.json` alone -- no GPU slot, no Kaggle
call, no `~/Claude/arc-artifacts/` corpus, so it runs on any checkout. Seven controls gate it and
each is proven red on a mutation (9 mutations, one control green); a failing control prints no
numbers.

Two layers sit under the totals and BOTH are still graded, because replacing a derivation with a
reference is how a derivation stops being checked:

- `derive_totals` anchors a game whose score sits exactly on the cap (17 of 25 games).
- `bound_totals` brackets the rest: `score <= cap` holds in every cell, so
  `tri(total) <= 100 * tri(cleared) / score` per cell, tightest wins.
- `eval/fixtures/game-totals.json` is the EXTERNAL reference for all 25, and CONTROL 7 grades the
  other two against it -- every derived total exact (17 of 17), every bound containing (22 of 22).
  The tables downstream use the reference; the derivation is not replaced by it.

**`re86` is 8 levels**, which its bound had placed at 4..8 -- the largest single contributor to
per-game variance, and not a shallow game. Efficiency headroom over all 25 games now reads
**v10cal 4.71 -> 5.80**, meeting B20's independently-derived ceiling of 5.80 exactly.

`eval/abandoned_tokens.py` reads the one quantity no committed artifact carries: the
`note="tokens=N"` field on each game's `[finished]` line, which is larger than the `tokens=M`
that `summary.txt` totals and that the LEDGER's `Mtok` column reports. **N − M is generation that
returned but was never credited to an action** — ⚠️ NOT generation in flight, which was the first
reading and is refuted (B46 + `arc-agi-pub` #146) — and it is **9.1%–25.0% of every one of 17
runs** (B45, 2026-08-26) — so every `Mtok` and every tok/action figure derived from one counts only
the requests that came back. Individual games reach **100%**: four runs contain a game that took
**0 actions while generating 96 k–133 k tokens**, which is the mechanism under the zero-action
stalls this repo had recorded three times without one. It pulls logs through
`KaggleApi().kernels_logs(<slug>)` rather than `kernels output`, which writes the log last and dies
on the 250 MB `vllm-site-packages` directory; no GPU slot, no run. ⚠️ Two things it does not
establish: what `note=` counts is INFERRED (three checks in the module docstring, none decisive
alone), and no cap that would bound the leak has ever been measured — `v9` proved 768 fatal and
nothing between 768 and unbounded has run. `--check` grades the slug→run mapping by asserting the
parsed action totals equal the LEDGER's, 17 of 17 exactly; the assertion is the only thing tying a
slug to a row, since `kernels_logs` always returns a slug's LATEST version.

`--shape` answers **where** it is (B46). The `read timeout=` value on the one error line any run
prints splits cleanly into hangs at `analyzer_timeout=900` (8–35/run, and the action retries at
~901 s intervals) and the terminal cancellation at the wall (21–25/run = one per game). Pricing
both leaves a **median ~45% residual** on the shared runs and **98–99% on the solo runs, which log
zero hangs** — so the bulk is generation inside requests that SUCCEEDED, in an action that never
terminated. That is **`LOCAL_ANALYZER_TOOL_STEPS = '0'`**, which **has never been changed in any run of this
campaign** and is not the `LOCAL_ANALYZER_MAX_OUTPUT` that `v9` set to 768 and died on. ⚠️ **But a
cap on it may be unreachable**: the same loop carries `LOCAL_ANALYZER_YIELD_SECONDS = 60`, checked
at the top of every iteration, and at the measured 72–126 s per request that fires after ONE step —
14–25× before a cap of 12 could. Unresolved; the discriminator is `req_in_turn` in the banked usage
rows. LEDGER §*Can a TOOL_STEPS cap even bind*. ⚠️ The residual is an
estimate for 25-game runs and not for solo, and solo's zero hangs discriminates nothing (p = 0.49
under the shared per-action rate). ⚠️ It also flags a config that lies: **every run prints
`max_runtime_s_per_game=7920.0`, `clock2x` included, whose games ran 15,891 s** — that field is
pre-override, so read the run duration instead.

## Layout, in dependency order

One-off probe scripts (the `<game>_<tag>.py` instruments the README cites by bare
filename) live in `probes/` since 2026-08-20; the root holds only the engine, drivers,
tests, and active chain runners.

`perception` (frame → objects, HUD, glyph bitmaps) → `identity` (cross-frame tracking) →
`discover` (movement model by acting) → `plan` (BFS routing) / `gate` (locks and the squares
that change them) / `signals` (counters, clock, refills) → `compete` (the rules-legal play
loop).

Nine **whole-game drivers** hang off the play loop, all wired the same way: constructed once
if their own signature matches the reset frame, asked first every round, and answering None
the moment they run out of ideas so the rungs take the level back. `cover` drives the
framed-box family (re86, signature = a cell ringed by eight identical cells); `swap` drives
the control-transfer family (sp80, signature = a single-colour band on BOTH screen edges plus
a solid block narrower than the board); `haul` drives the carry family (wa30, signature = two
or more crates -- a rectangle with a uniform border and a single-colour interior -- with the
biggest strictly bigger than the rest and wearing an interior colour none of them has);
`maze` drives the fixed-pitch maze family (tu93, signature = EXACTLY one notched 3x3 window,
8 cells of one colour and the ninth a second); `dial` drives the combination-lock family
(tr87, signature = two 7-row station strips plus a top region whose (icon, block) pairs name
at least two of the stations); `skewer` drives the skewer family (sk48, signature = one live
2-row braid arm plus solid 4x4 blocks both inside the arm's room and outside it); `tape`
drives the stacked-rooms family (bp35, signature = a piece standing in a floor room at least
30 wide and 5 tall, three or more blocks above its ceiling, and a narrow floor column over
that ceiling) and is the first driver that drives with CLICKS, so it is built only where the
game has a complex action and is dropped if that clicker is ever retired; `bridge` drives
the toggle-and-bridge family (dc22, signature = a play area and a panel with different
background colours, two identically sized framed markers in the play area, and a panel
object big enough to be a button) and clicks as well, so it carries the same rule; `sorter`
drives the load-the-machine family (sb26, signature = a recipe row and a stock row wearing
the SAME colours in another order, with one slot mark per block -- the set equality is what
separates it from sk48, whose rows read the same shape with different colours) and finds the
action that RUNS the loaded machine by trying the plain ones rather than assuming it. Its
slot order is the MACHINE PATH, not a row scan: on a two-machine board the upper row runs
left to right with the whole lower row spliced in where the connecting pipe interrupts it —
found by exhausting all 5,040 slot assignments on level 2 with the insertion order pinned to
the recipe, which was sound only because A5 was first measured position-pure while A7 is an
UNDO (the game keeps an insertion stack, so a frame-deduped search would have merged states
that differ in history — the sp80 hidden-state law). The general form is a depth-first walk
of the machine TREE, and the splice point needs NO pipe detection at all: **a child machine
splices into the upper row at its own x-centroid** — level 2 (pipe at 34, machine centred
32), level 3 (two framed sub-boxes centred 22.5 and 40.5, each splicing only its own slots)
and level 4 (box centred 31.5, pipe invisible) all agree, and the earlier pipe reader had
misread level 4's two pre-loaded blocks as pipes, since a placed block IS a width-4 run in
the pipe's row. Three more rules came from level 4 (`results/sb26-l4-solve.txt`): a level
can open with blocks the GAME placed — they unwind with A7 (LIFO, back to their stock
holders) and are part of the puzzle, so the driver unwinds them at level entry, one press
per filled slot; the stock is read from its band's TOP edge, because a HOLLOW block (level
4's e44e, a real placeable block and the level's eighth) reads as two width-1 wall runs on
its interior rows and solid on its top edge — the assignment search that lacked it
exhausted 6,000 leaves for nothing, and a solid block of the same colour inside a machine
with no slot mark is a fixture that sits outside the order entirely. The run-button hunt
happens ONCE per level: trying the plain actions on every wrong full load loops forever,
because the last one tried is A7 and undoing one block re-opens the load branch (~2,000
actions of that measured on the first level-3 contact, `results/sb26-l3a.txt`). Levels
5-8 (all cleared 2026-08-13, WIN in 123 actions, `results/sb26-drive7.txt`) added the
DUPLICATE-RECIPE grammar: **a hollow block is a REFERENCE to the box wearing its frame
colour, and the recipe is a box's contents flattened in x order, references expanding
recursively** — one child called twice (L5, found by exhausting the 10,080 assignments,
`sb26-l5-dfs.txt`), fixtures inside expansions (L6), nesting two deep with per-RUN
hollowness — the stock holds solid 9s beside a hollow 9 (L7), and a doubled recipe row
meaning two unrollings of a SELF- or mutually-referencing box, matched as a PREFIX (L8,
two randomised variants). The reader finds boxes by wall pairs (width-1 run = wall,
width>=3 = fixture, colour-2 pair = slot), drops unpointed slotless boxes as frame
artifacts (they steal the root), and solves by enumerating block-to-slot assignments
against a pure-computation flatten — the engine is never stepped during the solve.

Five more drivers landed 2026-08-13/14 (agent-fleet nights, `results/breadth-recon.md`
§Agent-fleet), taking the roster to FOURTEEN. `ferry` (ka59) — the aimed click is a SWAP:
the piece teleports to the dot and the dot, recoloured to the boxes' own colour, lands on
the piece's old square, so standing inside a box when clicking PLACES the dot there;
movement is a 3-cell lattice step that checks only the LANDING cell, which is how a
"closed" box is entered at all. `claw` (cn04) — a 14-action playbook; the game's trap is
that the wrong handedness gives the identical tip-to-tip vector and renders the same
"docked" overlay without winning, so only `levels_completed` may be read as a win.
`mirror` (ar25) — the player and a MIRROR sprite move in lockstep (vertical same,
horizontal opposite; the old trap note about ACTION3 was reading the mirror), and the win
docks the MIRROR on the target with one axis exact. `twin` (m0r0) — two pieces on shared
controls in non-mirrored halves, win = one specific cell. `roller` (cd82) — a tumbling
roller whose same-action-twice is a NO-OP (the visible correlate of the "hidden state"
that made the generic engine burn 1,306 actions revisiting one object 22 times), ACTION5
paints the wedge FACING it, and on level 2 the HUD icons are a COLOUR SELECTOR for that
paint. Three games are now cleared END TO END: ls20 7/7, sb26 8/8, and tu93 9/9 — the
last via `maze.py`'s `SCRIPTS` table, one BFS-found line per level gated on that level's
hazard census. **The gate must match the eye that reads it**: level 8's gate written from
an agent's hand census failed in-driver because `notched_all` reads the board differently;
the shipped gates are the driver's own censuses, taken from an instrumented run.

`haul` gained three guards for wa30's level 2, whose board runs an AUTONOMOUS CONVEYOR
that parks one crate at a time on its own: a queued GRAB is dropped when its target crate
has moved or entered the frame (a plan made in the open matures into lifting what the
conveyor just delivered), `_slots` also checks the LIVE board rather than trusting the
driver's own book of drops, and a life boundary is detected by the count of crates outside
the frame going UP (the level dies on a 70-action clock and re-enters pristine, so every
book describes a board that no longer exists). The 68-action win line is proven at probe
level; the in-driver replay is still short.

Every signature is measured against all seventeen games at reset before its driver is wired,
which is the whole mechanism by which every other game stays byte-identical — nothing in the
wiring scopes a driver to one game. `sigs.py` runs every SHIPPED predicate over all
seventeen reset frames in one invocation (`results/sig-sweep.txt`) and is the check to run
before adding another. Two things it exists to enforce:

- **Measure the shipped predicate, not a candidate table.** `maze_sig.py` prints the
  candidate table a signature is chosen from, and both of its candidates fire on five games;
  `maze.signature`, the function actually wired in, is neither of them.
- **They are no longer all disjoint.** `cover`'s is the loose one — it fires on ar25, re86,
  bp35 and tr87 (ar25 is now settled by `mirror` being asked first), and only ever ENGAGES re86, because a driver handed a board it cannot read
  answers None on its first round. So the contested board is settled by CASCADE ORDER: `dial`
  is asked before `cover` in `compete.play`, and `sigs.py` fails if any contested game has a
  driver other than the one built for it asked first. Keep its `CASCADE` list equal to the
  wiring.

`play.py` is the older rewinding searcher and is **not** rules-legal — its numbers are
upper bounds from a dev mode the competition does not offer.

## The Kaggle bundle

`kaggle/bundle.py` builds `kaggle/my_agent.py` -- the single-file submission agent the
official starter kit splices into the notebook. Its MODULES list must name every driver
`compete` imports, in dependency order: `tape`/`bridge`/`sorter` landed 2026-08-13 and
`ferry`/`claw`/`mirror`/`twin`/`roller` on 2026-08-14, and a bundle built without a module
`compete` imports dies at exec with an ImportError on Kaggle, not locally -- which is
exactly what a forgotten `roller` did on the v8 build, caught only because the bundle was
exec'd locally before pushing. **Exec the built bundle before every push.** It is the single-file agent the
official starter kit splices into the Kaggle notebook. It embeds every module
(zlib+base64, registered in `sys.modules` BEFORE exec or dataclasses break) and runs
`compete.play` unchanged on a worker thread behind a queue-backed proxy env
(`kaggle/adapter.py`). Verified through the starter kit's harness: ls20 7/7 at 43.59%,
driver games identical to compete.py (`results/kaggle-ls20-v2.txt`, `kaggle-local*.txt`).
**Rebuild the bundle after any change to the modules it embeds** -- it is a build
artifact, never hand-edited.
⚠️ **That rule was violated and it cost real score** (2026-08-16): the committed bundle was
still embedding an OLD `mirror.py`, so the submission agent carried **none of ar25's `L3_LINE`
or `L4_LINE`** -- the two levels the campaign had just won (1/8 -> 4/8, 2.778% -> 27.778%). A
rebuild changed exactly one line, the `mirror` payload. **A stale bundle scores the old level
count with nothing in the logs to explain why**, so rebuild-then-exec is the gate, not a habit.
**`kaggle/bundle_check.py` is that gate**, and it must be run with the starter kit on the path:

```bash
PYTHONPATH=<starter>/vendor/ARC-AGI-3-Agents ./.venv/Scripts/python.exe kaggle/bundle_check.py
```

**The whole submission runs from the CLI — the "human steps" below are not required.** Measured
end to end 2026-08-17 from `Desktop\ARC-AGI-3-Kaggle-Starter` (its own venv, not the agent's):

```bash
PYTHONUTF8=1 ./.venv/Scripts/python.exe scripts/build_notebook.py
KAGGLE_API_TOKEN=$(cat .kaggle/access_token) ./.venv/Scripts/kaggle.exe kernels push -p notebooks/
KAGGLE_API_TOKEN=$(cat .kaggle/access_token) ./.venv/Scripts/kaggle.exe kernels status sahasawatt/arc-prize-2026-arc-agi-3-starter
```

Copy `kaggle/my_agent.py` onto `<starter>/agent/my_agent.py` first and **assert the sha matches** —
the starter held a 224,752-byte bundle while the repo's was 230,211, i.e. it was still carrying the
stale-mirror build. `PYTHONUTF8=1` is not optional: `build_notebook.py` and `play_local.py` print
non-ASCII and Windows stdout is cp1252, so without it they die on a UnicodeEncodeError that looks
like a build failure. **Never echo the token** — read it from the file straight into the CLI's env.
The kernel then RUNS for hours (~7.3h of play inside the sample's 8h envelope); `wait_for_kernel.py`
in the starter dir polls every 10 minutes and must be backgrounded **from the main thread**, since a
background job a subagent starts dies with that agent. ⚠️ A `COMPLETE` that comes back fast is the
silent-worker-death shape this file already documents — **read the kernel log before submitting.**

It asserts, in order: the bundle exec's in a fresh namespace · every module named in
`bundle.py`'s MODULES reaches `sys.modules` (the ImportError-on-Kaggle case a forgotten
`roller` caused on v8) · all fourteen drivers are present by name · the agent class exists ·
every driver still exposes `signature()`. Without the `PYTHONPATH` it fails at step 1 with
`ModuleNotFoundError: No module named 'agents'` -- an environment fault, not a bundle fault.
⚠️ **Do NOT name a standalone check `*_test.py` or `test_*.py`.** The first version of this file
was `kaggle_exec_test.py`; pytest collected it by NAME, imported it, hit its `SystemExit(1)`,
and answered with an INTERNALERROR that took the suite from **330 passed to "no tests ran"**.
The failure reads as an empty suite, not as a broken test. Use `*_check.py`, `probe_*.py`, or
the existing `<game>_<tag>.py` convention. Two mechanics that cost a run each: `GameAction(v)` raises
on every int (map `{int(a.value): a}`), and the adapter's per-round timeout must dwarf
the slowest planning round (level-6 rounds think for minutes; 120s killed the worker
mid-run and the random fallback's 5/7 looked like a logic bug).

**The submission is scored on 110 HIDDEN games, and the drivers are nearly irrelevant
there**: v1 (drivers + a 2,600-action cap) scored 0.11 and v7 (fourteen drivers) scored
0.10, against the official sample's ~1.56. The sample's shape is the lesson -- it sets
MAX_ACTIONS to infinity, bounds the whole run with an 8-hour clock, and spends thousands
of cheap actions per game while LEARNING which actions move frames. So `kaggle/adapter.py`
is now budgeted by CLOCKS, not actions: `play` gets a wall-time slice per game (short on
games no driver signature claims -- its wander earns nothing there), a cheap mop-up gets
the rest of a per-game clock, and a global clock drains the tail. The mop-up is a
STATE-AWARE bandit -- per (frame-hash, action) it tracks how often that action changed the
frame from THAT state, falling back to a per-action global prior, with the click as a
candidate aiming at a random cell. Unit-driven on a two-state stub, it learns per-state
(239 vs 67). The daily submission quota is **1**, not 5 -- the CLI swallows the reason and
prints a bare 400; the real message is in the response body.

The adapter budgets by CLOCKS, not actions (2026-08-13, after v1 scored 0.11 against
the sample's 1.56 cluster): `compete.play` gets PLAY_SECONDS of wall time per game (the
queue-get timeout shrinks with the slice, superseding the per-round-timeout rule above
for Kaggle runs -- long planner rounds are deliberately truncated there), then a mop-up
spends the rest until GAME_SECONDS ends the game via `is_done`, with RUN_SECONDS (8h)
draining the whole run's tail the way the official sample does. The mop-up is a
frame-change bandit, not uniform random: weight `(changes+1)/(tries+2)` per action,
click included as a candidate aiming at a random cell. Submission quota is **1/day per
team** -- the CLI's bare `400` hides that; the reason lives in the response body (dig it
out with a requests spy on `Session.send`).

## Git

Branch `master`, remote `Sahasawatt/arc-agi-3-agent` (public, MIT-0 — the competition requires
open source for prize eligibility). **Ask before every commit**, and stage files by name.

## The Kaggle submission pipeline (`kaggle/`)

`kaggle/bundle.py` embeds the agent's modules (zlib+base64) plus the adapter class from
`kaggle/adapter.py` into `kaggle/my_agent.py` — the ONE file the official starter kit
(`github.com/arcprize/ARC-AGI-3-Kaggle-Starter`) splices into the submission notebook.
The generated file is a build artifact: never hand-edit, rebuild after any module change.
The adapter runs `compete.play` UNCHANGED on a worker thread against a queue-backed proxy
environment, because the Kaggle framework inverts control (it calls `choose_action` per
move, play() drives an env). Mechanics that already bit: `GameAction(v)` raises on every
int (`.value` is a property — map by iteration); a module must be in `sys.modules` BEFORE
its source is exec'd (dataclasses resolve their module at class-creation); local
`play_local` SSL-fails on the SECOND game per process (first always works — Kaggle's
gateway is unaffected). Verification state lives in the brief's QUEUE item 0: levels 1-5
of ls20 replay through the pipe action-for-action; level 6 diverges, under measurement.


## Versioning (adopted 2026-08-25, user directive)

The vNN-per-experiment era ended at v24 (11 measured modifications, 0 above band; dead
builders live in git history — `git show 0757309^:duckv<N>/...` and earlier). From here:

- **major.minor** — `duckv25/` would be a MAJOR: a new lever family or architecture
  change (new model, new harness structure, new agent line). A MINOR (`v25.1`, `v25.2`)
  refines the same lever (parameter value, prompt wording, cadence) and lives in the
  SAME `duckv25/` dir — the builder takes the variant as an argument or a clearly-named
  cell-12 file per minor, one kernel per major (Kaggle versions give the minor history).
- Precedent: v23 → v23.1 (grid lines → + rendering-aid note) was already this shape,
  as two pushes of one kernel.
- Directory set kept alive: `duckmod/` (SRC_NB every builder reads), `duckv10/`
  (baseline; the build hidden draws would rerun), `duckv24/` (last measured lever),
  `localrig/` (local verification rig — README there), `duck/` (upstream June bundle,
  untracked reference).
- The discipline that stays regardless of numbering: builder self-check + in-kernel
  teeth proven red on mutation BEFORE any push; smoke before full; `eval/rank_runs.py`
  is the only scoreboard; results land in `notes/LEDGER-all-runs.md` the same day.
- ⚠️ **A builder's self-check must compare against the BASE the build claims, not against
  `SRC_NB`.** Every builder here renders from `duckmod/taaf-duck-mod.ipynb` and edits a few
  cells, so `assert out["cells"][N] == src["cells"][N]` for a cell the builder never touches
  is a tautology: it passes by construction and prints a reassuring line. duckv25 shipped
  that way (2026-08-25) — its cell 12 carried duckmod's 14,355-char patch block while every
  artifact called it "v10 exact", and a kernel was pushed and run on it. **Assert against
  `duckv10/taaf-duck-v10.ipynb` (or whatever the row names as the base), and name the block
  that must be ABSENT** — an equality test alone does not say which side is wrong.
- ⚠️ **In-kernel teeth do not cover the cells they do not touch.** duckv25's teeth were
  genuinely red 5/5 on the rendered setup command in cell 8, and cell 12 went untested in the
  same build. A green teeth report is evidence about its own subject and nothing else; state
  which cells it graded.
