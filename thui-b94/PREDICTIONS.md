# B94 smoke predictions (written before any run)

This is a validity smoke, not a score run. It is **VALID** only if all of these hold:

- `THUI_B94_SERVING ok model=Qwen3.5-122B-A10B-NVFP4` prints after candidate identity validation.
- `/v1/models` returns exactly `Qwen/Qwen3.5-122B-A10B-NVFP4`.
- All three selected games (`tn36`, `vc33`, `bp35`) play and finalize.
- The run records zero CUDA out-of-memory failures.

Report total actions and elapsed play minutes, then compute actions/minute. Compare that rate with B81's smoke-equivalent rate using the same three games and 1,800-second per-game clock; do not interpret either number as a score.

**VOID** means the compatibility question was not measured: setup/load/readiness failed, the model identity was wrong, any selected game did not play, or a CUDA OOM occurred. A VOID run supplies diagnostics only and must not be used for the actions/minute comparison.

## Kill rules carried from MAP B94 Step 0 (written 2026-09-22, before the push)

- **K2 (VRAM) is read here.** A CUDA OOM at load, or serving_setup's own post-load gate `vLLM left too little free GPU memory` (`MIN_GPU_FREE_MIB = 4_096`), is a **K2 KILL** for this profile, not a VOID. Record `gpu_memory_mib` from the capture either way: Flash-Next's weights are ~76 GB on GPU (its 51 GB PLE table is CPU-offloaded), the candidate's are 83.5 GB, so ~7 GB less headroom is expected.
- **K3 (architecture)** passed at 0 GPU (the pinned image registers `Qwen3_5MoeForConditionalGeneration`); a load error naming the architecture or the ModelOpt NVFP4 path is still a K3 KILL.
- **Direction predicted:** FEWER actions/min than the reference. The candidate runs ~1.55× the active compute per token on a decode-bound chassis (B87).
- **Reference for actions/min:** `thui-a6-ctx64-smoke`, same three games at 1,800 s on the B81 profile. It differs by analyzer context (65,536 vs 32,768 here), so read the comparison as a direction, never a rank.
