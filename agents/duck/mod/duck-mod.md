# duck `mod` — the original fork

**Line** duck · **version** mod · **directory** [`duckmod/`](../../../duckmod) · **status** superseded by `v10`

## What it is

The fork as it existed before the rebase: the duck tools and prompt additions layered on the
**OLD** bundle. It is the only build in this tree that is not a one-change delta from `duckv10`,
because it predates `duckv10`.

Its cell 12 is **14,355 characters** — the largest patch payload on the line. That number matters
beyond history: `duckv25`'s builder read `duckmod` as its source and forgot to replace cell 12, so
a later build shipped this payload by accident. The `duckv25` page records how that was caught.

## Where it lives

| what | path |
|---|---|
| tools | `duckmod/duck_tools.py` |
| prompt additions | `duckmod/prompt_additions.txt` |
| notebook | `duckmod/taaf-duck-mod.ipynb` |
| kernel metadata | `duckmod/kernel-metadata.json` → `sahasawatt/taaf-duck-mod` |

There is no `build_notebook.py` here — this build predates the builder convention.

## What it scored

| run | public | hidden | levels | actions | bundle |
|---|---|---|---|---|---|
| `duck-mod` | **2.41** | **1.00** | 17 | 3,481 | old |
| `duck-mod cal` | **2.16** | — | 19 | 3,858 | old |

Dated reading from `notes/LEDGER-all-runs.md`, 2026-08-27.

## Verdict

**Superseded.** `v10` reached 4.55 by adopting a newer bundle and model and **deleting** the
patches this build is made of. That is the single most load-bearing fact about this line, and this
page is where it is easiest to see: the fork's own additions were worth less than the upstream it
was forked from.

Its hidden draw is also one of only four the campaign has ever taken (`duck-mod` 1.00, `v5` 0.84,
`v10` 1.70, the from-scratch agent 0.11), and it anchors the public→hidden shrink ledger.

## Read next

- `notes/LEDGER-all-runs.md` — the shrink ledger and every run
- [`../v10/v10.md`](../v10/v10.md) — the build that replaced it, and why
