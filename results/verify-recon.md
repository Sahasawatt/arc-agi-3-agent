# Audit of breadth-recon.md: tr87, tu93, g50t, wa30

Independent verification pass over the four unaudited sections. Two claims were
already verified in the main thread and are not repeated here: tu93 level 1 falls
to `[4,2,2,4,1,4,2,2,3,3,2,4,4,2,4,1,4,2]` (18 actions), tr87 level 1 falls to
`[1,1,1,1,1,4,1,1,1,1,1,4,1,1,1,4,1,1,1,1,1,1,4,1,1,1,1,1]` (28 actions).

Method: for each substantive claim, open the exact run file cited and check the
printed numbers/text against the write-up's paraphrase. Where a script's own
correctness was in question (e.g. the deepcopy fork test, the "excl budget"
label), the source `.py` was also read.

## Audit table

| # | Section | Claim | Verdict | Evidence |
|---|---|---|---|---|
| 1 | g50t | Foundation: baseline_actions [78,175,179,230,96,54,67], 2,153 steps/s, replay-deterministic (21 frames), colour census incl. 82-cell colour-8 snake, 24-cell ring piece at (14,8) | CONFIRMED | `results/g50t-found.txt` — every number matches exactly; board dump shows the ring's centre cell (x16,y10) as floor colour 5, confirming "5x5 with the centre out" |
| 2 | g50t | Only actions 2 and 4 move the piece at reset (1/3/5 are no-ops apart from clock); clock burns 1 cell per 2 actions | CONFIRMED | `results/g50t-acts.txt` — actions 1/3/5 show "no change" except alternating clock ticks (9→1:1 on odd presses only); 2/4 show real 48-49 cell moves |
| 3 | g50t | Action 5 recalls the piece to x=14 (measured 38→14 on one press) | CONFIRMED | `results/g50t-p8.txt` press 1 |
| 4 | g50t | Standing on the colour-8 snake's head retracts 25 cells (incl. all of x14-18,y38-42) and opens 24 void cells (14 into floor, 10 into a new colour-8 segment) around x20-25,y37-43 | CONFIRMED | `results/g50t-acts.txt` ACTION4 press 3: `8->5:25 ... 0->5:14 0->8:10` (14+10=24), exact coordinates in `results/g50t-p6.txt`. Note: this specific sentence has no inline citation in the prose, but the numbers are exactly reproduced in `g50t-acts.txt`, which *is* in the section's header citation list — not a real gap, just worth knowing where the numbers actually live |
| 5 | g50t | Every one of those cells comes back on stepping off / recalling (not consumption) | CONFIRMED | `results/g50t-p7.txt` step 4 (total8 66→82 on leaving) and `results/g50t-p8.txt` press 1/3 (66→82 on recall) |
| 6 | g50t | A death restores the board exactly (census delta {} vs reset) | CONFIRMED | `results/g50t-p4.txt` part B: `census delta vs RESET BOARD: {}`, `colour0 3006 -> 3006, colour8 82 -> 82` |
| 7 | g50t | Exhaustive engine BFS (depth ≤130, clock+actions-taken key) finds no win; 12 reachable positions, goal box among none | CONFIRMED, and the exhaustiveness is real | `results/g50t-p3.txt` (25 states, 12 positions, first pass) and `results/g50t-p5.txt` (3,162 states, 125 deaths, same 12 positions). Read `g50t_p5.py`: `MAX_DEPTH=130`, loop is `while frontier and expanded<MAX_NODES`; it terminated at expanded=3162 ≪ MAX_NODES=60000, i.e. **frontier emptied naturally** — a true exhaustion, not a node-budget cutoff. Win detection asks the real engine (`o.levels_completed>0`), not the piece-shape-dependent `touch` diagnostic, so the "ring not block" caveat the write-up flags does not undermine this null |
| 8 | g50t | `deepcopy` is a true fork (control: parent unaffected, negative control proves the comparison can say False) | CONFIRMED | `results/deepcopy-check.txt`: "parent's next frame matches an untouched replica: True", "control (a genuinely different frame compares False): True". Note: an *earlier*, differently-built probe in `results/g50t-p4.txt` part A prints a contradictory "parent unaffected: False" — read `g50t_p4.py` line 78-79, that line's `np.array_equal(...)` call is malformed and its side effect (`env.step(A[5])`) mutates the parent mid-comparison; it is not a valid test and the write-up correctly does not cite it |
| 9 | g50t | BFS harness sanity: sp80 level 1 → `[4,4,4,5]` in 38 expansions | CONFIRMED | `results/bfs-control.txt` |
| 10 | g50t | BFS harness clears a maze too: ls20 level 1 → 13-action win | CONFIRMED | `results/bfs-control-ls20.txt`: `win=[3,3,3,1,1,1,1,4,4,4,1,1,1] len=13` |
| 11 | g50t | 20 deliberate deaths: board/action-5 response byte-identical to reset every time (nothing accumulates); baseline_actions[0] is the engine's level 1 (order check vs ls20/re86/sp80) | CONFIRMED | `results/g50t-p9.txt` parts A and B, exact numbers match (sp80 "39 against 16" etc.) |
| 12 | g50t | No hidden state along two different routes to the same board (0/14 frames differ); control route differs at 4/14 | CONFIRMED | `results/g50t-p10.txt` |
| 13 | g50t | Colour 8 as wall: 11 reachable positions, goal unreachable; as floor: 20 positions, goal reachable at (44,50) | CONFIRMED | `results/g50t-p2.txt` |
| 14 | g50t | Not the framed-box family: `cover.py g50t 12` gives up at i=6 | CONFIRMED | `results/g50t-cover.txt`: `signature: False`, `i=6 out of ideas at level 1` |
| 15 | tr87 | Foundation: baseline_actions [54,58,40,45,71,146], 2,824 steps/s, 14-cell C-clamp piece, colour-1 64-cell bar at y63 | CONFIRMED | `results/tr87-found.txt`, `results/tr87-probe1.txt` — exact cell coordinates for both brackets (7+7=14) reproduced |
| 16 | tr87 | ACTION3/4 move the clamp across exactly 5 fixed stations (step 7, wraparound); ACTION1/2 never move it; room_cells_changed=0 on every 3/4 press | CONFIRMED | `results/tr87-probe3.txt`: stations 15,22,29,36,43, wraps to 15 on 5th press; reverse wraps to 43 |
| 17 | tr87 | REFUTED #1: hint icon's colour-5 mask equals one of its own station's 7 reachable states (0 matches across 5 stations × 7 states × 2 polarities) | CONFIRMED as a genuine refutation | `results/tr87-probe10.txt` (hint cell counts 13,11,15,15,11 match exactly) + `tr87_probe10.py` confirms the script builds all 7 deck states per station and tests both `matches` and `matches_inv` |
| 18 | tr87 | REFUTED #2: aligning stations 0/3/4 to a shared symbol does not complete the level; only clamp-bracket cells change outside room+bar | CONFIRMED | `results/tr87-probe8.txt`: `levels_completed: 0`, changed-cell list is entirely station-0/station-4 bracket coordinates; also confirms period-7 for stations 1 and 2 |
| 19 | tr87 | REFUTED #3: stations 1 and 2 share zero states with each other (full 7×7 cross-check) | CONFIRMED | `results/tr87-probe11.txt`: `matches ... []` |
| 20 | tr87 | Three of five stations (0,3,4) share one byte-identical 7-state deck; station3=state4, station4=state2; stations 1,2 match none of it | CONFIRMED | `results/tr87-probe7.txt` — station indexing in the script's own comment ("station 1") is internally 0-based for x=15 (the write-up's "station 0"); self-consistent, not an error |
| 21 | tr87 | Persistence: dial state is not tied to clamp presence (read from a different column, no return trip, byte-identical); visiting all 5 stations with zero dial presses never wins | CONFIRMED | `results/tr87-probe12.txt` parts A and B |
| 22 | tr87 | Single station alone at its target phase, even with clamp returned to x15, never wins | CONFIRMED | `results/tr87-probe17.txt` — both station29@phase3 and station22@phase5 leave `lvl=0` |
| 23 | tr87 | Setting all five stations (15→5, 22→5, 29→3, 36→6, 43→5) wins on the action that completes the last one (43) | CONFIRMED | `results/tr87-probe18.txt` — exact match, `LEVEL UP -- stopping` on station43 |
| 24 | tr87 | haul-sig "5 crates" reading: only 3 of 5 rectangles sit in the interactive room; the other 2 (w4h5@(46,5), w3h3@(25,25)) are in the unrelated top glyph region; `signature()` already returns False for tr87 | CONFIRMED | `results/tr87-probe2.txt` — coordinates match exactly |
| 25 | wa30 | Foundation: baseline_actions [71,119,183,98,368,68,79,442,415] (9 levels), 6,064 steps/s, background colour 1 (3,920 cells) | CONFIRMED | `results/wa30-found.txt` — exact match |
| 26 | wa30 | Piece carries a heading-tracking colour-0 edge (union of colour-0 + colour-14, not colour-14 alone); a colour-14-only reader reports a position shifted by one at exactly the steps where heading changes, e.g. (29,40) and (16,37) | CONFIRMED | `results/wa30-p1.txt` — `piece()` in `wa30_p1.py` reads `g==14` only; the printed lattice breaks exactly at the up→left transition (32,41)→(29,40): Δx=3,Δy=-1 instead of a clean step of 4, and again at left→up (17,40)→(16,37) |
| 27 | wa30 | A box's ring turning 4→3 is proximity, not state: it reverts when the piece steps away (steps 1&3, and again 10&15) | CONFIRMED | `results/wa30-p1.txt` — B3 ring: 4→3 (step1, "up"), 3→4 (step3, "left" away), 4→3 (step10, approach), stays 3 through step14 (refused presses beside it), 3→4 (step15, moves away) |
| 28 | wa30 | Engine BFS reaches 27,953 states at depth 12 after ~10 minutes and does not exhaust — the tree is too wide to search | CONFIRMED | `results/wa30-bfs.txt`: `expanded=16000 ... states=27953 depth~12 ... t=629s`; frontier still 11,953 and growing, never terminates by exhaustion (contrast with g50t's true exhaustion above) |
| 29 | wa30 | Rule 3 (drop over the frame slots in permanently, not occlusion): colour-2 count unchanged between "inside" and "read from afar" readings (12→12) | CONFIRMED | `results/wa30-p5.txt`: census after drop `{2: 12, ...}`, census after stepping off `{2: 12, ...}` — the 8 consumed cells (20−12) stay consumed |
| 30 | wa30 | Level 1 falls by hand in 27 actions | CONFIRMED | `results/wa30-solve.txt`: `*** LEVEL 1 CLEARED in 27 actions ***` |
| 31 | wa30 | Rule 4 citation: "the level ends on the press that takes it to zero (`wa30-solve.txt` step 26: slots 6 -> 0 -> lvl=1)" | **CONTRADICTED** | `results/wa30-solve.txt` line-by-line: the 6→0 transition happens at **step 24** (`24 left: ... slots=0 lvl=0`), not step 26. Step 26 itself reads `carried=(12,8,15,11,16) slots=60 lvl=1` — slots=60 (level 2's fresh count), not 0. No single line in the file shows "slots 6→0" simultaneously with `lvl=1`. The broader mechanic (frame counter reaches zero, then the final drop completes the level) is still directionally right — box 3's real consumption happens at the step-26 drop, and the step-24 zero is most likely the same cells being occluded by the piece+box passing over the frame's last slot before the official drop — but the specific line cited does not exist as described |
| 32 | tu93 | Foundation: baseline_actions [19,16,34,42,123,80,14,23,111] (9 levels), 8,905 steps/s, notched-3x3 piece, colour-4 notch at mid-right (16,17) in (y,x) order | CONFIRMED | `results/tu93-found.txt`, `results/tu93-p1.txt` — colour4 cell is exactly `(y=16,x=17)`, i.e. mid row / right column of the y15-17,x15-17 block |
| 33 | tu93 | Notch rotates with heading: bottom-middle after moving down twice | CONFIRMED | `results/tu93-p1.txt` retry block: after two `action2` (down) presses, colour4 cell is `(29,22)` — bottom row (y=29 of y27-29), middle column (x=22 of x21-23) |
| 34 | tu93 | Action2 refuted as a no-op: fires twice (18 cells changed each) before hitting its own wall, when retried from a different tile | CONFIRMED | `results/tu93-p1.txt`: `action2: 0: 18 ... 1: 18 ... 2: 0 ...` |
| 35 | tu93 | Level 1 win replay uses all four actions (1/2/3/4), corroborating "four ordinary directions" rather than one being special | CONFIRMED (indirect) | `results/tu93-verify.txt` — the 18-action win sequence fires action1 (×2), action2 (×7), action3 (×2), action4 (×7), all producing progress toward the win; a true no-op or one-shot-special action would not appear productively in a BFS-shortest solution |

## Findings not elevated to the table (checked, minor/non-issues)

- `g50t_p4.py`'s deepcopy sub-test (line 78-79) is buggy (malformed `np.array_equal` call with a side-effecting `env.step(A[5])` inside it) and its printed "parent unaffected: False" is not meaningful. The write-up does not rely on it — it cites the correctly-built `deepcopy-check.txt` instead. Flagging only so nobody re-derives from `g50t-p4.txt` part A.
- `tu93_p1.py`'s "changed_cells(excl budget)" label in the `== walk action4 up to 20x ==` block does **not** actually exclude the budget row (no y=63 mask applied there, unlike the retry block below it which does mask it). This makes most of those per-press numbers (mostly 1-2) budget-tick noise, not piece movement — a script-hygiene bug, not a write-up error, since the write-up doesn't quote those specific numbers.

## Worst problem

Finding #31 (wa30 rule 4 citation) is the one CONTRADICTED item: the specific
run-file line quoted for "the level ends on the press that takes it to zero"
does not exist as described — the counter actually reaches zero two actions
earlier than claimed, on an ordinary move rather than a drop, and the cited
step instead shows level 2's slot count. This does not appear to undermine the
underlying mechanic (frame-inner-as-counter, three boxes filling it, win on
completion) — which is otherwise well supported by `wa30-p5.txt`'s clean
inside/afar comparison — but the specific evidence pointer is wrong and would
mislead anyone trying to re-derive the exact transition step.

Everything else audited, including all three named REFUTED entries in tr87 and
the exhaustive-search null in g50t (verified as a true exhaustion, not a
node-budget cutoff, and immune to the piece's ring-vs-block shape because win
detection asks the real engine), holds up against its cited run file.
