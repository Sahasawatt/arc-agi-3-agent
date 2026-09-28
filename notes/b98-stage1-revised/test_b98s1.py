"""Checks for b98s1.py, with mutation teeth. Run: python test_b98s1.py [<real-events-file>]  -> ALL OK / FAILED.
Each MUTANT applies one edit to b98s1's source in memory, re-imports it, and asserts the suite now FAILS."""
import importlib.util
import json
import os
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "b98s1.py").read_text(encoding="utf-8")
REAL = sys.argv[1] if len(sys.argv) > 1 else None


def load(src):
    mod = types.ModuleType("b98s1_under_test")
    mod.__file__ = str(HERE / "b98s1.py")
    exec(compile(src, str(HERE / "b98s1.py"), "exec"), mod.__dict__)
    return mod


def board(fill="B", marks=()):
    rows = [[fill] * 8 for _ in range(8)]
    for r, c, ch in marks:
        rows[r][c] = ch
    return "\n".join("".join(r) for r in rows)


def ev(t, **kw):
    return json.dumps(dict(type=t, **kw))


def write(lines):
    d = tempfile.mkdtemp()
    p = os.path.join(d, "zz99-00000000_p0_events.jsonl")
    open(p, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return p


def transcript(level, text):
    return f"--- analysis_step=1 | action=1 | 00:00:00 | tool-agent ---\n[USER PROMPT]\nCurrent state: step 3, level {level}\n\n[THINKING]\n{text}\n"


def checks(m):
    out = []
    ok = lambda name, cond: out.append((name, bool(cond)))

    # T1 turns_of == the peer's turns() on the same text
    txt = transcript(2, "Pressing LEFT always moves the yellow block 3 cells left.") + "[ASSISTANT]\nClicking the red tile makes it disappear.\n"
    tf = os.path.join(tempfile.mkdtemp(), "t.txt")
    open(tf, "w", encoding="utf-8").write(txt)
    ok("turns_of equals stage0 turns()", m.turns_of(txt) == m.s0.turns(tf))
    if REAL:
        with open(REAL, encoding="utf-8") as fh:
            for line in fh:
                e = json.loads(line)
                if e.get("type") == "analysis":
                    open(tf, "w", encoding="utf-8").write(e["transcript"])
                    ok("turns_of equals stage0 turns() on a real transcript", m.turns_of(e["transcript"]) == m.s0.turns(tf))
                    break

    # T2 terminal skip with JSON bool values (the B81 chassis), where the peer parser misses it
    b0, b1, b2 = board(), board(marks=[(1, 1, "Y")]), board(marks=[(2, 2, "Y")])
    p = write([ev("initial", board_ascii=b0, level=1),
               ev("action", board_ascii=b1, level=2, action_name="ACTION4", action_display="RIGHT",
                  level_completed=True, game_over=False, board_changed=True),
               ev("action", board_ascii=b2, level=2, action_name="ACTION4", action_display="RIGHT",
                  level_completed=False, game_over=False, board_changed=True)])
    _, rows = m.read_game(p)
    dec = [r for r in rows if r["kind"] == "decision"]
    ok("terminal transition skipped on bool values", len(dec) == 1)
    ok("peer parser does NOT skip it (the documented string mismatch)", len(m.checker.parse_events(p)) == 2)

    # T3 held-out: the second occurrence of a key is excluded
    p = write([ev("initial", board_ascii=b0, level=1),
               ev("action", board_ascii=b0, level=1, action_name="ACTION1", action_display="UP", level_completed=False,
                  game_over=False, board_changed=False),
               ev("action", board_ascii=b0, level=1, action_name="ACTION1", action_display="UP", level_completed=False,
                  game_over=False, board_changed=False)])
    _, rows = m.read_game(p)
    ho = [r["held_out"] for r in rows if r["kind"] == "decision"]
    ok("repeat key excluded from held-out", ho == [True, False])

    # T4-T6 via score() on a synthetic extract + compiled dir
    move_left = {"action": {"name": "LEFT"}, "target": {"color": "Y"}, "effect": {"type": "move", "dr": 0, "dc": -1}}
    move_right = {"action": {"name": "LEFT"}, "target": {"color": "Y"}, "effect": {"type": "move", "dr": 0, "dc": 1}}
    generic = {"action": {"name": "LEFT"}, "target": {"color": "Y"}, "effect": {"type": "any_change"}}
    before, after = board(marks=[(3, 4, "Y")]), board(marks=[(3, 3, "Y")])

    def game(rows):
        return {"rows": rows, "n_candidates": 0, "n_rules": 1, "n_compile": 1}

    def dec_row(row):
        return {"kind": "decision", "row": row, "level": 1, "held_out": True, "action_name": "ACTION3",
                "action_display": "LEFT", "before": before, "after": after, "board_changed": True}

    def sent(row, id_):
        return {"kind": "sentence", "row": row, "level": 1, "text": "x", "rule": True, "board": before, "id": id_,
                "compile": True}

    def run(games, comp):
        d = Path(tempfile.mkdtemp())
        json.dump({"run": "t", "games": games}, open(d / "ext.json", "w"))
        (d / "c").mkdir()
        for k, h in comp.items():
            json.dump({"hypothesis": h, "status": "OK" if h else "NONE", "generated_tokens": 100},
                      open(d / "c" / f"{k}.json", "w"))
        return m.score(str(d / "ext.json"), str(d / "c"))

    r = run({"g1": game([dec_row(5), sent(9, "a")])}, {"a": move_left})
    ok("sentence AFTER the decision row cannot emit", r["emitting"] == 0 and r["held_out"] == 1)
    r = run({"g1": game([sent(1, "a"), dec_row(5)])}, {"a": move_left})
    ok("sentence BEFORE the decision row emits and is right", r["emitting"] == 1)
    r = run({"g1": game([sent(1, "a"), dec_row(5)])}, {"a": generic})
    ok("generic hypothesis never emits", r["emitting"] == 0 and r["generic_hyps"] == 1)
    ok("emits() itself refuses a generic hypothesis", not m.emits(generic, dec_row(5)))
    ok("emits() accepts the matching specific one", m.emits(move_left, dec_row(5)))
    ok("appear without region is not specific", not m.is_specific(
        {"action": {"name": "UP"}, "target": {"color": "Y"}, "effect": {"type": "appear"}}))
    ok("appear with region is specific", m.is_specific(
        {"action": {"name": "UP"}, "target": {"color": "Y", "region": [0, 1, 0, 1]}, "effect": {"type": "appear"}}))
    # most recent wins: older right hypothesis, newer wrong one -> the decision is scored wrong
    games = {"g1": game([sent(1, "a"), sent(2, "b"), dec_row(5)]),
             "g2": game([sent(1, "c"), dec_row(5)])}
    r = run(games, {"a": move_left, "b": move_right, "c": move_left})
    # g1 emits with b (wrong), g2 emits with c (right); null pool for g1 row = other-game hyps = {c}
    ok("most recent sentence wins", r["emitting"] == 2 and r["iii"]["c"] >= 1)

    # T7 McNemar
    ok("mcnemar 5/0 = 1/32", abs(m.mcnemar_one_sided(5, 0) - 1 / 32) < 1e-12)
    ok("mcnemar 0/0 = 1", m.mcnemar_one_sided(0, 0) == 1.0)
    ok("mcnemar 3/3 > 0.5", m.mcnemar_one_sided(3, 3) > 0.5)

    # T8 filter + cap
    ok("observation rejected by filter", not m.is_rule("clicking (23,61) made M(23,55) disappear"))
    ok("synthetic rule passes filter", m.is_rule("pressing LEFT always moves the yellow block 3 cells left"))
    # T9 v2 draft: the registered sentence controls still hold, the plan/question exclusion bites, markers fire
    ok("v2 rejects the observation control", not m.is_rule_v2("clicking (23,61) made M(23,55) disappear"))
    ok("v2 passes the synthetic rule", m.is_rule_v2("pressing LEFT always moves the yellow block 3 cells left"))
    ok("v2 rejects a plan", not m.is_rule_v2("I will press LEFT each step until the block moves."))
    ok("v2 rejects a question", not m.is_rule_v2("Does clicking the tile toggle the whole row?"))
    ok("v2 per-action quantifier", m.is_rule_v2("RIGHT moved columns by +3 each press."))
    ok("v2 habitual present", m.is_rule_v2("Clicking toggles the tile and its four neighbours."))
    ok("v2 conditional", m.is_rule_v2("When SPACE is pressed the box becomes white."))
    ok("v2 neg controls of stage 0 rejected", not any(m.is_rule_v2(s) for s in m.s0.CONTROLS_NEG))
    capped = m.cap_even(list(range(100)))
    ok("cap_even keeps 60, sorted, starts at 0", len(capped) == 60 and capped == sorted(capped) and capped[0] == 0)
    ok("cap_even leaves <=60 untouched", m.cap_even(list(range(7))) == list(range(7)))
    return out


MUTANTS = [
    ("bool terminal values ignored", 'return v is True or v == "True"', 'return v == "True"'),
    ("file-order gate removed", 'if row < d["row"] and', 'if'),
    ("generic hypotheses allowed to emit", "    if not is_specific(h):\n        return False\n", ""),
    ("oldest sentence wins", "_, h = max(cands", "_, h = min(cands"),
    ("every decision held out", '"held_out": key not in seen_keys', '"held_out": True'),
    ("turn level read from the step number", "int(m.group(2)) if m else None", "int(m.group(1)) if m else None"),
    ("cue list loses 'always'", '("always", ', "("),
    ("v2 plan/question exclusion removed", "    if V2_PLAN.search(sentence):\n        return False\n", ""),
    ("v2 habitual-present marker removed", "or V2_HABIT.search(sentence) ", ""),
]


def main():
    res = checks(load(SRC))
    for name, good in res:
        print(("ok   " if good else "FAIL ") + name)
    clean = all(g for _, g in res)
    teeth = True
    for name, old, new in MUTANTS:
        assert SRC.count(old) == 1, f"mutation anchor not unique: {name}"
        try:
            red = not all(g for _, g in checks(load(SRC.replace(old, new))))
        except Exception:
            red = True
        print(("ok   " if red else "FAIL ") + f"MUTANT goes red: {name}")
        teeth &= red
    print("ALL OK" if clean and teeth else "FAILED")
    sys.exit(0 if clean and teeth else 1)


if __name__ == "__main__":
    main()
