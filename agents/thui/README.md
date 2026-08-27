# `thui` — the instrumented line

Branched off `duckv10` to carry **per-run instrumentation** the duck line does not. Every thui
build is `v10` plus one change, and the first of those changes was a measuring device rather than
a lever.

## Versions with a directory at HEAD

| version | dir | one change vs `v10` | public | page |
|---|---|---|---|---|
| `v1.0` | `thuiv1/` | the per-request usage probe in cell 12 | 3.20 | [v1-0](v1/v1-0.md) |
| `v1.1` | `thuiv1/v1-1/` | probe **+** `LOCAL_ANALYZER_SEED` — `B37`'s clean arm | **5.24** | [v1-1](v1/v1-1.md) |
| `v2.0` | `thuiv2/` | animation retrieval **OFF** (`B39`) | 2.86 | [v2-0](v2/v2-0.md) |
| `v3.0` | `thuiv3/` | `LOCAL_ANALYZER_YIELD_SECONDS` 60 → 180 (`B48`) | 4.01 | [v3-0](v3/v3-0.md) |

Numbers are dated readings from `notes/LEDGER-all-runs.md` as of **2026-08-27**; that file is the
authority.

⚠️ **`v3.0` landed on `master` 2026-08-27**, after the run closed `B48`. It was on the
`thuiv3-yield` branch while it was in flight, and that branch is now behind `master` on everything
else — only its `thuiv3/` commit was taken.

## Why the line exists

`thui-v1-1-r2` was for two days **the only run on disk carrying `req_in_turn`**, so every
per-request finding this campaign has (`R44`'s decode rate, the turn-budget mechanism, the
ReadTimeout count) rested on one run at **n = 1**. `thui-v3-0` is the second, and because it moved
the knob rather than repeating the build it did more than double the n — it turned `R44` §3's
inferred gate into a measured one (`R47`). Extending that n is most of what a thui run buys
regardless of what it scores, and this is the worked example.

## The versioning convention

A **MAJOR** is a new lever family and gets its own directory; a **MINOR** refines the same lever
and lives in the same directory beside another cell-12 file, one kernel per major. `thuiv1/` and
`thuiv1/v1-1/` are that convention's worked example.

## The self-check every builder here runs

Cell 12 is compared against the **patch file** and cells 6/8 against
`duckv10/taaf-duck-v10.ipynb` — **never** against `SRC_NB`. `duckv25` shipped a run advertised as
"v10 + seed" that was `duckmod` + seed, because its assert compared cell 12 against the same source
the builder never touches: a tautology that passes by construction and prints a reassuring line.
