"""Runnable offline check against the exact downloaded serving source (no GPU).
python3 thui-fast/test_mtp_off.py /path/to/serving_setup.py
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
from unittest.mock import patch
from build_mtp_off import build, SETUP_SHA, VERIFY

source = Path(sys.argv[1])
assert hashlib.sha256(source.read_bytes()).hexdigest() == SETUP_SHA
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    with patch.dict(os.environ, {"TAAF_KAGGLE_BUNDLE_DIR": temp,
                                "TAAF_KAGGLE_WORKING_DIR": temp,
                                "TAAF_KAGGLE_SETUP_ENV": str(root / "env.json")}, clear=True):
        serving = runpy.run_path(str(source))
        full = build(root / "full")
        smoke = build(root / "smoke", True)
        cell = ast.parse("".join(full["cells"][3]["source"]))
        profile = next(ast.literal_eval(n.value) for n in cell.body
                       if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and
                       t.id == "PUBLIC25_VLLM_PROFILE_ENV" for t in n.targets))
        os.environ.update(profile)
        off = serving["resolve_vllm_tuning"]()
        off_argv = serving["server_command"](root, tuning=off)
        assert "--speculative-config" not in off_argv
        os.environ["TAAF_VLLM_MTP_TOKENS"] = "3"
        on = serving["resolve_vllm_tuning"]()
        on_argv = serving["server_command"](root, tuning=on)
        ix = on_argv.index("--speculative-config")
        assert json.loads(on_argv[ix + 1])["num_speculative_tokens"] == 3
        assert on_argv[:ix] + on_argv[ix+2:] == off_argv
        assert {k for k in off if off[k] != on[k]} == {"mtp_speculative_tokens"}
        provenance = {"vllm_tuning": off, "server_identity": {"argv": off_argv},
                      "model_hf_repo": serving["MODEL_HF_REPO"],
                      "model_hf_revision": serving["MODEL_HF_REVISION"]}
        (root / "vllm-setup-provenance.json").write_text(json.dumps(provenance))
        exec(VERIFY, {"WORKING_DIR": root, "json": json})
        for mutation in ("tuning", "argv"):
            bad = json.loads(json.dumps(provenance))
            if mutation == "tuning": bad["vllm_tuning"]["mtp_speculative_tokens"] = 3
            else: bad["server_identity"]["argv"] = on_argv
            (root / "vllm-setup-provenance.json").write_text(json.dumps(bad))
            try: exec(VERIFY, {"WORKING_DIR": root, "json": json})
            except AssertionError: pass
            else: raise AssertionError("in-kernel gate accepted mutation " + mutation)
        assert "bm.games = bm.games[:3]" in "".join(smoke["cells"][15]["source"])
        assert "7920.0" in "".join(full["cells"][13]["source"])
print("PASS: actual serving 0/3 control; argv differs only by speculative config; both in-kernel mutations RED; smoke/full compile")
