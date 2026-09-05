# thui `reflect v1.1` — the paired read: the fix restores the base and the memory buys nothing measurable

**Line** thui · **family** reflect · **directory** [`thui-reflect/`](../../../thui-reflect) · **ticket** `B62` · **status** ran, closed as a build candidate

## The one change

**Two changes in the wrapper, none in the memory.**

1. `_ReflectThinkFlag` replaces the module global: `bool()` reads a **per-thread** override, else the
   harness value; the memory call sets its own thread's override and clears it in `finally`. In-kernel
   teeth: a worker thread turns itself off and reads `False` while the main thread still reads `True`,
   asserted before the benchmark.
2. A summary object is counted **once** (`st["seen_summ"]`), so an idle turn cannot re-fire on stale
   flags.

K = 10, cap 1200, timeout 90 s unchanged — the cost question is answered by a read at the real
concurrency, not by guessing a K.

## Where it lives

| what | path |
|---|---|
| builder | `thui-reflect/build_notebook.py --full --suffix=-1` |
| notebook | `thui-reflect/taaf-thui-reflect-v1-1.ipynb` |
| kernel | `yocybercode/thui-reflect-v1-1` v1 — the only push |
| fixture | `eval/fixtures/thui-reflect-v1-1.json` (mean reproduces 4.3828) |
| design + read | `notes/B62-reflection-memory-design.md` |

## What it scored

| run | public | hidden | scoring | levels | actions | act/lvl | Mtok |
|---|---|---|---|---|---|---|---|
| `thui-reflect-v1-1` | **4.38** | — | 16 | 24 | 1,546 | 64.4 | 1.99 |

Run 2026-09-04 15:14Z–17:27Z, wall 2h 12m 50s = the full per-game clock. **Inside the same-build band
`[2.82, 5.24]` and level with the `B48` pool.** **Not drawn on hidden.**

Dated reading from `notes/LEDGER-all-runs.md`, whose row for this run landed on `master` with
[#121](https://github.com/Sahasawatt/arc-agi-3-agent/pull/121).

| comparison | mean | levels | per-game | p |
|---|---|---|---|---|
| vs `thuiv3-pool` (4 runs) | 4.39 → 4.38 (Δ −0.01) | 24.25 → 24 | 9 up / 13 down / 6 flipped | **0.998 NOT-DISTINGUISHABLE** |
| vs `thui-reflect-v1` (the DEFECTIVE run, single baseline, reason printed) | 1.39 → 4.38 (Δ +3.0) | 13 → 24 | 13 up / 4 down | **0.0019 BETTER** |

## Verdict

**The whole of `v1`'s 1.39 was the global flag** — the second row above is the proof, and it is exactly
what the amendment predicted.

**The lever is delivered and affordable at 25-game width once the leak is closed**: 105 reflection calls,
**0 `call FAILED`, 0 `wrapper error`**, latency mean **29.6 s** / max 50.8 / p90 41.9 against `v1`'s
59.8 / 88.9 / ~76. All 25 games log `new memory` injections, and the four games `v1` starved finished with
real action counts — `tr87` **123**, `tn36` **19**, `ft09` **81**, `sp80` **25** (`v1`: 2 / 4 / 5 / 7).
**tok/action 1,286** is back inside the family's 1,272–1,439 (`v1`: 280), which is the mechanism control
that thinking is on again.

⚠️ **`B62`: NOT MEASURABLE at n = 1, never *no worse*.** The row's own oracle asks for ≥ 2 runs per arm.
What one run settles is that the mechanism runs at full width without `v1`'s throughput collapse, and that
a working world-model rewrite every 10 steps moved **neither levels nor score**. Closed as a build
candidate on that; re-opening needs a second run, or a rewrite that changes **what** the seven fields say
rather than how often.

⚠️ **Free reading, not a verdict**: the main analyzer logged **78** `analyzer request failed … Read timed
out` (`v1`: 20). The pool runs' own count has not been derived, so whether the memory call still costs the
analyzer timeouts is open.

## Read next

- [`thui-reflect-v1.md`](thui-reflect-v1.md) — the confounded run this one re-reads
- [`thui-reflect-v0-1.md`](thui-reflect-v0-1.md) — where the global flag was introduced, and passed a smoke
