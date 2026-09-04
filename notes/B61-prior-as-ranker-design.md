# B61 — the frame-change prior as a RANKER / VETO over the LLM's own proposed actions

**Design ticket, 2026-09-02.** Route 2 of `arc-agi-pub/notes/deep-research-trained-components-arc3-2026-09-02.md`
(the only route in that corpus with a published *level* delta: StochasticGoose, preview 12.58% / 18 levels).
Successor to B60, which is CLOSED: the same prior used as a *fallback* that spends scored actions netted
−3.5 levels per run on 3 of 3 full runs. **B61 never issues an action.** Status: design → smoke (3 games) → decide.

Proposed MAP row:

> | B61 | build | **Frame-change prior as a veto/ranker over the LLM's proposed actions — spends no action, only refuses ones it predicts inert.** Same online CNN as B60 (per game, trained on the run's own executed actions), moved from the yield path to the `step_env` argument path: a proposed action whose predicted change-probability is below τ, after ≥N observations, is answered with the harness's own invalid-action payload so the LLM re-picks inside the same turn. Kill on sight if it ever degenerates into issuing actions (that is B60). Oracle unchanged: paired levels vs the same-seed base pair. | open |

## Why this role and not B60's

B60 proved the prior learns and predicts (83–84% of its own picks changed the board) and proved the
cost: any action the harness spends on the LLM's behalf is charged at RHAE and disrupts mid-plan games
(ft09 3→2 on every draw). A veto has the opposite cost profile — it can only *save* scored actions —
and its failure mode is a false veto, which costs one tool round-trip, not an action. The census says
what there is to save: B38 counted `tr87` firing one action family **226 times in a row**; B52 found
60% of stalls behind a frontier a sibling reached; the harness's own `NoopGuard` already blocks an
*exact* (state, action) no-op repeat, so B61 is that guard with generalisation across states.

## Seam

Identical wrap of `ToolAgent.analyze` as B60 (class-level, cell 12). Inside `rec_step_env(arguments)`:

1. Normalise the proposal: single `{"action": A, row, col}` or batch `{"actions": [...]}`.
2. Score each with the prior: `p_change(grid_now, action)`; ACTION6 uses the coord map at (row, col).
3. **Veto rule**: only when `prior.observed >= 20` for this game (cold prior vetoes nothing) and
   `p < 0.15`. A batch drops its vetoed members and executes the rest (never empties a batch — if every
   member is vetoed, the *first* is let through so the turn still acts). A single vetoed action returns
   the harness's own `_error_payload` shape — `{"executed": False, "error": "prior: <A> predicted inert
   (p=0.06); pick another action", "valid_actions": [...]}` — which is exactly what the LLM already sees
   for an invalid action, so the tool loop continues in-turn.
4. **Budget**: at most 2 vetoes per analysis step; the third proposal always executes. RESET is never
   vetoed. An action already observed as *changing* on this board signature is never vetoed.
5. Training unchanged: every executed action (LLM's, and after a veto the re-pick) trains the prior.

Every veto is logged with the proposal, p, and what the LLM did next; the **false-veto proxy** is the
case where the LLM re-proposes the same action, it executes, and `board_changed=True`.

## Pre-registered killers

1. **False vetoes on animated/latent actions** — an action that changes nothing visible but advances
   hidden state (sc25's absorbed first press; sp80's shot counter). The prior labels those no-change.
   Mitigation is the `frame_count > 1` label and the 2-per-step budget; the smoke measures the rate.
2. **Nothing to veto** — if the LLM rarely proposes inert actions after step 20, veto rate ≈ 0 and the
   run equals base. Smoke P1 is the veto count.
3. **Instrument** — as B60: paired levels, ≥2 runs per arm, +1 level in ≥6 games to read.

## Smoke — `thui-rank-v0` (tr87, sk48, sc25 · 900 s/game)

P1 ≥1 veto with `observed ≥ 20` · P2 prior trains (finite loss) · P3 COMPLETE, 3 games, no exception
in the wrapper (a wrapper error must never reach the harness — it degrades to pass-through and logs).
Report: vetoes / step, false-veto proxy count, actions vs B60 smoke (58 / 84).

### 2026-09-02 — built, NOT run: weekly GPU quota

`thui-rank/build_notebook.py` builds `taaf-thui-rank-v0.ipynb` (cells changed [0, 12, 14]; cell 12
parses; asserted to carry no `propose()` path). The push from `sahasawatt` failed with the CLI's own
message **`Kernel push error: Maximum weekly GPU quota of 30.00 hours reached.`** — which
`scripts/kaggle_push_kernel.py` reports only as *"(no url in its output)"*; the same message is what
killed `thui-prior-v1-1-r2` earlier today. Two ways forward, both zero-slot:

- wait for the weekly reset on this account, then `python3 scripts/kaggle_push_kernel.py repos/arc-agi-3-agent/thui-rank`;
- or push from the mac: `python3 thui-rank/build_notebook.py --owner=yocybercode` then the gate script
  (G4 will hold: the id's owner must match the pushing token).

Smoke oracle unchanged (P1 ≥1 veto at obs ≥ 20 · P2 finite loss · P3 COMPLETE, 3 games, 0 wrapper
errors). ⚠️ The gate script should print the CLI's error line verbatim on an empty status — it hid
a quota message twice today.

## Rebased 2026-09-04 onto the B48 chassis

Builder default is now `--base=v3` = `thuiv3/taaf-thui-v3-0.ipynb` (thui-v1-1 + yield 180: the build that drew the standing best 2.03 and holds the campaign's only 4-run public pool). The cell-12/14 seams are identical in that chassis (anchors asserted once; cell 8 asserted to carry the yield-180 injection twice). **Baseline for the paired read is the `thuiv3` arm** declared in `eval/fixtures/arms.json` (thuiv3-0 4.01 / thuiv3-0-r2 4.52 / thuiv3-1 5.17 / thuiv3-2 3.85; the three new fixtures banked from each run's `benchmark.json`, means reproducing the LEDGER), pooled as `eval/fixtures/thuiv3-pool.json`. Read: `python3 eval/rank_runs.py eval/fixtures/thuiv3-pool.json <candidate-pool>.json`, +1 level in >= 6 of 25 games on both candidate draws. `--base=v1` keeps the thui-v1-1 chassis for a control build only.

## 2026-09-04 — smoke pushed from the mac as `yocybercode/thui-rank-v0`

Built in a detached worktree at `d3e72ba` with `python3 thui-rank/build_notebook.py --owner=yocybercode --base=v3`; the
notebook came out **byte-identical to the tracked `taaf-thui-rank-v0.ipynb`** (only `kernel-metadata.json`'s `id` moved),
cell 12 `ast.parse` clean, 0 `propose(` calls. `scripts/kaggle_push_kernel.py` (G4: token identity `yocybercode` matches the
id's owner) → `Kernel version 1 successfully pushed`, status `QUEUED` — so the `sahasawatt` weekly quota was the only
blocker and the `yocybercode` account had room. **GPU quota only, no submission slot.** Smoke oracle unchanged (P1 / P2 / P3
above); the read is appended below once the run completes.

### Smoke read (`yocybercode/thui-rank-v0`, COMPLETE 2026-09-04 ~10:27Z, wall 1,347 s)

Read twice, independently — Sahasawat from `kernels output` (log + `_p0_events` sidecars + `benchmark.json`),
Watchara from `kernels logs` on the mac — every number agrees. Queue wait **~2h35m** (pushed 07:20Z, RUNNING
~09:55Z): the first measured queue wait on record; earlier notes had 38 min once and "no wait" twice.

- **P3 PASS** — 3 games finished (`tr87` 3 actions / `sk48` 11 / `sc25` 10, 0 levels), `wrapper error` 0,
  `observe skipped` 0, no action ever issued by the prior.
- **P2 PASS** — the one training update is finite: `thui-rank: update n=25 buf=10 loss=1.8076`.
- **P1 NOT EXERCISED** — `VETO` 0, `BATCH-DROP` 0. The veto arms at ≥ 20 observations per game and no game got
  past 11 executed actions in 900 s, so the branch the design is about never ran. Not a refutation: the smoke
  measured the harness path only.

**Next: `thui-rank-v0-1`** — same 900 s / 3-game smoke with the arming threshold lowered to **5** observations
(`build_notebook.py --min-obs=5`, smoke only; `--full` with any non-design threshold is refused by assert; cell 0
carries a "Smoke variant" line). It proves the veto PATH (score → harness invalid-action payload → LLM re-picks
in the same turn) once per game, and the false-veto proxy. Pushed from the mac 2026-09-04 10:53Z as
`yocybercode/thui-rank-v0-1`, QUEUED. Oracle unchanged. Then, only if the path behaves, `thui-rank-v1 --full`
at the design 20, paired vs the thuiv3 pool (2 draws).
