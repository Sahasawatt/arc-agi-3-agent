"""Build duckv19/taaf-duck-v19.ipynb — v10 plus ONE change: the banking graft.

v19 = v10 (anim bundle + Qwen3.8-27B-FP8, output UNCAPPED, upscale left at the
bundle default of 4 — v18 measured 8 as WORSE, 3.60 vs band [4.55, 4.71]) with
cell 12 replaced by duckv19/cell12_banking.py, which arms exactly one flag of the
community graft stack: banking.

Why banking and not one of the other seventeen modules: it is the only candidate
that changes the SCORING MECHANISM rather than tuning a heuristic, and all four
engine facts it rests on were read out of the actual installed packages
(arc_agi 0.9.8 / arcengine 0.9.3 from PyPI, symbol-matched against the ones the
harness imports) rather than taken from the fork's word. Details: notes/R23-banking.md.

Compatibility with the anim bundle was verified before any of this was built —
11/11 imported symbols present, _HarnessGameSession a superset (27 methods vs the
fork base's 24), 0 signature mismatches on the four overridden methods. R21.

Run:  python duckv19/build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_NB = REPO / "duckmod" / "taaf-duck-mod.ipynb"
OUT_NB = REPO / "duckv19" / "taaf-duck-v19.ipynb"
CELL12_SRC = REPO / "duckv19" / "cell12_banking.py"

OLD_SHARE = "jeroencottaar/taaf-kaggle-source-share"
NEW_SHARE = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
OLD_DS = "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot"
NEW_DS = "jakobbrggen/qwen3-8-27b-fp8-hf-snapshot"
GRAFT_DS = "sahasawatt/taaf-grafts-banking"

OLD_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""

# Byte-identical to v10's rewrite: model swap only. No output cap, no KV flag,
# no upscale change.
NEW_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    # duckv19: v10's model swap (R12 seam) and nothing else at this layer - the
    # one change lives in cell 12. NO output cap: v9 proved a 768-token ceiling
    # truncates the tool call that carries the action itself.
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
    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot" not in command, "duckv19: model slug rewrite missed"
    assert "Qwen3.6-27B-FP8" not in command, "duckv19: served-name rewrite missed"
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '0'" in command, "duckv19: output must stay UNCAPPED"
    assert "'MULTIMODAL_UPSCALE': '4'" in command, "duckv19: upscale must stay at 4 - v18 measured 8 worse"
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""


def main() -> None:
    cell12 = CELL12_SRC.read_text(encoding="utf-8")
    assert 'composite.install(bm, {"banking": True})' in cell12, "cell12: the install call is missing"
    assert "installed=" in cell12, (
        "cell12: composite.install() never raises, so a did-it-take print is the only "
        "way a silent stock fallback becomes visible in the commit log (R8)"
    )
    for flag in ("transfer", "recovery", "goalkeep", "efficiency", "shortcircuit"):
        assert f'"{flag}": True' not in cell12, f"cell12: {flag} must stay OFF - one change per run (R9)"

    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))

    c6 = "".join(nb["cells"][6]["source"])
    assert OLD_DS in c6 and OLD_SHARE in c6, "cell 6: expected dataset refs not found"
    c6 = c6.replace(OLD_SHARE, NEW_SHARE).replace(OLD_DS, NEW_DS)
    # Attach the graft dataset. It deliberately carries NO taaf-kaggle-bundle.json,
    # so _find_bundle_dir()'s rglob cannot mistake it for the source bundle.
    old_list = f'DATASET_SOURCES = ["{NEW_SHARE}", "driessmit1/arc3-vllm-h100-wheelhouse-v3", "{NEW_DS}"]'
    assert old_list in c6, "cell 6: DATASET_SOURCES line not in the expected shape"
    c6 = c6.replace(
        old_list,
        f'DATASET_SOURCES = ["{NEW_SHARE}", "driessmit1/arc3-vllm-h100-wheelhouse-v3", '
        f'"{NEW_DS}", "{GRAFT_DS}"]',
    )
    nb["cells"][6]["source"] = c6

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

    # Ask the parser, not only the text (duckv14 version 1 died on Kaggle with an
    # IndentationError after passing every content assert).
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
    o12 = "".join(out["cells"][12]["source"])
    assert NEW_SHARE in o6 and NEW_DS in o6 and OLD_SHARE not in o6 and OLD_DS not in o6
    assert GRAFT_DS in o6, "cell 6: the graft dataset is not attached"
    assert o6.count(GRAFT_DS) == 1, "cell 6: graft dataset attached more than once"
    assert "Qwen3.8-27B-FP8" in o8
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '768'" not in o8, "v19 must not cap output"
    assert "'fp8'" not in o8, "v19 must not carry v14's KV flag"
    assert "'MULTIMODAL_UPSCALE': '8'" not in o8, "v19 must not carry v18's upscale change"
    assert o12 == cell12, "cell 12 does not match duckv19/cell12_banking.py byte for byte"

    print("self-check OK: cells [6, 8, 12]; anim bundle + 3.8, no cap, upscale 4, banking armed")
    print(f"cell 12 == {CELL12_SRC.name} verbatim ({len(cell12)} chars)")


if __name__ == "__main__":
    main()
