# Kaggle vLLM model-selection trace

## Conclusion

At kernel runtime, vLLM’s launch command does **not** come from the solver pickle and is **not regenerated** by `duck_kaggle_setup_command()`. It is already rendered and stored in the attached read-only share dataset as:

[`duck/bundle/setup_commands.json`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/setup_commands.json:2)

The notebook reads that JSON and executes each command **before** loading `benchmark_initial.pkl`:

[`taaf_kaggle_run_share.ipynb`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/tufa-arc-agi-framework/src/taaf/kaggle/taaf_kaggle_run_share.ipynb:247)

Therefore the minimal safe customization is:

1. Attach `jakobbrggen/qwen3-8-27b-fp8-hf-snapshot`.
2. Replace the old dataset ref in notebook cell 6.
3. Rewrite three embedded assignments in each command immediately after loading it from `setup_commands.json`, before `subprocess.run()`.

No share-dataset file needs to be changed.

I use `vrfai/Qwen3.8-27B-FP8` below as the served name, preserving the existing logical namespace. vLLM treats this as an arbitrary API alias, so another exact alias is possible as long as every client-facing value uses it consistently.

---

## 1. Where the launch command lives

### Deployment/build time

`HarnessSolver.kaggle_setup_commands` calls `duck_kaggle_setup_command()`:

- Property: [`solver.py:859`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/solver.py:859)
- Command generation: [`solver.py:862`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/solver.py:862)
- Solver fields converted into `DuckKaggleVllmConfig`: [`solver.py:870`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/solver.py:870)

During deployment, `KaggleTarget.deploy()` reads that solver property and collects its rendered result:

[`deploy_kaggle.py:231`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/tufa-arc-agi-framework/src/taaf/deploy_kaggle.py:231) through [`deploy_kaggle.py:253`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/tufa-arc-agi-framework/src/taaf/deploy_kaggle.py:253).

It then writes the strings to `setup_commands.json`:

[`deploy_kaggle.py:512`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/tufa-arc-agi-framework/src/taaf/deploy_kaggle.py:512)

The benchmark and deploy target are pickled separately at lines 505–506; the setup commands are not read from either pickle at kernel runtime:

[`deploy_kaggle.py:505`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/tufa-arc-agi-framework/src/taaf/deploy_kaggle.py:505)

### Kernel runtime

The notebook performs this exact sequence:

```python
env = _command_env()
for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    print(f"taaf.kaggle: setup command: {command}", flush=True)
    subprocess.run(command, shell=True, check=True, cwd=WORKING_DIR, env=env)
    env = _command_env()
    os.environ.update(env)
```

Source: [`taaf_kaggle_run_share.ipynb:247-254`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/tufa-arc-agi-framework/src/taaf/kaggle/taaf_kaggle_run_share.ipynb:247).

Only afterward does the notebook open `benchmark_initial.pkl`—cell 10 in the customized notebook. Thus mutating the solver pickle cannot change the already executed launch.

### Rendered command contents

The local bundle’s command is one heredoc string in [`setup_commands.json:2`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/setup_commands.json:2), beginning effectively as:

```bash
"$PYTHON" - <<'PYSETUP'
...
MODEL_OWNER = 'driessmit1'
MODEL_SLUG = 'vrfai-qwen3-6-27b-fp8-hf-snapshot'
SERVED_MODEL_NAME = 'vrfai/Qwen3.6-27B-FP8'
...
MODEL_PATH = resolve_kaggle_dataset_path(MODEL_OWNER, MODEL_SLUG)
...
cmd = [
    sys.executable,
    '-m', 'vllm.entrypoints.openai.api_server',
    '--model', str(MODEL_PATH),
    '--served-model-name', SERVED_MODEL_NAME,
    ...
    '--tool-call-parser', 'qwen3_coder',
    ...
    '--reasoning-parser', 'qwen3',
]
```

The corresponding source template resolves the model mount from `TAAF_KAGGLE_INPUT_PATHS` at [`kaggle.py:173-194`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/kaggle.py:173), then passes the resolved path and served alias to vLLM at [`kaggle.py:306-337`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/kaggle.py:306).

---

## 2. Recommended intervention

### Required attachment change

The target dataset must be attached to the notebook/kernel. The existing kernel metadata attaches the old dataset at:

[`duck/kernel-metadata.json:14-18`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/kernel-metadata.json:14)

Replace:

```text
driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot
```

with:

```text
jakobbrggen/qwen3-8-27b-fp8-hf-snapshot
```

In notebook cell 6, make the same replacement in `DATASET_SOURCES`. That cell resolves each attached dataset’s actual Kaggle mount and publishes the map as `TAAF_KAGGLE_INPUT_PATHS`:

[`taaf_kaggle_run_share.ipynb:172-193`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/tufa-arc-agi-framework/src/taaf/kaggle/taaf_kaggle_run_share.ipynb:172)

### Exact command rewrite

In setup cell 8, add the rewrite immediately inside the loop and before the print/run:

```python
for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    command = (
        command
        .replace(
            "MODEL_OWNER = 'driessmit1'",
            "MODEL_OWNER = 'jakobbrggen'",
        )
        .replace(
            "MODEL_SLUG = 'vrfai-qwen3-6-27b-fp8-hf-snapshot'",
            "MODEL_SLUG = 'qwen3-8-27b-fp8-hf-snapshot'",
        )
        .replace(
            "SERVED_MODEL_NAME = 'vrfai/Qwen3.6-27B-FP8'",
            "SERVED_MODEL_NAME = 'vrfai/Qwen3.8-27B-FP8'",
        )
    )
    print(f"taaf.kaggle: setup command: {command}", flush=True)
    subprocess.run(command, shell=True, check=True, cwd=WORKING_DIR, env=env)
    env = _command_env()
    os.environ.update(env)
```

For fail-fast protection against upstream command changes, add:

```python
assert "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot" not in command
assert "vrfai/Qwen3.6-27B-FP8" not in command
```

Ordering is strict:

```text
attach dataset
  → run cell 6 and build TAAF_KAGGLE_INPUT_PATHS
  → rewrite command in cell 8
  → subprocess.run(command)
  → setup command writes analyzer environment
  → load benchmark pickle
```

### Why this is sufficient

The rewritten `MODEL_OWNER` and `MODEL_SLUG` produce the lookup key:

```text
jakobbrggen/qwen3-8-27b-fp8-hf-snapshot
```

That exactly matches the key generated in cell 6’s `TAAF_KAGGLE_INPUT_PATHS`. The resolver uses that mapping first, before fallback mount guesses:

[`kaggle.py:183-190`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/kaggle.py:183)

The rewritten `SERVED_MODEL_NAME` is reused by all three consumers:

- vLLM `--served-model-name`: [`kaggle.py:317-318`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/kaggle.py:317)
- Smoke-test request model: [`kaggle.py:344-352`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/kaggle.py:344)
- Both analyzer environment variables: [`kaggle.py:378-379`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/kaggle.py:378)

The command merges these values into `/kaggle/working/taaf_setup_env.json`; `_command_env()` rereads that file after every setup command and updates the notebook environment:

[`taaf_kaggle_run_share.ipynb:224-254`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/tufa-arc-agi-framework/src/taaf/kaggle/taaf_kaggle_run_share.ipynb:224)

---

## 3. Option ranking

1. **Rewrite the command loaded from `setup_commands.json` before execution — recommended.**  
   This reaches the actual kernel-runtime artifact and changes the model path, server alias, smoke test, and persisted analyzer environment together.

2. **Simpler variant: replace the three literals directly in notebook cell 8.**  
   Functionally identical to option 1. It is the smallest intervention if editing the existing cell is acceptable.

3. **Rewrite `taaf_setup_env.json` between setup steps — insufficient for a full swap.**  
   The model path and vLLM alias are already embedded in the Python heredoc. Changing the JSON cannot alter `MODEL_PATH` or the server’s `--served-model-name`. Moreover, the setup command later overwrites `LOCAL_ANALYZER_MODEL_ID` and `INFERENCE_ANALYZER_MODEL` from `SERVED_MODEL_NAME` at [`kaggle.py:368-401`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/kaggle.py:368).

4. **Monkeypatch `duck_kaggle_setup_command()` or `DuckKaggleVllmConfig` — ineffective at kernel runtime.**  
   Generation happened during bundle deployment. The notebook only reads the frozen JSON command; it never calls those APIs before launching vLLM.

5. **Mutate the loaded solver object — too late and wrong artifact.**  
   The benchmark pickle is loaded only after setup. Although the pickle contains `kaggle_model_dataset_source` and `kaggle_served_model_name`, those fields were consumed earlier when the bundle was built. Read-only pickle inspection found them at byte offsets 2742/2772 and 2819/2846 respectively.

---

## 4. Complete swap checklist

Must change:

- Attached dataset metadata:
  `jakobbrggen/qwen3-8-27b-fp8-hf-snapshot`
- Cell 6 `DATASET_SOURCES`
- `TAAF_KAGGLE_INPUT_PATHS` key, obtained automatically from the updated cell 6 list
- Embedded `MODEL_OWNER`
- Embedded `MODEL_SLUG`
- Embedded `SERVED_MODEL_NAME`
- Resulting `LOCAL_ANALYZER_MODEL_ID`, obtained automatically from `SERVED_MODEL_NAME`
- Resulting `INFERENCE_ANALYZER_MODEL`, obtained automatically from `SERVED_MODEL_NAME`
- vLLM `--served-model-name`, obtained automatically from `SERVED_MODEL_NAME`
- Smoke-test request’s `model`, obtained automatically from `SERVED_MODEL_NAME`

No manual change required:

- `LOCAL_ANALYZER_BASE_URL` / `OPENAI_BASE_URL`
- Port
- Context window, unless the new snapshot needs a different limit
- `--reasoning-parser qwen3`
- `--tool-call-parser qwen3_coder`
- Chat-template flags

The parsers are not tied to the `3.6` string; they are hardcoded independently at [`kaggle.py:325-334`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/kaggle.py:325). Because the target remains a Qwen3-family HF snapshot, retaining them is the minimal intervention. They should only change if the target model’s tokenizer/config is incompatible with those vLLM parsers.

The analyzer’s local preset reads `LOCAL_ANALYZER_MODEL_ID` dynamically at request resolution:

[`tool_agent.py:481-499`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/agent/tool_agent.py:481)

---

## 5. Every `Qwen3.6` / `vrfai` occurrence in the local bundle

Text occurrences:

- [`setup_commands.json:2`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/setup_commands.json:2)
  - old dataset slug
  - `SERVED_MODEL_NAME = 'vrfai/Qwen3.6-27B-FP8'`
- [`configs/inference.json:3`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/configs/inference.json:3)
  - `"model_name": "vrfai/Qwen3.6-27B-FP8"`
- [`configs/inference.openrouter.json:3`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/configs/inference.openrouter.json:3)
  - `"model_name": "Qwen/Qwen3.6-27B"`
- [`kaggle.py:11`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/kaggle.py:11)
  - default dataset source
- [`kaggle.py:12`](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/duck/bundle/src/ARC3-Inference/inference/framework/kaggle.py:12)
  - default served name

Binary pickle occurrences, which have byte offsets rather than source lines:

- `benchmark_initial.pkl`, byte 2742: field `kaggle_model_dataset_source`
- `benchmark_initial.pkl`, byte 2772: old dataset ref
- `benchmark_initial.pkl`, byte 2819: field `kaggle_served_model_name`
- `benchmark_initial.pkl`, byte 2846: `vrfai/Qwen3.6-27B-FP8`

The bundled config defaults and pickle values are inert for this kernel launch because `setup_commands.json` has already been rendered. The active runtime occurrences are the command string and notebook attachment/mount mapping.