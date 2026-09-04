#!/usr/bin/env python3
"""thui-stack -- the DRAW CANDIDATE: Watchara's B48 chassis + every harness arm of ours that has READ positive.

Composition rule (the only one that makes a stacked build draw-eligible): an arm enters the stack
only after its own paired public read clears the B35 floor (+1 level in >= 6 of 25 games on both
draws, vs eval/fixtures/thuiv3-pool.json). Until then the stack is a smoke artifact, never a
submission. Today (2026-09-04) NO arm has read, so the default stack is EMPTY and the build is the
B48 chassis byte-for-byte -- which is exactly what a resubmit of the standing best is.

    python3 build_notebook.py --arms=reflect,rank [--full] [--suffix=-r2] [--owner=yocybercode]

--arms selects which cell-12 payloads to chain, in order. `reflect` (B62) and `rank` (B61) both wrap
ToolAgent.analyze at class level, so chaining is wrapping the wrapper: the second arm's
`_orig_analyze` is the first arm's wrapper and every kwarg (step_env included) passes through.
`gemma` (B64) is NOT stackable here: it swaps the model and wheelhouse in cells 6/8 and must read alone.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SRC_NB = REPO / "thuiv3" / "taaf-thui-v3-0.ipynb"      # B48 chassis, always
META_SRC = REPO / "thuiv3" / "kernel-metadata.json"
OWNER = "sahasawatt"
SMOKE_GAMES = ("tr87", "sk48", "sc25")
GAME_CLOCK_S = 900
ARM_BUILDERS = {"reflect": REPO / "thui-reflect" / "build_notebook.py", "rank": REPO / "thui-rank" / "build_notebook.py"}


def _load_suffix(name: str) -> str:
    """Import the arm's builder module and take its CELL12_SUFFIX verbatim -- one source of truth per arm."""
    spec = importlib.util.spec_from_file_location(f"arm_{name}", ARM_BUILDERS[name])
    mod = importlib.util.module_from_spec(spec)
    saved = sys.argv; sys.argv = [str(ARM_BUILDERS[name])]  # the arm builders parse sys.argv at import
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.argv = saved
    suffix = mod.CELL12_SUFFIX
    assert "@" not in suffix.split("# ===")[0] or True  # placeholders are substituted inside each builder
    for ph in ("@K@", "@MAXTOK@", "@HIST@", "@VETO_P@", "@VETO_MIN_OBS@", "@VETO_PER_STEP@"):
        assert ph not in suffix, f"{name}: unsubstituted placeholder {ph}"
    return suffix


def cell0(arms: list[str], full: bool) -> str:
    what = " + ".join({"reflect": "B62 reflection memory", "rank": "B61 ranker/veto"}[a] for a in arms) or "no arm (chassis only)"
    scope = "full 25 games" if full else f"smoke: {' / '.join(SMOKE_GAMES)} at {GAME_CLOCK_S} s each — numbers meaningless, never quoted"
    return (f"# thui-stack — B48 chassis (`thui-v3-0`: thui-v1-1 + yield 180, the standing-best build) + {what}\n\n"
            f"`thui-v3-0` byte-for-byte except cell 12{'' if full else ' and cell 14'}: the listed arms' cell-12 payloads are appended in order, "
            f"each wrapping `ToolAgent.analyze` on top of the previous. {scope}. An arm is in this stack only after its own paired "
            f"public read cleared +1 level in ≥ 6 of 25 games vs `eval/fixtures/thuiv3-pool.json`; a stack with an unread arm is a "
            f"smoke artifact and not a submission. Design: `notes/B61-…`, `notes/B62-…`.\n\n"
            "Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit, Michal Tesnar, Stefano Viel) — "
            "executed unmodified from their attached dataset. This is a Knowless Crew / Thuitanium fork; none of their scores are ours.\n")


CELL14_ANCHOR = "    bm.games = _offline_games(competition_env_files)\n"


def cell14_filter() -> str:
    return ("    # thui-stack smoke: three games, at the REAL seam.\n"
            "    _SMOKE = " + repr(SMOKE_GAMES) + "\n    _n0 = len(bm.games)\n"
            "    bm.games = [g for g in bm.games if any(g.env_name.startswith(h) for h in _SMOKE)]\n"
            "    print(f\"thui-stack: smoke filter {_n0} -> {len(bm.games)} games\", flush=True)\n"
            "    assert len(bm.games) == " + str(len(SMOKE_GAMES)) + ", f\"thui-stack: expected " + str(len(SMOKE_GAMES)) + " games, got {len(bm.games)}\"\n"
            "    bm.solver.max_runtime_s_per_game = " + str(GAME_CLOCK_S) + ".0\n")


def main(arms: list[str], full: bool, slug_suffix: str, owner: str) -> None:
    for a in arms:
        assert a in ARM_BUILDERS, f"unknown arm {a!r}; known: {sorted(ARM_BUILDERS)}"
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 17, f"{SRC_NB.name}: expected 17 cells, found {len(cells)}"
    c8 = "".join(cells[8]["source"])
    assert c8.count("'LOCAL_ANALYZER_YIELD_SECONDS': '180'") == 2, "chassis is not the B48 build (yield-180 injection/assert not found twice)"
    before = ["".join(c["source"]) for c in cells]
    slug = "thui-stack-" + ("-".join(arms) if arms else "base") + ("-v1" if full else "-v0") + slug_suffix
    out_nb = HERE / f"taaf-{slug}.ipynb"

    cells[0]["source"] = cell0(arms, full).splitlines(keepends=True)
    c12 = "".join(cells[12]["source"])
    for a in arms:
        assert f"thui-{a}" not in c12, f"cell 12 already carries {a}"
        c12 += _load_suffix(a)
    if arms:
        c12 += "\n# thui-stack: composition teeth -- the analyze seam must be the LAST arm's wrapper\n"
        last = {"reflect": "_reflect_analyze", "rank": "_rank_analyze"}[arms[-1]]
        c12 += f"assert _ta.ToolAgent.analyze is {last}, 'thui-stack: outermost wrapper is not {arms[-1]}'\n"
        c12 += "print(" + repr(f"thui-stack: arms chained in order {'+'.join(arms)} on the B48 chassis") + ", flush=True)\n"
    cells[12]["source"] = c12.splitlines(keepends=True)
    if not full:
        c14 = "".join(cells[14]["source"])
        assert c14.count(CELL14_ANCHOR) == 1, "offline bm.games assignment not found once in cell 14"
        cells[14]["source"] = c14.replace(CELL14_ANCHOR, CELL14_ANCHOR + cell14_filter()).splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (x, y) in enumerate(zip(before, after)) if x != y]
    expected = [0] + ([12] if arms else []) + ([] if full else [14])
    assert changed == expected, f"cells changed {changed}, expected {expected}"
    for i in (12, 14):
        ast.parse("".join(cells[i]["source"]), filename=f"cell{i}")
    # a stack with no arms must be the chassis byte-for-byte in every code cell
    if not arms and full:
        assert all(before[i] == after[i] for i in range(1, 17)), "empty stack must not touch a code cell"

    out_nb.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(META_SRC.read_text(encoding="utf-8"))
    meta["id"] = f"{owner}/{slug}"; meta["title"] = slug; meta["code_file"] = out_nb.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"built {out_nb.name}: arms={arms} cells changed {changed}, id {meta['id']}")


if __name__ == "__main__":
    _arms = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--arms=")), "")
    _suf = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--suffix=")), "")
    _own = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), OWNER)
    main([a for a in _arms.split(",") if a], full="--full" in sys.argv, slug_suffix=_suf, owner=_own)
