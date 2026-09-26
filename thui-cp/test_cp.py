"""Teeth for thui-cp: execute the graft AS SHIPPED (cut out of the built notebook's cell 15) against the real taaf +
arc_agi and the local copy of the community pack; then 4 mutations that must go red.
Run with the starter venv (arc-agi 0.9.9 / arcengine 0.9.3):
  <starter>/.venv/Scripts/python.exe test_cp.py [<slug> <set: smoke|A|B>]      (default: thui-cp-smoke smoke)
Never enumerates the pack's environments dir: the graft copies only allow-listed game dirs, and the test asserts that."""
import ast, json, os, shutil, sys, tempfile, textwrap, types
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
S = HERE.parent
sys.path.insert(0, str(S / "anim-bundle" / "src" / "tufa-arc-agi-framework" / "src"))
for name in ("imageio", "imageio.v3", "scipy", "scipy.stats"):          # diagnostics-only imports, absent here
    mod = types.ModuleType(name); mod.__path__ = []; sys.modules[name] = mod
sys.modules["imageio"].v3 = sys.modules["imageio.v3"]; sys.modules["scipy"].stats = sys.modules["scipy.stats"]
import taaf.game_api as game_api  # noqa: E402

PACK_ROOT = str(S / "testbed" / "full")           # local copy of the dataset root (holds environment_files/)
SETS = json.loads((HERE / "cp_sets.json").read_text(encoding="utf-8"))
SLUG, WHICH = sys.argv[1:3] if len(sys.argv) > 2 else ("thui-cp-smoke", "smoke")
NB = json.loads((HERE / "out" / SLUG / f"{SLUG}.ipynb").read_text(encoding="utf-8"))
C15 = "".join(NB["cells"][15]["source"])
ORIG_START = game_api.GameAPI._start_game


def offline_games_fn():
    tree = ast.parse(C15)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_offline_games")
    ns = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "cell15:_offline_games", "exec"), ns)
    return ns["_offline_games"]


def shipped_graft():
    start = C15.index("    # ---- thui-cp:")
    end = C15.index("    bm.solver.max_runtime_s_per_game")        # the smoke clock line follows the graft
    return textwrap.dedent(C15[start:end])


def run_graft(src, roots, work):
    os.environ["THUI_CP_ROOTS"] = roots
    game_api.GameAPI._start_game = ORIG_START
    bm = SimpleNamespace(games=[], solver=SimpleNamespace(max_runtime_s_per_game=7920.0))
    ns = {"WORKING_DIR": Path(work), "bm": bm, "_offline_games": offline_games_fn()}
    exec(compile(src, "thui-cp graft", "exec"), ns)
    return bm


def expect_raise(label, exc, fn):
    try:
        fn()
    except exc as e:
        print(f"  RED as required: {label}: {type(e).__name__}: {str(e)[:90]}")
        return
    raise AssertionError(f"MUTANT SURVIVED: {label}")


def main():
    graft = shipped_graft()
    ids = SETS[WHICH]
    with tempfile.TemporaryDirectory() as work:
        bm = run_graft(graft, PACK_ROOT, work)
        env = Path(work) / "thui_cp_env"
        copied = sorted(f"{d.name}-{v.name}" for d in env.iterdir() for v in d.iterdir())
        assert copied == sorted(ids), copied                              # only allow-listed dirs were copied
        assert [g.env_name for g in bm.games] == list(ids)
        for g in bm.games:
            g.start_game()
            assert g.base_actions_per_level is None, g.base_actions_per_level
            assert g.number_of_levels == SETS["n_levels"][g.env_name], (g.env_name, g.number_of_levels)
        print(f"GREEN: shipped graft loads {len(bm.games)} games, copies only them, base=None, levels match cp_sets")
    # mutations
    no_none = graft.replace("    self.base_actions_per_level = None\n", "")
    assert no_none != graft
    reds = 0
    for gid in ids:
        with tempfile.TemporaryDirectory() as work:
            bm = run_graft(no_none.replace(f"tuple({ids!r})", f"tuple({[gid]!r})"), PACK_ROOT, work)
            try:
                bm.games[0].start_game()
            except AssertionError as e:
                reds += 1
                print(f"  RED as required: no-None wrapper on {gid}: {str(e)[:80]}")
                continue
            base = bm.games[0].base_actions_per_level
            if base is not None:   # same length as the level count: action ids would silently pose as human baselines
                reds += 1
                print(f"  RED as required: no-None wrapper on {gid}: base_actions_per_level = {base} (action ids, not baselines)")
    assert reds == len(ids), f"MUTANT SURVIVED on {len(ids) - reds} of {len(ids)} games"
    quarantined = graft.replace(f"tuple({ids!r})", f"tuple({(ids + ['ls20-cb3b57cc'])!r})")
    assert quarantined != graft
    with tempfile.TemporaryDirectory() as work:
        expect_raise("quarantined id in allow-list", AssertionError, lambda: run_graft(quarantined, PACK_ROOT, work))
        assert not (Path(work) / "thui_cp_env").exists(), "quarantine guard fired AFTER copying"
    with tempfile.TemporaryDirectory() as work, tempfile.TemporaryDirectory() as empty:
        expect_raise("dataset not mounted", RuntimeError, lambda: run_graft(graft, empty, work))
    with tempfile.TemporaryDirectory() as work:
        ghost = graft.replace(f"tuple({ids!r})", f"tuple({(ids + ['zz99-v1'])!r})")
        expect_raise("allow-listed game missing from the pack", RuntimeError, lambda: run_graft(ghost, PACK_ROOT, work))
    # the post-run coverage audit AS SHIPPED must accept the allow-list and reject the public 25 (verify wf_c73b5c08-5c6)
    a0 = C15.index("        public_runs = list(bm.game_runs)")
    audit = textwrap.dedent(C15[a0:C15.index("        unfinished = [", a0)])
    public = [f"pub{i:02d}-x" for i in range(len(ids))]
    for label, runs_ids, must_raise in (("allow-list runs", ids, False), ("public-25 runs", public, True)):
        ns = {"bm": SimpleNamespace(game_runs=[SimpleNamespace(game_id=g) for g in runs_ids]), "_CP_IDS": tuple(ids),
              "PUBLIC_GAME_IDS": tuple(public)}
        try:
            exec(compile(audit, "shipped audit", "exec"), ns)
            raised = False
        except RuntimeError:
            raised = True
        assert raised == must_raise, f"audit on {label}: raised={raised}"
    print("  audit as shipped: passes the allow-list, raises on other ids")
    game_api.GameAPI._start_game = ORIG_START
    print(f"test_cp {SLUG}: GREEN + {reds}/{len(ids)} no-None reds + 3 guard reds + audit 2/2")


if __name__ == "__main__":
    main()
