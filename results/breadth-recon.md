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
4. **The frame's inner is the counter, and the level ends on the DROP that fills
   the last slot -- not on the moment the count reads zero.** 10x2 = 20 cells at
   level 1; the three boxes cover 6 + 8 + 6 of it. CORRECTED 2026-08-08 by an
   audit of this file against its own run: the count reaches zero at step 24, an
   ordinary `left`, with `lvl` still 0, because the piece is standing over the
   frame and the zero is OCCLUSION. The level flips at step 26, the `act5` that
   drops the crate (`wa30-solve.txt`). The first write-up cited step 26 for the
   6 -> 0 transition and paired two different rows; the mechanic survives -- the
   consumption is real and was separately measured from afar
   (`wa30-p5.txt`) -- but the evidence pointer was wrong, and it was wrong in
   this repo's oldest way: a count read while the piece was standing on the thing
   being counted.

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

### tr87 level 1 FALLS: the win is a five-station SIMULTANEOUS combination lock, decoded from the un-explored top glyph region (2026-08-08, later)

Persistence and a null hypothesis, both cheap (`results/tr87-probe12.txt`): the
dial state at a station is NOT tied to the clamp's presence -- read directly
from a DIFFERENT station column with no return trip, byte-identical every
time (leave station0 at phase3, read its window from station1 and station2,
still phase3; walking back confirms the same) -- so "align all five" was
never impossible, the earlier open question is answered YES. Refuted in the
same run: visiting all five stations with zero dial presses (`ACTION4` x5,
no `ACTION1`) never trips `levels_completed`.

SHAPE match (not exact byte match) against the hint band, cross-station
too, is REFUTED cleanly (`results/tr87-probe13.txt`): built every station's
7-state deck, computed cell counts and a canonical form under all 8
dihedral transforms (rotations + reflections, direct and inverted-ink
polarity), and checked all 5 hints against all 35 states. Cell-count
coincidences are common (the five decks all draw counts from the same
small set `{14,15,16,17,19}`) but **zero shape matches survive
rotation/reflection**, own-station or cross-station.

The real answer was in the un-examined top region (`results/tr87-probe14.txt`,
`tr87-probe15.txt`, `tr87-probe16.txt`). It is not "six 7x7 tiles" loosely --
column-run segmentation on the background colour finds exactly two 17-wide
runs (x12-28, x35-51), each holding THREE row-bands (y4-10, y13-19, y22-28):
**six (icon, block) pairs**, an icon (colour-10 background, ink=5) beside a
block (colour-7 background, ink=5) previously assumed solid and never
dumped -- it isn't; every one of the six carries its own 5x5 texture
(`results/tr87-probe15.txt` census). Cropped to the same 5x5 interior every
other region here uses (1-cell border stripped) and run through the
dihedral-canon machinery from probe13:

- **The six ICONS identify a STATION.** Five of the six shape- (four) or
  byte- (one, `top-icon(2,0)` exactly equals `hint@22`) match one of the
  five hint-band icons one-for-one -- `(0,0)~hint29`, `(0,1)~hint36`,
  `(1,0)~hint43`, `(1,1)~hint15`, `(2,0)==hint22`. The sixth, `(2,1)`,
  matches none of the five hints -- not a station label.
- **The six BLOCKS identify a PHASE.** Each block's texture exact- or
  shape-matches one specific state in the SAME station's own 7-state deck
  (identified via its paired icon): `(0,0)->station29 state3` (exact),
  `(0,1)->station36 state6` (shape), `(1,0)->station43 state5` (shape),
  `(1,1)->station15 state5` (exact), `(2,0)->station22 state5` (shape).

Five pairs, five stations, no overlaps, one target phase each -- this is
level 1's full combination, not a per-level index into six levels as
guessed in "Not attempted" above (the sixth pair, unlabeled by any hint, is
not part of it; not investigated further).

Single-station tests refute the "any one station alone" reading
(`results/tr87-probe17.txt`): station29 alone at phase3, and station22
alone at phase5, both leave `levels_completed=0` even with the clamp
returned to x15 afterward (final clamp position is not gating either way,
on this evidence).

**Setting all five simultaneously wins** (`results/tr87-probe18.txt`,
re-verified clean in a fresh process `results/tr87-solution.txt`):
station15->5, station22->5, station29->3, station36->6, station43->5,
driven in that order. `levels_completed` flips to 1 on the action that
completes the LAST station (43), with the other four already holding
their target -- consistent with a pure AND-condition over all five dials,
checked continuously. 28 actions total (`results/tr87-solution.txt`,
action list
`1,1,1,1,1,4,1,1,1,1,1,4,1,1,1,4,1,1,1,1,1,1,4,1,1,1,1,1`),
well inside the 54-action level-1 baseline.

Not re-derived, still true: the shape-match refutation above is about the
HINT BAND specifically (a station's own display never matches its overhead
hint by shape either); the win condition lives in the previously-unexamined
top glyph region instead, and the "Not attempted" idea that it was six
per-level hints was half right (it does hold per-level information) and
half wrong (five of the six pairs are this level's per-STATION targets,
not a single pointer). Levels 2-6 are unmeasured -- whether the top
region's content changes with the level (a fresh 5-pair combination each
time) or whether the sixth unlabeled pair becomes relevant later is open.

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


## sb26 level 1 is a measured wall: every input channel is dead at every reachable state (2026-08-11)

Board (`results/sb26-found.txt`): four framed boxes across the top in colour
order 9, 14, 11, 15; a machine at y24-35 whose slot row holds four 2x2
colour-2 marks; four solid 4x4 blocks at the bottom in the different order
14, 15, 9, 11; a full-width colour-2 row at y53. Actions `[5, 6, 7]`,
baseline 18 for level 1 -- it reads like "click the bottom blocks in the top
row's order", and it is not:

- **ACTION5 is a pure timer burn**: one cell of the y53 row per press,
  right to left, GAME_OVER at press 64, nothing else ever changes
  (`sb26-p4.txt`).
- **ACTION7 is free and silent**: 70 presses burn nothing and change
  nothing, alone or interleaved with burns (`sb26-p4.txt`), and one to
  three presses after k burns for EVERY k in 0..63 neither win nor change a
  cell (`sb26-p5.txt`).
- **Clicks are dead EVERYWHERE at EVERY state**: a stride-2 full-grid sweep
  (1,024 spots, one episode each) changes zero cells (`sb26-p3.txt`); the
  block/box/machine spots re-clicked at every bar length in one episode
  never answer either, and a click does not even tick the clock -- so it is
  swallowed before the game logic, not rejected by it (`sb26-p6.txt`).
- Click sequences over the bottom blocks in both plausible orders: nothing
  (`sb26-p3.txt`).
- `obs.frame` holds exactly one layer at every state seen (`sb26-p6.txt`),
  so no animation channel is being missed.

Open: what a human's first effective input on this level even is. The next
instrument would be reading the engine's action schema for sb26 specifically
(does its complex action want data keys other than x/y?) -- but that borders
the answer key; the honest next step is the same as dc22's: back of the
queue.

## sk48 FALLS: a skewer machine, and the win is threading the recipe in order (2026-08-11)

Board (`results/sk48-found.txt`): a machine rides a vertical track (step 6),
its 2-row woven arm (`112112`/`211211`, period THREE -- not a cell-by-cell
alternation) extends right; three 4x4 blocks sit against the right wall (8 at
y19-22, 9 at y25-28, 14 at y31-34); the bottom HUD draws the machine with the
arm out and the blocks threaded on it in order 8, 14, 9. Actions
`[1, 2, 3, 4, 6, 7]`: 1/2 = track up/down, 4/3 = extend/retract, clock at y53
burns one cell per THREE actions (~192-action life), 6/7 unused.

- **Piercing**: extending until the braid reaches a block threads it; the
  block then rides the arm (retract pulls it along) and rides the machine
  vertically. The win fires ON the pierce of the last recipe block -- no
  delivery trip (`sk48-p5.txt`, frame-by-frame).
- **BFS found the line a hand model missed**: 14 actions vs baseline 61
  (`sk48-bfs.txt`, `bfs_solve.py` at depth 40 with the clock row masked;
  replay-verified forward-only in a fresh process, `sk48-verify.txt`). The
  hand model had invented a "dispenser queue" (blocks sliding left after a
  grab) out of misread x-offsets -- the blocks were riding the arm; and read
  a refused vertical move as a block "dropping off". Both wrong readings are
  the occlusion/part-of-a-thing trap family again.
- **The rung is `skewer.py`** -- signature: one live braid pair + solid 4x4
  blocks both inside the arm's room and outside it (the HUD picture);
  measured against all seventeen reset frames, sk48 alone
  (`sig-sweep.txt`). Controls learned by need (three of six actions are
  dead from reset -- the no-op trap), floor latched per level (with the tip
  pressed against a block the cell past it is the BLOCK), room flooded from
  both sides of the arm (fully extended it SPLITS the floor in two). Clears
  level 1 in 24 actions, score-capped same as the 14-line
  (`sk48-skewer1.txt`).
- **Level 2 is the same machine with a REARRANGE puzzle**: four blocks in
  one row (recipe [8, 12, 9, 14] against row order 14, 9, 12, 8 from the
  machine); ploughing straight through threads all four in the wrong order
  and does not win. The mechanic that reorders them is unmeasured -- its own
  project, like tu93's level 3.

## bp35 opened: the board is two vertical CONVEYORS, and the instrument wall came first (2026-08-11)

**The BFS instrument is dead on this game** -- bp35's own (obfuscated) game code
recurses infinitely on a `deepcopy`'d env: RecursionError at the default limit
AND at 20,000, same one-line frame repeating, under an ordinary `step` of the
copy. Every other playable game deepcopies cleanly, so the likely mechanism is
an object-identity invariant (a visited set, a memo keyed on `id()`) that the
copy breaks. `bfs_solve.py` gained two things on the way: a dead-action latch
(25 consecutive None answers retires an action -- bp35/cn04's click raises
inside the game and every attempt logged a full traceback) and the higher
recursion limit. sp80's control line `[4,4,4,5]` is intact after both.
Forward-only probes are the only road here.

**Measured so far** (`bp35_p1.py` -> `results/bp35-p1.txt`, `bp35_p2.py` ->
`bp35-p2.txt`): actions `[3, 4, 6, 7]`, click raises (cn04-class, retire it);
y63 is a counter row filling one cell per action. The piece is the 4x5
colour-9/11 marker in the bottom box; A3/A4 slide it 6px left/right, refused
at walls. TWO frame layers -- layer 0 is the mid-animation position, useful
as a free direction reading. **A7 from reset is a no-op; later it moves the
piece or fires the big event -- context-dependent, unmapped.**

**The 1,141-cell event**: when the piece arrives under the x43-47 chute, the
WHOLE BOARD rearranges. Comparing full dumps (reset vs after): the left
column x13-29 went from [3-block group, box] to [box, 3-group, 3-group,
3-group]; the right column x31-53 from [box, 4-group, box] to [box, 4-group
lower]; the chute itself moved y30-36 -> y48-54 and the bottom box shrank.
Both columns SHIFTED with new content entering -- two vertical conveyors
stepping past a fixed transfer point, not a camera (the piece's screen rows
did not move). The event also fires on A7 from some states.

Open, in order: (a) map A7's contexts (when is it a no-op / a piece move /
the event); (b) does the event REPEAT deterministically -- dump three
consecutive events and diff the conveyor steps; (c) what the win condition
could be -- baseline 21 for level 1 is roughly piece-to-chute (4) + a few
events + slack, so "step the conveyor until some alignment" is the shape to
test first.

### bp35, second pass: A7 is LEFT, the event fires on every chute crossing, and crossings are a BUDGET (2026-08-11)

- **A7 is a move-left** -- piece_x walks 44 -> 38 -> 32 -> 26 -> 20 under
  repeated A7 and no-ops at the left wall, which is why it read "no-op" from
  reset (the piece starts against that wall) and "context-dependent" before:
  the roster's no-op trap, third appearance this campaign (`bp35-p3.txt`).
  Why the game has TWO left actions (3 and 7) is unknown -- suspect they
  differ somewhere not yet visible.
- **The 1,141-cell event fires on EVERY crossing of x44** (under the chute):
  A4 arriving, A3 leaving, A7 leaving -- all fire it (`bp35-p3.txt`,
  `bp35-p4.txt`).
- **Crossings are a BUDGET, not a pump.** Shuttling across the chute fires
  events that ERASE the board from the bottom up -- bands y48+ empty first,
  then y42, y36 -- while bands y0-36 hold perfectly still; at the SIXTH event
  the run is GAME_OVER (`bp35-p4.txt`). The final event also degraded the
  right column's 4-block group to ~1 block. Reading: each crossing burns a
  finite tape (fuel? terrain passed?), and whatever the level wants must
  happen within ~5 crossings. The rocket-shaped piece (9 body, 11 flame)
  suggests an ASCENT frame -- each event one stage climbed, the emptying
  bands the world passing below -- but that is a hypothesis, not a
  measurement.
- Next probes: (a) what distinguishes A3 from A7; (b) dump the FULL frame at
  each of the six events in one run and diff properly (the band fingerprint
  hides sub-band structure -- the "static" top may be animating inside
  bands); (c) steer DURING the burn: cross once, then explore with A3/A4
  between crossings and watch whether the e-block groups interact with the
  piece at all.

### bp35, third pass: the piece has a HEADING, the erasure is a RISING FLOOD, and only the first event climbed (2026-08-11)

Full-frame dumps at every event of one run (`bp35_p5.py` -> `bp35-p5.txt`):

- **The piece carries a heading marker** -- the colour-11 cell sits on
  whichever side the piece last walked (`599b` at reset, `5b99` after an A3
  leg): wa30's edge-marker lesson, fourth game. Any reader keyed on the
  9-cells alone reports a position that shifts on turns.
- **The bottom-up "erasure" is a RISING FLOOD of colour 15** -- a woven f
  pattern climbing ~one band per chute-crossing event from y62 upward, on
  the same colour the y63 action counter uses (mask both before any census).
  GAME_OVER at the sixth event = the flood reaching the piece's chamber. The
  crossings-are-a-budget reading stands, with the mechanism now visible.
- **Only event #1 rearranged the tower** (the ascent-shaped shift); events
  2-6 raised the flood and moved nothing above y36. Hypothesis: entering the
  chute-aligned column ascends ONE chamber, and the chute the piece came up
  through is the y48-54 stub visible BELOW it afterwards; the shuttle's
  later crossings happened inside one chamber and only fed the flood. If
  right, level 1 is "climb chambers faster than the flood": find each
  chamber's upward passage, park under it, and never waste a crossing.
  Untested.

Next session: (a) after event #1, walk the FULL width and log where the next
event fires -- that maps the new chamber's passage; (b) climb as fast as the
passages allow and see whether the level falls; (c) A3-vs-A7 discriminator
still unknown.

### bp35, fourth pass: the trigger is ARRIVING at x44, and nothing else on the floor triggers anything (2026-08-11)

`bp35_p6.py` -> `bp35-p6.txt`, two fresh episodes after event #1: walking
LEFT the full width (44 -> 14) and RIGHT to the wall (44 -> 50) fires ZERO
events and never moves the tower. With `bp35-p4.txt`'s shuttle (which fired
on every return) the discriminator is clean: the event fires on the piece
ARRIVING at x=44 -- standing under the chute -- not on crossing that column,
and no other x in the bottom chamber triggers anything. So: every x44
arrival raises the flood one band; the FIRST arrival also stepped the tower
once; arrivals 2+ moved nothing above y36 in that run. Why only the first
climbed is THE open question -- candidates: the chamber above was blocked
(the 4-group sat at y31-35 after step #1), the climb needs an arrival from
a specific side, or A7 (which reads as a REVERSE move -- it went left while
the heading marker pointed right) does something at x44 that A3/A4 do not.
Level-1 baseline 21 says the whole dance is ~5 climbs' worth of actions.

### THE CLICK WAS NEVER AIMED -- repo-wide, and it is one line (2026-08-11)

`compete.py:1965` attaches click coordinates with `clicker.set_data({...})`
and then calls `env.step(clicker)`. The local wrapper builds its own
`ActionInput` from its own `data` kwarg and never reads the action object
(`local_wrapper.py:234`: `ActionInput(id=action, data=data or {})`), so
every click this agent has ever made arrived with `data={}`.

Measured side by side, same game, same coordinates, one invocation
(`results/click-probe.txt`):

| game | `set_data` then step | `step(action, data={...})` |
|---|---|---|
| cn04 | DEAD -- `KeyError: 'x'`, obs None | alive, state NOT_FINISHED |
| bp35 | DEAD -- `KeyError: 'x'`, obs None | alive |
| dc22 | alive (its game tolerates the missing key) | alive |

So **CLAUDE.md's cn04 trap is wrong about whose bug it is**: "cn04's own
`step()` raises `KeyError('x')` on its complex action" is this call site,
not the game. The play loop's guard (a click answered with `obs=None`
retires the clicker for the run) has therefore been firing on the agent's
own malformed call, on every click game, from the first click.

What the aimed click finds, in games where the un-aimed one found nothing:

- **dc22**: 35 components clicked one per fresh episode
  (`results/dc22-click.txt`) -- exactly two respond with real changes,
  (48,19) n=129 and (48,36) n=97; everything else answers 1 cell (the
  action counter). breadth-recon's "63 single clicks all eventually answer
  zero changed cells" was 63 un-aimed clicks.
- **bp35**: the click is the game's whole second verb (below).

Not yet changed in `compete.py` -- that is a gated edit (17-game sweep) and
`kaggle/adapter.py:83`'s proxy `step(self, action)` takes no `data`, so the
bundle needs the same widening or it breaks on the first click.

### bp35, fifth pass: the flood is an ACTION TIMER, the click is the verb, and the tape only oscillates (2026-08-11)

Four of the earlier readings do not survive per-action tracing
(`bp35_p7.py`/`bp35_p8.py` -> `results/bp35-p7.txt`, `bp35-p8.txt`):

- **"The event fires on ARRIVAL at x44" is false.** p4 read a `>100 cells`
  threshold as one event class; it is two. The 1,141-cell TOWER step fired
  once, at the first arrival; the 357-444 cell events at i=15,17,19,21 are
  the FLOOD rising and are not positional at all. Ten further arrivals at
  x44 fired nothing.
- **"Crossings are a budget" is false -- the budget is ACTIONS.** Pressing
  A3 into the left wall, doing nothing at all, floods at action 8 and is
  GAME_OVER at 16 (`bp35-p8.txt` E8). A run with one tape event floods at
  16 and dies at 24; a run with four events was still dry at action 40
  (`bp35-climb1.txt`). The law that fits all four runs: **flood starts at
  action 8 + ~8 per tape event, then climbs one band every 2 actions.**
- **A3 and A7 differ by exactly 4 cells, the heading marker** (E1, byte
  comparison of two arms from the same state). A7 is the reverse move:
  same displacement, heading unchanged.
- **A6 is not a broken action, it is the CLICK** -- `KeyError: 'x'` was the
  un-aimed call above, not the game.

The mechanics, all forward-only and each with its run:

- **The tape is a stack of rooms.** The piece holds screen rows y37-41
  always; a ride scrolls the tape so the piece is in the room above (+18)
  or below (-18/-24, room heights differ).
- **A4 at the shaft column x43-47 rides UP when a shaft section sits above;
  A7 there rides DOWN when one sits below** (p12 E15: A7 at x44 fired 1343
  cells with the piece not moving). Returning to x44 from either side never
  re-fires (`bp35-p8.txt` E7, ten attempts).
- **A click turns a colour-14 block into colour-10 FLOOR** -- printed rows
  either side, `3eee35` -> `aaaaa5` (p12 E16).
- **A click on the block directly ABOVE the piece rides; a click anywhere
  else only clears** (`bp35-p13.txt`: x33/x39/x51 answer 36-43 cells, x45
  answers 1290-1381 and the tape moves).
- **Clearing the whole band does not buy a longer ride.** Arms A-D of p13
  land on the same tape position whether one block or four were cleared --
  a ride is one room, always.

Where it stands: the reachable set is two tape positions, T0 (one ride from
reset) and T1 (T0 + the click over the piece), and they map onto each other
-- click up, A7 down, forever (`bp35-climb1.txt`, 40 actions, no flood, no
level). At T1 the piece's room is x31-53 y37-53 with **background above it**
on its own side; the blocks that could be cleared sit at x13-29, behind a
one-column background gap at x30 that no click closes, and the walk left
stops at x=32 (p12 E15). A digging climber keyed on adjacency finds nothing
to click at all, because every block in this game is separated from every
room by that one-column gap (`bp35-climb2.py`, `bp35-climb2.txt`).

Open, in order: (a) what opens a passage on the piece's own side at T1 --
the candidates left are a click on a room/gap cell rather than a block, a
ride down to a room with a different geometry, or an x the shaft occupies
in some other tape position; (b) whether the tape is a LOOP -- ride down
repeatedly from reset and see whether new rooms arrive; (c) the win
condition is still unmeasured, and level 1's baseline of 21 actions against
a flood that starts at 8 says it is roughly two rides plus a dozen actions.

### bp35, sixth pass: the wall is the BLOCKS, and the room widens when they go (2026-08-11)

Three more measurements, same session (`bp35_p14.py`, `bp35_p15.py`,
`bp35_climb3.py`):

- **A ride is the same ride from every column.** At T0 four blocks sit over
  the room at x31-35/37-41/43-47/49-53 and the piece can stand under any of
  them; riding from x38, x44 and x50 lands on the identical tape position
  (`bp35-p14.txt` E17). The door is not the shaft column, but the ride is
  one room whatever door is used.
- **Riding DOWN bottoms out at the starting position.** A7 at the shaft
  column from T0 returns the reset tape every time, six in a row
  (`bp35-p14.txt` E18) -- so as driven, the reachable tape is exactly three
  positions.
- **The wall the walk hits is the BLOCKS, not the one-column background gap
  at x30.** At T1 the walk left stops at x=32; clear the three blocks in the
  room's own row band and it runs 44 -> 14, with the uncleared control
  stopping at 32 in the same invocation (`bp35-p15.txt`). So clearing is how
  the room grows, and the left column's own overhead doors are reachable
  after all -- p14's "three positions" is a statement about an UNCLEARED
  board.
- **What broke the first attempt at that was the picker, not the game**: it
  took the median of every colour-14 cell near the piece and landed between
  two blocks, clearing a neighbour. A block is a door only when it overlaps
  the piece's own five columns.

`bp35_climb3.py` (overlap picker, clear-then-walk-then-ride) rides four
times in eleven actions and still does not finish the level; it then wedges
clicking a phantom target that answers one cell. Level 1 remains unwon and
the win condition remains unmeasured -- what is now cheap to ask, with
clearing understood, is whether the level wants a particular room ENTERED or
simply every block gone.

### bp35 LEVEL 1 FALLS -- 20 actions against a baseline of 21 (2026-08-11)

Full line, two identical runs and the mechanics behind each step:
`results/bp35-solution.txt` (`bp35_p17.py` -> `bp35-p17.txt`, `bp35-p17b.txt`).

**The win is a colour-7 object the piece walks onto**, and the reason
fourteen probes never saw one is that it only exists in the room reached by
the THIRD ride -- which is only reachable after clearing the blocks that
wall the room in, which was only measurable once the click was aimed. The
chain: ride the reset chute, ride again off the block overhead, clear the
room's row band (the walk then runs 44 -> 14 instead of stopping at 32),
ride from the LEFT column, walk back right, ride once more -- and that ride
brings the colour 7 down from y19-21 into the piece's own room at y37-39,
two steps away.

So p14's "the reachable tape is exactly three positions" was a statement
about an uncleared board, and this is the second time in one session that a
reachability claim expired with the equilibrium it was measured in.

Not in the agent: this is a hand line. A bp35 driver in the six drivers'
shape needs its signature measured by `sigs.py` over all 17 reset frames
before wiring, and the cascade order re-checked.

### dc22 LEVEL 1 FALLS -- 20 actions against a baseline of 59 (2026-08-12)

Full line and the board model: `results/dc22-solution.txt` (`dc22_climb.py` ->
`dc22-climb1.txt`, `dc22-climb1b.txt`, two identical runs). Recon:
`dc22_p1.py`/`p2`/`p3` -> `results/dc22-p1.txt`, `dc22-p2.txt`, `dc22-p3.txt`.

**Both of §dc22's standing verdicts were artefacts of the un-aimed click.**
"Clicks are INERT on this level -- 6 floor/panel spots, all 20 object centres,
double-clicks, pairs: zero play-area cells changed, ever" and "the piece's
room is SEALED -- all nine positions probed in all four directions" were
measured through `set_data`, which the local wrapper ignores, so every click
in that campaign arrived at one empty-dict destination. Aimed, exactly two
targets answer, and they are BUTTONS:

  * (48,19) swaps the colour-8 block between a 6x4 at (12-17, 30-33) and a
    4x6 at (18-21, 24-29) -- a bridge, stood up or laid down;
  * (48,36) swaps the checkered 9/4 pad at (8-11, 34-37) with the solid
    9-block at (18-21, 20-23) -- checkered is WALL, solid is FLOOR.

The room is sealed only while that pad is checkered. Pressing the 9-button is
the level's first move, and the walk that recon called impossible then runs
from y40 to y30 (`dc22-p3.txt` E7/E8: 9 reachable positions become 18).

The genre is now legible: the colour-4 field is void, blocks are the only
ground, the buttons lay the route, and the piece walks to a marker that wears
the same frame the piece does. Level 2 is unseen; a driver is a BFS over
(position, toggle state) with the toggles learned in four actions, since they
are reversible.

### sb26 LEVEL 1 FALLS -- 9 actions against a baseline of 18 (2026-08-12)

Full line, controls and the retraction: `results/sb26-solution.txt`
(`sb26_p1.py`/`p2`/`p3`, `sb26_solve.py` -> `results/sb26-p1.txt`,
`sb26-p2.txt`, `sb26-p3.txt`, `sb26-solve1.txt`, `sb26-solve2.txt`).

The click is half a DRAG: click a bottom block to select it, click one of the
machine's four colour-2 slot marks to load it. Load all four in the order the
TOP row names, then press ACTION5 -- the action §sb26 recorded as "a pure
timer burn, nothing else ever changes" -- and the machine runs. Loaded in the
blocks' own order instead, the same ACTION5 answers one cell and nothing
happens, so the control discriminates.

**All three of §sb26's "measured wall" readings were readings about an
unreachable state set.** The 1,024-spot click sweep measured one destination
1,024 times (the un-aimed click); ACTION5 and ACTION7 were both characterised
on an EMPTY machine, which was the only machine that could exist while no
click could land. That is the third game today whose wall dissolved with the
click fix, after bp35 and dc22 -- and the general form is worth keeping: a
channel can read dead because the state that wakes it is only reachable
through a channel that was broken.

Also measured in passing (`results/click-sweep-all.txt`, every playable game
with a complex action swept at reset, one fresh episode per component):
ka59 answers two clicks of 3 cells each, sc25 answers NONE of its 22
components, and g50t has no complex action at all -- so of the four remaining
zero-level games, only ka59's walls could still be a click artefact.

### ka59: the click is a PICKUP-AND-FERRY, the right room falls open, and the win is still unmeasured (2026-08-12)

Probes `ka59_p1..p8` -> `results/ka59-p1.txt` .. `ka59-p8.txt`. What the aimed
click adds to the standing model:

- **The click answers only when aimed at the grey dot or its ring, and it
  moves the PIECE onto the dot's square** -- not a general teleport (seven
  other targets across the map answer nothing, `ka59-p2.txt`).
- **The dot is CONSUMED by that click**: it is gone from the frame even after
  the piece steps away (`ka59-p3.txt`), and the piece then walks with its
  ring travelling around it -- n=18-19 cells per move against 8-9 bare
  (`ka59-p6.txt`) -- which reads as a carried state.
- **The right room is reachable for the first time in the campaign**: kick
  the dot east (it flies to its invariant landing at (43,31), across the
  colour-15 bar), then click the landing -- the piece follows it over. The
  74-state keyboard BFS was the state space of a game whose second verb had
  never landed.
- The whole right room was walked from inside (`ka59-p6.txt`): open floor,
  the hollow slot, no new objects, no colour-5 anywhere.

Measured dead, one fresh episode each: standing in either slot with or
without the carry, clicking every distinctive target from the carried state
(all n<=1, `ka59-p7.txt`), bump-dropping against every right-slot wall,
kick-without-follow with the piece parked in the left slot / either ring, and
holding through two full timers in the right room -- the 100-action death
fires there too (`ka59-p8.txt`).

Open, sharper than before: the drop verb, if one exists, is none of {stand,
click self, click destination, bump}; and the win may need the dot IN a slot,
which no measured verb can do -- the kick lands it at (43,31) invariantly and
the click eats it. The next instruments: (a) does a SECOND kick geometry
exist -- kick the dot north/south within the corridor by approaching on
different rows (the recon note says "every row tried" but predates the aimed
click); (b) whether the ring travelling with the piece can be handed back --
click the EMPTY ring left in the corridor was n=0, but only from two standing
positions; (c) sc25-style: the win may simply not involve the slots.

### sb26 LEVEL 2 FALLS -- the recipe walks the MACHINE PATH (2026-08-12)

L2 board: seven recipe boxes, seven stock blocks, and TWO machines -- three
slots up, four down, joined by a colour-14 pipe. Loading in recipe order was
correct but every hand-guessed slot mapping was silent, and A5 turned out to
be an all-or-nothing oracle. Two instruments settled it:

- **A7 is UNDO** -- it pulls the most recently placed block back to stock,
  one per press (`results/sb26-l2d.txt`, cells diffed). So the game keeps an
  insertion stack, which put frame-dedup search off the table (two states
  with one frame can differ in history -- the sp80 hidden-state law).
- **A5 is position-pure**: the same assignment loaded in two insertion
  orders answers identically (`results/sb26-l2-dfs.txt` soundness lines).
  That licence is what made the search sound: pin the insertion order to the
  recipe, exhaust WHICH SLOT each colour takes -- 7! = 5,040 leaves, winner
  at the 34th (`sb26_l2_dfs.py`).

The winning order is geometric: **upper row left to right, with the whole
lower row spliced in where the pipe interrupts it** -- U22, U28, [pipe] L22,
L28, L34, L40, U40. Replayed forward-only twice, identical: level 2 in 15 of
its own actions (`results/sb26-l2-solve.txt`).

`sorter.py` now reads slot rows across machines and orders them by that
path; the driver clears both levels in 24 actions (`results/sorter-try5.txt`)
and sb26 smokes at 2/8 `[9, 15]`, 8.333%.

### bp35 level 2: a clear-order puzzle, and three of its rules measured (2026-08-12)

Probes from the driven L1 (`bp35_l2a..e` runs -> `results/bp35-l2a.txt` ..
`bp35-l2e.txt`). The board: the piece starts under TWO full seven-block
bands, above them an open mid room, above that a top room holding three
colour-15 doors with 11-0-11 marks -- colours `tape.mark()` deliberately
ignores (15 is the flood, 11 the heading, 0 the counter), which is why the
driver wanders 2,202 actions there.

Measured, each with its run:

- **A ride into an uncleared room KILLS.** Click the block over the piece
  (ride #1) lands the piece in a pocket inside the lower band; riding again
  puts it inside the upper band's blocks and the run is GAME_OVER
  (`bp35-l2c.txt`, n=1569). L1 never taught this because its rooms were
  empty. So on this board a ride must be PREPARED -- the destination
  cleared first.
- **Every block here clears, including ones over the piece's own column in
  higher bands** (n=31/37/36, `bp35-l2d.txt`) -- the L1 reading "a click on
  a higher block over the piece answers n=1" does not transfer.
- **Clearing can OPEN a chute, and walking into it is a ride with a death
  on the other end**: after clearing (27,33) a vertical open column stood
  at x25-29 beside the pocket (`bp35-l2e.txt` BEFORE frame), and the
  sideways step A4 into it fired a 1,561-cell tape event, the piece
  materialised nowhere, GAME_OVER. The walk itself is the trigger -- the
  L1 law "arriving at a chute column rides" -- but here the chute was
  MANUFACTURED by the clear, and its far end was not survivable.

- **Pre-carving makes even ride #1 lethal** (`bp35-l2f.txt`): clear the
  band-2 block over the piece FIRST and the very ride that was survivable
  bare now kills (n=1576) -- because a ride runs TO THE FIRST BLOCK, not one
  room (L1's own E13 law: clearing the block over the chute doubled the
  trip). The pocket only exists if the block above it is still there. All
  four deaths (l2c, l2d, l2f x2) end in the same frame family: the tape
  scrolled until the door room sits just above the piece row, and the piece
  is nowhere.

- **The full-shaft carve dies too** (`bp35-l2g.txt`): both bands cleared in
  one column from a distance, walk back in -- the arrival ride fires
  (n=1586) and the piece is gone, same terminal frame family as the other
  three deaths. So "rides stop at the first block" does not rescue a longer
  shaft; whatever the ride does past one room is lethal REGARDLESS of what
  was cleared, and the next instrument has to read the DEATH itself
  (layer 0 of the frame -- L1's probes saw mid-animation positions there)
  before any more lines are spent.

Open: the safe clear order -- rides stop AT blocks, so the shaft must be
carved to stop the piece exactly one room short of danger each time, which
makes this a planning puzzle over clear-sets, not a walk. The 11-0-11 marks
under the three doors are presumably the ask; nothing has reached the top
room alive. Cheap next instruments: ride #1 bare (survivable), then from
the pocket clear sideways and STAY within the band, working horizontally
toward the side chute at x25-29 WITHOUT stepping into it; and dump what
distinguishes the three doors from the mid room before approaching.

### dc22 level 2: two toggles, a 405-state graph, and no win inside it (2026-08-12)

The bridge driver clears L1 and stalls on L2 after pressing both panel
buttons from one spot (`results/dc22-l2a.txt`). What the level holds:

- the piece starts at the BOTTOM (x17-19, y53-55) and the twin marker sits
  at the TOP (x20-23, y12-15); between them a horizontal colour-8 band
  (y24-27), a colour-9 column, a colour-7 column and a colour-6 bar.
- **both L2 buttons are PURE TOGGLES**, measured cell-by-cell twice each
  (`dc22-l2b.txt`): (52,22) swaps colour 7 between a vertical column
  (x16-19, y32-51) and a horizontal bar (x8-27, y40-43); (52,40) swaps
  colour 9 between (x4-7, y32-39) and (x8-11, y28-31). Press twice =
  byte-identical board.
- that purity makes frame-dedup BFS SOUND here (unlike sb26's stack), and
  the search exhausts: **405 states over {4 walks, 2 buttons}, depth <= 40,
  no win** (`dc22-l2-bfs.txt`).
- a full component click-sweep on the L2 board finds NOTHING beyond the two
  buttons (`dc22-l2c.txt`, 52 targets, 2 responders).

⚠️ Weigh this against ka59: its "74 reachable states, no level-up" was also
an honest exhaustion, of a game whose second verb had never landed. Here the
click-sweep says there is no unlanded click. The depth-80 rerun
(`dc22-l2-bfs80.txt`) closes two of the holes at once: **512 states (the
depth-40 cap had hidden 107), zero terminal transitions, no win** -- so
nothing in the graph even dies, and "a fall pruned as GAME_OVER" is refuted.
What remains outside the instrument is TIME: the y63 step counter is masked
out of the state key (it advances every action, so keying on it makes every
state unique), and a mechanic gated on it -- stand somewhere for N steps --
would be invisible to this search by construction. That is the sp80
hidden-state law from the third side: masking a counter is as much a claim
as keying on it.

bp35 L2 and dc22 L2 are now both walls with their shape measured; sb26's L3
is unexplored and its driver generalised once already.

### sb26 LEVEL 3 FALLS -- the machine path is a TREE walk (2026-08-13)

L3's board (`results/sb26-l3b.txt`, clean dump): seven recipe boxes, seven
stock blocks at the BOTTOM, an upper machine with three slots and TWO pipes,
and two framed sub-boxes below it -- a colour-14 frame holding two slots and
a colour-9 frame holding two. The pipes' frames wear the sub-boxes' colours,
but colour is not the rule (level 2's pipe is colour 14 over a colour-8
machine); x-nearness is.

The order that wins -- first guess, straight from the tree reading, two
identical forward-only runs, reversed-order control silent
(`results/sb26-l3c.txt`): **walk the upper row left to right, and at each
pipe splice in that pipe's OWN box's slots**: U21, [e-pipe -> E19, E25],
U33, [9-pipe -> N38, N44], U45. Level 3 in 15 of its own actions.

`sorter.py` generalised: pipes are read from the row ABOVE the slot row
(on the slot row itself a pipe is two width-1 wall runs and any width
filter drops it -- the first generalisation broke level 2 exactly there,
`sorter-try6.txt`), each lower slot homes to its nearest pipe in x, and the
order is the depth-first walk. The driver also had an INFINITE LOOP fixed
in the same change: on a wrong full load it tried every plain action, and
the last one is A7 = UNDO, so the load dropped by one, it reloaded, forever
(~2,000 actions of it on the first L3 contact, `sb26-l3a.txt`). The
run-button hunt now happens once per level.

Driver clears all three known levels in 39 actions (`sorter-try7.txt`) and
answers None cleanly on level 4.

### sb26 level 4: the pre-load is a decoy, and 5,160 assignments are dead (2026-08-13)

L4 arrives mid-loaded: recipe b,8,e,9,6,c,f; b and 8 sit in the upper
machine, e in the middle one, and the bottom row holds 6,c,f,9 plus two
colour-2 holders and an e44e frame (`results/sb26-l4a.txt`).

Measured, in order:

- **The driver read the two pre-loaded blocks as pipes** (width-4 runs in
  the row above the slot row -- exactly where pipes live) and built a
  nonsense order; it answers None safely but its L4 geometry is wrong.
- **A7 unwinds the game's own pre-load**: 8 returns to the bottom holder at
  x31, then b to x10, then the stack is EMPTY -- so e is a FIXTURE of the
  middle machine, not a placed block, and the bottom row's two 22-holders
  are b's and 8's home squares (`sb26-l4c.txt`). The pre-load is therefore
  part of the PUZZLE, not part of the solution's prefix.
- The pre-loaded blocks are selectable (b, 8 answer the 20-cell border);
  the middle machine's e is not (n=0). The bottom holders accept blocks;
  the e44e frame does not (`sb26-l4b.txt`).
- **Assignment search is exhausted twice**: with b,8 left where the game
  put them, all P(5,4)=120 placements of 9,6,c,f (`sb26-l4-dfs.txt`); and
  after unwinding, all P(7,6)=5,040 placements of b,8,9,6,c,f with the
  insertion order pinned to the recipe (`sb26-l4-dfs2.txt`). No win in
  either. Three hand-built "machine path" lines with an invisible pipe
  between U25 and U31 are also silent (`sb26-l4d.txt`).

So L4 falsifies one of the assumptions the first three levels licensed.
The candidates, in order of likelihood: **insertion ORDER matters here**
(L2's position-purity was measured on L2 alone, and a search over both
order and slots is 6! x P(7,6) -- needs a smarter oracle, not brute force);
A5 must be pressed mid-sequence (per machine?); or the win reads something
the frame shows that the slot model does not (the e44e frame's role is
still unexplained). Next instrument: measure order-dependence directly --
pick ONE full assignment, load it in several insertion orders, and diff
the A5 answers; any difference collapses the space to order-search.

### sb26 LEVEL 4 FALLS -- the hollow block was the missing piece (2026-08-13)

The wall broke on a re-read of one old measurement. `sb26-l4b.txt` E3 had
recorded "9 -> e44e frame: n=20" as *the frame does not take a block* -- but
n=20 is the SELECTION border, so that click had actually selected the frame:
**the hollow e in the bottom row is a real, placeable block**, the level's
eighth. With it in the pool the recipe's colours all exist in stock (its e
means the hollow block; the middle machine's solid e is a fixture with no
slot mark), the eight slots and eight blocks match, and the assignment
search that had exhausted 6,000 leaves without it finds the winner at leaf
17 of 120 (`sb26-l4-dfs4.txt`): hollow-e at U31, then 9,6 in the middle
box, c,f at U37,U43. Forward-only twice, identical; a control with hollow-e
and c swapped is silent (`sb26-l4-solve.txt`). Level 4 in 11 of its own
actions.

The generalisation that came out is SIMPLER than the pipe reading: **a
child machine splices into the upper row at its own x-centroid** -- level
2 (pipe 34, centroid 32), level 3 (22.5 / 40.5), level 4 (31.5, pipe
invisible) all agree, and the pipe detector had misread level 4's two
pre-loaded blocks as pipes anyway (a placed block IS a width-4 run in the
pipe's row). `sorter.py` now: unwinds game-placed blocks with A7 at level
entry (one press per filled slot; LIFO back to their holders), reads stock
from the band's top edge (a hollow block is solid there), and orders slots
by the centroid splice. Driver clears all four levels in 54 actions
(`sorter-try8.txt`) and answers None on level 5.

### sb26 level 5, first look: duplicate recipe colours and two hollow 9s (2026-08-13)

One dump only (`results/sb26-l5a.txt`, board reached by the driver's 54-action
L1-L4 run). What breaks each assumption the driver carries:

- **The recipe has DUPLICATE colours**: nine boxes reading 6,e,8,8,e,8,8,b,f
  (8 four times, e twice). `read()` rejects any recipe with duplicates -- a
  rule that was load-bearing on L1-L4 -- so the driver answers None before
  trying anything.
- **Stock is eight blocks including TWO hollow 9s** (9-frames with hollow
  interiors, the L4 hollow-e shape), and the recipe names NO 9 at all.
- Slots: five upper, three lower in a single colour-9-framed child box --
  eight slots for eight blocks, so the count closes; what is open is the
  MAPPING. Duplicate colours make "insertion pinned to the recipe" ambiguous
  (four 8-entries against two solid-8 blocks), and the hollow 9s must stand
  for something -- the L4 precedent says a hollow block is a real block, and
  the frame colour of L4's hollow-e matched the recipe entry it filled, so
  the hollow 9s matching the CHILD BOX's frame colour may be the hint.
- Next instruments, in order: (a) greedy load with exact-colour matching
  along the machine path, hollow-9s tried in the two plausible roles (as the
  extra 8s / as the extra e), A5 per arm -- four arms; (b) if silent, the
  assignment space is small enough to exhaust once the insertion-order
  question is settled the L4 way (A7-unwind first to check for pre-loads --
  none were visible in the dump); (c) the recipe row may also need re-reading
  -- nine boxes over eight slots means at least one box is not an entry.

### sb26 FALLS COMPLETELY -- the hollow block is a SUBROUTINE CALL (2026-08-13)

Levels 5-8 all fell in one session, and the mechanic they teach is one idea
deepening: **a hollow stock block is a REFERENCE to the box wearing its frame
colour, and the recipe is a box's contents flattened, references expanding
recursively.**

- **L5** (instruments (a)+(b) above): the four greedy arms all load cleanly
  and A5 answers a single cell -- which `sb26-l5-cell.txt` shows is just the
  y53 TIMER advancing, identical for a plausible arm and an absurd control,
  so there is no feedback channel. The 10,080 distinct assignments (8 blocks,
  two colour-pairs interchangeable) with insertion pinned to the machine path
  were then exhausted the L2 way: winner at leaf 1,211 (`sb26-l5-dfs.txt`),
  forward-only twice + swapped control (`sb26-l5-solve.txt`). The winning
  shape: recipe [6,e,8,8,e,8,8,b,f] = upper row [6, 9h, 9h, b, f] where each
  hollow-9 expands to the child 9-box's content (e,8,8) -- loaded ONCE,
  called twice. Soundness check (one assignment, two insertion orders, same
  A5 answer) passed before the search ran.
- **L6** (first try, no search): recipe [9,b,b,c,f,f,e,6,6], four boxes --
  8-framed root with three slots, and e/9/c-framed boxes each carrying one
  FIXTURE block and two slots. Root = [h9, hc, he]; each expansion = fixture
  + slots: (9,b,b),(c,f,f),(e,6,6). The generalised reader cleared it on its
  first run -- strong validation of the grammar.
- **L7**: nesting two deep, [8,9,e,b,e,9,8] (a palindrome) = 8-box
  [8, ref9, 8] -> 9-box [9, ref-e, 9] -> e-box [e, (b), e]. Three new facts:
  HOLLOWNESS IS PER-RUN not per-colour (stock holds two solid 9s AND a
  hollow 9); a fixture may sit mid-box wearing a foreign colour (the b
  between the e-box's slots); boxes stack outside the middle third (y16 and
  y42 on a 64-high board). Wall-pair grouping replaced gap-grouping: a
  width-1 run is a wall, width>=3 a fixture, and two slots 12 apart with a
  fixture between them are one box when the same walls enclose them.
- **L8** (two variants seen -- BOARDS ARE RANDOMISED PER EPISODE): the
  recipe row is written TWICE (two identical bands, y1-6 and y8-13) and
  means the concatenation -- two unrollings of an INFINITE expansion.
  Variant 1: 8-box [8, b, ref9, ref8] SELF-REFERENCING, 9-box fixtures-only
  (c,9,e,f), stock just h8+h9 with six empty holders. Variant 2: mutual
  recursion, 8-box [8,b,c,ref9] / 9-box [9,e,f,ref8], six solids + h8 + h9.
  Matching is therefore PREFIX match against the truncated unrolling. The
  final reader enumerates block-to-slot assignments (multiset perms, engine
  untouched -- flatten is pure computation) and tries every box as root,
  unpointed boxes first; a slotless box nothing points at is a wall
  artifact (0-cornered frame rows read as walls around one long run) and
  gets dropped, or it steals the root.

Driver clears ALL EIGHT levels in 123 actions, state WIN
(`sb26-drive7.txt`). pytest 330 green. sb26 done: 4/8 -> 8/8.

### ka59 FALLS -- the click was a SWAP all along, and the detectors were colour-blind (2026-08-13)

Level 1 in 14 driver actions; `ferry.py` is the tenth driver. The chain that
broke it, because each probe's failure taught the next one's instrument:

- **Movement is a 3-cell lattice step, and it checks only the LANDING cell**
  (`ka59-p11.txt`: every direction moves exactly 3; `ka59-p14.txt`: pressing
  south at (13,31) lands the piece INSIDE the "closed" left box at (13,34),
  stepping over the wall). Both slot boxes are enterable; three days of
  probes had treated them as sealed.
- **The kick has a flight cap of ~15 cells, passes over the colour-15 bar,
  and is clamped by outer walls** (28->43 east over the bar; 19->10 west
  into the wall). The corridor is a dead-end arm (x24-32 exists only on
  rows 30-32), so the east kick is the ONLY reachable one at spawn -- the
  north/south/west kick geometries do not exist there.
- **The aimed click is a SWAP, not a consume** (`ka59-p16.txt`, the probe
  that finally did a full-colour census per press): the piece teleports to
  the dot's square and the dot -- RECOLOURED 5 -> 4, the boxes' own colour
  -- lands on the piece's old square. Every earlier probe searched colour 5
  only, so the swapped dot vanished from their reads and "the click
  consumes the dot" went unchallenged into three probe generations.
- **The win: 4-dot in one box, piece in the other** (`ka59-p18.txt`,
  verified twice + floor control in `ka59-solve.txt`): kick the dot east,
  stand inside the left box, click the dot (the swap places the 4-dot in
  the box and teleports the piece across the bar), walk into the right box.
  Level fires the moment the piece lands inside.

Driver notes: geometry (bar + boxes) is cached per level -- a travelling
ring parks against a box wall and occludes it from a live read (the landed
dot's ring erased the right box; the piece's own ring erased the left one
mid-walk); the piece/dot reads are cluster-centroid with spread <= 2,
because animation frames smear the piece over 2-4 cells. Signature: piece
in a 14-ring + 5-dot in a 14-ring + full-height 15-bar + two closed 4-boxes
= ka59 alone (`sig-sweep-ferry.txt`, VERDICT PASS).

Level 2 (`ka59-l2.txt`): a different animal -- THREE dots of different
shapes (1x2, 2x1, 2x2), four boxes of different interior sizes on both
sides of a vertical bar, piece bottom-right. Smells like size-matching the
swaps into the right boxes; the driver answers None there cleanly (its
exactly-one-object read rejects the multi-dot board).

### Agent-fleet night (2026-08-13/14): six games probed in parallel, one fell, four walls got their true shape

Six sonnet subagents ran the measured-probe loop per game (scripts `<game>_q*.py`,
results `results/<game>-q*.txt`), main thread verified evidence files and
integrated. Round counts: sc25 x5, g50t x3, bp35 x4, dc22 x2, ka59-L2 x2, tu93 x1.

- **tu93 L3 FELL** (see the maze L3 playbook in `maze.py`): deepcopy BFS found a
  19-action line (q7), forward-only verified twice + one-action-short control
  (q8, re-run by the main thread in `tu93-q8-main.txt`). Hazards = three
  notched-3x3 pieces (body 8, notch 15); the killing one JUMPED onto the cell
  the piece was stepping into, reactive not clock-driven (q6); the y63 budget
  row burns ~1-2 cells/action and its GAME_OVER is distinct from hazard death
  (q5); GAME_OVER resets scope to the CURRENT level (q8). Caveat kept: the
  agent's claim that bare-Maze driving dies mid-L2 contradicts the sweep's
  [31,14] -- artifact of driving outside compete.play; not acted on.
- **sc25's "clicks are dead" was FALSE** -- three days of probes never aimed at
  the southern half. The board is two puzzles: a rigid 4x4 two-tone block in a
  corridor it can never pass (footprint never changes; N/S only flip the
  colour halves in place -- q9; round 1's "(+4,0) from N/S" was a discover.py
  multi-object aliasing artifact, settled q11), and **box B: a 3x3 grid of
  independent 2-state click-toggles** (q12/q13). 4-edges-all-14 = a penalty
  event that wrecks the piece (q14). The full 2^9 pattern space (480
  non-penalty patterns, Gray-code walk, 13 lives, 549 actions) contains NO win
  (q16) -- box B is closed as the win mechanism. Only EDGE-block clicks burn
  the x62-63 death timer (4 cells/click). Open: box A (click-inert so far),
  piece-x-pattern interactions.
- **g50t's phantom mechanic found and closed**: recall-after-travel toggles a
  2-state indicator (q5; round 1 read one half of the cycle as a "permanent +4
  shift") -- inert w.r.t. reachability. The old exhaustive BFS's key was SOUND
  (source-read q: p3/p5 mask only the clock row). The wall's final shape (q8/q9):
  the gate's opening is MOMENTARY -- it reverts the instant the piece steps off
  (38,8), the gate room is a dead end so stepping off is mandatory, and with the
  segment hypothetically held open a 13-waypoint path reaches the goal box. The
  78-action baseline vs 0-wins-in-130-BFS contradiction stands, now narrowed to
  "what could hold the opening".
- **bp35 L2's death and budget law**: a ride is a tape scroll; a killing ride
  BURIES the piece (its cells painted over by unconverted block texture
  scrolling through, q2). Only the near band rides (far-band clicks just clear,
  q5). The ride budget is ONE PER LIFE (q8) -- but the board fully REVERTS on
  every reset (byte-for-byte, two episodes, q9), so no multi-life ladder
  exists: L2 must fall within one life, one ride. Bonus: the piece's sprite
  paints background over adjacent floor, so room extents read ~5 cells short
  when measured with the piece next to the boundary (q7/q8).
- **dc22 L2 CLOSED as measured-unsolvable under the current action model**: the
  timer row y63 is a pure decoupled life-clock (~190 actions, q3), toggles are
  clock-phase-invariant (q5), and an exhaustive joint (position x toggle-bits)
  BFS -- the exact blind spot hypothesised for the old 512-state exhaustion --
  fully exhausts with no path (q9). No third button exists (q10); the void gap
  and goal cell are click-inert (q11). De-prioritised.
- **ka59 L2**: ring-size == box-interior-size matching discovered (dot0
  3x6<->box1, dot1 6x3<->box3, dot2 6x6<->box0; box2 3x3 matches the PIECE --
  standing in it empty-handed recolours it and clears the dotless spawn ring,
  q17). The click-swap needs NO proximity (q4) and does NO size validation
  (q16). But the left region (box0/box1) is unreachable: flood-fill over the
  3-cell lattice from all four occupancy phases never crosses the moat (q20),
  so every reachable placement was made (q15/q18) and the level does not
  complete. Parked pending a new verb. A walk() bug in ka59_solve.py (edge-
  triggered levels_completed) was found and worked around by the agents --
  ferry.py does not share that code.

### Agent-fleet wave 2 (2026-08-14 early hours): two more fell, two walls shaped

- **cn04 FELL — driver #11 `claw.py`**: ACTION5 = quarter-turn, moves = 3-cell,
  and the game sets a TRAP — the wrong handedness (1 rotate, not 3) gives the
  identical tip-to-tip vector and renders the same "docked" third colour
  without winning. The 14-action line (rotate x3, down x7, right x4) verified
  twice per process, cross-process by the main thread (`cn04-q11-main.txt`),
  with truncation AND false-dock controls. Sweep: cn04 [131] -> [14], 0.233 ->
  4.762% (`sweep-claw.log`, 16/17 identical, control cn04). L2 is a four-shape
  jigsaw (12 pads, `cn04-q12.txt`) — untouched.
- **tr87 L2 FELL — dial.py playbook**: the L2 station-naming scheme is the
  four hint-labelled icon groups FLATTENED IN HINT-BAND X ORDER (not the top
  region's row-band order — that hypothesis failed cleanly first), block-counts
  1/3/2/1 summing to exactly the 7 stations. Verified x3 + a per-station
  wrong-phase control; main thread re-verified the 58-action line
  (`tr87-verify-main.txt`, winner x2 = lvl 2, one-short control = lvl 1). The
  30-action L2 segment ships as a playbook in dial.py (one data point for the
  convention; generalise at L3). NOTE: the agent's later probe scripts
  (q13-q19) were run inline and exist only as results files.
- **sk48 L2 wall shaped**: retract does NOT keep the tether (it snaps mid-drag
  and strands the block where the arm was — a third outcome vs both round-1
  hypotheses), a re-plowed block re-pierces at its OWN original slot, and the
  arm is one continuous strip built outward from the housing — so first-contact
  order is structurally fixed at row order and REORDER IS IMPOSSIBLE with the
  four live verbs. All-four-pierced-at-once does not win. Deep BFS (sound per
  its own two checks) is 2x rounds of ~40 min, both stuck near depth 16,
  frontier growing — not exhausted. Refuted across rounds: LIFO-unload, clicks,
  second entrance, touch-order-without-retract, reorder-via-retract.
- **re86 L6 wall shaped**: reach-elasticity re-verified on a second axis
  (square DOWN-compress conserves sum 36 AND persists after walking away —
  the first valid persistence result), but the plus COLLAPSES 48 -> 24 on
  LEFT-compress at this wall face (discontinuous, permanent, reproduced at two
  offsets), and its redistribution grows DOWN at RIGHT's expense — so the
  needed (3,3,18,18) profile at centre (12,9) was never reached; boxes never
  consumed. Round 2's "unmapped NW obstacle" was refuted by a clean static
  dump (only the wall + the pen exist); the anomalies were real shape-edge
  geometry. Next lever: find a compression route for the plus that avoids the
  LEFT-collapse face.
- dc22 L2 (closed), sc25 (box-B space exhausted), g50t (momentary gate),
  bp35 (one-life-one-ride, board reverts), ka59 L2 (left side unreachable) —
  see the wave-1 section above.

### Agent-fleet wave 3 (2026-08-14 ~03:00): three more fell, one driver bug found by its own book

- **ar25 FELL — driver #12 `mirror.py`**: a colour-10 wall splits the board;
  the colour-5 player and colour-4 MIRROR sprite move in lockstep (vertical
  same, horizontal OPPOSITE — the old CLAUDE.md trap note "ar25 answers
  ACTION3 with right" was reading the mirror, not the player). Win = drive
  the mirror onto the static colour-11 target; ONE axis exact suffices.
  15-action line [down x10, left x5], verified x2 + 3 controls, main-thread
  re-verified (`ar25-verify-main.txt`). Sweep [173] -> [15], 0.095 -> 2.778%.
- **m0r0 FELL — driver #13 `twin.py`**: two 5x5 pieces on SHARED controls in
  non-mirrored halves; the win is piece A reaching one specific coarse cell.
  27-action joint-BFS line, verified x3 + 3 controls, main-thread re-verified
  (`m0r0-verify-main.txt`). Sweep [53] -> [27]. L2 = same mechanic, 4px step,
  colour-8 checkerboard patches unexplained.
- **sp80 L2 FELL — swap.py playbook**: the aimed click is a MAGAZINE-FREE
  control transfer to any colour-8 body — a verb the old exhaustive 39k-state
  BFS structurally never had (it predates the click transport fix). Re-running
  the same BFS recipe with click edges found the win at ~5k expansions: the
  win is gated on TWO bodies' positions at once (80-body parked right x2 AND
  block1 walked right x3), refuting every single-body map. Line
  [4,4,click(13,17),4,4,4,5] verified x2 + 3 controls, main-thread re-verified
  (`sp80-verify-main.txt`). Sweep sp80 1/6 -> 2/6. Also closed: L1's win is a
  literal level-complete, not a hidden control-transfer.
- **wa30 L2 = haul.py's own bookkeeping bug, precisely caught**: L2 grew an
  AUTONOMOUS CONVEYOR (one un-slotted crate at a time turns ring 4->5, slides
  4 cells per player action toward a slot, x-aligns then y-aligns, settles,
  reverts) and haul.py's `self.filled` is asserted at plan-commit and never
  re-checked — at the reproducible stuck frame two "filled" slots were live-
  empty and two conveyor-filled slots were "free": livelock at action 105
  (`wa30-q9.txt`). Fixed in `_slots()`: keep the latched book AND drop slots
  that read occupied on the live board, excluding any slot the piece
  overlaps (the oscillation trap the latch was guarding against). The fix
  swept clean (no regression) but did not yet clear L2 — the conveyor
  interplay needs its own line. Also: haul.py's "NOT wired" docstring is
  stale, and the solid colour-12 4x4 at (24,36) is WALKABLE, not an obstacle.

### Agent-fleet wave 4 (2026-08-14 ~05:00-08:00): tu93 L4 fell; five walls got measurably harder shapes

- **tu93 L4 FELL — maze.py SCRIPTS table**: BFS 515 expansions -> 17-action line,
  forward-verified x2 + one-short control on the 81-action combined line
  (`tu93-q9.txt`, main-thread re-run `tu93-q9-main.txt`). maze.py's playbook
  generalised to a per-level SCRIPTS dict gated on (x0,y0,body) hazard spawns;
  L4 adds a new hazard skin (body 12, notch 15). Smoke: 4 levels in 80 actions.
  PENDING the next sweep (goes into the wave-5 gate).
- **tr87 L3 (3 rounds, parked)**: station IDs via hint-offset -3 are almost
  surely right; the 49-combo ambiguous-pair brute, offset +4, pairing rules
  (column-alignment, ignore-icons e1/e2), and the 5-station theory (49/49,
  stations 8/50 untouched) are ALL refuted; nearest-LEFT and row-below rules
  don't even cover 7 stations. The icon->block TARGET assignment rule is the
  hidden piece. Next: hybrid coverage rule, sweep station 8 jointly,
  shape-canon check, order-dependence (`tr87-q23..q26.txt`).
- **sp80 L3 (2 rounds + r3 in flight)**: model overturned — FIRE from a block
  = unconditional return-to-driven (position-free); FIRE from driven = grabs
  block2 only inside castle0's zone, once; CLICK = universal control-grab any
  time. 12 x-left compositions + seeded BFS (4808 nodes) failed; block1/driven
  (w=24) can never reach castle2-left (clamp 40). Y-axis, right/centre
  alignment, closing-fire = r3 (`sp80-q13..q23.txt`).
- **cn04 L2 (4 rounds, parked)**: TWO instrument bugs corrected — reset()
  re-scopes after any L2 action (blind L1 replays corrupt state), which had
  faked both "randomized per process" AND the "first-press jump" (L2 is
  DETERMINISTIC; first presses are clean 3-cell steps). Pad ownership
  0:2/9:2/11:4/14:4. The whole docking family is now exhausted: the one
  same-shape pad-pair candidate, sequential singles, hidden flags, wide arm,
  boundary-interlock across ALL FOUR distinct A5 silhouettes (A5 cycles 4
  different cell-sets, not 2 — states 0/2 and 1/3 share bboxes only), and the
  socket/concavity fit (0%). Colour-3 = transient overlap indicator, no
  persistence. Wall = non-geometric (`cn04-q20..q44-summary.txt`).
- **m0r0 L2 (3 rounds, parked)**: checker bands are Y-band hazards firing
  from every column and direction (silent both-pieces respawn); B is Y-locked
  to A with X mirrored, and r1's "B boxed to 3 cells" was a DFS bug (A's
  un-mirrored deltas) — B's true region is 37 cells, fully covered, no win;
  the joint space is ONE DIAGONAL (rowA==rowB, colA+colB==14, 0 exceptions).
  Clicks inert at 7 targets. Next: exhaustive clicks across both mapped
  regions (`m0r0-q37..q40.txt`).
- **ar25 L2 (3 rounds, parked)**: A4x5 aligns the player's true bbox EXACTLY
  onto the colour5 dock (the dock paints OVER the player — the "wall
  occlusion" was false); position space exhausted, no win. A5 scatters the
  colour0 markers but they oscillate between two 8/4-cell subsets (7% of the
  dock's 116 empty cells — slot-fill refuted). New unexplained: an aimed
  dock-centre click changes 21 cells elsewhere; A5x5-then-A4 leaves player -3
  and frozen. Third colour5 component = a top-right A5-press clock
  (`ar25-q12..q15.txt`).

Wave-4 addendum (sp80 r3, `sp80-q24..q29.txt`): placement is 2D (all four
bodies step 4 cells on A1-A4) BUT a hard y=16 ceiling bars every body from
the castle band (y4-11) — castle-adjacency in any form (left/right/centre/
raise) is structurally dead. Click-back-then-fire adds nothing (auto-return
already covers it). Seeded BFS grew to 6532 nodes with no plateau and no
win. New unexplored mechanic: two bodies overlapping can GAME_OVER outside
of FIRE. Next levers: block-RELATIVE offsets (never castle-keyed), a
multi-hour BFS, block2-as-final-actor.

### Agent-fleet wave 5 close-out (2026-08-14 morning)

- **tu93 SOLVED WHOLE — 9/9, GameState.WIN** (driver: maze.py SCRIPTS L3-L9,
  WIN at 201 actions in-driver; sweep 22.222 -> 100.0). Levels 5-9 each fell
  to the same loop (determinism check, dedup-soundness fork, deepcopy BFS,
  forward-verify x2 + one-short control) — `tu93-q10..q14.txt`, main-thread
  re-verified `tu93-win-main.txt`. Gate lesson: the L8 spawn-gate written
  from the agent's hand census FAILED in-driver; the driver's own
  notched_all read differs — gates were re-measured through the driver's
  eye (instrumented run) and pinned to THOSE censuses. The gate must match
  the eye that reads it.
- **cd82 L1 decoded + driver #14 roller.py**: the piece is a tumbling
  roller (same action twice = no-op; alternation required) — the visible
  correlate of the "hidden state" that made the generic engine burn 1,306
  actions revisiting one object 22x. ACTION5 paints the wedge of the target
  facing the roller; L1 = below + x-aligned = [3,2,3,2,4,5], verified x2 +
  no-align control (`cd82-q13..q16.txt`, main `cd82-verify-main.txt`).
  Sweep [1306] -> [6]. L2 = same mechanic + third colour + diagonal split
  (`cd82-q14.txt`) — next lever queued.
- **wa30 L2's true wall = a 70-action level clock**: every life GAME_OVERs
  at exactly action 70 (11 lives byte-identical, two movement patterns);
  the conveyor delivers at most 2 of 5 crates in that budget hands-free
  (`wa30-q11..q13.txt`). Next: haul-carry + conveyor combined under 70.
- **ka59 L2 closed harder**: colour-14 is a halo not a wall; full boundary
  scan = min moat thickness 9 (no 3-step crossing anywhere); board
  deterministic across episodes (`ka59-q21..q23.txt`). Left boxes
  unreachable under the verb set, period.
- **re86 L6 physics revised again**: the up/down collapse keys on centre-y
  inside the wall's y-span at ANY x (refutes round 3's box-proximity
  story); pen extent + an (6,39) marker-vanish anomaly unresolved
  (`re86-q16..q19.txt`).
- **sk48 exhaust** (r3): hash-only dedup proven sound; 800k-node BFS run —
  final verdict in `sk48-q14.txt` (the agent's completion report is
  pending; read the file before citing exhaustion).
- **Kaggle**: v7 scored 0.10 (vs v1 0.11, baseline 1.56) — drivers are
  ~irrelevant on the hidden 110; adapter v8 (pushed, kernel v8) adds a
  claim-gated play slice (unclaimed games: 60s play, rest to mop-up) and a
  STATE-AWARE bandit ((frame-hash, action) table with global prior;
  unit-driven: per-state learning 239 vs 67). Submit v8 at the next 07:00.

### wa30 L2 FELL at the probe level (2026-08-14 ~09:40) — in-driver integration incomplete

The 68-action L2 line is PROVEN (agent wave-6: unmodified Haul to 5/6 filled
at tick 51, then FREEZE to harmless [1,2,3,4] cycling and the conveyor
delivers the last crate; clear registers at action 68 of the 70-action level
clock; verified twice byte-identically + a 67-action control that fills 6/6
but does not register — `wa30-q20..q23*.txt`, main-thread re-run
`wa30-q22-main.txt`). Root cause of Haul's old self-regression measured: a
QUEUED grab planned in the open matures into lifting a crate the conveyor
has since parked in a slot — Haul's `self.filled` only records its OWN
drops. haul.py got two safe additions (a pick-target guard that drops a
stale grab plan, and an idle-instead-of-surrender branch while un-slotted
crates remain) — pytest 330, no sweep regression — but the in-driver replay
still stalls (`wa30-haul-drive*.txt`, done latched with filled=3 and one
in-frame crate visible): per-level books go stale across the 70-action
deaths (Haul has no fresh-life detector the way swap/maze do). NEXT: add a
fresh-life reset (crate-count jump ⇒ board reverted ⇒ clear filled/queue)
plus freeze-at-5/6, then sweep. L3's entry frame is already captured in
`wa30-q22.txt` tick=68 (8x16 frame, 6 crates).

### sc25 CLOSED for the campaign (2026-08-14 ~12:30) — a completeness proof, not a sample

Round 7's full-grid flood fill (every one of 4096 cells) finds exactly 22
connected components, all classifying into the four known structures (timer
stripe, corridor/piece/target box, box A, box B) — ZERO unknown components
(`sc25-q21.txt`). Target-box interior + border: 0/34 clicks respond
(`sc25-q22.txt`). Combined with box B's 480/480 toggle exhaust, box A's
100/100 click sweep, the timer/top-region probes, and the piece's rigid
4-row footprint against a 2-row gap, every visible component is
individually refuted. Round 6 also CORRECTED the timer model: the x62-63
stripe burns on a general per-action clock (~60% rate) — no click type is
free (`sc25-q20.txt`). The win trigger, if any, is a combinatorial joint
state with no visible correlate. sc25 stays 0/6 until a genuinely new verb
idea arrives.

### g50t CLOSED for the campaign (2026-08-14 ~12:40) — live-exhausted, not heuristic-exhausted

Round 5's exhaustive live DFS pressed all four directions at every reachable
lattice cell: the region is EXACTLY 12 cells (the heuristic's 11 + the gate
room; the round-4 decorative-icon false wall was the only one). The west
segment opens only while standing at (38,8) and reverts on the FIRST press
of any departure (censused per press over the full 8-press route). Action
space = 5, no click. The goal box is >4 lattice steps beyond the only
(dead) route (`g50t-q14..q16.txt`). The 78-action-baseline contradiction
stands unexplained but every avenue in the current verb set is
live-refuted. g50t stays 0/7 pending a genuinely new idea (e.g. revert
keyed on something other than displacement).

### bp35 L2 CLOSED for the campaign (2026-08-14 ~12:50) — pure reel arithmetic, no bypass in 6 rounds

Round 6 refuted the last three instruments: ACTION7 is an ordinary -6
leftward move (the "L1 shaft-ride" premise was a misreading of the
deepcopy-corrupted bfs log; the L1 solve line never presses 7); the door
marks (colour-0 at y11) are inert to distance clicks singly and in
sequence; the floor's colour set pre/post-ride is exactly the terrain set —
no hidden win-mark (`bp35-q13..q16.txt`). With rounds 1-5 (ride = 6-row
reel shift, ONE per life, doors 26 rows = 4-5 shifts away and recurring as
decoration, pre-clear cascade lethal, board reverts per life), bp35 L2 =
doors unreachable within a life under every tested verb. Loose thread
recorded: A3 pitch measured -5 vs A7's -6. bp35 stays 1/9.

### cd82 L3 PARKED on an impossibility proof (2026-08-14 ~13:30)

The legend's four target regions are 43/35/12/10 cells; every producible
wedge is 50 (flat) or 55 (diamond) and the terminal paint always shows its
full mask — so NO order/colour/station assignment of the known verbs can
reproduce the target (`cd82-q37/q48.txt`). Seventeen candidate mechanisms
are measured dead across three rounds, including: five drag payload forms
(the SDK's ComplexAction schema has no second point; the unvalidated local
data path passes extras through and the game ignores them), legend
eyedropper, colour-11, repeat/timing variants, ring topology (8x4
brute-force table: closed, no 9th station), partial-paint boundaries
(pure-function wedges), the census window (verified against raw frame;
the out-of-window colour cells are a selection-preview tint on the roller
itself), and ACTION7 (does not exist in this game's action space).
cd82 stays 2/6; the sub-50-cell paint verb, if any, leaves no trace in
anything probed so far.

### m0r0 L2 CLOSED for the campaign (2026-08-14 ~14:30)

Round 4 swept clicks across both pieces' full safe regions (30/33 of A,
~24/37 of B before an API resource limit; the pattern is 100% null
throughout) — no click anywhere moves a piece, changes a colour, resets or
wins; the only diff is a global per-action counter tick reproduced by a
plain no-op, so "clicks are position-gated" is refuted (`m0r0-q41/q42`).
The diagonal invariant's MEETING cell (colA=colB=7) is confirmed
unreachable: column 7 is wall on every row except 11-12, which sit behind
an always-resetting hazard band from both sides (`m0r0-q44`). One
mid-sweep "unexpected reset" was retracted as a DFS bookkeeping artifact
after a clean two-run re-test with a stop-short control (`m0r0-q43`) —
worth remembering as the shape of a false positive. Only unexamined
surface left: whether ACTION6's data payload accepts more than {x,y}
(the same question cd82 answered NO for its own engine path). m0r0 stays
1/6.

### cn04 L2 CLOSED on geometry (2026-08-14 ~15:00) — the mover was the missing variable, and it changed nothing

Round 5 found the mechanic three rounds of geometry had been missing:
**ACTION6 click SELECTS which shape you control** (it recolours to the mover
colour; the previous mover reverts), each moves in 3-cell steps, selection
is exclusive and re-clickable (`cn04-q47/q48`). Round 6 therefore redid the
entire search with every shape as mover: 119 single-pad placements (4 movers
x 4 rotation states x every own-pad→pad pairing) and 48 best-per-group
boundary-interlock placements out of 855 candidates, ALL driven live — zero
wins (`cn04-q55..q58`). Multi-select persistence was verified first (a moved
shape keeps its position under its own colour when another is selected,
`q59`), then a live 3-phase composition assembled all four shapes into a
structurally-verified single connected mass — still no win (`q60`). Also
settled: colour4 is an action-budget bar (~1 cell per 3 actions, never
recovers), which explains the varying counts round 4 read as a docking
signal (`q46`). cn04 stays 1/6; every geometric hypothesis across five
rounds is exhausted, and the remaining candidates are non-geometric.

### ar25 L2 FALLS — the mark grants LEVEL 1's control scheme for one move (2026-08-14 ~15:20)

Nine rounds, and the door was a verb nobody had composed: an aimed click on
the DOCK's centre column (52,24) places a "mark" that grants exactly ONE
subsequent action under LEVEL 1's control scheme — which carries the
VERTICAL that unmarked L2 does not (unmarked: only ±6 horizontal) — and a
click on the WALL's centre (37,31) toggles the mark off, restoring normal
movement. So mark → step → untoggle is a CYCLE that walks the piece three
cells south at a time. Two unmarked left presses first put the piece in the
colour-11 shadow's own x-range (3-17); without that alignment the descent
freezes at y=27. Eight cycles cross the wall and clear the level: 40 actions
from reset, verified twice + a one-action-short control
(`ar25-q30/q31.txt`, main-thread `ar25-l2-verify-main.txt`), in-driver via
mirror.py's L2_LINE at i=39 twice. Corrections banked along the way: the
round-4 "click_x is a free variable, any column reachable" claim was false
(click_x is not a variable at all; only two trigger points exist); the
round-4 "WIN at press 64" was a false positive from `state != NOT_FINISHED`
also matching GAME_OVER; and "vertical is unreachable" — believed for five
rounds — was only ever true UNMARKED.

### re86 L6: enclosure, centre-landing and scenery contact all inert (2026-08-14 ~15:30)

Round 8 tested the reframed hypotheses from round 7's geometry closure:
driving the ring's hollow interior to strictly contain each box (4/4
colour-9, 3/4 colour-11), driving the plus inside the ring, landing each
shape's CENTRE exactly on its own-colour boxes (all 8 — survivable, which
refutes cover.py's generic "centre on a frame cell is GAME_OVER" for
own-colour pairs, and consumes nothing), pressing into the colour-1 wall
(refused 13 cells early — the arm tip, not the centre, is what the refusal
checks) and along the bottom bar, and three two-shape arrangements. ~150
live presses, no level change (`re86-q39..q42.txt`). Also measured: a
blocked press is still charged budget. Unresolved: a ±1 off-lattice jitter
in the ring's tracked centre near dense colour-11/colour-1 regions, most
likely `at()`'s first-pixel heuristic rather than real movement.

### sk48 L2: the pierce is an EXTEND-ARRIVAL event, so the touch order really is forced (2026-08-15, main thread)

The agent-fleet round-4 report (`sk48-q20.txt`) reproduced the known wall — L2's stock is four
blocks on one row at x=30,36,42,48 wearing `[14, 9, 12, 8]`, the recipe display below reads
`[8, 12, 9, 14]`, and `touch_order == list(reversed(recipe))`. It also, without meaning to,
exposed the one state nobody had ever pressed anything from: the driver reaches
`pierced={8,12,9,14 all True}` at action 8 of level 2 and then **gives up with the state still
NOT_FINISHED**. That is sb26's law wearing sk48's clothes — a loaded machine needs the action
that RUNS it, and sb26's driver had to FIND that action by trying the plain ones. Three probes,
all from the fully loaded state, all with the load asserted before the probe and a noop baseline
measured alongside:

- **No plain action runs it** (`sk48-q21.txt`). Each of A1/A2/A3/A4/A7 pressed 1x/2x/3x from its
  own `deepcopy` of the loaded env: every arm stays `levels_completed=1`, `NOT_FINISHED`. They
  are not inert — A1/A2 move 305 cells, A3 20 per press, A7 4 per press — they just do not
  complete anything. The parent frame was re-read after every child and asserted byte-identical.
- **No click anywhere runs it** (`sk48-q22.txt`). All **4,096** cells swept with an aimed click
  (`env.step(action, data={"x","y"})`, the transport CLAUDE.md records as the only one the games
  read), each from its own deepcopy: **0 clicks changed a single cell**, 0 levelled up, 0 won,
  0 answered `obs=None`. This is a completeness proof for single clicks from that state, not the
  fourteen hand-chosen targets of `sk48-q2.txt`.
- **The verb map, measured at L2 ENTRY rather than at full extension** (`sk48-q23.txt`), is what
  reframes the wall. The arm does not start beside the blocks: it starts at rows **44/45** with
  its tip at **x=16**, far below the stock row (y=25). A1 lifts the machine **6 rows per press**
  (44 → 38 → 32 → 26), A4 extends the tip **6 columns per press**, A3 retracts it, and at entry
  A2 and A7 are exact no-ops. So the driver's rise-then-extend crosses the blocks left to right
  because that is the order it chose, not obviously because it is the only one.

**The hypothesis that follows, and its refutation** (`sk48-q24.txt`): extend FIRST along the empty
row 44 until the tip is past x=48, THEN lift into the block row — now the only direction the tip
can travel across the blocks is leftward under A3, which is `8, 12, 9, 14`, the recipe in order.
Three arms off one deepcopy'd entry state, with the known behaviour as the control:

    A (control) rise x3 then extend  ->  pierces 14, 9, 12, 8 at tips 34/40/46/52, lvl stays 1
    C  extend to tip 52 on row 44, then rise into rows 26/27, STOP  ->  pierced = [] 
    B  extend to tip 52, rise, then retract 16 -> 52 across every block  ->  pierced = []

The control reproduces `[14, 9, 12, 8]` exactly, so the instrument is sound. Arms C and B pierce
**nothing at all**. That is the real mechanic and it is stronger than the thing it refutes:
**a block is pierced only when an EXTEND press lands the tip on it.** An arm that is already long
when it arrives in the row pierces nothing (C), and retracting back across four blocks pierces
nothing (B) — the `Skewer.pierced` detector agrees, since what it reads is braid arriving on the
block's LEFT. So the touch order is not an artifact of the driver's choice: rightward extend is
the only piercing motion, and block 8 at x=48 can never be first.

Together with `sk48-q21/q22`, L2 is now a wall with a measured shape rather than a search that
ran out of time: the load is reachable and complete, and from it every plain action and every one
of 4,096 clicks is a no-op. What is NOT proven is that no longer sequence exists — the deep BFS
runs (`sk48-q4/q11/q14.txt`) explicitly report `exhausted=False` at depth ~19 against a ~192-action
life. **sk48 L2 is PARKED**, and the next lever is not another verb hunt: it is either a
full-life search or a mechanic no game in this campaign has shown yet.

### wa30 L3: an AUTONOMOUS CONVEYOR delivers two crates by itself, and the driver livelocks chasing a third it is already carrying (2026-08-15, agent fleet round 5 + main thread)

L3's board is a much bigger version of L2's: an 8x16 frame (84 empty interior cells, ring 9,
inner 2) at (52,24), three to four times L1's twenty-cell frame, plus five 4x4 crates (ring 4,
inner 9) at (32,32), (32,12), (20,20), (12,44), (8,16). The level is NOT randomised — the reset
frame and the whole 113-action L1+L2 prefix are byte-identical across two independent processes,
with a positive control proving the equality check can fail (`wa30-q40..q42.txt`). So a fixed
line is the right target in principle.

**The new mechanic, and it is not L2's conveyor.** A colour-12 4x4 "cursor" slides 4 cells LEFT
along row y=12 on every player action, whatever the action was and wherever the piece is. When it
reaches a crate it flips that crate's ring 4 -> 5 ("activated"), and the crate then slides 4 cells
per player action toward the frame **on its own** (`wa30-q43.txt`). Idling — pressing only
directions, never GRAB — therefore delivers **2 of the 5 crates hands-off**, the two sitting on or
near the cursor's sweep path, after which it stalls for the rest of a life (`wa30-q45.txt`).
L3's life clock is **99 actions**, measured identically three times, against L2's 70.

**Where the driver stops.** Warm-started exactly as `compete.play` does — one `Haul` carried
through L1 -> L2 -> L3, `dirs` learned on L1 and never re-learned — it clears L1 in 43 and L2 in
70, then on L3 manually delivers ONE crate beyond the conveyor's two, reaching three filled slots
`{(52,24), (52,32), (56,32)}` within ~85 actions, and never adds a fourth: flat across **2,500
actions and 23 life-boundary resets** in one run and reproduced in a second
(`wa30-q46/q49/q50.txt`). What it does instead is re-plan a pickup for a crate near (28,28) whose
position **drifts by 4 cells between successive plans** — that is a third crate the cursor has
also activated and is carrying, and the pick/carry cycle never converges.

Two readings were refuted along the way, both worth keeping:

- **The 63 -> 75 rise in the frame's interior count is NOT piece occlusion.** The piece's bbox
  never overlaps the frame's bbox in that run, and the non-overlapping readings alone still show
  the rise (`wa30-q47.txt`). It is the delivered crate's own multi-tick transit animation passing
  through the frame's bounding box — the thing `_confirm_delivered`'s transit note already names.
- **"The whole-board colour-2 census goes flat at 51" is the wrong metric**, and it is the one an
  earlier round reported. It mixes the frame's true interior with the moving rail and cursor's own
  colour-2 pixels, and it describes the IDLE condition (no GRAB at all), which is not how the
  driver plays. The real wall is 3 slots of N via `crates()`, not 51 cells.

Also refuted: the stall being the life clock (`filled` is flat at the same three slots across 23
resets; idling stalls at two well before any boundary) and the stall being "no reachable crates"
(two to three loose crates are present every stalled round, including the one being chased).

**A latent driver bug found on the way, flagged not fixed** (`wa30-q48.txt`): a COLD-started
`Haul` — one built fresh at L3 rather than carried from L1 — hits `_slots()`'s `sy = ... or 1`
fallback, because no `dy != 0` entry exists in `dirs` at that call. The slot lattice degrades to
1-cell pitch and produces overlapping origins like (52,24)/(52,25)/(52,26)/(52,27), which one
delivered crate then retires wholesale. Real campaign play always warm-starts one `Haul` across
the whole game, so this never fires in a sweep — but any probe that constructs a driver at a
level boundary is measuring that bug rather than the game.

**Next lever** (not yet run): instrument `_slots()` and `_walk()` on a warm-started run to decide
whether the fourth-slot livelock is L2's pick-target GRAB guard firing on a conveyor-moved target
or the carrying branch clearing `pick_target` mid-delivery. The fix, if it is the former, is a new
guard shaped like the one `haul.py` already carries for L2 — *a crate under active conveyor
transit is not a crate to chase manually* — and it is a driver change, so it needs a full sweep
with wa30 as the positive control.

### ar25 L3 OPENS: the pegs are CLICK-SELECTABLE PIECES, and selection redirects every movement verb (2026-08-15, main thread)

The fleet's round-8 report shaped L3 as a piston puzzle: a 3-row colour-10 wall that A1 lifts and
A2 lowers three rows a press, A7 undoing one such press, **A3 and A4 inert**, and two static
colour-5 "peg" objects built of stacked 3x3 rings that nothing moved. Its ruled-out list included
"clicking peg centres produces zero state change". Three main-thread runs turned that inside out.

**`ar25-q50.txt` — the plain-action channel, closed completely.** Every reachable piston position
(drive A1 to the top edge and A2 to the bottom: **21 distinct positions**, rows (0,2) through
(60,62)) crossed with all six plain actions, each arm off its own deepcopy, parent re-read and
asserted byte-identical after every one. Nothing levels up, and A3/A4 change **zero cells at every
single position** — the sample-based "A3/A4 are inert" is now a complete statement.

**`ar25-q51.txt` — 86,016 clicks, and the by-product is the finding.** All 4,096 cells swept at all
21 positions. No click completes the level (the completeness proof the hand-chosen target lists
could not give), but **2,457 arms changed a cell — 117 at every position** — and they are not
scattered: x=12-14/y=21-28 and x=45-56/y=27-28, which is exactly where the two pegs are. The pegs
were always interactive; the earlier probe aimed at each blob's CENTROID, and a peg built of
stacked 3x3 rings has a hole there.

**`ar25-q52.txt` — what a peg click IS.** The 117 responsive cells form exactly **two connected
parts** (63 cells at rows 21-32/x12-23, 54 at rows 27-32/x45-56). One click changes ~27 cells,
mostly 0 -> 9, spread across x 1-61 — it draws something board-wide, it does not tint the peg.
Clicking the same part **twice is a no-op** (press 2 reproduces press 1 exactly). Clicking A then B
lands on B-alone's board and B then A on A-alone's, differing in 13 cells: **the last click wins**.
Idempotent, mutually exclusive, last-one-wins is not a dial — it is a SELECTOR.

**`ar25-q53.txt` — and the selector reassigns the controls.** Same six actions, three conditions:

    condition   A1    A2    A3    A4    A5   A7
    none       397   334     0     0    28    0      <-- reproduces q50 exactly
    selA        73    73    73    73    14    0
    selB        73    73    37    37    27    0

With nothing selected, A1/A2 move the 3-row piston (397/334 cells) and A3/A4 are dead. **With a peg
selected, A3 and A4 wake up**, and A1/A2 stop moving the piston: all four change 73 cells, which is
a peg-sized object moving. So level 3's grammar is *click a peg to take control of it, then the
four direction verbs drive THAT peg* — the piston was never the level's piece, and "A3/A4 are
inert" was a statement about the unselected condition, measured 21 times and true in all of them.

L3 is therefore a two-piece placement puzzle in the same family as L1 and L2 (where the win docks
the MIRROR on a colour-11 target with one axis exact), with four static colour-11 objects mirrored
top and bottom across the piston's start row as the candidate targets. Not yet solved: no arm here
won, including holding a selection through the piston's entire A1 x16 / A2 x4 range. What is now
open is a SEARCH over two pieces x four directions, which is a completely different problem from
the one the level looked like an hour ago.

### Two proposed driver patches, both measured before landing — one rejected, one held (2026-08-15)

Both came from agent-fleet diagnoses that were right about the CAUSE and untested about the FIX.
Each was applied TEXTUALLY to a copy of the driver's source, exec'd as a shadow module, and driven
against the unpatched original in the same run — so `dial.py` and `haul.py` were never edited and
no sweep was spent on either.

**wa30 / `haul.py` — REJECTED, it breaks level 1** (`results/wa30-q70.txt`). The diagnosis is
sound: `act()`'s queue-drain never checks that a popped queued action moved the piece, so a step
refused by terrain `_walk`'s BFS never modelled lets the rest of a 13-step plan fire from the wrong
square and the trailing GRAB drops the crate outside every slot (`wa30-q60..q65.txt`). The proposed
guard — on a refused step with a queue outstanding, clear `queue`/`pick_target`/`claim` — was
reasoned to be regression-free from the absence of refusals in unpatched L1/L2 runs. Measured:

    unpatched   L1 at 43, L2 at 113 cumulative, max filled slots 4
    patched     ZERO levels cleared, 3,000 actions burned, max filled slots 0

Haul's own pickup approach *presses into refusals on purpose* (`act` already special-cases the GRAB
with its `still`/`inside` checks), so a blanket "refusal means the plan is stale" kills every
delivery. The diagnosis survives; the guard has to exclude the deliberate-refusal cases. **An
argument that a patch cannot regress is not a measurement of whether it does** — this one cost a
two-minute A/B and would otherwise have cost a 100-minute sweep and a broken driver.

**tr87 / `dial.py` — VERIFIED CORRECT, and HELD because it is inert** (`results/tr87-q80.txt`).
Two fixes: `read_board`'s top-region boundary becomes "the last row before the hint band drawn in
any of the four tile colours" instead of a row-majority walk (which halts one row INTO content on a
dense board — L2 row 4, L3 row 7 — while L1's rows 34-39 are a solid block of a FIFTH colour, which
is why naively widening to `hint - 1` made L1 worse); and `top_pairs` becomes a full 7x7 border
scan with proximity dedupe and greedy nearest pairing, instead of a row-band scan that overwrites
its one icon and one block per band. Measured across all three levels:

    level   old top_end/pairs/combo    new top_end/pairs/combo
      1        33 /  6 /  5               28 /  6 /  5     <-- combination dicts EQUAL, not just equal-sized
      2         3 /  0 /  0               28 /  6 /  0
      3         6 /  0 /  0               28 /  8 /  0

L1 = 28 actions and L2 = 58 cumulative under BOTH readers, and L1's combination dict compares `==`
to the shipped one. The reader is strictly better — L2 and L3 go from zero readable pairs to six
and eight — but `combination()` still returns `{}` on both, because L3's icons match no station
hint under any transform (independently re-derived through the fixed instrument), so the level
count does not move: **plain 2, patched 2**. Landing it now would spend a full sweep on a
byte-identical outcome, which is the same call the repo already made for the four inert `ls20`
wirings. The patch text is in `tr87_q80.py` and lands with whatever finally decodes L3 — the named
next lever being to build each station's full 7-phase room deck by dialing and match the top BLOCKS
against the decks, inverting the documented icon-identifies/block-targets roles.

### ar25 LEVEL 3 FALLS — the piston is a PRECONDITION behind a one-way door (2026-08-15)

Level 3 is a third machine, unrelated to L1's lockstep mirror and L2's mark/untoggle cycle, and it
resisted three complete sweeps for one reason: **the control surface the win depends on becomes
unreachable the moment you engage the pieces.**

The grammar, measured (`ar25-q50/q51/q52/q53/q80.txt`): with nothing selected, A1/A2 drive the
3-row colour-10 piston (397/334 cells) and A3/A4 are dead at **every one of its 21 reachable rows**.
The two colour-5 "pegs" are click-SELECTORS — 117 responsive cells forming exactly two connected
parts, idempotent, mutually exclusive, last-click-wins — and the instant one is clicked, all four
direction verbs drive THAT PEG (73 cells) and A3/A4 wake up. Selection is a **one-way door**: a
background click, clicking the same peg, clicking the other peg, A5 and A7 all leave the peg
selected, and the piston cannot move at all while a peg is held.

So the piston's row has to be chosen **before the first peg click**, and every search that started
by clicking a peg was a slice at the entry row. That is why the following are all measured dead and
all irrelevant: each peg driven over its ENTIRE reachable grid alone at the entry row (324 + 360
cells, `q57`), the same at **all 21 piston rows** (14,364 cells, `q61`), and the full peg-A x peg-B
joint grid of **116,640 states** at the entry row (`q58`). Also dead: both pegs docked bbox-exact on
their size-matched targets at the entry row (`q55`/`q56`), and A5 pressed up to three times after
every such dock (`q59`).

The win wants both pegs docked on their **size-matched** targets — peg A is 12x12 (63 cells) and
bbox-matches only the two 12x12 targets, peg B is 6x12 and matches only the two 6x12 ones — with
the piston parked at rows 27-29. The 40-action level-3 line: **A1 x7** (piston up, nothing
selected), click (13,31) to take peg A, **A2 x7 + A4 x7** onto (42,53,33,44), click (51,29) to take
peg B, **A2 x5 + A3 x12** onto (42,47,9,20).

**Main-thread verified before wiring** (`ar25-q90.txt`): two independent fresh-Arcade replays of the
full 80-action line (L1's 15 + L2's 25 + these 40) reach `levels_completed == 3` at action index 79;
a one-action-short control stops at level 2; and a control that drops **only the seven piston
presses**, leaving every dock and click identical, also stops at level 2 — which is what makes the
precondition load-bearing rather than incidental. In-driver via `mirror.Mirror`: levels cleared at
i=14 / 39 / 79, twice. pytest 330. Gating sweep: `results/sweep-wave10.log`, control ar25.

The transferable shape, and it is worth checking elsewhere: **a win can depend on a control surface
that the puzzle's own main objects lock you out of, so the order of engagement is part of the
solution.** A search that begins by touching the pieces can be exhaustive and still never see it.

### cd82 L3 stays a WALL — but the round replaced a sampled impossibility proof with an exhaustive one, and exposed an instrument trap (2026-08-15)

Re-opened with the lens that had just cracked ar25 L3 (a win gated on a control surface the pieces
lock you out of). It does not apply here, and the reason is now measured rather than assumed
(`results/cd82-q300..q303.txt`).

**The instrument trap first, because it is the transferable half.** A naive click sweep on cd82
reports **all 4,096 cells as responsive** — every click changes exactly one cell, `(63,63)` toggling
4 <-> 5, which is a universal per-action counter tick (the same shape CLAUDE.md already records for
m0r0's "global per-action counter reproduced by a plain no-op"). A change-detector cannot see past
it. Worse, the inverse error is just as easy: **the state a click sets can be invisible until a VERB
reads it** — cd82's colour selection changes nothing on the board, it changes what the next ACTION5
paints. So a click-then-LOOK sweep answers the wrong question in both directions, and the sweep that
means something is **click-then-ACT**: click the cell, then press each verb, and compare against the
same verb pressed with no click.

Redone that way, cd82 L3 has exactly **6 responsive 5x5 icon boxes** (colours 0, 8, 9, 11, 12, 14;
colour 15 is the L3 default) and every other cell — the paint block, the roller, the legend, all
4,041 of them — is click-inert. The colour selection is **stateless and fully reversible**
(A -> B -> A is byte-identical to A alone, double-click is idempotent) and has **zero effect on
ACTION1-4** (tumble bboxes identical selected vs unselected). So there is no one-way door here; the
cd82 click mechanism is a reversible parameter, not a precondition. Colour 0 at all 8 ring stations
still paints the established 50/55-cell wedge — the sub-50 verb the size argument requires does not
exist on the click axis either.

The round also caught a miscalibrated coordinate in an earlier probe: `cd82_q49.py`'s
`ICONS[0]=(26,5)` sits in a dead 7-cell gap between the real colour-0 button (x21-25) and colour-12
(x33-37), so any earlier conclusion drawn through it was aimed at nothing.

**Verdict: WALL, sharper than before.** The round-2 impossibility proof rested on partial samples of
the verb axis; the click axis and the condition axis are now exhaustive. What remains unswept is
state that a single-life deepcopy fan-out structurally cannot see — order- or time-dependent state
across MULTIPLE lives, or a very long action count — so the next probe on this game has to be a long
continuous live run, not another fan-out from a fresh L3 entry.

### sk48's click wall survives the sharper instrument — 20,480 click-then-ACT arms, zero (2026-08-15)

The cd82 round above showed that a click-then-LOOK sweep answers the wrong question in both
directions: a per-action counter can make every cell read as responsive, and a click that sets real
state can read as inert because nothing on the board changes until a VERB reads it. `sk48-q22.txt`
was a click-then-LOOK sweep, so its "no click does anything" was, strictly, "no click changes the
board" — a weaker claim than the section above it made.

Re-run properly (`results/sk48-q30.txt`): from L2's fully loaded state, every one of the 4,096 cells
clicked and then **each of the five plain verbs pressed**, each arm off its own deepcopy, compared
against a stated no-click baseline for that verb — **20,480 arms, zero verb-outcome differences,
zero level-ups, zero wins**. Negative control (click (0,0) then A1) matches the baseline; the parent
env is byte-identical after the sweep. So the click channel on sk48 L2 really is dead, not merely
invisible, and the wall stands as written.

Worth keeping as the general rule: **"clicking changed nothing" is a claim about the RENDERER until
you have pressed a verb afterwards.** The cheap form is one baseline per verb plus a click-then-act
sweep; it costs 5x the arms and it is the difference between a measurement and a phrasing.

### tr87 L3 CLOSED for the campaign — ten rounds, three disjoint alphabets, and every channel measured dead (2026-08-15)

The level was reopened because `dial.py`'s reader was demonstrably broken on it (`combination()` returned
`{}`), and it closes with the reader FIXED and the level still unsolved — which is the useful result,
because it separates "we could not read the board" from "the board does not say what we assumed".

**The reader fix works and is verified inert** (`tr87-q80.txt`, patch text in `tr87_q80.py`, not
applied): with it, L3's top region yields **8 (icon, block) pairs** where the shipped reader yields
zero, while L1's combination dict compares `==` to the shipped one and L1/L2 still clear in 28 and 58.

**What the fixed instrument then showed, and it is structural.** Building all seven stations' FULL
seven-phase decks by actually dialing (114 actions, one life, zero deaths, every station returned to
its own entry phase) proves the seven decks are **one shared 7-cycle `G,A,E,D,B,C,F` at per-station
phase shifts** (8→0, 15/22/43→6 and byte-identical, 29→5, 36→2, 50→4). So "a block's shape names its
station" is not underdetermined — it is **impossible by construction**: every block matches every
station at some phase. Entry letters are `8=A, 15=G, 22=G, 29=F, 36=D, 43=G, 50=C`; the eight blocks
decode to `G,D,C,B,B,A,C,F` with **E absent entirely**.

Then the same treatment on the icons, which no instrument had ever compared against each other:
the ten icons canonicalise to exactly **7 distinct shapes** — the label-sized number — and all three
cross-checks come back **fully disjoint**: icon ∩ room = 0, hint ∩ room = 0, icon ∩ hint = 0. Three
mutually disjoint seven-symbol vocabularies coexist on this board. Both channels share one odd shape
on the same eight pairs: six of seven letters used, two doubled, one entirely excluded (`E` on the
block side, `a` on the icon side, the latter sitting only at the structurally unpaired orphan tile).

**Everything tried, and refuted.** Shape-identifies-station (three variants: icon-vs-hint under full
dihedral+polarity with min Hamming 5-15 of 25; block-vs-deck; icon-vs-icon). Position-encodes-station
(three variants — reading-order under all eight drop candidates, exact `block_x`, row-band grouping —
all refuted OFFLINE against a free self-consistency gate: any correct rule must leave stations
8/29/36/50, already unique at A/F/D/C, correct at **zero** presses; exact-x additionally conflicts at
station 15 and would displace station 29). And finally the top-region-is-irrelevant nulls, all live
(`tr87-q95.txt`): mere presence at all seven stations (65 actions), every station moved off its entry
phase (14), all seven driven to a common letter (20), and all six anchor+B/E all-distinct
permutations (9-12 each) — **none wins**, across nine fresh lives with **zero deaths**, so every
failure is the hypothesis being wrong rather than a clock expiring.

Two process notes worth more than the negative result. The self-consistency gate — *does the rule
leave the already-correct stations untouched* — killed three rules offline for the price of zero live
actions; a rule that has to move something already right is wrong, and that is checkable before
spending anything. And when asked for an icon-side rule, the round **declined to fabricate one**: a
drop-3 combinatorial search with no independent justification is guess-and-run wearing a hypothesis's
clothes, and reporting the finding was the correct output.

**Next session: stop looking at the top region and the room alphabet.** The two channels this
campaign has never examined for L3 are the CLAMP (whether where it is parked matters when some other
condition fires) and the room windows' RAW pixel content — colour and position detail that `canon`
deliberately discards, and which shape-matching therefore throws away by design.

### ar25 LEVEL 4 FALLS — the same law, and the decoration that looked like the mechanic (2026-08-15)

Level 4 is a fourth distinct machine and it obeys level 3's law in new clothes. Two
click-selectable colour-5 pistons (a full 4,096-cell sweep finds exactly two responsive
components) translate 3 cells a press in **all four** directions once selected, stopped only by
the board edges — they collide with nothing, not the colour-11 scenery and not each other.
Selection itself is switchable here, last click wins, unlike L3's peg. But **clicking any piston
permanently forfeits A1/A2 control of the colour-10 wall**, and A7 undoes a movement press and
never a selection. So the wall's row at the moment of the FIRST click is the precondition again:
of its **18 reachable rows exactly ONE** — six down-presses — makes the dock complete the level,
and the identical dock is measured dead at the other seventeen (`ar25-q119.txt`). The dock
geometry had been right on the first pass and failed for want of that one row.

**The trap worth keeping is the thing that led there.** The two colour-4 blocks riding the wall
look exactly like a mechanic: their count walks **18 → 117 → 0** as the wall descends, and one UP
press appears to destroy them permanently. On level 1 colour-4 IS the mirror sprite that has to be
docked, so a colour-4 mechanic would have been entirely in character. Two of the first round's own
bullets contradicted each other — "a rendering artifact" and "permanently lost, never recovers" —
and a rendering artifact does not survive its cause being undone. Read per-CELL instead of by
count, it resolves: colour-4 is a reversible artifact keyed purely to the wall's row, and pressing
down after the "kill" returns the exact count (`ar25-q115..q118.txt`). Decoration. But chasing the
contradiction is what enumerated the wall's rows, which is where the real precondition was.

Line (29 actions): wall DOWN x6 with nothing selected, click (18,40) to take piston B and dock it
x-only, click (19,22) to take piston A and dock it x-only. Main-thread verified
(`ar25-q130.txt`): two independent fresh-Arcade replays reach `levels_completed == 4` at action
index 108 of the full 109; a one-action-short control stops at level 3; and a control dropping
**only the six wall presses** — same docks, same clicks, same order — also stops at level 3.

**ar25 is now 4 of 8**, `[15, 25, 40, 29]`, from 1 of 8 this morning. Gating: L3 by
`sweep-wave10.log` (ar25 2/8 → 3/8, 16 of 17 identical, no game loses a level, mean 21.297% →
21.787%), L4 by `sweep-wave11.log`.

**The generalisable rule, now seen twice on the same game:** *a win can depend on a control
surface that engaging the puzzle's own pieces locks you out of, so the ORDER of engagement is part
of the solution.* A search that begins by touching the pieces can be exhaustive — 116,640 states
on L3, all 18 wall rows crossed with the dock on L4 — and still never see it. The cheap test is to
ask, of every condition found: **is this a one-way door?** If yes, it has to be set first, and it
belongs in front of the search rather than inside it.

### ar25 L5: a five-round WALL, and three corrections that each invalidated the round before (2026-08-15)

Level 5 does not fall, but the round is worth reading for the corrections rather than the search.
Each one was found by the agent testing its own previous conclusion, and each retroactively voided
an earlier reading.

**Correction 1 — the "lethal cell" was the life budget.** A raster over S's reachable rectangle
died at action 128 and, replayed press-by-press, pinned a coordinate; that read as a positional
hazard. Rebuilt as a BFS with **one deepcopy per node** and GAME_OVER children marked lethal and
dropped, S's full **289-cell rectangle came back entirely safe — including the exact coordinate**.
The real mechanism is a **real-move budget of ~127 non-blocked presses per life**; a 200x
single-verb probe survived because that verb hits its own wall in ~12 steps and the remaining ~188
presses are blocked no-ops, which do not consume it. The original raster also only checked for WIN,
never for death, so once it died every later reading was taken on a board that had reset to level 1
— "294 presses" meant nothing about location.

**Correction 2 — W's position space is 2D, not 1D.** Every round had measured W's SELECTED
horizontal range (A3=3, A4=17) at one row. Its UNSELECTED vertical range (A1=5, A2=15) had never
been measured, and the row survives the select transition: **441 positions, not 21**. All 441 were
then swept with S untouched — W alone never wins. The same probe showed W's unselected drive moves
the **whole comb rigidly** (ladder plus horizontal band), not the isolated ladder an earlier
horizontal-only test had concluded.

**Correction 3 — colour 4 is universal occlusion paint.** A clean bump profile over 21 W rows
(0 at the extremes, plateau 99/151 at rows −3..−6) with S frozen, zero sensitivity to S's
horizontal position, and an exact non-sticky round trip all read as *a vertical overlap gauge
between the comb and S*. Then the one untested crossing — W's selected column at a non-zero row
with S at a non-default phase — sent colour 4 to **243 while colour 5 stayed flat at 151**: the comb
had slid onto a **fourth static colour-10 object** (bbox ≈ (0,62,0,11)) that had been misread as
part of the ladder since the first component scan. Colour 4 subsumes cells from background,
colour 10 AND colour 11 wherever the comb overlaps them. It is collision rendering, universal
across object types, and it is decoration — the same trap L4's colour-4 blocks set, in a new guise.

Everything measured and dead: the full (21 W rows × 21 S phases) = 441-combination surface, whose
S-overlap maximum is exactly **99/151** with no win anywhere; W alone at all 441 positions; S's
whole reachable rectangle; the A5 mode cycle (exactly the three click-reachable states, a
convenience alias, not a fourth mode); and the complete movable-vs-static interaction matrix — S
against the right-edge colour-11 column, the comb against the colour-11 zigzag and the small 3x3
markers across five row/column combinations — **inert beyond the collision paint**, no colour change
other than to 4, no shape change, no disappearance, and the collision region fails a dock check
under both bbox-exact and one-axis-exact geometry.

**Two things left untried, and the second is the one that fits this game's family.** (1) A genuinely
interleaved search where both W and S move within one continuous life — every probe so far parks one
and drives the other. (2) **The click sweep has only ever been run at the ENTRY configuration.** The
two clickable components were found there and never re-derived after W or S had moved, so a third
clickable object that only exists in some other board state cannot be ruled out — and on this exact
game, levels 3 and 4 both turned on a control surface that a search starting from the pieces was
blind to.

**ar25 L5 addendum — the one remaining gap is closed, and it corrected the entry reading anyway**
(`ar25-q200/q201.txt`). Nine non-entry configurations (W at both vertical extremes, W at its
horizontal extreme selected, S at all four axis extremes, two mixed W-and-S-off states) each swept
click-then-ACT over all 4,096 cells x 6 verbs — **221,184 combinations, no third clickable object,
no win, and no invisible click-set state a later verb reveals**. Two things fell out that matter
more than the null:

- **"Exactly two click-responsive components at entry" was an OCCLUSION artifact.** S's default
  position covers part of W, so the entry sweep under-counted W's own hitbox — 189 cells there
  versus **288-369** once S is driven away. Every component census on this level taken at entry is
  therefore a lower bound on shape, which is the same law the repo already carries for plates and
  crates: *the piece covers what it stands on.*
- **A same-object DESELECT zone exists.** An 18-cell colour-10 fragment of W's own body, visible
  only in config 8, reverts the controls to the nothing-selected scheme when clicked. Earlier rounds
  concluded selection here was switchable-but-never-clearable; that was true of every cell they had
  tried, and false of the board. On L3 the deselect question WAS the mechanic, so this is worth
  carrying even though it did not win L5.

Untested and left explicitly open: a genuinely INTERIOR joint state (both W's row and column
off-default while S is mid-move rather than at an extreme), and any configuration reached by using
A5 — the mode-cycle alias — as the prefix step before a click, which no round has ever used.

### wa30 L3: four reactive guards measured, none beats the control — the defect is the PLANNER, not the refusal handling (2026-08-15)

The diagnosis stands (`wa30-q60..q65.txt`): `act()`'s queue-drain never checks that a popped action
moved the piece, so a refusal `_walk`'s BFS never modelled lets the rest of a delivery fire from the
wrong square and the trailing GRAB drops the crate outside every slot. Four candidate guards were
A/B'd against the unpatched control in the same invocation, shadow-module style, never editing
`haul.py` (`wa30-q80/q81.txt`):

    arm                control L1/L2      arm L1/L2        L3 filled_hi   verdict
    control            43 / 113           --               4             --
    A_pickup_exempt    43 / 113           43 / DIED @112   --            BREAKS L2, by ONE action
    B_n_consec         43 / 113           43 / 113         4 (57 acts)   controls hold, ties ceiling
    C_keep_target      43 / 113           0 levels         0             BREAKS L1 (= q70's fix)
    D_combo            43 / 113           43 / 113         4 (57 acts)   identical to B

Three things worth keeping:

- **A legitimate refusal exists during DELIVERY too**, not only in the documented pickup approach.
  A_pickup_exempt exempts the pickup and still kills L2 — at action **112 against L2's own 113**,
  one short. That is as sharp a refutation as this campaign gets.
- **The control's real L3 ceiling is `filled_hi = 4`, not the 3 the diagnosis named.** The first pass
  measured a GLOBAL filled counter, which conflates L2's leftover book with L3's own progress; the
  corrected per-level counter is in q81. A ceiling quoted from the wrong scope makes every arm look
  like it tied when the bar itself was wrong.
- **B and D hold both controls exactly and still do not beat the control** — they tie `filled_hi=4`
  and then give up (`self.done=True`) after **57 L3 actions against the control's 2,806**. A guard
  that quits 49x sooner at the same ceiling is not an improvement.

**The redirect that follows: reactive guards cap out at MATCHING the control, never beating it.** The
control spends 2,806 flat actions and B/D quit fast, and both point at the same thing — `_plan()`
re-deriving a doomed route, not a one-off bad refusal. The next probe is a pixel trace of ONE replan
cycle on L3 (box position, `blocked` contents, and the BFS route chosen) asking whether the carrying
footprint or a conveyor-adjacent crate is missing from `blocked` at plan time. Fix the planner's
obstacle model; stop patching the refusal handler.

### re86 L6: the budget was wrong by 2x, and four more interaction classes are inert (2026-08-15)

**The correction is the result.** Every L6 round has been sized against a "<100 actions per level"
figure. Measured directly (`re86-q51.txt`) — from L6 entry, oscillating far from every box, the wall
and both group territories — **L6 gives 199 actions to GAME_OVER**, with colour15 draining 64 → 0 at
**0.322 units per action** and colour1 rising in exact lockstep (the two together are the 64-cell
bar, offset by the wall's static 40 colour-1 cells). Reproduced at smaller scale over 21 presses in
`q50`. This does not contradict the repo's `round(0.64 n)` law so much as locate it: **the clock's
rate belongs to the LEVEL** — the same lesson ls20 already paid for — and 0.322 per colour against
0.644 across both is exactly the factor of two between the two readings. What matters practically is
that **no L6 hypothesis has ever died of the clock**, which is what the old number implied and every
round quietly assumed.

L6's layout is deterministic: reached at action **421** from a fresh reset across six independent
process launches today, with byte-identical box coordinates every time —
`{(12,6):9, (9,9):9, (30,9):9, (12,27):9, (45,30):11, (54,30):11, (15,48):marker, (45,57):11, (54,57):11}`.

Four new inert classes, each measured rather than argued:
- **Shape-on-shape ARM overlap** — the plus parked so its horizontal arm crosses the ring's left and
  right border columns AND its vertical arm crosses the ring's top and bottom border rows
  simultaneously: all four crossing cells read colour 11 before, during and after, nudged off and
  back in all four directions. No recolour, no consumption, no state change.
- **Shape-on-shape CENTRE-on-CENTRE overlap** — control toggled to the ring and driven onto the
  plus's parked centre so both bodies occupy the same cell: NOT_FINISHED, `boxes()` unaffected,
  freely reversible.
- **TOGGLE adjacency** — action 5 behaves identically pressed far from or one lattice step beside
  the other shape's native position. No adjacency gate, so no one-way door here.
- **The static wall's sealed hole holds nothing** — settled by a whole-grid component census
  (`q33`) rather than by exploring it: no component's bbox lies inside (28,28)-(35,35) except the
  wall's own 40-cell ring. Plain background, not a masked marker.

**Two cells genuinely untried, and the first is cheap.** (1) **Cross-colour centre-landing has never
been tested** — every centre-landing probe on this board was own-colour, and the "centre landing is
lethal" law it assumed comes from levels 1-5 and has never fired on L6. Does the plus's centre
landing on a colour-11 box, or the ring's on a colour-9 box, differ from the own-colour
survive-and-noop? (2) The budget bar itself is the only other dynamic object on the board and has
never been tested as a trigger — including whether GAME_OVER on L6 re-enters at L6 (per the
established `reset()`-scopes-to-the-current-level law) rather than costing the whole run, which
decides how expensive every future L6 round is.

**re86 L6 addendum — two assumptions that shaped every previous round are measured FALSE** (2026-08-15,
`re86-q53/q54/q55.txt`):

- **GAME_OVER on L6 re-enters at L6, not at level 1.** After burning the full 199-action budget,
  `reset()` returns `levels_completed=5` with the board byte-equal to L6 entry. The repo's general
  `reset()`-scopes-to-the-current-level law, now confirmed on this specific board. Combined with the
  199-action correction, **future L6 rounds can burn budget freely** and never repay the 421-action
  climb through levels 1-5 — which is the opposite of the caution every round so far has been
  designed around.
- **Cross-colour centre-landing is survivable and inert**, exactly like own-colour: the plus (wearing
  colour 9) landed cleanly on all four colour-11 boxes, the ring (wearing colour 11) on all four
  colour-9 boxes, and the plus on the marker's cell at (15,48) — nine fresh climbs, zero GAME_OVERs,
  all reversible. The "centre landing is lethal" law it was tested against comes from levels 1-5 and
  has never fired here.

**And the round did not stop at "nothing printed."** Cross-colour landing makes the box vanish from
`boxes()`, which reads exactly like consumption. Settled with the oracle this repo already owns:
land on (45,30), walk **eight steps away**, and the accumulate-then-drop-on-all-background detector
still holds `(45,30):11` — the 3x3 patch never went all-background, so the disappearance was the
known *a box under an arm is invisible to the ring detector* artifact, not a win. That distinction is
the whole difference between a mechanic and an artifact, and it cost one probe.

Ten interaction classes are now dead on this board, none of them to the clock. The untried cell is
**JOINT STATE**: every probe tests one placement in isolation, and nothing has landed BOTH shapes on
their own-colour box pairs in the same run without moving off between.

### re86 L6 CLOSED for the campaign — the win is not a PLACEMENT (2026-08-15)

Joint state is dead too (`re86-q56.txt`). Five pairings, each reached AND HELD with control toggled
back and forth three times while both shapes stayed parked: own/own (plus (30,9) + ring (45,57);
plus (12,27) + ring (54,30)), cross/cross (plus (45,30) + ring (12,27)), and mixed in both
directions. No win, no state change, and **no deviation from the budget bar's 0.322/action line** —
which was logged per press precisely so a hidden cost or trigger would show, and none did. The
accumulate oracle confirms neither landed box is ever truly consumed: occlusion under two shapes at
once is exactly as misleading as under one, and the same oracle catches it.

The round also *used* the free re-entry it had just discovered: **one 421-action climb total**, then
pairing after pairing chained through burn-to-GAME_OVER + `reset()`, never re-climbing, four times
in one process. That is what the correction was worth in practice.

**Thirteen interaction classes are now dead on this board** — enclosure, own-colour centre-landing,
scenery contact, cross-colour centre-landing, marker landing, shape-arm overlap, centre-on-centre
overlap, TOGGLE adjacency, and joint placement in four combinations — **and not one of them died of
the clock**: every test finished under 55 of the 199 available actions, with retries free.

So the conclusion is structural rather than another null: **the win on L6 is not a placement**, solo
or joint, same-colour or cross, in any toggle ordering. Every lever in `cover.py`'s own model
(covering, enclosure, recolour-by-swatch, centre-landing) is confirmed absent from this specific
board. The next session should stop probing placement variations entirely and re-read L6's frame for
an object nobody has named — the whole-grid component census in `re86-q33.txt` exists but has never
been re-read against the current understanding, and something dismissed as scenery early is now the
most likely place the mechanic is hiding.

### Two codex read-only recons, and both found a detector defect the campaign had never named (2026-08-15, late)

Delegated as `codex exec --sandbox read-only` through `codexChat()` (sandbox pinned at the call site,
answer read from the `-o` file). Cost: **59s and 68s**. Both prompts carried the repo's one
non-negotiable rule, and **both were verified afterwards from their own session logs** — every
occurrence of `environment_files` in `~/.codex/sessions/…/rollout-*.jsonl` is my prompt text echoed
back plus codex's own statement of intent; **no tool call touched the answer key**. That check is the
price of using a lane whose sandbox bounds writes and has no opinion about reads.

**`haul.py` (`results/haul-recon-codex.md`)** — located the planner's blind spot exactly, and the
main thread verified every line against the source:

    blocked = [(c[4], c[5], c[0], c[1]) for c in cr if ... != frame ...]      haul.py:594

`blocked` is built **solely from `crates()` output**, and `_walk`'s BFS rejects a candidate only on
overlap with one of those rectangles (`haul.py:521`). **No raw terrain cell ever enters it.** And
`crates()` recognises only axis-aligned rectangles ≥3×3 with a single-colour border and a single
different interior colour (`haul.py:107-131`) — never isolated pixels, sparse dither, lines,
sub-3×3 shapes, non-rectangles or broken borders. The level-3 refusal that strands every delivery
happens on a square whose raw board is *background plus sparse colour-2 dither*: exactly the class
`crates()` structurally cannot see. It also confirmed the route is computed ONCE and queued
(`haul.py:462/491`) and re-derived never, and that conveyor-activated crates enter `blocked` only at
their plan-time position with no swept path. Its own proposed fix — block every non-background cell
outside the piece and the frame — it flagged as unverifiable from source ("nothing here distinguishes
solid terrain from passable decoration"), which is correct and is why it went to an A/B
(`wa30_q90.py`) rather than into the driver.

**`cover.py` (`results/re86-recon-codex.md`)** — asked to find an object re86 L6 has that the driver
has no category for, since thirteen placement classes are dead. It found two, both verified here:

- **The colour-1, 40-cell wall at (28,28)-(35,35) is not in `lava`.** The driver's entire obstacle
  set is `{cells == self._frame(g)}` (`cover.py:207`), and `_frame` returns the ring colour of a
  detected box — colour **4** on this board. So a wall wearing colour 1 is invisible to routing. It
  is also not a box, not a swatch and not a shape, by each detector's own condition.
- **The colour-0 marker at (15,48) is returned by `boxes()` as a ninth BOX, of colour 0.** Verified
  in source: the test is `if f != int(g[y, x]) and (ring == f).all()` (`cover.py:52-62`) — there is
  **no `f != bg` condition**, so an isolated marker cell surrounded by background satisfies it. The
  driver then groups it by colour and carries a colour-0 group that **no shape wears and no swatch
  establishes**, and the accumulate-across-frames repair only fixes false negatives, never false
  positives (`cover.py:257-270`).

Neither is proven to BE level 6's win condition — they are driver defects, and the session's placement
probes drove the shapes by hand rather than through `cover.py`, so a mis-planning driver cannot
explain a hand-driven null. But an unroutable wall and a permanently-unsatisfiable phantom group are
both concrete, both were invisible for nine rounds, and both were found in a minute of source reading
by an instrument with no stake in the previous conclusions.

**What the lane is good for, measured:** source and artifact reading where the context is the file
rather than the conversation. What stayed here: judging whether a finding is real, running the gates,
and anything needing the engine — the answer-key rule cannot be enforced by a sandbox that only
bounds writes, so the more a task needs to *run* this repo, the less it belongs on this lane.

**And the A/B answered codex's own UNCERTAIN with a clean no** (`results/wa30-q90.txt`). Its recon
asked whether every non-background cell is physically solid; it could not tell from source, and it
said so. Measured, both arms:

    control        L1=43  L2=113  L3 filled_hi=4 over 2,888 actions
    A_all_nonbg    L1=43  L2=never clears   L3 never reached
    B_unmodelled   L1=43  L2=never clears   L3 never reached

Blocking non-background cells **seals the board** — level 2 stops clearing entirely, and arm B seals
it too even after excluding every cell inside a detected crate, so the cells doing the sealing are
non-crate, non-frame, non-piece decoration the piece routinely walks over. **The dither is passable.**

So the recon's #1 blind spot is refuted as the cause: the level-3 refusal is not raw terrain
occupancy. What survives is its #2 and #3 — the conveyor's **swept path** (a ring-5 crate blocks only
where it stood at plan time; there is no time dimension) and **board change during a queued route**
(nothing is re-read between the plan and the trailing GRAB). Both are about TIME, not geometry, which
is consistent with everything else measured on this level: the plan is right when made and wrong when
executed.

Worth keeping as a method note: the recon was right about the code, right about its own uncertainty,
and wrong in its ranking — and the ranking is the only part that needed an engine to check. Locations
are findings, conclusions are hypotheses, and a proposed patch is a hypothesis wearing a diff.

### re86 L6: the real cause is UPSTREAM of both defects — and one of the defects is load-bearing (2026-08-16)

Both `cover.py` defects the codex recon found are real in source. Tested against the live driver
(`re86-q60/q61.txt`, shadow-module arms, `cover.py` never touched on disk), **neither explains level
6 — and the more interesting one must not be fixed.**

**The phantom box is ACCIDENTALLY LOAD-BEARING.** `boxes()` returning the colour-0 marker as a ninth
box is a genuine false positive, and applying the one-line fix (`f != bg`) **regresses the level
immediately before L6**: the patched driver stops at level 4 (action 233) and never reaches L6 at
all, while control and the wall arm both arrive at action 421 exactly. Mechanism, traced through
`sig`/`known` rather than guessed: the phantom's coordinate **moves** every time it is re-detected —
the wandering marker lands on a new all-one-colour neighbourhood each sample — and that changing key
is precisely what defeats the wave loop's `sig == prev_sig` stagnation check. Control's wave 2 gains
the phantom at a NEW coordinate (11 keys against wave 1's 10) and is therefore not stagnant, buying
an extra wave in which colour 8's boxes, revealed progressively from under the shape arms, finish
being found and consumed. Remove the phantom and wave 2 reads 10 == 10, `_level()` returns one wave
early, and the level never completes. **A defect the driver depends on**, and the controls bar caught
it before it could ship.

**The invisible-wall fix is provably inert**, by a full plan/path event-sequence diff rather than an
inference: with the colour-1 cells unioned into `lava`, every event across all six levels is
byte-identical to control. The reason is upstream — `route()` is `lava`'s only reader and is **never
called on L6 in either arm**. A fix to an unreachable code path is inert regardless of whether the
defect claim behind it is correct. (Reproducibility note kept honest: the 40-cell wall at
(28,28)-(35,35) appears in 2 of 3 raw reads; one read saw zero colour-1 cells at nominally the same
point, most likely occlusion at that transition frame — flagged, not reconciled.)

**And the measured proximate cause, which sits above both:** `group_plan()` requires the single
eligible shape for a colour to cover **ALL of that colour's boxes in ONE stationary placement**. On
L6 the plus (colour 9) and the ring (colour 11) each have exactly one matching shape, and their
candidate placements yield **7 and 6 coverage subsets respectively — none equal to the 4-box group**.
So `group_plan` returns None for both real groups, no plan is ever constructed, and the driver's
entire L6 contribution is **11 actions of shape-discovery overhead followed by permanent give-up**
(`self.gen = None`). Zero actions are ever spent attempting the level.

That retroactively explains the whole nine-round history. The thirteen dead placement classes were
probing a level the driver never reaches a placement on, and the earlier finding that *box-covering
is geometrically capped at 2 of 4 per group* was correct and is now explained rather than merely
observed: **one placement cannot cover the group, so the level requires more than one visit.**

**The lever, and it is a rules question before it is a code question:** is SEQUENTIAL coverage —
the same shape covering its group across several placements — legal in this game at all? Measure that
against the engine before investing in teaching `group_plan` to compose multi-visit plans inside
L6's 199-action budget. If it is legal, the same limitation may be capping other levels too.

**And the rules question is answered: SEQUENTIAL COVERAGE IS ILLEGAL** (`re86-q70.txt`). Coverage is
**occlusion, not deletion** — the game never mutates a box's cells on contact, it draws the shape over
them while parked. Land the plus on the candidate covering `{(12,6), (12,27)}`, route it away to the
candidate covering the other two, and both come back `STILL-A-BOX (reverted)`: raw colour 9 with a
clean 3x3 ring `[[4,4,4],[4,9,4],[4,4,4]]`, not background. Same for the ring across its two colour-11
pairs. **Positive control on level 1** — a level the driver clears normally, same shape, same
technique — reverts identically, so "consumed" has a reference reading on this game and the L6 result
is not a special case. Three independent trials, zero consumptions, zero mismatches.

That closes the last hypothesis nine rounds had not tested, and it converts L6 from "we cannot find
the mechanic" into an **impossibility proof for the covering mechanic specifically**:

- the plus geometrically **cannot cover all four colour-9 boxes at once** (max 2 of 4, established in
  `q60`/`q61`), and
- the engine **will not credit partial coverage across time**.

So no ordering, no multi-visit plan, and no `group_plan` change can clear L6 by covering. That also
confirms `cover.py`'s docstring literally, from the other direction — *consumed the moment shapes
wearing that colour cover all of it AT ONCE* — and explains why its own multi-shape plans work: the
shapes are placed one at a time but all stay **parked simultaneously**, and the consumption check runs
once per wave after every colour's plan has finished.

**Standing verdict on re86 L6: the win is not box-covering at all**, and `cover.py`'s contribution
stays capped at its 11-action discovery-then-give-up. Anything further needs a mechanic outside the
covering model — which is now a statement backed by an impossibility argument rather than by a tally
of things that did not work.

**wa30's TIME arms fail too, and the reason is the same shape as everything else here**
(`results/wa30-q91.txt`):

    control             L1=43   L2=113   L3 filled_hi=4 over 2,888 actions
    C_replan_moves      L1=43   L2=never          (movement re-derived every round)
    D_replan_onchange   L1=never                  (queue dropped when the crate set changes)

C re-derives movement every round and cannot clear level 2. D is worse — it never clears level **1**
— and the reason is worth more than the arm: **any invalidation keyed on "the board changed" fires
on the driver's OWN movement**, because a carried crate is still a crate to `crates()`, so its
position changes on every step the piece takes and the signature never matches. The guard designed to
notice the conveyor cannot tell the conveyor from the piece.

So **six candidate fixes have now been measured and rejected on this level** — four reactive refusal
guards (`q80`/`q81`), one obstacle-model widening (`q90`), and two time-dimension arms (`q91`) — and
every one of them was rejected by the CONTROLS, not by failing to help L3. The queue-as-committed-plan
is load-bearing on a board whose conveyor moves something every action, exactly as the phantom box is
load-bearing in `cover.py`. That is now twice in one night that the obvious repair to a real defect
broke a level that already worked.

**The standing rule this earns:** on these drivers, *a defect and a dependency are the same object
until an A/B separates them*. The shadow-module harness makes that separation cost two minutes
(`wa30_q90.py`/`wa30_q91.py`/`re86_q60.py`: patch the source as TEXT, exec it as a module beside the
original, drive both in one invocation), and nothing should reach a full sweep without it.

### A latent structural defect in TWO drivers, found by a read-only audit that playing could never have found (2026-08-16)

A batched `codex exec --sandbox read-only` pass over all fourteen drivers asked one question — *where
and why does each give up, and does the give-up survive a level boundary* — and turned up exactly two
that do. Verified here in source (`results/giveup-a/b/c-codex.md`):

    skewer.py:237   if not self.on or self.done: return None      <-- checked FIRST
    skewer.py:242       if lvl != self.lvl: ...                   <-- reset block, no `done = False`
    dial.py:205     if not self.on or self.done: return None      <-- same inversion
    dial.py:211         if lvl != self.lvl: ...                   <-- same, no reset

Every other driver checks its terminal flag **after** the boundary block — `mirror.py:134-137` resets
`self.dead` on a level change and only then tests it. In `skewer` and `dial` the order is inverted, so
`self.done` (tripped at `skewer.py:267/288/301/305/323` and `dial.py:225/228/237`) can never be
cleared: **once either driver fails on any level it is dead for the rest of the game.**

That is invisible from any single level's behaviour — from inside one level a permanently-dead driver
looks exactly like one that simply has nothing to say — which is why nine months of play never
surfaced it and one read-only pass did.

**Measured today: the fix is INERT** (`results/donereset-q1.txt`). Moving the flag check after the
boundary reset changes nothing on either game — sk48 still clears L1 at 24 and gives up at 33, tr87
still clears L1 at 28 and L2 at 58 and gives up at 58, marks byte-identical in both arms. That is the
expected result and not a reason to dismiss it: `done` trips on the level where the driver already has
nothing, so there is no later level for it to cost **yet**. The moment a line is written past either
give-up, the flag is what will silently eat it.

**Filed as a prerequisite, not a change:** land the two-line reorder bundled with the first line that
needs it, so the sweep it costs is paid once for something that also scores. The patch is in
`donereset_q1.py`.

Two notes on the lane itself. The single-shot version of this audit **died at `token cap
92,936/60,000`** — fourteen drivers plus `compete.py` (2,746 lines alone) does not fit, and a
read-only run has no disk output, so a capped run loses everything rather than truncating. Split into
three batches by size with `compete.py` excluded by instruction, all three returned in 72-117s. And
the mirrored skill corpus has a broken file that every run complains about:
`~/.codex/skills/vercel-react-best-practices/references/react-native/SKILL.md: missing YAML
frontmatter` — harmless, but real.

### wa30 L3: EIGHT candidate fixes, all rejected on the CONTROLS — and that is now the finding (2026-08-16)

    control             L1=43   L2=113   L3 filled_hi=4 over 2,888 actions
    E_sig_excl_piece    L1=never                  (signature ignoring crates the piece overlaps)
    F_sig_ring5_only    L1=43   L2=never          (signature over conveyor-activated crates only)

E was written to fix D's exact failure — D keyed on every crate and died because a carried crate is
still a crate — and it dies harder, never clearing level 1: excluding what the piece overlaps still
changes the signature every time the piece grabs, drops, or walks past something. F narrows to ring-5
crates only, which is immune to the piece by construction, holds level 1, and then dies on level 2
because **that is exactly the board where the conveyor moves an activated crate on every single
action**, so the ring-5 signature changes every round and the queue is dropped every round.

Running total on this level: four reactive refusal guards (`q80`/`q81`), one obstacle-model widening
(`q90`), two time arms (`q91`), two signature arms (`q92`) — **eight, and all eight died on the
controls rather than on failing to help L3.**

That is no longer eight failures; it is one measurement repeated eight ways. **On a board where
something moves every action, every plan-invalidation criterion fires constantly, and the committed
queue is what makes any progress possible at all.** The driver is not accidentally tolerant of a
stale plan — it depends on tolerating it, the same way `cover.py` depends on its phantom box. Any
criterion sensitive enough to catch the conveyor is sensitive enough to catch the driver itself.

So the shape of a real fix is not *when to drop the plan* — that space is now measured empty in every
direction that matters. It is **planning that survives the conveyor**: routing to where a moving crate
will BE rather than where it was, or only committing a delivery once its target crate is parked. Both
are `_plan` changes rather than `act()` changes, and neither has been attempted.

---

## 2026-08-16 — wa30 L3 is an ARITHMETIC wall, not a planning one (main thread, `wa30_r1..r6.py`)

The paragraph directly above proposed two `_plan` changes as the untried direction. Neither was
written, because tabulating the level first — which nine rounds of fixes had never done — showed the
question was wrong. This is the re86 shape again: rounds of probing aimed at a level's mechanics
while the real constraint sat one measurement away.

**What level 3 is, measured under controls** (`wa30_r3.py`, `wa30_r6.py`):

| quantity | value | how |
|---|---|---|
| clock | **100 actions, exact** | `filled` reverts at a=114, 214, 314 … 2914 — 28 identical lives (`wa30-r1.txt`) |
| frame | 8 x 16 at (52,24), ring 9, inner 2 | detected by the driver ON L3, control-checked against L2's |
| interior proper | **84 cells** of colour 2 | 6 x 14; the other 44 cells of the rect are the border |
| `_slots` | **8 windows**, n = 12,12,12,12,9,9,9,9 | they **tile** the interior exactly; sum = 84 |
| crates in existence | **5** | and 300 idle actions spawn none (`wa30-r2.txt`) |
| conveyor | **delivers nothing on L3** | 300 idle actions, board byte-identical, `levels_completed` flat |

A crate is 4x4 and the lattice step is 4, and the frame is 8 wide — so a crate can sit in exactly one
window. **Five crates therefore cover at most 12+12+12+12+9 = 57 of 84.** No placement, and no amount
of speed, empties this interior.

So one of two things is true, and both retire the whole line of work: either the win on L3 is **not**
"empty the interior" — in which case `haul.py`'s target is simply wrong on this board and every guard
argued over for nine rounds was defending the wrong goal — or level 3 is unwinnable as the driver
models it. The `_plan` changes proposed above are not worth writing either way.

Also measured, and worth carrying: **the shipped driver's L3 trajectory is byte-identical every
life** — the same events at i=11, 13, 14, 15, 24, 25, then again at 111…, 211…, 311… across 28 lives.
A driver that plays a level exactly the same way 28 times is not exploring it.

### Three metrics wrong in three ways, each caught by a control and not by inspection

Worth more than the wa30 result, because every one of them looked right in its own output:

- **`wa30_r2.py` read the census through LEVEL 2's rectangle.** The probe stopped its climb the instant
  `levels_completed == 2`, so `act()` never ran on an L3 frame — and `act()` is where `self.frame` and
  `self.slotlist` are cleared and rebuilt. Everything it printed (frame, 2 free slots, interior
  histogram, the inside/outside split) described the wrong rectangle. **The tell was inside its own
  output**: the frame tuple said `inner=2` and the interior it printed contained no colour 2 at all,
  which `_slots` makes impossible for a freshly detected frame. *A driver's cached geometry belongs to
  the last level it RAN on, not to the level the env is on.*
- **`wa30_r4.py` counted interior cells with the piece standing on them**, so a delivery and a walk-past
  were the same event. Caught by a step of **-12**: consumption is permanent, so a count that goes back
  UP is measuring occlusion. It also produced a step of +18 — larger than a crate's whole 16-cell
  footprint — which read as "the footprint rule is refuted, the level is alive". It was a carried crate.
- **`wa30_r5.py` masked the piece but counted the frame RECT, border included**, and accumulated an
  "ever gone" set with no upper bound. Caught by `|ever_gone| = 92 of a possible 84` — **a number that
  cannot exist**. The control I had written was that the set may never shrink; the control that would
  have caught it was that it may never overflow. *A monotonicity check and a bound check are different
  instruments, and the cheap one is the bound.*

`wa30_r6.py` is the version with all three controls (interior proper = 84 at entry · coverage never
exceeds 84 · the eight slot values sum to 84), and it is the only one of the four whose numbers are
evidence.

## 2026-08-16 — re86 L6: box-covering is closed BY PROOF, both groups (agent, `re86_r1..r3.py`)

Three rounds, and the third is the one that settles it. Prior standing was an impossibility argument
about the plus and its colour-9 group; it is now a verified proof covering the whole mechanic.

1. **The ring cannot cover 4 of 4 either — the level is symmetric in its impossibility.** Footprint
   read fresh with the one-probe-per-axis method: reach ±9 in all four directions, 72 body cells. The
   four colour-11 boxes are two same-row pairs 9 apart, the pairs 27 apart in y; the ring's own
   diameter is 18. `candidates()` confirms **max simultaneous coverage = 2 of 4**, the same ceiling as
   the plus. This kills the "one group is coverable, one is not" hypothesis outright.
2. **The 40-cell wall is inert, and it is the ONLY thing L6 adds relative to L5.** A chamfered octagon,
   bbox (28,28)-(35,35), hollow middle. It refuses both shapes (never lethal), does not push, is not
   consumed, is not destructible over 10 rams, changes nothing about the toggle nearby, and colour 1
   does not occur anywhere on L5. *Caught in passing: a whole-grid colour-1 count APPEARED to show the
   wall growing — it was the budget bar's own colour15→colour1 transition. A whole-board count on a
   board with a ticking clock is contaminated by the clock.*
3. **Covering consumes NOTHING at partial coverage — and the positive control proves the rule is the
   GAME's, not L6's.** Three arms in one invocation: ARM P drove `cover.py` to a natural L1 win (31
   actions) so consumption is demonstrably detectable; ARM N covered a genuine 2-of-4 pair on **L1**,
   moved fully off, and both boxes **reverted**; the L6 arms did the same for both groups and both
   **reverted**. So partial coverage failing to consume is not an L6 quirk and not a broken metric —
   **consumption requires simultaneous FULL-group coverage everywhere in this game**.

(1) + (3) is a proof: consumption needs 4 of 4, neither shape can exceed 2 of 4 on its own group, and
only one shape wears each colour on L6 because the level has no swatches. **The win on re86 level 6 is
not box-covering, and no placement, ordering or combination can make it one.**

The methodological point is the third arm. My own framing to the agent offered two readings — "the
control also consumes nothing" meant the metric was broken — and it had a third: the RULE is
all-or-nothing everywhere. Only running the partial-cover test on a level that DOES clear separates
them, and that arm is what turned a thirteen-round exhaustion into a proof.

## 2026-08-16 — sp80 L3: multi-life is closed, the wall reproduces (agent, `sp80_r2..r4.py`)

L2 already falls in the shipped agent (`swap.py`'s `L2_LINE`, 7 actions, gated in `sweep-wave11.log`);
see the stale-numbers note below for how an agent was sent at it anyway.

- **Nothing persists across an L3 death.** Died immediately, and died again after moving the driven
  body first: both times `env.reset()` landed **byte-identical** to the L3 entry board. The positive
  control is inside the same probe — the pre-death diff was 34 cells, so the instrument can see a
  difference and reports none. Consequence: every death edge in a state graph points back to the single
  root, so **chaining lives is provably equivalent to restarting the same single-life search**. The
  multi-life hypothesis is closed, and closed for a reason rather than by exhaustion.
- **The BFS wall reproduces independently**: 5,778 nodes expanded, 18,944 states, 21,589 clicks tried,
  no win, frontier 13,166 and still growing. Same shape and scale as the two earlier attempts
  (`sp80-q23.txt` 4,808, `sp80-q29.txt` 6,532). Not a completeness proof — time-bounded, unexhausted.
- Two levers named and still untested: **block-relative offsets** (every search so far has keyed
  castle positions in world coordinates) and **block2-as-final-actor** (ending a plan with a specific
  body firing, not merely any body).

## 2026-08-16 — tr87 L3: both named-open directions refuted (agent, `tr87_r1..r4.py`)

- The **343-combination triple** does not survive a look at the board: there is no board-native
  three-unknown-slot structure, and the only grouping that ever named three stations was a byproduct of
  the already-refuted hint-offset-3 position rule. Not run live, and correctly so — brute-forcing it
  would have been re-testing a dead rule under a new name.
- **"A display exists that no reader frames" is refuted by exhaustive pixel accounting**: all 4,096
  cells of the L3 entry frame classified into known regions, leftover exactly 82 cells = row 63 (a
  decrementing budget bar, confirmed with 5 throwaway presses) and an 18-cell decorative connector
  present identically in all three bands. **Zero cells unclassified.** The one unframed candidate — a
  2-row colour-0 bracket — tracks the clamp 1:1 through all 7 stations plus a wrap, so it is a cursor.
- Independently reconfirmed on fresh instrumentation: the 8 top-region icons dihedral-match **zero** of
  the 7 hint glyphs.
- Carried forward: the shipped reader's `top_end` bug fires on the L3 board too — `combination()`
  returns `{}` and the driver would give up on this board even before the icon problem. The fix in
  `tr87_q80.py` remains correct, inert, and unlanded.

## 2026-08-16 — a stale block in the brief cost an agent a whole run

The brief's §GATE "Values that must not move" block still carried `sweep-sorter4.log`'s numbers —
sp80 `1/7 [16]`, tr87 `1/6 [28]`, cd82 `[1306]`, cn04 `[131]`, m0r0 `[53]`, tu93 `2/9`, sb26 `4/8` —
while the GOAL line at the top of the same file had been kept current through eleven sweeps. A brief
written from that block sent an agent to crack **sp80 level 2, which already falls in the shipped
sweep**. The agent's work was correct; the target was not.

The general form is worse than "a doc went stale": **the file contained both numbers, one fresh and
one rotten, and the rotten one read as authoritative because it was the more specific of the two.**
A per-game action list looks like harder evidence than a headline percentage. The rule that follows is
narrow enough to act on: *refresh the per-game block in the same edit as the headline, every sweep* —
a pair of numbers where only one is updated is more dangerous than a pair where neither is, because
the fresh half vouches for the stale half. Block refreshed to wave-11 and annotated in place.

## 2026-08-16 — the action-space table, and a cheap audit that did NOT reopen six games

`actionspace.py` → `results/actionspace.txt`. One reset per game, zero actions. Nobody had written
this down, and two of its columns are load-bearing.

| game | standing | plain verbs | click? |
|---|---|---|---|
| ls20 | 7/7 | 1,2,3,4 | no |
| tu93 | 9/9 | 1,2,3,4 | no |
| sb26 | 8/8 | **5,7** | yes |
| re86 | 5/8 | 1,2,3,4,5 | **no** |
| ar25 | 4/8 | 1,2,3,4,5,**7** | yes |
| sp80 | 2/6 | 1,2,3,4,5 | yes |
| tr87 | 2/6 | 1,2,3,4 | no |
| cd82 | 2/6 | 1,2,3,4,5 | yes |
| wa30 | 2/9 | 1,2,3,4,5 | **no** |
| sk48 | 1/8 | 1,2,3,4,**7** | yes |
| cn04 | 1/6 | 1,2,3,4,5 | yes |
| m0r0 | 1/6 | 1,2,3,4,5 | yes |
| dc22 | 1/6 | 1,2,3,4 | yes |
| ka59 | 1/7 | 1,2,3,4 | yes |
| bp35 | 1/9 | **3,4,7** | yes |
| sc25 | 0/6 | 1,2,3,4 | yes |
| g50t | 0/7 | 1,2,3,4,5 | no |

Two things fall out immediately:

- **Every one of the six games stuck at exactly one level has a click** (cn04, m0r0, dc22, ka59, bp35,
  sk48). So all six level-2 closures rest on click evidence, with no exceptions to fall back on.
- **Action 7 is a real verb on four games** (sb26, ar25, sk48, bp35) and it is not the same thing on
  each: sb26's is the UNDO of its insertion stack, bp35's is a plain -6 move. sk48's and ar25's are not
  separately characterised anywhere. `bp35` has only THREE plain verbs (3, 4, 7) and `sb26` only two.
  Any "press each verb" sweep written against an assumed 1-5 misses them.

**The audit those two facts motivated, and its negative result.** The un-aimed click bug — corrected
2026-08-11, when `clicker.set_data({...})` was found to attach coordinates the local wrapper never
reads, so every click before that arrived with `data={}` — would invalidate any closure argued from
click evidence swept before the fix. Since all six stuck games have clicks, that was worth checking
rather than assuming. Scanned all 800 `*.py` at the repo root: exactly **two** files use `set_data`
without ever passing `data={...}` — `sk48_q3.py` and `sb26_p6.py` — and **neither is a probe that
closed a level**. The twelve files containing both forms are the diagnostics that deliberately
measured the two paths against each other, `compete.py` among them.

So no level-2 closure rests on un-aimed clicks, and six games do NOT reopen on this argument. Worth
the ten minutes precisely because the answer could have been the other way, and worth writing down so
nobody spends the ten minutes again — *an audit that finds nothing still has to be recorded, or its
absence reads as never having been done.*

⚠️ **Instrument note, RTK.md's own trap, walked into while doing this**: `ls *.py | while read f` fed
`awk` filenames like `actionspace.py  3.1K`, because `rtk` rewrites `ls` to print a size beside every
name. Every iteration failed with `cannot open file`. Enumerate files with python's `glob`, never by
parsing `ls` in this shell — same rule as `diff`, `grep` and pytest.

## 2026-08-16 — ar25 L5: the last gap is closed, and it closes at 13 configurations (agent, `ar25_r1.py`)

The standing note said every click sweep had run at the ENTRY configuration only, and named that as
the one hole in an otherwise measured wall. It is now filled from both ends.

- **Four more non-entry configurations swept click-then-ACT, 28,672 arms each = 114,688 this round**,
  on top of the prior round's 221,184 across nine. **Thirteen distinct non-entry configurations plus
  entry, zero wins anywhere.** Two of the four were deliberately INTERIOR — both of W's row and column
  off-default and not at an axis extreme, with S also off-default and mid-range, reached inside one
  continuous life at 30 real moves, leaving every arm ≤32 of the ~127 budget.
- **A5 is a convenience alias for the click, verified rather than assumed**: A5x1 vs click(W) and A5x2
  vs click(S) are **byte-identical** once the two known per-action HUD counter cells `{(0,63),(1,63)}`
  are excluded. There is no hidden fourth state behind the selector.
- **A third click-responsive component appeared in one interior configuration** — a 9-cell colour-11
  blob at bbox (27,29)-(30,32), never seen at entry or in the nine earlier configurations — and was
  followed up rather than reported as a lead. Clicking it toggles the same 6-cell diagonal selection
  indicator A5 produces, A5 immediately after nearly reverses it, A1/A2 go inert while A3/A4 keep
  driving S. It is the already-documented deselect mechanic reappearing at a different position and
  colour **because W's body had physically moved there** — not a new control surface, and no verb from
  the clicked state wins.

That last item is the reusable part: *a component that appears only in one configuration is more
likely to be a known object relocated than a new one discovered*, and the way to tell is to press
every verb from the clicked state and look for the signature you already know.

**What is still not covered, named rather than glossed** — the agent's own list, and it is honest:
only **2 points of the 441 x 289 joint interior** were sampled and both sit in one quadrant; a truly
ALTERNATING W/S interleave within one life was never run (the interior configs move W fully, then S,
which is sequential-but-continuous); and the reverse selection order — S driven off-default first,
then W moved into overlap with S's new position, ending with W selected — was not tried. So ar25 L5 is
closed the way sk48 L2 is closed: by a large, structured, honest arm count, not by a proof.

## 2026-08-16 — re86: a refusal is NOT only "the marker did not move" (agent, `re86_r4/r5.py`)

The enumeration asked what change on level 6 is permanent. One is, and it is an engine-level fact
about this game that no level-specific probe would ever have surfaced:

**A refused press against the WALL desyncs the shape's rendered arm from its own tracked marker by the
attempted, denied displacement.** Staged at (30,15), one refused DOWN: the marker stays at (30,15)
while the arm's horizontal row jumps to y=18. A later RIGHT press moves marker and arm by the same
delta — the offset never closes. Five consecutive refused DOWNs walk the arm 18 → 21 → 24 → 27 → 27,
the marker frozen throughout.

Four properties, each measured:
- **Bounded by the shape's natural reach.** It stops at row 27, exactly one lattice step short of the
  wall's own top edge at 28 — the same margin every other wall-collision test has measured. So it
  never puts an arm anywhere legal movement could not already put it.
- **Specific to the wall OBJECT, not to refusal in general.** The board-edge clamp at x=0 produces a
  normal single non-accumulating shift; three repeated refused presses there are byte-identical.
- **Permanent by the campaign's own definition** — it survives toggling to the other shape and back.
- **Cleared only by `reset()`**, after which the board is byte-identical to L6 entry.

**This corrects a repo claim.** `CLAUDE.md`'s traps list says *"what actually shows a refusal is that
the piece's position does not change"*. That is true of the MARKER and false of the rendered body on
this game: a refusal against the wall changes what is drawn while the tracked position holds. Any
reader that infers "refused" from the marker alone is right; any reader that infers "nothing changed"
from the FRAME is wrong, and a diff taken across a refusal will show cells moving for a press that was
denied. Scoped note added to `CLAUDE.md`.

It does not open level 6 — the reach ceiling holds, so it cannot place either shape over more boxes
than `candidates()` already reaches, and the covering proof from `re86_r3.py` stands. Recorded because
it is a general mechanic correction, not because it is a lead.

**The instrumentation catch is worth as much as the finding.** The round's first pass routed shapes
home using an oversized fixed-margin avoid-zone around the wall; it was large enough to trap the shape
with no exit, `go()` failed silently, and the resulting diff was **a stuck probe reported as a game
signal**. Caught by asserting arrival before trusting any diff — after which the ring's four wall-rim
arms were logged `home_confirmed=False` and their diffs **discarded as UNTRUSTED rather than reported**.
That is the second time in two rounds on this game that a plausible signal was a broken instrument (the
first was a whole-grid colour count contaminated by the budget bar). *An avoidance margin that is too
large fails the same way one that is too small does — silently, and with output that looks like data.*

## 2026-08-16 — bp35 L2: the closure's load-bearing clause is now measured (main thread, `bp35_r1.py`)

bp35 is 1 of 9 — the largest untouched headroom in the campaign — and its level 2 was closed on this:

> reel arithmetic: ONE RIDE PER LIFE, doors 4-5 rides away, A7 is a plain -6 move, **board reverts**

That is a multi-life argument, and "board reverts" is the half everything rests on: if one ride is all
a life affords and the door is four rides away, the level is impossible **only if** nothing a ride
accomplishes survives the death after it. As written up, that clause was asserted, not diffed.

Measured today with the same shape of probe that settled the identical question on sp80:

| arm | pre-death diff vs L2 entry | post-reset diff |
|---|---|---|
| A — die with no prefix | 0 | **0** |
| B — act first (8 cells changed), then die | **8** | **0** |

Arm B is the positive control and it **fired**: the diff demonstrably sees a change and reports none
after the reset. So nothing persists, every death edge returns to the same root, chaining lives is
equivalent to restarting a single life, and **the closure holds — now for a reason rather than by
assertion.** bp35's verbs are also confirmed as only `plain=[3, 4, 7]` plus the click.

(Forward-only by necessity: bp35's own game code recurses infinitely on a `deepcopy`'d env, so it is
the one game in the campaign that cannot be searched with deepcopy nodes at all. A die-and-compare
needs no deepcopy, which is why this question was answerable here and a BFS is not.)

**The transferable move, used twice today on two different games:** *when a level is closed by an
argument, find the clause in it that is a claim about the WORLD rather than about arithmetic, and
measure that one clause.* On sp80 and bp35 both, the arithmetic was sound and the world-clause was
"the board reverts" — cheap to test, decisive either way, and the version that reopens the level is
worth seven levels of headroom. Both came back closed, which is a result and not a wasted probe: a
closure that has been tested is a different object from one that has been argued.

## 2026-08-16 — g50t level 1 is PROVEN unwinnable (main thread, `g50t_r1.py` + `g50t_r2.py`)

The first game in this campaign closed by **exhaustion** rather than by argument or by arm count.

g50t was one of two 0-level games, closed on a per-cell DFS: *"live DFS of every direction at every
reachable cell: 12 cells, gate reverts on the first departure press."* That is a search over single
presses, not over SEQUENCES — and twelve reachable cells with five verbs is a small enough graph to
spend entirely. So it was spent.

**`g50t_r1.py` — the search.** Real-engine BFS on `copy.deepcopy(env)` nodes, visited key = raw board
bytes, every plain verb from every reachable state:

| | |
|---|---|
| nodes expanded | 1,854 |
| distinct boards | 1,854 |
| **frontier left** | **0** |
| deaths (children dropped) | 40 |
| elapsed | 110.8s of a 900s budget |
| **EXHAUSTED** | **True** |
| hidden-state divergence | **0 cases** |

Three properties make this a proof rather than another null:
- **The action set is COMPLETE.** g50t's `action_space` is `plain=[1,2,3,4,5]`, `complex=[]` — there is
  no click on this game (`results/actionspace.txt`), so no click channel is missing from the sweep.
  This is the sp80 lesson inverted: there, the one-life BFS looked exhaustive and was blind to click
  edges. Here there are none to be blind to.
- **A deepcopy fidelity control ran in the same invocation** — same action on a copy and on the
  original produced identical boards — so the ~3 ms nodes are faithful and not a simulation.
- **Zero hidden-state divergence** across all 9,270 (board, action) pairs: no board+action pair ever
  produced two different successors. That is direct evidence the board-bytes key is sound, which is
  precisely the assumption that broke an earlier sp80 search when ammo turned out to be real hidden
  state the board does not show.

**`g50t_r2.py` — the assumption the proof rested on, measured rather than assumed.** The search DROPPED
its 40 GAME_OVER children, which is only sound if a death returns to a state already covered. Same
probe shape as sp80 and bp35 today:

| arm | pre-death diff vs L1 entry | post-reset diff |
|---|---|---|
| A — die with no prefix | 0 | **0** |
| B — act first, then die | **51** | **0** |

Arm B's 51 cells is the positive control and it fired, so the zeros mean something. A g50t death
reverts to level-1 entry, every death edge points at the search's own root, and the root was expanded
first — the 40 dropped children were not subtrees.

**g50t level 1 contains no win reachable by any sequence of its own actions.** The game is 0/7 and
stays 0/7; no future session should spend a round on it. Worth noting what made this possible while
every other wall in the campaign stayed an arm count: a *small* reachable graph and a *complete* action
set. Where either fails — sk48's 4,096 click targets, ar25's 441x289 joint space — exhaustion is not
available and an honest arm count is the best that exists.

**The move that produced all three of today's persistence results, stated once:** *when a level is
closed by an argument, find the clause in it that is a claim about the WORLD rather than about
arithmetic, and measure that one clause.* Today it was "the board reverts" on sp80 L3, bp35 L2 and
g50t L1 — three closures, three cheap probes, all three held. And on g50t the clause was not even part
of the original closure: it was an assumption **I** introduced by dropping death children, which is
the kind that never gets audited because nobody wrote it down.

## 2026-08-16 — EIGHT of seventeen games return a MULTI-PLANE frame, and every reader in the repo takes only the last one (`framestack.py`, `sc25_r3.py`)

The session's most structural finding, and it was reached by chasing a contradiction inside my own
probe's output rather than by looking for it.

Every reader here — `compete.py`, all fourteen drivers, all 800 probes — turns an observation into a
board the same way:

```python
f = np.array(obs.frame)
return f[-1]          # the LAST plane of the stack
```

Correct when a step returns one board. **Silent information loss when a step returns an ANIMATION.**

| game | reset planes | multi-plane verbs (planes/distinct) |
|---|---|---|
| sb26 | 1 | action 5 → **42/11** |
| sp80 | 1 | action 5 → **22/18** |
| sc25 | 1 | **all four verbs → 22/5** |
| cd82 | 1 | action 5 → **15/15** |
| tu93 | 1 | action 4 → 8/6 |
| g50t | 1 | actions 2 and 4 → **7/7** each |
| bp35 | **2** | 3 → 5/3, 4 → 5/4, 7 → 2/1 |
| sk48 | 1 | 1, 3, 4 → 2/2 each |
| ls20 · re86 · tr87 · wa30 · ar25 · cn04 · m0r0 · dc22 · ka59 | 1 | none — single plane throughout |

Two conclusions, and they pull in opposite directions, so both have to be stated.

**Reading `f[-1]` is SOUND for play.** sb26 returns 42 planes on its run action and the campaign
clears it **8/8**; sp80 returns 22 on its fire and clears 2/6. The last plane is what the engine
settles to, and wins are read from `levels_completed`, never from a frame. Nothing about the shipped
agent is broken by this.

**Reading `f[-1]` is a keyhole for DISCOVERY.** Any probe that pressed once and concluded "that action
did nothing" measured the end of an animation. On sc25 that is not a hypothetical:

- at reset `obs.frame` is `(1, 64, 64)`; after the **first press of any verb** it is **22 planes**
- their diffs against entry run `0, 9,9,9,9,9, 18,18,18,18,18, 27,27,27,27,27, 36,36,36,36,36, 0` —
  a four-stage progression in constant 9-cell steps that **snaps back to entry**
- so `f[-1]` = 0, and sc25's first press reads as a no-op while twenty planes show it doing something
- the second press onward returns a single plane and sticks; `sc25_r2.py` shows the second press's
  change is sized by the SECOND action alone (1/2 → 8 cells, 4 → 16, 3 → 32), the first irrelevant —
  which is exactly what an absorbed first press looks like

**sc25 is closed on a full-grid flood fill of "22 components, all four structures individually
refuted".** Twenty-two planes, twenty-two components. That coincidence is now a thing to check rather
than a thing to notice, and if those refutations were single-press probes they refuted the revert.

### How this was found, because the method is the reusable part

`sc25_r1.py` — written by me, an hour earlier — reported the keyboard-only graph **EXHAUSTED at 1 node,
1 distinct board, frontier 0**, and printed a confident verdict that sc25 "cannot be won without the
click". Its own output contained the refutation: the death-control arm in the same file reported a
**20-cell diff** after six plain presses. A board that is a fixed point under every single press cannot
also move twenty cells after six of them. **The file's two halves disagreed, and the half with the
verdict attached was the wrong one.** `sc25_r1.py` is kept as a worked example rather than deleted; its
verdict line is void.

That is the third instrument failure today whose tell was internal inconsistency rather than an error
(after wa30's `-12` step and its `92 of a possible 84`). The pattern is worth naming: *a probe that
prints more than one number is auditing itself, and a probe that prints only its verdict cannot.*

⚠️ **`g50t_r1.py`'s exhaustion proof is QUALIFIED by this, and the qualification is mine to state.**
g50t's actions 2 and 4 return 7 planes, and that search keyed on `f[-1]` like everything else. It is
therefore a proof over END-STATE boards resting on two assumptions now written down: that `f[-1]` is
the true post-action state (sb26's 8/8 through 42-plane frames is the evidence that it is), and that
the board carries the whole state (1,854 distinct boards with zero divergence over 9,270 pairs is the
evidence for that). Win detection is unaffected. The claim stands, scoped: **a proof about end states,
not about animations.**

## 2026-08-16 — cd82 L3: the wall survives a strictly stronger instrument (agent, `cd82_r1/r2.py`)

- **The roller's tumble graph is EXHAUSTIVE at 8 states**, keyed on the roller's full colour-2 pixel
  mask rather than its bbox, frontier drained in 0.2s over 32 step-calls. Every state maps 1:1 to a
  distinct bbox; no bbox holds more than one mask. That **refutes the "hidden face" hypothesis** — the
  roller has no orientation beyond its ring position — and because the graph is closed under all four
  tumble actions from every state, **order and path can never matter**, which is strictly stronger than
  the two ad-hoc one-loop spot-checks it replaces.
- Paint census at all 8 states: every one paints exactly `{0:50, 5:10, 9:50}` or `{0:45, 5:10, 9:55}`.
  Zero deviation, zero sub-50 result. The existence argument (every wedge >= 50, every target region
  < 50) is reconfirmed by an independently built instrument rather than re-asserted.
- **New fact: cd82 L3 has a 100-action life budget ending in GAME_OVER**, never noted in 58 prior probe
  files, and `reset()` after it **preserves `levels_completed=2`** with a byte-identical board. Note
  the shape it shares with wa30 L3, measured the same day: a 100-action clock and a board that reverts
  in full. Two different games, same number.

## 2026-08-16 — sp80 L3: the offset re-key collapses the space 10x and exhausts, with an honest hole (agent, `sp80_r5.py`)

- **Lever 1 landed.** Re-keying on `(offsets from the driver to each of the 3 castles, ammo, driver
  identity)` instead of the board hash: **1,860 states, frontier fully drained in 145s**, against the
  board-keyed search's 18,944 states at 5,778 nodes in 480s **still unexhausted**. A ~10x collapse, and
  the difference that matters is not the ratio but that this one finished. **No win.**
- **Lever 2 answered from the same search rather than a second pass**: all four body identities were
  reached as driver, fire was attempted 416/336/348/388 times from each, none won. So
  "block2-as-final-actor" is not the missing piece.
- ⚠️ **It is not a completeness proof, and the gap is bigger than the search.** **2,987 transitions were
  dropped as unmatchable** — 2,657 because a body's blob count came back != 4 (real occlusion: a body
  walking onto another's screen position merges with it, the documented "occluded, not consumed"
  mechanic) and 330 `multimove` cases whose mechanism is unidentified. **The dropped set outnumbers the
  1,860 visited states.** Any win reachable only by walking one body over another is invisible to this
  search. The instrument's own control is that `multidriver` ambiguity was **0 of 2,987** — whenever a
  frame was matchable it was matched unambiguously, so the drops are the instrument refusing to guess
  rather than guessing wrong.
- Next lever, named: a search that walks THROUGH occlusion events on purpose.

## 2026-08-16 — ka59 L2: THE MOAT IS CROSSED, and the closure was answering a different question (agent, `ka59_r1..r6.py`)

The best result of the session, and it came from re-opening a level on a structural objection rather
than from a new search. The closure read:

> ka59 L2 (moat min thickness 9, no 3-step crossing)

That is an argument about **walking**. ka59's click is a SWAP — the piece teleports to the dot and the
dot lands on the piece's old square — so a verb that does not walk was never covered by it. The
re-open asked one question: *does the closure's sweep cover the click?* It did not.

**What was found — a KICK, never reported for this game before.** Walking into a dot from certain
approach angles launches it a fixed distance, and the flight is **permeable to the moat and to the
bar**. dot0 sits at x=34, close enough that a westward kick lands it at **x=19 — past the moat's far
edge at 21**. Clicking a dot needs no proximity (already known), so clicking the relocated dot
teleports the PIECE across. From there walking reaches box0's interior cleanly.

Proven live, twice, with controls that fired: `ka59_r2.py` reproduced the eastward kick on a fresh
clone before testing westward; `ka59_r3.py` hard-asserted the kick's reproduction before proceeding
and then read `piece[0] = 19 < 21`. **box0 and box1 — previously "unreachable under every possible
sequence of clicks and moves" — are now proven reachable and were both filled** (`ka59_r4/r5.py`).

**The wall has changed kind: it is now the action budget.** The life ended in GAME_OVER at ~138 actions
with box2 and box3 unconfirmed, because the greedy walker "routinely burns its full 40-80 action cap
approaching a target it never exactly reaches". That is an engineering problem — the movement rule is
a 3-cell lattice step checking only the landing cell, which is an exact BFS, the same shape as
`haul.py`'s `_walk`. A precise router is the next lever, not a new mechanic.

**Two corrections the round made to its own earlier reasoning, both worth more than a clean run:**
- Part A argued from phase conservation that a kick was geometrically impossible. Part D then fired one
  by accident (dot1 moved 15 cells east). The conclusion was **retracted rather than defended** — the
  movement model has slides and redirects that break strict phase conservation, visible as an
  unexplained `dy=-4` in `ka59-q7.txt` all along.
- Clicks resolve to a **fixed canonical cell per dot object**, not to the literal pixel clicked — found
  because a control that was supposed to reproduce a known landing did not, and six offset probes were
  spent before anything else was trusted. A control that fails is not always an instrument failure;
  here it was the finding.

⚠️ **One inference in that report is not yet safe, and it is flagged for the next round.** The argument
that dot1 and dot2 cannot also cross (41-15=26 and 44-15=29, both landing inside the 9-cell band,
versus dot0's 34-15=19) assumes the flight distance is always 15. **The same report records flights of
3 and 12 cells.** So the clearance arithmetic needs redoing against a measured distribution of flight
distances, not a constant.

Also still unknown: **`GameState.WIN` was never observed on L2**, so the level's actual win condition
— all boxes, a subset, the piece somewhere — is unconfirmed. Filling what is reachable and reading
`levels_completed` after each fill is what would settle it for free.

## 2026-08-16 — what is actually IN the discarded planes (main thread, `planes_r1.py`)

Follow-through on `framestack.py`, and it **narrows my own finding** rather than widening it. Opened
the multi-plane verbs of the games that are still stuck plus the two whose conclusions leaned on
`f[-1]`:

| game | verb | plane series (diff vs entry) | reading |
|---|---|---|---|
| sk48 | 1 | 66 → **96** | a two-stage motion; `f[-1]` is the settled end |
| sk48 | 3, 4 | 6 → **12** | the braid arm consuming in two steps, end state correct |
| bp35 | 3, 4 | 35 → 39 → 47 → 47 → **47** | settles by plane 2, monotone, end correct |
| cd82 | 5 (paint) | 1 → 41 → … → 209 → … → **51** | sweeps out, then colour 15 fills in; ends at 51 |
| g50t | 2 | 0 → 12 → 22 → 28 → 38 → 48 → **48** | monotone, colour histogram never changes = pure movement |
| sp80 | 5 (fire) | 82 → … → 706 → **2** | the projectile's whole flight, ending back at ~entry |
| **sc25** | all four | 0 → 9 → 18 → 27 → 36 → **0** | **non-monotone: returns to entry** |

**The keyhole only costs a conclusion where the animation is NON-MONOTONE — and that is sc25 alone.**
Everywhere else the last plane is the settled end state, monotonically arrived at, and reading `f[-1]`
loses only the intermediate rendering. Two specific worries are retired by this table:

- **cd82's L3 impossibility premise survives.** Its argument is that every wedge is >= 50 cells while
  every target region is < 50; if an intermediate paint plane were sub-50 the premise would have been
  measured on the wrong plane. The paint's intermediate planes run 41 → 209, never below 50 except
  plane 0's single HUD cell. The premise holds.
- **`g50t_r1.py`'s exhaustion proof survives visibly**, not just by argument: action 2's planes rise
  monotonically 0 → 48 and stop, so `f[-1]` = 48 is the settled state the BFS keyed on, and the colour
  histogram is identical at every plane (pure movement, nothing created or consumed).

sp80's is the most striking picture — action 5's 22 planes are the projectile's entire flight, ending
at a board 2 cells from entry (the HUD) — but it costs nothing, because a shot that changes nothing
IS a miss, and that is what the last plane correctly reports.

*A finding that survives its own follow-through in narrowed form is worth more than one that stays
large: the campaign has one game read through a keyhole, not eight.*

## 2026-08-16 — cn04: colour3 is the WRONG-ANSWER signature, and the handedness axis does not exist (agent, `cn04_r1..r6.py`)

Two results, one that changes how this game is read and one that closes a hypothesis in a single arm.

**1. The true L1 win renders NO dock overlay.** Tracing every frame of the true win (rotate x3) against
the false dock (rotate x1, identical translation math): **colour3 — the "docked" overlay every level-2
experiment has chased — never appears in the true-win trace at all.** The board jumps straight to the
L2 layout on the winning press. colour3 appeared only in the FALSE dock.

Put beside the game's standing fact — *the wrong handedness gives the identical tip-to-tip vector and
renders the same docked overlay without winning* — this makes colour3 **the signature of a coincidence
that is WRONG**. A right-handed coincidence never renders it, because the level is already over. So
every L2 round, including the ones that measured colour3 stacking additively (18, then 18+18=36, then
+9=45), was watching a counter of wrong answers accumulate. Confirmed directly in the L1 table below:
`n_rot=1` gives colour3 **True**, win **False**; `n_rot=3` gives colour3 **False**, win **True**.

**2. The pad-ASSIGNMENT axis I proposed does not exist — refuted on L1, structurally.** The hypothesis
was that with two pads on the mover and two on the target there are two pairings, that pairing is what
handedness means here, and that a harness which picks one implicitly would look exhaustive from inside.
The code trace supported the premise: `cn04_q11_final.py`'s `derive()` does `sorted(pads)` on both
lists and pairs by sorted index — one fixed assignment, never the swap. But driven live across both
assignments and all four rotation states:

| n_rot | assignment | self-consistent | colour3 | WON |
|---|---|---|---|---|
| 0 | A (sorted, incumbent) | no | — | — |
| 0 | B (swapped) | no | — | — |
| 1 | A | **yes** | **True** | False |
| 1 | B | no | — | — |
| 2 | A / B | no | — | — |
| 3 | A | **yes** | **False** | **TRUE** |
| 3 | B | no | — | — |

**The swap is never self-consistent, and it cannot be**: with exactly two landmark points under a pure
translation, `static[a] - moved[0] == static[b] - moved[1]` and its swap are conditions that are
negatives of each other, so generically at most one can hold. Sorted order kept winning that check by
geometry, not by the harness's arbitrary choice. Rotation changes the body SILHOUETTE — which is what
actually separates the true win from the false dock — and does not touch which pairing is valid. So
the axis is a derived fact of rotation, not a second free dimension, and neither harness could ever
have missed a candidate there.

The agent also hand-traced that the L2 own-pad-pair search (`cn04_q49_multi_mover_candidates.py`) loops
both `(i,j)` source orders and both `(a,b)` target orders, so it was already covering both directed
deltas — checked rather than assumed, since it is the same class of bug.

**No L2 actions were spent.** The brief carried an explicit exit clause — validate on L1 first, and if
it fails there say so cheaply — and it was used as written. *An exit clause only saves anything if the
agent is willing to stop at it, and this is the case where one did.*

cn04 L2 now stands at **191 live-driven placements and sequences across eight criteria**, plus four
non-geometric classes refuted this session (clicking the dock overlay, holding to budget exhaustion
while genuinely static and docked, cross-pair dock→undock→dock in both orders, and a 3-junction
all-four-shapes assembly at colour3=45). The level rests.

## 2026-08-16 — sc25's 22-plane animation, explained (agent, `sc25_r4/r5.py`)

The keyhole is opened and what was behind it is a **title-screen flourish**, not a mechanic. Recorded
in full because the shape of the answer is what makes the game's closure safe.

**What the animation is.** Four of box B's own 9-cell colour-0 EDGE blocks — the ones
`sc25_q16.py`'s 3x3-of-3x3 toggle grid has always modelled — flashing to colour 14 one at a time,
cumulatively, then all snapping back together on the last plane:

| plane(s) | what changed | cells |
|---|---|---|
| 0 | nothing (entry) | 0 |
| 1-5 | edge block (49-51, 29-31): colour 0 → 14 | 9 |
| 6-10 | + (54-56, 24-26) | 18 |
| 11-15 | + (54-56, 34-36) | 27 |
| 16-20 | + (59-61, 29-31) | 36 |
| 21 | all four snap back to colour 0 | 0 (== entry) |

Each stage is held for five identical planes (framerate padding), it is strictly additive, and it is
**byte-identical across all four plain verbs AND the click** — 0 of 22 planes differ between them.

**What triggers it, measured rather than inferred.** Not "the first press of a life", and not "an
action that achieved nothing": the trigger is **the board before the action being byte-identical to
the level's entry frame**. The decisive test walked the board off entry with two real presses
(diff 32), then found a genuine mid-life no-op at press 7 — its stack is **single-plane**. A click on
an inert cell shows the flourish on *both* clicks (the board never leaves entry either time), while a
click on a real box-B edge cell shows it on click 1 and a persistent single-plane 9-cell commit on
click 2. It also recurs identically after a mid-life `reset()` and after a real GAME_OVER + reset.

**The 22/22 coincidence is explained, not a missed structure.** The animation's 36-cell peak is
**exactly the union of 4 of the flood fill's own 22 components** — zero peak cells fall outside a
pre-existing component. The closure's census is a static-state census and is unaffected.

⚠️ **But it leaves one narrow, real exposure, and the agent found it in its own follow-through.**
`sc25_q16.py`'s 480-state Gray-code closure walks its sequence across roughly **10-15 life-boundary
rebuilds**, and each rebuild opens with one click from the reverted entry board — which is therefore
**absorbed rather than committed**. That matters more than 15-of-479 sounds, because *a Gray code is a
PATH*: a silently failed transition does not skip one state, it continues from a state the sweep
believes it is not in, so one absorbed click can mislabel an arbitrarily long tail. Being chased now;
the cheap first step is reading whether the rebuild loop reads its census back and retries.

**The reusable part is the trigger's shape.** "Fires when the board equals the level's entry frame"
is a condition no single-press probe can distinguish from "fires on the first press", and the two
imply different things about every later press. Separating them cost one arm — a no-op taken from an
off-entry board — and that arm is the whole difference between an explanation and a story. *When a
cue seems keyed to an EVENT, check whether it is keyed to a STATE.*

### Main-thread verification of the ka59 crossing (2026-08-16, `ka59_v1.py`)

The campaign's rule is that an agent's summary is intent and the agent is the entity that may be
wrong, so the session's biggest claim was re-derived here rather than relayed. What needed checking
was not the positions — those carry their own evidence — but the BOUNDARY they are measured against,
which the agent inherited from the very closure it was overturning.

Re-derived from the level-2 board in the main thread: counting non-background cells per column,
**x = 21..29 hold 64 each — the full height of the board** — while x = 15..20 hold 7 and x = 30+ hold
31 to 37. So the moat is a solid **nine-column** band, exactly the thickness the original closure
claimed, and it is now measured rather than quoted.

Against that boundary the crossing is real: dot0 kicks from x=34 to **x=19**, the click swaps the
piece from **x=37 to x=19**, and LEFT x4 then walks to x=7. Right side to left side, across all nine
columns, confirmed.

*The closure's arithmetic was never wrong. It was answering "can the piece WALK across nine columns",
and the answer to that is still no.* What it did not cover was that this game has a verb which does
not walk, and a second one — the kick — that nobody had found. **A closure is scoped to the verbs its
author knew about, and that scope is invisible in the sentence it is written as.**

## 2026-08-16 — CORRECTION to the sc25 trigger, and sc25 is CLOSED (agent, `sc25_r6.py`)

**The entry above is wrong about the trigger and this supersedes it.** It records the flourish as
firing when *"the board before the action is byte-identical to the level's entry frame"* — measured,
written up as the reusable lesson, and refuted one round later.

**The real rule: action-index 1 of the life is absorbed, regardless of type — verb or click — and
everything from action-index 2 onward commits normally**, provided the action has a genuine target.

The discriminator that separates them, which the earlier round did not run: press one plain verb
(index 1, absorbed) and then **click a real box-B edge block as index 2**. Under "board == entry" that
click must also be absorbed, because an absorbed verb leaves the board entry-equal. It is not — it
commits immediately, single-plane, diff 9, first try. Corner block likewise.

Why the earlier reading survived its own test: the decisive arm there was a genuine mid-life no-op
taken from an off-entry board, and **both** rules predict a single plane for it. Index-1 and
entry-equality coincide in every arm that had been run, so the two hypotheses were observationally
identical until an arm was built where they disagree. *A hypothesis confirmed by every test so far can
still be the wrong one of two that no test has yet separated — and the tell is not that the evidence
is weak, it is that no arm has been designed to make the rivals disagree.*

(One residual quirk, noted and not chased: a click on a DEAD cell re-shows the reveal indefinitely
rather than settling into a flat single-plane no-op, because it never leaves the
"nothing-has-happened-yet" state. It does not touch any real target, and `sc25_q16.py` never clicks
one.)

### And with the corrected rule, sc25's closure is SOUND — 0 of 479 transitions affected

The exposure flagged in the previous entry — that `sc25_q16.py`'s 480-state Gray-code walk opens each
of its life-boundary rebuilds with an absorbed click, and that a Gray code is a PATH so one silent
failure mislabels an arbitrarily long tail — **does not exist**, for a reason nobody predicted:

- **Every reset site in `sc25_q16.py` is immediately followed by a plain-verb "warmup" press**, before
  any click fires (three sites reached in the historical run; a fourth only on a win event, which
  never fired). The warmup consumes the life's one-time absorption slot, so every rebuild click and
  every main-walk click happens at action-index >= 2. **No click in the file is ever the life's first
  action.**
- `do_rebuild` genuinely has no read-back retry — it logs `MISMATCH` and moves on — so the safety is
  not error recovery, it is the warmup.
- **Cross-checked against the historical run's own artifact**: `results/sc25-q16.txt` has **zero
  `MISMATCH` lines** across all 13 life-boundary rebuilds and finishes `patterns_visited=480/480`. Had
  a rebuild click been silently absorbed, the very next `cur == expect` check would have printed one.

Two independent lines — the structural argument from the source and the recorded output of the run
itself — and they agree. **sc25's box-B closure holds end to end; the game is retired.**

*The safety was accidental.* Nothing in `sc25_q16.py` knew about an absorption rule that was only
discovered today; the warmup press was there for some other reason and happened to be the exact
countermeasure. Worth noticing rather than celebrating: the next probe written for this game will not
have a warmup unless someone puts one there deliberately.

## 2026-08-16 — absorption is sc25-ONLY, measured across all seventeen (`absorb_r1.py`)

The sc25 rule — *action-index 1 of every life is absorbed, verb or click alike* — would be expensive
if it were a family trait rather than a quirk: every scripted LINE on such a game would be off by one,
every level-entry probe would silently waste its first action, and a level that dies on a clock would
pay the tax **every life** (wa30 level 3 alone takes 28 lives in a 3,000-action run).

Checked directly: each game, each plain verb, from a fresh reset, pressed twice, reading the settled
board after each. Absorption looks like `diff1 == 0` with `diff2 > 0`.

| verdict | games |
|---|---|
| **COMMITS on the first action** (16) | ls20, re86, tu93, tr87, sk48, sp80, wa30, ar25, cn04, m0r0, cd82, bp35, dc22, sb26, ka59, g50t |
| **ABSORBED** (1) | **sc25** |
| unclear | none |

And across a real death, where it would actually accumulate: sc25 after GAME_OVER + reset gives
press-1 diff **0**, press-2 diff **8** — **absorbed every life**, not merely at the start of the run.

So no driver anywhere else is off by one, and the worry is retired for the cost of one probe. Worth
recording precisely because the answer was the boring one: *the value of the check was never the
chance it would fire, it was that a per-life off-by-one is invisible from inside any single game.*

Note the per-verb columns also settle several small things for free — sk48's action 2 and action 7
move nothing at all from the entry board (`2:0->0`, `7:0->0`), sb26's action 7 likewise (`7:0->0`,
consistent with it being the UNDO on an empty stack), and g50t's actions 1, 3 and 5 move a single cell
while 2 and 4 move 48 (`1:0->1`, `2:48->49`) — which is the HUD ticking versus real movement, and it
is why `g50t_r1.py`'s graph was driven by two verbs' worth of real transitions.

## 2026-08-16 — ka59 L2: budget was never the wall, and the real one is a SECOND moat (agent, `ka59_r7..r12.py`)

The diagnosis from the previous round — "the wall is now the action budget" — is **refuted by its own
fix**, which is the good outcome. An exact 3-lattice BFS router (`haul.py`'s `_walk` shape, adapted;
only the found shortest path is ever replayed on the real trajectory, so exploration is free) reached
dot0's kicking region in **3 actions where the greedy walker needed 50 and still missed**. The whole
line then cost:

| leg | actions | running |
|---|---|---|
| L1 → L2 entry (ferry driver) | 11 | 11 |
| route to dot0 + kick west | 4 | 15 |
| route to dot1 (avoiding dot0/dot2) + kick west | 10 | 25 |
| route to box3 (avoiding dot2) | 5 | 30 |
| click dot0 **from inside box3** (fills box3 AND crosses, for free) | 1 | 31 |
| route to box0 | 3 | 34 |
| click dot1 from inside box0 (fills box0) | 1 | 35 |
| click dot2 (return trip) | 1 | 36 |
| route to box2 | **not found** at 900 BFS nodes | 36 |

**36 actions of a ~127-action clock, >90 to spare.** And `levels_completed` stayed at 1 through both
fills, read after each — so two boxes is not the win.

**The real wall: a SECOND, internal moat.** A colour-15 band **6 rows thick (y=24-29, full width
x=0-21)** splits box1 (y=8-15) from box0 (y=41-48) inside the left region. None of the three dots'
kicks, in the geometries tested, crosses it.

**Kick geometry is now aimable, and the flight distance is emphatically not a constant:**

| dot | approach | direction | distance |
|---|---|---|---|
| dot0 | from due east | **west** | **−15** (34 → 19) — clears the 9-column moat |
| dot1 | from due east | **west** | **−24** (41 → 17) — clears it with margin |
| dot1 | from due south | north | **−3** — nowhere near the 6-row band |
| dot2 | same relative approach as dot0/dot1 | **east**, not west | — |

So direction is a property of **approach geometry**, not of which button is pressed — and the earlier
"dot1/dot2 cannot cross because 41−15=26 lands in the moat" arithmetic was wrong in exactly the way
flagged: it assumed 15. dot1 goes −24.

**Death semantics re-measured here rather than inherited**: 123 presses to exhaust the clock,
GAME_OVER, `reset()` returns the board **byte-for-byte to L2 entry**, piece and all three dots — with
the kick fired first as the positive control so the diff was shown able to fire. Matches sp80, bp35
and g50t. The whole line must fit in one life.

**What is open, in the order it is being chased**: (1) **box2's unreachability is undiagnosed** —
router bug, node budget, or genuine obstruction were never separated, and a search that fails to find
a path is worthless without a positive control; (2) **whether box1 is required at all** was never
confirmed — if box2 completes the level the internal moat is irrelevant, which is why box2 comes
first; (3) **chained kicks** (nobody has kicked an already-kicked dot, and dot1 sits at (17,34) after
its −24 flight) and northward geometry on dot0/dot2, untested on a quantity already shown to vary by a
factor of eight.

## 2026-08-16 — ka59 L2: the PHASE LAW, box1 proven required, and a chained kick that crosses the internal band (agent, `ka59_r13..r16.py`)

Three results, and the first is a law rather than a fact.

**1. box2 was never obstructed — it was a PHASE MISMATCH.** The router found no route from (44,48) to
box2 at 900 nodes and then none at 5,000, so the null was not a budget. A flood fill from (44,48) on
the 3-lattice converged at **88 cells** — converged, far under any cap tried — with box2's interior
absent. Comparing coordinates settled it: (44,48) mod 3 = **(2,0)**, box2's interior (52,52) mod 3 =
**(1,1)** = **spawn's own phase**.

> **Movement changes one axis by a multiple of 3 per press, so `(x mod 3, y mod 3)` is INVARIANT under
> walking. The only verb that changes phase is the CLICK.**

So box2 was reachable only from spawn's phase, and every dot-click in the earlier line had already
moved the piece off it. **This makes the ORDER of clicks part of the solution** — the third game in
this campaign where that is the whole puzzle, after ar25's levels 3 and 4, and the same lesson: *a
one-way door belongs in FRONT of the search.* A failed path search is worthless without a positive
control, and this one had one (the router re-deriving the known 3-action dot0 approach), which is what
made "not a bug" believable before the phase arithmetic was even looked at.

**2. box1 is REQUIRED, measured rather than inferred.** Visiting box2 first at spawn phase (17
actions) and then running the kick/cross/fill line for box3 (dot0) and box0 (dot1): box2 visited,
box3 filled, box0 filled, box1 empty → **still `NOT_FINISHED` at action 45**. Three of four is not the
win.

**3. A CHAINED kick crosses the internal band.** dot1 kicked west to (17,34) is still an active,
unconsumed dot; approached from the south at its NEW position and pressed UP, **it kicks again** —
(17,34) → (17,19), a −15 flight, crossing y=24 into the far side of the 6-row band. First confirmation
that a kicked dot can be kicked a second time.

**Flight table, and the distance varies by a factor of eight:**

| dot | approach | direction | from → to | distance |
|---|---|---|---|---|
| dot0 | east side, near (36-39, 42-46) | west | (34,44) → (19,44) | **−15** |
| dot1 | east side, region (48-52, 33-35) | west | (41,34) → (17,34) | **−24** |
| dot1 | south, region (38-45, 36-43) | north | (41,34) → (41,31) | −3 |
| dot1 (already crossed) | south of (17,34) | north, **chained** | (17,34) → (17,19) | **−15** |
| dot1 | west side, walking toward it | east (accidental) | (41,34) → (56,34) | +15 |
| dot2 | west side, walking toward it | east (accidental) | (44,47) → (59,47) | +15 |

Consistent with the L1 reading that a kick is **slide-until-blocked**, not a fixed-distance teleport.

**Still open**: routing from the chained-kick landing (19,38) to box1's interior (9-11, 9-14) is NOT
FOUND at 1,500 nodes, and **phase is not the culprit this time** — (19,38) mod 3 = (1,2) matches
box1's (1,2) exactly. Undiagnosed: obstruction, avoid-list interaction, or a still-larger cap. The
box2 diagnostic (converged flood fill, print size and extent) is the obvious instrument and was not
run. Also unassembled: no single life has yet done all of it — `r14` proved the three-target line in
45 actions while `r15`/`r16` proved the chain with dot0 spent as a bare ferry and dot1 never clicked
into any box. With ~127 actions of clock against 45 for three targets, **the budget is very unlikely
to be the remaining wall**; the assembly is a sequencing problem under the phase law.

## 2026-08-16 — ka59 L2: the full line assembles in 45 actions, and the wall is a THIRD phase mismatch (agent, `ka59_r17/r18.py`)

**The zero-waste line now exists end to end** and runs inside one life: box2 visited at spawn phase
(17 actions) → dot0 and dot1 both kicked west (35) → box3 filled by dot0 with a **free crossing**,
because the click was made from inside box3 (41) → dot1 **chain-kicked north** from (17,34) to
(17,19), clearing the 6-row internal band (44) → dot1 clicked, piece crosses to (18,19) for free (45).
**45 actions of a ~127 clock.** `levels_completed` stayed at 1 throughout, consistent with box1 being
required.

**And box1 is blocked by the same law for the third time.** The flood fill from (19,38) converged at
**70 cells** (x=1-19, y=32-60) under a 3,000-node cap with box1's interior absent — again not a budget
problem. But the diagnosis is not "a wall": the piece's landing cell after the crossing is **(18,19),
phase (0,1)**, while box1's centre (10,11) is **phase (1,2)**. Three mismatches now, in three
different places, and they are one mechanic rather than three obstacles:

> **The click swaps the piece onto the clicked dot's canonical cell, so the piece's post-crossing
> PHASE is a property of where the DOT is. And the dot's position is set by the KICK.**

So phase is not something that happens at the end of a crossing — it is a knob that gets set *before*
clicking, by choosing where the dot is kicked to. That turns "find a route to box1" into "which
reachable dot landing has a canonical cell of phase (1,2)?", which is an enumeration rather than a
search. Direct evidence that the approach row is a real degree of freedom is already in the table:
dot1's two westward flights differ, **−24 from one region and −3 from another**.

⚠️ **The canonical cell is not always the dot's own coordinate** — the dot sat at (17,19) and the piece
landed at **(18,19)**. Any phase arithmetic has to use the cell the PIECE lands on, measured, not the
dot's.

Two cheap questions that could make the enumeration unnecessary and have never been asked: **does box1
need a DOT placed in it, or only a piece VISIT?** (box2 counted as *visited*, not filled, in the r14
line — so a visit may be the whole requirement) and where box0 belongs in the final ordering, since
r18's assembly dropped it while r14 had filled it.

**Instrument debt, flagged and unpaid:** `bfs_route` overwrites `cur_env`/`cur_obs` on its
None-return path — present since r10, harmless so far only because every call site after it either
asserts or is a run's last leg. *A state-corrupting failure path inside the one routine every leg
depends on is exactly the shape of bug that produces a confident wrong measurement*, and the next
round will not necessarily be lucky.

## 2026-08-16 — ka59 L2: the phase knob WORKS, and "fill all four boxes" is FALSIFIED (agent, `ka59_r19/r20.py`)

**The knob works, and the mechanism is a conservation law rather than a heuristic.** dot0's west kick
lands at **(19,44), phase (1,2)** — exactly box1's centre phase. Chain-kicking it north **preserves
that phase**, because kick distances are multiples of 3 just like walking. Clicking it landed the
piece at **(19,20), phase (1,2), confirmed live**, and box1's interior opened immediately — routed
straight in, reaching (10,14) at action 59, after two flood fills had shown it unreachable from every
earlier landing.

> **A kick moves a dot without changing which phase-class it can hand the piece. So each dot has a
> FIXED phase it can deliver, decided at its spawn, and the kick only chooses where along that class
> it lands.**

That is stronger than "phase is a knob": it constrains the dot→box assignment before any planning
starts, and it is the third distinct place on this game where the ORDER of engagement turned out to be
the puzzle (box2's spawn-phase-first requirement, the main moat, and now box1).

**Phase / landing table:**

| dot | event | landing | phase | note |
|---|---|---|---|---|
| dot0 | west kick | (19,44) | **(1,2)** | matches box1's own phase |
| dot0 | + chain-kick north | (19,20)/(19,21) | **(1,2)** | preserved — the −24 flight is a multiple of 3 |
| dot1 | west kick | (17,34)/(18,34) | dot's cell (2,1); **piece lands (18,34)/(18,19)** = (0,1) | canonical cell != dot's own coordinate, confirmed twice |
| dot2 | untouched | (44,48) | (2,0) | |
| box0 centre | — | (8,44) | (2,2) | south of the internal band |
| box1 centre | — | (10,11) | **(1,2)** | |
| box2 centre | — | (52,52) | (1,1) | = spawn's phase, which is why box2 must be visited FIRST |

**And the win condition is now falsified rather than unknown.** Three arms in sequence, in one life:
box1 **visited empty-handed** → still `NOT_FINISHED` (action 59); box1 **with a dot placed** → still
`NOT_FINISHED` (60); and then the full zero-waste assembly — box2 visited, dot1 into box3, dot0 into
box0, dot2 into box1, **all four targets satisfied with no dot spent as bare ferry fare** — **still
`NOT_FINISHED` at action 64**, of a ~127 clock.

**So "fill all four boxes" is not the win.** The most likely remaining reading, and the one nobody has
run: **the pairing is SIZE-MATCHED**. The zero-waste routing happened to produce **dot0→box0 and
dot2→box1**, which is the **reverse** of the recon's original ring-size guess (dot0↔box1,
dot2↔box0). If this level pairs a dot to a box by an observable property, every line run so far has
placed the right number of dots in the wrong boxes — which reads from outside exactly as it does:
everything filled, nothing won.

Being chased, in order: measure what actually distinguishes the dots and the boxes (if all three dots
are identical in every readable respect the hypothesis dies for free), check whether the matched
assignment is even **phase-feasible** from the table above before spending actions on it, then the
remaining permutations. Plus two questions that are not about pairing at all: whether the PIECE must
END somewhere specific (r20 left it at (44,48), wherever the last click put it), and whether **box2
needs a DOT rather than the visit it has always been given** — box2 is the one target that has only
ever been visited, and it is also the one that forced the entire spawn-phase-first ordering. *It would
be characteristic of this level for the thing that looks like a free visit to be the requirement
nobody tested.*

Gap in the data, flagged: **dot2's kick geometry has never been cleanly measured** — only dot0 and
dot1 have full kick+chain data, and dot2 is the dot a matched pairing may need to reposition.

## 2026-08-16 — ka59 L2: the SIZE-MATCHED PAIRING is measured fact, and box2 matches the PIECE (agent, `ka59_r21..r23.py`)

The recon's original ring-size guess is no longer folklore. Measured, zero extra actions: every dot's
footprint is tiny (1x2, 2x1, 2x2) but each sits inside a **colour-14 HALO** whose bounding box matches
one box's interior **exactly**, in orientation, with no dot matching two boxes:

| dot | footprint | halo bbox | halo size | | box | outer bbox | interior | matches |
|---|---|---|---|---|---|---|---|---|
| dot0 | 1x2 | (33,42)-(35,47) | **3x6** | | box1 (top-left) | (8,8)-(12,15) | **3x6** | dot0 |
| dot1 | 2x1 | (39,33)-(44,35) | **6x3** | | box3 (right) | (53,38)-(60,42) | **6x3** | dot1 |
| dot2 | 2x2 | (42,45)-(47,50) | **6x6** | | box0 (bottom-left) | (5,41)-(12,48) | **6x6** | dot2 |
| | | | | | **box2** (piece station) | (50,50)-(54,54) | **3x3** | **the PIECE itself** |

**That last row answers a different question than the one being asked.** Three dots each match one
box; the fourth box matches the PIECE. So box2 is the piece's own station, and "does the piece have to
END somewhere" stops being a loose end and becomes the obvious fourth requirement — every run so far
has left the piece wherever the last click happened to drop it.

**The matched pairing was then run and still does not win**: box2 visited, box3 filled with dot1
(matched), box0 filled with dot2 (matched), box1 reached and visited but not filled — dot0 spent as a
pure bridge onto open floor. 64 actions, `levels_completed` 1. So visiting box1 is not enough even
with the other two correctly matched.

**The reported deadlock — 4 demands against 3 dots — rests on a premise that was stated and never
measured**: that a dot clicked onto open floor is SPENT. Two readings, not the same object:
- **consumed only when it lands in a BOX** → an open-floor click merely RELOCATES it, it stays
  clickable, and there is no deadlock: cross via dot0, walk into box1, click dot0 again from inside.
- **one click per dot, period** → the count holds.

The round's own earlier data leans to the first — dot1 was kicked west, then **chain-kicked again from
its new position while described as "an active, unconsumed dot"** — and clicks have no proximity
requirement, so a dot's location never limits whether it can be clicked. One arm settles it: click a
dot onto open floor, then click the same dot again. Being run now.

If dots survive open-floor clicks the line is nearly written, and it is the natural reading of the
table above: cross using whichever dot's phase serves, walk into each box, click its MATCHED dot from
inside (proximity is irrelevant — only the PIECE has to be in the box), then walk to **box2** and
stop. That would be the first line in this game's history satisfying all four property-table matches
at once.

If dots really are one-click-only, the named escape is a **third kick**: dot0 sits at (19,20)/(19,21)
after its chain, and a third kick west from the east side might land it *inside* box1's interior
(x9-11), so one click both crosses the piece and places dot0 correctly. Every chain so far stopped at
two deep for no reason other than nobody trying a third.

*The transferable point: a resource-counting impossibility argument is only as good as its consumption
rule, and consumption rules are exactly the kind of premise that gets asserted in passing while the
arithmetic around it gets all the scrutiny.*

## 2026-08-16 — ka59 L2: dots are ONE-CLICK-ONLY (my hypothesis refuted), and a COMPOUND SWEEP nobody chased (agent, `ka59_r24/r25.py`)

**The consumption question is settled against me.** I argued the 4-demands-vs-3-dots deadlock rested
on an unmeasured premise and that a dot clicked onto open floor probably just relocates. It does not:
kicked dot0 west, clicked it (piece → (19,44), dot0's cells gone from the dot list, the vacated cell
reading plain floor colour 1), walked one step away, clicked the **identical coordinate** again — the
piece did not move and no dot cells changed. **Dots are one-click-only.** The deadlock is real as
reported.

**But the arithmetic double-counts, and the correction is a trick the same agent used twice and then
stopped using.** `r14` and `r20` both did it: clicking a dot **while standing inside a box** fills that
box AND teleports the piece to wherever the dot is. So a click spent as *cargo* is simultaneously a
free *ride*, and the count is not 4 demands against 3 dots — it is

> **3 dots → 3 clicks → 3 boxes filled AND 3 crossings.**

which is exactly enough, and turns a resource shortage into a **sequencing** problem. The plan follows
from the measured tables: kick every dot into position FIRST, while the piece is still on the right
side and everything is reachable; then box3 ← dot1 (piece lands where dot1 was pre-kicked, past the
main moat), box0 ← dot2 (pre-kicked north of the internal band on phase (1,2), which a chained north
kick preserves), box1 ← dot0 (pre-kicked toward box2, where the piece should end).

**Two other results this round:**

- **The third-kick escape is circular and dead.** Reaching "east of dot0's chained position (19,20)"
  requires already being north of the internal band — which is the crossing dot0 itself was meant to
  provide. Same circularity, one level deeper.
- **A COMPOUND SWEEP: one kick moves TWO dots.** Approaching dot2 from the east with a route that
  deliberately avoided dot0's cells, the first westward press relocated **both**: dot0
  (34,44) → **(13,44)** and dot2 (44,47) → **(17,47)**, both past the moat. It reproduces the same
  effect seen twice earlier in `r7`/`r9`, so it is **not an approach-path artifact** — and it was left
  entirely untested. Two dots pre-positioned for one approach is precisely what a plan needing three
  pre-kicked dots wants. What governs it — which dots move together, and whether each landing can be
  steered — is the open question.

Also still untested after five rounds: **whether box2 needs a dot or only a visit.** Under the
sequencing plan box2 is where the piece ENDS, so a visit is what it would naturally get.

*The reusable point, and it cuts against my own last message as much as for it: an impossibility
argument built on counting requires both a consumption rule AND a correct accounting of what each
expenditure BUYS. The consumption rule here was right and I doubted it; the accounting was wrong and
nobody checked it, because a click that does two jobs looks like one job in a ledger.*

## 2026-08-16 — ka59 L2: the phase argument becomes structural, and the fill-permutation space is exhausted (agent, `ka59_r26.py`)

**The five premises, each measured, and together they say box1 cannot be correctly filled:**

1. **box1's interior is walkable only from phase (1,2)** — two independent flood fills, both bounded
   and converged (70 cells from (19,38); 88 cells from (44,48)), both excluding it.
2. **Each dot's canonical click-phase is fixed by its own identity**: dot0 → **(1,2)**, dot1 → (0,1),
   dot2 → (2,0).
3. **Kicks preserve phase** — flight distances are multiples of 3, so a kick moves a dot only within
   its own phase class. Re-confirmed this round.
4. **Dots are one-click-only** (measured last round: second click on the identical coordinate does
   nothing).
5. **The halo↔interior size match is exact and one-to-one**: dot0 3x6 ↔ box1, dot1 6x3 ↔ box3,
   dot2 6x6 ↔ box0, box2 3x3 ↔ the piece.

From (1)+(2)+(3): the only click that can put the piece **into** box1 is a click on **dot0**. From (4):
that click spends dot0. From (5): box1's correct occupant **is** dot0. So the click that grants access
and the click that places the matched dot are the same click, and it cannot be both. **Under the
measured model, box1 can never be correctly filled.**

**And the fill-permutation space is exhausted**, which is what makes that a problem rather than a
puzzle: box3 matched + box1 visited (59) · box3 matched + box1 filled mismatched, box0 empty (60) ·
box3 + box0 both matched, box1 visited (r22, 64) · **all three boxes filled with all three dots, only
box3 correct (r20, 64)**. Every reachable 2-of-3 and 3-of-3 combination has been run and none wins —
so a pure "N dots placed" count is refuted too, and correctness is required somewhere the model cannot
deliver it.

**Conclusion: something in the model is wrong**, and re-sequencing inside it cannot find what. Same
place re86 level 6 reached — every arrangement of the known mechanic refuted, so the mechanic is not
the one.

**The surface that has never been swept, and it is the obvious candidate**: every click in this game's
history has been aimed at a **dot**. The whole model — swap, canonical cell, phase class, consumption
— is built from those clicks. But the click is a general verb with 4,096 targets and **level 2 has
never had a click sweep at all**. The structures the model currently treats as scenery are exactly the
ones that carry its information: the boxes' interiors and frames, the **colour-14 halos** (the object
that carries the size-matching, and never once clicked), the moat columns, the internal band, and box2
itself. Being swept now, click-then-ACT.

Also finally being run: **does box2 need a DOT or only a VISIT** — flagged three rounds running, one
arm, and if box2 needs a dot then four boxes need four dots against three that exist, which would
falsify the model outright.

**Open and uninterpreted**: the COMPOUND SWEEP. One westward press near dot2 relocates dot0 as well,
reproducibly, on routes built to avoid dot0 — seen in `r7`, `r9` and `r25`. It was set aside as moot
for the phase plan (it cannot change dot2's y-phase) but its mechanism is unexplained, and an
unexplained mechanic on a board whose model is known to be wrong is not a detail to leave lying.

## 2026-08-16 — ka59 L2: CLOSED, STRUCTURAL — with the premise to attack named (agent, `ka59_r27/r28.py`)

Both final surfaces came back empty and the level rests on a stated contradiction rather than on an
arm count.

- **The non-dot click sweep found nothing.** 19 candidates click-then-ACT (every box's frame and
  interior corner, 2 halo cells per dot, 2 moat columns, 2 internal-band cells), each clicked on a
  fresh deepcopy then diffed against the same presses with no click. **Box frames, box interiors, moat
  columns and the internal band are all click-inert.** All six halo cells "responded" — and a direct
  check killed it: clicking **(33,42)**, a colour-14 halo cell one cell outside dot0's own footprint,
  lands the piece at **(34,44)**, dot0's exact canonical cell. That is the known dot-swap re-firing
  through its proximity tolerance, not a new mechanic. *A response is not a new mechanism until you
  check whether the old one explains it.*
- **box2 needs neither a dot nor a visit — it wins nothing either way.** Walked in, clicked dot1 from
  inside, dot1 consumed, piece moved, `levels_completed` still 1. The question flagged for three
  rounds is answered and it does not open anything.

### The closure, and the part worth keeping

Five measured premises:

1. **box1's interior is walkable only from phase (1,2)** — two bounded, converged flood fills exclude
   it from every phase tried except the one dot0 delivers.
2. **Each dot's canonical click-landing phase is fixed by identity** — dot0 (1,2), dot1 (0,1), dot2
   (2,0), measured across every kick geometry tried.
3. **Kicks preserve mod 3** — every measured flight (−15, −24, −3, +15, −15) divides evenly by 3; no
   kick has ever shifted a dot's phase class.
4. **Dots are one-click-only** — a second click on the coordinate a dot's marker vacated does nothing.
5. **The halo↔interior size match is exact and exhaustive** — dot0 3x6↔box1, dot1 6x3↔box3, dot2
   6x6↔box0, box2 3x3↔the piece; no other pairing exists.

Together: the only click producing phase (1,2) is dot0's, and it is spendable once, so **no line can
both deliver the piece to box1 and leave dot0 available to be correctly placed there.** Every fill
combination reachable under these five has been run and lost.

**What would have to be false — ranked, which is the actually useful output**: most attackable is
**premise 2 or 3** — a single counter-example (one kick, one untried approach angle, any dot, landing
off its "locked" phase class) collapses the deadlock immediately, because the corrected
click-does-two-jobs plan otherwise writes itself from premise 5's tables. Next is **premise 1** — only
two flood fills have ever run, both from origins dot0 or its chain produced, so a fill from a
genuinely different phase is untried. **Premises 4 and 5 are the most solidly measured and the least
likely to be wrong.**

Left uncovered and worth naming: the sweep was 19 hand-picked cells, not the 4,096; the halo's full
extent as a click target is unswept beyond two corners; "one-click-only" was measured for an
open-floor click and *assumed* for a box-placed marker; and **the compound sweep is still
uncharacterised** — whether it is steerable, and whether it could produce a phase dot0's own kicks
cannot, which is precisely the counter-example premises 2 and 3 need.

*This is the shape a stuck level should end in. Not "we tried a lot", but "here are five facts, here
is the contradiction they force, and here is which one to break." A future session attacks a premise
instead of re-deriving a board.*

## 2026-08-16 — ka59: premises 2+3 HOLD under a real sweep, and the compound sweep is characterised (agent, `ka59_s1..s4.py`)

The structural closure was handed a target — *break premise 2 or 3 and the whole deadlock collapses* —
and the target survived a much harder instrument than the four scattered angles that produced it.

**156 arms**: all 3 dots x all 4 approach sides x offsets −18..+18 in 3-cell steps (126 reachable, 30
NOT FOUND), producing 28 distinct kick events. **Zero displacements not congruent to 0 mod 3.**

| dot | approach | pressed | displacement | mod 3 |
|---|---|---|---|---|
| dot0 | east / west / south(wide) / north | west / east / north / south | −15 / +15 / −12 / +15 | (0,0) |
| dot1 | east / west / south / north / chained-north | west / east / north / south / north | −24 / +15 / −3 / +15 / −15 | (0,0) |
| dot2 | east / west / south / north | west / east / north / south | −27 / +15 / −12 / +12 | (0,0) |

Premise 2 is not independently testable — it is a corollary of premise 3 plus each dot's fixed spawn
phase — and the same data confirms it: every dot0 landing is phase (1,2). **The box1 deadlock stands**,
and the next premise to attack is **1** (only two flood fills have ever run, both from origins dot0 or
its chain produced).

**The compound sweep is now characterised — the *what*, not the *why*.** It is real (verified by
re-reading dot state immediately after routing, BEFORE the explicit press) and it is
**approach/geometry-specific, not a fixed dot-pair property**:

| trigger press | dots that move | displacements | mod 3 |
|---|---|---|---|
| dot2 west (east approach) | dot0 + dot2 | −21, −27 | (0,0) both |
| dot0 east (west approach) | dot0 + dot2 | +15, +9 | (0,0) both |
| dot1 south (north approach) | dot1 + dot2 | +15, +6 | (0,0) both |
| dot2 north (south approach, wide) | dot2 + dot1 | −12, −3 | (0,0) both |

**dot0 pairs with dot2 and dot1 pairs with dot2; dot0 and dot1 were never observed pairing directly.**
Kicking dot0 alone does *not* move dot2 — the coupling is press-specific, not a standing bond. Every
compound landing is mod3 = (0,0) for both members, so the sweep relocates two dots at once and never
breaks phase. Mechanism uninterpreted: a domino along the flight path, or a shared launch-eligibility
condition independent of proximity.

⚠️ **An attribution bug was caught and fixed mid-round, and it would have manufactured findings.**
`bfs_route`'s `avoid` parameter only forbids LANDING on a dot's cells, not passing near one — so a
route can kick an unrelated dot **during pathfinding**, before the intended press. Re-running every arm
that reported >=2 movers with the dot state re-read immediately after routing: 8 of 9 were genuine
same-press compounds, **1 was a route-induced false positive**. *A probe whose own navigation can
trigger the effect it measures needs a reading taken between the navigation and the trigger.*

## 2026-08-16 — ar25 L5: two searches died on the KEY, and the third diagnosis is the ticker (main thread, `ar25_s1..s3.py`)

Level 5 had never had a search — 25+ probe files and 335,872 click-then-ACT arms, all sampling.
Exhaustion looked available because **A5 is a measured byte-identical alias for the click**, collapsing
4,096 targets into one verb already in the plain set, so `[1,2,3,4,5,7]` is a complete action set.

- **`ar25_s1.py`** — board-keyed BFS. Controls all passed: deepcopy fidelity, and **a death REVERTS**
  with a 321-cell positive control firing, so dropping `GAME_OVER` children is sound. It did not
  converge, and the growth curve is the tell: boards +1.73 per node expanded, frontier +0.73, **dead
  straight** at branching six. *A search converging on a finite state space does not do that* — the key
  was separating states that are the same, and the run was enumerating action SEQUENCES. Killed at
  10,000 nodes rather than allowed to burn its budget to a guaranteed "not exhausted".
- **`ar25_s2.py`** — same search with **row 63 masked**, on my theory that the known per-action HUD
  counter (the two cells the A5-vs-click check had to exclude) was the ticker. **4,263 KEYS against
  4,263 raw boards — the mask changed nothing.** Hypothesis refuted by its own instrument, cheaply.
- **`ar25_s3.py` found it.** Pressing the same verb twice and intersecting the two deltas: **181 cells
  change on BOTH presses, bbox (0,12)-(62,14), colour 9 at entry** — **a full-width, 3-row band that
  advances every action.** That is the "moving comb" this level's own write-up names when it explains
  colour 4 as occlusion paint. A board-derived key can never converge while the comb repaints part of
  the board every action.

Two facts fell out for free: **actions 3, 4 and 7 change NOTHING from the L5 entry state** (0 cells),
while action 1 moves 318 cells, action 2 moves 345 and introduces colour 4, and action 5 moves 36.

The comb is almost certainly deterministic and periodic, which makes the search tractable again —
key on `(board with the comb's rows masked, comb phase)`, or on `(masked board, depth mod period)` if
the comb advances with the action count, since BFS depth then fixes the phase. Being run.

*Two failed searches, and the useful output of both was a growth CURVE rather than a result. A search
that does not converge is telling you about your key, and the shape of the divergence says which
hypothesis to test next — straight-line growth at full branching means "every child is novel", which is
a statement about the state function, not about the game.*

## 2026-08-16 — sp80: ⚠️ CORRECTION — `sp80_r5.py`'s "exhausted, no win" is a SUSPECTED FALSE NEGATIVE (agent, `sp80_s1..s5.py`)

**This supersedes the sp80 entry above.** That entry recorded the offset re-key as the round's success:
*1,860 states, frontier fully drained in 145s, versus the board-keyed search's 18,944 unexhausted.* The
collapse was real. **The exhaustion was not, and the key is why.**

I told this round to keep the offset re-key. That instruction was wrong, and the agent proved it rather
than following it:

> Keying on `(offsets from the driver to each castle, ammo, driver identity)` **omits the other three
> bodies' absolute positions entirely** — and any of those bodies can itself have been driven and moved
> earlier in the search. So two genuinely different boards, same driver position and ammo and identity
> but different history for the other bodies, **alias to the same key**.

**Proven live, and the positive control is what caught it.** Re-deriving level 2's known 7-action win
by blind BFS: with the driver-relative offset key the search reported **full exhaustion at depth 7 with
NO win**, while a scripted replay of the exact known winning line through the *identical* transition
code succeeded with zero anomalies at every step. Switching the key to the **full absolute positions of
all four bodies** made the blind BFS find the known win. So the instrument could not find a win it was
standing on, and said "exhausted" while doing it.

**Consequence: `sp80_r5.py`'s result is not a null about level 3, it is a null about that key** — and it
is now suspect independently of the occlusion-drop problem it was already known to have.

*The general form is worth more than the sp80 fact: a state key that omits part of the mutable state
does not merely lose states, it MERGES them, and a merged search reports EXHAUSTION — the most
confident possible negative — while silently pruning the answer. Only a positive control on a win you
already possess can catch it, because every other symptom looks like a hard level.*

### And the occlusion subgraph is recovered — 2,972 of 2,987

The 2,987 dropped transitions were never a mystery about the game; they were a reading artifact, and
two measurements settle it:

- **Non-driven bodies provably never move** (all four arrows displace only the driven body, exactly
  4px on its axis, clamped at edges).
- **A covered body's visible bbox shrinks from the covered side** under partial occlusion, vanishes at
  full overlap (blob count 4→3), and reappears correctly on separation — while the driver's own blob
  stays undistorted, because it draws on top and is never itself occluded.

So the fix is to stop re-reading them: a non-driven body's position is learned once from an unoccluded
bootstrap and carried forward, and a transfer is resolved by matching the post-action colour-9 position
against the four stored positions. That recovers **2,972 of the 2,987** (down to 15 unresolvable "no id
matched" anomalies).

**The 330 `multimove` cases are explained and were never real**: in all 8 sampled, the driver moved by
its own known displacement AND a *static* body's reported x0 shifted one lattice step perpendicular —
exactly the partial-occlusion pixel effect above, on a body sharing a row or column with the driver's
new position. **Zero of the 8 were a second-order move.**

**Where the search stands**: 25,644 states, 6,910 nodes expanded in 540s, **frontier 17,723 and still
growing**, no win. A time-bounded null, explicitly not a proof, at ~12.8 nodes/s. Caveats the agent
flagged rather than buried: 1,695 "transfer_multi_match" cases are resolved by a plausible but unproven
heuristic (prefer the current/clicked id), and 15 "transfer_no_match" cases are unexplained and could
be a third mechanism or a residual instrument gap.

## 2026-08-16 — ar25 L5: an exhaustion at 21 states, HELD PENDING one reconciliation (agent `ar25_t1.py` + main-thread check `ar25_v1.py`)

An agent reports level 5's reachable graph **EXHAUSTED at 21 distinct keys, divergence 0, no win** —
which would be a proof and would close ar25's remaining four levels. It is recorded here as **held, not
banked**, because the same report flags a contradiction it could not resolve, and a proof with an
unexplained inconsistency in it is not a proof yet.

**What the search established, and this part is solid:**
- **THE COMB: step 3 rows per real press, 21 distinct phases, and it CLAMPS rather than wrapping** —
  at phase 0 and phase 60 the press is itself blocked. Direction is verb-dependent (action 1
  decrements, action 2 increments). **It does not advance on blocked presses** — measured directly,
  action 3 pressed 60 times from entry, 0 of 60 produced any diff.
- **A SECOND ticker, found by round-trip validation** (action1-then-action2 is net-zero yet did not
  return to the entry key): two things bundled — a decorative colour-0 dash lattice flipping in place,
  and **a second HUD counter at COLUMN 63** (colour 11→12, rows 0-2), the twin of the known row-63 one.
- **A false lead chased and killed inside the round**: colour 11's total count drops by 1 per real
  press regardless of direction, which looked like the band permanently eroding a target. Measuring the
  target blob directly (207 cells, rows ~15-41, column 63 excluded) shows it never changes under any
  action — the "erosion" was entirely the column-63 HUD tick.
- Key validation was done properly: mask-keeps-signal PASS, **0 divergence over 21 nodes x 6 actions**,
  and **21 distinct keys against 80 distinct raw boards** — so the mask collapses 80 semantically
  identical boards into 21 real states rather than over-masking into a trivial graph.

**The contradiction, which the agent flagged rather than glossed:** the campaign's standing L5 numbers
are *W's position space is 441 (21x21)* and *S's reachable rectangle is 289*. A graph of 21 states
cannot contain those. And **21 is exactly the number of band phases** — i.e. under this key nothing
except the comb ever changes anywhere in the reachable graph.

**Main-thread verification (`ar25_v1.py`), and it does not refute the result:** centroid and cell count
of every colour on the RAW board, no mask, over 12 presses of each verb.
- actions **3, 4 and 7: no colour's centroid moves at all**;
- **colour 10 moves a lot but is PAINT** — count goes **288 → 328 under both action 1 and action 2**,
  the same +40, centroid travelling in opposite directions: that is the band painting, not a piece;
- **colour 11 moves 0.5-1.4px with its count falling** — the column-63 HUD tick the agent identified;
- **no compact colour makes a clean rigid translation under any verb.**

**So the search is not obviously wrong. It is unreconciled**, on two points that are one point seen
twice: **colour 5 holds exactly 151 cells**, and the standing note reads *"the joint (W row x S phase)
surface maxes at 99/151"* — that 151 is almost certainly this object, which makes colour 5 the thing
every earlier round measured, and the agent **never once observed it move**. Meanwhile the search's
action set includes A5, a measured byte-identical alias for the click, so selection should have been
reachable inside it and movement after selection should have expanded the graph. It did not.

Being settled now: identify W and S by driving `mirror.py`'s `L4_LINE` on **level 4**, where they
demonstrably move, and matching the colour that translates rigidly; then check whether that colour is
inside the band rows the key zeroes; then ask whether pressing A5 changes what any arrow subsequently
does on L5 at all.

*The rule this is being held to: an exhaustion proof is only as good as the claim that its key preserves
every mobile object, and "mask keeps signal" proves that SOME signal survives — never that the PIECE
does. The number that made this suspicious was not an error in the output; it was 21 matching another
21 that had no reason to be the same.*

## 2026-08-16 — sp80: a SECOND instrument correction, and the property it reveals (agent, `sp80_s6/s7.py`)

**The 15 `transfer_no_match` anomalies were not a third mechanism. They were fallout from a bug in the
search's own transition function**, found by reading the code rather than by chasing examples:

> `sp80_s5.py`'s plain-action loop treated **FIRE (action 5) as pure movement**, always relabelling the
> *current* driver's position — on a game whose own recorded model says **FIRE can TRANSFER control**
> (return-to-driven from a block, or grab block2 inside castle0's zone).

So every real FIRE-transfer silently corrupted the tracked state **and flagged nothing**. Fixed to
resolve exactly like CLICK — match the post-action colour-9 position against all four stored positions
— and re-running gives **0 no_match anomalies in 5,124 expansions / 17,249 states**.

⚠️ **Blast radius: the previous round's headline (25,644 states, frontier 17,723, no win) was computed
with this bug in place.** It is not superseded in the ordinary sense — it was measuring a **different
transition function**. Nobody should quote it.

**That is the second instrument correction on sp80 in two rounds** (the first being the offset key that
merged states and reported exhaustion at depth 7 on a level whose win it was standing on), and both
were caught by the agent's own checks rather than by the output looking wrong. Which is the property
worth naming:

> **On this search, every wrong version still runs to completion and still reports a number.** A merged
> key reports EXHAUSTED. A corrupted transition reports states and a frontier. Neither errors, neither
> stalls, neither produces a shape a reader would question. The only things that have ever caught them
> are a positive control on a win already possessed, and reading the transition code against the game's
> own documented model.

**The multi_match fork is real, and small.** Running the corrected search twice for 200s with opposite
tie-breaks: run A (prefer current driver) 30 multi_match events, 24 resolved by keeping current; run B
(prefer other) 34 events, 0 kept current. Comparing reachable physical configurations with the driver
label stripped: **3,704 states in common, 12 only in A, 1 only in B** — a ~0.35% fork, so the caveat
does **not** dissolve. Honest qualifier from the agent: neither run exhausted, so part of that gap may
be BFS-order or budget noise rather than true divergence.

The long convergence run is being collected. The deciding instrument remains the growth curve, and it
must be read **from the corrected run only** — the FIRE fix changes the transition function, so
anything measured before it belongs to a different search.

### sp80 L3 growth curve, from the FIRE-corrected run (2026-08-16, `sp80_s8.py`, partial)

| expanded | states | frontier | d_states/2000 | d_frontier/2000 | anomalies | t(s) |
|---|---|---|---|---|---|---|
| 2,000 | 7,355 | 5,355 | 7,354 | 5,354 | 28 | 154 |
| 4,000 | 13,518 | 9,518 | 6,163 | 4,163 | 102 | 310 |
| 6,000 | 19,710 | 13,710 | 6,192 | 4,192 | 178 | 471 |
| 8,000 | 25,829 | 17,829 | 6,119 | 4,119 | 206 | 629 |
| 10,000 | 31,580 | 21,580 | 5,751 | 3,751 | 249 | 789 |
| 12,000 | 36,788 | 24,788 | 5,208 | 3,208 | 306 | 954 |

`d_frontier/2000` changes by −1191, +29, −73, −368, −543 over successive windows: **declining, and
accelerating.** That is emphatically **not** the flat, straight-line signature that would mean the key
still omits state — the shape that killed two earlier searches on this game and both searches on ar25
level 5 today. **The key is sound; the space is merely large**, and saying so is itself a result after
two rounds that diagnosed the opposite.

Extrapolated forward from the table at ~12.6 nodes/s with the decline continuing at roughly 500 per
window: the frontier **peaks near 36,700 at ~26,000 expanded** and falls from there. The 3,000s budget
reaches roughly **38,000 expanded with a frontier still around 27,000** — so **the run will not
exhaust**, and its ending must be reported as a curve plus an extrapolation rather than as a null.

*A converging curve turns "we searched and found nothing" into "here is the node count at which this
becomes a proof, and here is what it costs in wall-clock" — which is a decision a future session can
actually make, rather than a number it has to re-derive.*

## 2026-08-16 — the deepcopy frontier is a MEMORY wall, and it is repo-wide (main thread)

The sp80 convergence run reported **6.3 GB RSS at 12,000 nodes expanded**, holding `deepcopy(env)`
objects in its frontier. Its own growth curve projects a frontier peak near **36,700** at ~26,000
expanded — roughly three times the current size, so **on the order of 20 GB**, on a 32 GB box that was
also running a second agent's searches and the user's session.

That run does not finish. It dies partway, having produced nothing beyond the checkpoints already
collected, and it can swap the machine on the way there. Killed; the box came back clean (largest
python process 0.08 GB, **14.6 GB free of 31.8 GB**).

**The constraint is structural, not incidental to this run.** `copy.deepcopy(env)` is legal, faithful
and ~3 ms — which is why this campaign uses it everywhere — but that measurement is about
**expansion**, and it has been silently generalised into **storage**. `bfs_solve.py` and every ad-hoc
search probe in the repo hold env objects in their frontier.

Two fixes, both cheap to implement and neither free:
- **Frontier of ACTION PATHS**, rebuilding the env by replay when a node is popped. Memory becomes
  trivial. At depth ~20 replay costs ~60 ms against ~3 ms — a **~20x slowdown that must be priced into
  any wall-clock estimate**, not waved away.
- **Layer-by-layer BFS**: keep envs only for the layer being expanded, emit the next layer as paths,
  rebuild once per layer. Memory bounds to one layer, and each node is replayed once rather than once
  per pop.

Added to `CLAUDE.md`'s traps list, because the next search written here will otherwise inherit the
same shape.

*The general form: a per-node cost measured once ("deepcopy is 3 ms, therefore deepcopy nodes are
cheap") is a claim about TIME, and a search's frontier is a claim about SPACE. The first measurement
does not license the second, and the failure it hides does not look like a slow run — it looks like a
run that vanishes.*

## 2026-08-16 — ar25 L5: the 21-state proof is RETRACTED, and the reason generalises (agent, `ar25_t2/t3.py`)

**The hold was right.** `ar25_t1.py`'s "EXHAUSTED at 21 states, 0 divergence, no win" is withdrawn by
its own author, and the root cause is the most transferable finding of the session.

**What the key could not see: a BOARD-INVISIBLE SELECTION STATE with a period-3 cycle in the raw A5
press count.** Measured at two band phases with two different arrow verbs:

| `n mod 3` (A5 presses) | what the arrows do |
|---|---|
| 0 | move the **band**; the piece is held |
| 1 | **nothing moves** — inert (and this phase looked "unselected" to the old key) |
| 2 | move the **PIECE** by 3px (rows for 1/2, columns for 3/4); the band is held |

Selection survives an intervening non-A5 action (`A5, A5, action3, action1` still moves the piece), so
it is history, not board state — **nothing on the board says which phase you are in, so no
board-derived key could ever have represented it.**

**And the piece was identified properly rather than guessed**: driving `mirror.py`'s `L4_LINE` on
**level 4**, where pieces demonstrably move, a colour-5 component of 48 cells translates rigidly by
3px. At the L5 entry colour 5 splits into a 63-cell row-63 HUD line and an **88-cell blob at rows
36-50, cols 42-56** — the piece. It becomes selectable exactly at `sel_phase == 2`, which lines up with
the standing fact **A5x2 = click(S)**, so **colour 5 = S**. W was not found as a separate movable
object; the best-supported hypothesis is that **W is the band itself** (driven by default at
`sel_phase == 0`), whose 1-D phase range is exactly **21** — matching the 21 in "441 = 21x21" — but the
second axis was not found, and this is flagged as a hypothesis, not a finding.

### ⚠️ Why the divergence check read zero, and this is the part worth carrying to every search

> **The `seen`-set collision dropped the node BEFORE its successors were ever computed, so the
> divergence counter never got the chance to fire.**

A divergence check that sits **downstream of a dedup** cannot detect a key that merges states, because
the merge happens first. **Zero divergence under a merging key is not evidence of soundness — it is
the merge working.** Every other control passed too: deepcopy fidelity, death-reverts, mask-keeps-
signal, and 21 keys against 80 raw boards (so the mask was demonstrably not over-collapsing). *A full
set of green controls, and the one thing none of them could see was the thing that was wrong.*

The identical shape hit **sp80 the same day** under a completely different key — an offset re-key that
merged states and reported exhaustion at depth 7 on a level whose win it was standing on. Two games,
two keys, one failure mode: **a search cannot audit a state function from inside itself.** What caught
it in both cases was external: on sp80 a positive control on a win already possessed; here a
main-thread challenge to a number (21) that matched another 21 with no reason to.

**The corrected key** — board with colour-0 dashes undone and colour-10 wall undone (deliberately NOT
row-windowed, since a windowed mask could erase the piece whenever it sat in the band's rows), HUD row
and column zeroed, plus `band_phase` **and `sel_phase`** carried through the BFS like depth (+1 mod 3
iff the action is 5) — is validated by the two assertions that matter: `selected-then-action1` key
**!=** `unselected-action1` key (the exact case the old key got wrong), and `A5x3-then-action1` key
**==** `unselected-action1` key (the phase wraps).

Re-run under it: **5,396 nodes, 6,712 distinct keys against 18,022 raw boards, frontier 1,316, 0
divergence, no win, NOT exhausted** — budget-bound at 540s, not stuck. **A frontier of 1,316 is close**,
and finishing it is the next step.

## 2026-08-16 — sp80 L3: converging, priced, and handed over (agent, `sp80_s6..s9.py`)

The round asked for a decision rather than a result, and produced one.

- **The path-only frontier was cross-validated, not assumed**: `sp80_s9.py`'s states and frontier at
  expanded 2,000 / 4,000 / 6,000 are **byte-identical** to the env-frontier run's (7,355/5,355 ·
  13,518/9,518 · 19,710/13,710). Changing how nodes are stored changed nothing about which are visited.
- **The replay cost is far below the worst case**: **11.31 nodes/s** against ~12.6-12.8 with envs —
  a **10-12% slowdown, not 20x** — because replay is O(depth) and `MAX_DEPTH=40` bounds it near
  120-160ms/node. Memory stays trivial by construction (a `seq`+`pos` tuple against a ~500KB deepcopy).
- **The curve, corrected-transition only** (the pre-FIRE-fix curve is void): `d_frontier/2000` running
  5354 → 4163 → 4192 → 4119 → 3751 → 3208, successive changes −1191, +29, −73, −368, −543. **Declining
  and accelerating.**
- **Priced**: peak frontier **30,000-37,000** around expanded **20,000-26,000**, total exhaustion on
  the order of **40,000-55,000 expanded nodes ≈ 1-1.7 hours** of continuous, memory-safe background
  compute. Explicitly an order-of-magnitude estimate off six curve points with a noisy second
  derivative.
- Named as missing: **checkpointing** — `sp80_s9.py` restarts from the L3 root each call, so a long run
  should save the frontier and `seen` set between invocations rather than re-deriving the first 12,000
  nodes.

**Launched from the main thread** as `sp80_s10.py` (the same file with `TIME_BUDGET_S` 540 → 7200), in
the background, where it survives across turns — unlike an agent's own background job, which dies with
the agent.

### ar25 L5, chained under the corrected key — and a stop condition I got wrong (2026-08-16, `ar25_t4.py`)

| run | nodes expanded (cum.) | distinct keys (cum.) | frontier | elapsed |
|---|---|---|---|---|
| 1 | 4,614 | 5,720 | 1,106 | 500.1s |
| 2 | 8,885 | 11,215 | 2,330 | 500.0s |

Divergence **0** across both, deaths 0, raw boards 53,311 at the 8,885-node mark — **11,215 keys against
53,311 raw, a 4.75x collapse**, and both `sel_phase` assertions re-asserted and printed at the top of
every invocation rather than cited from the file that first proved them. The frontier is path-based and
checkpointed, never an env object, per the 6.3 GB lesson from sp80 the same day.

**I told the agent to stop if the frontier turned and climbed. That rule was wrong here, and it cost
the run.** A climbing frontier is a valid end-of-search signal only *near* the end: in a BFS over a
finite graph, distinct keys grow near-linearly and the frontier keeps widening until the exploration
passes the largest shell — the new-keys-per-node ratio falls only as the search begins re-finding old
states, i.e. near saturation. At **11,215 keys against the model's own ~18,000** (289 piece positions x
21 band phases x 3 sel phases) the search is around **62% explored**, and a ratio of 1.24 → 1.29 is
exactly what 62% looks like. It would be alarming at 95%.

Resumed with a stop rule that can actually distinguish the two cases:
1. **exhausted** — frontier 0 (the proof);
2. **model refuted** — keys pass ~36,000 (2x predicted) with the ratio still >= ~1.2, which would mean a
   second independently-movable object exists and the model is missing it;
3. **budget** — four more chained blocks, then report the curve priced in nodes and wall-clock.

*The general form: a termination heuristic borrowed from the END of a process is not valid at its
MIDDLE, and the tell is that it fires while every soundness check is still green. I read "frontier
climbing" as a symptom when it was a phase.*

If condition 2 fires the next question is already framed. The game's own mechanic is *the player and a
MIRROR sprite move in lockstep, vertical the same and horizontal opposite* — so there should be **two**
sprites, and only one 88-cell colour-5 blob has been found. Either the mirror is derived from the piece
(no extra state) or it is independently drivable (a great deal of extra state), and a space twice the
predicted size is exactly what the second would look like.

## 2026-08-16 — sp80 L3: the 2h run finished, and it REFUTES the exhaustion estimate (main thread, `sp80_s10.py`)

Ran `sp80_s9.py` with `TIME_BUDGET_S` 540 → 7200 from the main thread, where a background job survives
across turns. Completed cleanly, exit 0.

| | |
|---|---|
| expanded | **72,684** |
| elapsed | 7,200s at **10.09 nodes/s** |
| states visited | **192,247** |
| frontier | **118,643** |
| replay cost | 1,403s = **19.5%** of wall-clock |
| exhausted | **False** |
| win | none |

**The priced estimate was wrong, and by a lot.** The previous round extrapolated exhaustion at
**40,000-55,000 expanded nodes ≈ 1-1.7 hours** from six curve points, explicitly labelled an
order-of-magnitude figure. At **72,684 expanded the frontier is still growing** — 118,643 and climbing
by ~2,683 per 2,000 nodes.

Re-derived from the tail of the real curve: new-states-per-node runs 2.585 → 2.595 → 2.450 → 2.388 →
**2.341**, declining roughly 0.06 per 2,000-node window. **The frontier stops growing when that ratio
reaches 1.0**, which at the observed rate is ~45 more windows ≈ **90,000 more expanded nodes**, and the
frontier peaks far above 118,643 before it drains. A realistic total is **on the order of 300,000-500,000
expanded nodes ≈ 8-14 hours** of continuous compute, not one to two.

*The lesson is about the extrapolation, not the agent that made it: six points with a visibly noisy
second derivative supported a factor-of-ten error, and the estimate was labelled as such and believed
anyway — by me, when I sized a 2-hour run from it. **A range quoted with its own caveat still gets
spent as if it were the midpoint.** The honest form is to size the run from the pessimistic end, or to
run until the ratio itself crosses a threshold rather than until a predicted node count.*

**Anomalies at scale:** `transfer_no_match` **0** (the FIRE fix holds across 72k expansions — that is a
strong confirmation), `driver_blob_count` **0**, and `transfer_multi_match` **3,730** — of which
**2,254 had the driver id NOT among the matches**. That is the majority, so the tie-break heuristic is
now load-bearing at a scale where the earlier 12-vs-1 fork measurement no longer bounds its effect.
Any future run needs that resolved before its null means anything.

Fire coverage by driver identity, tabulated: **all four ids reached and fired from** — 18,390 / 19,493
/ 14,890 / 19,353. So "a specific body must fire last" stays refuted at this much larger scale.

**Priced honestly for a future session**: exhaustion is an overnight job, not an afternoon one, and it
needs checkpointing first (`sp80_s9/s10.py` restart from the L3 root each invocation) plus a decision
on the multi_match tie-break. Whether that is worth an overnight run against the other open levers is
a judgement call, not an obvious yes.

## 2026-08-16 — operational: the weekly agent limit was reached

The last agent (ar25 L5, chained BFS) terminated on `You've hit your weekly limit · resets 9pm
(Asia/Bangkok)`. No further subagents this session. Its work is not lost — `ar25_t4.py` checkpoints a
**path-based** frontier and has a `--report` mode that reproduces the curve from the checkpoint alone,
so a future session resumes rather than re-derives. State at the cut: **8,885 expanded, 11,215 distinct
keys, frontier 2,330, divergence 0**, against a model predicting ~18,000 states — roughly 62% explored,
with the corrected key that represents `sel_phase`.

## 2026-08-16 — delegating the probe-writing to codex: what worked, what the lane cannot do

Claude's weekly agent limit was reached, so the fan-out moved to `codex exec` (ChatGPT subscription,
zero Claude tokens). Three constraints were found by probing rather than assuming, and they decide the
shape of every future codex round on this repo.

**1. `codexReady()` → ok. Transport works: cwd resolves to `/mnt/c/Users/.../arc-agi-3-agent`.**

**2. ⚠️ codex CANNOT RUN ANYTHING in this repo.** A smoke test asking it to run
`./.venv/Scripts/python.exe -c "import sys; print(sys.version)"` returned
`WSL ERROR: UtilBindVsockAnyPort:309: socket failed 1` — codex lives in WSL and the repo's venv is a
**Windows** executable, unreachable across the interop boundary. So codex is a **writer only** here.
That is the skill's own "a delegate that cannot run its tests writes tests that were never run",
arriving as a hard platform fact rather than a discipline.

**3. The forbidden-directory audit came back CLEAN, and was worth running.** The rollout log
(`~/.codex/sessions/…/rollout-*.jsonl` inside WSL) showed 4 mentions of `environment_files`: two are my
own prohibition text echoed in the prompt, one is codex stating it will not inspect it, and the tool
calls contain a single `exec`. No read. *The sandbox bounds writes, never reads — so this audit is the
only thing standing between a delegated run and a poisoned result, and it has to be run every time.*

**Two wrapper failures, both instructive:**
- **`codex-run.js` is not safe to run in parallel.** Two simultaneous invocations collided on a fixed
  worktree name: `fatal: Unable to create '.git/worktrees/wt/index.lock': File exists`. The skill
  recommends process-level parallelism as the default fan-out shape; this wrapper needs a unique
  worktree name per run before that is available.
- **`TOKEN_CAP` at 61,514 > 60,000 — and the file was written anyway.** `ka59_x1.py`, 9,324 bytes, was
  sitting in the worktree. Exactly as the skill warns: the cap bites at the END, during self-review,
  after the useful work is on disk. **Check the worktree before reading a non-`OK` status as nothing.**

### The delegated probe: geometry verified, verdict VOID

`ka59_x1.py` was well-shaped — a positive control, geometry derived from the board rather than
hard-coded, an explicit nine-phase closure, a plain final verdict. It failed once on a runtime fact
codex could not have known (`ferry.act()` returns a **tuple** for an aimed click, not an int — and
clicks are ka59's whole mechanic, so it fired on the first round), which I fixed in the main thread.

Then it ran, and **its geometry half is independently correct** — it re-derived, from the board alone,
the same figures I had measured in the main thread hours earlier: **moat = full-height columns
(21, 29)**, **internal band = full-width rows (24, 29)**, **box1 interior bbox (9,11)-(9,14)**.

**And its verdict is void, refuted by its own printed intermediate.** It reported *all nine phases
reach box1*, which would demolish premise 1 outright — but two lines above, it printed
`piece anchor/size: (37, 55) / (1, 1)`. **A 1x1 piece.** Its `piece_shape` looks for colour 0, and a
census confirms colour **0 has exactly one cell on the whole board**. It was flood-filling a point,
which naturally reaches everything, so "YES" nine times is a property of the reader and not of the
game. (The census also confirms **colour 5 is the three DOTS at sizes 4, 2, 2** — matching the agent
table's 2x2, 1x2, 2x1 exactly — so the piece is neither.)

**The correct next step is to use `ferry.py`'s own piece reader rather than guessing a colour**, which
is what every campaign probe that worked has done.

*The loop functioned exactly as designed: the delegate's LOCATIONS were findings and its CONCLUSION was
a hypothesis, and the hypothesis died on a number the delegate itself printed. Worth noting how nearly
it survived — the verdict was clean, confident, formatted as asked, and would have retracted a
five-premise structural argument. What killed it was reading the two lines above the answer.*

## 2026-08-16 — ka59 premise 1: CONFIRMED, and upgraded from "we looked" to a structural fact (`ka59_x2.py`)

The level-2 closure named premise 1 as the most attackable of its five. It is now the most solid.

**The walk graph on ka59 level 2 partitions into 27 connected components, and every component is
PHASE-PURE** — each holds exactly one `(x mod 3, y mod 3)` class. That is the phase law appearing as
graph structure rather than as an observation about particular flood fills.

| landmark | position | component | phase |
|---|---|---|---|
| the piece | (37, 55) | **22** | (1, 1) |
| box2 (the piece's own station) | centre (52, 52) | **22** | (1, 1) |
| box1 | centre (10, 11) | 8 | **(1, 2)** |
| box3 | centre (56, 40) | 25 | (2, 1) |
| box0 | centre (8, 44) | 17 | — |

So from the start the piece can walk to **box2 and nothing else**; every other box needs a click.

**Premise 1 no longer rests on two flood fills that did not happen to find a way in.** box1's centre is
at (10, 11), and 10 mod 3 = 1, 11 mod 3 = 2 — so its component is phase **(1,2)** by construction, and
because components are phase-pure, a cell of phase (1,2) is reachable **only** from phase (1,2). The
premise is structural.

**A sharper fact than the closure had**: **box3 is on the SAME side of both barriers as the piece**
(x=56 and x=37, both right of the moat at columns 21-29) **and is still unreachable** — component 25,
phase (2,1), against the piece's 22, phase (1,1). *Phase alone separates them, with no barrier
involved.* The moat and the internal band are not the only things partitioning this board; the lattice
is.

Both barriers re-derived here as controls: **moat = full-height non-background columns 21-29** and
**internal band = full-width non-background rows 24-29** — matching the main-thread measurement from
earlier today exactly.

### Two errors on the way, and the second is mine

- **The delegate's probe (`ka59_x1.py`) unioned the closures of EVERY walkable cell of a phase** and
  then asked whether box1 was in the union. Cells *inside box1* are themselves walkable cells of some
  phase, so the test was circular — box1 is reachable from box1 — and it answered YES nine times out of
  nine. The union also hides disconnection: a phase that splits into three components still unions to
  its own seed count, which is exactly the `closure == seeds` line its output showed for all nine.
- **My first diagnosis of that was wrong too.** It printed `piece anchor/size: (37,55) / (1,1)` and a
  census shows colour 0 holds exactly one cell, so I called it a 1x1-piece bug. But `ferry.py`'s own
  `find_cell()` defines the piece as *"one cell, or a tight cluster"* — a single-cell piece is this
  game's real shape. The bug was the union, not the reader.
- **And my own probe failed its own control first**: `C2 piece start in walkable set: FAIL`, because
  the piece's cell reads as non-background — it *is* the piece. A model that cannot place the piece
  where it demonstrably stands is wrong, and the control is the only reason that surfaced before the
  verdict did. Fixed by adding the piece's cell (and the dots' cells, which become ground once a swap
  moves them) to the walkable set.

*Three wrong answers in one probe chain, each caught by something printed above the verdict rather than
by the verdict looking wrong. The delegate's circular union, my misdiagnosis of it, and my own model's
missing cell — none of them errored, all three produced a clean confident result.*

## 2026-08-16 — ka59 level 2, as ONE map (`ka59_x3.py`)

With the phase-pure component partition from `ka59_x2.py`, the whole level reduces to a reachability
table with no search in it. Computed from the board alone, all four controls passing (both barriers
re-derived and non-empty; the piece's own cell walkable; 27 components; **every component phase-pure**):

| region | components | contains |
|---|---|---|
| RIGHT | 18-26 (all nine phases) | **the piece starts here (22, phase (1,1))** · box3 · box2 |
| LEFT-TOP | 0, 1, 2, 6, 7, 8, 12, 13, 14 | **box1** |
| LEFT-BOTTOM | 3, 4, 5, 9, 10, 11, 15, 16, 17 | **box0** |

Each box interior spans **all nine phases** of its own region (box1 18 cells, box3 18, box0 36, box2 9),
so standing in a box is a question about REGION, not about phase.

**Without kicks the piece cannot leave the right region at all** — the generous union over every
component any dot's cells touch is exactly `[18..26]`. So box3 and box2 are fillable and **box1 and
box0 are not**. That matches every measured result on this level and explains why the kick is a
required mechanic rather than a shortcut.

**And the gap this file declared in its own docstring is closed by its own numbers.** dot0 was measured
kicked (34,44) → (19,44): `34 mod 3 == 19 mod 3 == 1`, so the flight **preserves phase and changes
component**, carrying the dot from the right region into the left. That is the kick's entire function
here — it is the only operation in the game that moves anything between regions.

### The win line, as a skeleton the map forces

A box is filled by standing **inside** it and clicking any dot: the dot lands on the piece's old cell
(inside the box) and the piece teleports to where the dot was. **Clicks have no proximity requirement**,
so the dot may be anywhere. Three dots, one click each, three boxes to fill, and the piece must finish
in box2 (whose interior matches the piece — the fourth size-match).

1. stand in **box3** (right region, reachable by walking) → click a dot **pre-kicked into the
   left-bottom region** → box3 filled, piece crosses to that dot's position;
2. walk into **box0** → click a dot **pre-kicked into the left-top region** → box0 filled, piece crosses;
3. walk into **box1** → click the **third dot, still in the RIGHT region** → box1 filled, and the piece
   teleports back across to the right;
4. walk to **box2** and stop.

Every kick happens first, while the piece is still on the right and everything is reachable.

**What is left to compute is one table**: for each dot, the set of components it can be KICKED into
(slide-until-blocked, phase preserved). The skeleton above is satisfiable iff that table contains a
left-bottom component for one dot and a left-top component for another, with the third left in place.

### Three wrong answers on the way to that map, none of which errored

- **The delegate's probe unioned the closures of every walkable cell of a phase** and asked whether box1
  was in the union — but cells *inside* box1 are themselves such cells, so the test was circular and
  answered YES nine times of nine.
- **My first diagnosis of that was also wrong**: I blamed a 1x1 piece reading, but `ferry.py`'s own
  `find_cell()` defines the piece as *"one cell, or a tight cluster"*, so a single-cell piece is this
  game's real shape. The bug was the union.
- **Then my own probe tested each box's CENTRE**, and a 6x6 interior spans all nine phases — so a
  centre's phase says nothing about whether the box can be entered. Its first verdict ("only box2 is
  ever reachable") was void for that reason, and the corrected run says box3 is reachable too.

*Each of the three produced a clean, confident, correctly-formatted verdict. What caught all three was a
line printed above the answer — the seed count, the piece size, the interior cell count.*

## 2026-08-16 — ka59 L2: an EXECUTABLE win candidate, built entirely from already-measured kicks (`ka59_x4.py`)

Mapping the thirteen previously-measured kick landings onto the component partition closes the map.
Every measured flight preserves phase (`from mod 3 == to mod 3`, checked per row) and several cross
regions:

| dot | regions it has been MEASURED to reach |
|---|---|
| dot0 | LEFT-BOTTOM (box0) · RIGHT |
| **dot1** | LEFT-BOTTOM · **LEFT-TOP (box1)** · RIGHT |
| dot2 | LEFT-BOTTOM · RIGHT |

**dot1 is the only dot measured able to reach LEFT-TOP**, via the chained kick (41,34) → (17,34) →
(17,19), landing in component 13.

### The candidate line — satisfiable with no new search

1. **Pre-kick, all while the piece is still on the right and everything is reachable:** dot1 west then
   chained north → **(17,19), LEFT-TOP**; dot0 west → **(19,44), LEFT-BOTTOM**; leave dot2 in the RIGHT.
2. stand in **box3** (right region, walkable from the start) → click **dot0** → box3 filled, piece
   crosses to (19,44), LEFT-BOTTOM.
3. walk into **box0** → click **dot1** → box0 filled, piece crosses to (17,19), LEFT-TOP.
4. walk into **box1** → click **dot2** (still on the right — **clicks have no proximity requirement**)
   → box1 filled, and the piece is thrown back to the RIGHT.
5. walk into **box2** and stop.

Four targets, three clicks, the piece ending in box2 — whose interior is the fourth size-match, the one
that matches the PIECE.

### Why this contradicts premise 5, and why that may be the point

The size-match pairing is box1↔dot0, box3↔dot1, box0↔dot2. The line above pairs box3←dot0,
box0←dot1, box1←dot2 — the wrong pairing on all three.

**But the matched pairing is not reachable under the measured kicks.** It would require the piece to
arrive in LEFT-TOP by clicking **dot2** (since box1 must be filled by dot0, the click that lands the
piece in box1's region has to be a different dot), and **dot2 has never been measured reaching
LEFT-TOP**. Only dot1 has.

So exactly one of these is true, and both are testable:
- **the pairing is required** → then the open question is whether **dot0 or dot2 can chain a second
  kick north** from their LEFT-BOTTOM landing, which is the untested item an earlier round flagged in
  its own "what I did not cover" (only dot1's chain was ever tried);
- **the pairing is not required** → then the line above wins, and the reason `r20` failed with all
  three boxes filled is not the pairing at all: **`r20` left the piece at (44,48)**, not in box2. *No
  experiment on this level has ever controlled the fill set and the piece's final position at the same
  time* — r20 controlled the fills and not the ending; r22 controlled the pairing and left box1 empty.

Either way ka59 level 2 is now **one drive** from an answer rather than one insight, and the drive
reuses machinery that already exists (`bfs_route` from the earlier rounds routes on the 3-lattice, and
the kick approach geometry for both required kicks is recorded).

*The reduction came from refusing three clean verdicts in a row — a delegate's circular union, my own
misdiagnosis of it, and my own centre-instead-of-interior test — and each time the refutation was a
number printed above the answer rather than anything wrong with the answer's shape.*

## 2026-08-16 — ar25 L5: the position model is REFUTED by a factor of two (agent, `ar25_t4.py`, 7 chained runs)

Seven chained 500s runs on the checkpointed, path-based, `sel_phase`-aware search:

| run | expanded | distinct keys | frontier | Δkeys | ratio |
|---|---|---|---|---|---|
| 1 | 4,614 | 5,720 | 1,106 | 5,719 | 1.24 |
| 2 | 8,885 | 11,215 | 2,330 | 5,495 | 1.29 |
| 3 | 13,004 | 16,319 | 3,315 | 5,104 | 1.24 |
| 4 | 17,067 | 21,337 | 4,270 | 5,018 | 1.24 |
| 5 | 20,383 | 25,241 | 4,858 | 3,904 | 1.18 |
| 6 | 24,000 | 29,536 | 5,536 | 4,295 | 1.19 |
| 7 | 28,627 | **34,909** | 6,282 | 5,373 | 1.16 |

Rate stable at 8-9 nodes/s. **Frontier grew every single run** (+1,224, +985, +955, +588, +678, +746) —
a BFS past its widest shell shows the frontier *shrinking*, and that has not started in seven runs.
**Divergence 0 and deaths 0 across all 28,627 expansions**, with C1 (deepcopy fidelity), C2
(death-reverts, 321-cell positive control) and both `sel_phase` identities re-verified fresh at the top
of every process. That discipline is what makes the number below mean something.

**34,909 distinct keys against a model predicting 18,207** (289 piece positions x 21 band phases x 3
sel phases) — **1.94x, and still climbing.** The position model is refuted.

⚠️ **And the gate I wrote would not have fired**, which is the second stop rule I have gotten wrong on
this game in two rounds. I set `MODEL_REFUTED` as "keys past ~36,000 **and** ratio still >= 1.2". The
ratio clause was meant to separate *"the space is bigger than modelled"* from *"we are approaching
saturation"* — but by run 7 the thing it gated on had already happened, and the clause was pure
arithmetic standing in front of it (ratio 1.16, keys 1,091 short of a threshold I picked by eye).
*A compound gate fires on its weakest clause, so every extra condition is a new way for a true verdict
to be withheld — and the one that withholds it will look like diligence.*

**What the missing state most likely is.** The game's own mechanic is *the player and a MIRROR sprite
move in lockstep — vertical the same, horizontal opposite*. Only **one** movable object has ever been
found on level 5 (the 88-cell colour-5 blob at rows 36-50, cols 42-56). A mirror strictly derived from
the piece adds no state and the model would fit; it does not fit. The natural reading is that **the
mirror is a second independently-positioned object whose lockstep BREAKS** — most obviously when one of
the pair is blocked by a wall and the other is not — after which the state is a PAIR of coordinates and
the space is roughly (piece x mirror x band phase x sel phase), which is millions and **not
BFS-exhaustible at all**.

Being tested now, and it needs no search: locate both objects by driving `L4_LINE` on level 4 and
watching for two components translating together (one matching the piece's displacement, one opposite
in x and equal in y), then try to decouple them against a wall and read whether their offset ever
changes.

Operational note: the checkpoint is **690 MB** and growing linearly with keys. The BFS is not being
resumed while the mirror question is open.

## 2026-08-16 — ka59 L2: the candidate line RAN, and failed at the step that reconfirms premise 2 (agent, `ka59_y1.py`)

The map's win candidate was driven for real. It reached **2 of 4 targets in 39 of the ~127-action
clock** and then failed, at exactly the place the premises predict — which makes it a confirmation
rather than a dead end.

| step | action# | piece | phase | result |
|---|---|---|---|---|
| L2 entry | 11 | (37,55) | (1,1) | dots at (34,44) (41,34) (44,47) |
| kick dot0 west | 15 | (37,46) | (1,1) | dot0 → **(19,44)** |
| kick dot1 west | 25 | (46,34) | (1,1) | dot1 → **(17,34)** |
| enter box3 | 30 | (55,40) | (1,1) | |
| **click dot0** | 31 | **(19,44)** | **(1,2)** | **box3 FILLED**, piece crossed |
| chain-kick dot1 north | 34 | (19,38) | (1,2) | dot1 → **(17,19)** |
| enter box0 | 38 | (10,42) | (1,0) | |
| **click dot1** | 39 | **(18,19)** | **(0,1)** | **box0 FILLED**, only dot2 left |
| route to box1 | — | **NO ROUTE** at 3,000 nodes | — | box1 needs phase (1,2) |

`levels_completed` stayed at 1 through every click; no `GameState.WIN`. **No compound-sweep side
effects on any of the three kicks** — each moved exactly its target.

**Why it failed, and it is premise 2 verbatim**: clicking dot1 lands the piece at dot1's canonical
cell, **(18,19), phase (0,1)** — not at the dot's own (17,19). box1 needs (1,2). *The assignment was
mine and it was wrong: I had dot1 carrying the piece into box1's region, and dot1 cannot deliver that
phase.* Only **dot0** has (1,2).

**The agent also corrected the line's ORDER before it could run at all, and that correction is
load-bearing**: the chain-kick's approach cell sits *past the moat*, and the region map says the piece
cannot walk to any x<21 cell without a prior crossing. **So the crossing must come before the chain**,
not before the crossing. My step 1 had asked for both kicks up front, which is not physically
realisable.

### The corrected line — dot0 CARRIES, it is never the cargo

`r19` had already measured that **dot0's chain reaches phase (1,2) cleanly**. Combined with the above,
the assignment writes itself:

1. on the right: kick **dot0** west → (19,44); kick **dot1** west → (17,34); leave **dot2** in the RIGHT;
2. box3 → click **dot1** → box3 filled, piece crosses to LEFT-BOTTOM;
3. *now on the left*, chain-kick **dot0** north → **(19,20)/(19,21)**, phase **(1,2)**;
4. box0 → click **dot0** → box0 filled, piece crosses to (19,20), phase (1,2);
5. box1 → click **dot2** (still on the right — proximity is irrelevant) → box1 filled, piece thrown back RIGHT;
6. walk into **box2** and stop.

Four targets, three clicks, ending in box2, every landing already measured. Being driven now.

**Both outcomes are decisive**, which is the point of running it:
- **wins** → the size-match pairing was never required (this line violates it on all three), and the
  earlier all-three-filled run failed because **it left the piece at (44,48)** instead of box2;
- **loses with all four satisfied and the piece in box2** → the pairing IS required, and then the
  deadlock is **formal**: box1's only phase-(1,2) access is dot0, and dot0 would have to be both the
  vehicle and the cargo. That closes the level by proof rather than by exhaustion.

## 2026-08-16 — ar25 L5: MIRROR NOT FOUND, and the 1.94x blowup is unexplained again (agent, throwaway probe)

The mirror hypothesis is retired by measurement rather than left hanging.

- **Colour-4 is absent from level 5 entirely.** `mirror.py`'s `signature()` ties colour-4 (45 cells) to
  the reset frame; at level-4 entry it is present as two 9-cell blocks, and through `L4_LINE` it
  fluctuates 9 → 63 → 9 → 27 → 45 → 54 → 63 purely as a function of the wall's row — never a sustained
  one-directional displacement paired with a piston. **At level-5 entry its census is empty.**
- **Level 4, where pistons demonstrably move, shows no lockstep companion either** — only the selected
  piston (colour 5) shows a sustained matched displacement per press.
- **Level-5 entry census**: one `c5, n=88, bbox=(36,50)-(42,56)` (the known piece), one static
  `c11, n=189` (a target/marker, centroid stationary throughout), some small `c11`/floor regions.
  Nothing sized or shaped like a second mover.
- **Directional probe at `sel_phase=2`**: A1 → c5 only, d=(-3,0); A2 → c5 only, (+3,0); A3 → c5 only,
  (0,-3); A4 → c5 only, (0,+3); **A7 → nothing moves.**
- **The decisive test — a 30-press decoupling walk.** A3 pressed 30 times from the selected state.
  Presses 0-13: the piece's x-centroid walks 47.9 → 8.9, exactly **-3.0 per press, 14 straight**, and
  **no other component ever shows a matched displacement** (the `c11`/`c9` wobbles mid-walk are the
  piece's own 88-cell body occluding the static target and floor, never tracking its vector). Press 13
  → 14: the centroid stops — a hard stop. **Presses 14-29: `changed=[]` on every one; the frame is
  byte-identical, press after press.**

**There is no lockstep to break because there is no second body.** The piece was held against a wall
for sixteen confirmed-dead presses and nothing appeared, tracked, lagged or diverged.

⚠️ **So the 1.94x key blowup (34,909 against a model of 289 x 21 x 3 = 18,207) is open again**, and it
is now the only thing between this search and either a proof or a decision to abandon BFS here. Three
candidates, and the run to separate them is arithmetic rather than discovery — instrument a few
thousand nodes to record the **piece centroid**, the **band phase** and the **sel_phase** per node, then
compare `len(distinct) x len(distinct) x len(distinct)` against the distinct-key count:

1. **the piece's reachable positions exceed 289** — the agent's own walk is suggestive, 14 consecutive
   -3 presses is 42 cells of travel on one axis, and the 289 = 17x17 figure came from an old
   click-sweep framing rather than from this action set;
2. **`band_phase` has more than 21 values**;
3. **the key carries something that is not state** — the key's transform undoes colour-0 dashes and the
   colour-10 wall but **never touches colour-9 floor cells**, which were observed fragmenting between
   frames. *Note the tension inside the agent's own data, which is exactly why this needs measuring:
   sixteen byte-identical frames at the wall argue the floor does NOT flicker freely.* Both
   observations are its own; only an instrumented run reconciles them.

If the product matches the key count, the model simply had the wrong factors and exhaustion can be
priced honestly. If the key count far exceeds it, **the key is separating states identical in all three
factors — which would be the FOURTH key on this campaign today to do exactly that**, so it is the
expected answer rather than a surprise, and the next step is to diff two raw boards that share all
three factors and mask whatever differs.

Explicitly held: **do not edit `key_of` on a hypothesis.** A key change invalidates the 690 MB
checkpoint, so it is a one-way door and only gets walked through with the diff in hand.

## 2026-08-16 — ka59 L2: ALL THREE BOXES FILLED, no win — and the fill model is now EXHAUSTED (agent, `ka59_y2.py`)

The corrected line ran and did exactly what it was designed to do, up to the last step.

| step | action# | piece | phase | note |
|---|---|---|---|---|
| L2 entry | 11 | (37,55) | (1,1) | |
| kick dot0 west | 15 | (37,46) | (1,1) | dot0 → (19,44) |
| kick dot1 west | 25 | (46,34) | (1,1) | dot1 → (17,34) |
| enter box3 | 30 | (55,40) | (1,1) | |
| **click dot1** | 31 | (18,34) | (0,1) | **box3 FILLED**, crossed |
| chain-kick dot0 north | 43 | (18,49) | (0,1) | dot0 → **(19,20)** |
| enter box0 | 47 | (8,46) | (2,1) | |
| **click dot0** | 48 | (19,20) | **(1,2)** | **box0 FILLED**, crossed — the predicted phase |
| enter box1 | 53 | (10,14) | (1,2) | **straight route, no search needed** |
| **click dot2** | 54 | (44,48) | (2,0) | **box1 FILLED — all three** |
| route to box2 | — | **NO ROUTE** | box2 needs (1,1) | |

**54 of the ~127 clock. `levels_completed` stayed at 1 through every click. Zero compound-sweep side
effects** — each kick moved exactly its target, re-read after every one.

**The reassignment worked exactly as reasoned**: dot0 carried the piece to phase (1,2) and **box1 opened
immediately, by a straight route, with no search** — after two earlier rounds had called it unreachable.

### And step 6 is a structural wall, deduced rather than searched

> **box2's interior is in component 22, phase (1,1) — the piece's own spawn phase. Walking preserves
> phase. Only a click changes it, and only to that dot's fixed canonical phase: dot0→(1,2),
> dot1→(0,1), dot2→(2,0), measured across a 156-arm sweep with zero exceptions. None of the three is
> (1,1).**

So once three dots are spent — which filling three boxes requires — **no walk can ever return the piece
to box2, under any of the six dot→box assignments.** `r20` corroborates independently: it also ended at
**(44,48)** after using dot2 last. The agent explicitly declined to re-run step 6 at a higher node cap,
correctly, since the argument is deductive from premises already at zero counter-examples.

### The fill model is exhausted, not merely unsolved

| line | outcome |
|---|---|
| box2 visited first + all three boxes filled (unmatched) — `r20` | **no win**, ended (44,48) |
| all three filled (different unmatched assignment), box2 not visited — `y2` | **no win**, ended (44,48) |
| the size-matched pairing | **structurally impossible**: box1 is enterable only at phase (1,2), only dot0 delivers (1,2), box1 must be filled *by* dot0, and dots are one-click-only |

**"Fill the boxes, visit box2" is not the win condition in any arrangement.** That closes a MODEL rather
than a permutation — the same place re86 level 6 reached, and the right moment to stop optimising
inside it.

**The unswept surface is the click.** Every click in this game's history has been aimed at a **dot**,
and the whole model — swap, canonical cell, phase class, one-click-only, the halo↔interior match — is
built from those. One earlier round swept **19 hand-picked cells of 4,096** and found only the known
dot-swap re-firing through its proximity tolerance; that is not a sweep. A real click-then-ACT sweep on
a 3-cell lattice (~450 candidates, respecting the movement lattice) is running, prioritising the
colour-14 halos in full, the box interiors and frames, the moat and the internal band, and **box2
itself** — the one target never filled, whose interior matches the PIECE rather than any dot, and which
now turns out to be unreachable after any complete fill line.

## 2026-08-16 — ka59 L2: the click surface is INERT — a real sweep, and a real negative (agent, `ka59_y3.py`)

**462 cells on a stride-3 lattice** (the movement lattice), click-then-ACT at every candidate, over the
full 64x63 board — every halo in full, all four box interiors and frames, both moat columns, the
internal band, and box2 inside and out. Zero real game actions spent: one reach-L2 sequence, then every
candidate on a throwaway deepcopy of the fixed entry state.

**8 of 462 respond, and all 8 are the same known mechanic.**

| responsive cell | halo of | piece lands at |
|---|---|---|
| (39,33), (42,33) | dot1 | **(42,34)** = dot1's own cell |
| (33,42), (33,45) | dot0 | **(34,44)** = dot0's own cell |
| (42,45), (45,45), (42,48), (45,48) | dot2 | **(44,48)** = dot2's own cell |

Every one lands the piece precisely on **its own dot's canonical cell** — the swap, re-triggered by
clicking the halo rather than the dot. That generalises the earlier one-off `(33,42) → (34,44)`
observation into the halo's full proximity tolerance, and shows it does nothing else anywhere it fires.
The varying per-verb diffs across the three dots are just the piece standing in three different places
afterwards, not a distinct effect.

**Zero response** from the remaining ~35 halo-lattice points, all four box interiors and frames, both
moat columns (x=21, 24, 27), the internal band (y=24, 27 across x=0-21), and **box2 specifically** —
inside, outside and its frame. The one target that matches the PIECE rather than a dot, and that no
complete fill line can end at, is click-inert like every other piece of scenery.

### The one gap left, and it is the shape this campaign has twice been taught to look for

Every one of those 462 clicks was a **first click from the untouched entry frame**. On `ar25`, levels 3
and 4 both fell to precisely this: *a win can depend on a control surface that engaging the puzzle's own
pieces locks you out of, so the ORDER of engagement is part of the solution* — a search that starts by
touching the pieces was exhaustive there (116,640 states on L3) and blind. **And this game has already
produced its own instance today**: box1 was called unreachable twice, then opened by a straight route
with no search once the piece arrived on phase (1,2). Configuration decided reachability, not geometry.

Running now: the same sweep from four **non-entry** configurations — after the two west kicks (the dots
have moved, so their halos have moved); after the first crossing, with the piece on the left where it
can never be at entry; after two boxes are filled (a filled box is a new object nobody has clicked); and
with the piece standing **inside box2**. *A filled box and an emptied dot cell are both board states that
did not exist at entry, and the halo result proves this game keys clicks to REGIONS AROUND OBJECTS — so
moving the objects moves the surface.*

If all four come back with nothing beyond the known dot-swap, ka59 level 2 is **closed by proof**: the
fill model exhausted in every arrangement, the size-matched pairing structurally impossible, and the
click surface inert from entry and from four distinct mid-line states.

## 2026-08-16 — ka59 L2: ⚠️ NEW MECHANIC — a FILLED BOX'S MARKER IS COLOUR 4, and it is still swappable (agent, `ka59_y4/y5.py`)

**The "click surface inert" closure is withdrawn**, and the reason is the campaign's own ar25 lesson
arriving a third time: the 462-cell sweep was rooted at the untouched entry frame, and **a board that
has been played contains objects the entry frame never had.**

Sweeping the same stride-3 lattice from four NON-ENTRY configurations (1,848 candidates, all
click-then-ACT against a per-configuration baseline, zero real actions — every config built by deepcopy
replay of already-measured sequences):

| config | how reached | responsive | new vs. entry sweep |
|---|---|---|---|
| 1. after two west kicks | kick dot0 west, kick dot1 west | 8 | none — the three dot halos, relocated with their dots |
| 2. after first crossing, **box3 filled** | + walk box3, click dot1 | 7 | **(54,39) — box3's own corner** |
| 3. after **box3 + box0 filled** | + chain-kick dot0, walk box0, click dot0 | 7 | **(54,39) persists + (6,45)/(9,45) — box0's corner** |
| 4. piece inside box2, spawn phase, 0 clicks | walk box2 from entry | 8 | none — identical to the entry sweep |

**A box's fill marker renders as colour 4, not colour 5** — which is why every probe in this game's
history missed it: they all scanned `dot_cells` for colour **5**. Clicking near the marker re-fires the
identical SWAP, read by pixel rather than inferred from a diff count:

```
box3 interior before the fill click:  [...,0,...]   (0 = piece standing there)
box3 interior after  the fill click:  [...,4,...]   (4 = the new "filled" marker)

click (54,39) on that filled board:
  piece (18,34) -> (55,40)                    [swapped IN to box3]
  diff: (17,34,0,4) (18,34,0,4) (55,40,4,0)   [piece's old footprint -> 4 ; marker cell -> 0]
```

A control click on a dead cell in the same state moved nothing, so this is not router noise.
**Filling a box is therefore NOT terminal** — the marker inside stays click-manipulable through its own
halo, exactly like an unconsumed dot.

### Two consequences that are bigger than the mechanic, and are being chased now

1. **It threatens every "boxes filled, no win" result already on record.** A route that merely *grazes*
   a filled marker's halo while pathing elsewhere could have **silently un-filled a box**, and **no
   probe has ever tracked colour-4 cells.** This is the same attribution-bug shape already caught once
   today for dots — `bfs_route`'s `avoid` forbids *landing* on a dot's cells but not *passing near*
   them, and a route kicked an unrelated dot mid-pathfind. If `y2` un-filled a box while walking, then
   "all three filled, no win" was never measured and **the fill model is not exhausted at all**.
2. **If an ejected marker can be clicked into a DIFFERENT box**, a wrongly-filled box can be corrected
   without spending a fresh dot — and the resource arithmetic behind the entire deadlock (3 dots, one
   click each, 3 boxes plus a carry) is wrong, because **markers are a fourth resource nobody counted.**
   That would reopen the size-matched pairing, which is currently ruled out only by dot scarcity.

Also being mapped: the marker's tolerance region — `(54,39)` responds and `(57,39)` does not, so it
exists and is unbounded so far, unlike the three dot halos which are now fully characterised.

**The ka59 closure I was about to write is held.** *"Click surface inert" was true of every board I had
asked about, and false of the board the game actually produces after you play it.*

## 2026-08-16 — ar25 L5: FACTORS EXPLAIN THE COUNT — the bbox proxy was wrong, not the key (agent, throwaway instrumented BFS)

The 1.94x blowup is explained, and the way it was explained matters more than the answer.

**First pass — piece position measured as a BOUNDING BOX**, which is what I asked for literally:

| factor | distinct |
|---|---|
| piece bbox | **15** |
| band phase | 19 (`[0,3,...,54]`, still climbing) |
| sel phase | 3 |
| **product** | **855** |
| **distinct keys, same 3,000 nodes** | **3,000** |

3,000 keys against a product of 855 — **every expanded node had a unique key, zero collisions.** That
fires the "the key separates identical states" branch, which would have been the fourth such key on this
campaign in one day. **The agent did not take it.** It found a colliding pair and diffed the raw boards,
and the 91 differing cells split cleanly:

- 4 cells at column 63 plus `0 ↔ 9` swaps — the known HUD-column and colour-0 dash noise, which
  `key_of` **already neutralises** (`k[:,63]=0`, `k[k==0]=9`). Not the explanation.
- **~26 cells at rows 36-40, cols 39-53, all `5 ↔ 9` swaps — the piece's OWN colour.** Two nodes sharing
  one bounding box had genuinely different colour-5 pixel patterns inside it. **The piece can occupy
  more than one internal configuration at a fixed extent.** That is real state a four-number bbox cannot
  see — not something to mask.

**Second pass — the piece's exact pixel footprint**, same run, same `key_of`, only the measurement
changed:

| factor | distinct |
|---|---|
| piece exact footprint | **127** |
| band phase | 19 |
| sel phase | 3 |
| **product** | **7,239** |
| **distinct keys** | **3,000** |

3,000 ≤ 7,239 — the product now bounds the key count from above, which is the healthy relationship (not
every combination is reachable). **The over-separation signal is gone the moment the piece factor stops
being an undercount.**

**The true size, and it lands on the blowup exactly.** The model's 289 was a bbox-shaped guess (17x17,
from an old click-sweep framing). Extrapolating from the real checkpoint's 34,909 keys with band ≈ 21
and sel = 3: **34,909 / 63 ≈ 554 piece positions** — roughly double 289, which *is* the 1.94x that
started this investigation. Self-consistent rather than coincidental.

⚠️ **And that arithmetic says the search is nearly done.** The corrected model is
554 x 21 x 3 ≈ **34,902 total keys**, and the checkpoint **already holds 34,909**. So the reachable state
set is essentially already discovered; the 6,282 frontier entries are nodes not yet *expanded*, whose
keys are already counted. Expanding them should add few or no new keys and the frontier should **drain**.
At 8-9 nodes/s that is about **12 minutes** — one or two chained runs, and a falsifiable prediction
either way. The BFS was resumed on exactly that basis, with the two assumptions stated: that band really
saturates at 21 (the sample saw 19 and was still climbing) and that every (piece, band, sel) triple is
jointly reachable.

*The transferable part: "the key over-separates" and "my proxy for a factor undercounts it" produce the
IDENTICAL symptom — a product far below the key count — and only diffing a colliding pair tells them
apart. Reaching for the mask first would have corrupted a sound key and voided a 690 MB checkpoint, on
evidence that was actually pointing at the measurement.*

## 2026-08-16 — ka59 L2: FILL IS REVERSIBLE, markers RECYCLE, and the deadlock arithmetic is wrong (agent, `ka59_y6/y7/y8.py`)

**Root cause of why this hid for so long: colour 4 is the box FRAMES' colour — 88 permanent cells across
all four boxes, present from level-2 entry.** `CLAUDE.md` already said the placed dot takes "the boxes'
own colour", but no probe had ever subtracted the frame baseline, so every raw colour-4 count was
reading frame pixels. Fixed with `extra4() = colour4_now − colour4_at_L2_entry`, and the three answers
below are all pixel reads under that baseline, not diff-count inference.

**Q1 — FILL IS REVERSIBLE.** Click dot1 from inside box3: cell (55,40) goes colour 1 (floor) → colour 4
(filled). Click the marker's halo at (54,39) and walk away: **(55,40) goes colour 4 → colour 1, back to
floor**, and the ejected marker sits at (17,34)/(18,34) — the piece's old position at the moment of the
second click. The identical swap, run twice on the same object.

**Q2 — `y2`'s fills SURVIVED their own routing.** Replayed y2's exact line with an `extra4` census after
**every one of 37 real actions**: `[]` through action 19, `[(55,40)]` from the box3 fill at action 20
and **unchanged for the next 16 actions**, then `[(8,46),(9,46),(55,40)]` at the box0 fill. Final census
exactly 3 cells, all inside box3's and box0's bboxes, nothing outside. **The attribution-bug risk did
not materialise on that line — y2's "two fills, blocked at box1's phase wall" stands as measured.**
(Only that line is re-certified; `r18`-`r28` are not individually re-walked.)

**Q3 — a recycled marker fills a DIFFERENT box.** Filled box3 with dot2 (never kicked, stays right, no
crossing needed), ejected it via the halo re-click, walked to **box2**, clicked from inside:

```
fill box3 with dot2:       extra4 = [(55,40)]
eject via halo click:      extra4 = [(44,47),(44,48),(45,47),(45,48)]   (dot2's old resting cells)
walk to box2, click there: extra4 = [(52,52)]                          (inside box2's bbox)
```

**So markers are a REUSABLE resource, not a one-time-use dot** — and the arithmetic that ruled out the
size-matched pairing ("3 dots, one click each, 3 boxes plus a carry") assumed each dot buys exactly one
placement. **It is wrong.**

**Q4 — the marker's halo is a plain 3x3 centred on the fill cell** (`{54,55,56} x {39,40,41}` around
(55,40)), identical in shape and size to the raw dot halos. No new geometry; the same proximity rule.

⚠️ **The consumption rule, narrowed precisely rather than conveniently**: a dot clicked onto **open
floor** is consumed (the earlier `r24/r25` result stands — the vacated cell reads plain floor and a
second click does nothing), while a dot placed **into a box** becomes a persistent, recyclable colour-4
object. *Same verb, opposite outcome, gated on where the piece was standing when it clicked.* Both are
now measured; neither generalises to the other.

**The question that now decides the level, and it is being measured next: does a recycled marker's
click still deliver its ORIGIN DOT's canonical phase?** The deadlock was — box1 is enterable only at
phase (1,2); only dot0 delivers (1,2); box1 must be filled *by* dot0 under the size match; a dot is
one-click-only, so dot0 must be both vehicle and cargo. **Recycling breaks the last premise.** If dot0's
marker still delivers (1,2) after being placed and re-ejected, dot0 can be spent as the vehicle and
recovered as the cargo, and the matched pairing reopens. Being tested on **two** different dots, because
"the marker keeps its origin's phase" and "the marker's phase is positional" predict the same thing for
one sample and different things for two.

## 2026-08-16 — ka59 L2: marker phase is POSITIONAL — which closes the recycling escape and opens a better one (agent, `ka59_y9.py`)

**A recycled marker delivers the phase of the CELL IT CURRENTLY OCCUPIES, never its origin dot's.**
Two arms, designed so a coincidence could not pass — box3's fill cell is phase (1,1), which differs
from dot0's canonical (1,2) *and* from dot2's (2,0):

| marker from | created at | its phase | clicked from | piece landed | landing phase |
|---|---|---|---|---|---|
| dot0 | (55,40) | **(1,1)** | (34,44), phase (1,2) | (55,40) | **(1,1)** |
| dot2 | (55,40) | **(1,1)** | (44,48), phase (2,0) | (55,40) | **(1,1)** |

So the swap carries **no identity tag under the position** — click an object, the piece goes wherever
that object currently sits. Placing dot0 into a box and ejecting it does *not* preserve a reusable
"(1,2) delivery"; the ejected marker's phase is set by where it lands.

**A loose marker can also be KICKED, and inherits its origin's geometry exactly**: ejected dot2's marker,
approached from the east and pressed west, moved 44 → 17 (d = −27) — dot2's own measured flight — and
**dragged dot0 along in the same compound-sweep pairing** already characterised for raw dot2. Steerable,
but only within its current phase class, since kicks preserve phase.

### ⚠️ And that result contains the escape the deadlock was missing

The wall was: *box2 is phase (1,1); walking preserves phase; a click delivers a dot's fixed canonical
phase; dot0→(1,2), dot1→(0,1), dot2→(2,0), none of them (1,1) — so after three clicks the piece can
never return to box2.* **Every clause of that assumed the click's phase belongs to the DOT.**

It belongs to the **cell**. And the table above shows that cell's phase is **(1,1)** — box2's own phase.
So the three canonical phases were never the full set of deliverable ones: **a marker parked on a (1,1)
cell delivers (1,1), and that is a return ticket to box2.** The premise dies not because markers keep
an identity, but precisely because they do not — their phase is real estate, and real estate can be
chosen.

Two orderings now worth driving, and the second is what the agent's own "what I did not cover" was
circling:
1. **end on a click against a marker sitting at (1,1)** — e.g. clicking box3's marker from inside box1
   fills box1 and sends the piece to (55,40), phase (1,1), from which box2 is walkable. It costs box3
   its fill, so count what remains filled and read `levels_completed` anyway: **nobody actually knows
   how many boxes the win needs** — every failed line so far assumed three.
2. **bare-ferry into box1 with dot0 (as `r22` did, leaving box1 empty), then fill box1 from within with
   a different object's marker** — Q3 proved a marker enters any box regardless of origin, so this
   combination has never been tried.

Also cheap and unmeasured: **box2 is fillable** (Q3 filled it with a recycled marker). If the win wants
**four** filled boxes against three objects that is an impossibility worth stating; if it wants three
filled plus the piece standing in box2 — whose interior matches the PIECE — then a (1,1) landing is
exactly what makes that reachable, and it has never been available before.

Being driven now with the per-action `extra4` census on and `levels_completed` read after every action,
so a partial-fill win cannot be walked past.

## 2026-08-16 — ar25 L5: keys past 40,000, frontier decelerating but not turned (agent, runs 8-9)

| run | expanded | keys | frontier | Δkeys | ratio | Δfrontier |
|---|---|---|---|---|---|---|
| 1-7 | 4,614 → 28,627 | 5,720 → 34,909 | 1,106 → 6,282 | — | 1.16-1.29 | — |
| 8 | 32,313 | 39,228 | 6,915 | 4,319 | 1.17 | **+633** |
| 9 | 35,928 | **43,225** | 7,297 | 3,997 | 1.11 | **+382** |

Keys are **24% past the corrected model's predicted ceiling** (43,225 against 34,902) and still adding
~4,000 a run. The frontier is **decelerating** — +633 then +382, a ratio of about 0.60 — but has **not
turned negative**. Every soundness check still green across all 35,928 expansions: divergence 0,
deaths 0, C1, C2 and both `sel_phase` identities re-asserted at the top of every process.

**The agent's postmortem of the 554 estimate is the part worth keeping**, and it is a self-critique
rather than an excuse: 554 came from a **single division** (34,909 / 63) applied to a **3,000-node
sample, about 8% of the search**, and it silently inherited two things that sample had itself flagged as
unconfirmed — the band count had seen **19 of an assumed 21 and was still climbing**, and the 127 exact
piece footprints were a **sample lower bound read as a ceiling**.

> *The arithmetic was not wrong on its face. It was applied to a search that had not reached the point
> the estimate assumed.*

Which is the same failure mode as the sp80 exhaustion price earlier today (40-55k nodes ≈ 1-1.7h, from
six noisy points; the real run passed 72,684 with the frontier still climbing). **Twice in one session
an order-of-magnitude extrapolation was quoted with its caveat and then spent as if it were the
midpoint.**

**Now chained from the MAIN thread** (`ar25_run_to_exhaust.py`, backgrounded — a main-thread background
job survives across turns where a subagent's dies with it). If the 0.60 deceleration holds, the frontier
peaks near 7,900 within ~10 runs and drains, putting a real exhaustion — and therefore a **proof** about
level 5 — about a hundred minutes out. The loop stops on frontier 0, on a win, on its wall-clock cap,
**or on three consecutive runs where the growth is not decelerating**, because two data points are not a
trend and the loop should not burn a budget defending one.

## 2026-08-16 — ka59 L2: the (1,1) return ticket WORKS, and it exposes a probable router bug in an earlier "wall" (agent, `ka59_y11.py`)

The construction was driven and it did exactly what the map predicted.

| act | leg | event | `extra4` after |
|---|---|---|---|
| 1-14 | kick dot0 west, kick dot1 west (right region, no clicks) | | `[]` |
| 15-20 | box3, **click dot1** → box3 filled | | `[(55,40)]` |
| 21-32 | chain-kick dot0 north — **the fill survives 12 actions of routing untouched** | | `[(55,40)]` |
| 33-37 | box0, **click dot0** → box0 filled, piece → phase (1,2) | | `[(8,46),(9,46),(55,40)]` |
| 38-42 | walk into box1 — **straight route, no search**, phase matches | | unchanged |
| 43 | **click box3's marker from inside box1** → box1 filled, box3 EMPTIED, piece → (55,40), **phase (1,1)** | | `[(8,46),(9,46),(10,14)]` |
| 44-48 | walk to box2, land dead centre **(52,52)** | | unchanged |

**Final: 2 boxes filled, the piece standing exactly in box2, `levels_completed` = 1.** No death, no
accidental graze in 48 actions — every fill that should have persisted did, and the one deliberately
spent shows up precisely where and when it was clicked.

So the (1,1) ticket is real and **costs a box's fill**: box3's is the only measured (1,1) cell, and
spending its marker to reach that phase empties it. 2-of-3 plus the piece in box2 is not the win.

### ⚠️ But `ka59_x3.py`'s own output says an earlier "wall" was probably a ROUTER GOAL bug

`x3` reported, for every box, the components its **interior** spans — and for box2:

> `box2  centre (52,52) interior=9 cells -> 9 components [18,19,20,21,22,23,24,25,26]`

**Nine interior cells in nine different components — one per phase of the right region.** Every box
interior spans all nine phases; that correction is what made `x3` valid in the first place, and it
applies to box2 too. So *"box2 requires phase (1,1)"* is a fact about its **centre**, not about the box:
**from anywhere in the right region, some box2 interior cell is reachable at the piece's current phase.**

Which puts `ka59_y2.py`'s terminal failure in a different light. It ended *"NO ROUTE FOUND from (44,48),
phase (2,0) — box2 requires phase (1,1)"*, with **all three boxes filled**. (44,48) is in the right
region. If that route was aimed at box2's **centre** rather than at any interior cell, it would
correctly report no route while a route to a different interior cell existed — and **y2 would have been
one correctly-aimed route away from finishing, making the "fill model is exhausted" conclusion built on
it void.**

Being checked now, in that order: first ask for a route to **each of box2's nine interior cells
individually** from y2's exact end state; then, if any succeeds, re-drive y2's line and finish into
whichever cell matches the piece's phase — with the per-action census running.

**That configuration has never actually been achieved**: `r20` visited box2 *before* filling, `y2`
filled and could not return, `y11` reached box2 with only two filled. Three fills **and** the piece
inside box2, simultaneously, at the end, remains untested.

*And the next lever after that, if it is still needed, comes from y11's own data: a marker lands on the
cell the piece was standing on, so **standing on a (1,2) cell inside box3 mints a (1,2) marker outside
box1** — arbitrary phase delivery, which would dissolve the phase constraint entirely and let dot0 be
placed in box1 matched rather than spent as a ferry.*

## 2026-08-16 — ka59 L2: y2's "wall" is attested only by an UNCONTROLLED NULL (main thread, `ka59_v2.py`)

`ka59_y12.py` killed my router-goal hypothesis with a well-designed test: from y2's exact terminal
state it asked for a route to **all nine** box2 interior cells, not just the centre, and got **0 of 9** —
including `(53,51)`, whose phase (2,0) matches the piece's own. A centre-aiming bug cannot explain an
unreachable same-phase cell, so the wall looked real.

**Main-thread check says the walk graph disagrees.** Recomputed the partition with a control that
passes — the entry board reproduces `x3` exactly, **27 components, all phase-pure** — then rebuilt y2's
terminal board by marking its four census cells `[(8,46),(9,46),(10,14),(55,40)]` as filled:

```
box2 interior components : [18,19,20,21,22,23,24,25,26]   (unchanged from entry)
(53,51)                  -> component 24
piece (44,48)            -> component 24
                                    -> CONNECTED
```

**The one cell the test correctly identified as decisive is in the SAME component as the piece.** So a
route exists, and the router said NOT FOUND — for that cell and for the other eight.

⚠️ **Which means the wall is attested only by a null from an instrument that was never shown to
succeed.** `y12` ran no positive control. *A search that fails to find a path is worthless without one*
— the rule that has already caught two instruments on this campaign today (the offset key that reported
exhaustion on a level whose win it was standing on, and the FIRE-transfer bug that produced confident
wrong states with no anomaly counter). **Zero-for-nine is exactly what a broken router looks like, and
it is indistinguishable from a real wall without one arm that must succeed.**

Caveat stated on my own side rather than hidden: board B here is a **simulation** — four cells marked
filled on the entry board, not a replay of the line — and the real terminal board also has two kicked
dots whose cells have moved. That should not affect connectivity *within* component 24, but the
authoritative partition is the one computed on the real board.

Being run now, in order: (1) give the router a **positive control** from y2's terminal state — a route
to a cell known reachable, one step away; if that also returns NOT FOUND, every "NO ROUTE" verdict on
this level needs re-reading; (2) recompute the partition on the **real** terminal board; (3) if the
router is the problem, fix it and drive y2's line to completion — **three boxes filled AND the piece
inside box2**, the configuration nobody has ever achieved and the one the entire fill-model closure
rests on.

*Three times in this game's history a "wall" has turned out to be an instrument: box1 unreachable
(twice) until the piece arrived on phase (1,2); the click surface "inert" until the sweep ran from a
board that had been played; and now this. The pattern is specific enough to act on — **on ka59, a
negative result about reachability has never once survived being given a positive control.***

## 2026-08-16 — ka59 L2: WALL CONFIRMED by exhaustion — and the phase-component MODEL is the thing that was wrong (agent, `ka59_y13/y14/y15.py`)

Three instruments, and only the third is authoritative. **This corrects my own `ka59_v2.py`, which
concluded CONNECTED and was wrong.**

**1. The router's positive control PASSED.** From y2's real terminal state, one real press in each
direction, then asking the router for the exact cell it had just proved reachable:

```
press 1: (44,48) -> (44,44)   router asked for (44,44): FOUND len=1
press 2: (44,48) -> (44,50)   router asked for (44,50): FOUND len=1
press 3: (44,48) -> (42,48)   router asked for (42,48): FOUND len=1
press 4: (44,48) -> (48,48)   router asked for (48,48): FOUND len=1
```

So it is not broken on trivial targets — the uncontrolled-null worry is answered.

**2. The static partition, recomputed on the REAL terminal board** (marker cells excluded from the walk
set, as a control against my own caveat), still said **piece (44,48) → component 24** and
**(53,51) → component 24 — CONNECTED**. Escalating `bfs_route` against (53,51) at **3,000 / 6,000 /
12,000** nodes: **NOT FOUND every time.** Graph says yes, router says no, three budgets apart.

**3. The authoritative instrument settles it — an exhaustive real BFS that targets nothing and just
drains the queue:**

```
expanded 88 nodes, 88 distinct reachable positions -- EXHAUSTED (queue drained, cap was 15,000)
(53,51) in reachable set: False
all nine box2 interior cells: False
reachable set bbox: x=[32,60] y=[32,60]
```

**A queue that drains at 88 against a 15,000 cap is not a budget failure — there is nothing left to
explore.** Box2 sits *inside the bounding rectangle* of the reachable region and is not among its 88
cells. So **y2's wall is real**, and the fill-model closure is reinstated on the strongest evidence it
has had: not a failed route, but a fully drained reachable set containing zero box2 cells.

### ⚠️ The correction that matters more than the verdict

**The static colour-based flood fill OVERCOUNTS connectivity**, and both the agent's version and my
`ka59_v2.py` did it. A same-colour-implies-walkable model is not a safe stand-in for the engine's own
walk graph — *at least once a board has been altered by fills*.

Likely mechanism, not chased and flagged as unproven: `ferry.py`'s own `find_cell()` describes the piece
as *"one cell, or a tight cluster — the piece smears over 2-4 cells"*. If the piece effectively occupies
more than one cell, a landing needs more than one clear cell, and a point-model admits landings the
engine refuses. That would produce exactly this — a permissive map over a restrictive reality.

**Practical rule for this campaign, effective immediately: the phase-pure component model
(`x2`/`x3`/`x4`) is a HYPOTHESIS GENERATOR, not an oracle.** It was right about phase-purity, right that
box1 needed (1,2), and right about the region structure at entry — and it is wrong about reachability on
a board that has been played. **Verify any reachability claim with an exhaustive real BFS before acting
on it.** The cheap tell is the one seen here: a static model and a real router disagreeing, at which
point the model loses.

*This session has now had a "wall" turn out to be an instrument three times on this game — box1 twice,
the click surface once — which is exactly why I pushed back here. The fourth time it was the wall, and
the instrument that proved it was the one that answers without being asked a question: not "can you
reach X" but "what can you reach at all".*

Still unattempted, and now the live next move: **arbitrary phase delivery** — a marker lands on the cell
the piece was standing on, so standing on a chosen off-phase cell *inside* a box before clicking mints a
marker at a phase of your choosing, rather than at whatever the auto-route happened to leave.

## 2026-08-16 — ar25 L5: BFS IS THE WRONG INSTRUMENT — the deceleration was noise (main thread, `ar25_run_to_exhaust.py`)

Six more chained runs from the main thread, and the loop's own stop rule fired:

| run | expanded | keys | frontier | Δfrontier |
|---|---|---|---|---|
| 1 | 39,484 | 47,345 | 7,861 | — |
| 2 | 42,704 | 50,835 | 8,131 | +270 |
| 3 | 46,283 | 54,939 | 8,656 | **+525** |
| 4 | 49,781 | 58,659 | 8,878 | +222 |
| 5 | 53,269 | 62,530 | 9,261 | +383 |
| 6 | 56,701 | **66,325** | 9,624 | +363 |

**The +633 → +382 "deceleration" that justified this run was noise from two data points.** Across six
runs the frontier delta is flat and jittery (+270, +525, +222, +383, +363) with no downward trend at
all. Final state: **56,701 expanded, 66,325 distinct keys, frontier 9,624**, 340,207 raw boards,
**deaths 0 and divergence 0 throughout** — the key stayed sound the whole way.

Keys are now **90% past** the "corrected" model's 34,902, which was itself the second estimate to be
refuted. **The space is larger than any estimate anyone has produced for it, and the frontier grows
steadily.**

**Conclusion: BFS cannot exhaust ar25 level 5.** It is the wrong instrument — the level needs a hand
solve or a goal-directed search, not completeness. That is a real result: it retires an approach that
has now consumed fifteen chained runs, and it says what the next session should NOT spend time on.

*The loop's stop rule is the part worth keeping.* It was written as: **stop if three consecutive runs
fail to decelerate**, precisely because the two-point trend that motivated the run might be noise — and
it was. Encoding "two data points are not a trend" as a **condition in the script** rather than as an
intention saved roughly seventy minutes of futile compute, on the same day two order-of-magnitude
extrapolations (sp80's 40-55k nodes, ar25's 554 positions) were each quoted with their caveats and then
spent as if they were midpoints. *The caveat only protects you if it is executable.*

Checkpoint left intact at 56,701 expanded, so nothing is lost if a future session wants the state for a
different purpose — but it should not be for more BFS.

## 2026-08-17 — ar25 L5: the induced L1-L4 win predicate does NOT transfer literally (agent, `ar25_u1/u2.py`)

**Verdict: PREDICATE_FOUND_NOT_REACHED.** The predicate induced from board-diffs at all four win
instants (replay landed at the documented action indices 14/39/79/108) is: *a movable colour-5
piece (rendered colour-4 in flight) docks bbox- or axis-exact onto a static colour-11 target; the
docking machinery is a new ruleset every level, but the precondition pattern repeats — a control
surface must be set BEFORE the first piece-selecting click (one-way door).*

Translated to L5: S (88 cells, 15x15 bbox) vs a 189-cell colour-11 zigzag with two 3x3 corner
markers at (36-38,15-17) and (12-14,39-41). Driven center-exact onto BOTH markers (13 presses each,
arrival measured from bbox, tolerance ±2), under band preconditions +0/+3/+7/+14 DOWN presses —
**all arms `levels_completed=4`, `NOT_FINISHED`**. All three band preconditions converged to the
identical final board, so no L3/L4-style one-way-door effect in the sampled phases.

**CORRECTION to an earlier note: L5's axis pairing is A1=up(dy-3) A2=down(dy+3) A3=left(dx-3)
A4=right(dx+3)** — the OPPOSITE of the breadth-recon directional note (A1/A2=x, A3/A4=y). Found
because the walker built on the old note overshot into a wall; re-measured from raw bbox deltas
(`results/ar25-u2.txt`). Changes no verdict (reachable set identical), but future walkers must use
the corrected pairing.

Main-thread verification: probe's `won=True` in the raw output means ARRIVED, not win — the code
returns True on arrival or win alike; the authoritative readings are `levels_completed=4` +
`NOT_FINISHED` in every arm, present per-step in `results/ar25-u2.txt`.

**Named untested (the next cheap arm): axis-exact dock against the zigzag's 189-cell INTERIOR**
(L1's predicate was axis-exact, not size-matched — the corner markers were an L3 analogy). Mirror-
decouple was correctly skipped: colour 4 absent from L5's board, already measured.

## 2026-08-17 — ka59 L2: ARBITRARY PHASE DELIVERY IS REAL — and the agent's REFUTED verdict is OVERSTATED (agent `ka59_z1..z4.py`, main-thread scope correction)

**Arm 1 VERIFIED (live, both measurements exact):** standing on a chosen cell before clicking mints
a colour-4 marker AT that cell; clicking that marker later delivers the piece to that exact cell at
that cell's phase. Minted at (52,52) box2-interior (1,1) via clicking dot2; delivery confirmed.
**Plus a gap closed: dot2's kicks preserve its phase set** (3 of 4 kick arms relocated it, none
gained (1,1)) — the notes/next-session-prompt.md:374 gap.

**The drive (z2) died at the mint click**: clicking dot2-at-entry strands the piece in dot2's (2,0)
RIGHT pocket — exhaustive real BFS from the post-mint state drained at **60 nodes** (z3, verified in
main thread from results/ka59-z3.txt), reaching neither dot, nor box2, nor dot0's approach region.

⚠️ **Main-thread correction: the agent's "REFUTED — no reordering can fix it" covers ONLY the
mint-via-dot2-at-entry variant.** The refutation argument ("no raw dot delivers (1,1)") attacks
*walking* into box2 — but the ticket construction never needs the piece to walk there: the FINAL
click delivers it (clicks have no proximity requirement), and the ticket's own (1,1) is planted
early while box2 is free to enter from spawn. The stranding is a property of WHICH object triggers
the mint and WHERE it sits. Untried variants, concrete:

**The candidate line (mint-via-dot0), every leg either y11-proven or one check away:**
1. Pre-kick dot0 west then chain north to (19,20) (y11's proven kicks — phase (1,2) preserved,
   NORTH of the internal band). Pre-kick dot2 west past the moat (compound sweep does this cheaply).
2. Fill box3: enter box3 (RIGHT), click dot1 at entry → box3 filled, piece to dot1's cell (RIGHT).
3. Walk to a box2 interior cell AT THE PIECE'S CURRENT PHASE (interiors span all 9 phases; verify
   reachability by real BFS, not the static map). MINT: click dot0 → ticket lands in box2, piece
   lands at (19,20), phase (1,2), north of the band — the mint click IS the moat crossing.
4. Walk into box1 (y11's proven leg). Fill box1: click dot2 (LEFT-BOTTOM, proximity irrelevant) →
   box1 filled by dot2's marker, piece to dot2's cell, phase (2,0), LEFT-BOTTOM.
5. Walk into a box0 interior (2,0) cell (ONE reachability check — the only truly new leg).
6. FINAL: click the box2 ticket → box0 filled by the relocating ticket, piece delivered INTO box2.
   End state: box3+box1+box0 filled, piece inside box2 — the never-achieved config.

Two reachability checks decide it (step 3's box2-interior-at-phase, step 5's box0-(2,0)); each
needs a positive control per this game's law (a negative reachability result has never survived one).
Arm 4 (four boxes) stands as a DEDUCTION (3 markers = ceiling 3 fills; recycling conserves count).

## 2026-08-17 — ar25 L5: the zigzag region is SWEPT — 169/169 raster + 8 axis-exact legs, no win (agent, `ar25_u3_zigzag_sweep.py`)

**SWEPT_NO_WIN, quantified by census** (`results/ar25-u3-result.json`, verified): all 169 lattice
cells whose 15x15 S-bbox overlaps the zigzag's bbox visited (13x13 raster, 0 interior blocks), plus
8 axis-exact extension legs along both marker rows/columns out to the board edge (all 8 blocked only
by the boundary), plus a band+10 variant on the 10 central cells, plus **an A5-click branch test at
every one of 193 visited positions** (deepcopy → press → check → discard; sel_n%3 asserted, no
drift). 183 distinct positions, zero `levels_completed` change, 6.7s wall.

**New structural fact: the zigzag's outer bbox pixels (x=12,38 / y=15,41) are OFF the piece's 3px
lattice from entry** (mod-3 parity mismatch) — a literal center-match on those exact coordinates is
structurally impossible regardless of sweeping. Both 3x3 marker centers ARE on-lattice.

This closes the axis-exact/interior-dock arm the goal-directed session named. L5's dockable surface
under the L1-L4 predicate is now exhausted at the position level. What remains untried on L5 is not
position: it is the JOINT space (band phase x S position) beyond the 4+1 phases sampled, and any win
condition not of the docking family at all.

## 2026-08-17 — sp80 L3: s11 engineering VERIFIED — multi-match resolved by SIZE, checkpointing live, long run launched (agent + main thread)

`sp80_s11.py` replaces the load-bearing tie-break with a two-tier resolver: (1) body SIZE (w,h is a
fixed physical property; the freshly-detected driver blob is never occluded, so its size is exact) —
**55/55 multi-match events across 3,624 smoke expansions resolved by size alone**; (2) frame re-read
on size ties; 0 survivors → FORK both branches instead of guessing (code-reachable, never fired at
smoke scale ~1% of expected total — honest caveat, the fork counter is in every FINAL line).
Checkpoint = atomic pickle every 2,000 expansions + on exit; resume verified live (705 → 1,403
continuing); growth curve at expanded=2,000 byte-identical to the historical run (7,355 states /
5,355 frontier) so the transition function is unchanged; **positive control = the known L2 win
replayed through the SAME resolver code, PASS**.

Main thread launched the long run (background, chained): 12 x 3300s cap (~11h), stop early on
`exhausted=True` or `win=True` in FINAL, log `results/sp80-s11-run1.txt`, checkpoint
`results/sp80_s11_ckpt.pkl`. Watch `multi_match`/`forked` counters — if `forked` starts firing the
state count is no longer comparable to prior runs.

## 2026-08-17 — ka59 L2: ticket line BROKE AT LEG 1 — and the break narrows the construction to ONE order (agent `ka59_w1..w5.py`, main-thread redesign)

**BROKE_AT_LEG_1, mechanism measured**: a kick throws the DOT across the moat but the PIECE stays —
chain-kicking dot0 north requires the piece standing in dot0's new (LEFT) component, which requires a
prior CLICK-crossing (139-node exhausted BFS from the post-kick state; dot0's new cell outside the
reachable bbox [31,61]x[31,61]). Minting off raw unkicked dot0 lands the piece in a component from
which box1 is unreachable (0/18 cells, 77-node exhaustion). Reversed kick order = no-op.
My step-1 summary had silently dropped dot1's crossing role from y11's line — a compressed
plan-restatement is itself an unchecked given.

**Corrected construction (main thread — resolves the conflict: dot0 cannot be both the chain-kick
passenger and the mint trigger; so dot1 stays RIGHT as the box3 filler, dot2 carries the band
crossing):**
1. Kick dot0 west (19,44) + dot2 west (17,47) (compound sweep does both; piece stays RIGHT).
   dot1 stays at entry (41,34) RIGHT.
2. Fill box3: stand in box3 (RIGHT), click dot1 -> box3 filled, piece to (41,34) RIGHT (0,1). No crossing.
3. Walk to a box2 interior cell on the (0,1) lattice (CHECK A + positive control). MINT: click dot0
   (west) -> ticket lands in box2, piece lands (19,44) LEFT-BOTTOM (1,2) -- the mint IS the crossing.
4. Chain-kick dot2 north past the internal band (CHECK B -- dot2's south-approach chain at its west
   position is unmeasured; dot1's chained (17,34)->(17,19)).
5. Fill box0: stand in a box0 (1,2) interior cell (CHECK C), click dot2 (north) -> box0 filled,
   piece to dot2's cell NORTH of band, phase (2,0).
6. Walk into a box1 interior (2,0) cell (CHECK D -- "box1 only at (1,2)" was measured from specific
   positions, never from a (2,0) NORTH component; real BFS + control).
7. FINAL: stand in box1, click the TICKET -> box1 filled by the relocating ticket, piece delivered
   into box2. End: box3+box0+box1 filled, piece in box2.
Checks A-D each = exhaustive real BFS + positive control. Any check failing = the wall is real at
that leg, and the census says what IS reachable.

## 2026-08-17 — ar25 L5: the JOINT (band phase x dock) space is swept — 21 phases x 3 docks x A5, no win (agent `ar25_u4_joint_sweep.py`)

**JOINT_SWEPT_NO_WIN**: 21/21 band phases (rows 0-60 in 3-row steps; 5 above entry, 15 below, both
clamps verified by zero-frame-change) x 3 docks (marker1, marker2, zigzag interior centre) — 63/63
arms arrived exact-centre, 63/63 A5-click branches, zero wins. S's post-selection spawn identical
(49.0,43.0) at all 21 phases — band phase does not affect S's dock geometry at all.

**Instrument note worth keeping**: the first clamp detector used a colour-10 component reader and
found only 12/21 phases — it was reading its OWN blindness as "clamped" (the band 4-connects with a
static colour-10 column near the extremes, breaking component decomposition, while raw frames kept
changing). Fixed by frame byte-equality (the repo's blocked-press law). 9 of 21 phases have
row_observed=None in the census for this reason — their identity rests on predicted row + non-equal
frames, stated rather than hidden.

Named remaining gaps on L5: the full 21x~169 (phase x S-position) grid, and any win family that is
not docking at all.

## 2026-08-17 — ka59 L2: BROKE_AT_LEG_3 — box3's fill DISCONNECTS box2, and the fix is to make box3 the LAST box (agent `ka59_t1/t2.py`, main-thread redesign 3)

Verified legs: **compound sweep works exactly as recorded** (one westward press relocates dot0 →
(13,44)/(13,45) AND dot2 → (17,47)..(18,48), both past the moat, dot1 untouched) and **box3-fill via
dot1 works** (piece to (42,34), phase (0,1)). Then CHECK A failed: from the post-box3-fill state,
**box2 is unreachable at ANY phase** (exhaustive BFS drained at 102 nodes, positive control PASS).
Diagnostic `ka59_t2.py`: **box2 WAS reachable right after the compound sweep, before box3 was
touched** (129-node census, control PASS). Filling box3 first is what strands the piece — the
(0,1) component at dot1's landing does not contain box2.

**Redesign (main thread) — order the jobs so box3 is filled LAST, by the relocating ticket, and use
the no-proximity click to fill box1 from across the map (x4's own trick):**
1. Compound sweep: dot0 → (13,44) LEFT-BOTTOM, dot2 → (17,47) LEFT-BOTTOM; dot1 stays at entry RIGHT.
2. Walk into box2 (PROVEN reachable at this point — t2's 129-node census). MINT via dot0 → ticket in
   box2, piece to dot0's canonical cell ~(13,44), phase (1,2), LEFT-BOTTOM. The mint IS the crossing.
3. Chain-kick dot2 north past the internal band (CHECK B — unmeasured).
4. Fill box0: stand in a box0 (1,2) interior cell (CHECK C), click dot2 (north) → box0 filled, piece
   to dot2's canonical cell NORTH of band, phase (2,0).
5. Walk into a box1 interior (2,0) cell (CHECK D).
6. Fill box1 FROM AFAR: click dot1 (still at entry, RIGHT — clicks have no proximity requirement) →
   box1 filled by dot1's marker, piece returned to dot1's canonical cell (41,34)-area, phase (0,1),
   RIGHT. The click that fills box1 is also the return ticket to the RIGHT region.
7. Walk into a box3 interior (0,1) cell (CHECK E — t1's failed census was box2-from-(42,34) on a
   different board; box3's (0,1) interior is a different question).
8. FINAL: stand in box3, click the TICKET → box3 filled by the relocating ticket, piece delivered
   into box2. End: box0+box1+box3 filled, piece in box2 — every job done with three dots, because
   the ticket fills the last box AND delivers, and dot1's fill click doubles as the return crossing.

## 2026-08-17 — ar25 L5: FULL GRID CLOSED — 21 phases x 169 raster x A5, zero wins (agent `ar25_u5_fullgrid_sweep.py`)

**FULL_GRID_SWEPT_NO_WIN, verified census** (`results/ar25-u5-census.json`): 21/21 band phases
(phases_missing=[]) x the 169-cell overlap raster = **3,549/3,549 arrivals + 3,549 A5-click
branches, 0 blocked cells, 0 wins**, post-select spawn (49,43) reconfirmed at every phase, 60.6s.
The docking/position/click family on L5 is CLOSED at census level.

Remaining families, named: (a) the far-corner board regions outside the raster + axis-extension
footprint (no session has swept them), (b) non-positional effects — timing/order invisible to a
static-arrival census. After (a), L5 joins re86 L6 / tr87 L3 as "needs a fundamentally new idea".

## 2026-08-17 — ar25 L5: POSITION FAMILY CLOSED BOARD-WIDE — level PARKED pending a structurally new idea (agent `ar25_u6_wholeboard_sweep.py`)

**BOARD_CLOSED_NO_WIN**: the frame region outside the 169-cell raster (right/top/bottom strips, 191
candidates/phase) swept at all 21 band phases — **1,869 arrivals + 483 boundary blocks + 2,268
A5-click branches, zero wins**, counts byte-identical across every phase (band phase has zero effect
on this region too). The 79 skipped cells/phase sit OUTSIDE the measured playable extent
(x∈[7,55], y∈[1,55] on the lattice — a uniform rectangle confirmed independently across all strips,
extending the two axis-line boundary measurements to the whole width/height).

**Cumulative census for the position x phase x click family on L5: raster 3,549 + joint 63 + zigzag
193 + whole-board 1,869 arms — all with per-press levels_completed reads and A5 branches — ZERO
wins.** The family is closed over the entire board. **ar25 L5 is PARKED** alongside re86 L6 and
tr87 L3: what remains is non-positional (press order/timing effects invisible to arrival censuses)
or an unknown verb outside {A1-A5}. Do not spend more rounds on position sweeps here.

## 2026-08-17 — ka59 L2: BROKE_AT_LEG_5 — box1 needs (1,2), so the dot ASSIGNMENT is now forced (agent `ka59_u1/u2.py`, main-thread redesign 4)

Legs 1-4 of the box3-last line WORKED: compound sweep, box2 entry + MINT via dot0 (ticket at
(52,52)), **dot2 chain-kick past the internal band — needs 2 real kicks, not 1** (single kick
reaches y=32/33, still south; CHECK B closed), box0 filled via dot2 (CHECK C: 70-node BFS, 2/4
phase cells reachable, control PASS). **CHECK D killed it: from dot2's north cell (18,18) phase
(2,0), box1 is unreachable at ANY phase — 42-node exhausted BFS, control PASS — a genuine negative.**
Plus one instrument fact: a MINT click landing beside box0's wall produces one transient corrupted
frame (spread-guard trips); one settle action resolves it (auto-handled in ka59_u1.py).

**The constraint set now forces a single assignment.** Box1 entry has only ever succeeded at phase
(1,2) — dot0's canonical delivery, nobody else's. Therefore dot0 CANNOT be the mint trigger; it must
be the box0-filler whose click delivers the piece to (1,2) NORTH (y11's exact leg). The mint must
use dot2. dot1 stays the from-afar box1 filler / RIGHT-return. **Redesign 4 — the last assignment
consistent with every measurement:**
1. Compound sweep (dot0 → (13,44), dot2 → (17,47), dot1 stays RIGHT).
2. Walk into box2, MINT via **dot2** → ticket in box2, piece to dot2's canonical cell LEFT-BOTTOM
   (2,0) (CHECK A': is that LEFT (2,0) component non-isolated? The z3 isolation was dot2-at-ENTRY).
3. Chain-kick **dot0** north from (13,44) past the band — 2 kicks likely, geometry unmeasured at
   this x (CHECK B').
4. Fill box0: stand in a box0 (2,0)-lattice interior cell (CHECK C'), click dot0 (north) → box0
   filled, piece to dot0's north cell, phase **(1,2)**, NORTH.
5. Walk into box1 at (1,2) — y11's proven leg shape (CHECK D').
6. Fill box1 FROM AFAR: click dot1 (RIGHT) → box1 filled, piece to (41,34) (0,1) RIGHT.
7. Walk into a box3 (0,1) interior cell (CHECK E').
8. FINAL: click the ticket → box3 filled, piece in box2.
If ANY check fails here, the ticket construction is exhausted across all consistent assignments —
that itself would close the marker-fill family and the level needs a different mechanism entirely.

## 2026-08-17 — ka59 L2: attempt 4 BROKE AT CHECK B' — but by an ACCIDENT of the settle press, so the closure does NOT bank yet (agent `ka59_s1_forced.py`, main-thread audit)

Legs 1-2 worked (sweep; mint via dot2, ticket parked in box2, piece to dot2's LEFT (2,0) cell).
**Then the instrument spent the plan's own resource**: the mint's auto-settle press — chosen only by
"does this un-corrupt the frame" — walked INTO dot0 and kicked it 12 west to the wall,
(13,44)→(1,44). The first CHECK A'/B' then ran against the STALE position (0/4 routes = pure
artifact, caught); the corrected run measured the JAMMED position: 52-node exhausted component,
only 3 approach cells reachable, no direction kicks dot0 north off the wall. **BROKE_AT_LEG_3.**

⚠️ **Main-thread audit: the agent's "every assignment now tried and failed" claim is CONTAMINATED —
the B' failure was caused by the accidental settle-kick, not by the assignment.** Nobody has
measured dot0's north-chain from its PROPER (13,44) landing with the piece in the post-mint (2,0)
component. The lesson that does bank: **a recovery/settle action is not neutral — it can spend a
dot's favourable position that a later leg depends on.** Settle directions must be chosen to avoid
every dot's footprint.

Attempt 5 = Redesign 4 unchanged, with the settle press CONSTRAINED away from all dot footprints
(any direction that un-corrupts and touches nothing). If B' then fails structurally — dot0 at
(13,44) unreachable or unchainable north from the (2,0) component — the box3-last family closes for
real, with the census to show it.

## 2026-08-17 — ka59 L2: clean-settle attempt confirms the DIRECT assignments dead — but the family is NOT closed: two mechanics were never composed (agent `ka59_s4_clean_settle.py`, main-thread analysis)

**Uncontaminated re-run**: the settle fix worked (trial log shows west WOULD have re-kicked dot0 —
the accident reproduced inside the fix's own trial data — and the clean direction was chosen; dot0
asserted at (13,44) post-mint). Then CHECK B' failed structurally: from the post-mint (2,0)
component, only 4/132 of dot0's approach cells are reachable (44-node exhausted BFS, control PASS)
and every reachable approach kicks dot0 AWAY from the band (north-approach → south, west-approach →
east). **Both direct dot-role assignments (mint-via-dot0 / mint-via-dot2) are dead.**

**Main-thread analysis — the remaining space is ORDERINGS composing two never-used mechanics:**
(a) **the return-click fill**: standing INSIDE an unfilled box and clicking dot1 (still at entry,
RIGHT) fills that box with dot1's marker AND returns the piece RIGHT — one click, two jobs, never
driven; (b) **markers inherit their origin dot's kick geometry** (measured: ejected dot2's marker
flew dot2's own −27), so **dot1's marker parked at (17,34) should chain north (17,34)→(17,19) like
dot1 itself did in y11** — a north-of-band delivery that does not involve dot0 at all, landing
(2,1)-phase; box1's (2,1) interior cell reachability from there has never been measured.
The endgame shape that survives every measured constraint: box0+box1 filled while LEFT (one via a
raw dot, one via the return-click or a recycled marker), piece re-enters RIGHT late via dot1's
return click, walks into box3, and the FINAL click on the box2 ticket fills box3 + delivers the
piece into box2. The open questions are pure reachability/ordering — enumerable, not open-ended.
Next: a GUIDED SEARCH over click/kick orderings with live deepcopy validation per leg, instead of
hand-deriving attempt 6, 7, 8 one wall at a time.

## 2026-08-17 — ka59 L2: marker-geometry CONFIRMED for dot1's marker; composed line broke on a THIRD approach-contamination (agent `ka59_g1_composed_line.py`)

**Banked mechanic**: dot1's marker kicked from dot1's own entry cell/approach lands on the exact
cells (17,34)/(18,34), dx=-24 — markers inherit origin geometry, now measured on TWO dots.
**Composed line #1** (no mint: dot2 does the crossing+box3 fill, dot0 keeps y11's proven north
chain, dot1 saved for the return-click fill of box1, walk to box2 last): **broke at leg B by
CONTAMINATION, not a wall** — the approach BFS toward dot2 silently kicked it EAST en route; leg D's
69-node empty census matches "the crossing never happened", not a dot0 wall. Legs G (return-click
fill) and H (walk to box2) = NOT RUN. **Third contamination incident of the day (settle press,
approach walk x2) — the class is: ANY routed walk passing adjacent to a dot can kick it.**

Fix going forward, harness-level: a `safe_route` that forbids every cell adjacent to any dot/marker
footprint unless the leg IS a kick — verified per-press with deepcopy trials like the clean-settle
fix. Note for leg H: t1's box2-unreachable wall was measured with fill set {box3} from (42,34); the
composed line ends with fills {box3,box0,box1} — the walk graph differs per fill set (markers occupy
cells), and y11 DID reach box2 with fills {box0,box1}. Run the census fresh from the real end state.

## 2026-08-17 — ka59 L2: BROKE_AT_LEG_4 doubly confirmed — and a MODEL CORRECTION bigger than the verdict (agent `ka59_g2_safe_route.py`/`g2b_fallback.py`)

The safe_route harness works (fired correctly on the compound sweep — a documented pair-move, not
contamination — and exposed a dot0-vs-dot2 misclassification in the sweep reader, fixed by the
smaller-x fact). Primary line legs 1-3 clean; **leg 4 wall: the crossing click on west-kicked dot2
lands the piece at (18,50), phase (0,2), a 44-cell exhausted component** (control PASS) reaching
nothing useful — identical landing and identical wall in BOTH orderings (box3 via dot2 / via dot1),
so the wall is intrinsic to that landing cell. Also measured live: **the click-swap works from 25+
cells away** (no proximity, now demonstrated at range).

⚠️ **MODEL CORRECTION: a dot's delivery phase is NOT fixed by identity — it is POSITION-DEPENDENT
for multi-cell dots.** dot2's canonical delivery was "(2,0), zero exceptions in 156 arms" — and its
west-kicked canonical cell delivered **(0,2)**. Mechanism: a multi-cell footprint spans multiple
phases (dot2's 2x2 = {(2,2),(2,0),(0,2),(0,0)}; dot0's 1x2 = {(1,2),(1,0)}; dot1's 2x1 =
{(2,1),(0,1)}) and WHICH cell the piece lands on varies with the dot's location. Consequences:
(a) the structural deadlock proof's premise 2 ("phase fixed by identity") is FALSE as stated —
every delivery-phase argument must be re-read as "phase drawn from the footprint's phase SET at the
current position"; (b) (1,1) is still in NO dot's phase set, so box2 delivery still needs a marker
parked in box2 (the mint) — that part of the deadlock survives; (c) box1's (1,2) can only come from
dot0's set — dot0 remains the box1-entry key; (d) kick placement now CHOOSES the delivery phase
within the set — a whole new planning dimension nobody has used deliberately.
Legs G (return-click fill) and H remain NOT RUN — dot1 was spent in the fallback ordering.

## 2026-08-17 — ka59 L2: ALL THREE BOXES FILLED SIMULTANEOUSLY — first time ever — and the endgame reduces to ONE measurable question (agent `ka59_g3*.py`)

**`ka59_g3f_drive.py`, 43 actions, verified per-action**: kick dot0 west → kick dot1 west → box3 ←
click dot1 (crossing) → chain dot0 north ((19,20), works exactly when sequenced POST-crossing — a
kick never moves the piece, only a click does; g3b settled that the earlier "chain walls" were
pre-crossing category errors) → box0 ← dot0 (piece north (1,2)) → walk box1 → box1 ← click dot2
(from inside box1, at range). **{box0, box1, box3} filled simultaneously — never reached before**
(y11's recipe structurally empties one box to fill another). Piece exiled to dot2's canonical
(44,48) (2,0) — an 88-node exhausted component with zero overlap with box2 (three converging
positive-controlled censuses: g3d, g3f-final, g3g). `levels_completed` stayed 1. **So
"3 filled + piece ANYWHERE-but-box2" is refuted; the untested config is still 3-filled + piece IN
box2.**

**The one move that would produce it, named by the report itself and never measured: kick dot2 so
its CANONICAL CELL lands INSIDE box2's interior.** Then g3f's exact proven line, with that pre-kick
added, ends: click dot2 from inside box1 → box1 filled + piece delivered INTO box2. dot2 kicks east
from some approach (z4 measured 3 of 4 approaches relocating it to different regions — check
results/ka59-z4.txt for an east landing before driving new kicks). Slide-until-blocked vs box2's
frame is the open geometry question. If no kick lands dot2's canonical inside box2 → measure and
record; that closes the g3f-line family and the level's fill model entirely.

## 2026-08-17 — ka59 L2: FILL MODEL CLOSED — dot2's reachable rectangle never intersects box2, so "3 filled + piece in box2" is UNREACHABLE (agent `ka59_g4_dot2_canon.py`)

**FILL_MODEL_CLOSED.** Five dot2 states measured (entry, east kick, south kick, both 2-kick chain
orders): every canonical click-landing lies OUTSIDE box2's interior, and the two independently-
ordered chains CONVERGE on the identical SE corner (59,59)-(60,60) — dot2's kickable positions form
a closed 4-corner rectangle (NW entry / NE east / SW south / SE chains) whose corners never share
box2's x or y band. Kicks slide-until-blocked and nothing blocks inside box2's band, so no cardinal
kick sequence can ever park dot2 (or its canonical) in box2. With dot0 and dot1 both structurally
required elsewhere in the g3f line (box1's (1,2) key; box3's crossing), no resource can deliver the
piece into box2 with all three boxes filled.

**ka59 L2 is now PARKED**: every fill/placement configuration reachable under the measured mechanics
is either driven (all NOT_FINISHED — including the never-before-reached 3-simultaneous-fill) or
proven unreachable (this closure). Like re86 L6, the win condition is NOT the fill model — the next
idea must come from outside it (the uninterpreted compound-sweep mechanic is the one unexplained
phenomenon left on this board). Wave standing: ka59 stays 1/8+.

## 2026-08-17 — KAGGLE: v9-lite SCORED 0.10 — v8's 0.01 is EXPLAINED, and yesterday's "quota-blocked" submit had actually LANDED

`kaggle competitions submissions` (2026-08-17 01:32 UTC) shows the discriminating experiment already
ran: **submission 55559497, 2026-08-16 17:40 UTC, v9-lite, COMPLETE, publicScore 0.10** — the bare
400 we chased into the quota body was thrown AFTER a submission that day had already been accepted;
the "blocked" reading was wrong about the first attempt having failed. **Verdict: reverting v8's two
changes (60s unclaimed play slice + qstate bandit) restored the score 0.01 → 0.10 — the drop was
caused by v8 itself.** Consistent with (but no longer needing) the silent-worker-death/qstate-memory
hypothesis; both written explanations that predicted proportional loss stay refuted.

Cost of the wrong reading: today's 01:32 UTC submit (55567678, PENDING) is a byte-identical
DUPLICATE of v9-lite — today's quota spent re-confirming 0.10. **The next real submission is the
HYBRID (sample base ~1.56 + driver overrides), which still needs a REBUILD (it predates current
mirror.py) — build + verify + push it TODAY so tomorrow's 00:00 UTC window tests something new.**
Instrument lesson: "submission blocked" must be verified against `competitions submissions` (the
resource), not against the submit command's error text — the exact ledger-vs-worker rule from
long-running-job-discipline, on a remote resource.

## 2026-08-17 — sp80 LEVEL 3 FALLS — the checkpointed BFS wins at expansion 229,506, replayed independently, L3_LINE landed (main thread)

**The sp80_s11.py chain (6 checkpointed invocations, ~6.3h total) found a WIN**: 
`seq=[4, click(8,20), 4, click(8,32), 3, 3, click(40,28), 3, 3, 5]` — fired by body id 3,
levels_completed 2 → 3 on the final FIRE. **Replayed independently in the main thread**
(results/sp80-win-replay.txt): fresh env, L1 recipe + L2_LINE + the 10-action seq, level-up
confirmed on the last action. Run totals: 229,506 expanded, 545,138 states, frontier 315,631 still
growing (the win predates exhaustion — the 300-500k estimate was for EXHAUSTION, the win needed
less), multi_match 13,058 with **13,057 resolved exactly by the size tier and 1 forked** (the fork
path fired once and cost one branch), transfer_no_match 0, all four driver ids fired from
(58k/60k/46k/61k attempts).

**Landed as `L3_LINE` in swap.py** (the win seq in the driver's 4-tuple click format), wired
beside L2_LINE with its own board guard (L3 entry c8=240/c9=96 vs L2's 96/80 — measured, so test
fixtures and other boards fall through to the normal machinery). pytest 330 passed
(results/pytest-l3line.txt). **Full 17-game sweep running as wave-12** — the gate verdict
(sweep_diff vs wave-11, control = sp80 which must differ) decides the landing.

## 2026-08-17 — WAVE-12 GATE: PASS — sp80 L3_LINE lands, mean 22.441% → 23.281%

`sweep_diff.py results/sweep-wave11.log results/sweep-wave12.log sp80`:
**16/17 games identical to the digit** (ar25 bp35 cd82 cn04 dc22 g50t ka59 ls20 m0r0 re86 sb26 sc25
sk48 tr87 tu93 wa30), control fired (sp80 differs, comparison not blind), **sp80 (2,6) → (3,6),
actions [16,7] → [16,7,10]**, GAMES THAT LOST A LEVEL: NONE, VERDICT PASS. pytest 330
(results/pytest-l3line.txt). **results/sweep-wave12.log is the new clean gate** (chain: wave-6 →
wave-8 → wave-9 → wave-10 → wave-11 → wave-12).
Standing: **15/17 games with a level, mean 23.281%, sp80 3/6 = 28.571%.**

## 2026-08-17 — sp80 L4: s12 engineered + long chain LAUNCHED (agent + main thread)

`sp80_s12.py` = s11 mechanically adapted (root through L3_LINE, ckpt results/sp80_s12_ckpt.pkl,
control = L3_LINE replay through the resolver — PASS; smoke fresh/resume both pass, resume continues
exactly from FINAL). **L4's body model, re-derived: SIX tracked bodies (colour-9 driver + five
colour-8), in three size tiers of exactly two each — (15,3) x2, (12,3) x2, (9,3) x2.** Every size
duplicated (L3 had one tied pair of four), so the frame-re-read/fork tier carries more load; the
resolver logic is byte-identical to s11's. Long chain launched from the main thread (12 x 3300s cap,
stop early on exhausted/win, log results/sp80-s12-run1.txt). Flagged UNVERIFIED from smoke: ids 0/2
never drove in 803 expansions — sample too small to read as structural.

## 2026-08-17 — sp80 L4: the s12 chain was STOPPED at ~43k expansions — driver_blob_count fired 56,477 times and every one DROPPED a child (main-thread audit)

The counter that stayed ZERO across L3's entire 229,506-expansion run fired on more than half of
L4's expansions (56,477 at 43k expanded), and the handling at all three sites is `continue` — **the
child is silently pruned**. A search dropping >1 edge per node explores a SUBGRAPH: any negative it
reports is void, and a win behind any dropped edge is invisible. Same trap family as the merged key
and the FIRE-transfer bug — runs to completion, reports numbers, flags nothing (the counter is the
only tell, and nothing gates on it).

Why L4 differs (hypothesis, to verify in the fix): 6 bodies on a denser board overlap the colour-9
driver far more often; occlusion can SPLIT the driver blob (count 2) or merge it with a neighbour
(count includes wrong blob), and `driver_blob()` requires exactly one. The fix direction: recover
instead of drop — reunify split blobs / pick by the driver's known size tier / frame-re-read, and
FORK when genuinely ambiguous (the s11 multi-match philosophy applied to the driver reader). A fixed
reader needs a FRESH search — the dropped children never entered `seen`, and their parents are
already popped, so the old checkpoint under-covers by construction.

## 2026-08-17 — sp80 L4: the anomaly is a TWIN-MERGE (a real game state), s13 forks it — chain relaunched (agent `sp80_s13.py`, main thread)

Diagnosis over 149 random trajectories, 3 seeds: **120/120 anomalies are the identical event — after
a control transfer (click/fire), the (9,3)-size body pair (root (8,29) and (20,29)) BOTH render
colour 9 simultaneously.** A genuine twin-merge by direct frame inspection, not occlusion; SPLIT and
MISSING never observed. So L4 has board states with two colour-9 bodies at once — the one-driver
reader was structurally wrong there, and s12's smoke oddity (ids 0/2 never driving) is explained:
every path to them WAS the dropped anomaly. `driver_blob_recover()` tiers: exact-size → split-union
→ dropped_hard (none seen) → FORK ≤3; production smoke: **driver_forked == anomaly count exactly,
driver_dropped_hard=0** — zero silent drops. Control (L3 win replay) PASS; resume exact.
Long chain relaunched fresh (12 x 3300s, log results/sp80-s13-run1.txt). Note the branch factor:
forking on every twin-merge may grow the space several-fold vs the (void) s12 numbers — correctness
first, the census will say.

## 2026-08-17 — m0r0 LEVEL 2 FALLS — the "CLOSED" verdict was hypothesis-scoped, and the hypothesis-free BFS won in 35 seconds (agent `m0r0_b1/b2.py`, main thread)

**The earlier "m0r0 L2 CLOSED for the campaign" closed ONE HYPOTHESIS (the diagonal meeting-cell
col=7 unreachable), never the level** — no hypothesis-free search had ever run. The real-engine BFS
from the L2 root: **WIN at depth 23 — 1,653 nodes expanded, 0 deaths, 0 key divergence, 34.9s.**
Verified twice fresh + a one-action-short control (stays at 1) + an independent main-thread replay
(levels_completed=2 after the 50-action line). Deepcopy fidelity control PASS (first use of this
instrument on m0r0).

Landed as `L2_LINE` in twin.py (SEQ[27:] — the 27-action L1_LINE prefix matches byte-for-byte),
act() wired for lvl in (0,1). pytest 330 (results/pytest-m0r0l2.txt). Sweep wave-13 running.

*The campaign-level lesson, third instance today (sp80 L3, m0r0 L2): a closure is scoped to the
question its instrument asked. "Hypothesis X is impossible" and "the level is unwinnable" are
different claims, and the cheap completeness instrument — a real-engine BFS that reads
levels_completed and needs NO win-condition theory — retires the second claim or wins. Every parked
level whose closure is hypothesis-shaped deserves one BFS pass before staying parked.*

## 2026-08-17 — dc22 L2: BLOCKED with the mechanism named — the panel buttons are multi-state RATCHETS, not toggles (agent `dc22_b1..b4.py`)

L1 recipe = bridge.py's own 25 actions (reproduced x3). L2 fresh characterization: piece (colour 14)
and goal (colour 11) on platforms across two 8-row void gaps; **component-centered click sweep found
exactly 2 real controls of 51 clickable objects** (a coarse-lattice sweep first returned a false
0/121 — the lattice missed the components); deepcopy control PASS; 320 direction presses, no death
observed (negative, not proof). **Root cause of the driver stall: both panel buttons are RATCHETS —
>=7 distinct states in 6-7 presses, no repeat — while bridge.py models a binary toggle and presses
each once per position.** Structurally unsolvable by the current driver, not a search-depth issue.
Next arm (scoped, not run): cycle-detect each button's true period, then BFS keyed on
(piece position, button-state pair).

## 2026-08-17 — cn04 L2: model-free BFS to depth 4 EXHAUSTED, no win — the space is a 4-body product (agent `cn04_b*.py`)

First hypothesis-free evidence on this level (complements, does not repeat, the 191 criteria-ranked
placements): board-keyed real-engine BFS from the L2 root, click alphabet bounded to clickable
OBJECTS (16 targets + 6 verbs = 22 actions/node). **Depths 0-4 fully exhausted — 32,954 actions
tried, 7,878 distinct states, zero wins**; depth 5 truncated by a memory cap; growth steady at
4.3-6.4x per layer = the product-state signature of four freely-overlapping movable bodies. Facts
banked: at L2 entry shape "0" is ALREADY selected (no click needed); bare ACTION6 without click
data dies (the known data trap); centroid click-targeting silently misses concave shapes — click a
member cell (instrument note). Deepcopy control passed 4/4.
Verdict PARTIAL/GROWING — this level needs either a sound reduced key (the ar25 lesson looms: a
merging key reports false exhaustion; any reduction needs a positive control) or goal-directed
pruning, not deeper blind layers.

**cn04 L2 amendment (the background run completed after the first write-up):** final census =
**150,011 actions / 24,387 distinct states / zero wins**, stopped by the script's own
MAX_TOTAL=150,000 node cap at depth 6 (not exhaustion, not the clock). Exact through depth 4,
partial depth 5 (~5,650 of 6,380), fragmentary depth 6 (16,509 states). Throughput measured
~2.7ms/candidate steady. The agent also caught its own log overstating a layer ("expanded 6000" vs
~5,350 actually processed before the cap) and corrected it in the report rather than leaving it.
Verdict unchanged: GROWING/PARTIAL — next lever is a sound reduced key (with positive control) or a
directed search, not deeper blind layers.

## 2026-08-17 — re86 L6: first hypothesis-free BFS — GROWING at 31,609 boards over 12 layers, no win (agent `re86_b1_bfs.py`)

Root built by monkeypatching env.step to halt compete.play at levels_completed>=5 — **421 actions,
matching sweep-wave12's [31,56,66,80,188] sum exactly**, ~38s. Action space = [1..5] only (no
click). Deepcopy control PASS. **86,864 env.step calls, 31,609 distinct boards, 55,256 merges, 12
layers, ZERO wins, zero GAME_OVERs** (the free-re-entry fact stayed unexercised — noted, not
asserted). Stopped by its 300s cap mid-layer-12; per-layer growth bounces 1.1-3.4x with no
consistent trend — neither converging nor hopeless on this sample. Checkpoint = 6,414 frontier
ACTION-PATHS (not envs). The agent corrected its own script's auto-conclusion (a cumulative 0.364
new/expanded scalar claiming convergence) against the per-layer curve — the dedup-hides-growth
precedent applied by the agent itself.
Next: an s11-style chain runner (resume + budget) — the checkpoint has no loader yet.

## 2026-08-17 — dc22 L2: the "ratchet" is bigger than measured, movement is keyed on button B, and DEATH DOES NOT REVERT (agent `dc22_c1.py`)

Corrections to the b-series: **both buttons show no board repeat within 40 presses** (period > 40,
unresolved — "≥7 states" was a floor, not a period). Button A's diff footprint settles to a fixed
box alternating two shapes while the full board still never repeats; **button B's footprint GROWS
one-way** (x1 11→26 over 40 presses) — an extension, not a cycle, in the tested range. Cross-effects:
A and B never touch each other's button regions, but **which arrow is REFUSED rotates with a
period-3 pattern keyed on B's state** (tested across A 0-7). 8x8 movement grid: no single press
reaches the goal from any sampled combo. **NEW: GAME_OVER is reachable at L2 (first at depth 11,
440 dead branches) and measured NOT to revert the board** — first game in the campaign where death
carries persistent state; dropping dead branches is NOT free here (c1 dropped them after the one
measurement — a future search must model post-death boards or justify the drop).
Board-keyed BFS (4 arrows + 2 clicks): **8,023 states to depth 19, 40k-expansion cap, frontier
climbing (903), no win.** Checkpoint results/dc22_c1_ckpt.pkl (paths). GROWING.

## 2026-08-17 — FOUR chained hypothesis-free BFS runs now grind in parallel (main thread)

sp80 L4 (`sp80_s13.py`, twin-merge forking reader) · wa30 L3 (`wa30_b2_l3chain.py`) · re86 L6
(`re86_b2_l6chain.py`, seeded from b1's live ckpt at 28k expanded) · dc22 L2 (`dc22_c2_l2chain.py`,
seeded from c1's 903 frontier paths; **death measured per-process: post-death obs carries an EMPTY
frame — a third outcome beside None/board — env terminates, branches dropped and counted**).
All four: path frontier, atomic checkpoint every 2,000 expansions, budget on the success path,
stop-early on exhausted/win, logs results/<game>-*-run1.txt. The instrument lesson standing behind
this fan-out: today it produced two levels (sp80 L3, m0r0 L2) from closures that were only ever
hypothesis-scoped.

## 2026-08-17 — WAVE-13 GATE: PASS — m0r0 L2_LINE lands, mean 23.281% → 23.841%

`sweep_diff.py wave-12 wave-13 m0r0` on the COMPLETED log: **16/17 identical to the digit**, control
fired, **m0r0 (1,6)[27] → (2,6)[27,23]**, no game lost a level. (An earlier diff run mid-sweep
showed cd82/sb26 as None — a diff against a log still being written reads absence as change; wait
for the sweep's mean line before diffing.) pytest 330 (results/pytest-m0r0l2.txt).
**results/sweep-wave13.log is the new clean gate** (chain: … wave-11 → wave-12 → wave-13).
Standing: **15/17 games with a level, mean 23.841%, m0r0 2/6 = 14.286%. TWO levels landed today.**

## 2026-08-17 — dc22 L2: the EXHAUSTION IS VOID — 73/100 collision pairs diverge, the board key merges hidden state (agent `dc22_c3_verify.py`)

c2's "EXHAUSTED at 28,495 states" does NOT bank. Control 2 (collision-divergence): 6,848 collision
pairs collected across depths 2-12; of 100 sampled — replay both paths, press every action,
byte-compare — **73 produced different successors from an identical board key under an identical
action.** Hard hidden state, the ar25-sel_phase/sp80-offset mechanism, fourth false exhaustion this
campaign caught by a control. Control 1 (L1 positive) was budget-limited (soft fail, 300s not
reaching the depth-25 win) — moot given Control 2's hard result. Scope statement stands (6-action
alphabet; 49 objects' inertness measured only at <=40-press button states).
**A bigger c2 run cannot fix this — it would keep merging.** Next: identify the hidden variable
(candidate: per-button press COUNTS — the refused-arrow rotates period-3 on B's state; the true
periods are >40 and may be pure counters), re-key as (board + carried counters), drive the
divergence sample to ZERO under the new key, THEN re-run the exhaustion.

## 2026-08-17 — dc22 L2: the hidden variable is IDENTIFIED and the sound key validated at 0/100 (agent `dc22_c4_hidden.py`)

Characterization of 30 divergent pairs: **nA/nB identical in every pair — only TOTAL path length
differs (by 1-3 arrow presses)**, every mismatch a single-cell frame diff, and the multi-plane
escape is ruled out (all mismatching frames are single-plane — the variable is genuinely absent
from the render). Validation ladder, each round a fresh collect+replay: board+total%3 → 37/100 ·
board+total_raw → 1/100 (the residual pair: equal length, 0-vs-2 clickA composition) ·
**board + total_len + nA + nB → 0/100 over 3,857 fresh collisions. SOUND.** Size inflation ~1.39x
at comparable budgets. Structural note for c5: in strict FIFO BFS total_len is constant per layer,
so the effective per-layer key is (board, nA, nB) — code-derived, per-depth census NOT RUN.
Key importable: `from dc22_c4_hidden import key_total_raw_plus_nAnB_raw`.
So dc22 L2's game state ticks on a GLOBAL press counter plus per-button counters — the ar25-band
mechanism family, third game in the campaign where history-not-board is real state.

## 2026-08-17 — tr87 L3: first hypothesis-free BFS — GROWING at depth 8, and the level's facts firm up (agent `tr87_b1_bfs.py`)

Root = the settled 58-action L1+L2 line, live-confirmed. **tr87 has NO click verb** (plain [1,2,3,4],
complex empty — confirms actionspace.py). Deepcopy faithful (positive + negative controls).
**Death: ACTION1-spam hits GAME_OVER at 128 actions (row-63 budget bar ~64 units draining 1 per 2
actions); `.reset()` returns levels_completed=2 with a byte-identical L3-entry frame — reset is
scoped to the CURRENT LEVEL, not the game.** BFS board-keyed (frame minus the budget bar), 4 verbs:
depth 8, 6,085 states, 10,084 expanded, no win, growth x2.4-2.5/layer. Stopped by session budget,
not the cap. **Implementation note for b2: the layer loop replays every frontier node FROM ROOT each
layer (O(depth) per node per layer — depth 7→8 cost 99s vs 0.2s at depth 2); the chain runner must
use replay-on-pop or held deepcopy envs.** Checkpoint results/tr87_b1_ckpt.pkl (depth 8, 3,564
frontier paths).

## 2026-08-17 — bp35 L2: the FIRST real search on this game — GROWING, and a nondeterminism red flag that gates everything (agent `bp35_b1/b2.py`)

deepcopy is impossible on bp35 (infinite recursion) so no BFS had ever run; replay-from-reset does
not need it. Root recipe (20-action L1 line) replays deterministically (diff=0 twice); action space
plain [3,4,7] + click [6]; at the L2 root ALL 7 block-clicks ride the piece (L1: most just clear);
death-revert reconfirmed a third time. Replay-BFS: **5,965+ distinct boards, frontier growing, no
win** — two stages, 24,542 nodes total. Two instrument bugs caught+fixed (Arcade().make per node =
~1s network each; root hash pre-seeded into visited silently blocked all children).
⚠️ **GATING CAVEAT: the two runs — identical method — disagree on death counts (91 vs 0) over
overlapping node ranges. Something past the root is not run-to-run reproducible even though the
root path is.** Under replay-from-reset, nondeterminism poisons every path's identity — no bp35
search verdict banks until this is settled: either (a) find the RNG/state source and pin it, or
(b) prove the discrepancy was a script difference (the two files handled deaths differently), or
(c) demonstrate divergence with one script on one path replayed twice — which would retire the
replay-BFS instrument on this game entirely.

## 2026-08-17 — bp35 L2: determinism verdict MIXED — the ENGINE replays byte-identically; the 91-vs-0 suspect is a PRE-USED SHARED ENV (agent `bp35_b3_determinism.py`)

(c) 3x-replay grid: **20/20 paths (depths 5-40, incl. both death paths) byte-identical across three
fresh-reset replays each — zero divergence, death indices matching every time.** (b) static diff:
death classification functionally identical between b1/b2; the real asymmetry is that b1 ran ~30
characterization replays + a live death/reset on the SHARED env before its BFS — candidate
mechanism for its 91 deaths, unproven. Verdict MIXED: the replay-from-FRESH-RESET instrument shows
no crack anywhere it was probed; b1's counts stay quarantined. Practical rule for any bp35 search:
every replay from a virgin env.reset(), never a pre-used env — then the instrument stands on the
b3 evidence.

## 2026-08-18 — bp35 L2 chain: 543k expanded / 115k real states — the 79% dup rate is STRUCTURAL, not a bug (main-thread audit)

b4's lazy dedup (visited-check on pop, after the replay) looks wasteful — 543,332 expanded vs
115,016 distinct states = ~79% of replays spent on duplicates — but on a game with NO deepcopy it
is near-optimal: a child's board is unknowable without stepping to it, stepping requires the
replay, and eager child-keying would cost |children|x|path| re-replays per node, roughly the same
arithmetic. The frontier (543k paths) is RAM-heavy but sound. Implication: when novel states dry
up, draining the dup-laden frontier to prove exhaustion costs ~2-3h of pure dup pops at ~65/s —
budget for it before reading "frontier still large" as "far from done". Chain extended.

## 2026-08-18 — sp80 L4: the twin-merge is DETERMINISTIC — s13's 1.24M forks were pure inflation, fresh search required (agent `sp80_s14_twinmerge.py`)

Across 6 merged states (3 byte-identical reproductions): **arrows move BOTH twin members in lockstep
(moved_idx=(0,1), zero exceptions); FIRE resolves the merge deterministically (both revert to
colour 8, driver_blob comes back count==1 on a different (15,3) body — 5/5 valid states); click on
the twin is inert.** UNVERIFIED (flagged): whether fire's selection is provably deterministic
beyond this sample. Verdict: s13's tier-(d) fork was unnecessary — and the fork branches carried
WRONG driver assignments into `seen`, so the s13 chain's 1.6M states / 481k expanded are polluted;
do not quote them and do not resume that checkpoint. s15 = deterministic twin handler (arrows apply
one shared delta to both bodies; fire re-runs driver_blob over the full list), fresh chain.
The pattern to name: **a fork policy is a hypothesis about ambiguity — measure whether the ambiguity
is real before paying exponential rent on it** (this campaign's counters made the rent visible:
driver_forked ~2.6/expansion was the tell).

## 2026-08-18 — KAGGLE: the HYBRID is submitted (55590173, PENDING, 02:26 UTC)

First submission whose predicted score rests on the sample's own baseline (~1.56) + driver
overrides rather than our drivers alone. Verified via `competitions submissions` (the resource).
The 2026-08-17 duplicate v9-lite completed at 0.10 exactly as predicted. Expect the hybrid's
server-side run ~7.3h; read the score at the next session/wakeup, and remember what it tests:
beat 0.11 = the hybrid architecture works and iteration continues there; ~0.10-0.11 = the sample
base did not survive the bundling, debug the goose extraction.

## 2026-08-18 — KAGGLE: hybrid scored 0.05 — WORSE than drivers-only, and the timing says the run DIED

Submission 55590173 COMPLETE at ~1.6h after submit (02:26 → before 04:04 UTC) with **publicScore
0.05** — half of v9-lite's 0.10, against a scoring run that should take ~7h. The v8 signature again:
a kernel that dies partway scores zero for every game after it. Leading suspect class (same as v8's
qstate table): the goose/torch sample base + 14 drivers in ONE process across 110 games — memory.
"A per-unit cost measured cheap is a claim about TIME, never about SPACE."
Decision context for tomorrow's single submission: v1 (0.11, no drivers) remains the best score;
drivers-only ceiling ~0.10-0.11; the hybrid only beats that if the death is found and fixed
LOCALLY first — never spend quota on an unreproduced fix again (two quota-days lost to
untested-bundle classes so far).

## 2026-08-18 — KAGGLE INTEL (results/kaggle-intel-20260818.md): our instrument family took 2nd in the preview — and the scoring rewards COMPLETION over polish

Key findings (sources in the intel file): the goose baseline (RL/CNN legality+frame-change
predictor, ~12.58% preview) is ARC Prize's own documented dead end ("good exploration, poor
conversion"); Tufa's current line is an LLM-in-REPL, but **scoring runs with NO INTERNET** —
hosted-API approaches are out. The 2nd-place preview finisher ("Blind Squirrel") is a
**deterministic state-transition graph + pruning agent — the exact family this campaign has been
building for two days** (board-keyed real-engine search, sound keys, divergence controls,
action-effect models). "Executable World Models" (best-quantified academic entry) = same family +
simplicity bias. Scoring confirmed: quadratic in action-efficiency but ZERO for unsolved levels —
**complete more levels first, polish later**. NOT FOUND/unverified: the 240s/game clock (our
adapter's assumption!), specific OOM reports, what the current top-5 handles actually run.

**The decisive unknown: is v1's 0.11 the true strength of compete.play on hidden games, or has the
ADAPTER been dying early on every submission?** (v8's recorded 120s-timeout worker death; the
hybrid's 1.6h COMPLETE.) If the adapter dies, our true score is unmeasured. The crash-test in
flight answers the hybrid's half; the same audit must cover the compete adapter before we write off
the generic rungs. Strategy: bank a working base tonight, then port the campaign's graph-search
machinery into a GENERIC agent (the Blind Squirrel path) — our comparative advantage is exactly
there.

## 2026-08-18 — HYBRID DEATH REPRODUCED: the adapter leaks one permanently-blocked thread PER CLAIMED GAME (agent `kaggle_hybrid_crashtest.py`)

Mechanism, traced not hypothesized: `kaggle/adapter_hybrid.py` runs compete.play on a worker thread
behind a queue proxy; **the reply to the worker's LAST step()/reset() is only delivered at the top
of the NEXT choose_action — and Agent.main() checks is_done() first and exits when the terminal
frame arrives, so that reply is structurally never sent.** The worker blocks forever on an un-timed
Queue.get(), un-joined: **28/28 claimed game-runs leaked a daemon thread** (even sb26's WINs — not
a timeout artifact), RSS 251MB → 2,639MB post-GC across one 35-run local sweep. On Kaggle's 110
games this kills the run partway = the 0.05 / 1.6h-COMPLETE signature, and likely suppressed every
driver-carrying submission (consistent: v1 with NO drivers = 0.11 is our best).
Fix (ranked in the report): deliver the terminal reply unconditionally before is_done() can end the
loop; join/kill the worker on teardown; re-verify with the SAME crash-test harness (0 leaked
threads, flat RSS) before spending tomorrow's quota.

## 2026-08-18 — g50t L1 IS WINNABLE — squirrel v1 cleared it on its FIRST eval, overturning the campaign's "closure by exhaustion" (main-thread verified)

The generic online graph agent (squirrel.py, built this afternoon for the Kaggle score push)
cleared g50t L1 at agent-action 156 in its 17-game eval — and the main thread reproduced it
independently (seed 0, results in-session). **The 2026-08-16 exhaustion proof (1,854 boards,
frontier 0, "g50t is 0/7 and stays 0/7; spend no more rounds") is the campaign's FIFTH false
exhaustion.** The proof searched a SINGLE life and dropped GAME_OVER children after measuring one
death revert; squirrel's winning line passes through RESETS — multi-life states the BFS never saw
(or the f[-1] keyhole the proof's own qualification flagged). Reproduction + mechanism
characterization + landable-line extraction in flight (g50t_w*).
*The instrument lesson, sharpened: an exhaustion proof inherits every scoping assumption of its
root and its dropped children — and the cheapest refuter turned out to be a domain-blind agent
that simply did not know the level was "closed".*

## 2026-08-18 — WAVE-14 GATE: PASS — g50t L1 lands (0/7 → 1/7), SIXTEEN of seventeen games now hold a level

`sweep_diff wave-13 wave-14 g50t`: 16/17 identical to the digit, control fired, **g50t (0,7)[] →
(1,7)[26]**, no game lost a level. The 26-action line found by the domain-blind squirrel agent —
through a level closed by a false exhaustion proof — is now `glide.py`, wired into compete.py's
dispatch (import + one rung after twin), pytest 330. **results/sweep-wave14.log is the new clean
gate.** Only sc25 remains at 0 (its closure is the absorption-mechanics one — completeness-shaped,
but the g50t lesson says: let squirrel take a swing at it too).

## 2026-08-18 — squirrel v2: an honest regression — and the g50t win is revealed as LUCK the fixed ordering stumbled into (agent)

v2 (HUD-union mask, novelty shuffle, farthest-frontier jump, absorption guard) scores **0.000%**
vs v1's 0.053% — it loses g50t's 1/7, and 13 seed-combination diagnostics pin the cause: the
seeded SHUFFLE replaced the fixed action ordering that had lucked into g50t's 26-action line.
(No campaign loss — the line is already glide.py/wave-14.) sc25: absorption guard fires, 3 seeds x
2000 actions, still 0/6. **Read honestly: blind-exploration tweaks are not the lever; the g50t win
was a lottery ticket, not a capability.** Squirrel iteration PAUSED until v12's score lands —
if the fixed adapter restores the goose base (~1.5), the next work is goose-side; if v12 stays low,
bundle forensics first. The local generic-agent crown stays with compete.play's rungs.

## 2026-08-18 — KAGGLE INTEL 2 (browser, primary sources): the milestone winner's FULL CODE is public — and the road to 2.35+ is a Duck fork with better tools

From the competition's own discussion threads (read live):
- **Milestone-1 winner = Tufa's "Duck Harness"** (successor to Goose, authors incl. Jeroen Cottaar):
  **Qwen 3.6 27B FP8 in a Python REPL** — game state exposed as Python variables, agent iterates
  reason→tool→act, oldest context evicted to play indefinitely, multimodal frame input + ASCII
  grid + a segmentation tool. Best official 1.21 (variance 0.77-1.3, σ≈0.4 on public games).
  **Code fully open**: kaggle.com/code/jeroencottaar/taaf-duck-harness-kaggle (lucky-score) and
  …-kaggle-share (recommended base); agent code attached as a Kaggle dataset.
- Kaggle env per their writeup: **RTX Pro 6000, 96GB VRAM, 9 HOURS for 110 games** (not T4/7.3h —
  our build_notebook currently pins accelerator: t4; the upgraded-accelerators thread confirms).
- Referenced approaches: **Symbolica "ARCgentica" hit 36%** with frontier models (offline-infeasible);
  **RGB Agent** = generic coding harness (OpenCode), near-human action efficiency, full-history log
  + grep pattern. Today's top5 (2.35+) most plausibly = improved Duck forks post-open-source.
**Strategy consequence: our goose/hybrid line is chasing a superseded baseline.** Plan: (1) v12
tonight unchanged — it validates OUR adapter fix cheaply; (2) fork duck-harness-share, run it
locally/commit-run, bank ~1.0-1.2; (3) the top-5 differentiator = inject this campaign's measured
mechanics as REPL TOOLS for the LLM (component click enumeration, transition-graph builder,
level-clock/budget awareness, absorption guard) — the Duck writeup's own thesis is that the harness
wins by giving the model better hands, and two days of instrument-building is exactly that.

## 2026-08-18 — Duck fork LIVE: sahasawatt/taaf-duck-fork v1 pushed (RTX Pro 6000), source bundle pulled locally (main thread)

Pulled the milestone winner's notebook (jeroencottaar/tufa-labs-duck-harness-june-30-milestone-
winner, public score 1.25) + its TAAF source dataset (duck/bundle/src: ARC3-Inference +
tufa-arc-agi-framework — the whole agent, Apache 2.0). Forked under our account with identical
inputs (vLLM wheelhouse, TAAF source share, Qwen3.6-27B-FP8 snapshot), machine NvidiaRtxPro6000,
internet off. Commit run in flight (~2.4h expected).
**Tomorrow's window decision (one slot): duck fork (proven-family ~1.25) vs v12 (validates our
adapter fix, uncertain score). Score-first goal → duck takes the slot if its commit run is clean;
v12 slides.** After banking: differentiation = our campaign mechanics as REPL tools inside TAAF's
harness (the src is now on disk to study).

## 2026-08-18 — TAAF harness mapped (results/taaf-study-20260818.md): one python tool, injected names, a never-evicted prompt, and a Customization hook

Study highlights (file:line refs in the report): the notebook is infra-only — the solver arrives as
a pickled HarnessSolver in benchmark_initial.pkl; all logic in duck/bundle/src/ARC3-Inference.
**Exactly ONE OpenAI tool (`python`)**; action()/current_frame/history/segmentation are names
injected into an ISOLATED subprocess namespace (segmentation.py deliberately stdlib-only so its
source can be spliced in). System prompt = 6 constants in prompts.py, permanent messages[0].
Context survives via a token sliding window PLUS an LLM-maintained "world model" prose block that
is regex-reinjected past eviction. Games run CONCURRENTLY (semaphore + pool) with per-game runtime
and shrinking LLM timeouts. Ranked injections: (1) HUD/budget-bar auto-flag (their own prompt names
this trap), (2) online transition-graph builder over history, (3) component-click enumeration
(highest risk — our ka59 evidence says centroids mislead). The notebook's own "Customization hook"
section is the intended mod point. Sequencing: baseline fork must complete under our account first
— one unknown at a time.

## 2026-08-18 — taaf-duck-mod v1 PUSHED: our first modified harness (HUD auto-flag + TransitionGraph as LLM tools)

duckmod/ built + verified locally (results/duckmod-build-20260818.md): the notebook's Customization
hook cell now monkeypatches the sandbox bootstrap (source-splice, anchor-based) to inject
`hud_mask(history)` and `TransitionGraph` (both stdlib-only) plus their docs into the permanent
system prompt. **Instrument catch worth keeping: `from X import NAME` copies the binding — patching
the source module post-import is a silent no-op; the patch must target the importer's global.
Proven with a negative control.** UNVERIFIED: a live LLM turn using the helpers (no local GPU).
Kernel sahasawatt/taaf-duck-mod v1 pushed — commit run (~2.4h + queue) will show mean score vs the
baseline's 1.25 on the same 25 public games. Tonight's slot = baseline duck fork; duck-mod is
tomorrow's candidate IF its commit run's mean >= baseline.

## 2026-08-19 — SUBMITTED: duck-mod (55613165, PENDING) — our tools DOUBLED the harness's public mean (2.41 vs 1.25)

taaf-duck-mod's commit run on the same 25 public games: **mean 2.41 vs the baseline fork's 1.25**
(median 0.08 vs 0.02, actions 3,481 vs 4,090 — fewer actions, more score). The two injected tools
(hud_mask + TransitionGraph, with prompt docs) are the only delta. Submitted at 02:53 UTC
(verified via competitions submissions — the window-miss almost cost the day; the wakeup chain
silently lapsed overnight, caught by the user's "เสร็จยัง" probe). If the public→hidden transfer
holds even at high variance, 2.41-class is TOP-5 TERRITORY (top5 = 2.35+ as of Aug 18).
Score lands in ~7-9h. Next iteration candidates regardless of outcome: injection #3
(component-click enumeration, with the ka59 centroid caveat), tuning the graph advice in the
prompt, and reading duck-mod's own transcripts (duckmodout/transcripts) for how the LLM actually
used the tools.

## 2026-08-19 — duck-mod forensics: the 2.41 is NOT tool adoption — 0 TransitionGraph calls, 2 hud_mask calls, a 2-game effect (agent, results/duckmod-transcripts-20260819.md)

Parsed [TOOL CALL] blocks (not raw grep — the docs repeat per turn and pollute text counts):
**TransitionGraph constructed 0 times in 2,001 tool turns; hud_mask called twice** (both clean, one
inconclusive). The whole +1.16 mean gain sits in ft09 (+22.20) and ar25 (+7.73) — the other 23 games
NET −0.91 — and **neither winning game touched either tool**. Verdict: prompt-priming and/or
single-run variance (documented σ≈0.4/game), not verified capability. Cost found: ~450-500
tokens/turn of tool docs paid ~2,000 times for 2 invocations.
**Design law for the next iteration: an LLM under a 3s/turn budget does not do BOOKKEEPING through
an API — compute it FOR the model and put it in the observation.** v3 = auto-push: every turn the
harness itself computes (a) HUD-masked frame diff summary, (b) state-novelty flag + untried-action
list from an automatically-maintained transition graph, (c) revisit counts — injected as a short
OBSERVATION block, no callable API, zero adoption risk. Ablation option (advice-prose-only) kept as
the control arm if a second commit-run slot is available. The pending hidden score (55613165) is
one more data point, not a verdict either way.

## 2026-08-19 — duck-v3 commit run: mean 0.80 — the auto-push block did NOT help on this single run

Same 25 public games, single unseeded runs: baseline 1.25 · duck-mod 2.41 · **duck-v3 0.80**
(median 0.00, actions 4,336). Three single runs with documented per-game σ≈0.4 cannot cleanly rank
designs — but v3 shows no sign of lift and possible harm (the observation block may distract or the
novelty/untried info may mislead on games where the masked key fragments). Standing decision input
for tomorrow's 00:00 UTC slot: the duck-mod HIDDEN score (55613165, still PENDING) is the next real
datum; candidates = resubmit duck-mod v1 (second sample of the same artifact — averages the hidden
estimate) vs baseline vs a fixed v3. No new submission before that lands.

## 2026-08-19 12:09 UTC — HIDDEN SCORE LANDED: duck-mod = 1.00

- Submission 55613165 (taaf-duck-mod v1) COMPLETE, publicScore **1.00**, rank **585/2409** (median 0.26; 581 teams above, 11 tied at 1.00).
- vs history: ours 0.05/0.10/0.11 → 1.00 = 20x jump, first score above median.
- Public 2.41 -> hidden 1.00: consistent with forensics (results/duckmod-transcripts-20260819.md) — 2.41 was a 2-game public effect (ft09+ar25), priming/variance, NOT tool adoption. Hidden set does not carry it.
- Leaderboard moved: top5 bar 2.35 -> **2.57**, #1 = 3.57 (cstl).
- Decision (tree branch 1.0-1.5): resubmit duck-mod v1 at 2026-08-20 00:00 UTC — Kaggle keeps best score, so a second hidden draw is free upside. Baseline fork (public 1.25) expected lower; duck-v3 (0.80) still barred as-is.
- Strategic read: re-rolls of a ~1.0-mean design cannot reach 2.57. Top-5 requires a design improvement on the duck harness, not another sample.

## 2026-08-19 17:30 UTC — CALIBRATION LANDED: duck-mod identical rerun = 2.16 (vs 2.41 first run)

- taaf-duck-mod v2 (byte-identical rerun of v1) public mean **2.16**, 2h12m, 3,858 actions.
- Run-to-run band for identical code on the public 25: **[2.16, 2.41]**, range 0.25 — first
  direct measurement of aggregate variance (R5's calibration unknown now has n=2).
- Implication for v4's bar: mean >= ~2.1 with a clean log (patches fired, no crashed states)
  = within-band, submit-worthy; anything below ~1.9 = likely regression, hold.
- Also recalibrates the hidden drop: public band [2.16,2.41] vs hidden 1.00 → the public→hidden
  gap is real (~2.2x), not a bad public draw.

## 2026-08-19 18:00 UTC — v4 EVAL: 1.73, BELOW the calibration band -> HOLD; submit duck-mod v1 at the window

- taaf-duck-v4 v2 public mean **1.73**, median 0.04 (calibration band for unchanged code:
  [2.16, 2.41], median 0.25). 25/25 gave_up, 0 crashed — the id() fix works, but the design
  underperforms out-of-band. **Decision: do NOT submit v4; window slot = duck-mod v1 resubmit.**
- Log reads: `compacted:` markers = **0** (the world-model cap never fired — lever inert as
  built); per-game tokens cluster tightly at ~66-90k with gave_up at ~70k, suggesting the
  BINDING per-game constraint may be a token budget, not the wall clock R1 assumed — if so,
  time reallocation cannot help by construction. ft09 dropped 3 levels/28.57 -> 2/14.29.
- v4 artifacts: /tmp/duckv4out2 (v1 crash artifacts: /tmp/duckv4out). Analysis agent launched
  to diff v4 vs calibration per-game and settle the binding-constraint question -> v4.1/v5 spec.

## 2026-08-19 18:25 UTC — R7 POSTMORTEM: v4's levers were mostly INERT; the 1.73 gap is rollout variance

- **Binding stop = wall clock ONLY** (should_stop() solver.py:246-261 has no token check;
  all 75 game-runs across 3 runs end via runtime_limit_reached). The ~70k-token uniformity
  I read as a token budget was correlation (range 37k-91k at the same 7920s cutoff) — my
  hypothesis REFUTED by R7.
- **Reallocator fired correctly** (4 shrinks exactly matching its predicate: cn04 -1779s,
  sk48 -1970s, tr87 -2155s, sc25 -384s; ft09 +625s) but MAX_EXTENSION_PER_GAME_S ==
  TOTAL_POOL_CAP_S == 600 → ft09 alone exhausted the whole pool; other leveling games got
  noise. Shrunk games scored 0 in every run anyway (no measurable cost) — possible
  feedback loop: shrinking deadline also shrinks per-call LLM timeout (tr87 stall 4.6-8x).
- **World-model cap never fired because the premise was wrong at runtime**: fields are
  OVERWRITTEN each turn (tool_agent.py:1109-1111), max observed 3,501 chars < 6000 cap;
  **77.1% of turns wrote ZERO assistant prose** — the world model is mostly EMPTY. This is
  R6's Mode 1 (state amnesia) measured from the other side.
- **The -0.43 vs band = 3 games** (ft09 -13.63, vc33 -5.94, tu93 -4.85); two ran on
  untouched budgets, ft09 got MORE time and still lost levels → dominant driver = rollout
  variance at temp 0.6, not the levers.
- Consequence: v4 ≈ neutral-but-unproven; hold stands (tonight = duck-mod v1). The REAL
  lever per R6+R7 convergence: the state channel itself — v5 (B3) = server-side
  auto-persist/accumulate + auto-pushed transition record, built on duck-mod base.

## 2026-08-19 21:10 UTC — v5 EVAL: 2.43, TOP OF BAND — best public run of the campaign; window slot switches to v5

- taaf-duck-v5 v1 public mean **2.43**, median 0.27 (band [2.16, 2.41]; duck-mod best 2.41).
  0 crashed / 25 gave_up (clean clock endings). Features PROVEN LIVE from transcripts, not
  the stdout log (prompts never hit stdout — checking the log for prompt-injected content
  is a category error): first 10 games alone carry 1,106 PROGRESS DIGEST blocks and 594
  GAME RESET banners. ft09 16.98 (3 levels) + re86 16.67 (3 levels) led the run.
- n=1 — 2.43 vs band top is NOT statistical proof of superiority; it IS proof of
  non-regression + mechanism live. Per score-first EV: tonight's 00:00 UTC slot = submit
  **v5** (hidden draw of the better design, 24h earlier; Kaggle keeps best, so downside
  vs a duck-mod resubmit is zero).
- v5 = duckmod base + accumulating world model + auto-pushed transition digest + reset
  banner (build: results/duckv5-build-20260820.md, artifacts /tmp/duckv5out).

## 2026-08-20 00:05 UTC — SUBMITTED: duck-v5 as 55633845

- Submission **55633845** (taaf-duck-v5 v1, public 2.43) PENDING at 00:02:25 UTC, verified
  via `competitions submissions`. Hidden score expected ~09:00-12:00 UTC (9h envelope).
- Context: duck-mod's hidden draw was 1.00 (from public band [2.16,2.41]); v5's public 2.43
  with the same ~2.2-2.4x public->hidden shrink would land ~1.0-1.1 — the REAL test is
  whether the state channel shrinks LESS (its levers target exactly the failure modes R6
  found, which should be as common on hidden games).

## 2026-08-20 03:35 UTC — v5 CALIBRATION: 2.37 → v5 band [2.37, 2.43]

- taaf-duck-v5 v2 (identical rerun) public mean **2.37**, median 0.30. v5's own band =
  **[2.37, 2.43]** (range 0.06) vs duck-mod's [2.16, 2.41] (range 0.25). Both v5 samples
  sit at/above duck-mod's band top; means 2.40 vs 2.285 (n=2 each — suggestive, not proof).
- Public-sample ledger now: duck-mod 2.41, 2.16 · v4 1.73 · v5 2.43, 2.37.
- Waiting: hidden score of 55633845 (~09:00-12:00 UTC) decides the v6 direction per the
  tree in the brief.

## 2026-08-20 06:00 UTC — codex lanes landed: R8 digest audit + duckv6/hud_semantics

- **R8 (codex read-only, results/wayfinder/R8-digest-audit.md)**: digest bookkeeping
  mechanically CORRECT (15/15 spot-checks: tried=changed+noop, last-5 matches, milestones
  right); reset banner **0/5 false positives** (the 594-fire rate = agents exhausting
  budgets repeatedly, not spam). Weaknesses: ADOPTION thin (10 explicit references total,
  ALL in losing games — the two best runs never cited it; usage is reactive, not
  exploration-control) and the append-only world model preserves superseded beliefs /
  grows into clutter. Top-3 v6 fixes: split `changed` into gameplay vs HUD-only vs unknown
  · make the digest an INTERVENTION (fire advice when thrash detected) not a ledger ·
  typed revised state instead of append-only accumulation.
- **duckv6/hud_semantics.py landed** (codex writer via codex-run.js worktree lane, patch
  reviewed + self-test re-run in main thread, commit a24327f): timer/budget vs goal
  classifier for R6 Mode 4 — and it is exactly the instrument R8's fix #1 needs (its
  region classification feeds the gameplay-vs-HUD split). Not yet wired.
- v6 design now has three converging inputs: R8's three fixes + hud_semantics + the v5
  hidden score (pending) which decides how hard to push this axis.

## 2026-08-20 09:50 UTC — v5 HIDDEN = 0.84; leaderboard stays on duck-mod's 1.00

- Submission 55633845 (duck-v5, public band [2.37, 2.43]) COMPLETE: hidden **0.84** —
  below duck-mod's hidden 1.00 (public band [2.16, 2.41]). Kaggle keeps best → leaderboard
  unchanged at 1.00.
- Shrink ratios: duck-mod ~2.4x, v5 ~2.9x. The "state channel shrinks less" hypothesis is
  NOT supported on this draw (n=1 per design — a single draw cannot rank them either way,
  but there is no evidence of hidden-side improvement).
- Decision-tree branch: <1.0 → re-read R7's hidden-behavior hypotheses before shipping
  anything new. v6's PUBLIC eval (kernel running, done ~11:00 UTC) is still worth reading:
  in-band public + clean log keeps v6 as a candidate, but the public->hidden gap now looks
  like the dominant unknown — two designs with near-identical public bands drew 1.00 and
  0.84 hidden.
- Aug-21 slot leading options (decide when v6 eval lands): (a) duck-mod v1 resubmit —
  second draw of the best-known design, EV of best-kept >= 1.00; (b) v6 if its public run
  is in-band+ AND its log shows the warnings actually change behavior (not just render).

## 2026-08-20 11:20 UTC — v6 EVAL: 1.85, OUT OF BAND LOW -> HOLD; Aug-21 slot = duck-mod v1 resubmit

- taaf-duck-v6 v1 public mean **1.85**, median 0.00, actions **2,802** (v5: 4,000 — down
  30%). 0 crashed / 25 gave_up. Feature audit: advisory warnings fired (74 in 8 games'
  transcripts) but **hud hints fired 0 times** (confidence gate never satisfied on real
  frames) → the changed-split had no confident HUD regions either, so v6's effective delta
  over v5 = the warnings alone. Read: warnings suppressed exploration throughput — fewer
  actions inside the same wall clock is exactly the wrong direction when the binding
  constraint is the clock (R1/R7).
- Ledger of builds vs duck-mod (public band [2.16,2.41], hidden 1.00): v4 1.73 inert-held ·
  v5 [2.37,2.43] public but hidden 0.84 · v6 1.85 held. **duck-mod remains champion.**
- Aug-21 00:00 UTC slot: duck-mod v1 resubmit (second hidden draw of the best design;
  Kaggle keeps best, EV >= 1.00). Before ANY v7 design: read R7's hidden-behavior
  hypotheses (mandated by the <1.0 tree branch) + this v6 lesson (an intervention that
  costs actions must pay for itself in redirected exploration, not just correctness).

## 2026-08-20 12:45 UTC — POLICY: submissions on-demand only (user)

- User: "ไม่ต้องส่งทุกวันก็ได้นะ" — daily auto-resubmit cancelled. A slot is spent only on
  a bar-passing candidate or a deliberate probe (baseline hidden-shrink probe stays listed
  in MAP.md as the candidate probe). Leaderboard holds at duck-mod's 1.00 meanwhile.

## 2026-08-20 13:25 UTC — RIVAL RECON (fan-out): the meta moved to "duck v12"; we rebase

- Kaggle CLI (the angle R3's web sweep couldn't reach) listed competition kernels by
  score: the field runs "arc3 duck v12" lineage notebooks; FOYSAL (leaderboard ~2.23)
  publishes "LB-9 arc3 duck v12 with Qwen 3.8 27B" (141 votes); a v19 lineage exists.
- Their source = public dataset jakobbrggen/taaf-kaggle-source-anim-20260807-anim =
  Tufa's OWN branch feature/animation-awareness (2026-08-07, 5 weeks past our base):
  +noop_guard.py (blocks known no-op actions BEFORE spending env actions — a loop
  intervention, stronger than our v6 advisory), +animation.py (multi-plane frame
  retrieval — the exact keyhole our CLAUDE.md documents: 8/17 games answer with
  multi-plane frames and last-plane reads miss it), prompts/sandbox/solver rewired.
- R13 (results/wayfinder/R13-anim-bundle-diff.md): REBASE not port; anim
  setup_commands.json is byte-identical to ours → the R12 model-swap seam holds; and
  upstream STILL ships max_output uncapped → our R10 cap is an edge they lack.
- FOYSAL's overlay: Qwen3.8 (as a Kaggle Model attachment), regex setup rewrite (same
  seam), offline env hardening, public-eval override (n_passes=1, concurrency 28).
- Built + launched duckv9 = duckmod shell → anim bundle + qwen3-8 dataset + MAX_OUTPUT
  768, duckmod patches dropped (R8 zero adoption + stale patch points). Three-way eval
  in flight: v7 (cap on old base) · v8 (3.8 on old base) · v9 (rebase+3.8+cap).

## 2026-08-20 15:30 UTC — v8 (Qwen3.8 swap) = 3.31 PUBLIC: first run ever ABOVE duck-mod's band

- taaf-duck-v8 v1 (duck-mod base + Qwen3.8-27B-FP8 via setup-command rewrite, R12 seam):
  **mean 3.31, median 1.64**, 2h13m, 0 crashed / 25 gave_up. Model verified from the vLLM
  log: served_model_name = vrfai/Qwen3.8-27B-FP8, weights from jakobbrggen/qwen3-8-27b-fp8
  -hf-snapshot, zero Qwen3.6 references.
- Structural, not lottery: **15/25 games score (vs 13/25)** and **22 levels completed (vs
  19 and 17)** — breadth AND depth up. Actions FELL 3,858 -> 1,946 while score rose, so the
  gain is per-action quality, not throughput (3.8 spends ~2x tokens/action: 2.12M total
  tokens vs 1.56M; generated tok/s 265 vs 196).
- This is the first candidate whose public mean sits outside every prior band; duck-mod's
  band is [2.16,2.41], v5 [2.37,2.43], v6 1.85, v4 1.73. Still ONE run (R9: single runs
  cannot rank designs) — but the level count is a lower-variance signal and it moved too.
- Open: v9 (anim rebase + 3.8 + output cap) still running — if the rebase adds on top of
  the model gain, that is the submission candidate; if v9 < v8, the anim bundle's guards
  cost more than they buy at this model tier.

## 2026-08-20 16:00 UTC — v9 = 0.22 and the CAUSE KILLS R10's top lever: the output cap truncates TOOL CALLS

- taaf-duck-v9 (anim rebase + Qwen3.8 + LOCAL_ANALYZER_MAX_OUTPUT=768) public **0.22**,
  median 0.00, only **255 actions across 25 games** (v8: 1,946), every game gave_up on the
  clock with almost nothing executed.
- Mechanism, measured from transcripts (8 games sampled): **finish_reason `length` 704 vs
  `tool_calls` 68**. The model's action IS a tool call whose payload is python code, so a
  768-token ceiling truncates it mid-XML; vLLM's parser then throws
  (`qwen3coder_tool_parser: ValueError: substring not found`, 87 occurrences) and the turn
  produces NO action. CONTROL (same instrument, uncapped runs): v8 = tool_calls 326 /
  stop 4; duck-mod cal = tool_calls 673 / stop 2 — zero `length` finishes.
- **R10's "hard-cap analyzer output" recommendation is REFUTED as implemented.** Its
  premise (a 1k-token answer costs ~110s at ~9 tok/s) was arithmetically right and the
  remedy was wrong: capping total output truncates the *action itself*, not just thinking.
  Any future version of this lever must bound THINKING only (a reasoning budget), never the
  completion that carries the tool call. v7/v7b (same cap on the old base) are dead by the
  same mechanism — do not run them.
- Confound note: v9 changed three things at once (bundle + model + cap). The cap alone
  explains the collapse, so the anim bundle remains UNTESTED — a clean anim+3.8 (no cap)
  run is the outstanding question, not a settled loss.
- Standing verdict: **v8 (duck-mod base + Qwen3.8, uncapped) = 3.31 is the campaign's best
  and the only candidate** — confirmation rerun next for a band.

## 2026-08-20 16:40 UTC — R16 vs R17 collide, and the resolution is a PROMPT, not a knob

- **R16 (v8 forensics)**: the binding constraint moved but stayed generation-side —
  v8 spends **2.71x the tokens/action** and **2.13x the seconds/action** of the Qwen3.6
  baseline (median 1,262 tok and 127.9 s per action vs 463 / 60.0), and in six sampled
  games **90.2% of generated characters are REASONING** (1,422,859 reasoning chars vs
  155,008 tool-payload chars) with 264/266 completions ending in valid tool calls. The
  model buys better decisions (22 levels in 1,946 actions vs 19 in 3,858) and pays for
  them in deliberation. R16's recommendation: a thinking-only token budget.
- **R17 (feasibility, same day)**: that knob DOES NOT EXIST here. vLLM 0.19.0 exposes
  `chat_template_kwargs.enable_thinking` (binary) and a TOTAL `max_tokens`; the harness
  forwards no arbitrary fields; the 5-weeks-newer upstream adds none. A total cap is
  exactly what collapsed v9. Completion-length distribution from v8: p50 ~1.6k, p90 ~4.6k,
  p99 ~9.5k proxy tokens — so any total cap low enough to save time truncates actions.
- **Resolution (both reports respected):** the diagnosis is R16's, the remedy must be one
  that CANNOT truncate a tool call. Built **duckv11 = v8 + a system-prompt brevity
  addendum** (ask for <~300 words of reasoning per turn, never shorten the tool call),
  output left uncapped. Verified against the real bundle: PYTHON_ADDENDUM 3,817 -> 4,143
  chars through the same global duckmod documented as the only working seam.
- Falsifiable prediction for v11: actions > 1,946, levels >= 22, malformed tool calls stay
  ~0, mean >= 3.31. If actions rise but levels fall, the long reasoning was load-bearing
  and the lever is dead — that outcome retires the whole "cut deliberation" axis.

## 2026-08-20 18:45 UTC — v10 = 4.55 (campaign best) and v8's band lands [2.87, 3.31]

- **taaf-duck-v10** (anim bundle + Qwen3.8, output UNCAPPED): public **4.55**, median 0.96,
  14/25 scoring, **22 levels**, 1,285 actions, 0 crashed. Config verified from the kernel
  log: `SERVED_MODEL_NAME='vrfai/Qwen3.8-27B-FP8'`, `LOCAL_ANALYZER_MAX_OUTPUT='0'`
  (uncapped), and the solver line reads `hard_noop_guard=True, animation_awareness=True` —
  the anim bundle's own features are live. finish_reason over 8 games: tool_calls 317,
  stop 1, **zero `length`** (the v9 truncation is gone, as designed).
- **v8 confirmation rerun**: 2.87 (median 1.26, 13/25 scoring, 19 levels, 1,586 actions).
  So v8's band is **[2.87, 3.31]** — a 0.44 spread on identical code, consistent with R9's
  finding that reruns move materially. Its midpoint ~3.09.
- Ranking on public means: **v10 4.55 > v8 [2.87,3.31] > duck-mod [2.16,2.41] > v5
  [2.37,2.43] > v6 1.85 > v4 1.73 > v9 0.22**. v10 is a single run and needs its own
  confirmation before it can be called better than v8 with confidence — but it beats v8's
  BEST run by 1.24, which is ~3x the width of v8's own band.
- Mechanism read: v10 = v8's model plus the anim bundle's guards. Same 22 levels as v8's
  best run from **34% fewer actions** (1,285 vs 1,946) — consistent with noop_guard
  refusing known-dead actions before they are spent, i.e. the guard converts wasted actions
  into score rather than taxing them (the opposite of what our own v6 warnings did).
- Next: confirmation rerun of v10 for a band; v11 (v8 + brevity prompt) is now the LOWER
  priority arm — the same brevity idea should be re-cut on the v10 base if v10 confirms.
