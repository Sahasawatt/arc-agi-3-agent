"""Build duckv26/taaf-duck-v26.ipynb -- v10 plus ONE change: the family brake (B38).

Cell 12 carries duckv26/brake_patch.py verbatim. Cells 6 and 8 are duckv10's, byte for
byte -- same anim bundle, same Qwen3.8-27B-FP8, output UNCAPPED, upscale 4, v10's clock,
temperature and seed untouched.

⚠️ The self-check compares cell 12 against the PATCH FILE and cells 6/8 against
duckv10/taaf-duck-v10.ipynb -- never against SRC_NB. duckv25 shipped a run advertised as
"v10 + seed" that was duckmod + seed, because its assert compared cell 12 against the same
source the builder never touches: a tautology that passes by construction and prints a
reassuring line (fixed 2026-08-25; see CLAUDE.md §Versioning).
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_NB = REPO / "duckmod" / "taaf-duck-mod.ipynb"
V10_NB = REPO / "duckv10" / "taaf-duck-v10.ipynb"
PATCH = REPO / "duckv26" / "brake_patch.py"
OUT_NB = REPO / "duckv26" / "taaf-duck-v26.ipynb"


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    v10 = json.loads(V10_NB.read_text(encoding="utf-8"))

    # cells 6 and 8 come from v10 -- the dataset refs and the setup loop, unmodified
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
    assert o12 == patch, "cell 12 must be brake_patch.py verbatim"
    # The config claims, asserted on the cell that actually carries them. `o8 == v8`
    # above is the strong form and subsumes these; they are kept because they name the
    # property in the failure message. ⚠️ MULTIMODAL_UPSCALE and LOCAL_ANALYZER_TEMPERATURE
    # are NOT set in the notebook at all -- they come from the bundle's own
    # setup_commands.json (R40 §2: the lever table's "current" column has to come from a
    # run's taaf_setup_env.json, not from the source). A first cut of this builder asserted
    # them here, copied from duckv25 whose cell 8 does inject a key, and failed correctly.
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '0'" in o8, "duckv26: output must stay UNCAPPED"
    assert "LOCAL_ANALYZER_SEED" not in o8, "duckv26 must not pin the seed -- that is B37"
    # and the patch's own identity, so a stale or truncated copy cannot ship
    assert "duckmod: inject HUD auto-flag" not in o12, "duckmod's patch block leaked into cell 12"
    assert "NoopGuard.is_known_noop = _is_known_noop" in o12, "brake not installed"
    assert "NoopGuard.observe = _observe" in o12, "counter not installed"
    for idx in diff:
        compile("".join(out["cells"][idx]["source"]), f"cell{idx}", "exec")

    print(f"syntax OK: cells {diff} compile")
    # Says only what was checked: upscale and temperature are the bundle's, not ours,
    # so claiming them here would be the same class of reassuring-but-unchecked line
    # that let duckv25 ship (CLAUDE.md §Versioning).
    print("self-check OK: cells 6/8 = duckv10 byte-exact; cell 12 = brake_patch.py; "
          "output uncapped; no seed pinned")


if __name__ == "__main__":
    main()
