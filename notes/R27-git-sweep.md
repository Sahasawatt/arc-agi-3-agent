# The top-5 git sweep — nothing public above us, and two calibration points below

2026-08-23. Asked directly: can we see what the top 5 run, on GitHub?

## The direct answer is no

- Kaggle usernames of the top 5 (`gatamaz`,`tehnar` = cstl 3.57; `lordhansolo` 2.76;
  `saltb0x` 2.73; `abelincoln1865` 2.72) match **no GitHub repos** in a 352-result sweep of
  arc-agi-3 repositories.
- **Tufalabs/duck-harness's last commit is 2026-07-01** — Milestone-1 era. Whatever took
  Tufa from ~1.6 to 3.04 was never published. R22's open lead ("walk their commits") closes
  empty.
- `saltb0x` (rank 4) is the same account whose Qwen3.8 dataset mirror we saw — he publishes
  weights, not code.

## Two public repos that calibrate the landscape

**`jinbowang1/arc-prize-2026`** — pure search, no LLM. Semantic state tuples
`(grid, shape, color, energy)`, reverse-BFS offline model, staged solving. **Fully clears
six public games at the 115 cap** (ls20 7/7 at 335 actions vs baseline 776; tr87, ft09,
cd82, sc25 all capped; sb26 8/8 at 100.00), verified on fresh env reruns. And **zero Kaggle
results, by their own admission**: scoring runs with `environments_dir=""` — no game source
— so the offline model that powers all of it cannot exist there. Full wins ARE achievable
on public games (banking's precondition), but only by a method the competition's scoring
environment structurally excludes.

**`BDR-Pro/arc-prize-2026-arc-agi-3`** — the v17 idea built for real (learned transition
model, volatility-masked hashing, object-centric nav), 73 versions of notes. Local 0.36 →
**Kaggle 0.26**. A serious pure-algorithm agent lands 6x below our Duck baseline, and their
own conclusions repeat ours: *"budget/levels are a dead end"* (our v14/v20/v21 axis), plus
one we had not named — *"nav displaces productive stumbling"*.

## What this settles

The LLM-harness family is the right family (pure-algo public ceiling on the hidden set is
~0.26), the top teams' actual edge is not public anywhere, and the only attributed,
unmeasured lever left is the rank-21 team's prompt work — which v22 now runs (their
PYTHON_ADDENDUM ported verbatim by AST extraction, both import bindings patched, teeth
in-kernel; their effort flag deliberately left out after v21 measured it WORSE).

⚠️ Worth recording: the v22 builder's first version tripped its own guard —
`assert "reasoning_effort" not in cell12` matched the provenance COMMENT explaining why the
flag was excluded. Same lesson as v16's `'fp8'` assert: a negative assert must target the
functional token (`LOCAL_ANALYZER_REASONING_EFFORT`, `build_chat_payload`), never a word
that legitimate prose about the exclusion will contain.
