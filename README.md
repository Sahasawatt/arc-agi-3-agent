# arc-agi-3-agent

Team **Thuitanium**'s entry to
[ARC Prize 2026 — ARC-AGI-3](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3),
open source from the first commit.

**This repo holds two independent agents, and the one with the 103 KB operating manual is
not the one being submitted.** Read the next two sections before changing anything.

## The two lines

| | **Line A** — algorithmic | **Line B** — duck-harness fork |
|---|---|---|
| Lives in | root `*.py` + `kaggle/` | `duckmod/`, `duckv5`–`duckv14`, `duckv16` (there is no `v15`) |
| What it is | perception → discovery → planner. No model in the loop | Tufa Labs' LLM-in-a-REPL harness, re-patched per version |
| Ships as | one generated file, `kaggle/my_agent.py` | a Kaggle notebook plus an attached source dataset |
| Best hidden score | 0.10–0.11 | **1.70** (`duck-v10`, 2026-08-21) |
| Status | dormant | **the live campaign** |
| Its manual | [`CLAUDE.md`](CLAUDE.md) | [`notes/wayfinder/MAP.md`](notes/wayfinder/MAP.md) |

⚠️ `CLAUDE.md` documents Line A and does not mention Line B at all. An agent that loads it
and starts optimising is optimising the dormant line.

**Why an algorithmic Line A at all.** The competition notebook has no internet, so a frontier
model cannot be called — the public ARC-AGI-3 leaderboard leader scores 30.2% online while the
Kaggle leaderboard leader scores 1.86%. The ARC engine, meanwhile, runs locally at ~2,000 FPS
with no rate limit, so search is nearly free and only *scored* actions are expensive. Scoring
rewards minimal action sequences, which is what a planner produces and a language model does
not. Line B bets the other way, on a local model in a REPL — and it is winning by 15×.

⚠️ `duckv10`, the current line, **patches nothing** — its cell 12 is a comment. The public
gain that got it there came from adopting a newer upstream bundle and a newer model and
*deleting* the fork's own patches. Line B is not "a patch mechanism".

## public and hidden are different numbers

- **public** — a local eval over the **25 public games**.
- **hidden** — the Kaggle leaderboard column, drawn from the **110 scored games**.

The repo's own hidden-shrink ledger ([`notes/wayfinder/MAP.md`](notes/wayfinder/MAP.md))
puts the gap at **2.4–2.9×**: duck-mod 2.41 → 1.00, v5 2.43 → 0.84, v10 ~4.55 → 1.70. Quote
a public number as a hidden one and you overstate the agent by more than double.

⚠️ **A hidden score is one draw.** `duck-v10` was submitted twice on byte-identical code and
drew **1.70** and then **1.32**. A hidden delta under ~0.4 ranks nothing.

⚠️ **Line A cannot be ranked on one run either** — per-game SD is 2.15–4.88. The "σ ≈ 0.4"
repeated through three build reports is Tufa's spread of the *aggregate* 25-game mean.

## The one rule we impose on ourselves

**Never read, grep, list or derive anything from `environment_files/`.** It is the source
code of the 25 public games — an answer key — and nothing derived from it generalises to the
110 hidden games that are actually scored. It is gitignored, and the SDK writes into it, so
never `git add -A` either.

It is not a competition rule. It is a rule about not poisoning your own measurements.

## Quick start

```bash
uv sync
uv run python -m pytest -q        # 330 tests, offline, ~15 s
uv run python compete.py ls20     # play one game under competition rules
uv run python compete.py          # every playable game
```

An anonymous API key is fetched automatically; no account is needed for development. The
engine also runs fully offline, which is how the competition notebook uses it.

## Layout

Root `*.py` is deliberately flat: `kaggle/bundle.py` embeds each engine and driver module by
**bare name** into the single submitted file, and every module imports its neighbours the
same way. Moving one is a change to the shipping artifact, not a tidy-up.

| Directory | Changes when |
|---|---|
| root `*.py` | the engine, a driver, or a live chain runner changes |
| `kaggle/` | the Line A submission harness changes — `bundle.py` builds `my_agent.py`, `bundle_check.py` gates it |
| `duckmod/`, `duckv*/` | a Line B version is built; each is a Kaggle push root (`kernel-metadata.json` + notebook + `build_notebook.py`) |
| `tests/` | the suite changes — `pytest` only collects here |
| `probes/` | a one-off investigation is written; nothing here is shipped |
| `scripts/` | an operator batch changes |
| `docs/` | the rules snapshot or the Line A campaign log changes |
| `notes/` | the campaign's live state changes |
| `results/` | a run produces an artifact worth keeping |

### The engine (Line A)

| Module | What |
|---|---|
| `perception.py` | frame → connected-component objects, movement events, HUD counters, scale-normalised glyph bitmaps |
| `identity.py` | cross-frame object tracking — the thing that makes the rest trustworthy |
| `discover.py` | works out a game's movement mechanics by acting: piece, footprint, step, direction per action, wall colours |
| `plan.py` | routing from a discovered model — candidate targets, containment-aware goals, BFS |
| `gate.py` | plates, displays, and the square that changes one: which targets let the piece in, and what to walk onto to change that |
| `signals.py` | finds a game's counters anywhere on the frame, tells a clock from a consequence, reads a life's remaining actions |
| `trace.py` | frame-by-frame record of what each action did |
| `scoring.py` | the competition's scoring formula, the 115 cap and the completion cap, for offline analysis |
| `goal_llm.py` | asks a local model which object is the goal — it ranks, the planner routes, the engine judges |

### The runners

| Module | What |
|---|---|
| `compete.py` | plays under the real competition rules — one `make()`, no rewinding, forward only |
| `play.py` | the permissive dev loop: discover, search object sequences, keep what clears a level. **Not rules-legal** — it resets and replays |
| `sigs.py` | every shipped driver signature against every playable game's reset frame; the check before another driver is wired |
| `probe_games.py` | measures, per game, whether the walkable-map assumptions hold at all |

### The whole-game drivers

`bridge` · `claw` · `cover` · `dial` · `ferry` · `glide` · `haul` · `maze` · `mirror` ·
`roller` · `skewer` · `sorter` · `swap` · `tape` · `twin` — one per game family, each behind
a reset-frame `signature()` predicate, with a random fallback for everything else.

⚠️ **`glide` is the fifteenth and it is missing from three of the four rosters** —
`kaggle/bundle.py`'s `MODULES`, `kaggle/bundle_check.py`'s `DRIVERS` and `sigs.py` all list
fourteen, while `compete.py:54` imports it. Filed as
[issue #1](https://github.com/Sahasawatt/arc-agi-3-agent/issues/1).

## Running

```bash
uv run python compete.py [game]              # rules-legal play
uv run python sigs.py                        # driver signatures vs every reset frame
uv run python probe_games.py                 # do the map assumptions hold?
uv run python -m probes.<name>               # a one-off probe, from the repo root
```

### Building a Line A submission

```bash
uv run python kaggle/bundle.py                                       # writes kaggle/my_agent.py
PYTHONPATH=<starter>/vendor/ARC-AGI-3-Agents python kaggle/bundle_check.py
```

⚠️ **Rebuild, then exec — every time.** A stale bundle scores the old level count with
nothing in the logs to explain why. It has happened twice. `bundle_check.py` is that gate:
it exec's the bundle in a fresh namespace and asserts every module in `MODULES` reached
`sys.modules`, every driver is present by name, and each still exposes `signature()`.

### Building a Line B notebook

```bash
python duckv10/build_notebook.py    # patches duckmod/taaf-duck-mod.ipynb, self-checks the cell diff
```

Each `build_notebook.py` asserts which cells it changed and fails loudly if the source
notebook moved under it.

⚠️ **A submission is not a build step.** One per UTC day, per team, shared. Spending the
slot spends someone else's day and it is not recoverable.

## Testing

```bash
uv run python -m pytest -q
```

⚠️ If `rtk` is on the path it rewrites pytest's output — a run *with failures* was reported
as `Pytest: No tests collected`, **exit code 0**. Redirect to a file and read the file.

⚠️ **Never name a standalone check `*_test.py` or `test_*.py`.** `kaggle/bundle_check.py` was
once `kaggle_exec_test.py`; pytest collected it by name, hit its `SystemExit(1)`, and turned
330 passing tests into "no tests ran" — which reads as an empty suite, not as a break.

## Reading further

| | |
|---|---|
| [`notes/wayfinder/MAP.md`](notes/wayfinder/MAP.md) | the campaign's current state, decisions and open questions, on one page |
| [`CLAUDE.md`](CLAUDE.md) | Line A's operating manual and its verification bar |
| [`docs/campaign-log.md`](docs/campaign-log.md) | Line A's measurement diary — every level, every retraction, the eight rules that were right on paper and each cost a game a level |
| [`docs/competition-rules.md`](docs/competition-rules.md) | the rules, quoted, with sources |
| [`docs/notes-ls20.md`](docs/notes-ls20.md) | the reverse-engineered rules of `ls20` and the probe traps that produced confident wrong answers |
| `results/wayfinder/R1`–`R12` | the research reports behind the current design |
| `results/*-build-*.md` | one build report per Line B version |

**A number in any of these is a dated reading, not current state.** Scores move when a
hidden sample is drawn, not when a file is edited.

## The verification bar

It is the architecture, not a preference. Any change to Line A:

1. **A full 17-game sweep before and after** — per game, not just the mean.
2. **No game loses a level.** Eight rules that were correct on paper have each cost a
   different game its own level; they are written up rather than deleted.
3. **One change at a time.** Two at once and a revert tells you nothing.
4. **A claim needs the run that produced it.** "It should help" is not a result.

## Credits

Built by **Thuitanium** — Sahasawat and Watchara Sueasakul.

`duckmod/` and every `duckv*/` derive from the **Tufa Labs** ARC-AGI-3 duck harness
notebook, by Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit, Michal Tesnar and
Stefano Viel. This repo's contribution on that line is the per-version `build_notebook.py`
patches and the build reports in `results/`, not the harness.

## License

MIT No Attribution — see [`LICENSE`](LICENSE).

⚠️ Earlier revisions of this file stated that the competition *requires* open source for
prize eligibility. That has not been verified against the Kaggle rules page, which renders
as a client-side app. MIT-0 is the team's own choice; treat the eligibility claim as
unconfirmed.
