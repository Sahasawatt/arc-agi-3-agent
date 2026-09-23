# ---- thui-daq: process-wide depth-aging admission queue before local vLLM.
import os as _thui_daq_os
import re as _thui_daq_re
import threading as _thui_daq_threading
import time as _thui_daq_time
import urllib.request as _thui_daq_urllib

_THUI_DAQ_ENFORCE = True
_DAQ_CAP_FLOOR = 10
_DAQ_HEADROOM = 2
_DAQ_AGE_S = 60.0
_DAQ_METRICS_TTL_S = 2.0
_DAQ_POLL_S = 0.5
_THUI_DAQ_MARK = _thui_daq_re.compile(r"Current state: step \d+, level (\d+)")
_THUI_DAQ_COND = _thui_daq_threading.Condition()
_THUI_DAQ_METRICS = {}
_THUI_DAQ = {"active": 0, "seq": 0, "waiters": [], "admits": 0, "waited_ge1s": 0,
             "aged": 0, "metrics_fail": 0, "max_active": 0, "by_level": {}}


def _thui_daq_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(p.get("text", "")) for p in content
                         if isinstance(p, dict) and p.get("type") == "text")
    return ""


def _thui_daq_level(self, messages):
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            found = _THUI_DAQ_MARK.findall(_thui_daq_text(message.get("content")))
            if found:
                try:
                    return max(1, int(found[-1]))
                except (TypeError, ValueError):
                    pass
            break
    try:
        return max(1, int((getattr(self, "_last_step_summary", None) or {}).get("level")))
    except (TypeError, ValueError):
        return 1


def _thui_daq_root(base_url):
    root = base_url.rstrip("/")
    return root[:-3] if root.endswith("/v1") else root


def _daq_fetch_running(root):
    with _thui_daq_urllib.urlopen(root + "/metrics", timeout=1.0) as response:
        text = response.read().decode("utf-8", "replace")
    found = _thui_daq_re.findall(r"(?m)^vllm:num_requests_running(?:\{[^}]*\})?\s+([-+0-9.eE]+)\s*$", text)
    if not found:
        raise ValueError("vllm:num_requests_running not in /metrics")
    return sum(float(value) for value in found)


_THUI_DAQ_FETCH_LOCK = _thui_daq_threading.Lock()


def _daq_running(base_url):
    """Read the only vLLM saturation metric, sharing a short process cache.

    Single-flight: when the cache expires, one thread refreshes it and the others keep using the stale value, so a
    notify_all over 25 waiters cannot stampede the API server's /metrics endpoint.
    """
    root = _thui_daq_root(base_url)
    cached = _THUI_DAQ_METRICS.get(root)
    if cached and _thui_daq_time.monotonic() - cached[0] < _DAQ_METRICS_TTL_S:
        return cached[1]
    if cached is not None:
        if not _THUI_DAQ_FETCH_LOCK.acquire(blocking=False):
            return cached[1]
    else:
        _THUI_DAQ_FETCH_LOCK.acquire()
    try:
        cached = _THUI_DAQ_METRICS.get(root)
        if cached and _thui_daq_time.monotonic() - cached[0] < _DAQ_METRICS_TTL_S:
            return cached[1]
        try:
            running = _daq_fetch_running(root)
        except Exception:
            running = None
        _THUI_DAQ_METRICS[root] = (_thui_daq_time.monotonic(), running)
        return running
    finally:
        _THUI_DAQ_FETCH_LOCK.release()


def _thui_daq_cap(self):
    running = _daq_running(self._model.base_url)
    if running is None:
        with _THUI_DAQ_COND:
            _THUI_DAQ["metrics_fail"] += 1
        return None
    return max(_DAQ_CAP_FLOOR, int(running) + _DAQ_HEADROOM)


def _thui_daq_key(waiter, now):
    if now - waiter["enqueued_at"] >= _DAQ_AGE_S:
        return (0, waiter["seq"])
    return (1, -waiter["level"], waiter["seq"])


def _thui_daq_acquire(self, level):
    started = _thui_daq_time.monotonic()
    waiter = None
    try:
        with _THUI_DAQ_COND:
            waiter = {"seq": _THUI_DAQ["seq"], "level": level, "enqueued_at": started}
            _THUI_DAQ["seq"] += 1
            _THUI_DAQ["waiters"].append(waiter)
        while True:
            # The metrics read is an HTTP call: never make it while holding the process-wide lock.
            cap = _thui_daq_cap(self)
            with _THUI_DAQ_COND:
                now = _thui_daq_time.monotonic()
                waited = now - started
                aged = int(waited >= _DAQ_AGE_S)
                first = min(_THUI_DAQ["waiters"], key=lambda w: _thui_daq_key(w, now))
                # The control arm records the same queue facts, but deliberately never holds it.
                if not _THUI_DAQ_ENFORCE or cap is None or (_THUI_DAQ["active"] < cap and first is waiter):
                    _THUI_DAQ["waiters"].remove(waiter)
                    _THUI_DAQ["active"] += 1
                    _THUI_DAQ["max_active"] = max(_THUI_DAQ["max_active"], _THUI_DAQ["active"])
                    _THUI_DAQ_COND.notify_all()
                    return waited, _THUI_DAQ["active"], cap, aged
                _THUI_DAQ_COND.wait(timeout=_DAQ_POLL_S)
    except BaseException:
        # A waiter that dies while queued must not stay at the head of the queue and block every game.
        with _THUI_DAQ_COND:
            if waiter is not None and waiter in _THUI_DAQ["waiters"]:
                _THUI_DAQ["waiters"].remove(waiter)
            _THUI_DAQ_COND.notify_all()
        raise


def _thui_daq_release():
    with _THUI_DAQ_COND:
        _THUI_DAQ["active"] -= 1
        _THUI_DAQ_COND.notify_all()


def _thui_daq_record(level, waited, active, cap, aged):
    with _THUI_DAQ_COND:
        _THUI_DAQ["admits"] += 1
        _THUI_DAQ["waited_ge1s"] += int(waited >= 1.0)
        _THUI_DAQ["aged"] += aged
        waits = _THUI_DAQ["by_level"].setdefault(level, [])
        waits.append(waited)
        if len(waits) > 2000:
            del waits[:-2000]
        count = _THUI_DAQ["admits"]
        if count % 200 == 0:
            by_level = ",".join(f"{lv}:{len(ws)}/{sorted(ws)[len(ws)//2]:.1f}"
                                for lv, ws in sorted(_THUI_DAQ["by_level"].items()))
            print("THUI_DAQ_STATS admits={0} waited_ge1s={1} aged={2} metrics_fail={3} max_active={4} by_level={5}".format(
                count, _THUI_DAQ["waited_ge1s"], _THUI_DAQ["aged"], _THUI_DAQ["metrics_fail"],
                _THUI_DAQ["max_active"], by_level), flush=True)
    if waited >= 1.0:
        print(f"THUI_DAQ_WAIT level={level} waited={waited:.1f} active={active} cap={cap} aged={aged}", flush=True)


_thui_daq_orig_cc = _tool_agent.ToolAgent._chat_completion


def _thui_daq_chat_completion(self, messages, *, tools, request_timeout_seconds=None):
    level = _thui_daq_level(self, messages)
    waited, active, cap, aged = _thui_daq_acquire(self, level)
    # Everything after a granted permit sits inside the finally: a leaked permit is process-wide and never recovers.
    try:
        _thui_daq_record(level, waited, active, cap, aged)
        # The timeout was budgeted before queueing, so only the remaining request time is sent.
        timeout = None if request_timeout_seconds is None else max(0.1, request_timeout_seconds - waited)
        turn_base = getattr(self, "_daq_base_yield_seconds", None)
        if turn_base is not None:
            self._daq_turn_wait = getattr(self, "_daq_turn_wait", 0.0) + waited
            self._yield_seconds = turn_base + self._daq_turn_wait
        return _thui_daq_orig_cc(self, messages, tools=tools, request_timeout_seconds=timeout)
    finally:
        _thui_daq_release()


_thui_daq_orig_analyze = _tool_agent.ToolAgent.analyze


def _thui_daq_analyze(self, *args, **kwargs):
    base = self._yield_seconds
    self._daq_base_yield_seconds = base
    self._daq_turn_wait = 0.0
    try:
        return _thui_daq_orig_analyze(self, *args, **kwargs)
    finally:
        # Queue time is not useful agent thinking time; put the original budget back per turn.
        self._yield_seconds = base
        self.__dict__.pop("_daq_base_yield_seconds", None)


_thui_daq_chat_completion.__wrapped__ = _thui_daq_orig_cc
_thui_daq_analyze.__wrapped__ = _thui_daq_orig_analyze
_tool_agent.ToolAgent._chat_completion = _thui_daq_chat_completion
_tool_agent.ToolAgent.analyze = _thui_daq_analyze
assert _tool_agent.ToolAgent._chat_completion is _thui_daq_chat_completion
print(f"THUI_DAQ_GRAFT ok enforce={_THUI_DAQ_ENFORCE} cap_floor=10 headroom=2 age_s=60.0", flush=True)
# The gate fails OPEN when /metrics is unreadable, so a wrong URL would silently turn the arm into B81. Say so now, loudly;
# the registered read treats a missing "THUI_DAQ_METRICS ok" line as VOID.
_thui_daq_boot_root = _thui_daq_root(_thui_daq_os.environ.get("LOCAL_ANALYZER_BASE_URL", "http://127.0.0.1:1234/v1"))
try:
    print(f"THUI_DAQ_METRICS ok root={_thui_daq_boot_root} running={_daq_fetch_running(_thui_daq_boot_root):g}", flush=True)
except Exception as _thui_daq_exc:
    print(f"THUI_DAQ_METRICS FAIL root={_thui_daq_boot_root} error={type(_thui_daq_exc).__name__}: {_thui_daq_exc}",
          flush=True)
