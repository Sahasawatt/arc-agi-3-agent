# arc-agi-3-agent

An agent for [ARC Prize 2026 — ARC-AGI-3](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3).
Open source from the first commit (MIT-0), which the competition requires for prize
eligibility anyway.

## Where this is

The loop is closed and it is getting through levels. Playing under the competition's own
rules — one `make()`, no rewinding — the agent clears **`ls20` levels 1 to 6 with no
human in it**, in 23, 45, 99, 178, 292 and 844 actions against human baselines of 22,
123, 73, 84, 96 and 192. Level 2 is inside the 1.15x cap so it scores the maximum 115,
and the game stands at **23.528%**. Level 6's changers turned out to be objects
PATROLLING the corridors — the planner that cleared it BFSes over position × patrol
phase × panel, and taught itself the glyph alphabet one deliberate press at a time
([the section below](#the-sixth-level-falls-the-changers-were-patrolling-all-along)).

Neither level is a bigger maze. Both are **locks**. Level 2 draws a glyph inside the goal box
and shows another on a plate in the corner, and refuses the piece until they are the same.
Level 3 does it with **two halves at once** — the ink colour and the shape, moved by two
different squares twenty actions apart — on a board where the refills that make the walk
possible only come back when a life is lost, which also resets the display. `gate.py` reads
all of that off the frame without being told any of it and `compete.stage` searches the order
to walk it in; the [sections below](#the-second-level-is-a-lock-not-a-longer-maze) are what
that cost to get right.

**Measured so far, on public game `ls20`:**

| Approach | Result |
|---|---|
| random actions, 5 seeds × 200 actions | 0 levels, every seed |
| local LLM (`qwen2.5:7b`) on the raw 64×64 grid, 200 actions | 0 levels |
| local LLM on an object-level scene + movement feedback, 3 × 200 actions | 0 levels, but 25–34 blocked moves vs random's 39–75 (non-overlapping) |
| map read off one frame + BFS + budget-aware routing, driven by hand | level 1 in 14 actions; a level-2 route was recorded but **does not reproduce** — replaying `NOTES-ls20.md`'s sequence reaches the refill and ends 54 actions in with the level still uncleared |

Level 1 caps its per-level score. The level-2 line is why the recorded sequence is worth re-deriving rather than trusting: it was written down from a session, not replayed back.

## The rules, read late

Everything above this line, and everything below it that names `play.py`, was measured in a
mode the competition does not offer; [`docs/competition-rules.md`](docs/competition-rules.md)
records why with sources. The `compete.py` numbers are the rules-legal ones.

The load-bearing rule: competition mode permits **one `make()` per environment** and turns a
game reset into a **level reset**. The search in `play.py` reaches a state by resetting and
replaying a prefix, thousands of times per level — after level 1 is cleared, that replays
level-1 actions against the level-2 board. It would not fail loudly; it would evaluate
nonsense. **Treat every `play.py` number here as an upper bound from a permissive dev mode,
not as a competition score.**

A correction while we were at it: the "5x human median" action cap we briefly believed in is
from the technical report's own evaluation protocol, not from the competition rules, which
document no action cap at all — only 600 RPM.

## Playing by the rules turned out to be better, not worse

`compete.py` plays the way competition mode actually allows: one `make()`, no rewinding, the
only reset the one the engine forces when a run ends. It was built expecting to score worse
than the search — and it clears **four times as many levels**.

| | levels cleared | mean over 17 environments |
|---|---|---|
| `play.py` — search that resets and replays to evaluate | 1 game (`ls20`) | — |
| `compete.py` — forward only, rules-legal | 4 games (`ar25`, `ls20`, `m0r0`, `cd82`) | 0.120% |
| **the same, once it can read a glyph, a clock and a moving floor** | **the same 4 games, and `ls20` four deep** | **0.950%** |

| game | levels | actions | baseline | score | |
|---|---|---|---|---|---|
| `ls20` | **4** of 7 | 39, 45, 109, **306** | 22, 123, 73, 84 | **15.233%** | was 1.136% |
| `m0r0` | 1 of 6 | 73 | 30 | 0.804% | was 74 |
| `ar25` | 1 of 8 | 173 | 32 | 0.095% | |
| `cd82` | 1 of 6 | 1,034 | 55 | 0.013% | was 812 |

Level 2 at 45 actions against a baseline of 123 is inside the 1.15x cap, so it scores the
maximum 115; level 3 at 109 against 73 scores 44.9 and level 4 at 306 against 84 scores 7.5,
which is where the upside now is — the same level in 78 actions would take the game to
**30.6%** against a 35.7% completion ceiling.
No game has lost a level along the way, which took some doing: seven separate rules that
were right on paper each cost a different game its own, and are written up below.

**The rewind was not just illegal, it was harmful.** Evaluating a candidate meant resetting
and replaying a prefix, which threw away every state change the level had accumulated — the
pickups collected, the switches thrown. Games that need progress to accumulate cannot be
solved by a searcher that undoes it between every guess. Forward-only play keeps it, and
that alone is worth three extra games.

### Reaching for level 2, and not getting there

Three changes aimed at the second level, all measured, none of which moved it on their own.
They are kept because each turned out to be load-bearing later: the model is now **carried
across a level boundary** rather than rediscovered (the mechanics do not change within a
game, and rediscovery spends actions where the weights are highest); a **refill is detected**
by the clock jumping the wrong way, since a clock only falls and a rise is an event caused by
whatever vanished on that step; and a refill is distinguished from **losing a life**, which
also restores the clock — only a step the piece actually walked can be a pickup. Without that
last filter the detector marked `ls20`'s own level marker as a refill.

Carrying the model briefly cost `m0r0` its level, through a regression introduced while
making it: locating the piece by appearance works across boards and is worse on the board
that built the model, so track ids come first and appearance is the fallback.

The mean is lower than the 0.456% reported elsewhere in this README for three separate
reasons, all of which make it more honest: the completion cap is now applied, the average is
over all 17 playable environments rather than 9, and legal play spends more actions (39
against 13 on `ls20`) because it cannot rehearse.

## The second level is a lock, not a longer maze

Everything above walks to things. `ls20` level 2 will not let you, and the reason is drawn on
the board in plain sight:

- a glyph sits inside the goal box, and a plate in the corner shows the glyph the piece is
  currently wearing. They differ, and the box **physically refuses the piece** until they
  match — it is not a scoring rule, the move simply does not happen;
- walking onto a white cross turns the corner glyph a quarter turn, and turning it twice
  means stepping off the square and back on, because it is *entering* that counts;
- a life is 21 actions. The cross is 17 from the start and the goal box is 20 from the
  cross, so **no life reaches both** — the two yellow squares that refill the budget are
  what make a route exist at all.

`gate.py` reads that off the frame knowing none of it. A **plate** is a region with its own
colour all the way round and a shape drawn inside; a plate whose shape *changes* is a
**display**, because it reports state rather than being a place; whatever the piece was
standing on when a display changed is a **changer**; and a target wearing a shape no display
is showing is **locked**. `perception.icon` does the comparing, and it already handled the
part that makes this hard — the indicator is drawn at twice the goal marker's scale, so
shapes are trimmed to their own bounding box and runs of identical adjacent rows and columns
are collapsed before anything is compared.

A plate is also **promoted into the candidate list** past the rarity ordering, because there
are only ever one or two of them and rarity ranks by colour: `ls20` level 3 paints its goal
box in the colour that also draws the border and the status strip, so it sorted tenth of
twelve and was never considered.

And a plate is remembered as **(ink colour, shape)**, not shape alone, because both are part
of what it says — see level 3 below, where the two halves are moved by two different squares
and reading only the shape sends the piece to a door in the wrong colour.

Each changer's **cycle** is learned the same way: which value it turns each half *into*,
recorded from what it was seen to do. The planner used to price a changer at "walk there,
plus two actions in case it needs one more turn", which is why it kept arriving with the
wrong half showing — on a real run it answers **two** turns 217 times against one 144 times.
A value the changer has never been seen to produce answers nothing, and the old assumption
of one turn is what it falls back to.

That turns the level into an ordering problem, which is what `compete.choose` now is: a door
the display says is open outranks everything, because walking anywhere else can only close
it; a door out of reach is a door to refuel for; a refill is taken while it is still
*reachable* rather than when the tank reads low; and the display is only worth turning if
this life can still get from the changer to somewhere that keeps it going.

## The third level locks twice

Level 3 was read as the same puzzle as level 2, and it is not. Walking the piece to the box with the
right *shape* showing gets it refused — measured three times by hand and again from the
agent's own run, under the state whose marker its bitmap matches exactly. What shows the
refusal is that **the piece does not move** — the trace has it standing on the same square
with the plan's last action spent.

*A correction, because this README said otherwise until it was checked.* The tell first
written down here was that a blocked move is **not charged budget**, read off one run where
nine planned actions left the clock reading one instead of zero. It is wrong: driven into a
wall twenty times from two levels, **every single blocked press charged the bar**, with an
equal number of walked presses as a positive control charging it too (20/20 and 20/20). The
one-action discrepancy that suggested otherwise was a plan that ended early, not a free
press. The claim was load-bearing for how a refusal was told from starving, so it is
retracted here rather than quietly fixed — and the thing that actually distinguishes them,
the piece's own position, was in the same trace all along.

What the board was actually saying, found by walking onto the one object nothing had a
story for: **the multi-coloured square recolours the indicator's ink** — 12, then 9, then
14, then 8 — while the white cross turns its shape. The goal box is drawn in ink 9 with a
particular quarter turn, so the lock is **(ink, shape)** and a run comparing shapes alone
arrives wearing the right shape in the wrong colour. `gate.py` now remembers a plate as
the pair, learns **which half each changer moves**, and picks the changer that moves the
half that is wrong.

That is as far as it gets, and what is left is a **planner**. The constraint is sharp: the
display resets when a life is lost and the refills only come back when a life is lost, so
the whole level is one chain of lives on one set of refills. A route exists —
start → far refill (19) → colour-changer (5, ink lands on 9) → near refill (8) →
shape-changer (10, one turn) → one more turn (2) → door (9), which is 21 exactly on the
last life and 53 actions against a baseline of 73. The agent walks it in the wrong order:
it spends the refill 10 actions from the shape-changer on the way *to* the colour-changer,
and the one that is left is 12 away from a leg that needs to be 10. **Which refill is
spent first decides the level**, and `choose` picks one leg at a time.

Two greedy fixes for that were built and measured back out, because a refill is not only
fuel — it is the fuel *for a particular leg*: reserving refills for the rungs that refuel
with a purpose, and firing the take-it-while-reachable rung only before anything is known
to be locked. Both are right about the endgame and both **break the opening**: with
nothing locked yet there is nothing to refuel towards, so the agent never crosses the
board, never stands on a changer, and never learns what the level wants at all. Level 3
went from turning the glyph to circling its own starting square.

So `compete.stage` searches the order instead — over which changer to turn first and which
refill to spend before which leg, keeping only the first action and re-planning after it.
The route it walks is the one the distances predict: far refill, recolour the ink to the
box's 9, near refill, cross, turn, door.

Two things had to be true before it held together, and each was a measured failure first.
**A planned route has to be re-planned every action.** Run blind, it desynchronises the
moment a move is refused — nineteen actions of a route to a refill ended somewhere else
entirely — and re-planning is a handful of BFS on an engine that runs at 2,000 FPS.
**And the planner has to keep its heading when the plan flickers.** The display reads back
differently for one frame, the search finds nothing, and the ordinary rungs fill the gap
by walking to the nearest rare thing — which on that board is the square that recolours
the ink, one step of which undoes the half already set. The agent got to four actions from
the second changer that way, repeatedly. Remembering where the last plan that existed was
walking to, and continuing there, is what turned it into a clear.

Keeping the piece off changers except by deliberate plan is the obvious alternative, and
it was measured twice — outright, and gated on something being locked. **Both cost `ls20`
level 2**, where walking to the changer because it is the rarest thing on the board is how
the first turn of the glyph happens, and where after that turn the goal box is locked and
the cross is the only thing that can unlock it. The two levels want opposite policies from
the same rung; holding a heading gives the planner the wheel without taking the rung away.

Three generic changes came out of getting that far, all measured neutral on every game
that scores: **a plate is promoted into the candidate list** even when rarity ranks it out
(candidates are ordered by how rare their colour is, and level 3 paints its goal box in
the colour that also draws the border and the status strip, so it sorted tenth of twelve
and the gate never saw it); **a changer out of reach is something to refuel for, and which
refill decides the level** (one is 10 actions from the changer and one 18, against a
21-action life and a 9-action walk on to the door); and **the engine overrules the
bitmap** — collapsing runs of identical rows and columns is what makes a glyph comparable
across scales, and it throws away detail, so a door that refuses the piece settles that
state and every untried state becomes worth trying.

One rule was tried and measured back out, for the record: *the changer is a mechanism, not
a destination, so never walk onto it as an ordinary target.* It is exactly right about
level 3, where rarity walks 13 actions to a changer the affordability check has just
refused — and it **costs `ls20` level 2**, where walking to the changer because it is the
rarest thing on the board is how the first turn of the glyph happens at all.

## The fourth level moves the floor

Levels 2 and 3 are locks the piece walks to. Level 4 keeps the lock and takes away the thing
every plan in this repo is built on: **one action is no longer one step**. Walked one action
at a time and compared against what the model predicted, `press 4` at (14, 35) landed the
piece at (19, 45) rather than (19, 35), and `press 1` at (24, 45) landed it at (9, 40) rather
than (24, 40) — carried on past the square it asked for, by multiples of the step size.

Nothing here models that, and nothing needs to. A plan is a sequence of actions aimed from a
square, so the moment the piece is somewhere the model did not predict, every action left in
it is aimed from the wrong place — **drop it and plan again from where the piece actually
is**. `compete.slid` is that test, and the case it deliberately excludes is the one that
matters: a piece that did not move *at all* is blocked, and its plan still holds, because
dropping the plan there is the rule that already cost `cd82` its only level. Blocked keeps
the plan; carried does not.

Three measurements came out of it, in the same run. It is worth 203 → **109** actions on
level 3 and 74 → **73** on `m0r0`, because both had been walking routes that quietly stopped
being true. It costs `cd82` 812 → 1,034 — its level survives, at a lower score. And it is
what lets level 4's shape half move at all: before, the indicator was read 252 times and
never once changed; after, all four of its shapes appear, including the one the goal box is
asking for.

Two further steps were built on top of that and both were measured back out, which is the
useful part of the round:

- **Planning *through* the slides.** If the board carries the piece from a square, remember
  it and route with it — the map is empty on a game with no slides, so it costs nothing
  there. It cost `ls20` its third level. Tightened to require the same square doing the same
  thing **twice** before believing it, `ls20` held and **`cd82` lost its only level**. One
  sighting is a claim about a moment; two is still a claim about a board that is moving.
  Recording the slides is free and reading them is what does the damage.
- **Going to look for the half nothing explains.** Level 4 has two changers, one per half of
  the lock, and rarity keeps returning to whichever was found first — so the ink cycles to
  the goal box's 9 and the shape never moves, or the reverse, and `turns_for` stays empty
  either way so no plan can exist. Skipping squares already known to be changers found
  **both**: `turns_for` went from empty to populated 77 times in one run, and the exact state
  the goal box wants — ink 9 with its own shape — was reached for the first time. It also
  cost `cd82` its level, and level 4 still did not fall, so it is out. It goes back in the
  moment level 4 clears with it.

**Played by hand, level 4 does not even reach its first changer.** Driving it directly —
read the board, pick the waypoints, walk one action at a time and re-plan after every step,
reading the indicator after every entry — the piece failed to stand on the ink-changer once
in sixty consecutive steps. So the problem is not a stale plan. The plan is wrong when it is
made, because the router does not know where the floor will put the piece.

Which makes routing *through* the observed slides the obvious answer, and it was measured
three ways. The first attempt had a defect worth keeping: **losing a life also moves the
piece somewhere the action did not ask for** — back to the start — so a teleport was being
recorded as a property of the square and routed through. Filtering on the clock jumping back
up fixes that, and then the results split by how many sightings it takes to believe a slide:

| | `ls20` | `cd82` | `m0r0` | four-game total |
|---|---|---|---|---|
| do not route through slides | 14.156% | 0.013% (1,035) | 0.804% | **15.068** |
| believe one sighting | 14.156% | 0.053% (520) | **0** | 14.304 |
| require two | 14.156% | **0** | 0.804% | 15.055 |

`cd82` wants one, `m0r0` wants two, and **level 4 falls under neither** — so all of it is out.

**Then the rule itself was measured**, by a run whose whole job was to disentangle it: what
decides the carry is the **destination**, not the source square, the action, the direction of
arrival, the number of repeats, or a counter's phase. The disentangling observation is one
line: pressing *right* from (14, 35) and pressing *up* from (19, 40) aim at the same cell,
(19, 35), and both land at (19, 45). Four alternatives were each varied while holding the
aimed-at cell fixed and the outcome never moved; a wall was ruled out with `walkable` (the
aimed-at cell is open floor), a moving object by diffing the whole object list across nine
frame advances (nothing moved), and a marked floor colour by reading the cells from a frame
where the piece is elsewhere (all plain colour 3, like every other floor cell). Three such
cells were found opportunistically, each with its own constant offset, and a control one step
away from one of them behaves completely normally.

That is why keying the table on the source square and the action never paid: it is one row
per *way of arriving*, so the router almost never has the row it is asking for, while keying
on the destination is one row per redirecting cell and every route through it gets the same
row. Re-keyed that way and re-measured, it still splits the same three ways — one sighting
helps `cd82` and costs `m0r0`, two sightings never accumulate inside the budget and change
nothing at all, and level 4 falls under neither. So it is out again, and what is left is the
part worth having: the mechanism is now known, and a deliberate sweep for redirecting cells
is a different and much cheaper thing to build than a learner that hopes to trip over them.
The negative result is the useful part: if a slide were a fixed property of a square and an
action, routing through it would have worked. It did not, so `ls20` level 4's floor depends
on something else — the direction the piece arrived from, or something on the board that
moves. That is the next thing to measure, and it is a different question from the one this
round kept trying to answer.

### What finally cleared it

Two rules, both of them read straight off a measurement rather than reasoned into existence.

**A map may never remove a route.** Six redirecting cells learned by accident cut the
reachable board from 67 squares to 57 and put *both* glyph-changers outside it — while the
agent had demonstrably stood on both. An incomplete map is not a smaller truth, it is a wrong
one, so `route_to` uses the map when it finds a way and falls back to the plain model when it
does not. Walking the route the model believes in is also what maps the cells along it, and
those are exactly the cells that route needs.

**A cell has to be confirmed on purpose.** Trusting one sighting routes through phantoms and
costs `m0r0` its only level; waiting to trip over the same cell twice never happens, because a
redirect drops the plan and the next route goes elsewhere — measured, the confirmed map stayed
empty for an entire run. So when something is locked and the map has an unvouched-for cell in
it, the agent walks back and re-aims at that cell deliberately, to find out whether it is the
way through or a phantom. It fires **only on a board that has a lock**, which is why `m0r0`,
which has no display at all, never reaches it and keeps its level.

That is the whole difference between 3 of 7 and 4 of 7. Level 4 falls in 306 actions against a
baseline of 84 — a long way from the 78 that would cap it, and most of the excess is the
sweep, which is the honest price of a board that does not move the way it looks like it moves.

### Where level 4's 306 actions actually go

The obvious suspicion is the sweep — walking back to re-aim at cells costs actions and buys
only knowledge. Measured, it is **35 of the 306, across three probes**. The cost is the
churn: **784 actions were issued inside plans and 306 were walked**, so three in five were
aimed from a square the piece had already been moved off.

That points at committing less, and committing less is wrong. A plan is now carried with the
squares it is aimed from (`compete.trajectory`) and checked against the piece's real position
before every action, which is free and correct; but truncating each plan to a single action
on a carrying board took `ls20` from **4 of 7 down to 2 of 7**. The reason is small and
specific: turning a display means stepping off the square and back on, and that is a
two-action plan — cut it in half and the glyph never turns at all.

So the saving is not in walking shorter. It is in the first plan being right, which means a
wider sweep earlier — and the sweep now looks cheap enough to afford one, at roughly a dozen
actions per cell settled.

The same trace also explains an earlier reading. `infer_dirs` on level 4 had reported "up" as
`(-10, -5)`, which was written off as a frame that lied — it was measuring a slide, correctly.

## The fifth level was played by a stray pixel

Level 5 is not cleared. What it produced instead is the flattest bug in the project: for 352
planning rounds the agent walked a board that was not there.

The symptom was a livelock. The piece appeared to sit in a three-square pocket at
`(15, 37)`, `(20, 37)`, `(25, 37)`, planning a twelve-action route to the glyph-changer every
round and never arriving. A map of the floor cells that carry the piece was learned — twelve
of them, each confirmed twice — and it collapsed the reachable board from 70 squares to 3.
Every escape from the row bounced straight back into it.

Two rules were built to break the livelock and both were measured back out again:

- **Fire the carry-confirming probe wherever the floor carries the piece**, rather than only
  where a lock is known. The reasoning was that the lock cannot be seen until a changer has
  been entered, entering one needs a route that survives the carry, and gating the probe on
  the lock switches off the thing that would make that route exist. It cost `cd82` and
  `m0r0` their only level outright — 0/6 each.
- **Fire it once the walk is visibly thrashing** — N plans dropped mid-route without
  arriving. Tuned to fire early it cost `ls20` level 4; tuned late enough to leave level 4
  alone it made no difference to level 5 either, at any threshold. It bought nothing and was
  deleted.

Both were treatments for a symptom. What made the pocket was that `y = 37` is not on the
board's lattice: the piece moves five cells at a time and every real position it has ever
occupied is `y ≡ 0 (mod 5)`. The thing at `(20, 37)` was never the piece.

A level boundary resets the evidence, so the first model rebuilt on the new board is inferred
from one or two actions — and one action was enough for `infer_player` to name a stray 1x1
pixel of colour 1 as the player. `dirs`, `blocking` and `parts` all already had carry-over
rules for exactly this reason; the piece's **identity** did not, because until level 5 no
board had offered a convincing enough decoy. `keep_identity` adds it: what the piece looks
like is a property of the GAME, so the previous level's reading wins any disagreement, unless
it can no longer find its own piece on this board — which is the one case where the game
really has changed the piece underneath it.

The size is half of that identity and needed checking separately. With `parts` alone
arbitrated, level 5 produced a model that agreed about the piece's components and still
reported its box as 1x1. `walkable` tests a w-by-h footprint, so a 1x1 box makes the entire
board look passable: the clock came back unreadable in 560 of 618 rounds, no refill was ever
found, and 574 rounds produced no plan at all.

With both halves arbitrated, level 5 stops hallucinating and starts playing:

| | before | parts only | parts and size |
|---|---|---|---|
| planning rounds spent | 352 | 618 | 281 |
| squares actually stood on | 3 | 12 | 11 |
| times the display was seen to change | 0 | 4 | 21 |
| rounds that produced no plan at all | — | 574 | 46 |
| rounds where the clock was unreadable | — | 560 | 0 |

It still does not clear it. The lock is read correctly now — the goal box wants ink 8 and the
panel reads ink 12, and `locked=['c8']` in nearly every round — but only the *shape* half ever
turns. The piece never crosses the middle of the board: it lives at `x ∈ {9, 14}` on the left
and `x ∈ {39, 44, 49, 54}` on the right, and the ink-changer sits at `x 30-32`. Two carrying
cells fence the gap, `(39, 25)` throwing the piece twenty cells up and `(34, 20)` ten cells
right, on a level that allows 21 actions per life — 84 units of bar at 4 per action — against
a 96-action human baseline.

One more bug fell out of the same trace and would have crashed any run that got this far: the
rung that walks to a changer picks one into `turn` and then measured the rest of the trip from
`gate.changer`, the last changer *observed*, which is `None` until one has been. It had never
fired before because no level had reached that rung with an unobserved changer.

### What level 5 turned out to need, and what it still does not have

Playing it by hand settles the shape of it. The goal box asks for `(ink 8, #.#/##./.##)`; the
panel starts at `(12, .#./##./.##)`, so both halves are wrong. The board has one ink-changer
— a five-colour cluster at `x 30-32, y 26-28`, entered from `(29, 25)` — whose ink runs
`12 → 9 → 14 → 8` on a four-cycle, and **two** shape-changers: a white cross at
`(20-22, 11-13)`, entered from `(19, 10)`, and a second blob at `(16, 36)`, entered from
`(19, 35)`. Fuel is 84 units at 4 per action, so a life is 21 actions, and there are three
refills — one beside each changer and one beside the goal box. **A death puts the whole
panel back**, measured directly: the shape reverted to its starting value on the action the
piece starved. So the sequence has to run without dying, on a floor that carries the piece
from eight known cells.

Three things were wrong in the agent, all fixed and all measured neutral on every other
game and level:

- **The two shape-changers have to be interleaved.** Walked on its own the cross cycles six
  states and the blob four, and the glyph the goal box asks for is in neither — it exists
  only in what the two reach together, which a plan that walks one changer's own cycle
  cannot express. `Gate.leg_for` searches every changer's transitions at once and returns
  the first leg; `presses_for` remains the single-changer reading.
- **The glyph normal form was not injective.** Collapsing runs of identical adjacent rows
  and columns is scale-invariant, and it has to be — the panel draws at 2x — but it maps
  `#.#/#.#/###` onto `#.#/###`, and level 5 draws both. Dividing by the scale the glyph is
  actually drawn at, the gcd of every run length in the bitmap, keeps the invariance without
  the collision.
- **A changer is credited to wherever the piece was when the plates were last read**, and
  they were read once per plan. On a level whose routes run a dozen actions that put both
  shape-changers on the refill the piece happened to be walking past: neither square that
  writes the shape was ever learned. Reading them after every action fixed the credit —
  `(19, 10)`, 78 times, against 21 display changes seen before.

None of it clears the level, because the ink-changer is still never reached. It sits behind
one cell, `(34, 5)`, which throws the piece twenty cells down to the changer's doorstep;
without that cell in the map the changer is unreachable, so every route goes elsewhere and
the cell is never learned. Walking to the nearest square the piece has **never stood on** —
"unknown" cannot mean "not reachable", because a cell whose carry has not been seen looks
like ordinary floor and is already inside what the map thinks it can reach, which is why a
frontier defined that way came back empty 280 times in a row — takes the squares actually
visited from 11 to 35 and finds both shape-changers, and still runs out of budget before the
ink cluster.

### Level 5, played by hand: cleared in 98 actions

The agent does not clear it. Driving it by hand does, in 98 actions against a baseline of 96,
and what that took is worth more than the number.

The board asks for `(ink 8, #.#/##./.##)` and starts at `(12, .#./##./.##)`. Three squares
write it. The five-colour cluster at `x 30-32, y 26-28`, entered from `(29, 25)`, runs the ink
`12 → 9 → 14 → 8` and touches nothing else. The white cross at `(20-22, 11-13)`, entered from
`(19, 10)`, walks an alphabet of glyphs — the cell count changes, so it is not a rotation. And
the blob at `(16, 36)`, entered from either `(14, 35)` or `(19, 35)`, **turns the glyph ninety
degrees clockwise**: four measured edges agree exactly, which makes how many entries it needs
arithmetic rather than search. The goal box's glyph is `##./.##/#.#` turned twice, and
`##./.##/#.#` is two entries of the cross away from the start. So: cross twice, blob twice,
ink three times, then the door.

Five things had to be right at once, and each was found by getting it wrong first:

- **A death resets the whole panel.** Fuel is 84 units at 4 per action — 21 actions a life —
  and there are three refills, one beside each changer. The sequence has to survive on one
  chain of lives, which is why the run that reached the goal glyph at action 85 and starved
  at 110 scored nothing at all.
- **Routes between changers cross changers.** Walking from the cross to the blob steps over
  `(14, 35)`, which turns the glyph, and refuelling at `(9, 10)` crosses the cross twice —
  once each way. A plan walked to its end is a plan built on a panel that has changed under
  it; the decision has to be re-made after every single press.
- **A refill behind a changer is not a refill.** The nearest one to the cross costs two
  unwanted entries per visit and undoes the glyph it was fetched to protect.
- **The door is inside the box, not against it.** `(54, 10)` clips the frame's bottom row and
  does nothing; `(54, 5)` is inside. `footprints_touching` already knows this — it is the
  hand-driver that had to learn it.
- **The goal box covers its own glyph.** The piece is 5x5 and the box is 7x7, so walking in
  hides what the box is asking for, and `plates` stops reporting it *exactly* when it starts
  to matter. Re-read at that moment, the driver concluded the panel it had spent ninety
  actions setting was wrong and walked away — one press from the door, three times in a row.
  Remembering the last reading is what cleared the level.

That last one is a bug in the agent too, and finding the right form of it took two wrong
ones. Keeping every vanished plate costs `ls20` levels 3 and 4; so does keeping only the ones
never seen to change. Counting the disappearances says why: over a full run there are 19 of
them, none is a display, none reappears under another key — and **only 13 are the piece
standing on the plate**. The rest are plates that are simply gone, refills that have been
picked up, and remembering one of those leaves the planner routing to fuel that is not there.

So the rule is: keep the last reading of a plate the piece is **standing on**, and forget one
that vanishes out of reach. That is neutral on every level of every game that scores — `ls20`
still 39, 45, 109, 306 — and it is the thing the hand-driver needed on its last press.

### What the agent can do on level 5 now, and the one thing it cannot

It does not clear it. It does, unprompted, reproduce most of what the hand-driver had to be
told:

- **The whole carry map** — all eight cells, the same eight found by hand, including
  `(34, 5)`, the one cell the ink-changer sits behind. Sweeping toward the stuck target
  rather than to the nearest square nobody has stood on is what finds it; nearest-first
  fills in the room the piece is already in and never leaves it.
- **The shape recipe** — `[((19, 10), 2), ((14, 35), 2)]`: the cross twice, then the
  quarter-turn twice. That is exactly the sequence the hand-driver worked out from the
  rotation law, and the agent gets there from observed transitions alone, by searching every
  changer's edges at once rather than walking one changer's own cycle.
- **The order** — it refuels before crossing the board, and turns the changer the order
  search picked rather than the last one that happened to pay out.

What it cannot do is close the ink cycle. `12 → 9 → 14 → 8` needs three entries in one life;
it arrives at the cluster with four actions of fuel, the three entries cost exactly four, and
a death puts the display back to 12 — so it watches `12 → 9` over and over and never learns
what 14 turns into. Four attempts at that are written up below as rules that were measured
back out; the fifth, reserving fuel for a way out of every leg, is in and is not enough on
its own.

### A trip is now validated mid-flight, and committed whole only when it is a recipe

The order search used to be re-run every planning round and commit one hop, which is where
most of level 5's 250+ rounds went; an earlier experiment committed the whole trip blind and
bought those rounds back at the price of level 3, whose second changer is found by noticing
the display move under a walk one leg at a time. `stage` now returns the trip with a
per-action prediction of what it does to the display — an entry onto a changer moves it, a
walking step does not — and the play loop drops the trip the moment reality disagrees either
way, checking the piece's square before every action and the display after it.

How much of the trip to commit was then measured, and the answer is sharper than the
validation: **committed whole by default it loses level 4 outright**, 864 actions looping on
one square across 102 trips of which 98% died within three actions. The killer is not the
blindness the validation guards against — it is that a press executed inside a plan never
books `gate.cycled()`, so the counter that forgets a changer that has stopped paying never
moves and the loop never breaks. Two plausible fixes measured inert on that loop before the
real one landed: filtering stage's routes against the squares a press has been refused from,
and gating the whole-trip commit on every leg coming from a watched cycle. So the default
commit is the first hop's route, exactly as before, and the whole trip — walk, off/on pairs
and refills woven — is committed only when it is a *recipe with a chain in it*: every leg
from a watched cycle AND some leg needing two or more entries. Both halves of that gate are
measured against the two neighbouring shapes: `known` alone re-costs level 3 its 55 actions
through single-entry trips (an unmapped carry, `(9, 10)` to `(34, 5)`, throws the piece
mid-walk and the rest of the committed walk starves the life), and requiring an interleaved
half instead never fires at all, because level 5's ink is one leg of one square. Under the
landed gate every game and level holds its number (`ls20` 23, 45, 99, 178; `cd82` 1,034;
`m0r0` 53; `ar25` 173) and the trips fire where they were built to: on level 5's ink,
`[((29, 25), 3)]`, once its cycle is watched. In the best traced run the committed trip
landed two of the three entries — the panel walked `12 → 9 → 14`, one press from the 8 the
door wants — before a death put it back, which is further round that cycle than any
truncated run has been. What was left was fuel, and two rules about it are what cleared the
level.

### Level 5 falls: a chain starts full, unless the alternative is starving

The chains were being committed from whatever tank the moment offered — an exact fit,
`cost + escape = clock`, on a board that carries the piece 2-3 actions off the route a
couple of times per crossing. Each bounce came out of a margin the plan did not have; the
piece starved between the second and third entry, the death reset the panel, and the level
looped through seven deaths in one run, always the same way. Giving a chain leg three
`MARGIN`s of slack on top of its escape is what pushes the order search to put a **refill in
front of the chain** — a chain walked from a full tank is the one that affords the bounces —
and deaths fell from seven to four, with the ink finishing for the first time.

The run that finished the ink then exposed the rule's other half: the recipe stood one leg
from done — shape twice, everything else right — with eight actions on the clock, and the
slack that had saved the early chains refused every plan, so the piece starved while
refusing to try. The slack is a preference, not a wall: **a search that finds nothing with
it runs again without it**, because an exact fit that might land beats a certain death.
With both halves in, `ls20` level 5 falls — 23, 45, 99, 178, **347** against baselines of
22, 123, 73, 84, 96, one death on the level, and the game goes from 20.489% to **21.856%**
with every other game and level holding its number (`cd82` 1,034; `m0r0` 53; `ar25` 173).
347 against a 96 baseline scores the level low — the next inch is walking it tighter, and
the ceiling for clearing levels 6 and 7 is now open.

### Where the actions go, measured — and the first two levers pulled

`ARC_ACCT` writes one line per executed action naming the rung of `choose` that emitted it
(invariants: per-level counts sum to the reported actions; two runs are byte-identical).
The first table it produced redirected the tuning twice. **Doubling the budget was measured
and reverted**: level 6 spent 1,708 actions and did not fall, with 65% of them — 1,115 —
inside the confirm-probe rung, so the block is structural, not the budget. **And the deaths
were signed**: of the fourteen lives lost in one run, twelve ended in the `desperate` rung
with a probe two steps earlier — a blind probe walks out on a tank that cannot pay for the
walk back, and a death resets the panel the probes exist to serve. A blind probe now has to
afford the way back to a known refill. Demanding that of the *targeted* probes as well was
measured and costs level 3 twenty-six actions, so only the blind ones pay it — and with
that, level 5 falls in **306** instead of 347 (one fewer death), the game stands at
**22.246%**, and level 6's probe loop is gone from its accounting.

### The sixth level puts the changers in the corridors

Level 6 is diagnosed and not cleared, and both halves of that sentence were bought with
measurements worth keeping. The board: a ring of walkways, two goal boxes wearing two
different glyphs, refills in the corners — and its white crosses sit **inside the
walkways**, wide enough that the piece's 5x5 footprint enters them from three to five
lattice squares per row. Every route to anywhere presses; one accounted run saw the display
move 365 times in 1,708 actions with nobody ever *choosing* to press. The thirteen
"changers" the gate learns there are all real — they are the overlap positions — and the
whole planning stack, built on "a changer is a square you walk to on purpose", cannot say
anything about a board where walking IS pressing: `locked` reads 0 nearly every round
because the panel never holds still long enough to disagree with a door.

Two wrong turns are recorded so they are not walked again. **The crosses do not patrol** —
two frames 500 actions apart showed them in different places and the piece *covers what it
stands on*, so a static cross under the piece reads as a vanished one; a collider-attribution
model built on that reading found nothing to attribute (movers stayed empty) while its
discriminator mis-fired on the piece's own churned track ids and cost levels 3-5 in one
stroke before it was tightened, then reverted whole. And a **phase-counting router** — BFS
over (position, presses mod cycle), arriving at the door with the panel already right — is
the correct planner shape for this board, but wired under `locked` it structurally cannot
fire (locked is 0 there), and gated on "≥4 squares moving one half" it fires on level 5
instead (entry-square counts cross any threshold) and loses it; the guard that held was
*uniformity* — every counted shape square proven a rotator in `gate.rotates`, which silences
level 5's alphabet-walking cross by mechanism rather than by number. What the next attempt
needs is the trigger `locked` cannot provide: the corridor signature itself (many squares,
one half), plus `phase_need` answered from the rotation law and the game's ink alphabet.

One more carry-over joined the model and the controls: **the ink alphabet is a property of
the game**. `ls20` runs the same `12 → 9 → 14 → 8` on levels 3 and 5, and re-watching it was
part of every deep level's price. Ink transitions (ints — never shapes, which have
per-square graphs; level 5 alone has two shape-changers walking two different ones) now
carry across levels in `Gate.legacy`, consulted only for a square already seen to move that
half on this board, and dropped by the same refutation that kills a phantom edge if a game's
levels turn out to disagree. Level 5 falls in **292**; the game stands at **22.419%**.

One more thing fell out of the trace: level 3 has an undocumented carry, `(9, 10)` throwing
the piece to `(34, 5)` with no clock rise — met twice by the wider-ranging trips, learned by
the same two-sighting rule as every other cell, and invisible until now because the winning
route never crossed it.

### The sixth level falls: the changers were patrolling all along

The diagnosis above got the planner shape right and the board wrong, twice over. The
crosses were first read as patrolling from two frames 500 actions apart, then corrected to
static because the piece covers what it stands on — and the correction was the error.
Tracked one position per piece-move (`results/l6-circuits.txt`), the changers are three
small objects walking deterministic **period-8 patrol tracks**: an ink cluster circling the
mid-left block and two crosses shuttling the corridors. They advance exactly one lattice
step per piece MOVE — a refused press freezes all of them — and a press is the piece's
footprint overlapping a patroller **after** the move. That model, driven by a scripted BFS
over position × patrol phase × panel (`l6drive.py`), predicted every position and every
panel value of a 23-action drive exactly, which is what "the presses are random" had been
hiding: the randomness was patroller phase.

The locks are two doors and a corridor between them. Door B asks `(8, #.#/##./.##)` — the
full pair, three mixed-panel combinations refused — and is a checked PASSAGE: behind it a
pocket only reachable through it, holding door A, which asks `(9, #.#/..#/###)`. No
patroller reaches the pocket, so the panel is frozen there and one pass cannot satisfy
both doors. What resolves it is measured in `results/l6-driveAB2.txt`: **a door passed
while matched stays open** (until a death resets the panel, and the door with it), and
**entering door A wearing its ask ends the level**. The ink alphabet closes into a cycle
at level 6 — `12 → 9 → 14 → 8 → 12` — and the phantom `12 → 14` edge that poisoned
`Gate.legacy` was the death reset (panel back to `(14, ##./.##/#.#)`, respawn at the
start) recorded as if a square had done it.

The agent's version is four pieces, each of which failed measurably before it worked.
`Gate.track` records every small object against a **piece-move clock** and reads periods
off phase consistency, because a patroller is invisible exactly when it matters — the
piece pressing it covers it and its track id churns — and the piece's own parts must be
excluded by footprint overlap, not by id: a piece pacing back and forth earns its own
fragments a period and a press credit, and that phantom patroller glued to the piece
blanketed every neighbouring square with unplannable presses (the BFS explored ONE state).
Press credit goes to the patroller whose **predicted** position overlaps the footprint —
crediting what is visible instead left every period-carrier without edges (and finding
that took tracing a shadowed variable: the observe loop reuses `h` for a half index, so
the footprint had been 5×1 for the whole hunt). `Gate.route_moving` is the planner: BFS
over position × phase × panel × refills × opened doors, fuel carried as a value to
maximise, marked plates as checked gates a plan may open mid-route — and the goal chosen
is the plan that opens the MOST gates, because entering the shallow door as the goal
strands the piece there with no fuel for the deep one (measured, three lives in a row).
`Gate.route_learn` is the missing half of discovery: the planner can only press values it
has watched, and door A's glyph sits five presses down an alphabet nobody had a reason to
walk — so when no door is plannable and a patroller moves the wrong half at a value it has
never been watched on, one deliberate, fuel-bounded press teaches the next edge, and
replanning chains the rest.

Two supporting changes are scoped deliberately. A carry the plan predicted does not drop a
"moving" trip — the timing against the patrol clock IS the plan — but extending that keep
to every trip was measured at once: level 5 went 292 → 339, so it is `psrc == "moving"`
only. And BUDGET rises 1200 → 2000: the earlier doubling was rightly reverted when 65% of
the extra went to a structurally-blocked probe loop, but with the planner in place the run
ends at the cap mid-choreography with the accounting showing monotone progress — the
budget is the binding constraint for the first time.

With all of it, `ls20` clears level 6 unaided: **[23, 45, 99, 178, 290, 1187]**, six of
seven levels, **23.006%** (`results/rung-ls20m.log`).

### Cutting level 6, and two ways of not cutting it

The accounting says where the 1,187 go: **483 in `stage1`**, the square-changer order
search, on a board whose changers are not squares — and 12 deaths, each resetting the
panel and every door already opened. Three changes were measured against that.

**What worked: press what you do not know, and walk there through what you do.** The
first learn rung could only teach the edge leading *out of the value the panel was
showing*, and level 6's ask sits several unwatched presses further on — so every round
whose plan needed a deeper edge fell through to the square-changer rungs. Inverting the
planner's goal instead — same BFS, ending on the first press whose edge is unknown,
fuel-bounded so the press survives to be used — takes level 6 from **1,187 to 844** and
the game to **23.528%** (`results/l6-learn2.log`), with every other level unchanged.

**What did not: taking the square-changer rungs away.** Their trips aim at
footprint-overlap positions, which are not places, and they were 317 of the remaining
844 — apparently pure waste, so they were replaced with "top the tank up instead". That
**loses level 6 outright** (5/7, 22.446%): the freed rounds went to the confirm-probe
rung (40 → 329 actions) and bought nothing, because a stuck round is short of a watched
EDGE, not of fuel. Walking the corridors toward a fictional destination still walks the
corridors, and on a board where walking is pressing that is how the alphabet gets
watched at all.

**And neither did clearing the stale patrol histories on a death.** A death puts the
patrollers back, so entries from before it contradict the ones after at the same phase
and every period is lost — verified, on the exact action a life ends. Clearing the
histories to re-earn a period in one lap rather than three also **loses level 6** (5/7,
22.419%). The contradicting entries are not only noise: they are what stops a period
being re-read too eagerly off a handful of post-respawn frames, and a wrong period sends
every planned press to the wrong tick.

So level 6 stands at 844 against a baseline of 192, and the way down is teaching the
alphabet faster rather than walking less. Level 7 is now reachable — and it is a lock
nothing in this repo can see yet (`results/l7-first-look.md`).

### A third way of not cutting it: the tank was never the problem

Every arrow the accounting draws on level 6 points at fuel. The level is **ten lives**,
nine of them ending in a death that puts the panel and every opened door back; five end
with the square-changer rungs spending 42, 43, 43, 43 and 44 actions — a full tank each,
to the action — and then starving. Every one of the nine has a tail of `desperate` and
`cand` walking on an empty tank, about ninety actions in all. Not one of the 844 actions
goes to a refuel rung: `near-fuel`, `turn-fuel` and `door-fuel` are all zero here, where
level 5 spends thirty actions in them. And the patrol planner is handed a median of
**19** actions of a 42-action tank (`results/l6-rmdbg.log`) against a recipe that takes
72 by hand. Read together that is one story — the choreography is being planned out of a
half-empty tank and never fits — and it names its own fix: make the door trip leave from
a full one.

The fix is inert, and asking why is the interesting part. It went in as a
discriminator rather than as a rule, because topping the tank up whenever neither
planner answered had already been measured and had lost the level: refuel *only* when
the same search finds a plan that the tank is the only thing blocking, and otherwise
fall through to the square-changer rungs, which is where presses get watched. That
question can be asked of any round, and the answer on level 6 is always the same one.
In **121 of 121** rounds where both planners came back empty, no marked door has a plan
at a tank of **200** actions either — five times the real one
(`results/l6-fueldbg3.log`). The rung never fires, the four-game sweep is byte-identical
to the baseline, and the code is not in the repo.

What that buys is not the level, it is the elimination. "Those rounds were short of an
EDGE, not of fuel" was previously an inference from a level that got lost; it is now a
per-round measurement, and fuel is retired as a lever on this board. Two things fell out
of asking the question. A resource hypothesis is settled by handing the search an absurd
amount of the resource — one run, no code, no sweep to interpret. And `full` itself is
unreliable here: it reads **21 in 72 of those 121 rounds** on a board whose tank is 42,
because `drain` takes the most common fall over the last twenty steps and that flips
between 2 and 4 within the level. Any lever keyed on the tank size is reading a number
that is wrong most of the time — which is its own open thread, and not the one that was
costing level 6 its actions.

### 844 to 570: a period outlives a death, a phase does not

With fuel eliminated, what is left is the other reason the planner refuses: *"no ready
movers"*, which is `mover_period` returning None for every patroller at once. It happens
for a reason with a shape. A death puts each one back at the start of its lap, so every
entry recorded before it contradicts the ones after it at the same phase, and the period
stays lost for the three laps the old entries need to age out of the window. While it is
lost neither planner can plan — including the learn planner, which is the only thing that
deliberately teaches an edge — so the rounds fall through to the square-changer rungs and
the alphabet is learned only by accident, by walking.

(How big that is was not knowable from the debug log at the time, and one of this
session's numbers was wrong for a while because of it. `ARC_RMDBG` printed the refusals
without saying which LEVEL had asked, and the rung is called — and correctly refuses — on
every board with any tracked object, so its 588 refusals were read as level 6's when most
of them belong to levels 2 to 5, where there is nothing patrolling to be ready. The lines
now carry `lvl=`, and level 6's own split is in the next paragraph but one.)

Clearing the histories on a death was the obvious fix and it lost the level (5/7,
22.419%), because a period re-read off a handful of post-respawn frames can be the wrong
one, and a wrong period sends every planned press to the wrong tick. The distinction that
was missing: **a period belongs to the object and a phase belongs to the life.** The lap
is eight steps long on this life and it was eight steps long on the last one; what the
death destroyed is only the knowledge of where along it each patroller now is.

So the period is remembered once earned and, when the full window is contradictory,
re-used — never re-read off the short history, only *checked* against it, so this life's
frames can refute the inherited period and can never invent one. The phase map is built
from this life's sightings alone, and a phase this life has not seen yet answers None,
which is the same silence the occluded stretch of a lap already gives. Two lines of state
(`Gate.reset`, `Gate.mover_p`), one branch in `mover_period`, one bound in `mover_at`.

Level 6 goes **844 → 570** and the game to **24.85%**, with levels 1-5 unchanged to the
action and `cd82`, `m0r0` and `ar25` unmoved (`results/sweep-phase.log`). Deaths fall
from nine to six, the square-changer rungs from 317 actions to 209, and the level is now
reached with enough budget left that level 7 gets 793 actions to be baffled by instead of
519.

And with the refusals finally attributed to the level that asked, what is left on level 6
is not this: of 723 refusals, **555 are `bfs exhausted`** — a real search, median 1,968
states and up to 70,046, that finds no route — against 168 of "no ready movers". Two
readings of the 555 have been tried and both are refuted. It is not fuel: no marked door
has a plan at a tank of 200 either. And it is not a phase map too thin to predict the
presses along a route, which is what one would expect the cost of reading phases off one
life to be — at the moment those searches give up the maps are **full for 83% of the
movers they are planning against** (2,634 of 3,156 mover-entries, `results/l6-fill.log`).
The searches are refused for the reason the level has been refusing them all along: the
alphabet. 189 of the 555 are the LEARN planner giving up, which is the sharper form of
the same thing — not merely "no route to the ask" but "no unknown press worth walking to
either".

The obvious reading of that is that the edge the level needs sits on a patroller this tank
cannot reach, and it is wrong. Asked of every one of those 189 rounds what an **infinite**
tank would do — the same trick that retired fuel as a lever a section ago — the answer is
that in **159 of them there is no unknown press to walk to at any tank size**. Only 30 are
affordability. So the learn planner is not being starved; it has genuinely run out of
things to learn from where it stands, and making its trips cheaper would buy 30 rounds.

What those rounds are short of is a panel VALUE. The derivation that followed was that the
reachable set must be *closed* — every press from every state the known edges span already
recorded — so the door's ask lies outside it and the only move that crosses the frontier is
a **death**, whose reset puts the panel at `(14, ##./.##/#.#)` wherever it was. That would
have meant the agent was using its lives as a state-reset mechanism without anything in it
knowing so, which is a good story, and the panel trace refutes it in one look.

`ARC_L6` records the panel per round; over the level it visits **24 distinct states**, and
what matters is when each was first seen. The five deepest shapes — the tail of the
alphabet, ending on door A's own glyph `#.#/..#/###` — are first seen at actions 1039,
1040, 1041, 1042 and 1043. Five consecutive actions is five *presses*, not a death; the
deaths are at 679, 760, 837, 916, 993 and 1098. Door A's full ask `(9, #.#/..#/###)` first
appears at 1192 and the level ends at 1207. A death introduces exactly one state in the
whole level, `(14, ##./.##/#.#)` at the first one, which is the reset and nothing more.

So "nothing left to learn within reach" is a **local** condition — of the piece's position,
the patrol phase and the panel's current value together — and not a closure. The level does
walk its whole alphabet, in a burst of five presses, once it is finally standing somewhere
it can.

### 570 to 285: the planner could not see the patrollers it had not watched

One question was left: with an infinite tank and no unknown press anywhere, what is
actually missing? Asked of the board rather than of the search, the answer is sitting in
plain sight. `route_moving` builds its patroller list from movers that have a period **and
a known half** — everything else contributes nothing to `presses`, so walking over it is
not modelled as a press at all. A patroller nobody has watched yet is therefore not
"unknown" to the planner; it is *invisible*, and no plan can be made to go and find out
what it does.

Measured, that is not a corner case: in **183 of the 189** rounds the learn planner gave
up on, there were two to seven such patrollers on the board, every one of them already
carrying period 8. The search was right that nothing among the movers it could see was
unknown, and the movers it could see were not all of them.

In learn mode, a patroller with a period and no known halves IS the unknown press. Six
lines: collect them, read each against its own period (so the least common multiple above
does not have to cover them), and treat a footprint overlapping one as the blind press the
learn goal already knows how to walk to — under the same fuel guard, because a press the
piece starves on teaches nothing that survives.

    ls20  [23, 45, 99, 178, 292, 285]   32.144%     was 570 and 24.85%

Levels 1-5 identical to the action, `cd82`, `m0r0` and `ar25` unmoved
(`results/sweep-mute.log`). The accounting says exactly what happened: `stage1` — the
square-changer order search, on a board whose changers are not squares — goes from **209
actions to 3**, `moving-learn` from 82 to 154, `turn-walk` and `desperate` from 38 and 29
to nothing and 2, and the deaths from six to **one**. Two hundred actions of walking the
corridors hoping to trip over a press were replaced by seventy of going to find one.

### 285 to 265: the same alphabet, learned six times

With the learning finally deliberate it can be counted, and the count is embarrassing.
Those 285 actions make **85 presses** and gain **51 new edges**, and they end holding 122
edges filed under **26 keys** — for three patrollers. The gains arrive in bursts of about
six consecutive actions, six times over. It is the same six edges, relearned.

The cause is the thing that made the patrol model hard in the first place: a patroller is
invisible exactly when it is pressed, because the piece covers it, so its track id churns
on the tick that matters most and everything filed under the old id is stranded. Keeping
edges across a *game over* was measured and lost the level, because the ids there land on
whatever the tracker hands out next. Within a life there is better evidence than a guess
about numbering: the **lap**. Two objects standing on two of the same squares of a
deterministic circuit are one object — two rather than one, because one shared square is
where two tracks cross — so when a track earns its period it inherits the halves and the
alphabet of any circuit it matches. The records are copied rather than aliased, so every
reader stays as it was, and a wrong adoption is refutable exactly like any wrong edge.

    ls20  [23, 45, 99, 178, 292, 265]   33.668%     was 285 and 32.144%

Levels 1-5 identical again, the other three games unmoved (`results/sweep-adopt.log`).

### 265 to 209: a circuit is recognised in pieces, and on every look

That first version closed 26 keys to 24, where three patrollers of two halves want six, and
the reason is two words of the code. It asked only on the reading that **earns** a period —
never on the far commoner one that inherits it, so a board that kills the piece adopts
nothing for the three laps after every death — and it compared a **snapshot** of the circuit
taken at that instant, which holds whatever few phases happened to have been sighted by
then. A partial circuit matches nothing, and once stored it never improved.

Ask on every reading, and let the lap **accumulate**: the squares of a circuit are the same
on the next life, because a death moves a patroller back along its track rather than off it,
so the union is taken across lives while `mover_at`'s phase map stays strictly within one.

    ls20  [23, 45, 99, 178, 292, 209]   40.503%     was 265 and 33.668%

Levels 1-5 identical, the other three games unmoved (`results/sweep-adopt2.log`). The key
count barely moves — 24 to 22 — and that is the wrong number to watch: what changes is that
the edges **spread**, 151 to 221 across those keys, so whichever id the tracker is currently
calling a patroller already knows what it does. Level 6 now runs at **1.09x the human
baseline**, against 4.4x when the session started.

### 265 to 209: a circuit is recognised in pieces, and on every look

That first version closed 26 keys to 24, where three patrollers of two halves want six, and
the reason is in two words of the code. It asked only on the reading that **earns** a
period — never on the far commoner one that inherits it, so a board that kills the piece
adopts nothing for the three laps after every death — and it compared a **snapshot** of the
circuit taken at that instant, which holds whatever few phases happened to have been sighted
by then. A partial circuit matches nothing, and once stored it never improved.

Both are one-line problems. Ask on every reading, and let the lap **accumulate**: the
squares of a circuit are the same on the next life, because a death moves a patroller back
along its track rather than off it, so the union is taken across lives while `mover_at`'s
phase map stays strictly within one.

    ls20  [23, 45, 99, 178, 292, 209]   40.503%     was 265 and 33.668%

Levels 1-5 identical, the other three games unmoved (`results/sweep-adopt2.log`). The key
count barely moves — 24 to 22 — and that turns out to be the wrong thing to watch: what
changes is that the edges **spread**, 151 to 221 across those keys, so whichever id the
tracker is currently calling a patroller already knows what it does. Level 6 now runs at
**1.09x the human baseline**, against 4.4x when the session started.

### The seventh level is a window, and the agent thinks it is a board

Level 7 has no plates, nothing patrols, and the first look at it recorded an arena that
"shrinks into a triangle". Walked with a census printed per step, what it actually does is
stranger and simpler. One step up destroys 98 floor cells and 86 wall cells behind the
piece and creates 38 wall and 8 floor cells ahead of it; one step back restores every
count exactly, in both axes, with no hysteresis. The board is a pure function of where the
piece is standing.

The obvious reading — a scrolling world — is wrong, and one measurement settles it.
Comparing two consecutive frames at every shift from -8 to +8 in both axes, the best match
is **dx=0, dy=0 at 94-95%**: the world is not moving under a camera. What moves is the
colour-5 region, and across ten positions the non-5 extent is `piece_x - 18 … piece_x + 21`
by `piece_y - 18 … piece_y + 21`, clipped by the screen and by the world's own walls. The
frame is a **40x40 window around the piece**, and everything outside it is painted the same
colour this game has used for its border since level 1.

Which is exactly why the agent gets nowhere: every reader in the repo treats the frame as
the whole board. The fog reads as wall, so the piece appears boxed in by something that
recedes as it walks; every planning round sees a different board, so targets appear and
vanish and the route is rebuilt from scratch. Level 7's accounting is **776 of 793 actions
in `cand`**, the rarity router — which is what a board that will not hold still looks like
from the inside, and it was previously being read as the agent having no idea what to do.

The shape of the fix falls out of the same measurement. Because the coordinates are fixed,
the windows stitch: remember every non-5 cell at the coordinates it was seen at, and treat
colour 5 as *unknown* rather than as wall. That is a change to perception rather than to
the gate, and it has to be gated on something this level has and the others do not — the
colour-5 region moving with the piece — because on levels 1 to 6 colour 5 IS the border.

What ends the level is still unknown. But the probe that went looking for it answered a
different question that had been open since level 1.

### The counter in the corner is the lives, and the third death is not like the others

`hud`'s colour-8 counter reads 12 and sat there through every walk, which is what a static
decoration looks like. Starved on purpose three times in a row, it goes **12 → 8 → 4 →
game over → 12**, and it reads 12 at the start of levels 2, 4, 6 and 7. It is the game's
life counter, four cells a life, three lives, twenty-two actions each against an 84-unit
bar spent four at a time.

That matters more than a readout. The agent has always treated a death as one thing — the
panel goes back and the doors with it. Two of the three are that. The third is a game
over, and the engine's reset takes the patrol model and the alphabet with it: `movers`,
`mover_edges` and `mover_p` are all cleared, because the tracker restarts its numbering
and histories filed under the old ids would describe patrollers that are not there. `ls20`
reaches one **twice per run** on level 6, and until now nothing in the agent knew which
kind of death it was about to take.

The obvious repair is to keep the expensive half. An edge is a fact about the game's
alphabet, not about a life; level 6 refuses 555 of its 723 planning rounds with a search
that finds no route, which is a missing edge every time; and the board after a game over
is the same board, walked by the same tracker in the same order — the repo's own stated
reason for restarting the numbering there is that the ids land on the same objects. Keeping
`mover_edges` across it **loses level 6 outright**, 5/7 at 22.419%. Whatever those ids
land on, edges filed under them plan presses that do not happen, and a wrong edge costs
more than an absent one. The histories and the edges go together or not at all.

### Stitched, level 7 has a door — and two reasons the code is not in the repo

Stitching the windows offline and handing the composite to the agent's own plate reader
answers the question the window had been hiding. There is a plate at **x28-34, y49-55,
asking `(8, #.#/##./.##)`** — which is door B's exact ask on level 6; the game reuses its
alphabet across levels the same way its ink does. It sits far below anything a window from
the start can show, so "no plates at all" was a measurement of the viewport, not of the
level. Level 7 is the level 2-6 lock after all.

Built into the agent, stitching does exactly what it was designed to: the latch fires on
the second action of the level, the remembered world grows from 1,165 to 2,839 cells, and
the door is visible in **777 of 789 planning rounds**. It is still not in the repo.

The first reason is that seeing a door is not enough. `gate.displays` stays at zero for
the whole level, because no plate is ever seen to *change* — and a plate that never
changes is not a display, so nothing is `locked`, and the door is just another rarity
target the router walks to and is refused by. The indicator is probably the big colour-12
L glyph at the bottom left, whose normal form is `.#./###` against the door's
`#.#/##./.##`; `plates` cannot read it because nothing frames it. That is the next thread,
and it is a perception problem rather than a planning one.

The second reason is the one worth writing down. The latch keys on colour 5 trading
terrain in both directions, which is an `ls20` fact wearing a general one's clothes.
Measured on a single sighting and again on three consecutive sightings, `cd82`, `m0r0` and
`ar25` all latch too and **lose their only level each** — 1,981 of 2,000 actions spent
wandering a board painted from the memory of a board that had been redrawn underneath it.
The failure is instructive: a memory of the world is strictly worse than no memory when
the thing remembered was never stable, and the guard against that cannot be a threshold on
how much changed. A general version has to find the fog colour in the frame rather than
being handed it, which is its own problem and not this one.

The full level-7 model, controls and open threads are in `results/l7-model.md`;
`probe7.py` is the instrument, and `-map` stitches the windows into one world offline.

### Level 7, solved by hand: the ask is a composition, and the door is a hole

The lock's last secret was that no single changer can produce what it asks. The
indicator's shape changer at (19,40) walks a six-state ring that CLOSES without ever
showing the ask `#.#/##./.##` — measured by driving it round twice (`results/l7-ring.txt`)
— and the nearest it gets, `##./.##/#.#`, is the ask rotated 180°. The x55 patroller
turns the shape a quarter per press. Two quarters are 180°: ring state plus two patroller
presses is the ask exactly, and `down` from (29,45) — the move that had refused every
wrong panel — simply happens when the panel is right, and ends the level.

`results/l7-solution.txt` is a 71-action line from the level-7 start that does it: ink to
8 (three re-entries of one square), the ring to `##./.##/#.#` (five re-entries of
another, a refill woven mid-walk because the ring does not fit one life), a loop north to
a second refill taken on the life's final action, a carry into the east corridor, two
CHASE presses of the patroller — following it down its own lap overlaps it every tick,
so the count is controlled by stepping off the column sideways the moment the panel
reads right — a third refill beside the patroller, a carry home, and in. Three refills,
two carries, zero deaths (`results/l7-solve.txt` ends `lvl=7`).

The agent itself still plays 6/7. The plan above mixes the square machinery's presses
with phase-timed patroller presses and three woven refills, and no planner in the repo
can compose the two: the square order search cannot extrapolate a rotator to a value it
has never seen, and `route_moving` cannot hand off to `stage` mid-plan. That
integration is the open problem the solution defines. What this session DID land in the
agent: refill colours latch for the level on windowed boards, and the square rungs get
the round before the learn trip there — presses 31 → 68 per run, probe 516 → 73, every
other game and level unchanged to the digit.

### Level 7 falls: the shape errand had been walking to the ink square

The integration above was, in the end, already built. Every piece the hand solution needs
landed across the sessions that followed — the ink ring, the shape ring, the remembered lap,
the interceptor that pays the patroller's quarters, the return leg, the door walk — and each
was measured working on its own while the level stayed at 6/7. What they were all waiting on
was a half that nothing was pressing.

`ls20` level 7 has two changer squares: (9,40) writes the ink, (19,40) writes the shape.
Over one full run the ink square was arrived at **126 times and the shape square 10**; 120
of the run's 127 display changes were ink; `wander` spent all 90 of its rounds standing on
(9,40), and 66 of the run's 123 engine refusals happened there. `changer_for` — the method
whose whole job is to answer *which square moves the half that is wrong* — answered (9,40)
in **424 of ~470 decisions, 68 of them with the shape as the only wrong half**.

The cause is one word. A display's two halves are credited to the square the piece was
standing on when they moved, and on this board one stale reading folded onto one of the ink
square's many entries credits it with the SHAPE half as well: `gate.changers` reads
`{(9,40): {0,1}, (19,40): {1}}` in **452 of 507 planning rounds**. The rule that picks
between them sorts the *halves* correctly — blind half first, a fix from an earlier session —
and then takes the first square in **insertion order** that claims the winning half. The ink
square is learned first every life, so the phantom credit won every time, and every shape
errand walked to the one square that cannot move the shape.

The square with the most **watched edges** for a half wins instead (`Gate._square_for`): a
phantom credit carries a single folded edge, a real changer carries its cycle. Ties keep
insertion order, and off a windowed board — every level of every other game — the choice is
unchanged, so the rest of the sweep is identical by construction rather than by luck.

    ls20  [23, 45, 99, 178, 292, 209, 526]  43.629%   7/7      was [.. 209] 40.503%, 6/7
    cd82 [1213], m0r0 [53], ar25 [173]                         identical to the digit

Level 7 completes in **526 of its 2,000 actions**. The full seventeen-game sweep reproduced
it on an independent run — the same seven counts to the digit, no game losing a level, mean
over 17 environments **2.662%** (`results/sweep-sqfor.log`, `results/sweep-sqfor-full.log`). Two things are worth more here than the
code. The first: a claim about what the agent can reach **expires with the equilibrium it was
measured in**. The session before this one wrote down that the panel state `.#./##./.##`
"reaches `##./.##/#.#`", and built a whole latch to exploit it; that was true of an earlier
run which booked eight shape edges and false of the calm one, which books three — so the
latch measured inert and was blamed for a bug it did not have. The second: the per-round
`gate` dump the agent already writes is a **replayable oracle**. Loading it back and running
the suspect scan offline cleared it in seconds, against the very run that was said to
disprove it, and pointed at the real question — why the ring stopped growing — without
spending a live run on the wrong hypothesis.

### Five bugs, each of which was invisible until the run was traced
<!-- five in the list, plus the track-id one below that only level 3 could show -->

None of these announced themselves. Each was found by printing what the agent chose, and each
one alone was enough to lose the level:

1. **The clock was being read as a constant.** `ls20` runs two counters that move on every
   action — the yellow bar shrinking and the grey it leaves behind growing in its place —
   and their sum is always 84. Adding them up reads a full tank on the step before starving,
   which is why the refill logic built on that sum could never fire once, on any game.
2. **The rate belongs to the level, not the game.** The same bar spends 2 cells an action on
   level 1 and 4 on level 2, so a rate averaged over the run reads a level-2 life as twice as
   long as it is. It is now measured over the last 20 actions.
3. **A model rebuilt on a new board has no walls.** The evidence is reset at a level
   boundary, so `classify_colours` sees no blocked move yet, `blocking` comes back empty, and
   `walkable` lets every plan route straight through a wall — a 16-action walk to the changer
   became a 5-action plan that spent its life bumping into one. The previous level's terrain
   is now kept until this level finds a wall of its own — inherited from the model as it
   stood at the **end of the previous level**, not from the one built an action ago.
   Inheriting from the current model instead accumulates within a level, which is a different
   and worse thing: `classify_colours` deliberately retracts a colour once it stops being the
   sole unexplained thing in the way, and a running union keeps every colour it has ever
   suspected. That alone cost `cd82` its 812-action level — a game that never reaches a
   second level, so a level-boundary carry-over could only ever hurt it.
4. **The controls are a property of the game, and were being re-derived per level.** A model
   rebuilt on `ls20` level 4 inferred **two of its four directions**, and `walkable` shrank
   the board from 67 reachable positions to three — every route came back None while the
   piece sat still, which reads exactly like a level with no solution. Carrying them across
   fixed it, and then the *precedence* mattered too: letting the new level's evidence
   override, `infer_dirs` read "up" as `(-10, -5)` off a frame that lied, and the piece sat
   in a pocket whose only exit was up while all four directions reported blocked. The older
   reading wins — it has already walked three levels — and the new one fills in only the
   actions the prior never saw. Worth 91 → 45 actions on level 2 and 203 → 137 on level 3,
   because both had been routing around walls that were not there.
5. **A model that cannot find its own piece was replacing one that could.** `parts` comes out
   empty whenever the body's track ids churn, and `locate` needs it to recognise the piece on
   a board the model was not built from. Fifty actions of level 2 were spent blind, mid-level,
   with the agent unable to plan anything at all.

And a sixth, on the level after: **track ids restart at a level boundary and collide.** The
new board's tracker hands out the same integers the old model's body is written in, so
`body_box` answers with whatever the new board happens to call 0 and 1 — and the agent steers
a decoration. On `ls20` level 3 it read the piece as standing still for **1,070 actions**
while pressing a direction into a wall. Numbering now carries on across a level boundary but
still restarts on a level *reset*, where the tracker walks the same board in the same order
and the same ids are the right answer — carrying on there instead cost `ar25` its level, so
that distinction is measured rather than argued. Level 3 is not cleared, but the piece moves,
routes and refuels on it now instead of standing still.

### Two reactions to a blocked move, both measured back out

A move that does not happen is information, and both obvious ways of using it made things
worse. They are worth more written down than the code was:

| rule | reasoning | measured |
|---|---|---|
| abandon the plan, since the piece is a square behind where the rest of the route assumes | sound | `m0r0` 74 → 71 actions, **`cd82` loses its only level** |
| remember which target refused, and stop walking to it | the gate announcing itself | **`m0r0` loses its level**, `ls20` unchanged |

The refusal memory fails for a structural reason worth keeping: a refusal has to expire on
*something*, the only thing available is the displays, and before one has been seen to change
there is nothing to expire against — so the first bump into a mis-modelled wall blacklists
the goal for the rest of the level. Reading the glyph makes it unnecessary anyway: a shut
door is known to be shut before the walk, not after it.

## Why an algorithmic agent rather than a model

The competition notebook has **no internet**, so a frontier model cannot be called — the
public ARC-AGI-3 leaderboard leader scores 30.2% online while the Kaggle leaderboard leader
scores **1.86%**. Meanwhile the ARC engine runs locally at ~2,000 FPS with no rate limit,
so search is nearly free and only *scored* actions are expensive. Scoring is
`min((baseline_actions / actions_taken)² × 100, cap)` weighted by level index, which rewards
minimal action sequences — what a planner produces and a language model does not.

## Layout

| File | What |
|---|---|
| `perception.py` | frame → connected-component objects, movement events between frames, HUD counters, scale-normalised glyph bitmaps |
| `identity.py` | cross-frame object tracking — the thing that makes any of the rest trustworthy |
| `discover.py` | works out a game's movement mechanics by acting — piece, footprint, step, direction per action, wall colours; `locate()` finds that piece on any later frame |
| `plan.py` | routing from a discovered model: candidate targets, containment-aware goals, BFS |
| `gate.py` | plates, displays, and the square that changes one — which targets will let the piece in, and what to walk onto to change that |
| `goal_llm.py` | asks a local model which object is the goal — it ranks, the planner routes, the engine judges |
| `signals.py` | finds the game's counters anywhere on the frame, tells a clock from a consequence, and reads how many actions a life has left |
| `trace.py` | frame-by-frame record of what each action did — what vanished, what the status bar did, when a level fell |
| `compete.py` | plays under the real competition rules — one make(), no rewinding, forward only |
| `cover.py` | whole-game driver for the framed-box family (`re86`): park every shape so its own boxes lie under it |
| `swap.py` | whole-game driver for the control-transfer family (`sp80`): sweep the board firing the action that hands the arrows to another body |
| `haul.py` | whole-game driver for the carry family (`wa30`): grab the crate the piece is facing, carry it, drop it into the frame |
| `maze.py` | whole-game driver for the fixed-pitch maze family (`tu93`): read the wall lattice off the frame and walk a notched heading-piece to the goal block |
| `dial.py` | whole-game driver for the combination-lock family (`tr87`): read which phase each station is asked for, and dial them all there |
| `skewer.py` | whole-game driver for the skewer family (`sk48`): thread the wall blocks onto the machine's woven arm in the HUD's order |
| `sigs.py` | every shipped driver signature against every playable game's reset frame — the check before another driver is wired |
| `play.py` | the autonomous loop — discover, search object sequences, tour a kind, sweep every reachable square, keep what clears a level |
| `solver.py` | walkable map from a single frame, BFS, multi-waypoint routing with an action budget |
| `agent.py` | play loop with a swappable policy (`random`, two LLM policies) |
| `scoring.py` | the competition's scoring formula, reimplemented for offline analysis |
| `probe_games.py` | measures, per game, whether the walkable-map assumptions hold at all |
| `walk.py` | replay a prefix then probe — per-step position, budget, glyph match |
| `probe.py` | repeat one action from a reset, to see what it does |
| `capture.py` | run an action list; dump PNGs and print what moved |
| `NOTES-ls20.md` | the reverse-engineered rules of `ls20`, the level-2 solution, and the probe traps that produced confident wrong answers |

## Running it

```bash
uv sync
uv run python solver.py ls20 <prefix-actions> cross,yellow1,goalbox0
uv run python walk.py ls20 <prefix-actions> -- <probe-actions>
```

An anonymous API key is fetched automatically; no account needed for development. The
engine can also run fully offline, which is how the competition notebook will use it.

## How far the approach generalises

`probe_games.py` measures, per game, whether the assumptions behind the solver hold: does
anything move under an action, by a constant step, over separable terrain, in several
directions. Full table in [`results/generalisation-probe.md`](results/generalisation-probe.md).

| verdict | games | |
|---|---|---|
| **MAZE_LIKE** — walkable-map + BFS applies | **9 / 25** | trustworthy; every one is `keyboard`-tagged and `ls20` reproduces its known behaviour |
| NEEDS_POINTER | 9 | 6 confirmed by their `click` tag; `ft09`, `cd82`, `sb26` are likely false negatives |
| NOT_GRID_STEPPED | 6 | suspect — the three worst have 183 / 64 / 56 segmented objects, so the object matcher is probably linking the wrong pair |
| PARTIAL | 1 | |

Every verdict is a **lower bound**: the probe presses each action twice from a single
reset, so a piece that starts against a wall reads as immovable. `ft09` is a proven false
negative — arXiv 2512.24156 Table 1 has a keyboard agent clearing three of its levels.

## Discovering the mechanics without a human

`solver.py` only works because a human read ls20's screen: the piece is colour 12, a move
is 5 cells, colour 4 is the wall. `discover.py` derives all three by acting, and nothing in
it is per-game. Full table in [`results/discovery.md`](results/discovery.md).

| | 9 MAZE_LIKE games |
|---|---|
| piece, footprint, step size, direction per action | **9 / 9** |
| wall colours found | **5 / 9** (`ar25`, `dc22`, `ka59`, `ls20`, `m0r0`) |
| checked against a known-good model | 1 — `ls20` |

On `ls20` the discovered model matches the hand-read one — a two-part 5×5 piece, step 5,
wall colour 4 — `locate()` finds that piece on a board the model was not built from, and
BFS to the goal box returns the same 6 moves `solver.py` finds.

### Identity was upstream of everything

Objects used to be keyed on `(colour, cell_count)` and looked up in a dict, so two objects
sharing that key in one frame collided and one was **silently discarded — 55 objects across
the 9 games at reset alone**, 19 of `dc22`'s 31. Everything downstream was reasoning about a
partial board, which is why inferred directions contradicted each other.

[`identity.py`](identity.py) replaces the key with tracks: each predicts where it should be,
every object is scored against every track on position, colour and area together, and pairs
are taken best-first, so any one attribute can drift without losing the object. Three more
defects surfaced only once that was in place — requiring a part to move with the piece on
*every* action dropped it after one missed frame (a 5×2 box for a 5×5 piece, whose own second
colour then read as a wall); a part that loses its track returns under a new id and splits its
agreement across two (171 and 106 of 278 moves on `ls20`), so agreement is now judged against
the frames each id was visible in; and a model built from track ids is useless on a fresh
board, which `locate()` fixes by recognising the piece from the shape signature of its parts.

### What is left

`cn04`, `re86`, `sc25` and `sp80` still find no wall colour, and it is neither an absence of
walls (committing to one direction gets the piece blocked within 1–15 moves on all nine games)
nor a shortage of evidence (`sc25` collects 119 blocked observations and learns nothing from
them). Their pieces are still mis-identified, just less often than before.

Four earlier readings of this failure were wrong — over-segmented footprints, open boards, too
little exploration, and a stale randomised hash making every run a different experiment. Each
was a guess; each was disproved by measuring.

## Playing without a human

`play.py` closes the loop: discover the mechanics, then find out what ends a level the only
way available — walk onto things and watch `levels_completed`. The engine is local and a
reset is free, so a wrong guess costs wall-clock rather than score, and only the sequence
that worked is kept.

| game | levels cleared | actions | baseline | score |
|---|---|---|---|---|
| `ls20` | 1 of 7 | 13 | 22 | **4.107%** |
| the other eight | 0 | — | — | 0% |

Level 1 caps its per-level score (115 of a possible 115), and level 1 is worth 1/28 of a
seven-level game — which is the whole shape of this competition in one line.

One object is rarely the answer: on `ls20` the piece must touch the marker before the goal
box will accept it, so the six moves straight into the box do nothing. The search is over
*sequences* of objects, shortest total first. Two things had to be right for it to work at
all — reaching a large object means being **inside** it, not clipping its edge; and a wall
colour has to be the *only* unexplained thing in the way, more than once. Taking every
unfamiliar colour in a blocked destination made `dc22` treat the wall's neighbour as solid
and sealed its board down to 9 reachable positions.

### It writes down what happened

Every attempt used to be judged by one bit — did `levels_completed` move — and the rest of
the run was discarded. `trace.py` keeps it: per action, which objects vanished or appeared,
which status counters moved, and whether a level fell. It lands in
`results/traces/<game>.jsonl` and reads back as a log a person can follow:

```
press 3: nothing changed
press 1: nothing changed
press 1: object colour 0 at x21 y31 disappeared; object colour 1 at x20 y32 disappeared;
         object colour 1 at x21 y33 disappeared
```

That is `ls20`'s pickup, visible for the first time. Three filters were needed before the
log said anything, and each removed noise that had been drowning the signal: the piece is
excluded by **colour**, not by exact size, or it reads as vanishing and reappearing on every
step; an object that moves by exactly the action's own displacement **walked**, which catches
the piece parts the body model missed; and a status counter that ticks on nearly every press
is a clock, not a consequence, so it is dropped from the summary. `levels_completed` is a
running total, so a level completion is announced when it *increases* — testing it directly
printed LEVEL COMPLETED on all sixteen lines of a summary for one event.

The same summary is what the local model now reads instead of a still board, so it can be
asked what the rule is rather than what looks important.

**The first thing the capture found: `perception.hud` is looking in the wrong place.** It
reads rows 60 and below, and that is only where `ls20` keeps its status bar. `cn04` moves a
colour-4 marker one cell to the right along **row 0** on every press; `sc25` slides a
colour-14 marker down the **right-hand column** two cells at a time and then turns it another
colour; `re86` runs two counters at once, one climbing 6→7→8 and one falling 58→57→56. None
of those were visible before, which is why the clock-detector finds no clock on three of the
nine games.

That looked like the way out: a marker read wherever it lives would be a **reward signal
between levels**, something to hill-climb on, where `levels_completed` alone is one bit that
flips only at the end. `signals.py` was built to find it and `play.climb` to follow it.

**Measuring killed the idea.** Every counter these games expose is a straight line in the
number of actions taken — `ls20`'s budget 1.000, `re86`'s pair 0.980, `cn04`'s row-0 marker
0.976, `sc25`'s right-hand column 0.956. They are all clocks; they differ in *speed*, not in
kind, and the slower ones are exactly what made them look like progress at first. Not one
waits for an event, so the climb finds no gradient and stalls on its first step in all four
games. Rate is the wrong test and shape is the right one, which is what `signals.classify`
now measures — but on this evidence there is nothing here to climb.

### It remembers

Discovery costs 400 actions and the search costs thousands more, and none of it changes
between runs of the same game, so what was found is written to `results/learned.json` and
reused. The note is not trusted on sight — the stored solution is replayed and checked
against `levels_completed` first, and re-derived if it does not hold. A second run of `ls20`
takes **6 seconds and 0 discovery actions** for the same score. In the scored setting, where
exploration is charged at exactly the same rate as play, the gap between knowing and
re-deriving is most of the score.

### What did not work

"Collect all of one kind" was the obvious rule for the five games that answer a touch, and
it was built: find the kinds that respond, then tour every instance, replanning after each
pickup. **It moved the score not at all.** Along the way it exposed a worse bug in the thing
that chose which kinds to tour — a detector comparing total object counts before and after,
which fired for every candidate including objects on the far side of the board, because the
parser's component list flickers by a couple of entries between frames. Asking instead
whether *the touched object* is gone cut nine games' worth of "everything reacts" down to a
real distribution, and the tour still cleared nothing: on `re86` it collects 4→3→2 and then
strands, and the second kind's count oscillates 3→2→3→2 because the items come back.

Three further adjustments were built and measured, and **none moved the score**: candidate
targets extended to cover region-sized goals (`perception.objects` drops any colour over 400
cells, which left `m0r0` with nothing to aim at); the sequence search taken to six waypoints;
and the reaction detector rewritten. Each is a real improvement to the machinery and the mean
stayed at 0.456%. What the measurements did establish, which is worth more than the attempts:

- **`dc22` is not a maze.** Its piece moves exactly one step in each direction and stops —
  measured against the live game, so the model's 9 reachable cells are correct, not a bug.
  Nine positions in a 3×3 is a selector, not a board to cross.
- **There is no hidden switch.** Across all nine games only `ar25` and `m0r0` have an action
  that never moves the piece, and pressing it changes 1 cell and 0 cells respectively. The
  agent is not missing a door-opening control.
- **The budget is readable.** `ls20`'s HUD carries a counter that falls by exactly 2 per
  action (84 → 68 over eight), so remaining actions can be planned against instead of
  discovered by dying. Nothing uses this yet.
- **Level 2 is reachable and still not solvable.** After the level-1 solution the agent sees
  12 targets, routes to 8 of them, and has 42 actions of budget — depth-6 search over those
  clears nothing, because `ls20` level 2 wants a *glyph match*, not an arrival. That is the
  research problem, not a parameter.

**Standing on every square changes nothing either.** The object list is a hypothesis about
where the goal is; `plan.bfs_all` plus `play.sweep` is the space itself — every reachable
position, nearest first, capped at 600. Boards here have 37 to 1024 reachable positions and
the engine runs locally, so the whole sweep is free. Run across all seventeen playable games
it clears the same single level. **No level here ends by the piece standing anywhere**, which
retires a whole class of hypothesis rather than adding one.

### Two more things that did not work

**A local model choosing the goal changed nothing.** `goal_llm.py` shows qwen2.5:7b the
object list, the piece, the walls and the status bar, and asks for up to four ranked plans;
the planner routes them and `levels_completed` judges. It was consulted for real — 55s per
call, varied board-specific indices, zero request failures — and the mean over the nine games
came back at **0.456%, identical to the digit without it**. Two prompt defects had to be
fixed first and both are worth knowing: an example plan in the prompt (`[[2], [0, 2]]`) was
copied verbatim on boards where it made no sense, and the model pairs each plan with its
reason as `[[6], "reach the small object"]` about as often as it returns the bare list it was
asked for.

**Nine more games clear nothing either.** Of the sixteen games outside the MAZE_LIKE set,
nine expose keyboard actions; discovery gets a working movement model for eight of them
(`ft09` exposes only pointer actions, so there is nothing to drive) — and `cd82`, which the
earlier probe wrote off as NEEDS_POINTER, yields directions, confirming that false negative.
All eight then clear **0 levels**. Across eighteen games measured, exactly one level has been
cleared.

The eight games that clear nothing are not failing on movement — they have pieces,
footprints and directions. Their levels end on something other than walking onto an object,
and that is the next thing to find out.

## Next

1. **`ls20` level 5**, now reached, and **level 4 in far fewer than 306 actions** — it is
   weight 4 of 28, and the same level in 78 would take the game from 15.2% to 30.6%. Most of
   the 306 is the deliberate sweep for redirecting cells; a sweep that probes the cells on
   the route it actually needs, rather than the first unvouched-for cell it can reach, is
   the obvious saving.
2. **`ls20` level 3 in 68 actions rather than 203**, which is what the 1.15x cap wants and
   would take the game from 10.7% to its 21.4% completion ceiling. Most of the 203 is spent
   discovering the two changers before any plan can exist; a game whose mechanics carried
   across a level boundary would not pay that twice.
3. What ends a level in the eight games where walking onto objects does not.
4. `sp80`, which clears a level under some of the versions above and not under the one that
   shipped, on changes that have nothing to do with it. A level that falls at 175 or 266
   actions or not at all, depending on exploration order, is a lottery ticket rather than a
   capability — worth understanding before any of these numbers are read as skill.
5. Re-probe the false negatives from more than one starting state.
6. A harness under `OperationMode.COMPETITION` (one `make()` per environment, no resets)
   for a real baseline across all games.

## Testing

```bash
uv run python -m pytest -q
```

⚠️ If `rtk` is on the path it rewrites pytest's output — a run with failures was reported
as `Pytest: No tests collected` with **exit code 0**. Redirect to a file and read that.

## License

MIT-0. See `LICENSE`.

## re86: the framed-box family (2026-08-06)

`re86` is a COVER puzzle, not a maze and not a collection game. Every level draws
some shapes — 13-arm pluses, hollow diamond rings, X's, a 44-wide bar — and a set
of boxes, each a cell (or block) ringed by a single frame colour. Action 5 cycles
which shape the arrows drive, the board's only colour-0 cell rides the ACTIVE
shape's centre, arrows move it +/-3 on one axis clamped to the board, and every
shape and frame is transparent to the walk. **A group of boxes is consumed the
moment one shape covers ALL of it**; the level falls when every group is covered.
Level 1's four boxes share an x in pairs and a y in pairs, so ONE centre at the
intersection covers all four — 20 actions.

Two things had to be measured before any of that was visible, and both were
instrument problems:

- **The bottom row is a 100-action-per-level BUDGET**, filling at `round(0.64 n)`
  of 64 cells and ending the game at 64. It refills on level-up. Every action
  costs, including the toggle and a move that changes nothing. Two unexplained
  deaths in the previous session were this and a centre standing on a frame cell.
- **The modal centre of a shape's colour DRIFTS** once an arm clips the board
  edge or another shape overlaps it — track the colour-0 cell instead. And a
  shape's own cells must be read from what MOVES under a probe, one probe per
  AXIS (a shape shifted along an arm hides that arm in its own trail), because
  level 3 gives three shapes one colour and level 4 pairs a shape colour with a
  different box colour. An arm hanging off the board edge reads SHORT and is
  recovered by symmetry.

The rung is `cover.py`, gated on a signature that is re86 alone of the seventeen
at reset (a cell ringed by eight identical cells: `results/re86-sig.txt`), so
every other game is identical by construction. It answers None when it runs out
of ideas and the normal rungs take the level back.

Session 2 found the win condition's missing clause: a group is all the boxes of
one COLOUR, and it consumes only under shapes WEARING that colour — levels 1-3
hide this because every shape spawns in its group's colour. Level 4's 6x6
"legend" blocks are SWATCHES: paint pots that recolour the active shape on
contact, and the contact that counts is any CELL of the shape touching the
block, not the centre — a route that only steers the centre scrambles the coat
in passing, so every walk avoids each swatch dilated by the shape's own
offsets, except the colour it wears or is fetching. Two more measured rules:
a box whose ring is under an arm is invisible to the detector (the set is
accumulated across frames, removed only when its whole 3x3 reads background),
and a level can consume in WAVES (replan until the box set holds still).
**5/8 levels, [31, 56, 66, 80, 188], 41.477%** single-game, sweep clean.
Level 6 is a new mechanic — colour-1 WALLS (the game's first refusals), no
swatches, a sealed ring-with-hole as the only unexplained object; six
hypotheses measured dead in `results/breadth-recon.md` §session 2.

## sp80: the control-transfer family (2026-08-07)

`sp80` hands the arrows to a **different body** when you press action 5. From most
places it does nothing at all; level 1 ends from one column of them. Sweeping every
one of the 108 reachable positions with a fire, the nine wins are exactly the ones
with the driven block's left edge at x=24 (`results/sp80-p6.txt`), which is the
column that centres it on the pair of castles at the bottom of the board.

The rung is `swap.py`, and it is a SWEEP: fire from where you stand if that position
has not been tested, otherwise walk to the nearest untested one. It keeps no plan —
every round is read off the frame in front of it, which is what makes a death
harmless, because the block simply reappears at the level's start and the rung reads
where it is. The arrow mapping is not assumed (`ar25` answers ACTION3 with right) but
measured from the block's own displacement, and the driven colour is learned the same
way: the one body that translates as a rigid set between two frames.

**The magazine is the whole design.** The fifth press of action 5 in one life is a
GAME_OVER — and it MASKS a win: the identical position that levels up on a fresh
magazine dies silently as shot five (`results/sp80-p18.txt`, A against its own
control B). A sweep that marks every fired position tested therefore crosses off the
one position that answers the level and can never come back to it. So shots are
counted, the magazine size is LEARNED from the first death rather than assumed, the
last shot of a life is spent deliberately as a one-action reset, and the position it
was spent on goes back on the list. That reset is cheap because the play loop answers
a GAME_OVER with a level reset and carries on — the engine itself does not: without
that call it stays GAME_OVER and returns empty frames forever (`sp80-p17.txt`).

Two bugs are worth more than the code that fixed them:

- **A signature function and a per-round tracker are not the same instrument even
  when they read the same feature.** The life detector re-read the band structure
  every round to notice the clock refilling. The clock is a full-width BAND only
  while it is FULL — one burnt cell makes its row mixed, the colour drops out of the
  reading on the very first action, the refill is never seen, and the magazine stays
  unlearned for the whole run (`sp80-swap1.txt`, `mag=None`). Latch the colours from
  the level's first frame and count them whole thereafter.
- **A death is a rigid translation, so a frame pair that straddles one teaches the
  arrows a lie.** The block coming back to the level's start looks exactly like a
  move, and the arrow that had just been pressed had its vector overwritten —
  measured as a sign flip, `(0, 4)` → `(0, -4)`, against an honest-answer control
  that stayed clean (`results/sp80-d1.txt`). Ask whether the board was just put back
  BEFORE reading anything off the pair.

**sp80 0/6 → 1/6 levels, [16] actions, 0% → 4.762%**, sweep clean; the roster goes
6/17 → 7/17 games with a level. Level 2 is a measured wall rather than an unsearched
one: exhaustive BFS over the real engine — 39,328 states, `(board, ammo)` as the
visited key, depth 44 against the 45-action budget — finds no win within one life
(`sp80-p11.txt`), transfer legality is position-pure (`sp80-p14.txt`), the win is not
clock-gated at the natural candidates (`sp80-p15.txt`), and the level-2 board is
byte-identical for three different level-1 exits (`sp80-p16.txt`). An earlier null
from that same search was the INSTRUMENT twice over — a depth cap below the budget,
and fires-used missing from the visited key, because ammo is real hidden state.


## wa30: the carry family (2026-08-08)

One action grabs the crate the piece is **facing** — and the heading is whichever way it
last walked, so arriving beside a crate sideways refuses. That single rule killed the
first hand solve, which stood directly under a crate facing left. A second press drops
the crate; dropped over the 12x4 frame it slots in and eats the frame interior beneath
it for good, and the level ends when the interior empties. Level 1 by hand: 27 actions
against a baseline of 71.

The rung is `haul.py`, gated on a signature measured over all seventeen reset frames —
two or more crates, the biggest strictly bigger and wearing an interior colour none of
the others has — which wa30 alone shows. It clears level 1 in **43 actions**.

Nine bugs, and almost all of them one family: **a reading taken from a part of a thing,
or while something was standing on it, or with a detector that only works at reset.**
The displacement came from one colour when the piece's body is a 4x3 that swaps ends on
a turn. The piece was found by flood-filling non-background, so a carried crate touching
the frame swallowed the frame. The frame was re-detected each round, when the first
slotted crate stops its interior being one colour. Its free slots were read live, when
the piece covers what it stands on. A refused probe was not counted as attempted, so a
piece that starts under a crate presses UP forever. And the route walked straight through
crates.

The last one is worth keeping: fixing the eighth bug changed **nothing**, and a
byte-identical run after a code change means the change never mattered. Reading the trace
again with the filtering PRINTED rather than assumed showed the crate filter was correct
and the plan was aimed at the right crate — it was the walk that was wrong.


## tu93: the fixed-pitch maze family (2026-08-09)

A notched 3x3 piece on a 6px lattice, four fixed directions, walls, and a colour-14 goal
block. Level 1 by hand: 18 actions against a baseline of 19 (`tu93-verify.txt`). The
driver is `maze.py`, wired into the play loop like the other three, and it clears
**two levels in 31 and 14 actions** — 5.946%, tu93's first score
(`results/tu93-maze.txt`, `results/tu93-wired.txt`, `results/sweep-maze.log`).

Three things the repo's generic machinery could not do here, all of them readings:

* **The piece is not rigid in its own body colour.** The notch names the heading and moves
  to whichever side the piece last walked, so the body colour alone is not a pure
  translation of itself across a heading-changing press, and a `shifted()`-style check
  refuses a real move. The union of body and notch is the only rigid reading.
* **A life reset is a rigid translation, so a frame pair straddling one teaches a lie** —
  the sp80 lesson again, measured here as `dirs[4]` flipping to `(-12, 6)` on a board
  whose real step is `(6, 0)` (`tu93-life-reset.txt`). What detects the reset is a latched
  budget-band colour whose count goes UP; re-reading `bands()` each round cannot, because
  the band is a full-width row only while it is full.
* **Three of the four actions are dead from the reset corner**, so a refusal is not retried
  in place: ask every direction once from here, walk on one that works, ask the rest from
  the new position.

The signature is EXACTLY one notched 3x3 window at reset. "At least one" is not the
discriminator — the other sixteen games come back 0 or 3 to 69, by accident, on busy art
(`results/maze-sig.txt`); tu93's board is otherwise a clean two-colour grid where an 8:1
split almost never happens. Worth separating from the code: that table's two *candidate*
predicates each fire on five games, and neither is what `maze.signature` computes.
`sigs.py` runs every shipped predicate over all seventeen reset frames in one
invocation — maze fires on tu93 alone and no other driver claims it (`results/sig-sweep.txt`),
and the sweep is then identical to the digit on 16 of 17 games with tu93 the only change
(`sweep-haul.log` -> `sweep-maze.log`, mean 5.527% -> 5.876%).

**It stops at level 3, and the blocker is named.** The only route to that goal passes a
cell patrolled by a MOVING colour-8 hazard and the driver has no phase model — it
blacklists a square only after dying there (`results/tu93-death.txt`). Same class of
mechanic ls20's levels 6-7 needed, so it is its own project, not a bug. Measured on the
way: **tu93's GAME_OVER is not budget exhaustion** — it fires with 60 of 64 bar cells
left, on collision with that moving body (`results/tu93-budget-trace.txt`).


## tr87: the combination-lock family (2026-08-09)

Five stations on a 7-pitch lattice, each an independent 7-state cycle; one action dials
the station under the clamp, another slides the clamp along. The level opens when every
station holds its own target phase **at once** — and the board says which phase each one
wants, in a region an entire session had dumped and never matched against anything
(`results/breadth-recon.md` §tr87). Level 1 by hand: 28 actions against a baseline of 54.
The driver is `dial.py`, and it clears level 1 in **28 actions** — the same line, derived
in-run rather than looked up.

The reading, all of it off one frame and none of it a coordinate literal
(`results/tr87-probe20.txt`, whose control is the hand solution's five pairs):

* the HINT band and the ROOM are the two 7-row strips of the lower region; each has a
  frame colour and one ink colour, and the stations are the 5-wide windows on its lattice.
* a top (icon, block) pair is framed in **those two strips' colours** — the icon in the
  hint band's, the block in the room's. That is what pairs a tile to a meaning without
  knowing where it is: the icon says which station, the block says which phase of that
  station's deck.
* a pair whose icon names no station, or two, is dropped rather than guessed. tr87's
  sixth pair is exactly that.

Three things worth keeping:

* **A shape match, not a byte match.** Two of the five icons equal their hint exactly and
  three only up to rotation or reflection, so an exact comparison reads three of the five
  stations as unlabelled. The canon is dihedral-8 over both ink polarities.
* **"Dial until the window matches" is only correct because the deck keys are distinct.**
  Measured, not assumed: all seven states of every station have different shape keys, so
  the match cannot stop at a lookalike. That question is the one the plan rests on and it
  costs one probe to answer.
* **The drive needs no route and no arithmetic.** If the clamp is parked at a station that
  is not at its target, dial; otherwise slide. The slide wraps, so one action covers every
  station whichever direction it turns out to go — the direction is never assumed because
  it is never needed. Everything is re-read from the live frame, so a death costs the plan
  nothing.

**Level 2 is the same family with a different geometry, and the driver correctly declines
it**: seven stations rather than five, and a hint band on its OWN lattice offset that does
not line up with the room's, so a hint no longer names a station by position
(`results/tr87-l2.txt`). It answers None and the rungs take the level back.

The signature is the first that is **not disjoint from every other**: `cover`'s fires on
tr87 too (it fires on four games and engages one). The wiring settles it by asking `dial`
first, and `sigs.py` now checks that ordering for every contested game rather than checking
disjointness it no longer has (`results/sig-sweep.txt`).


## sk48: the skewer family (2026-08-11)

A machine rides a vertical track and extends a woven two-row arm sideways; three 4x4
blocks hang on the right wall, and the bottom HUD draws the goal as a picture: the arm
fully out with the blocks threaded on it in order. Extending until the braid reaches a
block THREADS it — it rides the arm from then on — and the level ends the instant the
last recipe block is pierced. No delivery trip. Level 1: **14 actions against a baseline
of 61**, found by `bfs_solve.py` over the real engine and replay-verified forward-only
(`results/sk48-bfs.txt`, `sk48-verify.txt`); the driver `skewer.py` clears it in 24, the
same capped score.

The hand model that preceded the search got two things confidently wrong, both from the
repo's oldest trap family — a reading taken from a part of a thing, or while something
covered it. Blocks "sliding along a dispenser queue" were blocks riding the arm, read at
misjudged x-offsets; a block "dropping off" when the machine moved was a refused vertical
move (a threaded block against the wall blocks travel — one retract clears it). The BFS
line embarrassed both misreadings in fourteen presses.

The braid is period three (`112112`), not a cell-by-cell alternation — the first braid
detector found nothing on the exact board it was written from. The driver's other three
lessons, each measured before it cleared the level: controls are learned BY NEED, not
upfront (three of six actions are dead from the reset state — the roster's no-op trap);
the room floor is LATCHED once per level (with the arm's tip pressed against a block, the
cell past the tip is the block, and deriving the floor from it reads the wrong room); and
a fully extended arm SPLITS the room's floor in two, so the room is flooded from both
sides of the arm and unioned.

**Level 2 is a rearrange puzzle wearing the same machine**: four blocks in one row, and
the recipe order (8, 12, 9, 14) is nearly the reverse of the row order the geometry
forces. Ploughing through threads all four and does not win. Whatever reorders them is
unmeasured — its own project, like tu93's level 3.

sb26, probed the same session, is the opposite outcome and is written up in
`results/breadth-recon.md`: every input channel measured dead at every reachable state —
clicks swallowed before the game logic (they do not even tick the clock), the free action
silent at all 64 bar lengths, the burn action a pure timer. A wall, filed behind dc22.


## The Kaggle port: the whole agent through a queue (2026-08-11)

The competition notebook drives an agent through `choose_action(frames, latest_frame)`
— it inverts control, where `compete.play` drives an environment. Rather than rewrite
seven hundred measured lines as a state machine, the bundle runs `play` UNCHANGED on a
worker thread against a proxy environment whose `reset`/`step` block on a queue;
`choose_action` answers the queue (`kaggle/adapter.py`). `kaggle/bundle.py` embeds all
fifteen modules (zlib+base64) into the one file the official starter kit splices into
the submission notebook.

Verified through the starter kit's own harness — the same `Agent.main()` loop the
Kaggle gateway drives: **ls20 7/7 WIN at 43.59%**, per-level transitions identical to
the local sweep to the action; the six driver games identical to their compete.py
numbers. Three traps that cost a run each:

* **`GameAction(v)` raises on every int** — the enum's `.value` is a property over a
  richer `_value_`, so lookup-by-call never works. Map `{int(a.value): a}` instead.
* **A module exec'd into a namespace must be in `sys.modules` BEFORE exec** — the
  `@dataclass` decorator resolves its own module through `sys.modules` at
  class-creation time, and registering after exec hands it `None`.
* **A per-round timeout is a fail-open kill switch, not a safety net.** ls20's level-6
  patrol planner legitimately thinks for minutes on one round; a 120s timeout killed
  the worker mid-level, the random fallback played the rest, and the run reported 5/7
  with no error anywhere — the tell was the accounting file truncated at the OS buffer
  boundary (never closed = worker still blocked) plus resets every ~130 actions in the
  tail (the fallback dying to the lives clock). The timeout is now 1800s and exists
  only against a true hang; Kaggle's own wall clock bounds the run.

What a submission still needs from a human: accept the competition rules, put a Kaggle
username in the starter kit's `kernel-metadata.json`, `make submit`, then Save & Run
All and Submit to Competition on the kernel page.
