# ka59 L2 — driving the corrected 7-step ticket line: BROKE_AT_LEG_3

2026-08-17. Verdict: **BROKE_AT_LEG_3** (box2 unreachable after the box3 fill). `levels_completed`
never left 1. No WIN. No config beyond y11's already-measured 2-of-3-filled result was reached.

Scripts: `ka59_t1.py` (full 7-leg driver of the corrected construction from breadth-recon.md's
2026-08-17 "ticket line BROKE AT LEG 1" tail), `ka59_t2.py` (diagnostic — isolates whether box2's
unreachability is caused by the box3 fill or pre-exists it). Raw logs: `results/ka59-corrected-
ticket-run.txt`, `results/ka59-corrected-ticket-diag.txt`.

## Per-leg table

| leg | action | piece after | phase | extra4 after | levels_completed | result |
|---|---|---|---|---|---|---|
| entry | — | (37,55) | (1,1) | [] | 1 | — |
| 1 | compound sweep: approach dot2 east (avoid dot0), press west | (49,49) | (1,1) | [] | 1 | **WORKS** — dot0 (34,44)/(34,45) → (13,44)/(13,45); dot2 (44,47..45,48) → (17,47)/(17,48)/(18,47)/(18,48). Both past the moat (x<30) in ONE press, confirming the compound sweep. dot1 untouched at entry. |
| 2 | fill box3: walk in, click dot1 (41,34) | (42,34) | (0,1) | [(55,40)] | 1 | **WORKS** — box3 filled (marker at piece's pre-click cell (55,40)), piece delivered to dot1's cell (rounded centroid (42,34)), phase (0,1) exactly as predicted |
| 3 (CHECK A) | exhaustive BFS: box2 interior reachable at phase (0,1)? | (42,34) | (0,1) | [(55,40)] | 1 | **BROKE** — 102-node exhaustion (queue drained, not cap-hit), reachable-box2 = **0 cells at ANY phase**, not just the wrong phase. Positive control PASS (a real press landed in the reachable set). |
| CHECK B (chain-kick dot2 north) | — | — | — | — | — | **NOT RUN** — leg 3 broke first |
| 5 (fill box0 via dot2) | — | — | — | — | — | **NOT RUN** |
| CHECK C / D | — | — | — | — | — | **NOT RUN** |
| 7 (final click on ticket) | — | — | — | — | — | **NOT RUN** (no ticket was ever minted — leg 3's mint click never fired) |

## Diagnostic (`ka59_t2.py`) — is box2's unreachability caused by the box3 fill, or pre-existing?

Reran leg 1 (compound sweep) identically, then ran the exhaustive real BFS **before** touching box3
or dot1 at all:

```
post-sweep (pre-box3-fill): piece=(49, 49) phase=(1, 1)
exhaustive BFS: expanded 129 nodes, 129 distinct reachable positions (EXHAUSTED)
reachable bbox: x=[31,61] y=[31,61]
box2 cells reachable (any phase): [(52, 52)]
box2 cells reachable at entry phase (1,1): [(52, 52)]
positive control: one real press landed at (52, 49), in reachable set: True (PASS)
```

**Box2 IS reachable right after the compound sweep, before box3 is touched** — 129-cell exhaustion,
`(52,52)` at phase (1,1) sits inside the same walkable pocket the piece already occupies (bbox
`[31,61]x[31,61]`, the same RIGHT-region pocket seen in every prior ka59 L2 session on this side of
the moat). This matches arm 1 of `ka59-phase-delivery-20260817.md` (`ka59_z1.py`), which minted
successfully by standing at this exact cell `(52,52)` at phase (1,1) directly from spawn.

**So the box3 fill is what disconnects box2, not a pre-existing gap.** Clicking dot1 delivers the
piece to phase (0,1) at `(42,34)` — a cell in a **different walkable component** than the RIGHT
pocket the piece was just standing in at `(49,49)`. The exhaustive BFS from that landing cell drains
its queue at 102 nodes and never touches box2's interior at all, at any phase. This is the same
family of result as `breadth-recon.md`'s ka59 L2 static-map-vs-real-router warning: a click is a
teleport across component boundaries, and the destination component's own walkability is a separate
fact from the departure component's — filling box3 first spends the piece's position on a component
that structurally cannot reach box2.

## Conclusion

**The corrected 7-step line, as specified in the recon tail, is not executable in the order given.**
Leg 1 (compound sweep) is confirmed working exactly as the recon predicted — both kicks fire from one
press, both dots land past the moat, dot1 is undisturbed. Leg 2 (box3 fill) is confirmed working
exactly as predicted — phase (0,1) delivered at dot1's cell. But leg 2's landing component is
disconnected from box2, which was reachable one leg earlier. The brief's own fallback (i) — "try
filling box3 from a different interior cell first... it changes nothing downstream" — is explicitly
inert by the brief's own reasoning (a click's landing cell is fixed by the clicked object's identity,
independent of the stand cell used to reach it), and the diagnostic confirms there is no rescue
available within the box3-fill-first order: box2 is unreachable from `(42,34)` regardless of how that
cell was reached.

**Not run, for lack of a specified path forward**: fallback (ii) applies only at CHECK B (dot2
chain-north failure), not at CHECK A, so it does not apply here. The one structural option the recon
tail itself named as a *known-working* alternative (from the prior `ka59_w1.py` session's own
docstring, not part of this session's prescribed fallback list) — mint via dot0 **before** filling
box3, i.e. reordering legs 2 and 3 — was **not attempted**, since it falls outside the fallback list
this brief specified (fallback (i) only) and the anti-goal against inventing new arms not in the
brief. Recorded per instruction (iii): the wall, with its full reachable census, above.

## Verdict

**BROKE_AT_LEG_3.** Config reached: box3 filled (1 of {box1,box3,box0}), piece at `(42,34)` phase
`(0,1)`, no ticket minted, `levels_completed=1` throughout both scripts. This is a genuine negative
result on the specific 7-step order given — box2 is reachable from the compound-sweep state but not
from the box3-fill state, so the order **box3-then-mint** (as specified) is structurally broken at
exactly the seam the recon tail asserted would hold (`"the current lattice"` assumption at CHECK A).
y11's prior-session result (2 of {box1,box3,box0} filled + piece in box2, via the box3-un-fill route)
remains the best config reached on this game to date.
