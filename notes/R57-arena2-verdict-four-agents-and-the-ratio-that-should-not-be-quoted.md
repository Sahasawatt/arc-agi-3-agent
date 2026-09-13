# R57 — arena 2 verdict: four agents, three of my own premises refuted, and the conversion nobody may use

**2026-09-13.** Four agents (opus), one brief, four assigned axes, no contact. Judge = the main
session, which re-ran every cited computation. Brief: `ARENA2.md`. Follows R56.

**Headline: the contest refuted the judge's brief three times, and the three refutations do not agree
with each other about what follows.** Everything below reproduced exactly unless marked.

## Winner: AGENT-2 (TRANSFER)

Not because its axis was productive — it reported BARREN — but because it is the only agent that
falsified the **load-bearing premise of the whole exercise**, and it did so with a control.

| agent | axis | verdict | what it established |
|---|---|---|---|
| **A2** | TRANSFER | barren, premise refuted | **the public→hidden ratio is within-build noise and the LEDGER forbids quoting it**; level totals derivable 22/22 with zero mismatches; bar re-priced in depth space at **+34–41% public, not +70%** |
| A4 | free / null | barren | **public screen MDE = 4.030 pts** ⇒ eleven "closed" families were unresolvable by construction; hidden sd 0.3074 (df 8); the fork tracks the field's growth rate |
| A1 | breadth | barren *as specified, spec wrong* | **the brief's disqualifying 8.76 was priced on a retired build**; on the shipped chassis +1 level everywhere = **16.473** at m=1.14 |
| A3 | throughput | barren by 10–60× | the waste pool caps at ×1.209 against a needed ×1.674; realised conversion 8.7%; three corrections to the brief's own figures |

## The three refutations of my brief, each verified

### 1. A2 — the conversion I built everything on is forbidden (the deepest one)

`ARENA2.md` asserted *hidden ≈ public / 2.68–2.91* as a measured fact and derived the bar, the target
and the "+70%" from it. The LEDGER contains, verbatim:

> **A per-build ratio is unusable and must not be quoted** … *Predicting one build's hidden score
> from its public score is not supported by this data.*

And the whole range is reproduced inside **one byte-identical build at one seed**: `thui-v1-1` drew
hidden **1.29** on public 5.24 (**4.06×**), `thui-v1-1-r2` drew **2.02** on public 4.33 (**2.14×**) —
and `arms.json` calls the second *"byte-identical notebook to thuiv1-1 at the same seed — the repeat
that answers B37, so the pair IS the reading rather than two datapoints."* Within-arm span **89.5%**
against the band's **8.6%**, i.e. the quantity's noise is ~10× the band claimed to measure it.

⇒ **Every public↔hidden conversion in this session is unsound**, including R56's bar table, ARENA2's
~16 target, and **A4's entire bar-pricing** (its 15.97–17.34 public equivalent, and the z-scores that
depend on which side you stand on).

### 2. A1 — the disqualifying arithmetic was priced on a retired build

The brief's *"+1 level in every game is only worth 8.76"* comes from CLAUDE.md's B35, computed on
**`clock2x`** (30 levels, 6.40 public). On the build actually shipped
(`thui-animfast-b71-full25-r1`, 9.5584 public, 39 levels): the completion cap is the **binding** term
in **20 of 25 games**, +1 level everywhere is **18.545** under the cap model and **16.473** at B35's
own shippable m = 1.14, and the per-game marginal spans **2.22 (bp35) … 28.57 (ft09)**.

⇒ depth was never arithmetically disqualified; the judge priced it on the wrong base.

### 3. A3 — three of the brief's own figures were wrong, and one framing inverted

- abandoned generation is **9.1 – 38.7%, median 15.6%** over 19 runs (not 9.1–25.0%), and it is
  computable **offline with no credentials** — the brief said otherwise.
- the zero-action population is **8 game-runs across 5 runs at 83,546–132,587 tokens**; the brief's
  "four runs at 96k–133k" is the subset above an arbitrary 96k floor.
- **the 67.3% STARVED headline is not evidence the wall binds.** `eval/per_level_census.py`'s own
  docstring pre-registers the refutation: *"STARVED is the shape of the corpse, not the cause of
  death."* The brief used it as a cause. Batching is already **3.39 actions per acting model step**,
  so "fewer turns per action" is not headroom either.

## What survives all three, and is the actual finding

**A4's MDE, which is the most useful single number of the session.** Pooled within-build per-game
score-delta sd over the 14 same-build pairs in `arms.json` is **7.1904 (df 336)**, so the paired
25-game screen resolves **4.030 public points at 80% power**. Every non-serving lever this campaign
ever built sits under ~3. ⇒ **the eleven nulls were predicted by the instrument's power**; R55's
"closed by measurement" overstates them, and "closed" should read "unresolvable with this screen".
Buying resolution is unaffordable: k=16 draws per arm reaches 1.01 points for **32 runs / 70.4 GPU-h**.

**A4's hidden-space arithmetic survives A2's refutation because it never crosses the ratio.** Pooled
within-build hidden sd **0.3074 at df 8**, re-deriving the LEDGER's own 0.307/df 8 from scratch; the
bar sits **2.22 above the best draw ever taken against a full observed six-draw range of 1.06 = 2.09
spreads**; and the re-draw lottery is closed — 50 draws buy 11.7–23.7% of the gap, **10¹² draws buy
79–91% and still do not reach it**.

**The growth reading, also ratio-free:** 2026-08-24 → 09-08, top-5 bar **4.968%/day**, this fork
**5.080%/day**, Tufa **6.041%/day**. The fork tracks the field. Closing 1.594× by the 11-02 close needs
**0.8508%/day of excess for 55 days** against a measured **0.112%/day** — 7.6× short — and the fork's
whole rate is **one event (B69), not a rate**.

⚠️ **Superseded in part on 2026-09-13 by [R58](R58-bar-re-dated-and-tufa-is-flat.md), which re-read the
board.** The bar's 4.968%/day survived out of sample (5.0644%/day over the next five days) — but
**Tufa's 6.041%/day did not**: 11.04 → 11.04 flat, with 136 entries and a submission 12 h before the
read. So *"the fork tracks the field"* still holds and *"Tufa compounds at 6%/day"* does not. The bar
is **7.63**, not 5.96, so the 1.594× above is now **2.040×** and the excess needed by 11-02 is
**1.4362%/day over 50 days**, not 0.8508% over 55.

**A2's level-total derivation, with a real control:** the completion-cap identity recovers each game's
total level count uniquely for **22 of 22** anchorable games and matches `game-totals.json` ground
truth with **zero mismatches** (sum **183**). In depth space the bar then needs **+0.426 to +0.506
levels per game**, which on public is **×1.337–1.406 (+34–41%)** — ⚠️ but this still crosses a
public↔hidden bridge, and A2 marks its own hidden-side inputs UNVERIFIED (it assumes the hidden set's
level-count distribution resembles the public one). **So the bar's public equivalent is not known, in
either direction.** That is the honest state, and it is new.

## The convergence, and the one action that costs nothing

**Three of the four proposals have the same prerequisite, reached from three unrelated axes:** the
shipped chassis has no per-level data anywhere, so every instrument that prices a depth lever is blind
to it. Verified four ways: `per-level-census.json` holds **21 runs and zero Flash-Next rows**; there
are **zero `*_p0_events.jsonl` on disk**, so `eval/near_miss.py` prints only its usage line;
`eval/score_shape.py` exits **1** with `CONTROLS FAILED`; and `oracle_ceiling.py`'s `LEDGER_PUBLIC`
holds 19 runs, none of them Flash.

- **A1** proposes exactly this harvest (4 runs × `kernels_output(file_pattern=r"_p0_events\.jsonl$")`).
- **A3** proposes it as a regex extension to `abandoned_tokens.py` plus four census rows, and names the
  two traps: `kernels_logs` has no version argument so `thui-fast-v0`'s two draws cannot both come
  from the slug, and the animfast log carries 14 repeated blocks of which only the last may be parsed.
- **A2's** own lever lists it as a prerequisite — *"without it the current chassis cannot be scored at
  all."*

⇒ **The next action is the harvest, at 0 slots and 0 GPU, needing read-only Kaggle credentials.**
Its refuter is one call: if `kernels_list_files` returns no `_p0_events.jsonl` for those slugs, the
step becomes 1 slot and must be re-decided.

## The prize — A2's instrument, with its own disclosed weakness attached

A `--budget A` mode on `rank_runs.py` that re-scores banked `per_level` data under a per-game action
budget and runs the existing permutation test on that vector. Calibrated, not chosen: **A = 22
actions/game** (29% of the census's 75.5 baseline) is where the public 25 reproduces the observed
ratio 0.3740. It has teeth — re-ranking the 19 banked runs gives **Spearman 0.5702** against the
full-clock order, 13 of 19 move ≥3 places, and it promotes **v16 from rank 9 to rank 1**, the run whose
LEDGER line reads *"Most games scoring ever, best efficiency ever, still lost — breadth does not pay"*
and which has the census's highest reach at 19/25.

⚠️ **A2 disclosed the weakness itself, measured:** the statistic is **noisier** than the public mean it
would replace (27.9% vs 19.0% spread on the byte-identical pair), and its top-1 pick is unstable
across A = 15–30. So it is an ordering over a promoted **set**, pooled over ≥2 draws — never a single
winner. And its calibration constant is derived from the same forbidden ratio A2 refuted, which is a
tension A2 states and does not resolve.

## What this note does not do

No ticket closed, no MAP row added, no build proposed. It does not endorse spending a slot. It records
that **this session's own conversion between public and hidden was unsound, so the bar's distance is
unknown rather than known-far or known-near** — and that the cheapest next step is the one three
independent axes converged on.

⚠️ **Scope of the corrections:** R53–R56 and the external `ARENA.md` / `ARENA2.md` /
`OPTIMIZE-findings-2026-09-13.md` all quote the 2.68–2.91× conversion somewhere. This note is the
authoritative correction for every one of them; they are not individually amended, because the
conversion appears in them as context rather than as a load-bearing step — **except** R56's bar table
and ARENA2's target, which are load-bearing and are therefore void.
