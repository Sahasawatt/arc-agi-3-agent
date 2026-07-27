# arc-agi-3-agent

An agent for [ARC Prize 2026 — ARC-AGI-3](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3).
Open source from the first commit (MIT-0), which the competition requires for prize
eligibility anyway.

## Where this is

Early. The perception and planning pieces work and have solved two levels of one public
game; the part that matters — discovering a game's mechanics without a human reading the
screen — is not built.

**Measured so far, on public game `ls20`:**

| Approach | Result |
|---|---|
| random actions, 5 seeds × 200 actions | 0 levels, every seed |
| local LLM (`qwen2.5:7b`) on the raw 64×64 grid, 200 actions | 0 levels |
| local LLM on an object-level scene + movement feedback, 3 × 200 actions | 0 levels, but 25–34 blocked moves vs random's 39–75 (non-overlapping) |
| **map read off one frame + BFS + budget-aware routing** | **levels 1 and 2, in 14 and 45 actions vs human baselines of 22 and 123** |

The last row is the direction. Both levels cap the per-level score; no LLM is in that loop.

## Why an algorithmic agent rather than a model

The competition notebook has **no internet**, so a frontier model cannot be called — the
public ARC-AGI-3 leaderboard leader scores 30.2% online while the Kaggle leaderboard leader
scores **1.86%**. Meanwhile the ARC engine runs locally at ~2,000 FPS with no rate limit,
so search is nearly free and only *scored* actions are expensive. Scoring is
`min((baseline_actions / actions_taken)² × 100, cap)` weighted by level index, which rewards
minimal action sequences — what a planner produces and a language model does not.

## Layout

| File | What |
|---|---|
| `perception.py` | frame → connected-component objects, movement events between frames, HUD counters, scale-normalised glyph bitmaps |
| `solver.py` | walkable map from a single frame, BFS, multi-waypoint routing with an action budget |
| `agent.py` | play loop with a swappable policy (`random`, two LLM policies) |
| `scoring.py` | the competition's scoring formula, reimplemented for offline analysis |
| `probe_games.py` | measures, per game, whether the walkable-map assumptions hold at all |
| `walk.py` | replay a prefix then probe — per-step position, budget, glyph match |
| `probe.py` | repeat one action from a reset, to see what it does |
| `capture.py` | run an action list; dump PNGs and print what moved |
| `NOTES-ls20.md` | the reverse-engineered rules of `ls20`, the level-2 solution, and the probe traps that produced confident wrong answers |

## Running it

```bash
uv sync
uv run python solver.py ls20 <prefix-actions> cross,yellow1,goalbox0
uv run python walk.py ls20 <prefix-actions> -- <probe-actions>
```

An anonymous API key is fetched automatically; no account needed for development. The
engine can also run fully offline, which is how the competition notebook will use it.

## How far the approach generalises

`probe_games.py` measures, per game, whether the assumptions behind the solver hold: does
anything move under an action, by a constant step, over separable terrain, in several
directions. Full table in [`results/generalisation-probe.md`](results/generalisation-probe.md).

| verdict | games | |
|---|---|---|
| **MAZE_LIKE** — walkable-map + BFS applies | **9 / 25** | trustworthy; every one is `keyboard`-tagged and `ls20` reproduces its known behaviour |
| NEEDS_POINTER | 9 | 6 confirmed by their `click` tag; `ft09`, `cd82`, `sb26` are likely false negatives |
| NOT_GRID_STEPPED | 6 | suspect — the three worst have 183 / 64 / 56 segmented objects, so the object matcher is probably linking the wrong pair |
| PARTIAL | 1 | |

Every verdict is a **lower bound**: the probe presses each action twice from a single
reset, so a piece that starts against a wall reads as immovable. `ft09` is a proven false
negative — arXiv 2512.24156 Table 1 has a keyboard agent clearing three of its levels.

## Next

1. Make rule discovery autonomous. Today a human reads the mechanics off the frames; the
   9 MAZE_LIKE games are where an automated version would pay off first.
2. Re-probe the false negatives from more than one starting state.
3. A harness under `OperationMode.COMPETITION` (one `make()` per environment, no resets)
   for a real baseline across all games.

## Testing

```bash
uv run python -m pytest -q
```

⚠️ If `rtk` is on the path it rewrites pytest's output — a run with failures was reported
as `Pytest: No tests collected` with **exit code 0**. Redirect to a file and read that.

## License

MIT-0. See `LICENSE`.
