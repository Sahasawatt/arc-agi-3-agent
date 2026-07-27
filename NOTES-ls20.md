# arc-play — ARC-AGI-3 toolkit sandbox

Playground for the [ARC Prize toolkit](https://docs.arcprize.org/toolkit/overview).

## Setup

```bash
uv sync
```

No API key needed — the toolkit fetches an anonymous one on first use. Set
`ARC_API_KEY` to attach scorecards to an account (register at three.arcprize.org).

> **Gotcha:** the project name must not be `arc-agi`, or `uv add arc-agi` fails with
> `self-dependencies are not permitted`. Hence `name = "arc-play"` in `pyproject.toml`.

## Scripts

| Script | What it does |
|---|---|
| `agent.py` | The agent — play loop with a swappable policy. |
| `perception.py` | 64x64 colour grid → object list, movement events, HUD counts, glyph bitmaps. |
| `solver.py` | Reads the maze off one frame, BFS-es routes, plans a waypoint route against the budget. |
| `walk.py` | Replay a prefix, then probe — prints block position, budget, glyph match per step. |
| `probe.py` | Press one action repeatedly from a fresh reset, to see what each action does. |
| `capture.py` | Run an action list, dump every frame to PNG **and** print what moved each step. |
| `random_agent.py` | The first smoke test. Superseded by `agent.py --policy random`. |

```bash
uv run python agent.py --policy ollama2 --game ls20 --steps 200
uv run python solver.py ls20 <prefix> cross,yellow1,goalbox0   # plan a route
uv run python walk.py ls20 <prefix> -- <probe>                 # run an experiment
```

## Policies

A policy is `f(obs, actions, history) -> (GameAction, data)`. Add one to `POLICIES` in
`agent.py`; nothing else changes.

- `random` — baseline.
- `ollama` — sends the raw 64x64 grid as 64 lines of hex.
- `ollama2` — sends `perception.py`'s object list plus what the last 8 actions did.

Both ollama policies talk to a local ollama on `127.0.0.1:11434` (`--model`, default
`qwen2.5:7b`). No hosted API key exists on this box; the policy seam is where one goes.

## Results — ls20, 200 steps

| policy | levels | resets | blocked moves | note |
|---|---|---|---|---|
| `random`, seeds 0-4 | 0 (5/5) | 1 | 39–75 / 200 (n=5) | the floor |
| `ollama` (raw grid) | 0 | 1 | 44 / 200 (n=1) | inside random's range |
| `ollama2` (perception) | 0 | 1 | 25–34 / 200 (n=3) | below random's range, no overlap |
| hand-played | **1** | 0 | — | in 14 actions |

No LLM policy completed a level, so on the metric that counts, both tie with random.

Feeding the raw 64x64 grid bought nothing — 44 blocked moves sits inside the range random
produces by chance. The perception layer does separate cleanly: 25/31/34 against random's
39/46/50/63/75, non-overlapping. So the object list plus "nothing moved means blocked"
feedback teaches a 7B model to stop walking into walls, and nothing beyond that.

`fallback_to_random` counts steps where the model named an action it could not take, so a
policy can't look better than it is by silently degrading to random.

> **Metric caveat.** "Blocked moves" counts steps changing ≤2 cells. It cannot be `== 0`:
> the budget bar ticks 2 cells on *every* action, so a move into a wall still changes 2.
> An earlier version of this table used `== 0` and reported 0–5/200 for random, which
> measured the budget bar, not the agent. Any older numbers are not comparable to these.

## ls20 rules, reverse-engineered

Levels 1 and 2 solved by hand — 14 and 45 actions. Level 3 reached.

- `ACTION1/2/3/4` = up / down / left / right, 5 cells per press.
- The white `+` **rotates the block's glyph 90° per touch** — a 4-state cycle that returns
  to where it started. Standing on it does nothing; you must *enter* the square again, so
  step off and back on to rotate twice.
- The plate at bottom-left is the block's current glyph; the plate on the goal box is the
  one it must be wearing. **The goal box physically blocks the block until they match** —
  it is not a scoring rule, the move simply doesn't happen.
- The yellow bar is a budget: 84 cells, **4 cells per action, so 21 actions to a life**.
  It runs out → lose a life, level restarts. Three red squares = three lives.
- A **yellow 3x3 square refills the budget to full** and is consumed. Nothing else — not a
  portal, not a glyph changer, not a hazard.
- Level 2's real puzzle is budget routing: the `+` is 17 moves away in one corner and the
  goal is 16 moves away in the other, so no single life reaches both. The two yellows are
  the refuel stops that make a route exist.
- Level 3 adds a multi-coloured square, two white ticks, and switches the glyph's ink from
  blue to orange.

**Level 2 solution** (after the level-1 prefix `3,3,3,1,1,1,1,1,4,4,4,1,1,1`):

```
1,4,1,1,1,1,1,4,4,2,4,2,2,2,2,2,2,2,3,3   far yellow  (20, budget 21→1, refill)
4,1,4                                      the cross   (3)
1,2                                        rotate once more — the step that was missing
1,1,1,1,1,1,1,3,3,3,3,3,3,2,3              near yellow (15, refill)
2,2,2,2,2                                  into the goal
```

### Four traps, each of which produced a confident wrong answer

1. **A probe from one position is not a claim about an action.** `probe.py` first reported
   `ACTION2` as a no-op; the block simply starts with a wall below it.
2. **Repeated single-direction probing cannot solve a maze.** Every direction from level 2's
   start dead-ends within one move. Reading the walkable map off the frame and running BFS
   found the route with zero further API calls — and its self-check reproduced all four
   known blocked/free directions before it was trusted.
3. **Measuring the wrong strip.** `hud()` reads rows ≥60, which is the budget bar — *not*
   the glyph panel at `x1-10 y53-59`. The "pattern" numbers it produced were meaningless
   until the glyph was read from the panel itself.
4. **Cell counts are not shapes, and shapes need normalising.** The indicator is drawn at
   2x the goal marker's scale, so identical glyphs compare unequal and different glyphs
   can share a cell count. `icon()` collapses repeated adjacent rows/columns before
   comparing.

And one that cost a whole life: a 44-move action list was **hand-copied with one `1`
missing**, so the block turned left a row too early into a wall and starved. Assemble long
action lists from variables, never by retyping.

## Toolkit notes

- 25 environments; `Arcade().get_environments()` lists them with a `tags` field saying
  which inputs a game takes: `keyboard` (ACTION1-4), `click` (ACTION6 + x/y),
  `keyboard_click` (both).
- A frame is `(1, 64, 64)` int8 over a 16-colour palette.
- `render_mode`: `terminal` / `terminal-fast` / `human` (matplotlib). `capture.py` skips
  those and writes PNGs, so frames can be inspected outside a terminal.
- `Arcade.listen_and_serve()` is a REST API server (how Kaggle runs a submission), not a
  playable UI.

## Open

- No hosted LLM key on this box, so the only brain available is `qwen2.5:7b` (text-only,
  no vision). A vision model reading `frames/*.png` is the obvious next policy.
- `perception.py` over-splits some objects (an icon's inner notch becomes its own
  component) — fine for movement tracking, noisy in the prompt.
- Only `ls20` explored, and only to level 2 of 7.
