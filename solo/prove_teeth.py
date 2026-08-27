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

# NOT stubbable the way the rendering deps are: taaf.game imports `arcengine` and `matplotlib`
# before taaf.benchmark can load. arcengine is not vendored anywhere in this repo (`git ls-files`
# has no match) and taaf.game uses `arcengine.GameAction` as a real type, so a callable stub
# raises at class-definition time -- faking it would mean inventing the vendor's API. On a
# checkout without a wheelhouse install this file used to die HERE, before case 1. Now the
# Benchmark-backed cases report SKIPPED with the reason, and the reachability cases still run.
try:
    import taaf.benchmark  # noqa: E402
    _BENCH_ERR = ""
except Exception as _exc:  # noqa: BLE001
    taaf = None  # type: ignore[assignment]
    _BENCH_ERR = f"{type(_exc).__name__}: {_exc}"

GAMES = ["sk48", "g50t", "lp85", "ar25", "ft09"]   # env_name, as cell 14 builds them


class _FakeGame:
    """Shaped like a pre-start GameAPI, which is NOT what a naive fake looks like.

    `taaf.game.Game` declares `game_id: str = field(default="", init=False)` and only
    `_start_game()` populates it, so before the run every game_id is the EMPTY STRING and the
    id lives in `env_name`. The first version of this fake set `game_id` to the full run id --
    the shape the author believed -- so the rig confirmed a filter that matched 0 of 25 on
    Kaggle. `taaf.game_api` cannot be imported here (it needs `arcengine`), so the real object
    is out of reach and this fake is the only subject available: it must therefore be built
    from the SOURCE's declaration, which `test_pre_start_game_id_is_empty` below re-reads.
    """

    def __init__(self, env_name):
        self.env_name = env_name
        self.game_id = ""      # exactly what a pre-start Game carries


def _injected_block(nb_path: Path) -> str:
    """Slice the block out of the BUILT notebook, dedented -- never retype it."""
    src = json.loads(nb_path.read_text(encoding="utf-8"))["cells"][14]["source"]
    start = src.index("    # solo probe (B41/B42)")
    end = src.index("bm.n_passes = 1")
    block = src[start:end]
    return "".join(ln[4:] if ln.startswith("    ") else ln for ln in block.splitlines(True))


class _Skipped(Exception):
    """Raised when a case cannot run at all. Caught BEFORE the must_raise logic, so a mutation
    case is never credited for 'raising' when what it raised was the rig giving up."""


def _run(block, *, games, true_submission=False, weights=None):
    if _BENCH_ERR:
        raise _Skipped(_BENCH_ERR)
    bm = taaf.benchmark.Benchmark()
    bm.games = [_FakeGame(g) for g in games]
    bm.game_weights = weights
    env = {"bm": bm, "TRUE_SUBMISSION": true_submission, "print": lambda *a, **k: None}
    exec(compile(block, "<solo>", "exec"), env)  # noqa: S102 -- this IS the subject under test
    return bm


# duckv10's own line, above BOTH splice points and present in every build. Starting the region at
# `if TRUE_SUBMISSION:` instead would exclude the module-level guard, which sits above it -- the
# region would then miss the very thing it is meant to reach and report a correct build as broken.
REGION_START = 'os.environ.setdefault("RECORDINGS_DIR"'
REGION_END = "bm.n_passes = 1"
LIVE_GAMES = [f"h{i:03d}" for i in range(110)]   # what the gateway hands back on a submission


class _FakeBenchmark:
    """Stand-in for the reachability cases ONLY.

    The cases above use the real vendored Benchmark, because what they test is the filter
    operating on it. These test whether cell 14's branch structure REACHES the injected code at
    all, which touches nothing but `games` and `game_weights` -- so a real Benchmark buys no
    coverage here and would make the one group guarding a never-submit rule unrunnable on any
    checkout lacking arcengine.
    """

    def __init__(self):
        self.games = None
        self.game_weights = None


def _branch_region(nb_path: Path) -> str:
    """Cell 14 from REGION_START to `bm.n_passes`, WITHOUT dedenting.

    _injected_block strips the 4-space indent, which lifts the filter out of the else branch it
    lives in. That is right for testing the block's logic and structurally blind to whether the
    block is REACHED: a guard spliced into the else branch passes every dedented mutation and is
    skipped by the notebook whenever TRUE_SUBMISSION is true. Keeping the if/else intact is the
    only way to see it.
    """
    src = json.loads(nb_path.read_text(encoding="utf-8"))["cells"][14]["source"]
    lines = src.splitlines(True)
    start = next(i for i, ln in enumerate(lines) if ln.startswith(REGION_START))
    end = next(i for i, ln in enumerate(lines) if ln.startswith(REGION_END))
    assert start < end, "cell 14 no longer has the branch above bm.n_passes"
    region = "".join(lines[start:end])
    assert "if TRUE_SUBMISSION:" in region, "the region lost the branch it exists to exercise"
    return region


def _run_region(region, *, true_submission):
    """Execute the branch region with the if/else INTACT; fake only the game-list builders."""
    bm = _FakeBenchmark()
    env = {
        "bm": bm,
        "TRUE_SUBMISSION": true_submission,
        "print": lambda *a, **k: None,
        "os": __import__("os"),
        "Path": Path,
        "WORKING_DIR": Path("/tmp/solo-teeth"),
        "_competition_games": lambda: [_FakeGame(g) for g in LIVE_GAMES],
        "_offline_games": lambda _d: [_FakeGame(g) for g in GAMES],
        "_wait_for_gateway": lambda _url, timeout_s=600.0: None,
    }
    exec(compile(region, "<cell14-branch>", "exec"), env)  # noqa: S102 -- the subject under test
    return bm


def case(name, fn, *, must_raise):
    try:
        fn()
    except _Skipped as exc:
        print(f"  SKIP  {name:<52} could not run: {str(exc)[:56]}")
        return None
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

    if _BENCH_ERR:
        print(f"Benchmark under test: UNAVAILABLE on this checkout -- {_BENCH_ERR}")
        print("  the filter cases below are SKIPPED, not passed; the reachability cases "
              "still run and do not need Benchmark\n")
    else:
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
        assert bm.games[0].env_name == "sk48", bm.games[0].env_name
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
        lambda: _run(block.replace('"sk48"', '"s"'), games=["sk48", "sp80", "lp85"]),
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

    # The claim this whole rig rests on, re-read from the framework SOURCE rather than assumed:
    # a pre-start game carries game_id == "" and the id lives in env_name. If a future bundle
    # changes that, this fails here instead of 483 seconds into a Kaggle run.
    def _pre_start_game_id_is_empty():
        src = (REPO / "localrig" / "tufa-arc-agi-framework" / "src" / "taaf" / "game.py"
               ).read_text(encoding="utf-8")
        assert 'game_id: str = field(default="", init=False)' in src, (
            "taaf.game.Game no longer declares game_id as an empty-by-default, init=False "
            "field -- re-read game.py before trusting env_name as the filter key"
        )
        assert "_start_game() must populate game_id" in src, (
            "the assert that proves game_id is populated only at start is gone from game.py"
        )
        api = (REPO / "localrig" / "tufa-arc-agi-framework" / "src" / "taaf" / "game_api.py"
               ).read_text(encoding="utf-8")
        assert "env_name: str = field(kw_only=True)" in api, (
            "GameAPI no longer declares env_name -- the filter key would be wrong"
        )
    results.append(case("CONTROL source still says game_id is empty pre-start",
                        _pre_start_game_id_is_empty, must_raise=False))

    # ...and the filter must actually depend on env_name: a game whose env_name does NOT match
    # must be excluded even when some other attribute would have matched.
    def _filters_on_env_name_not_game_id():
        bm = _run(block, games=GAMES)
        assert bm.games[0].env_name.startswith("sk48"), bm.games[0].env_name
        # every input carried game_id == "" -- if the filter read game_id it would have got 0
        assert all(g.game_id == "" for g in bm.games), "fake no longer models a pre-start game"
    results.append(case("CONTROL filter keys on env_name while game_id is empty",
                        _filters_on_env_name_not_game_id, must_raise=False))

    # ---- reachability: the two cases the dedented rig above cannot see ------------------
    region = _branch_region(nb)
    assert "if TRUE_SUBMISSION:" in region and "_solo_before = list(bm.games)" in region, (
        "sliced the wrong region -- it must hold both the branch and the injected filter"
    )

    # CONTROL: with the branch intact the offline path must still filter. Without this, the
    # mutation below could be raising for a reason that has nothing to do with the guard.
    def _region_offline():
        bm = _run_region(region, true_submission=False)
        assert len(bm.games) == 1, f"offline path gave {len(bm.games)} game(s)"
    results.append(case("CONTROL branch intact, offline path still filters to one game",
                        _region_offline, must_raise=False))

    # NOT must_raise=True: both outcomes raise AssertionError -- the guard's own, or the one this
    # function throws to report a miss -- so must_raise would credit the failure as a pass. Assert
    # WHICH assertion surfaced instead. Red on the build that shipped without solo_guard.py:
    # TRUE_SUBMISSION=True returned 110 games and raised nothing.
    def _region_true_submission():
        try:
            bm = _run_region(region, true_submission=True)
        except AssertionError as exc:
            assert "must never be submitted" in str(exc), (
                f"the branch raised, but not from the never-submit guard: {str(exc)[:80]}"
            )
            return
        raise AssertionError(
            f"NEVER-SUBMIT GUARD IS UNREACHABLE: TRUE_SUBMISSION=True did not raise; "
            f"bm.games holds {len(bm.games)} game(s) and the run would submit"
        )
    results.append(case("GUARD never-submit fires with the branch intact",
                        _region_true_submission, must_raise=False))

    ran = [r for r in results if r is not None]
    skipped = len(results) - len(ran)
    ok = all(ran)
    note = f", {skipped} SKIPPED (Benchmark unavailable: {_BENCH_ERR})" if skipped else ""
    print(f"\n{'TEETH OK' if ok else 'TEETH FAIL'}: {sum(ran)}/{len(ran)} cases behaved{note}")
    if skipped:
        print("  a SKIPPED case is not a passed one -- run this on a checkout with the "
              "wheelhouse installed to exercise the filter against the real Benchmark")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
