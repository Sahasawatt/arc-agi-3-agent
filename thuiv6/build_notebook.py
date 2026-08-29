"""thui-v6-0 -- B54's knob: LOCAL_ANALYZER_CONTEXT_WINDOW 32768 -> 49152, and nothing else.

WHY THIS LEVER (notes/R51-the-window-is-half-what-the-server-serves.md, 0 slots, 0 GPU):
  * every run of this campaign echoes, in its own setup, a server that accepts 65,536 tokens
    and an agent configured for 32,768.  `32768` is `tool_agent.py`'s own default
    (`_get_env_int("LOCAL_ANALYZER_CONTEXT_WINDOW", 32768)`) copied into the setup script --
    nobody chose it for the 27B.
  * the trim is ACTIVE, not theoretical: over 7,147 usage rows from the six probe-carrying
    runs, `prompt_tokens` sits at median ~22k / p90 ~25k / max 30.9k against a derived
    `context_budget_tokens: 31744` printed by all 935 ANALYZER STATUS blocks, while
    `history_messages` stays flat at median 18 / max 36 across games that run 40-80 turns.
    Old evidence falls off the back every turn.
  * so the agent is discarding history the server would have carried for free.

WHY 49152 AND NOT 65536.  `max_model_len` bounds prompt PLUS completion, not the prompt
alone.  At a 65,536 window the prompt budget is 64,512, and the completion tail measured over
9,147 requests is p95 5,148 / p99 8,325 / max 11,989 -- so 64,512 + p99 = 72,837, past the
server's ceiling.  Sizing it properly: budget + worst observed completion <= 65,536 gives
budget <= 53,547, window <= 54,571.  49,152 takes it with room: prompt budget 48,128 (+51.6%
over today) and 48,128 + 11,989 = 60,117, still 5.4k under the ceiling.  Retainable history
rises roughly 1.5x, not 2.9x.

BASE IS thui-v1-1, NOT duckmod.  Per CLAUDE.md Versioning: "A builder's self-check must
compare against the BASE the build claims, not against SRC_NB" -- duckv25 shipped a
tautological assert that way.  v1-1 is v10 + the request_usage_probe (cell 12) + the seed
pin, its two runs scored 5.24 and 4.33, so this build is ONE variable against a two-run
baseline and it carries the probe that measures the very quantity being moved.

THE ANCHOR IS CONFIRMED FROM TWO INDEPENDENT SOURCES, not from a log echo:
  * tracked generator `localrig/ARC3-Inference/inference/framework/kaggle.py:161` emits
    `ANALYZER_CONTEXT_WINDOW = __ANALYZER_CONTEXT_WINDOW__`, substituted at :100 with
    `repr(int(...))` -- a bare integer, no quotes.
  * the bundle on disk carries `ANALYZER_CONTEXT_WINDOW = 32768` exactly once, and `32768`
    itself occurs exactly once in the whole 10,076-char command (negative control: 0).

WHAT THIS DOES NOT CLAIM.  The size of the lever is not established, only its mechanism.
thui-v3-0 gave the model 3x thinking time per turn and bought nothing, and "more context" is
that lever's cousin; long-context degradation on a 27B is real, so retained history may be
noise rather than signal.  A single public run cannot rank this (B35 floor ~ +4).  The
STRUCTURAL oracle is what this build is actually for, and cell 12 measures it: `prompt_tokens`
must climb toward 48,128 and `history_messages` must rise by roughly half -- and
`prompt + completion` must stay under 65,536 on every request (worst case observed today is
39,382; at the new budget it would be 60,117).  If those do not move, the knob did not
deliver, whatever the score says.
"""

from __future__ import annotations

import ast
import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
BASE_NB = REPO / "thuiv1" / "v1-1" / "taaf-thui-v1-1.ipynb"
OUT_NB = HERE / "taaf-thui-v6-0.ipynb"
OUT_META = HERE / "kernel-metadata.json"

OLD = "ANALYZER_CONTEXT_WINDOW = 32768"
NEW = "ANALYZER_CONTEXT_WINDOW = 49152"

# The window literal lives in the BUNDLE's setup_commands.json, not in the notebook -- so the
# build adds a link to cell 8's existing .replace() chain, exactly as the v1-1 seed pin and
# the v3-0 yield pin do.  Anchor is the chain's closing paren followed by the first assert.
CHAIN_ANCHOR = '        )\n    )\n    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot"'
CHAIN_NEW = (
    '        )\n'
    '        .replace(\n'
    '            "ANALYZER_CONTEXT_WINDOW = 32768",\n'
    '            "ANALYZER_CONTEXT_WINDOW = 49152",\n'
    '        )\n'
    '    )\n'
    '    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot"'
)

OLD_PRINT = 'print("thui-v1-1: sampler pinned, seed=20260825, temperature untouched", flush=True)'
NEW_PRINT = (
    'print("thui-v6-0: CONTEXT_WINDOW 32768 -> 49152 (B54/R51); seed=20260825, '
    'yield 60 and temperature untouched", flush=True)'
)

# The teeth. Appended to cell 8 inside the setup loop, so they run IN-KERNEL before the
# benchmark starts -- a silent no-op would otherwise score normally while measuring nothing.
TEETH = '''    # thui-v6-0 TEETH, in-kernel, before the benchmark starts. The window IS this build:
    # if the anchor moved in a newer bundle the replace is a silent no-op and the run would
    # score normally while measuring nothing (the duckv25 shape).
    assert "ANALYZER_CONTEXT_WINDOW = 49152" in command, (
        "thui-v6-0 TEETH FAIL: window injection missed -- "
        "\\"ANALYZER_CONTEXT_WINDOW = 32768\\" is not in this bundle's setup command"
    )
    assert "ANALYZER_CONTEXT_WINDOW = 32768" not in command, (
        "thui-v6-0 TEETH FAIL: the old 32768 value survives -- two values would race"
    )
    assert command.count("ANALYZER_CONTEXT_WINDOW = ") == 1, (
        "thui-v6-0 TEETH FAIL: the window is assigned more than once"
    )
    assert "'LOCAL_ANALYZER_CONTEXT_WINDOW': str(ANALYZER_CONTEXT_WINDOW)" in command, (
        "thui-v6-0 TEETH FAIL: the assignment no longer reaches the analyzer env -- the "
        "lever would be editing a dead variable"
    )
    assert "VLLM_MAX_MODEL_LEN = 65536" in command, (
        "thui-v6-0 TEETH FAIL: the server ceiling is not 65536, so 49152 is unsized -- "
        "max_model_len bounds prompt PLUS completion (budget 48128 + worst observed "
        "completion 11989 = 60117, which only fits under a 65536 ceiling)"
    )
    assert "'LOCAL_ANALYZER_YIELD_SECONDS': '60'" in command, (
        "thui-v6-0 TEETH FAIL: YIELD must stay 60 -- this arm is ONE lever against v1-1 "
        "and must not cross B47's variable"
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
        print("FAIL: cell 8 already carries a CONTEXT_WINDOW literal -- base is not v1-1",
              file=sys.stderr)
        return 1
    if OLD_PRINT not in src:
        print("FAIL: the v1-1 print line is not in cell 8 -- base drifted", file=sys.stderr)
        return 1

    new_src = src.replace(CHAIN_ANCHOR, CHAIN_NEW).replace(OLD_PRINT, NEW_PRINT)
    # Teeth go immediately before the (now renamed) print line. NEW_PRINT carries no indent
    # and the line it replaces already sits at 4 spaces, so TEETH's first line is lstripped
    # -- otherwise it lands at 8 and the block reads as if it were nested (v3-0 has that).
    new_src = new_src.replace(
        NEW_PRINT, TEETH.rstrip("\n").lstrip() + "\n    " + NEW_PRINT.lstrip()
    )
    cells[8]["source"] = new_src.splitlines(keepends=True)

    # ---- self-check AGAINST THE BASE THIS BUILD CLAIMS, naming what must differ ----
    bad = []
    for i, (b, o) in enumerate(zip(base["cells"], cells)):
        bs, os_ = "".join(b.get("source", [])), "".join(o.get("source", []))
        if i == 8:
            if bs == os_:
                bad.append("cell 8 is UNCHANGED -- the whole build is a no-op")
            if NEW not in os_:
                bad.append("cell 8 does not carry the 49152 value")
            if CHAIN_NEW not in os_:
                bad.append("cell 8 does not carry the new .replace() link -- the lever "
                           "would never reach the bundle command")
            if os_.count(OLD) < 1:
                bad.append("cell 8 never names the 32768 value, so nothing can be replaced")
            if "'LOCAL_ANALYZER_YIELD_SECONDS': '180'" in os_:
                bad.append("cell 8 carries a YIELD rewrite -- this build must cross no "
                           "second variable")
        elif bs != os_:
            bad.append(f"cell {i} differs and must not -- this build changes cell 8 ONLY")
    if len(base["cells"]) != len(cells):
        bad.append("cell count changed")

    # cell 12 is the request_usage_probe and is the instrument for the structural oracle
    # (prompt_tokens toward 48,128; prompt+completion under 65,536); it must ride untouched
    c12 = "".join(cells[12].get("source", []))
    if "req_in_turn" not in c12:
        bad.append("cell 12 lost the request_usage_probe -- nothing would measure the change")

    # the splice is string surgery, so it can emit python that does not parse -- which the
    # kernel discovers at cell 8, after it has already paid for cells 0-7 on a GPU.
    for i, c in enumerate(cells):
        if c.get("cell_type") != "code":
            continue
        try:
            ast.parse("".join(c.get("source", [])))
        except SyntaxError as e:
            bad.append(f"cell {i} does not parse after the build: {e}")

    if bad:
        for b in bad:
            print(f"SELF-CHECK FAIL: {b}", file=sys.stderr)
        return 1

    OUT_NB.write_text(json.dumps(out, indent=1) + "\n")

    meta = json.loads((REPO / "thuiv1" / "v1-1" / "kernel-metadata.json").read_text())
    meta["id"] = "yocybercode/thui-v6-0"
    meta["title"] = "Thui v6.0"
    meta["code_file"] = OUT_NB.name
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n")

    owner = meta["id"].split("/")[0]
    if owner != "yocybercode":
        print(f"SELF-CHECK FAIL: kernel id owner is {owner!r}, not 'yocybercode'",
              file=sys.stderr)
        return 1
    # the solo-probe lesson: an allowlist metadata builder silently dropped machine_shape and
    # Kaggle handed the kernel a Tesla P100.  Inheritance is the fix; assert it landed.
    if meta.get("machine_shape") != "NvidiaRtxPro6000":
        print(f"SELF-CHECK FAIL: machine_shape is {meta.get('machine_shape')!r}, "
              f"not 'NvidiaRtxPro6000'", file=sys.stderr)
        return 1

    print(f"built {OUT_NB.name}")
    print(f"  base            : {BASE_NB.relative_to(REPO)}")
    print(f"  cells changed   : [8] only ({len(cells)} cells total)")
    print(f"  lever           : {OLD}  ->  {NEW}")
    print(f"  prompt budget   : 31744 -> 48128 (+51.6%); worst case 48128+11989=60117 < 65536")
    print(f"  probe carried   : cell 12 request_usage_probe present")
    print(f"  kernel id       : {meta['id']}  ({meta['machine_shape']})")
    print(f"  in-kernel teeth : 6 asserts (49152 present, 32768 absent, one assignment, "
          f"reaches env, ceiling 65536 intact, YIELD still 60)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
