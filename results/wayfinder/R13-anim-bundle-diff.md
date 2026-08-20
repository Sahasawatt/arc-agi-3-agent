# Upstream duck-harness evolution review

## Executive recommendation

**Choose (a) REBASE:** build the next campaign notebook on the public animation-aware bundle and reapply only the small customization cell.

This is substantially safer than porting isolated files. Animation-awareness is a coordinated, end-to-end change across engine-frame capture, solver state, sandbox IPC, model-visible metadata, prompts, logging, and the no-op guard. A partial port could silently retain the exact last-frame blindness it is intended to fix.

The anim bundle’s `setup_commands.json` is byte-identical to our current bundle and retains the exact `MODEL_OWNER`, `MODEL_SLUG`, and `SERVED_MODEL_NAME` assignments used by the R12-style rewrite. Rebase therefore preserves our model-swap seam without a new deployment integration problem ([anim setup_commands.json:2](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/setup_commands.json:2), [current setup_commands.json:2](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/setup_commands.json:2)).

One customization should be added immediately: **cap analyzer output**. Upstream still sets `analyzer.max_output` to `0`, meaning uncapped, while leaving thinking enabled at temperature `0.6` ([inference.json:55](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/configs/inference.json:55)). Given the measured ~9 tokens/s and identified throughput leak, do not inherit that value unchanged.

Verdict: **REBASE, with a minimal campaign overlay; do not copy only `noop_guard.py`, `animation.py`, and prompts.**

---

## 1. Substantive source changes

### `inference/agent/tool_agent.py`

This is the principal behavior change.

- Adds two default-on experiment switches, `ARC3_HARD_NOOP_GUARD` and `ARC3_ANIMATION_AWARENESS`. Explicit constructor values override process environment values, allowing the selected behavior to survive benchmark pickling and Kaggle deployment ([tool_agent.py:161](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:161), [tool_agent.py:1108](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1108)).

- Computes the pending action signature before execution, including canonicalized `MOUSE(row=…, col=…)` coordinates, so a known no-op can be recognized before spending an environment action ([tool_agent.py:200](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:200)).

- For a single known no-op, it does **not** call the environment. It returns `executed=False`, `executed_count=0`, `stop_reason="known_noop"`, and explicitly says that no action budget was spent ([tool_agent.py:1775](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1775), [tool_agent.py:1798](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1798)).

- Multi-action batches are now walked one action at a time so known no-ops can be filtered independently. Results are reaggregated with total reward, executed/blocked counts, terminal reason, maximum per-action frame count, and the most informative animation summary ([tool_agent.py:280](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:280), [tool_agent.py:1854](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1854), [tool_agent.py:1889](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1889)).

- Animated actions are explicitly excluded from no-op classification using `frame_count > 1`, even if their final board matches the initial board ([tool_agent.py:221](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:221)).

- Adds compact animation descriptions to the next model digest and a proactive hint when the agent is stuck on a level with hidden transient information ([tool_agent.py:1204](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1204), [tool_agent.py:1441](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1441)).

- Adds the host-side handler for `animation()`. It retrieves a stored animation through the solver callback without executing an action, builds a budgeted view, and records whether retrieval was prompted or spontaneous ([tool_agent.py:1906](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1906)).

Why it matters: this file converts animation-awareness and no-op prevention into actual loop behavior. Porting only the utility modules would achieve neither.

### `inference/agent/prompts.py`

The runtime-state addendum now tells the model:

- `current_frame` is only the final animation frame.
- `last_action_result["animation"]` carries frame count, unique-frame count, final-board status, transient-pixel count, and transient bounding box.
- An unchanged final board after an animation is not evidence of a no-op.
- `animation()` retrieves a compact timeline or a cropped individual frame without spending action budget ([prompts.py:63](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/prompts.py:63)).

Why it matters: metadata and retrieval would be weakly adopted unless the model knows the semantic distinction between `board_changed` and intermediate-frame effects.

### `inference/agent/python_tool_sandbox.py`

Adds an `animation(action_num=None, frame=None, region=None)` sandbox function. It sends an IPC request to the host, receives either `animation_result` or a sanitized `animation_error`, and exposes the function only when animation support is enabled ([python_tool_sandbox.py:369](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/python_tool_sandbox.py:369), [python_tool_sandbox.py:474](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/python_tool_sandbox.py:474), [python_tool_sandbox.py:585](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/python_tool_sandbox.py:585)).

Why it matters: raw animation data stays in the trusted host process; only a compact, size-controlled representation crosses into the Python tool.

### `inference/agent/noop_guard.py`

The new guard stores exact `(level, board-before signature, action signature)` facts. Board signatures are 8-byte BLAKE2b digests of normalized integer grids; action signatures have whitespace normalized ([noop_guard.py:16](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/noop_guard.py:16), [noop_guard.py:23](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/noop_guard.py:23)).

Storage is bounded to 512 board states per level and 16 actions per board state, with oldest entries evicted ([noop_guard.py:27](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/noop_guard.py:27), [noop_guard.py:34](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/noop_guard.py:34), [noop_guard.py:78](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/noop_guard.py:78)).

It records a no-op only when both `board_changed=False` and `animated=False`. If later evidence shows either a board change or animation for the same tuple, the stale no-op is removed ([noop_guard.py:39](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/noop_guard.py:39), [noop_guard.py:67](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/noop_guard.py:67)).

Why it matters: it prevents waste while narrowly keying the intervention to an exact level and visible state.

### `inference/utils/animation.py`

This is the exact implementation of the last-plane fix.

- It normalizes every frame returned for an action, not merely `raw.frame[-1]` ([animation.py:3](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/utils/animation.py:3), [animation.py:59](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/utils/animation.py:59)).

- It identifies transient cells by comparing every intermediate frame with the final frame. These are precisely the cells that final-plane-only inspection cannot observe ([animation.py:68](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/utils/animation.py:68)).

- Multi-frame actions receive compact metadata: total frames, unique frames, whether the final board is unchanged from before the action, transient-pixel count, and an inclusive transient bounding box. Single-frame actions receive no animation block, avoiding ordinary-turn token overhead ([animation.py:86](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/utils/animation.py:86)).

- Retrieval collapses consecutive identical frames and produces a transition timeline rather than raw 64×64 planes. Budgets are 8 timeline steps, 24 enumerated cells per step, 80 cells overall, and 1,024 cells for a cropped frame ([animation.py:28](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/utils/animation.py:28), [animation.py:268](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/utils/animation.py:268)).

- `animation(frame=k)` returns one cropped frame. Without an explicit region it uses the transient bounding box plus two cells of padding; full-board responses are intentionally prohibited by the crop budget ([animation.py:191](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/utils/animation.py:191), [animation.py:238](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/utils/animation.py:238)).

- The proactive hint requires at least 6 turns without progress, 2 qualifying animations, and 8 transient pixels in each counted animation; the cooldown is 6 turns and retrieval within 3 turns is counted as following the hint ([animation.py:44](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/utils/animation.py:44), [animation.py:332](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/utils/animation.py:332)).

### `inference/framework/solver.py`

This is the engine-side half of the feature.

- Reads the entire raw frame list for every executed action and independently reports frame count ([solver.py:107](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/solver.py:107), [solver.py:817](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/solver.py:817)).

- Stores the last four animated actions in an in-memory deque. The full planes are deliberately not serialized to runtime state ([solver.py:62](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/solver.py:62), [solver.py:216](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/solver.py:216)).

- Handles `query="animation"` as a read-only query. It executes nothing and consumes no environment action ([solver.py:663](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/solver.py:663), [solver.py:684](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/solver.py:684)).

- Persists `hard_noop_guard` and `animation_awareness` as solver fields so their values travel inside `benchmark_initial.pkl` and are passed into every `ToolAgent` ([solver.py:884](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/solver.py:884), [solver.py:1362](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/solver.py:1362)).

- Emits per-attempt experiment counters for stage-1 metadata, stage-2 retrieval, and stage-3 hinting, allowing adoption/effect analysis after a run ([solver.py:458](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/solver.py:458)).

### `inference/framework/run.py`

The anim branch removes its dependency on the old local catalog package.

- Dataset/tag enumeration is removed. Built-in selection is limited to explicit game IDs or the 25 hardcoded official games ([run.py:117](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/run.py:117)).

- With no explicit local directory, ordinary runs fall back to the live online API. Kaggle deployment instead supplies its competition-mounted offline directory because competition-attached notebooks cannot access the internet ([run.py:165](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/run.py:165), [run.py:182](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/run.py:182)).

- The CLI option is renamed from the package-specific form to the generic `--environments-dir` ([run.py:1235](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/run.py:1235)).

Why it matters: rebase changes how local/offline testing is selected. Existing scripts depending on dataset/tag enumeration need conversion to explicit game lists.

### `configs/inference.json`

The inference behavior is essentially unchanged:

- Model remains `vrfai/Qwen3.6-27B-FP8`, context window 32,768 ([inference.json:2](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/configs/inference.json:2)).
- `max_output` remains **0/unbounded**.
- Thinking remains enabled.
- Temperature remains `0.6`, with `top_p=0.95` and `top_k=20`.
- Tool output remains limited to 1,024 tokens ([inference.json:55](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/configs/inference.json:55)).

Only infrastructure defaults change: result root `/sw` → `/shared`, local catalog source removed, Slurm partition/account defaults changed, and viewer port becomes 8022 ([inference.json:8](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/configs/inference.json:8), [inference.json:23](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/configs/inference.json:23), [inference.json:75](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/configs/inference.json:75)).

Campaign implication: animation-awareness does **not** address the measured generation-throughput leak. Set `LOCAL_ANALYZER_MAX_OUTPUT` to an experimentally chosen finite cap in the customization cell.

### Evaluation tools

- `eval.py` stops writing the removed local-catalog commit into score metadata; all other score construction remains intact ([eval.py:664](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/tools/eval.py:664)).

- `significance.py` drops only the compatibility check requiring equal local-catalog commits. Hardware, dataset, runtime-budget, trial-count, and model compatibility remain ([significance.py:606](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/tools/significance.py:606)).

- `traces.py` now gets per-level baseline-action counts from the run artifact itself instead of an external local catalog. Missing or invalid baseline values disable per-level rescoring ([traces.py:279](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/tools/traces.py:279), [traces.py:625](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/tools/traces.py:625)).

### TAAF changes

- `competition_arcade.py` embeds the 25 public official IDs instead of importing them from the removed catalog dependency ([competition_arcade.py:48](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/tufa-arc-agi-framework/src/taaf/competition_arcade.py:48), [competition_arcade.py:59](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/tufa-arc-agi-framework/src/taaf/competition_arcade.py:59)).

- `game_api.py` no longer resolves the `__auto__` sentinel. It rejects that mode; callers must use an explicit local directory or live competition arcade ([game_api.py:22](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/tufa-arc-agi-framework/src/taaf/game_api.py:22), [game_api.py:30](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/tufa-arc-agi-framework/src/taaf/game_api.py:30)).

- `standard_benchmarks.py` disables the former all-game benchmark and builds the official-110 benchmark from the embedded 25-game list ([standard_benchmarks.py:16](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/tufa-arc-agi-framework/src/taaf/standard_benchmarks.py:16), [standard_benchmarks.py:54](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/tufa-arc-agi-framework/src/taaf/standard_benchmarks.py:54)).

- `deploy_kaggle.py` no longer excludes a separate catalog repository from public bundles because that source is gone. Authentication is delegated to the standard Kaggle CLI rather than loading `.env` files and manually injecting keys into subprocesses ([deploy_kaggle.py:46](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/tufa-arc-agi-framework/src/taaf/deploy_kaggle.py:46), [deploy_kaggle.py:211](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/tufa-arc-agi-framework/src/taaf/deploy_kaggle.py:211), [deploy_kaggle.py:411](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/tufa-arc-agi-framework/src/taaf/deploy_kaggle.py:411)).

- `deploy.py` and `deploy_slurm.py` have comment/documentation generalization only; no material runtime change.

- Both `pyproject.toml` files remove the old local-catalog package dependency. ARC3-Inference also changes its keyword from `re-arc` to `arc-agi` ([ARC3 pyproject.toml:13](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/pyproject.toml:13), [TAAF pyproject.toml:8](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/tufa-arc-agi-framework/pyproject.toml:8)).

---

## 2. No-op guard: intervention versus advisory digest

The guard is a **hard loop intervention**.

Mechanism:

1. Before executing an action, the agent hashes the current grid and combines it with level and normalized action signature ([tool_agent.py:1733](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1733)).
2. If that exact tuple was previously observed with no board change and no animation, the environment callback is skipped ([tool_agent.py:1775](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1775)).
3. The model receives a synthetic action result explaining the block, but that information is secondary—the prohibited action has already been prevented ([tool_agent.py:1783](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1783)).
4. The default state/action capacities are 512 per level and 16 per state; there is no confidence threshold or repeat threshold. One verified single-frame no-op is sufficient ([noop_guard.py:34](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/noop_guard.py:34)).

By contrast, advisory warnings in the digest merely ask the model to cooperate. The module’s own history says that the earlier advisory approach left approximately 12% repeated no-ops; this guard was introduced specifically to block them before execution ([noop_guard.py:1](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/noop_guard.py:1)).

One caution: because one observation is enough, correctness depends heavily on the animation exemption. Upstream correctly treats every multi-frame response as real evidence and therefore never records it as a no-op ([noop_guard.py:48](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/noop_guard.py:48)).

---

## 3. Animation-awareness data path

Yes—this is the fix for reading only the final plane.

```text
Environment action
  → all raw frames normalized
  → compact metadata added to action result
  → full frames retained for last 4 animated actions in solver memory
  → digest tells model that an animation occurred
  → model may call animation()
  → sandbox IPC asks host
  → host returns compact diff timeline or cropped frame
```

What is retrieved:

- Default `animation()`: deduplicated, chronological frame-difference timeline.
- `animation(frame=k)`: one verbatim frame cropped around the transient region or an explicitly supplied region.
- `animation(action_num=n)`: one of the most recent four animated actions ([animation.py:214](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/utils/animation.py:214), [solver.py:62](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/solver.py:62)).

When it reaches the model:

- Immediately after any animated action, compact metadata and a natural-language description enter the following digest ([tool_agent.py:1282](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1282), [tool_agent.py:1441](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1441)).
- Detailed frames reach the model only on an explicit Python `animation()` call.
- After six non-progress turns and two animations containing at least eight transient pixels, the digest proactively suggests that call ([animation.py:52](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/utils/animation.py:52)).

This is deliberately more than “feed all planes to the model”: it detects which intermediate pixels disappear from the final plane and exposes them under a strict response budget.

---

## 4. FOYSAL LB-9 notebook customization

The notebook adds four important layers above the anim bundle.

### Model swap

It swaps Qwen3.6-27B-FP8 for:

- Owner: `foysalemonshanto`
- Model: `qwen3-8-27b-fp8-repacked-v1`
- Variation/version: `hf-fp8/1`
- Served name: `Qwen/Qwen3.8-27B-FP8`

It validates a repacked 18-file safetensors layout, including 16 layer shards, before starting vLLM ([FOYSAL notebook:1](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/lb-9-arc3-duck-v12-with-qwen-3-8-27b/lb-9-arc3-duck-v12-with-qwen-3-8-27b.ipynb:1)).

### Setup-command patching

Rather than replacing the setup script, it regex-rewrites the three stable assignments:

- `MODEL_OWNER`
- `MODEL_SLUG`
- `SERVED_MODEL_NAME`

It also injects offline Hugging Face/Transformers variables and fails if any expected assignment is missing ([FOYSAL notebook:1](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/lb-9-arc3-duck-v12-with-qwen-3-8-27b/lb-9-arc3-duck-v12-with-qwen-3-8-27b.ipynb:1)).

That patch is compatible with both our setup file and the anim bundle because those files are identical and contain the same assignments ([anim setup_commands.json:2](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/setup_commands.json:2)).

### Runtime/environment overrides

It enables strict offline operation, maps all Kaggle inputs into `TAAF_KAGGLE_INPUT_PATHS`, enables reset-only behavior, and suppresses heavy diagnostics during real submissions ([FOYSAL notebook:1](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/lb-9-arc3-duck-v12-with-qwen-3-8-27b/lb-9-arc3-duck-v12-with-qwen-3-8-27b.ipynb:1)).

### Public-evaluation override

Outside a true competition rerun, it replaces the bundled benchmark games with all 25 public games, sets:

- `n_passes = 1`
- `game_weights = None`
- `concurrency = 28`
- `max_runtime_s_per_game = 7920`

A true rerun instead replaces the games from the live competition gateway and also uses one pass ([FOYSAL notebook:1](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/lb-9-arc3-duck-v12-with-qwen-3-8-27b/lb-9-arc3-duck-v12-with-qwen-3-8-27b.ipynb:1)).

### Where the Qwen3.8 weights come from

The model is **not** one of the two dataset inputs. It is a separate attached **Kaggle Model**, `modelInstanceVersion` source ID `966079`, mounted under `/kaggle/input/models/foysalemonshanto/qwen3-8-27b-fp8-repacked-v1/pytorch/hf-fp8/1` ([FOYSAL notebook:1](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/lb-9-arc3-duck-v12-with-qwen-3-8-27b/lb-9-arc3-duck-v12-with-qwen-3-8-27b.ipynb:1)).

Thus the apparent list `[wheelhouse, anim-source]` describes datasets only; the weights arrive through Kaggle’s separate Model attachment system.

---

## 5. Rebase versus port

### Recommend: REBASE

Reasons:

1. **Animation-awareness is cross-layer.** The source must capture all frames, retain them, answer read-only queries, bridge them through sandbox IPC, summarize them, prompt the model, and exempt animations from no-op blocking. Porting selected files risks an apparently enabled but nonfunctional feature.

2. **The deployment seam is unchanged.** The two `setup_commands.json` files have the same SHA-256 and preserve the R12 rewrite points ([anim setup_commands.json:2](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/setup_commands.json:2), [current setup_commands.json:2](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/setup_commands.json:2)).

3. **The benchmark pickle is materially different.** The anim pickle contains `hard_noop_guard=True` and `animation_awareness=True`, while the milestone pickle predates those solver fields. It also contains six targeted games, four passes, concurrency 28, and a 7,920-second per-game cap; the milestone pickle has a larger game set and one pass. The notebook can override the game list and passes as FOYSAL does, but the anim pickle is the correct schema carrier for the new solver ([solver.py:884](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/solver.py:884), [FOYSAL notebook:1](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/lb-9-arc3-duck-v12-with-qwen-3-8-27b/lb-9-arc3-duck-v12-with-qwen-3-8-27b.ipynb:1)).

4. **Our duckmod additions can be deleted.** With measured zero adoption for `hud_mask` and TransitionGraph, retaining a fork solely to preserve them adds merge and prompt surface without demonstrated value.

5. **Upstream has removed a dependency and changed offline selection.** Rebase makes the new assumptions coherent across source packaging, benchmark construction, Kaggle paths, and evaluation tools; piecemeal porting leaves a hybrid whose local-catalog semantics differ from upstream.

### Minimal campaign overlay after rebase

Keep only:

- R12 model-owner/slug/served-name rewrite.
- Attached-model path mapping and offline environment settings.
- Explicit evaluation game list, `n_passes`, concurrency, and runtime cap.
- A finite `LOCAL_ANALYZER_MAX_OUTPUT`.
- Optional explicit `ARC3_HARD_NOOP_GUARD=true` and `ARC3_ANIMATION_AWARENESS=true` for auditability, although the pickled solver already defaults both on.
- Any proven submission/runtime fixes.

Drop:

- `hud_mask`.
- TransitionGraph tools.
- Any prompt material that describes those unused tools.
- Old local-catalog compatibility glue.
- Any duplicated animation/no-op patch already present upstream.

### Suggested rollout

Run a small paired campaign before the full spend:

- Same model and decoding settings.
- Same games and seeds.
- Arm A: animation-aware + no-op guard.
- Arm B: both disabled through solver fields.
- Record completion score, actions consumed, repeated-no-op blocks, animation retrieval count, hint-follow rate, generated tokens, and wall time.

Then separately test output caps; do not confound the animation adoption comparison with a simultaneous token-cap change.

---

## 6. Evaluation-protocol changes to adopt

### Adopt

- **Artifact-contained baseline scoring.** It makes trace rescoring reproducible without an external catalog revision ([traces.py:279](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/tools/traces.py:279)).

- **Animation experiment counters.** Use these to distinguish:
  - animations merely detected,
  - explicit unprompted retrieval,
  - proactive hints emitted,
  - hints followed ([solver.py:463](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/solver.py:463), [tool_agent.py:1906](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1906)).

- **Explicit game lists for fast evaluation.** Dataset/tag discovery is no longer supported beyond `official`; freeze the evaluation IDs in the customization cell ([run.py:117](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/run.py:117)).

- **One-pass fast evaluation only as screening.** FOYSAL’s 25-game × 1-pass shape is suitable for coverage and gross regression detection, not for a final significance claim ([FOYSAL notebook:1](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/lb-9-arc3-duck-v12-with-qwen-3-8-27b/lb-9-arc3-duck-v12-with-qwen-3-8-27b.ipynb:1)).

### Do not inherit blindly

- The bundle’s pickle uses a six-game animation-focused set with `n_passes=4`; that is an experiment fixture, not a campaign-wide evaluation protocol.
- FOYSAL’s notebook overwrites it to 25 games × 1 pass. Use that for broad smoke evaluation, then increase passes for decisions.
- Dropping the old catalog-commit compatibility check is appropriate because the dependency disappeared, but comparisons must still use the same explicit game IDs and equivalent environment build ([significance.py:606](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/tools/significance.py:606)).
- Upstream does not introduce a new significance threshold or statistical method; it only removes the obsolete catalog-commit gate.
- Upstream does not solve uncapped generation. Apply and benchmark a finite output cap before the full campaign ([inference.json:55](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/configs/inference.json:55)).

## Bottom line

Rebase onto the anim bundle, reproduce FOYSAL’s narrow setup/model rewrite strategy, explicitly override the benchmark for each campaign phase, and add a finite analyzer-output cap. The animation feature directly addresses the multi-plane keyhole, and the no-op guard is a genuine action-budget-saving intervention. Porting selected files would carry considerably more correctness risk for no compensating benefit.