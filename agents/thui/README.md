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

Numbers are dated readings from `notes/LEDGER-all-runs.md` as of **2026-08-27**; that file is the
authority.

⚠️ **`v3.0` exists as a branch and is NOT merged.** `thuiv3/` — `LOCAL_ANALYZER_YIELD_SECONDS`
60 → 180, ticket `B48` — lives on `thuiv3-yield` and has no directory at `master`, so it has no
page here yet. A page pointing at a directory that does not exist is worse than no page.

## Why the line exists

`thui-v1-1-r2` is **the only run of the eight on disk that carries `req_in_turn`** — the other
seven have no `*_usage.jsonl` at all. Every per-request finding this campaign has (`R44`'s decode
rate, the turn-budget mechanism, the ReadTimeout count) rests on that single run, at **n = 1**.
Extending that n is most of what a thui run buys regardless of what it scores.

## The versioning convention

A **MAJOR** is a new lever family and gets its own directory; a **MINOR** refines the same lever
and lives in the same directory beside another cell-12 file, one kernel per major. `thuiv1/` and
`thuiv1/v1-1/` are that convention's worked example.

## The self-check every builder here runs

Cell 12 is compared against the **patch file** and cells 6/8 against
`duckv10/taaf-duck-v10.ipynb` — **never** against `SRC_NB`. `duckv25` shipped a run advertised as
"v10 + seed" that was `duckmod` + seed, because its assert compared cell 12 against the same source
the builder never touches: a tautology that passes by construction and prints a reassuring line.
