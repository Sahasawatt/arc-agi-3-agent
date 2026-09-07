# B70 — the ACT-NOW breaker on the duck chassis (`thui-act`)

Opened 2026-09-07, offline, 0 slots, 0 GPU. Build: `thui-act/build_notebook.py` (smoke `thui-act-v0`,
full `thui-act-v1`). Port of the AVO arm's breaker A (#135, `thui-avo/build_notebook.py --v1`).

## Why move it off AVO

The AVO arm shrinks **3.8×** public→hidden (4.40 → 1.15) against the duck line's 2.7× (LEDGER), so a
breaker that works there earns less than the same breaker on the chassis that owns the standing best
(2.03 hidden, thui-v1-1-r2). The failure class exists on duck: **B40** measured ~30 % of `analyze()`
turns ending with no executed action, and the per-level census (B52) puts 67 % of stalls in the
starved shape. Breaker B (exploit-off) has no counterpart on duck and is not ported.

## What the local replay showed (an 8B result, not a 27B one)

`scratchpad/avo_directive_all.py`, 2026-09-07: for each of the 25 AVO-v0 games, the turn at which the
directive would switch on (the 2nd of two consecutive dead pre-exploit turns) rebuilt from the
transcript and replayed on local qwen3-8b, base vs +directive ×2:

| | base | +ACT-NOW |
|---|---|---|
| action in the first tool call | 21/50 | **35/50** |
| any action in the turn | 31/50 | 36/50 |
| games acting on both reps | 6/25 | 16/25 |
| paired per game | — | up 13 · down 4 · tie 8, sign test p = 0.049 |

19 of 100 replies were empty (thinking spent the 1,500-token replay cap; 12 hit it exactly) — a
property of the replay, not of Kaggle's server-default output. The 8B does not reproduce the 27B's
93-turn stall (m0r0), so what this proves is that the directive is well-formed and shifts an
instruction-following model toward acting; whether the 27B obeys it is the run's question. The
supervisor's 30 STAGNATION paragraphs on m0r0 were ignored, which is the prior against it — the
directive differs from those in naming the mechanism (the yield cut) and the required FIRST call.

## The mechanism, and why the order is fixed by the score

`GameRun._compute_final_score`: a level scores `min(115, (baseline/actions)² · 100)` and only completed
levels count. An action spent on a level the model later clears costs score quadratically; a game
with no level scores 0 whatever it spent. So:

1. **directive** on top of the next user prompt after **K = 2** dead turns (**6** once a level is
   cleared) — costs no action;
2. **forced action** through the session's `step_env` only after **2 more** dead turns under the
   directive; **≤ 3 per level, ≤ 25 per game**; a withheld action leaves the directive on.

Seams: class-level wraps of `ToolAgent.analyze` (after-turn read of `result.step_executed`; the
solver passes `valid_actions` / `step_env` as keywords) and `ToolAgent._build_user_prompt` (directive
prefix; keyword-only `valid_actions` / `current_frame`, from which the cleared-level count is read).
State per agent keyed by the game read from the state-path stem (#127), reset on a game change.
`_last_step_summary` persists across turns, so every per-turn read is gated on `step_executed`.
Teeth: 20 assertions on a fake agent (thresholds, order, round-robin, per-level cap and ledger,
scoring-game thresholds, game reset, prompt wrap on/off), quiet so no fake `game=m0r0` line reaches
the run log. Base: `thui-v3-0`; cells changed [0, 12] (full) / [0, 12, 14] (smoke).

## Pre-registered read

- **Smoke (v0, m0r0 / tr87 / sk48, 1,800 s each)**: `directive on` fires ≥ 1× on m0r0; `wrapper error`
  0; forced ≤ 3 per level; 3 games finish; the 27B's first tool call after a directive is `action(`
  in ≥ half of directive turns (read the prompt log / transcript). Below half → the directive is
  ignored like the supervisor's and only stage 2 remains, which is a weaker build to carry.
- **Full (v1)**: `rank_runs.py` vs `thuiv3-pool`; B35 floor; forced count per scoring game ≤ 3 in the
  log (the cost side); dead-turn rate vs B40's 30 %.

## Not in this build

Breaker B; any prompt or clock change; the AVO arm itself (#135 stays as the AVO-side record).

## Smoke record (2026-09-07, sahasawatt/thui-act-v0 version 2, m0r0 / tr87 / sk48 at 1,800 s)

- Teeth line at 408 s (after the server came up); `wrapper error` 0; forced actions 0; 3 games finished.
- Directive fired **3×** (sk48 twice, m0r0 once). Reconstructed from the usage sidecars (a turn = `req_in_turn == 1`;
  executed = the action count rose before the next turn): sk48 `AAAAAAAA..A...`, m0r0 `AAAAA.AAAA...`,
  tr87 `AAAA.AAAAAAAA.`. The one directive that had a full turn after it (sk48, turn 10) was **obeyed** — the next
  turn executed. The other two fired on each game's last turn, which the clock cut (every game's final request is
  a `ReadTimeout` at the wall), so they count for nothing either way. n = 1 real test, positive.
- Dead-turn rate on the 27B duck here: **11 of 41 turns (27 %)** — B40's ~30 % reproduced.
- Actions in 1,800 s: tr87 55, m0r0 17, sk48 13 — the duck 27B acts on m0r0 where the AVO arm made 0 actions in
  7,920 s, so the breaker's stage 2 never arms on this chassis in the smoke; stage 1 is what a full run measures.
- Version 1 died at 6.5 s on Kaggle's flat `/kaggle/input/<comp>` layout (the solo trap); the builder now carries
  the mount resolver in cells 4 + 14. Full run `thui-act-v1` queued behind `thui-fast-v0` / `thui-gemma-v1`.

## Full-run record (sahasawatt/thui-act-v1, 2026-09-07 08:51–11:12Z, wall 8,458 s) — in the band; stage 2 never armed

Public **5.51 / 27 levels / 17 of 25 scoring / 1,661 actions / 2.20 M generated tokens**. `rank_runs.py` vs
`thuiv3-pool` (n=4): +1.12 mean, +2.75 levels, 10 up / 12 down, **p = 0.3177 → NOT-DISTINGUISHABLE**. B35 floor
**3 of 25** at +1 level (ar25, ft09, su15) against a floor of 6; 1 at −1 (lp85). Fixture banked
`eval/fixtures/thui-act-v1.json`. Same shape as the eleven levers before it: inside the same-build band.

What the breaker did, from the log and the 25 usage sidecars (765 turns):

- **Stage 1 fired 35 times** across 20 games (`ACT-NOW directive on`), wrapper errors 0.
- **Obedience 51 %** — of 116 directive-carrying turns that had a full next turn, 59 executed an action and 57 did
  not. Better than the supervisor's 0 of 30 on the AVO arm; not the ≥ half-on-first-call the smoke read hoped for
  once the 27B is under 25-way load.
- **Dead-turn rate did not move**: 289 / 765 = **38 %**, against the chassis's own 39 % (thui-compact-v1) and 41 %
  (thui-rank-v1) on the same sidecar reconstruction. The directive redistributes dead turns; it does not remove them.
- **Stage 2 never armed — and could not have.** `forced #` 0, `withheld` 0, while games sat at 4+ consecutive dead
  turns (tn36: 20 dead of 36). Cause, read from the bundle after the fact: the solver hands `analyze()` the ENGINE
  action names (`_engine_action_names` → `arcengine.GameAction.from_id(...).name`, i.e. `ACTION1`…`ACTION7`), and
  the wrapper filtered them against the MODEL names (`UP`/`DOWN`/…) — an empty candidate list, so `_act_pick`
  returned None and the forced branch was skipped silently, with no log line. The directive text fell back to the
  default action list, so stage 1 was unaffected. The teeth drove the breaker with `["UP", "DOWN", "MOUSE"]`, a
  fixture built from a belief about the harness (the AVO transcript's *prompt* prints model names) — the same
  shape as the `game_id`-is-empty trap in CLAUDE.md. Fix for a v2: normalise through the bundle's own
  `to_model_action` before filtering, and log the withheld case when the candidate list is empty.

Verdict: **stage 1 alone is in-noise on the duck 27B at full width**; stage 2 is untested here by a wiring
defect, not by a result. A v2 with the name mapping fixed would measure stage 2 for the first time — B40's
30–40 % dead turns are still on the table — but the honest prior from this draw is that a prompt-level nudge
does not move levels on this chassis (v12/v16/B32 already said so), and only the executed-action stage is new.

## Full-run record, v2 (sahasawatt/thui-act-v2, 2026-09-07 09:31–11:45Z, wall 8,480 s) — CLOSED

Public **2.47 / 19 levels / 16 of 25 scoring / 1,249 actions / 2.31 M generated tokens**. `rank_runs.py` `thuiv3-pool`
→ v2: −1.92 mean, −5.25 levels, 8 up / 15 down, 8 flipped, **p = 0.0309 → DISTINGUISHABLE, WORSE**. v1 → v2:
p = 0.0924, NOT-DISTINGUISHABLE. The two draws pooled (informally — v1 and v2 differ by the name-mapping fix, so
they are not declared one arm in `arms.json`): 3.99 vs the pool's 4.39, 10 up / 13 down, p = 0.3774, in the band.
B35 floor **1 of 25** at +1 (tr87), 4 at −1 (cd82, ft09, lf52, sc25). Fixture banked `eval/fixtures/thui-act-v2.json`.

What the fix bought, from the log and the 25 usage sidecars (732 turns):

- **Stage 1 fired 20 times**, wrapper errors 0, teeth passed at build. Obedience **43 %** (54 of 127 directive-carrying
  turns with a full next turn) — v1 was 51 %. Dead-turn rate **42 %** (304 / 732) — v1 38 %, chassis 39–41 %. The
  directive does not move the rate on this draw either.
- **Stage 2 armed in exactly one game.** ls20 sat at 37 dead turns of 42 (0 obeyed / 33 ignored) and crossed the
  scoring threshold (6 + 2 = 8 consecutive dead) three times; `forced #1 act=UP`, `#2 act=DOWN`, `#3 act=LEFT`, then
  the per-level cap withheld the fourth. **All three logged `executed=False changed=None level_completed=None`** — the
  `step_env({"actions": [act]})` call returned a payload without an `executed` key, so by the breaker's own reading
  nothing was executed for the model. The mapping fix worked (`_act_pick` returned model names); the execution seam
  did not. Whether the harness stepped the environment and reported it in a shape the wrapper does not read, or did
  not step at all, is not distinguishable from this log — ls20's level count did not move either way.
- Why only one game: the other 24 never reached 8 consecutive dead turns under the directive (after a clear, k = 6),
  and the no-level games (k = 2 + 2 = 4) that did have such streaks logged no forced line — consistent with `step_env`
  arriving as `None` on those turns, which the wrapper treats as "cannot force" silently. Not measured further.

Verdict: **B70 closed.** Two full draws, both prompt-level stages inside or below the band, and the executed-action
stage reached once and executed nothing through this seam. The one thing left unmeasured — a forced action that
actually steps the environment — needs the harness's real `step_env` return shape read from the bundle, not a third
draw of this wrapper. Against the same day's B66 result (the serving lane clearing the rule at p = 0.002), no v3 is
priced. Cost: 40 min smoke + 2 × 2 h 20 m full on sahasawatt.
