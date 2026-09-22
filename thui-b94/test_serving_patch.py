"""Static and executable contract tests for the B94 serving patch."""

import ast
import contextlib
import io
import os
import re
import tempfile
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


def execute_linkfix(text: str, env: dict[str, str], library_dirs: list[Path], tmp_root: Path) -> dict[str, str]:
    tree = ast.parse(text)
    runtime = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "runtime_environment"
    )
    ld_index = next(
        index
        for index, node in enumerate(runtime.body)
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Subscript)
        and isinstance(node.targets[0].value, ast.Name)
        and node.targets[0].value.id == "env"
        and node.targets[0].slice.value == "LD_LIBRARY_PATH"
    )
    cache_env_index = next(
        index
        for index, node in enumerate(runtime.body[ld_index + 1 :], ld_index + 1)
        if isinstance(node, ast.For)
        and isinstance(node.target, ast.Tuple)
        and [part.id for part in node.target.elts] == ["key", "path"]
    )
    extracted = ast.FunctionDef(
        name="run_linkfix",
        args=ast.arguments(
            posonlyargs=[],
            args=[ast.arg(arg=name) for name in ("env", "library_dirs", "TMP_ROOT")],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[],
        ),
        body=runtime.body[ld_index + 1 : cache_env_index] + [ast.Return(value=ast.Name(id="env", ctx=ast.Load()))],
        decorator_list=[],
    )
    module = ast.fix_missing_locations(ast.Module(body=[extracted], type_ignores=[]))
    namespace = {"os": os, "re": re, "Path": Path, "RuntimeError": RuntimeError, "print": print}
    exec(compile(module, "linkfix-extract", "exec"), namespace)
    return namespace["run_linkfix"](env, library_dirs, tmp_root)


def assert_linkfix_contract(text: str) -> None:
    with tempfile.TemporaryDirectory() as raw_tmp:
        root = Path(raw_tmp)
        real_lib = root / "cuda" / "lib64"
        real_lib.mkdir(parents=True)
        target = real_lib / "libcudart.so.13"
        target.touch()
        (real_lib / "libcudart.so.12").touch()
        stubs = root / "cuda" / "lib64" / "stubs"
        stubs.mkdir()
        (stubs / "libcudart.so").touch()
        linkfix_dir = root / "thui-b94-linkfix"
        linkfix_dir.mkdir()
        (linkfix_dir / "libcudart.so").symlink_to(root / "stale-libcudart.so.99")
        env = {"LIBRARY_PATH": "/pre-existing/library"}
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = execute_linkfix(text, env, [stubs, real_lib], root)
        link = linkfix_dir / "libcudart.so"
        assert link.is_symlink()
        assert link.resolve() == target.resolve()
        assert result["LIBRARY_PATH"].split(os.pathsep) == [str(linkfix_dir), "/pre-existing/library"]
        assert output.getvalue() == f"THUI_B94_LINKFIX libcudart={target.resolve()}\n"

        missing = root / "missing"
        missing.mkdir()
        try:
            execute_linkfix(text, {}, [stubs, missing], root / "no-candidate")
        except RuntimeError as exc:
            assert str(missing) in str(exc)
            assert str(stubs) not in str(exc)
        else:
            raise AssertionError("missing libcudart candidate did not raise")

        mutated = text.replace(
            '    env["LIBRARY_PATH"] = os.pathsep.join(\n'
            '        [str(linkfix_dir)]\n'
            '        + ([env["LIBRARY_PATH"]] if env.get("LIBRARY_PATH") else [])\n'
            '    )\n',
            '    env["LIBRARY_PATH"] = env.get("LIBRARY_PATH", "")\n',
            1,
        )
        assert mutated != text, "teeth mutation did not find LIBRARY_PATH prepend"
        try:
            assert_linkfix_mutation_fails(mutated, root, stubs, real_lib)
        except AssertionError:
            pass
        else:
            raise AssertionError("teeth failed: skipped LIBRARY_PATH prepend passed")


def assert_linkfix_mutation_fails(text: str, root: Path, stubs: Path, real_lib: Path) -> None:
    env = {"LIBRARY_PATH": "/pre-existing/library"}
    with contextlib.redirect_stdout(io.StringIO()):
        result = execute_linkfix(text, env, [stubs, real_lib], root)
    assert result["LIBRARY_PATH"].split(os.pathsep)[0] == str(root / "thui-b94-linkfix")


def main() -> None:
    original = SOURCE.read_text()
    patched = patch(original)
    assert_candidate_contract(patched)
    assert_linkfix_contract(patched)
    failed_without_patch = False
    try:
        assert_candidate_contract(original)
    except AssertionError:
        failed_without_patch = True
    assert failed_without_patch, "teeth failed: unpatched serving setup passed"
    print("test_serving_patch: ok; compile, candidate identity, linkfix behavior, disabled Flash-Next path, preserved B81 profile, teeth")


if __name__ == "__main__":
    main()
