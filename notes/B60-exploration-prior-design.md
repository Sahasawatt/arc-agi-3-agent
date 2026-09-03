# B60 — a per-game learned exploration prior as the harness's fallback on no-action turns

**Design ticket, 2026-09-02.** Route A of `arc-agi-pub/notes/think-research-deep-learning-before-draw-2026-09-02.md`.
Status: design → smoke (3 games) → decide on a full paired run. **0 slots until the oracle reads.**

Proposed MAP row (for the maintainer to land; this note is the body):

> | B60 | build | **Per-game online exploration prior (StochasticGoose-class CNN) as the fallback on no-action turns.** The only ARC-AGI-3 *trained* component with competition evidence (preview #1, 12.58% vs LLM agents ≤8%) aimed at the failure B52 measured (67% STARVED, 60% of stalls behind a sibling's frontier) and the run property B55 found predicts depth (cheap early levels). Smoke `thui-prior-v0` on g50t/sk48/tr87. Oracle = paired **levels** vs same-seed base, ≥2 runs per arm. | open |

## Question

Does giving the duck harness a learned, game-agnostic *which-actions-change-the-board* prior — trained online from the run's own executed actions and used only when the LLM turn produces no action — clear more levels on the 25 public games, read as levels in a paired design, before any hidden draw is spent?

## Why this and not the other DL routes (evidence)

- Every 100-RHAE system (NVIDIA AVO, Tycho) trains no weights; the same AVO harness on Qwen3.8 was in-band here (thui-avo-v0 4.40, p = 0.946 vs pooled v10 arm) → harness lane is model-bound at our model class.
- LoRA SFT on our own winning turns: held-out 2.45 / 3.69 vs base 4.61 / 6.35 → null (thui-lora e1 ×2).
- StochasticGoose: 4-layer CNN, 16-ch one-hot 64×64 → action logits + ACTION6 coord map, trained **during play** on `(state, action) → frame_changed`, no pretraining; won the preview against every LLM agent. Buys exploration efficiency, not reasoning (the foundation's own reading).
- Census: 67.3% of failed levels STARVED; B40 no-action turns and B45 abandoned generations are exactly the turns where the harness currently does nothing with the clock it spends.
- B55 step 1: runs that clear early levels cheaper go deeper (0.612 vs 0.501 ± 0.052 null, p ≈ 0.018).

## Seam (read from the live bundle `experiment/avo-v2` @ 74ff3df, byte-verified)

`_HarnessGameSession.play()` (`framework/solver.py:332`) calls `self.analyzer.analyze(state_path, action_count, valid_actions=…, step_env=self.step_env, …)` each turn and does `if not result.step_executed: continue` — that `continue` IS the no-action turn. Two facts make the seam cheap:

1. `step_env` is the session's bound method (`solver.py:724`): it takes `{"action": "UP"}` or `{"action": "MOUSE", "row": r, "col": c}` (also `{"actions": [...]}`), validates against `game.current_state.available_actions`, and returns `executed / board_changed / frame_count / level_completed / reward / action_name`. So `step_env.__self__` is the session → `_grid_from_state(session.game.current_state)` is the exact pre-action grid, and the return payload is the label. **Every** action the LLM takes also flows through this callable (the sandbox's `action()` → `_handle_action` → `step_env`), so wrapping it observes the LLM's actions for free.
2. `ToolAgent` is built per game (`_make_analyzer`) and cell 12 already wraps `ToolAgent` methods before `bm.run()` (the usage probe). Patching `ToolAgent.analyze` at class level from cell 12 keeps the upstream flow intact — the codebase-design decision of 2026-09-01 (subclass/inject at cell 12, never fork the dataset).

Injection (cell 12, after the inherited probe):

```
ToolAgent.analyze  ──wrap──►  rec_step_env = step_env + observe(grid_before, action, payload)
                              result = orig_analyze(..., step_env=rec_step_env)
                              if not result.step_executed and not retryable and not yielded:
                                  act = prior.propose(grid_now, valid_actions)   # one action
                                  payload = rec_step_env(act)
                                  if payload.executed: return AnalyzerTurnResult(step_executed=True, reasoning="thui-prior fallback")
                              return result
```

One fallback action per no-action turn; the harness then re-analyzes on the new frame as it would after any executed step. The prior never overrides an LLM action.

## The prior

- Input: grid → 16-channel one-hot, zero-padded to 64×64.
- Net: conv 32→64→128→256 (3×3, ReLU), action head (5 logits: ACTION1–5) from pooled features, coord head 1×64×64 map for ACTION6 (kept spatial, no flatten — StochasticGoose's own note).
- Label: `board_changed or frame_count > 1` (an animated action is never a no-op — `NoopGuard.observe`'s own rule).
- Buffer: per game, dedup on `(board_sig, action_sig)`, cap 20k. Train BCE, a few SGD steps after every executed action; **CPU**, so vLLM's VRAM reservation is never touched (smoke decides whether GPU is needed).
- Propose: restrict to valid engine actions; sample action type ∝ sigmoid(p) with ε-floor; ACTION6 samples a coordinate from the map; skip `(board_sig, action_sig)` pairs already observed as no-change (own tiny memory — the harness's `NoopGuard` lives inside the LLM's action path and is not reachable here).
- Cold start: before the first update the prior is uniform over valid actions = a random step, which is still one more scored action than a no-action turn spends.

## What could kill it (pre-registered)

1. **RHAE**: fallback actions are scored actions. If the LLM would have acted on the next turn anyway, the prior converts thinking time into wasted actions. Read: actions/level up, levels flat → kill.
2. **Trigger rarity**: if `step_executed == False` turns are rare in these games, the prior never fires and the run equals base. Smoke P1 counts fires.
3. **Instrument**: public-25 single run ranks nothing inside `[2.82, 5.24]`; a real gain has to show as **levels** (+1 in ≥6 games, B35 floor). Paired against a same-seed base, ≥2 runs per arm (B37: the seed does not reproduce), ~4 kernel runs ≈ 9 GPU-h. Mean is not the oracle.
4. **Cross-game transfer** (B55's real question) is out of scope for v0: the prior resets per game. A cross-game minor is a later cell-12 file in the same dir.

## Smoke — `thui-prior-v0`

thui-v1-1 chassis, cells 0 / 12 / 14 changed. Games = the three the census says die most: `g50t` (0 levels in 19/19 runs), `sk48` (19/20), `tr87` (17/19). Clock 900 s/game.

- **P1** the wrapper is installed and fires: log shows `thui-prior: fallback fired` ≥ 1 with an `executed: True` payload behind it.
- **P2** the prior trains: `thui-prior: update n=… loss=…` lines, loss finite, buffer growing.
- **P3** the harness path is intact: run reaches `COMPLETE`, summary.txt prints the 3 games.
- Numbers from the smoke are **not** a score and must not enter any ledger.

Then: full 25 paired run only if P1–P3 pass and fires > 0 on ≥ 2 of the 3 games.

### Smoke run 1 (2026-09-02 08:10 UTC, `sahasawatt/thui-prior-v0` v1) — P2 ✓ P3 ✓ **P1 ✗ (0 fires)**

COMPLETE in 15m33s; 58 actions over the 3 games; prior trained (100 updates, finite loss); harness
path intact. **The wrapper never fired because the trigger was wrong, not because dead turns are
rare.** Read from the event logs: g50t step 2 ended `Yielded control to solver: turn_time_budget`
and re-entered, again and again, until `stop_requested` — 7 analysis rows for 1 action in 900 s.
A turn that has not acted does **not** return `step_executed=False`; the 60 s yield returns
`yielded_control=True` and `play()` re-enters the SAME step. So the no-action signal *is* the yield,
and killer #2 ("trigger rarity") was a mis-specified trigger.

Two facts corrected in the same read: (1) games run **in parallel** inside `bm.run` — total wallclock
2,734 s ≈ 3 × 911 s against a 15m33s duration, so a 25-game run at 7,920 s/game is one 2.2 h slice
with 25 games sharing one vLLM server (this is also the campaign's open "~56 s/game" item: it was
never per-game serial time); (2) the yield REASON is not on `AnalyzerTurnResult` — only the bool —
but `session.should_stop()` separates `stop_requested` from `turn_time_budget`.

v2 trigger: fire on the **K-th consecutive yield since the last executed action** (K = 2, ≥ 120 s
silent), execute one prior action, hand the yield back unchanged so the step re-enters on the new
frame; the original `step_executed=False` path is kept. `yields_since_action` resets on any executed
action, the LLM's included.

### Smoke run 2 (2026-09-02 09:38 UTC, v2 trigger) — **P1 ✓ P2 ✓ P3 ✓**

COMPLETE in 15m00s. **4 fires, all `via=yield`, all `executed=True`, all `changed=True`** (DOWN ×1,
UP ×3), 0 level-ups; 6 prior updates; actions **58 → 84** (g50t 1 → 8, tr87 22 → 42, sk48 35 → 34).
Gate to the full run is met on the fire count; the per-game split is not readable from run 2's log
(the fire line did not carry the game id — added for v1). Numbers are smoke, not score.

Next: `thui-prior-v1` (cell 12 only, full 25 games, inherited clock), two runs (`v1`, `v1-r2`),
paired levels vs the pooled same-seed base (`thuiv1-1`, `thuiv1-1-r2`) with `rank_runs.py` under the
B57 baseline rule.

### Full run 1 (2026-09-02, `sahasawatt/thui-prior-v1`) — public **3.81, levels 20**, NOT-DISTINGUISHABLE

Against the same-seed pool (thuiv1-1 + r2, mean 4.78, levels 24): delta −0.97, **p = 0.5361**;
against the 4-run v10 pool (4.28): delta −0.46, p = 0.7592. Actions 1,607 (base 1,285–1,633), tokens
2.35 M (in band). **241 fires in 24 of 25 games, 203 (84%) changed the board, 1 level cleared by a
prior action directly.** Per-game levels vs the two base draws: **above both in 4** (cn04 0→1,
m0r0 0→1, wa30 0→1, sb26 2→4 — every one a game where base sat at 0–2), **below both in 5**
(ft09 3→2, lf52 1→0, r11l 1→0, re86 3→1, tu93 2→0 — games where the LLM was already progressing).
That is killer #1 in its predicted shape: a fallback that fires on silence cannot tell *stuck* from
*mid-plan*, and in the games with a plan its action is a scored disruption. Same trade the LoRA arm
showed (gain where base is dead, loss where base is alive), which is the signature of a lever that
adds variance rather than depth.

### Full run 2 (`thui-prior-v1-r2`) — public **3.92, levels 21**; pair verdict below

223 fires / 185 changed (83%), actions 1,510. Per-game vs the two base draws, **consistent across
both prior draws**: cn04, m0r0, wa30 **0 → 1 in 2 of 2** (base 0 in 2 of 2), ft09 **3 → 2 in 2 of 2**.
Everything else flips between draws (sb26 4 then 1, re86 1 then 3, lp85 1 then 3).

### Pair vs pair (B57 baseline rule, `pool_runs.py` → `rank_runs.py`)

| baseline pool | mean | levels | delta | p |
|---|---|---|---|---|
| same-seed base (thuiv1-1 + r2) | 4.78 → **3.87** | 24.0 → **20.5** | −0.92 | **0.4605** NOT-DISTINGUISHABLE |
| 4-run v10 arm | 4.28 → 3.87 | 24.0 → 20.5 | −0.41 | 0.6171 NOT-DISTINGUISHABLE |

**Verdict on B60 as built: NOT BETTER, and the sign is negative on both draws.** The mechanism is
proven (≈230 fires/run, 83–84% change the board, three dead games woken twice out of twice), and the
cost is proven with it: a silence-triggered fallback fires inside games where the LLM is mid-plan
(ft09 loses a level both draws) and the arm nets −3.5 levels per run. Same shape as the LoRA arm —
gain where base is dead, loss where base is alive — so a second lever now says the public-25
ceiling for *this* model is set by the games it already plays, not by the ones it never starts.

**What is left in this row, priced**: v1.1 = **progress-gated trigger** — no fire within N minutes
of a level-up or of a board-changing LLM action, K raised to 3 — keeps the dead-game wake-ups
(cn04/m0r0/wa30 are games where nothing changes for the whole clock) and stops the mid-plan
disruption by construction. One cell-12 minor in this dir, one more pair (~4.4 GPU-h, 0 slots).
If that pair is not above the base pair on **levels**, close B60. Do not spend a hidden slot on
any version of this arm before that reads.

### v1.1 built and in flight (2026-09-02) — `thui-prior-v1-1`, `-r2`

Same cell-12 payload, two constants: `_PRIOR_YIELD_K = 3`, `_PRIOR_QUIET_S = 300`. Progress clock
per prior: `last_progress` is reset by a level-up or by a board-changing action **not** issued by the
prior (`from_prior` flag around the fallback's own `step_env` call). Fire needs both the K-th
consecutive yield and `now - last_progress >= 300 s`. The builder is parameterised (`--v11`,
`--suffix=`); rebuilding `--full` still yields K=2 / QUIET=0 byte-for-byte (regression asserted).
⚠️ The first v1.1 push shipped a cell 12 that did not parse — a patch script wrote a literal
backslash-`n` into the raw-string template where a line continuation was meant — and was pushed
before `ast.parse` ran. The rebuilt notebook was pushed over it minutes later; the broken version
burns a few minutes of GPU and nothing else. Parse the cell **before** the push, every time.

### v1.1 run 1 (`thui-prior-v1-1`, 2026-09-02) — public **3.04, levels 20** — and the row CLOSES

144 fires in 21 games (v1: 241/24), 120 changed the board, every fire at quiet ≥ 310 s — the gate
worked as specified. It did not buy the outcome it was built for: **ft09 3 → 2 and re86 3 → 2 again**
(the LLM's plans on those games span silences longer than 300 s, so a silence gate cannot separate
*thinking* from *stuck* there either), while the dead-game wake-ups it was meant to keep were mostly
lost (cn04 0 → 1 kept; m0r0, wa30 back to 0). Against the same-seed base pair: delta −1.74, levels
24.0 → 20, p = 0.1565, NOT-DISTINGUISHABLE — the arm's worst mean of four runs.

**Why r2 is not needed to decide.** The oracle is the pair's levels against the base pair's 24.0.
With r1 at 20, r2 would have to clear **≥ 28 levels** for the pair to reach 24 — more than any
25-game run on this chassis has ever cleared at the standard clock (best 28 = v10cal/thui-v6-0;
clock2x's 30 needed a doubled clock). The decision is therefore fixed by r1 alone. r2's push also
did not land (the gate script reported the CLI returned no URL and the slug answers 404 — most
likely GPU quota after ~25 GPU-h on this account today); it was not retried.

**B60: CLOSED, null-to-negative.** Mechanism proven (the prior fires, trains, changes the board,
wakes games the base never starts); effect on levels negative on 3 of 3 full runs (20, 21, 20 vs
base 25, 23). Together with the LoRA arm this is the second lever whose signature is *gain where
base is dead, loss where base is alive*: for this model on public-25 the ceiling is set by the
games it already plays, and a fallback that spends scored actions on its behalf costs more there
than it earns elsewhere. A future version would need a trigger keyed on the LLM's own STATE (e.g.
its transcript declaring it has no hypothesis) rather than on time; that is a different design and
gets its own row if anyone wants it. **No hidden slot was spent on this arm.**
