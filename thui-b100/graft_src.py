
# ---- thui-b100 (MAP B100 OutcomeSieve, keep rule revised 2026-09-22): send a COPY of the message list in which the stored
# `reasoning` key is removed ONLY from assistant messages of levels the agent has already LEFT, except the message that
# produced a level clear. Every assistant message of the CURRENT level keeps its reasoning. Content, tool calls, tool
# results and the harness's own list are untouched. Level of a message = the last "Current state: step S, level L" line
# in a preceding user message; the clearing message = the last assistant message before a marker with a higher level.
# Setting the STRIP flag below to False builds the logging-only control.
import re as _thui_b100_re
import threading as _thui_b100_threading

_THUI_B100_STRIP = True
_THUI_B100_MARK = _thui_b100_re.compile(r"Current state: step \d+, level (\d+)")
_THUI_B100_LOCK = _thui_b100_threading.Lock()
_THUI_B100 = {"requests": 0, "post_clear_requests": 0, "post_clear_prompt_tokens": 0, "all_prompt_tokens": 0,
              "stripped_msgs": 0, "stripped_chars": 0, "kept_clear_msgs": 0, "sent_reasoning_chars": 0,
              "post_clear_stripped_chars": 0, "post_clear_sent_reasoning_chars": 0}


def _thui_b100_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(p.get("text", "")) for p in content if isinstance(p, dict) and p.get("type") == "text")
    return ""


def _thui_b100_plan(messages):
    """Return (sent_messages, stats). Pure: never mutates `messages` or its dicts."""
    levels, level = [], None
    for m in messages:
        if isinstance(m, dict) and m.get("role") == "user":
            found = _THUI_B100_MARK.findall(_thui_b100_text(m.get("content")))
            if found:
                level = int(found[-1])
        levels.append(level)
    current = level
    clearing = set()
    last_assistant, seg_level = None, None
    for i, m in enumerate(messages):
        lv = levels[i]
        if isinstance(m, dict) and m.get("role") == "user" and lv is not None and seg_level is not None and lv > seg_level:
            if last_assistant is not None:
                clearing.add(last_assistant)
            last_assistant = None
        if isinstance(m, dict) and m.get("role") == "user" and lv is not None:
            seg_level = lv
        if isinstance(m, dict) and m.get("role") == "assistant":
            last_assistant = i
    sent, st = [], {"stripped_msgs": 0, "stripped_chars": 0, "kept_clear_msgs": 0, "sent_reasoning_chars": 0}
    for i, m in enumerate(messages):
        if isinstance(m, dict) and m.get("role") == "assistant" and m.get("reasoning"):
            r = len(str(m.get("reasoning")))
            left = current is not None and levels[i] is not None and levels[i] != current
            if left and i in clearing:
                st["kept_clear_msgs"] += 1
            if left and i not in clearing and _THUI_B100_STRIP:
                m = {k: v for k, v in m.items() if k != "reasoning"}
                st["stripped_msgs"] += 1
                st["stripped_chars"] += r
            elif left and i not in clearing:
                st["stripped_msgs"] += 1          # control: counted as eligible, still sent
                st["stripped_chars"] += r
                st["sent_reasoning_chars"] += r
            else:
                st["sent_reasoning_chars"] += r
        sent.append(m)
    st["post_clear"] = bool(current is not None and current >= 2)
    return sent, st


_thui_b100_orig_cc = _tool_agent.ToolAgent._chat_completion


def _thui_b100_chat_completion(self, messages, **kwargs):
    sent, st = _thui_b100_plan(messages)
    result = _thui_b100_orig_cc(self, sent, **kwargs)
    usage = getattr(result, "usage", None) or {}
    pt = int(usage.get("prompt_tokens") or 0) if isinstance(usage, dict) else 0
    with _THUI_B100_LOCK:
        _THUI_B100["requests"] += 1
        _THUI_B100["all_prompt_tokens"] += pt
        for k in ("stripped_msgs", "stripped_chars", "kept_clear_msgs", "sent_reasoning_chars"):
            _THUI_B100[k] += st[k]
        if st["post_clear"]:
            _THUI_B100["post_clear_requests"] += 1
            _THUI_B100["post_clear_prompt_tokens"] += pt
            _THUI_B100["post_clear_stripped_chars"] += st["stripped_chars"]
            _THUI_B100["post_clear_sent_reasoning_chars"] += st["sent_reasoning_chars"]
        snap = dict(_THUI_B100)
    if snap["requests"] == 1 or snap["requests"] % 50 == 0:
        print("THUI_B100_STATS strip=" + str(_THUI_B100_STRIP) + " "
              + " ".join(f"{k}={v}" for k, v in snap.items()), flush=True)
    return result


_tool_agent.ToolAgent._chat_completion = _thui_b100_chat_completion
assert _tool_agent.ToolAgent._chat_completion is _thui_b100_chat_completion
print(f"THUI_B100_GRAFT ok strip={_THUI_B100_STRIP} rule=current-level+clearing", flush=True)
