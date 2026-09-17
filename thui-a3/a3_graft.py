# ---- thui-a3 (A3): an executable world model the agent writes, keeps, and checks against what happened ----
# The python tool is ephemeral (one sandbox subprocess per call), so nothing the model writes survives a call. This graft
# (1) stores the string assigned to a top-level `WORLD_MODEL = '''...'''` in any python call, per game session;
# (2) prepends that source, plus parse_action() and verify_world_model(), to every later python call, so predict()
#     and the agent's other functions are simply defined; the prefix costs no prompt tokens;
# (3) verify_world_model() replays recorded same-level transitions through predict(rows, action) and reports misses;
# (4) appends a short block to every user prompt: the instruction and the current model / verify status.
# Unchanged: the harness, the solver, the serving profile; no action is issued or refused by this code.
import ast as _a3_ast
import re as _a3_re
import textwrap as _a3_textwrap
import threading as _a3_threading

import inference.agent.tool_agent as _a3_ta

_A3_TL = _a3_threading.local()
_A3_MAX_SRC_CHARS = 16000
_A3_STATS = {"python_calls": 0, "calls_with_model": 0, "saves": 0, "rejects": 0, "verifies": 0, "load_errors": 0, "prompts": 0}

_A3_HELPERS = r'''
def parse_action(action):
    import re as _re
    text = str(action)
    name = _re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", text)
    row = _re.search(r"row\s*=\s*(-?\d+)", text)
    col = _re.search(r"col\s*=\s*(-?\d+)", text)
    return (name.group(1) if name else text, int(row.group(1)) if row else None, int(col.group(1)) if col else None)


def verify_world_model(show=3, last=60):
    try:
        _predict = predict
    except Exception:
        print("A3_VERIFY no predict(rows, action) is defined -- save WORLD_MODEL first")
        return None
    pairs = [t for t in transitions if t.before_frame is not None and t.after_frame is not None
             and t.before_frame.level == t.after_frame.level]
    pairs = pairs[-last:]
    exact = 0
    raised = 0
    bad = []
    for t in pairs:
        before = str(t.before_frame.ascii).split("\n")
        after = str(t.after_frame.ascii).split("\n")
        try:
            pred = [str(r) for r in _predict(list(before), t.action)]
        except Exception as exc:
            raised += 1
            if len(bad) < show:
                bad.append((t.action, "raised " + type(exc).__name__ + ": " + str(exc)[:100]))
            continue
        if pred == after:
            exact += 1
            continue
        wrong = []
        for r in range(max(len(after), len(pred))):
            a_row = after[r] if r < len(after) else ""
            p_row = pred[r] if r < len(pred) else ""
            for c in range(max(len(a_row), len(p_row))):
                a = a_row[c] if c < len(a_row) else "?"
                p = p_row[c] if c < len(p_row) else "?"
                if a != p:
                    wrong.append((r, c, p, a))
        if len(bad) < show:
            bad.append((t.action, str(len(wrong)) + " cells wrong; first (row, col, predicted, actual): " + str(wrong[:4])))
    print("A3_VERIFY exact=" + str(exact) + "/" + str(len(pairs)) + " raised=" + str(raised))
    for item in bad:
        print("  miss:", item[0], "->", item[1])
    return {"exact": exact, "total": len(pairs), "raised": raised}
'''


def _a3_state(agent):
    run_dir = getattr(agent, "_session_runtime_dir", None)
    st = getattr(agent, "_a3_state", None)
    if not isinstance(st, dict) or st.get("dir") != run_dir:
        st = {"dir": run_dir, "src": "", "saves": 0, "last_reject": "", "verify": "", "load_error": ""}
        agent._a3_state = st
    return st


def _a3_extract(code):
    try:
        tree = _a3_ast.parse(code)
    except SyntaxError:
        return None
    for node in tree.body:
        if (isinstance(node, _a3_ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], _a3_ast.Name)
                and node.targets[0].id == "WORLD_MODEL" and isinstance(node.value, _a3_ast.Constant)
                and isinstance(node.value.value, str)):
            return node.value.value
    return None


def _a3_prefix(src):
    parts = [_A3_HELPERS]
    if src:
        parts.append("try:\n" + _a3_textwrap.indent(src, "    ") + "\n    pass\n"
                     "except Exception as _a3_exc:\n"
                     "    print('A3_MODEL_LOAD_ERROR ' + type(_a3_exc).__name__ + ': ' + str(_a3_exc)[:160])\n")
    return "\n".join(parts) + "\n"


_a3_orig_run_python_tool = _a3_ta.ToolAgent._run_python_tool
_a3_orig_sandbox = _a3_ta.run_sandboxed_python
_a3_orig_build_user_prompt = _a3_ta.ToolAgent._build_user_prompt


def _a3_run_python_tool(self, state_path, arguments):
    try:
        self._ensure_session(state_path)
        st = _a3_state(self)
        new_src = _a3_extract(str((arguments or {}).get("code", "")))
        if new_src is not None:
            if len(new_src) > _A3_MAX_SRC_CHARS:
                st["last_reject"] = "too long (" + str(len(new_src)) + " chars > " + str(_A3_MAX_SRC_CHARS) + ")"
                _A3_STATS["rejects"] += 1
            else:
                try:
                    compile(new_src, "<world_model>", "exec")
                    st["src"], st["last_reject"], st["verify"], st["load_error"] = new_src, "", "", ""
                    st["saves"] += 1
                    _A3_STATS["saves"] += 1
                except SyntaxError as exc:
                    st["last_reject"] = "SyntaxError line " + str(exc.lineno) + ": " + str(exc.msg)
                    _A3_STATS["rejects"] += 1
    except Exception as exc:   # the graft must never cost the turn
        print(f"thui-a3: store error (pass-through): {type(exc).__name__}: {exc}", flush=True)
    _A3_TL.agent = self
    try:
        return _a3_orig_run_python_tool(self, state_path, arguments)
    finally:
        _A3_TL.agent = None


def _a3_sandbox(*, code, **kwargs):
    agent = getattr(_A3_TL, "agent", None)
    if agent is None:
        return _a3_orig_sandbox(code=code, **kwargs)
    st = _a3_state(agent)
    prefix = _a3_prefix(st["src"])
    offset = prefix.count("\n")
    _A3_STATS["python_calls"] += 1
    _A3_STATS["calls_with_model"] += 1 if st["src"] else 0
    result = _a3_orig_sandbox(code=prefix + code, **kwargs)
    try:
        err = result.get("error")
        if isinstance(err, str) and err:
            def _fix(m):
                n = int(m.group(1)) - offset
                return 'File "<python_tool>", line ' + (str(n) if n > 0 else "(saved WORLD_MODEL / helpers)")
            result["error"] = _a3_re.sub(r'File "<python_tool>", line (\d+)', _fix, err)
        out = str(result.get("stdout") or "")
        hits = _a3_re.findall(r"A3_VERIFY exact=(\d+)/(\d+) raised=(\d+)", out)
        if hits:
            e, t, r = hits[-1]
            st["verify"] = e + "/" + t + " exact" + (", " + r + " raised" if r != "0" else "")
            _A3_STATS["verifies"] += 1
        load = _a3_re.findall(r"A3_MODEL_LOAD_ERROR ([^\n]*)", out)
        if load:
            st["load_error"] = load[-1][:160]
            _A3_STATS["load_errors"] += 1
        if _A3_STATS["python_calls"] % 200 == 0:
            print(f"thui-a3: STATS {_A3_STATS}", flush=True)
    except Exception as exc:
        print(f"thui-a3: post error (pass-through): {type(exc).__name__}: {exc}", flush=True)
    return result


_A3_PROMPT = (
    "\n\n[EXECUTABLE WORLD MODEL]\n"
    "Keep your best hypothesis of this game's rules as runnable code. In any python call, assign "
    "WORLD_MODEL = '''<python source>''' as a plain string literal at top level. The source must define "
    "predict(rows, action) -> rows, where rows is a frame as a list of ASCII strings (frame.ascii.split('\\n')) and "
    "action is a transition's action string (parse_action(action) returns name, row, col). Once saved, the source runs "
    "at the top of every later python call, so predict and anything else it defines is already there. "
    "verify_world_model() replays the recorded transitions through predict and prints the ones it gets wrong. "
    "When it misses, fix the model before trusting a multi-step plan; when it matches, simulate candidate action "
    "sequences with predict before spending real actions.\n"
)


def _a3_build_user_prompt(self, *args, **kwargs):
    text = _a3_orig_build_user_prompt(self, *args, **kwargs)
    try:
        st = _a3_state(self)
        if st["src"]:
            status = "saved (" + str(st["src"].count("\n") + 1) + " lines, save #" + str(st["saves"]) + ")"
            status += "; last verify: " + (st["verify"] or "not run since this save")
            if st["load_error"]:
                status += "; LOAD ERROR: " + st["load_error"]
        else:
            status = "none saved yet"
        if st["last_reject"]:
            status += "; last WORLD_MODEL rejected: " + st["last_reject"]
        _A3_STATS["prompts"] += 1
        return text + _A3_PROMPT + "World model status: " + status + "\n"
    except Exception as exc:
        print(f"thui-a3: prompt error (pass-through): {type(exc).__name__}: {exc}", flush=True)
        return text
