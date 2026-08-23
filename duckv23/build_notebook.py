"""Build duckv23/taaf-duck-v23.ipynb — v10 + upscale 8 + grid lines on the board PNG.

WHY (notes/R29-grid-lines.md): the post-anim TAAF bundle ships a grid-line renderer
whose gate reads MULTIMODAL_GRID_LINES == "1" while the author's own setup says
'true' — the feature has never run anywhere. Our anim bundle predates it entirely.
R28 measured that 4/5 stuck levels hold a WRONG goal model, and at least 3 of the 5
wrong goals pivot on a SPATIAL misread (cd82's stamp-overlap arithmetic, lp85's
single-ring model, re86's shape confusion). A 1px cell lattice is coordinate
scaffolding at the perception layer — not prompt pressure (the lane B28 closed).

ATTRIBUTION: two deltas vs v10 (upscale 8, lines) — but v18 already measured
upscale 8 WITHOUT lines: 3.60, p=0.508, NOT-DISTINGUISHABLE from v10cal. So v18 is
the no-lines control arm and any out-of-band v23 result attributes to the lines.
8 is also the author's intended pairing, and gives 7x7px cells + 1px line.

Cells changed vs duckmod base: 6 (share+model datasets), 8 (v10 rewrite + v18's
upscale flip), 12 (duckv23/cell12_grid_lines.py — replaces v10's stub, same as
every build since v10 dropped duckmod's June-era patches).

Run:  python duckv23/build_notebook.py
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_NB = REPO / "duckmod" / "taaf-duck-mod.ipynb"
OUT_NB = REPO / "duckv23" / "taaf-duck-v23.ipynb"
CELL12_SRC = REPO / "duckv23" / "cell12_grid_lines.py"

OLD_SHARE = "jeroencottaar/taaf-kaggle-source-share"
NEW_SHARE = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
OLD_DS = "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot"
NEW_DS = "jakobbrggen/qwen3-8-27b-fp8-hf-snapshot"

OLD_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""

# v10's rewrite + v18's upscale flip, byte-for-byte the tested forms.
NEW_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    # duckv23: v10's model swap (R12 seam) + v18's upscale flip. The grid-line
    # renderer itself is ported in cell 12 (the anim bundle lacks the feature).
    # NO output cap (v9), NO KV flag (v14).
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
    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot" not in command, "duckv23: model slug rewrite missed"
    assert "Qwen3.6-27B-FP8" not in command, "duckv23: served-name rewrite missed"
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '0'" in command, "duckv23: output must stay UNCAPPED"
    assert "'MULTIMODAL_CONTEXT': 'current_grid'" in command, "duckv23: vision channel vanished"
    assert "'MULTIMODAL_UPSCALE': '8'" in command, "duckv23: upscale rewrite missed"
    assert "'MULTIMODAL_UPSCALE': '4'" not in command, "duckv23: old upscale survived"
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""


def offline_teeth(cell12: str) -> None:
    """Run cell 12's own in-kernel teeth here, against stubbed bundle modules.

    The stubs mirror the two facts the patch depends on (verified in the anim
    source): vision_context exposes ARC_COLOR_MAP / current_grid_image_upscale /
    frame_to_png_data_url, and tool_agent does NOT bind frame_to_png_data_url.
    """
    import base64
    import io

    from PIL import Image

    vc = types.ModuleType("inference.agent.vision_context")
    vc.ARC_COLOR_MAP = {0: (0, 0, 0), 1: (30, 60, 90), 2: (200, 50, 50), 3: (50, 200, 50), 4: (50, 50, 200)}
    vc.current_grid_image_upscale = lambda: 8

    def stock_frame_to_png_data_url(frame, *, upscale=None):
        rows = len(frame.grid)
        cols = max(len(r) for r in frame.grid)
        scale = 8 if upscale is None else int(upscale)
        img = Image.new("RGB", (cols, rows))
        px = img.load()
        for y, row in enumerate(frame.grid):
            for x in range(cols):
                px[x, y] = vc.ARC_COLOR_MAP.get(int(row[x]), (0, 0, 0))
        img = img.resize((cols * scale, rows * scale), Image.Resampling.NEAREST)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    vc.frame_to_png_data_url = stock_frame_to_png_data_url
    ta = types.ModuleType("inference.agent.tool_agent")
    assert not hasattr(ta, "frame_to_png_data_url")

    agent_pkg = types.ModuleType("inference.agent")
    agent_pkg.vision_context = vc
    agent_pkg.tool_agent = ta
    inference_pkg = types.ModuleType("inference")
    inference_pkg.agent = agent_pkg
    mods = {
        "inference": inference_pkg,
        "inference.agent": agent_pkg,
        "inference.agent.vision_context": vc,
        "inference.agent.tool_agent": ta,
    }
    saved = {k: sys.modules.get(k) for k in mods}
    sys.modules.update(mods)
    try:
        exec(compile(cell12, str(CELL12_SRC), "exec"), {"__name__": "__duckv23_cell12__"})
        # the patch must have landed on the stub module
        assert vc.frame_to_png_data_url is not stock_frame_to_png_data_url, (
            "offline teeth: patch did not replace frame_to_png_data_url"
        )
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


def main() -> None:
    cell12 = CELL12_SRC.read_text(encoding="utf-8")
    assert "_vc.frame_to_png_data_url = _grid_lined_frame_to_png_data_url" in cell12, (
        "cell12: the module-attribute patch line is missing"
    )
    assert "TEETH FAIL" in cell12, "cell12: the in-kernel teeth are missing (R8)"
    assert 'hasattr(_ta, "frame_to_png_data_url")' in cell12, (
        "cell12: missing the seam guard against a tool_agent direct binding"
    )

    offline_teeth(cell12)
    print("offline teeth OK: cell 12's own _teeth() passed against stubbed modules")

    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))

    c6 = "".join(nb["cells"][6]["source"])
    assert OLD_DS in c6 and OLD_SHARE in c6, "cell 6: expected dataset refs not found"
    nb["cells"][6]["source"] = c6.replace(OLD_SHARE, NEW_SHARE).replace(OLD_DS, NEW_DS)

    c8 = "".join(nb["cells"][8]["source"])
    assert OLD_LOOP in c8, "cell 8: expected setup loop not found"
    nb["cells"][8]["source"] = c8.replace(OLD_LOOP, NEW_LOOP)

    nb["cells"][12]["source"] = cell12

    OUT_NB.parent.mkdir(parents=True, exist_ok=True)
    OUT_NB.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"wrote {OUT_NB} ({OUT_NB.stat().st_size} bytes)")

    # --- self-check ---
    src = json.loads(SRC_NB.read_text(encoding="utf-8"))
    out = json.loads(OUT_NB.read_text(encoding="utf-8"))
    diff = [i for i in range(len(src["cells"])) if src["cells"][i]["source"] != out["cells"][i]["source"]]
    assert diff == [6, 8, 12], f"unexpected diff cells: {diff}"

    for idx in diff:
        cell_src = "".join(out["cells"][idx]["source"])
        try:
            compile(cell_src, f"cell{idx}", "exec")
        except SyntaxError as exc:
            raise AssertionError(
                f"cell {idx} is not valid Python: {exc.msg} at line {exc.lineno} -> {(exc.text or '').rstrip()!r}"
            ) from None
    print(f"syntax OK: cells {diff} compile")

    o6 = "".join(out["cells"][6]["source"])
    o8 = "".join(out["cells"][8]["source"])
    o12 = "".join(out["cells"][12]["source"])
    assert NEW_SHARE in o6 and NEW_DS in o6 and OLD_SHARE not in o6 and OLD_DS not in o6
    assert "Qwen3.8-27B-FP8" in o8
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '768'" not in o8, "v23 must not cap output"
    assert "kv-cache-dtype" not in o8, "v23 must not carry v14's KV flag"
    assert o12 == cell12, "cell 12 does not match duckv23/cell12_grid_lines.py byte for byte"

    print("self-check OK: cells [6, 8, 12]; anim + 3.8, no cap, upscale 8, grid lines armed in cell 12")
    print(f"cell 12 == {CELL12_SRC.name} verbatim ({len(cell12)} chars)")


if __name__ == "__main__":
    main()
