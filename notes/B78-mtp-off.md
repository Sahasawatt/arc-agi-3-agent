# B78 — disable MTP on the frozen Flash-Next serving stack

Pre-registered 2026-09-10 before the first push. User authorized B77–B79, build, push,
PR/merge, submission and a post-submission relay in this session.

## Question and bounded interpretation

Measure MTP's marginal contribution on Flash-Next, not a model/volume percentage.
B77's aggregate 98.4 vs 58.5 actions/level reproduces, but does not identify intrinsic
per-action quality: deeper trajectories and different policies confound that ratio.
The 69/31 and 34/66 extrapolations remain descriptive sensitivity fits, not causal shares.
MTP-off holds weights and requested solver settings fixed; numerical/batching effects and
finite-run stochasticity mean identical token distributions are not empirically established.
A single ablation cannot separate model identity from quantization or prove equivalent policies.

## Artifact and one intervention

`thui-fast/build_mtp_off.py` reuses the existing builder. Full differs from the regenerated
B69 notebook only in cells 0/3/5/9/15: header, MTP 3→0, supported wheelhouse mount resolver,
server provenance checks, and matching competition root. No solver/harness/weight edits.
Smoke adds cell 13 budget 180 seconds and reduces the final selected list in cell 15 to
its first three games. It explicitly refuses a competition rerun. Full retains all 25,
7,920 seconds/game, analyzer 900 seconds, solver concurrency 28, server concurrency 8.
No ACTION7 patch is included: baseline is B69, not B76.

Source `serving_setup.py` is downloaded alone from the attached Keith Tyser dataset,
SHA-256 `037c041c9bd9dcffa9084b32f47af9cf1bf35849d5eaf2e1a3422daac098b2e2`.
The source already accepts MTP=0 and omits `--speculative-config`. Its default fast-start
mode is preserved explicitly; full synthetic preflight expects positive MTP and is not this arm.
Post-start check demands actual server argv without speculation, tuning=0, pinned model
revision, unchanged quantization, KV budget, concurrency and chunked/prefix settings.
Two planted bad provenance records must be rejected in the kernel before games start.

## Validity, outcomes and controls

1. Smoke: COMPLETE, source SHA holds, `B78_MTP_OFF_VERIFIED`, two in-kernel rejections,
   exactly 3 terminal game records and >0 total actions. Startup or coverage failure = VOID;
   fix mechanics and rerun smoke before full. Smoke score is never compared to public-25.
2. Full: COMPLETE, same serving checks, exactly 25 terminal records, >0 actions, zero watchdog
   restart attempts. Wall and per-game runtime must be recorded. Missing evidence = no verdict.
3. Primary baseline: `eval/fixtures/thui-fast-pool.json`, B69's TWO draws only.
   Run `eval/rank_runs.py --selftest` then rank full against the pool; include the two
   individual draws as descriptive sensitivity. Keep all 25 games; no chosen exclusion.
4. Report action ratio to baseline 3,739, level ratio to 38.5, tokens, elapsed wall, and
   paired score p-value. Action ratio <=0.8 is predeclared substantial throughput loss;
   >0.8 does not give a strong volume intervention. Lower actions and lower levels is
   consistent with MTP contributing progress; stable levels is not proof of equivalence.
   No percentage allocation to model vs volume from n=1, regardless of p-value.
5. Hidden: user authorized the resulting verified full candidate. Check current shared slot,
   latest version from the actual page, pulled attribution, and leader gate before submission.
   A single hidden draw is descriptive; do not turn its difference from 3.21 into superiority.

## Local verification

`python3 thui-fast/test_mtp_off.py /tmp/arc-b78-source/serving_setup.py` passed:
actual serving parser at 0/3, command differs ONLY by speculative-config, both bad-provenance
mutations rejected, smoke/full build and syntax checks. This is not a GPU/load result.

## Run record

Smoke and full completed in the handoff lane documented in workspace PR #312.
Full version 1 COMPLETE reverified 2026-09-10. Pulled notebook matches all 18 cell sources
of a fresh build from this builder; the completed version is reused, not repushed.
Actual benchmark.json: 25 unique terminal gave_up records, 4,049 actions, 40 levels,
mean 6.960912303027024, 20 scoring games. Rank against B69 pool p=0.5166, NOT-DISTINGUISHABLE
on the handoff log-rounded fixture; the committed fixture uses exact final_score values
and reproduces **p = 0.5163**, same verdict (`eval/rank_runs.py --selftest` green, 6 controls,
then the pairing re-run against `eval/fixtures/thui-fast-pool.json` on 2026-09-10). Quote 0.5163:
it is the number the committed artifacts produce.
Actual setup elapsed is 494.944 seconds from vllm-setup-provenance.json, not the
~624-second total overhead inferred by subtracting game wall from kernel elapsed.

The previously UNPROVEN watchdog condition is now directly observed:
results/b78/vllm-watchdog-status.json contains event=watchdog_stopped, restart_attempts=0.
Downloaded vllm_server_watchdog.py initializes this counter at zero, increments before
attempting recovery and writes the final status on stop (lines 361,398,430).
Teardown has identity_valid=true, port_closed=true, no surviving owned process records;
its GPU query still reported PID 220 using 90,684 MiB after process exit. Do not claim
complete GPU cleanup or attribute this post-score issue to MTP without a baseline.

## Next-submission decision (2026-09-10)

Choose this exact verified version for the first hidden observation of MTP-off.
The target estimate is this arm's hidden outcome distribution; one observation starts
it but cannot establish a mean, superiority, equivalence, or the model/volume split.
Repeating a7 is the alternative if estimating that exact build's mean is the objective;
it is not the selected objective today. Adding another serving/quantization arm would
leave the current tested arm unmeasured on hidden and B79 is not load-validated.
No follow-up GPU run is necessary to submit a version that already completed.
Board at 12:3xZ: Thuitanium 3.32 rank 248, top-five boundary 6.17, first 11.04;
this ablation is not a demonstrated path to closing that gap.
G1 page evidence: Version 1 of 1. G2/G3/G4/G6 dry-run passed without overrides.
Submission **56144280**, confirmed by competitions submissions at **2026-09-10 12:35:36.140000 UTC**, kernel version 1. Hidden result pending; do not resubmit.

