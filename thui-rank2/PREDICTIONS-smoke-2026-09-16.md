# thui-rank2 smoke — pre-registered 2026-09-16 (before push)

Kernels: yocybercode/thui-rank2-anim-smoke, yocybercode/thui-rank2-fast-smoke (private). Games tn36 / vc33 / bp35 @ 1800 s.

VALIDITY (either fails = VOID, fix and re-smoke, no reading of levels):
- V1 `thui-rank2: pure teeth ok` and `THUI_RANK2_GRAFT ok` each print once.
- V2 `new ranker for game #3` prints (all three sessions reached the observe path).
- V3 `wrapper_errors` == 0 in the last STATS line, and no `analyze without a bound step_env`.

MECHANISM (the smoke's actual question — REACH):
- P1 >= 1 `VETO #` line per arm. Zero on both = the lever never fired; v2's reach fix failed.
- P2 inert_labels > 0 (HUD band or no-change labels exist on these games; the census saw 6.2% HUD-only actions).
- P3 reach: vetoes / proposals >= 3% on at least one arm (v1: 0.9%). Below that the full run cannot measure anything.
- P4 cost: train_s / observed <= 0.5 s mean; above that the prior slows the harness at 28-way concurrency — kill before full.
- P5 false_veto_proxy / vetoes <= 30%.

Levels on 3 games are NOT read as a score. Full-25 only if V1-V3 and P1, P3, P4 pass.

## r1 read (anim, COMPLETE 11:21Z) — VOID
V1 ok, V2 ok, V3 FAIL: 47 `observe error` = `CUDA error: out of memory` (t=673–936 s), mechanism unmeasured.
P1 13 vetoes (all ACTION6), P3 ~2.6% (below 3%), P4 FAIL: train_s 639 / 400 obs = 1.6 s per action inline.
Also read: anim bundle runs `hard_noop_guard=True` (upstream no-op guard already on).
Fix for r2 (same predictions, unchanged thresholds): every tensor pinned to cpu + a default-device probe line;
net 16/32/64/128/256 -> 16/16/32/32/64; 1 train step, batch 16.

## r1 read (fast, COMPLETE 11:25Z) — P4 FAIL, re-smoke as r2
V1 ok. V2 ok (games=3; the #1/#2 lines merged on one log line). V3 ok: wrapper_errors 0, no OOM on this base
(so the r1 OOM is anim-specific). Three Tracebacks are upstream `serving_teardown.py` after the run, not ours.
P1 33 vetoes (all ACTION6). P2 inert_labels 88/400. P3 21/383 = 5.5% at the 400-obs STATS line (PASS; v1 0.9%).
P4 FAIL: train_s 696 / 400 obs = 1.74 s per action. P5 false_veto_proxy 0.
Same r2 fix as anim.

## r2 read (both COMPLETE 12:20Z) — PASS both
anim r2: V1-V3 ok (probe = cpu, 0 errors). P1 30 vetoes (ACTION6). P3 24/804 = 3.0% at the last STATS. P4 0.082 s/obs. P5 0.
fast r2: V1-V3 ok (probe = cpu). P1 32 vetoes (ACTION6). P3 21/575 = 3.7%. P4 0.068 s/obs. P5 3/32 = 9%.
Watchara, 2026-09-16: "ถ้าผ่านแล้วส่ง full เลย" -> full-25 pushed for both.

# full-25 — pre-registered before push
Kernels: yocybercode/thui-rank2-anim-full25-r1 (vs the B71 build's public run), yocybercode/thui-rank2-fast-full25-r1
(vs thui-l1-ctl-full25-r1 and the fast pool). Oracle: eval/rank_runs.py paired per-game, --selftest first. n=1 per arm,
so NOT-DISTINGUISHABLE is the expected verdict and is not a loss.
VALID only if: wrapper_errors 0; train_s/obs <= 0.5 at 25-game width; vetoes/proposals >= 1% (reach survived width);
run completes inside the 32,400 s notebook budget. Otherwise VOID.
READ: levels vs comparator per game (B35 floor: no game loses a level it always clears), false_veto_proxy/vetoes <= 30%.
Submission: only if VALID and public levels >= comparator; the slot choice stays with a read of the submission record.

## STATE @ 2026-09-16 ~12:45Z (handover)
- Running: yocybercode/thui-rank2-anim-full25-r1 and yocybercode/thui-rank2-fast-full25-r1, pushed ~12:25Z, private, v1 each.
  ETA ~15:00Z (unmeasured; prior Flash-Next full runs ~2.5 h). Monitor btzkolbo5 in the old session may not survive a compact.
- Next on COMPLETE: `kaggle kernels logs <slug>` (JSON rows; join .data) -> check VALID block above -> `kernels output` ->
  `eval/rank_runs.py --selftest` then rank vs comparator -> LEDGER row + MAP B61 row (colleague repo: ask before commit).
- Comparators UNRESOLVED: anim vs B71 public run (thui-animfast-b71-full25-r1, public 9.5584 / 39 levels per its submission
  description); fast vs thui-l1-ctl-full25-r1 — neither fixture path confirmed yet.
- Nothing committed. Builder + this file live only in this clone, branch b61v2-rank2 (shallow clone of agent master f4c847a).
- Smoke logs were in the session scratchpad (gone after compact); re-fetch with `kernels logs` — slugs thui-rank2-{anim,fast}-smoke[-r2].
- Seam sources: ~/Claude/arc-artifacts/_src/b61v2-seams-2026-09-16/{keith,anim}/inference/.

## full-25 read (both COMPLETE 14:47Z; logs + outputs in runs/)
Comparator fixtures FOUND: eval/fixtures/thui-animfast-b71-full25-r1.json, eval/fixtures/thui-l1-ctl-full25-r1.json.
rank_runs.py --selftest: OK (6 controls) in the same session.
anim: teeth/graft ok, probe cpu, wrapper_errors 0 (0 observe/veto errors, 0 OOM, 0 Traceback), 25 rankers.
  train_s/obs 113.8/2200 = 0.052. reach 23/2217 = 1.04% at last STATS (obs 2200; 25 VETO lines total) -> VALID, barely.
  runtime 12:31:23 -> 14:44:06 = 7,963 s. vetoes ACTION6 14 / ACTION1 11. false_veto_proxy 3/23.
  vs B71: public 9.56 -> 8.07, levels 39 -> 36, 5 up / 12 down, p = 0.2599 NOT-DISTINGUISHABLE.
fast: teeth/graft ok, probe cpu, wrapper_errors 0, 25 rankers. train_s/obs 212.6/3600 = 0.059.
  reach 29/3118 = 0.93% at last STATS (obs 3600; 29 VETO lines total) -> FAILS the pre-registered >= 1% -> VOID.
  runtime 12:31:23 -> 14:43:31 = 7,928 s. vetoes ACTION6 18 / ACTION4 6 / ACTION1 4 / ACTION5 1. fvp 4/29.
  (for the record only) vs thui-l1-ctl: 8.64 -> 7.01, levels 41 -> 37, 4 up / 13 down, p = 0.5112.
Submission: rule not met on either arm (levels below comparator; fast VOID). Not submitted.
Slot 2026-09-16 still unused at 14:56Z (31 rows, newest 2026-09-15 15:52).
