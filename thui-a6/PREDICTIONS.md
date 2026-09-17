# thui-a6-ctx64-full25-r1 — pre-registered 2026-09-17 before push

**Change vs `thui-a5-mtp0k7s28-full25-r1` (B81): one.** The analyzer context goes from 32,768 to 65,536.
- His `serving_setup.py:129` constant `ANALYZER_CONTEXT = 32_768` sets both vLLM `--max-model-len` (`:2322`) and
  the persisted `LOCAL_ANALYZER_CONTEXT_WINDOW` (`:2935`), so this is not an env knob.
- Cell 9 builds an overlay bundle in `/kaggle/working`: symlinks for everything, a patched `serving_setup.py`, and
  `SOURCE_IDENTITY.json` re-stamped with the patched sha. The script refuses to run on an identity mismatch (`:599-608`).
- Cell 0 changes only its header.

**Gate before push (owner's rule 2026-09-17).** Push only if B81's hidden draw `56291375` lands at or above the B71
family (3.74 / 3.41 / 2.90).

## Prior that argues AGAINST
B54 (closed) raised `thui-v1-1` from 32,768 to 49,152 on the June chassis:
- throughput −31%, levels 28 → 28;
- its row says any optimum is likely BELOW 49,152.

This build tests the same axis on a different chassis. KV 7 GiB holds 263,568 tokens: 8.04× concurrency at 32k,
**~4.0× at 64k**. B81 already runs KV at 95% with 10 running / 15 waiting, so longer prompts should cut concurrency.
Expected: levels ≈ equal or lower.

## Offline teeth (2026-09-17, before push)
- Overlay run against the real downloaded `serving_setup.py`: `ANALYZER_CONTEXT = 65_536`, the re-stamped identity
  matches the patched sha, sibling entries are symlinks, other identity keys are kept.
- Mutation 1: the literal is absent → `thui-a6: ANALYZER_CONTEXT literal moved`.
- Mutation 2: the identity does not match the original setup → `refusing to re-stamp`.
- Cell order: overlay < setup loop < persisted-context assert < solver-window assert.
- The dataset's real `SOURCE_IDENTITY.json` `serving_setup_sha256` equals the sha of the downloaded
  `serving_setup.py` (True, 2026-09-17), so the overlay's original-identity assert passes on the real bundle.
- **Not yet checked:** whether the model/vLLM accept `--max-model-len 65536`. Smoke answers it.

## VALID (any failure = VOID, no score read)
- V1: `THUI_A6_OVERLAY ok ctx=65536` and `THUI_A6_CTX ok solver_window=65536` print. The server argv carries
  `--max-model-len 65536` and the B81 profile (seqs 28, KV 7516192768, no speculative config).
- V2: no CUDA OOM or engine death; COMPLETE inside 32,400 s; 25 games in `benchmark.json`.

## Smoke first
Run 3 games before the full run. VOID-by-startup if vLLM rejects 65,536 or the KV profile fails to start.

## MECHANISM
- P1: the share of requests with prompt > 32,768 tokens is > 0. If it is 0, the context never binds →
  NULL-by-mechanism. Read it from the vLLM periodic log or usage sidecars.
- P2: median Running (vLLM periodic log), reported against B81's 10. The prediction is lower.
- P3: total actions, reported against B81's 2,965.

## READ
- First `rank_runs.py --selftest`.
- Then compare against `eval/fixtures/thui-a5-mtp0k7s28-full25-r1.json`. That fixture must be built first — it is not banked yet.
- Levels per game against B81's 41.
- n = 1, so NOT-DISTINGUISHABLE is expected. Same-build noise is ~4.75 levels SD on a paired total (probes-2026-09-17 §3).

## Submission rule
Only if VALID, P1 > 0, and public levels > 41. Otherwise no submission.
