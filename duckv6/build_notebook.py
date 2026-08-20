"""Build the generated v6 notebook by stacking v6 sources on duckmod cell 12."""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DUCKMOD_NB = REPO_ROOT / "duckmod" / "taaf-duck-mod.ipynb"
ACCUM_SRC = REPO_ROOT / "duckv5" / "duckv5_worldmodel_accum.py"
HUD_SRC = REPO_ROOT / "duckv6" / "hud_semantics.py"
DIGEST_SRC = REPO_ROOT / "duckv6" / "duckv6_digest.py"
OUT_NB = REPO_ROOT / "duckv6" / "taaf-duck-v6.ipynb"
_SYSTEM_PROMPT_ADDITION = "A PROGRESS DIGEST block is auto-appended each turn, including conservative gameplay/HUD/uncertain outcomes, advisory intervention warnings, and HUD semantics when confident."


def _source_without_demo(path):
    text = path.read_text(encoding="utf-8")
    marker = "\nif __name__ == \"__main__\":"
    return text[:text.index(marker)].rstrip() + "\n"


def _duckmod_cell12_source():
    nb = json.loads(DUCKMOD_NB.read_text(encoding="utf-8"))
    return "".join(next(c for c in nb["cells"] if c.get("id") == "12")["source"])


def _cell12_source():
    return f'''{_duckmod_cell12_source().rstrip("\n")}

# === duckv6: v5 world model + HUD-aware digest and intervention advisories ===
_DUCKV6_ACCUM_SOURCE = {_source_without_demo(ACCUM_SRC)!r}
exec(compile(_DUCKV6_ACCUM_SOURCE, "<duckv5_worldmodel_accum>", "exec"), globals())
install_patch(tool_agent)
_DUCKV6_HUD_SOURCE = {_source_without_demo(HUD_SRC)!r}
exec(compile(_DUCKV6_HUD_SOURCE, "<duckv6_hud_semantics>", "exec"), globals())
_DUCKV6_DIGEST_SOURCE = {_source_without_demo(DIGEST_SRC)!r}
exec(compile(_DUCKV6_DIGEST_SOURCE, "<duckv6_digest>", "exec"), globals())
install_patch(tool_agent)
tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM = tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM + "\\n" + {_SYSTEM_PROMPT_ADDITION!r}
print(f"duckv6: world model +{{len(_DUCKV6_ACCUM_SOURCE)}} chars, HUD +{{len(_DUCKV6_HUD_SOURCE)}} chars, digest +{{len(_DUCKV6_DIGEST_SOURCE)}} chars")
'''


def main():
    nb = json.loads(DUCKMOD_NB.read_text(encoding="utf-8"))
    source = _cell12_source()
    cell = next(c for c in nb["cells"] if c.get("id") == "12")
    cell["source"] = source.splitlines(keepends=True)
    cell["outputs"] = []
    cell["execution_count"] = None
    OUT_NB.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT_NB} ({OUT_NB.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
