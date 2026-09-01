# Every run this campaign produced — what it scored and why

Assembled 2026-08-22 from the `summary.txt` and `benchmark.json` of every downloaded run.
Public = the 25-game commit-run mean. Hidden = the 110-game leaderboard draw, only for the
four builds ever submitted.

## The table

| run | public | hidden | scoring | levels | actions | act/lvl | Mtok | bundle | what changed, and why it landed there |
|---|---|---|---|---|---|---|---|---|---|
| **v10cal** | **4.71** | — | 18 | 28 | 1597 | 57.0 | 2.03 | anim | rerun of v10; the campaign's best number |
| **v25** | **3.69** | — | 16 | 22 | 1341 | 61.0 | 1.82 | anim | B37's sampler pin — `LOCAL_ANALYZER_SEED=20260825`, temperature left at the harness default. **P1 and P2 both pass**: wall **2h 12m 30s** (thui-v1 was 2h 12m 35s, so not the silent-worker-death shape) and `taaf_setup_env.json` from the run carries `LOCAL_ANALYZER_SEED: 20260825` with `LOCAL_ANALYZER_TEMPERATURE: 0.6` untouched. `rank_runs.py` vs **v10cal p=0.5046**, vs **clock2x p=0.2919**, both NOT-DISTINGUISHABLE — a fifth in-band sample of the v10 family, which is what P1 predicted. ⚠️ **This run is NOT v10+seed and must not be quoted as one.** The builder read `SRC_NB=duckmod` and never replaced cell 12, so the notebook (**sha256 `1504012d`**) carried duckmod's 14,355-char patch block; the corrected build is **`d5473ba8`** and has never run. **Measured what that leak actually cost**, over 1,105 analysis turns with the R33/R39 section discipline: the patch is **additive only — it does not wrap `action`**, it uses that line as an anchor and injects `hud_mask` + `TransitionGraph` beside it. Adoption is **TransitionGraph 0.0%** and **hud_mask 0.7%** (8 turns across 5 games) against an `action()` positive control at 32.6% and a negative control of 0 — and the probe proves it is not blind, since the SYSTEM PROMPT names `TransitionGraph` in all 1,105 turns. **So the real confound is not the tools, it is the PROMPT**: 16,039 chars against clock2x's 14,204, i.e. **+1,835 = +12.9% every turn** to advertise two tools nobody calls — R6's Mode-2 law and B32's lesson in one run. **P2 is unaffected** (a seed does not travel through the prompt); **P1 is conditional** — 3.69 belongs to a build with a longer prompt than v10. **P3 (spread) is untested and now needs two runs of `d5473ba8`, which is a different build from this one.** Kernel `sahasawatt/taaf-duck-v25` v1, 2026-08-24. `results/v25-summary-20260824.txt` |
| **thui-v1-1** | **5.24** | **1.29** | 15 | 25 | 1325 | 53.0 | 2.10 | anim | **B37's sampler pin on the CLEAN arm** — v10 exact + `LOCAL_ANALYZER_SEED=20260825` in `setup_env`, temperature untouched at the harness default. This is the arm `v25` above was meant to be: `thuiv1/` sources its own cell 12, so it cannot carry v25's `SRC_NB` defect, and the v1-0→v1-1 diff is **AST-verified as ONE executable change** (cells `[8, 12]` differ; cell 12 is AST-identical, +9 lines of docstring prose, both dumping to 12,980 chars after stripping bare-string `Expr`; controls cells 0 and 14 byte-equal). **All four gates pass.** **P1**: wall **2h 12m 52s** (v25 2h 12m 30s, thui-v1-0 2h 12m 35s — not the silent-worker-death shape); seed literal 1 hit in the setup echo against a `LOCAL_ANALYZER_TEMPERATURE` control at 1, and the run's own `taaf_setup_env.json` confirms it independently (`SEED=20260825`, `TEMPERATURE=0.6`, `MAX_OUTPUT=0`, `UPSCALE=4`). **P3 adoption = 0 calls in 0 of 25 games with a non-zero control (`segmentation`=369)** — `clock2x`'s shape exactly, so this run really is `v10`+seed and not `duckmod`+seed. Against v25's **hud_mask 0.7% / TransitionGraph 0.0%** that is the contrast the two arms exist to draw. **P4**: 25 of 25 `*_usage.jsonl`. `rank_runs.py` (`--selftest` cleared both poles in the same session first): vs **v10cal p=0.8001**, vs **v25 p=0.3094**, vs **clock2x p=0.5868** — all NOT-DISTINGUISHABLE, a **sixth** in-band sample of the v10 family. ⚠️ **The mean rose while the levels FELL** (4.71→5.24 but 28→25, 8 up / 9 down / 7 flipped) — noise, not a lever; and 5.24 clearing the old `[2.82, 4.71]` band is a **screen, not a verdict**, exactly as clock2x's 6.40 was. ⚠️ **The band is now `[2.82, 5.24]`, and that widening is ARITHMETICALLY TRIVIAL, not evidence against B37** — a band is a min/max over samples, so adding one can only widen it or leave it. **B37 is still run 1 of 2**: the reading it needs is the spread across ≥2 runs of THIS build, and nothing here measures that. The seed is proven **SENT**, never **DETERMINISTIC** — batched vLLM is not bit-reproducible across differing batch compositions and 25 games share one server. **Rode free — P5, the v25 free rider, is answered**: under duckmod's cell 12 `ft09` and `bp35` emitted **0** and **1** actions against a floor of **9** anywhere in 125 game-runs; here they are **86** and **63**, i.e. normal, so that stall belongs to the **duckmod prompt**, not to the harness or the sampler. ⚠️ **`v10cal`'s action total is 1597** — the `1285` that appears in older prose is `v10out`, a different run, and swapping them puts tok/action out by 24%. Kernel `yocybercode/thui-v1-1` v1, 2026-08-25. `eval/fixtures/thuiv1-1.json`. **HIDDEN 1.29** (`55773197`, read 2026-08-26 with `55662656`/1.70 as the control in the same call) — the **lowest** of the v10 family's four draws, and it ranks nothing: 0.03 from draw 2 and 0.09 from draw 3, against a ~0.4 floor. Since B37 proved the seed inert this is a fourth draw of one build, not an arm; the family mean falls 1.51 → **1.42**. See CORRECTION 3. |
| **thui-v1-1-r2** | **4.33** | **2.02** | 14 | 23 | 1260 | 54.8 | 1.94 | anim | **The repeat that answers B37** — byte-identical notebook to `thui-v1-1`, same seed `20260825`, so the pair IS the reading rather than two datapoints. `rank_runs.py` 5.24 → 4.33: delta −0.91, levels 25 → 23, 6 up / 8 down / 5 flipped scoring↔zero, p = **0.7318 NOT-DISTINGUISHABLE** (`--selftest` cleared both poles first — `dadd293` changed the instrument after run 1 was ranked). **The pin reproduces nothing: 0 of 25 games identical on score+levels+actions, 0 of 25 transcripts identical** after normalising timestamps and tool-call ids. Rows whose scores match exactly got there by different paths (`lf52` 1.82/1.82 on **50 vs 42** actions). The split is at the FIRST response, not accumulated: across the first request of every game `prompt_tokens` is identical **25/25** (the control — same board, same prompt) while `completion_tokens` matches only **6/25**, and `ft09` opens with `reasoning_chars` **527 vs 73**. Seed delivery verified by source at all four hops to `payload["seed"]` (`openai_compat.build_chat_payload`, vllm branch, seed ≥ 0); P1 passed, P3 adoption **0 of 25** control 448, so both runs are v10+seed and are the same subject. ⚠️ Mechanism INFERRED not measured — the run's own `vllm-openai-server.log` shows `enable_prefix_caching`, `enable_chunked_prefill`, `cudagraph_mode=FULL_AND_PIECEWISE`, `fp8`: a per-request seed pins the sampling RNG, not the logits it samples from. ⚠️ Nothing in this run observes the request body, so runtime arrival at the server is unproven (server log 0 seed lines — its `seed=0` is the ENGINE seed; usage probes 0, control 1306). ⚠️ The apparent spread narrowing (0.91 against `v10cal`↔`v19` 1.89) is one pair against one pair and ranks nothing. P5 second sample: `tr87` 57 → **0** actions (63 requests all at turn 0), `bp35` 63 → **1**, below the floor of 9 — the locked-family shape B38 targets. ⚠️ **CORRECTED 2026-08-27 (Watchara, `notes/B45-the-gap-is-not-in-flight-2026-08-27.md` in `Knowless-Crew/arc-agi-pub` #146)** — this row first said those 63 requests ended `__exception__:ReadTimeout`. Read from the run's own 63 usage rows: **62 ended `tool_calls` and exactly ONE was a `ReadTimeout`.** So `tr87` is not a game whose requests failed; it is a game where 62 requests **succeeded** and the game emitted no action. `bp35` is the same shape one step down — 109 `tool_calls`, 1 action. Kernel `yocybercode/thui-v1-1-r2`, 2026-08-25, 2h 12m 39s. Write-up `notes/B37-run2-the-pin-does-not-reproduce-2026-08-25.md` in `Knowless-Crew/arc-agi-pub` (#90). **HIDDEN 2.02** (`55832247`, 2026-08-28 03:14 UTC, pinned `scriptVersionId=344816821` — the real version-1 run; the provenance gate's first live pass): **NEW BEST, board 1.70 → 2.02.** This was the 08-28 slot's pre-registered σ measurement, and it landed in the bottom band of its own table: |2.02 − 1.29| = **0.73 ≥ 0.55** → *"σ is larger than assumed; every hidden figure on record is weaker evidence than it has been written up as"* (`which-kernel-gets-the-slot-2026-08-28.md` §5, Knowless-Crew/arc-agi-pub). Same-build pool is now **5 draws** (1.29–2.02): mean **1.542**, sd **0.313** — vs the 0.1887 every prior write-up used. Shrink 4.33/2.02 = **2.14×**, the ratio table's new low. |
| **thui-v2-0** | **2.86** | — | 18 | 23 | 1425 | 62.0 | 2.08 | anim | **B39's retrieval kill-switch — the removal buys nothing measurable.** Ported from the post-anim upstream, which turned `animation_retrieval` OFF by default because *"across Experiments 3 and 4 it bought no score"* (R39); our `anim` bundle has the retrieval and no flag to disable it, so the patch supplies one. **P1 read off the run's own artifacts, controls first**: the driver log carries `thuiv2: retrieval OFF (animation_record -> None), prompt -3 advert lines, 737 chars; awareness lines kept` **exactly once** at t=422.1s, with `LOCAL_ANALYZER_TEMPERATURE` and `MULTIMODAL_UPSCALE` at 1 each as positive controls and a negative control at 0. ⚠️ **The 25 per-game logs carry neither the marker NOR the controls**, so their zeros are a fact about which file the driver writes to and not about the patch — checked before the marker was read, because a 0 on the marker alone is exactly what a failed injection returns (Watchara's reading, in `f5c31cf`; the by-value trap this row was most afraid of did not fire). ⚠️ **This build is NOT seed-pinned** — `taaf_setup_env.json` has no `LOCAL_ANALYZER_SEED` at all while `LOCAL_ANALYZER_TEMPERATURE` sits at 0.6 as the control — so **`v10cal` is the one-variable comparison and `thui-v1-1`/`-r2` cross TWO** (retrieval off AND sampler unpinned); read the v10cal line, not the thui ones. `rank_runs.py` (`--selftest` cleared both poles in the same session first): vs **v10cal 4.71 → 2.86 (−1.85), levels 28 → 23, 6 up / 12 down / 8 flipped, p = 0.1646** · vs **clock2x p = 0.059** · vs **thui-v1-1 p = 0.2463** · vs **thui-v1-1-r2 p = 0.4056** (levels DEAD LEVEL at 23-23, and 10 up / 6 down — v2 wins more games while scoring lower, which is the noise signature) · vs **v25 p = 0.4934**. All NOT-DISTINGUISHABLE, an **eighth** in-band sample of the v10 family, and 2.86 sits inside `[2.82, 5.24]`. ⓘ One column reads oddly and is logged as a quantity to watch rather than as a finding: **scoring games 18 ties `v10cal` for the most in the family** (clock2x 17, v25 16, v26 15, thui-v1-1 15, -r2 14) while the mean is near the bottom — breadth without depth. On n=25 with every pairwise verdict NOT-DISTINGUISHABLE, nothing here separates that from noise. ⚠️ **`p = 0.059` against clock2x is the closest this campaign has come to α = 0.05 and it still does not clear it** — that pair is also the widest mean gap on record (6.40 → 2.86), which is what a band this wide costs. **Watchara's framing, kept: NOT MEASURABLE, never "no worse"** — at p = 0.16 the −1.85 and a 0 do not separate, so the row closes as a build candidate and not as a demonstration of equivalence. Wall **2h 12m 41s** (the v10 clock, not the silent-worker-death shape; `summary.txt` and `benchmark.json` agree independently on mean, actions and duration), 25 of 25 games `gave_up` at the wall as always. Kernel `yocybercode/thui-v2-0` v1, 2026-08-25. `eval/fixtures/thuiv2-0.json` — built through `rank_runs.load()` rather than by re-deriving the fields, and it reproduces every figure `f5c31cf` published, to 4 decimal places on both p-values. Design note `notes/R42-the-retrieval-switch-is-built.md`. ⚠️ **What retrieval COST in tokens is still unmeasured** (R39's open item), and the removal was never ranked on hidden. |
| **thui-v3-0** | **4.01** | **1.63** | 17 | 23 | 1401 | 60.9 | 2.02 | anim | **B48 — the turn budget tripled: `LOCAL_ANALYZER_YIELD_SECONDS` 60 → 180, and nothing else.** Base is `thui-v1-1`, so the seed stays `20260825` and this is a ONE-variable comparison against the only two-run same-build baseline on record. The literal lives in the bundle's `setup_commands.json`, not the notebook, so the build adds one link to cell 8's existing `.replace()` chain and asserts every other cell byte-equal. **P1 passed on THREE readings, not one**: `'LOCAL_ANALYZER_YIELD_SECONDS': '180'` present, the OLD `'60'` **absent** (two live values race and the run measures neither — the builder asserts this in-kernel too), `LOCAL_ANALYZER_TEMPERATURE` control present; in-kernel teeth line `thui-v3-0: YIELD_SECONDS 60 -> 180 (B47/R44)` at t=422 s, and those asserts run BEFORE the benchmark, so a missed injection kills the kernel rather than scoring normally. `rank_runs.py` (`--selftest` cleared both poles in the same session first): vs **`thui-v1-1` 5.24 → 4.01, levels 25 → 23, p = 0.5370** · vs **`thui-v1-1-r2` 4.33 → 4.01, levels DEAD LEVEL 23-23, 9 up / 3 down, p = 0.8145** · vs **`v10cal` 4.71 → 4.01, levels 28 → 23, p = 0.4759** — all NOT-DISTINGUISHABLE, a **ninth** in-band sample of the v10 family, and the band `[2.82, 5.24]` does not move. **NOT MEASURABLE, never no-worse** — at p = 0.54 the −1.23 and a 0 do not separate. 🔴 **The run's real value is `notes/R47-the-yield-gate-moves-with-the-knob.md`: R44's gate is now proven by INTERVENTION.** R44 §3 inferred it from `tool_agent.py` plus one setting, which cannot separate *the gate is YIELD_SECONDS* from *turns are short*. This run breaks the 60 s bound on **96 of 297** multi-request turns while never violating 180 s across all 297, and each run's bound sits flush against its own knob — max `cum(but last)` **59.4 s of 60** (r2) and **178.8 s of 180** (here). Every mechanistic prediction landed: `analyze()` calls **1,070 → 719**, requests per call **1.22 → 1.67**, turns reaching iteration 2 **186 → 297**, single-request turns blowing the gate **91.0% → 62.6%**, requests over budget **70.5% → 29.9%**, and median completion ÷ budget **1.74× → 0.60×** — the inversion R44 named. So the agent really did deliberate longer per decision (tok/action 1,272.6 on v10cal → **1,438.8**) and cleared the same levels. Third member of the more-reasoning-per-decision family to close this way, after `B25` (MoE) and `B34` (double clock). ⚠️ **R44 §6's refusal is confirmed and WORSENS at the second point** — the first-request-time curve over-predicts headroom **43% at Y=60 and 53% at Y=180**, same cause both times (95% / 96% of the gap ended on `tool_calls`, i.e. correctly); anyone pricing a further increase from it over-states it. ⚠️ **n = 1 → 2 for every R44 figure** (25 of 25 usage probes), but these are two runs at two SETTINGS — nothing here estimates same-setting spread, and B37 already put one build's two runs 0.91 apart. ⚠️ `__exception__` rows **30 → 38** (2.3% → 3.2%); the ReadTimeout cluster R44 flagged is still uninvestigated and slightly larger. ⚠️ **Why the extra depth converts to nothing is untouched** — usage rows cannot answer it, transcripts can. Kernel `yocybercode/thui-v3-0` v1, 2026-08-27, wall ≈ 2 h 21 m. `eval/fixtures/thuiv3-0.json` — built through `rank_runs.load()` rather than by re-deriving the fields, and it reproduces all three p-values from `benchmark.json` exactly. Instrument `scripts/b27/r44_turn_budget.py`, whose `--selftest` re-derives 15 published R44 figures from the n=1 corpus and refuses to run otherwise. Page `agents/thui/v3/v3-0.md`. |
| **thui-v3-0 v3** | **4.52** | **1.59** | 14 | 23 | 1635 | 71.1 | 1.93 | anim | **The same kernel re-run, and the second within-build pair the campaign needed.** Not a new build and not a new slug: `yocybercode/thui-v3-0` **version 3**, pushed 2026-08-28 20:24 UTC and started 20:30:44 by its own `summary.txt`, 2h 21m 36s on an RTX Pro 6000. Its `taaf_setup_env.json` carries `YIELD_SECONDS=180`, `SEED=20260825`, `MAX_OUTPUT=0` — B48's lever unchanged. **Why it was run at all was housekeeping, not science**: every `yocybercode` kernel sat at `Version 2 of 2` where V2 was the cell-0 retitle quick-save (7-9 s, ZERO output files), so the only submittable artifact was a Tufa-headered V1 reachable via `--submit-older`. Re-running mints a V3 that is both our-headered and output-bearing; Version History reports **`Diff +0 -0` against V2**, so the corrected markdown rode the re-run with no second edit and that kernel's fork is closed for good. ⚠️ **`Version N of M` reports the version BEING DISPLAYED, not the latest** — measured in an anonymous pane AND in the owner's logged-in browser, which agreed exactly at `Version 2 of 3` after a forced reload, because the default display stays on the last version saved from the editor. The `>` beside it collapses the sidebar; it is not a version stepper. V3 is reached via the pill -> `...` on the Version 3 row -> **View full version**, and only there does the control read `Version 3 of 3`. This is a trap for every `--submit-older` decision, since `2 of 3` is not evidence that a later version is unsubmittable. **HIDDEN 1.59** (`55856045`, 2026-08-29 00:21:04 UTC; G2/G3/G4/G5 all passed and no `--submit-older` reason was needed). **The pair is 1.63 vs 1.59, range 0.04** — against the v10 family's `thui-v1-1` <-> `-r2` at **0.73**. Under the sd 0.313 that pool gives (sd_diff 0.443), P(|diff| <= 0.04) = **7.2%**. ⚠️ **This does NOT show sd is smaller here**: each build has exactly ONE pair and n=2 estimates no spread, so 7.2% is unlikely-but-ordinary and the v10 pair could equally be the outlier. What the two pairs together refute is treating 0.313 as a constant of the channel. ⚠️ They are also not the same experiment — the v10 pair is byte-identical code at one pinned seed, while V1 and V3 differ by cell-0 markdown (`+43 -20` at V2, `+0 -0` at V3): text only, no executable change, but not the identical-artifact comparison `-r2` was. Public 4.518 vs V1's 4.01 with levels DEAD LEVEL at 23-23, inside `[2.82, 5.24]`, ranks nothing. Board unmoved: Kaggle keeps BEST and 1.59 lost to 2.02. Write-up `notes/which-kernel-gets-the-slot-2026-08-29.md` §6 in `Knowless-Crew/kc-arc-agi-pub` (#209). |
| **thui-v4-0** | **1.92** | — | 12 | 16 | 1131 | 70.7 | 1.27 ⚠️ | anim | **The spread lever — `LOCAL_ANALYZER_TEMPERATURE` 0.6 → 1.0 — works as a mechanism and fails as a build.** Base `thui-v1-1`, seed kept at `20260825`, one variable. Read in the pre-registered order. **P1 ✅**: marker at t=7.6s, `'1.0'` in the setup echo = 1, `'0.6'` = 0, seed ×2 and `MULTIMODAL_UPSCALE` as positive controls, duckmod marker and `AssertionError` = 0. ⚠️ The first P1 probe reported the marker ABSENT — it searched the raw kernel-log JSON, where `>` is escaped `\u003e`; decode the records before counting, or a passing build reads as a failed injection. **P2 ✅** 2h 12m 36s. **P3 ❌ 1.92 — the lowest 25-game public of the anim family, below the floor of `[2.82, 5.24]`**, levels 16 (previous family low: 20), scoring 12. `rank_runs.py` (`--selftest` first): vs **`thui-v1-1` p=0.1168** and vs **`-r2` p=0.1722** NOT-DISTINGUISHABLE — but vs **`v10cal` p=0.0162 WORSE** and vs **`clock2x` p=0.0172 WORSE**, the campaign's third and fourth distinguishable results, both in the wrong direction (`v20`, `v21` were the first two). 🔴 **CORRECTED 2026-09-01 — that sentence rests on a pairing `rank_runs.py` now REFUSES, and the honest verdict is NOT-DISTINGUISHABLE.** `v10cal` is one of four declared members of the `v10` arm (`eval/fixtures/arms.json`), so since `B57` (#105) `rank_runs.py fixtures/v10cal.json fixtures/thuiv4-0.json` exits 4 with the pooling remedy printed. Pooled instead, measured at `6e6a29e` with `--selftest` clearing its six controls first: **all 25 games 4.28 → 1.92, p = 0.0613** · **the 21 games that played 3.23 → 2.29, p = 0.3867**, both NOT-DISTINGUISHABLE, against a positive control on the same 21 (`v20`, p = 0.0001 WORSE) proving the subset test still has teeth. ⚠️ The played-21 subset is post-hoc **and biased toward `thuiv4-0`** — the four dropped games are dropped because v4 failed them and one (`ft09`) is the baseline's best, so the pooled baseline falls 4.28 → 3.23 while v4 loses nothing; both directions agree anyway. ⚠️ **`2.29 < 2.82` is also a unit mismatch** — `[2.82, 5.24]` is an all-25 band and 2.29 is a 21-game mean; on the matched 21 the baseline arm's own members span **2.42 – 4.29** (`thuiv1-1-r2` 2.4179 · `v19` 2.6363 · `v10cal` 3.5936 · `thuiv1-1` 4.2897). The `clock2x` pairing survives the gate (`clock2x` is not a declared arm member) but `clock2x` is not this build's base, so it was never the one-variable comparison. **What stands: the pre-written kill rule fired correctly as a SCREEN on the all-25 mean, and the screen never converted into a distinguishable verdict** — the same reading this file already applies to `clock2x`'s 6.40 and `thui-v1-1`'s 5.24, and it cuts both ways. Consequence for the run plan: the `0.8` retry named below has **lost its trigger**, because *the mean cost at 1.0 is too high* is now unmeasured; `B53`'s rerun at 1.0 unchanged is unaffected, since its subject is the stall count rather than the score. Write-up `notes/thui-v4-0-recheck-2026-09-01.md` in `kc-arc-agi-pub`. Per the build's own pre-written rule — *below 2.82 → mean cost too high, kill or retry at 0.8* — **this configuration is dead at 1.0**. **P4 ✅ and it is the finding**: within-run `completion_tokens` CV **115.3%** (n=1,890) against T=0.6's four-run range **95.3–102.5%** — **+12.8 points above the maximum**, so the sampler moved; not the seed's failure shape. Mean completion halved (1,806–2,056 → **1,099**) and requests rose ~1,300 → **1,890**: shorter answers, more of them. ⚠️ **P4's own threshold was too shallow, recorded before this run's result was read**: the 6.6-point bar came from `thui-v3-0`'s CV delta, but the four T=0.6 runs span **7.2 points** among themselves (95.3 / 98.5 / 101.9 / 102.5), so +6.6 sits INSIDE same-build noise and only v4's +12.8 clears the honest bar. An effect smaller than ~7 points would have been unfalsifiable at n=1. ⚠️ **Free observation, n=1**: abandoned generation **38.7%** — the highest of any 25-game run (previous max `v14` 25.0%), median per-game 19.6%. At T=1.0 more of the budget died in flight-that-returned. ⚠️ What n=1 still cannot say: the variance gain this lever was priced on (43.2% at +50% spread, mean flat) — a single run has no spread, and 1.92 says the *mean flat* premise is likely false at 1.0; whether 0.8 keeps enough of the CV shift while staying in-band is exactly the retry the kill rule names. ⚠️ **AMENDED the same day (Watchara, `notes/B-thui-v4-0-temperature-result-2026-08-27.md` in `arc-agi-pub` #182) — half the drop is a DEFECT, not the lever**: **four of 25 games emitted zero actions and zero tokens** (`vc33` `sp80` `cd82` `ft09`, run indices 10/14/17/21, scattered — not budget exhaustion, later games ran full clocks), against **one such game in 175 game-runs** across seven prior runs. `ft09` is the base's highest scorer; the four are worth **1.64 public = 49% of the 3.32 drop**. So do NOT quote *"temperature 1.0 costs 3.32"* — the defensible magnitude is **−47% on the 21 games that played** (post-hoc subset, labelled as such). The kill verdict stands either way: 2.29 on the played-21 is still below the 2.82 floor. **Open and new**: what produces a zero-action game — 4/25 here vs 1/175 historically; either T=1.0 breaks something upstream of the first action or this run met an unrelated fault. The 0.8 retry the kill rule names would also count the zeros, one discriminator for the price of one GPU slot. Kernel `yocybercode/thui-v4-0` v1, 2026-08-27. `eval/fixtures/thuiv4-0.json` — built through `rank_runs.load()` on the run's own `benchmark.json` (the `[finished]`-line derivation rounds scores to 2 decimals and broke `score_shape`'s cap-inference controls 6/7; full precision passes all 7). |
| **thui-v5-0** | **3.08** | — | 15 | 22 | 1333 | 60.6 | 1.57 | anim | **`thui-v3-0` plus ONE change: `LOCAL_ANALYZER_TEMPERATURE` 0.6 → 1.0 — the last cell of a 2×2 assembled out of runs built for other reasons.** **P1 ✅ on TWO independent halves**: temperature `'1.0'` present / `'0.6'` absent, AND yield `'180'` present / `'60'` absent, the second half carrying a control independent of its subject plus a fake-key negative control at 0 — half A's control is its own subject key and can only catch an empty log. In-kernel teeth present. **Score ranks nothing**: 3.08 is inside `[2.82, 5.24]` and every comparison is NOT-DISTINGUISHABLE (`thuiv3-0` p=0.524, `thuiv4-0` p=0.3075, `thuiv1-1` p=0.2526, `v10cal` p=0.2326; `--selftest` cleared both poles first). **P2 — 0/25 zero-action games, and the grid reads the opposite way round from the proposal**: with one instrument over `actions == 0`, yield 60 / temp 0.6 = 1/125, yield 60 / temp 1.0 = 4/25, yield 180 / temp 0.6 = 0/25, yield 180 / temp 1.0 = 0/25. Fisher two-sided: **temperature at yield 60 is the only significant cell, p = 0.0028**; whether yield 180 *removes* the stall is NOT established (4/25 vs 0/25, p = 0.1099), and three of four cells are n=1 so *"yield rescues"* and *"`thui-v4-0`'s 4/25 was one draw"* are not separable. ⚠️ The first census used a `history` walker against fixtures that carry no history: every run read `0/0`, every test returned `p = 1.0000`, nothing errored, and only the failing positive control (`thui-v4-0` must read 4) exposed it. **P3 is what the slot bought**: `req_in_turn` mean **3.97**, max **15**, against 1.23/1.36/1.62 and max 5–6 for the three siblings — super-additive, each knob alone moving +11% and +32%. Actions are flat across all four (1131–1401), so it is more requests per action, not more work; `rows/action` tracks TEMPERATURE (1.70/1.71 vs 0.86/1.04) while `req_in_turn` tracks the INTERACTION. n=1 per setting: a mechanism, not an effect size. `notes/thui-v5-0-the-two-knobs-interact-2026-08-28.md` (kc-arc-agi-pub). |
| **clock2x** | **6.40** | — | 17 | 30 | 2637 | 87.9 | 4.33 | anim | v10 with `max_runtime_s_per_game` 7920→15840 and nothing else (B34). **The highest public number this campaign has produced, and it ranks NOTHING**: `rank_runs.py` vs v10cal p=**0.2761** NOT-DISTINGUISHABLE, 10 up / 6 down / 5 flipped. Read the LEVELS column instead — 28→30, i.e. **+2 for double the clock**, against B34's own pre-written P4 of +1 per GAME. So the depth-by-time axis is answered `no` at its strongest setting, and B36 (reallocating the same budget) is bounded below that. P1 passed: wall **4h 24m 50s**, so `bm.solver` does reach the per-game session — the lever worked and the effect is small, which is the one outcome no probe could have told apart from a broken lever. ⚠️ **Ships nowhere**: hidden = 4 waves × 15840s = 17.6h against a 9h budget, and cell 12 degrades to v10 under `TRUE_SUBMISSION` by design. Its lasting value is a by-product — `summary.txt` gave the per-game TOTAL level counts (sum 183) that closed B35's blocker. Kernel `yocybercode/clock-2x-v1`, 2026-08-24. `results/clock2x-summary-20260824.txt` |
| **v26** | **3.19** | — | 15 | 20 | 1165 | 58.3 | 1.87 | anim | **B38's family brake, K=20 — the mechanism passes every gate and buys nothing.** **Armed**: the log carries `duckv26: family brake armed, K=20` exactly once at t=449s (`Traceback` 0, negative control 0). **Bound**: across all **1,165 executed actions of 25 games NO action family exceeds 20, and six stop at exactly 20** (`g50t` `m0r0` `re86` `s5i5` `tr87` `tu93`) — against R38's own control on `clock2x`, where `vc33` walked `row=56` **101** times; here `vc33` maxes at **7**. Refusals fired in **10 batches across 3 games** (g50t 2 · m0r0 3 · tu93 5), the largest tu93 refusing **26 consecutive DOWNs** at the moment `ACTION2` reached 20; the other three capped games never asked that family again. ⚠️ **B29 and the family brake are NOT separable from the refusal TEXT** — the patch sets no `stop_detail` of its own, so both emit B29's *"exact board state"* wording; **the ceiling is the discriminating evidence, not the message**. `rank_runs.py` (`--selftest` cleared both poles in the same session first — negative NOT-DIST, positive p=0.0001 WORSE): vs **v10cal p=0.2045**, vs **thui-v1-1 p=0.3328**, vs **thui-v1-1-r2 p=0.3671**, vs **clock2x p=0.1326** — all NOT-DISTINGUISHABLE, a **seventh** in-band sample of the v10 family, and the band `[2.82, 5.24]` does not move. **What it cost**: levels **20** and actions **1,165** are the family's LOWEST, and generated tokens **1.868 M fall BELOW the 2.02–2.21 M band B33 measured as near-constant campaign-wide** — the first run to leave it downward — at **1,603 tok/action**, the family's highest (v10cal 1,272.6); a refused batch pays tokens and returns no action. ⚠️ **R38 predicted the brake would speak on 25.9% of decisions; observed ~1%** (10 batches). The only reading available is INFERRED, never measured: the brake changes the trajectory, so the long families R38 counted on `clock2x` never form here — 25.9% describes a path this run does not take. **R41 §6's first open question is answered**: an action CAN be blocked, and what the agent does instead is not better. Wall **2h 12m 32s** (the v10 clock, not the silent-worker-death shape); `summary.txt` and `benchmark.json` agree on mean, actions and duration independently. ⚠️ Kernel `sahasawatt/taaf-duck-v26` — on the LEADER's account, not ours, per the token boundary in R41 §5. No `results/` artifact committed for this run; read from the kernel output. |
| **v10out** | **4.55** | **1.70** | 14 | 22 | 1285 | 58.4 | 1.87 | anim | anim bundle + Qwen3.8, output uncapped. The rebase onto Tufa's animation-awareness branch is the single largest jump in the campaign |
| **v24** | **3.78** | — | 14 | 20 | 1196 | 59.8 | 2.11 | anim | v10 exact + the B32 untried-ledger nudge (R36): per-level tried/never-tried counting spoken through the hint channel at turns 8/16/24. Rig-verified on an 8B first (fired correctly, model obeyed in 4 actions). On the 27B: **64 fires across 18 games, obedience 30/58 = 52% within 6 actions, with hard refusal streaks** (sb26 ACTION7 named 7x never pressed; tr87 arrows named 9x across 72 turns, untouched) — the channel that carried animation nudges 7/7 carries this one only half the time. `rank_runs.py`: **p=0.304, NOT-DISTINGUISHABLE** (8 up / 9 down / 8 flips). Campaign tally: 11 modifications of v10, 0 above the band. `notes/R36-untried-ledger.md` RESULT |
| **v23** | **3.32** | — | 15 | 20 | 1634 | 81.7 | 2.21 | anim | v10 + upscale 8 + the grid-line renderer NO ONE had ever run (ported from the newer bundle whose own setup arms 'true' against a == "1" reader — R34) + one system-prompt line saying the lattice is a rendering aid. The note exists because the v23 SMOKE caught ka59 reading the lattice as GAME STRUCTURE and burning a 7k-char turn on the image-vs-ascii contradiction; v23.1's smoke showed the note in 111/111 prompts and the confusion gone. Full run: `rank_runs.py` **p=0.4061, NOT-DISTINGUISHABLE** (8 up / 11 down / 7 flips, levels 28→20). Mid-band — B49 (this row was `B31` until the ids were made unique on 2026-08-27) closes: coordinate scaffolding at the perception layer does not move score either. `notes/R34-grid-lines.md`. Cross-checks from the run artifacts (Watchara, merged 2026-08-25): vs v18 delta −0.28 p=0.8035, vs v19 +0.50 p=0.7325 — indistinguishable from ALL of v10cal/v18/v19; the lattice leaves NO verbal trace (1 of 1,048 turns mentions grid lines — and v18, which renders none, carries the same single mention in the same game re86, so that hit is not the feature); behavioural outlier cn04: 454 actions / 92 turns / 5 RESETs for 0 levels vs 26–41 actions in every sibling run. (His "not built in this repo" note was true when written — duckv23 landed at 3a77b0b and was pruned at 4a42e0b; builder in history) |
| **thui-v1** | **3.20** | — | 16 | 22 | 1493 | 67.9 | 2.16 | anim | v10 + the per-request usage probe in cell 12 (`thuiv1/request_usage_probe.py`). The instrument is inert by design and the number says so: a **fourth** sample of v10, inside the [2.82, 4.71] band, the same shape v19 has. `rank_runs.py` on this run's own `benchmark.json`: vs **v10cal** delta -1.51, **p=0.3027 NOT-DISTINGUISHABLE**; vs **v19** delta +0.38, **p=0.7579 NOT-DISTINGUISHABLE**. Measured, not inferred. `won: 0`, so a banking graft would still be inert here. What it bought is not the score: 25 `*_usage.jsonl` files carrying `completion_tokens` + `finish_reason` per request, which is the distribution duckv9 was capped without — read, and the answer is **no cap is worth placing**: the distribution has no fat tail, so 8192 saves 0.98% and 12288 saves nothing. It also showed **all 25 games hit `max_runtime_s_per_game=7920`** (min 7920, max 7955), so `gave_up` here is the clock, not the agent, and the score is a throughput number with input:output at 10.7:1. `notes/R35-usage-distribution.md`. Kernel `yocybercode/thui-v1-0`, 2h 12m 35s, 2026-08-23. |
| **v22** | **2.84** | — | 16 | 20 | 1612 | 80.6 | 1.99 | anim | v10 + the rank-21 team's PYTHON_ADDENDUM ported verbatim (AST-extracted, both import bindings patched, teeth in-kernel: `3817 -> 4571 chars`). `rank_runs.py`: **p=0.0798, NOT-DISTINGUISHABLE** — lands at the very bottom of the [2.82, 4.71] same-build band. B28 rode free: search-construct usage **19/935 = 2.0% (v10cal control, reproduced exactly) -> 22/902 = 2.4%** — the explicit BFS instruction moved nothing globally, and the two games where it DID spike locally both collapsed (tu93 36% of turns, score 5.22->0.08; g50t 20%, 0->0). The last attributed lever from the only public artifact above us closes. `notes/R27-git-sweep.md` RESULT |
| v12 | 3.72 | — | 17 | 24 | 1810 | 75.4 | 2.19 | anim | v10 + a "be brief" prompt. Below band → the cut-reasoning axis is dead in its soft form too |
| **v21** | **1.25** | — | 15 | 12 | 2921 | 243.4 | 2.27 | anim | v10 + `reasoning_effort=medium` (the rank-21 team's flag; template default is xhigh). Patch verified in-kernel. Mechanism worked exactly as designed — **tok/action 1271→776 (−39%), actions 1597→2921 (+83%)** — and levels HALVED (28→12). `eval/rank_runs.py`: **p=0.0052, WORSE** — the second result outside the same-build noise, in the opposite direction from the hope. `notes/R26-reasoning-effort.md` |
| **v20** | **0.18** | — | 3 | 3 | 7656 | 2552.0 | — | anim | v10 with the model swapped to **Qwen3.6-35B-A3B-FP8** (MoE, 256 experts / 8 active, ~3B active). vLLM booted it fine and tool calls parsed — the agent fired **7,656 actions, 4.7x v10's 1,597** — and cleared **3 levels against 28**. act/lvl 57 -> 2,552. **The first result of this campaign that lands outside the [2.82, 4.71] same-build spread**, so it is the first single run that can rank anything. `notes/R25-moe-result.md` |
| **v19** | **2.82** | — | 16 | 20 | 1638 | 81.9 | — | anim | v10 + the fork's `banking` graft, armed and verified installed (`solver HarnessSolver -> BankingHarnessSolver (installed=True)`). **It never fired**: banking needs a full-game WIN and all 25 games ended `gave_up` — 0 WINs, 20 of 183 levels. So this is a THIRD sample of v10 with an inert graft, and it is what widened the public band to [2.82, 4.71]. `notes/R23-banking.md` |
| **v18** | **3.60** | — | 15 | 22 | 1576 | 71.6 | — | anim | v10 + `MULTIMODAL_UPSCALE` 4→8. The board PNG went 256×256→512×512 (~64→~256 vision tokens for 4096 cells). Below band, and the shape is v14's exactly: **same 22 levels as v10out for 291 MORE actions** (1285→1576), act/lvl 58.4→71.6. Bigger image did not buy sight; it bought attempts. `notes/v18-vision-upscale.md` |
| v16 | 3.51 | — | **19** | 24 | 1218 | **50.8** | 2.02 | anim | v10 + a change summary pushed into every turn. Delivery doubled (46.6%→90.4% of turns) and the score fell. Most games scoring ever, best efficiency ever, still lost — breadth does not pay |
| v8out | 3.31 | — | 15 | 22 | 1946 | 88.5 | 2.12 | old | model swap to Qwen3.8 on the OLD bundle. Proved the model was worth ~+37% before the bundle was touched |
| v14 | 2.87 | — | 15 | 19 | 1633 | 85.9 | 2.35 | anim | v10 + `--kv-cache-dtype fp8`. Mechanism confirmed (KV 199k→398k tokens, prefix retention 22%→42%, +26% tok/s) and the capacity became **more actions, not more levels** |
| v8cal | 2.87 | — | 13 | 19 | 1586 | 83.5 | 2.19 | old | v8 rerun; band [2.87, 3.31] on identical code — 0.44 wide |
| v5out | 2.43 | **0.84** | 14 | 21 | 4000 | 190.5 | 1.76 | old | state channel (accumulating world model). Hidden draw came in below duck-mod |
| duck-mod | 2.41 | **1.00** | 13 | 17 | 3481 | 204.8 | 1.50 | old | Duck + our hud_mask/TransitionGraph patches. Held the leaderboard slot (rank 585/2409) until 08-22 |
| v5cal | 2.37 | — | 14 | 17 | 3740 | 220.0 | 1.77 | old | v5 rerun |
| duck-mod cal | 2.16 | — | 13 | 19 | 3858 | 203.1 | 1.56 | old | duck-mod rerun; band [2.16, 2.41] |
| v6 | 1.85 | — | 11 | 15 | 2802 | 186.8 | 1.58 | old | new digest; warnings taxed actions |
| v4 | 1.73 | — | 13 | 16 | 3867 | 241.7 | 1.66 | old | several levers at once, all measured inert (R7) |
| duck (stock) | 1.25 | — | 13 | 16 | 4090 | 255.6 | 1.54 | old | the unmodified upstream harness — our starting line |
| v3 | 0.80 | — | 12 | 13 | 4336 | 333.5 | 1.58 | old | early fork |
| **v9** | **0.22** | — | 2 | 2 | 255 | 127.5 | 0.22 | anim | `LOCAL_ANALYZER_MAX_OUTPUT=768`. The cap truncated the tool call that carries the action — `finish_reason=length` 704 times vs `tool_calls` 68 |
| v4out2 | 0.00 | — | 0 | 0 | 0 | — | 0.00 | old | dead run |
| our own agent | — | **0.11** | — | — | — | — | — | — | written from scratch before adopting Duck |

Never ran: **v13** (retrieval-discipline prompt, held — losing axis), **v15** (abandoned at design;
the batch path was already guarded and "surprise" has no harness-visible definition), **v7/v7b**
(ERROR twice on an infra flake).

## The solo probes (B41-B43) — one game, the whole clock

Not rows of the table above: these are **1-game** runs, so `public` has no meaning and nothing here
is comparable to a 25-game mean. Both are `duckv10` exact outside cell 14, `TRUE_SUBMISSION`
asserted off, diagnostic only. Builder + teeth: `solo/`.

| probe | actions | levels | score | tok | tok/action | that game's 9 shared runs (actions) | B43 bar | verdict |
|---|---|---|---|---|---|---|---|---|
| **sk48** solo | **80** | **0/8** | 0.00 | 235,664 | 2,946 | 21–139, median 54 | clear anything | **NO** |
| **lp85** solo | **14** | **1/8** | 2.78 | 154,026 | 11,002 | 13–70, median 38 | >4 levels | **NO** |
| **g50t** solo | **112** | **0/7** | 0.00 | 285,735 | 2,551 | 7–403, median 23 | clear anything | **NO** |

`sahasawatt/taaf-solo-sk48` v3 (2h 12m 0s) and `sahasawatt/taaf-solo-lp85` v1 (2h 12m 0s), both
2026-08-26. P1 cleared on both before any score was read — marker `solo: <game> only` exactly 1,
`LOCAL_ANALYZER_TEMPERATURE` and `MULTIMODAL_UPSCALE` at 1 as positive controls, the duckmod marker
and the *other* game's marker at 0, `AssertionError` 0 — and the summary read from the **last** of
the periodically reprinted blocks (28 of them in the sk48 log).

**`g50t` ran on 2026-08-30, four days late, and it answers the question the other two could not.**
`sahasawatt/taaf-solo-g50t` (2 h 18 m 48 s, wall 8,328 s). P1 cleared before any score was read —
`solo: g50t only` exactly 1, `LOCAL_ANALYZER_TEMPERATURE` and `MULTIMODAL_UPSCALE` at 1 as positive
controls, `duckmod` 0, `AssertionError` 0, `Traceback` 0.

**112 actions against g50t's human level-1 baseline of 78 is 1.44×, and it cleared NOTHING.** That
is B42's own reading rule: at or above the human count, a zero is a reasoning problem and not a
clock problem. **`g50t` is a WALL**, alongside `sk48`, and B52's *"the one never-clear game with no
causal test"* is answered. It also spent **285,735** accounted tokens (`note=` 310,595) on one game
— roughly 5× what a game gets in a 25-game run — for nothing.

⚠️ **The delivered budget again fell short of the row that asked for it.** B42's corrected figure
projected 1.7–3.0× the human baseline from the full clock; 1.44× is above the threshold that makes
the reading meaningful and about a fifth below the projection, so the third probe repeats the
pattern the other two set rather than escaping it.

⚠️ **The four-day delay was not the quota it was recorded as.** The original push was refused with
`Maximum weekly GPU quota of 30.00 hours reached` and nothing was created; a scheduled retry then
died silently (its own log ends `sleeping 388 min until 00:15Z` then `[killed]`), so *"waiting on
g50t"* was carried as true for a day. When it was finally retried the quota was fine and the run
died at cell 4 instead, on the intermittent `/kaggle/input` layout documented in CLAUDE.md's traps
— two unrelated failures wearing one label. B42 asked for three games *specifically so no outcome
could be a property of one lucky game*; it now has three.

### What the probe was built to deliver, and what it delivered

B41's arithmetic said solo buys **1,099 actions** against the 46 a game gets in a 25-game run.
Measured: **80** and **14** — 7.3% and 1.3% of that. B42's own ⚠️ had already cut the claim to
2.2–3.9× the human level-1 baseline; the delivered figures are **1.31×** (`sk48` 80 against 61) and
**0.82×** (`lp85` 14 against 17).

⚠️ **Both land INSIDE their own game's shared-run spread — the probe's central premise is refuted
by its own instrument.** `sk48`'s 80 is rank 7 of 10 against its nine 25-game runs, below the 88,
99 and **139** that `v20`, `v18` and `thui-v2-0` gave it *while 24 other games shared the GPU*.
`lp85`'s 14 is rank 9 of 10, above only `v19`'s 13. Dropping concurrency 25 → 1 moved the per-game
action count **nowhere outside its historical noise**, in either direction.

### Where the budget went: per-action token spend, not per-action wall

The GPU delivered the same generation in both runs. Total generated tokens (the `note=` field on
the `[finished]` line, which counts the abandoned final action; the summary's `total tokens` does
not) are **310,412** and **312,989** — **0.8% apart** — over an identical 7,920 s game budget, i.e.
39.2 and 39.5 tok/s. Against the shared run's 234.9 tok/s across 25 requests (9.40 each) that is
**4.2×** per request; on the like-for-like *accounted* figures the summary itself prints it is
**3.17×** (`sk48` 29.75) and **2.07×** (`lp85` 19.45), which brackets [#52](https://github.com/Sahasawatt/arc-agi-3-agent/pull/52)'s
3.0× prediction from the vLLM logs.

So throughput rose and actions did not, because **tok/action rose further**: 2,946 and 11,002
against the campaign band of **1,272.6** (`v10cal`) to **1,603** (`v26`, the previous high) — 1.8×
and 6.9× the top of that band.

**The spend is bimodal, in both runs, and it is measured from the trajectory the 600 s summaries
print:**

```
lp85   actions  1-11   20,689 tok    1,881/action     <- inside the campaign band
       actions 12-13  115,053 tok   57,527/action
       action     14   18,284 tok
       action     15  158,963 tok    NEVER RETURNED — 3,717 s = 47% of the game clock
sk48   actions  1-13   23,693 tok    1,822/action     <- inside the campaign band
       actions 18-58   22,470 tok      548/action
       action     73   47,997 tok
       action     81   74,748 tok    NEVER RETURNED — 1,916 s = 24% of the game clock
```

Both runs open inside the campaign's normal token band and then spend the majority of their budget
on a handful of actions 20–90× more expensive. During `lp85`'s last 62 minutes the log carries
nothing but the periodic summary reprint, and it ends
`analyzer request failed at action 15: … Read timed out. (read timeout=34.23)`, where 34.23 s is
not a configured timeout but *what was left of the 7,920 s*.

⚠️ **CORRECTED 2026-08-27 — that was NOT one request, and this row first said it was.** The mid-run
read timeout is 900 s, so any request running longer prints a failure line. `lp85` solo printed
**exactly one**, and its clamp of 34.2 s puts that request's start at t≈8291.6 — it ran 34 seconds.
The **3,682 s before it produced no failure line at all**, which under a 900 s bound means **at
least five successive requests, every one of which returned.** *"158,963 tokens in one HTTP call"*
is refuted by this row's own data, and PR [#57](https://github.com/Sahasawatt/arc-agi-3-agent/pull/57)
carries it uncorrected.

⚠️ **Solo does NOT cause the runaway — it is campaign-wide, and it was measured after this row was
first written.** The census below finds abandoned generation in **every one of 17 runs**, 9.1% to
25.0% of tokens, with individual games reaching **100%**. Solo’s 24.1% and 50.8% sit in the upper
part of that per-game distribution and outside none of it, on n=2. What the solo runs did was make
a campaign-wide leak visible, by removing the 24 other games whose progress had been hiding it.
⚠️ **This paragraph claimed R35 was blind here. It is not** (corrected 2026-08-27, and it is the
one claim §What the gap actually is left standing). R35 read `thui-v1-0`’s per-request completion
tokens and concluded *no cap is worth placing — 8192 saves 0.98%*; **its denominator is the
GENERATED total, not the counted one** — see below.

⚠️ `LOCAL_ANALYZER_MAX_OUTPUT` is 0 (uncapped) here, and `v9` proved a hard cap of 768 destroys the
run by truncating the tool call that carries the action. Nothing in this campaign has ever measured
a cap between 768 and unbounded, and these two runs are the first evidence that the upper end costs
something.

### What B43 can and cannot be told

On the letter of the rule fixed before the runs — *clearing more levels than that game's best-ever
counts as YES* — both are **NO**: `sk48` 0 against a bar of "clear anything", `lp85` 1 against 4.

⚠️ **That NO does not answer B43's question.** The rule presupposed 1,099 actions, i.e. 17× the
human level-1 count; at 1.31× and 0.82× a null is the expected outcome of the *budget*, which is
precisely the failure mode B42's own retarget note warned about — and it warned about it at
2.2–3.9×, still well above what ran. `lp85` is the sharper case: it **cleared level 1 in 9 actions
against a human baseline of 17**, then got **5 of the 38 actions** level 2 needs before the clock
died (`per-level=9/17,5/38,0/31,…`). Its 4-level best-ever is also from `clock2x`, a **double-clock**
run; under the normal 7,920 s clock its best is 3 levels at 49 actions (`v10cal`).

**What these two runs DO close is B41, not B43.** The budget axis was never tested, because
concurrency is not what binds the action count — per-action token spend is, and it is not under the
probe's control. Answering B43 needs the runaway bounded first.

## The abandoned-token census (B45) — 9–25% of every run has never been counted

Surfaced by the solo probes and then measured campaign-wide on **17 runs**, from the `[finished]`
line each game prints: `tokens=M` is what the summary and the `Mtok` column above report, and the
trailing `note="tokens=N"` is the larger figure. **N − M is generation that never landed on an
action.** ⚠️ **It is NOT generation in flight** — that was this section's first reading and it is
refuted; see *What the gap actually is* below.

| run | actions | Mtok (counted) | generated | abandoned | per-game abandoned % (min/med/max) |
|---|---|---|---|---|---|
| clock2x | 2,637 | 4.33 | 4.76 | **9.1%** | 0.0 / 3.5 / 43.2 |
| thui-v1-1 | 1,325 | 2.10 | 2.37 | 11.5% | 0.0 / 7.0 / 61.5 |
| v21 | 2,921 | 2.00 ⚠️ | 2.27 | 11.9% | 0.0 / 1.3 / 79.9 |
| thui-v1-0 | 1,493 | 2.16 | 2.46 | 12.3% | 0.0 / 8.9 / 56.9 |
| thui-v2-0 | 1,425 | 2.08 | 2.37 | 12.5% | 0.0 / 9.6 / 43.0 |
| v24 | 1,196 | 2.11 | 2.43 | 13.0% | 0.0 / 6.2 / 64.5 |
| v23 | 1,634 | 2.21 | 2.58 | 14.1% | 0.0 / 7.9 / 50.1 |
| v16 | 1,218 | 2.02 | 2.39 | 15.4% | 0.0 / 3.1 / **100.0** |
| v10cal | 1,597 | 2.03 | 2.41 | 15.6% | 0.0 / 5.0 / 63.5 |
| v18 | 1,576 | 2.11 | 2.50 | 15.6% | 0.0 / 5.5 / 67.8 |
| v22 | 1,612 | 1.99 | 2.36 | 15.8% | 0.0 / 13.4 / 52.6 |
| v19 | 1,638 | 2.02 | 2.41 | 16.2% | 0.0 / 9.2 / 75.6 |
| thui-v1-1-r2 | 1,260 | 1.94 | 2.39 | 18.5% | 0.0 / 3.5 / **100.0** |
| v25 | 1,341 | 1.82 | 2.26 | 19.2% | 0.0 / 3.9 / **100.0** |
| v26 | 1,165 | 1.87 | 2.33 | 19.9% | 0.0 / 12.5 / 92.5 |
| v20 | 7,656 | 3.00 | 3.93 | 23.7% | 0.0 / 0.0 / 91.8 |
| v14 | 1,633 | 2.35 | 3.14 | **25.0%** | 0.0 / 9.1 / **100.0** |
| `sk48` solo | 80 | 0.24 | 0.31 | 24.1% | — (one game) |
| `lp85` solo | 14 | 0.15 | 0.31 | 50.8% | — (one game) |

**Positive control, and it is what makes the table readable at all: the `actions` column parsed from
these logs reproduces the table above EXACTLY, 17 of 17 runs** — 1,597 for `v10cal`, 7,656 for
`v20`, 2,637 for `clock2x`, and so on. So each log is the run the LEDGER row names, and the regex is
reading the fields it claims to.

⚠️ **What `note="tokens=N"` counts is INFERRED, not documented.** Three checks, none decisive
alone: (a) games that finish cleanly give **N == M exactly** — every run has a per-game minimum of
0.0% — so N is not prompt+completion, which at R35's measured 10.7:1 input:output ratio would be
~11.7× M on *every* game; (b) `lp85` solo's gap of 158,963 matches its 3,717 s stall at that run's
own generation rate; (c) the actions control above.

### What the gap actually is — the in-flight reading is refuted, from two instruments

**This section's first reading was that `N − M` is generation still IN FLIGHT when the game hit its
wall. That is wrong.** Two independent measurements, neither of which needs a slot:

**1. Per-request usage rows (Watchara, `arc-agi-pub` #146,
`notes/B45-the-gap-is-not-in-flight-2026-08-27.md`).** The discriminator was already stated by the
census itself — *a request that never returns writes no `*_usage.jsonl` row*. So:

```
in flight            =>  usage-file sum  <  N     (rows missing)
returned, not counted =>  usage-file sum ==  N     (every row present)
```

Measured on `thui-v1-1-r2`, the only banked run with all 25 usage files and one of the four whose
100% signature this census names: **`usage sum == N` on 25 of 25 games**, `usage sum == M` on only
9, and **16 of 25 games carry a gap** (1,306 usage rows) — so the run does contain the population
under discussion, and the verdict is about the gap rather than about a run that has none.
**RETURNED-NOT-COUNTED.**

It also corrects `tr87`, this table's 100% case: **62 of its 63 requests ended `tool_calls` and
exactly one was a `ReadTimeout`** — not "all ending ReadTimeout" as the `thui-v1-1-r2` row said.
`tr87` is a game where 62 requests **succeeded** and it emitted no action at all.

**2. The 900 s bound, from the solo logs already in hand.** A mid-run request's read timeout is
900 s, so anything running longer prints a failure line. `lp85` solo printed **exactly one**, at the
wall, clamped to 34.2 s. Its 3,682 s stall therefore contained **≥5 successive requests that all
returned** — a single long request is impossible under that bound. `sk48` solo is the same shape
(1,916 s, one clamped event, ≥3 requests).

**So the two candidate shapes the Fog named are both absent**, and the census's size figures
(9.1%–25.0%) are unaffected — only the label was wrong. What the gap is instead: **tokens spent on
turns that produced no action**, which is `B40`'s population — *every `analysis` turn carrying
`turn_time_budget` ends `step_executed: False` while its own meta reads `finish_reason:
tool_calls`*, measured at **30.5%** of turns on `clock2x` and **30.2%** on `v25`. B45 and B40 have
been measuring one thing from two sides.

**What the same rows say about the SHAPE, and it is B46's loop seen per request** (added
2026-08-27, same probe, same files):

| game | rows | distinct `action` ids | max `wall_s` | sum `wall_s` | finish |
|---|---|---|---|---|---|
| `cd82` (43 actions, control) | 45 | **23** | 612.7 | 7,912.2 | 44 `tool_calls`, 1 RTO |
| `bp35` (1 action, 94.4%) | 110 | **2** | 164.0 | 7,915.8 | 109 `tool_calls`, 1 RTO |
| `tr87` (0 actions, 100%) | 63 | **1** | 147.6 | 7,914.0 | 62 `tool_calls`, 1 RTO |

`tr87` spent **7,914 s of a 7,920 s clock** on 63 requests, **none longer than 147.6 s** — so it
carries no 900 s hang either, and instrument 2's bound is met from the other direction. It is
**63 requests under one action that never ended** ⚠️ (whether they are steps of ONE tool-step loop
or one step each of 63 successive turns is not settled by this table — see *Can a TOOL_STEPS cap
even bind* below), which is `LOCAL_ANALYZER_TOOL_STEPS = '0'` read
directly rather than by residual. **The discriminator is the action-id count, not the request
count**: the healthy control advances through 23 ids on *fewer* requests than `tr87` fired under one.

⚠️ **n = 1 run for instrument 1** — the other three 100% games (`v14`/`ar25`, `v16`/`dc22`,
`v25`/`ft09`) have no banked usage files and are untested. ⚠️ **What `M` counts is inferred, not
read from the harness** — *"turns that produced an action"* fits every row, but the code was not
consulted; the refutation does not depend on it, resting only on `usage == N`.

### What it changes

**The `Mtok` column and every `tok/action` figure derived from it count only the requests that came
back.** Real generation is 9–25% higher, unevenly: `v26`'s 1,603 tok/action becomes 2,002, and
`v10cal`'s 1,272.6 becomes 1,508.

⚠️ **`v21`'s Mtok is the ONLY cell in the table above that is a GENERATED figure** — 2.27 M is its
generated total, its counted total is 2.00 M. So that row's headline *tok/action 1271→776 (−39%)*
compares `v10cal`'s **counted** 1,272 against `v21`'s **generated** 776. Like for like it is
1,272 → **683 (−46%)** counted, or 1,508 → **776 (−49%)** generated. The row's direction survives;
its magnitude was understated and its units were mixed.

**The zero-action stalls this campaign has recorded three times now have a mechanism.** Every game
that hit 100% abandoned took **0 actions while generating 96 k–133 k tokens**: `v14`/`ar25`,
`v16`/`dc22`, `v25`/`ft09`, `thui-v1-1-r2`/`tr87`. They were not idle and they were not blocked —
they were generating inside an action that never terminated. `bp35` sits next to `tr87` at **94.4%**
on 1 action, and at **94.9%** on 1 action in `v25`.

⚠️ **This sentence read *"into requests that never returned"* until 2026-08-27** — see
§What the gap actually is, above.

⚠️ **That refutes the attribution the `v25` row currently carries.** It reads the `ft09`/`bp35`
stall as belonging *to the duckmod prompt, not to the harness or the sampler*, on the evidence that
`thui-v1-1` gave those two 86 and 63 actions. But `thui-v1-1-r2` is the CLEAN v10+seed arm with no
duckmod anywhere, and it produced the identical signature on `tr87` (0 actions, 100%) and `bp35`
(1 action, 94.4%). The stall is not duckmod-specific; it moves between games across runs of the same
build. Left as a flagged inconsistency rather than an edit — which reading is right needs the
per-request timing that no committed artifact holds.

⚠️ **The solo runs are elevated but cannot be ranked**: 24.1% and 50.8% against a per-game
distribution whose median is 0–13.4% and whose maximum reaches 100% in four of seventeen runs. n=2.

⚠️ **Nothing here measures a fix.** `v9` proved `LOCAL_ANALYZER_MAX_OUTPUT=768` is fatal
(`finish_reason=length` 704 times against 68 tool calls) and no value between 768 and unbounded has
ever been run. ⚠️ **The line that stood here — *R35's 8192 saves 0.98% was measured on `*_usage.jsonl`, which a
request that never returns never writes, so it is silent about exactly this population* — is
REFUTED by this table's own arithmetic, 2026-08-27.** It is the last surviving consequence of the
in-flight reading. R35's three cap rows share one denominator: **24,173 / 0.0098**,
**318,137 / 0.129** and **847,994 / 0.344** all give **2.466 M**. That is `thui-v1-0`'s
**generated** 2.46 in the table above, not its **counted** 2.16 — a 14% gap that lands inside this
census's 9.1–25.0% band, and `thui-v1-0`'s own row says **12.3%**. The abandoned tokens were inside
R35's sample all along and its 0.98% already prices them, which follows directly from
`usage sum == N`: if every returned request writes a row and the sum equals `N`, the sample R35 read
IS the generated population. **So the cap axis gains nothing from a re-probe** — the reason to leave
`LOCAL_ANALYZER_MAX_OUTPUT` alone is now a measurement rather than `v9`'s wreck, and B46's
`LOCAL_ANALYZER_TOOL_STEPS` is the only untried knob on this axis — ⚠️ untried, but not established
to be REACHABLE; see *Can a TOOL_STEPS cap even bind* below.

Method: `KaggleApi().kernels_logs(<slug>)`, one call per run, no slot and no GPU.
Script `eval/abandoned_tokens.py`.

### What SHAPE the leak has (B46) — neither of the two candidates, and the knob has never been touched

The Fog asked whether the abandoned generation is **one very long request** or **many that time
out**. It is measurably a third thing, and the discriminator was already in the logs: every run
prints exactly one kind of error line, and its `read timeout=` VALUE splits it into two populations.

| population | events/run | when | what it is |
|---|---|---|---|
| `read timeout=900.0` **exactly** | 8–35 | spread through the run | a request killed at `analyzer_timeout=900`, and **the action retries** |
| clamped, `< 900` | **21–25** | **inside the last 1% of the run**, 19–24 of them at one instant | the terminal cancellation, one per game still mid-request at the wall; the value is the budget that was left |

638 unique events over 19 logs. Every log duplicates stderr **exactly ×2.0**, uniformly, so the
dedupe is safe. The retries are directly observed, not inferred: `v26` fires action **18** at
t=6434.8 **and** 7335.9, action **48** at 6660.6 and 7561.8, action **37** at 6813.4 and 7714.5 —
deltas **901.1 / 901.2 / 901.1**. Nothing bounds the retry count.

**Then price both populations and see whether they add up.** Charging every hang 900 s and every
terminal request its own clamp, at the run's average per-game token rate:

```
                 hung     terminal    RESIDUAL          residual as % of abandoned
v10cal        174,076      45,875     156,802                42%
v14           113,291      58,390     613,799                78%
v26           147,836      58,565     258,401                56%
clock2x       323,305      66,185      41,416                10%
thui-v1-1     192,608      59,988      18,988                 7%     <- the tightest
solo sk48           0       1,761      72,987                98%
solo lp85           0       1,353     157,610                99%
```

**Median residual across the 17 shared runs is ~45%, and for the two solo runs it is 98–99% with
ZERO hang events to model.** So the dominant mechanism is neither of the Fog's candidates: it is
generation inside requests that **completed successfully**, in an action that never terminated.

⚠️ **The `hung` and `terminal` columns are an UPPER bound on what those two populations explain,
and the direct measurement says they explain ~nothing.** This table prices a killed request's
tokens as if they were part of `N`; the usage-row measurement above finds **`usage sum == N` on
25 of 25 games**, i.e. every token in `N` came from a request that RETURNED — so a killed request's
generation is in neither `usage` nor `N`, and the true residual is nearer 100% than 45% on the one
run where it can be read. The columns still bound the *time* those populations consumed, which is
what the retry observation rests on. Read the row conclusion, not the arithmetic.

### The knob

```
LOCAL_ANALYZER_MAX_OUTPUT = '0'      unbounded output per response
LOCAL_ANALYZER_TOOL_STEPS = '0'      unbounded tool steps per ACTION      <- this one
```

One action is a tool-calling loop. A **step** is bounded — 900 s, and it is killed and retried when
it blows. ⚠️ **The loop is NOT bounded only by the game wall — see *Can a TOOL_STEPS cap even bind*
below.** It carries a second bound this section missed, `LOCAL_ANALYZER_YIELD_SECONDS = 60`, and on
measured request costs that bound fires **14–25× sooner than a cap of 12 ever could**. `lp85` solo is the
clean case: between its last completed action (t=4609) and the wall it spent **3,682 s and ~159 k
tokens with zero failures logged** — every request in that window returned, and the action simply
never finished.

**So the two fixes the Fog named are aimed at the smaller half.** An output cap is
`LOCAL_ANALYZER_MAX_OUTPUT`, which bounds ONE response — `v9` set it to 768 and killed the run by
truncating the tool call that carries the action. A shorter request timeout attacks the 900 s
population. **`LOCAL_ANALYZER_TOOL_STEPS` is `0` in every run this campaign has produced and has
never been changed** — a different knob from the one `v9` poisoned. ⚠️ **Whether a cap on it can
bind at all is UNRESOLVED, and this section first asserted that it could**; the arithmetic against
it, and the one-line check that settles it, are in *Can a TOOL_STEPS cap even bind* below.

⚠️ **The residual is an ESTIMATE for the 25-game runs**, and the error source is named: it prices a
hang at the run's *average* per-game rate, and a hung request may generate faster, slower, or not at
all. It is **not** an estimate for the solo runs — with no hang events there is nothing to model.

⚠️ **Solo's zero hangs does NOT show that contention causes them.** At the shared per-action hang
rate (256 events over 33,327 actions = 0.0077/action) the solo runs' 94 actions predict **0.72**
events, and observing zero has probability **0.49**. The reading is consistent with either world and
discriminates nothing.

⚠️ **The solver config line lies about the per-game clock, and `clock2x` is the proof.** Every run
prints `max_runtime_s_per_game=7920.0` — including `clock2x`, whose games actually ran **15,891 s**
(`duration: 4h 24m 50s`, and B34's whole point). The field is the value *before* the override lands,
so it is not evidence of the budget in force; the run duration is. `--shape` flags the mismatch
rather than trusting either number.

### Can a TOOL_STEPS cap even bind — the arithmetic says no, and one field settles it

`tool_agent.py` is byte-identical across all five vendored copies (`856bf9b8`), and the loop a
`TOOL_STEPS` cap acts on carries a **second** bound this section originally missed:

```python
_LOCAL_ANALYZER_TOOL_STEPS = _get_env_int("LOCAL_ANALYZER_TOOL_STEPS", 12)   # :151  default 12; we ship 0
turn_started_at = time.monotonic()                                           # :2151 once per analyze()
def control_yield_reason():
    if self._yield_seconds is not None and (time.monotonic() - turn_started_at) >= self._yield_seconds:
        return "turn_time_budget"                                            # :2161  yield = 60
while self._tool_steps is None or turn_count < self._tool_steps:             # :2167
    if control_yield_reason() is not None: break                             # checked at the TOP
    turn_count += 1
    ...one request...
```

`turn_started_at` is set **once per `analyze()` call**, and the yield is checked **before** each
iteration. So the first request that costs more than 60 s makes iteration 2 break — **`turn_count`
= 1**. Against `tr87`'s measured **125.6 s** mean per request and `bp35`'s **72.0 s** (their own
`sum wall_s / rows`, from the table above), a cap of 12 could only bind at **≤5 s per request** —
**14–25× away**. Two consequences: a `TOOL_STEPS` cap is inert at this latency, and the `0` this
campaign has always shipped has been indistinguishable from the harness's own default of 12.

**The loop that has no bound is one level out**, `framework/solver.py:316`:

```python
while not self.should_stop():                 # stop = event | run complete | GAME WALL | max_actions(None)
    result = self.analyzer.analyze(...)
    if result.retryable_failure:  ... continue    # no counter
    if result.yielded_control:    ... continue    # no counter
    if not result.step_executed:      continue    # no counter
```

All three no-action exits `continue` with nothing counting them, and a yield keeps the history
(`preserve_history = True`) and reuses the same `analysis_step`, so a turn that yields resumes
rather than restarts. That is the shape B40 measures at **30.5% / 30.2%** of turns.

⚠️ **Both readings fit every number banked.** `tr87`'s 63 requests under one action id are either
63 iterations of the inner loop (one `analyze()`) or one iteration each of 63 successive turns
(63 `analyze()` calls) — and `analysis_step` cannot tell them apart, because a yield sets
`retry_analysis_step = analysis_step` and the counter does not advance.

**The field that does is `req_in_turn`**, which the usage probe resets on every `analyze()` call —
*"A turn is one analyze() call; requests within it are numbered from 1"*
(`thuiv1/request_usage_probe.py:109`). On any banked `*_usage.jsonl`:

```
max(req_in_turn) for tr87 == 1    ->  63 turns, the OUTER loop; a TOOL_STEPS cap is inert
max(req_in_turn) for tr87 == 63   ->  one turn, the INNER loop; a cap binds and is worth a probe
```

✅ **RUN 2026-08-27, on all three probe runs.** `tr87` is **2** — so the pure-outer-loop reading
above is wrong too, and `#65` reached the same number first. What it settles is the conclusion, not
either prediction: over `thui-v1-0`, `thui-v1-1` and `thui-v1-1-r2` — **3,948 requests, 3,090
turns** — a cap of **12 cuts 0 turns**, and 82.6% of turns are a single step.

⚠️ **The margin is ONE, which is the shape `R43` just showed to be untrustworthy.** The deepest
turn in the corpus is **11**, in `thui-v1-1`/`bp35` at `action=63`; the six deepest are all that one
game, their requests cost **4.6–12.0 s** against a corpus median of **101.9 s**, and each totals
~60 s. So the binding constraint is always the budget — but reaching 12 needs ≤5.0 s per request
and that turn averaged **5.44 s**. **Did not bind ≠ cannot bind.**

⚠️ **CROSSED 2026-08-28, on the fourth run.** `thui-v5-0` (yield 180 × temp 1.0, B53) runs
**53 of 789 turns deeper than 12** — max **15**, with the distribution spiking at 12–15 (69 turns
≥12) — so the harness default `TOOL_STEPS=12` **binds in this regime**: it would cut 80 of 2,274
requests (3.5%), and the campaign's `0` stops being a no-op exactly here. *Did not bind* was a
yield-60 fact; the margin-of-one warning above cashed. Verified from v5's own usage rows, not the
run report. Two more numbers from the same rows: **within-run CV is super-additive like the
depth** — 95.3% (base) → 101.9% (yield alone) → 115.3% (temp alone) → **138.7%** (both; +43.4
against +26.6 if additive). ⚠️ And two statistics travel under one name: #86's *req_in_turn mean
3.97* is the mean of the FIELD over rows, which weights deep turns quadratically; requests/turns
is **2.88**. Max agrees at 15 — cite either only with its definition.

Three things replicate at n=3 that were n=1 before. **`usage sum == note N` on all three runs**
(2,461,226 / 2,369,874 / 2,386,886, exact), so RETURNED-NOT-COUNTED is no longer one run. **The
token-budget fit holds** — R² **0.9870 / 0.9886 / 0.9835**, decode **13.1 / 13.3 / 12.7 tok/s**,
60 s ≈ **811 / 817 / 784** completion tokens; the `-r2` row reproduces `#65`'s published
`-1.6 + 0.0786x`, R² 0.9835, 12.7 tok/s, 784 to every digit. And **R35's own published number
reproduces**: a cap at 8,192 saves **0.98%** of `thui-v1-0`'s output and 12,288 saves **0.00%**,
which is the external control on the parse.

Method: `eval/abandoned_tokens.py --fetch-usage <run> --out <dir>` then `--steps <dirs>`. No slot. ⚠️ The code reading above is a reading, not an execution: it
predicts `max(req_in_turn) == 1` and is refuted by any other value.

Method: `eval/abandoned_tokens.py --shape`. Same logs, same API, no slot.

## Why games pass and why they fail — the per-level census (B52)

Every `[finished]` line carries `per-level=SPENT/HUMAN,…` — actions this run spent on each level
against that game's own human baseline. Nine runs of prose never parsed it. Parsed for all 21 runs
(477 game-runs; the in-band family below = 17 runs × 25 = 425), two internal closures asserted per
row and passing 477/477: `sum(SPENT) == actions` and `len(pairs) == level total`. Script
`eval/per_level_census.py`, data banked in `eval/fixtures/per-level-census.json`.

⚠️ **Banked because the source went dark mid-analysis.** The cell-0 retitle (#81) was pushed to the
live kernels as save-only versions, and `kernels_logs` takes no version argument — so **every
`yocybercode/` slug now serves an 800-char nbconvert stub** and the real logs of `thui-v1-0`, `thui-v1-1`, `thui-v1-1-r2`,
`thui-v2-0`, `thui-v3-0`, `thui-v4-0` and `clock2x` are unreachable from the API (probed 2026-08-28; `sahasawatt/`
slugs unaffected). The fixture, built from logs fetched 2026-08-27/28 with the LEDGER-actions
control passing 21/21, is the surviving copy. `--check` in `eval/abandoned_tokens.py` now reports
those seven as UNREACHABLE and exits 3 instead of claiming 17/17.

### Why games pass: they clear the cheap levels, faster than the human count

377 levels cleared across the family. **Median cost 0.78× the human baseline** (p25 0.55, p75 1.14)
— when reasoning fits the level, the agent beats the human action count more often than not. And
the levels it clears are the cheap ones: **human baseline median 26 actions, against 44 for the
levels it dies on**. Efficiency on cleared levels is not the problem; the problem is that deeper
levels cost ~1.7× more while the wall stays fixed.

### Why games fail: three shapes, and the budget reading is refuted for two of them

Every family game-run ends `gave_up` (0 wins, 425/425). The dying level splits them:

| shape | count | share | meaning |
|---|---|---|---|
| STARVED (`SPENT < HUMAN` at death) | 286 | **67.3%** | the wall arrived before the human's action count |
| STUCK (`SPENT ≥ HUMAN`) | 131 | 30.8% | had the budget, did not solve |
| ZERO (0 actions all run) | 8 | 1.9% | B40's population |

⚠️ **STARVED is the shape of the corpse, not the cause of death.** Both causal tests are above in
this file: `clock2x` DOUBLED the wall for +2 levels, and solo `sk48` got **1.31×** its human count
and stayed 0/8. Budget converts to levels only where reasoning already works — solo `lp85` cleared
L1 at 9/17 then starved at L2 5/38. And SPENT counts **executed** actions only: B40's no-action
turns (~30% of turns) and B45's abandoned generation burn clock without appearing in any SPENT.

### The cut that is new: 60% of stalls are variance, 40% are walls

For each stall, ask whether **any sibling run of the same family ever cleared that level**:

```
BEHIND the game's own frontier (a sibling cleared that exact level):  255  (60%)  <- draw variance
AT the frontier (no family run has ever cleared it):                  170  (40%)  <- real walls
best-ever oracle (sum of each game's deepest level):                   47  vs best single run 30
```

The build already "knows how" to clear **47 levels** — spread across draws; any one draw collects
25–30. That is the arithmetic behind the spread lever (`thui-v4-0`) and behind the board keeping
MAX: most of what a draw loses, another draw of the same build has already won. The frontier
levels are the expensive ones — human baselines 31–189, median ~61, against 26 for cleared levels.

### The named walls

- **`g50t` — the only game with zero clears in all 17 runs**, STARVED in every one (0.26× median,
  human L1 = 78). ⚠️ **The only never-clear game that has never had its causal test**: its solo run
  was refused on GPU quota (B42) and never re-pushed. If a probe slot ever exists, it goes here.
- **`sb26`** — clears L1 in 17/17, then STUCK on L2 at **2.0× the human count**: the cleanest pure
  reasoning wall in the corpus.
- **`tr87` / `bp35` / `dc22` / `cn04` / `m0r0` / `tn36`** — die on L1 with STUCK dominant
  (0.9–1.3×): they get the budget and do not solve. `tr87` doubles as B40's zero-action case.
- **`sk48`** — STARVED-shaped in shared runs (0.56×) but solo PROVED it STUCK (1.31× → 0/8): the
  worked example of why the 67% headline cannot be read as "more budget would fix 67%".

### Hidden draws cannot be decomposed this way at all

The submissions API exposes score and `scriptVersionId` only, and **all three duck-v10 hidden
draws (1.70 / 1.32 / 1.38) share ONE scriptVersionId (`343774931`)** — the hidden rerun is a
private per-submission artifact with no log surface (probed 2026-08-27; `kernels output` was
already proven to ignore the version). Why hidden passes or fails is answerable only through the
public failure mix above plus the shrink ratio (CORRECTION 4: 2.68×).

## What the column that actually explains the score is

Not levels. Not games scoring. **Actions per level.**

```
duck stock  255.6 act/lvl → 1.25
duck-mod    204.8          → 2.41
v5          190.5          → 2.43
v8           88.5          → 3.31
v10          57.0          → 4.71
```

Five builds, monotonic, across two different bundles and two models. Score is
`min((baseline/actions)^2 * 100, 115)` weighted by level number, so halving the actions spent per
level roughly quadruples that level's contribution. Every real gain this campaign made was an
efficiency gain wearing some other name.

### CORRECTION 3 (2026-08-23) — the PUBLIC band was wrong too, and it invalidates every run comparison

v19 armed the banking graft and scored **2.82 public**. Then the check that should have come
before the run: **banking never fired.** `solver_note` on all 25 games contains only
`tokens=NNNNN` — no mention of a replay, a prune, or an abort — and the reason is in the
state column:

```
v19    : states {'gave_up': 25}   games reaching WIN: 0   levels cleared 20 of 183
v10cal : states {'gave_up': 25}   games reaching WIN: 0   levels cleared 28 of 183
```

`banking_solver` fires "once a session's WIN is fully recorded" — a WIN is the whole game,
every level. **This campaign has never won a single game.** Its four engine facts were all
verified correctly and none of them was ever reached.

So v19 is v10 with an inert graft, i.e. a THIRD sample of the same build:

| run | public |
|---|---|
| v10cal | 4.71 |
| v10out | 4.55 |
| **v19 (banking inert)** | **2.82** |

**The band this campaign has used to judge every design is [4.55, 4.71]. The real spread of
the same build is [2.82, 4.71] — 1.89 wide, 40% of the top.** Consequences:

| run | score | verdict recorded | verdict that survives |
|---|---|---|---|
| v12 | 3.72 | "below band, brevity axis dead" | inside v10's own spread |
| v16 | 3.51 | "delivery doubled and it still lost" | inside |
| v18 | 3.60 | "bigger image bought attempts, not sight" | inside |
| v14 | 2.87 | "KV fp8 mechanism works, score didn't move" | inside |

**Four of the eight closed directions were closed on a difference smaller than the noise of
the build they were compared against.** The mechanism findings inside them (v14's KV
retention doubling, v16's delivery going 46.6%→90.4%, v18's image arithmetic) are still real
— those were measured directly, not inferred from the score. What does not survive is the
verdict attached to each: "this axis is dead".

⚠️ v19 is not a clean A/A: `BankingHarnessSolver` swaps `session_class`, so trace recording
runs even when the replay never does. Actions moved 1597 → 1638 (2.6%), which does not
explain a 40% score drop, but the pair is a near-A/A rather than an A/A.

**What this costs going forward:** with n=3 spanning 1.89 on public and n=2 spanning 0.38 on
hidden, a single run cannot rank two designs on either set — R9 said this for public and was
under-believed. Any future claim that a change helped needs paired runs, and the campaign
does not have the quota to buy that for every idea.

**The instrument for this now exists: `eval/rank_runs.py`** — paired per-game sign-flip
permutation over the 25 games, verdict DISTINGUISHABLE only at p<0.05. Calibrated on both
poles in one invocation (`--selftest`): v10cal-vs-v19 (same build) reads NOT-DISTINGUISHABLE
at p=0.21 ✓, v10cal-vs-v20 (26x apart) reads WORSE at p=0.0001 ✓. Re-judging v18 with it:
**p=0.51, NOT-DISTINGUISHABLE** — this table's original "below band" verdict on v18 is now
refuted numerically, not just argued. Per-game fixtures for all four runs: `eval/fixtures/`.

### CORRECTION 2 (2026-08-23) — the hidden number has a ±0.19 spread and every past comparison sat inside it

v10 was resubmitted unchanged (ref 55694474) purely to measure hidden variance. Result:

| draw | hidden |
|---|---|
| 1 (ref 55662656, 2026-08-21) | **1.70** |
| 2 (ref 55694474, 2026-08-22) | **1.32** |

Same parquet, same build, **0.38 apart — 25% of the larger value**. So:

- **v10's hidden mean is ~1.51, not 1.70.** Every plan built on 1.70 was built on the
  luckier of two draws, and 1.70 was the number this campaign quoted all day.
- **Every hidden comparison this campaign ever made is inside the noise.** duck-mod 1.00
  vs v5 0.84 is a 0.16 gap; our own agent's 0.11 is the only number outside it. Two
  builds cannot be ranked on one hidden draw each — the same rule R9 established for
  public runs turns out to hold harder here.
- ⚠️ **CORRECTED 2026-08-24 by R30 — the 3.05x below mixes a MAX with a MEAN, which is the
  error this very correction flags one paragraph up about quoting 1.70.** It divides the
  top TWO public draws by the MEAN of the two hidden ones. `v10cal` 4.71, `v10out` 4.55,
  `thuiv1` 3.20 and `v19` 2.82 are all the same build, so means on both sides are **3.82
  public over 1.51 hidden = 2.53x**. It moves the target the easy way: a candidate needs
  public **7.29** to sit at the 2.88 bar, not 8.83, and B20's 5.80 ceiling is **2.29**
  hidden — still under the bar, so the depth conclusion is unchanged.
- **The shrink is worse than recorded**: public [4.55, 4.71] against a hidden mean of
  ~1.51 is **~3.05x**, not the 2.72x the depth table used. The +0 row of that table
  predicted 1.73 and was scored against 1.70; against the mean it over-predicts.
- **Top-5 needs 2.57 hidden**, so the gap from a mean of 1.51 is **+1.06**, not +0.87.

Two draws is n=2: 0.38 is a range, not a standard deviation, and the true spread could
be wider.

**Addendum 2026-08-24 — a SECOND hidden A/A pair existed all along, and it reads 0.00.**
Submissions 55559497 and 55567678 are a byte-identical accidental duplicate of v9-lite
(recorded contemporaneously in `notes/next-session-prompt.md`: *"Today's quota got spent on
an accidental byte-identical duplicate (55567678, PENDING — expect ~0.10)"* — and it drew
exactly 0.10, as predicted). So:

| build | draw 1 | draw 2 | spread |
|---|---|---|---|
| v9-lite (low score) | 0.10 | 0.10 | **0.00** |
| duck-v10 (high score) | 1.70 | 1.32 | **0.38** |

Hidden variance is not a constant — it **grows with the score**, which is exactly what the
per-game mechanism predicts: the swing lives in deep-level clears, and a 0.10 build has no
deep clears to flip. A single hidden draw is adequate for a weak build and inadequate for
precisely the builds worth ranking. What it already rules out is reading any single hidden number as a build's
value.

⚠️ **NARROWED 2026-08-24 by R30 — the v9-lite row contributes nothing to that conclusion.**
"Grows with the score" is a restatement of **constant CV**, and the CV is now measured
twice: **0.249** over the four same-build public draws and **0.178** over this hidden pair.
At v9-lite's 0.10 that same CV predicts σ = **0.025** — the pair had almost no room to
differ, whatever is true about how variance scales, so its 0.00 is implied by the v10 pair
rather than confirming it. The conclusion stands and rests on **one** pair. The public CV
also gives an INDEPENDENT reading of this build's hidden σ — 0.249 × 1.51 = **0.376**
against this pair's own **0.269**, agreeing within 1.40, which is what makes the B30
decision robust where n=2 alone could not.

### CORRECTION 3 (2026-08-26) — two more draws, n=2 becomes n=4, and the mean falls again

`55773197` (`thui-v1-1`: v10 plus `LOCAL_ANALYZER_SEED`, proven inert by B37 at `p=0.8001`
vs `v10cal`) drew **1.29** — the lowest of the family. Read with its control in the same
call: `55662656` still reports `COMPLETE` / `1.70`.

| draw | ref | date | hidden |
|---|---|---|---|
| 1 | `55662656` | 2026-08-21 | **1.70** |
| 2 | `55694474` | 2026-08-22 | 1.32 |
| 3 | `55755367` | 2026-08-24 | 1.38 ⚠️ |
| 4 | `55773197` | 2026-08-25 | **1.29** |

⚠️ **Draw 3's description is empty and the submissions endpoint carries no owner field, so
no read of ours can attribute it** — only a person can. Both readings are given below and
they do not disagree about anything that matters.

- **The mean is not 1.51.** With all four: **1.42** (sd 0.189, CV 0.133). With only the three
  whose description names the build: **1.44** (sd 0.229, CV 0.159). CORRECTION 2's 1.51 was
  the mean of the two luckiest draws on record, in the same way 1.70 was the luckier of two.
- **The range widens 0.38 → 0.41**, and for the first time it is not the only statistic
  available: n=2 could give a range but not a standard deviation, and CORRECTION 2 said so
  explicitly. The hidden CV now reads **0.133–0.159** against the **0.178** that pair implied
  and the **0.249** measured on public — so the earlier σ estimates were, if anything,
  generous, and the ordering public > hidden survives.
- **1.70 is confirmed as the TOP of a distribution, not the build's value.** Three of four
  draws sit in **[1.29, 1.38]**, a span of 0.09. Any plan quoting 1.70 as what v10 scores is
  quoting the best of four.
- **Draw 4 itself ranks NOTHING**, which is the correct outcome. Its deltas from draws 2 and 3
  are **0.03** and **0.09**, far under the ~0.4 floor. Its 0.41 gap from draw 1 is a
  max-against-min of one distribution — precisely the comparison this section exists to forbid.
- **The leaderboard does not move.** Kaggle scores a team on its best submission, so the entry
  stays at **1.70** and the rank changes only by decay.
- **The gap to top-5 is wider than recorded**: from a mean of 1.42 to the **2.88** bar is
  **+1.46**, not the +1.37 a mean of 1.51 gave. ⚠️ 2.88 is itself a dated board reading
  (2026-08-25 01:55 UTC) — re-download before quoting it.
- ⚠️ **The 2.53x shrink ratio in CORRECTION 2 is now stale on BOTH sides and is deliberately
  not recomputed here.** Its denominator was the 1.51 this section replaces, and its numerator
  was a public mean over four draws while the family's public band is now `[2.82, 5.24]` over
  **eight** in-band samples. Recomputing one side alone would repeat R30's own error — mixing
  populations across the fraction bar. It needs the current public set, in one deliberate pass.
  **CLOSED 2026-08-26 by CORRECTION 4 below** — the pass was made; the answer is 2.68x-2.91x.

What did not change: every conclusion CORRECTION 2 and its narrowing reached. Hidden variance
still grows with the score, a single hidden draw is still inadequate for exactly the builds
worth ranking, and no hidden comparison this campaign has made sits outside the noise.

### CORRECTION 4 (2026-08-26) — the shrink ratio, recomputed in one pass: 2.68x - 2.91x

Closes the open item CORRECTION 3 left. Both sides were recomputed together rather than one
of them, which is what that section refused to do.

**The estimator carries a positive control**: fed R30's own inputs it must reproduce
`3.82 / 1.51 / 2.53`, and it does to four decimal places, before any population is substituted.

R30's membership rule was **"all the same build"**, not "in-band" — load-bearing, because
almost every run this campaign is NOT-DISTINGUISHABLE from `v10cal` (this file's own tally:
*"11 modifications of v10, 0 above the band"*), so reading "the family" as "everything that
ranks nothing" sweeps in `v22`, `v23`, `v24`, `v18`, `v16` and `v12`, whose levers all fired.
Both readings were therefore computed rather than one being chosen.

- **STRICT (n=6)** — same build as v10, lever proven inert or absent: `v10cal` 4.71 ·
  `v10out` 4.55 · `thui-v1` 3.20 · `v19` 2.82 · `thui-v1-1` 5.24 · `thui-v1-1-r2` 4.33.
  Mean **4.14**.
- **LOOSE (n=9)** — everything this file calls an in-band sample of the family, adding
  `v25` 3.69 (⚠️ its own row says it *"is NOT v10+seed and must not be quoted as one"*),
  `v26` 3.19 (brake fired) and `thui-v2-0` 2.86 (retrieval off). Mean **3.84**.

| numerator | denominator | shrink | public needed for the bar |
|---|---|---|---|
| STRICT n=6 | all 4 draws, 1.4225 | **2.91x** | 9.23 |
| STRICT n=6 | attributed 3, 1.4367 | **2.88x** | 9.14 |
| LOOSE n=9 | all 4 draws | **2.70x** | 8.57 |
| LOOSE n=9 | attributed 3 | **2.68x** | 8.48 |

**All four land inside 2.68 - 2.91.** The population-boundary question CORRECTION 3 refused to
guess at turns out not to matter: it opens an 8% spread against a **22-23% CV on the public
samples themselves**. That is the useful half of this result.

`clock2x` 6.40 is excluded from every row. It is statistically in-band (`p = 0.2761` vs
`v10cal`) but under `TRUE_SUBMISSION` its cell 12 degrades to v10 by design, so **6.40 is not a
number the hidden set can ever draw**. Including it gives 2.88x-3.14x, i.e. pushes the ratio the
same way; it is left out because a predictor built from unreachable configurations predicts
nothing.

**The consequence is the opposite of R30's.** That correction moved the target *down*, 8.83 to
7.29, and said so in as many words — *"it moves the target the easy way"*. That has now fully
reversed, by two movements pulling together: the hidden mean fell 6% (1.51 → 1.42), and
`thui-v1-1` is the family's **highest** public (5.24) *and* its **lowest** hidden (1.29), so both
ends of one run push the ratio up.

⚠️ **And the bar itself moved, which no recompute could have caught.** Board re-downloaded
2026-08-26 01:18 UTC (read-only, no submission spent): the top-5 bar is **3.17, not 2.88**.
`Lord Han Solo` gained **+1.63** in a day to 4.99, `Tong Hui Kang` 3.39 is new to the top five,
`Tony G` 3.17 is the bar, and `Daniel Franzen` 2.88 was pushed out of it. `cstl` holds #1 at
5.99. We are rank **275 / 2,537** on an unchanged **1.70** — the rank slipped 22 places under a
score that did not move, and the submission count 10 → 12 is draws 3 and 4. **The bar drifted
+0.29 in 23.4 hours**, so a target computed against a stored bar is wrong within a day, in the
direction that flatters the agent.

**Target against the live bar: public 8.48 - 9.23** — back *above* the 8.83 R30 replaced.

| candidate | public | predicted hidden | vs bar 3.17 |
|---|---|---|---|
| v10 family as it stands | 4.14 | 1.42 - 1.55 | MISS by ~1.7 |
| B20 efficiency ceiling | 5.80 | 1.99 - 2.17 | **MISS** |
| `clock2x`, best public ever recorded | 6.40 | 2.20 - 2.39 | **MISS**, and unsubmittable |
| +1 level per game | 12.07 | 4.15 - 4.51 | **CLEARS** |

**The efficiency direction is now closed twice over** — B20 already ceilings it at 5.80 public
through the scorer's `completion_cap`, and this ratio puts 5.80 at 1.99-2.17 hidden, missing a
bar that has since moved further away. Independent corroboration in passing: B20 derives
*"~2.1 hidden"* for that ceiling from the cap arithmetic alone, never from a shrink ratio, and
2.1 falls inside 1.99-2.17. Two derivations, one number.

**Only structural depth clears, and now with a number attached**: about **+0.7 levels per game**
reaches 3.17, while the bar moves at +0.29/day. That is the same conclusion the frontier already
carried — `B34` closed depth-by-time, `B36` is priced under one level per run — but it was not
previously quantified.

⚠️ **A per-build ratio is unusable and must not be quoted.** Six builds carry both numbers, and one of them now carries TWO draws:

| build | public | hidden | ratio |
|---|---|---|---|
| duck-mod | 2.41 | 1.00 | 2.41x |
| v5out | 2.43 | 0.84 | 2.89x |
| v10out | 4.55 | 1.70 | 2.68x |
| **thui-v1-1** | **5.24** | **1.29** | **4.06x** |
| **thui-v3-0** | **4.01** | **1.63** | **2.46x** |
| **thui-v3-0 v3** | **4.52** | **1.59** | **2.84x** |
| **thui-v1-1-r2** | **4.33** | **2.02** | **2.14x** |

That spans **2.14x - 4.06x** around a mean of **2.78x** — i.e. **-23% to +46%**, an asymmetric spread that no single figure summarises — on a single hidden draw each (sixth member 2026-08-28: the LOW end came from the family's best hidden draw, not from a weak public run). The
ratio-of-means over a population is the only form with any stability, and even it inherits a
hidden CV of 0.133-0.159. **Predicting one build's hidden score from its public score is not
supported by this data** — only the population-level target is.

⚠️ **`thui-v3-0` is now the direct proof of that.** One build, two draws of the identical
lever, and its own ratio moves **2.46x -> 2.84x (+15%)** — so the instability is not merely
*between* builds, it is inside a single build, and a per-build ratio cannot be rescued by
picking a better build. Both of its rows are listed above deliberately, rather than averaged,
because the row's non-hidden columns (public, actions, Mtok) are per-RUN and merging them
would destroy V1's figures.

⚠️ Every figure above is a dated reading. The bar moved 10% in one day. Re-download before
quoting the target; the call is free and read-only. Full pass, with its controls:
`notes/B-shrink-ratio-recompute-2026-08-26.md` in `Knowless-Crew/arc-agi-pub` (#110).

### Where the variance comes from — per-game, and the big earners are the unstable ones

Asked "compare the logs of the two v10 runs and find what went wrong". Two limits first,
because they bound the answer:

- **The two HIDDEN runs cannot be compared at all from our side.** Submission uses
  `-k sahasawatt/taaf-duck-v10`, so Kaggle re-runs the kernel against the hidden set;
  both submissions uploaded the *same* `submission.parquet` (md5 `f1f99148da4a`, 2648 B).
  The 1.70 and the 1.32 runs happened on Kaggle, privately.
- **`kernels output <kernel>/<version>` silently ignores the version.** Versions 1, 2 and
  4 (4 may not even exist) all returned a byte-identical `benchmark.json`, md5
  `27b8e13acaa3`. So the 4.55 run's log is not retrievable either.

What IS on disk: v10cal (4.71) and v18 (3.60). Per game:

| game | v10cal | v18 | delta | levels |
|---|---|---|---|---|
| re86 | 0.124 | **27.143** | **+27.0** | 1 → 4 |
| ft09 | 22.966 | 4.762 | −18.2 | 3 → 1 |
| dc22 | 14.286 | **0** | −14.3 | 2 → 0 |
| lp85 | 16.667 | 8.333 | −8.3 | 3 → 2 |
| cd82 | 6.534 | **0** | −6.5 | 2 → 0 |
| ar25 | 8.333 | 2.778 | −5.6 | 2 → 1 |

**7 of 25 games (28%) flip between scoring and zero**, and the run mean moves only
4.71 → 3.60 because swings of ±27 on single games cancel each other out.

That pair is not a clean A/A (v18 also changed the upscale), but a ±27 swing on one game
is far larger than one knob explains — and the ledger already holds a true A/A: **v10out
vs v10cal, identical build, 22 vs 28 levels and 1285 vs 1597 actions.**

**The mechanism is structural, not a bug.** `score = (base/actions)^2 × level weight`, so a
deep level pays enormously (ft09 at level 3 = 22.97) and clearing a deep level is the part
that is a coin flip. **The games that earn the most are the least stable ones**, which is
why a 110-run hidden mean moves 25% between draws of one build.

Consequence for what to build: a lever that raises the *mean* while leaving this coin flip
intact inherits the same spread. `banking` (v19) replays an already-won trace
deterministically, so it should raise the floor on levels already cleared rather than buy
another coin flip — UNVERIFIED until v19 lands, but it is the reason it outranks the rest.

### CORRECTION (same day) — act/lvl is a symptom, and the axis has a hard ceiling

The table above is real but it is not the mechanism, and reading it as one points at the wrong
work. The scorer has **two** caps, and the second was missing from my recall until it was
recovered from `R4-ev.md:19-20` and verified against `benchmark.json`:

```
level_score(i)  = min((base_i / actions_i)^2 * 100, 115)     0 if the level was never completed
raw             = sum(level_score(i) * i) / W                W = 1+2+...+N
completion_cap  = 100 * sum(i for i in DONE levels) / W
game_score      = min(raw, completion_cap)
```

Verified exactly on five games of v10cal (`dc22` 14.286, `ar25` 8.333, `ft09` 22.966, `sc25`
11.759, `vc33` 8.699). The `completion_cap` term is why a formula without it overshot two of
four games by precisely 100/115.

What that changes, measured on v10cal:

| | |
|---|---|
| games already AT the completion cap | **7 of 25** — speed buys them exactly zero |
| share of total score locked at that cap | **41%** (48.3 of 117.8) |
| gain if every remaining game reached its cap | **+1.09 mean → 5.80 public** |

**So the entire efficiency axis has a hard ceiling of 5.80 public (~2.1 hidden).** It cannot reach
the 6.9-7.1 needed for top-5, let alone the ~8.0 that hidden 3.0 implies. Every efficiency win
listed in the table above was real, and the axis is now nearly spent.

Depth, by contrast, is not close to spent — recomputed through the true formula, assuming any
newly cleared level is taken at pace:

| every game clears | public | hidden @2.72x |
|---|---|---|
| +0 (today) | 4.71 | **1.73** (actual draw: **1.70**) |
| **+1 level** | **12.07** | **4.44** |
| +2 levels | 23.10 | 8.49 |
| all levels | 100.0 | — |

One extra level per game multiplies the score by **2.56x**. Hidden 3.0 needs public ~8.0, which
sits between +0 and +1 — about **0.6 extra levels per game**, i.e. one more level in roughly 15 of
the 25 games. That the +0 row predicts 1.73 against an actual 1.70 is the closest thing to
validation the shrink model has.

**Consequence for what to build next: nothing on the efficiency axis can reach the target, and
depth overshoots it. All remaining effort belongs to clearing levels we currently cannot.**

A corollary that killed a lever the same hour: actions burned on a level that is never cleared do
not enter any denominator, so a plateaued game that keeps acting costs **nothing** in score. The
"detect the plateau and stop playing" idea is worthless — it was proposed, measured and dropped
within one exchange.

The two exceptions prove the shape rather than breaking it:

- **v16** got act/lvl to **50.8**, the best ever, and scored 3.51. It spread its efficiency across
  *more games at shallow depth*, and the level-number weighting does not pay for shallow.
- **v14** raised throughput 26% and act/lvl went the wrong way (57.0 → 85.9). Capacity was spent on
  attempts.

### The axis, now measured in both directions (2026-08-23)

Three runs cut *reasoning per decision* three different ways, and depth fell every time:

| run | how thinking was cut | actions | levels | public |
|---|---|---|---|---|
| v14 | not cut — throughput raised 26% | more | 19 | 2.87 |
| **v21** | effort xhigh→medium (−39% tok/action) | ×1.8 | **12** | 1.25 (p=0.0052) |
| **v20** | capability 27B dense → ~3B active | ×4.7 | **3** | 0.18 (p=0.0001) |

**Deliberation per decision is monotonically load-bearing on this task**, and xhigh — the
maximum — is what v10 already runs. The rank-21 team ships `medium` inside a 6-file change
(trimmed prompt + a tried-this checklist); the flag alone, on our stack, is decisively
negative. There is no thinking-dial headroom left upward, no larger dense model on either
Kaggle registry, and the harness axes are closed. That is the evidence-backed shape of why
hidden 3.0 is out of reach with the models this competition makes available.

## What is closed, with the number that closed it

| direction | verdict | evidence |
|---|---|---|
| cap the model's output | dead | v9 = 0.22; 704 `length` finishes vs 68 tool calls |
| ask for brevity in the prompt | dead | v12 = 3.72, below v10's band |
| raise inference throughput | dead | v14 = 2.87 with the mechanism confirmed working |
| push more state into the turn | dead | v16 = 3.51 with delivery doubled |
| fix the "retry spiral" | ~+0.1 | only `lf52`/`tr87` exceed the streak threshold, and scoring games reach 25 |
| a better dense model | exhausted | Qwen3.8-27B-FP8 is the newest on Kaggle |
| a luckier draw | capped — **and now the operating route** | best-of-each-game oracle on v10 = 6.73 public ≈ 2.4-2.5 hidden — under the top-5 bar. **2026-08-28: the first deliberate repeat draw moved the board 1.70 → 2.02**, inside that ceiling; at the measured σ 0.313 (n=5), spending all 33 remaining slots on family repeats projects E[max] ≈ 2.2 — the draw route saturates under the moving bar (3.37), so depth remains the only route past it and every measured depth lever is dead |

## Where the points actually are (v10cal, the best run)

Top 8 games = **80%** of all points, and every one of them cleared **2-3 levels out of 6-9**.
31 of 51 cleared levels are already at the 115 cap, so efficiency on what we clear is nearly spent.

Six of those eight **plateaued and kept playing**: last level-up at 27-59% of their clock, actions
continuing to 75-95%. `ar25` cleared its last level at **27%** and spent the remaining 51% of the
clock acting without progress.

That is the one harness decision nobody has built: **it cannot tell that a game has stopped making
progress, and it has no move to make when it has.** Every other decision the harness makes — time
per game, yield budget, no-op blocking, animation nudges — is either fixed or already measured.
