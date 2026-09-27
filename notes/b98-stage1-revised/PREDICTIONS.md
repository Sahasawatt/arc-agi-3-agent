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
- **Budget**: sentences are the stage-0 extractor's candidates, deduplicated per game, **capped at 60 per game by
  even spacing in file order** (≤ 1,500 calls total). The cap and the spacing rule are fixed here so no sentence is
  chosen after seeing its effect.
- **Cost is reported as a number, never graded here**: tokens per compiled hypothesis and per game. B82 died on the
  live cost of exactly this step. A stage-1 PASS with a per-hypothesis cost the live harness cannot pay is recorded
  as PASS-UNAFFORDABLE, and stage 2 does not start on it.

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
- **Teeth control, VOID if it fails**: the same pipeline with each hypothesis's game-level assignment shuffled
  across games (seeded, fixed here: 20260927) must NOT pass (iii). A shuffled predictor that beats the null means
  the null is too weak, and nothing above is read.

Stage 1 **PASS** = (i)–(iv) all pass and the teeth control does not. Anything else is FAIL, and B98 closes at
stage 1 under the row's kill rule.

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

## Open for the owner before this is registered

1. Replication run: which banked B81 control.
2. Compiler model (default codex, 0 Claude tokens) and whether 60 sentences/game is the right cap.
3. Whether PASS-UNAFFORDABLE should need a numeric ceiling (tokens per hypothesis) written here, or be judged at
   stage 2.
