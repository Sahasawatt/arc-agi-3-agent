# R56 — arena verdict: two adversarial agents on the next lever, and the three things they corrected in my own notes

**2026-09-13.** Two agents, same brief, no contact in round 1, cross-examination in round 2. Judge =
the main session, which re-ran **every** cited computation. Brief and rubric were fixed before either
agent started (`ARENA.md`, outside this repo). The contest was not a debate: a proposal scored only
if it **survived the evidence already on disk while an adversary was paid to find the computation that
kills it**.

## Verdict: B wins

| axis | A | B |
|---|---|---|
| proposal | reopen B24 — fetch Tufa's **current** upstream, diff against the forked snapshot `6d8e3dd`, port via cell-6/8/12 | `thui-fast27` — swap the served model on the Flash-Next chassis from the 8B to `unsloth/Qwen3.8-27B-NVFP4` |
| round-1 citations that reproduced | **2 / 3** | **4 / 5**, every field exact |
| the miss | pred 3's **mechanism**, i.e. its central argument | pred 3's **command** (hex-escaped path, did not run) |
| round-2 attacks that reproduced | **2 / 2** | **2 / 2** |
| cost | 2 slots + GPU + credentials, **and its premise needs network access nobody here has** | 1 slot + GPU + credentials |
| conceded anything | no | **yes — conceded the mechanism and replaced its refuter** |

B wins on three things that are not close. Its citation accuracy was higher and its one failure was
cosmetic where A's was the mechanism of its own case. Both of its attacks landed on A's core. And
asked to defend a refuter the judge had already shown to be hollow, it **replaced** it with a better
one instead of restating it.

## What B landed on A (both verified)

1. **A's step 1 is work this repo already did and already closed.** `notes/R39-…md:14` reads
   *"75 files each, identical file set, **14 files differ in content**"* — a byte-diff of the pinned
   bundle against **exactly** `6d8e3dd`, the revision A called "the only revision B24 ever compared".
   Every differing file was characterised there; the one live candidate (`animation_retrieval`) was
   bracket-tested from both ends and **B13 was CLOSED 2026-09-01**. A proposed to re-derive a refuted
   diff.
2. **A's porting mechanism has a documented silent-no-op trap and A's plan has no check for it.**
   `solo/solo_patch.py`'s header, verbatim: *"B41's ticket said the change was 'one line in cell 12'.
   That is **WRONG and would have been a silent no-op**: cell 14 REPLACES bm.games wholesale on both
   paths"* — caught only by `solo/prove_teeth.py`'s placement mutation. A's *"port whatever the
   mechanism can reach"* would report a discarded patch as ported.

## What A landed on B (both verified, and one lands on me)

1. **B's patch surface does not exist on the chassis it names.** In
   `thui-anim-fast/thui-animfast-b71-full25-r1.ipynb` cells **8 and 12 are markdown** (233 and 181
   chars). The code cells are 3/5/7/9/11/13/15/17, and the `nvfp4`/`MTP` references live in **7 and 9**
   with `vllm` in **15**. B took CLAUDE.md's *"every version patches notebook cells 6/8/12 only"* —
   which is the **duck** numbering — and applied it to Flash-Next, the same off-by-one family as
   `bm.n_passes` sitting at cell 14 on `thuiv3` and **cell 15** here. Worse for the cost estimate:
   cell 7 carries `DATASET_SOURCES = ["keithtyser/duck-qwen38-nvfp4-mtp-vllm-smoke-v1", …]`, so the
   serving stack is a **third-party Kaggle dataset**. Swapping the model means replacing that
   artifact, not patching a cell — B's "1 slot, cell patch" is understated.
2. **"B6, 2.41 → 4.55" is wrong, and I propagated it.** MAP's **B6** row is `duckv8` at **3.31**
   public; the **4.55** is **B10** (`duckv10` = anim bundle **plus** Qwen3.8, so confounded).
   `notes/B64-…md:13` carries the bad figure while line 163 of the same file says B6
   *"moved within one family"*. Neither B6 nor B10 has a fixture, so **neither was ever
   `rank_runs`-tested**. Corrected in `ARENA.md`, R55 and the external findings doc.

   ⇒ The true record of the "change what runs underneath" class is **one significance-tested win
   (B69, p = 0.002)** against **one catastrophe (B64/Gemma, 0.41, p = 0.0, WORSE, 20 up / 2 down)**,
   plus B6's smaller untested bump. Both agents opened by calling it 2-for-2.

## The judge's own addition — the gap is a LEVEL, not a RATE

Both proposals' urgency rests on upstream pulling away. Read with its neighbours, it does not:

| quantity | 2026-08-24 | 2026-09-08 | ratio |
|---|---|---|---|
| `Tufa Labs` hidden | 4.58 | 11.04 | **2.41×** |
| top-5 bar | 2.88 | 5.96 | **2.07×** |
| this fork's hidden | 1.70 | 3.575 | **2.10×** |

The whole board roughly doubled in that window. The fork is **tracking the field** and sitting below
the bar — so "upstream more than doubled" is true and is not evidence of divergence. B's
*"single largest unexplained gap in the entire ledger"* overstates it.

⚠️ And the bar is harsher than either agent priced: CLAUDE.md's B35 arithmetic requires a shippable
lever to add a level in **25 of 25 games at m ≤ 1.14**, while *"the best any of the other 18 runs
managed is `clock2x` gaining in 6 of 25 games while losing 4"*. Nothing has ever been broad.

## The prize — B's amended refuter, which is the best artifact either agent produced

B's original refuter was a load/serve smoke test. The judge handed it the LEDGER row that kills that:
`thui-gemma-v1` was *"1.85× slower per request under 25-way load (185 s median, 45 ReadTimeouts)
**which the 3-game smoke could not see**"*. B conceded and replaced it with a **width-matched** probe:

- same 25 games, same 25-way concurrency — the width is what the old smoke got wrong
- `max_runtime_s_per_game` capped at **300 s** instead of 900–7920, so it costs minutes
- read per-request wall median / p90 / timeout count from the `*_usage.jsonl` sidecars
- **gate** against the Qwen chassis's own numbers from B64's table: **100 s / 366 s / 36 timeouts**

This is sound on an instrument that already exists: CLAUDE.md documents
`eval/abandoned_tokens.py --fetch-usage <run>`, i.e. `file_pattern=r".*_usage\.jsonl"` returns all 25
usage files (largest 20 KB) without the 250 MB blob. It is also the right shape in general — it scales
the **oracle** to the real width rather than shrinking the rehearsal, which is the rehearsal-width trap
CLAUDE.md's own B64 post-mortem names.

**It should gate every future member of the only class with a significance-tested win**, not just a
27B swap.

## What this note does not do

It does not reopen B24, close B71, or add a MAP row — all the maintainer's. It does not endorse
either proposal as worth a slot: A's is largely dead work by R39/B13, and B's is under-scoped on the
patch surface and under-priced on the serving artifact. Both agents' own final answer to *"if the
owner could do one thing"* converged on the same thing, and it is cheaper than either proposal:
**fetch Tufa's current public notebook and READ it.**

## Three corrections to my own notes, all forced by this round

1. **"The scorer is not vendored"** (R53) — false. It is at `localrig/tufa-arc-agi-framework/`,
   23 tracked files. My grep searched `RHAE` / `human_baseline_actions`; that code says `baseline`.
2. **"The scorer is now runnable offline"** (R54) — it already was. `eval/oracle_ceiling.py`
   reproduces all 19 published public means exactly; my 25/25 on three runs is a weaker control.
3. **The clip-share finding** (R54) — R37 measured it first, and CLAUDE.md already carries its
   correction to **55% (38 of 69)**. My 28/49 = 57% re-measures it on a subset.

All three are fixed in place with the reasoning kept, because the pattern is reusable: **each came
from searching a corpus for my own paraphrase of a name instead of the producer's literal.**
