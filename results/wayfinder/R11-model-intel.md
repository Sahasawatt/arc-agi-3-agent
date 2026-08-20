# R11 — Model & Serving Intel for ARC-AGI-3 (Duck Harness fork, Qwen 3.6 27B FP8 / vLLM)

Research-only pass. No code touched. Goal: find levers that raise actions-per-clock (throughput and/or quality-per-turn) inside the fixed envelope — vLLM on the Kaggle-provided RTX Pro 6000 96GB, no internet at scoring, model attached as a Kaggle dataset/model, ~25 concurrent agent loops, one repeated long system prompt, 9h wall clock over 110 hidden games.

Date of research: 2026-08-20 (per session clock).

---

## 1. vLLM throughput knobs for ~25 concurrent agentic loops with a repeated system prompt

### 1a. Prefix caching — the single most concrete, sourced finding in this report

Our fork's upstream, **Tufa Labs' `duck-harness`** (the winning ARC-AGI-3 Milestone-1 solution, and the thing "our fork of Tufa's Duck Harness" is forked *from*), is documented in its own Kaggle write-up as **not optimally using vLLM's prefix caching**, despite running the exact shape we're asking about: a system prompt repeated across every call, with the harness maintaining a ~32K-token context by evicting the oldest user message + subsequent assistant turns once it overflows. [Kaggle discussion](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/717133)

General vLLM data on what fixing this is worth:
- Shared-system-prompt chat/agent workloads see **70–90% cache hit rate** and **30–50% aggregate throughput** improvement with Automatic Prefix Caching (APC) on. [GIGAGPU deep-dive](https://gigagpu.com/vllm-prefix-caching-deep-dive/)
- For prompts with 2K+ shared tokens, **TTFT drops 60–80%**. [same source]
- Caveat that matters for us: APC only speeds up **prefill**, not decode — it doesn't shrink the cost of the actual action-generation step, only the cost of re-reading the growing shared context every turn. [vLLM docs](https://docs.vllm.ai/en/stable/design/prefix_caching/)

Confidence: **HIGH** that this is currently unexploited in the harness lineage we forked (source-confirmed, not inferred). **MEDIUM** on how much of the general 30–50% figure transfers to our specific eviction pattern — the harness's context isn't a static shared prefix, it's a sliding window that drops old turns, so the cache-hit rate depends on how much of each turn's prefix survives eviction unchanged turn-to-turn. Worth instrumenting `--enable-prefix-caching` cache-hit-rate metrics directly rather than assuming the general number.

### 1b. Scheduler/memory knobs

- `--max-num-seqs`: scheduler cap on concurrent sequences (v1 default 1024, i.e. not our bottleneck at 25). [vLLM docs](https://docs.vllm.ai/en/stable/configuration/optimization/)
- `--max-num-batched-tokens`: total tokens processed per scheduler iteration across all sequences; raise toward 16K–32K for throughput-oriented serving (default is workload-dependent, ~8K–32K). [Medium/Kaige Yang](https://medium.com/@kaige.yang0110/vllm-throughput-optimization-1-basic-of-vllm-parameters-c39ace00a519)
- `--gpu-memory-utilization`: since we're single-tenant (one model, one GPU, no sharing), pushing this toward 0.90–0.95 buys more KV-cache headroom directly, which is what determines how many of the 25 loops can run concurrently before requests queue. [vLLM docs](https://docs.vllm.ai/en/latest/configuration/conserving_memory/)
- Continuous batching (default-on) + PagedAttention already handle the scheduling/memory split; nothing to configure there beyond the above. [Spheron blog](https://www.spheron.network/blog/llm-serving-optimization-continuous-batching-paged-attention/)

Confidence: **MEDIUM** — standard vLLM tuning guidance, not measured on our exact 25-loop/32K-eviction shape. No public benchmark tests concurrency above 5 for our model (see 1e), so exact optimal values are unverified for this workload.

### 1c. Chunked prefill

Relevant because our workload mixes long, growing-prefix requests (agent history) with short decode bursts (single action token) across 25 loops simultaneously — exactly the "compute-bound prefill next to memory-bound decode" case chunked prefill targets. [Medium/Audrey Wang](https://audreywongkg.medium.com/understanding-vllm-scheduling-token-budgets-chunked-prefill-and-policies-2c879e3980e3)

Tuning tension: a larger chunk size reduces scheduling overhead for long prompts but lets one loop's prefill burst monopolize a step and stall the other 24 loops' decode; a smaller chunk protects fairness/tail latency at the cost of throughput on long-context turns. [same source, SGLang docs cited in it] Given 25 co-running loops where every other loop's turnaround time matters for total actions-per-clock, err toward the smaller-chunk / fairness side and measure tail latency, not just aggregate tok/s.

Confidence: **LOW-MEDIUM** — directionally correct from general agentic-serving literature, no ARC-AGI-3-specific measurement found.

### 1d. Speculative decoding (MTP) — real gain, but flagged risky at our concurrency

Qwen3.6 ships a **native MTP (multi-token-prediction) head** on its GDN-hybrid architecture, and vLLM has built-in MTP speculative decoding support for it. Measured single-stream gains: **1.4–2.2× faster generation**, mean accepted-draft length ~2.8–3.2, draft acceptance ~73–92% depending on config/source. [vLLM MTP docs](https://docs.vllm.ai/en/latest/features/speculative_decoding/mtp/), [lastloop-ai guide](https://github.com/lastloop-ai/vllm-blackwell-guide)

But the **official vLLM Qwen3.5/3.6 recipe page states explicitly**: *"MTP-1 reduces per-token latency but degrades text throughput under high concurrency because speculative tokens consume KV cache capacity, reducing effective batch size."* [vLLM recipes](https://docs.vllm.ai/projects/recipes/en/stable/Qwen/Qwen3.5.html) The vLLM team's own throughput-focused recipe for this model family does **not** include MTP — it recommends `--enable-expert-parallel --language-model-only --enable-prefix-caching`; MTP is only in their **latency-focused** recipe. At 25 concurrent loops we are closer to the throughput regime than the single-user-latency regime this feature was measured for.

Additional risk: INT4-quantized Qwen checkpoints have been reported to **drop or corrupt the MTP head**, causing vLLM's MTP loader to silently load zero parameters (feature quietly no-ops rather than erroring). [Medium/Allen Kuo] We're on FP8 already, which should be safer, but this hasn't been specifically verified for the 3.8 checkpoint (see §2).

Confidence: **MEDIUM** that MTP is net-negative or neutral at N≈25 concurrent given the vendor's own caveat; this is an A/B-test candidate, not a default-on recommendation.

### 1e. Quantization: FP8 vs AWQ/GPTQ

We're already on FP8, which the evidence supports as correct for our shape:
- FP8 gives near-FP16 quality and the **fastest tok/s at high batch size** (25–30% over FP16 in one benchmark), which matters more than VRAM efficiency for us since we have a full 96GB to ourselves and only one ~28GB model resident. [Sesame Disk / VRLA Tech roundups]
- AWQ/GPTQ (INT4) trade quality/VRAM for speed, but the gap is workload/kernel-dependent (one 2026 benchmark: GPTQ 8–19% faster than AWQ on vLLM 0.11; another: AWQ-Marlin edges out GPTQ-Marlin). [Zenn.dev benchmark], [jarvislabs.ai guide] Neither result environment matches ours (single-GPU, 25-way agentic concurrency, RTX Pro 6000/Blackwell specifically).
- Switching to INT4 to buy VRAM headroom is **not obviously worth it** given we're not VRAM-constrained (96GB vs a ~28GB FP8 checkpoint), and it reintroduces the MTP-head-corruption risk noted above.

Confidence: **HIGH** that FP8 is the right quant tier for this hardware/VRAM budget; **LOW** confidence on any specific % speed delta transferring from these general benchmarks to our workload.

### 1f. FP8 KV-cache specifically (separate from FP8 weights)

Measured gains (Llama-3.1-8B, vLLM's own blog): **14.9% higher output throughput, 13.0% faster total runtime, 14.8% lower median inter-token latency**; per-token KV cost drops to ~54% of BF16. Break-even point where FP8 KV starts winning: **~7K tokens of context** — below that, BF16 KV cache may be faster. [vLLM blog, 2026-04-22](https://vllm.ai/blog/2026-04-22-fp8-kvcache) Given the harness runs a 32K context window, most of our traffic should sit above that break-even.

**But — this is where the one hardware-specific landmine in this report sits (§1g).**

Confidence: **MEDIUM** on the throughput number transferring (measured on Llama-8B/H100/B200, not Qwen3.6-27B/RTX-Pro-6000); **HIGH** that we're operating above the stated break-even context length most of the time.

### 1g. ⚠️ Known bug: FlashInfer + FP8 KV-cache + CUDA graphs → silent output corruption, specifically on our exact GPU (sm_120)

Open vLLM GitHub issue: on **RTX 6000 Pro Blackwell (sm_120)** — our scoring GPU — combining the default FlashInfer attention backend, FP8 KV-cache quantization, and CUDA graphs (with `torch.compile`) produces **completely random output on long prompts**. Confirmed *not* to reproduce on H100 or B200 under the identical config, i.e. it's specific to this exact chip. [vLLM issue #41651](https://github.com/vllm-project/vllm/issues/41651)

- Reported 2026-05-04, still open across FlashInfer 0.6.8.post1–0.6.9 as of the last update found; a fix PR (#42650) exists but was pending merge.
- Workaround: `--attention-backend TRITON_ATTN` — reported to produce coherent output with FP8 KV-cache and CUDA graphs still enabled.
- This is the highest-severity item in this report because it's **silent** corruption, not a crash — on a long ARC-AGI-3 game (exactly where our context grows toward and past 32K), this could be quietly degrading action quality with no visible error, which would look indistinguishable from "the model is bad at this game."

Action: verify which attention backend the harness's vLLM launch actually uses today. If it's FlashInfer (the vLLM default on Blackwell) with FP8 KV-cache and CUDA graphs on, this is worth checking or switching to `TRITON_ATTN` before trusting any other perf tuning.

Confidence: **HIGH** that the bug exists and applies to our exact hardware (single well-documented GitHub issue, hardware-scoped root cause). **UNVERIFIED** whether our specific fork's launch config actually hits this combination — that's a config-read task against our own repo, out of scope for this research-only pass.

---

## 2. Qwen model family: sizes, benchmarks, and the size-vs-speed question

### 2a. What actually exists in the 3.6 line (and the 3.8 successor)

Contrary to the framing in the task ("4B/8B/14B/27B?"), the **Qwen3.6 line itself only shipped two sizes**: a **27B dense** model and a **35B-A3B MoE** model (April 2026). The 4B/8B/14B sizes exist only in the *older, weaker* mainline Qwen3 family, not as 3.6 variants. [dev.to/jamilxt writeup], [DEV Community Qwen3 lineup guide]

**New finding, not in the task's framing: Qwen3.8-27B shipped 2026-08-14** — 5 days before this research, same day-count as "today." Per its model card: **identical architecture and size** to 3.6-27B (same 64-layer hybrid pattern, same 27.78B params, same native 262,144-token context, Apache 2.0), so it should be a **same-envelope, drop-in FP8 checkpoint swap** — no expected change in tok/s. What changed is quality, evaluated by Qwen in the same harness/temp/context for both models:

| Benchmark | Qwen3.6-27B | Qwen3.8-27B |
|---|---|---|
| Terminal-Bench 2.1 | 63.4 | 73.0 |
| DeepSWE 1.1 | 13.3 | 42.2 |
| OSWorld-Verified | 63.9 | 84.3 |
| SWE-MM | 25.7 | 38.6 |

[dev.to comparison], [kingy.ai benchmarks], [aimadetools.com guide]

These are agentic / long-horizon / tool-use benchmarks, which is the closest public proxy to "playing an unfamiliar interactive game for many turns" that exists for this model pair. **This is the highest-confidence "free" lever in this report**: no throughput cost (same size/arch), plausible quality lift, zero evidence yet either way for ARC-AGI-3 specifically since it's brand new.

Confidence: **MEDIUM-HIGH** that it fits the envelope with no speed penalty (same architecture/params). **LOW** on how the benchmark deltas above translate to ARC-AGI-3 score — no ARC-AGI-3-specific evaluation of 3.8 exists yet (nothing in any public Kaggle notebook, since it's 5 days old). Also unverified: whether the 3.8 FP8 checkpoint's MTP head is intact under vLLM (§1d flags this as a known failure mode for some quantized Qwen checkpoints — untested specifically for 3.8).

### 2b. 35B-A3B MoE as a throughput alternative

Measured on 1× RTX Pro 6000 Blackwell FP8, Qwen3.6-35B-A3B (MoE, ~3B active params/token):

| Context | 1 req (tok/s) | 5 req aggregate (tok/s) |
|---|---|---|
| 1K | 196.4 | 449.0 (peak) |
| 32K | 183.0 | ~254 (50.7×5) |
| 96K | 157.0 | ~205 (41.0×5) |
| 256K | 116.3 | ~62 (12.3×5) |

[Millstone AI benchmark](https://www.millstoneai.com/inference-benchmark/qwen3-6-35b-a3b-fp8-1x-rtx-pro-6000-blackwell)

Compare to the 27B dense model's aggregate at the same points: **189.3 tok/s** (1K, 5 concurrent) and **92.5 tok/s** (32K, 5 concurrent) — i.e. MoE gives roughly **2.4× the aggregate throughput at low context**, narrowing to a smaller edge at 32K, because MoE's per-token compute advantage is largest when the batch is small and the model isn't yet decode-memory-bound. [Millstone AI 27B benchmark](https://www.millstoneai.com/inference-benchmark/qwen3-6-27b-fp8-1x-rtx-pro-6000-blackwell)

Two open gaps: **(1)** no public benchmark tests concurrency above 5 for either model — our real concurrency is ~25, and MoE's advantage or its expert-routing overhead at that scale is unmeasured; **(2)** no agentic-quality (SWE-bench-style) score was found for 35B-A3B specifically to compare against the 27B dense's 77.2 SWE-bench-Verified / AA-Agentic-Index-ties-Sonnet-4.6 result — can't say whether the extra throughput costs quality on ARC-AGI-3-shaped tasks.

Confidence: **LOW** — real throughput gain plausible at low concurrency, genuinely unverified at our concurrency and for our quality bar.

### 2c. Smaller/older Qwen3 sizes and the "action-budget beats per-action quality" question

The task asked whether a smaller model at 2-3× speed is a plausible net win under a wall-clock constraint. Two separate bodies of evidence, neither ARC-AGI-3-specific:

- **Within the Qwen3 family itself**, smaller sizes cost real agentic-task quality: APTBench-SWE scores scale with size — 1.7B: 24.3, 4B: 38.8, 8B: 41.6, 30B-A3B: 41.6 [arxiv 2510.24397] — all well below 3.6-27B's SWE-bench-Verified 77.2. There's no Qwen3.6/3.8-family model smaller than 27B to test the "same-family, smaller" hypothesis directly; going smaller means dropping to the weaker mainline Qwen3 generation, confounding size with generation/quality.
- **General agentic-systems literature** (not Qwen-specific, not ARC-AGI-3-specific) argues a small model can win on wall clock: reported per-step latency of 50–200ms for a 3–9B model vs 600–1500ms for a frontier model, and claims 40–70% of large-model agent-loop calls in some benchmarks (MetaGPT, Open Operator, Cradle) can be handled by well-tuned small models. [digitalapplied.com], [dev.to/syncsoftai] These numbers are for heterogeneous agent-loop step types (routing/tool-selection vs core reasoning), not for a single model doing every action in a visual reasoning game — the analogy to ARC-AGI-3's shape (every turn needs real visual/spatial reasoning, not mechanical tool dispatch) is weak.

Confidence: **LOW** on this lever specifically for ARC-AGI-3. The evidence that exists argues against it within the Qwen family (smaller = meaningfully worse on the closest available proxy benchmarks); the evidence that argues for it comes from a different task shape (tool-routing agent loops, not turn-by-turn game reasoning) and no source quantifies the actions-per-clock trade for anything resembling ARC-AGI-3.

---

## 3. What models do other public ARC-AGI-3 solutions use?

- **The Duck / Stochastic Goose lineage** (Dries Smit / Tufa Labs) — **Qwen 3.6 27B FP8 + local vLLM server** — is the dominant, best-documented public approach, and the base of our own fork. Milestone-1 (ended June 30 2026) winning score: **1.21% on the Kaggle leaderboard, 1.6% on the public train set** (25 public games, 20 attempts/game), with the authors themselves noting **large run-to-run variance** — same submission scored as low as 0.77% in another run. [Kaggle discussion 717133], [Tufa Labs writeup]
  - **Units caveat, unresolved**: these Milestone-1 numbers (~1.2–1.6%) and the current live-leaderboard numbers the task states (us: 1.00, top-5 bar: 2.57, #1: 3.57) do not obviously share a scale or measurement window — Milestone-1 ran on 25 public games with 20 attempts each, months before the numbers in the task's context. **Do not treat 1.6 ≈ "close to today's 2.57 bar"** without independently confirming they're the same metric; this report could not confirm that.
  - Their harness compares against a **GPT-5.4 + "Executable World Models"** approach solving a similar game set, calling their own vLLM-local approach "an order of magnitude cheaper" per game — but that comparison point is a hosted-API approach, not usable under our no-internet-at-scoring constraint anyway. [Tufa Labs writeup]
- **Could not find** any public notebook/discussion that names the model or serving stack behind the *current* top scores (#1 at 3.57, or the 2.57 top-5 bar cited in the task). This is a real gap — the competition's current leading approaches are not identifiable from what's publicly searchable right now.
- **Could not find** any public ARC-AGI-3 notebook or write-up using **SGLang** or **TensorRT-LLM** instead of vLLM, with or without a stated score. General (non-ARC) serving-stack comparisons say SGLang's RadixAttention is specifically strong for shared-prefix workloads (which matches our repeated-system-prompt shape) and TensorRT-LLM wins on raw single-model throughput. [jarvislabs.ai comparison] Neither claim has ARC-AGI-3-specific backing, and swapping the serving stack inside a fixed, no-internet, already-working Kaggle scoring image is a materially bigger/riskier lift than tuning vLLM flags — flagged as low-priority/exploratory only.

Confidence: **HIGH** that Qwen3.6-27B-FP8+vLLM is the standard public approach (well-documented, matches our own base). **NONE** — genuinely unknown — on what the current top-of-leaderboard solutions run.

---

## 4. Kaggle-specific environment facts

- **GPU**: RTX Pro 6000 Blackwell, 96GB VRAM, listed in the ARC-AGI-3 starter kit as accelerator `g4-standard-48`, "reserved for ARC-AGI-3 notebooks" (not to be used for early iteration on other accelerators). [docs.arcprize.org — fetched directly]
- **Internet**: confirmed directly from the official docs — "All accelerated Kaggle sessions have internet disabled, which is already the default in this kit." [docs.arcprize.org — fetched directly]
- **9-hour / 110-game limit**: this specific figure (9h runtime, 110 games, "play in any order") came from web-search synthesis, not from directly fetching primary text that stated it explicitly in this pass — **medium confidence**, worth a direct re-check against the official rules page before relying on it for scheduling decisions.
- **Model/dataset attachment size**: Kaggle's platform-wide limit is **200GB for both private and public datasets/models** (doubled from 100GB in a recent platform update). [Kaggle product announcement] This is a **platform-wide** figure, not confirmed as a competition-specific override — but it's generous relative to our need: a Qwen3.6/3.8-27B FP8 checkpoint is ~28–30GB, and even attaching both the 27B dense and the 35B-A3B MoE FP8 checkpoints simultaneously (~65GB combined on disk) would fit comfortably. The tighter real constraint is **VRAM (96GB)** for running inference, not the attachment quota.
- **Blackwell/sm_120 build specifics**: FlashInfer on Blackwell needs the **system CUDA 13 toolkit** — the PyPI wheel alone is reportedly insufficient. vLLM's own recommended Docker image for Blackwell is `vllm/vllm-openai:cu130-nightly`. [lastloop-ai guide], [vLLM recipes page] One source (single-sourced, not corroborated, possibly stale) additionally claimed vLLM still hit a DeepGEMM compile-path crash on sm_120 as of ~May 2026 and recommended SGLang as a workaround — **flagged low-confidence**, did not find a second source, and Kaggle's provided image is presumably already validated to run vLLM correctly on this GPU since the Duck harness's winning solution used exactly that combination.
- The single most load-bearing Kaggle-specific fact is §1g: the **FlashInfer + FP8-KV-cache + CUDA-graphs bug is scoped to this exact chip** (sm_120), confirmed absent on H100/B200. Anything using vLLM's Blackwell defaults with FP8 KV-cache should treat this as a live risk on Kaggle's hardware, not just a lab curiosity.

---

## Levers ranked by expected actions-per-clock gain × confidence

| # | Lever | Expected gain | Confidence | Cost/risk to try |
|---|---|---|---|---|
| 1 | Verify & properly exploit prefix caching (`--enable-prefix-caching`, check actual hit rate) | HIGH (30–50% aggregate throughput, 60–80% TTFT cut, general vLLM data) | HIGH that it's unexploited today in the harness lineage; MEDIUM on % transfer to our sliding-window context | Very low — config flag + instrumentation, no model change |
| 2 | Check attention backend vs the FlashInfer+FP8-KV+CUDA-graph corruption bug (§1g); switch to `TRITON_ATTN` if affected | Indirect — recovers silently-lost quality on long games, not a clock gain | HIGH bug exists on our exact GPU; UNVERIFIED whether our config triggers it | Very low — one flag, verify with a coherence check on a long-context run |
| 3 | Trial Qwen3.8-27B-FP8 in place of 3.6-27B-FP8 | Quality/actions-per-clock via fewer wasted turns on long-horizon tasks; same tok/s (same arch/size) | MEDIUM-HIGH on "fits with no speed cost"; LOW on ARC-AGI-3 transfer (no ARC eval exists yet, 5 days old) | Low — same-size checkpoint swap, verify MTP head loads correctly under vLLM |
| 4 | Raise `--gpu-memory-utilization` and `--max-num-batched-tokens` for single-tenant serving | MEDIUM — more KV-cache headroom at 25 concurrent, less queuing | MEDIUM — standard guidance, unmeasured at our exact concurrency | Low — config only |
| 5 | Tune chunked-prefill chunk size smaller to protect other loops' decode latency during a prefill spike | MEDIUM — protects tail latency across the 25 loops | LOW-MEDIUM — directionally right, no ARC-specific number | Low — config only |
| 6 | A/B test MTP speculative decoding at N≈25 concurrent (not default-on) | Possibly negative net (vendor's own caveat: degrades throughput under high concurrency) | MEDIUM that it's a wash or worse at our concurrency; HIGH that it helps single-stream latency | Medium — needs a real A/B, not a blind adopt; vendor's throughput recipe already excludes it |
| 7 | Evaluate 35B-A3B MoE as a throughput swap | Possibly HIGH raw tok/s at low concurrency (2.4× aggregate vs dense at 1K ctx/5 concurrent) | LOW — untested at N=25, no agentic-quality benchmark found for this model | Medium-high — quality parity vs dense 27B is unknown, real regression risk |
| 8 | Swap serving stack to SGLang for its shared-prefix (RadixAttention) design | Unknown | LOW — zero ARC-AGI-3 evidence, general claim only | High — full stack swap against a working, no-internet-constrained image |
| 9 | Drop to a smaller/older Qwen3 size for raw speed | Likely net-negative on ARC-AGI-3-shaped tasks per within-family benchmark data | LOW confidence it helps; MEDIUM confidence the within-family quality cost is real | High — meaningful quality regression risk, weak evidence it's worth it |

---

## Honest unknowns list

- Whether our fork's actual live vLLM launch config has prefix caching on/off, and what its real cache-hit rate is — needs a config read + instrumentation against our own repo (out of scope here: research-only, no code access in this pass).
- Whether our fork's launch config uses the FlashInfer + FP8-KV-cache + CUDA-graphs combination that's confirmed buggy on sm_120 — same caveat, needs a config read.
- Real aggregate tok/s achievable at our actual concurrency (~25) with our actual context-growth pattern (32K sliding window) — no public benchmark tests above 5 concurrent for this model on this GPU.
- Whether the Qwen3.8-27B-FP8 checkpoint's MTP head loads correctly under vLLM — untested in any source found; only INT4 Qwen checkpoints were documented as broken, FP8 should be safer but is unverified for this specific release.
- Whether Qwen3.8 has been used in any ARC-AGI-3 Kaggle notebook at all yet — no evidence found; it's 5 days old as of this research.
- What model(s) the current top-of-leaderboard entries (#1 at 3.57, top-5 bar 2.57) actually run — could not find this anywhere public.
- Whether the Duck harness's Milestone-1 scores (1.21–1.6%, 25 public games) are on the same scale/metric as the live leaderboard numbers cited in this task (1.00 / 2.57 / 3.57) — not confirmed; treat as a units mismatch until independently verified.
- Whether 35B-A3B MoE holds any agentic-quality parity with 27B dense on ARC-AGI-3-shaped (visual/spatial reasoning) tasks — no benchmark found either way.
- Whether the 9-hour/110-game figure is exactly right and current — sourced from search synthesis, not a directly-fetched primary quote in this pass.
- Whether the single-sourced "vLLM still crashes on sm_120 via DeepGEMM, use SGLang instead" claim is real/current or stale — only one source found, not corroborated, and contradicted in spirit by the fact that Duck's winning solution already runs vLLM successfully on this exact GPU.
