# thui-a3 — pre-registered 2026-09-16 before the smoke push

Change vs thui-animfast-b71-full25-r1: cell 13 appends the A3 graft (WORLD_MODEL store + prefix + verify_world_model +
prompt block); smoke also cell 15 (tn36 / vc33 / bp35 @ 1800 s). Serving profile unchanged (kv5 mtp3 seqs8).
Local teeth: real anim-bundle sandbox, control green, 4 mutations red (test_a3_local.py).

## smoke — thui-a3-wm-smoke
VALID (any fails = VOID, fix and re-smoke):
- V1 `thui-a3: teeth ok (7 checks, real sandbox)` and `THUI_A3_GRAFT ok` each print once.
- V2 no `thui-a3: store error` / `post error` / `prompt error` lines; run COMPLETE; 3 games in benchmark.json.
MECHANISM (the smoke's actual question — does a local model use the tool at all?):
- P1 WORLD_MODEL saved in >= 2 of 3 games (transcripts: `WORLD_MODEL =` in python code). 0 games = the lever is inert on this model -> stop, no full run.
- P2 verify_world_model() called >= 3 times in total (transcript stdout `A3_VERIFY`).
- P3 cost: actions per game not below 50% of thui-rank2-anim-smoke-r2's on the same games (the prompt block and model upkeep must not eat the clock). Report generated tokens.
- P4 at least one save after a verify miss (the loop closes: verify -> fix). Report count; 0 is a note, not a kill.
Levels on 3 games are NOT read as a score. Full-25 only if V1, V2, P1, P3 pass.

## full-25 — thui-a3-wm-full25 (if smoke passes)
VALID: V1/V2 as above, 25 games, inside 32,400 s. READ: rank_runs.py --selftest, then vs eval/fixtures/thui-animfast-b71-full25-r1.json.
n=1: NOT-DISTINGUISHABLE expected, not a loss. Submission only if VALID and public levels > B71's 39.

## smoke READ (COMPLETE 16:10Z; fetched 17:25Z / comparator 01:36Z 09-17 — vault locked in between)
V1 ok (teeth 1, graft 1). V2 ok (0 graft errors; 3 Tracebacks = upstream serving_teardown.py, same as every run on this chassis), 3 games.
P1 PASS: WORLD_MODEL saved in 3/3 games (bp35 25, vc33 15, tn36 7 saves; STATS at 200 python calls: saves 45, calls_with_model 188).
P2 FAIL: verify_world_model() called ONCE in the whole run (tn36: exact 0/14, raised 14 -- predict crashed on every transition).
P3 FAIL: actions vs thui-rank2-anim-smoke-r2 (same games, same clock): tn36 199/210 = 0.95, vc33 200/415 = 0.48, bp35 59/249 = 0.24; total 458/874 = 0.52.
  Two of three games below the pre-registered 50%.
P4: 0 verify->fix loops (only one verify happened).
Levels equal on all three games (1 / 3 / 1 both arms) -- not read as a score.
VERDICT: STOP, no full-25. The local model uses the store (writes and rewrites a model) but almost never checks it, and the
upkeep halves the action rate on two games. The mechanism that makes A3 work in the papers (verify -> fix) did not occur.
