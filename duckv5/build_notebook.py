"""Build duckv5/taaf-duck-v5.ipynb: duckmod's own cell 12 (HUD auto-flag +
TransitionGraph callable tool, verbatim) PLUS three new server-side state patches
appended to the SAME cell -- accumulating world-model fields, an auto-injected
transition digest, and a silent-reset banner. v5 = duckmod + these three; nothing from
v4 (the reallocator and world-model char-cap measured inert/never-fired,
results/wayfinder/R7-v4-postmortem.md).

Source of truth = duckv5_worldmodel_accum.py + duckv5_digest.py (the modules) + this
script + duckmod's own already-built notebook; the .ipynb is a generated artifact,
never hand-edited, same discipline the repo's CLAUDE.md states for kaggle/my_agent.py
(and duckv3/duckv4's own build scripts already apply one level up). Run:

    python duckv5/build_notebook.py
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DUCKMOD_NB = REPO_ROOT / "duckmod" / "taaf-duck-mod.ipynb"
ACCUM_SRC = REPO_ROOT / "duckv5" / "duckv5_worldmodel_accum.py"
DIGEST_SRC = REPO_ROOT / "duckv5" / "duckv5_digest.py"
OUT_NB = REPO_ROOT / "duckv5" / "taaf-duck-v5.ipynb"

_SYSTEM_PROMPT_ADDITION = (
    "A PROGRESS DIGEST block is auto-appended each turn (no function call needed): "
    "per-action tried/changed/noop counts, levels reached and when, and your last 5 "
    "actions with outcomes. A '!!! GAME RESET !!!' line appears on the turn right "
    "after a GAME_OVER or level regression -- treat it as authoritative: your prior "
    "position and state assumptions are invalid."
)


def _source_without_demo(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    marker = '\nif __name__ == "__main__":'
    idx = text.index(marker)
    return text[:idx].rstrip() + "\n"


def _duckmod_cell12_source() -> str:
    nb = json.loads(DUCKMOD_NB.read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        if cell.get("id") == "12":
            return "".join(cell["source"])
    raise RuntimeError("duckv5: could not find cell id=12 in duckmod's notebook")


def _cell12_source() -> str:
    duckmod_source = _duckmod_cell12_source().rstrip("\n")
    accum_source = _source_without_demo(ACCUM_SRC)
    digest_source = _source_without_demo(DIGEST_SRC)
    return f'''{duckmod_source}

# === duckv5: accumulating world model + auto-injected transition digest/reset banner ===
# Stacks on duckmod's patch above (same cell, same already-imported `tool_agent`
# module from the `from inference.agent import tool_agent, python_tool_sandbox` line
# at the top of this cell) -- two independent, additional patches:
#   (1) ToolAgent._update_summarized_knowledge_from_assistant now ACCUMULATES each
#       labeled field turn-over-turn (turn-stamped, exact-duplicate-paragraph dedup,
#       bounded with oldest-first trim) instead of overwriting it every turn -- R7
#       sec5 measured this is the call site duckv4's world-model cap missed: the
#       field never grows under the harness's own overwrite design, so a char cap on
#       the PARSER never fires. Capping the MERGE step instead means the bound now
#       actually matters.
#   (2) ToolAgent._build_user_prompt gets a compact PROGRESS DIGEST block appended
#       every turn (per-action outcome counts, levels reached, last 5 actions) plus a
#       one-shot "!!! GAME RESET !!!" banner on the turn right after a GAME_OVER or
#       level regression. Targets R6's Mode 2 (anti-loop tooling present every
#       prompt, called 0/0 times across the 9 worst-thrashing games) and Mode 3
#       (silent resets erasing 75-300 actions of progress, confirmed in 6/9 and
#       inferred in a 7th) structurally: the harness computes and shows, there is
#       nothing new for the model to call.
# Neither patch touches HarnessSolver/_HarnessGameSession (v4's reallocator target) --
# out of scope for v5 by design (v4's reallocator measured inert on the games that
# matter and is not carried forward). See results/duckv5-build-20260820.md for the
# full design writeup.

_DUCKV5_ACCUM_SOURCE = {accum_source!r}
exec(compile(_DUCKV5_ACCUM_SOURCE, "<duckv5_worldmodel_accum>", "exec"), globals())
install_patch(tool_agent)
_duckv5_accum_chars = len(_DUCKV5_ACCUM_SOURCE)

_DUCKV5_DIGEST_SOURCE = {digest_source!r}
_duckv5_digest_ns = {{}}
exec(compile(_DUCKV5_DIGEST_SOURCE, "<duckv5_digest>", "exec"), _duckv5_digest_ns)
_duckv5_digest_ns["install_patch"](tool_agent)
_duckv5_digest_chars = len(_DUCKV5_DIGEST_SOURCE)

_DUCKV5_SYSTEM_PROMPT_ADDITION = {_SYSTEM_PROMPT_ADDITION!r}
tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM = (
    tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM + "\\n" + _DUCKV5_SYSTEM_PROMPT_ADDITION
)

print(
    f"duckv5: patched ToolAgent._update_summarized_knowledge_from_assistant "
    f"(accumulate source {{_duckv5_accum_chars}} chars), "
    f"patched ToolAgent._build_user_prompt "
    f"(digest source {{_duckv5_digest_chars}} chars), "
    f"system prompt +{{len(_DUCKV5_SYSTEM_PROMPT_ADDITION)}} chars"
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
        raise RuntimeError("duckv5: could not find cell id=12 in duckmod's notebook")

    OUT_NB.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT_NB} ({OUT_NB.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
