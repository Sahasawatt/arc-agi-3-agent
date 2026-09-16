# ARC-AGI-3 2026 Kaggle — who is on top and how (as of 2026-09-15)

## A note on source reliability before anything else

Kaggle's leaderboard and discussion pages are JavaScript-rendered. Every attempt in this research to fetch them non-interactively returned only the page title, with no team/score/discussion data extractable ([kaggle.com/.../leaderboard](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/leaderboard)). This means **the specific identities and scores of the current Kaggle top 5 could not be independently confirmed by this research**, and neither could any of the Kaggle discussion-thread quotes attributed to individual competitors. Where the report below states something as fact, it is backed by a source that could actually be fetched and read (arcprize.org, tufalabs.ai, GitHub, HuggingFace, benchlm.ai). Where it can't be, that is stated explicitly rather than presented as settled.

---

## 1. Leaderboard top 5 — **UNCONFIRMED reading, not independently verified**

A public leaderboard reading was reported for 2026-09-15, but this research's own attempt to reproduce it against the live Kaggle page failed (JS-rendered page, no rows extractable). The table below is therefore an **unconfirmed snapshot**, not a verified fact:

| Rank | Team | Score | Entries | Source (unconfirmed) |
|---|---|---|---|---|
| 1 | Tufa Labs | 18.81 | 137 | [Kaggle leaderboard](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/leaderboard) (unconfirmed) |
| 2 | Ebi | 8.68 | 16 | same (unconfirmed) |
| 3 | Lord Han Solo | 8.44 | 63 | same (unconfirmed) |
| 4 | NVARC3 | 8.40 | 10 | same (unconfirmed) |
| 5 | Third Intelligence | 8.21 | 47 | same (unconfirmed) |

What can and can't be said about this:

- **Tufa Labs' presence near the top is the one part with independent corroboration**, albeit weak: a secondary aggregator search result also names Tufa Labs as holding rank 1 on this competition, but that too is a low-confidence, non-primary-source summary, not a fetched leaderboard page.
- **Ebi, Lord Han Solo, Third Intelligence, and NVARC3 have no independently verifiable public technical writeups in this research.** No blog post, GitHub repo, or Kaggle notebook for any of these four could be located and confirmed.
- **NVARC3's identity as an Nvidia team is unconfirmed.** A claim that "NvARC3 = Nvidia Arc3," and a purported team-member pushback on a "wins via GPU access" accusation, both trace to Kaggle discussion content that could not be fetched or located by search — see the Unconfirmed section below.
- The leaderboard itself is described (in the same unconfirmed reading) as scored on only ~50% of test data, with final standings to be decided by the other, currently-hidden half — consistent with how Kaggle competitions of this shape normally work, but that specific sentence could not be located on the live page either.

**Bottom line: only Tufa Labs' technical approach is documented well enough to write about with confidence (see §2). The rest of the "top 5" is a name-and-number list this research could not stand behind.**

---

## 2. Per-team detail

### Tufa Labs — "Duck" harness (Milestone #1 winner; only team with a full public writeup)

- **Model**: Qwen 3.6 27B, FP8 quantization. ([tufalabs.ai](https://tufalabs.ai/research/duck-harness/))
- **Serving**: a local vLLM server, or alternatively OpenRouter, as the inference backend ([GitHub](https://github.com/Tufalabs/duck-harness)). No public source specifies anything beyond FP8 for the quantization scheme, and no mention of multi-token-prediction or speculative decoding appears on Tufa's own page.
- **Harness/search approach**: "agent writes code" — a minimal coding harness built around a Python REPL. The model perceives the board, calls helper functions, runs code, and takes an action, repeating the loop. It is explicitly the *only* Milestone #1 winner using this code-writing approach; the 2nd and 3rd place solutions instead have the model pick a JSON action directly. ([arcprize.org](https://arcprize.org/blog/arc-prize-2026-milestone-1))
- **Perception**: combines a rendered image, the raw ASCII grid, and a segmentation tool for zooming into regions — the model picks whichever representation fits the moment. ([arcprize.org](https://arcprize.org/blog/arc-prize-2026-milestone-1))
- **Context management**: "infinite play via eviction" — continuously removes the oldest messages while keeping the system prompt and recent history, allowing indefinite play length. ([arcprize.org](https://arcprize.org/blog/arc-prize-2026-milestone-1))
- **Design philosophy** (per ARC Prize's own characterization of the team): keep the harness lightweight and generic and let the model drive; hand-crafted tools actually *hurt* performance, and letting the model improvise worked better. Reported gains came from multimodality and better base models, not engineered tooling. ([arcprize.org](https://arcprize.org/blog/arc-prize-2026-milestone-1))
- **What's public**: full harness source, one complete benchmark run (25 official games × 20 passes), an interactive run viewer, and a Kaggle notebook demonstrating the milestone-winning submission, all on [GitHub](https://github.com/Tufalabs/duck-harness). A more detailed technical write-up is linked from a Kaggle discussion post, but that page could not be fetched in this research.
- **Reported scores**: 1.21% at the June 30 Milestone #1 cutoff (per [Tufa's own announcement](https://x.com/tufalabs/status/2072336849465417747)); a later, updated version of the harness reports a mean of 1.6002 ± 0.4475 across the 25 public games, described as an order of magnitude cheaper per game than the "Executable World Models" comparison agent ([tufalabs.ai](https://tufalabs.ai/research/duck-harness/)).
- **Team**: Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit, Michal Tešnar, and Stefano Viel ([tufalabs.ai](https://tufalabs.ai/research/duck-harness/)).
- Note: Tufa Labs' *earlier* ARC-AGI-3 Preview-competition entry, "StochasticGoose," was an unrelated CNN + reinforcement-learning agent with no LLM at all, and won that separate preview competition ([Medium](https://medium.com/@dries.epos/1st-place-in-the-arc-agi-3-agent-preview-competition-49263f6287db)). Whether its lead specifically evaporated on the harder full benchmark (as a possible reason Tufa moved to the LLM-based Duck harness) is unconfirmed.

### Reki (Kaggle: ruichardliu) — Milestone #1, 2nd place

- **Model**: Gemma-4-31B, run locally.
- **Harness/search approach**: vision-LLM-as-policy. Each turn it renders the recent game frames as labeled images, feeds them to the local model, and asks for a single JSON object per turn describing what changed, a short plan, and the next 1–4 actions. Built on the official ARC Prize GPT-OSS-120B template with the model swapped to Gemma-4-31B.
- Adds: reflection memory, a numpy click heuristic favoring small/rare-colored button-like shapes as a fallback, a "dead-signature" mechanism that stops clicking object types producing no change, and JSON self-repair with legal-action constraints.
- **What's public**: full solution notebook on [Kaggle](https://www.kaggle.com/code/ruichardliu/milestone1-2nd-solution).
- (Source for all of the above: [arcprize.org](https://arcprize.org/blog/arc-prize-2026-milestone-1))

### Md Boktiar Mahbub Murad — "forge" framework — Milestone #1, 3rd place

- **Model**: Gemma-4-31B, run locally, in a similar vision-to-JSON architecture to Reki's.
- **Harness/search approach**: wrapped in a profile-driven framework called "forge," with candidate-action generators and an arbiter for scoring/selecting actions — but the top-scoring configuration actually **disabled** all the extra machinery, i.e. the simplest config won. Also built on the official GPT-OSS-120B template.
- **What's public**: notebook on [Kaggle](https://www.kaggle.com/code/mbmmurad/arc-agi-3-lb-0-86-3rd-place-candidate-milestone), scoring a public-leaderboard 0.86.
- (Source: [arcprize.org](https://arcprize.org/blog/arc-prize-2026-milestone-1))

### NVIDIA "AVO" — a separate research system, not a Kaggle team submission

- Reports a 100.00 RHAE score across all 25 ARC-AGI-3 public environments (183 levels), using **Claude Opus 5** as its primary model, via a direct-interaction harness with persistent memory and supervisory intervention rather than an explicit world model. ([NVIDIA developer blog](https://developer.nvidia.com/blog/nvidia-avo-reaches-100-on-arc-agi-3-demonstrating-a-frontier-level-general-purpose-architecture-for-long-horizon-autonomous-agents/))
- This is **not the same thing** as the Kaggle competition, which bans internet access during evaluation and so cannot call a hosted model like Claude Opus 5 at all (see §3). AVO's 100.00 is a research-lab result under different rules, not a Kaggle leaderboard entry.

### Ebi, Lord Han Solo, Third Intelligence, NVARC3

No independently verifiable public source (blog, GitHub, Kaggle notebook) describing these teams' models, serving stack, or harness could be located in this research. Their presence in the leaderboard table above is unconfirmed (§1), and no further detail can responsibly be reported.

---

## 3. Cross-team patterns — what the documented leaders share

- **Small, dense, open-weight models run locally, not large hosted frontier models.** Every documented Milestone #1 winner (Tufa Labs, Reki, Murad) runs a ~27–31B-parameter open-weight model (Qwen 3.6 27B or Gemma-4-31B) on a single local GPU. This is a rule of the competition, not a preference: **internet access is disabled on all accelerated Kaggle sessions**, ruling out API calls to hosted models like GPT, Claude, or Gemini during evaluation. ([arcprize.org competition rules](https://arcprize.org/competitions/2026/arc-agi-3); [docs.arcprize.org](https://docs.arcprize.org/arc-prize-2026))
- **A shared serving pattern: one model instance loaded once, served to many concurrent game threads.** One independent public repo notes explicitly that because the harness framework plays roughly 110 games in concurrent threads, the model must be loaded once and served as a shared singleton (e.g. via vLLM) — loading a separate model per thread OOMs the GPU. ([GitHub: BDR-Pro](https://github.com/BDR-Pro/arc-prize-2026-arc-agi-3))
- **Both documented winning harness shapes converge on structured perception + a compact action format** — either a Python REPL over multimodal board perception (Tufa), or a single JSON object per turn from a rendered/labeled image (Reki, Murad) — built in two of three cases on the same official ARC Prize GPT-OSS-120B starter template.
- **Context/session management matters at this scale**: Tufa's "infinite play via eviction" (continuously drop oldest messages, keep system prompt + recent history) is the one documented long-horizon technique.
- **Hardware target clusters around Kaggle's offered RTX 6000 (g4-standard-48) accelerator**, described by Kaggle itself as "heavy ML... ARC-AGI-3 exclusive, burns GPU quota faster" — independent public repos (ARCangel, arcgames) explicitly size their model choice and KV-cache budget around a 96GB RTX PRO 6000. ([docs.arcprize.org](https://docs.arcprize.org/arc-prize-2026); [GitHub: sidhulyalkar/ARCangel](https://github.com/sidhulyalkar/ARCangel); [GitHub: adityav31121999/arcgames](https://github.com/adityav31121999/arcgames))
- **Everyone budgets against Kaggle's 9-hour runtime kill.** At least one public repo builds an explicit "tournament timeout budget monitor" for exactly this. ([GitHub: adityav31121999/arcgames](https://github.com/adityav31121999/arcgames))
- **Scoring rewards efficiency, not just completion**: the official metric is RHAE (Relative Human Action Efficiency) — `level_score = (human_baseline_actions / ai_actions)^2`, capped at 1.15× the human baseline, against the *upper-median* human's action count (not the fastest speedrunner), weighted toward later levels in a game's overall score. ([docs.arcprize.org/methodology](https://docs.arcprize.org/methodology))

---

## 4. What nobody at the documented top does

- **Nobody documented uses hand-built, game-specific tooling or an explicit world model as the primary driver.** Tufa Labs' own reported finding is that hand-crafted tools *hurt* the model, and that letting a general model improvise outperformed engineered scaffolding — the opposite of a heavily hand-tuned symbolic approach. ([arcprize.org](https://arcprize.org/blog/arc-prize-2026-milestone-1))
- **Nobody documented calls a hosted frontier API model during actual competition play** — this isn't a design choice but a hard competition rule (no internet access during evaluation), so approaches like NVIDIA AVO's use of Claude Opus 5 are structurally excluded from the Kaggle leaderboard entirely.
- **A pure no-LLM, programmatic/symbolic approach is explicitly a minority strategy, not a top one.** One independent repo author states plainly that "the top of the board is entirely LLM agents (a large open-weights model reasoning in Python each turn, served on GPU)," while describing their own project as a deliberate departure — using no LLM at runtime at all, via a learned transition/world model instead. ([GitHub: BDR-Pro](https://github.com/BDR-Pro/arc-prize-2026-arc-agi-3))
- **Nobody at the documented top runs a maximal/heavyweight decision-time search stack** — the one case where a framework's extra machinery (Murad's "forge" candidate-generation-plus-arbiter scoring) was tested, the *simplest* configuration with that machinery disabled scored highest.

---

## 5. Open questions and unreachable sources

- **The current top-5 identity itself (§1) is unconfirmed** — the Kaggle leaderboard page is JavaScript-rendered and could not be read by this research's tools. This is the single largest gap in this report.
- **Every Kaggle discussion-thread quote in the underlying research data is unconfirmed** for the same reason — including claims about NVARC3 being an Nvidia team, a purported team-member's pushback on "wins via GPU" accusations, a reported model progression from Qwen 3.6 → Qwen 3.8 → Qwen 3.8-Flash-next-NVFP4 among competitors, speculation linking a top-3 score jump to the public "Polyphony Agent" harness, and a report that one team tried "AVO style ideas" without beating their existing harness. None of this could be located via search or direct fetch, so none of it appears above as fact.
- **The ARC-AGI-3 official technical report PDF** could not be parsed by available tooling (binary/compressed content) — only its title, "ARC-AGI-3: A New Challenge for Frontier Agentic Intelligence," was recoverable. ([arcprize.org/media/ARC_AGI_3_Technical_Report.pdf](https://arcprize.org/media/ARC_AGI_3_Technical_Report.pdf))
- **OpenAI's own post claiming two harness settings roughly tripled their ARC-AGI-3 score** returned HTTP 403 on direct fetch; its existence and general thrust are corroborated by secondary search results, but exact figures are unconfirmed here. ([openai.com](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/))
- **Milestone Prize #2's exact closing mechanics beyond the September 30, 2026 date and prize amounts** (a final-submission deadline of November 2, 2026 and a winners-announcement date of December 4, 2026 were reported in the underlying research but not found on the fetched competition page) are unconfirmed.
- **A separate, non-Kaggle frontier-model benchmark** (BenchLM.ai) shows GPT-6 Astra leading ARC-AGI-3 among *hosted* models at 62.7%, ahead of Claude Opus 5 (30.2%) and GPT-5.6 Sol (7.8%) — confirmed as a real reading, but explicitly **not** the Kaggle open-weights competition, and not to be conflated with §1. A separately reported 99.9% figure for GPT-6 Astra is not a contradiction on closer reading: per ARC Prize's own reporting, 99.9% is Astra's score under OpenAI's own "Provider Adapter" harness (retaining hidden reasoning state between turns), while 62.7% is the same model's score under ARC Prize's provider-neutral "Standard" harness — both real, harness-dependent measurements of one model. ([benchlm.ai](https://benchlm.ai/benchmarks/arcagi3))

---

## 6. Unconfirmed claims (listed separately, per methodology — not used as fact above)

- Live leaderboard rows for Ebi, Lord Han Solo, NVARC3, Third Intelligence, and their exact scores/entry counts (§1).
- "NvARC3 = Nvidia Arc3" identification, attributed to a Kaggle user "Fususu."
- A purported NVARC3-team member ("CPMP") pushback on a GPU-access accusation.
- A reported community shift in model choice (Qwen 3.6 → 3.8 → 3.8-Flash-next-NVFP4) and associated large rank swings, attributed to "Scott Le Grand."
- Speculation linking a simultaneous top-3 score jump to the public "Polyphony Agent - ARC" harness, attributed to "Jakob Brüggen."
- A report that a team ("rfbr") tried "AVO style ideas" without beating their existing harness.
- Whether Tufa Labs' Preview-competition CNN+RL lead specifically "evaporated" on the harder non-preview games (the cited article was unreachable — 404).
- The exact final-submission (Nov 2, 2026) and winners-announcement (Dec 4, 2026) dates for the 2026 competition.
- Whether ARC-AGI-3 was built specifically by an "in-house ARC Prize Foundation game studio" (from an unparsable PDF; title only confirmed).

---
Provenance: hand-authored deep-research workflow wf_7e546c1b-2f7 (11 sonnet agents, 5 angles x search+verify + synth), 2026-09-15, ~2.0M subagent tokens, 400 s; verify stats {"upheld": 60, "refuted": 4, "unverified": 13}. Kaggle pages were JS-rendered and unreadable to the agents; the leaderboard check via the Kaggle API is appended below.

## Leaderboard check via the Kaggle API (this box's creds, 2026-09-15 ~13:50 local) -- CONFIRMS the agents' unconfirmed table

```
Next Page Token = CfDJ8OasvsPNS7VMiSwiBm2YVpP8IL_2J6ArvNR1LYMYU71iIMkCISG2JID34aGl14s1_WBz4N1gCX-wZIANj_0tC70
  teamId  teamName                submissionDate              score  
--------  ----------------------  --------------------------  -----  
15486995  Tufa Labs               2026-09-13 20:48:42.076000  18.81  
16584226  Ebi                     2026-09-13 21:46:23.626000  8.68   
16371045  Lord Han Solo           2026-09-14 19:08:38.016000  8.44   
15770880  NVARC3                  2026-09-14 16:45:31.253000  8.40   
15494232  Third Intelligence      2026-09-14 00:06:22.870000  8.21   
16384837  Daniel Franzen          2026-09-15 00:20:26.893000  7.63   
16364346  mostik.ai               2026-09-06 16:33:00.890000  7.51   
15506893  Mark Slavin             2026-09-14 00:01:43.153000  7.29   
16609552  Kyutai                  2026-09-14 19:25:56.543000  7.19   
16053779  Fususu                  2026-09-14 00:02:24.013000  6.91   
15823039  Tong Hui Kang           2026-09-14 16:15:56.730000  6.65   
```
Top 5 = Tufa Labs 18.81 (submitted 2026-09-13, +7.8 over its 11.04 of 09-13 morning), Ebi 8.68, Lord Han Solo 8.44, NVARC3 8.40,
Third Intelligence 8.21. 5th-place bar moved 7.63 -> 8.21 in one day (Daniel Franzen 7.63 is now 6th). Thuitanium 3.74.

## Public notebooks (kernels list --competition, by votes) -- what the mid-board actually runs
| notebook | votes | model | harness | serving |
|---|---|---|---|---|
| jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner | 312 | Qwen3.6-27B-FP8 | duck (June) | vLLM |
| foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b (LB-9, Aug 18) | 283 | **Qwen3.8-27B-FP8** (own repack) | **anim** bundle `jakobbrggen/taaf-kaggle-source-anim-20260807-anim` | `driessmit1/arc3-vllm-h100-wheelhouse-v3`, concurrency 28, 7920 s/game |
| wuliao0/duck-qwen3-8-anim-base (updated 09-15) | 235 | Qwen3.8-Flash-Next-NVFP4 (Keith's asset) | **anim** on Keith's fork | profile identical to ours: KV 5 GiB, seqs 8, MTP 3, cg32 |
| keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp (our base) | 160 | Qwen3.8-Flash-Next-NVFP4 | duck | kv5-bf16-mtp3-c8-cg32 |
| jakobbrggen/taaf-anim-arc-agi-3-solver (Aug 7) | 120 | Qwen3.6-27B-FP8 snapshot | anim (origin) | wheelhouse v3 |
Reading: the whole public mid-board is duck/anim + a Qwen3.x 27B-class model on vLLM; our chassis is the commodity. The top-4
non-Tufa entries (8.2-8.7) have no public artifact at all; Tufa's 18.81 is private (its last public notebook is the June milestone,
1.21). The agents' unconfirmed discussion claims (community move Qwen 3.6 -> 3.8 -> 3.8-Flash-next-NVFP4; "Polyphony/anim"
harness behind a top-3 jump) are consistent with the notebook census but still unverified. Pulled copies: scratchpad/pub-nb/.
