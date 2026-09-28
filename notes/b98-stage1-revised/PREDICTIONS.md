# B98 stage 1 on the REVISED bar — REGISTERED 2026-09-27T16:49Z

Status: **registered 2026-09-27T16:49Z**, on the owner's go and with Watchara's agreement (relays `01M3H6W1D0FWHASX73T25DQF3T`,
`01M3H7Q6DNF5J1RMC8B25BPV2J`). At registration nothing has been run, no compile call has been made, and the primary
run's events have not been read for anything but their field names. Every number that decides a verdict is fixed
below. Any later change is a dated addendum under this text, never an edit of it.

## What this stage has to show

MAP B98 (revised 2026-09-24) passes stage 1 only on all four clauses:

1. **Held out by construction**: the predictor commits before the stored outcome is read, and is scored only on
   transitions whose `(level, board, action)` did not appear earlier in the same run.
2. **Availability**: the compiled hypothesis emits a prediction on **≥ 30 %** of those decisions (a lookup reached
   9.0 % — the figure is R31's, `notes/R31-transition-key.md`, recomputing B19's coverage argument on five runs).
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
  158 action / 37 analysis / 1 initial events). Replication run, read only after the primary verdict:
  **`sahasawatt/thui-b104-ctl-full25-r2` v1** (B81 + the B104 wrapper with the sheet flag OFF, COMPLETE 2026-09-27,
  first poll seeing it 12:48Z). Chosen by the review rule — the first COMPLETE of it and
  `yocybercode/thui-b105-ctl-full25-r1`, which ended 13:04:16 by its own `benchmark.json` (watchara, relay
  `01M3HJGDYS11YQ9NRV73RZJN9C`); the order holds under both bounds. Checked before naming: 25 events files, 2,814
  `action` events (= the run's action total), 0 missing `board_ascii` or `board_changed`, and the same action-event
  key set as the primary's.
- **Transitions**: exactly `stage1/SPEC.md`'s definition on the peer branch (before = preceding `initial`/`action`
  board, skip after `level_completed` / `game_over`). No state cloning: only stored boards are read.
- **Hypothesis text**: assistant-visible text and THINKING text in `analysis` events, extracted by the peer's
  `stage0_extract.py` (unchanged, recall 188/188 on its own control). ⚠️ One `analysis_step` can hold analysis rows on
  BOTH sides of its actions (workspace CLAUDE.md: the shape is `[analysis]* action* [analysis]`), so **a sentence is
  usable for a decision only if its row precedes that decision's action row in FILE order** — never by
  `analysis_step`.

## Held-out decisions (clause 1)

A decision = one transition whose key `(level, board_ascii_before, action_display)` has not occurred earlier in the
same game's file. This is R31's key exactly — the board as the agent is shown it (raw `board_ascii`, HUD included,
no mask) and the action as the agent issues it (`action_display`, so a click carries its cell; R31 showed that keying
clicks on `action_name` merged 662 distinct cells). Using the same key keeps this availability comparable with
R31's 9.0 %. Everything else is excluded before scoring. Reported: held-out count per game, and the excluded share
(R31 puts exact repeats at 4.1 %, so most decisions should survive — a much smaller survivor count is itself a
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
  `always`, `every time`, `each time`, `whenever`, `any time`, `causes`, `makes`, `moves by`, `rule`, `means that`.
  Bare `will`, `each`, `every` and `means` are deliberately absent: they match plans ("I will press UP") as readily
  as rules. The candidate already carries an action token and an effect verb (that is how stage 0 extracts it), so a
  cue is all the filter adds. Nothing else decides membership — no judge, no LLM. Controls, run before the filter
  touches the primary: the observation the stage-0 LEDGER validated ("clicking (23,61) made M(23,55) disappear" — a
  single past event, not a rule) must be REJECTED; a synthetic rule ("pressing LEFT always moves the yellow block 3
  cells left") must PASS; and the filter's rule share on the peer's 96 judged B99 sentences must land within ×2 of
  the judges' 10 / 96 — outside that band the filter is VOID-as-instrument and is revised and re-registered before
  use.
- **Budget**: the filtered rule sentences, deduplicated per game, **capped at 60 per game by even spacing in file
  order** (≤ 1,500 compile calls per run). The replication run is compiled only once the primary has passed
  (i)–(iv) — row 4 of the partition below — so the total never exceeds 3,000. The cap and the spacing rule are
  fixed here so no sentence is chosen after seeing its effect.

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
exceeds 10,007.** ⚠️ **The measured tokens are a PROXY.** They are codex's tokens (output plus reasoning, as the CLI
reports them), while the ceiling is denominated in the live model's tokens (Qwen3.8-Flash-Next on B81). The two
models tokenise and reason differently, and the direction of the error is not known. The proxy is graded as
measured. A median above **0.5 × the ceiling (5,004)** that still passes is reported as **NEAR-LINE** beside the
verdict, because a proxy error of 2× would flip it. NEAR-LINE is a flag on the PASS row, not a row of its own.

**Input tokens** (sentence + 64×64 board + prompt, ~1,400–2,000 for the board alone) are MEASURED on this stage's
calls and REPORTED, not graded. The live side of that comparison is **UNMEASURED — an instrument gap, not a zero
budget**: the banked `benchmark.json` reads `uncached_input_tokens = 0` on all 3,017 history entries of the primary,
which says the field is not populated on this chassis, not that input costs nothing (prefill is real GPU work and
real money). With no measured live input figure there is nothing to derive a ceiling from, so none is set; a
ceiling here would be a number with no source.

## The predictor

At each held-out decision, the active hypotheses are every compiled hypothesis from the same game and level whose
sentence precedes the decision in file order. **Only SPECIFIC hypotheses can emit**: `move`, `recolor`,
`disappear`, and `appear` / `count_delta` that name a `target.region`. `any_change`, `no_change`, and region-less
`appear` / `count_delta` never emit, because the SPEC never returns `na` for them — "pressing UP changes the board"
would predict every UP and buy availability without saying anything. Their counts are reported separately and never
graded. A specific hypothesis **emits** a prediction when its action matches the decision's action (SPEC matching
rules) and the checker's per-transition verdict on the BEFORE board would not be `na` — decided from the before
board alone. When several emit, the most recent sentence wins; ties are impossible
because file order is total. The outcome is read only after the prediction is fixed: the checker's `support` /
`contradict` on the stored AFTER board.

## Verdict (all four, per the row)

- **(i)** held out: satisfied by construction above; VOID if any scored decision's key occurs earlier in its game.
- **(ii) availability** = emitting held-out decisions / held-out decisions, over all games pooled. **PASS ≥ 0.30.**
  Anything ≤ 0.12 refutes the premise (a compiled rule generalises no better than a lookup, R31's 9.0 %) rather
  than this compiler. The two figures share a threshold, not a denominator: R31's 9.0 % counts decisions from a
  board SEEN before, this one counts emissions on decisions whose key is NEW — as the MAP row frames it.
- **(iii) accuracy — graded on the EFFECT, against a shuffled-hypothesis null on the same rows.** ⚠️ **This departs
  from the MAP row's wording** (*beats the 89.8 % majority-class null*); Watchara agreed on 2026-09-27 (relay
  `01M3H7Q6DNF5J1RMC8B25BPV2J`) and the B98 MAP row carries the same amended clause. Reason: every specific effect implies `board_changed = true`, which is what the majority class
  predicts already, so a `board_changed` test could only be won by `no_change` hypotheses — which cannot emit — and
  would FAIL whatever the premise. Procedure: for each emitting row, a NULL hypothesis is drawn (seed 20260927) from
  the pool of specific hypotheses compiled in OTHER games that would also emit on this row (same action kind,
  non-`na` on this before board); rows where none exists are dropped from BOTH sides and counted. Correct = the
  checker returns `support`. Test: exact one-sided McNemar on the discordant pairs (predictor right / null wrong vs
  the reverse). **PASS if p < 0.05.** Reported beside it and never graded: the MAP's `board_changed` accuracy against
  the majority class on the same rows, and the share of rows dropped for want of a null.
- **(iv)** **≥ 12 of 25 games** contribute ≥ 1 emitting held-out decision.
- **Teeth, both poles** (they test the instrument, not the hypothesis):
  - *negative*: a second shuffle (seed 20260928) scored against the first as if it were the predictor must NOT pass
    (iii). Null against null passing means the test fires on noise.
  - *positive*: an ORACLE predictor, which for each emitting row takes a specific hypothesis from the pool that the
    stored after-board supports, must PASS (iii). An oracle that cannot pass means the test cannot fire at all.

### The verdict partition — evaluated in this order, first match wins, every run lands in exactly one

| # | outcome | fires when | consequence |
|---|---|---|---|
| 1 | **VOID** | on the PRIMARY: any scored decision's key occurs earlier in its game (clause i broken), OR the rule filter fails its controls, OR either teeth pole misbehaves (negative passes / positive fails) | nothing read; fix the instrument, re-register, re-run |
| 2 | **REFUTED-PREMISE** | primary availability (ii) ≤ 0.12 | B98 closes: a compiled rule generalises no better than a lookup (R31's 9.0 %) |
| 3 | **FAIL** | primary: any of (ii) < 0.30, (iii) p ≥ 0.05, (iv) < 12 games | B98 closes at stage 1 under the row's kill rule |
| 4 | **NOT-REPLICATED** | primary passes (i)–(iv), and the REPLICATION run — compiled and scored by the identical pipeline — is VOID or fails any of (ii)–(iv) | recorded; B98 closes, stage 2 does NOT start |
| 5 | **PASS-UNAFFORDABLE** | both runs pass (i)–(iv) AND the primary's graded compile-cost median > 10,007 generated tokens/game | recorded; stage 2 does NOT start |
| 6 | **PASS** | both runs pass (i)–(iv) AND that median ≤ 10,007 (flagged NEAR-LINE if > 5,004) | licenses defining stage 2 (below) |

Every run lands in exactly one row. Row 2 is tested before row 3, and 0.12 < 0.30, so they cannot both claim a run.
Rows 1–3 read the primary only; once none of them has fired, the primary has passed (i)–(iv), and row 4 then
splits on the replication alone — which is why the replication is compiled only at that point. Rows 5 and 6 split
exactly on the one graded number. A replication VOID lands in row 4, not row 1: the primary's instrument has
already passed, and a broken second run cannot license anything.

## What a PASS licenses — and does not

It licenses defining stage 2 against the terms already sent to Watchara on 2026-09-27 (relay
`01M3H5GR875GYW6AS51Q4MNAZH`):
plan-search games = the games whose own availability is ≥ 30 % in THIS run, frozen as a list before any GPU;
3× human actions per LEVEL as a cap. It says nothing about score: every in-chassis lever so far read inside hidden
noise.

## Known confounds, carried

- The compiler sees the board, so it can write a rule the model never meant. The grounded hypothesis is the
  COMPILER's reading of the model's words; a PASS proves compilable availability, not that the model held the rule.
- One primary run: per-game availability is n = 1 per game, and the replication run is the only guard.
- The extractor keys on action tokens and effect verbs, so rules stated without them are invisible (the same bias
  the stage-0 PASS was measured under).

## Review decisions (Watchara, relay `01M3H6W1D0FWHASX73T25DQF3T`, 2026-09-27)

- Compiler = codex; 60 sentences/game with a hard cap of ≤ 1,500 calls — accepted as drafted.
- PASS-UNAFFORDABLE gets a numeric ceiling now — the section above.
- Verdict clauses must partition with no undefined case — the table above.
- **Agreed 2026-09-27 (relay `01M3H7Q6DNF5J1RMC8B25BPV2J`), on two conditions, both applied in rev 4:** (A) the
  B98 MAP row is amended in the same PR, so the MAP and this file state one bar; (B) live input cost is written
  as an UNMEASURED instrument gap, not as a zero budget. He noted that counting only specific hypotheses makes the
  30 % bar harder to clear; 30 % / 12 % stay as registered. Changes he agreed to, as introduced in rev 3: clause (iii) graded on the effect against a
  shuffled-hypothesis null instead of `board_changed` against the majority class (reason in the clause); generic
  hypotheses barred from emitting; the NOT-REPLICATED row; the cost proxy and NEAR-LINE flag.
- **Replication run named 2026-09-27** (see Data): `sahasawatt/thui-b104-ctl-full25-r2`, by the review rule, fields
  checked, before the primary is read.

## ADDENDUM 2026-09-28T07:12:54Z: the rule filter FAILS its registered control -> VOID-as-instrument (row 1). Nothing compiled or scored.

Run by the sahasawat session (worktree branch `b98/stage1-run` @ 52d43d4, tooling from `b98-stage01-artifacts` @ 6400779).
Order kept as registered: the filter controls ran BEFORE the filter touched the primary.

- Observation control "clicking (23,61) made M(23,55) disappear": REJECTED, as required.
- Synthetic rule "pressing LEFT always moves the yellow block 3 cells left": PASSED, as required.
- **Rule share on the peer's 96 judged B99 sentences = 2 / 96 = 0.021**, against the band [0.052, 0.208] (x2 around
  the judges' 10 / 96). The case-insensitive substring reading and a word-boundary reading both give 2 / 96.
  The filter catches **1 of the 10** sentences the judges called rules. The other 9 state rules with no listed cue,
  for example "RIGHT moved columns by +3 each press", "When SPACE destroys a box, …", "each click toggles only
  itself", and "The bubble moves LEFT/RIGHT in 6-col steps". The other match (h074) is a hypothetical
  ("What if … — always horizontal"). The 10 are the kind-rule labels of judge 0 among the 33 sentences both
  judges found checkable, the figure `stage0_agg.py` prints.
- **Consequence under this file's own rule:** the filter is revised and RE-REGISTERED before use. The primary's
  sentences were never filtered, no compile call was made, and no decision was scored. What WAS read from the
  primary: identity checks (ls20 158 action / 37 analysis / 1 initial; 3,017 actions; generated total
  2,428,876, median 100,066 per game; uncached_input 0 on all 3,017 entries; all match this file), field types,
  and ONE ls20 analysis transcript used only to prove the string extractor equals `stage0_extract.turns()`.
- ⚠️ **Any revision tuned on these 96 sentences makes the x2 control circular**, since this addendum's author
  has now read the 10 judged rules. A revised filter needs a control sample it was not built on.
- **Instrument finding, independent of the VOID:** SPEC.md documents event values as strings, and
  `checker.parse_events` tests `== "True"`. On the B81 chassis `level_completed` and `game_over` are JSON
  bools, so the peer parser NEVER skips a post-transition pair. `b98s1.py` implements the same definition with the
  value normalised. `test_b98s1.py` shows both behaviours (20 checks, 7 mutants red, ALL OK).
