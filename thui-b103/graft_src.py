
# ---- thui-b103 OneBoard (MAP B103, bar pre-registered in thui-b103/PREDICTIONS.md): every analyze() call appends a
# user message carrying the current board as a base64 PNG, and the persistent history keeps those messages, so a
# request re-sends every older board still in the window. The token estimator json-dumps the payload, so each image is
# charged len(base64)/3 and evicts text history. With the ONEBOARD flag on, every user message except the NEWEST one
# that carries an image loses its image parts (its text stays; the "Current grid image:" pointer is removed with it).
# With it off (the control) nothing is changed and the same counters are printed, so the bar is read from the log:
#   THUI_B103_STATS oneboard=<bool> trims=<n> images_seen=<n> images_dropped=<n> max_images=<n>
#     est_tokens_before=<sum> est_tokens_after=<sum>
import threading as _thui_b103_threading

_THUI_B103_ONEBOARD = True
_THUI_B103_POINTER = "\n\nCurrent grid image:"
_THUI_B103_LOCK = _thui_b103_threading.Lock()
_THUI_B103 = {"trims": 0, "images_seen": 0, "images_dropped": 0, "max_images": 0,
              "est_tokens_before": 0, "est_tokens_after": 0}
_thui_b103_orig_trim = _tool_agent.ToolAgent._trim_messages_for_context


def _thui_b103_is_image(part):
    return isinstance(part, dict) and part.get("type") == "image_url"


def _thui_b103_strip(messages):
    """Return (messages', seen, dropped). Only user messages older than the newest image-bearing one are rebuilt;
    every other dict is passed through by identity."""
    carriers = [i for i, m in enumerate(messages)
                if m.get("role") == "user" and isinstance(m.get("content"), list)
                and any(_thui_b103_is_image(p) for p in m["content"])]
    seen = sum(sum(1 for p in messages[i]["content"] if _thui_b103_is_image(p)) for i in carriers)
    if not _THUI_B103_ONEBOARD or len(carriers) <= 1:
        return messages, seen, 0
    out, dropped = list(messages), 0
    for i in carriers[:-1]:
        parts = []
        for p in messages[i]["content"]:
            if _thui_b103_is_image(p):
                dropped += 1
                continue
            if isinstance(p, dict) and p.get("type") == "text" and str(p.get("text", "")).endswith(_THUI_B103_POINTER):
                p = {**p, "text": p["text"][: -len(_THUI_B103_POINTER)]}
            parts.append(p)
        texts = [p.get("text", "") for p in parts if isinstance(p, dict) and p.get("type") == "text"]
        content = texts[0] if len(parts) == 1 and len(texts) == 1 else parts
        out[i] = {**messages[i], "content": content}
    return out, seen, dropped


def _thui_b103_trim(self, messages, *args, **kwargs):
    stripped, seen, dropped = _thui_b103_strip(list(messages or []))
    before = _tool_agent._estimate_tokens({"messages": list(messages or [])}) if messages else 0
    after = _tool_agent._estimate_tokens({"messages": stripped}) if stripped else 0
    with _THUI_B103_LOCK:
        _THUI_B103["trims"] += 1
        _THUI_B103["images_seen"] += seen
        _THUI_B103["images_dropped"] += dropped
        _THUI_B103["max_images"] = max(_THUI_B103["max_images"], seen)
        _THUI_B103["est_tokens_before"] += before
        _THUI_B103["est_tokens_after"] += after
        snap = dict(_THUI_B103)
    if snap["trims"] % 200 == 1:
        print("THUI_B103_STATS oneboard=" + str(_THUI_B103_ONEBOARD) + " "
              + " ".join(f"{k}={v}" for k, v in snap.items()), flush=True)
    return _thui_b103_orig_trim(self, stripped, *args, **kwargs)


_tool_agent.ToolAgent._trim_messages_for_context = _thui_b103_trim
assert _tool_agent.ToolAgent._trim_messages_for_context is _thui_b103_trim
print(f"THUI_B103_GRAFT ok oneboard={_THUI_B103_ONEBOARD}", flush=True)
