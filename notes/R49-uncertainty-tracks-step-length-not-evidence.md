# R49 — the agent's expressed uncertainty tracks how LONG a step was, not whether it was wrong

**2026-08-27, offline, 0 slots, 0 GPU.** `scripts/b27/b26a_evidence_update.py`, ten controls,
24 selftest cases, teeth proven by four mutations. Answers `B26-a`, the successor question the
2026-08-27 next-session guide ranked first, on the dead-end criterion that ticket fixed **before**
the run.

R46 measured expressed mechanic-uncertainty against TURN POSITION: a 48% decay, the same in games
that clear and games that never score. Its limit 1 names what it could not separate:

> Expressed uncertainty is not actual uncertainty. This probe cannot separate *learned the
> mechanics* from *stopped saying so* — and the identical decay in stalled games is evidence for
> the second reading.

`B26-a` proposes the discriminator: stop conditioning on time and condition on **evidence**. When
the agent fires actions and the board does not move, its theory of the mechanics has just been
falsified. If it is learning, that should show. If it is only running out of things to hedge
about, it should not.

**It does not show.** The effect that looks like evidence-updating is step LENGTH.

## 1. The link, which is not what the workspace docs say

The workspace `CLAUDE.md` records that one `analysis_step` emits many `analysis` events *"and then
0..N `action` events"*. The count half is right — an `analysis` event is a reasoning round, not a
turn. The ORDER half is not, and this probe cannot be built on it.

Measured over all 200 logs, the per-step shape is `[analysis]* action* [analysis]`:

| | |
|---|---|
| analysis rows BEFORE their step's first action | **3,942** (43.4%) |
| analysis rows AFTER their step's last action | **3,471** (38.2%) |
| between actions, or in an action-less step | 1,672 |
| acting steps with **no** analysis row before their first action | **2,069 of 3,538** |

So `analysis_step` alone cannot say which rows are a claim and which are a reaction; **file order
can**, and the trailing row is the reaction to the outcome. That trailing row is this probe's
subject. C6 asserts the partition is exhaustive on every run.

## 2. What was measured

| | |
|---|---|
| text | the agent's own prose only — `[ASSISTANT]` + `[THINKING]`, sliced by `b26_mechanic_belief.py`'s slicer **verbatim** |
| hit | a sentence carrying an action verb AND (a hedge OR a question mark) — same detector as R46 |
| rate | hits per 1,000 characters of that prose |
| outcome | per step, from `board_changed` on that step's own actions: all changed / none changed / mixed |
| M1 | post-action rows of the SAME step |
| M2 | pre-action rows of the NEXT step |

Step counts: **all_changed 3,027 · mixed 294 · none_changed 217.**

The slicer is not re-implemented. C2 prints **333** action verbs in the sliced prose of the first
25 games — the same figure R46 §5 published for its own C2, which is evidence the prose object is
literally the same one, not merely a similar one.

## 3. The result

| | n | median /1k | AUC | matched band | verdict |
|---|---:|---|---|---|---|
| **M1** post-action, same step | 217 vs 2,967 | 1.07 vs 0.75 | **0.607** | 0.065 | above — **and it is an artifact** |
| **M1, batch-matched** (C10) | 210 vs 1,676 | **1.09 vs 1.05** | **0.520** | 0.060 | **DEAD END** |
| **M2** pre-action, next step | 61 vs 1,131 | 0.80 vs 0.68 | 0.542 | 0.127 | **DEAD END**, underpowered |

**The mechanism of the false positive.** A no-op step holds **1.05** actions on average; a
confirmed step holds **3.58** (medians 1.0 and 1.0, means 1.05 and 3.58, max 5 and 99). A long
batch is the agent executing a plan it is confident in, so it hedges less per 1,000 characters.
Pin both groups to single-action steps and the gap closes to **1.09 against 1.05**, an AUC of
0.520 inside a 0.060 band.

**M2 is NOT MEASURABLE, not zero.** With n=61 the matched band is 0.127, so any effect smaller
than that was invisible before the run started.

## 4. The control that would have confirmed the artifact

C9 compares the two outcomes **within a single game**, which is the move R46 §3 makes to stop a
few verbose games carrying a pooled result. Run as first written it is emphatic:

```
C9 within-GAME, as first written (shares M1's batch confound)
   games holding both kinds of step: 96
   uncertainty HIGHER after falsification in 69, lower in 27, tied 0
   exact two-sided sign test p = 2.148e-05          <- looks decisive
```

It is worthless here, because it holds the GAME fixed and lets batch length vary — the same
assumption M1 makes. Re-run with both sides pinned to single-action steps, on essentially the same
games:

```
C9 within-GAME, BATCH-MATCHED, single-action steps only
   games holding both kinds of step: 93
   uncertainty HIGHER after falsification in 55, lower in 38, tied 0
   exact two-sided sign test p = 0.09657           <- does not separate
```

Both passes are printed by the script, deliberately. **Two methods agreeing is proof only if they
do not share an assumption**, and a p of 2×10⁻⁵ from a control that shares the confound is exactly
what a wrong finding looks like on its way to being published.

## 5. C8 is retired in place rather than deleted

C8 asked whether `mixed` steps — some actions moved the board, some did not — sit between the two
poles, as a dose-response. They do not: `mixed` is **0.63/1k**, *below* `all_changed`'s 0.75.

That reads as an inverted dose and it is not one. A step can only BE `mixed` by holding several
actions: median actions per step is **4.0** for mixed against **1.0** for both poles. Its position
is a statement about batch length, which is how the confound in §3 was found at all. The control
is kept in the output with its own retraction attached.

## 6. Limits, stated rather than discovered later

1. **This is expressed uncertainty, exactly as in R46.** A null here says the agent does not
   *write* differently after a falsification; it cannot say the agent does not *update*.
2. **`board_changed` is one bit of falsification.** An action that moves the board in a way the
   agent did not predict is recorded here as a confirmation. The richer miss is not measured.
3. **The batch match costs the multi-action population.** 210 of 217 no-op steps are single-action,
   so M1-matched is nearly the whole falsified group, but only 1,676 of 2,967 confirmed steps
   survive. The comparison is single-action steps, not all steps.
4. **8 runs are 8 draws of the same 25 public games.**
5. **The construct is a regex**, inherited unchanged, along with R46's own limit 3.

## 7. What it settles

`B26`'s last open half is answered, and the answer is the second reading of R46's limit 1: nothing
in the agent's expressed mechanic-uncertainty tracks evidence once **turn position** and **batch
length** are both held fixed. An intervention aimed at making the agent settle its theory faster —
or at making it re-open a settled theory when the board contradicts it — has no measurable target
in these artifacts, in either direction.

The two remaining `B26`/`B35` successor questions from the guide (`B26-b` prediction calibration,
`B35-a`/`B35-b` early-window detectors) are untouched by this and stay open on their own terms.

## 8. Reproduce

```bash
python scripts/b27/b26a_evidence_update.py --selftest   # 24 cases, no corpus
python scripts/b27/b26a_evidence_update.py --runs 1     # smoke on one run
python scripts/b27/b26a_evidence_update.py              # needs ~/Claude/arc-artifacts/
```

Teeth, proven by mutation — each reddens **only** its own case, so the run is not a compile error:

| mutation | case that must redden |
|---|---|
| `SECTION` regex loses its `:` branch (R46's own defect) | slice drops TOOL RESULT |
| post rows measured from the first action instead of the last | a row between actions is neither pre nor post |
| AUC gives full credit to ties | AUC of identical populations is 0.5 |
| `uncertainty_hits` drops the action-verb requirement | a hedge with no action verb does NOT count |
