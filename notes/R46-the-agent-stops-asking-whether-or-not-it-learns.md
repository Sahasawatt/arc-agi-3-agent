# R46 — the agent stops asking about the mechanics, and it stops at the same rate whether or not it is getting anywhere

**2026-08-27, offline, 0 slots, 0 GPU.** `scripts/b27/b26_mechanic_belief.py`, five controls,
15 selftest cases, one of which **failed on first run and was a real defect in the slicer**.

R32 closed the one-bit version of B26's remaining half and named what was left:

> This measures ONE BIT and does not touch R29 §2 — the agent's belief about what an action
> *does* (`lp85`'s "one big loop", `cd82` still asking "do arrows move the piece?" at turn 40)
> is a richer object, is untouched, and remains the load-bearing half.

That richer object is a **theory of the mechanics**, and there is no ground truth for a theory,
so "is the belief right" is not measurable. The exemplar R29 gives is temporal — *still asking at
turn 40* — so the measurable form is:

> does the agent's expressed uncertainty about the mechanics decay as a game goes on, and does it
> decay differently in games that clear levels than in games that stall?

Either answer is useful. Decay only in clearing games makes *never learns the mechanics* the stall
mechanism. Flat in both takes the belief off the critical path.

**Neither happened.** It decays by half, and it decays the same amount in both.

## 1. What was measured

**200 game logs over 8 runs, 9,085 analysis rows.** For each row, the agent's own prose — the
`[ASSISTANT]` and `[THINKING]` blocks and nothing else — is sliced out, and a sentence counts as
mechanic-uncertainty if it carries an action verb *and* either a question mark or a hedge. Each
row is placed in a **quartile of its own game's turn sequence**, so games of different lengths
compare. Rate is hits per 1,000 characters of that prose.

## 2. Pooled: a 48% decay, identical in both populations

| population | Q1 | Q2 | Q3 | Q4 | Q1→Q4 |
|---|---|---|---|---|---|
| all games (9,085 rows) | 1.09 | 0.74 | 0.65 | 0.57 | **−47.9%** |
| cleared ≥1 level (5,871 rows) | 1.16 | 0.74 | 0.67 | 0.60 | **−48.5%** |
| cleared nothing (3,214 rows) | 0.98 | 0.73 | 0.61 | 0.53 | **−46.3%** |

The two populations are **2.2 percentage points** apart on a 48-point effect.

## 3. Per-game, so a few verbose games cannot carry it — and a measured bar

A pooled rate over 200 logs can be driven by a handful of talkative games. One number per game,
compared by rank:

| quantity | cleared (n=127) | stalled (n=73) | AUC | inside the null band? |
|---|---|---|---|---|
| Q1 rate | median 1.12 | median 0.97 | 0.593 | **yes** |
| Q4 rate | median 0.55 | median 0.48 | 0.554 | **yes** |
| Q1→Q4 decay | median −50.9% | median −47.8% | **0.489** | **yes** |

The bar is measured, not assumed: shuffling which games count as "cleared" and re-computing, 600
relabellings, reaches **|AUC−0.5| = 0.159** on this sample. All three quantities sit inside it. On
the decay itself the AUC is **0.489** — the two populations are interchangeable.

## 4. What this says

**Expressed uncertainty about the mechanics tracks TURN POSITION, not knowledge.** The agent stops
asking whether the arrows rotate or translate at the same rate in a game it is solving and in a
game it will never score in.

Two consequences:

1. **`cd82` still asking at turn 40 is a real anecdote and not the general shape.** The general
   shape is the opposite — the agent stops asking everywhere, including where it should not.
2. **B26's remaining half is not load-bearing in the form R32 left it.** An intervention aimed at
   *"make the agent settle its theory of the mechanics faster"* has no measurable target in these
   artifacts: the settling already happens, at the same speed, in the games that go nowhere. What
   would be worth attacking is the opposite — that confidence arrives on schedule rather than on
   evidence — and that is a different proposal from the one B26 carries.

## 5. The defect the selftest caught, because it is the interesting one

The section-boundary pattern was first written `^\[[A-Z][A-Z ]*\]`. The two markers that actually
end an `[ASSISTANT]` block are **`[TOOL CALL: python]`** and **`[TOOL RESULT: python]`** — both
carry a colon, so neither matched, and the agent's "own prose" silently absorbed the
**environment's output**. Every rate in this note would have been a measurement of tool results.
It reads correctly, it produces plausible numbers, and only an explicit case (`slice drops TOOL
RESULT`) fails on it.

This is the third appearance of the same family in this repo: R33 recorded the section trap, R39's
first probe returned 100% on every column **including both controls** because the 14,204-char
`[SYSTEM PROMPT]` contains the tokens being counted, and here the boundary regex was one
punctuation class short. **C2 is that trap turned into a control** — a system-prompt-only phrase
must score **0** after slicing (it does) while action verbs in the sliced prose must be **> 0**
(333). Without both halves, a zero cannot be told from an empty slice.

## 6. Limits, stated rather than discovered later

1. **Expressed uncertainty is not actual uncertainty.** The agent may simply stop writing hedges
   while remaining exactly as lost. This probe cannot separate *learned the mechanics* from
   *stopped saying so* — and the identical decay in stalled games is evidence for the second
   reading, not the first.
2. **A live confound with the opposite cause.** As a game proceeds the agent may talk about
   *execution* rather than about *mechanics*, so the rate falls with no change in confidence at
   all. C3 rules out the volume version (prose per quartile is 12.8M / 14.7M / 16.2M / 15.0M
   chars — it **rises** into Q3) and C4 rules out a gross composition shift (a neutral frequent
   word varies 5.8% across quartiles), but neither rules out a topic shift.
3. **The construct is a regex.** A trend survives an imprecise detector only while the imprecision
   does not correlate with turn position; C4 is the check on that, and it is a proxy, not a proof.
4. **Tool-call code is excluded.** A belief stated only in a code comment is not counted.
5. **8 runs are 8 draws of the same 25 public games.**

## 7. Reproduce

```bash
python scripts/b27/b26_mechanic_belief.py --selftest   # 15 cases, no corpus
python scripts/b27/b26_mechanic_belief.py              # needs ~/Claude/arc-artifacts/ (0.56 GB, ~12 s)
python scripts/b27/b26_mechanic_belief.py --runs 1     # smoke on one run first
```
