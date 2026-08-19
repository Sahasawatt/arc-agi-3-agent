"""Build duckv4/taaf-duck-v4.ipynb from the ORIGINAL duck notebook, replacing
only cell 12 (the customization hook) with both duckv4 patches.

Source of truth = duckv4_worldmodel_cap.py + duckv4_reallocator.py (the
modules) + this script; the .ipynb is a generated artifact, never
hand-edited, same discipline the repo's own CLAUDE.md states for
kaggle/my_agent.py (and duckv3/build_notebook.py already applies one level
up). Built from the ORIGINAL notebook, not duckmod's or duckv3's: duckv4
implements two new, independent levers (world-model cap, depth-aware time
reallocation) and deliberately does not stack on the two tool-injection
designs (duckmod's callable API, duckv3's auto-pushed observation block) --
see the build report for why. Run:

    python duckv4/build_notebook.py
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BASE_NB = REPO_ROOT / "duck" / "tufa-labs-duck-harness-june-30-milestone-winner.ipynb"
WORLDMODEL_SRC = REPO_ROOT / "duckv4" / "duckv4_worldmodel_cap.py"
REALLOCATOR_SRC = REPO_ROOT / "duckv4" / "duckv4_reallocator.py"
OUT_NB = REPO_ROOT / "duckv4" / "taaf-duck-v4.ipynb"


def _source_without_demo(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    marker = '\nif __name__ == "__main__":'
    idx = text.index(marker)
    return text[:idx].rstrip() + "\n"


def _cell12_source() -> str:
    worldmodel_source = _source_without_demo(WORLDMODEL_SRC)
    reallocator_source = _source_without_demo(REALLOCATOR_SRC)
    return f'''# === duckv4: world-model field cap + depth-aware time reallocation ===
# Two independent levers, patched separately, on the ORIGINAL duck notebook:
#   (a) caps every labeled world-model field (tool_agent._extract_labeled_blocks)
#       instead of the unbounded max_chars=None the harness ships with, so a long
#       block written once stops compounding every following turn.
#   (b) gives each _HarnessGameSession an effective per-game deadline funded by a
#       shared, zero-sum-or-negative pool: games that just completed a level get
#       extra time harvested from games thrashing at 0 levels, both hard-capped.
# Neither touches HarnessSolver.concurrency/max_runtime_s_per_game themselves --
# both are LOAD-BEARING for the 9h envelope per results/wayfinder/R2-levers.md.
# Runs after bm/bm.solver are unpickled (cell 10) and before bm.run() starts
# (cell 14), so every ToolAgent/_HarnessGameSession constructed during the run
# is patched. See results/duckv4-build-20260819.md for the full design writeup.

from inference.agent import tool_agent
from inference.framework import solver

_DUCKV4_WORLDMODEL_SOURCE = {worldmodel_source!r}
exec(compile(_DUCKV4_WORLDMODEL_SOURCE, "<duckv4_worldmodel_cap>", "exec"), globals())
install_patch(tool_agent)
_worldmodel_chars = len(_DUCKV4_WORLDMODEL_SOURCE)

_DUCKV4_REALLOCATOR_SOURCE = {reallocator_source!r}
_realloc_ns = {{}}
exec(compile(_DUCKV4_REALLOCATOR_SOURCE, "<duckv4_reallocator>", "exec"), _realloc_ns)
_realloc_ns["install_patch"](solver)
_reallocator_chars = len(_DUCKV4_REALLOCATOR_SOURCE)

print(
    f"duckv4: patched tool_agent._extract_labeled_blocks "
    f"(worldmodel source {{_worldmodel_chars}} chars), "
    f"patched solver._HarnessGameSession.runtime_limit_reached/timing_payload "
    f"(reallocator source {{_reallocator_chars}} chars)"
)
'''


def main() -> None:
    nb = json.loads(BASE_NB.read_text(encoding="utf-8"))
    cell12_source = _cell12_source()
    replaced = False
    for cell in nb["cells"]:
        if cell.get("id") == "12":
            cell["source"] = cell12_source.splitlines(keepends=True)
            cell["outputs"] = []
            cell["execution_count"] = None
            replaced = True
            break
    if not replaced:
        raise RuntimeError("duckv4: could not find cell id=12 in the base notebook")

    OUT_NB.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT_NB} ({OUT_NB.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
