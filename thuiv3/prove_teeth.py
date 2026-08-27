"""thui-v3-0 teeth, proven against the REAL setup command a previous run printed.

The failure this guards is the duckv25 shape: an anchor that moved in a newer bundle makes
the .replace() a silent no-op, the run scores normally, and the artifacts call it a lever.
So the teeth are graded on the actual command text `thui-v1-1-r2` executed -- recovered from
that run's Kaggle log -- plus four mutations of it that must each be caught.

Usage:  python thuiv3/prove_teeth.py
Needs:  ~/Claude/arc-artifacts/thuiv1-1r2/thui-v1-1-r2.log
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

LOG = pathlib.Path.home() / "Claude/arc-artifacts/thuiv1-1r2/thui-v1-1-r2.log"
NB = pathlib.Path(__file__).resolve().parent / "taaf-thui-v3-0.ipynb"


def real_command() -> str:
    """The setup command text thui-v1-1-r2 actually ran, from its own log."""
    arr = json.loads(LOG.read_text(errors="replace"))
    txt = "".join(x.get("data", "") for x in arr)
    i = txt.find("taaf.kaggle: setup command:")
    if i < 0:
        raise SystemExit("FAIL: no setup command line in the log")
    seg = txt[i:i + 40000]
    # the command runs to the next taaf.kaggle: line
    j = seg.find("\ntaaf.kaggle:", 1)
    return seg[:j if j > 0 else len(seg)]


def apply_lever(command: str) -> str:
    """The exact transformation cell 8 performs for this build."""
    return command.replace(
        "'LOCAL_ANALYZER_YIELD_SECONDS': '60'",
        "'LOCAL_ANALYZER_YIELD_SECONDS': '180'",
    )


def teeth(command: str) -> None:
    """The four in-kernel asserts, verbatim in effect."""
    assert "'LOCAL_ANALYZER_YIELD_SECONDS': '180'" in command, "yield injection missed"
    assert "'LOCAL_ANALYZER_YIELD_SECONDS': '60'" not in command, "the old 60 s value survives"
    assert command.count("'LOCAL_ANALYZER_YIELD_SECONDS'") == 1, "yield key present more than once"
    assert "'LOCAL_ANALYZER_TOOL_STEPS': '0'" in command, "TOOL_STEPS must stay 0"


def main() -> int:
    fails = []

    if not LOG.exists():
        print(f"FAIL: fixture missing: {LOG}", file=sys.stderr)
        return 2
    cmd = real_command()

    # CONTROL 0 -- the fixture is the real thing, not an empty string
    if "'LOCAL_ANALYZER_YIELD_SECONDS': '60'" not in cmd:
        print("FAIL: fixture does not contain the 60 s literal -- wrong text extracted",
              file=sys.stderr)
        return 2
    if "'LOCAL_ANALYZER_SEED': '20260825'" not in cmd:
        print("FAIL: fixture is not a v1-1 command (no seed) -- wrong text extracted",
              file=sys.stderr)
        return 2
    print(f"  [ok]   CONTROL 0  fixture is the real v1-1 command ({len(cmd):,} chars)")

    # CASE 1 -- the real command, levered: teeth must PASS
    try:
        teeth(apply_lever(cmd))
        print("  [PASS] case 1  real command + lever -> teeth pass")
    except AssertionError as e:
        fails.append(f"case 1 the real command fails its own teeth: {e}")

    # CASE 2..5 -- mutations that must each be CAUGHT
    mutations = {
        "2 anchor moved (no space after colon)":
            cmd.replace("'LOCAL_ANALYZER_YIELD_SECONDS': '60'",
                        "'LOCAL_ANALYZER_YIELD_SECONDS':'60'"),
        "3 value already differs (bundle shipped 90)":
            cmd.replace("'LOCAL_ANALYZER_YIELD_SECONDS': '60'",
                        "'LOCAL_ANALYZER_YIELD_SECONDS': '90'"),
        "4 key duplicated (two values would race)":
            cmd.replace("'LOCAL_ANALYZER_YIELD_SECONDS': '60'",
                        "'LOCAL_ANALYZER_YIELD_SECONDS': '60',\n    "
                        "'LOCAL_ANALYZER_YIELD_SECONDS': '60'"),
        "5 TOOL_STEPS crossed (a second variable)":
            cmd.replace("'LOCAL_ANALYZER_TOOL_STEPS': '0'",
                        "'LOCAL_ANALYZER_TOOL_STEPS': '12'"),
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

    # CASE 6 -- the built notebook carries the link and changed cell 8 only
    if not NB.exists():
        fails.append("case 6: built notebook missing -- run build_notebook.py first")
    else:
        nb = json.loads(NB.read_text())
        c8 = "".join(nb["cells"][8].get("source", []))
        if "'LOCAL_ANALYZER_YIELD_SECONDS': '180'" not in c8:
            fails.append("case 6: cell 8 does not carry the 180 value")
        elif "req_in_turn" not in "".join(nb["cells"][12].get("source", [])):
            fails.append("case 6: cell 12 lost the usage probe")
        else:
            print("  [PASS] case 6  built notebook carries the lever and the probe")

    for f in fails:
        print(f"  [FAIL] {f}")
    if fails:
        print(f"\n{len(fails)} failure(s)", file=sys.stderr)
        return 1
    print("\nteeth proven: 4 mutations each caught, real command passes, notebook built")
    return 0


if __name__ == "__main__":
    sys.exit(main())
