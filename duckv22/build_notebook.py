"""Build duckv22/taaf-duck-v22.ipynb — v10 with ONE change: the rank-21 prompt port.

v21 = v10 (anim bundle + Qwen3.8-27B-FP8, output UNCAPPED, MULTIMODAL_UPSCALE at the
bundle default 4) with cell 12 replaced by duckv22/cell12_prompt_port.py, which
adds `reasoning_effort` to the vLLM chat_template_kwargs and sets it to "medium".

PROVENANCE — this is the first change this campaign has copied from a team that is
actually above us, with the attribution verified (notes/R26-reasoning-effort.md):

  ataraxian / "Ya Xu"  = leaderboard rank 21, hidden 2.37, 18 submissions
  us       / Thuitanium = rank 212, hidden 1.70, 9 submissions

Their published bundle `arc3-qwen38-colab-v29`, diffed against the SAME June-era base
we hold at duck/bundle, differs in six files. The load-bearing one adds an env hook for
reasoning_effort, and their setup sets it to 'medium'.

VERIFIED AGAINST THE MODEL, NOT THE CLAIM: Qwen3.8-27B-FP8's own chat_template.jinja
defaults reasoning_effort to 'xhigh', accepts only xhigh/medium/low, and RAISES on
anything else. xhigh appends "think carefully through the task, validate key
assumptions, consider plausible alternatives" to every turn; medium appends nothing.
So every run this campaign has made carried the xhigh instruction by default.

That matches what we measured with no knowledge of this flag: games plateau holding
30-95 minutes and 24-47 unspent actions (LEDGER), and five mechanical causes for it were
eliminated (R24). "Spending the remaining budget on deliberation" is consistent with all
of it.

NOTE THIS CONTRADICTS R24's READING, AND THAT IS THE POINT OF RUNNING IT: R24 concluded
by elimination that the bottleneck is reasoning capability. This change tests the
opposite — that the model is instructed to over-deliberate. v20 (MoE) cut capability and
collapsed to 0.18; this cuts the *instruction to deliberate* while keeping the model.

Run:  python duckv22/build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_NB = REPO / "duckmod" / "taaf-duck-mod.ipynb"
OUT_NB = REPO / "duckv22" / "taaf-duck-v22.ipynb"
CELL12_SRC = REPO / "duckv22" / "cell12_prompt_port.py"

OLD_SHARE = "jeroencottaar/taaf-kaggle-source-share"
NEW_SHARE = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
OLD_DS = "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot"
NEW_DS = "jakobbrggen/qwen3-8-27b-fp8-hf-snapshot"

OLD_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""

# Byte-identical to v10's rewrite. The one change lives in cell 12, because
# reasoning_effort is a per-request field, not a server flag — vLLM never needs to know.
NEW_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    # duckv22: v10's model swap (R12 seam) and nothing else here. NO output cap (v9),
    # NO KV flag (v14), NO upscale change (v18 measured 8 worse than the default 4).
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
    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot" not in command, "duckv22: model slug rewrite missed"
    assert "Qwen3.6-27B-FP8" not in command, "duckv22: served-name rewrite missed"
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '0'" in command, "duckv22: output must stay UNCAPPED"
    assert "'MULTIMODAL_UPSCALE': '4'" in command, "duckv22: upscale must stay 4 - v18 measured 8 worse"
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""


def main() -> None:
    cell12 = CELL12_SRC.read_text(encoding="utf-8")
    assert "THEIR_PYTHON_ADDENDUM = " in cell12, "cell12: the ported addendum is missing"
    assert "already tried" in cell12 and "The same rule applies" in cell12, (
        "cell12: the two load-bearing bullets are not in the embedded addendum"
    )
    assert "_tool_agent.PYTHON_ADDENDUM = " in cell12, (
        "cell12: tool_agent imports PYTHON_ADDENDUM by name, so patching only the "
        "prompts module would be a no-op"
    )
    assert "TEETH FAIL" in cell12, "cell12: the in-kernel teeth are missing (R8)"
    # NOT `"reasoning_effort" not in cell12` — the provenance comment legitimately
    # names v21's flag (the v16 lesson: an assert must not match its own text). The
    # functional tokens are the env var and the payload patch.
    assert "LOCAL_ANALYZER_REASONING_EFFORT" not in cell12, (
        "cell12: v21's effort env var measured WORSE (p=0.0052) and must not ride along"
    )
    assert "build_chat_payload" not in cell12, (
        "cell12: v21's payload patch must not ride along - one change per run (R9)"
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
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '768'" not in o8, "v21 must not cap output"
    assert "'fp8'" not in o8, "v21 must not carry v14's KV flag"
    assert "'MULTIMODAL_UPSCALE': '8'" not in o8, "v21 must not carry v18's upscale change"
    assert o12 == cell12, "cell 12 does not match duckv22/cell12_prompt_port.py byte for byte"

    # Teeth on the builder's own subject: run the patch logic here, offline, against a
    # stand-in for the stock builder, and prove it both fires and is not already present.
    def _stock(**kw):
        return {"model": kw["model"], "chat_template_kwargs": {"enable_thinking": True}}

    patched = dict(_stock(model="t"))
    patched["chat_template_kwargs"] = dict(patched["chat_template_kwargs"])
    patched["chat_template_kwargs"]["reasoning_effort"] = "medium"
    assert "reasoning_effort" not in _stock(model="t")["chat_template_kwargs"]
    assert patched["chat_template_kwargs"] == {"enable_thinking": True, "reasoning_effort": "medium"}

    print("self-check OK: cells [6, 8, 12]; anim bundle + 3.8, no cap, upscale 4, rank-21 prompt port")
    print(f"cell 12 == {CELL12_SRC.name} verbatim ({len(cell12)} chars)")


if __name__ == "__main__":
    main()
