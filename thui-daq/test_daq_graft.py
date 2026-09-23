"""0-GPU threaded checks for the DAQ cell-9 graft; use --mutants for test teeth.

usage: python test_daq_graft.py [bundle-dir] [--mutants]
The default bundle is this checkout's localrig/ARC3-Inference.  Queue tests force cap=1
by setting floor=1, headroom=0 and faking running=-1 (and cap=3 with running=3).
"""
import copy
import importlib
import sys
import threading
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = Path(next((a for a in sys.argv[1:] if not a.startswith("-")), HERE.parent / "localrig"))
sys.path.insert(0, str(BUNDLE / "ARC3-Inference"))
GRAFT = (HERE / "graft_src.py").read_text(encoding="utf-8")
import os as _os
# Never probe a real local port from the test: the install-time /metrics check goes to a closed port unless a test
# points it at its own server.
_os.environ["LOCAL_ANALYZER_BASE_URL"] = "http://127.0.0.1:9/v1"
try:
    import PIL.Image  # noqa: F401
except ImportError:
    pil = types.ModuleType("PIL"); pil.Image = types.ModuleType("PIL.Image")
    sys.modules["PIL"], sys.modules["PIL.Image"] = pil, pil.Image


def message(level, parts=False):
    text = f"Current state: step 7, level {level}"
    return [{"role": "user", "content": [{"type": "text", "text": text}]}] if parts else [{"role": "user", "content": text}]


def wait_until(pred, timeout=3.0):
    end = time.monotonic() + timeout
    while not pred() and time.monotonic() < end:
        time.sleep(.005)
    return pred()


class _Metrics:
    """A real local HTTP server serving a vLLM-shaped /metrics body (the line format copied from a B81 run)."""
    def __init__(self, running=7, delay=0.0, body=None):
        import http.server
        outer = self
        self.hits, self.delay = 0, delay
        self.body = body if body is not None else (
            '# HELP vllm:num_requests_running Number of requests in model execution batches.\n'
            '# TYPE vllm:num_requests_running gauge\n'
            f'vllm:num_requests_running{{engine="0",model_name="Qwen/Qwen3.8-Flash-Next-NVFP4"}} {float(running)}\n'
            'vllm:num_requests_waiting{engine="0",model_name="Qwen/Qwen3.8-Flash-Next-NVFP4"} 15.0\n')
        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                outer.hits += 1
                time.sleep(outer.delay)
                data = outer.body.encode() if self.path == "/metrics" else b""
                self.send_response(200 if self.path == "/metrics" else 404)
                self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
            def log_message(self, *a): pass
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/v1"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
    def close(self):
        self.server.shutdown()


def setup(graft_text, running=-1, floor=1, headroom=0):
    for name in list(sys.modules):
        if name.startswith("inference"):
            del sys.modules[name]
    ta = importlib.import_module("inference.agent.tool_agent")
    g = {"_tool_agent": ta, "__name__": "cell9"}
    exec(graft_text, g)
    g["_DAQ_CAP_FLOOR"], g["_DAQ_HEADROOM"] = floor, headroom
    g["__daq_real_running"] = g["_daq_running"]          # kept so the real reader can be tested against a real server
    g["_daq_running"] = lambda base_url: running
    agent = object.__new__(ta.ToolAgent)
    agent._model = types.SimpleNamespace(base_url="http://fake/v1")
    agent._yield_seconds = 180.0
    return ta, g, agent


def run_checks(graft_text, verbose=True):
    ok, results = True, []
    def check(name, condition):
        nonlocal ok
        results.append((name, bool(condition))); ok &= bool(condition)

    ta, g, agent = setup(graft_text)
    check("level parse supports str, parts, summary fallback, and default", [
        g["_thui_daq_level"](agent, message(2)), g["_thui_daq_level"](agent, message(3, True))] == [2, 3])
    agent._last_step_summary = {"level": "4"}
    check("level parse fallback and minimum", g["_thui_daq_level"](agent, [{"role": "user", "content": "missing"}]) == 4)
    agent._last_step_summary = None
    check("level parse defaults to one", g["_thui_daq_level"](agent, [{"role": "user", "content": "missing"}]) == 1)

    entered, release, order = threading.Event(), threading.Event(), []
    def held(self, messages, *, tools, request_timeout_seconds=None):
        level = g["_thui_daq_level"](self, messages); order.append(level)
        if level == 9: entered.set(); release.wait(2)
    g["_thui_daq_orig_cc"] = held
    h = threading.Thread(target=lambda: agent._chat_completion(message(9), tools=None)); h.start(); entered.wait(1)
    workers = [threading.Thread(target=lambda level=level: agent._chat_completion(message(level), tools=None)) for level in (1, 3, 2)]
    for worker in workers:
        # Enqueue order is made explicit (each waiter registered before the next starts), not left to sleep timing.
        n = len(g["_THUI_DAQ"]["waiters"]); worker.start(); wait_until(lambda: len(g["_THUI_DAQ"]["waiters"]) > n)
    release.set()
    for worker in workers: worker.join(2)
    h.join(2)
    check("deeper levels are admitted first at cap one", order == [9, 3, 2, 1])

    ta, g, agent = setup(graft_text); g["_DAQ_AGE_S"], g["_DAQ_POLL_S"] = .3, .03
    hold, go, l1_at = threading.Event(), threading.Event(), []
    def agefake(self, messages, *, tools, request_timeout_seconds=None):
        lv = g["_thui_daq_level"](self, messages)
        if lv == 9: hold.set(); go.wait(2)
        if lv == 3: time.sleep(.015)
        if lv == 1: l1_at.append(time.monotonic())
    g["_thui_daq_orig_cc"] = agefake
    holder = threading.Thread(target=lambda: agent._chat_completion(message(9), tools=None)); holder.start(); hold.wait(1)
    started = time.monotonic(); low = threading.Thread(target=lambda: agent._chat_completion(message(1), tools=None)); low.start()
    time.sleep(.03)
    # Pre-queue enough L3 work before releasing L9: L1 is still young at release,
    # then becomes aged while the L3 backlog remains.  This makes the starvation test deterministic.
    highs = [threading.Thread(target=lambda: agent._chat_completion(message(3), tools=None)) for _ in range(50)]
    [t.start() for t in highs]; time.sleep(.06); go.set()
    low.join(1.2); holder.join(1); [t.join(1) for t in highs]
    check("aged low-level waiter wins within age plus poll", bool(l1_at) and l1_at[0] - started <= .45)

    ta, g, agent = setup(graft_text)
    def boom(self, messages, *, tools, request_timeout_seconds=None): raise RuntimeError("boom")
    g["_thui_daq_orig_cc"] = boom
    try: agent._chat_completion(message(1), tools=None)
    except RuntimeError: pass
    g["_thui_daq_orig_cc"] = lambda *a, **k: "ok"
    next_result = []
    next_call = threading.Thread(target=lambda: next_result.append(agent._chat_completion(message(1), tools=None)), daemon=True)
    next_call.start(); next_call.join(.3)
    check("exception releases permit for immediate next caller", not next_call.is_alive() and next_result == ["ok"] and g["_THUI_DAQ"]["active"] == 0)

    ta, g, agent = setup(graft_text, running=3, floor=1, headroom=0)
    inside, peak, lock = 0, [0], threading.Lock()
    def bounded(self, messages, *, tools, request_timeout_seconds=None):
        nonlocal inside
        with lock: inside += 1; peak[0] = max(peak[0], inside)
        time.sleep(.06)
        with lock: inside -= 1
    g["_thui_daq_orig_cc"] = bounded
    ts = [threading.Thread(target=lambda: agent._chat_completion(message(2), tools=None)) for _ in range(12)]
    [t.start() for t in ts]; [t.join(2) for t in ts]
    check("cap limits concurrent original calls", peak[0] <= 3 and all(not t.is_alive() for t in ts))

    ta, g, agent = setup(graft_text, running=None)
    g["_thui_daq_orig_cc"] = lambda *a, **k: "open"
    check("metrics failure fails open and counts it", agent._chat_completion(message(1), tools=None) == "open" and g["_THUI_DAQ"]["metrics_fail"] == 1)

    ta, g, agent = setup(graft_text); g["_THUI_DAQ_ENFORCE"] = False
    held, freed, second = threading.Event(), threading.Event(), threading.Event()
    def controlfake(self, messages, *, tools, request_timeout_seconds=None):
        if g["_thui_daq_level"](self, messages) == 9: held.set(); freed.wait(1)
        else: second.set()
    g["_thui_daq_orig_cc"] = controlfake
    first = threading.Thread(target=lambda: agent._chat_completion(message(9), tools=None)); first.start(); held.wait(1)
    nxt = threading.Thread(target=lambda: agent._chat_completion(message(1), tools=None)); nxt.start(); second.wait(.2); freed.set(); first.join(1); nxt.join(1)
    check("control arm admits despite held cap", second.is_set())

    ta, g, agent = setup(graft_text); held, freed, seen = threading.Event(), threading.Event(), []
    def timeoutfake(self, messages, *, tools, request_timeout_seconds=None):
        if g["_thui_daq_level"](self, messages) == 9: held.set(); freed.wait(1)
        else: seen.append(request_timeout_seconds)
    g["_thui_daq_orig_cc"] = timeoutfake
    first = threading.Thread(target=lambda: agent._chat_completion(message(9), tools=None)); first.start(); held.wait(1)
    waiter = threading.Thread(target=lambda: agent._chat_completion(message(1), tools=None, request_timeout_seconds=2.0)); waiter.start(); time.sleep(.25); freed.set(); first.join(1); waiter.join(1)
    check("timeout is clamped by gate wait", bool(seen) and 1.65 <= seen[0] <= 1.85)

    ta, g, agent = setup(graft_text); held, freed, observed = threading.Event(), threading.Event(), []
    def yfake(self, messages, *, tools, request_timeout_seconds=None):
        if g["_thui_daq_level"](self, messages) == 9: held.set(); freed.wait(1)
        else: observed.append(self._yield_seconds)
    g["_thui_daq_orig_cc"] = yfake
    first = threading.Thread(target=lambda: agent._chat_completion(message(9), tools=None)); first.start(); held.wait(1)
    def body(self): self._chat_completion(message(1), tools=None); raise ValueError("end")
    g["_thui_daq_orig_analyze"] = body; agent._yield_seconds = 2.0
    turn = threading.Thread(target=lambda: _ignore(lambda: agent.analyze())); turn.start(); time.sleep(.2); freed.set(); first.join(1); turn.join(1)
    check("yield budget includes wait during turn and restores after raise", bool(observed) and observed[0] >= 2.15 and agent._yield_seconds == 2.0)

    ta, g, agent = setup(graft_text); captured = []
    g["_thui_daq_orig_cc"] = lambda self, messages, *, tools, request_timeout_seconds=None: captured.append(messages)
    msgs = [{"role": "user", "content": [{"type": "text", "text": "Current state: step 1, level 2"}]}]
    snap = copy.deepcopy(msgs); agent._chat_completion(msgs, tools=[])
    check("messages list and dictionaries remain untouched", msgs == snap and captured[0] is msgs)

    ta, g, agent = setup(graft_text); calls = [0]
    def flaky(base_url):
        calls[0] += 1
        if calls[0] == 1: raise RuntimeError("metrics boom")
        return -1
    g["_daq_running"] = flaky; g["_thui_daq_orig_cc"] = lambda *a, **k: "ok"
    try: agent._chat_completion(message(1), tools=None)
    except RuntimeError: pass
    after = []
    t = threading.Thread(target=lambda: after.append(agent._chat_completion(message(1), tools=None)), daemon=True)
    t.start(); t.join(.5)
    check("a waiter that raises while queued is removed and does not block the next caller",
          g["_THUI_DAQ"]["waiters"] == [] and after == ["ok"])

    ta, g, agent = setup(graft_text); g["_DAQ_POLL_S"] = .05
    def slow_metrics(base_url):
        time.sleep(.4); return -1
    g["_daq_running"] = slow_metrics
    a_in, a_go, a_done = threading.Event(), threading.Event(), []
    def slowfake(self, messages, *, tools, request_timeout_seconds=None):
        if g["_thui_daq_level"](self, messages) == 9: a_in.set(); a_go.wait(3)
    g["_thui_daq_orig_cc"] = slowfake
    a = threading.Thread(target=lambda: (agent._chat_completion(message(9), tools=None), a_done.append(time.monotonic())))
    a.start(); a_in.wait(3)
    b = threading.Thread(target=lambda: agent._chat_completion(message(1), tools=None), daemon=True); b.start()
    time.sleep(.2); t0 = time.monotonic(); a_go.set(); a.join(3)
    check("release is not blocked by another thread's slow metrics read", bool(a_done) and a_done[0] - t0 < .15)
    b.join(3)

    ta, g, agent = setup(graft_text); g["_thui_daq_orig_cc"] = lambda *a, **k: "ok"
    def bad_record(*a, **k): raise OSError("stdout pipe gone")
    g["_thui_daq_record"] = bad_record
    try: agent._chat_completion(message(1), tools=None)
    except OSError: pass
    check("a failure after admission but before the request (record/print) still releases the permit",
          g["_THUI_DAQ"]["active"] == 0)

    ta, g, agent = setup(graft_text, running=5, floor=1, headroom=2)
    check("cap = max(floor, running + headroom) with the shipped non-zero headroom", g["_thui_daq_cap"](agent) == 7)
    ta, g, agent = setup(graft_text, running=3, floor=10, headroom=2)
    check("cap never falls below the floor", g["_thui_daq_cap"](agent) == 10)

    ta, g, agent = setup(graft_text); sentinel = object()
    g["_thui_daq_orig_analyze"] = lambda self, *a, **k: sentinel
    check("analyze returns the wrapped result unchanged and restores the yield budget",
          agent.analyze() is sentinel and agent._yield_seconds == 180.0)

    # the REAL metrics reader against a real local HTTP server
    ta, g, _ = setup(graft_text); srv = _Metrics(running=7)
    try:
        v1 = g["__daq_real_running"](srv.url); v2 = g["__daq_real_running"](srv.url)
        check("real /metrics read strips /v1, parses the labelled gauge and caches within the TTL",
              v1 == 7.0 and v2 == 7.0 and srv.hits == 1)
    finally:
        srv.close()
    ta, g, _ = setup(graft_text); srv = _Metrics(body="vllm:num_requests_waiting 3.0\n")
    try:
        check("a /metrics body without the running gauge reads as unavailable (fail-open), not as 0",
              g["__daq_real_running"](srv.url) is None)
    finally:
        srv.close()
    ta, g, _ = setup(graft_text); g["_DAQ_METRICS_TTL_S"] = .05; srv = _Metrics(running=4, delay=.5)
    try:
        g["__daq_real_running"](srv.url)          # prime the cache (0.5 s)
        time.sleep(.08)                            # let it expire
        lat = []
        def reader():
            t = time.monotonic(); g["__daq_real_running"](srv.url); lat.append(time.monotonic() - t)
        ts = [threading.Thread(target=reader) for _ in range(8)]
        [t.start() for t in ts]; [t.join(3) for t in ts]
        fast = sorted(lat)[:-1]                    # one thread does the slow refresh; the rest must not wait for it
        check("expired cache: one thread refreshes, the others use the stale value without waiting (single-flight)",
              len(lat) == 8 and max(fast) < .2 and srv.hits == 2)
    finally:
        srv.close()

    import contextlib, io, os, re as _re
    srv = _Metrics(running=2); os.environ["LOCAL_ANALYZER_BASE_URL"] = srv.url; buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            setup(graft_text)
    finally:
        srv.close(); os.environ["LOCAL_ANALYZER_BASE_URL"] = "http://127.0.0.1:9/v1"
    check("install prints THUI_DAQ_METRICS ok with the live running value when /metrics is reachable",
          _re.search(r"THUI_DAQ_METRICS ok root=http://127\.0\.0\.1:\d+ running=2\b", buf.getvalue()) is not None)

    ta, g, agent = setup(graft_text); g["_thui_daq_orig_cc"] = lambda *a, **k: None
    g["_THUI_DAQ"]["admits"] = 199; buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        agent._chat_completion(message(3), tools=None)
    out = buf.getvalue()
    check("STATS line at every 200th admission, WAIT line absent for a sub-second wait",
          _re.search(r"THUI_DAQ_STATS admits=200 waited_ge1s=0 aged=0 metrics_fail=0 max_active=1 by_level=3:1/0\.0", out)
          is not None and "THUI_DAQ_WAIT" not in out)
    if verbose:
        for name, value in results: print(f"{'ok  ' if value else 'FAIL'} {name}")
    return ok, results


def _ignore(fn):
    try: fn()
    except ValueError: pass


MUTANTS = [
    ("priority sign flipped", "return (1, -waiter[\"level\"], waiter[\"seq\"])", "return (1, waiter[\"level\"], waiter[\"seq\"] )"),
    ("release not finally", "    finally:\n        _thui_daq_release()", "    except Exception:\n        raise"),
    ("aging off", "if now - waiter[\"enqueued_at\"] >= _DAQ_AGE_S:", "if False:"),
    ("dead waiter left in queue", "if waiter is not None and waiter in _THUI_DAQ[\"waiters\"]:\n                _THUI_DAQ[\"waiters\"].remove(waiter)", "if False:\n                pass"),
    ("record outside the finally", "    try:\n        _thui_daq_record(level, waited, active, cap, aged)\n", "    _thui_daq_record(level, waited, active, cap, aged)\n    try:\n"),
    ("metrics stampede (no single-flight)", "        if not _THUI_DAQ_FETCH_LOCK.acquire(blocking=False):\n            return cached[1]", "        _THUI_DAQ_FETCH_LOCK.acquire()"),
    ("missing gauge read as 0", "    if not found:\n        raise ValueError(\"vllm:num_requests_running not in /metrics\")\n", ""),
    ("headroom ignored", "int(running) + _DAQ_HEADROOM", "int(running)"),
    ("analyze result dropped", "        return _thui_daq_orig_analyze(self, *args, **kwargs)", "        _thui_daq_orig_analyze(self, *args, **kwargs)"),
    ("metrics read under the lock", "    running = _daq_running(self._model.base_url)", "    with _THUI_DAQ_COND:\n        running = _daq_running(self._model.base_url)"),
    ("timeout not clamped", "max(0.1, request_timeout_seconds - waited)", "request_timeout_seconds"),
    ("yield not restored", "        self._yield_seconds = base\n        self.__dict__.pop", "        self.__dict__.pop"),
    ("cap-is-None guard removed (unreadable metrics must admit, not crash)","not _THUI_DAQ_ENFORCE or cap is None or", "not _THUI_DAQ_ENFORCE or False or"),
]

if "--mutants" in sys.argv:
    all_ok, _ = run_checks(GRAFT, verbose=False); print(f"{'ok  ' if all_ok else 'FAIL'} CONTROL unmutated graft green")
    for name, old, new in MUTANTS:
        # A mutant that does not apply is a broken test (it silently re-runs the unmutated graft).
        assert GRAFT.count(old) == 1, f"mutant {name!r} does not apply exactly once -- fix the mutant, not the graft"
        try:
            mok, result = run_checks(GRAFT.replace(old, new, 1), verbose=False)
        except Exception as exc:
            mok, result = False, [(type(exc).__name__, False)]
        red = [n for n, value in result if not value]
        print(f"{'ok  ' if not mok else 'FAIL'} mutant red: {name} [{len(red)} red]"); all_ok &= not mok
    print("ALL OK" if all_ok else "FAILED", flush=True)
    # A red mutant (e.g. a leaked permit) leaves worker threads blocked forever; they are the evidence, not a bug in
    # the harness, but sys.exit would wait on them. Exit hard once the verdict is printed.
    import os; os._exit(0 if all_ok else 1)
ok, result = run_checks(GRAFT)
print(f"{sum(value for _, value in result)}/{len(result)} checks")
print("ALL OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
