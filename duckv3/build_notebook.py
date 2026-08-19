"""Build duckv3/taaf-duck-v3.ipynb from duckmod's notebook, replacing only
cell 12 (the customization hook) with the duckv3 auto-push patch.

Source of truth = duckv3_observer.py (the module) + this script; the .ipynb
is a generated artifact, never hand-edited, same discipline the repo's own
CLAUDE.md states for kaggle/my_agent.py. Run:

    python duckv3/build_notebook.py
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DUCKMOD_NB = REPO_ROOT / "duckmod" / "taaf-duck-mod.ipynb"
OBSERVER_SRC = REPO_ROOT / "duckv3" / "duckv3_observer.py"
OUT_NB = REPO_ROOT / "duckv3" / "taaf-duck-v3.ipynb"

_SYSTEM_PROMPT_ADDITION = (
    "An OBSERVATION block is auto-appended each turn (no function call needed): "
    "`HUD cells` = timer/chrome cells to ignore. `state` = NOVEL or SEEN(xN) for "
    "this masked board. `untried here` = valid actions never tried from this "
    "state. `last action` = whether the board changed."
)


def _observer_source_without_demo() -> str:
    text = OBSERVER_SRC.read_text(encoding="utf-8")
    marker = '\nif __name__ == "__main__":'
    idx = text.index(marker)
    return text[:idx].rstrip() + "\n"


def _cell12_source() -> str:
    observer_source = _observer_source_without_demo()
    return f'''# === duckv3: auto-push per-turn OBSERVATION block, no callable API ===
# Patches ToolAgent._build_user_prompt (inference/agent/tool_agent.py) --
# the function that assembles every turn's user-facing message -- to append
# a harness-computed OBSERVATION block (HUD auto-mask, state novelty, untried
# actions, last-action-changed-frame). Runs entirely in the harness KERNEL
# process, never inside the isolated python-tool sandbox subprocess, so
# unlike duckmod there is no splice into python_tool_sandbox._SANDBOX_BOOTSTRAP
# and nothing new for the LLM to call -- the harness computes and shows.
# Runs after bm/bm.solver are unpickled (cell 5) and before bm.run() starts
# (cell 7), so every ToolAgent constructed during the run is patched. See
# results/duckv3-build-20260819.md for the full design writeup.

from inference.agent import tool_agent

_DUCKV3_OBSERVER_SOURCE = {observer_source!r}
exec(compile(_DUCKV3_OBSERVER_SOURCE, "<duckv3_observer>", "exec"), globals())

install_patch(tool_agent)

_SYSTEM_PROMPT_ADDITION = {_SYSTEM_PROMPT_ADDITION!r}
tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM = (
    tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM + "\\n" + _SYSTEM_PROMPT_ADDITION
)

print(
    f"duckv3: patched ToolAgent._build_user_prompt "
    f"(observer source {{len(_DUCKV3_OBSERVER_SOURCE)}} chars), "
    f"system prompt +{{len(_SYSTEM_PROMPT_ADDITION)}} chars"
)
'''


def main() -> None:
    nb = json.loads(DUCKMOD_NB.read_text(encoding="utf-8"))
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
        raise RuntimeError("duckv3: could not find cell id=12 in duckmod notebook")

    OUT_NB.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT_NB} ({OUT_NB.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
