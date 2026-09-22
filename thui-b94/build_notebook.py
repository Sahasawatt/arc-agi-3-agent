"""Build the B94 three-game Qwen3.5 compatibility smoke notebook."""

import ast
import copy
import hashlib
import inspect
import json
import re
import sys
from pathlib import Path

from serving_patch import patch

HERE = Path(__file__).resolve().parent
SRC_DIR = HERE.parent / "thui-a5" / "out" / "thui-a5-mtp0k7s28-full25-r1"
SRC_NB = SRC_DIR / "thui-a5-mtp0k7s28-full25-r1.ipynb"
SRC_META = SRC_DIR / "kernel-metadata.json"
SLUG = "thui-b94-q35-122b-smoke"
OUT = HERE / "out" / SLUG
CANDIDATE = "ippeiogawa/qwen35-122b-a10b-nvfp4"
MODEL_ID = "Qwen/Qwen3.5-122B-A10B-NVFP4"
SMOKE_GAMES = ("tn36-ef4dde99", "vc33-5430563c", "bp35-0a0ad940")
SMOKE_CLOCK_S = 1800

CELL0 = f"""# {SLUG} (Thuitanium / Knowless Crew) — B81 with the served model swapped to Qwen3.5-122B-A10B-NVFP4

**Smoke: 3 games at 1800 s. Numbers are not a score.**

**This is a Knowless Crew / Thuitanium experiment notebook.** The B81 solver, prompts, clock and vLLM profile
(context 32,768 / KV 7 GiB / MTP 0 / max_num_seqs 28) stay fixed. The only experiment change is the served
model, supplied by the `{CANDIDATE}` dataset and patched into a writable serving-bundle overlay in cell 9.

Serving stack by [Keith Tyser](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp), harness by
[Tufa Labs](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner), anim solver
bundle `jakobbrggen/taaf-kaggle-source-anim-20260807-anim`.
"""


def replace_once(src: str, old: str, new: str, label: str) -> str:
    count = src.count(old)
    assert count == 1, f"{label}: expected one anchor, found {count}"
    return src.replace(old, new)


def patch_cell7(src: str) -> str:
    match = re.search(r"DATASET_SOURCES = \[(.*?)\]\n", src)
    assert match and src.count(match.group(0)) == 1, "cell 7 DATASET_SOURCES moved"
    refs = json.loads("[" + match.group(1) + "]")
    assert CANDIDATE not in refs
    refs.append(CANDIDATE)
    replacement = "DATASET_SOURCES = " + json.dumps(refs) + "\n"
    return src.replace(match.group(0), replacement)


def patch_cell9(src: str) -> str:
    src = replace_once(
        src,
        'assert _persisted.get("LOCAL_ANALYZER_MODEL_ID") == "Qwen/Qwen3.8-Flash-Next-NVFP4",',
        f'assert _persisted.get("LOCAL_ANALYZER_MODEL_ID") == "{MODEL_ID}",',
        "cell 9 persisted model",
    )
    src = replace_once(
        src,
        'assert os.environ["LOCAL_ANALYZER_MODEL_ID"] == "Qwen/Qwen3.8-Flash-Next-NVFP4"',
        f'assert os.environ["LOCAL_ANALYZER_MODEL_ID"] == "{MODEL_ID}"',
        "cell 9 environment model",
    )
    source = inspect.getsource(patch)
    helper_once = inspect.getsource(__import__("serving_patch")._replace_once)
    helper_section = inspect.getsource(__import__("serving_patch")._replace_section)
    module = __import__("serving_patch")
    constants = []
    for name in ("MODEL_CONSTANTS", "SOURCE_IDENTITY", "MODEL_FUNCTIONS"):
        constants.append(f"{name} = {getattr(module, name)!r}\n")
    embedded = helper_once + "\n" + helper_section + "\n" + "".join(constants) + "\n" + source
    overlay = f'''# ---- thui-b94: Qwen3.5 candidate serving overlay.
import hashlib as _hashlib
import shutil as _shutil
_b94_src = BUNDLE_DIR
_b94_dir = WORKING_DIR / "thui-b94-bundle-overlay"
if _b94_dir.exists():
    _shutil.rmtree(_b94_dir)
_b94_dir.mkdir(parents=True)
for _entry in _b94_src.iterdir():
    if _entry.name not in ("serving_setup.py", "SOURCE_IDENTITY.json"):
        (_b94_dir / _entry.name).symlink_to(_entry)
{embedded}
_b94_text = (_b94_src / "serving_setup.py").read_text()
_b94_text = patch(_b94_text)
(_b94_dir / "serving_setup.py").write_text(_b94_text)
_b94_ident = json.loads((_b94_src / "SOURCE_IDENTITY.json").read_text())
assert _b94_ident["serving_setup_sha256"] == _hashlib.sha256((_b94_src / "serving_setup.py").read_bytes()).hexdigest(), \\
    "thui-b94: original serving identity mismatch"
_b94_ident["serving_setup_sha256"] = _hashlib.sha256((_b94_dir / "serving_setup.py").read_bytes()).hexdigest()
(_b94_dir / "SOURCE_IDENTITY.json").write_text(json.dumps(_b94_ident, indent=2, sort_keys=True) + "\\n")
BUNDLE_DIR = _b94_dir
print(f"THUI_B94_OVERLAY ok bundle={{BUNDLE_DIR}} src={{_b94_src}}", flush=True)

'''
    anchor = "# Solver setup commands (wheels, vLLM server startup, ...) run before the benchmark loads.\n"
    src = replace_once(src, anchor, overlay + anchor, "cell 9 overlay")
    return src


def patch_cell15(src: str) -> str:
    match = re.search(r"PUBLIC_GAME_IDS = tuple\(\[\n(?:    \"[a-z0-9]{4}-[0-9a-f]{8}\",?\n){25}\]\)\n", src)
    assert match, "cell 15 public game tuple moved"
    assert all(f'"{game}"' in match.group(0) for game in SMOKE_GAMES)
    src = src.replace(match.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-b94 smoke subset\n")
    assert src.count("!= 25") == 2
    src = src.replace("!= 25", "!= len(PUBLIC_GAME_IDS)")
    src = replace_once(src, "    if missing or extra:\n", "    if missing or (extra and len(PUBLIC_GAME_IDS) == 25):\n", "cell 15 extras")
    selection = "    bm.games = [offline_by_id[game_id] for game_id in PUBLIC_GAME_IDS]\n"
    addition = selection + f"    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-b94 smoke clock\n" + '    print(f"thui-b94: smoke {len(bm.games)} games @ {bm.solver.max_runtime_s_per_game} s", flush=True)\n'
    return replace_once(src, selection, addition, "cell 15 selection")


def main() -> None:
    if sys.argv[1:] != ["--smoke"]:
        raise SystemExit("thui-b94 only builds the smoke; pass exactly --smoke")
    nb = json.loads(SRC_NB.read_text())
    original = copy.deepcopy(nb)
    cells = nb["cells"]
    cells[0]["source"] = CELL0.splitlines(keepends=True)
    cells[7]["source"] = patch_cell7("".join(cells[7]["source"])).splitlines(keepends=True)
    cells[9]["source"] = patch_cell9("".join(cells[9]["source"])).splitlines(keepends=True)
    cells[15]["source"] = patch_cell15("".join(cells[15]["source"])).splitlines(keepends=True)
    changed = [index for index, (old, new) in enumerate(zip(original["cells"], cells)) if old != new]
    assert changed == [0, 7, 9, 15], changed
    assert len(original["cells"]) == len(cells)
    compile("".join(cells[9]["source"]), "cell9", "exec")
    compile("".join(cells[15]["source"]), "cell15", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    assert "ANALYZER_CONTEXT = 65_536" not in "".join(cells[9]["source"])

    metadata = json.loads(SRC_META.read_text())
    metadata.update(id=f"yocybercode/{SLUG}", title=SLUG, code_file=f"{SLUG}.ipynb", is_private=True)
    assert metadata["dataset_sources"].count(CANDIDATE) == 0
    metadata["dataset_sources"].append(CANDIDATE)
    assert len(metadata["model_sources"]) == 1
    metadata["model_sources"] = []
    assert metadata["dataset_sources"].count(CANDIDATE) == 1
    assert metadata["model_sources"] == []

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{SLUG}.ipynb").write_text(json.dumps(nb, indent=1) + "\n")
    (OUT / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"built {SLUG}: cells changed {changed}, id={metadata['id']}, private, model_sources=[]")


if __name__ == "__main__":
    main()
