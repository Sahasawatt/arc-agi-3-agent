"""Prove the solo filter actually filters, against the REAL vendored Benchmark -- and prove the
guards are red on mutation rather than decorative.

The builder's self-check says the notebook is well formed. It cannot say the filter works. This
does: it slices the injected block out of the BUILT notebook (rather than retyping it), executes
it against a real `taaf.benchmark.Benchmark` holding real-shaped game ids, and then runs six
mutations that must each fail.

Run:  python solo/prove_teeth.py
"""
import json
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "localrig" / "tufa-arc-agi-framework" / "src"))

# `taaf/__init__` imports diagnostics, which imports imageio (and friends) for movie rendering.
# Those are absent on this box -- there is no localrig/.venv here, despite localrig/README.md
# describing editable installs. Stub ONLY the rendering deps, and say so in the output: the
# Benchmark class under test is the real vendored one, and nothing stubbed is on the path the
# filter touches.
_STUBBED = []
for _name in ("imageio", "imageio.v3", "scipy", "scipy.stats", "pandas", "plotly",
              "plotly.graph_objects", "plotly.express"):
    if _name not in sys.modules:
        try:
            __import__(_name)
        except Exception:  # noqa: BLE001
            mod = types.ModuleType(_name)
            mod.__getattr__ = lambda _a: (lambda *a, **k: None)  # type: ignore[attr-defined]
            sys.modules[_name] = mod
            _STUBBED.append(_name)

import taaf.benchmark  # noqa: E402

GAMES = ["sk48-d8078629", "g50t-5849a774", "lp85-305b61c3", "ar25-0c556536", "ft09-0d8bbf25"]


class _FakeGame:
    """Only the attribute the filter reads. The real Game is not constructible without a server."""

    def __init__(self, gid):
        self.game_id = gid


def _injected_block(nb_path: Path) -> str:
    """Slice the block out of the BUILT notebook, dedented -- never retype it."""
    src = json.loads(nb_path.read_text(encoding="utf-8"))["cells"][14]["source"]
    start = src.index("    # solo probe (B41/B42)")
    end = src.index("bm.n_passes = 1")
    block = src[start:end]
    return "".join(ln[4:] if ln.startswith("    ") else ln for ln in block.splitlines(True))


def _run(block, *, games, true_submission=False, weights=None):
    bm = taaf.benchmark.Benchmark()
    bm.games = [_FakeGame(g) for g in games]
    bm.game_weights = weights
    env = {"bm": bm, "TRUE_SUBMISSION": true_submission, "print": lambda *a, **k: None}
    exec(compile(block, "<solo>", "exec"), env)  # noqa: S102 -- this IS the subject under test
    return bm


def case(name, fn, *, must_raise):
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        got = type(exc).__name__
        ok = must_raise
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<52} raised {got}: {str(exc)[:60]}")
        return ok
    ok = not must_raise
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<52} did not raise")
    return ok


def main() -> int:
    nb = REPO / "solo" / "taaf-solo-sk48.ipynb"
    assert nb.is_file(), f"build it first: {nb}"
    block = _injected_block(nb)
    assert '_SOLO_TARGET = "sk48"' in block, "sliced the wrong region out of cell 14"

    print(f"Benchmark under test: {taaf.benchmark.Benchmark.__module__}."
          f"{taaf.benchmark.Benchmark.__qualname__} (the real vendored class)")
    print(f"stubbed to reach it: {_STUBBED or 'nothing'}")
    print("  -- all rendering/stats deps of taaf.diagnostics; none is on the path the filter "
          "touches, which is bm.games and bm.game_weights only\n")

    results = []

    # POSITIVE CONTROL -- the real block, unmutated, must reduce 5 games to exactly sk48.
    def _real():
        bm = _run(block, games=GAMES)
        assert len(bm.games) == 1, f"expected 1 game, got {len(bm.games)}"
        assert bm.games[0].game_id == "sk48-d8078629", bm.games[0].game_id
    results.append(case("CONTROL real block filters 5 games down to sk48", _real, must_raise=False))

    # And it must be a real reduction, not a no-op on an already-single list.
    def _reduction():
        bm = _run(block, games=GAMES)
        assert len(GAMES) == 5 and len(bm.games) == 1
    results.append(case("CONTROL the input really held 5 games", _reduction, must_raise=False))

    results.append(case(
        "MUT target matches nothing", lambda: _run(block.replace('"sk48"', '"zz99"'), games=GAMES),
        must_raise=True))
    results.append(case(
        "MUT target matches two games",
        lambda: _run(block.replace('"sk48"', '"s"'), games=["sk48-a", "sp80-b", "lp85-c"]),
        must_raise=True))
    results.append(case(
        "MUT TRUE_SUBMISSION is set", lambda: _run(block, games=GAMES, true_submission=True),
        must_raise=True))
    results.append(case(
        "MUT game_weights is populated",
        lambda: _run(block, games=GAMES, weights=[1, 2, 3, 4, 5]), must_raise=True))
    results.append(case(
        "MUT the offline env set lost sk48",
        lambda: _run(block, games=[g for g in GAMES if not g.startswith("sk48")]),
        must_raise=True))

    # The builder's own placement guard, exercised by moving the anchor.
    def _placement():
        src = json.loads(nb.read_text(encoding="utf-8"))["cells"][14]["source"]
        i = src.index("_solo_before = list(bm.games)")
        j = src.index("await bm.run(")
        assert i < j, "filter runs after bm.run()"
        k = src.index("    bm.games = _offline_games(competition_env_files)\n")
        assert k < i, "filter runs before the offline assignment that would overwrite it"
    results.append(case("CONTROL filter sits between the assignment and the run",
                        _placement, must_raise=False))

    # ...and that placement check must itself be able to FAIL, or it is a constant. Same check,
    # run against a cell-14 with the block moved ABOVE the assignment that would overwrite it --
    # which is exactly the mistake B41's ticket prescribed (cell 12).
    def _placement_can_fail():
        src = json.loads(nb.read_text(encoding="utf-8"))["cells"][14]["source"]
        anchor = "    bm.games = _offline_games(competition_env_files)\n"
        start = src.index("    # solo probe (B41/B42)")
        end = src.index("bm.n_passes = 1")
        blk = src[start:end]
        moved = src.replace(blk, "").replace(anchor, blk + anchor)
        k, i = moved.index(anchor), moved.index("_solo_before = list(bm.games)")
        assert k < i, "filter runs before the offline assignment that would overwrite it"
    results.append(case("MUT placement check catches a filter moved too early",
                        _placement_can_fail, must_raise=True))

    # The builder gained `assert o14.count(ANCHOR) == 1` after the defect above. Prove that
    # assert would fire: put a verbatim copy of the anchor back into a comment and count again.
    def _anchor_uniqueness_has_teeth():
        src = json.loads(nb.read_text(encoding="utf-8"))["cells"][14]["source"]
        anchor = "    bm.games = _offline_games(competition_env_files)\n"
        assert src.count(anchor) == 1, f"clean build already has {src.count(anchor)} anchors"
        regressed = src.replace(
            "    # solo probe (B41/B42)",
            "    # else:                bm.games = _offline_games(competition_env_files)\n"
            "    # solo probe (B41/B42)",
            1,
        )
        assert regressed.count(anchor) == 1, (
            f"the anchor occurs {regressed.count(anchor)} times after the splice"
        )
    results.append(case("MUT anchor-uniqueness assert catches a quoted copy",
                        _anchor_uniqueness_has_teeth, must_raise=True))

    ok = all(results)
    print(f"\n{'TEETH OK' if ok else 'TEETH FAIL'}: {sum(results)}/{len(results)} cases behaved")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
