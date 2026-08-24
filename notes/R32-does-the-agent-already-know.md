# R32 — the agent already has the model R31 said was learnable, so the brake has ~nothing to brake

2026-08-24. Closes **B26**'s remaining half and prices **B29**. Offline, 0 slots, 0 submissions.
Instrument: `scripts/b27/b26_beliefs.py`, five controls gating it, all passing, exit 0.

## The answer

R31 established that the ground truth is stable: given the same level, board and action **as
the agent issues and reads it**, the harness's `board_changed` flag reproduces 98.1%. That
says a verifier *could* be built. B26's remaining half asks whether the agent already behaves
as though it had one.

**It does.** On the one bit a verifier can check — *does this action change the board here* —
the agent is already right:

| | | null | |
|---|---|---|---|
| after firing an action that did NOTHING, re-fires that same action | **39 / 384 = 10.2%** | 52.2% | **5.1× lower** |
| returning to a board whose record holds an OLDER no-op, picks it | **0 / 63 = 0.0%** | — | — |

The null is the agent's own repetition habit measured where repeating is *not* futile: after a
**mover** it fires the same action again **3,880 of 7,429 = 52.2%** of the time. So this is not
an agent that rarely repeats itself. It repeats a working action half the time and a failed one
a tenth of the time.

It also looks. `transitions` / `history` / `last_transition` are named in the **executed**
code (the `[ASSISTANT]` tool call, not drafted `[THINKING]`) on **970 of 3,591 code turns =
27.0%**, in all five runs (145 / 199 / 222 / 189 / 215). R6's Mode-2 law — *"offered tools used
ZERO times 9/9"* — was measured on the algorithmic line and does **not** carry to this harness.

## The reading that had to be thrown away

The obvious framing gives a large, wrong number. Among the 324 exact repeats, only 12.0% are
of an action recorded as a no-op, against a 55.8% uniform-pick null over each board's own
record — **−43.8 pp**, which reads as decisive evidence of a transition model.

It is an artifact, and the stratification is what shows it:

```
repeats of the action fired at the PREVIOUS decision (lag 1)   39, of which no-op  39 = 100.0%
repeats of an OLDER record entry                              285, of which no-op   0 =   0.0%
```

A perfect split, and it is **structural**: a no-op leaves the agent standing on the same board,
so a no-op can only ever be re-fired at lag 1; a mover moves it off, so a mover repeat can only
ever be an older one. The two strata are disjoint by construction and the −43.8 pp is
arithmetic, not behaviour. Only asking each stratum its own question — with its own denominator
— produces the table above.

**Consistency control**: the lag-1 population is reachable two independent ways, by
`board_ascii` equality and by the `board_changed` flag. Both give **384 opportunities and 39
re-fires**. R31 showed those two signals disagree in general (74.1% board vs 98.1% flag), so
their agreeing here is a fact about this population, not a tautology.

## What this costs B29

B29's brake — *abort when the record says this action does nothing* — is buildable (R31) and
the agent is already doing it (above). Measured on the population it would act on, across
**five complete runs**:

- it suppresses **39 actions of 7,938 decisions = 0.49%**, i.e. **7.8 per run of ~1,587**
- of those 39, the board **actually changed 6 times = 15.4%** — wrong suppressions
- keyboard only: **0 of 32 wrong**; all 6 wrong ones are clicks
- **32 of the 39 are one game (`ls20`) and 7 are another (`s5i5`)** — two games of 25

Net prize: **33 correct suppressions across five complete runs**, concentrated in two games, at
a 15% false-suppression rate on the whole population and 0% on keyboard. Set against B20's
ceiling — the efficiency axis tops out at 5.80 public (~2.29 hidden) and the completion cap
already locks 41% of the score — this is not a candidate. **B29 should be closed as
built-but-worthless, not as blocked.**

The other half of B29 was already dead: the *plan selector* fails on coverage (9.0% of
decisions come from a seen board, 91% of those know one action out of ~6), which is B19's
argument and which R31 left untouched.

## What is NOT established

- **This measures ONE BIT.** *Does this action change the board here* is the only thing a
  recorded transition can be checked against cheaply, and it is not what R29 §2 claimed was
  wrong. §2's finding — the agent's belief about what an action **does** (`lp85`: "one big
  loop" against three independent rings; `cd82`: still asking "do arrows move the piece?" at
  turn 40) — is a richer object, is untouched here, and remains the load-bearing half.
  Nothing in R32 refutes it.
- **The populations are small.** 384 lag-1 opportunities and **63** return opportunities across
  five runs. The `0 of 63` is a zero over a small set; it is not "never".
- **`noop_while_mover_known = 0` is vacuous** and is reported that way: only **1 of the 39**
  no-op repeats had more than one action in its board's record at all, so there was almost
  never a known mover available to prefer. It is kept in the output beside its cardinality
  precisely so nobody quotes it.
- **`ls20` dominates the residual** exactly as `cn04` dominates R31's. 32 of 39.
- The 10.2% and 52.2% are pooled across five runs and 25 games; neither is broken out per game.

## Controls

All five gate the run; it exits 1 before printing any new number if one fails.

1. **Reproduces R31's headline** — 324 exact `(level, board_ascii, action_display)` repeats.
2. **Reproduces R31's coverage** — 7,938 decisions, 711 from a seen board, 638 knowing exactly
   one action. So the loader and the key are R31's, and any delta is the new question.
3. **Shuffled history bites** — consulting a random *other* board's record instead of this
   one's collapses the delta to `+0.0 / +0.1 / +0.2 pp` over three seeds, against the real
   −43.8. A control that cannot fail is a constant (R31 CONTROL 4's lesson).
4. **Code-scoping present/absent pair** — `current_frame` appears in 2,598 of 3,591 executed
   code blocks and `zzqq_not_a_symbol` in 0. Without this the 27.0% could be a dead reader.
   Scoping matters: the API description for `transitions` lives in `[SYSTEM PROMPT]`, so an
   unscoped grep matches every turn.
5. **Cardinality printed for every claim**, including the two that are zeros.

## Reproduce

```bash
python3 scripts/b27/b26_beliefs.py
```

Reads `~/Claude/arc-artifacts/{v10cal,thuiv1,v18,v19,v23}` through `scripts/b27/corpus.py`,
the same loader R29 and R31 used. Zero GPU slots, zero submissions, no model calls.
