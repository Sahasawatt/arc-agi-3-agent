# Autonomous mechanic discovery — what the agent works out for itself

9 MAZE_LIKE games, 3600 actions total. Nothing here is configured per game: the piece, its footprint, what each action does and which colours stop it are all measured by acting.

| game | piece | footprint | step | directions | walked | blocked | walls found | floor |
|---|---|---|---|---|---|---|---|---|
| ar25 | colour 5 (2 parts) | 9x6 | 3 | 5 | 116 | 20 | [10] | [0, 9] |
| cn04 | colour 0 (3 parts) | 15x15 | 3 | 5 | 128 | 70 | **none** | [10, 14] |
| dc22 | colour 14 (1 parts) | 2x2 | 2 | 4 | 266 | 131 | [4, 9] | [2] |
| ka59 | colour 0 (1 parts) | 1x1 | 3 | 4 | 317 | 75 | [2, 15] | [1] |
| ls20 | colour 12 (3 parts) | 5x5 | 5 | 4 | 274 | 74 | [4] | [0, 1, 3, 5] |
| m0r0 | colour 10 (1 parts) | 5x5 | 5 | 4 | 230 | 64 | [11, 12] | [5] |
| re86 | colour 9 (5 parts) | 1x13 | 1 | 5 | 56 | 5 | **none** | [4, 5, 11] |
| sc25 | colour 9 (1 parts) | 4x2 | 2 | 4 | 166 | 119 | **none** | [2, 5, 10] |
| sp80 | colour 8 (1 parts) | 12x4 | 4 | 5 | 81 | 16 | **none** | [9, 12] |

## What this does and does not establish

- **Movement is solved.** All 9 games yield a piece, a footprint, a step size and a direction per action.
- **Walls are found on 5 of 9** (ar25, dc22, ka59, ls20, m0r0). Without a wall colour every cell reads as walkable, so BFS will happily route through terrain — a discovered model with an empty `walls` column is not usable for planning yet.
- **`ls20` reproduces the hand-read model exactly**: footprint 5x5, step 5, wall colour 4, and BFS to the goal box returns the same 6 moves the hand-tuned `solver.py` finds. That is the only game where the discovered model has been checked against a known-good one.
- **Goal identification is still hardcoded.** Knowing where you can walk is not knowing where to walk to; `solver.py` still names the target colours by hand. That is the next problem, and the harder one.

## Why a game ends with no walls

A wall is only observable from a move that *failed*, so the whole difficulty is meeting one. Four causes have been found by measuring, each now pinned by a test:

1. Cycling the actions in order oscillates in place — up then down is a no-op pair, so 48 actions gave 47 successful moves and one wall.
2. Breaking ties by action number walks in a straight line; `sp80` used one of its five actions across 48 presses.
3. Subtracting every colour inside the piece's bounding box, rather than the piece's own colours, subtracted the floor too: `ar25` returned 38 empty observations from 38 moves.
4. The run stopped at the first game over, so asking for 400 actions delivered between 26 and 152. Exploring offline is free, so it now resets and keeps going — which is what raised `sc25` from 1 blocked move to 49 and `ls20` from 5 to 79.
5. The walk keyed its novelty table on `hash(frame_bytes)`, and Python randomises bytes hashing per process, so consecutive runs of the same game took different routes and reported different pieces and different walls. Any number measured before that was one sample of a random variable. The key is now the raw bytes and two runs of the same game agree exactly.

## Identity: the defect that was upstream of everything

Objects used to be keyed on `(colour, cell_count)` and looked up in a dict. Two objects sharing that key in one frame collided and one was silently discarded — **55 objects across these 9 games at reset alone**, 19 of `dc22`'s 31 and 16 of `re86`'s 22. Everything downstream was reasoning about a partial board, which is why the inferred directions contradicted each other.

`identity.py` replaces the key with tracks: each one predicts where it should be, every object is scored against every track on position, colour and area together, and pairs are taken best-first. Any single attribute can then drift without the object being lost. Three further defects surfaced only once that was in place:

- Requiring a part to move with the piece on *every* action dropped it after one missed frame, so every game returned a one-part body — on `ls20` a 5x2 box for a 5x5 piece, whose own second colour then classified as a wall.
- A part that loses its track returns under a new id, splitting its agreement across two (measured on `ls20`: 171 and 106 of the player's 278 moves). Agreement is now judged against the frames each id was visible in, where both read 1.00.
- A model is built from track ids, and those die with the board. `locate()` finds the piece on any frame from the shape signature of its parts, which is what makes a model usable on the next level or in a scored run at all.

## What is left

`cn04`, `re86`, `sc25` and `sp80` still end with no wall colour. It is not an absence of walls — committing to one direction gets the piece blocked within 1 to 15 moves on all nine games — and it is not the amount of evidence: `sc25` collects 119 blocked observations and learns nothing from them, because its inferred directions still disagree with each other. Their pieces are still being mis-identified, just less often than before.

Three earlier versions of this file were wrong about the cause: over-segmented footprints, then open boards, then too little exploration. Each was a guess and each was disproved by measuring.

**Update 2026-08-05: the "mis-identified" diagnosis resolved into two measured defects**
(details + run evidence in `breadth-recon.md` §walls-not-found class): `infer_player`
voting by count elects sc25's metronome faller over the steered piece — measured, fix
built, but NOT LANDED: ar25's baseline level depends on its own metronome winning the
early vote (the incoherent model blocks planning, the wander meets the walls), so the
election fix ships only paired with an arrival-counted walk cap (see breadth-recon).
And `infer_dirs` handing a scattering action its most_common let one junk vector veto
`coherent` and wreck the step gcd — re86's "step=1" in the table above was this bug, not
the game — FIXED: no dominant vector (<0.6 over ≥3 samples), no direction. With it,
re86/sp80 reach coherent with clean dirs and correct steps in live runs. The next
stratum for this class: walls still never classify (`block=[]` after 2,000 actions) and
no goal rung fires; sc25 is additionally a SLIDER (per-press magnitude varies), which
the fixed-vector model cannot express yet.
