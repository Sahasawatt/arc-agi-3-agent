# think-research ledger — unblocking goal inference

Question: is there a published technique that turns an interaction trace into a rule
hypothesis a **7B** can execute, and that ends up as offline code? Run 2026-07-27.

## CLAIMS

- **Every approach that scores well on ARC-AGI-3 has a frontier model writing or refining
  code, verified against recorded history.** — H — Schema (Impossible Research):
  "models act like physicists: they write each game's mechanics as an executable program,
  verify it against recorded history, and plan inside it using search", ~99% RHAE on the
  public set with Claude Opus 4.8 / Fable 5, 95.35% with GPT-5.6 Sol; self-reported, not
  independently verified. https://schema-harness.github.io/
- **The harness, not the weights, carried most of that gain.** — H — Schema reports a
  controlled comparison lifting a Claude Code baseline from **42.83% to 98.98% RHAE** on
  the same 25 public games, without changing model weights. https://schema-harness.github.io/
- **Executable World Models reaches the same shape independently.** — H — the agent keeps
  three Python files (transition engine, state IO, planner), a verifier checks the model
  reproduces recorded observations, and a plan executor compares predicted against observed
  frames. GPT-5.4 via Codex CLI, **$34–620 per game**, mean 32.58% RHAE, 7 of 25 games
  fully solved. https://arxiv.org/html/2605.05138v1
- **The milestone-1 winners used no search and no world model.** — H — all three are
  LLM-as-policy or agent-writes-code; Reki emits a single JSON object of 1–4 actions per
  step. https://arcprize.org/blog/arc-prize-2026-milestone-1
- **The winners' own conclusion is that hand-built tools hurt.** — H — Tufa Labs: hand-crafted
  tools "actually hurt the model; letting it improvise worked better", and their "gains came
  from multimodality and better base models, not hand-built tools". 1.21% with Qwen 3.6 27B.
  https://tufalabs.ai/research/duck-harness/ · https://arcprize.org/blog/arc-prize-2026-milestone-1
- **An 8B can induce game rules including termination conditions — but only for games it
  recognises.** — H — causal-induction study asks the model for a full VGDL definition
  (SpriteSet, LevelMapping, InteractionSet, **TerminationSet**) from ASCII traces; Qwen3-8B
  reaches ~74.7% and QwQ-32B ~77.5%, but the "Destructive" setting that withholds the game's
  name collapses accuracy from ~80% to **~45%**, and the authors conclude models "do not
  possess a complete or robust understanding" without external descriptions.
  https://arxiv.org/html/2602.00190
- **Classical ILP is not a way round the model.** — M — on IGGP (50 games, learn rules from
  traces) the best system solves **40% of tasks perfectly**, and predicate invention is "not
  yet sufficiently powerful". https://arxiv.org/abs/1906.09627
- **Frontier models used bare, without a harness, also fail.** — H — Gemini 3.1 Pro ~0.37%,
  Claude Opus 4.6 ~0.2%, humans near 100% over >1000 level attempts.
  https://www.emergentmind.com/topics/arc-agi-3

- ~~There is a hard action cap of 5x the human median.~~ **RETRACTED** — the official
  scoring and rate-limit docs document **no action cap**, only 600 RPM. The 5n figure is how
  ARC Prize terminated agents in *their own* evaluation for the technical report, and that
  same sentence names "the environment's intrinsic action limit" as a separate, larger thing.
  https://docs.arcprize.org/methodology.md · https://docs.arcprize.org/rate_limits.md
- **Competition mode allows one `make()` per environment and converts game resets into level
  resets.** — H — "Can only interact (call `make`) a single time for each environment";
  "Only *Level Resets* are premitted, *Game Resets* are not allowed and become *Level Resets*".
  This is what actually invalidates the current architecture: `play.at_state()` reaches a
  state by resetting and replaying a prefix, so after level 1 it would replay level-1 actions
  against the level-2 board. https://docs.arcprize.org/toolkit/competition_mode.md
- **The game score is capped by how many levels were completed, not just weighted by them.**
  — H — "To unlock a maximum game score of 100%, the AI must complete all levels, including
  the final one." `scoring.py` implements the formula and the 1.15x cap but not this.
  https://docs.arcprize.org/methodology.md
- **The benchmark is QA'd against random play.** — H — same report: "The first random regime
  runs for up to 50,000 steps and asserts that no level can be beaten by accident", with the
  caveat that on the deliberately-easy tutorial level "random agents can occasionally stumble
  into success ... which is acceptable by design".
- **Measured here, and it changes the plan: random play does clear levels on some games.** — H
  — 40,000 uniformly random actions per game, seed 7, resets on game over:
  `cn04` 1 level-up, `sp80` 1 level-up, and 0 for `ls20`, `sc25`, `ka59`, `re86`.
  Two of the six are games that five directed strategies never cleared.
  (`results/random-baseline.log`)

## OPEN QUESTIONS

- How long is a random-found solution, and can it be trimmed under the 5n cap? A success that
  cannot be replayed inside the cap scores nothing.
- Does a second seed reproduce the `cn04` / `sp80` successes, or were they one-offs?
- Schema's harness is the lever, but is any of it usable *without* a frontier model — is the
  win in the program-writing, or in the verify-and-search loop around it?

## WORKING ANSWER

**No published technique fits a 7B on novel games** — M-H. The one study that tests an 8B on
exactly this task (induce a game's rules, termination conditions included, from ASCII traces)
shows it at ~74.7% on games it recognises and **~45% once the game's identity is withheld**,
which is the ARC-AGI-3 condition. Classical ILP tops out at 40% perfect on a cleaner
benchmark. Everything that scores well uses a frontier model writing code.

**But the blocker was misdiagnosed, including by me.** It is not goal inference. It is the
absence of a single positive example: no inducer, LLM or ILP, can fit a rule to traces that
contain no success. And the cheapest possible generator — uniform random play, offline, free
— produces one on 2 of 6 games at 40k actions, on games the directed search never cleared.

So the transferable idea from Schema is the loop, not the model: **generate cheaply offline,
verify exactly, keep only what verified.** The generator does not have to be smart if
verification is free — and the engine makes it free.
