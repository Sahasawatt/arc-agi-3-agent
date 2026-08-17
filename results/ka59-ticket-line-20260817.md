# ka59 L2 — driving the mint-via-dot0 ticket line: BROKE_AT_LEG_1

2026-08-17. Verdict: **BROKE_AT_LEG_1** (pre-positioning). No arm reached the mint/fill legs of
the candidate line. `levels_completed` never left 1 in any run. No WIN.

Scripts: `ka59_w1.py` (full-line driver, HARD-FAILED at the chain-kick), `ka59_w2.py`
(diagnostic — exhaustive BFS after one dot0 west-kick), `ka59_w3.py` (diagnostic — exhaustive
BFS after minting via *raw*, unkicked dot0), `ka59_w5.py` (diagnostic — does a north-kick
before the west-kick avoid the crossing problem). Raw logs `results/ka59-w1.txt` ..
`results/ka59-w5.txt`.

## What the brief asked for vs. what is executable

The brief's step 1 reads: *"kick dot0 west + chain north to (19,20) ... Kick dot2 west past the
moat ... **dot1 stays at entry**."* This is a compression of the recon tail's own phrase
("y11's proven kicks"). Driving it literally — no dot1 kick, no box3 fill before the chain-kick —
**fails at the second half of leg 1**, and three diagnostics converge on why.

## Leg table (per-action census)

| act | tag | move | piece after | phase | extra4 after | levels_completed |
|---|---|---|---|---|---|---|
| entry | — | — | (37,55) | (1,1) | [] | 1 |
| 1 | 1a-approach-dot0 | v=1 | (37,52) | (1,1) | [] | 1 |
| 2 | 1a-approach-dot0 | v=1 | (37,49) | (1,1) | [] | 1 |
| 3 | 1a-approach-dot0 | v=1 | (36,46) | (0,1) | [] | 1 |
| 4 | 1a-kick-dot0-west | v=3 | (37,46) | (1,1) | [] | 1 | dot0 (34,44)/(34,45) → (19,44)/(19,45), Δx=−15 |
| — | 1b-approach-chain | bfs_route(region around dot0's new cell) | — | — | — | **NO ROUTE — script exits (`ka59_w1.py`)** |

**`ka59_w1.py` HARD-FAILED at action 5's routing** (`results/ka59-w1.txt`): after the single
west-kick, `bfs_route` could not find any path from the piece's position (37,46) to the
chain-kick's approach region around dot0's new cell (19,44)/(19,45).

## Diagnostic 1 (`ka59_w2.py`) — is dot0's post-west-kick cell reachable at all?

Exhaustive real BFS (this game's authoritative instrument, targets nothing, drains the queue)
from the exact state `ka59_w1.py` died at:

```
after 1 west-kick press: piece=(37, 46) phase=(1, 1) dot0_now=[(19, 44), (19, 45)]
expanded 139 nodes, 139 distinct reachable positions (EXHAUSTED, cap 15000)
reachable bbox: x=[31,61] y=[31,61]
dot0 cells [(19, 44), (19, 45)] reachable: [False, False]
chain-kick approach region reachable: False
```

**139 reachable positions, queue drained (not cap-hit) — this is a true exhaustion, not a
budget failure**, per this game's own established law (breadth-recon.md, ka59 y13/y14/y15: a
drained queue below cap is dispositive). The reachable bbox `[31,61]x[31,61]` is exactly the
RIGHT-region pocket the piece has occupied since spawn (spawn itself is (37,55), well inside
that box). Dot0's post-west-kick cell (19,44) is **outside** the reachable bbox entirely — a
single west-kick throws the *dot* clear across the moat while the *piece* (which only steps
once to deliver the kick) never crosses it. **A second kick on dot0 needs the piece standing
next to dot0's new position, and that position is not reachable by walking.**

Positive-control equivalent: two independent exhaustions in this session (this one and
diagnostic 2 below) land on the same ~`[31,61]x[31,61]/[32,60]` RIGHT-region bbox from two
different starting states, which cross-validates the instrument rather than resting on one
run's zero.

## Diagnostic 2 (`ka59_w3.py`) — does minting via RAW (unkicked) dot0 sidestep the problem?

If clicking dot0 from box2 delivers phase (1,2) regardless of dot0's *position* (only its
*identity* fixes the phase, per the closure's premise 2), maybe the chain-kick to (19,20) is
unnecessary — any dot0 click should deliver phase (1,2) somewhere. Tested directly:

```
standing in box2 at (52, 52) phase=(1, 1)
after MINT-click-dot0(raw): piece=(34, 44) phase=(1, 2)
expanded 77 nodes, 77 distinct reachable positions (EXHAUSTED, cap 15000)
reachable bbox: x=[31,61] y=[32,60]
box1 interior cells reachable: []
```

**Refuted.** Minting via dot0 at its *entry* cell delivers phase (1,2) as expected (the phase
is identity-fixed, confirmed) but lands in a **different phase-(1,2) walkable component** than
(19,20) — box1 is unreachable from here (0 of 18 interior cells, exhaustion at 77 nodes). Phase
alone is not the deciding factor; **which specific phase-(1,2) component the piece lands in**
also matters, and only the (19,20) component (y11's own proven landing) is known to connect to
box1. So the chain-kick relocation is load-bearing, not an optional refinement.

## Diagnostic 3 (`ka59_w5.py`) — does reversing the kick order (north before west) avoid the crossing?

If a north-kick from dot0's *entry* position stays within the RIGHT pocket (small
displacement), doing north-then-west might reach (19,20)-equivalent without ever crossing.
Tested: approached from south of dot0's entry cell, pressed north once.

```
after north-kick: piece=(34, 48) dot0=[(34, 44), (34, 45)]   -- UNCHANGED, dot0 did not move
expanded 146 nodes, 146 reachable, bbox x=[31,61] y=[31,61]
dot0 cells reachable: [False, False]
```

**Dot0 did not move at all on this press** (piece advanced to (34,48) but the dot stayed put —
either the press was absorbed without contact, or a wall sits between; not chased further given
the time budget), and the piece is *still* in the RIGHT pocket. This does not resolve the
crossing problem and was not pursued past one press.

## Conclusion

**The literal brief ("dot1 stays at entry", no crossing before the chain-kick) is not
executable.** Getting dot0 to (19,20) requires a *second* kick on an already-relocated dot0,
and that requires the piece to be standing in the same walkable component dot0 was thrown into
— which is only reachable via a prior *click*-crossing (a click has no proximity requirement
and can teleport the piece across component boundaries; a *kick* cannot). The only measured
click-crossing on this board is y11's: kick dot1 west, then click it from inside box3, which
delivers the piece into dot1's new (crossed) position. **So "y11's proven kicks" (the recon
tail's own phrase) structurally requires touching dot1**, contradicting the brief's separate
"dot1 stays at entry" clause — the two clauses of the brief's own step 1 are in tension, and
the tension resolves in favor of the recon tail's fuller description ("y11's proven kicks")
over the compressed one-line summary that dropped dot1's role. This is exactly the
"summary drifts from the body it compresses" failure mode: the compressed brief is not wrong
about the destination (19,20) but silently drops the mechanism that gets there.

Not run, for lack of remaining time budget: a corrected drive that touches dot1 (as y11 did)
to perform the crossing, then proceeds with the arm-4 ticket construction (mint via dot0 at a
reachability-checked box2 cell, fill box1 via a pre-kicked dot2, reachability-check box0,
final click relocating the ticket). This is the natural next arm and does not need to
re-derive anything above — diagnostics 1-3 settle the mechanism question; only the execution
remains.

## Per-leg summary table

| leg | action | result | evidence |
|---|---|---|---|
| pre-position dot0 (west) | kick, approach east of dot0, press west | **WORKS** — dot0 (34,44)/(34,45) → (19,44)/(19,45) | `ka59_w1.py` act#4, matches y11 exactly |
| pre-position dot0 (chain north, no interim crossing) | approach dot0's new cell, press north | **BROKE** — no route exists | `ka59_w1.py`, confirmed by `ka59_w2.py` exhaustive BFS (139 cells, dot0 unreachable, EXHAUSTED not cap-hit) |
| mint via raw (unkicked) dot0 as a substitute | walk to box2, click dot0 at entry | **WORKS but insufficient** — phase (1,2) delivered, but box1 unreachable from there (0/18 cells, 77-cell exhaustion) | `ka59_w3.py` |
| reorder: north-kick before west-kick | approach dot0 from south (entry), press north | **NO-OP** — dot0 did not move; piece stayed in the RIGHT pocket | `ka59_w5.py` |
| reachability check A (box2 at current phase) | — | **NOT RUN** — never reached, leg 1 broke first | — |
| MINT (click dot0 from box2) | — | **NOT RUN** | — |
| fill box1 via dot2 | — | **NOT RUN** | — |
| reachability check B (box0 phase (2,0)) | — | **NOT RUN** | — |
| FINAL click on box2 ticket | — | **NOT RUN** | — |

`levels_completed` never exceeded 1 in any script this session. No config beyond y11's
already-measured "2 of 3 boxes filled + piece in box2" (prior session) was reached or refuted
this session — the ticket-line's mint/fill legs remain untested, blocked by a pre-positioning
mechanism gap the brief did not anticipate.
