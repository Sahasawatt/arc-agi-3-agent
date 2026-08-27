"""thui-v5-0 -- thui-v3-0 plus ONE change: LOCAL_ANALYZER_TEMPERATURE 0.6 -> 1.0.

THE 2x2 CELL NOBODY HAS RUN, AND WHY IT IS THE ONE WORTH A SLOT

Zero-action games are the failure mode that costs an entire game: the turn hits
LOCAL_ANALYZER_YIELD_SECONDS, step_executed is False, and the turn restarts cold at
analysis_step 1 until the per-game token budget is gone. `ft09` is the base run's
HIGHEST-scoring game and it stalled in v4-0.

The four cells, three of which are now measured (kc-arc-agi-pub
notes/zero-action-stall-answered-offline-2026-08-27.md, 0 GPU-hours):

                      temp 0.6              temp 1.0
    YIELD  60      1/25 (thui-v1-1-r2)   4/25 (thui-v4-0)
    YIELD 180      0/25 (thui-v3-0)      ??? (THIS BUILD)

  * 4/25 against 2/200 over the 225 game-runs on disk is Fisher two-sided p = 0.00156,
    so temperature moves the stall rate and that is measured.
  * 0/25 against 1/25 is Fisher p = 1.0, so whether YIELD=180 removes the stall is NOT.
  * The obvious mechanism is REFUTED: temp 1.0 made requests SHORTER and faster (median
    wall_s 64.6 s / 650 completion tokens against 101.8 s / 1,368 at 0.6) and blew the
    first-request gate LESS often (62.4% against 75.1%). Whatever drives the rate, it is
    not request duration -- so "180 s is more headroom, therefore fewer stalls" is a
    hypothesis this cell tests rather than an inference already in hand.

WHAT THIS RUN BUYS THAT NO OTHER CELL CAN

It is the only cell that separates "the knob removes the stall" from "temperature causes
it". Both readings are live and they recommend opposite things:

  * stalls near 0/25  -> YIELD=180 dominates temperature, and the yield knob is a SAFETY
    lever independent of its (null) score effect. That makes 180 the default for every
    future arm, and it makes the temperature/spread lever (B-thui-v4-0) affordable again,
    because the 49% of v4-0's drop that was stalls would not recur.
  * stalls near 4/25  -> temperature causes the stall directly, the yield knob does not
    protect against it, and the spread lever is dead in the form v4-0 tried.

ATTRIBUTION: ONE variable against thui-v3-0. The seed stays 20260825, YIELD stays 180,
TOOL_STEPS stays 0, MAX_OUTPUT stays uncapped, UPSCALE stays 4 -- all asserted below in
both directions. Base is thuiv3/taaf-thui-v3-0.ipynb, NOT duckmod and NOT v1-1, per
CLAUDE.md Versioning ("a builder's self-check must compare against the BASE the build
claims"); duckv25 shipped a tautological assert that way.

PREDICTIONS, WRITTEN BEFORE THE PUSH

  P1 VALIDITY, read FIRST and before any score. The log must echo BOTH
     'LOCAL_ANALYZER_TEMPERATURE': '1.0'  AND  'LOCAL_ANALYZER_YIELD_SECONDS': '180'
     in the setup command, and must NOT echo '0.6' or '60' for those keys. If either
     literal is wrong THE RUN IS VOID and no number in it is readable -- a silent no-op
     scores normally, which is the duckv25 shape.
  P2 THE QUESTION. Zero-action games, counted from benchmark.json history length and
     cross-checked against summary.txt actions. Prior cells: 1/25, 0/25, 4/25.
     Any value is informative; ~0 and ~4 point opposite ways.
  P3 CHUNKING. R48 measured rounds/decision 2.50 (yield 60) -> 1.68 (yield 180). If the
     budget dominates, v5-0 should sit near v3-0's 1.68 rather than v4-0's shape.
     max(req_in_turn): v3-0 reached 6 (median 4), v4-0 reached 5 (median 3).
  P4 WALL. ~2h20m, as v3-0 (2h21m) and v4-0 (2h13m). Materially longer means the clock,
     not the lever, is what moved.

  SCREEN, fixed before the run: public < 2.82 kills the build as a SCORE arm -- v4-0
  already failed that screen at temperature 1.0 and this build inherits the risk. That
  does NOT void P2. This slot is bought for the stall count, not for the mean, and the
  stall count reads whatever the score does.

  WHAT IT CANNOT ANSWER: n=1 at this setting, so a stall count of 1 or 2 separates
  nothing (0/25 vs 1/25 is already p = 1.0). Only a value near 4 or exactly 0 moves the
  needle, and even then the row must say n=1. It also cannot price the spread lever --
  a hidden draw is a max over noisy samples and one public run has no spread.
"""

from __future__ import annotations

import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
BASE_NB = REPO / "thuiv3" / "taaf-thui-v3-0.ipynb"
OUT_NB = HERE / "taaf-thui-v5-0.ipynb"
OUT_META = HERE / "kernel-metadata.json"

OLD = "'LOCAL_ANALYZER_TEMPERATURE': '0.6'"
NEW = "'LOCAL_ANALYZER_TEMPERATURE': '1.0'"

# The TEMPERATURE literal lives in the BUNDLE's setup_commands.json, not in the notebook,
# exactly like the seed and the yield -- so the build adds one more link to cell 8's
# existing .replace() chain. Anchor is the chain's closing paren before the first assert.
CHAIN_ANCHOR = '        )\n    )\n    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot"'
CHAIN_NEW = (
    '        )\n'
    '        .replace(\n'
    '            "\'LOCAL_ANALYZER_TEMPERATURE\': \'0.6\'",\n'
    '            "\'LOCAL_ANALYZER_TEMPERATURE\': \'1.0\'",\n'
    '        )\n'
    '    )\n'
    '    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot"'
)

OLD_PRINT = (
    'print("thui-v3-0: YIELD_SECONDS 60 -> 180 (B47/R44); seed=20260825, temperature untouched", flush=True)'
)
NEW_PRINT = (
    'print("thui-v5-0: v3-0 + TEMPERATURE 0.6 -> 1.0; YIELD stays 180, seed=20260825", flush=True)'
)

# v3-0 inherited v1-1's tooth asserting temperature is STILL 0.6. This build moves it, so
# that assert would kill the kernel -- it is replaced by this build's own three, which
# assert both poles (new value present, old value absent, key not duplicated).
TOOTH_OLD = (
    '    assert "\'LOCAL_ANALYZER_TEMPERATURE\': \'0.6\'" in command, (\n'
    '        "thui-v1-1 TEETH FAIL: temperature is not 0.6 -- this arm must not touch it"\n'
    '    )\n'
)
TOOTH_NEW = (
    '    # thui-v5-0 TEETH, in-kernel, before the benchmark starts. The TEMPERATURE value IS\n'
    '    # this build: if the anchor moved in a newer bundle the replace is a silent no-op and\n'
    '    # the run would score normally while measuring nothing (the duckv25 shape).\n'
    '    assert "\'LOCAL_ANALYZER_TEMPERATURE\': \'1.0\'" in command, (\n'
    '        "thui-v5-0 TEETH FAIL: temperature injection missed -- "\n'
    '        "\\"\'LOCAL_ANALYZER_TEMPERATURE\': \'0.6\'\\" is not in this bundle\'s setup command"\n'
    '    )\n'
    '    assert "\'LOCAL_ANALYZER_TEMPERATURE\': \'0.6\'" not in command, (\n'
    '        "thui-v5-0 TEETH FAIL: the old 0.6 value survives -- two values would race"\n'
    '    )\n'
    '    assert command.count("\'LOCAL_ANALYZER_TEMPERATURE\'") == 1, (\n'
    '        "thui-v5-0 TEETH FAIL: temperature key present more than once"\n'
    '    )\n'
)

# Levers this build must NOT cross. Each already cost a slot or is the base's own variable.
MUST_HOLD = [
    ("'LOCAL_ANALYZER_YIELD_SECONDS': '180'", "the base's lever -- v5-0 is v3-0 PLUS temperature"),
    ("'LOCAL_ANALYZER_SEED': '20260825'", "the v1-1 seed pin rides along untouched"),
    ("'LOCAL_ANALYZER_TOOL_STEPS': '0'", "B47 measured a step cap inert; do not cross it"),
    ("'LOCAL_ANALYZER_MAX_OUTPUT': '0'", "v9 scored 0.22 when output was capped at 768"),
    ("'MULTIMODAL_UPSCALE': '4'", "B23 measured upscale in-noise; v10 exact"),
]


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
    if src.count(TOOTH_OLD) != 1:
        print(f"FAIL: expected exactly one v1-1 temperature tooth in cell 8, "
              f"found {src.count(TOOTH_OLD)} -- base drifted", file=sys.stderr)
        return 1
    if OLD_PRINT not in src:
        print("FAIL: the v3-0 print line is not in cell 8 -- base is not v3-0", file=sys.stderr)
        return 1
    if "'LOCAL_ANALYZER_YIELD_SECONDS': '180'" not in src:
        print("FAIL: cell 8 does not carry the 180 yield -- base is not v3-0", file=sys.stderr)
        return 1

    new_src = (src
               .replace(CHAIN_ANCHOR, CHAIN_NEW)
               .replace(TOOTH_OLD, TOOTH_NEW)
               .replace(OLD_PRINT, NEW_PRINT))
    cells[8]["source"] = new_src.splitlines(keepends=True)

    # ---- self-check AGAINST THE BASE THIS BUILD CLAIMS, naming what must differ ----
    bad = []
    for i, (b, o) in enumerate(zip(base["cells"], cells)):
        bs, os_ = "".join(b.get("source", [])), "".join(o.get("source", []))
        if i == 8:
            if bs == os_:
                bad.append("cell 8 is UNCHANGED -- the whole build is a no-op")
            if CHAIN_NEW not in os_:
                bad.append("cell 8 does not carry the new .replace() link -- the lever "
                           "would never reach the bundle command")
            if TOOTH_NEW not in os_:
                bad.append("cell 8 does not carry this build's teeth")
            if TOOTH_OLD in os_:
                bad.append("the v1-1 tooth asserting temperature is 0.6 SURVIVES -- "
                           "the kernel would die on its own assert")
            if NEW_PRINT not in os_:
                bad.append("cell 8 still announces itself as v3-0")
        elif bs != os_:
            bad.append(f"cell {i} differs and must not -- this build changes cell 8 ONLY")
    if len(base["cells"]) != len(cells):
        bad.append("cell count changed")

    c8 = "".join(cells[8].get("source", []))
    for literal, why in MUST_HOLD:
        if literal not in c8:
            bad.append(f"cell 8 lost {literal} -- {why}")

    # cell 12 is the request_usage_probe; it is the instrument P2 and P3 are read from
    c12 = "".join(cells[12].get("source", []))
    if "req_in_turn" not in c12:
        bad.append("cell 12 lost the request_usage_probe -- nothing would measure the change")

    # compile ONLY the cell this build changed. Notebook cells legally carry top-level
    # `await` (cell 14 does), which compile() rejects -- so a blanket sweep fails on cells
    # the build never touched and says nothing about the edit.
    try:
        compile(c8, "<cell 8>", "exec")
    except SyntaxError as e:
        bad.append(f"cell 8 does not compile: {e}")

    if bad:
        for b in bad:
            print(f"SELF-CHECK FAIL: {b}", file=sys.stderr)
        return 1

    OUT_NB.write_text(json.dumps(out, indent=1) + "\n")

    meta = json.loads((REPO / "thuiv3" / "kernel-metadata.json").read_text())
    meta["id"] = "yocybercode/thui-v5-0"
    meta["title"] = "Thui v5.0"
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
    print(f"  held constant   : {len(MUST_HOLD)} literals asserted present")
    print(f"  probe carried   : cell 12 request_usage_probe present")
    print(f"  kernel id       : {meta['id']}")
    print(f"  in-kernel teeth : 3 temperature asserts + v3-0's 4 yield asserts inherited")
    return 0


if __name__ == "__main__":
    sys.exit(build())
