"""Record what the agent did and what happened, one action at a time.

Every attempt so far was judged by one bit — did `levels_completed` move — and everything
in between was thrown away. That is the information the goal is hiding in: an object that
vanishes when touched, a counter that jumps, a wall that opens two moves later. Keeping
the frame-by-frame record makes it available to a human reading `results/traces/` and to a
model that would otherwise only ever see a still board.
"""

import json
from pathlib import Path

from perception import hud, objects

OUT = Path("results/traces")


def _index(frame, model):
    """The board as {(colour, x, y): cells}, with the piece left out.

    Excluded by COLOUR, not by exact size: matching `(colour, w, h)` loses the piece the
    moment it is drawn a cell shorter, and then every single step of the trace reports it
    as an object that disappeared and reappeared — 66 lines of the piece walking, which
    is the one thing the reader already knows.
    """
    own = {c for c, _, _ in model.parts}
    return {(o["colour"], o["x"][0], o["y"][0]): o["cells"]
            for o in objects(frame)[0] if o["colour"] not in own}


def _moved(gone, new, model, action):
    """Pairs that are one object walking, not one vanishing and another appearing.

    The body model routinely misses a part of the piece — a second colour, a trailing
    highlight — and that part then shows up on every single step as a disappearance plus
    an appearance. If the two are the same colour and the gap between them is exactly what
    this action displaces, it walked.
    """
    d = model.dirs.get(action) if getattr(model, "dirs", None) else None
    if d is None:
        return set(), set()
    g_out, n_out = set(), set()
    for g in gone:
        for n in new:
            if g[0] == n[0] and (n[1] - g[1], n[2] - g[2]) == d:
                g_out.add(g)
                n_out.add(n)
                break
    return g_out, n_out


def step(before, after, action, model):
    """One action's worth of consequence."""
    b, a = _index(before.frame, model), _index(after.frame, model)
    hb, ha = hud(before.frame), hud(after.frame)
    gone, new = b.keys() - a.keys(), a.keys() - b.keys()
    walked_g, walked_n = _moved(gone, new, model, action)
    gone, new = gone - walked_g, new - walked_n
    return {
        "action": action,
        "gone": [list(k) for k in sorted(gone)],
        "new": [list(k) for k in sorted(new)],
        "hud": {str(k): [hb.get(k, 0), ha.get(k, 0)]
                for k in set(hb) | set(ha) if hb.get(k, 0) != ha.get(k, 0)},
        "levels": after.levels_completed,
    }


def summarise(steps, budget_keys=(), limit=14):
    """The trace as short English, for a model that cannot read a 64x64 grid.

    Drops the counters that move on every action — a status bar that ticks down each press
    says nothing about what the press *did*, and 60 lines of "budget 84 to 82" is most of
    the context window.
    """
    lines = []
    # `levels` is a running total, so testing it directly announces the completion on
    # every step that follows it — sixteen lines of LEVEL COMPLETED for one event.
    tail = steps[-limit:]
    prev = tail[0]["levels"] - 1 if tail and tail[0].get("levels") else 0
    for s in tail:
        bits = []
        for k in s["gone"]:
            bits.append(f"object colour {k[0]} at x{k[1]} y{k[2]} disappeared")
        for k in s["new"]:
            bits.append(f"object colour {k[0]} appeared at x{k[1]} y{k[2]}")
        for k, (was, now) in s["hud"].items():
            if int(k) in budget_keys:
                continue
            bits.append(f"status colour {k} went {was} to {now}")
        if s["levels"] > prev:
            bits.append(f"LEVEL COMPLETED ({s['levels']})")
        prev = s["levels"]
        lines.append(f"  press {s['action']}: " + ("; ".join(bits) if bits else "nothing changed"))
    return "\n".join(lines)


def per_action_keys(steps):
    """Status-bar colours that change on (almost) every action — the clock, not a signal."""
    if not steps:
        return set()
    counts = {}
    for s in steps:
        for k in s["hud"]:
            counts[int(k)] = counts.get(int(k), 0) + 1
    return {k for k, n in counts.items() if n >= 0.9 * len(steps)}


def save(game, steps):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{game}.jsonl"
    with path.open("a", encoding="utf-8") as f:
        for s in steps:
            f.write(json.dumps(s) + "\n")
    return path
