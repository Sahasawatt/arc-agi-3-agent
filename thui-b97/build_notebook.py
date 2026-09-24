"""thui-b97: MAP B97 on the B81 base (thui-a5 KV7/MTP0/seqs28) -- window 48k with the KV that pays for it.

Two changes against the base, by design (the row says so):
  cell 3  TAAF_VLLM_KV_CACHE_MEMORY_BYTES 7 GiB -> 13.5 GiB
  cell 9  the setup commands are rewritten before any of them runs: VLLM_MAX_MODEL_LEN 32768 -> 65536 (the
          server's ceiling on prompt PLUS completion) and ANALYZER_CONTEXT_WINDOW 32768 -> 49152 (the agent's
          prompt budget, 48128 after the 1024 reserve).

13.5 GiB is the number that keeps concurrency: B87 measured KV tokens linear in bytes (263,568 at 7 GiB,
452,340 at 12), so 13.5 GiB is ~508,900 tokens, and at the ~48k prompts this window invites that is ~10.6
concurrent against the ~10.5 the 7 GiB / ~25k-prompt base runs at today. KV 12 alone would be ~9.4.

--control builds the identical notebook at the BASE window and BASE KV, so the pair differs only in these
two numbers and both arms report on the same instrument.

Smoke pair (all 25 public games, per-game clock 1,800 s): thui-b97-v0-smoke25 and thui-b97-ctl-smoke25.
Read: thui-b97/PREDICTIONS.md (written before push). Teeth: thui-b97/test_b97_window.py.
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
SLUG = "thui-b97-ctl-smoke25" if CONTROL else "thui-b97-v0-smoke25"
OUT = HERE / "out" / SLUG
CLOCK_S = 1800
KV_BASE, KV_NEW = 7 * 1024 ** 3, 27 * 1024 ** 3 // 2          # 7 GiB -> 13.5 GiB
WINDOW = (HERE / "window_src.py").read_text(encoding="utf-8")

CELL3_KV = (f'    "TAAF_VLLM_KV_CACHE_MEMORY_BYTES": "{KV_BASE}",', f'    "TAAF_VLLM_KV_CACHE_MEMORY_BYTES": "{KV_NEW}",')
CELL3_ASSERT = ('assert PUBLIC25_VLLM_PROFILE_ENV["TAAF_VLLM_KV_CACHE_MEMORY_BYTES"] == str(7 * 1024 ** 3)',
                'assert PUBLIC25_VLLM_PROFILE_ENV["TAAF_VLLM_KV_CACHE_MEMORY_BYTES"] == str(27 * 1024 ** 3 // 2)')
CELL3_NAME = ("PUBLIC25_VLLM_PROFILE_NAME = 'kv7-bf16-mtp0-c28-cg32'", "PUBLIC25_VLLM_PROFILE_NAME = 'kv13p5-bf16-mtp0-c28-cg32'")
CELL3_PRINT = ('print("THUI_A5_PROFILE ok mtp=0 kv=7GiB seqs=28", flush=True)',
               'print("THUI_A5_PROFILE ok mtp=0 kv=13.5GiB seqs=28", flush=True)')

CELL9_ANCHOR = "# Solver setup commands (wheels, vLLM server startup, ...) run before the benchmark loads.\nenv = _command_env()\n"
CELL9_LOOP = 'for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):\n'
CELL9_LOOP_NEW = 'for command in _thui_b97_rewrite(json.loads((BUNDLE_DIR / "setup_commands.json").read_text())):\n'

SELECT = "    bm.games = [offline_by_id[game_id] for game_id in PUBLIC_GAME_IDS]\n"
ARM = "ctl" if CONTROL else "b97"
CLOCK_NEW = SELECT + (
    f"    bm.solver.max_runtime_s_per_game = {CLOCK_S}.0   # thui-b97 smoke clock\n"
    f'    print(f"THUI_B97_SMOKE arm={ARM} games={{len(bm.games)}} clock={{bm.solver.max_runtime_s_per_game}}", flush=True)\n')

CELL0 = f"""# {SLUG} (Thuitanium / Knowless Crew) — a 48k prompt window with the KV cache that pays for it

**Smoke: all 25 public games at a 1,800 s clock. Numbers are not a score.**

**This is a Knowless Crew / Thuitanium experiment notebook.** Solver, prompts and games are exactly
`thui-a5-mtp0k7s28-full25-r1`; the per-game clock is 1,800 s.
{"CONTROL build: the base window (32768) and the base KV (7 GiB) — this arm changes nothing."
 if CONTROL else
 "Two changes: the vLLM KV cache goes 7 GiB -> 13.5 GiB (cell 3), and the setup commands are rewritten before "
 "they run so the server accepts 65536 tokens while the agent's prompt budget becomes 49152 (cell 9). The KV "
 "number is chosen so concurrency does not fall at the larger prompts: B87 measured KV tokens linear in bytes."}

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

    s3 = "".join(cells[3]["source"])
    for old, new in (CELL3_KV, CELL3_ASSERT, CELL3_NAME, CELL3_PRINT):
        assert s3.count(old) == 1, f"cell 3 anchor moved -- re-derive: {old!r}"
        if not CONTROL:
            s3 = s3.replace(old, new)
    compile(s3, "cell3", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    if not CONTROL:
        cells[3]["source"] = s3.splitlines(keepends=True)

    s9 = "".join(cells[9]["source"])
    assert s9.count(CELL9_ANCHOR) == 1, "cell 9 setup-command block moved -- re-derive"
    assert s9.count(CELL9_LOOP) == 1, "cell 9 setup-command loop moved -- re-derive"
    if not CONTROL:
        s9 = s9.replace(CELL9_ANCHOR, WINDOW + "\n" + CELL9_ANCHOR).replace(CELL9_LOOP, CELL9_LOOP_NEW)
    compile(s9, "cell9", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    if not CONTROL:
        cells[9]["source"] = s9.splitlines(keepends=True)

    s15 = "".join(cells[15]["source"])
    assert s15.count(SELECT) == 1, "cell 15 game-selection line moved -- re-derive"
    s15 = s15.replace(SELECT, CLOCK_NEW)
    compile(s15, "cell15", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    cells[15]["source"] = s15.splitlines(keepends=True)

    changed = [i for i, (a, b) in enumerate(zip(orig["cells"], cells)) if a != b]
    assert changed == ([0, 15] if CONTROL else [0, 3, 9, 15]), changed
    assert len(orig["cells"]) == len(cells)

    body = json.dumps([c["source"] for c in cells[1:]])
    assert body.count(str(KV_NEW if not CONTROL else KV_BASE)) == 1, "exactly one KV byte count must ship"
    assert body.count(str(KV_BASE if not CONTROL else KV_NEW)) == 0, "the other arm's KV number must not ship"
    assert body.count("_thui_b97_rewrite(json.loads(") == (0 if CONTROL else 1)
    assert body.count("THUI_B97_WINDOW ok") == (0 if CONTROL else 1)
    assert body.count('print(f\\"THUI_B97_SMOKE arm=') == 1
    assert body.count(f"max_runtime_s_per_game = {CLOCK_S}.0") == 1
    assert '"TAAF_VLLM_ENABLE_PREFIX_CACHING": "0"' in "".join(cells[3]["source"]), "prefix caching must stay off"
    assert '"TAAF_VLLM_MAX_NUM_SEQS": "28"' in "".join(cells[3]["source"]), "seqs must stay 28 -- one axis"
    assert '"TAAF_VLLM_MTP_TOKENS": "0"' in "".join(cells[3]["source"]), "MTP must stay 0 -- one axis"
    assert "_thui_b100_" not in body and "_thui_ap_" not in body, "must carry no other graft"
    assert "PUBLIC_GAME_IDS = tuple([" in "".join(cells[15]["source"]), "25-game tuple must stay intact"
    if not CONTROL:
        # the rewrite has to be defined before the loop that consumes it
        assert s9.index("def _thui_b97_rewrite(") < s9.index(CELL9_LOOP_NEW)

    meta = json.load(open(SRC_META, encoding="utf-8"))
    meta.update(id=f"{OWNER}/{SLUG}", title=SLUG, code_file=f"{SLUG}.ipynb", is_private=True)
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(nb, open(OUT / f"{SLUG}.ipynb", "w", encoding="utf-8"), indent=1)
    json.dump(meta, open(OUT / "kernel-metadata.json", "w", encoding="utf-8"), indent=2)
    print(f"built {SLUG}: cells changed {changed}, id {meta['id']}, private, gpu={meta.get('enable_gpu')}, "
          f"machine={meta.get('machine_shape')}, kv={'13.5' if not CONTROL else '7'} GiB")


if __name__ == "__main__":
    main()
