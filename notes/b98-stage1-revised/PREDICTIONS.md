# B98 stage 1 on the REVISED bar — DRAFT, not registered

Status: **draft for the owner's review, 2026-09-27.** Nothing below has been run and no compile call has been made.
It becomes the registration only when committed unchanged after review; every number that decides a verdict is
fixed here, before any output exists.

## What this stage has to show

MAP B98 (revised 2026-09-24) passes stage 1 only on all four clauses:

1. **Held out by construction**: the predictor commits before the stored outcome is read, and is scored only on
   transitions whose `(level, board, action)` did not appear earlier in the same run.
2. **Availability**: the compiled hypothesis emits a prediction on **≥ 30 %** of those decisions (B19's lookup reached
   9.0 %).
3. **Accuracy on what it emits** beats the majority-class null on the SAME rows, **tested**, not compared with R31's
   corpus-wide 98.1 %.
4. **≥ 12 games** contribute, **no state cloning**.

The old-bar stage 1 (peer run 2026-09-24, branch `b98-stage01-artifacts` @ `6400779`) did not reach clause 2 at
all: its wall was COMPILE — 5 of 33 judged-checkable sentences compiled faithfully from text, because the model names
objects (*the piece*, *the block*) rather than colours and cells. The row says any stage 1 under the new bar needs a
**board-grounded compile step, registered as a new test**. That is this document's one new mechanism.

## Data (frozen)

- **Runs**: B81 controls only (the arm under test is the harness; a treated run would move the text). Primary:
  `sahasawatt/thui-b103-ctl-full25-r1` v1 (B81 + an inert counting wrapper, COMPLETE 2026-09-27, 25 games). Its
  `artifacts/<game>_p0_events.jsonl` carry `board_ascii` and `board_changed` on every `action` event (probed on ls20:
  158 action / 37 analysis / 1 initial events). Replication run, read only after the primary verdict: a second
  banked B81 control, named before the primary is read.
- **Transitions**: exactly `stage1/SPEC.md`'s definition on the peer branch (before = preceding `initial`/`action`
  board, skip after `level_completed` / `game_over`). No state cloning: only stored boards are read.
- **Hypothesis text**: assistant-visible text and THINKING text in `analysis` events, extracted by the peer's
  `stage0_extract.py` (unchanged, recall 188/188 on its own control). ⚠️ One `analysis_step` can hold analysis rows on
  BOTH sides of its actions (workspace CLAUDE.md: the shape is `[analysis]* action* [analysis]`), so **a sentence is
  usable for a decision only if its row precedes that decision's action row in FILE order** — never by
  `analysis_step`.

## Held-out decisions (clause 1)

A decision = one transition whose key `(level, board_ascii_before, action_display)` has not occurred earlier in the
same game's file. Everything else is excluded before scoring. Reported: held-out count per game, and the excluded
share (B19 puts exact repeats at ~4 %, so most decisions should survive — a much smaller survivor count is itself a
finding to report, not to tune).

## Board-grounded compile (the new mechanism)

- **Input per sentence**: the sentence, the game id and level, and the board at the moment it was written — the
  `after` board of the last `action` row before the sentence in file order (the `initial` board if none).
- **Output**: one hypothesis in the peer's DSL (`stage1/SPEC.md`: action + target colour/region + effect), or
  `NONE` when the sentence states no checkable transition rule. The compiler resolves *the piece* to a colour and
  region using the board; it may not read any later row.
- **Compiler**: one fixed prompt and one fixed model, both committed under `notes/b98-stage1-revised/` before the
  first call. Model: `codex exec --sandbox read-only` (0 Claude tokens) unless the owner names another.
- **Scope: RULES only, by a mechanical filter.** Compiling every candidate cannot be afforded live (see the ceiling
  below: 326 candidates/game leaves ~31 generated tokens each), so only sentences that state a GENERAL rule are
  compiled. A stage-0 candidate is a rule iff, case-insensitively, it contains at least one cue from this fixed list:
  `always`, `every time`, `each time`, `whenever`, `any time`, `every`, `each`, `will`, `causes`, `makes`,
  `always moves`, `moves by`, `rule`, `means that`, `means`. Nothing else decides membership — no judge, no LLM.
  Controls, run before the filter touches the primary: the stage-0 LEDGER's rule example ("clicking (23,61) made
  M(23,55) disappear" is an OBSERVATION and must be rejected), a synthetic rule ("pressing LEFT always moves the
  yellow block 3 cells left" must pass), and the rule share on the peer's B99 sample must land within ×2 of its
  judged 10 / 96 — outside that band the filter is VOID-as-instrument and is revised and re-registered before use.
- **Budget**: the filtered rule sentences, deduplicated per game, **capped at 60 per game by even spacing in file
  order** (≤ 1,500 compile calls total). The cap and the spacing rule are fixed here so no sentence is chosen after
  seeing its effect.

## Cost ceiling (registered number, derivation shown)

B82 died on the live cost of exactly this step, so affordability is graded here, not deferred to stage 2.

1. **Live budget, measured.** `thui-b103-ctl-full25-r1` (a B81 control, KV 7 GiB / MTP 0 / seqs 28, full clock),
   `benchmark.json`, `game_runs[*].history[*].generated_tokens` summed per game: **median 100,066 generated tokens
   per game** over the 7,920 s clock (25 games, run total 2,428,876).
2. **Overhead share, CHOSEN, not measured: 10 %.** Live compilation may add at most one tenth of what the model
   already generates in a game. A larger share would be paid out of the same decode capacity B87 showed is the
   binder, so 10 % is a deliberate limit, not a derived one.
3. **Per-game ceiling: 0.10 × 100,066 = 10,007 generated tokens per game spent on compiling.**
4. **Implied per-hypothesis figure, at the rule rate the stage-0 sample suggests**: 326 candidates/game (8,146 / 25
   on the B99 run) × 10 / 96 judged rules ≈ 34 rules/game → **≈ 294 generated tokens per compiled hypothesis**.
   This is illustration; the graded quantity is the per-game one in (3).

**Graded:** projected live compile cost per game = (rule sentences per game in the primary run, before the 60 cap)
× (mean generated tokens per compile call, measured on this stage's calls). **UNAFFORDABLE iff its median over games
exceeds 10,007.** Input tokens (sentence + 64×64 board + prompt, ~1,400–2,000 for the board alone) are MEASURED AND
REPORTED, not graded: the banked `benchmark.json` carries `uncached_input_tokens = 0` on this chassis, so no
prompt-token budget exists to derive a ceiling from, and inventing one would be a number with no source.

## The predictor

At each held-out decision, the active hypotheses are every compiled hypothesis from the same game and level whose
sentence precedes the decision in file order. A hypothesis **emits** a prediction when its action matches the
decision's action (SPEC matching rules) and the checker's per-transition verdict on the BEFORE board would not be
`na` — decided from the before board alone. When several emit, the most recent sentence wins; ties are impossible
because file order is total. The outcome is read only after the prediction is fixed: the checker's `support` /
`contradict` on the stored AFTER board.

## Verdict (all four, per the row)

- **(i)** held out: satisfied by construction above; VOID if any scored decision's key occurs earlier in its game.
- **(ii) availability** = emitting held-out decisions / held-out decisions, over all games pooled. **PASS ≥ 0.30.**
  Anything ≤ 0.12 refutes the premise (a compiled rule generalises no better than B19's lookup) rather than this
  compiler.
- **(iii) accuracy**: on the emitting rows, the predictor's implied `board_changed` (false for `no_change`, true for
  every other effect) is scored against the stored `board_changed`, and compared with the majority-class null
  **on those same rows**. One-sided exact binomial test of the predictor's correct count against the null rate:
  **PASS if p < 0.05.** Full-effect support rate (support / (support + contradict)) is reported beside it and
  not graded.
- **(iv)** **≥ 12 of 25 games** contribute ≥ 1 emitting held-out decision.
- **Teeth control**: the same pipeline with each hypothesis's game-level assignment shuffled across games (seeded,
  fixed here: 20260927) must NOT pass (iii). A shuffled predictor that beats the null means the null is too weak.

### The verdict partition — evaluated in this order, first match wins, every run lands in exactly one

| # | outcome | fires when | consequence |
|---|---|---|---|
| 1 | **VOID** | any scored decision's key occurs earlier in its game (clause i broken), OR the rule filter fails its controls, OR the teeth control passes (iii) | nothing read; fix the instrument, re-register, re-run |
| 2 | **REFUTED-PREMISE** | availability (ii) ≤ 0.12 | B98 closes: a compiled rule generalises no better than B19's lookup |
| 3 | **FAIL** | any of (ii) < 0.30, (iii) p ≥ 0.05, (iv) < 12 games | B98 closes at stage 1 under the row's kill rule |
| 4 | **PASS-UNAFFORDABLE** | (i)–(iv) all pass AND the graded compile cost's median > 10,007 generated tokens/game | recorded; stage 2 does NOT start |
| 5 | **PASS** | (i)–(iv) all pass AND that median ≤ 10,007 | licenses defining stage 2 (below) |

Rows 2 and 3 cannot both claim a run: row 2 is tested first, and 0.12 < 0.30. Rows 4 and 5 split exactly on the
one graded number. A run the table does not reach cannot exist: rows 3–5 together cover every combination of
(ii)–(iv) and cost once rows 1–2 have not fired.

## What a PASS licenses — and does not

It licenses defining stage 2 against the terms already sent to Watchara on 2026-09-27 (relay `01M3H5GR…`):
plan-search games = the games whose own availability is ≥ 30 % in THIS run, frozen as a list before any GPU;
3× human actions per LEVEL as a cap. It says nothing about score: every in-chassis lever so far read inside hidden
noise.

## Known confounds, carried

- The compiler sees the board, so it can write a rule the model never meant. The grounded hypothesis is the
  COMPILER's reading of the model's words; a PASS proves compilable availability, not that the model held the rule.
- One primary run: per-game availability is n = 1 per game, and the replication run is the only guard.
- The extractor keys on action tokens and effect verbs, so rules stated without them are invisible (the same bias
  the stage-0 PASS was measured under).

## Review decisions (Watchara, relay `01M3H6W1…`, 2026-09-27)

- Compiler = codex; 60 sentences/game with a hard cap of ≤ 1,500 calls — accepted as drafted.
- PASS-UNAFFORDABLE gets a numeric ceiling now — the section above.
- Verdict clauses must partition with no undefined case — the table above.
- **Still open, and the only thing between this draft and registration:** the replication run. Rule from the review:
  whichever of `sahasawatt/thui-b104-ctl-full25-r2` and `yocybercode/thui-b105-ctl-full25-r1` is COMPLETE first,
  after checking its events carry `board_ascii` and `board_changed` exactly as the primary's do; named here before
  the primary is read.
