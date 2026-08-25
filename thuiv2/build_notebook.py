"""Build thuiv2/taaf-thui-v2.ipynb -- v10 plus ONE change: animation retrieval OFF (B39).

Cell 12 carries thuiv2/retrieval_off_patch.py verbatim. Cells 6 and 8 are duckv10's, byte
for byte -- same anim bundle, same Qwen3.8-27B-FP8, output UNCAPPED, upscale 4, v10's clock,
temperature and seed untouched.

⚠️ The self-check compares cell 12 against the PATCH FILE and cells 6/8 against
duckv10/taaf-duck-v10.ipynb -- never against SRC_NB. duckv25 shipped a run advertised as
"v10 + seed" that was duckmod + seed, because its assert compared cell 12 against the same
source the builder never touches: a tautology that passes by construction and prints a
reassuring line (CLAUDE.md §Versioning).

Behavioural teeth for the patch itself are thuiv2/prove_teeth.py -- 13 cases against the
real vendored source, proved red by 6 mutations. This builder checks only what it builds.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_NB = REPO / "duckmod" / "taaf-duck-mod.ipynb"
V10_NB = REPO / "duckv10" / "taaf-duck-v10.ipynb"
PATCH = REPO / "thuiv2" / "retrieval_off_patch.py"
OUT_NB = REPO / "thuiv2" / "taaf-thui-v2.ipynb"


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    v10 = json.loads(V10_NB.read_text(encoding="utf-8"))

    for idx in (6, 8):
        nb["cells"][idx]["source"] = "".join(v10["cells"][idx]["source"])

    patch = PATCH.read_text(encoding="utf-8")
    nb["cells"][12]["source"] = patch

    OUT_NB.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"wrote {OUT_NB} ({OUT_NB.stat().st_size} bytes)")

    # --- self-check: every claim this build makes, asserted against its real base ---
    out = json.loads(OUT_NB.read_text(encoding="utf-8"))
    src = json.loads(SRC_NB.read_text(encoding="utf-8"))
    diff = [i for i in range(len(src["cells"]))
            if src["cells"][i]["source"] != out["cells"][i]["source"]]
    assert diff == [6, 8, 12], f"unexpected diff cells: {diff}"

    o6, o8, o12 = ("".join(out["cells"][i]["source"]) for i in (6, 8, 12))
    v6, v8 = ("".join(v10["cells"][i]["source"]) for i in (6, 8))
    assert o6 == v6, "cell 6 must be duckv10's, byte for byte"
    assert o8 == v8, "cell 8 must be duckv10's, byte for byte"
    assert o12 == patch, "cell 12 must be retrieval_off_patch.py verbatim"
    # ⚠️ MULTIMODAL_UPSCALE and LOCAL_ANALYZER_TEMPERATURE are NOT set in the notebook at
    # all -- they come from the bundle's own setup_commands.json (R40 §2). Asserting them
    # here is the mistake duckv26's builder made and caught.
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '0'" in o8, "thuiv2: output must stay UNCAPPED"
    assert "LOCAL_ANALYZER_SEED" not in o8, "thuiv2 must not pin the seed -- that is B37"
    # the patch's own identity, so a stale or truncated copy cannot ship
    assert "duckmod: inject HUD auto-flag" not in o12, "duckmod's patch block leaked into cell 12"
    assert "_sess.animation_record = _no_retrieval" in o12, "edit 1 (retrieval) missing"
    assert "_ta.STRUCTURED_RUNTIME_STATE_ADDENDUM = _after" in o12, "edit 2 (prompt) missing"
    assert "import inference.agent.prompts" not in o12, (
        "cell 12 must not touch inference.agent.prompts -- tool_agent imports the addendum "
        "BY VALUE, so rebinding there changes nothing and the run measures nothing")
    for idx in diff:
        compile("".join(out["cells"][idx]["source"]), f"cell{idx}", "exec")

    print(f"syntax OK: cells {diff} compile")
    print("self-check OK: cells 6/8 = duckv10 byte-exact; cell 12 = retrieval_off_patch.py; "
          "output uncapped; no seed pinned; both edits present; prompts module untouched")


if __name__ == "__main__":
    main()
