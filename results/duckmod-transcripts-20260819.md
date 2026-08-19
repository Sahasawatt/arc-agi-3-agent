# Duck-mod injection #2 (`hud_mask` + `TransitionGraph`) — why the score doubled

Sources: `duckmodout/{summary.txt,benchmark.json,transcripts/*}` vs `duckout/{summary.txt,transcripts/*}` (baseline, unmodified prompt, same model/games/token budget). System-prompt diff confirmed the **only** change between the two runs is the two doc/advice blocks for `hud_mask(history)` and `TransitionGraph()` — nothing else in the prompt moved (`ft09` system prompt diffed line-by-line, `+1835 chars`, 30 added lines, rest identical).

## 1. Per-game score table — where the gain comes from

| game | mod | base | Δ | mod actions | base actions | note |
|---|---:|---:|---:|---:|---:|---|
| **ft09-0d8bbf25** | 28.57 | 6.37 | **+22.20** | 44 | 92 | 3/6 levels vs 2/6, in HALF the actions |
| **ar25-0c556536** | 7.73 | 0.00 | **+7.73** | 164 | 152 | unlocked level 2/8 (base never left level 1) |
| sp80-589a99af | 4.76 | 1.36 | +3.40 | 194 | 207 | |
| ls20-9607627b | 2.06 | 0.02 | +2.04 | 49 | 267 | far fewer actions |
| tu93-0768757b | 1.46 | 0.14 | +1.32 | 110 | 85 | |
| s5i5-18d95033 | 0.08 | 0.00 | +0.08 | 206 | 83 | |
| bp35 / cn04 / dc22 / g50t / ka59 / lf52 / lp85 / m0r0 / r11l / sb26 / sc25 / sk48 / su15 / tn36 / tr87 / wa30 | — | — | ≈0 | — | — | unchanged both runs (mostly 0.00 or identical score) |
| cd82-fb555c5d | 0.00 | 0.91 | −0.91 | | | regressed |
| vc33-5430563c | 0.00 | 1.11 | −1.11 | | | regressed |
| re86-8af5384d | 0.89 | 6.56 | **−5.67** | | | regressed hard (2/8 levels → 1/8) |
| **sum of Δ over 25 games** | | | **+29.02** | → mean Δ = 29.02/25 = **1.16**, matches reported 2.41−1.25 | | |

**Verdict: this is a 2-game effect, not a broad lift.** `ft09` (+22.20) and `ar25` (+7.73) together contribute **+29.93**, i.e. *more than 100%* of the total +29.02 gain — every other game's deltas net to **−0.91** once you sum them (three regressions of −5.67/−1.11/−0.91 largely cancel four small gains of +3.40/+2.04/+1.32/+0.08). 20 of 25 games are flat. This matches the "2-3-game fluke is a real possibility" concern in the brief: with documented σ≈0.4 per-game run-to-run noise, a single unseeded run per game cannot distinguish "the injection specifically helped ft09/ar25" from "this run's stochastic draw happened to land well on ft09/ar25 and badly on re86/vc33/cd82."

## 2. Did the LLM actually call the new tools? — No, essentially never

Raw text search for `hud_mask` / `TransitionGraph` across the 25 duck-mod transcripts returns 4,409 / 2,938 hits — but that number is **illusory**: the harness re-injects the full tool-doc system prompt on *every single turn*, so those are almost entirely documentation text, not usage. Isolating just the text inside `[TOOL CALL: python] ... [TOOL RESULT: python]` blocks (i.e. code the LLM actually wrote and executed) across all 2,001 tool-call turns in all 25 games:

| helper | actual invocations | games that used it at all |
|---|---:|---|
| `hud_mask(history)` (as a call, `hud_mask(`) | **2** | `cd82` (1), `ls20` (1) |
| any mention of `hud_mask` in code (incl. comments that don't call it) | 4 | `cd82`, `ls20`, `s5i5` |
| `TransitionGraph()` constructed | **0** | none |
| `.record(...)` / `.untried(...)` / `.path_to_nearest_untried(...)` | **0** | none |

Baseline transcripts (unmodified prompt) contain **zero** occurrences of either term — confirms these are 100% duck-mod-introduced and the count above isn't leaking from elsewhere.

**Critically: the two games that drive the entire net gain (`ft09` +22.20, `ar25` +7.73) never called either helper — 0 calls in both.** The two actual `hud_mask` calls happened in `cd82` (net −0.91) and `ls20` (net +2.04, a minor contributor).

Representative uses — this is the complete set of real invocations, not a curated sample (both quoted verbatim from the tool-call code):

```python
# cd82-fb555c5d — one of two real calls in the whole run
seg = current_frame.segmentation
...
from collections import Counter
hud = hud_mask(history)
print(f"\nHUD cells: {len(hud)}")
```

```python
# ls20-9607627b — the other real call; hud came back empty
from collections import Counter
hud = hud_mask(history)
print(f"\nHUD cells count: {len(hud)}")
# Check if block positions changed
```
Result of the `ls20` call: `HUD cells count: 0` — printed, then never referenced again in that turn's plan.

**Conclusion for Q2: the score lift is not tool usage.** With TransitionGraph never once constructed and hud_mask called twice (both inconclusively, neither in a winning game), whatever changed the model's behavior on `ft09`/`ar25` came from the *prose* around the tools (general advice like "avoid repeating explored actions", "re-check the new board before repeating a plan", "don't mistake a ticking clock for gameplay state") acting as generic priming, or from plain run-to-run variance — not from the agent exercising the new capability.

## 3. Misuse / waste patterns

- **No errors from the helpers.** Grepped every tool-call block across all 25 games (2,001 total) for `NameError`/`AttributeError`/`Traceback` co-occurring with `hud_mask`/`TransitionGraph` code: **0 hits**. The 2 real `hud_mask` calls both executed cleanly.
- **No misreading.** In `ls20` the model printed `HUD cells count: 0`, correctly interpreted it (no HUD chrome detected), and moved on — not a misread, just low-value output.
- **No TransitionGraph rebuild cost** — because it was never built, there's nothing to measure.
- **General error rate unaffected.** `Traceback` count across all games: 12 in duck-mod vs 16 in baseline — noise-level, no evidence the extra prompt confused the model generally.
- **The real waste is pure prompt/context tax with ~0.1% utilization.** The added system-prompt block (~30 lines, +1,835 chars ≈ +450–500 tokens) is repeated on **every turn of every game** (2,001 tool-call turns total), for a feature that was invoked twice. That's paid on every one of the ~2,000 turns for a payoff realized in 2 of them. (Total token budget didn't blow up — 1.50M mod vs 1.54M baseline — only because duck-mod needed 609 fewer total actions/turns; the per-turn tax was more than offset by whatever caused `ft09`/`ls20` to finish faster, which circles back to Q2/Q4: the efficiency gain is real but not attributable to the two new call-sites.)

## 4. Recommendations for injection #3, ranked by evidence strength

1. **(highest confidence) Run ft09/ar25 (and re86/vc33/cd82) multiple seeded repeats before trusting this delta at all.** The entire result is one unseeded run per game against documented σ≈0.4. A ±1-2 game swing this large is exactly what that variance predicts even with a no-op prompt change. This isn't a new tool to add — it's a prerequisite before designing #3 at all, or #3 risks being tuned to noise the same way #2 appears to have been.
2. **(b) Stronger graph-planning advice is *not* supported by this evidence — the opposite.** `TransitionGraph` got a full paragraph of instructions plus a rich `.record`/`.untried`/`.path_to_nearest_untried` API and was **never constructed once** in 2,001 turns. Simply writing better prose about it a second time is unlikely to change that; the tool as specified is too much bookkeeping overhead (call `.record` after every action, derive a `state_key`) for a model running under a tight `python_timeout_seconds: 3` / `context_budget_tokens: 31744` per-turn budget (seen in `[ANALYZER STATUS]` in the transcripts). If this direction is kept, make it near-zero-effort: e.g. auto-record transitions inside the harness's own `action()` call so the model only ever *reads* `.untried()`/`.path_to_nearest_untried()` instead of maintaining the graph itself.
3. **(a) Component-click / centroid caveat (ka59) — not addressed by this data.** `ka59` scored 0.00 in both runs; the transcript contains zero mentions of "centroid" or component-click reasoning specific to that failure mode, so this run gives no evidence either for or against — it's a distinct, unexercised failure class worth a targeted injection, but can't be evaluated from this data. NOT FOUND (no transcript evidence either way).
4. **(c) Budget/level-clock awareness — plausible, weakly supported.** The one clear real-tool signal (`hud_mask` distinguishing HUD/timer chrome from gameplay state) was used exactly once and returned an empty set — inconclusive, not a demonstrated win. Worth keeping the *concept* but the current opt-in, model-invoked design isn't getting exercised; consider making HUD-masking automatic (subtracted server-side before frames are shown) rather than a tool the model has to remember to call.
5. **(d) What the transcripts themselves suggest:** the actual behavioral change in `ft09` (44 vs 92 actions to clear one more level) and `ar25` (unlocked a level baseline never reached) happened with **zero use of either new tool** — so whatever helped is either (i) the plain-English advice lines being read and internalized without ever manifesting as a tool call ("re-check the new board before repeating a plan," "don't mistake a ticking clock for gameplay state" as general heuristics, not API calls), or (ii) sampling variance. Before building injection #3 on top of #2, it would be worth an ablation: ship *only the prose advice* (delete the `TransitionGraph`/`hud_mask` API entirely, keep just the two heuristic sentences) and see if `ft09`/`ar25` still improve — that would cleanly separate "prompt priming works" from "this specific tool works," which the current data cannot.

## Bottom line

**Broad lift or 2-3-game fluke → points to fluke/prompt-priming, not verified tool adoption.** 2 games account for >100% of the net gain, both scored 0 tool calls to the new helpers; the other 23 games are flat or net negative. `TransitionGraph` (0/2001 calls) and `hud_mask` (2/2001 calls, both inconclusive) were built, documented at length, and essentially unused. Recommend re-running with seeds before shipping injection #3, and if the ft09/ar25 lift replicates, ablate prose-vs-API to find out what's actually causing it.
