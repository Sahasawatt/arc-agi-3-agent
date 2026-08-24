# R33 — v22 does not carry a new BFS instruction, and its two real bullets have no room to move

2026-08-24. Re-aims **B28**. Offline, 0 slots, 0 submissions.
Instrument: `scripts/b27/b28_v22_probe.py`, four controls gating it, all passing, exit 0.

## The premise is false

B28's row reads: *"v22's ported addendum carries the rank-21 team's explicit BFS instruction.
When v22 lands, re-run the v17 search-construct probe over its transcripts."*

The BFS bullet is **byte-identical** in the stock addendum and in the port, and it has shipped
in **every run of this campaign**:

```
run      sysprompt  addendum   BFS  flood fill  beam search | 'already tried'  CTRL cf/zzqq
v10cal      14189      3814      2      1           1       |       0            20 / 0
thuiv1      14189      3814      2      1           1       |       0            20 / 0
v18         14189      3814      2      1           1       |       0            20 / 0
v19         14189      3814      2      1           1       |       0            20 / 0
v23         14369      3814      2      1           1       |       0            21 / 0
```

The bullet, present on both sides word for word:

> `- IMPORTANT: Especially when the game is about making an agent navigate to a target, it is
>   usually safer to write an explicit search algorithm such as BFS. …pathfinding, flood fill,
>   BFS, DFS, beam search, shortest-path search, limited action-sequence search, or custom
>   heuristics are all valid.`

So a search-construct probe over v22 measures a prompt difference that **does not exist**, and
whatever it returns — up, down or flat — cannot be attributed to a BFS instruction.

**`duckv22/cell12_prompt_port.py` is not the thing that is wrong.** Its own comment names the
change correctly — *"Their two genuinely new bullets"* — and the measurement agrees: stock
addendum 23 bullets / 3,814 chars, port 18 bullets / 4,568 chars, **12 verbatim identical**,
and the rest reworded apart from two additions:

1. keep a tried-checklist in `Recent findings:` — *"before you declare a 'completely different
   approach', read that checklist"*
2. never transcribe ASCII rows in your own **reasoning** — write code for diffs instead

The cell's teeth assert only on (1) (`"already tried"`), which is why a run whose BFS half is
unchanged still passes them. The teeth are right about what they check. It is the frontier
ticket that describes a different experiment from the one that was built.

## And the two real bullets have almost nothing to fix

Both new bullets target behaviours whose baseline is already at the floor, measured over the
same five runs:

| baseline | v10cal | thuiv1 | v18 | v19 | v23 |
|---|---|---|---|---|---|
| turns carrying a `Recent findings:` block | 1 / 974 | 10 / 999 | 2 / 1062 | 2 / 969 | 2 / 1048 |
| | 0.10% | 1.00% | 0.19% | 0.21% | 0.19% |
| turns transcribing ≥3 ASCII board rows in `[THINKING]` | 7 / 974 | 4 / 999 | 2 / 1062 | 0 / 969 | 1 / 1048 |
| | 0.72% | 0.40% | 0.19% | 0.00% | 0.10% |
| rows transcribed, total | 196 | 89 | 70 | 1 | 3 |

Bullet 2 forbids something that happens in **0 to 7 turns of ~1,000**, and in three of the five
runs costs the agent **1 to 70 rows** for a whole run. Bullet 1 asks for a checklist that four
of five runs produce in **1 to 2 turns**.

Set against B28's own floor (R29 §10): stratified on the game, a single v22-sized run detects
**+3 pp per game**. These baselines are ~0.2%. A bullet that *doubles* either of them moves
0.2 pp — two orders of magnitude under the floor.

**So v22 as built cannot rank anything, whichever probe is used.** That is a slot saved, not a
result withheld.

## What to do instead

- **Do not spend a slot on v22 as a B28 test.** Either rebuild it around a bullet whose baseline
  has room, or drop the ticket. If it runs anyway for another reason, read it against the two
  probes above, whose baselines are now recorded.
- **Run B28's search-construct probe as a NEGATIVE control** if v22 does run. The BFS text is
  unchanged, so a moved search rate is evidence the *probe* drifts between runs — which is
  exactly what R29 §10 already found unstratified (4 of 10 unprompted pairs separate, worst
  `thuiv1` vs `v23` p=0.0003) — and not evidence the prompt worked.
- **Fix B28's row text.** It states a file fact that a grep refutes, and the row is the thing
  the next reader will act on.

## What is NOT established

- The port is compared against the **stock addendum as it reaches the system prompt in the five
  recorded runs**, not against `inference/agent/prompts.py` on disk in whatever bundle v22
  pins. If v22 re-bases onto a different bundle, the stock side moves and this must be redone.
- The bullet-level diff calls 12 of 23 identical and the remainder "reworded". That
  classification is by eye over the printed pairs; only the BFS bullet and the two additions
  were checked byte-for-byte.
- The ASCII-row detector keys on the prompt's own colour alphabet at ≥40 characters. It is
  proved on a real board row and on a prose line in the same invocation, but a partial row or a
  row the model paraphrases is not counted, so the transcription baseline is a **lower bound**.
- Nothing here says the rank-21 team's prompt is not better. It says **this** diff cannot be
  measured by **this** campaign's probes on **one** run.

## Controls

1. **Present/absent pair on the system-prompt reader** — `current_frame` 20–21 hits per prompt,
   `zzqq` 0. A `BFS=0` from a broken reader would have read as the premise being *true*.
2. **The addendum is isolated by its own header** (`Python tool guidance:`) and re-found at
   3,814 chars in all five runs, so the diff is addendum-against-addendum and not
   addendum-against-whole-prompt (the first cut of this compared 18 bullets against the
   system prompt's 83 and reported "71 bullets removed", which is nonsense).
3. **The ASCII-row detector is proved in the same invocation** on a real `board_ascii` row
   (matches) and on a prose bullet (does not).
4. **Every rate carries its denominator**, and the counters that could return an uninformative
   zero carry a present/absent control beside them.

## Reproduce

```bash
python3 scripts/b27/b28_v22_probe.py
```

Reads `~/Claude/arc-artifacts/{v10cal,thuiv1,v18,v19,v23}` and
`duckv22/cell12_prompt_port.py`. Zero GPU slots, zero submissions, no model calls.
