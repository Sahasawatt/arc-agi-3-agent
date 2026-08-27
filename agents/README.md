# `agents/` — one page per agent variant that was actually built

Two lines have been built in this repo. Every variant of each one has a directory here:

```
agents/<line>/<version>/<variant>.md
```

- **`duck/`** — the duck-harness fork. This is the line that ships.
- **`thui/`** — the thui line, branched off `duckv10` to carry per-run instrumentation.

## What this tree IS

An **index**. Today the facts about any one variant are scattered across four places — a row
in `notes/LEDGER-all-runs.md`, a row in `notes/wayfinder/MAP.md`, a docstring in
`<dir>/build_notebook.py`, and an `R`-note. A page here names all four for one variant, so
"what was `v24` and what happened to it" is one file rather than four greps.

## What this tree is NOT

**Not a second ledger.** This repo has been bitten more than once by a summary drifting from
its body, so nothing here is authoritative:

| question | the authority |
|---|---|
| what did a run score | `notes/LEDGER-all-runs.md` |
| what is the campaign doing, and which tickets are open | `notes/wayfinder/MAP.md` |
| what exactly did a build change | `<dir>/build_notebook.py` and its patch file |
| why it was built and what the run proved | the `R`-note each page names |

Every number on these pages is a **dated reading**, marked as such. If a page and the ledger
disagree, the ledger is right and the page is stale — say so rather than reconciling them
silently.

## Reading a page

Each page answers the same six questions in the same order, so they can be skimmed side by side:

1. **What line and version** — and which ticket it was built to answer
2. **The one change** — every build after `duckv10` changes exactly one thing on purpose
3. **Where it lives** — the build directory and the file that carries the change
4. **Which kernel ran it** — slug, and whose account it actually landed on
5. **What it scored** — public, hidden if it was ever submitted, dated
6. **The verdict** — and the note that argues it

## The rule every one of these builds obeys

**One change at a time.** Two at once and a revert teaches nothing. `v9` is the counter-example
that made the rule: it changed the bundle, the model and the output cap together and scored
`0.22`, and it took a separate build (`duckv10`) to learn which of the three did it.

## Builds that no longer have a directory

`4a42e0bd` (2026-08-24) deleted **16** version directories: `duckv5`–`duckv9`, `duckv11`–`duckv14`,
`duckv16`, `duckv18`–`duckv23`. Their runs are still in the ledger and their code is still in git
history — `git show 0757309^:duckv<N>/build_notebook.py`. They have no page here because a page
that points at a directory which does not exist is worse than no page.
