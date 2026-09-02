#!/usr/bin/env python3
"""thui-lora-e1 -- held-out eval: the TRAINED adapter over the 6 held-out games.

WHAT DECIDES. The LoRA arm's gate (grilled 2026-09-01) is held-out games: the adapter
trained on 19 games' winning turns must not score WORSE than base on the 6 games it never
saw (ls20, ft09, ka59, cd82, su15, wa30 -- the HELDOUT set train_lora.py excludes, byte
identical here). This kernel produces the adapter side of that comparison; the base side
is thui-v1-1's own runs restricted to the same 6 games.

HOW IT DIFFERS FROM thui-v1-1 (and from the thui-lora-v0 smoke):

  cell 0   markdown: what this run is, attribution unchanged in spirit.
  cell 8   three chained `.replace()` on the runtime `command` string
           (same anchor discipline the smoke proved):
             1. `--enable-lora --lora-modules thui-lora=/kaggle/working/adapter`
                injected before `--max-model-len` -- the pairing v0 proved serves.
             2. `'LOCAL_ANALYZER_MODEL_ID': SERVED_MODEL_NAME`  -> `: 'thui-lora'`
             3. `'INFERENCE_ANALYZER_MODEL': SERVED_MODEL_NAME` -> `: 'thui-lora'`
           SERVED_MODEL_NAME itself is NOT touched: it also names the vLLM base alias
           and the server health probe's model field, and renaming the base would break
           both. Only the two ANALYZER bindings move to the adapter, so every agent
           request routes through LoRA while the server plumbing stays stock.
           A prefix stages the trained adapter from its dataset into /kaggle/working.
  cell 14  the REAL game-selection seam (learned from the v0 smoke, whose cell-12
           `bm.games` slice was inert): filter AFTER `bm.games = _offline_games(...)`
           down to the 6 held-out games, asserted == 6.

Clock, sampler, seed, wheels: inherited from thui-v1-1 unchanged. The run plays 6 games
at the full 7920s/game clock -> worst case ~13h... which busts the 12h GPU cap, so the
clock is capped at 5400s/game here (6 x 1.5h = 9h worst case). That cap is a DEVIATION
from base conditions and the comparison must say so; base per-game wall-clock on these 6
games is far below 5400s in every census run, so the cap binds only where base also
starved.

    python3 build_notebook.py    # writes taaf-thui-lora-e1.ipynb + kernel-metadata.json
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SRC_NB = REPO / "thuiv1" / "v1-1" / "taaf-thui-v1-1.ipynb"
OUT_NB = HERE / "taaf-thui-lora-e1.ipynb"
OWNER = "sahasawatt"
SLUG = "thui-lora-e1"
ADAPTER_DATASET = "sahasawatt/thui-lora-adapter-v1"

HELDOUT = ("cd82", "ft09", "ka59", "ls20", "su15", "wa30")
GAME_CLOCK_S = 5400

CELL0_MD = """# thui-lora-e1 — held-out eval of the trained LoRA adapter

**This kernel is the adapter side of the LoRA arm's held-out gate.** It is `thui-v1-1`
byte-for-byte except three cells: the vLLM server additionally mounts the adapter trained
by `thui-lora-train` (`--enable-lora --lora-modules thui-lora=...`), the analyzer is
addressed at `thui-lora` instead of the base model, and the game list is filtered to the
six games the adapter never trained on (cd82, ft09, ka59, ls20, su15, wa30). Clock is
capped at 5400s/game to fit the GPU session; sampler and seed are inherited unchanged.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

# Prepended to cell 8: stage the trained adapter into a writable path before the server
# starts. peft's save_pretrained layout (adapter_config.json + adapter_model.safetensors)
# is exactly what vLLM --lora-modules expects.
CELL8_PREFIX = '''# --- thui-lora-e1: stage the trained adapter before the server starts -------------
import glob as _glob, os as _os, shutil as _shutil

_src = None
for _pat in ("/kaggle/input/datasets/sahasawatt/thui-lora-adapter-v1",
             "/kaggle/input/thui-lora-adapter-v1"):
    _hits = _glob.glob(_pat)
    if _hits:
        _src = _hits[0]
        break
assert _src, "thui-lora-e1: adapter dataset not mounted under either input layout"
# the adapter may sit at the dataset root or under adapter/
if _os.path.isdir(_os.path.join(_src, "adapter")):
    _src = _os.path.join(_src, "adapter")
for _req in ("adapter_config.json", "adapter_model.safetensors"):
    assert _os.path.exists(_os.path.join(_src, _req)), f"thui-lora-e1: {_req} missing at {_src}"
_ad = "/kaggle/working/adapter"
if not _os.path.isdir(_ad):
    _shutil.copytree(_src, _ad)
print(f"thui-lora-e1: adapter staged {_src} -> {_ad}", flush=True)
# ----------------------------------------------------------------------------------

'''

# The seed pin's .replace() block, verbatim from thui-v1-1's cell 8 (same anchor the
# smoke used). All three eval replaces chain immediately after it.
CHAIN_ANCHOR = (
    "        .replace(\n"
    "            \"    'LOCAL_ANALYZER_TEMPERATURE':\",\n"
    "            \"    'LOCAL_ANALYZER_SEED': '20260825',\\n    'LOCAL_ANALYZER_TEMPERATURE':\",\n"
    "        )\n"
)
EVAL_REPLACES = (
    "        .replace(\n"
    "            \"        '--max-model-len',\",\n"
    "            \"        '--enable-lora',\\n\"\n"
    "            \"        '--lora-modules',\\n\"\n"
    "            \"        'thui-lora=/kaggle/working/adapter',\\n\"\n"
    "            \"        '--max-model-len',\",\n"
    "        )\n"
    "        .replace(\n"
    "            \"'LOCAL_ANALYZER_MODEL_ID': SERVED_MODEL_NAME\",\n"
    "            \"'LOCAL_ANALYZER_MODEL_ID': 'thui-lora'\",\n"
    "        )\n"
    "        .replace(\n"
    "            \"'INFERENCE_ANALYZER_MODEL': SERVED_MODEL_NAME\",\n"
    "            \"'INFERENCE_ANALYZER_MODEL': 'thui-lora'\",\n"
    "        )\n"
)

CELL8_TEETH = (
    "    # thui-lora-e1 TEETH on the RESOLVED command: a moved anchor must fail loud, not no-op.\n"
    "    assert command.count(\"--enable-lora\") == 1, \"thui-lora-e1 TEETH FAIL: enable-lora != 1\"\n"
    "    assert \"thui-lora=/kaggle/working/adapter\" in command, \"thui-lora-e1 TEETH FAIL: lora-modules path missing\"\n"
    "    assert \"'LOCAL_ANALYZER_MODEL_ID': 'thui-lora'\" in command, \"thui-lora-e1 TEETH FAIL: analyzer model not rebound\"\n"
    "    assert \"'INFERENCE_ANALYZER_MODEL': 'thui-lora'\" in command, \"thui-lora-e1 TEETH FAIL: inference analyzer not rebound\"\n"
    "    assert \"--served-model-name\" in command, \"thui-lora-e1 TEETH FAIL: base alias flag gone\"\n"
    "    print(\"thui-lora-e1: adapter mounted, analyzer rebound to thui-lora, base alias intact\", flush=True)\n"
)

# Injected into cell 14 right after the offline game list is built -- the REAL seam.
CELL14_ANCHOR = "    bm.games = _offline_games(competition_env_files)\n"
CELL14_FILTER = (
    "    # thui-lora-e1: held-out filter -- the 6 games train_lora.py excluded, verbatim.\n"
    "    _HELD = " + repr(HELDOUT) + "\n"
    "    _n0 = len(bm.games)\n"
    "    bm.games = [g for g in bm.games if any(g.env_name.startswith(h) for h in _HELD)]\n"
    "    print(f\"thui-lora-e1: held-out filter {_n0} -> {len(bm.games)} games\", flush=True)\n"
    "    assert len(bm.games) == 6, f\"thui-lora-e1: expected 6 held-out games, got {len(bm.games)}\"\n"
    "    bm.solver.max_runtime_s_per_game = " + str(GAME_CLOCK_S) + ".0  # 6 x 1.5h fits the GPU cap; deviation noted in cell 0\n"
)


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 17, f"thui-v1-1 source expected 17 cells, found {len(cells)}"

    before = ["".join(c["source"]) for c in cells]

    cells[0]["source"] = CELL0_MD.splitlines(keepends=True)

    c8 = "".join(cells[8]["source"])
    assert CHAIN_ANCHOR in c8, "seed .replace() block not found in cell 8 -- source moved"
    assert c8.count(CHAIN_ANCHOR) == 1, "seed .replace() block appears more than once"
    assert "--enable-lora" not in c8, "cell 8 already carries enable-lora -- double build?"
    c8 = c8.replace(CHAIN_ANCHOR, CHAIN_ANCHOR + EVAL_REPLACES)
    teeth_anchor = '    print(f"taaf.kaggle: setup command: {command}", flush=True)'
    assert teeth_anchor in c8, "teeth anchor (setup-command print) not in cell 8"
    c8 = c8.replace(teeth_anchor, CELL8_TEETH + teeth_anchor)
    cells[8]["source"] = (CELL8_PREFIX + c8).splitlines(keepends=True)

    c14 = "".join(cells[14]["source"])
    assert c14.count(CELL14_ANCHOR) == 1, "offline bm.games assignment not found once in cell 14"
    assert "held-out filter" not in c14, "cell 14 already filtered -- double build?"
    cells[14]["source"] = c14.replace(CELL14_ANCHOR, CELL14_ANCHOR + CELL14_FILTER).splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert changed == [0, 8, 14], f"cells changed {changed}, expected [0, 8, 14]"

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads((REPO / "thuiv1" / "v1-1" / "kernel-metadata.json").read_text(encoding="utf-8"))
    meta["id"] = f"{OWNER}/{SLUG}"
    meta["title"] = SLUG
    meta["code_file"] = OUT_NB.name
    srcs = meta.get("dataset_sources") or []
    if ADAPTER_DATASET not in srcs:
        srcs.append(ADAPTER_DATASET)
    meta["dataset_sources"] = srcs
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}")
    print(f"dataset_sources: {srcs}")
    print("push AFTER the adapter dataset exists: "
          "python3 scripts/kaggle_push_kernel.py repos/arc-agi-3-agent/thui-lora/eval  (from arc-agi-pub)")


if __name__ == "__main__":
    main()
