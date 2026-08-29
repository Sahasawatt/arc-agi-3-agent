"""thui-v6-0 teeth, proven against a REAL setup command plus mutations of it.

The failure this guards is the duckv25 shape: an anchor that moved in a newer bundle makes
the .replace() a silent no-op, the run scores normally, and the artifacts call it a lever.

FIXTURE RESOLUTION -- three sources, first one that exists wins, and the source is PRINTED.
v3-0/v5-0 hardcode `~/Claude/arc-artifacts/...`, which does not exist on every box, so those
proofs cannot run there at all -- a proof that cannot run is not a proof.

  1. $THUI_SETUP_COMMAND      a file holding the raw command text (explicit override)
  2. ~/Claude/arc-artifacts/thuiv1-1r2/thui-v1-1-r2.log   the log echo v3-0/v5-0 use
                              (POST-v1-1: already carries the seed and the model swap)
  3. <repo>/duck/bundle/setup_commands.json               the bundle on disk
                              (PRE-v1-1: the raw text cell 8 receives)

Sources 2 and 3 are at different points in cell 8's chain, so `apply_chain` reproduces the
v1-1 links first when they are absent -- what is graded is what cell 8 actually produces.

Usage:  python thuiv6/prove_teeth.py
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
NB = HERE / "taaf-thui-v6-0.ipynb"

LOG = pathlib.Path.home() / "Claude/arc-artifacts/thuiv1-1r2/thui-v1-1-r2.log"
BUNDLE = REPO / "duck" / "bundle" / "setup_commands.json"


# ---------------------------------------------------------------- fixture


def _from_log(path: pathlib.Path) -> str:
    arr = json.loads(path.read_text(errors="replace"))
    txt = "".join(x.get("data", "") for x in arr)
    i = txt.find("taaf.kaggle: setup command:")
    if i < 0:
        raise SystemExit(f"FAIL: no setup command line in {path}")
    seg = txt[i:i + 40000]
    j = seg.find("\ntaaf.kaggle:", 1)
    return seg[:j if j > 0 else len(seg)]


def _from_bundle(path: pathlib.Path) -> str:
    cmds = json.loads(path.read_text(encoding="utf-8"))
    if len(cmds) != 1:
        raise SystemExit(f"FAIL: {path} holds {len(cmds)} commands, expected 1 -- "
                         f"cell 8's teeth assume a single command")
    return cmds[0]


def real_command() -> tuple[str, str]:
    """(command text, where it came from). Never guesses; lists what it looked at."""
    override = os.environ.get("THUI_SETUP_COMMAND")
    tried = []
    if override:
        p = pathlib.Path(override)
        tried.append(str(p))
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace"), f"$THUI_SETUP_COMMAND {p}"
    tried.append(str(LOG))
    if LOG.exists():
        return _from_log(LOG), f"log echo {LOG}"
    tried.append(str(BUNDLE))
    if BUNDLE.exists():
        return _from_bundle(BUNDLE), f"bundle on disk {BUNDLE}"
    raise SystemExit("FAIL: no setup-command fixture reachable. UNREACHABLE:\n  "
                     + "\n  ".join(tried))


# ---------------------------------------------------------------- the transform


def apply_chain(command: str) -> str:
    """Exactly what cell 8 performs, in order. The v1-1 links are replayed only when the
    fixture predates them, so a post-v1-1 log and a pre-v1-1 bundle grade the same text."""
    if "'LOCAL_ANALYZER_SEED': '20260825'" not in command:
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
                "    'LOCAL_ANALYZER_SEED': '20260825',\n    'LOCAL_ANALYZER_TEMPERATURE':",
            )
        )
    return command.replace(
        "ANALYZER_CONTEXT_WINDOW = 32768",
        "ANALYZER_CONTEXT_WINDOW = 49152",
    )


# The six in-kernel asserts. Each entry is (label, the predicate's SOURCE TEXT as it must
# appear in cell 8, the callable). Case 8 greps the source text out of the built notebook,
# so this file cannot drift into being a second, kinder implementation of the gate.
TEETH = [
    ("49152 present",
     '"ANALYZER_CONTEXT_WINDOW = 49152" in command',
     lambda c: "ANALYZER_CONTEXT_WINDOW = 49152" in c),
    ("32768 absent",
     '"ANALYZER_CONTEXT_WINDOW = 32768" not in command',
     lambda c: "ANALYZER_CONTEXT_WINDOW = 32768" not in c),
    ("one assignment",
     'command.count("ANALYZER_CONTEXT_WINDOW = ") == 1',
     lambda c: c.count("ANALYZER_CONTEXT_WINDOW = ") == 1),
    ("assignment reaches env",
     '"\'LOCAL_ANALYZER_CONTEXT_WINDOW\': str(ANALYZER_CONTEXT_WINDOW)" in command',
     lambda c: "'LOCAL_ANALYZER_CONTEXT_WINDOW': str(ANALYZER_CONTEXT_WINDOW)" in c),
    ("ceiling 65536 intact",
     '"VLLM_MAX_MODEL_LEN = 65536" in command',
     lambda c: "VLLM_MAX_MODEL_LEN = 65536" in c),
    ("YIELD still 60",
     '"\'LOCAL_ANALYZER_YIELD_SECONDS\': \'60\'" in command',
     lambda c: "'LOCAL_ANALYZER_YIELD_SECONDS': '60'" in c),
]


def teeth(command: str) -> None:
    for label, _src, fn in TEETH:
        if not fn(command):
            raise AssertionError(label)


# ---------------------------------------------------------------- the proof


def main() -> int:
    fails = []
    cmd, where = real_command()
    print(f"  fixture: {where}")

    # CONTROL 0 -- the fixture is the real thing, not an empty string or the wrong slice.
    # Positive probes it MUST contain, and one negative that must be absent.
    for probe in ("ANALYZER_CONTEXT_WINDOW = 32768",
                  "VLLM_MAX_MODEL_LEN = 65536",
                  "'LOCAL_ANALYZER_YIELD_SECONDS': '60'",
                  "'MULTIMODAL_UPSCALE': '4'"):
        if probe not in cmd:
            print(f"FAIL: fixture does not contain {probe!r} -- wrong text extracted",
                  file=sys.stderr)
            return 2
    if "ZZZ_NEGATIVE_CONTROL" in cmd:
        print("FAIL: fixture contains the negative control -- the probe does not "
              "discriminate", file=sys.stderr)
        return 2
    if len(cmd) < 5000:
        print(f"FAIL: fixture is {len(cmd)} chars -- too short to be the real command",
              file=sys.stderr)
        return 2
    print(f"  [ok]   CONTROL 0  fixture is a real setup command ({len(cmd):,} chars), "
          f"4 positive probes + 1 negative")

    # CASE 1 -- the real command through the real chain: teeth must PASS
    try:
        teeth(apply_chain(cmd))
        print("  [PASS] case 1  real command + chain -> all 6 teeth pass")
    except AssertionError as e:
        fails.append(f"case 1: the real command fails its own teeth: {e}")

    # CASE 2..7 -- one mutation per tooth, each must be CAUGHT
    mutations = {
        "2 anchor moved (double space before =)":
            cmd.replace("ANALYZER_CONTEXT_WINDOW = 32768",
                        "ANALYZER_CONTEXT_WINDOW  = 32768"),
        "3 bundle already ships a different window (40960)":
            cmd.replace("ANALYZER_CONTEXT_WINDOW = 32768",
                        "ANALYZER_CONTEXT_WINDOW = 40960"),
        "4 assignment duplicated (two windows would race)":
            cmd.replace("ANALYZER_CONTEXT_WINDOW = 32768",
                        "ANALYZER_CONTEXT_WINDOW = 32768\n"
                        "ANALYZER_CONTEXT_WINDOW = 32768"),
        "5 env rewired off the variable (lever edits dead code)":
            cmd.replace("'LOCAL_ANALYZER_CONTEXT_WINDOW': str(ANALYZER_CONTEXT_WINDOW)",
                        "'LOCAL_ANALYZER_CONTEXT_WINDOW': '32768'"),
        "6 server ceiling lowered to 32768 (49152 becomes unsized)":
            cmd.replace("VLLM_MAX_MODEL_LEN = 65536", "VLLM_MAX_MODEL_LEN = 32768"),
        "7 YIELD crossed (a second variable)":
            cmd.replace("'LOCAL_ANALYZER_YIELD_SECONDS': '60'",
                        "'LOCAL_ANALYZER_YIELD_SECONDS': '180'"),
    }
    for name, mutant in mutations.items():
        if mutant == cmd:
            fails.append(f"case {name}: mutation did not apply -- the case grades nothing")
            continue
        try:
            teeth(apply_chain(mutant))
            fails.append(f"case {name}: teeth PASSED on a mutant -- they have no teeth")
        except AssertionError as e:
            print(f"  [PASS] case {name} -> caught by [{e}]")

    # CASE 8 -- the shipped notebook. The lever, the probe, and every predicate above must
    # appear VERBATIM in cell 8, so this file cannot be a kinder second implementation.
    if not NB.exists():
        fails.append("case 8: built notebook missing -- run build_notebook.py first")
    else:
        nb = json.loads(NB.read_text())
        c8 = "".join(nb["cells"][8].get("source", []))
        if '"ANALYZER_CONTEXT_WINDOW = 49152",' not in c8:
            fails.append("case 8: cell 8 does not carry the 49152 replace link")
        if "req_in_turn" not in "".join(nb["cells"][12].get("source", [])):
            fails.append("case 8: cell 12 lost the usage probe")
        missing = [label for label, src, _ in TEETH if src not in c8]
        if missing:
            fails.append(f"case 8: cell 8 is missing {len(missing)} of {len(TEETH)} graded "
                         f"predicates verbatim: {missing}")
        if not fails:
            print(f"  [PASS] case 8  notebook carries the lever, the probe, and all "
                  f"{len(TEETH)} predicates verbatim")

    for f in fails:
        print(f"  [FAIL] {f}")
    if fails:
        print(f"\n{len(fails)} failure(s)", file=sys.stderr)
        return 1
    print(f"\nteeth proven: {len(mutations)} mutations each caught, real command passes, "
          f"notebook carries every predicate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
