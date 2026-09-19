"""thui-a10: B81 (thui-a5 KV7/MTP0/seqs28) with world-model slots ALSO filled from the model's reasoning. One change.

Design: workspace notes/DESIGN-textual-world-model-experiment-2026-09-19.md, arm A1'(b). A1'(a) (thui-a9, the
`World model:` line REQUIRED) was KILLED at G1 twice (cost + compliance), which closes (a) and leaves (b).
The chassis keeps seven slots, parsed ONLY from the VISIBLE `content` and ONLY when content is non-empty
(`tool_agent.py` analyze(), two `_update_summarized_knowledge_from_assistant(content)` sites @ 01e36e6).
Step 0 (a1_step0_v2): in B81, the reasoning fills a slot the visible text did not in 25/25 games
(`World model` 17/25), but thinking-sourced values reach 35,907 chars -- the extractor and the render cap nothing.

Mechanism: ONE wrapper on the imported module function `_format_model_response_meta`, which analyze() calls
on every response with keyword `reasoning=` and `content=`. After the original runs, it parses the reasoning
with the chassis's own `_extract_scientist_note` and writes a slot ONLY where the same response's visible
content wrote nothing, capped at CAP chars with the chassis's own `_normalize_summary_text`. The visible path
is byte-for-byte untouched (visible values are never capped, and they still overwrite later in the same
response), so the cap binds only the new source. `self` is read from the caller frame (analyze), no globals
shared across game threads. --control: identical notebook, no wrapper, marker `THUI_A10_GRAFT control`.

Build:  python3 thui-a10/build_notebook.py --smoke            -> out/thui-a10-thk-smoke
        python3 thui-a10/build_notebook.py --smoke --control  -> out/thui-a10-ctl-smoke
        python3 thui-a10/build_notebook.py [--control] [--run=N] -> out/thui-a10-{thk,ctl}-full25-rN
Teeth:  thui-a10/test_a10_graft.py  (0 GPU: runs the built GRAFT against the REAL localrig tool_agent module)
Push:   python3 scripts/kaggle_push_kernel.py <out dir>   (from the workspace repo)
"""
import ast
import copy
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "thui-a5" / "out" / "thui-a5-mtp0k7s28-full25-r1" / "thui-a5-mtp0k7s28-full25-r1.ipynb"
SRC_META = HERE.parent / "thui-a5" / "out" / "thui-a5-mtp0k7s28-full25-r1" / "kernel-metadata.json"
SMOKE = "--smoke" in sys.argv[1:]
CONTROL = "--control" in sys.argv[1:]
RUN = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--run=")), "1")
ARM = "ctl" if CONTROL else "thk"
SLUG = f"thui-a10-{ARM}-smoke" if SMOKE else f"thui-a10-{ARM}-full25-r{RUN}"
SMOKE_GAMES = ("tn36-ef4dde99", "vc33-5430563c", "bp35-0a0ad940")   # the thui-a3 / a6 / rank2 smoke set
SMOKE_CLOCK_S = 1800
C15_EXTRA_OLD = "    if missing or extra:\n"
C15_EXTRA_NEW = "    if missing or (extra and len(PUBLIC_GAME_IDS) == 25):   # thui-a10 smoke: a subset leaves extras by design\n"
C15_SELECT = "    bm.games = [offline_by_id[game_id] for game_id in PUBLIC_GAME_IDS]\n"
OUT = HERE / "out" / SLUG

IMPORT_ANCHOR = "import inference.agent.tool_agent as _tool_agent\n"

CAP = 488   # chars per thinking-sourced slot: 2x B81's median voluntary `World model` (244), the a9 K3 line

GRAFT = f'''# ---- thui-a10: slots also filled from the reasoning where the visible text left them empty, capped.
import inspect as _inspect
import sys as _sys
_A10_CAP = {CAP}
_A10_CLS = _tool_agent.ToolAgent
_a10_src = _inspect.getsource(_A10_CLS.analyze)
assert _a10_src.count("response_meta = _format_model_response_meta(") == 1, "thui-a10: meta call site moved -- re-derive"
assert _a10_src.count("reasoning=reasoning,") == 1 and _a10_src.count("content=content,") == 1, \\
    "thui-a10: meta call no longer passes reasoning/content by keyword -- re-derive"
assert _a10_src.count("self._update_summarized_knowledge_from_assistant(content)") == 2, \\
    "thui-a10: visible update sites moved -- re-derive"
_a10_orig = _tool_agent._format_model_response_meta
THUI_A10_COUNTS = {{"calls": 0, "responses_filled": 0, "slots_filled": 0, "no_self": 0, "errors": 0}}


def _a10_meta(*args, **kwargs):
    out = _a10_orig(*args, **kwargs)
    try:
        THUI_A10_COUNTS["calls"] += 1
        agent = _sys._getframe(1).f_locals.get("self")
        if not isinstance(agent, _A10_CLS):
            THUI_A10_COUNTS["no_self"] += 1
            if THUI_A10_COUNTS["no_self"] == 1:
                print("THUI_A10_NO_SELF first", flush=True)
            return out
        if THUI_A10_COUNTS["calls"] == 1:
            print("THUI_A10_APPLIED first", flush=True)
        reasoning = kwargs.get("reasoning") or ""
        if not reasoning.strip():
            return out
        content = kwargs.get("content") or ""
        seen = _tool_agent._extract_scientist_note(content) if content.strip() else {{}}
        got = _tool_agent._extract_scientist_note(reasoning)
        n = 0
        for key, value in got.items():
            if value and not seen.get(key):
                agent._summarized_knowledge[key] = _tool_agent._normalize_summary_text(value, max_chars=_A10_CAP)
                n += 1
        if n:
            THUI_A10_COUNTS["slots_filled"] += n
            THUI_A10_COUNTS["responses_filled"] += 1
            if THUI_A10_COUNTS["responses_filled"] in (1, 10) or THUI_A10_COUNTS["responses_filled"] % 100 == 0:
                print(f"THUI_A10_FILLED {{THUI_A10_COUNTS}}", flush=True)
    except Exception as exc:  # the lever must never cost a response
        THUI_A10_COUNTS["errors"] += 1
        if THUI_A10_COUNTS["errors"] == 1:
            print(f"THUI_A10_ERROR first {{type(exc).__name__}}: {{exc}}", flush=True)
    return out


_a10_meta.__wrapped__ = _a10_orig
_tool_agent._format_model_response_meta = _a10_meta
assert _tool_agent._format_model_response_meta is _a10_meta, "thui-a10: wrapper not installed"
print(f"THUI_A10_GRAFT ok cap={{_A10_CAP}} cls={{_A10_CLS.__module__}}.{{_A10_CLS.__name__}} file={{_tool_agent.__file__}}", flush=True)
'''
CONTROL_MARK = 'print("THUI_A10_GRAFT control (no wrapper; extraction unchanged)", flush=True)\n'

CELL0 = f"""# {SLUG} (Thuitanium / Knowless Crew) — the B81 anim build, {"CONTROL (unchanged)" if CONTROL else "world-model slots also filled from reasoning"}

{"**Smoke: 3 games at 1800 s. Numbers are not a score.**" if SMOKE else "Full public 25."}

**This is a Knowless Crew / Thuitanium experiment notebook.** Solver, prompts, clock, games and the vLLM profile
(KV 7 GiB / MTP 0 / max_num_seqs 28) are exactly `thui-a5-mtp0k7s28-full25-r1`. {"Nothing changes: this is the same-day control for `thui-a10-thk`." if CONTROL else f"One change: world-model slots the visible reply left empty are also filled from the model's reasoning, capped at {CAP} chars, via a wrapper on the imported response-meta function in cell 9."}

Serving stack by [Keith Tyser](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp), harness by
[Tufa Labs](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner), anim solver
bundle `jakobbrggen/taaf-kaggle-source-anim-20260807-anim`.
"""


def patch_cell9(s9: str) -> str:
    assert s9.count(IMPORT_ANCHOR) == 1, f"cell 9 anchor moved -- re-derive: {IMPORT_ANCHOR!r}"
    return s9.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + (CONTROL_MARK if CONTROL else GRAFT))


def main():
    nb = json.load(open(SRC_NB))
    orig = copy.deepcopy(nb)
    cells = nb["cells"]
    assert "Knowless Crew" in "".join(cells[0]["source"])
    cells[0]["source"] = CELL0.splitlines(keepends=True)
    cells[9]["source"] = patch_cell9("".join(cells[9]["source"])).splitlines(keepends=True)
    if SMOKE:
        s = "".join(cells[15]["source"])
        m = re.search(r"PUBLIC_GAME_IDS = tuple\(\[\n(?:    \"[a-z0-9]{4}-[0-9a-f]{8}\",?\n){25}\]\)\n", s)
        assert m, "cell 15: the 25-game PUBLIC_GAME_IDS tuple not found"
        assert all(f'"{g}"' in m.group(0) for g in SMOKE_GAMES)
        s = s.replace(m.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-a10 smoke subset\n")
        assert s.count("!= 25") == 2 and s.count(C15_EXTRA_OLD) == 1 and s.count(C15_SELECT) == 1
        s = s.replace("!= 25", "!= len(PUBLIC_GAME_IDS)").replace(C15_EXTRA_OLD, C15_EXTRA_NEW).replace(
            C15_SELECT, C15_SELECT + f"    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-a10 smoke clock\n"
            '    print(f"thui-a10: smoke {len(bm.games)} games @ {bm.solver.max_runtime_s_per_game} s", flush=True)\n')
        cells[15]["source"] = s.splitlines(keepends=True)
        compile(s, "cell15", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    changed = [i for i, (a, b) in enumerate(zip(orig["cells"], cells)) if a != b]
    assert changed == ([0, 9, 15] if SMOKE else [0, 9]), changed
    assert len(orig["cells"]) == len(cells)
    compile("".join(cells[9]["source"]), "cell9", "exec")
    meta = json.load(open(SRC_META))
    meta.update(id=f"yocybercode/{SLUG}", title=SLUG, code_file=f"{SLUG}.ipynb", is_private=True)
    assert meta["id"].startswith("yocybercode/")
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(nb, open(OUT / f"{SLUG}.ipynb", "w"), indent=1)
    json.dump(meta, open(OUT / "kernel-metadata.json", "w"), indent=2)
    print(f"built {SLUG}: cells changed {changed}, id {meta['id']}, private, datasets={meta['dataset_sources']}")


if __name__ == "__main__":
    main()
