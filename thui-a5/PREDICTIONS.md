# thui-a5-mtp0k7s28-full25-r1 — pre-registered 2026-09-16 before push

Change vs thui-animfast-b71-full25-r1: cell 3 vLLM profile only (MTP 3->0, KV 5->7 GiB, max_num_seqs 8->28). Cell 0 header.
Mechanism (measured on thui-rank2-anim-full25-r1, same chassis): vLLM median Running 3 / Waiting 22 all run; 75% of requests
> 20k prompt tokens. Bench 2026-09-15: this profile starts, 263,568 KV tokens, c25 570 tok/s vs 359, 0 preemptions.

VALID (any fails = VOID, no score read):
- V1 `THUI_A5_PROFILE ok` prints; server log non-default args carry max_num_seqs 28, kv_cache_memory_bytes 7516192768, no speculative config.
- V2 no CUDA OOM / engine death; run COMPLETE inside 32,400 s; 25 games in benchmark.json.
MECHANISM:
- P1 median Running (vLLM periodic log) >= 6 over the run (was 3). Below 5 = the lever did not move the binder -> read as NULL-by-mechanism.
- P2 actions total > B71's (report both); generated tokens reported.
READ (n=1, NOT-DISTINGUISHABLE expected and not a loss): rank_runs.py --selftest, then vs eval/fixtures/thui-animfast-b71-full25-r1.json.
Levels per game vs B71; closed-axis prior: B16/B34/B78 say more throughput has not bought levels -> expect levels ~ equal.
Submission: only if VALID and public levels > B71's 39.

## READ (COMPLETE 18:01Z 09-16; fetched 01:40Z 09-17 after the vault unlocked)
V1 PASS: `THUI_A5_PROFILE ok` once; server argv --max-num-seqs 28, --kv-cache-memory-bytes 7516192768, no --speculative-config;
  vLLM: "GPU KV cache size: 263,568 tokens, Maximum concurrency for 32,768 tokens per request: 8.04x".
V2 PASS: 0 OOM; 3 Tracebacks = upstream serving_teardown.py (as every run on this chassis); 25 games; 15:45:42 -> 17:58:46 = 7,984 s
  (page: "8549.8 second run - successful", Version 1 of 1).
P1 PASS: vLLM periodic log, 798 lines, three equal windows: median Running 10 / Waiting 15 / KV 95% in every window (was 3 / 22 / 81%).
P2: actions 2,965 vs B71 2,008 (+48%); generated tokens 2.60M (rank2-anim same chassis 1.95M); requests 1,753 (1,372); preemptions 98.
READ: rank_runs.py --selftest OK (6 controls). vs thui-animfast-b71-full25-r1: public 9.56 -> 8.72, levels 39 -> 41 (+2),
  9 up / 8 down / 6 flipped, p = 0.6491 NOT-DISTINGUISHABLE. Level changes: ar25 3->5, bp35 0->1, cd82 1->2, cn04 0->1, g50t 0->1,
  m0r0 0->1, s5i5 1->2, sb26 1->2 | dc22 2->1, ft09 5->4, sc25 3->2, su15 2->1, tn36 1->0, tr87 1->0, tu93 3->2.
Submission rule (VALID and levels > 39): MET. Gate dry-run 01:47Z: G1 evidence "Version 1 of 1", G3 slot 2026-09-17 unspent, G4 ok,
  G6 BLOCKED -- sahasawatt ran thui-rs-{v0,ctl} 25.2 h ago and thui-af-{v0,ctl} 35.8 h ago. Needs the owner's call.
SUBMITTED 2026-09-17 01:46:55Z as 56291375 (v1) on Watchara's explicit instruction; G6 overridden with --leader-clear
("owner instructed, leader not asked"). Gate rc=0, record read back. Slot 2026-09-17 spent. Hidden score pending.
