"""Build thui-cp (unseen-game proxy eval: COMMUNITY games instead of the public 25) from the B81 notebook.
The graft goes ONLY into cell 15's offline (interactive) branch, so a competition rerun can never execute it.
usage: python build_notebook.py --smoke | --quick --set A|B | --full --set A|B      (builds only; never pushes)
--quick = a whole set at the smoke clock, read against the public 25-game runs at that same clock.
"""
import ast, copy, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_DIR = HERE.parent / "wt-daq" / "thui-a5" / "out" / "thui-a5-mtp0k7s28-full25-r1"
SRC_NB = SRC_DIR / "thui-a5-mtp0k7s28-full25-r1.ipynb"
SRC_META = SRC_DIR / "kernel-metadata.json"
GRAFT = (HERE / "cp_graft_src.py").read_text(encoding="utf-8")
SETS = json.loads((HERE / "cp_sets.json").read_text(encoding="utf-8"))
DATASET = "poonszesen/arc-interactive-community"
SMOKE_CLOCK_S = 1800
OWNER = "sahasawatt"


def cell0(slug, games, smoke, short):
    scope = f"**Smoke: {len(games)} games at {SMOKE_CLOCK_S} s — a validity check, not a measurement.**" if smoke \
        else f"**Quick: {len(games)} community games at the short {SMOKE_CLOCK_S} s clock.**" if short \
        else f"**Full: {len(games)} community games at the normal 7,920 s clock.**"
    return f"""# {slug} (Thuitanium / Knowless Crew) — B81 on UNSEEN community games

{scope}

**This is a Knowless Crew / Thuitanium experiment notebook — an evaluation instrument, not a submission.** The B81
solver, prompts, clock and vLLM profile are unchanged. One graft in cell 15, installed only in the offline
(interactive) branch, replaces the 25 public games with community-made ARC-AGI-3-style games from the MIT dataset
[`{DATASET}`](https://www.kaggle.com/datasets/{DATASET}), which neither we nor the harness authors tuned on. The pack
has no human baselines, so the metric is levels cleared. It never runs in a competition rerun.

Serving stack by [Keith Tyser](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp), harness by
[Tufa Labs](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner), anim solver
bundle `jakobbrggen/taaf-kaggle-source-anim-20260807-anim`.
"""


def replace_once(src, old, new, label):
    assert src.count(old) == 1, f"{label}: expected one anchor, found {src.count(old)}"
    return src.replace(old, new)


def patch_cell15(src, games, short):
    # insert AFTER the base's own public-25 guard + print, so that guard keeps checking what it was written for
    anchor = "    print(f'PUBLIC25_SELECTION games={len(bm.games)} passes=1', flush=True)\n"
    graft = replace_once(GRAFT, "tuple(__THUI_CP_IDS__)", "tuple(" + repr(list(games)) + ")", "graft allow-list")
    indented = "".join(("    " + line) if line.strip() else line for line in graft.splitlines(keepends=True))
    extra = ""
    if short:
        extra = (f"    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-cp short clock\n"
                 '    print(f"thui-cp: short clock {len(bm.games)} games @ {bm.solver.max_runtime_s_per_game} s", flush=True)\n')
    src = replace_once(src, anchor, anchor + indented + extra, "cell 15 offline selection print")
    # the post-run coverage audit compared against PUBLIC_GAME_IDS: point it at the allow-list (verify wf_c73b5c08-5c6)
    src = replace_once(src, "        if len(public_runs) != 25 or public_run_ids != list(PUBLIC_GAME_IDS):\n",
                       "        if len(public_runs) != len(_CP_IDS) or public_run_ids != list(_CP_IDS):   # thui-cp allow-list\n",
                       "post-run coverage audit")
    src = replace_once(src, "f'PUBLIC25_AUDIT runs=25 actions=", "f'PUBLIC25_AUDIT runs={len(public_runs)} actions=",
                       "audit print")
    assert src.count("!= 25") == 1, "only the base's pre-graft public-25 guard may still compare with 25"
    comp = src.index("bm.games = _competition_games()")
    else_at = src.index("\nelse:\n", comp)
    graft_at = src.index("# ---- thui-cp:")
    assert comp < else_at < graft_at < src.index("bm.n_passes = 1"), "thui-cp graft is not inside the offline branch"
    return src


def main():
    args = sys.argv[1:]
    smoke = args == ["--smoke"]
    assert smoke or (len(args) == 3 and args[0] in ("--quick", "--full") and args[1] == "--set" and args[2] in ("A", "B")), \
        "pass --smoke, or --quick|--full --set A|B"
    short = smoke or args[0] == "--quick"
    games = SETS["smoke"] if smoke else SETS[args[2]]
    slug = "thui-cp-smoke" if smoke else f"thui-cp{args[2].lower()}-{'q1800' if short else 'full25'}-r1"
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    original = copy.deepcopy(nb)
    cells = nb["cells"]
    cells[0]["source"] = cell0(slug, games, smoke, short).splitlines(keepends=True)
    cells[15]["source"] = patch_cell15("".join(cells[15]["source"]), games, short).splitlines(keepends=True)
    changed = [i for i, (a, b) in enumerate(zip(original["cells"], cells)) if a != b]
    assert changed == [0, 15], changed
    c15 = "".join(cells[15]["source"])
    compile(c15, "cell15", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    assert c15.count("THUI_CP_GRAFT ok") == 1 and c15.count("_cp_game_api.GameAPI._start_game = _cp_start_game") == 1
    assert not re.search(r"['\"](ft09|ls20|vc33)-[0-9a-z]+['\"]", c15.split("# ---- thui-cp:")[1]), "quarantined id in graft"
    metadata = json.loads(SRC_META.read_text(encoding="utf-8"))
    assert DATASET not in metadata["dataset_sources"]
    metadata.update(id=f"{OWNER}/{slug}", title=slug, code_file=f"{slug}.ipynb", is_private=True,
                    dataset_sources=metadata["dataset_sources"] + [DATASET])
    out = HERE / "out" / slug
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{slug}.ipynb").write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
    (out / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"built {slug}: {len(games)} games, cells changed {changed}, id={metadata['id']}, private, "
          f"datasets={metadata['dataset_sources']}")


if __name__ == "__main__":
    main()
