# R7 — duck-v4 postmortem: mean 1.73 vs calibration 2.16

Read-only diagnosis, no fixes applied. Compares three runs, all on the ORIGINAL duck harness
(unmodified except as noted), same 25 games, same solver config (`concurrency=28`,
`max_actions_per_game=None`, `max_runtime_s_per_game=7920.0`, confirmed by unpickling
`solver.pkl` from each run's artifacts):

| run | dir | levers | mean | median |
|---|---|---|---|---|
| **v4** | `duckv4out2` | (a) world-model field cap (6000 chars) + (b) BudgetReallocator | 1.73 | 0.04 |
| **cal** (calibration) | `duckmodcal` | none (identical code minus both patches) | 2.16 | 0.25 |
| **first** (duck-mod, 2 days earlier) | `duckmodout` | none | 2.41 | 0.08 |

Bottom line up front: **the reallocator did fire at runtime and is correctly implemented, but
its own design (`MAX_EXTENSION_PER_GAME_S == TOTAL_POOL_CAP_S == 600`) lets a single early
leveler consume the entire run's extension budget, and the one game that consumed it (ft09)
still scored worse than both baselines anyway.** The world-model cap never fired — not because
it's wired wrong, but because the field it caps never gets close to the cap under this harness's
own overwrite-not-accumulate design. Neither lever explains the bulk of the mean-score gap; three
games (ft09, vc33, tu93) that lost score under *unmodified or actively-helped* budgets account for
essentially all of it, which points at rollout variance (temperature 0.6 sampling), not the levers.

## 1. Three-way per-game table

Format per cell: `score/levels/actions/wallclock_s/tokens`. Tokens = the harness's own
`solver_note` `tokens=N` field (cumulative `total_tokens` per `_analyzer_reported_tokens`,
solver.py:80-84, 332-334). Wallclock = `final_wallclock_seconds` from `benchmark.json`. The last
column is v4's wallclock minus the flat 7920.0s baseline every game in cal/first sits at
(±1s scheduling noise) — this is the direct, measured fingerprint of the reallocator.

| game | v4 | cal | first | v4 wallclock delta |
|---|---|---|---|---|
| ar25 | 6.29/2/136/7940/70696 | 0.00/0/339/7946/65111 | 7.73/2/164/7922/64873 | +19.9 |
| bp35 | 0.06/1/439/7921/66495 | 0.00/0/44/7921/49841 | 0.28/1/230/7922/65266 | +0.7 |
| cd82 | 0.00/0/97/7921/69648 | 0.00/0/106/7920/65880 | 0.00/0/98/7922/66101 | +0.6 |
| cn04 | 0.00/0/228/6141/52189 | 0.00/0/189/7921/65343 | 0.00/0/99/7921/66465 | **-1779.3 SHRUNK** |
| dc22 | 0.00/0/94/7921/69718 | 0.00/0/51/7921/65829 | 0.00/0/73/7921/66677 | +0.8 |
| ft09 | 14.29/2/66/8545/90814 | 27.91/4/132/7921/65410 | 28.57/3/44/7922/58176 | **+625.5 EXTENDED** |
| g50t | 0.00/0/125/7920/70133 | 0.00/0/262/7920/55639 | 0.00/0/53/7923/59423 | +0.2 |
| ka59 | 1.08/1/127/7920/70505 | 0.96/1/154/7942/67236 | 0.00/0/58/7955/68132 | +0.5 |
| lf52 | 1.22/1/157/7920/69003 | 1.82/1/42/7923/67194 | 1.82/1/234/7922/65163 | +0.4 |
| lp85 | 2.78/1/40/7921/69894 | 2.78/1/69/7921/58065 | 2.78/1/59/7922/50041 | +0.6 |
| ls20 | 0.00/0/86/7920/58294 | 0.32/1/106/7920/66429 | 2.06/1/49/7922/55246 | +0.3 |
| m0r0 | 0.00/0/83/7942/71541 | 0.49/1/156/7921/65221 | 0.00/0/418/7931/64989 | +22.0 |
| r11l | 4.76/1/132/7920/69616 | 1.99/1/102/7920/66480 | 4.76/1/58/7922/65662 | +0.4 |
| re86 | 2.51/2/327/7920/68224 | 1.73/2/188/7920/54253 | 0.89/1/70/7922/58045 | +0.4 |
| s5i5 | 0.00/0/59/7920/70667 | 0.00/0/43/7950/65977 | 0.08/1/206/7922/65716 | +0.3 |
| sb26 | 2.78/1/116/7920/70072 | 2.78/1/199/7920/65071 | 2.78/1/113/7922/65058 | +0.3 |
| sc25 | 0.00/0/154/7536/66502 | 0.00/0/58/7920/66915 | 0.00/0/151/7922/66317 | **-383.5 SHRUNK** |
| sk48 | 0.00/0/189/5950/50443 | 0.00/0/131/7921/66399 | 0.00/0/174/7922/65683 | **-1969.6 SHRUNK** |
| sp80 | 4.76/1/280/7938/69811 | 0.25/1/198/7920/66229 | 4.76/1/194/7922/66742 | +17.7 |
| su15 | 2.03/1/75/7955/70089 | 2.22/1/256/7920/65605 | 2.22/1/110/7922/65553 | +35.2 |
| tn36 | 0.00/0/124/7921/68297 | 0.00/0/155/7928/58671 | 0.00/0/182/7922/66163 | +0.7 |
| tr87 | 0.00/0/206/5765/40636 | 0.00/0/351/7921/64187 | 0.00/0/240/7922/63734 | **-2155.4 SHRUNK** |
| tu93 | 0.00/0/125/7921/69954 | 4.85/2/63/7921/54939 | 1.46/2/110/7922/60576 | +0.6 |
| vc33 | 0.04/1/74/7936/70331 | 5.98/2/52/7920/66309 | 0.00/0/34/7922/40463 | +16.3 |
| wa30 | 0.69/1/328/7921/69688 | 0.00/0/412/7933/65590 | 0.00/0/260/7922/65527 | +0.6 |

Every one of 75 game-runs across all three files has `state: "gave_up"` (`benchmark.json`,
per-run field) and `final_score` computed from whatever level it reached before that. None won,
none crashed.

## 2. Which games drive the mean gap (2.16 → 1.73)

`sum(v4.score - cal.score) = -10.78` over 25 games (= -0.43/game = exactly the observed
1.73 - 2.16 headline). Sorted by delta:

**Losers:** ft09 -13.63, vc33 -5.94, tu93 -4.85, lf52 -0.59, m0r0 -0.49, ls20 -0.32 (rest ≈ 0)
**Gainers:** ar25 +6.29, sp80 +4.51, r11l +2.77, re86 +0.78, wa30 +0.69, ka59 +0.12 (rest ≈ 0)

Three games — **ft09, vc33, tu93** — account for -24.42 of raw loss, offset by +14.16 of gains
elsewhere, netting -10.78. Critically:

- **tu93** (v4: 0 levels, wallclock delta +0.6 — untouched by either lever) went from cal's
  2 levels/63 actions to 0 levels/125 actions on an *identical, unmodified* budget. Pure rollout
  variance: it took nearly twice the actions and still didn't reach cal's level 2.
- **vc33** (v4: 1 level, wallclock delta +16.3 — noise-level, not a real reallocator grant, see
  §4) went from cal's 2 levels/52 actions to 1 level/74 actions on an effectively identical
  budget. Also rollout variance.
- **ft09** (v4: 2 levels, wallclock delta **+625.5 — the one real, unambiguous extension in the
  whole run**) still underperformed both baselines, which had *less* time. See §4.

None of the three biggest losses is explained by the reallocator taking time away from that
specific game, and the one game the reallocator demonstrably gave *extra* time to is the single
biggest loss. The model at temperature 0.6 with top_p 0.95 (`taaf_setup_env.json`,
`LOCAL_ANALYZER_TEMPERATURE`/`TOP_P`) is not deterministic between runs, and these three deltas
are consistent with sampling variance dominating whatever the levers contributed.

## 3. Q1 — what actually stops a game

**Answer: wall-clock deadline only. There is no token-based stop condition anywhere in the
harness.** `_HarnessGameSession.should_stop()` (`ARC3-Inference/inference/framework/solver.py:246-261`):

```python
def should_stop(self) -> bool:
    run = self.game.game_run
    if run is None or run.state != "playing":
        return True
    if self.stop_event.is_set():
        return True
    if _is_run_complete(self.game):
        return True
    if self.runtime_limit_reached():          # <-- the only numeric deadline check
        return True
    if (self.solver.max_actions_per_game is not None
        and self.action_count >= self.solver.max_actions_per_game):
        return True
    return False
```

Four ways out: run already finished, a global cancellation event, run complete (all levels won),
or `runtime_limit_reached()` (solver.py:212-217, patched by the reallocator in v4). The fifth
guard, `max_actions_per_game`, is configured `None` in **all three runs** (confirmed by
unpickling `solver.pkl` from each output dir — see §6 for method), so it never fires.
Token totals are tracked purely for reporting: `_analyzer_reported_tokens` (solver.py:80-84)
feeds `run.solver_note = f"tokens={total_tokens}"` (solver.py:332-334) at game end, and are read
by nothing that decides whether to keep playing. `soft_time_remaining_seconds()`
(solver.py:1164-1172, driven by `solver.soft_end_time`, which *was* set — see below) only feeds
`request_timeout_seconds()` (solver.py:227-244), i.e. it clamps a single LLM call's timeout, not
the game loop's stop condition — this matches the reallocator module's own docstring claim that
"the soft-deadline graceful-drain path is dead code on TRUE_SUBMISSION."

Confirmed empirically: `should_stop()`'s deadline check is exactly what fires everywhere — every
one of 75 game-runs across all three files ends in state `gave_up` (`taaf/game.py:631`, the
generic "loop exited via `finish_game()`, not a win, not an explicit cancel" state), and 71 of
those 75 sit within ±1s of the flat `max_runtime_s_per_game = 7920.0` (confirmed identical across
v4/cal/first solver.pkl). The apparent "games gave up around ~70k tokens" pattern from the quick
read is a *correlation*, not a mechanism: token totals at game-end range 37,445–90,814 across the
three runs (a 2.4× spread) at the *same* 7920s cutoff, because different games burn tokens at
different rates per unit wall-clock (frame/segmentation size, prose verbosity, retry rate), not
because any budget enforces ~70k.

`concurrency=28` also matters for reading the reallocator's effect: with 28 ≥ 25 games, this run
had **no wave structure** — every game session ran on its own thread from t=0, contending for one
shared `asyncio.Semaphore`/`ThreadPoolExecutor` at effectively full parallelism the whole time.

## 4. Q2 — did the reallocator actually do anything at runtime

**Yes — verified two ways, both from real numbers, not source-text.**

**(a) Install actually ran.** The v4 log (`taaf-duck-v4.log`, offset 143494) prints, at t=581.7s:

```
duckv4: patched tool_agent._extract_labeled_blocks (worldmodel source 6026 chars),
patched solver._HarnessGameSession.runtime_limit_reached/timing_payload (reallocator source 14569 chars)
```

matching the char counts of the actual `duckv4/*.py` source files (minus their `__main__` demo
blocks) — this is the harness's own interpreter confirming both `install_patch()` calls executed
against the real `inference.framework.solver` / `inference.agent.tool_agent` modules, not stubs.

**(b) `final_wallclock_seconds` moved, and moved on exactly the predicted games.** Four games —
**cn04 (-1779.3s), sc25 (-383.5s), sk48 (-1969.6s), tr87 (-2155.4s)** — ended well short of the
flat 7920s, and these are *precisely* the four games satisfying the reallocator's own thrashing
predicate at some point in the run: `levels == 0 and actions >= THRASH_ACTION_FLOOR (150)`
(`duckv4_reallocator.py:128`). Every other 0-level game in v4 (cd82, dc22, g50t, ls20, m0r0, s5i5,
tn36, tu93) stayed under the 150-action floor and shows only ±1s deltas — no false positives, no
false negatives, in either direction. This is the reallocator's shrink path firing on real
sessions, not source text.

One game — **ft09 (+625.5s)** — got a real, unambiguous extension. `MAX_EXTENSION_PER_GAME_S` and
`TOTAL_POOL_CAP_S` are both `600.0` (`duckv4_reallocator.py:45-46`) — two ~300s
(`EXTEND_STEP_S`) grants land almost exactly on that per-game cap, and ft09 leveled up twice
(action 35 at wallclock 4755.6s, action 44 at 5719.6s — `benchmark.json` `actions_per_level`
boundaries), well-separated relative to the 120s tick interval, so it plausibly received one
~300s grant at each level-up tick, totalling ~600s; the residual ~25s over that is consistent with
one slow tail action overshooting the deadline check granularity (the loop only checks
`should_stop()` *between* actions — R1 already measured 19-233s/action latency on this harness,
and `analyzer_timeout=900.0`, so a single slow call can push wallclock well past the last-checked
deadline).

**All other "leveled" games in v4 got nothing (deltas +16 to +35s, indistinguishable from
scheduling noise).** This is not a measurement gap — it's structurally forced by the code, and the
timing evidence pins it down:

- Harvesting (the only source that funds the pool) requires a thrashing game to first cross
  `THRASH_ACTION_FLOOR = 150` actions. The earliest that happens in this run is **tr87 at
  wallclock 4481.4s** (150th recorded action). Before that instant, the pool is provably empty —
  nothing has been harvested yet.
- **su15** leveled at 975.3s, **sp80** at 1430.7s, **ar25**'s first level-up at 863.5s and second
  at 4115.8s — all four before 4481.4s, i.e. before any harvest could exist. Zero grant is the
  only possible outcome, and that's exactly what their ±16-35s deltas show.
- **ft09**'s two level-ups (4755.6s, 5719.6s) straddle the 4481.4s harvest-start point and land
  squarely in the window where tr87 (then sk48 at 5103.0s, then cn04 at 5453.5s) are actively
  feeding the pool — ft09 is the only leveler whose timing overlaps live harvesting.
- Because `MAX_EXTENSION_PER_GAME_S == TOTAL_POOL_CAP_S == 600`, ft09 hitting its own per-game
  ceiling **simultaneously exhausts the entire system-wide pool for the rest of the 9,128s run.**
- **vc33** leveled at 7530.8s — after ft09 had already maxed the pool (~5720s + one tick) — so
  `self._total_granted >= TOTAL_POOL_CAP_S` (`duckv4_reallocator.py:149`) blocks it categorically,
  regardless of how much the pool held. Its +16.3s delta is noise, matching.

So: the reallocator is not a no-op — it moved real wall-clock on real sessions, correctly gated by
its own thrash predicate — but its own configuration (equal per-game and system-wide caps) means
**at most one early-enough leveler benefits per run, and every other leveler gets nothing**,
independent of how deserving they are. In this run that one beneficiary (ft09) still lost 2 of its
4 cal-run levels despite the extra time (§2) — so the lever's entire measurable positive effect
this run bought nothing.

**Did shrinks hurt the shrunk games?** No evidence they did. cn04, sk48, tr87 and sc25 scored 0
in **all three runs** (v4, cal, first) regardless of budget — nothing suggests these four are
budget-limited at all; they look unsolved by this model/harness combination categorically (README
already documents cn04 needing a hand-built "claw" playbook the generic tool-calling loop doesn't
have). Additionally, three of the four shrunk games show the harvested seconds coming out of dead
time, not action-producing time: comparing each game's last-recorded-action wallclock to its
`final_wallclock_seconds`, the "tail gap" (time between the last action and game-end) is
`cn04: 163.7s, sk48: 69.7s, sc25: 115.0s` — all within the same range as these games' *own* tail
gaps in the unshrunk cal/first runs (`cn04: 122.8s/11.3s, sk48: 18.7s/103.2s, sc25: 426.4s/22.3s`)
— i.e. normal end-of-game stall, not something the shrink caused. **tr87 is the exception**: its
v4 tail gap is **1259.3s**, 4.6-8× larger than its own tail gap in cal (157.4s) or first (273.9s).
This is consistent with a feedback loop the reallocator's design creates but this artifact set
can't fully instrument: `request_timeout_seconds()` (solver.py:227-244) takes
`min(configured_timeout, remaining_deadline, soft_remaining)`, and `remaining_deadline` is read
from the *patched* `timing_payload()` — so as the reallocator shrinks a thrashing game's effective
deadline, the per-call LLM timeout shrinks with it, which can turn slow calls into
`retryable_failure`s (which sleep `ANALYZER_RETRY_BACKOFF_SECONDS = 1.0s` and loop, burning wall
clock without producing an action). This is a plausible mechanism, not a proven one — no reallocator-internal
instrumentation exists in these logs to confirm it directly for tr87 specifically.

## 5. Q3 — why the world-model cap never fired

**Both hypotheses in the brief are partially right, but the dominant cause is a third one: the
field the cap protects structurally cannot grow the way R2 assumed, because the harness overwrites
it every turn instead of accumulating it.**

Confirmed the patch **is** on the runtime path (not the "wrong function" failure mode): the same
log line from §4(a) shows `install_patch(tool_agent)` ran against the real module, and
`duckv4/verify_against_bundle.py` independently proves `_extract_labeled_blocks` is the function
`_extract_scientist_note` (tool_agent.py:263-266) actually calls, resolved by name at call time
against `tool_agent.__dict__` — same-module monkeypatch mechanics, verified against the real
bundle, not just the module's own fake test double.

But `_update_summarized_knowledge_from_assistant` (tool_agent.py:1105-1111):

```python
def _update_summarized_knowledge_from_assistant(self, content: str) -> None:
    note = _extract_scientist_note(content)
    if not note:
        return
    for key, value in note.items():
        if value:
            self._summarized_knowledge[key] = value   # <-- OVERWRITE, not append
```

**overwrites** each field (`world_model`, `goal_model`, etc.) with whatever the *current* turn's
assistant text contains — it never concatenates across turns. `_extract_labeled_blocks` itself
(tool_agent.py:226-260) also only parses the labeled section out of ONE turn's `content` string.
So the value passed through `max_chars=None` on any given call is bounded by how much prose one
LLM turn writes under one label, not by how many turns have passed — R2's "long block written once
is paid on every following turn" is about re-injection *cost* compounding across turns (the same
short-ish text gets included in every subsequent prompt), not about the *field's own size*
compounding. The 6000-char cap defends against a failure mode (a single block growing unbounded)
that this code path doesn't structurally produce.

Measured directly against v4's own transcripts, parsing every turn with the *unpatched* parsing
logic (i.e., what the cap would have seen before capping):

- Sampled per-game max single-field size across 4 games first (ft09: 381 chars, cn04: 335 chars),
  then **every field in every turn across all 25 games**: **692 extracted label blocks total,
  max 3,501 chars** (`tu93`, a `Plan:` block), **p99 = 505 chars, p50 = 99 chars. Zero fields
  exceeded 6000.**
- Widening further to raw per-turn assistant `content_chars` (the `[MODEL RESPONSE META]` field
  in each transcript, an upper bound on any one field since a field is a substring of the turn's
  content): **2,003 model-response turns across all 25 games, max content_chars = 1,184**
  (`tu93`), **77.1% of all turns wrote zero assistant prose at all** (pure tool calls, no
  `World model:`/`Plan:`/etc. narration — `_extract_scientist_note` returns `{}` immediately on
  `if not content.strip()`, tool_agent.py:264-265).

So the cap's effective ceiling (6000 chars) sits roughly **5× above the single largest block ever
written in this entire run**, and most turns don't populate the field at all. The patch is
correctly wired to the correct call site; the assumption that a field would grow large enough to
need capping doesn't hold for this harness's actual per-turn-overwrite prompt-construction design.

## 6. Method note (for reproducing solver.pkl reads)

`solver.pkl` was pickled on a Linux Kaggle worker (contains `PosixPath` objects) and needs
`scipy.stats`/`imageio.v3` importable transitively via `taaf/__init__.py` → `taaf/diagnostics.py`,
neither of which is installed in this repo's `.venv` and neither of which was needed for anything
actually read. Unpickled by stubbing both modules in `sys.modules` and temporarily aliasing
`pathlib.PosixPath = pathlib.WindowsPath` (safe here since only scalar fields — floats, ints, one
datetime — were read off the object, no path operations performed).

## 7. What v4.1/v5 must do differently

1. **The reallocator should target the constraint that's actually binding for MOST games, and
   right now that's not obviously wall-clock at all for the games that matter.** 21 of 25 games in
   this run sat within ±36s of the flat 7920s deadline regardless of lever — i.e. wall-clock is
   binding almost everywhere, confirming R1's premise. But the pool design only ever helps the
   *first* game to level up after harvesting has accumulated (a timing accident, not a
   scoring-aware choice), and starves every subsequent leveler by construction
   (`MAX_EXTENSION_PER_GAME_S == TOTAL_POOL_CAP_S`). Decouple the two caps — a per-game ceiling of
   600s should not equal the entire run's grant budget — or explicitly rank leveling games by some
   scoring-relevant signal (depth reached, weighted per the competition's own
   `level_number`-weighted scoring) instead of first-come-first-served-by-tick-timing.
2. **Re-measure whether ft09's own outcome (2 levels vs cal's 4, despite +625s) is lever-caused or
   rollout variance before trusting the reallocator's central claim.** Nothing in this dataset
   supports the lever *hurting* ft09 mechanically (it got strictly more time, never less) — the
   simplest explanation is sampling variance at temperature 0.6, and if so the reallocator's single
   real beneficiary this run is a coin flip, not a lever. A same-seed or majority-of-N rerun on
   ft09 alone, budget held fixed, would settle whether v4 vs cal's ft09 gap is signal or noise
   before attributing anything to the reallocator.
3. **The world-model cap targets the wrong quantity.** If R2's real concern is re-injection
   *cost* (a short field paid on every subsequent turn for the rest of a level), capping the
   field's *character length* doesn't address that at all — the fix for a compounding-across-turns
   cost is capping how many *turns* a field survives unchanged, or trimming the number of labels
   re-injected, not lowering a ceiling that's never approached. Before shipping any version of this
   lever again, measure the actual per-game token cost attributable to
   `_summarized_knowledge_lines()` re-injection (tool_agent.py:1128+) directly, rather than
   inferring it from field size.
4. **If the reallocator ships again, log its own ticks.** Neither `BudgetReallocator` nor
   `install_patch` prints or records anything — every finding in §4 had to be reconstructed
   indirectly from `final_wallclock_seconds` deltas and action-boundary timestamps. A one-line log
   per tick (`entry, delta, pool, total_granted`) would have turned §4's "consistent with" and
   "plausible mechanism, not proven" into direct evidence, and would let the tr87 tail-gap
   hypothesis in §4 be confirmed or ruled out in the log instead of inferred from wallclock gaps.
