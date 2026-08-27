# R44 — B47 answered: the cap is inert, both its arms were wrong, and the live knob is the clock

**2026-08-27, offline, 0 slots, 0 GPU.** Corpus is `thui-v1-1-r2`'s `*_usage.jsonl` —
**1,306 requests / 1,070 `analyze()` calls / 588 logical steps / 25 games.**

⚠️ **It is the ONLY run that carries the probe.** All eight runs under `~/Claude/arc-artifacts/`
were checked: `thuiv1-1r2` has 25 usage files with `req_in_turn`; `clock2x`, `thuiv1`, `v10cal`,
`v18`, `v19`, `v23` and `v25seed` have **none**. Everything below is n=1 run.

## 1. Both arms of B47's discriminator are refuted

B47 offered a binary: `max(req_in_turn)` for `tr87` **== 1** means the outer loop and a
`LOCAL_ANALYZER_TOOL_STEPS` cap is inert; **== 63** means the inner loop and a cap is worth a
probe. It closed by naming its own refutation — *"it predicts `max(req_in_turn) == 1` and any
other value refutes it."*

**Measured: `tr87` is 2.** Neither arm. Corpus-wide the distribution is

| req_in_turn | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| requests | 1,070 | 186 | 40 | 9 | 1 |

deepest anywhere is **5** (`su15`). The inner loop *does* iterate — so the pure-outer-loop reading
is wrong — and it never approaches 12.

`tr87` reproduces B47's own figures exactly: 63 requests, **1** distinct action id, mean
**125.6 s**/request, only 2 of 63 under 60 s.

## 2. B47's CONCLUSION survives, now measured rather than inferred

A `TOOL_STEPS` cap of 12 cannot bind. From the fit in §4, twelve requests inside the 60 s turn
budget needs **≤5.0 s/request**; **4 of 1,306 requests (0.3%)** are that fast, and the deepest
turn ever observed is 5. The campaign's `0` has indeed been indistinguishable from the harness
default of 12 — for a reason B47 got right by a mechanism it got wrong.

## 3. The mechanism is confirmed, and more strongly than a code read could

Hypothesis from `tool_agent.py`: `turn_started_at` is set once per `analyze()` and
`LOCAL_ANALYZER_YIELD_SECONDS = 60` is checked at the **top** of every iteration, so a turn keeps
iterating while cumulative wall time is under 60 s.

| check | result |
|---|---|
| multi-request turns with `cum(all but last) < 60 s` | **186 / 186 = 100.0%**, zero violations |
| CONTROL A — single-request turns whose first request alone exceeded 60 s | **804 / 884 = 91.0%** |
| CONTROL A — median first-request wall, `n=1` vs `n>1` turns | **134.7 s vs 24.6 s** |
| CONTROL B (negative) — `cum(including last) < 60 s` | **5.9%** |

CONTROL B is what rules out *"those turns were just short"*: the bound holds on the cumulative
**before** the last request and not on the total, which is the signature of a gate at the top of
a loop. `su15`'s deepest turn reads `[17.2, 10.8, 10.2, 19.1, 244.5]` — 57.3 s accumulated, the
gate passes, and the fifth request then runs for four minutes.

## 4. The turn budget is a TOKEN budget, and the median request is 1.74× over it

Fit over 1,276 usable requests (30 have `completion_tokens = None`; see §6):

```
wall_s = -1.6 + 0.0786 * completion_tokens      R^2 = 0.9835
                                                decode ~ 12.7 tok/s
completion range 53 .. 10,174 tokens            (the spread is what makes the fit separable)
```

The intercept is **≈ 0** despite a median prompt of **22,349 tokens** — prefill is effectively
free here, which is what prefix caching looks like. So the 60 s gate is, to within the fit:

- **60 s ≈ 784 completion tokens**
- median request generates **1,368** = **1.74×** the whole turn budget
- **~73%** of all requests exceed the 60 s-equivalent

**That is why iteration 2 is rare: the model's ordinary reasoning length already spends the turn.**

## 5. What the yield loop costs

- **1.82 `analyze()` calls per logical step** (1,070 over 588), **2.22 requests per step**
- **482 of 1,070 calls = 45.0%** are beyond the first for their step
- each re-sends the prompt. At the median 22,349 prompt tokens that is roughly **10.7 M of the
  run's 27.1 M prompt tokens ≈ 40%** — ⚠️ an **ESTIMATE**: retry calls are not separable from
  first calls in the usage rows, so this multiplies a count by a median rather than summing the
  actual rows.

## 6. 🔴 The obvious next step does NOT follow, and the control says so

The tempting move is a counterfactual: raise `YIELD_SECONDS` and read off how many more turns
reach a second iteration, from each turn's own first-request time.

**Do not.** At the one value where it can be checked it over-predicts by 43%:

| | predicted by the rule | observed |
|---|---|---|
| turns reaching iteration 2 at YIELD = 60 s | 266 (24.9%) | **186 (17.4%)** |

The 80-turn gap is not the model giving up: **76 of the 80 = 95% finished `tool_calls`**, not
`stop`. They ended because the tool call **was an action, it executed, and the turn was over** —
the correct exit. A turn ends either because the clock passed 60 s **or because the agent did the
thing it is supposed to do**, and only the first is what this knob can move. Any curve built on
first-request time alone is an **upper bound** on the headroom, inflated by every turn that ended
well.

So the size of this lever is **not established**. Its mechanism is.

## 7. Cross-links

- **B40** measured 30.5% of turns ending without moving the game and attributed it to this same
  60 s budget. §3 is the same finding from the other side: 91% of single-request turns had their
  first request alone blow the budget. ⚠️ **This note's first attempt at that rate read 60.0% and
  was discarded** — it counted `analyze()` calls, and `analyze()` calls **== `analysis` rows
  exactly (1,070 == 1,070) == 1.82× the 588 distinct `(action_num, analysis_step)` pairs**, which
  is precisely the ~2× row-counting inflation B40 already retracted. Landing on B40's own
  withdrawn number is what exposed it. **Use B40's 30.5%; this corpus adds nothing to it.**
- **A second control failed and killed a different number**: the usage `action` field advances on
  only **428** of 1,070 turns against **1,260** action rows in the events, so it is the action id
  at turn *start* and one turn can emit many actions — the batch path B38 §7 warns about. No
  per-turn action rate can be derived from the usage files alone.

## 8. Not known

1. **n = 1 run.** No other run carries the probe, so none of this has a second sample.
2. **Whether moving `YIELD_SECONDS` moves score.** Unmeasured, and §6 says the cheap estimate of
   its headroom is wrong in the optimistic direction.
3. **It is a reallocation, not more clock** — unlike B34, which doubled the budget and returned
   +2 levels at `p = 0.2761`. Fewer, deeper turns inside the same per-game wall.
4. **`__exception__:ReadTimeout` on 30 requests (2.3%)**, 12,232 s of summed request time, spread
   over `wa30` 4, `cn04` 3, `lp85` 2, `m0r0` 2, `r11l` 2, `ar25` 1. Not investigated here.
5. ⚠️ **The 54.93 h of summed request time is across 25 games running concurrently** — it is not
   the run's wall clock and must never be quoted as one.

## 9. Reproduce

```bash
ls ~/Claude/arc-artifacts/thuiv1-1r2/*_usage.jsonl     # 25 files; no other run has them
```

Group rows into turns by `req_in_turn == 1` resets; `wall_s`, `completion_tokens`,
`prompt_tokens`, `finish_reason` and `action` are the fields used.
