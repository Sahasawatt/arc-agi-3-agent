# `thui` — the instrumented line

Branched off `duckv10` to carry **per-run instrumentation** the duck line does not. Every thui
build is `v10` plus one change, and the first of those changes was a measuring device rather than
a lever.

## Versions with a directory at HEAD

| version | dir | one change vs its base | public | hidden | page |
|---|---|---|---|---|---|
| `v1.0` | `thuiv1/` | the per-request usage probe in cell 12 | 3.20 | — | [v1-0](v1/v1-0.md) |
| `v1.1` | `thuiv1/v1-1/` | probe **+** `LOCAL_ANALYZER_SEED` — `B37`'s clean arm | **5.24** | 1.29 | [v1-1](v1/v1-1.md) |
| `v2.0` | `thuiv2/` | animation retrieval **OFF** (`B39`) | 2.86 | — | [v2-0](v2/v2-0.md) |
| `v3.0` | `thuiv3/` | `LOCAL_ANALYZER_YIELD_SECONDS` 60 → 180 (`B48`) | 4.01 / 4.518 | 1.63 / 1.59 | [v3-0](v3/v3-0.md) |
| `v3.1` | `thuiv3/` | **nothing** — third draw of the same build | 5.17 | **2.03** | [v3-1](v3/v3-1.md) |
| `v3.2` | `thuiv3/` | **nothing** — fourth draw of the same build | 3.85 | **1.35** | [v3-2](v3/v3-2.md) |
| `v4.0` | `thuiv4/` | `LOCAL_ANALYZER_TEMPERATURE` 0.6 → 1.0 at yield 60 | 1.92 | — | [v4-0](v4/v4-0.md) |
| `v4.1` | `thuiv4/` | **nothing** — repeat of v4.0's cell | 3.79 | — | [v4-1](v4/v4-1.md) |
| `v4.2` | `thuiv4/` | **nothing** — second repeat of that cell | 3.23 | — | [v4-2](v4/v4-2.md) |
| `v5.0` | `thuiv5/` | temperature 1.0 at yield 180 (`B53`) | 3.08 | — | [v5-0](v5/v5-0.md) |
| `v5.1` | `thuiv5/` | **nothing** — repeat of v5.0's cell | 2.34 | — | [v5-1](v5/v5-1.md) |
| `v5.2` | `thuiv5/` | **nothing** — second repeat of that cell | 2.68 | — | [v5-2](v5/v5-2.md) |
| `v6.0` | `thuiv6/` | `LOCAL_ANALYZER_CONTEXT_WINDOW` 32768 → 49152 (`B54`) | **6.05** | 1.26 | [v6-0](v6/v6-0.md) |

Numbers are dated readings as of **2026-09-03**. `notes/LEDGER-all-runs.md` is the authority — and
⚠️ **it had no rows for `v3.1`, `v3.2` or `v6.0` until 2026-09-02**, so those three were recovered
from the Kaggle submission record. ✅ **Their per-run columns were filled 2026-09-03** from
`kaggle kernels output` — the artifacts were retrievable all along, because all three were pushed
AFTER the cell-0 Quick Save that left the five older kernels serving no output.

⚠️ **`v3.1` and `v3.2` change nothing at all**, and that is the point: by 2026-09-01 the binding
uncertainty was the hidden channel's own spread, not any lever. The build's four public draws are
4.01 / 4.518 / 5.17 / 3.85 and its hidden draws are 1.63 / 1.59 / 2.03 / 1.35 — **neither ordering
predicts the other**, and 5.17 (second-highest public of the campaign) still sits inside the
same-build band.

⚠️ **`v3.0` landed on `master` 2026-08-27**, after the run closed `B48`. It was on the
`thuiv3-yield` branch while it was in flight, and that branch is now behind `master` on everything
else — only its `thuiv3/` commit was taken.

⚠️ **Four variants ran on 2026-09-01 and had no page here until 2026-09-03** — `v4.1`,
`v4.2`, `v5.1`, `v5.2`. Their results were recorded nowhere: no ledger row, no page, and the wave
note that names them logs the **push**, not the outcome. They matter more than a gap in an index:
each pair is a byte-identical repeat, so they turn two single-run cells of the temperature × yield
2×2 into cells of three — and the (1.0, 60) cell then spans **1.87** against a difference of cell
means of **0.28**.

## Where the line stands

**Standing best hidden 2.03** (`v3.1`, `55943442`), against a top-5 bar of **4.45** read
2026-09-02 13:05 UTC. `v3.2` resolved at **1.35** on 2026-09-02, the build's lowest; nothing is in flight. Every row in `notes/wayfinder/MAP.md`
reads closed — which means nothing is queued, not that nothing is left.

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

⚠️ **A repeat draw is a MINOR with an empty change set.** `v3.1` and `v3.2` add no file at all — they
are the same notebook submitted again, and they get version numbers because *what was learned* is
indexed by submission, not by diff. A page whose "one change" section reads **None** is correct, not
unfinished.

## The self-check every builder here runs

Cell 12 is compared against the **patch file** and cells 6/8 against
`duckv10/taaf-duck-v10.ipynb` — **never** against `SRC_NB`. `duckv25` shipped a run advertised as
"v10 + seed" that was `duckmod` + seed, because its assert compared cell 12 against the same source
the builder never touches: a tautology that passes by construction and prints a reassuring line.
