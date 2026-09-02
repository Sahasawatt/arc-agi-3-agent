#!/usr/bin/env python3
"""thui-lora-v0 -- the FP8+LoRA smoke, built on thui-v1-1 byte-for-byte.

THE ONE RISK THIS BUILD EXISTS TO RETIRE. The LoRA arm's production chain is: adapter
trained elsewhere -> served by vLLM beside the FP8 base (`--enable-lora`). Nothing in this
campaign has ever run vLLM 0.19 + Qwen3.8-27B-FP8 + a LoRA adapter together, and FP8-base +
LoRA is a pairing that has genuinely broken in some vLLM versions. Everything else about
LoRA (data, training, eval) can be built offline; this pairing can only be proven on the
kernel GPU. So v0 proves it for the cost of a short run and nothing else:

  P1  the vLLM server comes up with `--enable-lora --lora-modules smoke=<dir>` and
      /v1/models lists BOTH the base model and `smoke`.
  P2  a chat completion addressed to model `smoke` answers 200 with content -- the adapter
      path actually serves, not merely registers.
  P3  the agent plays 3 games briefly (capped clock) through the same server -- the
      harness's own request path is undisturbed with the adapter mounted.

WHY THE ADAPTER IS A DUMMY AND WHY THAT IS ENOUGH. The smoke adapter is generated
in-kernel from the model's own config.json: rank-8 A initialised small-random, **B all
zeros**, q_proj/v_proj only. B=0 makes the adapter the mathematical identity, so P2/P3
cannot fail for behaviour reasons -- any failure is the serving chain itself, which is the
only thing under test. No peft is needed to WRITE an adapter (it is a config.json + one
safetensors file); peft enters later, at training time (v1).

WHERE THE INJECTION LANDS, learned by this file's own first failure: the vLLM serve
invocation lives inside the `command` STRING that cell 8 loads from the source dataset's
setup_commands.json at runtime -- it is not in the cell source. So the flag injection is
one more anchored `.replace()` chained where the seed pin already chains, and the teeth
assert on `command` AFTER the replaces ran, exactly as thui-v1-1's own teeth do.

WHAT THIS BUILD DOES NOT DO. It scores nothing (3 games, capped clock -- the summary is
meaningless and must not enter any ledger), trains nothing real, and it does not touch the
sampler: the seed/temperature teeth from thui-v1-1 are inherited unchanged.

Naming: family `thui-lora` (owner's call, 2026-09-01) -- a new lever family, deliberately
outside the thuivN numbering so it cannot collide with thuiv2's retrieval arm.

    python3 build_notebook.py            # writes taaf-thui-lora-v0.ipynb + kernel-metadata.json
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SRC_NB = REPO / "thuiv1" / "v1-1" / "taaf-thui-v1-1.ipynb"
OUT_NB = HERE / "taaf-thui-lora-v0.ipynb"
OWNER = "sahasawatt"          # pushed from the Windows box; the token decides anyway (G4)
SLUG = "thui-lora-v0"

SMOKE_GAMES = 3
GAME_CLOCK_S = 900            # 3 games x 15 min ceiling ~= 45 min worst case, vs 7920 real

CELL0_MD = """# thui-lora-v0 — FP8 + LoRA serving smoke (scores nothing)

**This kernel is an infrastructure test, not a scoring run.** It is `thui-v1-1` byte-for-byte
except three cells, and it exists to retire one risk: that vLLM 0.19 cannot serve a LoRA
adapter beside the Qwen3.8-27B **FP8** base. It plays 3 games on a capped clock only to prove
the harness's request path still works with the adapter mounted — the resulting numbers are
meaningless and must never be quoted.

The adapter is a rank-8 dummy with B=0 (mathematical identity), generated in-kernel from the
model's own config.json. See `thui-lora/build_notebook.py` in the agent repo for the full
rationale and the teeth.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

# Prepended to cell 8: write the dummy adapter BEFORE the setup command starts the server.
# Runs in the notebook env (Kaggle base image ships torch + safetensors; the wheelhouse env
# belongs to the server subprocess and is not needed to write a safetensors file).
CELL8_PREFIX = '''# --- thui-lora-v0: dummy adapter, written before the server starts ---------------
# B=0 => identity. Any P2/P3 failure is therefore the serving chain, never behaviour.
import glob as _glob, json as _json, os as _os
import torch as _torch
from safetensors.torch import save_file as _save_file

_snap = None
for _pat in ("/kaggle/input/datasets/*/qwen3-8-27b-fp8-hf-snapshot",
             "/kaggle/input/qwen3-8-27b-fp8-hf-snapshot"):
    _hits = _glob.glob(_pat)
    if _hits:
        _snap = _hits[0]
        break
assert _snap, "thui-lora-v0: model snapshot not mounted under either input layout"
# Qwen3.8-27B is a VL model with a HYBRID text stack: config nests under text_config, and
# only 16 of 64 layers are full_attention (the rest are linear_attention with different
# module names entirely). Target ONLY the full-attention layers' q/v projections -- an
# adapter naming a module the model does not have is exactly the crash this smoke hunts,
# but it must be vLLM's crash on a REAL mismatch, not ours on a fictional layer list.
_cfg = _json.load(open(_os.path.join(_snap, "config.json")))
_t = _cfg.get("text_config") or _cfg
_hidden = int(_t["hidden_size"])
_heads = int(_t["num_attention_heads"])
_kv_heads = int(_t.get("num_key_value_heads", _heads))
_head_dim = int(_t.get("head_dim") or _hidden // _heads)
_lt = _t.get("layer_types") or ["full_attention"] * int(_t["num_hidden_layers"])
_full = [_i for _i, _x in enumerate(_lt) if "full" in _x]
assert _full, "thui-lora-v0: no full-attention layers found in layer_types"
_R = 8
_ad = "/kaggle/working/smoke-adapter"
_os.makedirs(_ad, exist_ok=True)
_json.dump({
    "peft_type": "LORA", "r": _R, "lora_alpha": 16, "lora_dropout": 0.0,
    "target_modules": ["q_proj", "v_proj"], "bias": "none", "task_type": "CAUSAL_LM",
    "layers_to_transform": _full,
    "base_model_name_or_path": _snap,
}, open(_os.path.join(_ad, "adapter_config.json"), "w"))
_w = {}
for _i in _full:
    _p = f"base_model.model.model.layers.{_i}.self_attn"
    _w[f"{_p}.q_proj.lora_A.weight"] = (_torch.randn(_R, _hidden) * 0.01).to(_torch.bfloat16)
    _w[f"{_p}.q_proj.lora_B.weight"] = _torch.zeros(_heads * _head_dim, _R, dtype=_torch.bfloat16)
    _w[f"{_p}.v_proj.lora_A.weight"] = (_torch.randn(_R, _hidden) * 0.01).to(_torch.bfloat16)
    _w[f"{_p}.v_proj.lora_B.weight"] = _torch.zeros(_kv_heads * _head_dim, _R, dtype=_torch.bfloat16)
_save_file(_w, _os.path.join(_ad, "adapter_model.safetensors"))
print(f"thui-lora-v0: dummy adapter written ({len(_full)} full-attn layers of {len(_lt)}, "
      f"r={_R}, B=0) -> {_ad}", flush=True)
# ----------------------------------------------------------------------------------

'''

# The seed pin's .replace() block, verbatim from thui-v1-1's cell 8. The LoRA replace
# chains immediately after it. Escapes matter: in the CELL SOURCE this appears with a
# literal backslash-n inside the replacement string.
CHAIN_ANCHOR = (
    "        .replace(\n"
    "            \"    'LOCAL_ANALYZER_TEMPERATURE':\",\n"
    "            \"    'LOCAL_ANALYZER_SEED': '20260825',\\n    'LOCAL_ANALYZER_TEMPERATURE':\",\n"
    "        )\n"
)
LORA_REPLACE = (
    "        .replace(\n"
    "            \"        '--max-model-len',\",\n"
    "            \"        '--enable-lora',\\n\"\n"
    "            \"        '--lora-modules',\\n\"\n"
    "            \"        'smoke=/kaggle/working/smoke-adapter',\\n\"\n"
    "            \"        '--max-model-len',\",\n"
    "        )\n"
)

CELL8_TEETH = (
    "    # thui-lora-v0 TEETH on the RESOLVED command: a moved anchor must fail loud, not no-op.\n"
    "    assert command.count(\"--enable-lora\") == 1, \"thui-lora-v0 TEETH FAIL: enable-lora != 1\"\n"
    "    assert \"smoke=/kaggle/working/smoke-adapter\" in command, \"thui-lora-v0 TEETH FAIL: lora-modules path missing\"\n"
    "    print(\"thui-lora-v0: LoRA flags injected, sampler inherited from thui-v1-1\", flush=True)\n"
)

CELL12_SUFFIX = '''

# === thui-lora-v0 smoke: P1/P2 asserts + 3-game capped run =========================
import json as _j
import urllib.request as _u

_base = "http://127.0.0.1:1234/v1"
_models = _j.load(_u.urlopen(_base + "/models", timeout=30))
_ids = [m.get("id") for m in _models.get("data", [])]
print("thui-lora-v0 P1: served models =", _ids, flush=True)
assert "smoke" in _ids, "thui-lora-v0 P1 FAIL: LoRA module not listed by /v1/models"

_req = _u.Request(
    _base + "/chat/completions",
    data=_j.dumps({"model": "smoke", "max_tokens": 32,
                    "messages": [{"role": "user", "content": "Reply with the word ready."}]}).encode(),
    headers={"Content-Type": "application/json"})
_resp = _j.load(_u.urlopen(_req, timeout=120))
_choice = (_resp.get("choices") or [{}])[0].get("message", {})
_txt = _choice.get("content") or _choice.get("reasoning_content") or ""
print("thui-lora-v0 P2: adapter completion ->", repr(_txt[:80]), flush=True)
assert _txt.strip(), "thui-lora-v0 P2 FAIL: adapter-addressed completion came back empty"

bm.games = bm.games[:@GAMES@]
bm.solver.max_runtime_s_per_game = @CLOCK@.0
print(f"thui-lora-v0 P3: {len(bm.games)} games at @CLOCK@s/game -- numbers are smoke, not score",
      flush=True)
# ==================================================================================
'''.replace("@GAMES@", str(SMOKE_GAMES)).replace("@CLOCK@", str(GAME_CLOCK_S))


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 17, f"thui-v1-1 source expected 17 cells, found {len(cells)}"

    before = ["".join(c["source"]) for c in cells]

    # cell 0: replace the markdown wholesale
    cells[0]["source"] = CELL0_MD.splitlines(keepends=True)

    # cell 8: prepend adapter generation, chain the serve-flag replace, append teeth
    c8 = "".join(cells[8]["source"])
    assert CHAIN_ANCHOR in c8, "seed .replace() block not found in cell 8 -- source moved"
    assert c8.count(CHAIN_ANCHOR) == 1, "seed .replace() block appears more than once"
    assert "--enable-lora" not in c8, "cell 8 already carries enable-lora -- double build?"
    c8 = c8.replace(CHAIN_ANCHOR, CHAIN_ANCHOR + LORA_REPLACE)
    teeth_anchor = '    print(f"taaf.kaggle: setup command: {command}", flush=True)'
    assert teeth_anchor in c8, "teeth anchor (setup-command print) not in cell 8"
    c8 = c8.replace(teeth_anchor, CELL8_TEETH + teeth_anchor)
    cells[8]["source"] = (CELL8_PREFIX + c8).splitlines(keepends=True)

    # cell 12: append the smoke block after the inherited probe
    c12 = "".join(cells[12]["source"])
    assert "bm.games" not in c12, "cell 12 already slices bm.games -- double build?"
    cells[12]["source"] = (c12 + CELL12_SUFFIX).splitlines(keepends=True)

    # teeth on the build itself: exactly cells 0, 8, 12 changed
    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert changed == [0, 8, 12], f"cells changed {changed}, expected [0, 8, 12]"

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads((REPO / "thuiv1" / "v1-1" / "kernel-metadata.json").read_text(encoding="utf-8"))
    meta["id"] = f"{OWNER}/{SLUG}"
    meta["title"] = SLUG
    meta["code_file"] = OUT_NB.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}")
    print("push with: python3 scripts/kaggle_push_kernel.py repos/arc-agi-3-agent/thui-lora  (from arc-agi-pub)")


if __name__ == "__main__":
    main()
