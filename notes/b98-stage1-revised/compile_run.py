"""Rev-5 compile runner: one codex call per selected rule sentence, resume-safe, output per sentence id.

usage: python compile_run.py <extract.json> <out-dir> [workers=6]
Compiler fixed by the rev-5 addendum: codex gpt-5.6-luna, reasoning effort low, --sandbox read-only, prompt
compile_prompt_rev5.md with {game} {level} {sentence} {board} substituted (plain replace: the prompt holds JSON braces).
Each <id>.json: status OK | NONE | INVALID | ERROR, hypothesis (DSL dict or null), generated_tokens, input_tokens.
ERROR is a failed CALL, not a compile outcome: it is left for a re-run and never scored.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMPT = (HERE / "compile_prompt_rev5.md").read_text(encoding="utf-8")
MODEL, EFFORT, TIMEOUT_S = "gpt-5.6-luna", "low", 300
COLORS = set("WwgGcBMPRbSYOrNp")
NAMES = {"UP", "DOWN", "LEFT", "RIGHT", "SPACE", "RESET", "CLICK"} | {f"ACTION{i}" for i in range(1, 8)}
STOP = {"flag": None}


def valid(h):
    """Structural check against SPEC.md's DSL; anything else is INVALID, never a hypothesis."""
    try:
        a, t, e = h["action"], h["target"], h["effect"]
        if a["name"] not in NAMES or set(a) - {"name", "at"}:
            return False
        if "at" in a and (a["name"] != "CLICK" or len(a["at"]) != 2 or not all(isinstance(v, int) for v in a["at"])):
            return False
        if t.get("color") not in COLORS:
            return False
        if "region" in t and (len(t["region"]) != 4 or not all(isinstance(v, int) for v in t["region"])):
            return False
        k = e["type"]
        if k == "move":
            return isinstance(e["dr"], int) and isinstance(e["dc"], int)
        if k == "recolor":
            return e["from"] in COLORS and e["to"] in COLORS
        if k == "count_delta":
            return isinstance(e["delta"], int)
        return k in {"appear", "disappear", "no_change", "any_change"}
    except (KeyError, TypeError):
        return False


def usage(jsonl):
    """(generated, input) from the CLI's turn.completed usage. Probed 2026-09-28 (run log): codex 0.153.4 reports
    output_tokens INCLUSIVE of reasoning (49 output vs 42 reasoning on a 2-char answer), so generated = output_tokens;
    adding reasoning_output_tokens would count reasoning twice."""
    gen = inp = None
    for line in jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "turn.completed":
            u = ev.get("usage") or {}
            gen = u.get("output_tokens")
            inp = u.get("input_tokens")
    return gen, inp


def error_text(jsonl):
    for line in jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
        if '"error"' in line or "turn.failed" in line:
            return line[:300]
    return ""


def one(out, r, game):
    rid = r["id"]
    done = out / f"{rid}.json"
    if done.exists() and json.loads(done.read_text(encoding="utf-8")).get("status") != "ERROR":
        return "skip"
    if STOP["flag"]:
        return "stopped"
    prompt = (PROMPT.replace("{game}", game).replace("{level}", str(r["level"]))
              .replace("{sentence}", r["text"]).replace("{board}", r["board"] or ""))
    (out / f"{rid}.prompt").write_text(prompt, encoding="utf-8", newline="\n")
    for f in (f"{rid}.out", f"{rid}.jsonl"):
        (out / f).unlink(missing_ok=True)
    cmd = ["wsl.exe", "-d", "Ubuntu-24.04", "--cd", str(out), "-e", "bash", "-c",
           f'codex exec --sandbox read-only --skip-git-repo-check -m {MODEL} -c model_reasoning_effort="{EFFORT}" '
           f"--json -o {rid}.out < {rid}.prompt > {rid}.jsonl 2> {rid}.err; echo $? > {rid}.exit"]
    try:
        subprocess.run(cmd, timeout=TIMEOUT_S, capture_output=True)
    except subprocess.TimeoutExpired:
        pass
    jl, o = out / f"{rid}.jsonl", out / f"{rid}.out"
    gen, inp = usage(jl) if jl.exists() else (None, None)
    rec = {"id": rid, "game": game, "level": r["level"], "generated_tokens": gen, "input_tokens": inp,
           "model": MODEL, "effort": EFFORT}
    if not o.exists() or o.stat().st_size == 0:
        err = error_text(jl) if jl.exists() else "no jsonl"
        if "usage_limit" in err or "usage limit" in err:
            STOP["flag"] = err
        rec.update(status="ERROR", hypothesis=None, error=err)
    else:
        txt = o.read_text(encoding="utf-8").strip()
        if txt == "NONE":
            rec.update(status="NONE", hypothesis=None)
        else:
            try:
                h = json.loads(txt)
                rec.update(status="OK", hypothesis=h) if valid(h) else rec.update(status="INVALID", hypothesis=None,
                                                                                  raw=txt[:500])
            except json.JSONDecodeError:
                rec.update(status="INVALID", hypothesis=None, raw=txt[:500])
    done.write_text(json.dumps(rec), encoding="utf-8")
    return rec["status"]


def main():
    ext = json.load(open(sys.argv[1], encoding="utf-8"))
    out = Path(sys.argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    jobs = [(r, game) for game, g in ext["games"].items() for r in g["rows"] if r.get("compile")]
    print(f"{len(jobs)} compile jobs, {workers} workers, model {MODEL}/{EFFORT}", flush=True)
    counts = {}
    with ThreadPoolExecutor(workers) as pool:
        for i, st in enumerate(pool.map(lambda j: one(out, *j), jobs), 1):
            counts[st] = counts.get(st, 0) + 1
            if i % 25 == 0 or i == len(jobs):
                print(f"{i}/{len(jobs)} {counts}", flush=True)
    if STOP["flag"]:
        print("STOPPED on usage limit:", STOP["flag"], flush=True)
    print("final", counts, flush=True)


if __name__ == "__main__":
    main()
