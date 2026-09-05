"""B65 prompt-lint on REAL dropped-turn blocks, against a local same-family model (qwen3:8b via ollama).

What this CAN establish: that the shipped prompt is followable at all on real input -- five labels emitted,
step ids cited, output inside the 600-token cap. What it CANNOT: whether compaction moves levels (needs the
games, the 27B and the clock), and whether the call is affordable at 25-game concurrency (that is the smoke).
Stronger evidence already exists for the format question: thui-reflect-v1-1 (Qwen3.8-27B, thinking off,
cap 1200) returned all SEVEN labelled fields on 105 of 105 calls.

Control: one run with the labels stripped out of the prompt -- if the counter still reports 5/5, it is reading
the prompt rather than the reply.
"""
import glob, json, os, re, sys, time, urllib.request

MODEL = os.environ.get('LINT_MODEL', 'qwen3:8b')
D = os.environ.get('LINT_EVENTS', 'C:/Users/Vampi/Desktop/archive/arc-traj/thui-v3-1/**/*_p0_events.jsonl')  # banked trajectories, outside every repo
LABELS = ("Rules:", "Unknown:", "No-op/harmful:", "Hypotheses:", "Plan:")

NB = os.environ.get("LINT_NB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "taaf-thui-compact-v0.ipynb"))
_c12 = "".join(json.load(open(NB, encoding="utf-8"))["cells"][12]["source"])
_m = re.search(r"_COMPACT_SYSTEM = \((.*?)\n\)\n", _c12, re.S)
assert _m, "prompt not found in the notebook -- the lint must test the SHIPPED text, never a copy"
_ns = {}
exec("SYS=(" + _m.group(1) + chr(10) + ")", _ns)
SYSTEM = _ns["SYS"]
SYSTEM_NOLABELS = re.sub(r"Output exactly these labelled lines.*?No preamble, no code\.",
                         "Write a short memento, under 120 words. No preamble, no code.", SYSTEM, flags=re.S)


def blocks(path, first_step, n_steps, per_turn=600):
    """Render n_steps consecutive acting steps the way _compact_dropped would: one line per message, capped."""
    by_step = {}
    for line in open(path, encoding='utf-8', errors='replace'):
        r = json.loads(line)
        try:
            s = int(r.get('analysis_step'))
        except (TypeError, ValueError):
            continue
        if not (first_step <= s < first_step + n_steps):
            continue
        if r.get('type') == 'analysis':
            tr = r.get('transcript') or ''
            tail = tr[-per_turn:]
            by_step.setdefault(s, []).append(f"[assistant] step {s}: {tail}")
        elif r.get('type') == 'action':
            by_step.setdefault(s, []).append(
                f"[tool] step {s}: {r.get('action_name','?')} -> board_changed={r.get('board_changed')} "
                f"level={r.get('level')} reward={r.get('reward')}")
    return "\n".join(l for s in sorted(by_step) for l in by_step[s])


def ask(system, user, num_predict=600):
    body = json.dumps({"model": MODEL, "think": False, "stream": False,
                       "options": {"num_predict": num_predict, "temperature": 0.6},
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request('http://127.0.0.1:11434/api/chat', data=body,
                                 headers={'Content-Type': 'application/json'}, method='POST')
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as r:
        out = json.loads(r.read().decode())
    return out.get('message', {}).get('content', ''), time.time() - t0, out.get('eval_count', 0)


files = sorted(glob.glob(D, recursive=True))
print(f"model={MODEL} games available={len(files)}")
rows = []
for f in files[:3]:
    game = os.path.basename(f)[:4]
    block = blocks(f, 3, 10)
    if len(block) < 500:
        print(f"{game}: block too small ({len(block)} chars), skipping"); continue
    block = block[-6000:]
    user = f"PREVIOUS MEMENTO:\n(none yet)\n\nTURNS ABOUT TO BE DELETED (oldest first):\n{block}"
    txt, dt, n = ask(SYSTEM, user)
    labs = [l for l in LABELS if l in txt]
    steps_cited = len(re.findall(r'\bstep\s*\d+', txt, re.I))
    words = len(txt.split())
    rows.append((game, len(labs), steps_cited, words, len(txt), round(dt), n))
    print(f"{game}: labels={len(labs)}/5 missing={[l.rstrip(':') for l in LABELS if l not in labs]} "
          f"step-citations={steps_cited} words={words} chars={len(txt)} eval_tokens={n} {dt:.0f}s")
    print("   " + txt.replace("\n", "\n   ")[:700])

# control: the same block with the labels removed from the prompt
if rows:
    f = files[0]; block = blocks(f, 3, 10)[-6000:]
    txt, dt, n = ask(SYSTEM_NOLABELS, f"PREVIOUS MEMENTO:\n(none yet)\n\nTURNS ABOUT TO BE DELETED (oldest first):\n{block}")
    labs = [l for l in LABELS if l in txt]
    print(f"CONTROL (labels removed from the prompt): labels={len(labs)}/5 words={len(txt.split())} {dt:.0f}s "
          f"-- a 5/5 here would mean the counter reads the prompt, not the reply")
print("\nSUMMARY", rows)
