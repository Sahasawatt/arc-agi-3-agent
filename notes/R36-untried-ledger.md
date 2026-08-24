# R36 — B32 built: the untried-ledger nudge (duckv24), rig-verified

2026-08-24. The only open build ticket after B26-B31 closed, and the only lever with
observational evidence behind it (R28: 3/5 clears trace to a probe taken before the
theory was finished; ft09's stuck run never clicked anything for 24 turns).

## What it does

`duckv24/ledger_patch.py` wraps `ToolAgent._animation_hint_line` (the hint channel
measured obeyed — sk48 7/7): per level it accumulates which action TYPES were executed
and which cells were MOUSE-clicked, from `previous_step_summary.executed_actions`
("MOUSE(row=R, col=C)" / bare names — solver._format_action_display). At analysis turns
8/16/24... on the same level, while something valid remains untried, it appends one line:

    Probe ledger for this level: N analysis turns so far; actions tried: ...;
    NEVER tried: ...[; distinct cells clicked: M]. One cheap probe of an untried
    action, followed by reading the diff, often reveals the mechanic faster than
    more analysis of the current theory.

Cadence-gated and self-silencing (everything tried -> no line) — deliberately NOT the
v16 every-turn info push (3.51, in-band-worse). Level change resets the ledger.

## Rig verification (localrig, qwen3-8b, all on this machine, $0)

| test | game | result |
|---|---|---|
| function teeth | — | cadence floor, line content, mouse parse, level reset, everything-tried silence — run at module import |
| correct silence | ft09 | MOUSE-only game, 8B clicked from turn 0 → untried empty → SILENT for 34 turns (by design) |
| live fire | ls20 | fired at turn 8 exactly: "actions tried: RIGHT; NEVER tried: DOWN, LEFT, UP" — and the model pressed LEFT + DOWN within 4 actions; turn 16 silent (all tried by then) |

Side finding: the 27B's never-probe pathology (R28 ft09) does NOT reproduce on the
ascii-only 8B — it clicks immediately. Consistent with the wrong-goal loop being a
property of theory-building depth, not of clicking ability.

## Kernel

`duckv24/` = v10 EXACT (upscale 4, output uncapped, stock prompts) + cell 12 embedding
ledger_patch.py verbatim (teeth run in-kernel on exec, before the benchmark). Single
change vs v10 → rankable with `eval/rank_runs.py`. Built + self-checked; awaiting a
Kaggle slot (quota resets Sat 00:00 UTC). Smoke first, per campaign discipline.

## UNVERIFIED

- Whether the 27B obeys the ledger the way the 8B does (channel obedience measured on
  sk48/27B for ANIMATION nudges only), and whether obeying it buys levels — that is the
  Kaggle run's question. B28's lesson stands: induced behaviour ≠ score.
- The one-turn lag: an action executed in the same turn window as a fire can appear as
  NEVER tried (ls20's UP did). Cosmetic; the model's own last turn is in its context.


## RESULT (2026-08-25) — measured on the 27B, in-noise, B32 closed

Full run: **3.78 public, p=0.304, NOT-DISTINGUISHABLE** from v10cal (8 up / 9 down /
8 scoring-flips, levels 28→20; the highest mean of the last three builds and still
mid-band). Identity verified: armed line in the kernel log at t=450s.

The mechanism-level answer is the valuable part. The ledger fired **64 times across 18
games** with correct content, and the 27B obeyed **30/58 = 52%** (a named never-tried
action executed within 6 actions of the fire; 6 fires had no judgeable window). Against
that: hard refusal streaks — sb26 was told ACTION7 seven times and never pressed it once;
tr87 was told the four arrows nine consecutive fires across 72 turns and never touched
any. The channel that carried animation nudges at 7/7 (sk48) carries THIS content at
half rate: the model treats "you never tried X" as advice it may overrule, not as an
instruction. The 8B obeyed immediately; the 27B's deliberation is exactly what
overrules it — consistent with R28's premature-theory reading and with v20/v21
(deliberation is where both the strength and the pathology live).

R28-class games: ft09 +5.6, re86 +2.7, lp85 flat L3, dc22 −14.3, cd22/cd82 −6.5 —
single-run cells, noise-shaped, no attribution.

So B32 closes the way B28 predicted it might: induced (even half-induced) behaviour
does not convert to score. Campaign tally: **11 modifications of v10 measured, 0
outside the band upward.** The wayfinder line is fully closed — B26 through B33 all
resolved; B30 (where the remaining hidden draws go) is the only live decision, and
nothing measured this week has changed its answer: v10 resubmits for tail draws remain
the only positive-EV spend.
