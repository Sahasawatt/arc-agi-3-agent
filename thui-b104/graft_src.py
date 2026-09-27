
# ---- thui-b104 ContactSheet (MAP B104, bar pre-registered in thui-b104/PREDICTIONS.md): the anim bundle keeps the raw
# frames of recent animated actions in memory (solver `animation_history`, served to the agent through
# step_env({"query": "animation"})) but the model only ever SEES them if it writes python that calls animation(), which
# returns a text diff timeline. With the SHEET flag on, when the action just before this analyze() call animated
# (>= 2 frames), its frames are rendered as ONE labelled contact-sheet image (<= 8 panels, first and last always kept,
# integer NEAREST upscale) and attached to the new user message BEFORE the stock current-grid image, which stays last.
# Only the newest sheet is ever sent: older user messages lose their sheet (marker text + image) at trim time.
# With the flag off (the control) the same eligibility is computed and counted, and nothing is attached.
#   THUI_B104_STATS sheet=<bool> builds=<n> eligible=<n> attached=<n> stripped=<n> panels=<sum> sheet_b64=<sum chars>
#     query_errors=<n> render_errors=<n>
import base64 as _thui_b104_base64
import io as _thui_b104_io
import threading as _thui_b104_threading

from PIL import Image as _thui_b104_Image, ImageDraw as _thui_b104_Draw

import inference.agent.vision_context as _thui_b104_vc

_THUI_B104_SHEET = True
_THUI_B104_MAX_PANELS = 8
_THUI_B104_SCALE = 2
_THUI_B104_GAP = 2
_THUI_B104_HEADER = 11
_THUI_B104_COLS = 4
_THUI_B104_MARK = ("Animation of your last action, as one contact sheet: panels in time order, labelled by frame "
                   "index, the last panel is the final board. The current grid image follows it.")
_THUI_B104_POINTER = "\n\nCurrent grid image:"
_THUI_B104_LOCK = _thui_b104_threading.Lock()
_THUI_B104 = {"builds": 0, "eligible": 0, "attached": 0, "stripped": 0, "panels": 0, "sheet_b64": 0,
              "query_errors": 0, "render_errors": 0}
_thui_b104_orig_build = _tool_agent.ToolAgent._build_user_message
_thui_b104_orig_trim = _tool_agent.ToolAgent._trim_messages_for_context


def _thui_b104_bump(key, n=1):
    with _THUI_B104_LOCK:
        _THUI_B104[key] += n


def _thui_b104_report():
    """Printed on the 1st, 51st, ... ELIGIBLE build, so both arms print on the same schedule."""
    with _THUI_B104_LOCK:
        snap = dict(_THUI_B104)
    if snap["eligible"] % 50 == 1:
        print("THUI_B104_STATS sheet=" + str(_THUI_B104_SHEET) + " "
              + " ".join(f"{k}={v}" for k, v in snap.items()), flush=True)


def _thui_b104_pick(n):
    """Frame indices to show: all when n <= MAX, else evenly spaced with the first and the last always kept."""
    if n <= _THUI_B104_MAX_PANELS:
        return list(range(n))
    k = _THUI_B104_MAX_PANELS
    return sorted({round(i * (n - 1) / (k - 1)) for i in range(k)})


def _thui_b104_render(frames):
    idx = _thui_b104_pick(len(frames))
    h = len(frames[0])
    w = max((len(r) for r in frames[0]), default=0)
    if h <= 0 or w <= 0:
        raise ValueError("empty frame")
    pw, ph = w * _THUI_B104_SCALE, h * _THUI_B104_SCALE + _THUI_B104_HEADER
    cols = min(_THUI_B104_COLS, len(idx))
    rows = -(-len(idx) // cols)
    g = _THUI_B104_GAP
    sheet = _thui_b104_Image.new("RGB", (cols * pw + (cols + 1) * g, rows * ph + (rows + 1) * g), (128, 128, 128))
    draw = _thui_b104_Draw.Draw(sheet)
    white = _thui_b104_vc.ARC_COLOR_MAP[0]
    for slot, fi in enumerate(idx):
        grid = frames[fi]
        panel = _thui_b104_Image.new("RGB", (w, h), white)
        px = panel.load()
        for r, row in enumerate(grid[:h]):
            for c in range(w):
                v = row[c] if c < len(row) else 0
                px[c, r] = _thui_b104_vc.ARC_COLOR_MAP.get(int(v), white)
        panel = panel.resize((pw, h * _THUI_B104_SCALE), _thui_b104_Image.Resampling.NEAREST)
        x = g + (slot % cols) * (pw + g)
        y = g + (slot // cols) * (ph + g)
        draw.rectangle([x, y, x + pw - 1, y + _THUI_B104_HEADER - 1], fill=(255, 255, 255))
        label = f"{fi}/{len(frames) - 1}" + (" final" if fi == len(frames) - 1 else "")
        draw.text((x + 2, y), label, fill=(0, 0, 0))
        sheet.paste(panel, (x, y + _THUI_B104_HEADER))
    buf = _thui_b104_io.BytesIO()
    sheet.save(buf, format="PNG")
    return "data:image/png;base64," + _thui_b104_base64.b64encode(buf.getvalue()).decode("ascii"), len(idx)


def _thui_b104_build(self, user_prompt, current_frame):
    msg = _thui_b104_orig_build(self, user_prompt, current_frame)
    _thui_b104_bump("builds")
    content = msg.get("content")
    cb = getattr(self, "_step_env_callback", None)
    if not isinstance(content, list) or cb is None or not getattr(self, "_animation_awareness_enabled", False):
        return msg
    try:
        raw = cb({"query": "animation", "action_num": None})
        rec = raw.get("record") if isinstance(raw, dict) else None
    except Exception:
        _thui_b104_bump("query_errors")
        return msg
    if not isinstance(rec, dict) or rec.get("action_num") != getattr(current_frame, "step", None):
        return msg
    frames = list(rec.get("frames") or [])
    if len(frames) < 2:
        return msg
    _thui_b104_bump("eligible")
    if not _THUI_B104_SHEET:
        _thui_b104_report()
        return msg
    try:
        url, panels = _thui_b104_render(frames)
    except Exception:
        _thui_b104_bump("render_errors")
        return msg
    sheet = [{"type": "text", "text": _THUI_B104_MARK}, {"type": "image_url", "image_url": {"url": url}}]
    head = content[0]
    if isinstance(head, dict) and head.get("type") == "text" and str(head.get("text", "")).endswith(_THUI_B104_POINTER):
        prompt = {**head, "text": head["text"][: -len(_THUI_B104_POINTER)]}
        new = [prompt, *sheet, {"type": "text", "text": _THUI_B104_POINTER.strip()}, *content[1:]]
    else:
        new = [*content[:-1], *sheet, content[-1]]
    _thui_b104_bump("attached")
    _thui_b104_bump("panels", panels)
    _thui_b104_bump("sheet_b64", len(url))
    _thui_b104_report()
    return {**msg, "content": new}


def _thui_b104_has_sheet(m):
    c = m.get("content")
    return m.get("role") == "user" and isinstance(c, list) and any(
        isinstance(p, dict) and p.get("type") == "text" and p.get("text") == _THUI_B104_MARK for p in c)


def _thui_b104_trim(self, messages, *args, **kwargs):
    messages = list(messages or [])
    carriers = [i for i, m in enumerate(messages) if _thui_b104_has_sheet(m)]
    if len(carriers) > 1:
        messages = list(messages)
        for i in carriers[:-1]:
            parts, skip = [], False
            for p in messages[i]["content"]:
                if skip:
                    skip = False
                    if isinstance(p, dict) and p.get("type") == "image_url":
                        continue
                if isinstance(p, dict) and p.get("type") == "text" and p.get("text") == _THUI_B104_MARK:
                    skip = True
                    continue
                parts.append(p)
            messages[i] = {**messages[i], "content": parts}
            _thui_b104_bump("stripped")
    return _thui_b104_orig_trim(self, messages, *args, **kwargs)


_tool_agent.ToolAgent._build_user_message = _thui_b104_build
_tool_agent.ToolAgent._trim_messages_for_context = _thui_b104_trim
assert _tool_agent.ToolAgent._build_user_message is _thui_b104_build
assert _tool_agent.ToolAgent._trim_messages_for_context is _thui_b104_trim
print(f"THUI_B104_GRAFT ok sheet={_THUI_B104_SHEET}", flush=True)
