# B73 / B74 — what the fast base does on the level it never clears (d2 events + transcripts)

Read 2026-09-08 from `sahasawatt/thui-fast-v0` **version 2's** own output (`artifacts/*_p0_events.jsonl`: every action
with level / `board_changed` / `level_completed`; every analyzer turn with its transcript). Version 1's output is no
longer fetchable (Kaggle serves the latest version's output), so every number here is **n = 1 (draw 2)**. Tool:
`eval/stall_read.py <events_dir> [game …]`. 0 slots, 0 GPU.

## B73 — click-only stalls: wrong target, or an action never tried? → **neither: the game IS click-only; the loss is the plan**

| game | failed level | actions / turns on it | board changed | distinct cells, top repeat | valid actions on that level | never tried |
|---|---|---|---|---|---|---|
| s5i5 | L3 | 115 / 36 | 65 / 115 | 31, (48,35) ×23 | MOUSE | — |
| ft09 | L4 | 79 / 30 | 62 / 79 | 27, (17,39) ×7 | MOUSE | — |
| sb26 | L2 | 166 / 49 | 163 / 166 | 23, (22,28) ×23 | MOUSE, SPACE, ACTION7 | ACTION7 |
| su15 | L2 | 76 / 45 | 75 / 76 | 57, (10,10) ×11 | MOUSE, ACTION7 | ACTION7 |
| tn36 | L1 | 251 / 52 | 251 / 251 | 52, (42,21) ×33 | MOUSE | — |
| vc33 | L4 | 103 / 33 | 103 / 103 | 20, (62,15) ×26 | MOUSE | — |
| r11l | L2 | 20 / 39 | 20 / 20 | 16, (25,4) ×2 | MOUSE | — |

- **Action-space blindness is ruled out on 5 of 7**: MOUSE is the only action the game offers there. On sb26 / su15 the
  one untried valid action is `ACTION7` — and the harness cannot execute it (below).
- **Wrong-target clicks are a minority except on s5i5**: 50 of s5i5's 115 clicks and 17 of ft09's 79 changed nothing;
  the other five games' clicks all moved something. So "perception" (upscale / render lever) has one clear case, s5i5.
- **The dominant shape is a wrong or unfinished hypothesis, searched slowly**: tn36 "≈150 configs failed … one untested
  dimension remains" (52 turns, 251 clicks on a 10-switch board); vc33 "overshot — P3 = 33 too high for the gate" (33
  turns on a fluid puzzle, rev 28 of its world model); su15 "each pair … new hypothesis" (57 distinct cells probed);
  sb26 "3 swaps to reach … no level_completed — maybe need SPACE or ACTION7 to submit"; ft09 "template-match fail,
  plainOR fail, next plainXOR"; r11l 39 turns for 20 clicks at 274 s / 3.8 k tokens per turn (thinking-bound, → B75).
  Each turn is one hypothesis test; at 30–50 turns per level the search does not converge inside the wall.

Verdict: **closed.** No prompt-side lever is charted from this — eleven of them sat in the band on the 27B and the
failure is the search itself, not a missing instruction. Two narrow, cheap things fall out instead: s5i5's dead clicks
(perception, one game) and the ACTION7 seam (B76).

## B74 — the deep-tail levels nobody has cleared: wall, or time? → **3 time-bound, 2 capability**

| game | failed level | reached it at | actions / turns on it | board changed | last world model (excerpt) | reading |
|---|---|---|---|---|---|---|
| tr87 | L5 | 5,928 s | 32 / 14 | 32 / 32 | "UP cycles glyphs through an ordered alphabet; measuring the cycle order from box E1b" | **time** — plan active, 1,992 s left |
| lp85 | L6 | 6,672 s | 29 / 10 | 29 / 29 | "Matching failed — check whether snapshots preserve tile-colour multisets" | **time** — 1,248 s left |
| sc25 | L4 | 7,600 s | 4 / 4 | 4 / 4 | still describing the board ("big barrel … probing whether arrow presses re-roll the grid") | **time** — 320 s left |
| vc33 | L4 | 2,734 s | 103 / 33 | 103 / 103 | "Overshot … no direct P3-drain button" | **capability** — 5,186 s, wrong model |
| ft09 | L4 (d2) / L5 (d1) | 3,711 s | 79 / 30 | 62 / 79 | "template-match (fail), plainOR (fail), next plainXOR" | **capability** — 4,209 s, hypothesis search |

tr87 / lp85 / sc25 reached their deepest level with 320–2,000 s of a 7,920 s wall left and an active plan: the seconds
were spent on the EARLIER levels (tr87 took 5,928 s for L1–L4). The lever for those three is not the tail level — it is
time per turn on the levels before it (B75's completion cap, or the serving itself). vc33 L4 and ft09 L4/L5 are the
capability wall: hours on one level, every click landing, the model's rule for the level wrong. Together the five hold
+92 of the deep games' +107 next-level points; **≈ 60 % of that is time-bound**, not wall.

Verdict: **closed.** Charted onward: nothing new on the wall side; the time side is B75.

## The ACTION7 seam (found on the way, minted as B76)

Six of the 25 public games offer `ACTION7` in their valid-action set every turn (ar25 51 turns, bp35 54, lf52 52,
sb26 54, sk48 49, su15 54). The harness **cannot press it**: `inference/agent/action_names.py`'s
`ENGINE_TO_MODEL_ACTION` maps ACTION1–6 + RESET only, so `to_engine_action("ACTION7")` returns `None` and
`solver.py:520` answers `Unknown action at index i: 'ACTION7'` with `executed: False` — while `_engine_action_names`
passes the same name straight into the prompt's "Valid actions right now" line. The model tried it **30 times across
the six games** (ar25 6, bp35 6, lf52 2, sb26 4, sk48 8, su15 4 `action()` calls naming ACTION7), got an error or an
all-`None` result each time, and on sb26 concluded *"all 4 slots filled … no level_completed — maybe need SPACE or
ACTION7 to submit"*. What ACTION7 does in those games is unknown (`arcengine` 0.9.3 defines it as a SimpleAction and
documents nothing); whether it is the missing confirm on sb26 / su15 / sk48 is exactly the smoke's question. Same
defect class as B70's stage-2 seam (an action the model emits that the harness drops), one line to fix, and it is in
both solver bundles (June duck and anim: `action_names.py` is byte-identical between them).

### B76 smoke record (sahasawatt/thui-a7-v0 v1, 2026-09-08 09:09–09:49Z, queue 4 h 16 min, run ~40 min) — PASS

Builder `thui-a7-sa/build_notebook.py` (fast base + mount resolver + the two-entry map patch in cell 9; notebook sha256 `a0ceacbd…`).
Read against the pre-registered items in the builder docstring, from the kernel's own log + `benchmark.json` + events:

1. **Patch landed** — `THUI_A7_PATCH ok engine_map=[ACTION1…ACTION7, RESET]` before any `inference` import; competition mount NESTED.
2. **ACTION7 executes** — 97 executed `action_name == ACTION7` across the three games (sb26 78, su15 14, sk48 5), **93 of them changed
   the board**; 0 `Unknown action` turns (V2: 0 executed, 30 attempts all refused). The first use came at action #2 (su15, 25 s) and
   action #5 (sk48, 30 s) — the model reaches for it unprompted, as it did in V2.
3. **Score** — levels in 1,800 s: **su15 3 of 9** (V2 full 7,920 s: 1; V2 by 1,800 s: 1), sb26 1 (V2: 1 / 1), sk48 0 (V2: 0 / 0).
   su15 cleared L1 at 105 s, L2 at 1,312 s, L3 at 1,635 s; score 7.83 vs V2's 2.22. Actions 806 over the three games at 3-way
   concurrency (V2's first 1,800 s: 71).
4. **What ACTION7 is** — the model's own read on su15, confirmed by the frames: *"ACTION7 undid the last placement: the token was
   removed and the dot reappeared … ACTION7 = UNDO."* It then used it as a probe primitive — `MOUSE(x), ACTION7, MOUSE(y), ACTION7, …`
   inside one Python call — to map the level's mechanic without spending state, which is how L2/L3 fell. On sb26 it undid 78 times
   on L2 without progress; sk48 stayed at 0.

Verdict: **PASS on item 3 (su15 > 1)** — an undo the harness had been refusing on six public games is a real action, and on one of
the three smoke games it turns a 7,920 s stall into two levels in 1,800 s. n = 1 smoke; the effect is one game so far. Priced next:
`--full` (thui-a7-v1, 25 games) — two draws pooled against the `fast` arm (n=2, 8.69) is the bar, B35 floor vs the same pool.
Cost 2 × ~2.4 h GPU on sahasawatt, 0 slots. Not started (needs the owner's OK).

### B76 full-25 draw 1 (sahasawatt/thui-a7-v1 v1, 2026-09-08 14:52–17:17Z, wall 8,540 s) — in band, low end; the smoke effect did not reproduce

Same builder `--full` (notebook sha256 `913bebea…`), competition mount drew the FLAT layout this time (the resolver from B71 is what
kept this run alive; his hardcoded cell 5 would have died at 6.5 s). Read against the pre-registered items:

1. **Patch + serving landed** — `THUI_A7_PATCH ok`, profile `kv5-bf16-mtp3-c8-cg32`, `MODEL_IDENTITY_ONLY files=419`, watchdog 0,
   `PUBLIC25_AUDIT runs=25 actions=3970`.
2. **ACTION7 executed 31 times** on the six games that offer it (sb26 15, sk48 5, ar25 4, bp35 3, lf52 2, su15 2), 30 changed the
   board; 0 refused (V2: 0 executed / 30 refused).
3. **Score** — public **5.76 / 34 levels / 21 of 25 scoring / 3,970 actions**. `rank_runs.py` `fast` pool (8.69 / 38.5) → this draw:
   **−2.93, −4.5 levels, 9 up / 11 down, 3 flipped, p = 0.0699 NOT-DISTINGUISHABLE**; vs `thuiv3-pool` +1.37, p = 0.18. Fixture
   `eval/fixtures/thui-a7-v1.json`. On the six ACTION7 games vs V2: lf52 **2** (V2 1), ar25 2 = 2, bp35 1 = 1, sb26 1 = 1, sk48 0 = 0,
   **su15 1 = 1** — the smoke's 3 levels in 1,800 s did NOT reproduce at 25-way concurrency over the full wall. The −2.93 is three deep
   games the patch cannot touch: tr87 2 (fast 4 / 4), lp85 2 (3 / 5), sc25 0 (0 / 3) = −65 of the −73 points — B74's time-bound
   tail, i.e. draw variance on the fast base, not the lever.
4. **Cost** — wall 8,540 s ≤ 8,700 s.

Reading, one draw: **ACTION7 executes and buys nothing measurable at full width** (+1 level on lf52 is inside the band); the smoke's
su15 result was a favourable 3-game draw. The pooled n=2 read is still the pre-registered bar; a second draw costs 2.4 h GPU and,
on this evidence, would price a NULL rather than a lever. Held for the owner's call.

### B76 full-25 draw 2 (sahasawatt/thui-a7-v1 v2, 2026-09-08 18:59–21:25Z, wall 8,496 s) — and the pooled verdict: CLOSED, in band

Same notebook (`--over`, sha256 `913bebea…`), mount FLAT again, `THUI_A7_PATCH ok`, `PUBLIC25_AUDIT runs=25 actions=3466`.
ACTION7 executed 45× (bp35 13, sk48 13, ar25 6, lf52 6, sb26 4, su15 3). Public **8.23 / 37 levels / 20 of 25 scoring**.
Fixture `eval/fixtures/thui-a7-v1-d2.json`. Draw 1 → draw 2: +2.48, 10 up / 9 down / 5 flipped, p = 0.087 — one build on the
same evidence the `fast` arm used (same bytes, same graft line), declared as arm `a7` in `arms.json`; note the within-build
spread (5.76 → 8.23) is as wide as the fast arm's (8.07 → 9.32) and wider than the chassis's.

**Pooled (the pre-registered bar)** — `pool_runs.py` → `eval/fixtures/thui-a7-pool.json`, **7.00 / 35.5 levels**.
`rank_runs.py` `fast` pool (8.69 / 38.5) → `a7` pool: **−1.70, −3.0 levels, 12 up / 8 down, 1 flipped, p = 0.4627 →
NOT-DISTINGUISHABLE**; B35 floor vs the `fast` pool 2 of 25 at +1 (ar25, sp80), 2 at −1 (lp85, tr87). `thuiv3-pool` → `a7` pool:
+2.61, +11.25 levels, p = 0.0316 BETTER.

Verdict: **B76 closed — ACTION7 (undo) executes on all six games that offer it (76 executions over two draws, ~97 % board-changing)
and buys no score at full width.** The smoke's su15 result was a favourable 3-game draw; at 25-way the six ACTION7 games sit where
V2 left them. The seam was real (a valid action the harness refused) and fixing it is free, so the map patch stays in the builder for
any future fast-base build — as hygiene, not as a lever. Nothing to submit from this arm.

**Member 3, 2026-09-09 — Watchara's `yocybercode/thui-a7-full25-r1` (public 8.25 / 38 levels / 3,843 actions; submitted 56099301 → hidden
3.32, the team best).** A different notebook build (sha256 `f35f95ac…` vs our `913bebea…`), so membership was settled the way the `avo`
arm's was — by MEASUREMENT, field for field from the runs' own artifacts, not by bytes: the 19-key analyzer/multimodal env subset hashes to
the same `6f0fd8dc…` on all three runs (his check, five serialisations tried, one matched — the control that the probe discriminates);
the vLLM serve command `argv_sha256 60b4549a…` matches (read from his public kernel output's `vllm-server-identity.json`, which he had not
banked); `git_status.txt` identical; the ACTION7 mechanism identical (same two dict entries in cell 9 before any `inference` import, same
`THUI_A7_PATCH ok engine_map=…` log line, no prompt edit in either build). Fixture `eval/fixtures/thui-a7-full25-r1.json`; `arms.json`
`a7` rule rewritten in the avo form.

**Pooled n=3** — `thui-a7-pool.json` **7.41 / 36.3 levels**. `fast` pool → `a7` pool: **−1.28, −2.2 levels, 12 up / 9 down, p = 0.4309
NOT-DISTINGUISHABLE**; B35 floor vs `fast` 0 up / 2 down (lp85, tr87). `thuiv3-pool` → `a7` pool: +3.02, p = 0.0129 BETTER. The verdict
does not move with the third draw; the arm's within-build spread (5.76 / 8.23 / 8.25) is the fast base's own.
