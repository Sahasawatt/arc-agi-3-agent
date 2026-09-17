# B83 — remove `Cross-level notes`: is there anything to remove?

Opened 2026-09-17. Type `measure`: a 0-GPU pre-read decides whether an ablation build exists at all.

## Why this was raised

Competitor recon, 2026-09-17. Kaggle user `ataraxian` (public LB #13, 6.23 on the 2026-09-17T03:45Z board)
publishes duck-fork bundles as public datasets. Between two consecutive versions:

- `ataraxian/arc3-duck-prompt-v33a` (2026-08-17) added a **required** `Cross-level notes:` write at every level
  transition, plus parsing and persistence of it across levels;
- `ataraxian/arc3-duck-prompt-v36a` (2026-08-18) removed all of it again — `tool_agent.py` in v36a is
  byte-identical to their earlier `arc3-qwen38-colab-v29`.

**Nothing public ties that removal to a score.** Their last public bundle predates every jump on their board
history (3.48 on 09-02, 4.57 on 09-05, 6.23 on 09-15). In competition thread 732854 they describe the 6.23 build
as a private fork of the public flash-next notebook with changes to the harness structure, and say it may be
luck. The removal is therefore a candidate lever, not an observed cause.

## What our chassis has

The anim bundle every current build runs on (`jakobbrggen/taaf-kaggle-source-anim-20260807-anim`,
`src/ARC3-Inference/inference/agent/tool_agent.py`, read 2026-09-17). `localrig/ARC3-Inference` carries the same
six sites at the same line numbers.

| line | site |
|---|---|
| 424 | `"Cross-level notes"` in the prefix-extraction label list |
| 437 | extracted into `_summarized_knowledge["cross_level_notes"]` |
| 456 | initialised to `""` |
| 1347–1356 | level-transition clear wipes six slots and **spares** `cross_level_notes` |
| 1366 | rendered into the carried world model — only when non-empty |
| 1486, 2302 | named among the optional prefixes in the prompt text |

Unlike their v33a, ours never **requires** the write. It is one optional label out of seven.

## What is already measured

- **R21** (`notes/R21-the-grafts-finding.md`): on the June duck chassis the model **never wrote** `Cross-level
  notes`, in any game, in either run. 134 transcript hits were all echoes of the prompt's own prefix list.
- **B62** (`thui-reflect`): a reflection call that rewrites all seven fields, `cross_level_notes` included,
  read p = 0.9978 NOT-DISTINGUISHABLE vs `thuiv3-pool`.
- **B65-c** (fold the wiped slots into `cross_level_notes` at level-up) is parked.

If R21 still holds on the anim chassis, the slot is always empty, line 1366 never renders, and a removal arm
changes nothing but one word at 1486/2302. A build on that would be a slot spent on a run that cannot rank
anything (build-loop §0, R33 precedent).

## Step 0 — pre-read, 0 GPU (pre-registered 2026-09-17, before any count)

- **Instrument:** the banked output of the base run (`yocybercode/thui-a5-mtp0k7s28-full25-r1`, B81's run; any
  full-25 anim-chassis run output if that one holds no transcripts). Count, per game, assistant turns (text or
  reasoning) that **write** a `Cross-level notes:` line with content.
- **Echo filter:** exclude every occurrence inside system/user prompt text — R21's first count was 134 echoes and
  0 writes.
- **Positive control:** written `World model:` lines in the same assistant blocks must be > 0. A 0 there means
  the parser is broken, not that the model is silent.
- **Negative control:** the same counter over prompt text alone must return 0 after the filter.
- **Kill rule:** written notes in **fewer than 6 of 25 games** → close B83 as *no mechanism*, no build.
  The threshold is `rank_runs`' own floor: the paired sign-flip test cannot reach p < 0.05 with fewer than 6
  moving games (minimum p = 2^(1−k); k = 5 gives 0.0625). An arm whose mechanism exists in fewer games cannot
  rank at any magnitude.
- **Proceed rule:** 6 or more games → Step 1.

## Step 1 — build (only if Step 0 proceeds)

- **One change** against the base build: delete the six sites above. Everything else stays, including
  `prompts.py` and the anti-full-frame guidance that v36a removed in the same version — that is a separate lever
  and is not folded in.
- **Builder** asserts the diff is exactly those lines and compiles every changed cell.
- **Teeth**, in-kernel at import, both poles, proven red by mutation first:
  1. an assistant text containing `Cross-level notes: X` extracts nothing into `cross_level_notes`;
  2. the same text still extracts `World model:`;
  3. the rendered prompt contains no `Cross-level notes`.
- **Predictions:**
  - P1 (validity) — the teeth line is printed and 0 prompts in the transcripts contain `Cross-level notes`.
    Anything else and the run is VOID, whatever it scores.
  - P2 — NOT-DISTINGUISHABLE on levels vs the same-chassis pool. The mechanism is a rarely written optional slot.
- **Oracle:** `eval/rank_runs.py --selftest` first, then paired against the same-chassis pool. One run cannot rank
  a design (workspace constraint 8).
- **Reads in both directions:** NOT-DISTINGUISHABLE at n = 1 is underpowered, not a negative. DISTINGUISHABLE
  WORSE says the slot carries value when written, and the follow-up is the opposite lever: force the write, as
  in their v33a — the B65-c neighbourhood.

## Out of scope

- Forcing a write at transition (v33a's arm).
- The anti-full-frame and row-diff guidance removal in v36a.
- Anything read from `environment_files/`.
