"""thui-b100: MAP B100 OutcomeSieve on B81 (thui-a5 KV7/MTP0/seqs28), keep rule revised with Watchara 2026-09-22. One change.

The graft (`graft_src.py`, the SAME bytes `test_b100_graft.py` executes against the real ToolAgent._chat_completion) is
appended to the end of cell 9: each request is sent a COPY of the messages in which the stored `reasoning` key is
removed only from assistant messages of levels already LEFT, except the level-clearing message; every message of the
current level keeps its reasoning. --control builds the identical notebook with _THUI_B100_STRIP = False (logging only),
so both arms report prompt tokens on the same instrument.

Smoke pair (all 25 public games, per-game clock 1,800 s): thui-b100-v0-smoke25 and thui-b100-ctl-smoke25, cells [0, 9, 15].
Read: thui-b100/PREDICTIONS.md (written before push). Reader: thui-b100/b100_read.py. Test: thui-b100/test_b100_graft.py.
"""
import ast
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "thui-a5" / "out" / "thui-a5-mtp0k7s28-full25-r1" / "thui-a5-mtp0k7s28-full25-r1.ipynb"
SRC_META = HERE.parent / "thui-a5" / "out" / "thui-a5-mtp0k7s28-full25-r1" / "kernel-metadata.json"
OWNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), "sahasawatt")
CONTROL = "--control" in sys.argv[1:]
SLUG = "thui-b100-ctl-smoke25" if CONTROL else "thui-b100-v0-smoke25"
OUT = HERE / "out" / SLUG
CLOCK_S = 1800
GRAFT = (HERE / "graft_src.py").read_text(encoding="utf-8")
if CONTROL:
    assert GRAFT.count("_THUI_B100_STRIP = True") == 1
    GRAFT = GRAFT.replace("_THUI_B100_STRIP = True", "_THUI_B100_STRIP = False")

CELL9_TAIL = """      f"temperature={os.environ['LOCAL_ANALYZER_TEMPERATURE']} upscale={os.environ['MULTIMODAL_UPSCALE']}", flush=True)
"""
SELECT = "    bm.games = [offline_by_id[game_id] for game_id in PUBLIC_GAME_IDS]\n"
CLOCK_NEW = SELECT + (
    f"    bm.solver.max_runtime_s_per_game = {CLOCK_S}.0   # thui-b100 smoke clock\n"
    f'    print(f"THUI_B100_SMOKE arm={'ctl' if CONTROL else 'b100'} games={{len(bm.games)}} clock={{bm.solver.max_runtime_s_per_game}}", flush=True)\n')

CELL0 = f"""# {SLUG} (Thuitanium / Knowless Crew) — the B81 build that stops re-sending reasoning from levels already left

**Smoke: all 25 public games at a 1,800 s clock. Numbers are not a score.**

**This is a Knowless Crew / Thuitanium experiment notebook.** Solver, prompts, games and the vLLM profile
(KV 7 GiB / MTP 0 / max_num_seqs 28) are exactly `thui-a5-mtp0k7s28-full25-r1`; the per-game clock is 1,800 s.
The one change, at the end of cell 9: each request is sent without the stored thinking of assistant messages from
levels the agent has already left, except the message that cleared a level; the current level keeps all of it.
{"CONTROL build: the same wrapper only LOGS (nothing is removed)." if CONTROL else ""}

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

    s15 = "".join(cells[15]["source"])
    assert s15.count(SELECT) == 1, "cell 15 game-selection line moved -- re-derive"
    s15 = s15.replace(SELECT, CLOCK_NEW)
    compile(s15, "cell15", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    cells[15]["source"] = s15.splitlines(keepends=True)

    changed = [i for i, (a, b) in enumerate(zip(orig["cells"], cells)) if a != b]
    assert changed == [0, 9, 15], changed
    assert len(orig["cells"]) == len(cells)

    body = json.dumps([c["source"] for c in cells[1:]])
    assert "".join(cells[9]["source"]).endswith(GRAFT), "cell 9 must END with the exact tested graft bytes"
    assert body.count("_tool_agent.ToolAgent._chat_completion = _thui_b100_chat_completion") == 1
    assert body.count("THUI_B100_GRAFT ok") == 1 and body.count("THUI_B100_STATS strip=") == 1
    assert body.count("_THUI_B100_STRIP = False" if CONTROL else "_THUI_B100_STRIP = True") == 1
    assert body.count('print(f\\"THUI_B100_SMOKE arm=') == 1
    assert body.count(f"max_runtime_s_per_game = {CLOCK_S}.0") == 1
    assert body.count(str(7 * 1024 ** 3)) == 1, "serving profile must stay B81 (KV 7 GiB)"
    assert '"TAAF_VLLM_ENABLE_PREFIX_CACHING": "0"' in "".join(cells[3]["source"]), "prefix caching must stay off"
    assert '\\"LOCAL_ANALYZER_TOOL_OUTPUT_TOKENS\\"' not in body, "must not carry the thui-to knob -- one change"
    assert "_thui_ap_" not in body, "must not carry the thui-ap graft -- one change"
    assert "_thui_tb_" not in body and "_thui_p3_" not in body, "one change only"
    assert "PUBLIC_GAME_IDS = tuple([" in "".join(cells[15]["source"]), "25-game tuple must stay intact"
    # the graft must come AFTER the harness import and its teeth
    assert s9.index("THUI_ANIMFAST_GRAFT ok") < s9.index("_thui_b100_orig_cc = _tool_agent.ToolAgent._chat_completion")

    meta = json.load(open(SRC_META, encoding="utf-8"))
    meta.update(id=f"{OWNER}/{SLUG}", title=SLUG, code_file=f"{SLUG}.ipynb", is_private=True)
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(nb, open(OUT / f"{SLUG}.ipynb", "w", encoding="utf-8"), indent=1)
    json.dump(meta, open(OUT / "kernel-metadata.json", "w", encoding="utf-8"), indent=2)
    print(f"built {SLUG}: cells changed {changed}, id {meta['id']}, private, gpu={meta.get('enable_gpu')}, "
          f"machine={meta.get('machine_shape')}, graft {len(GRAFT)} chars")


if __name__ == "__main__":
    main()
