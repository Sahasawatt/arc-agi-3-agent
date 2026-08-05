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
