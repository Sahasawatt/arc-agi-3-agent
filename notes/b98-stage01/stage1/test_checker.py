import importlib.util
import io
import json
import os
import tempfile
from contextlib import redirect_stdout

import checker


def board(rows):
    return rows


def h(effect, action="LEFT", level=1, region=None, color="Y"):
    target = {"color": color}
    if region is not None:
        target["region"] = region
    return {"id": "h", "game": "g", "level": level, "action": {"name": action}, "target": target, "effect": effect}


def transition(before, after, action="LEFT", level=1, name=None):
    return (before, after, {"action_name": name or action, "action_display": action}, level)


def checks(module):
    b = board(["........", "..Y.....", "........", "........", "........", "........", "........", "........"])
    moved = board(["........", "...Y....", "........", "........", "........", "........", "........", "........"])
    assert module.verdict_one(h({"type": "move", "dr": 0, "dc": 1}), b, moved) == "support"
    assert module.verdict_one(h({"type": "recolor", "from": "Y", "to": "G"}), b, board(["........", "..G.....", "........", "........", "........", "........", "........", "........"])) == "support"
    assert module.verdict_one(h({"type": "appear"}, color="G"), b, board(["G.......", "..Y.....", "........", "........", "........", "........", "........", "........"])) == "support"
    assert module.verdict_one(h({"type": "disappear"}), b, board(["........"] * 8)) == "support"
    assert module.verdict_one(h({"type": "count_delta", "delta": 1}, color="G"), b, board(["G.......", "..Y.....", "........", "........", "........", "........", "........", "........"])) == "support"
    assert module.verdict_one(h({"type": "no_change"}), b, b) == "support"
    assert module.verdict_one(h({"type": "any_change"}), b, moved) == "support"
    click = transition(b, moved, "MOUSE(row=10, col=11)", name="ACTION6")
    assert module.match(h({"type": "no_change"}, "CLICK", region=None), click)
    assert module.match(h({"type": "no_change"}, "CLICK", region=None) | {"action": {"name": "CLICK", "at": [20, 20]}}, click) is False
    assert module.evaluate(h({"type": "no_change"}, level=2), [transition(b, b, "LEFT", level=1)])["verdict"] == "untested"
    terminal = transition(b, moved, level=1)
    terminal = (terminal[0], terminal[1], {**terminal[2], "action_display": "LEFT"}, 1)
    assert module.parse_events is not None
    assert module.evaluate(h({"type": "move", "dr": 0, "dc": 1}), [terminal])["verdict"] == "validated"
    support = transition(b, moved)
    contradict = transition(b, b)
    assert module.evaluate(h({"type": "move", "dr": 0, "dc": 1}), [support])["verdict"] == "validated"
    assert module.evaluate(h({"type": "move", "dr": 0, "dc": 1}), [contradict])["verdict"] == "falsified"
    assert module.evaluate(h({"type": "move", "dr": 0, "dc": 1}), [support, contradict])["verdict"] == "mixed"
    assert module.evaluate(h({"type": "move", "dr": 0, "dc": 1}, action="RIGHT"), [support])["verdict"] == "untested"
    for effect in [
        {"type": "move", "dr": 1, "dc": 2}, {"type": "recolor", "from": "Y", "to": "G"},
        {"type": "appear"}, {"type": "disappear"}, {"type": "no_change"},
        {"type": "any_change"}, {"type": "count_delta", "delta": 2},
    ]:
        twin = module.negate(h(effect, color="Y"))
        assert twin["id"] == "h~neg"
    assert module.negate(h({"type": "move", "dr": 0, "dc": 0})) is None
    assert module.negate(h({"type": "count_delta", "delta": 0})) is None
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "g_p0_events.jsonl")
        events = [
            {"type": "initial", "board_ascii": "\n".join(b), "level": "1"},
            {"type": "analysis"},
            {"type": "action", "action_name": "ACTION1", "action_display": "LEFT", "board_ascii": "\n".join(moved), "level": "1", "level_completed": "False", "game_over": "False"},
            {"type": "action", "action_name": "ACTION2", "action_display": "RIGHT", "board_ascii": "\n".join(b), "level": "1", "level_completed": "True", "game_over": "False"},
            {"type": "action", "action_name": "ACTION3", "action_display": "LEFT", "board_ascii": "\n".join(b), "level": "1", "level_completed": "False", "game_over": "False"},
        ]
        with open(path, "w", encoding="utf-8") as stream:
            for event in events:
                stream.write(json.dumps(event) + "\n")
        parsed = module.parse_events(path)
        assert len(parsed) == 2
        assert len([t for t in parsed if t[3] == 1]) == 2
        hypotheses = [{**h({"type": "move", "dr": 0, "dc": 1}), "game": "g"}]
        hp = os.path.join(directory, "h.json")
        with open(hp, "w", encoding="utf-8") as stream:
            json.dump(hypotheses, stream)
        out = io.StringIO()
        old = os.sys.argv
        try:
            os.sys.argv = ["checker.py", hp, directory]
            with redirect_stdout(out):
                module.main()
        finally:
            os.sys.argv = old
        assert len(out.getvalue().splitlines()) == 2


def load_mutant(source):
    spec = importlib.util.spec_from_loader("checker_mutant", loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, "checker.py", "exec"), module.__dict__)
    return module


def run():
    results = []
    for label, fn in [("core checks", lambda: checks(checker))]:
        try:
            fn()
            results.append((label, True))
        except Exception:
            results.append((label, False))
    source = open("checker.py", encoding="utf-8").read()
    mutations = [
        ("MUTANT move shift sign", "shifted = {(r + dr, c + dc) for r, c in before_cells}", "shifted = {(r - dr, c - dc) for r, c in before_cells}"),
        ("MUTANT recolor after color", "after[r][c] == effect[\"to\"]", "after[r][c] == effect[\"from\"]"),
        ("MUTANT level filter", "if transition[3] != h[\"level\"] or not match(h, transition):", "if False or not match(h, transition):"),
    ]
    for label, old, new in mutations:
        try:
            assert source.count(old) == 1
            mutant = load_mutant(source.replace(old, new))
            try:
                checks(mutant)
            except Exception:
                results.append((label, True))
            else:
                results.append((label, False))
        except Exception:
            results.append((label, False))
    for label, passed in results:
        print("ok " + label if passed else "FAIL " + label)
    all_ok = all(passed for _, passed in results)
    print("ALL OK" if all_ok else "FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(run())
