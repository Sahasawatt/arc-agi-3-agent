# thui-rs smoke — VOID on rule 1 (3 restarts), and the events show why the lever cannot pay (2026-09-16)

`sahasawatt/thui-rs-v0` vs `thui-rs-ctl`, sb26 / g50t / wa30 / ka59 @ 1,800 s, both COMPLETE 08:15 local (~40 min each, ~1.4 GPU-h,
0 slots). Outputs `kout-sa-thui-rs-{v0,ctl}/`. Graft markers ok, 0 wrapper errors.

## Rule 1 — 3 restarts (VOID by the letter), all late
Restarts fired on sb26 (turn 25), wa30 (28), ka59 (32) of 30–35 turns — the level-2 stall reaches 20 distinct turns only after
L1 took its 5–12 — so the fresh context got **2–5 turns** (3–6 actions). `restart_read.py`: 0 clears after a restart. Not readable.

## Where the actions went (the question asked)
| game | arm | turns | actions | levels | yields | actions/turn profile |
|---|---|---|---|---|---|---|
| sb26 | v0 | 26 | 79 | 1 | 5 (1 of 2 post-restart) | 1–3 all the way; post-restart `1 1 1 .` |
| sb26 | ctl | 38 | 226 | **3** | 2 | 1–2 early, then 9-action batches after L2/L3 cleared |
| ka59 | v0 | 33 | 96 | 1 | 3 (2 of 3 post-restart) | 1–2; post-restart `5 1 .` |
| ka59 | ctl | 41 | 267 | **2** | 1 | 9-action batches from turn 25 |
| g50t | v0 | 23 | 92 | 1 | 4 (no restart) | 1–6 |
| g50t | ctl | 31 | 107 | 1 | 1 | 1–9 |
| wa30 | v0 | 29 | 125 | 1 | 4 (**4 of 5 post-restart**) | 1–9 pre; post-restart `3 .` then 4 yields |
| wa30 | ctl | 38 | 300 | 1 | 4 | 9-action batches late |

Tokens per game are the same in both arms (v0 101–114k vs ctl 100–115k on the three full-clock games) — the model thought as much,
it just did not act. Three separate things:
1. **The fresh context yields.** After a restart the model sees a mid-level board with no history and no step summary and spends its
   turns re-deriving: wa30 4 of 5 post-restart turn ends were 180-s yields, ka59 2 of 3, sb26 1 of 2. A restart mid-level costs
   ~3–4 turns (~10 min) before the first real action — a fresh RUN starts at L1 with the game's opening; a fresh CONTEXT at L2 has to
   re-learn L1's mechanics from a board it never saw begin. That is Q2 of the ledger, answered against the lever.
2. **The stale context clears late.** ctl sb26 cleared L2 at turn ~27, AFTER the point where the rule would have restarted it (and
   ctl ka59 cleared L2 at turn ~25). Earlier, af-ctl bp35 and tn36 also cleared past turn 20 without any restart. So the rule would
   have thrown away clears that were coming — on sb26 the restart is exactly what stopped v0 at 1 level while ctl reached 3.
3. **Draw variance in batching.** ctl's action counts come from 9-action batches the model issues once it is "in" a level it
   understands (after clearing L2/L3); v0 never got there, so its per-turn count stayed 1–3. That is downstream of 1 and 2, not a
   separate cause. Pre-restart yields (v0 g50t 4 vs ctl 1, no restart on g50t) are draw noise at this width (af-ctl: 2/4/1).

## Correction to the ledger's oracle
C4/C5 ("cleared levels take median 10 turns, 84 % within 20; stalled levels burn 32") are **right-censored by run length**: a
25-way run gives a game ~35 turns, so no clear in that data could take 40, and "stalled" just means "the clock ran out". The 69 %
"sibling cleared it" was the family max over 32 runs, not the probability a fresh context clears it in the turns that remain. Both
biases point the same way, and the smoke measured the direction: forgetting costs turns and kills late clears.

## Verdict — PARK thui-rs; the "forget everything" pole is priced
Rule 1 VOID; the mechanism evidence (1) + (2) says a full-25 draw would read at or below control (wm's own pair already said keeping
knowledge across deaths changes nothing at p = 0.67; forgetting mid-level costs ~3 turns per restart and discards late clears). Two
narrower rungs, each cheap, neither built: (a) restart that keeps `_summarized_knowledge` and `_last_step_summary` and drops only the
history + reseeds ("new plan, same model" — B62-adjacent), (b) K tied to the game's own L1 clear time rather than a constant 20.
Neither has an oracle above noise after this correction. Cost: 2 kernels, ~1.4 GPU-h, 0 slots. Not harvested. Nothing submitted.
