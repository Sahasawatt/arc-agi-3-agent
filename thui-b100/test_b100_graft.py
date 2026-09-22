"""0-GPU test of the thui-b100 graft against the anim bundle's REAL ToolAgent._chat_completion (only requests.post faked).

usage: python test_b100_graft.py <anim-bundle-dir> [--mutants]
Synthetic history (Watchara's teeth, keep rule revised 2026-09-22): level 1 = an old failure + the clearing message,
level 2 = the current level with 3 assistant turns. Must send: L1 failure WITHOUT reasoning, L1 clear WITH it, every L2
message WITH it; the caller's list and dicts unchanged; content / tool calls byte-identical; control sends everything.
"""
import copy, importlib, json, sys, types
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = Path(sys.argv[1])
sys.path.insert(0, str(BUNDLE / "src" / "ARC3-Inference"))
GRAFT = (HERE / "graft_src.py").read_text(encoding="utf-8")
try:
    import PIL.Image  # noqa: F401
except ImportError:
    _pil = types.ModuleType("PIL"); _pil.Image = types.ModuleType("PIL.Image")
    sys.modules["PIL"], sys.modules["PIL.Image"] = _pil, _pil.Image
    print("note: PIL stubbed (not installed here)")


def user(level, step, image=True):
    text = f"Some header.\nCurrent state: step {step}, level {level}.\nMore lines."
    return {"role": "user", "content": [{"type": "text", "text": text}, {"type": "image_url", "image_url": {"url": "x"}}]
            if image else text}


def asst(tag):
    return {"role": "assistant", "reasoning": f"R-{tag} " * 20, "content": f"C-{tag}",
            "tool_calls": [{"id": tag, "type": "function", "function": {"name": "python", "arguments": "{}"}}]}


def tool(tag):
    return {"role": "tool", "tool_call_id": tag, "content": f"out-{tag}"}


HISTORY = [{"role": "system", "content": "sys"},
           user(1, 1), asst("L1fail"), tool("L1fail"),
           {"role": "user", "content": "You have not acted yet. Investigate first."},
           asst("L1clear"), tool("L1clear"),
           user(2, 9), asst("L2a"), tool("L2a"), asst("L2b"), tool("L2b"),
           user(2, 12, image=False), asst("L2c"), tool("L2c"),
           user(2, 14)]


def run_checks(graft_text, verbose=True):
    for name in list(sys.modules):
        if name.startswith("inference"):
            del sys.modules[name]
    ta = importlib.import_module("inference.agent.tool_agent")
    sent_payloads = []

    class R:
        status_code = 200; text = ""
        def raise_for_status(self): pass
        def json(self):
            return {"choices": [{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 1000, "completion_tokens": 5}}

    def fake_post(url, headers=None, json=None, timeout=None):
        sent_payloads.append(json); return R()
    ta.requests.post = fake_post
    ok, results = True, []

    def check(name, cond):
        nonlocal ok
        results.append((name, bool(cond))); ok &= bool(cond)

    g = {"_tool_agent": ta, "__name__": "cell9"}
    try:
        exec(graft_text, g)
    except Exception as exc:
        check(f"graft executes ({type(exc).__name__}: {exc})", False)
        return ok, results
    agent = object.__new__(ta.ToolAgent)
    agent._model = types.SimpleNamespace(provider="vllm", model_id="m", base_url="http://x/v1")
    agent._timeout, agent._api_key, agent._max_output_tokens = 60.0, "k", None
    msgs = copy.deepcopy(HISTORY)
    snapshot = json.dumps(msgs)
    try:
        agent._chat_completion(msgs, tools=[{"type": "function"}])
    except Exception as exc:
        check(f"call raised {type(exc).__name__}: {exc}", False)
        return ok, results
    wire = sent_payloads[-1]["messages"] if sent_payloads else []
    by_tag = {m["tool_calls"][0]["id"]: m for m in wire if m.get("role") == "assistant"}
    check("one request sent", len(sent_payloads) == 1)
    check("L1 failure (level left, not clearing) sent WITHOUT reasoning", "reasoning" not in by_tag.get("L1fail", {"reasoning": 1}))
    check("L1 clearing message keeps reasoning", "reasoning" in by_tag.get("L1clear", {}))
    check("every current-level (L2) message keeps reasoning", all("reasoning" in by_tag.get(t, {}) for t in ("L2a", "L2b", "L2c")))
    check("caller's list and dicts unchanged", json.dumps(msgs) == snapshot)
    check("same number of messages, same order", [m.get("role") for m in wire] == [m.get("role") for m in HISTORY])
    strip_keys = lambda m: {k: v for k, v in m.items() if k != "reasoning"}
    check("content / tool calls / tool results byte-identical",
          [strip_keys(m) for m in wire] == [strip_keys(m) for m in HISTORY])
    stats = g["_THUI_B100"]
    check("stats: 1 stripped, 1 kept clear, post-clear counted, prompt tokens logged",
          stats["stripped_msgs"] == 1 and stats["kept_clear_msgs"] == 1 and stats["post_clear_requests"] == 1
          and stats["post_clear_prompt_tokens"] == 1000)
    # level 1 only (nothing left yet) -> nothing stripped
    sent_payloads.clear()
    early = copy.deepcopy(HISTORY[:4])
    agent._chat_completion(early, tools=None)
    check("on level 1 nothing is stripped", all("reasoning" in m for m in sent_payloads[-1]["messages"] if m.get("role") == "assistant"))
    # history window starting without any marker -> unknown level -> kept
    sent_payloads.clear()
    nomark = [{"role": "system", "content": "s"}, {"role": "user", "content": "no marker"}, asst("u1"), tool("u1"), user(3, 40)]
    agent._chat_completion(nomark, tools=None)
    check("unknown-level message kept", all("reasoning" in m for m in sent_payloads[-1]["messages"] if m.get("role") == "assistant"))
    # control build: same graft with STRIP False sends everything, still counts eligibility
    for name in list(sys.modules):
        if name.startswith("inference"):
            del sys.modules[name]
    ta2 = importlib.import_module("inference.agent.tool_agent")
    ta2.requests.post = fake_post
    g2 = {"_tool_agent": ta2, "__name__": "cell9"}
    exec(graft_text.replace("_THUI_B100_STRIP = True", "_THUI_B100_STRIP = False"), g2)
    agent2 = object.__new__(ta2.ToolAgent)
    agent2.__dict__.update(agent.__dict__)
    sent_payloads.clear()
    agent2._chat_completion(copy.deepcopy(HISTORY), tools=None)
    check("control sends every reasoning key", all("reasoning" in m for m in sent_payloads[-1]["messages"] if m.get("role") == "assistant"))
    check("control still counts 1 eligible message", g2["_THUI_B100"]["stripped_msgs"] == 1)
    if verbose:
        for n, v in results:
            print(f"{'ok  ' if v else 'FAIL'} {n}")
    return ok, results


MUTANTS = [
    ("strip all (B92 shape)", "            if left and i not in clearing and _THUI_B100_STRIP:", "            if _THUI_B100_STRIP:"),
    ("strip current level too", "left = current is not None and levels[i] is not None and levels[i] != current", "left = True"),
    ("in-place edit of caller dict", '                m = {k: v for k, v in m.items() if k != "reasoning"}', '                m.pop("reasoning", None)'),
    ("clearing mis-associated to first assistant of the segment", "            last_assistant = i", "            last_assistant = i if last_assistant is None else last_assistant"),
    ("clearing message not protected", "            if left and i not in clearing and _THUI_B100_STRIP:", "            if left and _THUI_B100_STRIP:"),
    ("marker regex wrong", r'r"Current state: step \d+, level (\d+)"', r'r"Current state: level (\d+)"'),
    ("wrapper never installed", "_tool_agent.ToolAgent._chat_completion = _thui_b100_chat_completion\n", ""),
]

if "--mutants" in sys.argv:
    all_ok, _ = run_checks(GRAFT, verbose=False)
    print(f"{'ok  ' if all_ok else 'FAIL'} CONTROL unmutated graft green")
    for name, old, new in MUTANTS:
        if old not in GRAFT:
            print(f"FAIL mutant '{name}': anchor not found"); all_ok = False; continue
        try:
            mok, res = run_checks(GRAFT.replace(old, new, 1), verbose=False)
        except Exception as exc:
            mok, res = False, [(f"crashed {type(exc).__name__}", False)]
        red = [n for n, v in res if not v]
        print(f"{'ok  ' if not mok else 'FAIL'} mutant red: {name}  [{len(red)} red: {red[:2]}]")
        all_ok &= not mok
    print("ALL OK" if all_ok else "FAILED")
    sys.exit(0 if all_ok else 1)
ok, res = run_checks(GRAFT)
print(f"{sum(v for _, v in res)}/{len(res)} checks")
print("ALL OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
