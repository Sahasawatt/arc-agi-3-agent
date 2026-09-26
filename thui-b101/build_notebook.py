"""thui-b101: MAP B101 KeepOnDeath on B81 (thui-a5 KV7/MTP0/seqs28), full clock. One change.

The graft (`graft_src.py`, the SAME bytes `test_b101_graft.py` executes against the real
ToolAgent._update_summarized_knowledge_from_step_summary) is appended to the end of cell 9: a death alone no longer
wipes the six summarized-knowledge slots; level-transition and run-complete wipes stay. --control builds the identical
notebook with _THUI_B101_KEEP = False (B81's wipe, same counters), so both arms report on the same instrument.

Full pair (all 25 public games, B81 clock): thui-b101-keep-full25-r1 and thui-b101-ctl-full25-r1, cells [0, 9].
Read: thui-b101/PREDICTIONS.md (written before build). Test: thui-b101/test_b101_graft.py.
"""
import ast
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "thui-a5" / "out" / "thui-a5-mtp0k7s28-full25-r1" / "thui-a5-mtp0k7s28-full25-r1.ipynb"
SRC_META = HERE.parent / "thui-a5" / "out" / "thui-a5-mtp0k7s28-full25-r1" / "kernel-metadata.json"
OWNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), "yocybercode")
CONTROL = "--control" in sys.argv[1:]
SLUG = "thui-b101-ctl-full25-r1" if CONTROL else "thui-b101-keep-full25-r1"
OUT = HERE / "out" / SLUG
GRAFT = (HERE / "graft_src.py").read_text(encoding="utf-8")
if CONTROL:
    assert GRAFT.count("_THUI_B101_KEEP = True") == 1
    GRAFT = GRAFT.replace("_THUI_B101_KEEP = True", "_THUI_B101_KEEP = False")

CELL9_TAIL = """      f"temperature={os.environ['LOCAL_ANALYZER_TEMPERATURE']} upscale={os.environ['MULTIMODAL_UPSCALE']}", flush=True)
"""

CELL0 = f"""# {SLUG} (Thuitanium / Knowless Crew) — the B81 build that keeps its written notes across a death

**Full run: all 25 public games at the B81 clock.**

**This is a Knowless Crew / Thuitanium experiment notebook.** Solver, prompts, games, clock and the vLLM profile
(KV 7 GiB / MTP 0 / max_num_seqs 28) are exactly `thui-a5-mtp0k7s28-full25-r1`.
The one change, at the end of cell 9: when the agent dies inside a level, the six summarized-knowledge slots it had
written are kept instead of wiped; a level transition still wipes them.
{"CONTROL build: the same wrapper wipes on death exactly as B81 does, and only counts." if CONTROL else ""}

Serving stack by [Keith Tyser](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp), harness by
[Tufa Labs](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner), anim solver
bundle `jakobbrggen/taaf-kaggle-source-anim-20260807-anim`.
"""


def main():
    nb = json.load(open(SRC_NB, encoding="utf-8"))
    orig = copy.deepcopy(nb)
    cells = nb["cells"]
    assert "Knowless Crew" in "".join(cells[0]["source"])
    cells[0]["source"] = CELL0.splitlines(keepends=True)

    s9 = "".join(cells[9]["source"])
    assert s9.endswith(CELL9_TAIL), "cell 9 no longer ends with the graft-teeth print -- re-derive the anchor"
    assert "import inference.agent.tool_agent as _tool_agent" in s9
    s9 = s9 + GRAFT
    compile(s9, "cell9", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    cells[9]["source"] = s9.splitlines(keepends=True)

    changed = [i for i, (a, b) in enumerate(zip(orig["cells"], cells)) if a != b]
    assert changed == [0, 9], changed
    assert len(orig["cells"]) == len(cells)

    body = json.dumps([c["source"] for c in cells[1:]])
    assert "".join(cells[9]["source"]).endswith(GRAFT), "cell 9 must END with the exact tested graft bytes"
    assert body.count("_tool_agent.ToolAgent._update_summarized_knowledge_from_step_summary = _thui_b101_update") == 1
    assert body.count("THUI_B101_GRAFT ok") == 1 and body.count("THUI_B101_STATS keep=") == 1
    assert body.count("_THUI_B101_KEEP = False" if CONTROL else "_THUI_B101_KEEP = True") == 1
    assert body.count(str(7 * 1024 ** 3)) == 1, "serving profile must stay B81 (KV 7 GiB)"
    assert '"TAAF_VLLM_ENABLE_PREFIX_CACHING": "0"' in "".join(cells[3]["source"]), "prefix caching must stay off"
    assert "_thui_b100_" not in body and "_thui_b99_" not in body and "_thui_ap_" not in body, "one change only"
    assert "PUBLIC_GAME_IDS = tuple([" in "".join(cells[15]["source"]), "25-game tuple must stay intact"
    assert s9.index("THUI_ANIMFAST_GRAFT ok") < s9.index("_THUI_B101_KEEP = ")

    meta = json.load(open(SRC_META, encoding="utf-8"))
    meta.update(id=f"{OWNER}/{SLUG}", title=SLUG, code_file=f"{SLUG}.ipynb", is_private=True)
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(nb, open(OUT / f"{SLUG}.ipynb", "w", encoding="utf-8"), indent=1)
    json.dump(meta, open(OUT / "kernel-metadata.json", "w", encoding="utf-8"), indent=2)
    print(f"built {SLUG}: cells changed {changed}, id {meta['id']}, private, gpu={meta.get('enable_gpu')}, "
          f"machine={meta.get('machine_shape')}, graft {len(GRAFT)} chars")


if __name__ == "__main__":
    main()
