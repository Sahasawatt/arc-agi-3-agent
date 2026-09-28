# B98 stage 1 — transition-hypothesis checker (offline, no state cloning)

Evaluate compiled transition hypotheses against STORED transitions of ARC-AGI-3 game runs. Pure Python 3.12,
standard library only. Files: `checker.py` (library + CLI), `test_checker.py` (runs with `python test_checker.py`,
prints one `ok`/`FAIL` line per check and `ALL OK` / `FAILED`, exit 0 / 1; no pytest).

## Stored transitions
A run's `artifacts/<game>_p0_events.jsonl` has one JSON object per line. Relevant lines:
- `{"type": "initial", "board_ascii": "...", "level": "1", ...}` — the starting board (may be absent; then the first
  action has no before-board and is skipped).
- `{"type": "action", "action_name": "ACTION1".."ACTION7" | "RESET", "action_display": "UP" | "DOWN" | "LEFT" |
  "RIGHT" | "SPACE" | "MOUSE(row=27, col=13)" | "RESET" | ..., "board_ascii": "<64 lines of 64 chars>",
  "level": "3", "level_completed": "True"/"False", "game_over": "True"/"False", ...}` — the board AFTER the action.
  All values are strings. Other types (`analysis`, `experiment`) are ignored.
A transition = (before, after, action, level) where `after` is an action event's `board_ascii`, `before` is the
`board_ascii` of the immediately preceding `initial`/`action` event, `level` = int of the PRECEDING event's `level`.
Skip a transition if either board is missing, or the preceding event had `level_completed` or `game_over` "True"
(the board jumps to a new scene). Boards are compared as lists of strings (rows); cells are single letters
(W w g G c B M P R b S Y O r N p).

## Hypothesis DSL (JSON)
```json
{"id": "h012", "game": "ar25-0c556536", "level": 2,
 "action": {"name": "LEFT"} | {"name": "CLICK", "at": [row, col]} | {"name": "CLICK"},
 "target": {"color": "Y", "region": [r0, r1, c0, c1]},
 "effect": {"type": "move", "dr": 0, "dc": -3}
         | {"type": "recolor", "from": "b", "to": "Y"}
         | {"type": "appear"} | {"type": "disappear"}
         | {"type": "no_change"} | {"type": "any_change"}
         | {"type": "count_delta", "delta": -4}}
```
- `action.name` UP/DOWN/LEFT/RIGHT/SPACE match `action_display` exactly; `ACTION1`..`ACTION7` match `action_name`;
  `CLICK` matches `action_name == "ACTION6"`; with `at`, only clicks whose parsed (row, col) is within Chebyshev
  distance 2 of `at` match. `RESET` matches `action_name == "RESET"`.
- `target.region` is optional, inclusive bounds, clipped to the board; absent = whole board. `target.color` is
  required for move/recolor/appear/disappear/count_delta; for recolor, `from` is the colour looked at.
- A hypothesis is matched only against transitions of its own `game` and `level`.

## Per-transition verdict: "support" | "contradict" | "na"
Let R = region cells, T = set of R-cells whose BEFORE colour is target.color (for recolor: `from`).
- move(dr,dc): na if T empty or (dr,dc)==(0,0). Shifted S = {(r+dr,c+dc) for (r,c) in T} kept in-board. support iff
  >= 90 % of S has target.color in AFTER AND at least one cell of T \ S no longer has target.color in AFTER;
  else contradict. (S is NOT clipped to the region: objects may move out of it.)
- recolor(from,to): na if T empty. support iff >= 50 % of T has colour `to` in AFTER; else contradict.
- appear: count = number of R-cells with target.color. support iff after_count > before_count, else contradict.
- disappear: na if before_count == 0. support iff after_count < before_count, else contradict.
- count_delta(d): support iff after_count - before_count == d, else contradict.
- no_change: support iff R identical in BEFORE and AFTER, else contradict. any_change: the reverse.

## Hypothesis verdict
Over its matching transitions: `validated` (support >= 1, contradict == 0), `falsified` (contradict >= 1,
support == 0), `mixed` (both >= 1), `untested` (no support/contradict). Return also the counts.

## Negated twin (teeth control)
`negate(h)` returns a copy with id `h["id"] + "~neg"` and effect: move -> (-dr, -dc); recolor from/to swapped;
appear <-> disappear; no_change <-> any_change; count_delta d -> -d. Return None when no meaningful negation exists
(move (0,0), count_delta 0).

## CLI
`python checker.py <hypotheses.json> <run-dir>` — hypotheses.json is a JSON list; prints one JSON line per
hypothesis AND per non-None twin: `{"id","game","level","verdict","support","contradict","na","matched"}`.

## Tests (synthetic 8x8 boards, no files needed except one temp events.jsonl written by the test)
Positive cases for every effect type, a click matched by `at` and one rejected by distance, level filtering,
skip after level_completed, verdict aggregation (validated/falsified/mixed/untested), negate() for every type, and an
end-to-end CLI run on a temp events file. MUTANT checks (the test applies each mutation to the loaded module source
in memory, re-imports it, and asserts the suite now FAILS): (1) move shift sign flipped; (2) recolor checks `from`
instead of `to` in AFTER; (3) the level filter removed.
