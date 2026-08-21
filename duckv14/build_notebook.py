"""Build duckv14/taaf-duck-v14.ipynb — v10 plus ONE flag: --kv-cache-dtype fp8.

Tests the R19 hypothesis and nothing else. v10's own vLLM log states
`GPU KV cache size: 199,136 tokens` and `Maximum concurrency for 65,536 tokens per
request: 11.32x` while the harness runs 25 games — a 2.2x oversubscription. The
prefix-cache hit rate duly decays 63.8% -> 23.2% across the run, decode throughput
falls with it (392 -> 311-341 tok/s), and R19 lane A found 7 of 18 zero-score
game-runs dying in a re-prefill/yield spiral (`lf52`-A executed 0 steps in 72
attempts). fp8 KV roughly doubles tokens-per-byte, taking the stated concurrency
capacity to ~22.6x — the first value that covers 25 games.

Everything else is v10 byte-for-byte, including the UNCAPPED output: v9 proved a
768-token ceiling truncates the tool call carrying the action (score 0.22).

Falsifiable, per R19 section 3: prefix hit rate should not decay to 23%; `lf52` and
`tr87` should execute a non-zero number of actions; the low-vs-high-prefill decode gap
(452.5 vs 321.9 tok/s) should narrow; the `r11l`/`sk48` low-tok/s outliers (6.42 / 7.30
vs the fleet's 13.2-13.5) should disappear.

Run:  python duckv14/build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_NB = REPO / "duckmod" / "taaf-duck-mod.ipynb"
OUT_NB = REPO / "duckv14" / "taaf-duck-v14.ipynb"

OLD_SHARE = "jeroencottaar/taaf-kaggle-source-share"
NEW_SHARE = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
OLD_DS = "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot"
NEW_DS = "jakobbrggen/qwen3-8-27b-fp8-hf-snapshot"

# The vLLM launch args are a Python list literal inside the bundle's setup command.
# Anchor on the prefix-caching flag and inject the KV dtype right after it.
#
# These two constants are the SINGLE source of truth: NEW_LOOP below embeds them via
# json.dumps (which emits a valid Python string literal), and the teeth in main()
# exercise the same pair. An earlier draft spelled the substitution a second time
# inside NEW_LOOP, so the teeth proved a parallel implementation nobody ran — caught
# by the review-fanout verify pass on bad283a.
KV_ANCHOR = "        '--enable-prefix-caching',\n"
KV_INJECT = (
    "        '--enable-prefix-caching',\n"
    "        '--kv-cache-dtype',\n"
    "        'fp8',\n"
)

OLD_LOOP = """for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    print(f"taaf.kaggle: setup command: {command}", flush=True)"""

# Built, not hand-written, so the anchor/injection text cannot drift from the teeth.
NEW_LOOP = '''_kv_injected = False
for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):
    # duckv14: v10's model swap (R12 seam) + ONE new flag, --kv-cache-dtype fp8.
    # NO output cap - v9 proved a 768-token ceiling truncates the tool call that
    # carries the action itself.
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
    _kv_anchor = ''' + json.dumps(KV_ANCHOR) + '''
    _kv_inject = ''' + json.dumps(KV_INJECT) + '''
    if _kv_anchor in command:
        assert command.count(_kv_anchor) == 1, "duckv14: prefix-caching anchor is not unique"
        assert "'--kv-cache-dtype'" not in command, "duckv14: kv-cache-dtype already present upstream"
        command = command.replace(_kv_anchor, _kv_inject)
        _kv_injected = True
        print("taaf.kaggle: duckv14 injected --kv-cache-dtype fp8", flush=True)
    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot" not in command, "duckv14: model slug rewrite missed"
    assert "Qwen3.6-27B-FP8" not in command, "duckv14: served-name rewrite missed"
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '0'" in command, "duckv14: output must stay UNCAPPED"
    print(f"taaf.kaggle: setup command: {command}", flush=True)

# Fail LOUDLY rather than silently running a v10-identical experiment. Without this,
# a re-versioned bundle that reformatted its vLLM arg list would produce v10-shaped
# numbers that read as "R19 hypothesis refuted" when the flag never landed at all.
assert _kv_injected, (
    "duckv14: --kv-cache-dtype was NEVER injected - the bundle's launch args no longer "
    "match KV_ANCHOR. This run would silently be a v10 rerun; fix the anchor before "
    "reading any result as evidence about the R19 hypothesis."
)'''

CELL12 = (
    "# duckv14: stock anim bundle + Qwen3.8, output UNCAPPED, identical to v10 except\n"
    "# the vLLM server now runs --kv-cache-dtype fp8 (see duckv14/build_notebook.py\n"
    "# and results/wayfinder/R19-binding-constraint.md).\n"
    'print("duckv14: anim bundle + Qwen3.8, UNCAPPED, KV cache dtype fp8")\n'
)


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))

    c6 = "".join(nb["cells"][6]["source"])
    assert OLD_DS in c6 and OLD_SHARE in c6, "cell 6: expected dataset refs not found"
    nb["cells"][6]["source"] = c6.replace(OLD_SHARE, NEW_SHARE).replace(OLD_DS, NEW_DS)

    c8 = "".join(nb["cells"][8]["source"])
    assert OLD_LOOP in c8, "cell 8: expected setup loop not found"
    nb["cells"][8]["source"] = c8.replace(OLD_LOOP, NEW_LOOP)

    nb["cells"][12]["source"] = CELL12

    OUT_NB.parent.mkdir(parents=True, exist_ok=True)
    OUT_NB.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"wrote {OUT_NB} ({OUT_NB.stat().st_size} bytes)")

    # --- self-check: same three cells as v10, plus the one new flag ---
    src = json.loads(SRC_NB.read_text(encoding="utf-8"))
    out = json.loads(OUT_NB.read_text(encoding="utf-8"))
    diff = [i for i in range(len(src["cells"])) if src["cells"][i]["source"] != out["cells"][i]["source"]]
    assert diff == [6, 8, 12], f"unexpected diff cells: {diff}"

    o6 = "".join(out["cells"][6]["source"])
    o8 = "".join(out["cells"][8]["source"])
    assert NEW_SHARE in o6 and NEW_DS in o6 and OLD_SHARE not in o6 and OLD_DS not in o6
    assert "Qwen3.8-27B-FP8" in o8
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '768'" not in o8, "v14 must not cap output"
    assert "--kv-cache-dtype" in o8, "v14: KV dtype injection missing from cell 8"
    # The generated cell must carry the SAME constants the teeth below exercise —
    # this is what makes the teeth evidence about the code that actually runs.
    assert json.dumps(KV_ANCHOR) in o8, "v14: cell 8 does not embed KV_ANCHOR"
    assert json.dumps(KV_INJECT) in o8, "v14: cell 8 does not embed KV_INJECT"
    assert "_kv_injected" in o8, "v14: cell 8 is missing the did-it-fire guard"

    # --- the anchor, checked against the REAL artifact rather than a fixture ---
    # R13 recorded that the anim bundle v14 mounts has the same SHA-256 as this local
    # copy, so this is the launch command the Kaggle run will actually rewrite.
    bundle = REPO / "duck" / "bundle" / "setup_commands.json"
    if bundle.exists():
        cmds = json.loads(bundle.read_text(encoding="utf-8"))
        hits = sum(c.count(KV_ANCHOR) for c in cmds)
        assert hits == 1, f"anchor appears {hits} times in the real bundle, expected exactly 1"
        assert not any("--kv-cache-dtype" in c for c in cmds), "bundle already sets kv-cache-dtype"
        print(f"anchor check OK against {bundle} ({len(cmds)} command(s), 1 anchor)")
    else:
        print(f"WARNING: {bundle} absent - anchor NOT checked against a real launch command")

    # --- teeth: run the real substitution, on the same constants cell 8 embeds ---
    def inject(cmd: str) -> str:
        return cmd.replace(KV_ANCHOR, KV_INJECT) if KV_ANCHOR in cmd else cmd

    sample = (
        "    cmd = [\n"
        "        'vllm.entrypoints.openai.api_server',\n"
        "        '--enable-prefix-caching',\n"
        "        '--max-model-len',\n"
        "    ]\n"
    )
    got = inject(sample)
    assert "'--kv-cache-dtype',\n        'fp8',\n" in got, "teeth: injection did not fire"
    assert got.index("'--kv-cache-dtype'") > got.index("'--enable-prefix-caching'"), "teeth: wrong order"
    assert got.count("'--enable-prefix-caching'") == 1, "teeth: anchor duplicated"
    assert inject("no flags here\n") == "no flags here\n", "teeth: fired on an unrelated command"
    # and the guard has to be reachable: an anchorless corpus must NOT set the flag
    assert inject("no flags here\n").find("--kv-cache-dtype") == -1, "teeth: flag leaked without anchor"

    print("self-check OK: cells [6, 8, 12]; anim bundle + 3.8, no cap, KV fp8, fire-guard armed")


if __name__ == "__main__":
    main()
