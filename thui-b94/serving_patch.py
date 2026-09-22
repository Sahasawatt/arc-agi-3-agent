"""Text patch for the B94 Qwen3.5 serving smoke."""

from __future__ import annotations


def _replace_once(src: str, old: str, new: str, label: str) -> str:
    count = src.count(old)
    assert count == 1, f"{label}: expected one anchor, found {count}"
    return src.replace(old, new)


def _replace_section(src: str, start: str, end: str, replacement: str, label: str) -> str:
    assert src.count(start) == 1, f"{label}: start anchor count != 1"
    assert src.count(end) == 1, f"{label}: end anchor count != 1"
    before, tail = src.split(start, 1)
    _discarded, after = tail.split(end, 1)
    return before + replacement + end + after


MODEL_CONSTANTS = '''MODEL_HF_REPO = "ippeiogawa/qwen35-122b-a10b-nvfp4"
MODEL_DATASET = "ippeiogawa/qwen35-122b-a10b-nvfp4"
MODEL_CONFIG_SHA256 = "4bbd5a6e8662d412cb6e57efeee5dfd4f8e13dc07e2b43398994f85a58f9993d"
MODEL_QUANT_CONFIG_SHA256 = "0ee08c97b6123d808734e28951385ce0722c61737ac8c14a9f9a9e3889646c83"
MODEL_WEIGHT_SHARD_COUNT = 9
MODEL_WEIGHT_BYTES = 83_495_005_008

'''


SOURCE_IDENTITY = '''def source_identity() -> dict[str, Any]:
    path = BUNDLE_DIR / "SOURCE_IDENTITY.json"
    value = read_json(path)
    if not isinstance(value, dict):
        raise RuntimeError(f"Invalid source identity: {path}")
    expected_setup = str(value.get("serving_setup_sha256", ""))
    actual_setup = sha256_file(Path(__file__).resolve())
    if not expected_setup or expected_setup != actual_setup:
        raise RuntimeError(
            f"Serving setup identity mismatch: {actual_setup} != {expected_setup or '<missing>'}"
        )
    if value.get("runtime_manifest_sha256") != VLLM_RUNTIME_MANIFEST_SHA256:
        raise RuntimeError("Source identity has the wrong vLLM runtime manifest hash.")
    runtime = value.get("runtime") or {}
    if runtime.get("image") != VLLM_IMAGE or runtime.get("kaggle_dataset") != RUNTIME_DATASET:
        raise RuntimeError("Source identity has the wrong vLLM runtime.")
    return value


'''


MODEL_FUNCTIONS = '''def resolve_model_dir() -> Path:
    mapped = input_paths().get(MODEL_DATASET)
    candidates = [
        mapped,
        Path("/kaggle/input/qwen35-122b-a10b-nvfp4"),
        Path("/kaggle/input/datasets/ippeiogawa/qwen35-122b-a10b-nvfp4"),
    ]
    matches = []
    for candidate in candidates:
        if candidate is None:
            continue
        if (candidate / "config.json").is_file() and (candidate / "hf_quant_config.json").is_file():
            resolved = candidate.resolve()
            if resolved not in matches:
                matches.append(resolved)
    if len(matches) != 1:
        raise FileNotFoundError(f"Could not resolve one pinned {MODEL_DATASET}; matches={matches}")
    return matches[0]


def verify_model(model_dir: Path, *, full_file_hashes: bool = True) -> dict[str, Any]:
    del full_file_hashes
    config_path = model_dir / "config.json"
    quant_path = model_dir / "hf_quant_config.json"
    if sha256_file(config_path) != MODEL_CONFIG_SHA256:
        raise RuntimeError("Pinned model config hash does not match.")
    if sha256_file(quant_path) != MODEL_QUANT_CONFIG_SHA256:
        raise RuntimeError("Pinned ModelOpt quantization config hash does not match.")
    config = read_json(config_path)
    quant = read_json(quant_path)
    text_config = config.get("text_config") or {}
    quantization = config.get("quantization_config") or {}
    quant_details = quant.get("quantization") or {}
    if config.get("architectures") != ["Qwen3_5MoeForConditionalGeneration"]:
        raise RuntimeError(f"Wrong model architecture: {config.get('architectures')}")
    if config.get("model_type") != "qwen3_5_moe" or text_config.get("model_type") != "qwen3_5_moe_text":
        raise RuntimeError("Wrong Qwen3.5 model type identity.")
    if quantization.get("quant_method") != "modelopt" or quantization.get("quant_algo") != "NVFP4":
        raise RuntimeError(f"Wrong in-model quantization identity: {quantization}")
    if quant_details.get("quant_algo") != "NVFP4" or int(quant_details.get("group_size", -1)) != 16:
        raise RuntimeError(f"Wrong ModelOpt NVFP4 details: {quant_details}")
    if int(text_config.get("mtp_num_hidden_layers", -1)) != 1:
        raise RuntimeError("Wrong candidate MTP identity.")
    required = ("model.safetensors.index.json", "chat_template.jinja")
    for name in required:
        if not (model_dir / name).is_file():
            raise RuntimeError(f"Incomplete checkpoint; missing {name}")
    shards = sorted(model_dir.glob("model-*-of-00009.safetensors"))
    total = sum(path.stat().st_size for path in shards)
    if len(shards) != MODEL_WEIGHT_SHARD_COUNT or total != MODEL_WEIGHT_BYTES:
        raise RuntimeError(
            f"Checkpoint shard identity mismatch: count={len(shards)} bytes={total}"
        )
    result = {
        "dataset": MODEL_DATASET,
        "config_sha256": MODEL_CONFIG_SHA256,
        "quant_config_sha256": MODEL_QUANT_CONFIG_SHA256,
        "weight_shard_count": len(shards),
        "weight_bytes": total,
        "architecture": config["architectures"][0],
        "quant_algo": quantization["quant_algo"],
        "mtp_num_hidden_layers": text_config["mtp_num_hidden_layers"],
        "payload_check_deferred_to_vllm_load": True,
    }
    print("THUI_B94_SERVING ok model=Qwen3.5-122B-A10B-NVFP4", flush=True)
    return result


'''


def patch(src: str) -> str:
    src = _replace_once(
        src,
        "Prepare the pinned Qwen3.8-Flash-Next vLLM server on Kaggle.",
        "Prepare the pinned Qwen3.5-122B-A10B-NVFP4 vLLM server on Kaggle.",
        "module description",
    )
    src = _replace_section(src, 'MODEL_HF_REPO = "RadixArk/', "\nVLLM_IMAGE =", MODEL_CONSTANTS, "model constants")
    src = _replace_once(src, 'SERVED_MODEL_NAME = "Qwen/Qwen3.8-Flash-Next-NVFP4"', 'SERVED_MODEL_NAME = "Qwen/Qwen3.5-122B-A10B-NVFP4"', "served model")
    src = _replace_once(src, 'DEFAULT_MTP_TOKENS = 3', 'DEFAULT_MTP_TOKENS = 0', "MTP default")
    src = _replace_section(src, "def source_identity()", "def resolve_runtime_dir()", SOURCE_IDENTITY, "source identity")
    src = _replace_section(src, "def resolve_model_dir()", "def _apply_whiteouts(", MODEL_FUNCTIONS, "model functions")
    # runtime_environment: targeted edits only -- drop the PLE source requirement, its hash check and the
    # PLE/RadixArk env; keep cache paths, allocator pin, cutlass checks and the vLLM version check unchanged.
    src = _replace_once(
        src,
        '    ple_path = (\n        site\n        / "vllm"\n        / "models"\n        / "qwen3_8_flash_next"\n'
        '        / "nvidia"\n        / "ple_layer.py"\n    )\n',
        "",
        "PLE source path",
    )
    src = _replace_once(src, '        site / "flashinfer" / "__init__.py",\n        ple_path,\n', '        site / "flashinfer" / "__init__.py",\n', "PLE required file")
    src = _replace_once(
        src,
        '    if sha256_file(ple_path) != VLLM_PLE_PATCHED_SHA256:\n'
        '        raise RuntimeError("The patched PLE source hash changed before import.")\n',
        "",
        "PLE source hash",
    )
    src = _replace_once(
        src,
        '            "VLLM_PLE_CPU_OFFLOAD": "1",\n'
        '            "VLLM_PLE_OFFLOAD_READY_TIMEOUT": str(SERVER_READY_TIMEOUT),\n',
        "",
        "PLE offload env",
    )
    src = _replace_once(
        src,
        '            "VLLM_RADIXARK_QWEN38_NVFP4_PLE_FP8": "1",\n'
        '            "VLLM_RADIXARK_QWEN38_NVFP4_CONFIG_SHA256": MODEL_CONFIG_SHA256,\n',
        "",
        "RadixArk runtime env",
    )
    src = _replace_once(src, '            "ple_patch_sha256": VLLM_PLE_PATCHED_SHA256,\n        }\n', "        }\n", "fast-mode PLE hash field")
    # The full deep-preload branch imports the Flash-Next PLE module; B94 runs fast start only.
    src = _replace_once(
        src,
        ") -> tuple[dict[str, str], dict[str, Any]]:\n",
        ") -> tuple[dict[str, str], dict[str, Any]]:\n"
        "    if deep_preload_validation:\n"
        '        raise RuntimeError("thui-b94: deep preload validation imports the Flash-Next PLE module; '
        'run with TAAF_KAGGLE_FAST_START=1")\n',
        "fast-start guard",
    )
    src = _replace_once(src, '        "ple_patch_sha256": sha256_file(ple_path),\n', "", "full-mode PLE hash field (unreachable under the fast-start guard)")
    # gpu_inventory: drop only the host-memory gate that exists for PLE CPU offload.
    src = _replace_once(
        src,
        '    if available < MIN_HOST_AVAILABLE_BYTES:\n'
        '        raise RuntimeError(\n'
        '            f"Host memory is too small for FP8 PLE CPU offload: {available} < {MIN_HOST_AVAILABLE_BYTES}"\n'
        '        )\n',
        "",
        "PLE host-memory gate",
    )
    src = _replace_once(src, '        "--distributed-executor-backend",\n        "mp",', '        "--distributed-executor-backend",\n        "mp",\n        "--trust-remote-code",', "trust remote code")
    src = _replace_once(src, "    ple_patch = patch_ple_layer()", '    ple_patch = {"skipped": True, "reason": "Qwen3.5 has no Flash-Next PLE gate"}', "PLE patch bypass")
    src = _replace_once(src, '        "model_hf_revision": MODEL_HF_REVISION,', '        "model_dataset": MODEL_DATASET,', "provenance model")
    src = _replace_once(src, '        "VLLM_RADIXARK_QWEN38_NVFP4_PLE_FP8": "1",\n        "VLLM_RADIXARK_QWEN38_NVFP4_CONFIG_SHA256": MODEL_CONFIG_SHA256,\n', '', "persisted RadixArk gates")
    src = _replace_section(
        src,
        '    log_text = SERVER_LOG.read_text(encoding="utf-8", errors="replace")\n    ple_log_patterns = {',
        '    value = {\n',
        '',
        "PLE readiness logs",
    )
    src = _replace_once(src, '        "ple_offload_log_matches": ple_log_matches,\n', '', "PLE capture result")
    return src
