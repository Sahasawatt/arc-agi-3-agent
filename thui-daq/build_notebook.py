"""Build DAQ smoke/full notebook arms from B81; this script never pushes."""
import ast
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "thui-a5" / "out" / "thui-a5-mtp0k7s28-full25-r1" / "thui-a5-mtp0k7s28-full25-r1.ipynb"
SRC_META = HERE.parent / "thui-a5" / "out" / "thui-a5-mtp0k7s28-full25-r1" / "kernel-metadata.json"
OWNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), "sahasawatt")
FULL, CONTROL = "--full" in sys.argv[1:], "--control" in sys.argv[1:]
RUN = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--run=")), "1")
ARM = "ctl" if CONTROL else "daq"
SLUG = (f"thui-daq-ctl-full25-r{RUN}" if CONTROL else f"thui-daq-full25-r{RUN}") if FULL else ("thui-daq-ctl-smoke25" if CONTROL else "thui-daq-v0-smoke25")
OUT = HERE / "out" / SLUG
CLOCK_S = 1800
GRAFT = (HERE / "graft_src.py").read_text(encoding="utf-8")
if CONTROL:
    assert GRAFT.count("_THUI_DAQ_ENFORCE = True") == 1
    GRAFT = GRAFT.replace("_THUI_DAQ_ENFORCE = True", "_THUI_DAQ_ENFORCE = False")

CELL9_TAIL = """      f\"temperature={os.environ['LOCAL_ANALYZER_TEMPERATURE']} upscale={os.environ['MULTIMODAL_UPSCALE']}\", flush=True)
"""
SELECT = "    bm.games = [offline_by_id[game_id] for game_id in PUBLIC_GAME_IDS]\n"
CLOCK_NEW = SELECT + (f"    bm.solver.max_runtime_s_per_game = {CLOCK_S}.0   # thui-daq smoke clock\n"
    f'    print(f"THUI_DAQ_SMOKE arm={ARM} games={{len(bm.games)}} clock={{bm.solver.max_runtime_s_per_game}}", flush=True)\n')
CELL0 = f"""# {SLUG} (Thuitanium / Knowless Crew) — B81 with a depth-aging queue before local vLLM

**{'Full: all 25 public games at the B81 clock.' if FULL else 'Smoke: all 25 public games at a 1,800 s clock. Numbers are not a score.'}**

**This is a Knowless Crew / Thuitanium experiment notebook.** Solver, prompts, games and the vLLM profile
(KV 7 GiB / MTP 0 / max_num_seqs 28) are exactly `thui-a5-mtp0k7s28-full25-r1`. The one change at the end of cell 9
is a process-wide queue: when local vLLM is saturated, deeper levels go first, while waiting requests age so they cannot starve.
{'CONTROL build: the queue records the same measurements but admits immediately.' if CONTROL else ''}

Serving stack by [Keith Tyser](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp), harness by
[Tufa Labs](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner), anim solver
bundle `jakobbrggen/taaf-kaggle-source-anim-20260807-anim`.
"""


def main():
    nb = json.load(open(SRC_NB, encoding="utf-8")); orig = copy.deepcopy(nb); cells = nb["cells"]
    assert "Knowless Crew" in "".join(cells[0]["source"])
    cells[0]["source"] = CELL0.splitlines(keepends=True)
    s9 = "".join(cells[9]["source"])
    assert s9.endswith(CELL9_TAIL) and "import inference.agent.tool_agent as _tool_agent" in s9
    s9 += GRAFT; compile(s9, "cell9", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT); cells[9]["source"] = s9.splitlines(keepends=True)
    if not FULL:
        s15 = "".join(cells[15]["source"]); assert s15.count(SELECT) == 1
        s15 = s15.replace(SELECT, CLOCK_NEW); compile(s15, "cell15", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT); cells[15]["source"] = s15.splitlines(keepends=True)
    changed = [i for i, (a, b) in enumerate(zip(orig["cells"], cells)) if a != b]
    assert changed == ([0, 9] if FULL else [0, 9, 15]), changed
    body = json.dumps([c["source"] for c in cells[1:]])
    assert "".join(cells[9]["source"]).endswith(GRAFT)
    assert body.count("THUI_DAQ_GRAFT ok") == 1 and body.count("_THUI_DAQ_ENFORCE = False" if CONTROL else "_THUI_DAQ_ENFORCE = True") == 1
    assert body.count('print(f\\"THUI_DAQ_SMOKE arm=') == (0 if FULL else 1)
    assert body.count(str(7 * 1024 ** 3)) == 1
    assert '"TAAF_VLLM_ENABLE_PREFIX_CACHING": "0"' in "".join(cells[3]["source"])
    assert all(token not in body for token in ("_thui_ap_", "THUI_B99_", "THUI_B100_", "_thui_tb_", "THUI_A6_"))
    assert (str(CLOCK_S) not in "".join(cells[15]["source"])) if FULL else body.count(f"max_runtime_s_per_game = {CLOCK_S}.0") == 1
    meta = json.load(open(SRC_META, encoding="utf-8")); meta.update(id=f"{OWNER}/{SLUG}", title=SLUG, code_file=f"{SLUG}.ipynb", is_private=True)
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(nb, open(OUT / f"{SLUG}.ipynb", "w", encoding="utf-8"), indent=1)
    json.dump(meta, open(OUT / "kernel-metadata.json", "w", encoding="utf-8"), indent=2)
    print(f"built {SLUG}: cells changed {changed}, id {meta['id']}, private")


if __name__ == "__main__": main()
