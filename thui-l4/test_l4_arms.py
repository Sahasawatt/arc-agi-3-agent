"""Local teeth for the L4 bench, run BEFORE any GPU (0 GPU, no server).

Two seams, and both fail silently on the kernel if they are wrong:

  1. Does the arm's env delta actually reach the vLLM command line? An env key that `serving_setup.py` ignores
     produces a run that looks perfect and measures the SHIPPED profile three times. Asserted by building the
     real command with the real parser, one arm at a time, and diffing the argv.
  2. Does the bench cell's own `_spec` regex read a Prometheus body? Exercised against a synthetic /metrics
     body -- and the CONTROL for that is a body with the counters ABSENT, which must be reported as
     "names unknown", never as zero drafts.

  python thui-l4/test_l4_arms.py [path/to/serving_setup.py]
"""
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
SETUP = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    HERE.parent.parent / "ds-full" / "keith" / "serving_setup.py")
NB = HERE / "taaf-thui-l4-a.ipynb"
fails = []

PROFILE = {
    "TAAF_VLLM_ENABLE_PREFIX_CACHING": "0", "TAAF_VLLM_KV_CACHE_DTYPE": "auto",
    "TAAF_VLLM_KV_CACHE_MEMORY_BYTES": "5368709120", "TAAF_VLLM_MAX_CUDAGRAPH_CAPTURE_SIZE": "32",
    "TAAF_VLLM_MAX_NUM_BATCHED_TOKENS": "8192", "TAAF_VLLM_MAX_NUM_SEQS": "8",
    "TAAF_VLLM_MTP_TOKENS": "3", "TAAF_VLLM_OMP_THREADS": "1",
}
ARMS = {"a": {}, "b": {"TAAF_VLLM_MTP_INDEX_SHARE_FOR_ITERATION": "1"}, "d": {"TAAF_VLLM_MTP_TOKENS": "0"},
        "s16": {"TAAF_VLLM_MAX_NUM_SEQS": "16"}, "s28": {"TAAF_VLLM_MAX_NUM_SEQS": "28"},
        "k10s16": {"TAAF_VLLM_KV_CACHE_MEMORY_BYTES": str(10 * 1024 ** 3), "TAAF_VLLM_MAX_NUM_SEQS": "16"},
        "k7s16": {"TAAF_VLLM_KV_CACHE_MEMORY_BYTES": str(7 * 1024 ** 3), "TAAF_VLLM_MAX_NUM_SEQS": "16"},
        "mtp0k7s16": {"TAAF_VLLM_MTP_TOKENS": "0", "TAAF_VLLM_KV_CACHE_MEMORY_BYTES": str(7 * 1024 ** 3),
                      "TAAF_VLLM_MAX_NUM_SEQS": "16"},
        "mtp0k7s28": {"TAAF_VLLM_MTP_TOKENS": "0", "TAAF_VLLM_KV_CACHE_MEMORY_BYTES": str(7 * 1024 ** 3),
                      "TAAF_VLLM_MAX_NUM_SEQS": "28"}}

# ---- seam 1: the arm env must change the resolved tuning -----------------------------------------------
spec = importlib.util.spec_from_file_location("serving_setup_probe", SETUP)
mod = importlib.util.module_from_spec(spec)
os.environ.setdefault("TAAF_KAGGLE_BUNDLE_DIR", str(HERE))
os.environ.setdefault("TAAF_KAGGLE_WORKING_DIR", str(HERE))
os.environ.setdefault("TAAF_KAGGLE_SETUP_ENV", str(HERE / "_probe_setup_env.json"))
try:
    spec.loader.exec_module(mod)
except Exception as exc:                     # the module does real work at import on Kaggle
    print(f"note: serving_setup did not import standalone ({type(exc).__name__}); reading its resolver by ast")
    mod = None

resolve = None
if mod is not None:
    resolve = getattr(mod, "resolve_vllm_tuning", None)


def tuning(arm):
    saved = dict(os.environ)
    try:
        for k in list(os.environ):
            if k.startswith("TAAF_VLLM_"):
                del os.environ[k]
        os.environ.update(PROFILE)
        os.environ.update(ARMS[arm])
        return resolve()
    finally:
        os.environ.clear()
        os.environ.update(saved)


if resolve is None:
    # Fall back to the source itself: assert each arm's key is one the resolver actually reads, by name.
    src = SETUP.read_text(encoding="utf-8")
    for arm, delta in ARMS.items():
        for key in delta:
            if f'"{key}"' not in src:
                fails.append(f"arm {arm}: {key} does not appear in serving_setup.py at all")
    # control: a key that must NOT be there
    if '"TAAF_VLLM_NOT_A_REAL_KNOB"' in src:
        fails.append("control failed: a fabricated env key was found in the source")
    print("seam 1 (by name): every arm key is read by serving_setup.py; a fabricated key is not")
else:
    base = tuning("a")
    print(f"seam 1: resolver found, arm a tuning mtp={base['mtp_speculative_tokens']} "
          f"index_share={base['mtp_index_share_for_iteration']}")
    b, d = tuning("b"), tuning("d")
    if not b["mtp_index_share_for_iteration"]:
        fails.append("arm b did not turn on mtp_index_share_for_iteration")
    if int(d["mtp_speculative_tokens"]) != 0:
        fails.append(f"arm d did not turn MTP off: {d['mtp_speculative_tokens']}")
    if int(base["mtp_speculative_tokens"]) != 3 or base["mtp_index_share_for_iteration"]:
        fails.append(f"arm a is not the shipped profile: {base}")
    for arm, want_seqs, want_kv in (("s16", 16, 5 * 1024 ** 3), ("s28", 28, 5 * 1024 ** 3), ("k10s16", 16, 10 * 1024 ** 3), ("k7s16", 16, 7 * 1024 ** 3)):
        t = tuning(arm)
        if int(t["max_num_seqs"]) != want_seqs or int(t["kv_cache_memory_bytes"]) != want_kv:
            fails.append(f"arm {arm}: max_num_seqs={t['max_num_seqs']} kv={t['kv_cache_memory_bytes']} (want {want_seqs}, {want_kv})")
        if int(t["mtp_speculative_tokens"]) != 3:
            fails.append(f"arm {arm} moved MTP: {t['mtp_speculative_tokens']}")
    for arm, want_seqs in (("mtp0k7s16", 16), ("mtp0k7s28", 28)):
        t = tuning(arm)
        if int(t["max_num_seqs"]) != want_seqs or int(t["kv_cache_memory_bytes"]) != 7 * 1024 ** 3 or int(t["mtp_speculative_tokens"]) != 0:
            fails.append(f"arm {arm}: seqs={t['max_num_seqs']} kv={t['kv_cache_memory_bytes']} mtp={t['mtp_speculative_tokens']} (want {want_seqs}, 7 GiB, 0)")
    print("seam 1 ok: each arm changes exactly its own field (a/b/d + s16/s28/k10s16/k7s16 + mtp0k7s16/mtp0k7s28)")

# ---- seam 2: the bench's own _spec, executed from the NOTEBOOK's source ---------------------------------
cell15 = "".join(json.load(open(NB, encoding="utf-8"))["cells"][15]["source"])
i = cell15.index("SPEC_KEYS = (")
j = cell15.index("def _one(")
ns = {"re": re}
exec("import re\n" + cell15[i:j], ns)
_spec = ns["_spec"]

BODY_PRESENT = """# HELP vllm:spec_decode_num_draft_tokens_total drafted
# TYPE vllm:spec_decode_num_draft_tokens_total counter
vllm:spec_decode_num_draft_tokens_total{model_name="m"} 1200.0
vllm:spec_decode_num_accepted_tokens_total{model_name="m"} 480.0
vllm:spec_decode_num_drafts_total{model_name="m"} 400.0
vllm:num_requests_running{model_name="m"} 8.0
vllm:num_preemptions_total{engine="0",model_name="m"} 7.0
"""
BODY_ABSENT = """# HELP vllm:num_requests_running running
vllm:num_requests_running{model_name="m"} 8.0
vllm:generation_tokens_total{model_name="m"} 9999.0
"""

got = _spec(BODY_PRESENT)
if got["spec_decode_num_draft_tokens_total"] != 1200.0 or got["spec_decode_num_accepted_tokens_total"] != 480.0:
    fails.append(f"_spec misread a present body: {got}")
if len(got["seen_lines"]) != 3:
    fails.append(f"_spec should see 3 spec_decode value lines, saw {len(got['seen_lines'])}")
print(f"seam 2 ok: present body -> draft {got['spec_decode_num_draft_tokens_total']}, "
      f"accepted {got['spec_decode_num_accepted_tokens_total']}, lines {len(got['seen_lines'])}")
# v2: the preemption counter is the FEASIBILITY control for the s16/s28/k10s16 arms. The regex lives inside a
# doubly-quoted notebook string, so its escaping is exactly the thing this line proves.
if got.get("num_preemptions_total") != 7.0 or len(got.get("preempt_lines", [])) != 1:
    fails.append(f"_spec did not read the preemption counter: {got.get('num_preemptions_total')} / {got.get('preempt_lines')}")
else:
    print("seam 2 ok: preemption counter 7.0 read through the notebook's own regex (escaping survives)")

# the control that matters: absent counters must be DISTINGUISHABLE from zero drafts
gone = _spec(BODY_ABSENT)
if gone["spec_decode_num_draft_tokens_total"] != 0.0:
    fails.append("an absent counter should read 0.0")
if gone["seen_lines"]:
    fails.append(f"control failed: seen_lines is non-empty on a body with no spec metrics: {gone['seen_lines']}")
print("control ok: a body with no spec_decode metrics yields 0 drafts AND 0 seen_lines -- the kernel reports "
      "METRIC_NAMES_UNKNOWN there, not VOID")

# ---- the bench must not have kept any game machinery ---------------------------------------------------
for bad in ("bm.game_runs", "PUBLIC25_AUDIT", "submission.parquet", "evaluate_runs"):
    if bad in cell15:
        fails.append(f"cell 15 still carries game machinery: {bad}")
for need in ("THUI_L4_CONTROL", "teardown_commands.json", "temperature", "top_p", "num_preemptions_total", '"c25"'):
    if need not in cell15:
        fails.append(f"cell 15 is missing {need}")
print("cell 15 ok: no game machinery, teardown present, harness sampling present")

print("\n" + ("FAIL: " + " | ".join(fails) if fails else "ALL TEETH PASS (2 seams + 2 controls)"))
raise SystemExit(1 if fails else 0)
