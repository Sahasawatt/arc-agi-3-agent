# The rules we are actually playing under

Read from the official sources on 2026-07-27, because the agent had been developed against
assumptions that do not hold in the scored setting. Every line below is quoted; the
implications are marked as ours.

## Competition mode

Source: <https://docs.arcprize.org/toolkit/competition_mode.md>

> Can only interact (call `make`) a single time for each environment

> Only *Level Resets* are premitted, *Game Resets* are not allowed and become *Level Resets*

> Scoring is against all available environments, even if you choose not to interact with them

> Can only open a single Scorecard

`get_scorecard` does not work on an in-progress scorecard.

**What this breaks in our code.** `play.at_state()` resets and replays a prefix to reach a
state, and the whole search is built on it — `clear_level` calls it once per candidate,
thousands of times per level. In competition mode a reset **restarts the current level**, so
after level 1 is cleared, replaying a level-1 prefix runs those actions against the level-2
board. The search does not fail loudly; it silently evaluates nonsense. Everything measured
this session was measured in a mode the competition does not offer.

## Scoring

Source: <https://docs.arcprize.org/methodology.md>

> level_score = (human_baseline_actions / ai_actions) ^ 2

> The maximum score per level is capped at 1.15x human baseline.

> The game score is the weighted average of all per-level scores, using the 1-indexed level
> number as the weight.

> To unlock a maximum game score of 100%, the AI must complete all levels, including the
> final one.

The game score is additionally capped by how many levels were completed — clearing level 1
of seven does not merely score 1/28 of the weight, it also caps what the game can score at
all. `scoring.py` implements the formula and the 115 cap but **not** that completion cap.

## Limits

Source: <https://docs.arcprize.org/rate_limits.md>

> Rate limits are set at 600 requests per minute (RPM).

No per-game or per-run action cap is documented, and no timeout.

**A correction we made to ourselves.** The ARC-AGI-3 technical report says "given a human
median of n actions to completion, the agent is terminated after 5n actions" — but that is
how ARC Prize ran **their own evaluation** of frontier models, and the same sentence refers
to "the environment's intrinsic action limit" as a separate, larger thing. It is **not** a
documented competition rule. We briefly treated 5n as a hard cap and it is not established.
Source: <https://arcprize.org/media/ARC_AGI_3_Technical_Report.pdf>

## Running and submitting

Source: <https://docs.arcprize.org/arc-prize-2026.md>

> the local `arc-agi` PyPI package hosts the same game engine the Kaggle gateway runs

> Once downloaded, games are cached in `environment_files/` and you're fully offline

Kaggle runs the notebook once to validate it executes, then reruns it against the hidden
game set when you submit.

## What is NOT settled

- **Whether an agent may instantiate a game outside the scored scorecard.** The competition
  mode page restricts `make`, resets and scorecards; it says nothing about creating another
  environment instance. Absence of a prohibition is not permission, and it may not even be
  possible: on Kaggle the games come through a gateway, and there is no statement that the
  hidden games' files land in `environment_files/` where an agent could reach them.
- The full Kaggle rules page would settle it. It renders as a client-side app and could not
  be read; the search-engine summary claiming the competition "allows local engines and
  offline exploration" quotes no rule and is not evidence.

## The one rule we impose on ourselves

Never read, grep or derive anything from `environment_files/`. It is the source code of the
public games — the answer key — and nothing derived from it can generalise to the 110 games
that are actually scored.
