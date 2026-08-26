"""Build solo/taaf-solo-<game>.ipynb -- duckv10 plus ONE change: only one game plays (B41).

DIAGNOSTIC ONLY. This build must never be submitted; the injected code asserts that itself.

The change goes into CELL 14, not the documented cell-11/12 hook. B41's ticket said cell 12,
which would have been a silent no-op: cell 14 reassigns bm.games on both branches, after cell 12
has run. The injection is anchored on the exact offline assignment line and placed between it and
bm.run(), which is the only window where a filter survives.

There are TWO splices. The filter goes in the `else` branch (the only place bm.games survives);
the never-submit guard goes ABOVE `if TRUE_SUBMISSION:` at module level. Putting them together --
which the first build did -- makes the guard unreachable in the one case it names, because the
else branch is the TRUE_SUBMISSION=False path.

Self-check policy, per CLAUDE.md Versioning: assert against the BASE this build claims (duckv10),
never against SRC_NB, and name the block that must be ABSENT. duckv25 shipped a run advertised as
"v10 + seed" that was duckmod + seed because its assert compared a cell against the same source
the builder never touches.
"""
import argparse
import ast
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
V10_NB = REPO / "duckv10" / "taaf-duck-v10.ipynb"
PATCH = REPO / "solo" / "solo_patch.py"
GUARD = REPO / "solo" / "solo_guard.py"

# TWO splices, because the two blocks need different reachability.
#
# The FILTER must sit in cell 14's `else` branch: that is the only place bm.games survives being
# reassigned. The GUARD must NOT sit there -- spliced into the else branch it is skipped whenever
# TRUE_SUBMISSION is true, which is the only case it exists for. The first build of this probe put
# them together and the guard was dead: with the if/else intact, TRUE_SUBMISSION=True took the
# gateway branch and left bm.games holding 110 live games, no exception. So the guard goes above
# the branch, where both paths pass through it.
ANCHOR = "    bm.games = _offline_games(competition_env_files)\n"   # filter goes after this
ANCHOR_IF = "if TRUE_SUBMISSION:\n"                                # guard goes before this
# Must NOT be in the output: duckmod's patch block, the marker duckv25 shipped by accident.
DUCKMOD_MARKER = "duckmod: inject HUD auto-flag"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game", required=True, help="game id prefix, e.g. sk48")
    ap.add_argument("--owner", required=True, help="Kaggle account for the kernel id")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    assert args.game.isalnum() and len(args.game) == 4, (
        f"--game {args.game!r}: expected a 4-character alphanumeric prefix like 'sk48'"
    )
    out_nb = Path(args.out) if args.out else REPO / "solo" / f"taaf-solo-{args.game}.ipynb"

    nb = json.loads(V10_NB.read_text(encoding="utf-8"))
    v10 = json.loads(V10_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]

    patch = PATCH.read_text(encoding="utf-8")
    assert "__TARGET__" in patch, "solo_patch.py lost its __TARGET__ placeholder"
    patch = patch.replace("__TARGET__", args.game)

    guard = GUARD.read_text(encoding="utf-8")
    assert "assert not TRUE_SUBMISSION" in guard, "solo_guard.py lost its never-submit assert"
    assert "__TARGET__" not in guard, "the guard must not need substitution"

    src14 = cells[14]["source"]
    assert isinstance(src14, str), "cell 14 source is not a plain string; the splice assumes it is"
    assert src14.count(ANCHOR) == 1, (
        f"cell 14 does not contain the offline-assignment anchor exactly once "
        f"(found {src14.count(ANCHOR)}) -- a newer bundle moved it; re-read cell 14 before building"
    )
    assert src14.count(ANCHOR_IF) == 1, (
        f"cell 14 does not contain `if TRUE_SUBMISSION:` at column 0 exactly once "
        f"(found {src14.count(ANCHOR_IF)}) -- a newer bundle restructured the branch"
    )
    indented = "".join(("    " + ln if ln.strip() else ln) for ln in patch.splitlines(True))
    out14 = src14.replace(ANCHOR, ANCHOR + "\n" + indented + "\n")
    # guard first in the file, so it runs before the branch it protects. No indent: module level.
    out14 = out14.replace(ANCHOR_IF, guard + "\n" + ANCHOR_IF)
    cells[14]["source"] = out14
    # cell 14 ends in a top-level `await bm.run(...)`, which Jupyter accepts and plain compile()
    # does not -- the other builders here never hit this because they patch cell 12.
    compile(cells[14]["source"], "<cell14>", "exec", ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)

    # ---- self-check, against duckv10 and by naming what must be absent -------------------
    diff = [i for i, (a, b) in enumerate(zip(cells, v10["cells"]))
            if a["source"] != b["source"]]
    assert diff == [14], f"expected cell 14 to be the ONLY change, got {diff}"

    o14 = cells[14]["source"]
    # The anchor must still occur exactly ONCE after the splice. If the injected text quotes it
    # (a comment repeating the assignment verbatim did, until 2026-08-26), every index() below
    # silently measures the copy instead of the code and the placement asserts pass for the
    # wrong reason. prove_teeth.py's placement mutation is what caught it.
    assert o14.count(ANCHOR) == 1, (
        f"the anchor occurs {o14.count(ANCHOR)} times after the splice; the injected block must "
        f"not contain a verbatim copy of it, or the placement checks measure the wrong occurrence"
    )
    assert f'_SOLO_TARGET = "{args.game}"' in o14, "the target was not substituted into cell 14"
    assert o14.count("assert not TRUE_SUBMISSION") == 1, "the never-submit guard is missing"
    # ...and it has to be REACHABLE. Column 0 and above the branch, or it is skipped in the one
    # case it names. Asserted on the built text rather than trusted from the splice above.
    _guard_line = next(ln for ln in o14.splitlines() if "assert not TRUE_SUBMISSION" in ln)
    assert not _guard_line.startswith(" "), (
        f"the never-submit guard is indented ({_guard_line[:40]!r}) -- it is inside a branch and "
        f"will not run when TRUE_SUBMISSION is true, which is the only case it is for"
    )
    assert o14.count(ANCHOR_IF) == 1, (
        f"`if TRUE_SUBMISSION:` occurs {o14.count(ANCHOR_IF)} times after the splice; the guard "
        f"must not contain a verbatim copy of it, or the ordering check below measures the copy"
    )
    assert o14.index("assert not TRUE_SUBMISSION") < o14.index(ANCHOR_IF), (
        "the never-submit guard sits BELOW `if TRUE_SUBMISSION:` -- both branches must pass "
        "through it"
    )
    assert o14.count("bm.games = [_g for _g in _solo_before") == 1, "the filter is missing"
    assert o14.index(ANCHOR) < o14.index("_solo_before = list(bm.games)"), (
        "the filter runs BEFORE the offline assignment -- it would be overwritten"
    )
    assert o14.index("_solo_before = list(bm.games)") < o14.index("await bm.run("), (
        "the filter runs AFTER bm.run() -- it would never take effect"
    )
    assert DUCKMOD_MARKER not in o14, f"duckmod block leaked into cell 14 ({DUCKMOD_MARKER!r})"
    for idx in (6, 8, 12):
        assert cells[idx]["source"] == v10["cells"][idx]["source"], (
            f"cell {idx} differs from duckv10 -- this build claims v10 exact outside cell 14"
        )

    out_nb.parent.mkdir(parents=True, exist_ok=True)
    out_nb.write_text(json.dumps(nb, indent=1), encoding="utf-8")

    meta = {
        "id": f"{args.owner}/taaf-solo-{args.game}",
        "title": f"TAAF solo {args.game}",
        "code_file": out_nb.name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": False,
    }
    src_meta = V10_NB.parent / "kernel-metadata.json"
    if src_meta.is_file():
        base = json.loads(src_meta.read_text(encoding="utf-8"))
        for key in ("dataset_sources", "competition_sources", "kernel_sources", "model_sources"):
            if key in base:
                meta[key] = base[key]
    (out_nb.parent / f"kernel-metadata-{args.game}.json").write_text(
        json.dumps(meta, indent=1), encoding="utf-8"
    )

    print(f"wrote {out_nb} ({out_nb.stat().st_size} bytes)")
    print(f"  cells changed vs duckv10: {diff}  (cell 14 only)")
    print(f"  target {args.game!r} substituted; never-submit guard at column 0 ABOVE "
          f"`if TRUE_SUBMISSION:`; filter sits between the offline assignment and bm.run()")
    print(f"  cells 6/8/12 byte-identical to duckv10; duckmod marker absent")
    print(f"  metadata id: {meta['id']}")


if __name__ == "__main__":
    main()
