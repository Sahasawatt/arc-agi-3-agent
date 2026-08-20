# ARC-AGI-3 v8 forensic report

## Executive conclusion

The binding constraint has changed, but it is still generation-time related:

> **v8 is constrained by excessive reasoning decode per decision, not by environment-action capacity or parser failures.**

Compared with duckmod-cal, v8 generated **2.71× more tokens/action** at the median—**1,262 versus 463**—and took **2.13× longer/action**—**127.9 versus 60.0 seconds**. Consequently, actions fell from **3,858 to 1,946**, even though completed levels rose from **19 to 22** and mean score rose from **2.16 to 3.31**. These calculations use each run’s `history[].generated_tokens`, `sum(actions_per_level)`, and `final_wallclock_seconds`; the v8 totals reconcile exactly to the run summary. ([v8 summary lines 3–14](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/summary.txt:3), [v8 benchmark](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/benchmark.json:11), [cal benchmark](/mnt/c/Users/Vampi/AppData/Local/Temp/duckmodcal/benchmark.json:11))

The model swap bought substantially better decisions: v8 achieved **22 levels with 49.6% of cal’s actions**. But it spends most generated material thinking: in six sampled transcripts, reasoning represented **90.2% of reasoning-plus-tool-payload characters**, with **1,422,859 reasoning characters versus 155,008 tool-payload characters**. Finish reasons were **264/266 tool calls and 2/266 stop**, with no recovered/malformed tool calls. That makes a **thinking-only cap** the cleanest next lever.

---

## 1. Three-way per-game comparison

Actions are `sum(actions_per_level)`. Wall clock is seconds. All rows are computed from the corresponding `game_runs[]` records; v8’s rounded score/action/token values are independently printed at [summary lines 17–41](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/summary.txt:17). Structured sources: [v8 benchmark, approximately lines 11–14,000](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/benchmark.json:11), [duckmod-1 benchmark](/mnt/c/Users/Vampi/AppData/Local/Temp/duckmodout/benchmark.json:11), [duckmod-cal benchmark](/mnt/c/Users/Vampi/AppData/Local/Temp/duckmodcal/benchmark.json:11).

| Game | v8: score; levels; actions; sec | duckmod-1 | duckmod-cal | Result |
|---|---:|---:|---:|---|
| ar25 | 2.78; 1/8; 125; 7,920 | 7.73; 2/8; 164; 7,922 | 0.00; 0/8; 339; 7,946 | Mixed |
| bp35 | 0.00; 0/9; 54; 7,921 | 0.28; 1/9; 230; 7,922 | 0.00; 0/9; 44; 7,921 | Mixed/down |
| cd82 | 4.76; 1/6; 47; 7,920 | 0.00; 0/6; 98; 7,922 | 0.00; 0/6; 106; 7,920 | **Improved** |
| cn04 | 3.27; 1/6; 44; 7,921 | 0.00; 0/6; 99; 7,921 | 0.00; 0/6; 189; 7,921 | **Improved** |
| dc22 | 0.00; 0/6; 104; 7,921 | 0.00; 0/6; 73; 7,921 | 0.00; 0/6; 51; 7,921 | Zero all three |
| ft09 | 14.29; 2/6; 58; 7,980 | 28.57; 3/6; 44; 7,922 | 27.91; 4/6; 132; 7,921 | **Regressed** |
| g50t | 0.00; 0/7; 113; 7,920 | 0.00; 0/7; 53; 7,923 | 0.00; 0/7; 262; 7,920 | Zero all three |
| ka59 | 3.57; 1/7; 55; 7,921 | 0.00; 0/7; 58; 7,955 | 0.96; 1/7; 154; 7,942 | **Improved** |
| lf52 | 1.82; 1/10; 51; 7,921 | 1.82; 1/10; 234; 7,922 | 1.82; 1/10; 42; 7,923 | Unchanged |
| lp85 | 10.07; 3/8; 160; 7,956 | 2.78; 1/8; 59; 7,922 | 2.78; 1/8; 69; 7,921 | **Improved** |
| ls20 | 3.27; 1/7; 113; 7,920 | 2.06; 1/7; 49; 7,922 | 0.32; 1/7; 106; 7,921 | **Improved** |
| m0r0 | 0.00; 0/6; 33; 7,921 | 0.00; 0/6; 418; 7,931 | 0.49; 1/6; 156; 7,922 | Mixed/down |
| r11l | 4.76; 1/6; 13; 7,921 | 4.76; 1/6; 58; 7,922 | 1.99; 1/6; 102; 7,920 | Mixed/up |
| re86 | 16.67; 3/8; 113; 7,950 | 0.89; 1/8; 70; 7,922 | 1.73; 2/8; 188; 7,920 | **Improved** |
| s5i5 | 1.64; 1/8; 83; 7,920 | 0.08; 1/8; 206; 7,922 | 0.00; 0/8; 43; 7,950 | **Improved** |
| sb26 | 0.69; 1/8; 125; 7,920 | 2.78; 1/8; 113; 7,922 | 2.78; 1/8; 199; 7,920 | **Regressed** |
| sc25 | 0.00; 0/6; 60; 7,920 | 0.00; 0/6; 151; 7,922 | 0.00; 0/6; 58; 7,920 | Zero all three |
| sk48 | 0.00; 0/8; 43; 7,921 | 0.00; 0/8; 174; 7,922 | 0.00; 0/8; 131; 7,921 | Zero all three |
| sp80 | 0.00; 0/6; 63; 7,920 | 4.76; 1/6; 194; 7,922 | 0.25; 1/6; 198; 7,920 | **Regressed** |
| su15 | 1.48; 1/9; 66; 7,920 | 2.22; 1/9; 110; 7,922 | 2.22; 1/9; 256; 7,920 | **Regressed** |
| tn36 | 0.00; 0/7; 62; 7,931 | 0.00; 0/7; 182; 7,922 | 0.00; 0/7; 155; 7,928 | Zero all three |
| tr87 | 0.00; 0/6; 71; 7,959 | 0.00; 0/6; 240; 7,922 | 0.00; 0/6; 351; 7,921 | Zero all three |
| tu93 | 2.97; 2/9; 61; 7,921 | 1.46; 2/9; 110; 7,922 | 4.85; 2/9; 63; 7,921 | Mixed |
| vc33 | 10.71; 2/7; 28; 7,921 | 0.00; 0/7; 34; 7,922 | 5.98; 2/7; 52; 7,921 | **Improved** |
| wa30 | 0.00; 0/9; 201; 7,921 | 0.00; 0/9; 260; 7,922 | 0.00; 0/9; 412; 7,933 | Zero all three |

Strictly compared with both baselines:

- **Improved over both:** 8 games — `cd82, cn04, ka59, lp85, ls20, re86, s5i5, vc33`.
- **Regressed versus both:** 4 — `ft09, sb26, sp80, su15`.
- **Mixed/tied:** 5 — `ar25, bp35, m0r0, r11l, tu93`.
- **Identical across all three:** `lf52` plus the seven persistent zeros.
- **Zero in all three:** 7 — `dc22, g50t, sc25, sk48, tn36, tr87, wa30`.

The important qualitative change is `cd82` and `cn04`: both were classified DEAD over the preceding six-run corpus, yet v8 cleared level 1. Conversely, the reliable `ft09`, `sb26`, and `su15` regressed. ([R9 classifications lines 42–68](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/results/wayfinder/R9-stability.md:42))

---

## 2. The ten v8 zero-score games

“Plenty of actions” is conservatively defined as spending at least the human baseline on level 1. Transcript failures are counted separately; a terminal HTTP timeout at the remaining-clock boundary is not classified as a crash.

Sources for score/action totals: [v8 summary lines 18–41](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/summary.txt:18). Level baselines and wall clocks: [v8 benchmark](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/benchmark.json:11).

| Game | L1 actions/base | sec/action | Transcript result | Classification |
|---|---:|---:|---|---|
| bp35 | 54/21 = 2.57× | 146.7 | 60 tool-call finishes; 1 terminal timeout; no parser flags | **(a) Reasoning failure** |
| dc22 | 104/59 = 1.76× | 76.2 | 46 tool-call finishes; 1 timeout; no parser flags | **(a) Reasoning failure** |
| g50t | 113/78 = 1.45× | 70.1 | 29 tool-call finishes; 1 timeout; no parser flags | **(a) Reasoning failure** |
| m0r0 | 33/30 = 1.10× | 240.0 | 36 tool-call finishes; 2 timeouts; no parser flags | **(a), latency-amplified** |
| sc25 | 60/36 = 1.67× | 132.0 | 56 tool-call finishes; 1 timeout; no parser flags | **(a) Reasoning failure** |
| sk48 | 43/61 = 0.70× | 184.2 | 35 tool calls, 1 stop, 1 terminal timeout; no parser flags | **(b) Throughput/latency** |
| sp80 | 63/39 = 1.62× | 125.7 | 38 tool calls, 1 stop, 2 timeouts; no parser flags | **(a) Reasoning failure** |
| tn36 | 62/32 = 1.94× | 127.9 | 44 tool calls, 5 stops; no timeout/parser flags | **(a) Reasoning failure** |
| tr87 | 71/54 = 1.31× | 112.1 | 31 tool calls, 2 timeouts; no parser flags | **(a) Reasoning failure** |
| wa30 | 201/71 = 2.83× | 39.4 | 60 tool-call finishes; 1 terminal timeout; no parser flags | **(a) Reasoning failure** |

Thus:

- **Nine of ten** zeros are primarily reasoning/discovery failures by their own action evidence.
- **One of ten**, `sk48`, is clearly clock-starved: it received only 70% of the human action baseline.
- **Zero** crashed.
- **Zero** show tool-parser recovery, markup-tool recovery, or malformed-call evidence.
- Request timeouts occurred, but mostly as the final request inherited only the small remaining game-clock allowance. Every record still ended `state="gave_up"`, not `crashed`. ([representative v8 state and wall-clock block](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/benchmark.json:508))

### Start/middle/end samples of the three worst-latency zeros

The three lowest-action/highest-latency zeros were sampled at their start, midpoint, and end rather than read wholesale:

- **`m0r0`:** 33 actions, 240.0 sec/action. Tool calls are present at the beginning around lines 147–277, remain present through approximately lines 4,273–5,338, and continue at lines 9,021–9,647. It ends in a short-remaining-clock timeout at line 9,901; it also had an earlier 900-second request timeout. No parser flags were found. ([transcript start](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/transcripts/m0r0-492f87ba_p0.txt:147), [middle](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/transcripts/m0r0-492f87ba_p0.txt:4273), [end](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/transcripts/m0r0-492f87ba_p0.txt:9021))

- **`sk48`:** 43 actions, 184.2 sec/action, below its 61-action baseline. Tool calls persist from lines 147–545 through approximately lines 4,937–6,566 and lines 9,060–9,636. The final request times out with 234 seconds remaining at line 9,897. This is the strongest true throughput zero. ([start](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/transcripts/sk48-d8078629_p0.txt:147), [middle](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/transcripts/sk48-d8078629_p0.txt:4937), [end](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/transcripts/sk48-d8078629_p0.txt:9060))

- **`bp35`:** 54 actions, 146.7 sec/action, but already 2.57× its 21-action baseline. Tool calls persist at lines 147–622, through approximately lines 4,036–5,353, and lines 12,492–13,044; it ends with a 123-second-remaining timeout at line 13,352. The middle sample shows extended hypothesis revision about wave timing and triggers rather than a parser/tool failure. ([start](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/transcripts/bp35-0a0ad940_p0.txt:147), [middle](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/transcripts/bp35-0a0ad940_p0.txt:4036), [end](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/transcripts/bp35-0a0ad940_p0.txt:12492))

---

## 3. Binding constraint now

### Aggregate comparison

Calculated from all 25 records in [v8 benchmark](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/benchmark.json:11) and [duckmod-cal benchmark](/mnt/c/Users/Vampi/AppData/Local/Temp/duckmodcal/benchmark.json:11):

| Metric | v8 | duckmod-cal | Change |
|---|---:|---:|---:|
| Mean score | 3.3099 | 2.1631 | +53.0% |
| Levels completed | 22 | 19 | +3 |
| Actions | 1,946 | 3,858 | −49.6% |
| Generated tokens | 2,115,357 | 1,557,544 | +35.8% |
| Weighted tokens/action | 1,087 | 404 | **2.69×** |
| Median per-game tokens/action | 1,262 | 463 | **2.72×** |
| Median seconds/action | 127.9 | 60.0 | **2.13×** |
| Mean per-game seconds/action | 143.8 | 81.2 | **1.77×** |

The old throughput diagnosis remains mechanically true—generated tokens/action still drives seconds/action; prior runs showed correlations of **r=0.984–0.987**. But its interpretation changes: v8’s longer thinking often yields enough quality to compensate. ([R10 lines 9–21](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/results/wayfinder/R10-throughput.md:9))

The binding constraint is therefore not “maximize actions.” It is:

> **Eliminate low-value reasoning tokens while preserving the decision-quality gain.**

### Clock cutoff and unused potential

All 25 records ended near the configured **7,920-second** clock; the total per-game wall clock was **198,186.1 seconds**, and the job duration was **2h13m**. ([summary lines 6–14](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/summary.txt:6))

Using the active uncleared level `i = levels_completed`:

- **24/25 games** had at least one action recorded on the uncleared level at cutoff.
- `cd82` was the exception: it cleared level 1 on its final recorded action and entered level 2 with zero actions.
- **13/25** were still below the human baseline on that active level.
- **12/25** had already met or exceeded the baseline and still failed to clear it.
- All **10 zero-score games** were cut on level 1, but only `sk48` was below baseline by a substantial margin.

So the clock is universally active, but only roughly half the games show plausible unused action potential. For the other half, additional undirected actions risk buying more thrashing.

---

## 4. Depth economics: closest one-more-level opportunities

The baseline is not a guaranteed solve threshold, so this is a prioritization proxy, not a claim that the missing number of actions would certainly clear the level.

I ranked games still below baseline by:

`weighted gap = (baseline − current-level actions) / active level number`

Dividing by level number favors deeper levels, where another completion contributes more to final depth. Inputs are `actions_per_level`, `base_actions_per_level`, and `levels_completed` in [v8 benchmark](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/benchmark.json:11).

| Rank | Game | Active level | Current/base | Raw gap | Weighted gap | Why it matters |
|---|---|---:|---:|---:|---:|---|
| 1 | **su15** | L2 | 39/42 | **3** | **1.50** | Closest raw gap; reliable historically |
| 2 | **lp85** | L4 | 5/16 | **11** | **2.75** | Deepest near opportunity; v8 already jumped from 1 to 3 completions |
| 3 | **cd82** | L2 | 0/8 | **8** | **4.00** | Cleared L1 for the first time, but entered L2 exactly at cutoff |
| 4 | **tu93** | L3 | 10/34 | **24** | **8.00** | Existing two-level scorer; another level has meaningful depth value |
| 5 | **vc33** | L3 | 13/44 | **31** | **10.33** | Scored 10.71 with only 28 total actions; strongest action efficiency |

The best “one more level would have paid” targets are therefore not the zero-score thrashers. They are `su15`, `lp85`, `cd82`, `tu93`, and `vc33`, especially the deeper `lp85/tu93/vc33` group.

---

## 5. Finish reasons and thinking cost

Six games were sampled to cover a slow zero (`bp35`), the slowest zero (`m0r0`), a reliable scorer (`r11l`), the best v8 scorer (`re86`), the action-efficient scorer (`vc33`), and the highest-action zero (`wa30`). Sources: their transcripts under [v8 transcripts](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/transcripts/bp35-0a0ad940_p0.txt:147) and their histories in [benchmark.json](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv8out/benchmark.json:11).

| Game | Responses | Finish reasons | Median reasoning chars | Median tool payload chars |
|---|---:|---|---:|---:|
| bp35 | 60 | 60 tool_calls | 3,944 | 634 |
| m0r0 | 36 | 36 tool_calls | 3,210 | 453 |
| r11l | 36 | 34 tool_calls, 2 stop | 5,169 | 403 |
| re86 | 49 | 49 tool_calls | 2,728 | 492 |
| vc33 | 25 | 25 tool_calls | 3,581 | 574 |
| wa30 | 60 | 60 tool_calls | 2,875 | 552 |
| **Combined** | **266** | **264 tool_calls, 2 stop** | **3,425** | **549** |

Across these responses:

- Reasoning characters: **1,422,859**
- Tool-call argument characters: **155,008**
- Ordinary assistant content characters: **63,524**
- Reasoning is **90.2%** of reasoning plus tool payload, or **86.7%** of all three serialized output components.
- Tool-call success is **264/266 = 99.25%** by finish reason.
- No sampled transcript contains `tool_calls_recovered_from_markup: yes` or `tool_call_markup_in_text: yes`.

### Generated tokens per turn caveat

The transcripts do not store exact completion-token usage beside each response. The benchmark attaches generated tokens to environment-action history entries, and batched actions create subsequent zero-token entries. Therefore an exact response-level median cannot be reconstructed honestly.

The auditable proxies are:

- Median over **all action-history entries:** **0 tokens**, because batching attributes generation to the first action and records zero on the remaining actions.
- Median over **positive token-bearing action entries** in the six-game sample: **2,091 generated tokens**.
- Mean tokens per transcript response from the six games’ total **494,040 tokens / 266 responses:** approximately **1,857 tokens/response**.

This limitation does not weaken the central finding: serialized reasoning is about **9.2×** the tool payload by character count, and almost every response still produces a valid tool call. A thinking-only budget therefore has ample room to reduce decode without truncating the payload itself.

---

## 6. Recommendation

### Single highest-expected-value change

> **Add a separate hard budget for the thinking/reasoning block—initially 768–1,024 tokens—while leaving tool-call arguments independently uncapped.**

Do not impose one shared completion cap that can cut off the tool call after a long reasoning block. The implementation should reserve payload space or terminate thinking first, then permit the model to emit the complete structured call.

The evidence line carrying this recommendation is:

> In six representative games, **90.2% of reasoning-plus-tool-payload characters were reasoning**, while **264/266 responses still ended in valid tool calls**; concurrently, v8 used **2.72× cal’s median tokens/action** and **2.13× its seconds/action**.

This is more targeted than simply disabling thinking. The v8 gain came from higher per-action quality: **22 levels in 1,946 actions versus 19 in 3,858**. The goal is to retain that regime while cutting the long tail of deliberation. Prior analysis already established that output was unbounded and that generated tokens/action explained almost all latency variation. ([R10 lines 168–169](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/results/wayfinder/R10-throughput.md:168), [R10 recommendation line 215 onward](/mnt/c/Users/Vampi/Desktop/projects/arc-agi-3-agent/results/wayfinder/R10-throughput.md:215))

### Falsifiable prediction

With the same 25 games, clock, concurrency, seed policy, and model, a 768–1,024-token thinking-only cap should produce:

> **At least 2,400 actions, at least 24 completed levels, and a public mean above 3.31, with no increase in malformed/recovered tool calls above 2%.**

If actions rise but completed levels fall below 22 or mean falls below 3.31, the extra v8 reasoning was buying essential decision quality and the cap is too tight. If tokens/action does not fall by at least 25%, the budget is not actually being applied to the hidden reasoning channel.

## Final assessment

**High confidence:** v8’s current resource bottleneck is reasoning-token generation; crashes and parser failures are not material.

**Medium confidence:** a thinking-only cap will improve score, because 13 games were below their active-level baseline and the top five depth opportunities are concentrated among existing scorers.

**Still unsettled:** how much of v8’s quality gain requires its longest reasoning turns. That is precisely what the proposed controlled cap makes measurable.