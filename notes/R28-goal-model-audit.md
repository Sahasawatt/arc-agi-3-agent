# R28 — the goal-model audit: on stuck levels, the goal is usually WRONG (4/5)

2026-08-24. B27 executed. Method (never touches `environment_files/`): for each of the five
enumerated pairs, read the STUCK run's final `[THINKING]` on the stuck level and judge its
goal statement against the mechanic the CLEARING run's own turns demonstrate on the same
level. Same-model runs only (v20 excluded). Levels verified against fixtures; extraction
control: a file yielding zero thinking sections fails the parse rather than reading as an
agent with no thoughts.

Correction recorded in MAP the same day: v10cal events were on disk all along
(`Temp/duckv10cal/artifacts/`, 25 games — the v17 probe itself read them on 08-22); the
"never downloaded" claim in B27 was false when written. v18/v19 events fetched today via
`kernels output` (25 + 25 files).

## The five pairs

| game | stuck | clearing | stuck goal verdict |
|---|---|---|---|
| cd82 | v18 L0 | v10cal L2 | **WRONG** — concluded "definitively NOT canvas==panel" because its geometry said the canvas bottom was unreachable by any stamp; the clearing run stamps the bottom half directly (icon click → piece color → SPACE) and clears pursuing exactly that goal. A false mechanical premise propagated into rejecting the true goal |
| dc22 | v18 L0 | v10cal L2 | **WRONG** — spent its run enumerating gem positions × color states ("state4 + any gem position is not the goal"); the clearing run modeled a ball-and-bridge mechanic (toggles move bar segments to build a continuous path) and cleared |
| ft09 | v19 L0 | v10cal L3 | **WRONG** — treated the four 3×3 panels as an IQ-test "infer the missing pattern" puzzle and reasoned abstractly for 24 turns; the clearing run CLICKED a square at step 4, saw it toggle, and reframed: make the large grid match its own thumbnail. It never discovered clickability |
| lp85 | v19 L1 | v10cal L3 | **RIGHT goal, wrong action model** — "put the yellows on the brackets" is the correct objective; it modeled one global ring rotation and stalled on "a single rotation can't align both". The clearing run decoded per-row/arm rotations and (on L3) ran an actual BFS over the learned moves — one of v10cal's 19 search turns, and the one place search demonstrably paid |
| re86 | v10cal L1 | v18 L4 | **WRONG/ABSENT** — the BEST build is the stuck one. 38 turns on the level, all perception (segmentation inventories); a single tentative goal appears at the final step ("maybe the X needs to move to the diamond's center") and is wrong — the clearing run demonstrates color-matched covering (X covers the orange dots, SPACE cycles the active shape, each shape to its dots) |

**4 of 5 stuck levels hold a wrong (or never-formed) goal model.** The pre-registered
reading fires: the bottleneck is rule DISCOVERY, and B29's verify-loop is the wrong build —
verified plans toward a wrong goal are worthless.

## What separates clear from stuck, in these five

The clearing side's edge was never deduction. ft09 clicked and looked; cd82's clearer tried
the stamps instead of proving them unreachable; re86's clearer (v18, our weakest headline
build) found SPACE-cycling by pressing SPACE. Three of five clears trace to a probe action
taken before the theory was finished — BDR-Pro's "nav displaces productive stumbling"
(R27), measured in vivo on our own runs. The one deep-search success (lp85 L3 BFS) came
AFTER the controls were fully decoded by probing.

This also closes the loop with B28 (same day, v22 artifacts): prompt pressure cannot raise
search usage (2.0% → 2.4%), and where it locally did (tu93 36%), the game collapsed. Search
is not the missing behaviour. Premature THEORY is the failure mode — the model commits to an
invented goal instead of buying the cheap disconfirming probe.

## UNVERIFIED / limits

- n=5 pairs, judged by one reader (me) against clearing-run evidence; no second judge.
- The "goal" on the stuck side is reconstructed from its final thinking turn — a run that
  articulated a better goal earlier and drifted would be misread (spot-checks of earlier
  turns in cd82/ft09 showed the same goal throughout, so the risk is low, not zero).
- Same-model pairs only; whether v20's collapse shares this mechanism is unmeasured.
- "Probing beats theorizing" is a reading of 5 cases, not a measured intervention. The one
  intervention-shaped fact we hold points the other way for prompts: v12/v16/v22 all pushed
  behaviour via prompt and none moved score. No candidate build follows from this note.
