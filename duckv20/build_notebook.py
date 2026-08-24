"""Build duckv20/taaf-duck-v20.ipynb — v10 with ONE change: the model becomes a MoE.

v20 = v10 (anim bundle, output UNCAPPED, MULTIMODAL_UPSCALE left at the bundle's 4 —
v18 measured 8 as worse) with the dense Qwen3.8-27B-FP8 swapped for
**Qwen3.6-35B-A3B-FP8**: 256 experts, 8 active per token, ~3B active of 35B total.

WHY THIS IS THE RUN WORTH MAKING (notes/R24-what-actually-stops-us.md):
Five mechanical causes of the plateau were eliminated by measurement — the agent moves
the board (no-op 5.3-5.9%), does not lock in (median longest same-action run 5), believes
it knows the goal (Unknown 6.7%), stops with time and actions left, and clicking does not
correlate with scoring (the top game clicks zero times). What is left is the model's
ability to find the sequence that clears a level. Every strong published result on this
benchmark was measured on Opus 4.6/5 or Gemini 3.1; nobody has shown a harness mechanism
carrying an open-weight 27B into that range (R22). So the remaining lever is the model.

WHY IT WAS BELIEVED IMPOSSIBLE, AND WHY THAT WAS WRONG:
R20 and ticket B22 recorded "no MoE on Kaggle — only GGUF and ollama blobs". That was a
statement about the search, not about Kaggle: it searched the `datasets` registry with the
terms "a3b" / "qwen3-6-35b" / "moe fp8". Two things it missed —
  1. Kaggle has a separate **Models** registry (michaelpoluektov/qwen3-6-35b-a3b-fp8), and
     our kernel-metadata has carried an empty "model_sources": [] all campaign;
  2. the FP8 weights are ALSO in `datasets`, under a term the first sweep did not try:
     `cmechevalier/face-of-agi-qwen36-35b-fp8-weights`.

The dataset mirror is what this build uses, because the bundle's own
`resolve_kaggle_dataset_path` only knows three shapes — the TAAF_KAGGLE_INPUT_PATHS map,
/kaggle/input/<slug>, and /kaggle/input/datasets/<owner>/<slug> — and none of them is the
Models-registry layout (<slug>/<framework>/<variation>/<version>). Using the dataset keeps
the diff to the same three lines v10 already rewrites.

VERIFIED BEFORE BUILDING (nothing here is assumed):
  - config.json from the HF source: architectures = "Qwen3_5MoeForConditionalGeneration",
    model_type = "qwen3_5_moe", num_experts 256 / num_experts_per_tok 8, quant fp8 e4m3,
    max_position_embeddings 262144.
  - vLLM's supported-models table lists BOTH Qwen3_5ForConditionalGeneration (what our
    current run reports) and Qwen3_5MoeForConditionalGeneration, in the multimodal (T + I)
    section — which is the section that matters, since the harness sends a board image.
  - the mirror is byte-identical to the Models-registry copy where comparable
    (config.json 37000 B, chat_template.jinja 7764 B, README.md 64855 B) and complete:
    42 layer shards, 37.5 GB, with model.safetensors.index.json.

KNOWN TRADE, HALF-MEASURED: Qwen3.6 is one generation behind the 3.8 we run, and that exact
swap was worth +37% on this harness (duck-mod 2.41 -> v8out 3.31, old bundle). This run buys
MoE capacity at the price of a generation. No Qwen3.8 MoE mirror exists on either registry.

RISKS A SMOKE MUST CATCH (not asserted away, watched for):
  - vLLM 0.19.0 in this container may not carry the MoE variant -> server never boots.
  - the tool-call / reasoning parsers stay qwen3_coder / qwen3; if the MoE emits a
    different tool-call format, actions stop being parsed and the score goes to ~0 the way
    v9 did. The smoke check is whether action events appear at all.

Run:  python duckv20/build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_NB = REPO / "duckmod" / "taaf-duck-mod.ipynb"
OUT_NB = REPO / "duckv20" / "taaf-duck-v20.ipynb"

OLD_SHARE = "jeroencottaar/taaf-kaggle-source-share"
NEW_SHARE = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
OLD_DS = "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot"
MOE_DS = "cmechevalier/face-of-agi-qwen36-35b-fp8-weights"
MOE_OWNER = "cmechevalier"
MOE_SLUG = "face-of-agi-qwen36-35b-fp8-weights"
MOE_SERVED = "Qwen/Qwen3.6-35B-A3B-FP8"

OLD_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""

NEW_LOOP = f"""for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    # duckv20: same three-line seam v10 uses (R12), pointed at a MoE instead of a dense
    # model. NO output cap (v9: a 768-token ceiling truncates the tool call that carries
    # the action). NO upscale change (v18 measured 8 worse than the bundle default 4).
    command = (
        command
        .replace("MODEL_OWNER = 'driessmit1'", "MODEL_OWNER = '{MOE_OWNER}'")
        .replace(
            "MODEL_SLUG = 'vrfai-qwen3-6-27b-fp8-hf-snapshot'",
            "MODEL_SLUG = '{MOE_SLUG}'",
        )
        .replace(
            "SERVED_MODEL_NAME = 'vrfai/Qwen3.6-27B-FP8'",
            "SERVED_MODEL_NAME = '{MOE_SERVED}'",
        )
    )
    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot" not in command, "duckv20: model slug rewrite missed"
    assert "Qwen3.6-27B-FP8" not in command, "duckv20: served-name rewrite missed"
    assert "{MOE_SLUG}" in command, "duckv20: MoE slug did not land - THE change"
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '0'" in command, "duckv20: output must stay UNCAPPED"
    assert "'MULTIMODAL_UPSCALE': '4'" in command, "duckv20: upscale must stay 4 - v18 measured 8 worse"
    print(f"taaf.kaggle: setup command: {{command}}", flush=True)"""

CELL12 = (
    "# duckv20: stock anim bundle, no grafts. The ONE change vs v10 is the model:\n"
    "# Qwen3.8-27B-FP8 (dense) -> Qwen3.6-35B-A3B-FP8 (MoE, 256 experts / 8 active).\n"
    "# Rationale + what was verified first: duckv20/build_notebook.py docstring,\n"
    "# notes/R24-what-actually-stops-us.md.\n"
    'print("duckv20: anim bundle + Qwen3.6-35B-A3B-FP8 (MoE), output UNCAPPED, upscale 4")\n'
)


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))

    c6 = "".join(nb["cells"][6]["source"])
    assert OLD_DS in c6 and OLD_SHARE in c6, "cell 6: expected dataset refs not found"
    nb["cells"][6]["source"] = c6.replace(OLD_SHARE, NEW_SHARE).replace(OLD_DS, MOE_DS)

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

    # Ask the parser, not only the text (duckv14 v1 died on Kaggle with an IndentationError
    # after passing every content assert).
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
    assert NEW_SHARE in o6 and MOE_DS in o6, "cell 6: MoE dataset not attached"
    assert OLD_DS not in o6 and OLD_SHARE not in o6, "cell 6: an old ref survived"
    assert o6.count(MOE_DS) == 1, "cell 6: MoE dataset attached more than once"
    assert MOE_SERVED in o8 and MOE_SLUG in o8, "cell 8: MoE rewrite missing"
    assert "Qwen3.8-27B-FP8" not in o8, "v20 must not still serve the dense 3.8"
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '768'" not in o8, "v20 must not cap output"
    assert "'fp8'" not in o8, "v20 must not carry v14's KV flag"
    assert "'MULTIMODAL_UPSCALE': '8'" not in o8, "v20 must not carry v18's upscale change"

    # A "teeth" block used to sit here — same defect as duckv18's, removed the same day
    # (2026-08-24). It built a local `bundle` string already containing the three literals the
    # chain searches for, ran the chain over it, and asserted the replacements landed. The
    # fixture was hand-written to match the search strings, so it could not fail, while its
    # comment claimed it ran "over the bundle's own model block". The property IS guarded,
    # twice, and neither guard is here:
    #   - build time, line ~114: `assert OLD_LOOP in c8` — the REAL source notebook must still
    #     carry the seam, or this script dies before writing anything.
    #   - run time, on Kaggle, inside NEW_LOOP (lines ~90-91): the `not in command` asserts run
    #     against the bundle's own setup string and kill the kernel if a rewrite missed.
    # The `o8` asserts above are source-text checks only. Do not re-add a fixture.

    print("self-check OK: cells [6, 8, 12]; anim bundle + Qwen3.6-35B-A3B-FP8 MoE, no cap, upscale 4")


if __name__ == "__main__":
    main()
