#!/usr/bin/env python3
"""thui-gemma-v0 -- B64 serving+harness smoke: Gemma-4-31B-it as the duck agent.

Design: notes/B64-gemma-4-31b-duck-agent-design.md. The model-swap lane is the only lever that
ever gained in this campaign (B6: Qwen3.6 -> Qwen3.8 27B, 2.41 -> 4.55); the 2026-09-03 research
found no candidate with evidence, and one candidate with the right SHAPE: dense (B25's small-active
MoE kill does not apply), multimodal, 62.6 GB BF16 on Kaggle Models, run by Reki #2 and forge #3
of Milestone 1. Nobody has run it inside duck.

Two things must change, and both are measured blockers, not guesses:
  * the pinned wheelhouse (vLLM 0.19.0 + transformers 4.57.6) cannot load Gemma 4 (needs vLLM
    >= 0.19.1 and transformers >= 5.5, vllm-project/vllm#39216) -> wheelhouse swapped to
    ko0kip/vllm-0230-offline (vllm 0.23.0, transformers 5.12.1, torch 2.11.0; 192 files);
  * the vLLM flags are Qwen-specific (qwen3_coder tool parser, qwen3 reasoning parser,
    preserve_thinking) -> gemma4 / gemma4, and an explicit image limit because duck keeps prior
    turns' board images in history.

thui-v1-1 byte-for-byte except four cells: cell 0 markdown, cell 6 (inputs: wheelhouse dataset,
Kaggle MODEL mount mapped into TAAF_KAGGLE_INPUT_PATHS), cell 8 (setup-command rewrites: model,
wheelhouse, installer, parsers, fp8 weights), cell 14 smoke filter (tr87 / sk48 / sc25, 900 s/game).
`--full` drops the cell-14 filter; `--suffix=-r2` names a second run.

    python3 build_notebook.py [--full] [--suffix=-r2] [--owner=yocybercode] [--base=v3|v1]   # owner must match the pushing token (G4); base defaults to the B48 build
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
# Base chassis: "v3" = thui-v3-0 (the B48 build: thui-v1-1 + LOCAL_ANALYZER_YIELD_SECONDS 180, the build that
# drew the standing best 2.03 and has a 4-run public baseline pool 4.01 / 4.52 / 5.17 / 3.85); "v1" = thui-v1-1.
BASE = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--base=")), "v3")
SRC_NB = {"v3": REPO / "thuiv3" / "taaf-thui-v3-0.ipynb", "v1": REPO / "thuiv1" / "v1-1" / "taaf-thui-v1-1.ipynb"}[BASE]
META_SRC = {"v3": REPO / "thuiv3" / "kernel-metadata.json", "v1": REPO / "thuiv1" / "v1-1" / "kernel-metadata.json"}[BASE]
OWNER = "sahasawatt"

SMOKE_GAMES = ("tr87", "sk48", "sc25")
GAME_CLOCK_S = 900

MODEL_SOURCE = "google/gemma-4/transformers/gemma-4-31b-it/1"
MODEL_MOUNT = "/kaggle/input/models/google/gemma-4/transformers/gemma-4-31b-it/1"
MODEL_REF = "google/gemma-4-31b-it"          # owner/slug the bundle's resolver is given
SERVED_NAME = "google/gemma-4-31b-it"
WHEELS_SOURCE = "ko0kip/vllm-0230-offline"
WHEELS_SUBDIR = "vllm_0230_offline/wheels"
IMAGE_LIMIT = 32                             # duck keeps up to 30 assistant turns of history, each user turn carries a board image

CELL0_MD_SMOKE = """# thui-gemma-v0 — B64 smoke: Gemma-4-31B-it as the duck agent (serving + 3 games)

**Infrastructure smoke, not a scoring run.** `thui-v3-0` (the B48 build: thui-v1-1 + yield 180, the standing-best chassis) byte-for-byte except cells 6, 8 and 14.
The base model becomes `google/gemma-4-31b-it` (Kaggle Models, 62.6 GB BF16, served with online FP8
weights) on the `ko0kip/vllm-0230-offline` wheelhouse (vLLM 0.23.0 / transformers 5.12.1), with the
`gemma4` tool-call and reasoning parsers and an explicit 32-image prompt limit. Harness, prompts,
seed, temperature, clock: inherited unchanged. Cell 14 filters to tr87 / sk48 / sc25 at 900 s each.
Numbers are meaningless and must never be quoted. Design: `notes/B64-gemma-4-31b-duck-agent-design.md`.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. Wheelhouse credit:
ko0kip. This is a Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

CELL0_MD_FULL = """# thui-gemma-v1 — B64: Gemma-4-31B-it as the duck agent, full 25 games

`thui-v3-0` (the B48 build: thui-v1-1 + yield 180, the standing-best chassis) byte-for-byte except cells 6 and 8: base model `google/gemma-4-31b-it` (online FP8
weights) on the `ko0kip/vllm-0230-offline` wheelhouse (vLLM 0.23.0), `gemma4` parsers, 32-image
prompt limit. Harness, prompts, seed, temperature, clock and games inherited unchanged. Oracle:
paired **levels** vs the B48 build's public pool (`thui-v3-0` ×2, `thui-v3-1`, `thui-v3-2`: 4.01 / 4.52 / 5.17 / 3.85), ≥ 2 runs per arm.
Design + record: `notes/B64-gemma-4-31b-duck-agent-design.md`.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. Wheelhouse credit:
ko0kip. This is a Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

# ---- cell 6: inputs -------------------------------------------------------------------------
CELL6_OLD_SOURCES = 'DATASET_SOURCES = ["jakobbrggen/taaf-kaggle-source-anim-20260807-anim", "driessmit1/arc3-vllm-h100-wheelhouse-v3", "jakobbrggen/qwen3-8-27b-fp8-hf-snapshot"]'
CELL6_NEW_SOURCES = 'DATASET_SOURCES = ["jakobbrggen/taaf-kaggle-source-anim-20260807-anim", "' + WHEELS_SOURCE + '"]'
CELL6_ANCHOR = "# Published to setup commands and the solver via the environment:\n"
CELL6_MODEL_MAP = (
    "# thui-gemma-v0 (B64): the base model is a Kaggle MODEL, not a dataset -- the bundle's resolver only\n"
    "# probes dataset mounts, so hand it the model mount through the same input-path map.\n"
    "_GEMMA_MOUNT = Path(" + repr(MODEL_MOUNT) + ")\n"
    "assert _GEMMA_MOUNT.exists(), f\"thui-gemma-v0: model mount missing: {_GEMMA_MOUNT} (attach " + MODEL_SOURCE + ")\"\n"
    "assert (_GEMMA_MOUNT / 'config.json').exists(), 'thui-gemma-v0: model mount has no config.json'\n"
    "kaggle_input_paths[" + repr(MODEL_REF) + "] = str(_GEMMA_MOUNT)\n"
    "print(f\"thui-gemma-v0: model mount = {_GEMMA_MOUNT}\", flush=True)\n\n"
)

# ---- cell 8: setup-command rewrites, applied AFTER thui-v1-1's own chain -----------------------
CELL8_ANCHOR = '    assert "vrfai-qwen3-6-27b-fp8-hf-snapshot" not in command, "duckv10: model slug rewrite missed"\n'
CELL8_REWRITES = [
    # (old, new) -- each must occur exactly once in the setup command at run time (asserted in-kernel)
    ("MODEL_OWNER = 'jakobbrggen'", "MODEL_OWNER = 'google'"),
    ("MODEL_SLUG = 'qwen3-8-27b-fp8-hf-snapshot'", "MODEL_SLUG = 'gemma-4-31b-it'"),
    ("SERVED_MODEL_NAME = 'vrfai/Qwen3.8-27B-FP8'", "SERVED_MODEL_NAME = " + repr(SERVED_NAME)),
    ("WHEELHOUSE_OWNER = 'driessmit1'", "WHEELHOUSE_OWNER = 'ko0kip'"),
    ("WHEELHOUSE_SLUG = 'arc3-vllm-h100-wheelhouse-v3'", "WHEELHOUSE_SLUG = 'vllm-0230-offline'"),
    ("STAMP_TEXT = 'vllm==0.19.0 torch==2.10.0 flashinfer==0.6.6\\n'", "STAMP_TEXT = 'vllm==0.23.0 torch==2.11.0 transformers==5.12.1\\n'"),
    # installer: the ko0kip set has no requirements.lock; install by name from its wheels dir
    ("    requirements = WHEELHOUSE / 'requirements.lock'\n    if not requirements.exists():\n        raise FileNotFoundError(f'Missing wheelhouse lock file: {requirements}')\n",
     "    requirements = None  # thui-gemma-v0: ko0kip wheels carry no lock file\n"),
    ("        '--find-links',\n        str(WHEELHOUSE),\n        '--requirement',\n        str(requirements),\n",
     "        '--find-links',\n        str(WHEELHOUSE / " + repr(WHEELS_SUBDIR.split('/')[0]) + " / 'wheels'),\n        'vllm==0.23.0',\n        'transformers==5.12.1',\n"),
    # vLLM flags: Qwen parsers -> gemma4; preserve_thinking -> image limit + fp8 weights
    ("        '--tool-call-parser',\n        'qwen3_coder',\n", "        '--tool-call-parser',\n        'gemma4',\n"),
    ("        '--reasoning-parser',\n        'qwen3',\n", "        '--reasoning-parser',\n        'gemma4',\n"),
    ("        '--default-chat-template-kwargs',\n        '{\"preserve_thinking\": true}',\n",
     "        '--limit-mm-per-prompt',\n        '{\"image\": " + str(IMAGE_LIMIT) + "}',\n        '--quantization',\n        'fp8',\n"),
]


def _cell8_block() -> str:
    lines = ["    # thui-gemma-v0 (B64): model + wheelhouse + parser rewrites, each asserted to hit exactly once.\n",
             "    _GEMMA_REWRITES = " + json.dumps(CELL8_REWRITES) + "\n",
             "    for _old, _new in _GEMMA_REWRITES:\n",
             "        assert command.count(_old) == 1, f\"thui-gemma-v0 TEETH FAIL: anchor not found once: {_old[:60]!r}\"\n",
             "        command = command.replace(_old, _new)\n",
             "    assert 'qwen3_coder' not in command and \"'qwen3'\" not in command, 'thui-gemma-v0: a Qwen parser survived'\n",
             "    assert 'requirements.lock' not in command, 'thui-gemma-v0: lock-file path survived'\n",
             "    print('thui-gemma-v0: model=google/gemma-4-31b-it wheels=ko0kip/vllm-0230-offline parsers=gemma4 fp8 weights image-limit=" + str(IMAGE_LIMIT) + "', flush=True)\n"]
    return "".join(lines)


CELL14_ANCHOR = "    bm.games = _offline_games(competition_env_files)\n"
CELL14_FILTER = (
    "    # thui-gemma-v0 smoke: three games, at the REAL seam.\n"
    "    _SMOKE = " + repr(SMOKE_GAMES) + "\n"
    "    _n0 = len(bm.games)\n"
    "    bm.games = [g for g in bm.games if any(g.env_name.startswith(h) for h in _SMOKE)]\n"
    "    print(f\"thui-gemma-v0: smoke filter {_n0} -> {len(bm.games)} games\", flush=True)\n"
    "    assert len(bm.games) == " + str(len(SMOKE_GAMES)) + ", f\"thui-gemma-v0: expected " + str(len(SMOKE_GAMES)) + " games, got {len(bm.games)}\"\n"
    "    bm.solver.max_runtime_s_per_game = " + str(GAME_CLOCK_S) + ".0\n"
)


def main(full: bool = False, slug_suffix: str = "", owner: str = OWNER) -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 17, f"{SRC_NB.name}: expected 17 cells, found {len(cells)}"
    if BASE == "v3":  # teeth: the base must carry the yield-180 injection AND its own assert, or it is not the B48 build
        _c8 = "".join(cells[8]["source"])
        assert _c8.count("'LOCAL_ANALYZER_YIELD_SECONDS': '180'") == 2, "base v3: yield-180 injection/assert not found twice in cell 8"
    print(f"base = {BASE} ({SRC_NB.relative_to(REPO)})", flush=True)
    before = ["".join(c["source"]) for c in cells]
    slug = ("thui-gemma-v1" if full else "thui-gemma-v0") + slug_suffix
    out_nb = HERE / f"taaf-{slug}.ipynb"

    cells[0]["source"] = (CELL0_MD_FULL if full else CELL0_MD_SMOKE).splitlines(keepends=True)

    c6 = "".join(cells[6]["source"])
    assert c6.count(CELL6_OLD_SOURCES) == 1, "cell 6 DATASET_SOURCES line not found once"
    assert c6.count(CELL6_ANCHOR) == 1, "cell 6 publish anchor not found once"
    c6 = c6.replace(CELL6_OLD_SOURCES, CELL6_NEW_SOURCES).replace(CELL6_ANCHOR, CELL6_MODEL_MAP + CELL6_ANCHOR)
    cells[6]["source"] = c6.splitlines(keepends=True)

    c8 = "".join(cells[8]["source"])
    assert "thui-gemma" not in c8, "cell 8 already carries the swap -- double build?"
    assert c8.count(CELL8_ANCHOR) == 1, "cell 8 anchor (slug-rewrite assert) not found once"
    cells[8]["source"] = c8.replace(CELL8_ANCHOR, _cell8_block() + CELL8_ANCHOR).splitlines(keepends=True)

    if not full:
        c14 = "".join(cells[14]["source"])
        assert c14.count(CELL14_ANCHOR) == 1, "offline bm.games assignment not found once in cell 14"
        cells[14]["source"] = c14.replace(CELL14_ANCHOR, CELL14_ANCHOR + CELL14_FILTER).splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    expected = [0, 6, 8] if full else [0, 6, 8, 14]
    assert changed == expected, f"cells changed {changed}, expected {expected}"
    for i in expected[1:]:
        ast.parse("".join(cells[i]["source"]), filename=f"cell{i}")

    # teeth against the REAL setup command: every rewrite anchor must be present exactly once there
    # after thui-v1-1's own chain has run (simulate that chain here, byte for byte).
    command = json.loads((REPO / "duck" / "bundle" / "setup_commands.json").read_text(encoding="utf-8"))[0]
    command = (command
               .replace("MODEL_OWNER = 'driessmit1'", "MODEL_OWNER = 'jakobbrggen'")
               .replace("MODEL_SLUG = 'vrfai-qwen3-6-27b-fp8-hf-snapshot'", "MODEL_SLUG = 'qwen3-8-27b-fp8-hf-snapshot'")
               .replace("SERVED_MODEL_NAME = 'vrfai/Qwen3.6-27B-FP8'", "SERVED_MODEL_NAME = 'vrfai/Qwen3.8-27B-FP8'"))
    for old, new in CELL8_REWRITES:
        assert command.count(old) == 1, f"setup-command anchor not found once in the vendored bundle: {old[:60]!r}"
        command = command.replace(old, new)
    assert "requirements.lock" not in command and "qwen3_coder" not in command
    body = command.split("<<'PYSETUP'\n", 1)[1].rsplit("\nPYSETUP", 1)[0]
    ast.parse(body, filename="rewritten-setup-command")

    out_nb.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(META_SRC.read_text(encoding="utf-8"))
    meta["id"] = f"{owner}/{slug}"; meta["title"] = slug; meta["code_file"] = out_nb.name
    meta["dataset_sources"] = ["jakobbrggen/taaf-kaggle-source-anim-20260807-anim", WHEELS_SOURCE]
    meta["model_sources"] = [MODEL_SOURCE]
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"built {out_nb.name}: cells changed {changed}, id {meta['id']}")
    print(f"dataset_sources: {meta['dataset_sources']}  model_sources: {meta['model_sources']}")


if __name__ == "__main__":
    _suf = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--suffix=")), "")
    _own = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), OWNER)
    main(full="--full" in sys.argv, slug_suffix=_suf, owner=_own)
