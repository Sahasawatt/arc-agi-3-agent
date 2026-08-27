# `duck` — the line that ships

The duck-harness fork. Every submitted score this campaign has ever drawn came from this line.

## Versions with a directory at HEAD

| version | dir | one change vs its base | public | page |
|---|---|---|---|---|
| `mod` | `duckmod/` | the original fork: duck tools + prompt additions on the OLD bundle | 2.41 | [duck-mod](mod/duck-mod.md) |
| `v10` | `duckv10/` | anim bundle + Qwen3.8, output UNCAPPED — isolates the rebase | 4.71 / 4.55 | [v10](v10/v10.md) |
| `v24` | `duckv24/` | untried-ledger nudge (`B32`) | 3.78 | [v24](v24/v24.md) |
| `v25` | `duckv25/` | sampler pin, `LOCAL_ANALYZER_SEED` (`B37`) | 3.69 | [v25](v25/v25.md) |
| `v26` | `duckv26/` | family brake, `K=20` (`B38`) | 3.19 | [v26](v26/v26.md) |
| `clock2x` | `clock2x/` | per-game clock 7,920 s → 15,840 s (`B34`) | 6.40 | [clock-2x-v1](clock2x/clock-2x-v1.md) |

Numbers are dated readings from `notes/LEDGER-all-runs.md` as of **2026-08-27**; that file is the
authority.

## The two things to know before reading any of them

**`duckv10` patches nothing.** Its cell 12 is 253 characters of comment. The `2.41 → 4.55` gain
came from adopting a newer upstream bundle and a newer model and **deleting** the fork's own
patches. Every fork-authored patch shipped since has scored below its band. The line is not "a
patch mechanism".

**`v10` is still the baseline, and nothing has beaten it in a way that ranks.** `clock2x` scored
higher (6.40) and cannot ship — its per-game clock would need 17.6 h against a 9 h budget. Of the
builds that *could* ship, none separates from `v10` under `eval/rank_runs.py`.

## The band that makes most of these unrankable

Three runs of the **same** `v10` build scored **2.82 / 4.55 / 4.71**, so a single run landing
anywhere in `[2.82, 5.24]` ranks nothing on its own. Only `v20` (0.18) and `v21` (1.25) have ever
landed outside it. This is why every page below reports a verdict from `eval/rank_runs.py` rather
than from a mean.

## Where the rest went

`duckv5`–`duckv9`, `duckv11`–`duckv14`, `duckv16`, `duckv18`–`duckv23` were deleted by `4a42e0bd`.
Their rows are still in the ledger; their code is at `git show 0757309^:duckv<N>/…`.
