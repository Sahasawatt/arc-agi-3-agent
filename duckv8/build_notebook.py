"""Build duckv8/taaf-duck-v8.ipynb: duckmod's notebook with ONLY the model swapped
to Qwen3.8-27B-FP8 (dataset jakobbrggen/qwen3-8-27b-fp8-hf-snapshot).

Mechanism per results/wayfinder/R12-model-swap-trace.md: the vLLM launch command is a
string in the bundle's setup_commands.json (read-only at kernel runtime), so cell 8's
loop rewrites the command text before running it; cell 6 swaps the attached dataset.
Everything else (duckmod's cell 12 patches included) is byte-identical to duckmod.

Run:  python duckv8/build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_NB = REPO / "duckmod" / "taaf-duck-mod.ipynb"
OUT_NB = REPO / "duckv8" / "taaf-duck-v8.ipynb"

OLD_DS = "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot"
NEW_DS = "jakobbrggen/qwen3-8-27b-fp8-hf-snapshot"

OLD_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""

NEW_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    # duckv8: swap the vLLM model to Qwen3.8-27B-FP8 (R12 trace). The launch command
    # is baked into the read-only bundle, so rewrite it here before it runs.
    command = (
        command
        .replace("MODEL_OWNER = 'driessmit1'", "MODEL_OWNER = 'jakobbrggen'")
        .replace(
            "MODEL_SLUG = 'vrfai-qwen3-6-27b-fp8-hf-snapshot'",
            "MODEL_SLUG = 'qwen3-8-27b-fp8-hf-snapshot'",
        )
        .replace(
            "SERVED_MODEL_NAME = 'vrfai/Qwen3.6-27B-FP8'",
            "SERVED_MODEL_NAME = 'vrfai/Qwen3.8-27B-FP8'",
        )
    )
    # Fail fast if the upstream bundle's command shape drifted and a replace missed.
    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot" not in command, "duckv8: model slug rewrite missed"
    assert "Qwen3.6-27B-FP8" not in command, "duckv8: served-name rewrite missed"
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))

    c6 = "".join(nb["cells"][6]["source"])
    assert OLD_DS in c6, "cell 6: expected dataset ref not found"
    nb["cells"][6]["source"] = c6.replace(OLD_DS, NEW_DS)

    c8 = "".join(nb["cells"][8]["source"])
    assert OLD_LOOP in c8, "cell 8: expected setup loop not found"
    assert "duckv8" not in c8, "cell 8: already patched?"
    nb["cells"][8]["source"] = c8.replace(OLD_LOOP, NEW_LOOP)

    OUT_NB.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"wrote {OUT_NB} ({OUT_NB.stat().st_size} bytes)")

    # self-check: exactly cells 6 and 8 differ from duckmod
    src = json.loads(SRC_NB.read_text(encoding="utf-8"))
    out = json.loads(OUT_NB.read_text(encoding="utf-8"))
    diff = [i for i in range(len(src["cells"])) if src["cells"][i]["source"] != out["cells"][i]["source"]]
    assert diff == [6, 8], f"unexpected diff cells: {diff}"
    o6 = "".join(out["cells"][6]["source"])
    o8 = "".join(out["cells"][8]["source"])
    assert NEW_DS in o6 and OLD_DS not in o6
    assert "jakobbrggen" in o8 and "Qwen3.8-27B-FP8" in o8
    print("self-check OK: cells [6, 8] differ, swap strings in place")


if __name__ == "__main__":
    main()
