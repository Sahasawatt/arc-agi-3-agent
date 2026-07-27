"""Ask a local model which object is the goal. It proposes; the engine decides.

The algorithmic search knows how to reach anything and has no idea what to reach — it
tries objects shortest-route first, which is a guess with no prior. A language model has
seen a great many puzzles and is a decent prior over "what is a door, what is a key, what
is a prize", and it is wrong often enough that its answer cannot be trusted. So it never
acts: it ranks, the planner routes, and `levels_completed` is the only judge. Being wrong
costs a replay, which is free.

Requires ollama running locally. Absent, `propose` returns nothing and the caller falls
back to search — the whole point of the competition notebook having no internet.
"""

import json
import re

import requests

OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:7b"
TIMEOUT = 180
FAILURES = {"count": 0, "last": ""}   # silent fallback hid a timeout for a whole run


def describe(model, targets, hud_counts, level):
    """The scene as a short list. A 64x64 grid of numbers is unreadable for a 7B model."""
    lines = [f"Level {level} of a grid puzzle. You control one piece.",
             f"Piece: colour {model.colour}, {model.box[0]}x{model.box[1]} cells, "
             f"moves {model.step} cells per press, {len(model.dirs)} directions.",
             f"Walls (impassable colours): {sorted(model.blocking) or 'none found'}.",
             f"Floor (colours it walks on): {sorted(model.passable) or 'unknown'}.",
             f"Status bar counts by colour: {hud_counts}.",
             "", "Objects on the board:"]
    for i, o in enumerate(targets):
        w = o["x"][1] - o["x"][0] + 1
        h = o["y"][1] - o["y"][0] + 1
        lines.append(f"  [{i}] colour {o['colour']}, {w}x{h}, {o['cells']} cells, "
                     f"at x={o['x'][0]} y={o['y'][0]}")
    return "\n".join(lines)


PROMPT = """{scene}
{history}

The level ends when the piece does the right thing with the right objects. You do not know
the rules; work them out from what already happened above, then guess from the board. Common patterns: walk into a large
container or marked exit; pick something up first and then reach the exit; collect every
copy of one small object; match a shape shown in the status bar.

Give up to 4 different plans, best first. A plan is an ordered list of object indices for
the piece to walk onto. Keep plans short — 1 to 3 objects.

Answer with JSON only: an object whose key "plans" holds a list of plans, each plan a flat
list of integers and nothing else — indices from THIS board, in visiting order. No
explanations anywhere; indices only."""


def parse(text, n_targets, max_plans=4):
    """Pull plans out of the reply, dropping anything that is not a usable index list."""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    out = []
    for entry in data.get("plans", [])[:max_plans * 2]:
        plan = _indices(entry)
        # A 7B model pairs each plan with its reason as [[6], "because ..."] about as often
        # as it returns the bare list it was asked for. Take the indices wherever they are.
        if plan and plan not in out and len(plan) <= 4:
            out.append(plan)
        if len(out) >= max_plans:
            break
    return [p for p in out if all(0 <= i < n_targets for i in p)]


def _indices(entry):
    """The list of ints inside whatever shape the model wrapped its plan in."""
    if isinstance(entry, int):
        return [entry]
    if isinstance(entry, dict):
        entry = list(entry.values())
    if not isinstance(entry, list) or not entry:
        return []
    if all(isinstance(i, int) for i in entry):
        return entry
    for item in entry:
        got = _indices(item)
        if got:
            return got
    return []


def propose(model, targets, hud_counts, level, llm=MODEL, history=""):
    """Ranked plans as lists of indices into `targets`. Empty if the model is unavailable.

    `history` is the frame-by-frame record of what the agent already tried. A still board
    cannot say what a touch does; the trace can, and that is the only place the rule is
    written down.
    """
    if not targets:
        return []
    hist = ""
    if history:
        hist = "\n\nWhat happened when the piece moved so far:\n" + history + "\n"
    prompt = PROMPT.format(scene=describe(model, targets, hud_counts, level), history=hist)
    try:
        r = requests.post(OLLAMA, timeout=TIMEOUT, json={
            "model": llm, "prompt": prompt, "stream": False, "format": "json",
            "options": {"temperature": 0.2, "num_predict": 120}})
        r.raise_for_status()
    except Exception as e:
        # Swallowing this made "the model has no idea" and "the model never answered"
        # look identical, and a run reported four games' worth of empty plans that were
        # all read timeouts.
        FAILURES["count"] += 1
        FAILURES["last"] = f"{type(e).__name__}: {e}"
        return []
    return parse(r.json().get("response", ""), len(targets))
