# R55 — every conditional lever is already built, the one positive is its broken half, and B24's revisit condition cannot fire on the thing that now matters

**2026-09-13, offline, 0 slots, 0 GPU.** Banked fixtures + `eval/rank_runs.py` (seeded, deterministic)
+ the LEDGER and `thui-act/build_notebook.py`. Follows [R53](R53-the-draw-decides-depth.md) and
[R54](R54-score-is-depth-and-three-budget-levers-die.md).

## 1. The lever census — 8 built candidates against the B48 chassis

Every banked candidate that is not a serving swap, paired against `thuiv3-pool` (the arm CLAUDE.md
says `thui-rank` / `thui-reflect` / `thui-gemma` build on):

| candidate | what it is | Δ score | Δ levels | p | verdict |
|---|---|---|---|---|---|
| `thui-act-v1` | ACT-NOW breaker, **stage 2 inert (bug)** | **+1.12** | **+2.75** | 0.3177 | NOT-DIST |
| `thui-compact-v1` | B65 compaction of dropped history | +0.49 | +0.75 | 0.6794 | NOT-DIST |
| `thui-reflect-v1-1` | B62 reflection memory, 2nd build | −0.01 | −0.25 | **0.9978** | NOT-DIST |
| `avo-pool` | the AVO arm on duck (2 runs pooled) | −0.02 | −2.25 | **0.9851** | NOT-DIST |
| `thui-prior-v1` | B60 online exploration prior (CNN) | −0.57 | −4.25 | 0.6841 | NOT-DIST |
| `thui-rank-v1` | B61 prior as veto/ranker | −0.82 | −5.25 | 0.3862 | NOT-DIST |
| `thui-act-v2` | ACT-NOW breaker, **stage 2 armed** | −1.92 | −5.25 | **0.0309** | **WORSE** |
| `thui-reflect-v1` | B62, 1st build | −3.0 | −11.25 | — | **WORSE** |

```bash
for c in thui-act-v1 thui-act-v2 thui-compact-v1 thui-prior-v1 thui-rank-v1 \
         thui-reflect-v1 thui-reflect-v1-1 avo-pool; do
  python3 eval/rank_runs.py eval/fixtures/thuiv3-pool.json eval/fixtures/$c.json
done
```

Two of these are the only **significant** results in the set and both are losses. `avo-pool` at
p = 0.9851 with a 10-up / 10-down split and `thui-reflect-v1-1` at p = 0.9978 are as close to
perfectly null as this instrument can report.

**The families this closes by measurement, not by argument**: online prior (B60), prior-as-veto
(B61), reflection memory (B62), compaction (B65), the AVO harness on duck, and the ACT-NOW breaker
(B70). ⚠️ Every p here is an **underpowered null**, not a proof of no effect — but six families in a
row landing inside the band is the same shape the LEDGER already records as *"11 modifications of
v10, 0 above the band"*.

## 2. The one positive delta is the version whose second half was broken

`thui-act-v1` has the best Δ of any non-stack lever in the repo (+1.12, +2.75 levels), and it is the
build where the intervention **half did not run**. From `thui-act/build_notebook.py` (the v2 cell-0
text, verbatim):

> **v2**: v1 (public 5.51, in the band) never armed stage 2 — the solver passes engine action names
> (`ACTION1`…) and the wrapper filtered them against model names; v2 maps through the bundle's
> `to_model_action` first and logs a withheld action when no simple action exists.

The two stages are, by the builder's own definition: **stage 1** = an ACT-NOW directive on the next
prompt after K dead turns, *costs no action*; **stage 2** = one action executed *for* the model if
two further turns still execute nothing, ≤3 per level and ≤25 per game.

So the pair reads:

- **v1 = stage 1 only → +1.12 (p = 0.3177)**
- **v2 = stage 1 + stage 2 → −1.92 (p = 0.0309, the significant loss)**

And stage 1 did fire — the LEDGER records it: *"Directive fired 35×, obeyed 51% (59/116), dead-turn
rate **38%** vs the chassis's **39–41%**"*. It moved the mechanism it targets by **one to three
points**, which is not a mechanism working; so v1's +1.12 is a draw of the baseline distribution, not
a lever. Reading the table without the builder would have promoted the broken build for a second
draw. That is the slot this note saves.

⚠️ **A discrepancy to record, not load-bearing**: the LEDGER row for this run reads *"10 up 12
down"*; `rank_runs.py` printed **12 up / 10 down** here. Mean (+1.12), levels (+2.75) and p (0.3177)
match the row exactly, so one of the two transcribed the sign split in the other order.

## 3. Why stage 2 had to lose — the scorer's asymmetry, in arithmetic

`level_score = min(115, (H/A)² × 100)` and **only COMPLETED levels count**. Two consequences the
builder half-states and the measurement confirms:

- **Actions on a level that is never completed are free.** That level scores 0 whatever was spent.
- **Actions on a level that IS completed cost quadratically** — the builder computed the price of
  stage 2 in advance: `(b/(b+3))²` on a 30-action level is **−17%**. It shipped anyway, and the
  −1.92 / p = 0.0309 is that number arriving.

But the same curve cuts the other way once you are already past the baseline, and nobody has used
this: the penalty **decays**. At A = 3H a level scores 0.11; at A = 6H it scores 0.028. Doubling the
spend from 3× to 6× the human baseline costs **0.08 of one level's weight**, while completing it
unlocks the next level at a **higher weight** (weight = level index). So the score function rewards
grinding a level far past the human count much more than giving up on it — and the corpus says
the agent rarely gets the chance: **STARVED 67.3% vs STUCK 30.8%** (B52). Most game-runs die to the
wall, not to the penalty.

⚠️ **This is arithmetic on the published formula, not a measurement.** It predicts that a
persistence-biased policy is cheap, and predicts nothing about whether the agent can convert extra
actions into a clear — which is exactly what B43 tried to answer and could not.

## 4. B24's revisit condition cannot be triggered by upstream's score

B24 decided **"Stay on the anim bundle"**, and its escape clause is: *"Revisit only if a future
change needs a seam the string-replace cannot reach."* That is a **mechanical** trigger — a seam
problem. It contains no score term.

Dates, verified with `git log -S` plus a positive control (`B71` → 2026-09-11) and a negative control
(a string not in the file → empty):

- **B24's text entered the MAP on 2026-08-24** (`b9747f63`).
- **B69's row records, dated 2026-09-08**: *"the top-5 bar rose to **5.96** … while `Tufa Labs` — the
  upstream this line forks — reads **11.04**, having more than doubled its own hidden score in the
  window our fork went 1.70 → 3.21."*

So the decision is 15 days older than the reading that matters to it, it was taken on a **feature
comparison** of one upstream revision (`6d8e3dd`), and **no condition inside it can ever fire on
"upstream got much better."** Meanwhile the only lever family that has ever cleared this campaign's
own significance bar is exactly a change of what runs underneath: B6 (model swap, 2.41 → 4.55) and
B69 (serving swap, → 8.69 public / 3.21 hidden, p = 0.002).

**This note does not reopen B24** — that is the maintainer's, like B71's close. It records that the
premise has moved and that the trigger as written cannot notice.

## 5. Ranked by evidence

1. ✅ **DONE 2026-09-13 — and both halves answered NO.** The framework is vendored at
   `localrig/tufa-arc-agi-framework/`: `diagnostics.py` averages passes (*"per-pass mean"*, line
   422), so the +39% oracle is **not** purchasable at cell 15; and `actions_per_level` is cumulative
   (`game.py:259`), so a RESET does **not** re-zero a level's actions and "explore freely, then
   execute cleanly" is not expressible. Details and the corrected "scorer is not vendored" claim are
   in R53's 🟢 block; the offline scorer and the clip counts are in R54. **The next-cheapest item is
   now #2.**
2. **Re-examine the fork against current upstream** (§4). Class of lever: 2 wins from 2 attempts.
3. **B79 quantization counterparts** — same class, already scoped at pinned revisions.
4. **A second hidden draw of the B69 build** — hidden is n = 1 and `v10` swung 22% on byte-identical
   code. No rebuild, one slot.
5. **Do not spend a slot on another solver-side patch.** §1 plus R54 §3 close eight families; three
   of those were candidates this session generated and then killed on its own numbers (budget
   reallocation, the early-exit rule, and B61's veto — which turned out to be `thui-rank-v1`,
   already built at −0.82).
