"""Build thui-b106 CognitiveMap for B81/B99, arm/control, without running it."""

import ast
import copy
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
OWNER = next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--owner=")), "yocybercode")
BASE = next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--base=")), None)
CONTROL = "--control" in sys.argv[1:]
assert BASE in {"b81", "b99"}, "required: --base=b81|b99"
assert set(arg for arg in sys.argv[1:] if not arg.startswith("--owner=")) <= {f"--base={BASE}", "--control"}

if BASE == "b81":
    BASE_DIR = HERE.parent / "thui-a5" / "out" / "thui-a5-mtp0k7s28-full25-r1"
    BASE_SLUG = "thui-a5-mtp0k7s28-full25-r1"
else:
    BASE_DIR = HERE.parent / "thui-b99" / "out" / "thui-b99-rungpin-full25-r1"
    BASE_SLUG = "thui-b99-rungpin-full25-r1"

SRC_NB = BASE_DIR / f"{BASE_SLUG}.ipynb"
SRC_META = BASE_DIR / "kernel-metadata.json"
SLUG = f"thui-b106-{'ctl' if CONTROL else 'map'}-{BASE}-full25-r2"  # r2: frontier name fix
OUT = HERE / "out" / SLUG
GRAFT = (HERE / "graft_src.py").read_text(encoding="utf-8")
if CONTROL:
    assert GRAFT.count("_THUI_B106_MAP = True") == 1
    GRAFT = GRAFT.replace("_THUI_B106_MAP = True", "_THUI_B106_MAP = False")


def committed_cell9_tail(source):
    marker = 'assert os.environ["LOCAL_ANALYZER_MODEL_ID"]'
    start = source.rfind(marker)
    assert start >= 0, f"{BASE}: animfast tail marker moved -- re-derive"
    tail = source[start:]
    assert 'print(f"THUI_ANIMFAST_GRAFT ok' in tail and source.endswith(tail)
    return tail


def cell0_text():
    control_text = (
        " The control computes and counts the host-map note but does not show it."
        if CONTROL else ""
    )
    return f"""# {SLUG} (Thuitanium / Knowless Crew) — CognitiveMap on {BASE.upper()}

**Full run: all 25 public games at the {BASE.upper()} clock.**

**This is a Knowless Crew / Thuitanium experiment notebook.** Solver, prompts, games, clock and the vLLM profile
(KV 7 GiB / MTP 0 / max_num_seqs 28) are exactly the committed {BASE.upper()} build. The one change, at the end
of cell 9: the host records the NoopGuard state graph and adds a compact English map note to the user prompt.{control_text}

Ported from [Julian Camilo Villa's public notebook](https://www.kaggle.com/code/juliancamilovilla/arc-agi3-animfast-map),
cell 14 (Apache-2.0). Serving stack by [Keith Tyser](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp),
harness by [Tufa Labs](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner),
anim solver bundle `jakobbrggen/taaf-kaggle-source-anim-20260807-anim`.
"""


def main():
    notebook = json.loads(SRC_NB.read_text(encoding="utf-8"))
    original = copy.deepcopy(notebook)
    cells = notebook["cells"]
    assert len(cells) == 18
    assert "Knowless Crew" in "".join(cells[0]["source"])
    cells[0]["source"] = cell0_text().splitlines(keepends=True)

    source9 = "".join(cells[9]["source"])
    tail_anchor = committed_cell9_tail(source9)
    assert source9.endswith(tail_anchor)
    assert "import inference.agent.tool_agent as _tool_agent" in source9
    source9 += GRAFT
    compile(source9, "cell9", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    cells[9]["source"] = source9.splitlines(keepends=True)

    changed = [index for index, pair in enumerate(zip(original["cells"], cells)) if pair[0] != pair[1]]
    assert changed == [0, 9], changed
    assert len(original["cells"]) == len(cells)
    body = json.dumps([cell["source"] for cell in cells[1:]])
    assert "".join(cells[9]["source"]).endswith(GRAFT)
    assert body.count("_thui_b106_tool_agent.ToolAgent._ensure_session = _thui_b106_ensure_session") == 1
    assert body.count("_thui_b106_tool_agent.ToolAgent._build_user_prompt = _thui_b106_build_user_prompt") == 1
    assert body.count("_THUI_B106_MAP = False" if CONTROL else "_THUI_B106_MAP = True") == 1
    assert body.count("THUI_B106_GRAFT ok") == 1
    assert body.count("_thui_b106_ENGINE_TO_MODEL = {") == 1, "r2 frontier fix missing"
    assert body.count("THUI_B106_STATS map=") == 1
    assert body.count(str(7 * 1024 ** 3)) == 1, "serving profile must stay KV 7 GiB"
    assert '"TAAF_VLLM_ENABLE_PREFIX_CACHING": "0"' in "".join(cells[3]["source"])
    assert "PUBLIC_GAME_IDS = tuple([" in "".join(cells[15]["source"]), "25-game tuple must stay intact"
    assert source9.index("THUI_ANIMFAST_GRAFT ok") < source9.index("_THUI_B106_MAP = ")
    assert not any(f"_thui_b{number}_" in body for number in (100, 101, 103, 104, 105))
    assert "_thui_ap_" not in body
    if BASE == "b99":
        assert "THUI_B99_GRAFT ok" in body and "_b99_" in body
    else:
        assert "THUI_B99_GRAFT ok" not in body and "_b99_" not in body

    source_meta = json.loads(SRC_META.read_text(encoding="utf-8"))
    metadata = copy.deepcopy(source_meta)
    metadata.update(id=f"{OWNER}/{SLUG}", title=SLUG, code_file=f"{SLUG}.ipynb", is_private=True)
    assert metadata["id"] == f"{OWNER}/{SLUG}" and metadata["is_private"] is True
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{SLUG}.ipynb").write_text(json.dumps(notebook, indent=1), encoding="utf-8")
    (OUT / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"built {SLUG}: cells changed {changed}, id={metadata['id']}, private=True, graft {len(GRAFT)} chars")


if __name__ == "__main__":
    main()
