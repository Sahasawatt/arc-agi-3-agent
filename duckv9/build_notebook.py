"""Build duckv9/taaf-duck-v9.ipynb — the REBASE candidate (R13 recommendation):

- Source bundle -> Tufa's animation-awareness branch (public dataset
  jakobbrggen/taaf-kaggle-source-anim-20260807-anim; duck-v12 lineage, LB-proven
  by FOYSAL's LB-9). Found at runtime by the bundle marker, same as the old share.
- Model -> Qwen3.8-27B-FP8 (dataset jakobbrggen/qwen3-8-27b-fp8-hf-snapshot),
  via the same setup-command rewrite seam as duckv8 (R12; anim's setup_commands.json
  is byte-identical to the old bundle's).
- Output cap -> LOCAL_ANALYZER_MAX_OUTPUT '0' -> '768' in the same rewrite (R10's
  top throughput lever; upstream still ships uncapped).
- duckmod's cell-12 source patches are DROPPED (zero measured adoption, and their
  patch points target the old source tree).

Run:  python duckv9/build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_NB = REPO / "duckmod" / "taaf-duck-mod.ipynb"
OUT_NB = REPO / "duckv9" / "taaf-duck-v9.ipynb"

OLD_SHARE = "jeroencottaar/taaf-kaggle-source-share"
NEW_SHARE = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
OLD_DS = "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot"
NEW_DS = "jakobbrggen/qwen3-8-27b-fp8-hf-snapshot"

OLD_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""

NEW_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    # duckv9: Qwen3.8 swap + output cap, rewritten into the bundle's baked command
    # (R12 trace; anim bundle's setup_commands.json is byte-identical to the old one).
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
        .replace(
            "'LOCAL_ANALYZER_MAX_OUTPUT': '0'",
            "'LOCAL_ANALYZER_MAX_OUTPUT': '768'",
        )
    )
    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot" not in command, "duckv9: model slug rewrite missed"
    assert "Qwen3.6-27B-FP8" not in command, "duckv9: served-name rewrite missed"
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '0'" not in command, "duckv9: output-cap rewrite missed"
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""

NEUTERED_CELL12 = (
    "# duckv9: no source patches. The anim bundle (duck-v12 lineage) ships its own\n"
    "# no-op guard + animation awareness; duckmod's old patches targeted the June-30\n"
    "# source tree and measured zero adoption (results/wayfinder/R8).\n"
    "print(\"duckv9: stock anim bundle + Qwen3.8 + max_output=768 via setup rewrite\")\n"
)


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))

    c6 = "".join(nb["cells"][6]["source"])
    assert OLD_SHARE in c6 and OLD_DS in c6, "cell 6: expected dataset refs not found"
    nb["cells"][6]["source"] = c6.replace(OLD_SHARE, NEW_SHARE).replace(OLD_DS, NEW_DS)

    c8 = "".join(nb["cells"][8]["source"])
    assert OLD_LOOP in c8, "cell 8: expected setup loop not found"
    nb["cells"][8]["source"] = c8.replace(OLD_LOOP, NEW_LOOP)

    c12 = "".join(nb["cells"][12]["source"])
    assert "duckmod" in c12 or "hud_mask" in c12 or len(c12) > 2000, "cell 12: not the patch cell?"
    nb["cells"][12]["source"] = NEUTERED_CELL12

    OUT_NB.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"wrote {OUT_NB} ({OUT_NB.stat().st_size} bytes)")

    src = json.loads(SRC_NB.read_text(encoding="utf-8"))
    out = json.loads(OUT_NB.read_text(encoding="utf-8"))
    diff = [i for i in range(len(src["cells"])) if src["cells"][i]["source"] != out["cells"][i]["source"]]
    assert diff == [6, 8, 12], f"unexpected diff cells: {diff}"
    o6 = "".join(out["cells"][6]["source"])
    o8 = "".join(out["cells"][8]["source"])
    assert NEW_SHARE in o6 and NEW_DS in o6 and OLD_SHARE not in o6 and OLD_DS not in o6
    assert "768" in o8 and "Qwen3.8-27B-FP8" in o8
    print("self-check OK: cells [6, 8, 12] differ; anim bundle + 3.8 + cap in place")


if __name__ == "__main__":
    main()
