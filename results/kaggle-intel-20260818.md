# ARC Prize 2026 (ARC-AGI-3) Competitive Intel — 2026-08-18

Scope: read-only web research, 40-min budget. Our score 0.11 vs sample baseline ~1.56 vs top5 2.35–2.81.
Every claim below carries a source URL; anything without one is labeled **SPECULATION** or **NOT FOUND**.

---

## Q1 — Official baseline (StochasticGoose / Tufa Labs): architecture + weaknesses

**Architecture** (Tufa Labs, preview-competition 1st place, 12.58%):
- Simple RL agent, not an LLM. A CNN takes the current frame as input and predicts probabilities that each of the 5 simple actions is "legal" (i.e. will change the frame) — this replaces random exploration with a learned action-legality prior.
- For the coordinate action (`ACTION6`, click-a-cell), it uses a "spatially-aware decoding strategy" rather than flattening the grid into a flat softmax — preserves 2D locality when predicting where to click.
- Source: [ARC-AGI-3: A New Challenge for Frontier Agentic Intelligence (arXiv 2603.24621)](https://arxiv.org/html/2603.24621v1), [daily.dev writeup](https://daily.dev/posts/the-benchmark-with-no-instructions-tufa-labs-arc-agi-3--nagrqjc2f)
- The sample submission on Kaggle is literally this: [ARC3 Sample Submission - Stochastic Goose](https://www.kaggle.com/code/inversion/arc3-sample-submission-stochastic-goose) — confirms our "base" reference (~1.56 aggregate) is this exact agent family, tagged `StochasticGoose_v7_final`, currently ranked ~#30 on the live leaderboard. Source: [ARC-AGI-3 leaderboard Medium writeup](https://medium.com/@ccro8990/the-official-live-leaderboard-for-the-arc-agi-3-machine-learning-competition-hosted-on-kaggle-part-06dbe491c8dc)

**Known weaknesses** (from the ARC Prize's own 30-day preview retro):
- It learns *which actions change something*, but not *what a good sequence of actions is* — the retro explicitly frames the core failure mode as agents that "struggle to turn information from the environment into a workable strategy," i.e. good local exploration, weak global planning.
- "Random brute-force agents may eventually complete a level but require far more actions" — since scoring is action-efficiency-based (see Q3), this directly caps StochasticGoose-style agents' ceiling even if they eventually finish games.
- Source: [ARC-AGI-3 Preview: 30-Day Learnings](https://arcprize.org/blog/arc-agi-3-preview-30-day-learnings)

Tufa Labs itself has since moved off this architecture entirely — see Q2.

---

## Q2 — Top public approaches / writeups

Ranked by concreteness of what they publish (not by leaderboard position, which is not publicly attributable by team name — see caveat at bottom of this section).

1. **Duck Harness (Tufa Labs, current Kaggle rank-1 team)** — abandoned the RL/CNN StochasticGoose approach entirely; now an LLM-in-a-REPL harness. Frame observations are exposed to the LLM as both image and text-encoded Python variables; the model calls tools / evaluates pre-built helper functions inside a Python interpreter loop rather than emitting raw actions. Context is kept small via automatic oldest-message eviction (explicitly named as their weakest point). Model: "Qwen 3.6 27B FP8" as primary, GPT-5.4 for comparison. Their own framing: harness/cost-efficiency beats raw model capability — they got results "an order of magnitude cheaper" than heavier approaches, and note performance is "heavily dependent on model capability, not harness design" beyond a point.
   Source: [Duck Harness: Winning Solution for ARC-AGI-3 Milestone 1 — Tufa Labs](https://tufalabs.ai/research/duck-harness/)

2. **Blind Squirrel (Will Dick, preview-competition 2nd place, 6.71%)** — deterministic **state-graph** agent: stores every (state, action) → next-state transition ever seen, assumes the game is deterministic, and **prunes actions known to loop or produce no change**. Layers on a rules-based valid-action filter plus a small ResNet18 action-value model trained online, retrained every time a new milestone (deeper level) is reached, to rank (state, action) pairs by expected value toward the frontier.
   Source: [GitHub — wd13ca/ARC-AGI-3-Agents (2nd place)](https://github.com/wd13ca/ARC-AGI-3-Agents)

3. **"Explore It Till You Solve It" (dolphin-in-a-coma, preview 3rd place)** — explore-then-commit strategy, code public.
   Source: [GitHub — dolphin-in-a-coma/arc-agi-3-just-explore](https://github.com/dolphin-in-a-coma/arc-agi-3-just-explore)

4. **Graph-Based Exploration (Rudakov, Shock, Cowley — University of Helsinki, AAAI-2026 workshop paper)** — training-free: segments frames into visual components, prioritizes actions by visual salience, maintains a directed graph of explored states, and always walks the shortest path toward the nearest **untested** state-action pair (frontier-first exploration, not just avoid-repeats). Reported result: solved a median of 30/52 levels across 6 games, but the authors flag it scales poorly — cost grows with state-space size, so it degrades on games with large/continuous-feeling state spaces.
   Source: [arXiv 2512.24156](https://arxiv.org/pdf/2512.24156)

5. **Executable World Models (Sergey Rodionov, SingularityNET, AGI-2026)** — the most complete/quantified academic approach found. A coding agent maintains an **executable Python world model** of each game, verifies that model against every new observation, and — notably — actively **refactors the model toward a simpler form** (explicit MDL/Occam's-razor bias) whenever it still explains the data, then **plans through the model** (mentally simulates) before emitting a real action, instead of acting reactively frame-by-frame. Fully game-agnostic prompts/controller (no per-game hardcoding). On the 25 public games: GPT-5.5 fully solved 15/25 games, mean per-game RHAE 58.12%; GPT-5.4 solved 8/25, mean RHAE 41.29%. This is the single highest quantified transferable number in the research I found.
   Source: [arXiv 2605.05138](https://arxiv.org/pdf/2605.05138)

6. **Explore Before You Solve (Liew Keong Han)** — theory paper, reframes RHAE's square-of-ratio as a second-order penalty for deviating from a Speed/Depth Pareto frontier (action-efficiency vs information-gain-per-action). Useful mental model, not a shipped agent. Code: [github.com/farmountain/aera-arc3-paper](https://github.com/farmountain/aera-arc3-paper) (CC0). Source: [arXiv 2605.25931](https://arxiv.org/pdf/2605.25931)

**Daniel Franzen (named top-5 team) — prior ARC-AGI-2 style**: his known public method ("Product of Experts with LLMs") uses task-specific data augmentation through training/generation/scoring, a depth-first search over an LLM's candidate completions, and uses the LLM's own output token probabilities as a *scorer* to rank candidates (not just a generator) — got 71.6% on ARC-AGI-2's public eval set at ~2¢/task. Source: [arXiv 2505.07859](https://arxiv.org/html/2505.07859v1). **Caveat**: this is a static input→output grid transform method for ARC-AGI-1/2 (offline supervised puzzle-solving), not an interactive game-playing loop — I could NOT find any ARC-AGI-3-specific writeup from Franzen naming his current Kaggle approach; whether/how he ported the DFS+scorer idea to the interactive setting is **NOT FOUND**, flagging this as a stylistic prior only, not confirmed transfer.

**Caveat on all "top team" attribution**: Kaggle usernames `cstl`, `Lord Han Solo`, `rellik13`, `Tanaka Ai24` returned **NOT FOUND** in web search and the Kaggle leaderboard/discussion pages are JS-rendered and returned only page titles to my fetch tool (no body content) — I could not confirm which of the above techniques (if any) map to those specific handles. Everything in this section is "top public technique," not "confirmed technique of team X."

---

## Q3 — Concrete levers people report working

**A. Preserve reasoning/hypothesis state across turns, not just the action log** — OpenAI reports that their harness was dropping the model's private reasoning after each action, leaving only a bare move-log + short notes; turning on "retained reasoning" + "compaction" (already shipped in ChatGPT/Codex, exposed as API settings) took GPT-5.6 Sol from 13.3% → 38.3% (2.9x) on the public task set, while cutting output tokens 6x. Their own framing: "performance is a function of model plus product, not just the model." Directly transferable idea even without their exact API settings: don't let your harness collapse "why I took action N" down to just "action N" — keep the *hypothesis* the action was testing, not only its outcome.
Source: [OpenAI — How enabling two settings tripled our scores on ARC-AGI-3](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/) (confirmed via [Hacker News thread](https://news.ycombinator.com/item?id=49104184) and [explainx.ai summary](https://explainx.ai/blog/openai-arc-agi-3-retained-reasoning-compaction-july-2026); underlying OpenAI page itself 403'd my fetch tool, so this is search-snippet sourced, not full-text verified — treat percentages as reported-by-secondary-source, not primary-quoted).

**B. Deduplicate/prune the state-action space (Blind Squirrel, Graph-Based Exploration)** — assume determinism, cache every (state, action)→next-state transition seen, and hard-avoid actions already known to loop or no-op. This is cheap, well-attested twice independently (2nd-place preview finisher + a separate academic paper), and directly addresses the documented core weakness (Q1) of naive/RL exploration wasting actions on known-useless moves.
Sources: [wd13ca/ARC-AGI-3-Agents](https://github.com/wd13ca/ARC-AGI-3-Agents), [arXiv 2512.24156](https://arxiv.org/pdf/2512.24156)

**C. Explicit world-model + plan-before-acting, with a simplicity bias on the model itself** — the Executable World Models paper is the best-quantified single lever found (mean RHAE 58% vs the field's near-zero-to-low-single-digit baselines). Concretely: build/maintain a small program that predicts next-frame-given-action, verify it against every observation, prefer the *simpler* program that still fits (Occam bias), and simulate candidate actions through that model before spending a real action on the environment. This is architecturally the opposite of StochasticGoose (reactive, no explicit model) and is consistent with the "explore briefly then execute" human pattern named in the ARC Prize's own retro.
Sources: [arXiv 2605.05138](https://arxiv.org/pdf/2605.05138), [ARC-AGI-3 Preview: 30-Day Learnings](https://arcprize.org/blog/arc-agi-3-preview-30-day-learnings)

**D. Scoring-formula mechanics — confirmed structure, exploit implications:**
- Per-level score = `(human_baseline_actions / ai_actions)²`, capped at **1.15x** if you beat the human baseline. This is a *quadratic* efficiency penalty — using 2x the human's actions gives you only 25% credit on that level, not 50%. Source: [ARC-AGI-3 Scoring Methodology](https://docs.arcprize.org/methodology)
- Human baseline = the **upper-median** human by fewest actions (not average, not fastest) — so the bar is "a typical careful human," not a speedrunner.
- Per-game score = weighted average of per-level scores using the **1-indexed level number as weight** — later/harder levels are worth more per-level than early ones.
- **Completion is a hard ceiling**: unsolved levels count zero in the numerator but still count in the denominator of that weighted average — so a game where you clear 4/5 levels caps out around 66.7% even if the 4 you did clear were perfectly efficient. Implication for us: **prioritize reaching/clearing every level over polishing efficiency on levels you already clear** — an unsolved level anywhere in a game's ladder taxes the whole game's score more than an inefficient-but-solved level does.
- The **"240s/game clock"** and any hidden efficiency-exploit mechanism named in the task prompt is **NOT FOUND** anywhere in the official methodology doc or the ARC-AGI-3 rules doc I fetched — the docs describe an *action*-based (not time-based) efficiency metric with no stated wall-clock-per-game limit. Treat the 240s figure as **unverified / possibly from a different competition year or a Kaggle-infra execution limit rather than a scoring-relevant per-game clock** — flagging per anti-goals, not guessing further.
  Source checked: [ARC-AGI-3 Scoring Methodology](https://docs.arcprize.org/methodology), [ARC Prize 2026 Docs](https://docs.arcprize.org/arc-prize-2026)

**E. Avoid pure brute-force / random-with-priors as your main strategy at scale** — explicitly named in the preview retro as a trap: several preview games *could* be brute-forced, which pushed some developers to under-invest in real strategy, and that approach doesn't generalize to the 110-hidden-game private eval. Source: [30-Day Learnings](https://arcprize.org/blog/arc-agi-3-preview-30-day-learnings)

---

## Q4 — Submission/runtime pitfalls

Confirmed, from official docs (not forum-sourced — the Kaggle discussion pages are JS-rendered and unreadable by my fetch tool, so specific forum bug reports are **NOT FOUND**, only the official constraints below):

- **No internet access during evaluation** — rules out calling hosted LLM APIs (GPT/Claude/Gemini) inside the actual scored run; must be a self-contained model/weights or a from-scratch policy. Source: [ARC Prize 2026 Docs](https://docs.arcprize.org/arc-prize-2026)
- **Compute**: T4 GPU is the default accelerator (matches the official sample submission); CPU, P100, and RTX 6000 are also available. RTX 6000 is explicitly called out as **reserved for ARC-AGI-3 notebooks specifically** but **burns Kaggle GPU quota faster** than the other options — a quota-budget tradeoff to watch across your 5 daily submissions. Source: [kaggle-growth-lab README](https://github.com/Reasonofmoon/kaggle-growth-lab/blob/main/competitions/arc-prize-2026-arc-agi-3/README.md)
- **Two-phase run**: Kaggle first does a "Save & Run All" validation pass that must execute error-free before the real scoring pass triggers — a submission that only fails deep into a long run (not just at parse/import time) risks burning a full validation cycle before you find out. Source: [kaggle-growth-lab README](https://github.com/Reasonofmoon/kaggle-growth-lab/blob/main/competitions/arc-prize-2026-arc-agi-3/README.md)
- **Daily submission cap = 5, team size cap = 8.** Source: [ARC Prize 2026 Docs](https://docs.arcprize.org/arc-prize-2026)
- Grids are up to 64x64 with integer cell values 0–15, delivered as JSON frames; action semantics are **not documented per-game** and must be inferred at runtime (this is by design, not a bug). Source: [ARC Prize 2026 Docs](https://docs.arcprize.org/arc-prize-2026)
- Specific memory-limit / OOM / mid-run-death forum threads: **NOT FOUND** — my search and fetch tools could not retrieve Kaggle discussion-thread bodies (JS-rendered SPA, fetch returned page title only). If this matters, it needs a logged-in/JS-capable pass over `kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion`, which is out of scope for this read-only sweep.

---

## Ranked actionable levers for us (0.11 → target 1.5+)

1. **State-action dedup / transition cache (Blind Squirrel-style)** — *What*: hash each observed state, cache (state, action)→result, hard-skip actions already known to no-op or loop. *Expected impact*: high — directly attacks the exact weakness (wasted actions on known-useless moves) that the ARC Prize retro names as the #1 gap between AI and human play, and it's the cheapest lever on this list to build. *Local-verifiability*: fully local — replay any of our existing game logs, count how many actions were repeats of already-seen (state,action) pairs; that count is a direct, offline-measurable ceiling on savings before touching Kaggle at all.

2. **Explicit lightweight world-model + plan-before-act** — *What*: instead of reacting frame-by-frame, maintain a small predictive model per game (even a simple learned transition function, not necessarily an LLM-authored program), simulate 1–2 candidate actions through it, pick the best-predicted one. *Expected impact*: highest quantified result in the literature (58% mean RHAE vs near-zero baselines) — but it's the most implementation-effort item here. *Local-verifiability*: testable per-game offline against our own recorded episodes — does the model's next-frame prediction match the real next frame at improving accuracy over training? That's a clean local metric before ever burning a submission.

3. **Completion-first sequencing, not efficiency-first** — *What*: given the scoring's hard completion ceiling (unsolved levels count 0 but still divide the weighted average), restructure any per-game budget/retry logic to bias toward *reaching* every level at all, even sloppily, over polishing action-efficiency on levels already cleared. *Expected impact*: medium-high and nearly free — it's a scheduling/priority change, not new capability. *Local-verifiability*: re-score our own past runs against the documented formula (`(human_baseline/ai_actions)² weighted by level-index, zero for unsolved`) offline — compare "what we'd have scored if we'd spent the same total actions completion-first vs efficiency-first" on logged episodes.

4. **Preserve hypothesis/reasoning context across actions, not just the action log** — *What*: whatever memory/context our agent keeps between actions, make sure it retains *why* a past action was taken (the hypothesis being tested) and not merely *what* action was taken and what happened. *Expected impact*: OpenAI's own reported 2.9x from this class of change is the largest single number in this research (though sourced secondhand — see caveat in Q3-A). *Local-verifiability*: A/B on our own agent — run N games with hypothesis-context retained vs stripped, compare actions-to-solve; fully offline/local, no Kaggle submission needed.

5. **Cross-check against the 30-day retro's named failure mode before scaling anything up** — *What*: before investing in a bigger model or fancier search, verify our agent isn't stuck in the specific documented trap ("explores fine, can't convert exploration into a strategy" / relies on brute-force that won't generalize past a handful of games). *Expected impact*: lower direct-score impact but highest risk-mitigation — this is a sanity check, not a build item, and cheap to run before the other four. *Local-verifiability*: on our existing per-game logs, check whether action count scales roughly linearly with grid complexity/level depth (brute-force signature) vs plateauing after a short exploration phase (strategy signature) — a single offline pass over logs already on disk.

---

### Sources index (all fetched/searched 2026-08-18)
- https://arxiv.org/html/2603.24621v1 (ARC-AGI-3 technical report)
- https://tufalabs.ai/research/duck-harness/
- https://github.com/wd13ca/ARC-AGI-3-Agents
- https://github.com/dolphin-in-a-coma/arc-agi-3-just-explore
- https://arxiv.org/pdf/2512.24156
- https://arxiv.org/pdf/2605.05138
- https://arxiv.org/pdf/2605.25931
- https://arxiv.org/html/2505.07859v1
- https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/ (secondary-sourced, see caveat)
- https://news.ycombinator.com/item?id=49104184
- https://docs.arcprize.org/methodology
- https://docs.arcprize.org/arc-prize-2026
- https://arcprize.org/blog/arc-agi-3-preview-30-day-learnings
- https://www.kaggle.com/code/inversion/arc3-sample-submission-stochastic-goose
- https://medium.com/@ccro8990/the-official-live-leaderboard-for-the-arc-agi-3-machine-learning-competition-hosted-on-kaggle-part-06dbe491c8dc
- https://github.com/Reasonofmoon/kaggle-growth-lab/blob/main/competitions/arc-prize-2026-arc-agi-3/README.md
