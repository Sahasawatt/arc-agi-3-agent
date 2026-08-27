"""thui-v5-0 teeth, proven against the REAL setup command previous runs printed.

The failure this guards is the duckv25 shape: an anchor that moved in a newer bundle makes
the .replace() a silent no-op, the run scores normally, and the artifacts call it a lever.
So the teeth are graded on the actual command text `thui-v1-1-r2` executed -- recovered from
that run's Kaggle log -- with BOTH of this build's levers applied in the order cell 8 applies
them, plus six mutations that must each be caught.

CONTROL 1 is a second, independent run: `thui-v4-0`'s own log, which must show the
temperature literal landing as '1.0' in a real bundle command. Without it, a green result
here cannot separate "the replace works" from "the fixture happens to match my expectation".

Usage:  python thuiv5/prove_teeth.py
Needs:  ~/Claude/arc-artifacts/thuiv1-1r2/thui-v1-1-r2.log   (subject)
        ~/Claude/arc-artifacts/thui-v4-0/thui-v4-0.log       (CONTROL 1)
"""

from __future__ import annotations

import json
import pathlib
import sys

ART = pathlib.Path.home() / "Claude/arc-artifacts"
LOG = ART / "thuiv1-1r2/thui-v1-1-r2.log"
LOG_V4 = ART / "thui-v4-0/thui-v4-0.log"
NB = pathlib.Path(__file__).resolve().parent / "taaf-thui-v5-0.ipynb"

TEMP_OLD = "'LOCAL_ANALYZER_TEMPERATURE': '0.6'"
TEMP_NEW = "'LOCAL_ANALYZER_TEMPERATURE': '1.0'"
YIELD_OLD = "'LOCAL_ANALYZER_YIELD_SECONDS': '60'"
YIELD_NEW = "'LOCAL_ANALYZER_YIELD_SECONDS': '180'"


def setup_command(path: pathlib.Path) -> str:
    """The setup command text a run actually executed, from its own Kaggle log."""
    arr = json.loads(path.read_text(errors="replace"))
    txt = "".join(x.get("data", "") for x in arr)
    i = txt.find("taaf.kaggle: setup command:")
    if i < 0:
        raise SystemExit(f"FAIL: no setup command line in {path}")
    seg = txt[i:i + 40000]
    j = seg.find("\ntaaf.kaggle:", 1)
    return seg[:j if j > 0 else len(seg)]


def apply_lever(command: str) -> str:
    """The exact transformation cell 8 performs for this build: v3-0's yield, then temp."""
    return command.replace(YIELD_OLD, YIELD_NEW).replace(TEMP_OLD, TEMP_NEW)


def teeth(command: str) -> None:
    """This build's three asserts plus the four it inherits from v3-0, verbatim in effect."""
    assert TEMP_NEW in command, "temperature injection missed"
    assert TEMP_OLD not in command, "the old 0.6 value survives"
    assert command.count("'LOCAL_ANALYZER_TEMPERATURE'") == 1, "temperature key duplicated"
    assert YIELD_NEW in command, "yield injection missed"
    assert YIELD_OLD not in command, "the old 60 s value survives"
    assert command.count("'LOCAL_ANALYZER_YIELD_SECONDS'") == 1, "yield key duplicated"
    assert "'LOCAL_ANALYZER_TOOL_STEPS': '0'" in command, "TOOL_STEPS must stay 0"
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '0'" in command, "output must stay UNCAPPED"
    assert "'MULTIMODAL_UPSCALE': '4'" in command, "upscale must stay 4"
    assert "'LOCAL_ANALYZER_SEED': '20260825'" in command, "the seed pin must ride along"


def main() -> int:
    fails = []

    if not LOG.exists():
        print(f"FAIL: fixture missing: {LOG}", file=sys.stderr)
        return 2
    cmd = setup_command(LOG)

    # CONTROL 0 -- the fixture is the real thing, and it is the base state this build moves
    for literal, why in ((YIELD_OLD, "yield 60"), (TEMP_OLD, "temperature 0.6"),
                         ("'LOCAL_ANALYZER_SEED': '20260825'", "the v1-1 seed")):
        if literal not in cmd:
            print(f"FAIL: fixture does not contain {why} -- wrong text extracted",
                  file=sys.stderr)
            return 2
    print(f"  [ok]   CONTROL 0  fixture is the real v1-1 command ({len(cmd):,} chars), "
          f"at yield 60 and temperature 0.6")

    # CONTROL 1 -- an INDEPENDENT run proves this literal really lands as '1.0' in a bundle
    # command. Without it, case 1 cannot separate a working replace from a lucky fixture.
    if not LOG_V4.exists():
        fails.append(f"CONTROL 1 missing: {LOG_V4} -- cannot show the literal lands for real")
    else:
        v4 = setup_command(LOG_V4)
        if TEMP_NEW not in v4:
            fails.append("CONTROL 1: thui-v4-0's own command does NOT carry temperature 1.0 -- "
                         "the literal this build injects is not the one the harness reads")
        elif TEMP_OLD in v4:
            fails.append("CONTROL 1: thui-v4-0's command still carries 0.6 alongside 1.0")
        else:
            print("  [ok]   CONTROL 1  thui-v4-0's real command carries temperature 1.0, "
                  "0.6 absent")

    # CASE 1 -- the real command, levered: teeth must PASS
    try:
        teeth(apply_lever(cmd))
        print("  [PASS] case 1  real command + both levers -> teeth pass")
    except AssertionError as e:
        fails.append(f"case 1 the real command fails its own teeth: {e}")

    # CASE 2..7 -- mutations that must each be CAUGHT
    mutations = {
        "2 temperature anchor moved (no space after colon)":
            cmd.replace(TEMP_OLD, "'LOCAL_ANALYZER_TEMPERATURE':'0.6'"),
        "3 bundle shipped a different temperature (0.7)":
            cmd.replace(TEMP_OLD, "'LOCAL_ANALYZER_TEMPERATURE': '0.7'"),
        "4 temperature key duplicated (two values would race)":
            cmd.replace(TEMP_OLD, TEMP_OLD + ",\n    " + TEMP_OLD),
        "5 yield anchor moved (the inherited lever silently no-ops)":
            cmd.replace(YIELD_OLD, "'LOCAL_ANALYZER_YIELD_SECONDS':'60'"),
        "6 TOOL_STEPS crossed (a second variable)":
            cmd.replace("'LOCAL_ANALYZER_TOOL_STEPS': '0'",
                        "'LOCAL_ANALYZER_TOOL_STEPS': '12'"),
        "7 output re-capped at 768 (the v9 lever that scored 0.22)":
            cmd.replace("'LOCAL_ANALYZER_MAX_OUTPUT': '0'",
                        "'LOCAL_ANALYZER_MAX_OUTPUT': '768'"),
    }
    for name, mutant in mutations.items():
        if mutant == cmd:
            fails.append(f"case {name}: mutation did not apply -- the case grades nothing")
            continue
        try:
            teeth(apply_lever(mutant))
            fails.append(f"case {name}: teeth PASSED on a mutant -- they have no teeth")
        except AssertionError:
            print(f"  [PASS] case {name} -> caught")

    # CASE 8 -- the built notebook carries the link, this build's teeth, and NOT the old tooth
    if not NB.exists():
        fails.append("case 8: built notebook missing -- run build_notebook.py first")
    else:
        nb = json.loads(NB.read_text())
        c8 = "".join(nb["cells"][8].get("source", []))
        c12 = "".join(nb["cells"][12].get("source", []))
        checks = [
            (TEMP_NEW in c8, "cell 8 does not carry the 1.0 value"),
            (YIELD_NEW in c8, "cell 8 lost the inherited 180 yield"),
            ('"thui-v1-1 TEETH FAIL: temperature is not 0.6' not in c8,
             "the v1-1 tooth asserting 0.6 SURVIVES -- the kernel would die on its own assert"),
            ("thui-v5-0 TEETH FAIL" in c8, "cell 8 does not carry this build's teeth"),
            ("req_in_turn" in c12, "cell 12 lost the usage probe"),
        ]
        broke = [msg for ok, msg in checks if not ok]
        if broke:
            fails.extend(f"case 8: {m}" for m in broke)
        else:
            print("  [PASS] case 8  built notebook: lever, inherited lever, teeth swapped, probe")

    for f in fails:
        print(f"  [FAIL] {f}")
    if fails:
        print(f"\n{len(fails)} failure(s)", file=sys.stderr)
        return 1
    print("\nteeth proven: 6 mutations each caught, real command passes, "
          "2 controls, notebook built")
    return 0


if __name__ == "__main__":
    sys.exit(main())
