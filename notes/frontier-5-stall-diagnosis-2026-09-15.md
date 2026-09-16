# Why the agent stalls on the five frontier games (sp80, tn36, bp35, g50t, sk48) — 2026-09-15

Read from the artifacts of four full-25 draws (wm-v0, wm-ctl, b78-mtp0, animfast-b71): `_p0_events.jsonl` (every action,
`game_over`, `level_completed`, `board_ascii`), `transcripts/*_p0.txt` (the model's own world-model text and tool calls),
and the census. No environment file was opened. All numbers below are from those files; "ctl" = thui-wm-ctl-full25-r1.

## 0. The ceiling every game shares: ~52 decisions per game

Analysis turns per game in ctl: min 48, median 52, max 54 across all 25 games — 7920 s / 52 = **152 s per turn**, which is the
bench's c25 request wait (114-137 s median) plus generation. Actions per game vary 28-481 only because a turn can batch many
actions (tn36 ~9 clicks/turn) or none. **20-40% of turns end in `Yielded control to solver: turn_time_budget`** (yield 60 s)
with no action: ft09 37/51, re86 36/53, ls20 36/52, bp35 35/53, g50t 25/50. So a game gets ~30-40 executed decisions in 132 min.
Across 9 Flash draws corr(actions, levels) = 0.08; every draw had the same ~52 turns, so turns-vs-levels has never been varied.
The MTP-0 chassis (bench 65 s/request) would be the first run with ~100 turns/game — that, not "more actions", is what it tests.

## 1. tn36 — a known 61-tick budget spent on brute force (class: wrong goal model, lives as search budget)

Deaths at **exactly 61 actions after every RESET, 12/12** (5 in v0, 7 in ctl). The model's own world model at the end of ctl:
`Action model: solid (1 click = 1 toggle + 1 tick; expiry -> INIT + 61 ticks)` · `Goal model: exhaustive coverage of the 1024
mark-states; win presumed state-based` · `One-click-per-call is too slow (timed out after 25 clicks). Must batch.` It KNOWS the
budget and the death rule; it has decided the level is a 2^10 enumeration and is batching clicks to cover it, 61 per life, 7 lives,
481 actions, 0 levels. The board has no per-action counter (row-42 blocks toggle 2-4 times per life, they are the marks). b78
cleared 2 levels with 137 actions and 1 death — another draw found a rule instead of enumerating. Kept knowledge (wm) preserves the
wrong goal model; that is why v0 behaved identically (5 x 61).

## 2. sp80 — level 1 is a 30-action life, level 2 kills on SPACE; deaths used as probes (class: exploration by dying)

ctl: **11 deaths on level 1, each at exactly 30 actions**, 359 actions on level 1, cleared it on the last action. The model
reads the bar as a timer, plans `probe MOUSE on background cells ... then fall back to a SPACE sweep of untested row-44 columns`,
and its own tool output prints `SPACE (44,4) -> game_over True` three times in a row while it keeps sweeping. Level 2 (b78, v0):
**every death is SPACE** (8/8 in b78, 4/4 in v0). Note the one place the wipe guard visibly helped: v0 cleared level 1 in 2 lives
(79 actions) where ctl needed 11 — then spent 4 more lives on SPACE at level 2. B61 already named "sp80's shot counter".

## 3. bp35 — one click kills; a kept plan replays it (class: fatal-action repetition)

v0 died 10x on level 2; **7 of the 10 deaths were `MOUSE(row=33, col=21)`**, the other three the same row. ctl died once, on the
same cell, and stopped (28 actions; 35 of its 53 turns yielded). b78 died 6x on level 1 by LEFT/RIGHT/MOUSE(62,30) at 25-65 action
gaps. The wipe guard made this game WORSE: the kept plan contained the fatal click, and the harness's wipe had been the only thing
preventing the replay. A death blacklist (level, action_display) injected into the prompt is the cheap fix; nobody has built it.

## 4. g50t — the puzzle is real and the turns go to analysis (class: heavy reasoning under a 60 s turn)

0 levels in every run in the census (historic 19/19 per B60). No deaths, boards change 81-89% of actions. The model's world model
is coherent — `player, one connected red laser snake (tail + head + beam), ring goal (7,5), white hole (2,2), HUD, bottom bar` — and
it runs a 5x5-footprint walkability BFS in python every turn; 25 of 50 turns yield on the 60 s budget before acting. It concluded
the bottom bar is inert HUD (correct: it reached 0 with no game_over). What it lacks is the mechanic that opens the route (the
laser head / hole), and it has ~25 executed decisions to find it. Not a memory or budget problem; a search-space problem plus
yields.

## 5. sk48 — the model debugs its own board parser (class: perception tooling)

Cleared once in 9 draws (v0). No deaths, 53-182 actions, 80-98% board changes, moves only. Last world model in ctl: `beam clearly
grew again but parser still says L=0 — parser bug confirmed. Reading raw ascii strip of the ring row to measure beam extent
directly.` 23 world-model revisions, many spent on its own measurement code rather than the game. The harness already ships
`frame.segmentation` (objects with pixels/boundary), the model re-implements a parser per game and gets it wrong.

## What follows for levers

| lever | tn36 | sp80 | bp35 | g50t | sk48 |
|---|---|---|---|---|---|
| wipe guard (dropped) | no (preserves wrong model) | helped L1 | HARMED (replayed fatal click) | no | no |
| MTP-0 chassis (2x turns) | more lives, same enumeration | more sweeps | more replays | ~50 decisions instead of 25 — the one game where turns are the constraint | more parser debugging |
| stuck-game backoff (bo) | frees slots, changes nothing here | same | same | same | same |
| death blacklist (not built) | — | level 2 SPACE | YES | — | — |
| "budget seen -> plan, don't enumerate" nudge (not built) | YES (it already knows 61) | YES (30) | — | — | — |
| use `frame.segmentation`, forbid ad-hoc parsers (not built) | — | — | — | maybe | YES |

Nothing built so far addresses classes 1-2 (search strategy) or 5 (perception). Class 3 is one graft. Class 0 is the only thing
MTP-0 buys, and it is untested whether decisions convert (no draw has ever varied turns/game).
