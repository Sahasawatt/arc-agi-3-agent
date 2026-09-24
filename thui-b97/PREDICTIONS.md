# thui-b97 — registered before the push (2026-09-24)

MAP **B97**, on the B81 base (`thui-a5-mtp0k7s28-full25-r1`). Two changes, by design:

| | control arm | b97 arm |
|---|---|---|
| `TAAF_VLLM_KV_CACHE_MEMORY_BYTES` | 7 GiB (`7516192768`) | **13.5 GiB** (`14495514624`) |
| `VLLM_MAX_MODEL_LEN` (server ceiling, prompt + completion) | 32768 | **65536** |
| `ANALYZER_CONTEXT_WINDOW` (agent prompt budget) | 32768 (budget 31744) | **49152** (budget 48128) |

Everything else is the base: MTP 0, `max_num_seqs` 28, prefix caching off, same games, same 1,800 s clock.

## Why 13.5 GiB and not the row's 12

The row says *ctx 64k × KV 12*. Two numbers moved it, both read before building:

- **The server today is 32768, not the 65536 this campaign last recorded** (B54 era) — read out of the B100 smoke's
  own vLLM log, `'max_model_len': 32768`. So the window is two knobs, not one, and at a 32768 ceiling an analyzer
  budget of 48128 would be unservable.
- **Concurrency has to be divided by the prompts actually sent, not by `max_model_len`.** B87 measured KV tokens
  linear in bytes (263,568 at 7 GiB, 452,340 at 12 = 37,695 tokens/GiB). At the ~25k prompts the base runs today
  that is ~10.5 concurrent, which is exactly the Running 10–11 the B100 smoke logged. At the ~48k prompts this
  window invites, KV 12 gives ~9.4 — **below** today. 13.5 GiB gives ~508,900 tokens ≈ **10.6**, the smallest
  number that does not spend concurrency to buy window.

48k was chosen over the row's 64k for the same reason, and because B54 already sized 49152 against a 65536 ceiling:
48128 + the worst completion ever observed (11,989) = 60,117, still 5.4k under.

## VOID — the run says nothing, whatever the score

1. `THUI_B97_WINDOW ok server=65536 analyzer=49152 budget=48128 kv=13.5GiB` absent from the arm's log, or present
   in the control's. The rewrite asserts before any setup command runs, so a moved anchor stops the kernel rather
   than serving an unsized window.
2. The arm's vLLM log does not echo `'max_model_len': 65536`, or the control's does not echo `32768`.
3. `THUI_A5_PROFILE ok mtp=0 kv=13.5GiB seqs=28` absent from the arm (`kv=7GiB` from the control).
4. **OOM, or `serving_setup`'s free-GPU gate (< 4,096 MiB).** 13.5 GiB is above the 12 GiB B87 proved fits
   (`reserved 12.0 GiB`, no OOM); 13.5 is UNTESTED and this is the line that says so.
5. Any request where `prompt_tokens + completion_tokens >= 65536`. The whole window sizing rests on that never
   happening; B54's worst observed was 48,066 against the same ceiling.
6. Fewer than 25 games in either arm, or the arms' game sets differing.

## The mechanism reading — this is what the smoke is for

- **Prompt size must actually move**: the arm's median `prompt_tokens` rises from the base's ~22–25k toward
  **33–40k** (B54 measured median 33,734 at this exact 49152 window), with a non-trivial share above the old
  31,744 budget (B54: 61 %).
- **Concurrency must not fall**: median `Running` in the arm **>= 10**, and not below the control's. Read from the
  arm's own `vllm-openai-server.log`, medians over its stats lines.
  ⚠️ That log has been observed covering only the run's **first ~31 minutes** (B100 smoke), so this is a reading
  over the opening window, not the run. Report the span beside the medians; early prompts are the SHORT ones, so a
  Running that already sags there is worse than it looks, and one that holds is not proof it held at hour ten.
- **KILL on any of**: median `Running` < 8 (the row's bar); actions/min below 95 % of the control; the share of
  requests above 31,744 prompt tokens not rising at all (the window was bought and not used).

## What is NOT predicted, and why the smoke cannot settle it

**A level gain is not predicted.** Both halves of this cross have already been measured alone and both were flat:
B54 raised this same window and got levels 28 → 28, `p = 0.4333 NOT-DISTINGUISHABLE`, closing with *"the optimum is
somewhere below 49152"*; B87 raised KV to 12 and got levels 18 / 18 / 18 with actions peaking at KV 10 and falling
at 12. B97 is the bet that the cross behaves unlike either half. A smoke of 25 games cannot rank that — B99 r1 vs r2,
byte-identical, ran 37 → 45 levels — so levels and score here are DESCRIPTIVE. Only a full pair read per game
through `eval/rank_runs.py` (selftest first) can rank it, and the row's bar for that is +1 level on >= 12 of 25.

**Deviation from the row, registered:** the row names **B88** as the comparator. This smoke's control is the
**base** (KV 7, window 32768), matched same-day, because B88 is neither same-day nor same-window and is itself
NOT-DISTINGUISHABLE from B81 (public p = 0.459). So this pair answers *does the cross beat the base it is built
on*, and nothing about B88.

## Cost

~0.6 GPU-h per arm, ~1.2 GPU-h for the pair. 0 submission slots. The GPU session cap is 2, so the pair is the cap.
