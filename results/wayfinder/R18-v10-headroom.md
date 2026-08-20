# v10 next-score-lever report

## Executive finding

The next lever is **not another bundle switch**. The strongest actionable defect is animation-retrieval overuse: v10 made **669 `animation()` requests**, only **582 served successfully**, including pathological loops of **405 requests in `sb26`**, **137 in `tn36`**, and **41 in `sp80`**. Two of those three games scored zero. The feature was genuinely used, but its API invites repeated frame retrieval inside Python loops without adding game actions.

**Recommendation:** add a prompt-level retrieval policy: inspect the compact animation summary first, call `animation()` once per informative animated action, and request individual frames only when the first timeline identifies an unresolved transient region. Explicitly forbid iterating blindly over frame numbers.

Falsifiable prediction: this should reduce retrieval requests by at least **75% (669 → ≤167)**, with no reduction in levels on `ft09`, `sb26`, or `sc25`, and produce at least one additional level among `tn36`, `sp80`, `sk48`, or `cd82`. If those conditions fail on a confirmation run, discard the prompt change.

Confidence: **medium**. v10 is noisy enough that the modified run must be followed by an identical-code confirmation.

---

## 1. Unused/default switches

The authoritative v10 solver object was:

> `analyzer_timeout=900`, `max_actions_per_game=None`, `max_runtime_s_per_game=7920`, `concurrency=28`, `save_request_logs=False`, `hard_noop_guard=True`, `animation_awareness=True`, `start_local_server=False`, … `local_server_count=1`, `cancel_drain_timeout_s=120`

([taaf-duck-v10.log:655](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/taaf-duck-v10.log:655)). The two experiment fields were explicitly confirmed again at [taaf-duck-v10.log:661](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/taaf-duck-v10.log:661).

### Behavior-affecting environment/config defaults

| Switch or field | v10 value | What it does | Score-positive to flip? |
|---|---:|---|---|
| `LOCAL_ANALYZER_MAX_OUTPUT` | `0` | No total completion cap; `≤0` becomes server-default/unbounded ([tool_agent.py:148](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:148), [tool_agent.py:1086](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1086)). | **Possibly, but risky.** A finite cap may increase turns but can truncate the tool call after long reasoning. Prior analysis found no separate reasoning-only cap ([R17:177](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/results/wayfinder/R17-thinking-budget.md:177)). |
| `LOCAL_ANALYZER_TOOL_STEPS` | `0` | Disables the per-turn tool-step ceiling; positive values cap tool calls ([tool_agent.py:1083](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1083)). | **Plausibly positive now.** A moderate ceiling could stop 137/405-call animation loops, but could also interrupt legitimate search. Prompt policy is safer first. |
| `LOCAL_ANALYZER_TOOL_TIMEOUT` | `30` | Caps each Python call to 30 seconds ([tool_agent.py:1084](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1084)). | Low EV. Lower risks aborting BFS; higher is clamped to 30. |
| `LOCAL_ANALYZER_TOOL_OUTPUT_TOKENS` | `1024` | Caps Python/animation output and reserves roughly four characters per token ([tool_agent.py:1089](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1089)). | Low/negative EV to increase; animation already uses compact budgets. A lower value might save context but truncate useful evidence. |
| `LOCAL_ANALYZER_YIELD_SECONDS` | `60` | Causes long generations to yield periodically; v10 status confirms `60.0` ([tool_agent.py:1085](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1085), [re86 transcript:110](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/artifacts/re86-8af5384d_p0_events.jsonl:110)). | Low/uncertain. Reducing might generate more turns but fragment reasoning. |
| `LOCAL_ANALYZER_ENABLE_THINKING` | `true` | Enables Qwen reasoning ([tool_agent.py:155](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:155)). | **Experiment-worthy but high risk.** Disabling is the only verified way to remove reasoning overhead, but quality effect is UNVERIFIED ([R17:209](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/results/wayfinder/R17-thinking-budget.md:209)). |
| `LOCAL_ANALYZER_TEMPERATURE` | `0.6` | Sampling temperature ([tool_agent.py:156](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:156)). | Low evidence. Lowering may reduce lottery variance but also exploration. |
| `LOCAL_ANALYZER_TOP_P` | `0.95` | Nucleus sampling ([tool_agent.py:157](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:157)). | Low evidence. |
| `LOCAL_ANALYZER_TOP_K` | `20` | Top-k sampling ([tool_agent.py:158](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:158)). | Low evidence. |
| `LOCAL_ANALYZER_SEED` | absent, default `-1` | Leaves generation unseeded ([tool_agent.py:159](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:159)). | Not intrinsically score-positive; setting it improves reproducibility, not expected mean. |
| `MULTIMODAL_CONTEXT` | `current_grid` | Attaches the current grid as an image ([vision_context.py:34](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/vision_context.py:34), [vision_context.py:74](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/vision_context.py:74)). | Negative to disable without evidence; keep. |
| `MULTIMODAL_UPSCALE` | `4` | Nearest-neighbor image scale ([vision_context.py:42](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/vision_context.py:42), [vision_context.py:65](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/vision_context.py:65)). | Possibly positive to increase, but vision-token/latency effects are UNVERIFIED. |
| `ARC3_HARD_NOOP_GUARD` | `true` | Blocks an exact state/level/action tuple previously observed to be a non-animated no-op ([tool_agent.py:162](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:162)). | Already on; disabling is unlikely positive. |
| `ARC3_ANIMATION_AWARENESS` | `true` | Gates metadata, retrieval, and proactive hints ([tool_agent.py:167](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:167)). | Already on. Keep, but constrain retrieval behavior. |

All v10 environment values are recorded at [taaf_setup_env.json:10](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/taaf_setup_env.json:10)–[28](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/taaf_setup_env.json:28). They match the bundled analyzer and multimodal defaults at [inference.json:55](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/configs/inference.json:55)–[80](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/configs/inference.json:80).

### Solver fields still at their defaults

These are defaults in the solver dataclass and remained unchanged in v10:

- `max_actions_per_game=None`: no per-game action ceiling.
- `save_request_logs=False`: disables separate raw request logs.
- `start_local_server=False`: Kaggle uses its separately launched vLLM.
- Empty local-server config/key/repository controls and `local_server_port=None`.
- `local_server_tensor_parallel_size=None`.
- `local_server_count=1`.
- `cancel_drain_timeout_s=120`.

Definitions: [solver.py:879](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/solver.py:879)–[926](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/framework/solver.py:926).

None is a credible direct score lever in this deployment. The relevant non-default solver changes were the 900-second analyzer timeout, 7,920-second game runtime, and concurrency 28.

---

## 2. No-op guard effectiveness

### Verified firing count

**UNVERIFIED.** There is no no-op experiment counter analogous to `animation_counters`, and no `stop_reason="known_noop"`, nonempty `blocked_actions`, transcript marker, log line, or `solver_note` count was found in the supplied v10 artifacts.

The implementation would expose a single-action firing as:

- `executed=False`
- `executed_count=0`
- `stop_reason="known_noop"`
- “blocked before execution, no action budget spent”

([tool_agent.py:1774](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1774)–[1802](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1802)). Batched firings populate `blocked_actions` ([tool_agent.py:1850](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1850)–[1895](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1895)).

No such payload was preserved. Therefore:

- Guard firings: **UNVERIFIED**
- Actions saved by the guard: **UNVERIFIED**
- Productive actions over-blocked: **no artifact evidence, but absence cannot prove zero**

The guard is structurally conservative: it keys exact level, board signature, and normalized action, and refuses to learn a no-op from any multi-frame animation ([noop_guard.py:27](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/noop_guard.py:27)–[55](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/noop_guard.py:55), [noop_guard.py:67](/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/anim-bundle/src/ARC3-Inference/inference/agent/noop_guard.py:67)). That makes systematic productive over-blocking unlikely, but not empirically measured.

### Did lower action use convert to levels?

v10 used **1,285 actions for 22 levels** ([summary.txt:9](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/summary.txt:9)–[12](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/summary.txt:12)), versus v8’s supplied totals of 1,946/1,586 actions and 22/19 levels. Attribution to the guard is not valid because animation handling and stochastic trajectories changed simultaneously.

For games positive in both v10 and each v8 run:

| Comparator | Shared scoring games | v10 actions | v8 actions | v10 levels | v8 levels |
|---|---:|---:|---:|---:|---:|
| v8-out | 11 | 605 | 945 | 17 | 18 |
| v8-cal | 11 | 698 | 797 | 14 | 17 |

Per-game evidence comes from the three benchmark files ([v10 benchmark.json:1](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/benchmark.json:1), [v8-out benchmark.json:1](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/benchmark.json:1), [v8-cal benchmark.json:1](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8cal/benchmark.json:1)).

Notable common-score comparisons:

| Game | v10 actions/levels | v8-out | v8-cal | Reading |
|---|---:|---:|---:|---|
| `ft09` | 83 / 4 | 58 / 2 | zero / 0 | More actions than v8-out, but two extra levels—the largest conversion win. |
| `sb26` | 46 / 1 | 125 / 1 | 100 / 1 | 54–63% fewer actions, same level count. |
| `ar25` | 47 / 1 | 125 / 1 | 70 / 2 | Cheaper than both, but lost one level versus v8-cal. |
| `ls20` | 67 / 1 | 113 / 1 | 142 / 1 | Clear efficiency gain without added depth. |
| `re86` | 75 / 1 | 113 / 3 | 78 / 2 | Lower actions did not convert; depth regressed. |
| `s5i5` | 54 / 2 | 83 / 1 | 64 / 1 | Fewer actions and one extra level. |
| `vc33` | 46 / 2 | 28 / 2 | 38 / 2 | Same depth at slightly higher action cost. |

Conclusion: v10’s cheap actions sometimes converted (`ft09`, `s5i5`) but often merely reduced waste. The evidence does not isolate the guard as the cause.

---

## 3. Animation feature: enabled versus actually used

### Exact adoption

Animation retrieval was genuinely used:

- **669 requests**
- **582 successfully served**
- **638 unprompted**
- **53 proactive hints**
- **31 hints followed**
- **281 per-action animation summaries reported**
- **8 reported animations whose final board was unchanged**

These totals are sums of the per-game experiment events; representative exact records include `sb26` ([events.jsonl:94](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/artifacts/sb26-7fbdac44_p0_events.jsonl:94)), `tn36` ([events.jsonl:62](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/artifacts/tn36-ef4dde99_p0_events.jsonl:62)), `sp80` ([events.jsonl:105](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/artifacts/sp80-589a99af_p0_events.jsonl:105)), and `sc25` ([events.jsonl:131](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/artifacts/sc25-635fd71a_p0_events.jsonl:131)).

Retrieval occurred in **16/25 games**. Those games completed **16 levels** and had a mean raw per-game score of **5.57**. The nine without retrieval completed six levels and averaged **2.73** ([benchmark.json:1](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/benchmark.json:1)). This is observational, not causal: animation-heavy games differ intrinsically.

The most important counterexamples to a naïve “more retrieval is better” interpretation are:

- `sb26`: 405 requests, 386 served, one level.
- `tn36`: 137 requests, 92 served, zero levels.
- `sp80`: 41 requests, 33 served, zero levels.
- `ft09`: only three requests, all served, four levels.
- `sc25`: ten requests, nine served, three levels.

Thus moderate, targeted use correlates with the standout successes more plausibly than maximal use.

### Prompts and movies

The run created:

- `prompts/`: 25 logs, approximately **2.30 MB**, each 72–100 KB.
- `movies/`: 23 HTML/MP4 pairs, 46 files, approximately **364 KB** total; `lf52` and `tr87` have no movies because they executed no actions.
- A movie HTML is a small viewer wrapper; the MP4s range roughly 3.5–16.8 KB.

The model-visible prompt explicitly advertises `animation()`, its no-action cost, timeline structure, frame crop, and historical retrieval ([ft09 prompt:50](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/prompts/ft09-0d8bbf25_p0.log:50)–[55](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/prompts/ft09-0d8bbf25_p0.log:55)). Actual retrieval is visible, for example, in `cd82` at [prompt:197](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/prompts/cd82-fb555c5d_p0.log:197), followed by a proactive hint at [prompt:324](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/prompts/cd82-fb555c5d_p0.log:324).

---

## 4. The 11 zero-score games

Every game reached approximately the same 7,920-second cutoff; therefore wallclock alone does not distinguish latency. Actions and analyzer behavior do.

| Game | Actions | Classification | Evidence/read |
|---|---:|---|---|
| `sk48` | 34 | Reasoning failure | Ample analysis, 33 animations reported, 11 retrieval requests, seven hints, still never cleared L1 ([events:79](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/artifacts/sk48-d8078629_p0_events.jsonl:79)). |
| `tn36` | 19 | Retrieval/tool-loop starvation | Only 19 game actions but 137 animation requests, of which 45 failed; five hints followed ([events:62](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/artifacts/tn36-ef4dde99_p0_events.jsonl:62)). |
| `m0r0` | 61 | Reasoning failure | Spent 2.03× the L1 baseline action count and remained on L1 ([benchmark.json:1](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/benchmark.json:1)). |
| `cn04` | 29 | Reasoning failure | Exactly matched the 29-action L1 baseline but found no solution. |
| `dc22` | 85 | Reasoning failure | Used 1.44× L1 baseline; transcript repeatedly reconsiders the movement boundary rather than closing the hypothesis ([prompt:554](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/prompts/dc22-fdcac232_p0.log:554)–[676](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/prompts/dc22-fdcac232_p0.log:676)). |
| `ka59` | 23 | Reasoning failure | Near baseline, repeatedly revises whether the box/frame blocks movement ([prompt:197](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/prompts/ka59-38d34dbb_p0.log:197)–[242](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/prompts/ka59-38d34dbb_p0.log:242)). |
| `lf52` | 0 | Latency/tool-loop starvation | 72 analyzer cycles but zero environment actions; the summary records zero actions and zero generated tokens despite a full slot ([summary.txt:25](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/summary.txt:25)). Exact token-accounting discrepancy is **UNVERIFIED**. |
| `sp80` | 67 | Retrieval-assisted reasoning failure | 1.72× L1 baseline plus 41 animation requests, but no level ([events:105](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/artifacts/sp80-589a99af_p0_events.jsonl:105)). |
| `cd82` | 41 | Reasoning failure | Eight informative animations, 11 served retrievals, six hints; still zero. Animation information was available and consumed, but not converted ([events:84](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/artifacts/cd82-fb555c5d_p0_events.jsonl:84)). |
| `tr87` | 0 | Latency/tool-loop starvation | 55 analyzer cycles but zero environment actions; summary likewise reports zero actions/tokens ([summary.txt:38](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/summary.txt:38)). |
| `g50t` | 25 | Retrieval/tool-loop reasoning failure | 22 animation reports, four served retrievals and three hints, but little action throughput and no L1 ([events:53](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/artifacts/g50t-5849a774_p0_events.jsonl:53)). |

### Three worst transcript samples

1. **`lf52`** — worst because 72 analysis cycles yielded zero actions. Late responses still contain 4,121 reasoning characters and inspection-only Python calls around [transcript:17512](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/transcripts/lf52-271a04aa_p0.txt:17512). This is agent indecision/tool-loop starvation, not environment-action scarcity.

2. **`tr87`** — similarly, late responses contain 4,341 reasoning characters and another Python inspection call around [transcript:14048](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/transcripts/tr87-cd924810_p0.txt:14048), yet no environment action was ever executed.

3. **`tn36`** — a single late response reached **29,311 reasoning characters** before another tool call ([transcript:11190](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/transcripts/tn36-ef4dde99_p0.txt:11190)); its 137 animation requests confirm that the tool was being exercised heavily without game progress.

### Guard over-blocking

No zero-score game contains a verified `known_noop` refusal or nonempty `blocked_actions` payload. Therefore none can be classified as guard over-blocking from the artifacts. Exact absence of over-blocking remains **UNVERIFIED** because the run has no guard counter.

---

## 5. One-more-level ranking

Method: for each game, compare actions spent on its current unfinished level with that level’s baseline. “Closeness” is `spent / baseline`; weighting multiplies this by the target level number, because the request asks to favor deeper levels. This is a prioritization heuristic, not a probability of completion.

| Rank | Game | Target level | Current-level actions | Baseline | Ratio | Depth-weighted ratio |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `ft09` | 5 | 36 | 65 | 0.554 | **2.769** |
| 2 | `sb26` | 2 | 35 | 28 | 1.250 | **2.500** |
| 3 | `m0r0` | 1 | 61 | 30 | 2.033 | **2.033** |
| 4 | `wa30` | 2 | 118 | 119 | 0.992 | **1.983** |
| 5 | `vc33` | 3 | 28 | 44 | 0.636 | **1.909** |

All action and baseline vectors are in [benchmark.json:1](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/benchmark.json:1).

The most attractive real target is `ft09`: it was already the run’s four-level breakout and was 36 actions into level 5. `sb26` and `wa30` were around or beyond their baselines without clearing, suggesting reasoning quality—not raw action allowance—was the limiting factor. `vc33` is the other high-value depth target.

---

## 6. Ranked next moves

1. **Prompt-level animation retrieval discipline — recommended.**  
   Evidence line: `tn36=137`, `sb26=405`, `sp80=41` retrievals versus `ft09=3` and `sc25=10` ([tn36 event:62](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/artifacts/tn36-ef4dde99_p0_events.jsonl:62), [sb26 event:94](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/artifacts/sb26-7fbdac44_p0_events.jsonl:94), [ft09 event:112](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/artifacts/ft09-0d8bbf25_p0_events.jsonl:112)).  
   Prediction: ≤167 total retrievals, no depth loss on the three strong animation games, and ≥1 new level among the four named zero games.

2. **Confirmation rerun of unmodified v10.**  
   High value because identical-code action ratios have historically ranged widely and large score swings often fail to track action counts ([R9:189](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/results/wayfinder/R9-stability.md:189)–[220](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/results/wayfinder/R9-stability.md:220)). If only one more expensive run is affordable, confirmation is defensible; it estimates whether 4.55 is a repeatable frontier or a lottery peak.

3. **Per-game time reallocation.**  
   Target `ft09`, `vc33`, and `wa30`; reclaim time from `lf52`, `tr87`, and pathological retrieval loops. However, all games already received the same 7,920 seconds and cheap actions did not consistently convert into depth. A scheduler change is larger and less isolated than the prompt experiment.

4. **Flip an unused switch.**  
   Best candidate is a moderate `LOCAL_ANALYZER_TOOL_STEPS` cap; second is thinking-off. Both are blunter than correcting the observed retrieval misuse. A total-output cap remains especially risky because reasoning and tool-call serialization share one budget.

5. **Do nothing beyond confirmation.**  
   Reasonable only if the goal is leaderboard confidence rather than development. v10’s 4.55 rests heavily on `ft09=47.62` and `sc25=22.34` ([summary.txt:22](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/summary.txt:22), [summary.txt:33](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv10out/summary.txt:33)); both historical evidence and v8 contrasts indicate substantial per-game lottery variance.

## Working answer

**Highest-EV change:** preserve animation awareness and the no-op guard, but constrain animation retrieval at the prompt level before touching global generation controls.

**Settled:** animation retrieval was heavily used; no-op savings were not instrumented; most zeros are reasoning/tool-loop failures rather than action-budget exhaustion.

**Still UNVERIFIED:** exact guard firings, exact guard-saved actions, whether v10’s 4.55 repeats, and whether the proposed retrieval policy increases public score rather than merely reducing wasted tool work.