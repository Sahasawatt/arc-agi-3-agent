#!/usr/bin/env python3
"""Prove thui-v1-1's IN-KERNEL teeth red on a mutation, before the push.

The teeth live in cell 8 of the built notebook and run on the Kaggle kernel before the
benchmark starts. Green teeth over an untested assertion attest to nothing, so this script
extracts that block verbatim from the notebook and drives it against a REAL setup command --
the one `clock-2x-v1` echoed into its own log, i.e. the exact text the bundle renders.

    python3 prove_teeth.py ~/Claude/arc-artifacts/clock2x/clock-2x-v1.log

One positive control (unmodified command must pass) and five mutations, each asserted to
have actually applied before its verdict is read. A mutation that does not apply produces a
pass that looks like a working assertion.

The corpus is machine-local; absent it this cannot be re-run, and a recorded verdict is not
a reproduction.
"""
from __future__ import annotations

import ast
import json
import re
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
NB = HERE / "taaf-thui-v1-1.ipynb"
ANCHOR = "    'LOCAL_ANALYZER_TEMPERATURE':"


def teeth_block(nb_path: Path) -> str:
    """Cell 8's rewrite chain + asserts, dedented so `command` is a plain local."""
    lines = "".join(json.loads(nb_path.read_text())["cells"][8]["source"]).splitlines(True)
    i = next(n for n, l in enumerate(lines) if l.strip().startswith("command = ("))
    j = next(n for n, l in enumerate(lines) if "taaf.kaggle: setup command" in l and n > i)
    block = textwrap.dedent("".join(lines[i:j]))
    ast.parse(block)
    return block


def real_command(log_path: Path) -> str:
    rows = json.loads(log_path.read_text(encoding="utf-8", errors="replace"))
    buf = "".join(r.get("data", "") for r in rows)
    m = re.search(r"taaf\.kaggle: setup command: (.*?\nPYSETUP\n)", buf, re.S)
    assert m, f"{log_path}: no echoed setup command"
    cmd = m.group(1)
    assert ANCHOR in cmd, "fixture does not carry the anchor -- wrong log or newer bundle"
    assert "LOCAL_ANALYZER_SEED" not in cmd, "fixture already seeded -- use an UNPINNED run"
    return cmd


def main() -> int:
    log = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else None
    assert log and log.is_file(), f"usage: {Path(__file__).name} <unpinned-run.log>"
    block, real = teeth_block(NB), real_command(log)

    ns = {"command": real}
    exec(block, ns)                                   # positive control
    out = ns["command"]
    assert out.count("'LOCAL_ANALYZER_SEED'") == 1
    assert out.index("LOCAL_ANALYZER_SEED") < out.index("LOCAL_ANALYZER_TEMPERATURE")
    print("[+] real unpinned command        -> PASS, seed injected once, before TEMPERATURE")

    mutations = [
        ("anchor moved (newer bundle)", real.replace(ANCHOR, "    'LOCAL_ANALYZER_TEMP':")),
        ("bundle already seeded", real.replace(ANCHOR, "    'LOCAL_ANALYZER_SEED': '1',\n" + ANCHOR)),
        ("temperature set to 0.0 (B31)",
         real.replace("'LOCAL_ANALYZER_TEMPERATURE': '0.6'", "'LOCAL_ANALYZER_TEMPERATURE': '0.0'")),
        ("output capped at 768 (v9)",
         real.replace("'LOCAL_ANALYZER_MAX_OUTPUT': '0'", "'LOCAL_ANALYZER_MAX_OUTPUT': '768'")),
        ("upscale raised to 8 (B23)",
         real.replace("'MULTIMODAL_UPSCALE': '4'", "'MULTIMODAL_UPSCALE': '8'")),
    ]
    dead = 0
    for label, mutated in mutations:
        assert mutated != real, f"{label}: the mutation did not apply -- its verdict means nothing"
        try:
            exec(block, {"command": mutated})
            print(f"[-] {label:32s} -> PASS   <<< TEETH ARE DEAD")
            dead += 1
        except AssertionError as e:
            print(f"[-] {label:32s} -> caught: {str(e).splitlines()[0][:70]}")
    print(f"\n{len(mutations) - dead}/{len(mutations)} mutations caught")
    return 1 if dead else 0


if __name__ == "__main__":
    raise SystemExit(main())
