# localrig — run the duck harness on THIS machine, $0, no Kaggle quota

Built 2026-08-24 (MAP B33). Purpose: iterate on harness changes locally before
spending a GPU slot. **A local 8B CANNOT predict the 27B's score** (v20: small
model = 0.18) — this rig verifies MECHANICS and BEHAVIOUR (a patch fires, a
ledger computes, the loop does not crash, the model reacts to a nudge), never
score transfer. Kaggle remains the only scoreboard.

## Pieces

- `tufa-arc-agi-framework/` + `ARC3-Inference/` — vendored from the anim bundle
  (the exact source our Kaggle runs use; scratchpad copy `bundlecmp/anim`).
- `.venv/` — python 3.12, both packages editable-installed
  (`PIP_IGNORE_REQUIRES_PYTHON=1` for the ==3.12.12 pin; we run 3.12.10).
- Model: ollama `qwen3-8b-16k` / `qwen3-8b-10k` (derived Modelfiles here).
  10k fits the RTX 4060 Ti 8GB fully on GPU (~30 tok/s); 16k spills 20% to CPU
  (~12 tok/s). Same family as the Kaggle 27B (thinking + template).
- Env files: the engine machine-loads `../environment_files/` — NEVER read,
  grep, or list that directory yourself (standing rule; it is the answer key).

## Run one game

From `localrig/ARC3-Inference`, with the LOCAL_ANALYZER_* env block (see the
smoke commands in the session ledger / git history):

    ../.venv/Scripts/python.exe -m inference.framework.run       --model qwen3-8b-10k --deployment-target inline --timeout 120       --game ls20 --environments-dir ../../environment_files       --max-actions 10 --max-runtime-minutes 6 --n-passes 1 --concurrent-jobs 1       --experiments-dir ../runs --run-name <name>

Key env: BASE_URL http://localhost:11434/v1 · PROVIDER openai-compatible ·
CONTEXT_WINDOW matching the Modelfile num_ctx · MULTIMODAL_CONTEXT="" (8B has
no vision) · MAX_OUTPUT=0 (v9 rule: never cap).

Measured smokes: smoke1 (16k, 33s timeout) 3 actions then analyzer timeout;
smoke2 (10k, 120s timeout) 10/10 actions, 30.3 tok/s, zero timeouts.
