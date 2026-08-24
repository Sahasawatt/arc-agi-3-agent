"""Build duckv25/taaf-duck-v25.ipynb -- v10 plus ONE change: the sampler is PINNED.

`LOCAL_ANALYZER_SEED` is injected into the harness's setup_env. Nothing else differs from
duckv10: same anim bundle, same Qwen3.8-27B-FP8, output UNCAPPED, upscale 4, no KV flag, no
cell-12 patch, temperature LEFT AT 0.6.

WHY (MAP B37, notes/R37-the-cap-decides-most-cells.md)

Every run of this campaign has sampled with no seed at all. `tool_agent.py` defaults are
temperature 0.6 / top_p 0.95 / top_k 20 / seed **-1**, and `openai_compat.build_chat_payload`
ends `if seed is not None and seed >= 0: payload["seed"] = seed` -- so -1 sends no seed and
vLLM picks its own. No builder has ever set it; MAP.md and LEDGER-all-runs.md return zero hits
for `temperature`, `seed` and `sampling`.

That matters because the band `[2.82, 4.71]` -- one build, three runs -- is what makes every
result NOT-DISTINGUISHABLE and what B30 uses to forbid spending a hidden draw. This is a
META-lever: a null result on score is still a win if the SPREAD shrinks, because a narrower
band is what makes every other candidate measurable.

WHY SEED ONLY, TEMPERATURE UNTOUCHED

Greedy decoding (temperature 0) is a DIFFERENT agent, not a quieter one -- v21/B31 measured
that changing how the model deliberates halves levels (28 -> 12, p=0.0052 WORSE). Pinning the
seed changes no reasoning behaviour at all: the same distribution is sampled, from a fixed
starting point. Confounding the two in one build would make the result unreadable. If this arm
is measured and the spread does not move, temperature is the next arm, not the same one.

RIG-VERIFIED before this build (localrig backend, ollama qwen3-8b-10k, 2026-08-25)

The payload is built by the harness's OWN `openai_compat.build_chat_payload`, not a hand-written
one, and the full model output (reasoning + content) is hashed:

  seed = -1   (campaign default, no seed key sent)   3 of 3 responses DISTINCT
  seed = 20260825                                    1 of 3 -- identical all three times
  seed = 99   (control)                              differs from the 20260825 arm

So the field is sent, the backend honours it, and a different seed still gives a different
answer -- the pin is not simply flattening everything.

Two things the rig CANNOT show, and neither is a detail:
  - ollama is not vLLM. This proves the mechanism, never the Kaggle behaviour (see (a) below).
  - ollama ignores `chat_template_kwargs.enable_thinking`, so the first cut of this probe read
    an empty `content` for every arm -- including its controls -- and would have reported
    "seed changes nothing" from a broken instrument. The output had gone to `reasoning`.

WHAT THIS CANNOT DO, stated before the run

  (a) Batched vLLM is not bit-reproducible across differing batch compositions even at a fixed
      seed -- 25 games share one server, and their request interleaving is not controlled here.
  (b) The 7,920s wall cuts each game at a different point regardless of sampling (R37 Q_C), so
      some run-to-run variance survives any sampler setting.
  (c) A single run CANNOT show a variance reduction. The reading needs >= 2 runs of THIS build,
      compared for spread -- `eval/rank_runs.py` ranks a pair, it does not measure a band.
      Treat run 1 as banking a sample, not as a result.

PREDICTIONS, written before the run

  P1  public score lands inside [2.82, 4.71]. That is the EXPECTED outcome, not a failure --
      pinning a seed has no reason to move the mean.
  P2  the kernel log shows `'LOCAL_ANALYZER_SEED': '20260825'` in the setup command echo.
      Absent -> the injection missed and the run measures nothing; read this before any score.
  P3  a SECOND run of this build lands within a narrower gap of the first than the 1.89 the
      unpinned build spans. This is the actual hypothesis and one run cannot test it.

Run:  python duckv25/build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_NB = REPO / "duckmod" / "taaf-duck-mod.ipynb"
OUT_NB = REPO / "duckv25" / "taaf-duck-v25.ipynb"

SEED = "20260825"

OLD_SHARE = "jeroencottaar/taaf-kaggle-source-share"
NEW_SHARE = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
OLD_DS = "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot"
NEW_DS = "jakobbrggen/qwen3-8-27b-fp8-hf-snapshot"

OLD_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""

# v10's model swap byte-for-byte (duckv21/duckv24 carried the same block), plus ONE new
# rewrite: inject LOCAL_ANALYZER_SEED into the harness's setup_env dict.
#
# The dict has no SEED key at all -- `inference/framework/kaggle.py` has zero occurrences of
# the word -- so this ADDS a key rather than changing a value, anchored on the TEMPERATURE
# line that is always rendered immediately after where the seed belongs.
NEW_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    # duckv25: v10's model swap (R12 seam) + the sampler seed, and nothing else. NO output
    # cap (v9), NO KV flag (v14), NO upscale change (v18/v23), temperature UNTOUCHED (B31).
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
            "    'LOCAL_ANALYZER_TEMPERATURE':",
            "    'LOCAL_ANALYZER_SEED': '__SEED__',\\n    'LOCAL_ANALYZER_TEMPERATURE':",
        )
    )
    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot" not in command, "duckv25: model slug rewrite missed"
    assert "Qwen3.6-27B-FP8" not in command, "duckv25: served-name rewrite missed"
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '0'" in command, "duckv25: output must stay UNCAPPED"
    assert "'MULTIMODAL_UPSCALE': '4'" in command, "duckv25: upscale must stay 4 (v10 exact)"
    # TEETH, in-kernel, before the benchmark starts. The seed is the whole build: if the
    # anchor moved in a newer bundle the replace is a silent no-op and the run would score
    # normally while measuring nothing.
    assert "'LOCAL_ANALYZER_SEED': '__SEED__'" in command, (
        "duckv25 TEETH FAIL: seed injection missed -- the setup_env anchor "
        "\\"    'LOCAL_ANALYZER_TEMPERATURE':\\" is not in this bundle's setup command"
    )
    assert "'LOCAL_ANALYZER_TEMPERATURE': '0.6'" in command, (
        "duckv25 TEETH FAIL: temperature is not 0.6 -- this arm must not touch it"
    )
    assert command.count("'LOCAL_ANALYZER_SEED'") == 1, (
        "duckv25 TEETH FAIL: seed key injected more than once"
    )
    print("duckv25: sampler pinned, seed=__SEED__, temperature untouched", flush=True)
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""


def main() -> None:
    new_loop = NEW_LOOP.replace("__SEED__", SEED)
    assert "__SEED__" not in new_loop, "seed placeholder left unrendered"

    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))

    c6 = "".join(nb["cells"][6]["source"])
    assert OLD_DS in c6 and OLD_SHARE in c6, "cell 6: expected dataset refs not found"
    nb["cells"][6]["source"] = c6.replace(OLD_SHARE, NEW_SHARE).replace(OLD_DS, NEW_DS)

    c8 = "".join(nb["cells"][8]["source"])
    assert OLD_LOOP in c8, "cell 8: expected setup loop not found"
    nb["cells"][8]["source"] = c8.replace(OLD_LOOP, new_loop)

    OUT_NB.parent.mkdir(parents=True, exist_ok=True)
    OUT_NB.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"wrote {OUT_NB} ({OUT_NB.stat().st_size} bytes)")

    # --- self-check ---
    src = json.loads(SRC_NB.read_text(encoding="utf-8"))
    out = json.loads(OUT_NB.read_text(encoding="utf-8"))
    diff = [i for i in range(len(src["cells"])) if src["cells"][i]["source"] != out["cells"][i]["source"]]
    assert diff == [6, 8], f"unexpected diff cells: {diff}"
    for idx in diff:
        compile("".join(out["cells"][idx]["source"]), f"cell{idx}", "exec")
    print(f"syntax OK: cells {diff} compile")

    o8 = "".join(out["cells"][8]["source"])
    o12 = "".join(out["cells"][12]["source"])
    assert f"'LOCAL_ANALYZER_SEED': '{SEED}'" in o8, "seed literal missing from cell 8"
    assert "'MULTIMODAL_UPSCALE': '8'" not in o8, "v25 must not carry the upscale change"
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '768'" not in o8, "v25 must not cap output"
    assert "LOCAL_ANALYZER_TEMPERATURE': '0" not in o8.replace("'0.6'", ""), \
        "v25 must not set temperature; only assert it"
    assert "TEETH FAIL" in o8, "in-kernel teeth missing"
    assert o12 == "".join(src["cells"][12]["source"]), "cell 12 must stay v10 exact (no patch)"

    print("self-check OK: cells [6, 8]; v10 config exact + seed pinned; cell 12 untouched")
    print(f"seed = {SEED}; temperature deliberately left at the harness default 0.6")


if __name__ == "__main__":
    main()
