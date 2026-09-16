"""thui-l4 -- kernel-path sanity: is MTP-3 paying for itself on the shipped serving profile? (B80 lever L4)

Why (2026-09-11, B80). Two structural smells sit in our own kernel log, and one direct measurement agrees with both:

  1. vLLM warns on every start: `speculative.py:1010 Enabling num_speculative_tokens > 1 will run multiple times of
     forward on same MTP layer, which may result in lower acceptance rate`. Our profile sets MTP=3.
  2. The shipped profile `kv5-bf16-mtp3-c8-cg32` sets `TAAF_VLLM_MTP_TOKENS=3` FLAT and leaves two knobs the serving
     author himself provides unset: `TAAF_VLLM_MTP_INDEX_SHARE_FOR_ITERATION` (-> `index_share_for_mtp_iteration`,
     which addresses exactly the repeated-layer path in (1)) and `TAAF_VLLM_MTP_DYNAMIC_BATCH_SCHEDULE`
     (-> `num_speculative_tokens_per_batch_size`, so speculation can shrink as the batch fills). We run at
     `--max-num-seqs 8` with solver concurrency 28, i.e. a saturated batch, where speculation pays least.
  3. B78 (Watchara, MTP-OFF at full width) produced **4,049 actions against our two-draw pool's 3,739 mean** -- turning
     MTP off did not reduce action volume. Our own draws span 3,553-3,925, so 4,049 is just above our max: suggestive,
     not decisive, and no throughput number was recorded on either side.

None of that measures tok/s. This bench does, with no games, in under 20 minutes of GPU per arm.

What it does. Cells 0-14 are untouched, so the server comes up exactly as it does on a real run, under the real
profile. Cell 15's game loop is replaced by a load generator that replays THREE REAL analyzer prompts lifted from our
own transcripts (tn36 / vc33 / sk48, ~5.8-6.7 k tokens each) at the harness's own sampling parameters
(`temperature=0.6`, `top_p=0.95`, `max_tokens` = server default -- read from `tool_agent.py:145-146,1293-1295`), at
concurrency 1 and at concurrency 8, and reads vLLM's own `/metrics` for the speculative-decoding counters before and
after each phase.

Arms, one kernel push each (the env is the ONLY difference; every other cell is byte-identical between them):

  --arm a   shipped profile, MTP=3 flat                                    <- the CONTROL
  --arm b   shipped + TAAF_VLLM_MTP_INDEX_SHARE_FOR_ITERATION=1
  --arm d   shipped with TAAF_VLLM_MTP_TOKENS=0 (no speculation at all)    <- the reference

Pre-registered read (written before the first push):
  1. CONTROL, and it decides whether anything else can be read: arm a must report `draft_tokens > 0` and arm d must
     report `draft_tokens == 0`. If arm a drafts nothing, the bench is not measuring MTP and every number below is
     VOID -- not evidence about the lever.
  2. PRIMARY metric: aggregate output tokens/s at concurrency 8, which is the operating point we ship. Secondary:
     per-request median tok/s at concurrency 1, and acceptance rate = accepted / draft.
  3. DEAD for L4 if no arm beats arm a by more than 10 % on the primary metric. The knobs are then correctly left off
     and MTP-3 is not the tail's problem.
  4. ALIVE if an arm beats arm a by more than 10 % at concurrency 8. That justifies -- and only then -- a full-width
     25-game A/B, which is 2.4 GPU-h per draw and is NOT part of L4.
  5. What this cannot say: nothing here is a score. A throughput win has to survive a full-width A/B before it is a
     lever, because every solver-side lever measured on this base so far has priced NULL.

------------------------------------------------------------------------------------------------------------------
v2 (2026-09-14, ARENA 3 Phase 1 -- the winner's bench). Arm a v1 ran under the spec above (c1 + c8, uncapped output:
13.5-16.5 k tokens/request, 50 min): acceptance 0.51 at both concurrencies, 320 tok/s at c8, control OK. Those rows
stay as measured and are NOT compared to v2 rows.

The ARENA 3 winner (axis B) showed the solver admits 28 concurrent games while vLLM admits `--max-num-seqs 8`, with a
~125-140 s per-turn residual the judge could not attribute to generation (median wall/turn 152 s on fast-v0 d2 vs
12-29 s of generation at L4's measured rates). vLLM's own server log explains the 8: `GPU KV cache size: 105,202
tokens, Maximum concurrency for 32,768 tokens per request: 3.21x` on a 5 GiB KV set by config with memory profiling
SKIPPED, weights 81.8 GiB of 94.4 free -- so seqs and KV move together or preempt.

v2 arms (env is the only difference; cells [0,3] differ, the bench cell is sha-identical across arms):
  --arm a       shipped profile                                   <- the v2 CONTROL (re-run; v1 rows are another spec)
  --arm s16     TAAF_VLLM_MAX_NUM_SEQS=16
  --arm s28     TAAF_VLLM_MAX_NUM_SEQS=28
  --arm k10s16  TAAF_VLLM_KV_CACHE_MEMORY_BYTES=10 GiB + MAX_NUM_SEQS=16
v2 phases: c8 x3 rounds (the shipped server batch) and c25 x2 rounds (the shipped SOLVER concurrency), max_tokens 2048
(~1.3x the measured median harness turn of 1,553 tokens) so an arm is ~15 min. Reads `vllm:num_preemptions_total`
and any metric line containing "preempt" (raw lines kept, same guard as the spec counters: a missing NAME must not
read as zero preemptions).

Pre-registered read for v2:
  1. FEASIBILITY per arm: the server must start and both phases complete. A refused start / OOM is a RESULT (the knob
     is outside the card), not a failure of the bench. `preemptions` per phase is printed for every arm, incl. a.
  2. PRIMARY: aggregate output tok/s in phase c25 -- the operating point the solver actually presents.
  3. ALIVE if an arm beats arm a (v2) by > 10 % on the primary WITH preemptions == 0 in c25. An arm that is faster
     only while preempting is not counted; preemption at 25-way is what a full run would pay all wall long.
  4. DEAD if no arm clears 3. Then the 8-slot cap is where the card's KV ends and the queueing residual is paid for by
     memory we do not have; B's +6.84 ceiling is unreachable by this knob.
  5. Nothing here is a score. ALIVE buys a full-width A/B (2.4 GPU-h per draw); it does not buy a submission.

Build:  PYTHONUTF8=1 python thui-l4/build_notebook.py --arm a
Push:   python scripts/kaggle_push_kernel.py <this dir>   (from arc-agi-pub; rebuild the arm first -- code_file is shared)
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAST = HERE.parent / "thui-fast"
SRC_NB = FAST / "upstream-keithtyser-duck-qwen3-8-flash-next-nvfp4-mtp.ipynb"
SRC_META = FAST / "upstream-kernel-metadata.json"
PROMPTS = HERE / "bench_prompts.json"
OWNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), "sahasawatt")
ARM = next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--arm"), "a")
assert ARM in ("a", "b", "d", "s16", "s28", "k10s16", "k7s16", "mtp0k7s16", "mtp0k7s28"), f"unknown arm {ARM!r}"
SLUG = f"thui-l4-{ARM}"
OUT_NB = HERE / f"taaf-{SLUG}.ipynb"

ARM_ENV = {
    "a": {},                                                        # shipped profile, unchanged
    "b": {"TAAF_VLLM_MTP_INDEX_SHARE_FOR_ITERATION": "1"},
    "d": {"TAAF_VLLM_MTP_TOKENS": "0"},
    # ARENA 3 (2026-09-14) winner B, Phase 1: the solver admits 28 concurrent games but vLLM admits 8, and vLLM's own
    # log says KV 5 GiB = 105,202 tokens = 3.21x of a 32k request -- so seqs and KV move together or preempt.
    "s16": {"TAAF_VLLM_MAX_NUM_SEQS": "16"},
    "s28": {"TAAF_VLLM_MAX_NUM_SEQS": "28"},
    "k10s16": {"TAAF_VLLM_KV_CACHE_MEMORY_BYTES": str(10 * 1024 ** 3), "TAAF_VLLM_MAX_NUM_SEQS": "16"},
    # k10s16 OOMed at warmup (42 MiB free after weights 81.8 + KV 10); 7 GiB sits inside the ~7 GiB headroom the 5 GiB profile left
    "k7s16": {"TAAF_VLLM_KV_CACHE_MEMORY_BYTES": str(7 * 1024 ** 3), "TAAF_VLLM_MAX_NUM_SEQS": "16"},
    # k7s16 OOMed by ~370 MiB at the first batched prefill (248 MiB free). B78's full-25 at MTP 0 ran 4,049 actions vs 3,553 at
    # MTP 3 (LEDGER), and the bench's acceptance was 0.43 -- so the draft head is memory spent on nothing at c25. This arm
    # asks the one question left on axis B: does MTP-0 give back enough for KV 7 GiB to start and admit ~7 sequences?
    "mtp0k7s16": {"TAAF_VLLM_MTP_TOKENS": "0", "TAAF_VLLM_KV_CACHE_MEMORY_BYTES": str(7 * 1024 ** 3),
                  "TAAF_VLLM_MAX_NUM_SEQS": "16"},
    # mtp0k7s16 (2026-09-15 01:18) ALIVE: KV 7 GiB at MTP 0 = 263,568 tokens (per-seq ~10.4k vs ~19k at MTP 3 -- the draft head
    # was half the KV cost), c25 aggregate 570 tok/s (+59% vs 359), median request 59 s (vs 114), preempt 0, and `max Running` hit
    # the 16 cap with KV at 67%. So the seqs cap binds again; 28 = the solver's own concurrency, the last rung on this axis.
    "mtp0k7s28": {"TAAF_VLLM_MTP_TOKENS": "0", "TAAF_VLLM_KV_CACHE_MEMORY_BYTES": str(7 * 1024 ** 3),
                  "TAAF_VLLM_MAX_NUM_SEQS": "28"},
}[ARM]

CELL0_MD = f"""# {SLUG} (Thuitanium / Knowless Crew)

**B80 lever L4 -- kernel-path sanity, no games.** Forked from
[Keith Tyser's Flash-Next NVFP4 + MTP duck kernel](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp),
itself a fork of [Tufa Labs' Duck harness](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner).
Cells 0-14 are unchanged, so the vLLM server starts under the real profile; cell 15 plays no games and instead replays
three real analyzer prompts at concurrency 1 and 8 and reads vLLM's own speculative-decoding counters.

Arm **{ARM}** -- env delta over the shipped profile `kv5-bf16-mtp3-c8-cg32`: `{json.dumps(ARM_ENV) or "none (control)"}`.

Refuses a competition rerun. Writes `l4_bench.json` to the working dir and prints `THUI_L4_BENCH` lines.
"""

CELL3_ARM = f"""
# thui-l4: arm env delta, applied AFTER the measured profile and BEFORE any serving setup command runs.
THUI_L4_ARM = {ARM!r}
THUI_L4_ARM_ENV = {json.dumps(ARM_ENV, indent=4)}
for key, value in THUI_L4_ARM_ENV.items():
    os.environ[key] = value
print(f'THUI_L4_ARM name={{THUI_L4_ARM}} delta={{json.dumps(THUI_L4_ARM_ENV)}}', flush=True)
"""

CELL15 = '''# thui-l4 bench: NO GAMES. The server is already serving from cell 9's setup commands.
import concurrent.futures
import re
import statistics
import time
import urllib.request

if TRUE_SUBMISSION or os.environ.get("KAGGLE_IS_COMPETITION_RERUN") not in (None, "", "0"):
    raise RuntimeError("thui-l4 is a throughput bench and must never enter a competition rerun.")

BASE = "http://127.0.0.1:1234"
MODEL = "Qwen/Qwen3.8-Flash-Next-NVFP4"
# The harness's own sampling, read from inference/agent/tool_agent.py:145-146,1293-1295.
TEMPERATURE, TOP_P = 0.6, 0.95
MAX_TOKENS = 2048          # v2: ~1.3x the measured median harness turn (1,553 tokens), same for every arm
PROMPTS = json.loads((BUNDLE_DIR.parent / "thui_l4_prompts.json").read_text(encoding="utf-8")) \\
    if (BUNDLE_DIR.parent / "thui_l4_prompts.json").is_file() else THUI_L4_PROMPTS


def _post(payload, timeout=900):
    req = urllib.request.Request(
        BASE + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read())


def _metrics():
    """vLLM's own Prometheus counters. The speculative ones are the only place acceptance is reported."""
    with urllib.request.urlopen(BASE + "/metrics", timeout=60) as response:
        return response.read().decode("utf-8")


SPEC_KEYS = (
    "vllm:spec_decode_num_draft_tokens_total",
    "vllm:spec_decode_num_accepted_tokens_total",
    "vllm:spec_decode_num_drafts_total",
)


def _spec(text):
    """Counters plus the RAW matching lines. A metric NAME that does not exist in this vLLM build would
    otherwise return 0.0, which is indistinguishable from 'MTP drafted nothing' -- the reading that decides
    the control below. `seen_lines` makes a name mismatch visible instead of silent."""
    out = {"seen_lines": [l for l in text.splitlines() if "spec_decode" in l and not l.startswith("#")],
           "preempt_lines": [l for l in text.splitlines() if "preempt" in l.lower() and not l.startswith("#")]}
    pre = re.findall(r"^vllm:num_preemptions_total(?:\{[^}]*\})? ([0-9.eE+-]+)$", text, re.M)
    out["num_preemptions_total"] = sum(float(v) for v in pre) if pre else 0.0
    for key in SPEC_KEYS:
        values = re.findall(r"^" + re.escape(key) + r"(?:\\{[^}]*\\})? ([0-9.eE+-]+)$", text, re.M)
        out[key.split(":", 1)[1]] = sum(float(v) for v in values) if values else 0.0
    return out


def _one(prompt_text):
    t0 = time.time()
    body = _post({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "max_tokens": MAX_TOKENS,
    })
    dt = time.time() - t0
    usage = body.get("usage") or {}
    out_tok = int(usage.get("completion_tokens") or 0)
    return {"s": dt, "out": out_tok, "in": int(usage.get("prompt_tokens") or 0),
            "tok_s": out_tok / dt if dt > 0 else 0.0}


def phase(name, concurrency, rounds):
    before = _spec(_metrics())
    jobs = [PROMPTS[i % len(PROMPTS)]["text"] for i in range(concurrency * rounds)]
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(_one, jobs))
    wall = time.time() - t0
    after = _spec(_metrics())
    delta = {k: after[k] - before[k] for k in after if k not in ("seen_lines", "preempt_lines")}
    draft = delta["spec_decode_num_draft_tokens_total"]
    row = {
        "phase": name, "concurrency": concurrency, "requests": len(results), "wall_s": round(wall, 2),
        "out_tokens": sum(r["out"] for r in results),
        "aggregate_tok_s": round(sum(r["out"] for r in results) / wall, 2) if wall > 0 else 0.0,
        "median_req_tok_s": round(statistics.median(r["tok_s"] for r in results), 2),
        "median_req_s": round(statistics.median(r["s"] for r in results), 2),
        "draft_tokens": draft,
        "accepted_tokens": delta["spec_decode_num_accepted_tokens_total"],
        "acceptance": round(delta["spec_decode_num_accepted_tokens_total"] / draft, 4) if draft > 0 else None,
        "spec_metric_lines": len(after["seen_lines"]),
        "spec_metric_sample": after["seen_lines"][:6],
        "preemptions": delta.get("num_preemptions_total", 0.0),
        "preempt_metric_lines": len(after["preempt_lines"]),
        "preempt_sample": after["preempt_lines"][:4],
    }
    print("THUI_L4_BENCH " + json.dumps(row), flush=True)
    return row


try:
    # One warm request first: the first call pays cudagraph capture and is not a throughput sample.
    warm = _one(PROMPTS[0]["text"])
    print(f"THUI_L4_WARM {json.dumps(warm)}", flush=True)

    # v2 phases (ARENA 3 Phase 1): c8 = the shipped server batch, c25 = the shipped SOLVER concurrency. max_tokens is
    # capped at the harness's real turn size (~1.5k tokens/turn measured on fast-v0 d2) so 50 requests at c25 finish in
    # minutes; arm a's v1 numbers (uncapped, c1+c8) are a different spec and are not compared to v2 rows.
    rows = [phase("c8", 8, 3), phase("c25", 25, 2)]
    out = {
        "arm": THUI_L4_ARM,
        "arm_env": THUI_L4_ARM_ENV,
        "profile": PUBLIC25_VLLM_PROFILE_NAME,
        "profile_env": PUBLIC25_VLLM_PROFILE_ENV,
        "sampling": {"temperature": TEMPERATURE, "top_p": TOP_P, "max_tokens": MAX_TOKENS},
        "bench_spec": "v2",
        "prompts": [{"game": p["game"], "chars": len(p["text"])} for p in PROMPTS],
        "warm": warm,
        "phases": rows,
    }
    (WORKING_DIR / "l4_bench.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    # The control that decides whether any number above is readable.
    drafted = sum(r["draft_tokens"] for r in rows)
    seen = sum(r["spec_metric_lines"] for r in rows)
    expect_spec = int(os.environ.get("TAAF_VLLM_MTP_TOKENS", "3")) > 0
    # Three outcomes, not two: a metric NAME this build does not publish reads as draft_tokens == 0, which is
    # the same number MTP-off produces. Only `seen` separates them, and it decides whether the acceptance
    # column is readable at all. The tok/s columns do not depend on any of this.
    if expect_spec and seen == 0:
        verdict = "METRIC_NAMES_UNKNOWN -- acceptance unreadable, tok/s still valid"
    elif (drafted > 0) == expect_spec:
        verdict = "OK"
    else:
        verdict = "VOID"
    print(f"THUI_L4_CONTROL mtp_tokens={os.environ.get('TAAF_VLLM_MTP_TOKENS')} "
          f"draft_tokens={drafted} spec_metric_lines={seen} expected_speculation={expect_spec} "
          f"verdict={verdict}", flush=True)
    print(f"THUI_L4_DONE arm={THUI_L4_ARM} -> {WORKING_DIR / 'l4_bench.json'}", flush=True)
finally:
    for command in json.loads((BUNDLE_DIR / "teardown_commands.json").read_text()):
        print(f"taaf.kaggle: teardown command: {command}", flush=True)
        subprocess.run(command, shell=True, check=False, cwd=WORKING_DIR,
                       env=_command_env(), timeout=30.0)
'''

COMP = "arc-prize-2026-arc-agi-3"
WHEELS_NESTED = f"/kaggle/input/competitions/{COMP}/arc_agi_3_wheels"
CELL5_ANCHOR = '        "' + WHEELS_NESTED + '",\n'
CELL5_RESOLVER = """# thui-l4: resolve the competition mount instead of assuming its layout (Kaggle serves either
# /kaggle/input/competitions/<comp> or /kaggle/input/<comp>, varying between runs -- B71).
_COMP_CANDIDATES = ["/kaggle/input/competitions/__COMP__", "/kaggle/input/__COMP__"]
_COMP_DIR = next((_p for _p in _COMP_CANDIDATES if os.path.isdir(_p)), None)
assert _COMP_DIR is not None, "thui-l4: no competition mount found; /kaggle/input holds " + repr(
    sorted(os.listdir("/kaggle/input")) if os.path.isdir("/kaggle/input") else "MISSING")
_WHEELS = os.path.join(_COMP_DIR, "arc_agi_3_wheels")
assert os.path.isdir(_WHEELS), "thui-l4: resolved wheels dir is not a directory: " + _WHEELS
print("thui-l4: competition mount = " + _COMP_DIR, flush=True)
""".replace("__COMP__", COMP)


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 18, f"{SRC_NB.name}: expected 18 cells, found {len(cells)}"
    before = ["".join(c["source"]) for c in cells]
    prompts = json.loads(PROMPTS.read_text(encoding="utf-8"))
    assert len(prompts) == 3 and all(len(p["text"]) > 15000 for p in prompts), "bench prompts look wrong"

    cells[0]["cell_type"] = "markdown"
    cells[0]["source"] = CELL0_MD.splitlines(keepends=True)
    cells[1]["source"] = ["# thui-l4 bench (Thuitanium)\n", "\n",
                          "No games. Throughput and speculative-decoding acceptance only.\n"]
    cells[1].pop("attachments", None)

    s3 = "".join(cells[3]["source"])
    assert s3.count("PUBLIC25_VLLM_PROFILE name=") == 1
    cells[3]["source"] = (s3 + CELL3_ARM).splitlines(keepends=True)

    s5 = "".join(cells[5]["source"])
    assert s5.count(CELL5_ANCHOR) == 1, f"cell 5 wheels anchor x{s5.count(CELL5_ANCHOR)}"
    cells[5]["source"] = (CELL5_RESOLVER + s5.replace(CELL5_ANCHOR, "        _WHEELS,\n")).splitlines(keepends=True)

    body = ("THUI_L4_PROMPTS = " + json.dumps(prompts, ensure_ascii=False) + "\n\n" + CELL15)
    cells[15]["source"] = body.splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert changed == [0, 1, 3, 5, 15], f"cells changed {changed}"
    assert "attachments" not in cells[1] and "tufa_labs.png" not in json.dumps(nb)
    for i, c in enumerate(cells):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]), filename=f"cell{i}")
    assert after[9] == before[9] and after[13] == before[13] and after[11] == before[11]
    assert "bm.game_runs" not in after[15] and "PUBLIC25_AUDIT" not in after[15], "cell 15 still plays games"
    assert "THUI_L4_CONTROL" in after[15] and "teardown_commands.json" in after[15]

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(SRC_META.read_text(encoding="utf-8"))
    meta.pop("id_no", None)
    assert meta["machine_shape"] == "NvidiaRtxPro6000" and meta["enable_gpu"] is True
    meta["id"] = f"{OWNER}/{SLUG}"
    meta["title"] = SLUG
    meta["code_file"] = OUT_NB.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}, arm {ARM}, env {ARM_ENV or 'control'}")


if __name__ == "__main__":
    main()
