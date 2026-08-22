"""Build duckv16/taaf-duck-v16.ipynb — v10 plus ONE change: push the diff every turn.

v16 = v10 (anim bundle + Qwen3.8-27B-FP8, output UNCAPPED) with cell 12 carrying the
monkeypatch in duckv16/cell12_push_diff.py. Deliberately NOT stacked on v14: R9 says a
single run already struggles to rank designs, so the KV flag and this change cannot share
a run and still be told apart afterwards.

Evidence, R19's transcript lane: the model reads the board correctly and misreads its own
tool output — before_frame/history indexing confusion 8+ times in sk48, 6+ in cn04, a full
turn each. The harness already pushes a change description unasked, but only for animated
actions (tool_agent.py:1441); this wires the same, delivery-proven channel for ordinary
ones. Design note: notes/v16-push-the-diff.md. Ticket: B17 in notes/wayfinder/MAP.md.

The patch is verified locally against the real bundle source before any quota is spent —
teeth 4/4 green, and RED on three mutations including the index-based `history[-1]` read
that is the very defect it removes.

Run:  python duckv16/build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_NB = REPO / "duckmod" / "taaf-duck-mod.ipynb"
OUT_NB = REPO / "duckv16" / "taaf-duck-v16.ipynb"
CELL12_SRC = REPO / "duckv16" / "cell12_push_diff.py"

OLD_SHARE = "jeroencottaar/taaf-kaggle-source-share"
NEW_SHARE = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
OLD_DS = "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot"
NEW_DS = "jakobbrggen/qwen3-8-27b-fp8-hf-snapshot"

OLD_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""

# Identical to v10's rewrite: model swap only, NO KV flag, NO output cap.
NEW_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    # duckv16: v10's model swap (R12 seam) and nothing else at this layer - the one
    # change lives in cell 12. NO output cap: v9 proved a 768-token ceiling truncates
    # the tool call that carries the action itself.
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
    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot" not in command, "duckv16: model slug rewrite missed"
    assert "Qwen3.6-27B-FP8" not in command, "duckv16: served-name rewrite missed"
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '0'" in command, "duckv16: output must stay UNCAPPED"
    assert "'--kv-cache-dtype'" not in command, "duckv16: KV flag belongs to v14, not here"
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""


def main() -> None:
    cell12 = CELL12_SRC.read_text(encoding="utf-8")
    # The patch must carry its own failure modes into the kernel, not rely on this builder.
    assert "assert tool_agent.ToolAgent._build_user_prompt is" in cell12, (
        "cell12: the did-it-take assertion is missing - a silent no-op would read as "
        "'pushing the diff does not help' (R8: duckmod patches achieved zero adoption)"
    )
    assert "duckv16 teeth" in cell12, "cell12: teeth missing"
    assert "history_entries[-1]" not in cell12, (
        "cell12: uses a positional history read - that IS the defect this patch removes"
    )

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

    # Ask the parser, not only the text. duckv14 version 1 passed every content assert and
    # then died on Kaggle with `IndentationError: unexpected indent`, because OLD_LOOP
    # matches only the first two lines of the setup loop and a column-0 statement appended
    # to the replacement closes that loop early.
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
    assert "Qwen3.8-27B-FP8" in o8
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '768'" not in o8, "v16 must not cap output"
    # NOT `"--kv-cache-dtype" not in o8` — cell 8 legitimately contains that name inside
    # v16's own guard against it, so the naive form asserts against its own text. v14
    # injects the flag as a two-element pair, and `'fp8'` appears nowhere in v16.
    assert "'fp8'" not in o8, "v16 must not carry v14's KV flag"
    assert "KV flag belongs to v14" in o8, "v16: the anti-KV guard went missing from cell 8"
    # cell 12 must be the patch VERBATIM, so what was tested locally is what ships
    assert o12 == cell12, "cell 12 does not match duckv16/cell12_push_diff.py byte for byte"

    print("self-check OK: cells [6, 8, 12]; anim bundle + 3.8, no cap, no KV flag, diff pushed")
    print(f"cell 12 == {CELL12_SRC.name} verbatim ({len(cell12)} chars)")


if __name__ == "__main__":
    main()
