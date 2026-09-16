"""B78: existing serving switch MTP 3 -> 0; smoke precedes full.

python3 thui-fast/build_mtp_off.py --smoke --out /tmp/b78-smoke
python3 thui-fast/build_mtp_off.py --out /tmp/b78-full
"""
import argparse
import ast
import hashlib
import json
import tempfile
from pathlib import Path
import build_notebook as base

HERE = Path(__file__).resolve().parent
SETUP_SHA = "037c041c9bd9dcffa9084b32f47af9cf1bf35849d5eaf2e1a3422daac098b2e2"

VERIFY = r'''# B78: check the launched server, not only the requested environment.
def verify_mtp_off(provenance):
    tuning = provenance["vllm_tuning"]
    argv = provenance["server_identity"]["argv"]
    assert tuning["mtp_speculative_tokens"] == 0, "B78: MTP still enabled"
    assert "--speculative-config" not in argv, "B78: speculative argv survived"
    assert argv[argv.index("--quantization") + 1] == "modelopt_fp4"
    assert tuning["max_num_seqs"] == 8
    assert tuning["kv_cache_memory_bytes"] == 5368709120
    assert tuning["enable_chunked_prefill"] is True
    assert tuning["enable_prefix_caching"] is False
    assert provenance["model_hf_repo"] == "RadixArk/Qwen3.8-Flash-Next-NVFP4"
    assert provenance["model_hf_revision"] == "7b719225242aacd3dbd3f9407468c2ee9a9d2594"
    return argv

_provenance = json.loads((WORKING_DIR / "vllm-setup-provenance.json").read_text())
verify_mtp_off(_provenance)
for _fault in ("tuning", "argv"):
    _bad = json.loads(json.dumps(_provenance))
    if _fault == "tuning":
        _bad["vllm_tuning"]["mtp_speculative_tokens"] = 3
    else:
        _bad["server_identity"]["argv"] += ["--speculative-config", "{}"]
    try:
        verify_mtp_off(_bad)
    except AssertionError:
        pass
    else:
        raise AssertionError("B78 teeth failed to reject " + _fault)
print("B78_TEETH 2/2 faulty serving records rejected", flush=True)
print("B78_MTP_OFF_VERIFIED " + json.dumps(_provenance["vllm_tuning"], sort_keys=True), flush=True)
'''


def build(out, smoke=False):
    # Reuse the existing builder and its identity/attribution checks without changing its files.
    with tempfile.TemporaryDirectory() as tmp:
        base.HERE = Path(tmp)
        base.OUT_NB = base.HERE / "taaf-thui-fast-v0.ipynb"
        base.OWNER = "yocybercode"
        base.main()
        nb = json.loads(base.OUT_NB.read_text())
        meta = json.loads((base.HERE / "kernel-metadata.json").read_text())
    before = ["".join(c["source"]) for c in nb["cells"]]
    after = before.copy()
    slug = "thui-fast-b78-mtp0-" + ("smoke" if smoke else "full25-r1")
    after[0] = (f"# {slug} (Thuitanium / Knowless Crew)\n\n"
                "B78: MTP speculative decoding 3 → 0, using the existing serving switch. "
                "Same Flash-Next NVFP4 weights, scheduler and solver. "
                + ("Smoke: first three benchmark entries, 180 seconds per game. " if smoke else
                   "Full: 25 games, unchanged 7,920 seconds per game. ")
                + "Public results are measurements, not a claim about hidden performance.\n\n"
                + "## Inherited provenance\n\n" + before[0])
    assert before[3].count('"TAAF_VLLM_MTP_TOKENS": "3"') == 1
    after[3] = before[3].replace('"TAAF_VLLM_MTP_TOKENS": "3"', '"TAAF_VLLM_MTP_TOKENS": "0"').replace(
        "kv5-bf16-mtp3-c8-cg32", "kv5-bf16-mtp0-c8-cg32")
    # Same startup mode as upstream's default; its full diagnostic mode requires positive MTP.
    after[3] += '\nos.environ["TAAF_KAGGLE_FAST_START"] = "1"\n'
    old = '"/kaggle/input/competitions/arc-prize-2026-arc-agi-3/arc_agi_3_wheels"'
    assert before[5].count(old) == 1
    after[5] = ("# Resolve both supported competition mount layouts.\n"
                "_wheels = next((p for p in (\n"
                "    Path('/kaggle/input/competitions/arc-prize-2026-arc-agi-3/arc_agi_3_wheels'),\n"
                "    Path('/kaggle/input/arc-prize-2026-arc-agi-3/arc_agi_3_wheels'),\n"
                ") if p.is_dir()), None)\n"
                "assert _wheels is not None, 'Competition wheelhouse missing'\n"
                + before[5].replace(old, 'str(_wheels)'))
    after[9] = ("import hashlib\n"
                f"assert hashlib.sha256((BUNDLE_DIR / 'serving_setup.py').read_bytes()).hexdigest() == {SETUP_SHA!r}, 'B78: serving source drift'\n"
                + before[9] + "\n" + VERIFY)
    env_path = 'Path("/kaggle/input/competitions/arc-prize-2026-arc-agi-3/arc_agi_3_wheels")'
    assert before[15].count(env_path) == 1
    after[15] = before[15].replace(env_path, "_wheels")
    if smoke:
        anchor = "bm.n_passes = 1"
        assert after[15].count(anchor) == 1
        after[15] = after[15].replace(anchor,
            "PUBLIC_GAME_IDS = PUBLIC_GAME_IDS[:3]\n"
            "bm.games = bm.games[:3]\n"
            "assert len(bm.games) == 3\n"
            "print('B78_SMOKE_SELECTION games=3', flush=True)\n" + anchor)
        after[15] = after[15].replace("len(public_runs) != 25", "len(public_runs) != 3").replace(
            "PUBLIC25_AUDIT runs=25", "B78_SMOKE_AUDIT runs=3")
        after[13] = ("assert not TRUE_SUBMISSION, 'B78 smoke cannot be submitted'\n"
                     + before[13].replace("7920.0", "180.0"))
    expected = [0, 3, 5, 9, 13, 15] if smoke else [0, 3, 5, 9, 15]
    assert [i for i,(a,b) in enumerate(zip(before,after)) if a != b] == expected
    for i, cell in enumerate(nb["cells"]):
        cell["source"] = after[i].splitlines(keepends=True)
        if cell["cell_type"] == "code":
            ast.parse(after[i], filename=f"cell{i}")
    assert after[13] == before[13] or smoke
    assert '"TAAF_VLLM_MTP_TOKENS": "3"' not in after[3]
    out.mkdir(parents=True, exist_ok=True)
    meta.update(id=f"yocybercode/{slug}", title=slug, code_file=f"{slug}.ipynb")
    (out / meta["code_file"]).write_text(json.dumps(nb, ensure_ascii=False, indent=1))
    (out / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"B78 built {meta['id']}; changed cells {expected}; smoke={smoke}")
    return nb


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    build(args.out, args.smoke)
