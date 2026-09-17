# ---- thui-a3 teeth: run BEFORE install, against the REAL sandbox (in-kernel: the bundle's; locally: the same file) ----
def _a3_teeth():
    class _FakeAgent:
        _session_runtime_dir = "teeth-session"
        def _ensure_session(self, state_path):
            pass

    def _frame(rows, level=1, step=0):
        return {"ascii": "\n".join(rows), "step": step, "level": level, "shape": [len(rows), len(rows[0])],
                "grid": [[0] * len(rows[0]) for _ in rows]}

    f0 = ["ab", "cd"]
    f2 = ["ab", "cX"]
    state = {"current_frame": _frame(f2, step=2),
             "history": [{"action": "", "frame": _frame(f0)}, {"action": "UP", "frame": _frame(f0, step=1)},
                         {"action": "MOUSE(row=1, col=1)", "frame": _frame(f2, step=2)}],
             "valid_actions": ["UP"], "last_action_result": {}}

    def _run(agent, code):
        _A3_TL.agent = agent
        try:
            return _a3_sandbox(code=code, timeout_seconds=20, initial_state=state,
                               action_handler=lambda actions: {}, animation_handler=None)
        finally:
            _A3_TL.agent = None

    # 1. extraction: only a top-level plain string literal counts
    assert _a3_extract("WORLD_MODEL = '''def predict(rows, action):\n    return rows\n'''\n").startswith("def predict")
    assert _a3_extract("WORLD_MODEL = 'a' + 'b'\n") is None
    assert _a3_extract("def f():\n    WORLD_MODEL = 'x'\n") is None
    assert _a3_extract("WORLD_MODEL = f'{1}'\n") is None

    # 2. store + real sandbox + verify: identity predict gets the no-change step and misses the click
    agent = _FakeAgent()
    st = _a3_state(agent)
    st["src"] = "def predict(rows, action):\n    return rows\n"
    res = _run(agent, "out = verify_world_model()\nprint(parse_action('MOUSE(row=1, col=1)'))\n")
    out = str(res.get("stdout") or "")
    assert "A3_VERIFY exact=1/2 raised=0" in out, ("verify count", res)
    assert "(0, 1, 'd', 'X')" in out or "(1, 1, 'd', 'X')" in out, ("miss cell", out)
    assert "('MOUSE', 1, 1)" in out, ("parse_action", out)
    assert st["verify"] == "1/2 exact", st

    # 3. a wrong model that raises is counted, not fatal
    st["src"] = "def predict(rows, action):\n    raise ValueError('nope')\n"
    out = str(_run(agent, "verify_world_model()\n").get("stdout") or "")
    assert "A3_VERIFY exact=0/2 raised=2" in out, out

    # 4. user error line numbers are the user's own
    err = str(_run(agent, "x = 1\nraise ValueError('boom')\n").get("error") or "")
    assert 'File "<python_tool>", line 2' in err, err

    # 5. a model that fails at load is reported and the user's code still runs
    st["src"] = "raise RuntimeError('bad model')\n"
    res = _run(agent, "print('after-load')\n")
    out = str(res.get("stdout") or "")
    assert "A3_MODEL_LOAD_ERROR RuntimeError: bad model" in out and "after-load" in out, res
    assert st["load_error"].startswith("RuntimeError"), st

    # 6. control: with no agent bound (another thread, or the graft not entered) the code runs untouched
    res = _a3_sandbox(code="print('verify_world_model' in dir())\n", timeout_seconds=20, initial_state=state,
                      action_handler=lambda actions: {}, animation_handler=None)
    assert str(res.get("stdout") or "").strip() == "False", res

    # 7. prompt block carries the instruction and the live status
    class _PromptAgent(_FakeAgent):
        pass
    pa = _PromptAgent()
    global _a3_orig_build_user_prompt
    saved = _a3_orig_build_user_prompt
    _a3_orig_build_user_prompt = lambda self, *a, **k: "BASE"
    try:
        text = _a3_build_user_prompt(pa, 1, valid_actions=["UP"])
        assert text.startswith("BASE") and "[EXECUTABLE WORLD MODEL]" in text and "none saved yet" in text, text
        _a3_state(pa)["src"] = "def predict(rows, action):\n    return rows\n"
        _a3_state(pa)["saves"] = 1
        assert "saved (3 lines, save #1)" in _a3_build_user_prompt(pa, 2, valid_actions=["UP"])
    finally:
        _a3_orig_build_user_prompt = saved
    for k in _A3_STATS:
        _A3_STATS[k] = 0
    print("thui-a3: teeth ok (7 checks, real sandbox)", flush=True)


_a3_teeth()
