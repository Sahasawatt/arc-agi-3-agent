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

## Rules-legal note

All of tonight's probes ran offline against the local engine (`capture.py`, direct
`env.step`) — no scorecard consequence. `environment_files/` was never read.
