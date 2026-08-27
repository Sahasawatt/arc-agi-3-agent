"""thui-v3-0 -- B47's knob: LOCAL_ANALYZER_YIELD_SECONDS 60 -> 180, and nothing else.

WHY THIS LEVER (notes/R44-the-turn-budget-is-a-token-budget.md, 0 slots):
  * the tool-step loop is gated by cumulative wall time against YIELD_SECONDS, checked at
    the TOP of each iteration -- 186/186 multi-request turns keep cum(all but last) under
    60 s, zero violations, against a negative control of 5.9% for cum(including last).
  * decode runs at 12.7 tok/s (R^2 0.9835), so 60 s buys ~784 completion tokens while the
    median request generates 1,368 = 1.74x the whole budget.  That is why 91% of
    single-request turns blew the gate on their FIRST request.
  * the games are already ~100% busy (summed request wall 7,910 s of the 7,920 s clock) and
    make a median 38 analyze() calls, so each turn can afford ~208 s -- the gate is set to
    60 s, a 3.5x mismatch derived from the run's own clock rather than guessed.
  * 42.4% of all completion tokens sit in turns that were RETRIED, which is the same order
    as B45's ~45% "abandoned" residual measured by a different instrument.

WHY 180: p70 of first-request wall is 169.9 s, so 180 lets roughly the top 70% of first
requests reach a second tool step, while staying under the ~208 s median a turn can afford
so one turn cannot eat a game.  240 (p80) exceeds the 155 s IQR floor and risks exactly that.

BASE IS thui-v1-1, NOT duckmod.  Per CLAUDE.md Versioning: "A builder's self-check must
compare against the BASE the build claims, not against SRC_NB" -- duckv25 shipped a
tautological assert that way.  v1-1 is v10 + the request_usage_probe (cell 12) + the seed
pin, its two runs scored 5.24 and 4.33, so this build is ONE variable against a two-run
baseline and it carries the probe that measures the very quantity being moved.

⚠️ WHAT THIS DOES NOT CLAIM: R44 section 6 measured that reading headroom off each turn's
first-request time OVER-PREDICTS by 43% at the only checkable value (266 predicted vs 186
observed at YIELD=60), because a turn also ends, correctly, when its tool call was an action
that executed.  The size of this lever is NOT established.  Only its mechanism is.
"""

from __future__ import annotations

import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
BASE_NB = REPO / "thuiv1" / "v1-1" / "taaf-thui-v1-1.ipynb"
OUT_NB = HERE / "taaf-thui-v3-0.ipynb"
OUT_META = HERE / "kernel-metadata.json"

OLD = "'LOCAL_ANALYZER_YIELD_SECONDS': '60'"
NEW = "'LOCAL_ANALYZER_YIELD_SECONDS': '180'"

# The YIELD literal lives in the BUNDLE's setup_commands.json, not in the notebook -- so the
# build adds a link to cell 8's existing .replace() chain, exactly as the v1-1 seed pin does.
# Anchor is the chain's closing paren followed by the first assert.
CHAIN_ANCHOR = '        )\n    )\n    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot"'
CHAIN_NEW = (
    '        )\n'
    '        .replace(\n'
    '            "\'LOCAL_ANALYZER_YIELD_SECONDS\': \'60\'",\n'
    '            "\'LOCAL_ANALYZER_YIELD_SECONDS\': \'180\'",\n'
    '        )\n'
    '    )\n'
    '    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot"'
)

OLD_PRINT = 'print("thui-v1-1: sampler pinned, seed=20260825, temperature untouched", flush=True)'
NEW_PRINT = (
    'print("thui-v3-0: YIELD_SECONDS 60 -> 180 (B47/R44); seed=20260825, temperature untouched", flush=True)'
)

# The teeth. Appended to cell 8 inside the setup loop, so they run IN-KERNEL before the
# benchmark starts -- a silent no-op would otherwise score normally while measuring nothing.
TEETH = '''    # thui-v3-0 TEETH, in-kernel, before the benchmark starts. The YIELD value IS this
    # build: if the anchor moved in a newer bundle the replace is a silent no-op and the run
    # would score normally while measuring nothing (the duckv25 shape).
    assert "'LOCAL_ANALYZER_YIELD_SECONDS': '180'" in command, (
        "thui-v3-0 TEETH FAIL: yield injection missed -- "
        "\\"'LOCAL_ANALYZER_YIELD_SECONDS': '60'\\" is not in this bundle's setup command"
    )
    assert "'LOCAL_ANALYZER_YIELD_SECONDS': '60'" not in command, (
        "thui-v3-0 TEETH FAIL: the old 60 s value survives -- two values would race"
    )
    assert command.count("'LOCAL_ANALYZER_YIELD_SECONDS'") == 1, (
        "thui-v3-0 TEETH FAIL: yield key present more than once"
    )
    assert "'LOCAL_ANALYZER_TOOL_STEPS': '0'" in command, (
        "thui-v3-0 TEETH FAIL: TOOL_STEPS must stay 0 -- B47 measured a cap inert and this "
        "arm must not cross that variable"
    )
'''


def build() -> int:
    if not BASE_NB.exists():
        print(f"FAIL: base notebook missing: {BASE_NB}", file=sys.stderr)
        return 1
    base = json.loads(BASE_NB.read_text())
    out = copy.deepcopy(base)

    cells = out["cells"]
    src = "".join(cells[8].get("source", []))

    if src.count(CHAIN_ANCHOR) != 1:
        print(f"FAIL: expected exactly one replace-chain anchor in cell 8, "
              f"found {src.count(CHAIN_ANCHOR)} -- base drifted", file=sys.stderr)
        return 1
    if OLD in src:
        print("FAIL: cell 8 already carries a YIELD literal -- base is not v1-1", file=sys.stderr)
        return 1
    if OLD_PRINT not in src:
        print("FAIL: the v1-1 print line is not in cell 8 -- base drifted", file=sys.stderr)
        return 1

    new_src = src.replace(CHAIN_ANCHOR, CHAIN_NEW).replace(OLD_PRINT, NEW_PRINT)
    # teeth go immediately before the (now renamed) print line
    new_src = new_src.replace(NEW_PRINT, TEETH.rstrip("\n") + "\n    " + NEW_PRINT.lstrip())
    cells[8]["source"] = new_src.splitlines(keepends=True)

    # ---- self-check AGAINST THE BASE THIS BUILD CLAIMS, naming what must differ ----
    bad = []
    for i, (b, o) in enumerate(zip(base["cells"], cells)):
        bs, os_ = "".join(b.get("source", [])), "".join(o.get("source", []))
        if i == 8:
            if bs == os_:
                bad.append("cell 8 is UNCHANGED -- the whole build is a no-op")
            if NEW not in os_:
                bad.append("cell 8 does not carry the 180 value")
            if CHAIN_NEW not in os_:
                bad.append("cell 8 does not carry the new .replace() link -- the lever "
                           "would never reach the bundle command")
            if os_.count(OLD) < 1:
                bad.append("cell 8 never names the 60 value, so nothing can be replaced")
        elif bs != os_:
            bad.append(f"cell {i} differs and must not -- this build changes cell 8 ONLY")
    if len(base["cells"]) != len(cells):
        bad.append("cell count changed")

    # cell 12 is the request_usage_probe and is the instrument; it must ride along untouched
    c12 = "".join(cells[12].get("source", []))
    if "req_in_turn" not in c12:
        bad.append("cell 12 lost the request_usage_probe -- nothing would measure the change")

    if bad:
        for b in bad:
            print(f"SELF-CHECK FAIL: {b}", file=sys.stderr)
        return 1

    OUT_NB.write_text(json.dumps(out, indent=1) + "\n")

    meta = json.loads((REPO / "thuiv1" / "v1-1" / "kernel-metadata.json").read_text())
    meta["id"] = "yocybercode/thui-v3-0"
    meta["title"] = "Thui v3.0"
    meta["code_file"] = OUT_NB.name
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n")

    owner = meta["id"].split("/")[0]
    if owner != "yocybercode":
        print(f"SELF-CHECK FAIL: kernel id owner is {owner!r}, not 'yocybercode'", file=sys.stderr)
        return 1

    print(f"built {OUT_NB.name}")
    print(f"  base            : {BASE_NB.relative_to(REPO)}")
    print(f"  cells changed   : [8] only ({len(cells)} cells total)")
    print(f"  lever           : {OLD}  ->  {NEW}")
    print(f"  probe carried   : cell 12 request_usage_probe present")
    print(f"  kernel id       : {meta['id']}")
    print(f"  in-kernel teeth : 4 asserts (180 present, 60 absent, key count 1, TOOL_STEPS 0)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
