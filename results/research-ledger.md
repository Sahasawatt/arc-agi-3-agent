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

# Loop 2026-08-05: reducing actions structurally (post 7/7)

Context: ls20 7/7 43.629% [23,45,99,178,292,209,526]. Session audit measured every
remaining accounting-visible fat as LOAD-BEARING (L5 sweep = the discovery that finds
4 changers; L6 has 0 waste; L7's failed door trips are part of the winning trajectory
— gating them loses the level, `ug-run92.txt`). Local edits are exhausted; this loop
hunts structural levers.

## CLAIMS
- C1 — H — SOTA action efficiency on ARC-AGI-3 (OPINE-World: 78.4% efficiency, 20/25
  games, no per-game training) comes from programmatic/ontological world modeling with
  exploration prioritized by MODEL ERROR — actions chosen to maximally constrain the
  world model, not to cover ground. Source: arxiv.org/pdf/2607.01531.
- C2 — H — The RL/CNN preview winner (StochasticGoose, 12.58%) is self-described
  non-viable as games harden against brute force. Source: Dries Smit's Medium writeup.
- C3 — H — Pure graph/frontier exploration collapses on large state spaces — failed
  ls20 L3+ outright (our symbolic agent exceeds it there). Source: arxiv 2512.24156.
- C4 — H — Our blind sweep is coverage-driven (nearest never-stood), not uncertainty-
  driven; L5's sweep found the 4 shape changers by geography, not by aim. Source:
  `l5-gate2.jsonl` this session.
- C5 — H — The changer-signature READING is accurate (multi-colour block = changer,
  reads most changers from one frame) but all three cheap wirings measured inert or
  level-costing: (1) drive walks with it → costs L4, (2) offer as guessed changer →
  costs L3+L4, (3) reorder cand discovery → inert. Source: CLAUDE.md measured log.
- C6 — H — An accounting table alone cannot license a cut: the heading-gate experiment
  (drop stale headings at unmatched doors) read as ~150-190 saved actions and measured
  as LOSING level 7 (6/7). The wasteful-looking walks build the equilibrium the
  winning composition needs. Source: `ug-run92.txt` + l7-model.md §Tuning pass.

## OPEN QUESTIONS
- O1: Wiring #4 for the signature — re-rank the BLIND SWEEP's never-stood candidates
  (confirm()'s fresh list) by proximity to multi-colour blocks. A different call site
  than the three measured wirings. Risk profile: L4 barely uses the sweep (probe 12 of
  178); L5 is where it pays; L7 exploration is fog-explore, untouched. C6 applies:
  the sweep order IS L5's trajectory — full sweep or nothing.
- O2: A unified uncertainty queue (once{} unconfirmed carries + halves with no
  outgoing edge + mute movers) replacing the rung ladder's implicit priorities —
  the OPINE direction proper. Big refactor, high trajectory risk, park until O1 reads.
- O3: L7's 5 deaths ≈ 110 actions — is any death avoidable without touching round
  ownership? (C6 says: probably entangled.)
- O4: exact per-level baselines for ls20 (scoring.py) → true per-level caps, so gains
  are priced before they are attempted.

## WORKING ANSWER (iteration 1)
The structural direction with SOTA evidence behind it: move exploration from
coverage-first to uncertainty-first (C1). The smallest testable instance in this
codebase is O1 — signature-guided sweep ordering, wiring #4, at a call site the three
refuted wirings never touched. Everything else (O2) waits on how that measures.

## Iteration 2 result: wiring #4 REFUTED (2026-08-05)
Signature-ordered blind sweep (changer_blocks() ≥3 non-bg colours in a piece-sized
window, preferring never-stood squares whose footprint reaches one): suite green,
7/7 kept, but L5 292 → 350 (+58), L6 +1, score 43.629% → 42.871% (`ug-run94.txt`).
The geographic nearest-first sweep beats the signed ordering on the very board the
signature was supposed to help — the sweep's order IS the trajectory (C6 again, from
the winning side this time). Reverted. All FOUR cheap wirings of the sound signature
reading are now measured dead: drive-walks (costs L4), guessed-changer (costs L3+L4),
cand reorder (inert), sweep reorder (costs L5).

## WORKING ANSWER (final for this loop)
Uncertainty-first exploration remains the SOTA direction (C1) but retrofitting it
into this rung ladder one ordering at a time keeps measuring negative — the ladder's
trajectories are chaotically sensitive to ordering (heading-gate: loses L7;
sig-sweep: +58 on L5). The honest options, priced:
(a) O2 full uncertainty-queue refactor — the OPINE shape, weeks-scale, high risk,
    uncapped upside on deep levels;
(b) STOP tuning ls20 (43.6% ≈ plateau of this architecture) and spend the same
    effort on BREADTH: 13 of 17 games sit at 0/n and ls20 already contributes ~96%
    of the 17-game mean (2.662%). One additional game at even 20% ≈ doubles the
    competition mean; no ls20 tuning can.
Recommendation: (b) first, (a) only if a specific game's shape demands it.
