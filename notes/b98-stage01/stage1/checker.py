import json
import re
import sys
from copy import deepcopy


def parse_events(path):
    transitions = []
    previous = None
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            event = json.loads(line)
            if event.get("type") not in {"initial", "action"}:
                continue
            if event.get("type") == "action" and previous is not None:
                before = previous.get("board_ascii")
                after = event.get("board_ascii")
                terminal = previous.get("level_completed") == "True" or previous.get("game_over") == "True"
                if before is not None and after is not None and not terminal:
                    transitions.append((before.splitlines(), after.splitlines(), event, int(previous["level"])))
            previous = event
    return transitions


def _action_parts(transition):
    action = transition[2]
    if isinstance(action, dict):
        return action.get("action_name", ""), action.get("action_display", "")
    return "", str(action)


def match(h, t):
    name, display = _action_parts(t)
    wanted = h["action"]["name"]
    if wanted == "CLICK":
        if name != "ACTION6":
            return False
        if "at" not in h["action"]:
            return True
        found = re.fullmatch(r"MOUSE\(row=(-?\d+), col=(-?\d+)\)", display)
        if not found:
            return False
        row, col = (int(value) for value in found.groups())
        target_row, target_col = h["action"]["at"]
        return max(abs(row - target_row), abs(col - target_col)) <= 2
    if wanted.startswith("ACTION") or wanted == "RESET":
        return name == wanted
    return display == wanted


def _region(h, board):
    rows = len(board)
    cols = max((len(row) for row in board), default=0)
    bounds = h["target"].get("region")
    if bounds is None:
        return range(rows), range(cols)
    r0, r1, c0, c1 = bounds
    return range(max(0, r0), min(rows, r1 + 1)), range(max(0, c0), min(cols, c1 + 1))


def _cells(h, board, color):
    rows, cols = _region(h, board)
    return {(r, c) for r in rows for c in cols if c < len(board[r]) and board[r][c] == color}


def verdict_one(h, before, after):
    effect = h["effect"]
    kind = effect["type"]
    color = h["target"].get("color")
    if kind == "recolor":
        color = effect["from"]
    before_cells = _cells(h, before, color)
    after_cells = _cells(h, after, color)
    if kind == "move":
        dr, dc = effect["dr"], effect["dc"]
        if not before_cells or (dr, dc) == (0, 0):
            return "na"
        shifted = {(r + dr, c + dc) for r, c in before_cells}
        in_board = {(r, c) for r, c in shifted if 0 <= r < len(after) and 0 <= c < len(after[r])}
        retained = sum(after[r][c] == color for r, c in in_board)
        vacated = any((r, c) not in shifted and after[r][c] != color for r, c in before_cells)
        return "support" if retained >= 0.9 * len(in_board) and vacated else "contradict"
    if kind == "recolor":
        if not before_cells:
            return "na"
        changed = sum(0 <= r < len(after) and c < len(after[r]) and after[r][c] == effect["to"] for r, c in before_cells)
        return "support" if changed >= 0.5 * len(before_cells) else "contradict"
    before_count = len(before_cells)
    after_count = len(after_cells)
    if kind == "appear":
        return "support" if after_count > before_count else "contradict"
    if kind == "disappear":
        if before_count == 0:
            return "na"
        return "support" if after_count < before_count else "contradict"
    if kind == "count_delta":
        return "support" if after_count - before_count == effect["delta"] else "contradict"
    rows, cols = _region(h, before)
    same = all(c < len(before[r]) and c < len(after[r]) and before[r][c] == after[r][c] for r in rows for c in cols)
    if kind == "no_change":
        return "support" if same else "contradict"
    if kind == "any_change":
        return "support" if not same else "contradict"
    raise ValueError(f"unknown effect: {kind}")


def evaluate(h, transitions):
    counts = {"support": 0, "contradict": 0, "na": 0, "matched": 0}
    for transition in transitions:
        if transition[3] != h["level"] or not match(h, transition):
            continue
        counts["matched"] += 1
        counts[verdict_one(h, transition[0], transition[1])] += 1
    if counts["support"] and not counts["contradict"]:
        verdict = "validated"
    elif counts["contradict"] and not counts["support"]:
        verdict = "falsified"
    elif counts["support"] and counts["contradict"]:
        verdict = "mixed"
    else:
        verdict = "untested"
    return {"id": h["id"], "game": h["game"], "level": h["level"], "verdict": verdict, **counts}


def negate(h):
    twin = deepcopy(h)
    twin["id"] = h["id"] + "~neg"
    effect = twin["effect"]
    kind = effect["type"]
    if kind == "move":
        if (effect["dr"], effect["dc"]) == (0, 0):
            return None
        effect["dr"], effect["dc"] = -effect["dr"], -effect["dc"]
    elif kind == "recolor":
        effect["from"], effect["to"] = effect["to"], effect["from"]
    elif kind in {"appear", "disappear"}:
        effect["type"] = "disappear" if kind == "appear" else "appear"
    elif kind in {"no_change", "any_change"}:
        effect["type"] = "any_change" if kind == "no_change" else "no_change"
    elif kind == "count_delta":
        if effect["delta"] == 0:
            return None
        effect["delta"] = -effect["delta"]
    else:
        return None
    return twin


def main():
    with open(sys.argv[1], encoding="utf-8") as stream:
        hypotheses = json.load(stream)
    cache = {}
    for hypothesis in hypotheses:
        cache.setdefault(hypothesis["game"], parse_events(f"{sys.argv[2]}/{hypothesis['game']}_p0_events.jsonl"))
        for candidate in (hypothesis, negate(hypothesis)):
            if candidate is not None:
                print(json.dumps(evaluate(candidate, cache[hypothesis["game"]]), separators=(",", ":")))


if __name__ == "__main__":
    main()
