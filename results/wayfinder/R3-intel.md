# R3 Intel: What 2.5+ teams are doing that we aren't

Research date: 2026-08-19. Web research only (WebSearch/WebFetch), no code changes.
Kaggle's own leaderboard/discussion pages are client-side-rendered JS and returned empty/blocked
to every fetch attempt (WebFetch, r.jina.ai proxy) — see "What nobody discloses" for the
consequence. Everything below is reconstructed from Google-indexed snippets of those pages,
arcprize.org, GitHub, arXiv, and press coverage.

---

## 1. Milestone-1 winners (verified, June 30 2026 cutoff) — the only fully-disclosed cohort

These are the only ARC-AGI-3-Kaggle solutions with full public write-ups, because milestone
prize eligibility *requires* open-sourcing. Everyone currently sitting above milestone-1 scores
without a June 30 prize has no such obligation until Sept 30 (see §5).

| Place | Team | Score (semi-private) | Approach | Model | Sources |
|---|---|---|---|---|---|
| 1 | Tufa Labs, "The Duck" | 1.21 (official) / 1.6002 ±0.4475 mean on 25 public games | LLM writes/executes Python in a live REPL; game state exposed as Python variables; dual image+ASCII perception; "infinite play via eviction" (oldest messages dropped when context fills) | Qwen 3.6 27B FP8, local | [Tufa Labs write-up](https://tufalabs.ai/research/duck-harness/), [GitHub](https://github.com/Tufalabs/duck-harness), [Kaggle notebook](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner), [ARC Prize blog](https://arcprize.org/blog/arc-prize-2026-milestone-1) (2026-07-06) |
| 2 | Reki | (unlisted, 2nd) | Vision-LLM-as-policy: renders recent frames as labeled images → structured JSON plan; **running reflection memory refreshed every ~10 steps**; numpy click-heuristic biased toward button-like shapes; dead-signature detection to drop ineffective click types; JSON self-repair + legal-action constraints; plans 1-4 actions ahead | Gemma-4-31B, local | [Kaggle notebook](https://www.kaggle.com/code/ruichardliu/milestone1-2nd-solution), [ARC Prize blog](https://arcprize.org/blog/arc-prize-2026-milestone-1) |
| 3 | Md Boktiar Mahbub Murad, "forge" | (unlisted, 3rd) | Same vision-policy family as Reki but config-driven: multi-candidate action generation with a scoring arbiter, optional confidence-gated safety prompting for uncertain states, feature-toggle "profiles" | Gemma-4-31B, local | [Kaggle notebook](https://www.kaggle.com/code/mbmmurad/arc-agi-3-lb-0-86-3rd-place-candidate-milestone) |

**We are a fork of #1.** Our fork's public-set score was reportedly 2.41 (per your CONTEXT) before
dropping to 1.00 on the hidden set — worth comparing against Duck's own public→semi-private ratio:
1.6002 → 1.21, i.e. **~1.32x shrinkage**. Ours is **~2.41x shrinkage**, roughly double the
degradation the original Duck saw on its own public↔hidden split. That gap is itself a finding:
either our fork picked up public-game-specific behavior the base Duck didn't have, or the harness
regressed something Tufa's eviction/context logic was doing correctly. Worth a diff review before
adding new capability on top.

## 2. What beat the pure-LLM approach in the *preview* competition (pre-Kaggle, informs milestone-2 meta)

The July–August 2025 ARC-AGI-3 Preview (30 days, 3 public + 3 hidden envs) is the closest prior
data point to "what generalizes on a hidden set," and it's where StochasticGoose — Tufa's own
predecessor to the Duck — first placed 1st.

- **1st: StochasticGoose (Tufa Labs)** — 12.58% on preview. **Not an LLM.** CNN + lightweight RL
  predicting *which actions will change the frame*, biasing exploration toward those. When later
  run against the full official ARC-AGI-3 benchmark at launch, its score fell to **0.25%** — roughly
  frontier-LLM level — illustrating that a preview-tuned narrow model does not generalize to the
  full hidden game set. [ARC Prize 30-day learnings](https://arcprize.org/blog/arc-agi-3-preview-30-day-learnings) (undated, ~2025-08)
- **2nd: Blind Squirrel** — built an explicit **state graph from frames**, pruned actions that led
  to unproductive states, and reached meaningful progress using **~half the actions of the winner**
  (109K vs 256K) — i.e., worse at solving, but far more action-efficient, which under RHAE's squared
  efficiency term matters as much as raw completion. Same source as above.
- **Explicit finding from ARC Prize itself**: "some preview games were too friendly to random
  search" — i.e., naive exploration alone could clear some hidden environments, which is exactly
  the kind of confound the milestone/final scoring tries to design out with the 110-game hidden set
  and level-weighted scoring. Same source.

## 3. Published techniques with a plausible transfer path to our fork this week

Ranked by expected points delta, cheapest/most concrete first.

### 3a. Context compaction instead of eviction — **highest expected value, cheapest to try**
OpenAI reported a **13.3% → 38.3%** jump on the *public* ARC-AGI-3 set from exactly two harness
settings, no model change: (1) retaining reasoning state across turns instead of resetting it every
action, and (2) **summarizing evicted context instead of deleting it** (compaction vs. truncation).
[Context Studios analysis](https://www.contextstudios.ai/blog/arc-agi-3-measured-the-harness-not-just-the-model)
(undated, ~2026-08, citing OpenAI's own post which 403'd on fetch — could not independently verify
the exact numbers from OpenAI's page directly, only via this secondary source).

- Setting (1), "retained reasoning across turns," is an OpenAI Responses-API-specific feature
  (persisting internal reasoning tokens between tool calls) — **does not transfer** to a locally-run
  Qwen model in the way OpenAI implemented it, since we don't have that API's hidden-reasoning
  persistence mechanism.
- Setting (2), **compaction over truncation**, is architecture-agnostic and directly applicable: our
  fork inherits Duck's "evict oldest message" policy verbatim. Tufa's own write-up flags "context
  management" as an acknowledged weak point they didn't have time to fix
  ([tufalabs.ai/research/duck-harness](https://tufalabs.ai/research/duck-harness/)). Replacing
  hard eviction with an LLM- or rule-based summary of the evicted turns (what was tried, what state
  resulted, what's now known about the game's rules) is a harness-only change, no new model, and
  is the single most concrete "why not us" gap identified in this research pass.

### 3b. Explicit state-graph tracking with frontier-driven exploration
Two independent hidden-set-validated results point the same direction:
- **Graph-Based Exploration** (Rudakov, Shock, Cowley) — training-free: segments frames into
  components, builds a directed graph of explored states/transitions, and **prioritizes the action
  with the shortest path to an untested state-action pair**. Result: median 30/52 levels across
  6 preview games, **3rd place on the private leaderboard**, "substantially outperforming frontier
  LLM-based agents." [arXiv:2512.24156](https://arxiv.org/abs/2512.24156)
- **Blind Squirrel** (preview, 2nd place, §2 above) — same idea, cruder: state graph + pruning,
  half the actions of the winner.

Our fork inherits Duck's REPL/Python-variable state exposure but (per the write-up) does *not*
maintain a persistent explored-state graph across the session — the model has to re-derive what
it's already tried from context, which is exactly the kind of thing eviction destroys. A thin
graph layer (state hash → tried actions → resulting state hash) sitting outside the LLM context,
queryable via a REPL variable, is a moderate-size change with two papers' worth of hidden-set
evidence behind it.

### 3c. Executable/verified world model, refactored toward simplicity
Rodionov's coding-agent approach: the agent maintains an **executable Python world model**,
**verifies it against every prior observation**, and **refactors it toward simpler abstractions**
(an MDL/Occam's-razor bias) before planning through it. GPT-5.5 high-reasoning: 15/25 public games
fully solved, mean RHAE 58.12% (public only — "performance on the private validation set... remains
to be tested," so treat this as promising but unconfirmed on hidden data).
[arXiv:2605.05138](https://arxiv.org/abs/2605.05138)

This is conceptually adjacent to what Duck already does (Python-variable world state + REPL) but
adds two disciplines Duck's write-up doesn't mention: (i) an explicit verify-against-history step
before trusting a hypothesis, (ii) an explicit simplicity-bias refactor step. Both are prompt/loop
structure changes, not new infra — plausible to try, but note the public-only caveat above (§4) before
trusting the 58% number as representative of what we'd see on the 110 hidden games.

### 3d. Tiny-model exploration/verify/plan loop — lowest cost, lowest confidence
AERA (Liew Keong Han): explicit EXPLORE → VERIFY → PLAN phase structure with a formalized
Speed–Depth trade-off (a Pareto frontier between exploration breadth and reasoning depth, framed
against RHAE's quadratic action-efficiency penalty). Runs on **Qwen2.5-0.5B** — two orders of
magnitude smaller than Duck's 27B. RHAE=0.2116 (4/25) on public games with that tiny model; the
linked repo claims RHAE=0.30 on the **full 55-game private evaluation**.
[arXiv:2605.25931](https://arxiv.org/abs/2605.25931),
code: [github.com/farmountain/aera-arc3-paper](https://github.com/farmountain/aera-arc3-paper) (not independently verified — could not fetch repo contents in this pass)

Low raw score, but relevant because it's evidence the *phase structure* (explicit explore-then-verify-then-plan,
rather than one undifferentiated reasoning loop) buys something even at minimal model capacity —
worth reading their prompt/loop design even if we don't adopt the tiny model.

## 4. Public-vs-hidden gap calibration (for reading our own 2.41→1.00 drop)

- ARC Prize's own overfitting check: a **Public vs Semi-Private gap under ±15 percentage points**
  is "in good agreement" for ARC-AGI-3 (looser than ARC-AGI-2's ±10%, because the public demo is
  explicitly harder than semi-private by design).
  [ARC Prize verified testing policy](https://arcprize.org/policy)
- Verified (ARC-Prize-attested) frontier LLM performance on the **semi-private** set: 0.51% at
  March 2026 launch → 7.78% with GPT-5.6 Sol at max reasoning by July 2026.
  [Schema harness page via search snippet](https://schema-harness.github.io/)
- Schema (Zanette et al., Impossible Research) claims **~99% on the public set** with Claude Opus
  4.8/Fable 5, ~95% with GPT-5.6 Sol — via an executable-world-model harness (same family as §3c).
  **This is self-reported, not ARC-Prize-verified**, and the same source flags that "the 25 public
  games cannot distinguish legitimate intelligent exploration from trivial heuristics" — i.e., the
  99% number is widely read as evidence the *public set specifically* is gameable, not evidence the
  harness generalizes. [schema-harness.github.io](https://schema-harness.github.io/),
  [HN discussion](https://news.ycombinator.com/item?id=48935905)
- **Reading for our drop**: a ~99%-public / ~7.8%-verified-semi-private gap (>12x shrinkage) is the
  extreme "gamed the public set" end of the spectrum. Duck's own ~1.3x public→semi-private shrinkage
  is the "generalizes reasonably" end. Our fork's ~2.4x shrinkage sits meaningfully worse than Duck's
  own ratio but nowhere near the Schema-style extreme — consistent with "the fork regressed
  something in Duck's generalization-relevant logic (context/eviction, most likely per §3a)" rather
  than "the fork is overfit to the 25 public games" the way a from-scratch public-set-tuned harness
  would be.

## 5. What nobody discloses

- **Kaggle's leaderboard and discussion pages could not be read directly.** Both are fully
  client-rendered; every WebFetch attempt (direct, and via the r.jina.ai text-extraction proxy)
  returned only the page `<title>` with no table/thread content. This means **none of the specific
  current top-5 usernames' techniques (cstl, or whoever is 2nd–5th at 2.76/2.59/2.58/2.57) could be
  confirmed from primary sources in this pass** — everything above about "current leaders" is
  inference from milestone-1 (a different, older cohort) plus general-purpose technique papers, not
  a read of what the *current* #1–#5 are actually running. If you have Kaggle session cookies or can
  paste leaderboard/discussion HTML directly, that would close this gap.
- **No milestone-2 disclosure obligation until Sept 30 2026.** Milestone-1 prize winners had to
  open-source by the June 30 cutoff; anyone currently ahead of milestone-1 scores without having won
  a milestone-1 prize has **no incentive to publish anything until the Sept 30 deadline** — so the
  entire 6-week run-up to milestone-2 (roughly now through the deadline) is structurally the
  lowest-disclosure period of the competition. A leaderboard score of 3.57 today is not evidence a
  write-up exists or will exist soon.
- **Schema's 99%-public number is unverified by ARC Prize** and, per the discussion around it,
  possibly not meaningful as a generalization claim at all (see §4) — cited here as a data point
  about the public set's exploitability, not as a technique to copy.
- **Franzen/"the ARChitects" (ARC-AGI-1/2, test-time training + DFS + fine-tuned small models,
  53.5% private on ARC-AGI-1 in 2024) — no evidence found that this team or method has moved to
  ARC-AGI-3.** Their approach is built around each *task* shipping a handful of labeled
  input/output training examples that TTT fine-tunes on before inference. ARC-AGI-3 tasks ship no
  such training pairs at all — the agent has to discover the rules through interaction alone — so
  TTT-on-provided-examples has no obvious analog here, and DFS-over-candidate-programs likewise
  assumes a static input→output mapping ARC-AGI-3 doesn't have. Treat "does Franzen's method
  transfer" as **answered no by construction**, not as an open question needing more searching.
  NVARC's 2025 ARC-AGI-2 win (Sorokin/Puget, fine-tuned 4B + TTT + synthetic data, 27.64% public,
  $0.20/task) is the same story — same static-task assumption, same non-transfer.
- **Executable-world-model results (Schema, Rodionov) are reported almost exclusively on the public
  set.** Rodionov's paper explicitly states the private/hidden number "remains to be tested." Do not
  read the 58%/99% headline numbers as what you'd see on the 110 hidden games.
