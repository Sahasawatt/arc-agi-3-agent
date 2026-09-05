"""Replay the real Kaggle request (tr87, analysis_step 3, request 1 -- the one whose reply read the header as a title)
against local qwen3-8b, three header variants x N, thinking ON as on Kaggle. Measures the misread and the tool call."""
import json, re, sys, time, urllib.request
S = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 3
LOG = S + "/kout-compact-v0/prompts/tr87-cd924810_p0.log"
OLD = "MEMENTO (turns older than the window; carried forward):"
NEW = ("[Your own notes from earlier turns of this conversation, kept after those turns were trimmed to save "
       "context. Not part of the game.]")
lines = open(LOG, encoding="utf-8", errors="replace").read().split("\n")
# first [MODEL INPUT] block only
start = lines.index("[MODEL INPUT]"); end = len(lines)
for i in range(start + 1, len(lines)):
    if lines[i] == "[MODEL INPUT]": end = i; break
blk = lines[start + 1:end]
msgs = []; cur = None; buf = []
HDR = re.compile(r"^\[(SYSTEM|USER|ASSISTANT|REASONING|ASSISTANT TOOL CALL: (\w+)|TOOL RESULT: (\S+))\]$")
def flush():
    global cur, buf
    if cur is None: return
    text = "\n".join(buf).strip()
    kind = cur[0]
    if kind == "SYSTEM": msgs.append({"role": "system", "content": text})
    elif kind == "USER": msgs.append({"role": "user", "content": text.replace("Current grid image:", "").strip()})
    elif kind == "ASSISTANT":
        if text: msgs.append({"role": "assistant", "content": text})
    elif kind == "REASONING": pass  # not resent by the harness path we replay
    elif kind.startswith("ASSISTANT TOOL CALL"):
        cid = "call_%d" % len(msgs)
        if msgs and msgs[-1]["role"] == "assistant" and "tool_calls" not in msgs[-1]:
            msgs[-1]["tool_calls"] = [{"id": cid, "type": "function", "function": {"name": "python", "arguments": json.dumps({"code": text})}}]
        else:
            msgs.append({"role": "assistant", "content": "", "tool_calls": [{"id": cid, "type": "function", "function": {"name": "python", "arguments": json.dumps({"code": text})}}]})
    elif kind.startswith("TOOL RESULT"):
        cid = next((m["tool_calls"][0]["id"] for m in reversed(msgs) if m["role"] == "assistant" and m.get("tool_calls")), "call_x")
        msgs.append({"role": "tool", "tool_call_id": cid, "content": text})
    buf = []
for l in blk:
    m = HDR.match(l)
    if m: flush(); cur = (m.group(1),); continue
    buf.append(l)
flush()
assert msgs[0]["role"] == "system" and msgs[1]["role"] == "user" and msgs[1]["content"].startswith(OLD), msgs[1]["content"][:80]
print("messages reconstructed:", len(msgs), "roles:", "".join(m["role"][0] for m in msgs), flush=True)
TOOL = [{"type": "function", "function": {"name": "python", "description": "Run one ephemeral Python snippet against preloaded ASCII game state.",
         "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}}]
def variant(kind):
    out = json.loads(json.dumps(msgs))
    u = out[1]["content"]
    body = u[len(OLD):].lstrip("\n")
    mem, rest = body.split("The code executed", 1); rest = "The code executed" + rest
    if kind == "old": out[1]["content"] = OLD + "\n" + mem + rest
    elif kind == "new": out[1]["content"] = NEW + "\n" + mem + rest
    else: out[1]["content"] = rest
    return out
def call(ms):
    req = {"model": "qwen3-8b-16k", "messages": ms, "tools": TOOL, "max_tokens": 1500, "temperature": 0.6,
           "chat_template_kwargs": {"enable_thinking": True}}
    r = urllib.request.Request("http://localhost:11434/v1/chat/completions", data=json.dumps(req).encode(),
                               headers={"Content-Type": "application/json", "Authorization": "Bearer ollama"})
    t0 = time.time()
    with urllib.request.urlopen(r, timeout=600) as resp: d = json.load(resp)
    ch = d["choices"][0]["message"]
    return (ch.get("reasoning") or ch.get("reasoning_content") or ""), (ch.get("content") or ""), (ch.get("tool_calls") or []), time.time() - t0, d.get("usage", {})
PAT_TITLE = re.compile(r"\btitle\b|memory game|\bMEMENTO\b", re.I)
PAT_OWN = re.compile(r"my (own )?notes|earlier turns|previous turns|my previous|carried forward|from (my )?earlier", re.I)
rows = []
for kind in ("old", "new", "none"):
    ms = variant(kind)
    for i in range(N):
        rs, ct, tc, dt, us = call(ms)
        txt = rs + "\n" + ct
        row = {"variant": kind, "i": i, "title_reads": len(PAT_TITLE.findall(txt)), "own_notes_reads": len(PAT_OWN.findall(txt)),
               "tool_calls": len(tc), "action_in_call": int(any("action(" in json.dumps(c) for c in tc)),
               "reasoning_chars": len(rs), "content_chars": len(ct), "secs": round(dt, 1), "prompt_tok": us.get("prompt_tokens"), "completion_tok": us.get("completion_tokens")}
        rows.append(row); print(json.dumps(row), flush=True)
        snip = [s for s in re.split(r"(?<=[.!?])\s", txt) if PAT_TITLE.search(s) or PAT_OWN.search(s)][:3]
        for s in snip: print("   >", s.strip()[:200], flush=True)
json.dump(rows, open(S + "/b65header/replay_ab.json", "w"), indent=1)
print("DONE", flush=True)
