# ARC-AGI-3 duck-harness turn-latency and throughput forensics

## Executive finding

The 12×–15× seconds-per-action spread is not primarily mysterious GPU variance. It is mostly caused by how many environment actions each model turn produces.

Across games:

- Seconds/action versus generated tokens/action: **r=0.984** in `duckv5out`, **r=0.987** in `duckmodcal`.
- Seconds/action versus actions per nonzero-generation model turn: **r=−0.584** and **r=−0.610**.
- At the individual response level, generated tokens versus elapsed request/action-group time: **r=0.947** and **r=0.933**.

The GPU is continuously serving about 25 simultaneous requests. Its aggregate decode rate is approximately **234 tok/s** and **210 tok/s**, but each active request receives only about **9.5 tok/s** and **8.6 tok/s**. Thus a 1,000-token think/tool response naturally costs roughly **105–117 seconds**.

The single highest-leverage change is to impose a hard output-token cap. The runs explicitly set `LOCAL_ANALYZER_MAX_OUTPUT=0`, which becomes `max_tokens=None`; the request consequently omits `max_tokens`, while thinking is enabled and preserved. This permits responses of several thousand tokens. Evidence: `tool_agent.py:935-937`, `tool_agent.py:1289-1297`, `openai_compat.py:57-58`, and both `taaf-*.log:253-257`.

---

## 1. Seconds per action

Every game reached approximately 7,920 seconds, so seconds/action is essentially `final_wallclock_seconds / len(history)`. The artifacts identify 25 games and their action totals in `summary.txt:3-14`; the JSON records the final wall clock, for example `duckv5out/benchmark.json:40969-40976` and `duckmodcal/benchmark.json:39412-39419`.

| Game | duckv5out actions | v5 s/action | duckmodcal actions | mod s/action |
|---|---:|---:|---:|---:|
| ar25 | 131 | 60.46 | 339 | 23.44 |
| bp35 | 262 | 30.23 | 44 | 180.02 |
| cd82 | 76 | 104.21 | 106 | 74.72 |
| cn04 | 434 | 18.25 | 189 | 41.91 |
| dc22 | 113 | 70.09 | 51 | 155.31 |
| ft09 | 82 | 96.59 | 132 | 60.00 |
| g50t | 84 | 94.29 | 262 | 30.23 |
| ka59 | 155 | 51.10 | 154 | 51.57 |
| lf52 | 184 | 43.05 | 42 | 188.63 |
| lp85 | 49 | 161.65 | 69 | 114.79 |
| ls20 | 62 | 127.75 | 106 | 74.72 |
| m0r0 | 608 | 13.03 | 156 | 50.78 |
| r11l | 59 | 134.25 | 102 | 77.65 |
| re86 | 151 | 52.73 | 188 | 42.13 |
| s5i5 | 64 | 123.75 | 43 | 184.88 |
| sb26 | 187 | 42.36 | 199 | 39.80 |
| sc25 | 145 | 54.63 | 58 | 136.56 |
| sk48 | 91 | 87.04 | 131 | 60.46 |
| sp80 | 120 | 66.00 | 198 | 40.00 |
| su15 | 135 | 58.67 | 256 | 30.94 |
| tn36 | 82 | 96.59 | 155 | 51.15 |
| tr87 | 339 | 23.36 | 351 | 22.57 |
| tu93 | 104 | 76.16 | 63 | 125.72 |
| vc33 | 100 | 79.21 | 52 | 152.32 |
| wa30 | 183 | 43.30 | 412 | 19.26 |

### Distribution

| Run | Min | P10 | P25 | Median | Mean | P75 | P90 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| duckv5out | 13.03 | 21.32 | 43.17 | 66.00 | 72.35 | 96.59 | 130.35 | 161.65 |
| duckmodcal | 19.26 | 23.09 | 39.90 | 60.00 | 81.18 | 131.14 | 181.97 | 188.63 |

The supplied artifacts therefore show a **14.5×** observed range, from 13.03 to 188.63 seconds/action.

### What correlates with slowness?

#### A. Generated tokens

Strongly—but the best explanatory variable is generated tokens **per action**, not total tokens per game.

| Correlation with seconds/action | duckv5out | duckmodcal |
|---|---:|---:|
| Total generated tokens/game | −0.425 | −0.204 |
| Generated tokens/action | **0.984** | **0.987** |
| Tokens/nonzero-generation turn | 0.364 | 0.242 |
| Actions/nonzero-generation turn | **−0.584** | **−0.610** |

Total game tokens are similar because nearly every game consumes the entire clock. What differs radically is whether one expensive response executes one action or a batch of many.

Examples:

- `m0r0` in v5: 608 actions from only 42 nonzero-generation records, **14.48 actions/turn**, yielding 13.03 s/action.
- `r11l` in v5: 59 actions from 59 nonzero-generation records, **1.00 action/turn**, yielding 134.25 s/action.
- `lf52` in mod: 42 actions from 42 nonzero-generation records, **1.00 action/turn**, yielding 188.63 s/action.
- `tr87` in mod: 351 actions from 26 nonzero-generation records, **13.50 actions/turn**, yielding 22.57 s/action.

The harness explicitly allows ordered action batches and multiple `action(...)` calls inside one Python snippet (`tool_agent.py:1248-1250`). The benchmark confirms that subsequent actions within a batch can carry zero newly generated tokens and almost no additional wall time; see the consecutive zero-token records at `duckv5out/benchmark.json:114-147`.

#### B. Prompt length

Prompt size is material to GPU work but does **not** explain the cross-game 12× spread well.

A six-transcript sample—fast, middle, and slow games from both runs—measured:

| Run/sample | System prompt chars | Median user chars | User range | Median system + user |
|---|---:|---:|---:|---:|
| v5 `m0r0` | 14,873 | 4,634 | 2,982–7,433 | 19,507 |
| v5 `sp80` | 14,873 | 4,778 | 2,982–8,122 | 19,650 |
| v5 `lp85` | 14,873 | 3,892 | 2,952–8,429 | 18,765 |
| mod `wa30` | 14,516 | 3,183 | 2,714–3,250 | 17,699 |
| mod `ft09` | 14,516 | 3,390 | 2,748–3,694 | 17,906 |
| mod `lf52` | 14,516 | 2,890 | 2,780–3,350 | 17,406 |

The slowest sampled games do not have the largest user prompts. The invariant system prompt dominates the visible base prompt and is rebuilt into every request (`tool_agent.py:350-359`, `tool_agent.py:941-943`, `tool_agent.py:1751-1758`). Conversation history adds further input beyond these visible system+current-user measurements.

#### C. Co-scheduling and queueing

The configured solver concurrency is **28**, confirmed in each run at approximately `taaf-duck-v5.log:656` and `taaf-duck-mod.log:655`. Because there are only 25 games, the actual active fan-out is 25.

The implementation creates a 28-worker pool and a matching semaphore (`solver.py:802-805`, `solver.py:881-887`, `solver.py:896-917`). Each game independently calls the same OpenAI-compatible endpoint at `/chat/completions` (`solver.py:293-301`, `tool_agent.py:1302-1307`).

The log shows:

- Startup transient: 3 running, 22 waiting (`duckmodcal/vllm-openai-server.log:112`, approximately).
- Immediately afterward: 24–25 running, zero waiting (`duckmodcal/vllm-openai-server.log:113-148`).
- Across saturated samples:
  - v5: mean 24.62 running; mean waiting 0.03.
  - mod: mean 24.61 running; mean waiting 0.06.
- Later in the run, the server still reports 25 running and zero waiting (`duckmodcal/vllm-openai-server.log:903-910`, approximately).

Therefore, there is almost no prolonged **waiting-list queue**. The latency is concurrency dilution inside vLLM’s continuous decode batch: all 25 requests are “running,” but each advances at only a fraction of aggregate throughput.

---

## 2. Job throughput versus per-request throughput

`summary.txt` reports:

| Run | Job-wallclock generated rate | Total tokens | Duration |
|---|---:|---:|---:|
| duckv5out | 220.91 tok/s | 1,759,134 | 2h 12m 42s |
| duckmodcal | 195.91 tok/s | 1,557,544 | 2h 12m 30s |

Sources: `duckv5out/summary.txt:6-14`; `duckmodcal/summary.txt:6-14`.

From all saturated vLLM logger intervals:

| Run | Aggregate vLLM generation | Active requests | Aggregate/running request |
|---|---:|---:|---:|
| duckv5out | mean 234.46, median 227.8 tok/s | mean 24.62 | **mean 9.54, median 9.23 tok/s/request** |
| duckmodcal | mean 210.25, median 204.1 tok/s | mean 24.61 | **mean 8.56, median 8.27 tok/s/request** |

A representative early interval reports 460 aggregate tok/s across 25 requests, or 18.4 tok/s/request (`duckmodcal/vllm-openai-server.log:168`). Later intervals are commonly around 108–310 aggregate tok/s with 25 running (`duckmodcal/vllm-openai-server.log:903-910`, `1603-1610`, `2400-2410`).

There is no separate single-request benchmark in the artifacts, so “per-request rate” must be interpreted as aggregate logged generation throughput divided by logged running requests. It is not a direct concurrency-one measurement.

### Dilution

- v5: `234.46 / 24.62 = 9.52 tok/s/request`; approximately **24.6× dilution** versus aggregate hardware throughput.
- mod: `210.25 / 24.61 = 8.54 tok/s/request`; approximately **24.6× dilution**.
- Using the end-to-end summary rate gives `220.91 / 25 = 8.84` and `195.91 / 25 = 7.84 tok/s/game`, consistent after prompt/tool/HTTP idle overhead.

This also matches benchmark timing directly:

- v5 nonzero responses: 1,605 mean generated tokens, 174.6 mean seconds, **9.19 tok/s**.
- mod: 1,478 tokens, 181.6 seconds, **8.14 tok/s**.

A median roughly 1,000-token response therefore consumes about two minutes of a game’s clock.

---

## 3. Throughput levers

Effect classes:

- **Very high:** directly reduces decode tokens or increases actions returned per decode.
- **High:** materially reduces shared prefill/decode pressure.
- **Medium:** scheduler/memory tuning requiring measurement.
- **Low/guardrail:** prevents pathological stalls but does not raise steady-state GPU throughput.

| Lever | Current evidence and source | Expected effect |
|---|---|---|
| Hard-cap analyzer output tokens | Config default is `max_output: 0` (`configs/inference.json:55-59`). Zero becomes `None` (`tool_agent.py:935-937`); payload uses that value (`tool_agent.py:1289-1297`) and only emits `max_tokens` when non-null (`openai_compat.py:57-58`). Actual runs set `LOCAL_ANALYZER_MAX_OUTPUT='0'` at `taaf-*.log:253`. | **Very high.** Start testing 512–1,024. Cuts long thinking/tool generations directly; the observed per-response rate is only 8–9 tok/s. |
| Bound or disable thinking | `thinking: true` in `configs/inference.json:57-59`; payload receives it at `tool_agent.py:1294-1298`. The launch preserves thinking (`kaggle.py:330-334`; actual `taaf-*.log:637`). | **Very high.** Thinking is currently bounded only by request/server behavior because max output is absent. Test thinking off or a small explicit budget. |
| Increase environment actions per model turn | Prompt explicitly recommends batching and permits multiple calls (`tool_agent.py:1248-1250`). | **Very high.** This is the strongest empirical determinant of actions/clock. Reliable loops/searches can amortize one LLM turn over 5–15+ actions. |
| Shorten system prompt | Built by concatenating six large addenda (`tool_agent.py:350-359`) and resent each call (`tool_agent.py:1751-1758`). Measured at 14,516–14,873 chars. | **High prefill/context benefit.** Deduplicate repeated guidance and tool documentation. Also improves prefix-cache footprint and usable history budget. |
| Shorten current observation/user prompt | Built from state/history at `tool_agent.py:1161-1185`; sampled medians are 2.9–4.8k chars, peaks 8.4k. | **Medium–high.** Reduce progress digest/history descriptions and avoid redundant full-state summaries. |
| Tighten conversation-history retention | Every request contains system + `_history_messages` + current user (`tool_agent.py:1754-1758`); context trimming occurs before the request (`tool_agent.py:1788-1794`). | **High later-run prefill/KV benefit.** Use a compact state ledger rather than accumulating verbose assistant/tool history. |
| Preserve prefix caching | Enabled in the Kaggle launcher (`kaggle.py:330`) and actual server command (`taaf-*.log:637`); vLLM confirms it (`vllm-openai-server.log:7,17`). | **Already on; keep it on.** The repeated system prefix benefits, although the hit rate falls from roughly 70–80% early to about 23–34% later as histories diverge (`duckmodcal/vllm-openai-server.log:168-203`, `903-910`). |
| Make the cacheable prefix larger/identical | System prompt is stable, but each game’s accumulated history diverges after it. | **Medium.** Move stable tool schema and invariant instructions ahead of all dynamic material; compact dynamic history so more tokens share the same prefix. |
| Reduce `max-model-len` from 65,536 to the harness’s real context need | Actual launcher passes 65,536 (`kaggle.py:335-336`; `taaf-*.log:637`); engine confirms it (`vllm-openai-server.log:7-10`). The repository’s normal shared context is 32,768 (`configs/inference.json:3-6`). | **Medium memory/scheduler experiment.** The server reports only 10.12× full-65k concurrency despite 25 active requests (`vllm-openai-server.log:61-62`). A 32k ceiling better matches the harness and reduces pathological context exposure, though vLLM allocates KV dynamically, so this is not guaranteed to increase decode throughput alone. |
| GPU memory utilization | Generic Makefile supports `--gpu-memory-utilization` (`Makefile:111`, `Makefile:305`), and normal config says 0.92 (`configs/inference.json:38-48`). The Kaggle launch does **not** pass it (`kaggle.py:311-337`), so vLLM uses 0.9000; the log explicitly suggests 0.9102 under its profiling behavior (`vllm-openai-server.log:59-62`). | **Medium capacity lever.** Passing approximately 0.91–0.92 may expand KV headroom, but likely helps stability/concurrency more than raw decode speed. Validate OOM margin. |
| `max_num_batched_tokens` | Not explicitly passed by the harness. vLLM enables chunked prefill with 8,192 tokens (`vllm-openai-server.log:10`). | **Medium experiment.** Larger values may improve long-prompt prefill throughput but can hurt decode latency; benchmark actions/job, not isolated prompt tok/s. |
| `max_num_seqs` / batch-size control | No corresponding launch flag appears in `kaggle.py:311-337` or actual command `taaf-*.log:637`. vLLM therefore admits all 25. | **Medium experiment.** A cap can protect decode latency from oversized batches but may introduce explicit waiting. Measure total actions across all games. |
| Concurrency | Solver is configured for 28 (`taaf-duck-v5.log:656`, `taaf-duck-mod.log:655`), while only 25 games exist. Worker pool and semaphore enforce it (`solver.py:881-917`). | **Medium, ambiguous.** Fewer games would increase per-request token rate, but likely reduce aggregate batching efficiency and create multiple 7,920-second waves. With a one-wave 2h12 job, concurrency below 25 risks not giving every game its full clock. Sweep 8/12/16/20/25 only if the outer job budget permits waves; optimize total actions/job, not one-game latency. |
| Request timeout | Solver records `analyzer_timeout=900` in `taaf-*.log:655-656`. The effective timeout is the minimum of configured timeout and remaining game/job time (`solver.py:227-244`), passed to `analyze` (`solver.py:293-301`) and then `requests.post` (`tool_agent.py:1302-1307`). | **Low/guardrail.** Lowering it prevents a pathological response from consuming many minutes, but timeouts discard work and may cause retries. A token cap is cleaner. |
| Turn yield budget | Runs set `LOCAL_ANALYZER_YIELD_SECONDS=60` (`taaf-*.log:257`); the code checks it only between requests/tool iterations (`tool_agent.py:1767-1785`). | **Low as implemented.** It cannot interrupt an in-flight 100–200-second completion, so it does not enforce a real 60-second turn ceiling. |
| Tool-step bound | Runs set `LOCAL_ANALYZER_TOOL_STEPS=0`, which becomes unlimited (`tool_agent.py:932`; actual `taaf-*.log:254`). | **Medium guardrail.** Bound multi-request reasoning loops, though action execution often ends a turn sooner. |
| Tool-output budget | Defaults to 1,024 tokens (`configs/inference.json:63-66`; `tool_agent.py:938-943`). | **Medium prompt lever.** Reduce verbose Python output, particularly accumulated history, while retaining compact decision evidence. |
| Multimodal/image work | The user message may include the current-grid image (`tool_agent.py:1147-1158`). vLLM reports MM cache hits rising above 90% in later intervals (`duckmodcal/vllm-openai-server.log:903-910`). | **Low–medium.** Already heavily cached. Disable image input only if segmentation/ASCII is sufficient; otherwise the possible quality loss may outweigh saved encoder work. |
| Tensor parallelism / another GPU | Launcher fixes tensor parallel size from config (`kaggle.py:323-324`); logs show TP=1 and one server (`vllm-openai-server.log:17-20`). | **High if hardware exists, unavailable on the stated one-GPU setup.** A second independent server with game sharding is often preferable to assuming TP=2 will double decode. |

---

## 4. Is 28-way concurrency optimal?

Not proven, but the current evidence argues against simply lowering it as the first change.

At 25 active requests:

- Waiting is essentially zero.
- The GPU sustains roughly 200–235 aggregate decode tok/s.
- All games receive their full 7,920-second clock in one wave.
- The full run lasts only slightly longer than one game clock (`summary.txt:6-14`).

Reducing concurrency would raise each request’s instantaneous token rate, but if games run in waves, total runtime becomes approximately:

`ceil(25 / concurrency) × 7,920 seconds`

For concurrency 12, that is three waves, approximately 6.6 hours. If the job is capped near 2h12, later games would not run. Even without that cap, lower concurrency only wins if the reduced batch produces enough extra aggregate tokens/actions to offset extra waves.

The correct sweep metric is therefore:

**total valid environment actions across all 25 games per total job wall clock**, with score/quality as a guardrail.

Do not optimize per-request tok/s or one-game seconds/action in isolation.

---

## Highest-leverage recommendation

Set a hard `LOCAL_ANALYZER_MAX_OUTPUT`—initially test **768 or 1,024 tokens**—and, separately, test thinking disabled or tightly budgeted.

The decisive evidence chain is:

1. Actual runs set `LOCAL_ANALYZER_MAX_OUTPUT='0'` (`taaf-duck-v5.log:253`; `taaf-duck-mod.log:253`).
2. Zero becomes `self._max_output_tokens = None` (`tool_agent.py:935-937`).
3. That `None` is passed into request construction (`tool_agent.py:1289-1297`).
4. `max_tokens` is omitted when the value is `None` (`openai_compat.py:57-58`).
5. Thinking is enabled and preserved (`configs/inference.json:58`; `kaggle.py:330-334`).
6. Individual games emit up to approximately 5,380 generated tokens per nonzero turn on average, while an active request receives only 8–9 tok/s.
7. Generated tokens/action explains nearly all cross-game latency variation: **r≈0.99**.

This change attacks the actual bottleneck—unbounded serial decode under 25-way dilution—without reducing the number of games served or relying on public-game-specific behavior.

## Confidence and remaining measurement gap

- **High confidence:** token generation and actions-per-turn explain the latency spread; output is unbounded; 25 requests continuously share one GPU; prefix caching is on.
- **Medium confidence:** a 768–1,024 token cap will preserve enough reasoning quality. It needs a controlled run.
- **Unsettled:** true concurrency-one decode speed. The logs provide only aggregate throughput and active-request count, not a single-request benchmark.
- **Unsettled:** optimal concurrency. Run controlled sweeps after applying the output cap, because changing both simultaneously would confound the result.