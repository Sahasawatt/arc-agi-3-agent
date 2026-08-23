# v19 — banking: the four engine facts, read from the engine

2026-08-23. Design + pre-flight verification for `duckv19`. No GPU spent before this was done.

## Why banking, over the other seventeen graft modules

Selection was made against one criterion — *what could still reach hidden 2.57 (top-5)* —
and the state of the evidence at the time:

- The efficiency axis ceilings at **5.80 public (~2.1 hidden)**. Anything that only makes
  existing play cheaper cannot reach the target, so eight closed directions are closed for
  a structural reason, not bad luck.
- The hidden set is **out-of-distribution by construction** (R22 / arXiv 2603.24621 Table 1:
  25 public / 55 semi-private / 55 fully-private, non-overlapping). That puts transfer risk
  on any graft tuned to a specific card's quirk, and it kills `transfer_solver` outright —
  its premise is that the 110 runs are the 25 games cloned.
- `banking` is the only module that changes the **scoring mechanism** rather than a
  heuristic, and it does not rest on the clone premise.

## The four facts, and where each was read

Verified by installing the engine locally — `arc-agi==0.9.8`, `arcengine==0.9.3` from PyPI,
into a throwaway venv, after symbol-matching 5 of 6 identifiers against the ones the harness
itself imports (`GameAction`, `GameState`, `EnvironmentScoreList`, `EnvironmentWrapper`,
`Scorecard`) to establish it is the same package and not a name collision.

| # | fact | what the source says |
|---|---|---|
| 1 | a card's score is the MAX over its plays | `EnvironmentScoreList.score` → `return max(run.score for run in self.runs)` — **its docstring says "average"; the code says max** |
| 2 | RESET while WIN is a FULL reset, even under `ONLY_RESET_LEVELS=true` | `ARCBaseGame.handle_reset`: the first guard reads `os.getenv(...) == "true" and self._state != GameState.WIN`, so a WIN falls through to `elif self._action_count == 0 or self._state == GameState.WIN: self.full_reset()` |
| 3 | a full reset opens a NEW play on the SAME card | `Scorecard.update_scorecard`: on a reset action, `if full_reset: self.new_play(...)`; `Card.inc_play_count` appends a fresh `0` to `actions`, `levels_completed` and `actions_by_level` |
| 4 | the score formula | in the same module: `score = ((baseline_actions / actions_taken) ** 2) * 100`, `min(score, 115.0)`, and at run level `max_score = max_weights / total_weights * 100` with `min(score, max_score)` — **exactly the two caps this campaign derived and verified against five games** |

Put together: exploration can cost whatever it costs, because the *second* play's action
counter starts at zero. Replay a pruned winning trace there and `(baseline/actions)^2` is
computed against a much smaller denominator; the card keeps the better play. Every guard in
`banking_solver` fails toward "do nothing", and aborting is free because the recorded win
still owns the max.

## What v19 actually is

`v10` (anim bundle, Qwen3.8-27B-FP8, output uncapped, `MULTIMODAL_UPSCALE` left at the
bundle default of **4** — v18 measured 8 as worse) with cell 12 replaced by
`duckv19/cell12_banking.py`, which arms **one** flag: `banking`. `transfer`, `recovery`,
`goalkeep`, `hudmask`, `clickmap`, `searchmap`, `efficiency`, `shortcircuit`, `schema_*`
all stay off — R9 says one run barely ranks two designs.

Compatibility with the anim bundle was established in R21 before any of this: 11/11 imported
symbols present, `_HarnessGameSession` a superset (27 methods vs the fork base's 24), and 0
signature mismatches on the four overridden methods.

## Verification that shipped inside the notebook

`composite.install()` **never raises** — on any internal error it restores the stock solver
and prints a note. A silent fallback would appear in the ledger as "banking does not help",
which is precisely how duckmod's patches achieved zero adoption unnoticed (R8). So cell 12:

- asserts `BankingHarnessSolver` imports and has `from_solver`
- re-asserts facts 1, 2 and 3 **against the engine on the kernel**, by `inspect.getsource`,
  so a Kaggle-side version whose behaviour changed fails loudly instead of scoring like stock
- prints `solver <before> -> <after> (installed=…)` and a WARNING line when unchanged

Teeth proved locally against the real engine: all three predicates PASS on the installed
source, and all **3 of 3** fail when handed a mutated copy (`max(`→`sum(`,
`full_reset`→`level_reset`, `new_play`→`reset`).

## A packaging fact that would have failed the run silently

Kaggle unpacked the uploaded dataset **flat** — the modules land at the dataset root, not
inside a `taaf_grafts/` directory. Measured with `kaggle datasets files` *before* writing the
loader, not discovered from a failed run. Cell 12 handles both layouts and rebuilds the
package directory under `/kaggle/working` when the mount is flat.

## Status

Smoke pushed 2026-08-23 (`-t 900`, version 1). UNVERIFIED until it lands: that the grafts
*run* on the anim bundle (symbol and signature compatibility is necessary, not sufficient —
behaviour inside the overridden methods can still differ), and what banking is worth in
score. Its value is also unknown on the public set — the fork reports no number for it.
