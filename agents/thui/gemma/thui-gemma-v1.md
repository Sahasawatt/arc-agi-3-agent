# thui `gemma v1` — full 25 games: public 0.41, B64 CLOSED NEGATIVE

`thui-gemma-v0`'s builder with `--full`: `thui-v3-0` + Gemma-4-31B-it (online fp8, vLLM 0.23 offline wheels, gemma4
parsers, 32-image limit, the S0 env fix, the competition-mount resolver). Kernel `sahasawatt/thui-gemma-v1` v1,
2026-09-07 08:20–10:42Z, wall 8,664 s.

## What it scored

| public | levels | scoring | actions | gen tok | act/lvl |
|---|---|---|---|---|---|
| **0.41** | **5** | 4 / 25 | 1,562 | 0.56 M | 312 |

`rank_runs.py` vs `thuiv3-pool`: pool 4.39 / 24.25 levels vs this 0.41 / 5 — **20 up / 2 down for the pool,
p = 0.0, DISTINGUISHABLE (WORSE)**.

## Verdict

**Closed negative on one draw** — the gap is 10× the same-build spread, so the stated rule ranks it. Serving,
parsing, images and the harness all worked (S0–S3 of the smoke held in the full run: `tool_calls` 694/781, executed
turns 56 %); the model spent the same action budget as the chassis and cleared a fifth of the levels, generating a
quarter of the tokens. Throughput under 25-way load was 1.85× worse per request than Qwen (185 s median, 45 timeouts)
and the 3-game smoke could not have seen that — the rehearsal-width trap.

Full read: `notes/B64-gemma-4-31b-duck-agent-design.md` §Full-run record.
