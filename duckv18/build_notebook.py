"""Build duckv18/taaf-duck-v18.ipynb — v10 plus ONE change: MULTIMODAL_UPSCALE 4 -> 8.

v18 = v10 (anim bundle + Qwen3.8-27B-FP8, output UNCAPPED) with the grid image the
harness already sends rendered at 8x instead of 4x.

Why this is the change worth a slot. The anim bundle has been sending a PNG of the
current grid in every user message all campaign -- `_build_user_message` (tool_agent.py
:1377) calls `current_grid_image_part` and puts it in `content` -- at
`MULTIMODAL_UPSCALE=4`. Measured on a real dc22 frame (frames/dc22/000.png, a 64x64
grid): 4x renders 256x256px, which a Qwen-VL patcher reads as ~64 tokens for 4096
cells, i.e. ONE token per 8x8 block of cells. At 8x it is 512x512 -> ~256 tokens, one
per 4x4. Cost is ~+192 tokens per user message, ~+24% on v10cal's 2.03 Mtok.

Upstream reached the same knob independently: jakobbrggen/taaf-kaggle-source (branch
feature/explore-experiment, 6d8e3dd, 2026-08-22) ships '8' as its default.

NOT stacked with anything else. R9: one run barely ranks two designs, so the upscale
and the newer bundle's solver changes cannot share a run and still be told apart.

Grid lines are deliberately NOT attempted here: `grep -c GRID_LINE` on the anim
bundle's vision_context.py is 0, so MULTIMODAL_GRID_LINES has no reader in this tree
and setting it would be an inert flag, not a second variable.

Run:  python duckv18/build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_NB = REPO / "duckmod" / "taaf-duck-mod.ipynb"
OUT_NB = REPO / "duckv18" / "taaf-duck-v18.ipynb"

OLD_SHARE = "jeroencottaar/taaf-kaggle-source-share"
NEW_SHARE = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
OLD_DS = "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot"
NEW_DS = "jakobbrggen/qwen3-8-27b-fp8-hf-snapshot"

OLD_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""

NEW_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    # duckv18: v10's model swap (R12 seam) plus ONE new change - the grid image the
    # harness already sends goes from 4x to 8x. NO output cap: v9 proved a 768-token
    # ceiling truncates the tool call that carries the action itself.
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
        .replace("'MULTIMODAL_UPSCALE': '4'", "'MULTIMODAL_UPSCALE': '8'")
    )
    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot" not in command, "duckv18: model slug rewrite missed"
    assert "Qwen3.6-27B-FP8" not in command, "duckv18: served-name rewrite missed"
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '0'" in command, "duckv18: output must stay UNCAPPED"
    assert "'MULTIMODAL_CONTEXT': 'current_grid'" in command, "duckv18: vision channel vanished"
    assert "'MULTIMODAL_UPSCALE': '8'" in command, "duckv18: upscale rewrite missed - THE change"
    assert "'MULTIMODAL_UPSCALE': '4'" not in command, "duckv18: old upscale survived"
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""

CELL12 = (
    "# duckv18: stock anim bundle (ships its own noop_guard + animation awareness);\n"
    "# duckmod's patches are dropped - they target the June-era tree and measured\n"
    "# zero adoption (results/wayfinder/R8). The ONE change vs v10 lives in cell 8.\n"
    'print("duckv18: anim bundle + Qwen3.8, output UNCAPPED, MULTIMODAL_UPSCALE=8")\n'
)


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))

    c6 = "".join(nb["cells"][6]["source"])
    assert OLD_DS in c6 and OLD_SHARE in c6, "cell 6: expected dataset refs not found"
    nb["cells"][6]["source"] = c6.replace(OLD_SHARE, NEW_SHARE).replace(OLD_DS, NEW_DS)

    c8 = "".join(nb["cells"][8]["source"])
    assert OLD_LOOP in c8, "cell 8: expected setup loop not found"
    nb["cells"][8]["source"] = c8.replace(OLD_LOOP, NEW_LOOP)

    nb["cells"][12]["source"] = CELL12

    OUT_NB.parent.mkdir(parents=True, exist_ok=True)
    OUT_NB.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"wrote {OUT_NB} ({OUT_NB.stat().st_size} bytes)")

    # --- self-check ---
    src = json.loads(SRC_NB.read_text(encoding="utf-8"))
    out = json.loads(OUT_NB.read_text(encoding="utf-8"))
    diff = [i for i in range(len(src["cells"])) if src["cells"][i]["source"] != out["cells"][i]["source"]]
    assert diff == [6, 8, 12], f"unexpected diff cells: {diff}"

    # Ask the parser, not only the text. duckv14 version 1 passed every content assert
    # and then died on Kaggle with `IndentationError: unexpected indent`.
    for idx in diff:
        cell_src = "".join(out["cells"][idx]["source"])
        try:
            compile(cell_src, f"cell{idx}", "exec")
        except SyntaxError as exc:
            raise AssertionError(
                f"cell {idx} is not valid Python: {type(exc).__name__}: {exc.msg} "
                f"at line {exc.lineno} -> {(exc.text or '').rstrip()!r}"
            ) from None
    print(f"syntax OK: cells {diff} compile")

    o6 = "".join(out["cells"][6]["source"])
    o8 = "".join(out["cells"][8]["source"])
    assert NEW_SHARE in o6 and NEW_DS in o6 and OLD_SHARE not in o6 and OLD_DS not in o6
    assert "Qwen3.8-27B-FP8" in o8
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '768'" not in o8, "v18 must not cap output"
    assert "'fp8'" not in o8, "v18 must not carry v14's KV flag"
    assert "'MULTIMODAL_UPSCALE': '8'" in o8, "v18: the upscale rewrite is missing"

    # Teeth: the rewrite must actually fire against the REAL setup command, not just
    # appear in the source. Run the same .replace chain over the bundle's own text.
    bundle_env = (
        "    'LOCAL_ANALYZER_ENABLE_THINKING': 'true',\n"
        "    'MULTIMODAL_CONTEXT': 'current_grid',\n"
        "    'MULTIMODAL_UPSCALE': '4',\n"
        "}\n"
    )
    patched = bundle_env.replace("'MULTIMODAL_UPSCALE': '4'", "'MULTIMODAL_UPSCALE': '8'")
    assert "'MULTIMODAL_UPSCALE': '8'" in patched and "': '4'" not in patched, (
        "teeth: the replace does not fire on the bundle's own env block"
    )

    print("self-check OK: cells [6, 8, 12]; anim bundle + 3.8, no cap, upscale 4->8")


if __name__ == "__main__":
    main()
