# Breadth recon — why the 0/n games are 0/n (2026-08-05)

ls20 is at its architectural plateau (43.629%, ~96% of the 17-game mean); the next
points are in the thirteen games at 0/n. This is the first per-game diagnosis, all
measured (accounted runs `br-*.jsonl`, level-1 gate dumps, frame captures).

## The two structural gaps, named

1. **Complex actions are filtered out of existence.** `discover()` keeps only
   `not a.is_complex()`, so ACTION6 — the click — is never pressed, never modelled,
   never planned. Probed directly on `dc22`: `env.step(ACTION6, data={"x":24,"y":20})`
   **works and changes the board** (1 cell). Nine games are NEEDS_POINTER in
   `generalisation-probe.md`; none can score a level until clicks exist in the
   pipeline. This is the widest single unlock in the roster.
2. **The goal model is plates-and-doors only.** On `dc22`/`ka59` level 1 the whole
   gate machinery reads empty all run — `state=[]`, `marked=[]`, `tank=[]`, chg 0-1
   over 2,000 actions. These levels are other genres entirely; nothing in `choose`
   can even represent their win condition. `cand` rarity-walking is the only goal
   generator that fires, and it does not win them.

## Per-game evidence

| game | L1 accounting (2,000 actions) | reading |
|---|---|---|
| cn04 | cand 1493 · wander 507 · chg 0 · 26 gameovers | goal invisible to the gate; 15x15 piece |
| dc22 | **wander 1982** · refused **1,861/1,980** · 9 positions | piece boxed in a pocket; the game is CLICK-driven. Frame: right panel displays target shapes (red cap, blue cap), left panel holds materials — a build-the-picture genre. Walking is nearly irrelevant |
| ka59 | cand 1491 · probe 258 · **slid 491** · 20 gameovers · 56 positions | carry-heavy transport genre: two rooms with square slots, a purple gate, piece tied to a ring marker. No plates anywhere |

Frames: `frames/dc22/000.png`, `frames/ka59/000.png` (read them — one look answers
what genre a level is faster than any accounting).

## What was tried and already refuted this same night (do not re-derive)

- Tuning ls20 further: heading-gate loses level 7 outright; signature-ordered blind
  sweep costs level 5 fifty-eight actions. Both reverted (`l7-model.md` §Tuning pass,
  CLAUDE.md fourth-wiring entry). Ordering itself is load-bearing.

## The build order the evidence supports

1. **Click discovery** (biggest surface: 9 NEEDS_POINTER games + dc22).
   Graph-paper precedent (arxiv 2512.24156): stratify candidate clicks by segment
   size/morphology/colour salience instead of sweeping 64x64; OPINE precedent
   (arxiv 2607.01531): pick the click that most constrains the world model.
   Minimum first slice: during discovery, click each DISTINCT OBJECT once (rarest
   colour first), record what changed, and let `choose` fall back to "click the
   object whose last click changed the board" when no walk-plan exists.
   **Slice 1 is IMPLEMENTED (2026-08-05, same night): the `poke-click` rung** — a
   wander round on a game with a complex action clicks the smallest unprobed
   object's centre instead of pacing (`poked` box→cells-changed ledger, loudest
   responder re-clicked once all are probed, reset per level). Click rounds are
   kept OUT of `records` — a click that happens to move the piece would let
   `infer_dirs` mint a direction under action None and silently break every
   `dirs.get(value)` guard — while the trace row stays in because the clock
   ticked. Keyboard-only games never enter the branch by construction. Suite
   green; dc22 + ls20 regression measurement pending, then the 17-game sweep.
   **Sweep 1 (`sweep-click1.log`) FAILED the gate**: ls20 identical to the digit
   and dc22's probes measured real (63 clicks, every object eventually answering
   zero — the level needs click SEQUENCES, not single clicks), but ar25 and m0r0
   each lost their only level and cd82 paid 593 actions — on a walk-driven board
   the wander rounds are part of how the model gets built, and clicking through
   them starves it. The fix in the tree: **the frozen gate** — poke-click fires
   only after the piece has not moved for eight consecutive rounds (dc22's shape:
   nine positions in two thousand actions; a walking game never trips it while
   walking works). Reset with the board at each level boundary. Canary runs
   (ar25/m0r0/cd82/dc22): ar25 restored [173], **cd82 IMPROVED past its baseline
   (1213 → 809 actions, 0.01% → 0.022%)** — clicking when genuinely stuck helps
   that game — but m0r0 still lost its level (`br-m0r0-f8.txt`): its 53-action
   solve presses into refused squares ON PURPOSE, the piece is still while a plan
   is in flight, and the plain frozen count climbs through that choreography. Gate
   v3 in the tree: frozen counts only PLAN-LESS rounds (a round with a plan is
   never evidence the walk is dead). Canary rerun: m0r0 STILL lost at planless-8
   (a blocked press with no plan is that game's normal model-building), and the
   v2-only cd82 gain (809) went with it — the discriminator is DURATION, not
   plan-ness alone: dc22 parks >1,000 rounds at one square, m0r0's whole level is
   53 actions. **Gate v4 = fifty consecutive planless still rounds**: all four
   canaries clean — m0r0 [53], ar25 [173], cd82 [1213] to the digit, dc22
   unchanged (its unlock is slice 2, click sequences). Sweep 2 pending.
2. **Goal discovery for plateless boards** (cn04/ka59-class): the win condition has
   to be hypothesised from what a gameover/level-up correlates with. Needs a
   per-death ledger (what did the piece touch on the death tick?) before any rule
   can be written.
3. Only then the remaining MAZE_LIKE 0/n (re86, sc25, sp80 — walls never found:
   discovery's blocked-move sampling starves; see discovery.md §why no walls).

## dc22 level 1, hand-probed to a wall (2026-08-05, slice-2 recon)

Every cheap hypothesis about dc22's level 1 is now measured dead, offline:

- **Clicks are INERT on this level** — 6 floor/panel spots, all 20 object centers,
  double-clicks on 8 targets, and click-piece-then-click-destination pairs: zero
  play-area cells changed, ever. The "1 cell changed" the poke-click ledger recorded
  is a **HUD tick at row y=63** that advances one pixel every second action of any
  kind — the board never answered anything. (Slice 1's re-click policy was chasing
  that tick; harmless, but the ledger must exclude the HUD row.)
- **The keyboard works fine** — up/down/left/right move the 2x2 colour-14 piece by
  its step of 2 — but the piece's room is **sealed**: all nine positions of the 3x3
  room probed in all four directions, no exit. Pressing into the checkered wall
  eight times: nothing. A full snake tour of all nine cells: zero cells outside the
  room changed.
- Board reading (frame `frames/dc22/000.png`): left side is four machine-boxes
  (blue block, yellow-dot box, red bar, checkered pad, green piece box), right
  panel displays a red cap above a blue cap. The genre still looks like
  build-the-target, but the lever that starts it is none of: walking out, clicking
  anything once or twice, or dragging.

Open: what a human actually does first on this level. `play.py` (keyboard-only
sweeps) was set on it as the next probe; if its rewind search also finds nothing,
the level's first move is something no current probe can express, and dc22 goes to
the back of the queue behind ka59 goal discovery.

## ka59 level 1: the gameover is a TIMER, and the level is the purple bar (2026-08-05)

Per-death ledger over 4,000 random offline actions: deaths land at steps **99, 199,
299, 399, 499 — every 100 actions exactly**, wherever the piece stands. ka59's
gameover is a countdown, not a hazard — row y=63 is the bar (its colour-0 fill is
also why a naive "find the colour-0 piece" scan returns the whole bottom row; mask
row 63 before locating). A life is 100 actions; random play scores 30 deaths and 0
level-ups in 3,000.

Position census from the competition run (56 distinct positions, 2,000 actions):
the piece has **never been right of the purple bar** (colour 15, x33-38 y21-41).

The full offline dissection (2026-08-05, all rules-legal, probe scripts deleted
after use — rebuild from this note):

- **The map, read off the colour matrix** (rows 20-43): left room x9-23, right
  room x39-53. Between them a colour-2 wall block (x24-32) AND the colour-15 bar
  (x33-38), both full height — EXCEPT a 3-row corridor at y30-32 through the
  colour-2 wall. The grey dot (colour 5) sits in a ring at (27-29,30-32) INSIDE
  that corridor; the piece's own identical ring is at (18-20,30-32). Hollow
  colour-4 square slots: left (10-14,32-36), right (44-48,26-30).
- **Kick mechanic**: walking into the grey dot FLINGS it east down the corridor,
  over the bar, landing at **(43,31) — invariant** across every approach angle and
  row tried. It lands outside the right slot (interior 45-47,27-29) and nothing
  can reach it there. The corridor is the only access to the grey, and it runs
  west→east, so east is the only kick the geometry allows.
- **Clicks are inert on this level too**: a 440-point full-grid click sweep
  changed zero cells. (Second game in a row — dc22 the same. The click counter at
  row 63 there is the timer bar here; both games' HUD rows must be masked.)
- **The keyboard state space is TINY and winless**: BFS with frame-dedup (HUD row
  masked) exhausts at **74 reachable states, no level-up**, 296 expansions.
  Salient-click augmentation adds zero new states.
- **Timer facts**: death at exactly step 100 regardless of position; parking
  inside the left slot, either ring, or at the bar face until expiry all die.
- Piece movement: step 3 with jump-cells (22→28 in one press through the ring) —
  the `slid` events of the competition run.

Open hypotheses, in order: (a) the win needs BOTH dots slotted and the grey's
fixed landing means some OTHER actor must move it the last 3 cells — is there a
second kickable thing, or does the RIGHT room have its own corridor the stitched
map has not seen? (b) a state counter invisible in the frame (bump-repeat probe
was clean at 4 spots but false-positived at 2 — redo with a piece-trail mask);
(c) the 74-state graph is level-1-complete and the win is time-EXTENDED (survive
several timers?) — refutable by replaying the 74 states across two timer cycles.

## The campaign frame (new goal 2026-08-05: clear a level in EVERY game)

Standing: ls20 7/7 · ar25 1/8 · m0r0 1/6 · cd82 1/6 · **13 games at 0/n**.
Ordering by evidence: games whose level 1 the machinery can already act on
(MAZE_LIKE with walls found) first; click-driven and goal-opaque games behind
them. ka59 and dc22 both turned out goal-opaque WITH inert clicks — the next
recon targets are **cn04, re86, sc25, sp80** (MAZE_LIKE, walls-not-found class:
discovery's blocked-move sampling starves, a perception-side fix, not a puzzle).

## cn04 level 2 is a JIGSAW — the dock rung's overlap model runs out (2026-08-05, late)

Board (`frames/cn04/L2-real.png`, captured in-run via the new `ARC_FRAMED` dump —
offline sims DESYNC on the empty frames the engine returns mid-run, so recon
boards this way): four shapes on orange — white hook, green L, yellow blob, blue
U — each wearing 3x3 red pads, twelve pads in all. Three rung defects were found
and fixed against live dumps, each measured: the 80-cell marker cap excluded the
only marker colour (108 cells of red — now 200); a colour whose blobs never move
under the rotator re-ref'd forever (1,858 rounds on three static marks — three
silent identify-presses now kill it); and a geometrically matched pad pair the
walk cannot REACH stalled the piece on one refused step for 1,600 rounds (five
stalled rounds now veto the pair and the next match gets its turn).

With all three in, the rung does everything its model allows: identifies the
white piece's two pads by motion, walks the board (move 33 → 3), arrives
ADJACENT to the green shape's matching pair — and stops, because the level is
not pad-overlap, it is shape INTERLOCK: the pads mark where bodies join, the
completion condition is the jigsaw fit, and |move|<1 never becomes true for two
solid shapes. The next mechanic to build is boundary-interlock matching (shape
complementarity + the offset that mates them), reusing the same rotator +
motion-identify + veto machinery. cn04 stays 1/6 [131] throughout — the L2 work
freed 1,800 wasted rounds but cannot finish the level under the overlap model.

## Rules-legal note

All of tonight's probes ran offline against the local engine (`capture.py`, direct
`env.step`) — no scorecard consequence. `environment_files/` was never read.

## cn04 level 1: MECHANIC CRACKED by hand — the in-run wiring is blocked on identity (2026-08-05)

The game read off one frame + four probes: a white crane claw (its CABLE is the
piece's own colour — any bounding box stretches to y=0 after a rotation) wearing
two red pads, a socket wearing two red squares, **action 5 = rotate a quarter**
(4-cycle verified; its "displacement" scatters — (3,0)x2, (-3,3)x2, (0,-3)x1 over
six presses — which is how `infer_dirs` hands a rotator a real-looking direction,
a duplicate of action 4's). **Level 1 falls in 13-14 actions**: rotate until the
tip constellation (offsets from centroid, sorted) matches the target pattern,
then walk the single remaining vector; the offline sim
(motion-identified tips: press the rotator once, the blobs that moved are yours)
cleared it at 13, one faster than the hand line.

The in-run `dock` rung was built and measured through SIX iterations, each fixing
a real defect (greedy sum-of-nearest parks at a wrong minimum 231 rounds;
box-anchored tip scans lose the tips in half the orientations; refused steps get
chosen forever; `model.parts` thins after game-overs; rotate-loops need a
dead-colour kill switch) — and still fires only 83-104 of 2,000 rounds, because
**track identity does not survive cn04's 26 game-overs a run**: every reset
reissues track ids, `model.player` goes stale, `shifts` stop matching it, and
both the rotator-scatter test and the parts trigger starve. That identity repair
is the real prerequisite, it is a perception-layer change with blast radius over
every game, and the rung was REVERTED rather than shipped inert (repo rule: a
change that buys nothing measurable does not stay).

What survives for the next session: the sim recipe above (rebuild from this
note), the rotator-scatter discriminator, and the target — fix player-identity
across game overs FIRST (cheap oracle: `model.player in shifts` rate per run),
then re-land the dock rung unchanged.

## cn04 FALLS IN-RUN — the dock rung lands on iteration nine (2026-08-05, later)

`cn04 1/6 [131] 0.233%` — the fifth game with a scored level, and the first new
score the breadth campaign has bought. The final defect was the repo's oldest
trap in a new coat: the claw's own body OCCLUDES a socket pad on the approach
(the live blob list dropped to one target against two tips at the exact round
the match was about to pay — `br-cn04-dk3.txt`), and the fix is `Gate.observe`'s
own law applied to the rung: record the target constellation once at identify
time (`dk["tgts"]`) and never re-read it from the frame. Full nine-iteration
history with every measurement in CLAUDE.md's dock entry. The
identity-starvation hypothesis from the previous session block is REFUTED
(ARC_IDDBG: player-in-shifts 1,942/1,969) — strike that prerequisite; the rung
needed no identity repair, it needed occlusion-proof targets. Canary + 17-game sweep BOTH CLEAN
(`sweep-dock2.log`): cn04 1/6 [131] confirmed, every level-holder identical to the
digit (ls20 7/7 43.629%, ar25 [173], m0r0 [53], cd82 [1213]), mean 2.662% →
**2.676%**. One crash on the way: the dock plan's rotator action has no direction,
and `trajectory`'s `step_to` KeyError'd on it at game fifteen of the first sweep —
an action outside `model.dirs` now predicts in place.

## The engine is random ACROSS processes, and the shim is the only door to level 2 (2026-08-05, night)

Two facts that reshape all future probing, both measured:

- **Determinism is per-process.** Twin envs in one process diverge zero frames over
  twin action streams; re-reset is identical. But a 131-action prefix that cleared
  cn04 level 1 in the process that recorded it does NOT clear it in a fresh process
  — layouts/dynamics reseed per process. Replay-based probing is dead on arrival;
  every offline experiment must win its own way to the state it wants to study.
- **`probe_cn04.py` (committed) is the door**: a pass-through env shim that lets
  `compete.play` itself win level 1 — the dock rung wins on every layout — and
  raises out with the LIVE env the moment the level falls. Smoke-tested: hands back
  a live level-2 state in one command.

Level-2 interlock status: on a second independent layout the dock walk again drives
the white piece to body CONTACT with the target shape and stalls there — the
completion is a jigsaw fit, side x orientation unknown. Next session's first
experiment: the 4x4 trial matrix (rotate x4 · approach N/S/E/W · bump in) from the
shim's live state, with game-overs tolerated (a game over is a level reset back to
the level-2 start, not a loss of the state).

## cn04 level 2: the trial matrices rule out the cheap mates (2026-08-05, later night)

Two live-state matrices through `probe_cn04.py`'s shim, ~500 actions of evidence:

- **cn04 has the 100-action TIMER too** — deaths land at spent=100/200/300/400
  exactly, the same clock ka59 wears (its level-1 "26 gameovers a run" was the
  clock all along). Every level-2 attempt is a 100-action window.
- **Shapes OVERLAP freely** — the piece walks through the green shape's interior
  from any side; there is no collision. The dock stall at move=(3,-1.5) was
  therefore never a wall: the .5 components mean the pad lattices are OFF-GRID by
  a half-step, unreachable by walking — the same half-step the level-1 sim closed
  with its final two ROTATES.
- **4 orientations x 4 sides bump matrix: no glue. Rotate-bump weave at 7 contact
  spots including dead centre: no glue.** White x green with body-level contact is
  not the completion condition.

What remains for the solver session: measure the tip layout in all four
orientations relative to the piece centroid (they differ by rotation offsets that
include the half-steps), then solve orientation x position so the tips land
EXACTLY on a target pad pair — and if white x green exact-overlap still refuses,
the pairing itself is wrong (try yellow's and blue's pads as targets; twelve pads
across four shapes admit many pairings). The machinery to execute any solved
plan — shim, motion-identify, goto with sidestep, rotate weave — is all in this
file and `probe_cn04.py`.

## cn04 level 2, the night's last eliminations: EXACT overlap and click-select (2026-08-05, close)

The orientation-layout solver worked end to end: staged in an empty pocket, tips
motion-identified clean, all four orientation layouts measured exact (two tips,
rotation offsets carrying the half-steps), ten targets, and the lattice-parity
solve found exactly TWO reachable placements — both landing the white tips
PRECISELY on the yellow shape's pad pair. Both executed to the exact cell
(goto=ok, piece at P to the decimal) — **no completion**. Exact tip-on-pad
overlap is now eliminated along with adjacency, body contact, all orientations,
and rotate weaves.

Click-select eliminated too: clicking a shape then pressing a key still moves
WHITE (blue trial explicit). One anomaly worth chasing: cn04's own game code
raised `KeyError: 'x'` inside `perform_action` on some clicks — its complex
action may want a different data schema than dc22's `{"x","y"}`; read the
arcengine action contract before the next click experiment.

Remaining hypothesis space for the solver session: the white x green pairing
(off-lattice for walking — but every shape's lattice offset differs, and the
half-step lives in ROTATION offsets: rotate-at-P sequences can reach positions
walking cannot); pads may pair by SHAPE-piece identity (white's pads to green's,
yellow's to blue's — an assembly ORDER); or the mover changes after a correct
first mate. The full toolkit to test any of these is committed: `probe_cn04.py`
shim, motion-identify, orientation-layout measurement, the lattice-parity
solver, goto with sidestep.

## The walls-not-found class opens: two perception fixes, measured (2026-08-05, night 2)

Build-order item 3 (re86/sc25/sp80) turned out to be TWO defects stacked at the
very front of the pipeline, each caught by instrumenting a live run (`ARC_MDBG`
prints the model every 25 planning rounds — committed, opt-in):

1. **Player election votes for a metronome** (`br-sc25-md.txt`): sc25 has a
   component that falls (0,2) on EVERY action — all four buttons, ~130 shifts
   each. `infer_player` voted by shift count alone, elected the faller, its four
   identical "directions" can never pass `coherent`, and the run wandered its
   whole 2,000-action budget unplanned while the real piece (colour 9) lost the
   election. Fix: a steerable piece's displacement DEPENDS on the action — rank
   by (has ≥2 distinct modal vectors, votes). Single-mode candidates still rank
   by votes among themselves, so early warmup behaves exactly as before.
2. **One scattering action vetoes four clean directions** (`br-re86-fix.txt`):
   re86's actions 1-4 read a clean (0,±3)/(±3,0) — but action 5 scatters
   ((2,17), (-11,0), (11,0), ...), `infer_dirs` handed it most_common anyway,
   and that one junk vector both vetoed `coherent` (no inverse exists) and
   dragged `infer_step`'s gcd from 3 to 1 — the discovery table's "re86 step=1"
   was this bug, not the game. Fix: cn04's rotator-scatter law moved UPSTREAM
   into `infer_dirs` — ≥3 samples with no dominant vector (<0.6) = no direction
   at all; the action lands in the extras/rotator path instead.

After both (`br-sc25-fix.txt`, `br-re86-sc.txt`, `br-sp80-fix.txt`): sc25
elects the real piece; re86 reaches coherent with clean dirs and step 3; sp80
is coherent the whole run with step 4. Canaries hold: cn04 1/6 [131], ls20 7/7
43.629% — the scatter law's original home still works fed from upstream.

**Only the scatter fix LANDED.** The 17-game sweep caught the election fix
costing ar25 its level (0/8; bisect: pre-fix code reproduces [173], player-fix
alone reproduces the loss — `br-ar25-bisectA/B.txt`), and the reason is a
lesson bigger than the fix: **ar25's baseline level depends on electing the
WRONG player early.** The election table (`br-ar25-el.txt`, `ARC_EDBG`) shows a
second metronome — c=11, one mode, most votes until ~i=900 — whose incoherent
model BLOCKS planning, which forces the novelty wander, which is what meets
walls ([10]) — so that when the real piece finally outvotes it, planning starts
on a map that has terrain. Elect the right piece from round 25 and the cand
rung plans immediately on a wall-less map: `ar25-acct.jsonl` shows 1,942 of
2,000 actions pacing between two inert candidates, every move succeeding, and a
terrain model that never sees a failed move learns no walls, ever.

A walk cap was built to close that hole (two cand/desperate plans per object
per level, fuel exempt, counter on the Gate so it dies at the boundary) and it
proved BOTH claims: with election-fix + cap, ar25 went **2/8 [127, 1375]** —
faster on level 1 than the metronome accident and through level 2 for the first
time — but the sweep broke ls20 7/7→3/7, cn04 →0/6, cd82 →0/6
(`sweep-walkcap.log`): the v1 cap counted plan EMISSIONS, and a plan that is
interrupted and re-emitted (redirects, refusals — ls20 level 4's whole
personality) burns its object's budget without ever proving the object inert.

**v2 (arrival-counted) and v3 (board-change discriminator) are now BOTH
measured dead too — do not re-derive any of this:**

- v2, arrivals only (final action of an object walk popping; dropped plans cost
  nothing): ls20 7/7 restored, ar25 [127] — but cd82 lost its level and cn04
  0/6 even after the click-guard (below). The demand measurement
  (`ARC_NOCAP`+`ARC_WDBG` on the baseline trajectories, `br-*-wdbg.txt`)
  explains why no threshold exists: cd82's WINNING line completes 22 walks to
  one object and cn04's completes 162, while ar25's sterile pacing tops out at
  61 — the ranges overlap, so every cap either starves a real solve or misses
  the disease.
- v3, "did the board change since the last arrival at this object?"
  (`br-*-wdbg2.txt`): cd82's 21 repeat-arrivals are ALL on a byte-identical
  full frame — its productive grind is invisible in the pixels — while ar25's
  arrivals show a static goal-neighborhood but a churning frame (its second
  metronome falls forever). Productive revisits and sterile pacing are
  observationally equivalent at the frame level. A scope by "game has a
  clicker" also fails: ar25 has one too (`br-*-capv2d.txt`).
- Election reverted with the pair; the defect-contract test
  (`test_metronome_still_outvotes_the_piece`) stands. The counter survives as a
  measurement instrument only (`ARC_WDBG`; `Gate.walked`, read by nothing).
  The next lever worth building is exploration that learns walls DURING
  planning (a probe budget woven into successful walks), not a better election
  and not a cand cap.

**Kept from the chase, both net-positive:** (1) the CLICK-DEATH GUARD — cn04's
own `step()` raises `KeyError: 'x'` on its complex action, so ONE poke-click
killed the whole run at the engine (673/2,000 actions, `br-cn04-capv2b.txt`);
a click that comes back `obs=None` now retires the clicker for the run, resets
the level, and plays on with the keyboard. (2) `ARC_EDBG` — the election-table
dump that found the second metronome.

**Walls stratum, still open for re86/sp80** — with clean models both games
still end `block=[]` after 2,000 actions and no goal rung fires. sc25 has a
third disease of its own: it is a SLIDER — displacement magnitude varies per
press ((-2,0), (-4,0), (6,0) under one action), so even the true piece's modal
vector is unstable. Slide mechanics (press-until-stop, wall detection by
terminal cell) are a different model shape, parked behind the walls stratum.

## re86 is not a maze — it is TWO CROSSES collecting marked boxes (2026-08-06)

Read off the live board (`re86-board2.txt`, probes 1-7 in `br-re86-probe*.txt` /
`results/re86-probe*.txt`, all offline):

- Two giant plus-shapes: the P-cross (colour 11, arms 13 wide/tall) and the
  B-cross (colour 9) whose CENTER wears the board's only colour-0 cell (`@`).
  Eight 3x3 colour-4 frames, four holding a P cell, four holding a B cell —
  8 frames x 8 cells = the board's entire colour-4 census (64), so the frames
  ARE the "walls" the discovery table said were missing. There is no maze.
- **The arrow keys drive the B-cross** (step 3) — matching the old offline
  discovery's player=colour-9 reading; the competition run elects colour 11
  instead (agreement via overlap), which is a THIRD variant of the
  metronome-election family. Action 5's scattered displacement is unexplained
  (suspect: toggles control to the P-cross).
- **Walking the @ onto a B-box's centre COLLECTS it**: the box's inner B cell
  is consumed, the colour-4 frame loses 4 cells (opens), the B-cross itself
  loses cells as it collects (56 → 54 → 51). No level-up after one box.
- **Frames collide with the ARMS, not the centre**: approaches stall exactly
  where an arm tip meets a frame wall (centre x48 + 6-wide arm = wall at x55).
  The still-closed frames are the terrain; the cross must thread its whole
  footprint. Refusal points MOVE with the approach line — that is why
  `classify_colours` sees colour 9 as both passable (arms overlap freely) and
  blocking (frame contact), and why `block=[]` is CORRECT here.
- The engine returns EMPTY frames intermittently during collection (events);
  `np.array(obs.frame)[-1]` must be guarded, and the modal-column centre of
  colour 9 drifts when an arm clips the board edge — track the @ cell instead.

Next session's L1 attempt, in order: (1) collect all four B-boxes tracking the
@ (guarded frames, arm-aware approach: prefer the axis whose arm is clear);
(2) if no level-up, press action 5 and see whether control moves to the
P-cross and its four P-boxes; (3) the win is then likely both crosses' box
sets cleared. The competition-run blocker stays the election (colour 11 wins
the vote) — same parked family as sc25/sp80.

## re86: ACTION 5 IS A CONTROL TOGGLE — the mechanic set is complete (2026-08-06)

Live-probed additions to the cross-collect model (`re86-tog.txt`, `re86-defl*.txt`,
`re86-l1a.txt`):

- **Action 5 toggles which cross the arrows drive** (B → P → B, verified both
  ways). This finally explains the competition run's colour-11 election (half
  the warmup's arrows land on the P-cross) AND its scattered action-5
  "displacement".
- **Crosses and frames are transparent to the WALK**: pressing through box
  rows, frame walls, and straight through the other cross's body produces
  clean -3/+3 steps — no collision, no death, in a fresh run. The earlier
  "stuck at x54/x48" readings were an INSTRUMENT ARTIFACT: the modal-column
  centre of colour 9 drifts once arms lose cells or clip the board edge —
  track the @ (the board's only colour-0 cell, riding the B-cross centre).
- **Collection appears to be ARM-sweep, not centre-landing**: the confirmed
  collect (inner B at (40,24) consumed, frame -4 cells, B-cross -2) happened
  with the centre at (42,24), the arm covering the inner cell. One GAME_OVER
  was also logged with the vertical arm crossing box (48,16) on a different
  visit — collect-vs-death conditions are NOT yet separated (suspect: which
  cross is under control, or frame-cell overlap vs inner-cell overlap).
- **Parity table (step 3)**: from spawn, the B-cross's lattice reaches NONE of
  the four B-box inners exactly ((48,16),(40,24),(53,24),(48,35) — each off by
  1-2 on one axis); the P-cross reaches three of four P-inners ((15,3),(6,9),
  (24,9) on-lattice; (15,17) off). If collect is arm-sweep, parity stops
  mattering — the arm is 6 wide either side. The next session's first probe:
  sweep an arm across each inner cell deliberately (control the right cross!)
  and log collect vs death per overlap type; then chain all eight.

Board coordinates this night (fresh reset): B-cross centre @ (36,45), P-cross
centre (21,27); B-boxes (48,16),(40,24),(53,24),(48,35); P-boxes (15,3),(6,9),
(24,9),(15,17). Box inners detected by "9/11 cell wearing a colour-4 ring"
(`boxes()` in `re86-l1a.txt`'s script — rebuild from there).

## re86: the "collection" was an occlusion artifact — win condition still open (2026-08-06, last)

The full both-cross tour (`re86-l1b.txt`: arm-cover all four B-boxes, then
toggle and land EXACTLY on three P-box inners) produced **no level-up and no
persistent board change**: every B/P/colour-4 count that dropped during the
tour bounced back once the cross moved away. The earlier "collect" (inner
consumed, frame opened) was the active cross's own arms occluding cells at
render time. Two facts survive as real: **the @ cell rides whichever cross is
ACTIVE** (it jumps at toggle — the control indicator), and **the centre
standing on a frame cell is the GAME_OVER** (the one death; the no-death tour
never put the centre on a frame). Exhausted cheap hypotheses: exact-landing
(P side, 3 boxes), arm-sweep (both sides), centre-on-centre, pass-through
effects. Next session needs SEARCH, not probes: the engine is deterministic
per process, so DFS/BFS by replay-from-reset over (B centre, P centre, active)
watching `levels_completed` — with the frame-lava constraint pruning, the
reachable state space per parity class is small. Alternatively read
`frames/re86` renders for a display/indicator that names the goal (the
colour-15 row is one full HUD row; nothing else unexplained on the board).

## re86 FALLS — it is a cover puzzle, and the win condition was a HUD row nobody read (2026-08-06)

Three levels in the competition loop (`re86 3/8 levels actions=[32, 56, 66]
score=14.542%`, `results/re86-compete.txt`), from 0. Sweep clean
(`results/sweep-cover.log`): every canary identical to the digit — ls20 7/7
43.629%, ar25 [173], cn04 [131], m0r0 [53], cd82 [1306] — mean **2.676% ->
3.531%**, and the roster goes **5/17 -> 6/17 games with a level**. The rung is `cover.py`; the
whole mechanic came out of four offline probes in one sitting, and the two
readings that unlocked it are both instrument lessons rather than game lessons.

**1. The engine IS replayable in-process** (`re86-det.txt`). `reset()` plus a
fixed 20-action sequence returns byte-identical frames on the second pass, at
**4,307 steps/s** — so the BFS/DFS plan in the previous session's note was
affordable. It was never needed: the answer fell out of geometry first.

**2. The bottom row is a 100-ACTION BUDGET, and reading it is what explains the
deaths** (`re86-bar.txt`). Colour 15 fills one full row (64 cells) and turns to
colour 1 at `round(0.64 n)` — the bar reaches 64 at exactly the 100th action of a
level and the state goes `GAME_OVER`. It refills on level-up (measured: bar 8 →
0 across the level-1 boundary). Every action costs, including the toggle and
including a move that changes nothing. The previous session's "one GAME_OVER with
the vertical arm crossing a box" was a centre standing on a frame cell, and the
tour that survived was simply under 100 — two different deaths that looked like
one unexplained condition.

**3. The lattice never shifts** (`re86-edge.txt`). Both shapes spawn on
`x%3==0, y%3==0`, arrows are `±3` axis-aligned (1=up, 2=down, 3=left, 4=right)
and the board CLAMPS at 0 and 63 — both of which are on the lattice, so no edge
push can change parity. Pushing down parks the centre on row 63 UNDER the HUD,
where the `@` is invisible: `at()` returning None is a position, not an error.

**4. The win condition: every shape centred so that all of its boxes lie on its
own cells.** Level 1's four B-boxes are `(48,16),(48,35)` sharing x=48 and
`(40,24),(53,24)` sharing y=24 — the plus's arms are 13 long, so ONE centre at
the intersection `(48,24)` covers all four at once; the same for P at `(15,9)`.
Both parked = level up, **20 actions** (`re86-cross.txt`). The previous session's
"collection is an occlusion artifact" was right about the arm sweep and wrong
about the conclusion: a group IS consumed, but only when ONE shape covers ALL of
it, which no partial tour ever did.

What each level added, and what it forced into the solver:

| lvl | shapes | boxes | forced |
|---|---|---|---|
| 1 | two 13-arm pluses | 4 + 4, by colour | intersection |
| 2 | plus + two hollow DIAMOND rings | 4/3/3 | read the shape as an offset SET off the board, never assume a form |
| 3 | three shapes, ALL colour 8 | 8, all colour 8 | box colour cannot name the owner → geometric partition search; and the shape must be read from what MOVES (a colour mask is the union of all three) |
| 4 | plus + X, colours 6/10 | 3 colour-12 + 3 colour-14 | shape colour ≠ box colour at all → try the plans in rank order |

Two probe-design traps inside that, both measured:

- **A shape shifted ALONG an arm hides that arm in its own trail.** Probing with
  one direction read level 1's 52-cell plus as 32 cells. One probe per AXIS
  (up-or-down *and* left-or-right) recovers it exactly.
- **An arm hanging off the board edge is measured SHORT.** Level 4's plus reads
  `right=9` against `left=13` because its spawn at (54,36) puts the tip past
  x=63, and the missing four cells are exactly what made the level look
  uncoverable. Every shape seen so far is point-symmetric, so the offset set is
  symmetrised.

**Level 4 is open and is NOT a coverage problem.** All six boxes are consumed —
the plus at (15,30) takes the three colour-12s (census `12: 19 → 16`) and the X
at (39,30) takes the three colour-14s (`14: 19 → 16`), both verified to persist —
and the level still does not fall (`re86-l4both.txt`). What level 4 adds and
nothing else has: six 6x6 boxes in colour-2 frames at the top and bottom of the
board, paired by column — `(10,11)`, `(12,6)`, `(13,14)`. `boxes()` sees them
(the ring test is colour-agnostic) but the covering rule for a 4x4 inner is
unmeasured, and a shape has been observed to RECOLOUR (10 → 12) in one run and
not another. Next session starts there, with the budget bar in hand: a level-4
attempt costs 100 actions and the replay from reset to level 4 is under a second.

Two facts for whoever picks it up: a satisfied shape LOSES its `@` (the marker
does not just move — the colour-0 count goes to zero while that shape is active),
and the engine returns empty frames mid-level, so every read is guarded.

## re86 3/8 -> 5/8: the colour clause, swatches, waves, and the L5 overlap trap (2026-08-06, session 2)

The win condition has a clause the first three levels could not show: **a group is
all the boxes of one COLOUR, and it consumes only under shapes WEARING that
colour**. Levels 1-3 pair every shape with its own colour from spawn, so pure
geometry passed them; level 4's shapes (6, 10) match neither box colour (12, 14)
and covering both groups on the correct centres with the wrong coats is inert
(`re86-l4p1.txt`).

What level 4 adds is SWATCHES — 4x4 blocks ringed in a non-frame colour — and
**standing on one recolours the active shape to its colour, for keeps**
(`re86-l4p2.txt`: X on the 13-swatch goes 10 -> 13, persistent). Recolour each
shape to its group's colour, cover, level falls (`re86-l4p4.txt`). The "legend
pairs" reading of the first session was a red herring — the pairing columns mean
nothing; the blocks are just paint pots.

Three more measured rules from levels 5-6, each of which broke the solver in
turn:

1. **The recolour trigger is CELL OVERLAP, not the centre** (`re86-l5p6.txt`):
   driving the L5 X toward the 9-swatch flipped it at (9,54) — an arm entering
   the RING — three cells before the inner. A route that only keeps the centre
   off swatches scrambles the coat in passing (the L5 stall: a shape sent to
   wear 9 arrived wearing 11, `re86-l5p5.txt`). Routes now avoid every swatch
   DILATED by the shape's own offsets, except the swatch of the colour being
   worn or fetched — touching your own colour is a no-op.
2. **A box whose ring is under an arm is INVISIBLE to the ring detector** — L5's
   "two 8-boxes becoming four" was two more sitting under the spawned cross's
   arms all along. The box set accumulates across frames now, and a box only
   leaves it when its whole 3x3 reads background (consumed), which a 1-wide arm
   over a ring cannot fake. Corollary: the naked centre marker on open floor
   reads as a box ringed by background — the c=0 "boxes" in the wave logs;
   harmless (no shape wears colour 0) but they pollute the accumulator's
   signature, which is why the wave loop keys on progress, not equality.
3. **Consumption is per-group and immediate; a level can need several WAVES**:
   the planner replans until the box set stops changing.

`cover.py` now: 5/8 levels, `[31, 56, 66, 80, 188]`, 41.477% single-game
(`re86-compete2.txt`). Sweep clean (`sweep-cover2.log`): every canary identical
to the digit, mean **3.531% -> 5.116%**.

**Level 6 is open and is a NEW mechanic.** The board (`re86-l6p1.txt`): a
13-arm-class plus wearing 9, a 19x19 hollow SQUARE wearing 11, four 9-boxes,
four 11-boxes, **no swatches**, and an 8x8 colour-1 ring enclosing an empty
hole. Measured dead so far, one probe each (`re86-l6p2..7.txt`): colour-1 cells
are WALLS (a move whose arm would overlap one is refused — the first refusals
this game has shown); the hole is geometrically SEALED (any edge threading it
must cross the ring, both shapes); covering a same-colour PAIR does not consume
it; covering a whole quad with mixed coats (plus-9 + square-11) does not
consume; the centre CAN stand on a box inner (step 3 jumps the ring; the ring
kills only what the centre lands on) and nothing happens. Geometry says
plus@(12,9)+square@(21,18) covers the 9-quad and plus@(48,30)+square@(48,48)
covers the 11-quad — everything is in place except a way to change a coat with
no swatch on the board. The colour-1 ring is the only unexplained object.
Level 6's budget is also tighter: the bar reaches 64 in well under 100 actions,
so hypothesis probes there are one-shot per replay (~450 actions to reach L6
offline, deterministic).

## cn04 L2: the dock EXISTS and registers visually -- the completion trigger is still not found (2026-08-06, session 2 tail)

Live-shim recon (`cn04_l2*.py` -> `results/cn04-l2*.txt`; all offline, one live
env per process via `probe_cn04.live_at_level`). The L2 board IS stable across
processes (censuses and dumps byte-match), so cross-run geometry holds even
though trajectories are process-random.

Measured facts, several overturning the earlier session's model:

- **The white piece passes THROUGH every shape** -- the trial matrix (4
  rotations x 7 alignments, pushed right) sailed to the board edge every time
  (`cn04-l2c2.txt`). The historical "refused step held for 1,600 rounds" was a
  board-edge refusal, not shape collision: bodies do not collide on this level.
- **The board's pads pair by CONSTELLATION exactly once**: the piece's pad pair
  vector is (-3,+6), and of every pad pair on the board (12 pads: piece 2,
  e-shape 4, b-shape 4, 9-square 2) the ONLY match, at any of the four
  rotations, is the b-shape's ((18,39),(15,45)). Geometry singles out one dock.
- **The dock registers**: with the piece translated (0,+18) both pad pairs
  coincide, the bodies mesh with ZERO overlap (a true jigsaw fit), and all four
  involved pads VANISH from the frame (8-census 108 -> 72, back on undock,
  reproducible; `cn04-l2f.txt`). The engine sees the dock. The level does not
  fall.
- Measured inert at/around the dock: adjacency above/coincide/below
  (`cn04-l2d2.txt`), rotator pressed at dock x1 and x4 (`cn04-l2h.txt`), moving
  after docking (b never follows -- no carry/merge), hammering THROUGH b to the
  board bottom (`cn04-l2i.txt` -- and the "b lost its left column" reading en
  route was bbox-through-occlusion, the repo's oldest trap, again), a
  single-pad tour coinciding piece-pad-1 with every other pad on the board
  (`cn04-l2g.txt`), and pushing up into the top strip at four offsets
  (`cn04-l2j.txt`).
- **The colour-4 strip (x16-47, row 0) is a CLOCK, not a door**: it burns ~1
  cell per 3-4 actions, monotonically, and the loss persists across level
  resets (32 -> 27 across one probe battery). Long probe batteries on this
  level are spending a real budget; whatever completes the level must fit it.
- `env.reset()` after >=1 real action re-deals the same L2 board in-process --
  the retry loop every probe above leans on.

Open: what the dock is FOR. The one un-probed structural idea: the dock event
may need to happen with the clock/some other state in a particular phase, or
the level may want a sequence of docks the piece geometry cannot express with
its two pads -- in which case the next lever is reading how the 8-pads respond
to a dock over TIME (frames during dock showed no drift in one 4-tick hold).

## sp80 OPENS -- level 1 falls in one sitting; ACTION5 is a control TRANSFER, not a gun (2026-08-06, session 3)

The re86 playbook applied verbatim (determinism first, census + per-action
diffs, then hypothesis probes), and it paid out on the second hypothesis.
Everything below is offline; no scorecard touched.

**Foundation** (`sp80-det.txt`): replay-from-reset is byte-identical in-process
and a second `arc.make` starts identically; **80,469 steps/s** (19x re86). The
board: colour-14 bar across y0 (the budget clock), a 4x4-column stack of
colour-4 (3 rows) over colour-6 (4 rows) at x36-39 y1-7, the movable colour-9
block 20x4 at (12,16), two colour-11 castle shapes at y52-59 (4x4 towers on a
12x4 base, 4-wide gap between towers), and a colour-1 band y60-63.

**Measured mechanics, run files named:**

- Movement: 1=up 2=down 3=left 4=right, step 4, clean clamp walls (the brief's
  "movement model CLEAN" holds). 80-cell body: x0-44, y16-44 as x-left/y-top
  (`sp80-p2.txt` wall map). A blocked move burns budget and does not move.
- **Budget: bar burns ~2.13 cells/action; level 1 = 30 actions, level 2 = 45**
  (`sp80-p1.txt` test D, `sp80-p10.txt`). GAME_OVER at bar 0. The bar row
  flips to y63 on level 2 (the whole board flips vertically).
- **ACTION5 is the level's verb and a 5-shot magazine: the 5th press in one
  life = GAME_OVER, counted per-life TOTAL, not consecutive, position-blind**
  (`sp80-p1.txt` B, `sp80-p2.txt` A/A2: 5,5,5,5,1,5 dies on the 6th press;
  interleaving does not reset the count).
- ACTION6 (the complex/click action) is a no-op everywhere tried, on every
  object (`sp80-p2.txt` C). probe.py crashed on sp80's GAME_OVER empty frame
  before ever reaching ACTION6 -- the grid_of guard matters here too.
- **Level 1 win: fire with the block at x-left=24, ANY y -- the full win map is
  exactly the 9-position column** (`sp80-p6.txt`, all 108 reachable positions
  fired). Recipe: `[4,4,4,5]`, 4 actions of a 30-action budget.
- **What ACTION5 actually does (level 2 shows it): control TRANSFER between
  bodies.** Firing from a transfer-legal position moves colour 9 (= "you") onto
  the colour-8 target body; the old body parks as colour 8, keeps its own
  shape/size, and the arrows then move the NEW body (`sp80-p8.txt` S1: the
  48-cell block walks after takeover). Level 1's "win column" is presumably a
  transfer INTO the goal stack reading as level-complete -- unproven, needs the
  L1 diff read again with transfer eyes.
- Level 2 board: 3 castles hanging from the top, bar at y63, stack at x40-43
  bottom, and TWO 12x4 colour-8 bodies at (8,16) and (28,24). Bodies do NOT
  collide -- the active body walks through them; a body under another is
  OCCLUDED, not consumed (the repo's oldest trap, confirmed again
  `sp80-p5.txt`).
- **Transfer legality is positional and NOT yet explained** (`sp80-p12.txt`,
  `sp80-p13.txt`: full maps, 80-body-active and 48-body-active). Shape: a
  no-transfer wedge opens down-right of the target body; pressed against the
  LEFT wall (x0) or the CEILING (y16) transfer is legal from ANY x/y; the
  boundary is neither Manhattan, Chebyshev, Euclidean, sum-diagonal, nor any
  45-degree corner ray tried (all fitted and refuted against the maps).
- **The transfer chain on L2 is a fixed toggle: 80-body <-> block-2. Block-1 at
  (8,16) is NEVER a target** -- not even when the active body fully overlaps
  it (`sp80-p12/13.txt`, zero '1' entries in both maps). Block-1's role is
  open, and is probably the level's actual puzzle.
- Firing at a transfer-illegal position changes nothing but the clock -- a
  wasted charge from the 5-magazine.
- The reset-after-transition trap is a TOOL here: reset with zero actions after
  a level-up game-resets to level 1, which is how the L1 win map got 9 samples
  in one process (`sp80-p6.txt`).

**Instrument notes:** deepcopy(env) works, is faithful, ~2-3ms (`sp80-p10.txt`
B) -- BFS over the real engine at O(1) per node instead of replay-per-child.
`env.reset()` costs ~10ms and dominates naive sweeps; the p9 BFS null was an
instrument artifact TWICE (depth cap 29 on a 45-action budget, and fires-used
missing from the visited key -- ammo is real hidden state).

**Open, in order:** (1) p11 BFS (depth 44, ammo-keyed, deepcopy nodes) over L2
-- running at write time; (2) the transfer-legality rule; (3) block-1's role;
(4) whether L2's win is a transfer into the stack and from where.

**sp80 CLOSED for this session -- L1 solved, L2 is a measured wall (2026-08-06, session 3 tail):**

- **BFS over the real engine, exhaustive: level 2 has NO winning line within one
  life** (`sp80-p11.txt`: 39,328 states, frontier emptied, depth cap 44 on the
  45-action budget, fires-used in the visited key, deepcopy nodes). The p9 null
  was the instrument; the p11 null is the level.
- Transfer legality is **position-pure**: same position fired at different
  clocks and via different routes always answers the same (`sp80-p14.txt`).
  This licenses the BFS clock-masking for transfers -- and the win itself is
  not clock-gated either at the natural candidates: stack-aligned columns,
  both bodies, floor/ceiling rows, every affordable delay (`sp80-p15.txt`,
  zero wins).
- The L2 board is byte-identical (clock masked) for three different L1 exit
  recipes -- ceiling/home/floor fires (`sp80-p16.txt`); no cross-level state.
- Nothing measurable persists across lives: bodies reset, the bar refills, the
  magazine is per-life. Level 2's missing trigger is therefore OUTSIDE
  everything enumerated here -- the same verdict class as cn04-L2's dock.
  Untried levers, for whoever returns: interactions that need the ACTIVE body
  parked ON a specific object while a DIFFERENT condition holds (the maps only
  vary one body at a time); ACTION6 clicks landing on lattice cells NOT probed
  (only object centres were clicked); and reading the L1 win as "transfer into
  the stack" to derive what L2's stack expects geometrically.

**Campaign note: sp80's level 1 is now a KNOWN CLEAR** -- `[4,4,4,5]` from
reset, 4 actions, and the whole win column (24,y) is legal so a legal agent
has 9 targets to find. Wiring a discovery rung into compete.py (fire-sweep
under the 5-shot/30-action budgets) is a CODE change: full 17-game sweep +
no-level-lost gate applies. sp80 would be game #7 with a level.

## sp80 LANDS IN THE AGENT — a control-transfer rung, level 1 in 16 actions (2026-08-07)

`swap.py`, wired the way `cover.py` is: constructed once if a reset-frame
signature matches, asked first every round, answering None the moment it runs
out of ideas so the rungs take the level back (compete.py:1704-1710, 1834-1840).

**The signature was chosen from a measurement, not proposed and then defended**
(`results/sp80-sig.txt`, all seventeen playable games at reset): a single-colour
band on BOTH screen edges, plus a solid rectangle of >=60 cells that does not
span the width. sp80 is the only game of the seventeen that satisfies it —
dc22 is the only other with two edge bands and its largest non-full-width solid
block is 24 cells. Disjoint from cover's by measurement too: sp80 reads ZERO
framed boxes, re86 has no top band, so the two drivers are never both live.

**What the rung does.** It sweeps: fire from where you stand if that position
has not been tested, otherwise walk to the nearest untested one. It keeps no
plan — every round is decided from the frame in front of it, which is what makes
a death harmless (the block reappears at the level start and the rung reads
where it is). The arrow mapping is not assumed but read off the block's own
displacement (`ar25` answers ACTION3 with right, CLAUDE.md §Traps), and the
driven colour is learned the same way: the one body that TRANSLATES as a rigid
set between two frames.

**The magazine is the whole design, and it came from one measurement.** The
fifth fire of a life is a GAME_OVER and it MASKS a win: the same position that
levels up on a fresh magazine dies silently as shot five (`sp80-p18.txt` A vs
B — B is the control, same walk, fresh magazine, level up). A sweep that marks
every fired position tested therefore books a FALSE NEGATIVE at exactly the
position that answers the level, and can never find it again. So shots are
counted, the magazine size is LEARNED from the first death rather than assumed
(`mag = shots - 1`), the last shot of a life is spent deliberately as a one-action
reset, and the position it was spent on is put back on the list.

Two facts make that reset cheap enough to be a tool rather than a cost:
GAME_OVER is terminal at the engine unless someone calls `reset()`
(`sp80-p17.txt` A, B: the engine stays GAME_OVER and hands back empty frames
forever), and `compete.play` calls it and carries on, charging the death exactly
the one action that caused it (compete.py:1965-1972).

**One bug worth keeping.** The life detector first re-read the band structure
every round — and the clock is a full-width BAND only while it is FULL, so one
burnt cell makes its row mixed and the colour drops out of the reading on the
very first action. The refill is then never seen, `mag` stays None for the whole
run, and the rung goes on firing the masked fifth shot as a test
(`results/sp80-swap1.txt`: `mag=None`, 76 positions "tested"). The colours are
latched from the level's first frame and counted whole thereafter
(`sp80-swap2.txt`: `mag=4`). A signature function and a per-round tracker are
not the same instrument even when they read the same feature.

**Measured.** Offline harness: level 1 in 16 actions, then 113 positions swept
on level 2 with 84 targets correctly ruled unreachable — which is exactly the
number of lattice positions outside level 2's measured wall box (192 generated,
108 reachable) — then None at i=978, handing ~1,000 actions back to the rungs
(`sp80-swap2.txt`). Through `compete.py`: **sp80 0/6 -> 1/6 levels,
actions=[16], score 0% -> 4.762%** (`results/sp80-compete1.txt`); level 1's
baseline is 39 actions, so 16 is inside the scoring cap. pytest 219 -> 238
(`results/pytest-swap-full.txt`), the 19 new ones in `test_swap.py`, two of
which were proved to have teeth by putting each fix back and watching them go
red (`results/teeth-mut1.txt`, `teeth-mut2.txt`).

**Known narrowness, not measured as a problem here:** `_targets` reads the
lattice stride from actions 4/3 (x) and 2/1 (y) specifically, so a game whose
horizontal step lives only on some other action would sweep one column; and
`_here` takes the bounding box of the driven colour, which would span two bodies
if a board ever showed two of them at once (sp80 never does — a transfer repaints
the old body, so the driven colour is always exactly one blob).

**Sweep verdict and one more defect (2026-08-07, same session).**

Sweep 1 (`results/sweep-swap.log`, compared per game by `sweep_diff.py`, which
parses in python because `diff` is rewritten on this machine): **16 of 17 games
identical to the digit** — ar25 bp35 cd82 cn04 dc22 g50t ka59 ls20 m0r0 re86 sb26
sc25 sk48 tr87 tu93 wa30 — and the only change is
`sp80: 0/6 [] 0.0% -> 1/6 [16] 4.762%`. Mean **5.116% -> 5.396%**, roster
**6/17 -> 7/17 games with a level**. No game lost a level.

That sweep is also the strongest evidence the signature is exclusive, stronger
than the feature table it was chosen from: the driver acts on ANY board it is
handed, so if it had been constructed for any other game that game's trace would
have moved. Sixteen unchanged traces mean sixteen games never built one.

**D1, found by self-review and then measured** (`results/sp80-d1.txt`): the rung
read the arrow mapping from `moved(self.prev, g)` BEFORE asking whether a life had
just ended. When the life ends on the CLOCK the last action was a direction, so the
pair straddles the engine's reset — and the block coming back to the level's start
IS a rigid translation of the driven colour. Measured: the arrow just pressed had
its vector overwritten with a SIGN FLIP, `(0, 4) -> (0, -4)`, against an
honest-answer control on the same setup that stayed clean; a corrupt stride
collapses the sweep's target set from 192 positions to 32. Not reachable on level 1
(the rung wins at action 16 and its only death there is a magazine death, whose last
action is FIRE), reachable on level 2 where the sweep spends ~978 actions.

The first probe written for it answered "mapping intact" — and was measuring
nothing, because the driver FIRED that round instead of walking. Its own first line
said so (`emitted 5`). A positive control inside the same invocation (assert the
round emitted a direction) is what made the second run trustworthy, and the first
control was worthless besides: its assertion carried an `or` escape hatch that
accepted the very corruption it was written to rule out.

Fixed by asking `_fresh_life` first and skipping the learning step when the board
was just put back. Two tests, `test_a_death_teaches_the_arrows_nothing` (red before
the fix, `results/pytest-d1-red.txt`) and its partner
`test_an_honest_answer_still_teaches_the_arrows` (green before AND after, so the
guard cannot pass by simply deafening the learner). pytest 238 -> 240.
Sweep 2 is the acceptance run for the fixed bytes (`results/sweep-swap2.log`).

An adversarial review of the rung and its wiring — four lenses (signature safety,
sweep control flow, magazine bookkeeping, driver contract), every finding then
handed to an independent refuter — raised five findings and **none survived**; the
refutations are evidenced against the run files (for example: colour-8 bodies are
byte-identical across three consecutive RIGHT presses in `sp80-p8.txt`, which kills
the "moved() could attach to the wrong body" claim). D1 was not among what it found.

Sweep 2 (`results/sweep-swap2.log`, the acceptance run for the fixed bytes) is
**byte-identical to sweep 1 across all seventeen games** — so the D1 guard changes
no measured trajectory, which is the expected shape: level 1 wins at action 16 and
its only death there is a magazine death, whose last action is FIRE and never taught
the arrows anything. Against the standing baseline it is the same verdict: 16 of 17
identical to the digit, `sp80: 0/6 [] 0.0% -> 1/6 [16] 4.762%`, mean 5.116% ->
5.396%, no game loses a level.

## g50t: the mechanic is measured, level 1 is not solved, and the search says it cannot be (2026-08-08)

Next target after sp80, chosen for shape: `acts=[1,2,3,4,5]` with no complex
action -- exactly re86's and sp80's -- plus a full-width bar row. Everything below
is offline; no scorecard touched.

**Not the framed-box family.** g50t reads 3 framed boxes at reset against cover's
threshold of 4 (`results/sp80-sig.txt`), which was worth one probe: driven anyway,
`cover.py g50t 12` gives up at i=6 (`results/g50t-cover.txt`). The 3 are ring
artefacts.

**Foundation** (`results/g50t-found.txt`, `probe_found.py` -- a parameterised
replacement for copying `probe_re86.py` per game): replay-deterministic in-process,
**2,153 steps/s**, second env identical, baseline `[78, 175, 179, 230, 96, 54, 67]`.
The board is a maze: floor 5, void 0, a 24-cell piece (5x5 with the centre out) at
(14,8), a goal-box ring of colour 9 at (43-49, 49-55) with a marker inside, an
82-cell colour-8 snake, an indicator top-left, and a colour-9 bar filling y63.

**Measured mechanics** (`g50t-acts.txt`, `g50t-p1.txt`, `g50t-p7.txt`, `g50t-p8.txt`):

- arrows step **6**; the clock burns 1 cell per 2 actions, so a life is **128
  actions** against a level-1 baseline of 78.
- **only actions 2 and 4 move anything at reset** -- the piece starts in the
  maze's top-left corner, so up and left read as immovable. The repo's own
  generalisation-probe caveat, live.
- **action 5 RECALLS the piece to x=14**, measured directly (`g50t-p8.txt`: piece
  x-left 38 -> 14 on one press). `probe_acts` reported it as a no-op for eight
  presses because from reset the piece is ALREADY at x=14 -- the same shape of
  miss as "a piece that starts against a wall reads as immovable", one level up.
- **the colour-8 snake's head is a HOLD-TO-OPEN gate, not a collectible.**
  Standing on it at (38,8) retracts 25 of the snake's cells -- including the whole
  of x14-18 y38-42, the square that had refused the piece -- and opens 24 void
  cells into floor around a new segment at x20-25 y37-43. Step off, or press the
  recall, and **every one of those cells comes straight back** (`g50t-p7.txt`
  step 4: total8 66 -> 82 on leaving; `g50t-p8.txt`: 66 -> 82 on the recall). The
  first reading of this as a consumption was wrong in the repo's oldest way -- a
  state read while the piece is standing on the thing.
- a death restores the board **exactly**: census delta {} against the reset frame
  (`g50t-p4.txt` B). Nothing carries between lives.

**The level is unwinnable from reset, and the search that says so is controlled.**
BFS over real engine states with `copy.deepcopy` nodes: 25 distinct boards, 12
reachable piece positions, the goal box among none of them, no win
(`g50t-p3.txt`). Re-run with the CLOCK back in the visited key -- the exact shape
of the sp80 null, where the missing key was the magazine -- 3,162 states, 125
deaths, same answer (`g50t-p5.txt`). Two controls were then run rather than
assumed:

- **`deepcopy` is a true fork here.** The control run for sp80 asked "same next
  frame" and "advances independently", and BOTH are true even of a copy that
  SHARES its parent's state. The discriminating question is whether the PARENT
  moved after the copy stepped; it does not, on either game, against a positive
  control that proves the comparison can answer False (`results/deepcopy-check.txt`).
- **the harness finds a win it is known to have**: pointed at sp80 level 1 it
  returns `[4, 4, 4, 5]` in 38 expansions (`results/bfs-control.txt`).

**So the open contradiction is the finding.** A controlled exhaustive search says
no sequence of <=130 actions from the reset board completes level 1, the clock
allows 128, a death changes nothing, and the human baseline for that level is 78.
One of those is false and it is not the search. Candidates, none yet measured:
the recall may do more than move x (its y behaviour was never read); the top-left
indicator was seen shifting +/-4 under action 5 in a live run (`g50t-run1.txt`
i=1825) which no probe from reset reproduces, so something enables it; or the
hold-to-open gate has a second holder the board has not been asked about.

**Why the agent scores 0 today** is separately clear and does not depend on any of
that: discovery learns `block=[0, 8]` (`g50t-run1.txt`), and colour 8 is the gate.
Offline reachability on the reset frame with 8 as wall gives 11 positions and the
goal box unreachable; with 8 as floor it gives 20 and the goal box reachable at
(44,50) (`g50t-p2.txt`). The router is sealed out of its own level by one colour
in `blocking` -- which `classify_colours` earned honestly, because the move into
(14,38) IS refused 25 times over and 8 is the only unexplained colour there
(`discover.py` classify_colours, `bsets=[((0,), 89), ((5, 8), 25)]`). A colour that
blocks except while its head is held is a mechanic the wall model has no shape for.

**g50t, three more probes, all inert — the contradiction survives (2026-08-08).**

- **Nothing accumulates across a death.** Twenty deliberate lives: the board is
  byte-identical to reset every time, the top-left objects are identical, and
  action 5 answers with the same zero-cell change on every one
  (`results/g50t-p9.txt`). So the live run's `±4` shift under action 5 at i=1825
  (`g50t-run1.txt`) is a tracker artefact, not a mechanic a death unlocks.
- **`baseline_actions[0]` is the engine's level 1.** ls20 baseline 22 against the
  agent's measured 23, re86 26 against 31, sp80 39 against 16 — the same order in
  every case (`g50t-p9.txt` A). The 78 is level 1's.
- **No state hides outside the frame, along the routes tested.** Two different
  20-action routes that end on the same board, given the same 13-action
  continuation, produce byte-identical frames at every step; the control route
  that ends elsewhere differs at 4 of 14 (`results/g50t-p10.txt`). An incomplete
  visited key was the sp80 null's cause and is not this one's.
- **The BFS harness clears a MAZE, not just a four-action puzzle.** Pointed at ls20
  level 1 it returns a **13-action** win — shorter than the human baseline of 22
  and than the agent's own 23 (`results/bfs-control-ls20.txt`). A shallow control
  is weak evidence for a null found at depth 130; this one is not.

So the search stands and the contradiction is unexplained: a 12-position box that
a human is credited with taking 78 actions to clear. The one structural thing
noticed and NOT yet exploited: **the piece is a ring, not a block** — its centre
cell is background, so the footprint that must be clear is 24 cells with a hole,
and every hand-rolled reachability in this file (including `g50t-p2.txt`) treated
it as a solid 5x5. The engine BFS is unaffected (it asks the engine), but any
router built for this game must not inherit that assumption.

Not rules-legal, but worth recording: an engine BFS with `deepcopy` nodes is a
SOLVER, not only an analysis tool — 13 actions on a level the agent plays in 23.
`play.py` is the repo's existing note that rewinding searches are out of
competition; this is the same class, and the same upper-bound use.

## wa30: opened, and the piece has a HEADING (2026-08-08)

Next in the queue after g50t, same shape (`acts=[1,2,3,4,5]`, no complex action,
a full-width bar row). Replay-deterministic in-process, **6,064 steps/s**, second
env identical, baseline `[71, 119, 183, 98, 368, 68, 79, 442, 415]` -- nine levels
(`results/wa30-found.txt`).

The board is nearly empty: background colour 1 (3,920 cells) with a handful of
objects. A **piece 4x4 at (32,48)** stepping 4; three 4x4 boxes with a colour-4
ring and colour-9 inner at (44,24), (16,28), (32,36); one 12x4 colour-9 ring with a
colour-2 inner at (28,28); a colour-7 clock filling y63 that burns 1 cell per **3**
actions, so a life is ~192 actions.

Two things measured, and both correct a first reading:

- **The piece is not a solid block: it carries a one-row colour-0 EDGE that names
  its heading, and the edge MOVES to the side it walks toward.** At reset it reads
  `0000 / eeee / eeee / eeee` at y48-51; after a leftward walk the 0s are on the
  left. Any reader that finds the piece by its colour-14 cells alone therefore
  reports a position that shifts by one whenever the heading changes -- which is
  what made the first drive look like it was walking off the step-4 lattice
  (`results/wa30-p1.txt`, the (29,40) and (16,37) rows). The piece is the union of
  its 14 and 0 cells.
- **A box's ring turning colour 4 -> 3 is PROXIMITY, not state.** Standing under
  the box at (32,36) turns its ring to 3; stepping away turns it straight back
  (`wa30-p1.txt` steps 1 and 3, and again at 10 and 15). The same shape as g50t's
  hold-to-open gate, and the same trap: a reading taken while the piece is next to
  the thing is not a reading of the thing.

Searching it is not cheap the way sp80 was: the engine BFS reaches 27,953 states at
depth 12 after ten minutes and the level-1 baseline is 71 actions, so the tree is
far too wide to exhaust (`results/wa30-bfs.txt`). Where sp80's whole level lived
inside four actions, wa30 needs a mechanic read, not a search.

Open, in order: what a box's ring being 3 is FOR (nothing yet made it stick); what
the 12x4 colour-9 ring with the colour-2 inner is; and whether the heading is an
input the game reads (the piece rotates for free while walking, so a level that
cares about facing would be turned by the route).

**wa30 level 1 FALLS by hand, 27 actions against a baseline of 71
(`results/wa30-solve.txt`).** The whole game in four measured rules:

1. **Action 5 beside a box GRABS it.** The box's 12 ring cells take the piece's
   own edge colour and the pair moves as one (`wa30-p2.txt` A, `p3`).
2. **It acts along the HEADING, and the heading is whichever way the piece last
   walked.** Arriving beside a box sideways refuses the grab -- measured, the
   first solve attempt died on exactly that at step 10, with the piece standing
   directly under the box and facing left (`wa30-solve.txt`, first run). Drop a
   row, go west, come UP into it, and it grabs. This is what the colour-0 edge is
   FOR.
3. **A second press DROPS the box where it stands**, and a box dropped over the
   12x4 colour-9 frame SLOTS IN: its ring joins the frame's row and the cells of
   the frame's colour-2 inner beneath it are consumed for good -- still gone when
   the piece steps away, so not occlusion (`wa30-p5.txt`).
4. **The frame's inner is the counter.** 10x2 = 20 cells at level 1; the three
   boxes cover 6 + 8 + 6 of it, and the level ends on the press that takes it to
   zero (`wa30-solve.txt` step 26: slots 6 -> 0 -> `lvl=1`).

Level 2 is the same puzzle, larger: an 8x12 frame with **60** inner cells and
more boxes, on a board that redraws entirely.

So wa30 is buildable as a rung of the `cover.py` / `swap.py` shape: read the
frame as the ring with the largest distinct inner, read the boxes as the smaller
rings, and for each one route the piece to an adjacent square ARRIVING FROM the
side that faces the box, press, carry to a slot, press. The routing is ordinary;
the two things a naive version will get wrong are the heading (rule 2) and the
piece's own extent, which is the union of its body and its edge colour, not the
body alone (`wa30-p1.txt`).

## tr87: opened -- a 5-station cyclic-dial puzzle, mechanic measured, level 1 NOT solved (2026-08-08)

Picked from `haul-sig.txt` for its `[1,2,3,4]`-only action set (no complex
action) and a "5 crates" signature `cover.py`/`haul.py` cannot see. Offline
only, no scorecard touched.

**Foundation** (`results/tr87-found.txt`): replay-from-reset byte-identical
in-process (21 frames), a second `arc.make` starts identically, **2,824
steps/s**. `baseline_actions: [54, 58, 40, 45, 71, 146]` -- six levels.
Board 64x64: background colour 2 (top) / colour 3 (rest), a colour-1 bar
filling all of y63 (64 cells at reset) that burns **exactly 1 cell per
action** (`1->4`, seen on every single diff in `tr87-acts.txt` and every
probe run below) -- a life is ~64 actions, close to level 1's 54-action
baseline. Three regions, top to bottom: six 7x7 glyph-tile pairs at y4-28
(colour 10 ink on colour 5, paired with a colour-7 block each -- unexplored,
see refuted #1 below); a colour-10/5 band at y40-46 (see "the hint band"
below); the interactive room at y48-60.

**The piece is a C-clamp, not a walker** (`results/tr87-probe1.txt`):
colour 0, 14 cells total, two horizontal brackets -- 7 cells at y48-49
(`x[15-19]` top, opening down) and 7 at y59-60 (`x[15-19]` bottom, opening
up) -- bracketing the room vertically at whichever x-column it currently
occupies. `reset-vs-reset identical: True`, `second env identical: True`:
the whole board, including the y40-46 band, is stable in-process.

**ACTION3/4 move the clamp sideways across exactly 5 fixed stations, step 7,
with wraparound -- ACTION1/2 never move it** (`tr87-probe3.txt`). From reset
(x=15), ACTION4 visits x=22,29,36,43 then wraps back to x=15 on the 5th
press; ACTION3 walks the same five stations backward. `room_cells_changed`
is 0 on every ACTION3/4 press (`tr87-probe3.txt`) -- moving the clamp never
touches the room's own pixels.

**ACTION1/2 never move the clamp -- they cycle the ROOM PIXELS under the
clamp's current station, and ACTION2 is the exact step-by-step inverse of
ACTION1** (`tr87-probe4.txt`, `tr87-probe5.txt`). Diffed at the pixel level
(`tr87-probe4.txt`), one ACTION1 press at station 0 changes only cells in
`x[15-19]`, never the piece or the bar. Five ACTION1 presses then five
ACTION2 presses reproduces the forward hash list exactly reversed
(`backward == reversed(forward)? True`, `tr87-probe5.txt`) -- not just a
net-zero over a round trip, every intermediate step undoes cleanly.

**Every station is an independent 7-state cycle, period exactly 7, measured
directly at three of the five** (`tr87-probe5.txt` station 0: 30 presses,
repeats at press 7, 14, 21, 28; `tr87-probe8.txt` stations 1 and 2: each
closes at press 7). This is a structural constant of the mechanic, not a
property of one crate's shape.

**Three of the five stations (0, 3, 4) draw from ONE shared, byte-identical
7-symbol deck, just phase-shifted; stations 1 and 2 each have their OWN
deck, matching neither station 0's family nor each other** (`tr87-probe7.txt`,
`tr87-probe11.txt`). Station 3's reset frame is byte-identical to station
0's own deck-state 4; station 4's reset frame equals station 0's state 2.
Station 1 (x22) and station 2 (x29) reset frames match none of station 0's
seven states, and a full 7x7 cross-check between stations 1 and 2 finds zero
shared states either (`tr87-probe11.txt`, empty match list). The room is
one continuous colour-5/7 textured strip (x14-51, y51-57, bordered top and
bottom by solid-7 rows) rather than five separately-walled cells: pressing
the dial at a station with NO detected "crate" underneath (station 1 or 4)
still changes pixels there exactly as it does at a station that has one.

**The `haul-sig.txt` "5 crates" reading is partly a false positive.**
Re-running `haul.crates()` live (`tr87-probe2.txt`, read-only import of
`haul.py`, not modified) reproduces the same five rectangles byte-for-byte,
confirming the board itself is stable -- but only **three** sit in the
actual interactive room (w4h4 at (16,52), w5h3 at (36,52), w3h3 at (29,54)).
The other two, w4h5 at (46,5) and w3h3 at (25,25), fall inside the
unrelated top glyph-tile area (y4-46): coincidental ring=5/inner=7
sub-rectangles inside that region's own noise pattern, not crates to
interact with. `haul.py`'s own `Haul` driver would not engage tr87 regardless
-- `self.on = set(DIRS) | {GRAB} <= set(values)` requires action 5, and
tr87's action set is `[1, 2, 3, 4]` only; not worth a live test, the guard
is unconditional on the action set alone.

**The hint band (y40-46) is a new find, x-aligned exactly to the five
stations, and does not answer to the obvious matching rule.** Colour 10/5,
census `{3: 203, 5: 65, 10: 180}` (`tr87-probe9.txt`). Sliced at the same
five x-coordinates as the room stations it resolves into five distinct
5x7 icons (13, 11, 15, 15, 11 colour-5 "ink" cells respectively) -- too
precisely aligned to the station grid to be unrelated, and the most likely
carrier of each station's target pattern. Tested directly and refuted (see
below): none of it matches any station's own reachable dial state.

### What was refuted this session (do not re-derive)

1. **The hint icon's colour-5 mask equals one of ITS OWN station's seven
   reachable dial states.** Built each station's actual 7-state deck by
   code (not by hand) and compared both polarities (ink=5 and inverted)
   against that station's hint icon: zero matches across all 5 stations x 7
   states x 2 polarities (`results/tr87-probe10.txt`).
2. **Aligning the three stations that share a confirmed family (0, 3, 4) to
   a common symbol completes the level, or changes anything outside the
   room.** Drove station 3 from its reset phase (S4) to S0 (3 presses) and
   station 4 from S2 to S0 (5 presses), leaving station 0 untouched at S0;
   `levels_completed` stayed 0 and the only cells changed outside the room
   and the budget bar were the clamp's own bracket at its new column
   (`results/tr87-probe8.txt`).
3. **Stations 1 and 2 share a reachable symbol with each other** (a
   candidate second "pair" to align, symmetric to 0/3/4). Full 7x7
   cross-check, zero byte-identical matches (`results/tr87-probe11.txt`).
   The "families" are not a clean two-group split; at least three of the
   five stations are singletons relative to each other by this test.

### Not attempted

Whether the target is a SHAPE match (ink cell positions) rather than an
exact byte match, scaled or reflected, against a station's deck; whether
the hint band's five icons pair with the SIX top glyph-tiles (one hint
per level, six tiles for six levels -- an unconfirmed count coincidence,
not a measured fact); and whether visiting all five stations to ANY state
at least once (rather than a specific target) is itself the condition
(baseline 54 actions for six visits + some dialing is generous but not
disqualifying). None of these were probed -- flagging rather than guessing.

## tu93: SOLVED -- fixed-pitch maze, heading-notch piece, level 1 falls in 18 (2026-08-08)

Picked for the same `acts=[1,2,3,4]` no-complex-action shape as re86/sp80/wa30,
plus a full-width single-colour row at y63. Offline only, no scorecard touched.

**Foundation** (`results/tu93-found.txt`): replay-from-reset byte-identical
in-process (21 frames), second `arc.make` starts identically, **8,905
steps/s**. `baseline_actions: [19, 16, 34, 42, 123, 80, 14, 23, 111]` -- nine
levels. Board 64x64, background colour 5. Rows 15-47 hold a lattice of
colour-0/colour-2 cells on a 6px pitch (a small maze, not open floor); rows
0-14 and 48-62 are empty background. Row y63 is 64 cells of colour 6 --
matches every other budget row measured so far.

**The piece is a notched 3x3, not a solid block, and the notch marks
heading** (`results/tu93-p1.txt`, `tu93-p2.txt`). At reset it is a 3x3
colour-9 block at y15-17,x15-17 with ONE cell -- the mid-right cell
`(16,17)` -- recoloured 4 instead. Pressing the action that moves it right
relocates the whole 8-cell colour-9 body AND the single colour-4 cell
together in one press (`tu93-found.txt` ACTION4 diff: `9->0:8 0->9:8
4->0:1 0->4:1`), and the colour-4 cell's position **inside** the 3x3
rotates to track the side the piece last moved toward -- bottom-middle
after moving down twice, top-middle after moving up (`tu93-p3.txt`, steps
1-2 vs step 4/15). Same family as wa30's heading-edge and g50t's ring-with-
a-hole: the piece's own extent is the union of its body colour and its
notch, and reading body-colour alone would report the wrong facing.

**Movement is one full lattice-step per press, not incremental, and is
blocked directionally by maze walls** (`tu93-p1.txt`, `tu93-p2.txt`).
A single press moves the piece by exactly 6px (one grid cell) in a fixed
screen direction; 14 more presses of the SAME action at a wall then show
literally zero further change. This refutes the very first read taken
straight off `probe_acts.py`: from the reset corner, actions 1/2/3 looked
like permanent no-ops (0 cells changed across 10 presses each, only the
budget row burning) while action4 looked like a one-shot special. Retried
after one rightward move (Trap 1 -- never conclude no-op from one reset
position), action2 fired twice in a row (18 cells changed each = a full
8-body+1-notch displacement) before hitting its own wall. 1/2/3/4 are four
ordinary fixed absolute directions; all three "dead" actions were reading
a corner cell blocked in three of its four directions, not a broken action
set.

**The budget row burns ~1-2 cells per action regardless of whether the
move succeeds, and refills to 64/64 on level-up** (`tu93-p3.txt`: 64 ->
63 -> ... -> 42, then back to 64/64 on the same step `levels_completed`
went 0 -> 1). Same shape as every other budget row measured in this repo;
level 1's 18-action clear left more than half the bar (46 of 64 cells)
unspent.

**Level 1 SOLVED and verified live**: `bfs_solve.py tu93 25 60000` found a
win in 18 actions (baseline 19) after expanding 529 nodes / 591 states in
10s, zero deaths (`results/tu93-bfs.txt`):

```
[4, 2, 2, 4, 1, 4, 2, 2, 3, 3, 2, 4, 4, 2, 4, 1, 4, 2]
```

Replayed forward-only on a FRESH `arc.make` (not the BFS deepcopy tree),
`obs.levels_completed` goes 0 -> 1 on the 18th step
(`results/tu93-verify.txt`, `results/tu93-p3.txt`). The colour-14 3x3 block
first seen at y45-47,x45-47 sits untouched through steps 0-16 and is still
there when the level turns over -- the winning press (`act2`, step 17) is
the one that would have moved the piece from y39-41,x45-47 onto exactly
that cell, and the frame returned already belongs to level 2 (new piece
position at y33-35,x12-14, budget refilled, a colour-14 block again at the
same screen coordinates). Read together this says the colour-14 block IS
the per-level goal and stepping onto it wins -- but this is inferred from
the coincidence of timing and position, not from ever observing the piece
and the goal occupying the same cell in one frame, so it stays a strong
hypothesis, not a measured fact.

**Refuted:**
- Actions 1/2/3 are permanent no-ops -- refuted by retrying from a
  different tile; they are ordinary directions blocked only at the
  starting corner (`tu93-p1.txt`).
- Action4 is a one-shot special action -- refuted the same way; it is an
  ordinary direction that happened to face open corridor once from the
  reset tile (`tu93-p2.txt`).
- The piece is a solid 3x3 block -- refuted; it is a notched 3x3 whose
  notch rotates with heading (`tu93-p1.txt`, `tu93-p3.txt`).

**Next lever**: build the rung. The mechanic is simple enough (4 fixed
directions, 6px lattice, wall-blocked, single coloured goal square) that
`bfs_solve.py` or a direct BFS over the maze lattice should clear the
remaining 8 levels the same way level 1 fell, PROVIDED the goal-square
hypothesis above is confirmed on level 2 first (find whether the piece
must exactly overlap the colour-14 cells, or merely become adjacent, by
watching one level-2 approach frame-by-frame instead of inferring it from
the transition).

