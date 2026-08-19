"""Verify duckv4/taaf-duck-v4.ipynb the way duckmod/duckv3's own builds
verified theirs: valid JSON, only cell 12 differs from the ORIGINAL duck
notebook it was built from, every code cell's Python parses, and the exact
cell-12 source (as embedded in the notebook, not the standalone modules)
executes cleanly against the real bundle and reaches both patch targets.

Run:
    PYTHONPATH="duck/bundle/src/ARC3-Inference;duck/bundle/src/tufa-arc-agi-framework/src" \
        uv run --with imageio --with scipy python duckv4/verify_notebook.py

(imageio/scipy are transitive deps of taaf/diagnostics.py, not of anything
duckv4 adds -- `inference.framework.solver` pulls them in at import time
regardless of this patch; `--with` keeps them out of the repo's own
pyproject/lockfile.)
"""
import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BASE_NB = REPO_ROOT / "duck" / "tufa-labs-duck-harness-june-30-milestone-winner.ipynb"
DUCKV4_NB = REPO_ROOT / "duckv4" / "taaf-duck-v4.ipynb"


def main() -> None:
    base = json.loads(BASE_NB.read_text(encoding="utf-8"))
    duckv4 = json.loads(DUCKV4_NB.read_text(encoding="utf-8"))
    print(f"both notebooks parse as valid JSON, {len(duckv4['cells'])} cells")

    assert len(base["cells"]) == len(duckv4["cells"])
    diffs = [
        c1.get("id")
        for c1, c2 in zip(base["cells"], duckv4["cells"])
        if c1["source"] != c2["source"]
    ]
    assert diffs == ["12"], f"expected only cell 12 to differ, got: {diffs}"
    print(f"only cell 12 differs from the original notebook ({len(duckv4['cells']) - 1}/{len(duckv4['cells'])} identical)")

    for cell in duckv4["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell["source"])
        ast.parse(src)
    print("every code cell's Python parses (ast.parse)")

    cell12 = next(c for c in duckv4["cells"] if c.get("id") == "12")
    cell12_src = "".join(cell12["source"])
    ast.parse(cell12_src)
    print("cell 12 source itself parses (ast.parse)")

    # Execute the EXACT embedded cell-12 source (as a Kaggle kernel would)
    # against the real bundle.
    from inference.agent import tool_agent
    from inference.framework import solver

    ns = {"tool_agent": tool_agent, "solver": solver}
    before_wm_patched = getattr(tool_agent, "_duckv4_capped", False)
    before_realloc_patched = getattr(solver._HarnessGameSession, "_duckv4_realloc_patched", False)
    assert not before_wm_patched and not before_realloc_patched

    exec(compile(cell12_src, "<cell12>", "exec"), ns)

    assert getattr(tool_agent, "_duckv4_capped", False), "world-model patch did not apply"
    assert getattr(solver._HarnessGameSession, "_duckv4_realloc_patched", False), "reallocator patch did not apply"
    print("executed embedded cell-12 source against the real bundle: both patches applied")

    # Functional smoke test through the exact patched module objects.
    long_note = "\n".join(f"- finding {i}" for i in range(1000))
    content = f"World model:\n{long_note}\n"
    note = tool_agent._extract_scientist_note(content)
    assert len(note["world_model"]) < len(long_note), "world-model field must be capped post-patch"
    assert "[compacted:" in note["world_model"]
    print(f"real tool_agent._extract_scientist_note now caps a long field to {len(note['world_model'])} chars")

    import time

    class _State:
        def __init__(self, levels):
            self.levels_completed = levels

    class _Game:
        def __init__(self, levels):
            self.current_state = _State(levels)

    class _Session:
        def __init__(self, budget, levels, actions):
            self.solver = solver.HarnessSolver(max_runtime_s_per_game=budget)
            self.game = _Game(levels)
            self._actions = actions
            self.started_at = time.monotonic()

        @property
        def action_count(self):
            return self._actions

    sess = _Session(7920.0, levels=0, actions=5)
    remaining = solver._HarnessGameSession.timing_payload(sess)["time_remaining_seconds"]
    assert abs(remaining - 7920.0) < 1.0
    print("real solver._HarnessGameSession.timing_payload reads through the reallocator")

    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
