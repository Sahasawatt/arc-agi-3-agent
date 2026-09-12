# thui `animfast b71` — public 9.5584 and hidden 3.74, both the campaign's highest and both NOT-DISTINGUISHABLE from their own siblings; the ACTION axis is the only thing that ranks

## The one change

The **solver bundle**, and nothing else. `B69`'s chassis exactly — Keith Tyser's Flash-Next NVFP4 serving stack,
profile `kv5-bf16-mtp3-c8-cg32`, `TAAF_VLLM_MTP_TOKENS=3`, model asset `keithtyser/qwen3-8-flash-next-nvfp4` —
with Tufa's **June** duck bundle replaced by the **anim** bundle
`jakobbrggen/taaf-kaggle-source-anim-20260807-anim` on `sys.path`, plus the thui-v3 knobs
(`LOCAL_ANALYZER_SEED=20260825`, `LOCAL_ANALYZER_YIELD_SECONDS=180`). Budget 7,920 s / game, concurrency 28,
`max_actions_per_game = None` — identical to every full25 run in the LEDGER.

⚠️ **It is NOT the anim-base lineage.** The arm was first filed under the outside Qwen3.8-base notebook that
drew 4.16, from the kernel's *name* and its search result set. Pulling the artifact refuted that: 18 cells whose
serving base is Keith Tyser's notebook. The comparator is therefore the **Flash-Next family**, not anybody's
4.16 — a cleaner question, and still unanswerable at n=1.

⚠️ **The id `B71` is PROPOSED, not minted** — unclaimed at ceiling `B79` across all 69 remote tips, and used
because two *published* artifacts already assert it (the upstream notebook's cell 0 and our public slug).
Redirect it and this page moves.

## Where it lives

- Builder / vendored upstreams / notebook: `thui-anim-fast/` (it does **not** reconstruct the original
  authoring — that script is absent from every branch; it vendors Keith Tyser's notebook and
  `sahasawatt/thui-animfast-v1` and asserts the graft at cells **0, 1, 3, 5, 7, 9, 11, 15**).
- Kernel: `yocybercode/thui-animfast-b71-full25-r1` version 1, COMPLETE `2026-09-11T05:22:21Z`. **PUBLIC** —
  `is_private: false` was inherited verbatim from the upstream metadata and nothing chose it.
- Upstream that validated the notebook: `sahasawatt/thui-animfast-v0` / `-v1`, both COMPLETE, **never submitted**.
- Fixture: `eval/fixtures/thui-animfast-b71-full25-r1.json`. **No arm declared** — n=1.
- Run evidence: `~/Claude/arc-artifacts/_src/animfast-b71-run-2026-09-11/`; read-up in the workspace repo at
  `notes/B71-animfast-the-action-axis-moved-and-the-score-did-not-2026-09-11.md`.

## What it scored

| | public | levels | scoring | actions | act/lvl | gen tok | wall |
|---|---|---|---|---|---|---|---|
| v1 | **9.5584** | **39** | 20 / 25 | **2,008** (80 / game) | **51.487** | 1.825 M | 8,616 s (benchmark 8,005 + setup 611) |

**Hidden: 3.74** — `56160405`, submitted 2026-09-11 06:37:53Z (version 1, over a firing `G6`, on the
owner's explicit instruction, the override printed into the run), resolved and read from
`competitions submissions -v` on **2026-09-12 02:07Z** with `56144280` = 3.49, `56122994` = 2.68 and
`56099301` = 3.32 in the same call as controls, all three reproducing what the LEDGER already records.
The pre-registered `> 3.49` bracket fired.

| | draws on this chassis | mean | sd | range |
|---|---|---|---|---|
| before | 2.68 / 3.21 / 3.32 / 3.49 | 3.175 | 0.350 | 0.81 |
| with this one | 2.68 / 3.21 / 3.32 / 3.49 / **3.74** | 3.288 | — | **1.06** |

⚠️ **It ranks nothing.** Against the four prior draws at the pooled within-build hidden sd
**0.317 (df 7)**, 3.74 is **z = +1.78, two-sided p = 0.075 — NOT DISTINGUISHABLE**. Establishing the
+0.57 gap over that mean at 80% power needs **n = 5 submissions per arm**; the +0.25 step over the
previous best needs **n = 26**, i.e. 26 days at one slot a day. (Both re-derived by
`notes/probes/analyze_hidden_regimes.py` §7 in the workspace repo, which ceils rather than rounds
because a submission is indivisible — a `.0f` print reported 25 for the 25.24 this needs.) And **Kaggle keeps the MAXIMUM**, so
the board column reads 3.74 while saying nothing about which of five draws it is.

ⓘ Shrink pair **9.5584 / 3.74 = 2.556×** — below the 2.68–2.91 population band, the second sample to
land there after B78's 1.99×. It widens that spread downward; one sample moves no band.

Per game: ft09 5 · lp85 4 · ar25 re86 sc25 tu93 vc33 3 · dc22 su15 2 · cd82 ka59 lf52 ls20 r11l s5i5 sb26 sp80
tn36 tr87 wa30 1 · bp35 cn04 g50t m0r0 sk48 0.

**Score — NOT-DISTINGUISHABLE against every sibling on its own chassis:**

| baseline | mean | levels | p | verdict |
|---|---|---|---|---|
| `thui-fast-pool` (B69, June solver) | 8.69 → 9.56 (+0.87) | 38.5 → 39.0 | **0.6762** | NOT-DISTINGUISHABLE |
| `thui-a7-full25-r1` (same stack + ACTION7) | 8.25 → 9.56 (+1.31) | 38 → 39 | **0.6980** | NOT-DISTINGUISHABLE |
| `thui-fast-b78-mtp0-full25-r1` (same stack, MTP off) | 6.96 → 9.56 (+2.60) | 40 → **39** | **0.4839** | NOT-DISTINGUISHABLE |
| `thuiv3-pool` (the **previous** chassis) | 4.39 → 9.56 (+5.17) | 24.25 → 39 (+14.75) | **0.0006** | **BETTER** |

The only ranking row is the last, and it is **`B69` restated** — the serving swap. ⚠️ The `b78` row is the one
to read twice: **+2.60 on the mean with −1.0 on levels**, so nothing here says "deeper".

**Actions — DISTINGUISHABLE, and the instrument was proved before it was read.** `rank_runs.py`'s own
`perm_test`, imported rather than reimplemented, the import validated by reproducing that tool's published
`0.6762` / `0.0006` score p-values exactly in the same invocation:

| axis comparison | Δ actions / game | p |
|---|---|---|
| vs `thui-fast-pool` | **−69.2** | **0.0000** |
| vs `thui-a7-full25-r1` | −73.4 | 0.0001 |
| vs `thui-fast-b78-mtp0-full25-r1` | −81.6 | 0.0002 |
| vs `thuiv3-pool` | +22.2 | 0.0004 |

Negative controls on that same axis, all same-build pairs, all NOT distinguishable: `thui-fast-v0`/`-d2`
**−14.9, p = 0.5615** (this chassis) · `v10cal`/`v19` p = 0.9072 · `thuiv1-1`/`-r2` p = 0.7348 ·
`thuiv3-0`/`-r2` p = 0.4499. Positive pole `v10cal → v20`: **p = 0.0000** at +242 actions. So **−69.2 is 4.6×
the same-build action noise**, and the test is not simply always significant on count data.

act/lvl **51.487** sits in the *previous* chassis's efficiency band (thuiv6-0 48.0, thuiv3-2 52.8, thuiv1-1 53.0)
while holding *this* chassis's level count, against the family's 86.7 / 97.1 / 101.1 / 101.2.

## Verdict

**NOT MEASURABLE on score at n=1, on EITHER scale** — exactly as pre-registered. 9.5584 being the campaign's
highest public mean, and 3.74 its highest hidden draw, are both facts about a maximum over one draw rather
than about the agent. The campaign's own record for how little that means is this build's own family: the
`a7` arm spans 5.76 / 8.23 / 8.25 public on one declared build, and drew 3.32 then **2.68** hidden on one
unchanged notebook version — a 0.64 swing, wider than the 0.25 that separates this draw from the last best.

**But "no difference" is refuted.** The action axis separates the anim solver from the June solver on identical
serving at p ≤ 0.0002 with both poles of its own control — so this is a different agent that scores the same.

🔴 **The reading that would invert all of it was checked, not assumed.** Fewer actions in the same clock is what
a *hanging* solver looks like, and under that reading 9.5584 is luck. Refuted: all **25 games `state=gave_up`**
(every one burned the full cap, `action_cap=None`, so the run is clock-bound and the action count is a choice),
**`analyzer_timeout` fires 0 times**, 0 `Traceback`, 0 `call FAILED`, 0 `cancel`, 0 `retry`; 30 `Read timed out`
**lines** — quoted as lines, because stderr doubling is on record in this corpus, so ≤ 30 events, not re-derived.

⚠️ **Where the clock went instead is UNMEASURED and has no ticket.** 909 tok/action is *below* the campaign's
1,272–1,640 band, so it is not buying more reasoning per action either, and no sibling token totals were
harvested, so no paired test on tokens exists. **Half the actions, fewer tokens, the same score, the same clock**
is the measurement; the mechanism is not.

⚠️ Median spent/human over the 39 cleared levels is **0.72** — level with the 425-run census median 0.7541, so
this run is **not** unusually cheap per level; its advantage is wasting fewer actions on levels it never clears.
That is also nowhere near `B35`'s shippable **m = 1.140–1.145**.

## Provenance ⚠️

**Every number on this page was read off the PUBLIC kernel page, not `kernels output`** — the 1Password vault
answered `authorization timeout` throughout, and the read was only possible because the re-push inherited
`is_private: false`. Two independent instruments, each with its own control, agreeing game-for-game:

- **`score.json`**, exact floats. The 25 harvested games' mean reproduces the file's own `score` field
  `9.558403032428732` **to 1e-9** — the completeness control, which a partial harvest cannot pass.
- **The last of 14 repeated log summary blocks** (350 game-lines / 25 games), identifiable because only the final
  block carries `note="tokens=…"`. Its action sum equals the run's own
  `PUBLIC25_AUDIT runs=25 actions=2008`; the **first** block sums **175** — the negative control, and the exact
  size of the error a mid-run read would have made. Log line markers 1 … 1,141, all present.
- `benchmark.json`'s preview showing `game_runs: [6 items]` is a **preview truncation artifact** (the pane says
  so) and was refused as a reading.
- Benchmark identity in the same read: `label = anim-20260807-anim`, `solver_label = duck-harness`,
  `n_passes = 1`.

**Hidden: 3.74, drawn 2026-09-11 (`56160405`), read 2026-09-12.** The sentence that stood here — *"Hidden:
not drawn. No submission was spent on this build."* — was true when written and is kept as the record of
what changed. What it predicted still holds: the shrink band is 2.68–2.91× with per-build ratios spanning
2.41×–4.06×, so 9.5584 predicted nothing usable, and the pair it actually produced (**2.556×**) landed
*outside* the band in the direction B78 had already opened.
