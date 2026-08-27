# R43 — B38's margin was one, and the widened sweep says it was wrong

**2026-08-27, offline, 0 slots, 0 GPU.** `scripts/b27/b38_sweep.py`, five controls, teeth
proven red on two mutations.

R38 §5.1 named this as the first thing to do: *"Every number here is from `clock-2x-v1`. The
other runs' artifacts live in `~/Claude/arc-artifacts/` on the Mac and were not read. Re-running
§3's sweep across all five runs is free, changes no code, and is the first thing to do."*
It is done. There are **eight** runs on disk, not five.

R38 also named, in advance, the number it expected to be wrong:

> ⚠️ **The margin is one.** The deepest a family had fired at the moment of a real level-up is
> **19** … **That is the number most likely to be wrong here.**

It was wrong. The deepest is **55**.

## 1. The instrument reproduces R38 before it contradicts it

CONTROL 5 is external: `clock2x` at every k must return R38 §3's published table. It does —
reach **25.7%** against the published 25.9%, and **0 of 30** level-ups destroyed, on the same
run R38 measured.

Teeth, both proven red against that control rather than against a fixture:

| mutation | selftest | CONTROL 5 |
|---|---|---|
| count post-increment instead of prior-fires | 3 of 6 cases red | **FAIL** — k=20 reach 27.2% ≠ 25.9% |
| key a click by `(row, col)` instead of row alone | — | **FAIL** — k=20 reach 21.5% ≠ 25.9% |

So the sweep measures R38's quantity, and it can tell that quantity from two plausible
neighbours. A control failure exits 1 and prints no numbers.

**And it measures the quantity the BUILD enforces**, which is a separate claim. An independent
read of `duckv26/brake_patch.py` (cross-model, read-only) returns: click keyed
`("MOUSE_ROW", row)` — row only, `:50`; keyboard by name, `:51`; **every executed** action
counted, not only no-ops, `:88`; ledger reset on level change, per game, `:57`; `_K = 20`,
`:36`; B29 priority kept, `:66`; counter advances per action ITEM, `:1853`. Its one semantic
note is the load-bearing one: *"the code checks fires >= 20 before execution and increments
only after execution"* — which is prior-fires, exactly what this sweep counts.

## 2. What eight runs say

**13,176 decisions · 187 level-ups · 8 runs × 25 games.**

| k | reach | level-ups destroyed |
|---|---|---|
| 10 | 33.5% | 39 of 187 |
| 15 | 23.4% | 21 of 187 |
| **20** | **17.2%** | **7 of 187** |
| 25 | 13.4% | 7 of 187 |
| 30 | 11.0% | 5 of 187 |
| 56 | 6.3% | **0 of 187** ← safe floor |
| 60 | 6.1% | 0 of 187 |

Both headline numbers move against the lever:

- **reach at k=20: 25.9% → 17.2%.** clock2x is the second-highest of the eight
  (25.7%; `v23` 28.7%), and the low end is `thuiv1-1r2` at **3.7%**. The published figure was
  drawn from a run at the top of the spread.
- **destroyed at k=20: 0 of 30 → 7 of 187.** The margin of one is gone, and it is not a near
  miss — the safe threshold is **k=56**, nearly three times the built value.

## 3. The seven are legitimate, hand-read

| depth | run | game | level | family |
|---|---|---|---|---|
| 55 | thuiv1 | `ls20` | 2 | `(KEY, ACTION1)` |
| 42 | thuiv1 | `tu93` | 2 | `(KEY, ACTION2)` |
| 31 | v18 | `re86` | 5 | `(KEY, ACTION3)` |
| 31 | thuiv1-1r2 | `vc33` | 4 | `(MOUSE, 56)` |
| 30 | v23 | `re86` | 2 | `(KEY, ACTION1)` |
| 29 | v10cal | `re86` | 2 | `(KEY, ACTION3)` |
| 29 | v10cal | `lp85` | 4 | `(MOUSE, 41)` |

None is an artifact. `re86` appears three times across three different runs and two levels;
its own mechanic is walking a shape along an arm, so a long run of one direction is how it is
played. `ls20` and `tu93` are the two games this repo has cleared end-to-end, both by scripted
directional lines.

🔴 **The sharpest one is `vc33`.** R38's headline example of the pathology is *"`vc33` 101 clicks
along `row=56`"*. At level 4, in `thuiv1-1r2`, clicking along row 56 thirty-one times deep is
what **clears the level**. The lock and the solution are the same family on the same row of the
same game — so a repeat-count on a family cannot separate them, and `lp85` (R38's original
margin case at 19) is the same story one run over at 29.

## 4. What survives

- **The mechanism is real.** Re-measured here, **1,903 of clock2x's 2,637 actions = 72.2%**
  fire after the game's last level-up (R38 §2 published 1,920 = 73%, same denominator — a
  17-action difference, substantially reproduced but not exact, so quote 72.2% from this sweep
  or 73% from R38 and not a blend). The brake still speaks on a sixth of all decisions at k=20.
- **The safe version is much smaller than advertised.** k=56 destroys nothing and reaches
  **6.3%** — **12.9×** B29's exact-action brake (R32: 0.49%), not the 50× k=20 claimed.
- **Concentration is worse than R38 flagged.** Top 6 games carry **78.7%** of k=20
  suppressions; `tr87` alone is 31.3% and `cn04` 17.1%. R38 reported `tr87`+`ls20` at 379 of 682.
- **B40 confirmed.** `tr87` and `ft09` each fire **zero** actions in 1 of 8 runs — invisible to a
  repeat-based brake, exactly as B40 predicted. The two games with the most suppressions and the
  two games that stall are the same population.

## 5. What is still not known

1. **A blocked action is still not a better action.** Unchanged from R38 §5.2 — this measures
   only that the brake can fire without killing known level-ups, never that the agent then does
   something useful. At k=56 it fires on 6.3% of decisions; B32's law still applies.
2. **The 187 level-ups are eight draws of the public 25**, not an independent sample. `re86`
   contributing three of the seven is one game's mechanic, not three witnesses.
3. **Reach is a prediction about behaviour the brake itself changes.** Unchanged.
4. **k=56 was chosen by this corpus's maximum.** A ninth run with a deeper legitimate level-up
   moves it again — the same failure mode as k=20, one level up. The safe floor is a
   lower bound on the safe threshold, not the safe threshold.

## 6. Reproduce

```bash
python scripts/b27/b38_sweep.py --selftest    # 6 cases, no corpus
python scripts/b27/b38_sweep.py               # needs ~/Claude/arc-artifacts/
```

Reads `<run>/artifacts/*_events.jsonl`, `type == "action"` rows, exactly as R38 §6 specifies.
