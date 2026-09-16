# thui-af smoke — VOID by rule 1, and the reason is the smoke's WIDTH (2026-09-15, bp35 / sp80 / tn36 @ 1,800 s)

`sahasawatt/thui-af-v0` vs `thui-af-ctl`, both COMPLETE 21:42 local (~45 min each, ~1.5 GPU-h, 0 slots). Outputs `kout-sa-thui-af-{v0,ctl}/`.

## Rule 1 — mechanism: 0 fires
v0: `THUI_AF_GRAFT ok`, anim graft ok, bm.label anim, **0 `THUI_AF_FLOOR`**, 0 wrapper errors. ctl: control marker. (Both logs carry
Keith's `serving_teardown.py` "bounded terminal gate" tracebacks after the audit, as anim-r2 did — a teardown artefact, not a run error.)

## Why it did not fire — the transcripts
| v0 game | turn ends | executed | yields | actions in 1,800 s | actions in anim-r2's 7,920 s |
|---|---|---|---|---|---|
| bp35 | 33 | 32 | 1 | 251 | 37 |
| sp80 | 59 | 58 | 1 | 163 | 70 |
| tn36 | 33 | 32 | 1 | 230 | 46 |

At 3-way concurrency the model acts on 32 of 33 turn ends; one yield per game, never two in a row. In the full-25 run the same games
yielded on 15–19 of ~35 turn ends. The stall the lever targets — 180 s of wall passing with too little generation done to reach an
`action(...)` call — is a **queue-load** phenomenon: at 25-way the per-stream rate is ~14 tok/s and a turn's thinking does not finish
inside the yield budget; at 3-way it does, every time. The smoke removed the cause of the effect by being narrow. Rule 1 therefore
reads VOID, not FAIL, and no 3-game smoke of this lever can read anything (PROJECT_PATTERNS: a rehearsal at reduced WIDTH cannot
see an effect whose cause IS the width; name what the subject shares with its siblings — here the vLLM queue).

## What the smoke also shows (descriptive, one draw each)
- Levels v0 bp35 0 / sp80 1 / tn36 0 vs ctl 1 / 1 / 2 — with the wrapper never firing v0 is a second control draw, and the tn36 2-vs-0
  spread is the same one the db controls showed (2 vs 0 on the same morning). Draw variance, not a lever effect.
- Action density at 3-way: 5× the actions of a 25-way run in a quarter of the time (a 20× rate). The stalled games are not stalled
  when the queue is empty — which is the m0 result seen from the other side: give them the throughput and they act (m0: 5,722 actions)
  and still do not clear (tn36 0 / 2 / 0 levels at 230 / 279 / 481 actions).

## Where this leaves the lever
The action floor can only be measured at full width, and its precedents at full width are B60 (null-to-negative, 3/3 draws) and B70 v2
(WORSE, p = 0.031) on the June duck — Watchara's 14:05Z finding. A full-25 pair costs 4.8 GPU-h and cannot resolve < 4 public points.
The mechanism itself (harness commits one action after two no-action turns) is teeth-proven and the execution seam is now proven live
in the sense that matters for B70's trap: the wrapper installed cleanly and the call shape is the solver's own `step_env`; whether a
fire returns `executed=True` on Kaggle stays unproven (0 fires). **PARK thui-af.** If it is ever drawn at full width, the read is the
B60 one: paired levels on the dead games vs the alive games, not the mean.

Kept: `thui-af/` (builder, teeth red on 7 mutations, 4 notebooks), this note. Nothing harvested (3-game smokes are not census rows).
