"""Static contract tests for the B94 serving patch."""

from pathlib import Path

from serving_patch import patch

SOURCE = Path("/Users/yocyber-code/Claude/arc-artifacts/_src/next-direction-2026-09-22/b94/step1/keith-orig/serving_setup.py")


def assert_candidate_contract(text: str) -> None:
    compile(text, "serving_setup.py", "exec")
    assert 'SERVED_MODEL_NAME = "Qwen/Qwen3.5-122B-A10B-NVFP4"' in text
    assert '["Qwen3_5MoeForConditionalGeneration"]' in text
    assert 'config.get("model_type") != "qwen3_5_moe"' in text
    assert "ANALYZER_CONTEXT = 32_768" in text
    assert 'if resolved_tuning["kv_cache_dtype"] != "auto":' in text
    assert '["--kv-cache-dtype", str(resolved_tuning["kv_cache_dtype"])]' in text
    assert 'VLLM_VERSION = "0.1.dev20073+g8e685d198"' in text
    assert 'if import_info.get("vllm") != VLLM_VERSION:' in text
    assert "patch_ple_layer()\n    env" not in text
    assert '"VLLM_PLE_CPU_OFFLOAD": "1"' not in text
    assert '"VLLM_RADIXARK_QWEN38_NVFP4_PLE_FP8": "1"' not in text
    main_body = text.split("def main() -> None:", 1)[1].split("def _setup_timeout_handler", 1)[0]
    for forbidden in (
        "7b719225242aacd3dbd3f9407468c2ee9a9d2594",
        "135_253_622_894",
        "MODEL_FILE_COUNT = 419",
        "PleOffloadLayer",
        "VLLM_PLE_CPU_OFFLOAD",
    ):
        assert forbidden not in main_body


def main() -> None:
    original = SOURCE.read_text()
    patched = patch(original)
    assert_candidate_contract(patched)
    failed_without_patch = False
    try:
        assert_candidate_contract(original)
    except AssertionError:
        failed_without_patch = True
    assert failed_without_patch, "teeth failed: unpatched serving setup passed"
    print("test_serving_patch: ok; compile, candidate identity, disabled Flash-Next path, preserved B81 profile, teeth")


if __name__ == "__main__":
    main()
