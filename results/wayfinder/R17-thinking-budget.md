# ARC-AGI-3 reasoning-budget investigation

## Executive verdict

**Thinking-only budgeting is not feasible on the evidenced stack.**

The deployed stack exposes:

- A binary request-time switch: `chat_template_kwargs.enable_thinking`.
- A single total-completion limit: `max_tokens`.
- No evidenced `thinking_budget`, `max_thinking_tokens`, `reasoning_max_tokens`, or equivalent field.
- No harness forwarding mechanism for arbitrary request fields.
- No addition of such a capability in the five-weeks-newer upstream tree.

Therefore there is **no valid one-line intervention that bounds reasoning while preserving an independently unbounded tool-call payload**.

The only actionable one-line experiment is to disable reasoning entirely:

```python
os.environ["LOCAL_ANALYZER_ENABLE_THINKING"] = "false"
```

This must run before `tool_agent.py` is imported/configured. It is an on/off ablation, **not a reasoning budget**.

Falsifiable prediction: requests will contain `"chat_template_kwargs":{"enable_thinking":false}`, the separate reasoning field should become empty or nearly empty, and tool calls will remain governed by the uncapped total completion setting (`LOCAL_ANALYZER_MAX_OUTPUT=0`). Whether action quality remains acceptable is unverified.

---

## 1. What the deployed vLLM supports

The live server identifies itself as **vLLM 0.19.0**, serving a model resolved as `Qwen3_5ForConditionalGeneration`:

- Version and model: [vllm-openai-server.log](</mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/vllm-openai-server.log:3>)
- Resolved architecture: [vllm-openai-server.log](</mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/vllm-openai-server.log:8>)
- Maximum model length of 65,536: [vllm-openai-server.log](</mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/vllm-openai-server.log:9>)

Its relevant non-default launch configuration is:

- `reasoning_parser='qwen3'`
- `tool_call_parser='qwen3_coder'`
- `enable_auto_tool_choice=True`
- `default_chat_template_kwargs={'preserve_thinking': True}`

These are recorded at [vllm-openai-server.log](</mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/vllm-openai-server.log:7>). The corresponding launch construction is at [kaggle.py](</mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/kaggle.py:315>), specifically:

- Tool parser: lines 325–327.
- Default `preserve_thinking`: lines 331–332.
- Reasoning parser: lines 333–334.
- Model-length limit: lines 335–336.

### Supported control evidenced here

The smoke test demonstrates that the endpoint accepts:

```json
"chat_template_kwargs": {
  "enable_thinking": false
}
```

See [kaggle.py](</mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/kaggle.py:344>).

Thus, the artifacts directly evidence **binary reasoning on/off**.

`preserve_thinking` is a template-behavior flag, not a token budget. Neither the live launch arguments nor either source tree associates it with a numeric ceiling.

### Per-request reasoning limit

Searches of both source trees found no occurrence of:

- `thinking_budget`
- `max_thinking_tokens`
- `reasoning_max_tokens`
- `budget_tokens` used as a reasoning-generation limit

The newer tree still emits only:

```python
payload["chat_template_kwargs"] = {"enable_thinking": bool(thinking)}
```

at [newer openai_compat.py](</mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/utils/openai_compat.py:68>).

The two `openai_compat.py` files are identical. Upstream did not add a reasoning-budget knob during those five weeks.

**Conclusion:** the only reasoning-generation control evidenced by these artifacts is on/off. Whether an undocumented vLLM 0.19.0 field exists outside the supplied artifacts is **UNVERIFIED** and must not be relied upon.

---

## 2. Request construction and field forwarding

The action request is assembled at [tool_agent.py](</mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1282>).

The payload builder call begins at line 1289 and passes:

- `max_tokens` at line 1293.
- Sampling parameters at lines 1294–1296.
- The thinking boolean at line 1297.
- Tools and tool choice at lines 1298–1299.

The completed dictionary is posted unchanged as JSON at lines 1302–1307.

### Allow-list behavior

`build_chat_payload()` has an explicit argument signature at [openai_compat.py](</mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/utils/openai_compat.py:36>). It constructs a fixed payload containing:

- `model`, `messages`, `stream`, `temperature`, and `top_p`: lines 50–56.
- `max_tokens`: lines 57–58.
- `tools` and `tool_choice`: lines 59–62.
- `top_k`, `chat_template_kwargs`, and `seed` for vLLM: lines 64–70.

There is no `**kwargs`, `extra_body`, or generic dictionary merge. Consequently:

- Unknown settings cannot be supplied through the current builder API.
- A notebook cannot inject an arbitrary field merely by defining a new environment variable.
- A source or monkey patch could mutate the returned dictionary before `requests.post`, because the HTTP call itself forwards that dictionary unchanged.
- Such a patch would only help if the server actually supported the field—which is not evidenced here.

An implementation for a real budget field would belong immediately after payload creation at `tool_agent.py:1301`, or inside the vLLM branch at `openai_compat.py:64–70`.

---

## 3. What `LOCAL_ANALYZER_ENABLE_THINKING=true` does

The actual v8 environment used:

- `LOCAL_ANALYZER_MAX_OUTPUT="0"`: [taaf_setup_env.json](</mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/taaf_setup_env.json:18>)
- `LOCAL_ANALYZER_TEMPERATURE="0.6"`: line 23.
- `LOCAL_ANALYZER_TOP_P="0.95"`: line 24.
- `LOCAL_ANALYZER_TOP_K="20"`: line 25.
- `LOCAL_ANALYZER_ENABLE_THINKING="true"`: line 26.
- Harness context window 32,768: line 17.

At request time, that environment value flows through:

1. `_LOCAL_ANALYZER_ENABLE_THINKING` into the builder at [tool_agent.py](</mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1297>).
2. The builder emits:

   ```python
   payload["chat_template_kwargs"] = {
       "enable_thinking": bool(thinking)
   }
   ```

   at [openai_compat.py](</mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/utils/openai_compat.py:68>).

Setting the environment variable to false mechanically changes only that request value from `true` to `false`. It does not create or alter a token limit.

`LOCAL_ANALYZER_MAX_OUTPUT=0` is converted to `self._max_output_tokens=None` at [tool_agent.py](</mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/agent/tool_agent.py:935>), so no `max_tokens` field is emitted.

### Transcript composition

The sampled `ar25-0c556536_p0.txt` transcript contains 36 recorded completions:

- 270,732 reasoning characters.
- 22,892 serialized tool-call JSON characters.
- Reasoning therefore represents **92.2% by characters**.
- A simple word/number/punctuation token proxy puts reasoning at **87.9% of generated units**.

Across all 25 supplied v8 transcript files—1,094 completions—the corresponding figures are:

- 6,324,697 reasoning characters.
- 772,514 tool-call JSON characters.
- **89.1% reasoning by characters**.
- **84.8% reasoning under the lexical token proxy**.

A concrete first response shows `reasoning_chars: 394`, followed separately by the raw Python tool call and the `[THINKING]` block at approximately [ar25 transcript](</mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/transcripts/ar25-0c556536_p0.txt:147>).

These are not exact Qwen token fractions. The transcript formatter records character counts, not usage tokens, at [tool_agent.py](</mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/agent/tool_agent.py:323>). Although the response object receives server `usage` at lines 1325–1334, those per-request counts are not written into the transcript metadata.

Therefore, the exact generated-token fraction is **UNVERIFIED**. The available evidence nevertheless shows that reasoning overwhelmingly dominates output size.

---

## 4. Safe middle paths

### Total-output cap

No safe independently-action-preserving total cap exists. `max_tokens` covers the entire completion, including reasoning and tool-call serialization.

The uncapped v8 corpus had the following combined reasoning-plus-tool-call lengths:

| Percentile | Characters | Lexical token proxy |
|---|---:|---:|
| p50 | 4,959 | 1,602 |
| p90 | 14,653 | 4,621 |
| p95 | 19,704 | 6,164 |
| p99 | 26,870 | 9,457 |
| Maximum | 35,316 | 11,996 |

Thus, a cap near **9,500 tokens** is the proxy p99, and **12,000 tokens** exceeds the observed proxy maximum. Neither is a verified Qwen-token boundary, and both remain total caps capable of truncating a long action after long reasoning.

The exact `max_tokens` value that would preserve 99% is **UNVERIFIED**, because per-completion tokenizer counts were not retained. Using 9,500 as though it were exact would repeat the same category of unsafe intervention, merely at a higher threshold.

A very large cap also reduces the harness’s usable input-history budget because it reserves the configured output allowance when computing context space at [tool_agent.py](</mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/agent/tool_agent.py:935>).

### Disable tool-call requirement

The harness does not force a specific tool call; `_request_tool_choice()` returns `"auto"` when tools exist at [tool_agent.py](</mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/agent/tool_agent.py:311>). Removing tools would remove the Python action channel rather than protect it. It is not a useful middle path.

### Stop sequence

No `stop` field is exposed by `build_chat_payload()`. More importantly, the response presents reasoning separately from the tool call after parsing. There is no evidenced textual delimiter that can safely stop reasoning while instructing generation to continue into the tool-call payload. An ordinary stop sequence terminates generation; it does not transition from reasoning to an exempt output budget.

### Structured output

No `response_format`, guided-output, or structured-output setting is included in the request builder. The server log shows structured-output parsing configured with `enable_in_reasoning=False`, but that does not provide a reasoning-length budget. The required action is already represented as a tool call; changing its schema would not exempt it from `max_tokens`.

### Binary thinking-off mode

This is the only credible speed-oriented experiment visible in the code:

```python
os.environ["LOCAL_ANALYZER_ENABLE_THINKING"] = "false"
```

It preserves the tool interface and avoids adding a total cap, but it removes explicit reasoning rather than bounding it. Its effect on ARC performance must be measured.

---

## Final decision

**Thinking-only budget feasibility: NO, on the supplied stack and evidence.**

There is no exact one-line reasoning-budget intervention to recommend. The stack implements only:

```text
thinking = on/off
total completion = optionally capped
```

It does not implement:

```text
reasoning ≤ N tokens
tool-call payload remains independently available
```

The appropriate next experiment is the binary ablation, executed before importing the harness:

```python
import os; os.environ["LOCAL_ANALYZER_ENABLE_THINKING"] = "false"; os.environ["LOCAL_ANALYZER_MAX_OUTPUT"] = "0"
```

Prediction:

1. Outgoing requests contain `chat_template_kwargs.enable_thinking=false`.
2. `max_tokens` remains absent.
3. Separate reasoning output largely disappears.
4. Python tool-call payloads are no longer endangered by a configured total ceiling.
5. Wall-clock generation should fall materially because roughly 85–90% of sampled generated material is reasoning under the available proxies.
6. ARC score may rise, fall, or remain stable; that quality effect is **UNVERIFIED**.

A genuine middle setting requires a server/model-template feature that counts reasoning tokens separately and forces the reasoning terminator without ending tool-call generation. No such feature is evidenced in vLLM 0.19.0’s live configuration or either supplied harness tree.