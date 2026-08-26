"""Build solo/taaf-solo-<game>.ipynb -- duckv10 plus ONE change: only one game plays (B41).

DIAGNOSTIC ONLY. This build must never be submitted; the injected code asserts that itself.

The change goes into CELL 14, not the documented cell-11/12 hook. B41's ticket said cell 12,
which would have been a silent no-op: cell 14 reassigns bm.games on both branches, after cell 12
has run. The injection is anchored on the exact offline assignment line and placed between it and
bm.run(), which is the only window where a filter survives.

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

# The line cell 14 uses to build the offline game list. The filter goes directly after it.
ANCHOR = "    bm.games = _offline_games(competition_env_files)\n"
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

    src14 = cells[14]["source"]
    assert isinstance(src14, str), "cell 14 source is not a plain string; the splice assumes it is"
    assert src14.count(ANCHOR) == 1, (
        f"cell 14 does not contain the offline-assignment anchor exactly once "
        f"(found {src14.count(ANCHOR)}) -- a newer bundle moved it; re-read cell 14 before building"
    )
    indented = "".join(("    " + ln if ln.strip() else ln) for ln in patch.splitlines(True))
    cells[14]["source"] = src14.replace(ANCHOR, ANCHOR + "\n" + indented + "\n")
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
    assert o14.count("bm.games = [_g for _g, _i in zip(_solo_before, _solo_ids)") == 1, (
        "the filter is missing"
    )
    # The filter must key on env_name. taaf.game.Game sets game_id = "" until _start_game(),
    # so a game_id prefix test matches NOTHING at cell-14 time -- measured, it cost a 20-minute
    # Kaggle run (sahasawatt/taaf-solo-sk48 v2, 2026-08-26).
    assert 'getattr(_g, "env_name", None)' in o14, (
        "the filter no longer reads env_name; a pre-start game_id is the empty string and the "
        "prefix test would match 0 of 25"
    )
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

    # START from duckv10's metadata and override only what must change. Building a fresh dict
    # from a list of keys to copy DROPS whatever the list does not name, silently -- and the
    # first version of this dropped `machine_shape: NvidiaRtxPro6000`, so Kaggle handed the
    # kernel a Tesla P100 and the setup script died on
    #   AssertionError: Expected GPU type 'rtx-pro-6000', found ['Tesla P100-PCIE-16GB']
    # 12 seconds in (sahasawatt/taaf-solo-sk48 v1, 2026-08-26). `docker_image` is in the same
    # boat. An allowlist is the wrong shape for "same as the thing that works, but renamed".
    src_meta = V10_NB.parent / "kernel-metadata.json"
    assert src_meta.is_file(), f"missing base metadata to inherit from: {src_meta}"
    meta = json.loads(src_meta.read_text(encoding="utf-8"))
    meta["id"] = f"{args.owner}/taaf-solo-{args.game}"
    meta["title"] = f"TAAF solo {args.game}"
    meta["code_file"] = out_nb.name
    meta["is_private"] = True
    assert meta.get("machine_shape") == "NvidiaRtxPro6000", (
        f"base metadata does not select the RTX Pro 6000 (machine_shape="
        f"{meta.get('machine_shape')!r}); the setup script asserts the GPU type and will die"
    )
    (out_nb.parent / f"kernel-metadata-{args.game}.json").write_text(
        json.dumps(meta, indent=1), encoding="utf-8"
    )

    print(f"wrote {out_nb} ({out_nb.stat().st_size} bytes)")
    print(f"  cells changed vs duckv10: {diff}  (cell 14 only)")
    print(f"  target {args.game!r} substituted; never-submit guard present; "
          f"filter sits between the offline assignment and bm.run()")
    print(f"  cells 6/8/12 byte-identical to duckv10; duckmod marker absent")
    print(f"  metadata id: {meta['id']}")


if __name__ == "__main__":
    main()
