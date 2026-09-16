# B75 — a per-turn completion cap on the fast base (`thui-cap`)

Opened 2026-09-09 from the B72 census and the B74 read. Builder `thui-cap/build_notebook.py` (`--control` = same games, no cap).

## The claim this build tests

On the fast base three games spend 270–320 s and 3–4 k generated tokens per action (bp35 d1, r11l d2, lp85 d1 — 25–30 actions in
a 7,920 s game), and the deep-tail games that reached their last level with < 2,000 s of wall left (tr87 L5, lp85 L6, sc25 L4) had
spent the wall on the levels before it. The June solver sends **no `max_tokens`**: `tool_agent.py:137` reads
`LOCAL_ANALYZER_MAX_OUTPUT` (default 0 → "server default"), Keith's `serving_setup.py` persists that key as `"0"`, thinking is on,
so a single turn may run to the 32 k context. V2's per-turn output (1,331 turns, reasoning + content chars): p50 2,415 / p90 8,929 /
p95 11,905 / max 32,473 (~3.5 chars per token → p90 ≈ 2.5 k tok, p95 ≈ 3.4 k); `finish_reason: length` 5 times.

Hypothesis: capping a turn's completion at **3,072 tokens** (~p93) shortens the tail turns without eating tool calls, and the seconds
saved land as actions and, on the time-bound tail, as levels. What it costs if wrong: turns cut mid-reasoning end `finish_reason:
length` with no tool call — a dead turn.

Also found in the persisted env: `LOCAL_ANALYZER_TOOL_STEPS=0` — Keith's setup leaves the per-turn tool loop **unbounded** (the
solver default is 12). Part of a 300 s turn is the python search loop, not generation; that knob is a separate ticket (B59's territory).

## What differs from `thui-fast-v0` (asserted by the builder)

| cell | B69 | B75 |
|---|---|---|
| 5 / 15 | nested mount hardcoded | mount resolved (B71's resolver) |
| 9 | — | after his `serving_setup.py` persists the analyzer env and before the first `inference` import: assert the persisted key is `"0"`, set `LOCAL_ANALYZER_MAX_OUTPUT=3072` (persisted + `os.environ`); teeth: `_tool_agent._LOCAL_ANALYZER_MAX_OUTPUT == 3072`, thinking still on; marker `THUI_CAP ok`. `--control`: nothing set, teeth assert 0 |
| 15 (smoke) | — | bp35 / r11l / lp85 at 1,800 s |

## Pre-registered read (smoke, written before the push; amended before any result)

1. **Cap landed** — `THUI_CAP ok max_output=3072` and every turn's META reads `max_output_tokens: 3072`.
2. **Cost side** — turns ending `finish_reason: length` ≤ 15 % per game (V2: 5 of 1,331 overall).
3. **Levels** ≥ V2's at 1,800 s on each game (V2 @1,800 s: bp35 0, r11l 1, lp85 1).
4. **Throughput** — *amended 2026-09-09 02:10, before the first result*: V2's first-1,800 s action counts (bp35 25, r11l 12, lp85 17)
   are 25-way and cannot price a 3-way smoke (the B76 smoke did 806 actions on games whose V2 first 1,800 s held 71). Actions are
   read only against the matched no-cap control `thui-cap-ctl` (same games, same clock, same concurrency): PASS = actions ≥ 1.5×
   the control with levels ≥ the control's; FAIL = actions up, levels down (the thinking was buying the level) or actions not up.
5. Wall ~40 min per smoke; 0 slots.

## Smoke record (sahasawatt/thui-cap-v0 v2, 2026-09-08 19:19–19:59Z, wall 2,400 s) — items 1–3 PASS, item 4 pending the control

v1 of the slug died at 608 s on the builder's own teeth (`assert "LOCAL_ANALYZER_MAX_OUTPUT" not in _persisted`): his setup persists
the key with value `"0"`; the assert now checks the value. v2 = the corrected build, competition mount NESTED.

1. **Cap landed** — `THUI_CAP ok max_output=3072 thinking=True yield=60.0 seed=-1`; 387 of 387 turns carry `max_output_tokens: 3072`.
2. **Cost** — `length` stops: bp35 10 / 111 turns (9 %), lp85 5 / 138 (3.6 %), r11l 2 / 138 (1.4 %) — all under 15 %. Output per turn
   p50 858–1,756 chars, p95 6.5–8.7 k, max 9.4 k (the cap bites at ~10.7 k chars).
3. **Levels** — bp35 **1** (L1 at 630 s; V2 0 by 1,800 s, 1 at 2,709 s), r11l 1 (L1 at 133 s; V2 1 at 1,534 s), lp85 **3** (97 / 671 /
   923 s; V2 1 by 1,800 s, L3 at 3,217 s). All ≥ V2, two ahead of V2's own timeline.
4. **Throughput** — 673 actions (bp35 112, r11l 138, lp85 423), 111–138 turns per game in 1,800 s. Against the control: pending
   (`thui-cap-ctl` queued 20:00Z).

Not yet a verdict: items 1–3 say the cap is cheap and nothing broke; item 4 decides whether it buys time. The level timings (bp35
L1 at 630 s vs 2,709 s; lp85 L3 at 923 s vs 3,217 s) are suggestive but confounded by 3-way concurrency until the control lands.

## Control record (sahasawatt/thui-cap-ctl v1, 2026-09-08 20:40–21:25Z, no cap, same games / clock / 3-way) — item 4 FAIL, B75 CLOSED

`THUI_CAP ok max_output=0`, every turn `max_output_tokens: server default`, mount NESTED. Per game, cap → control:

| game | levels (tclear) cap | levels (tclear) control | actions cap / ctl | turns cap / ctl | `length` stops cap / ctl | chars p50 / p95 / max cap | control |
|---|---|---|---|---|---|---|---|
| bp35 | 1 (630 s) | 1 (377 s) | 112 / 270 | 111 / 114 | 10 / 0 | 1,756 / 8,660 / 9,395 | 896 / 7,549 / 17,756 |
| r11l | 1 (133 s) | 1 (184 s) | 138 / 321 | 138 / 227 | 2 / 0 | 1,368 / 6,512 / 8,944 | 930 / 2,966 / 9,345 |
| lp85 | 3 (97 / 671 / 923 s) | **5** (97 / 299 / 422 / 751 / 993 s) | 423 / 126 | 138 / 77 | 5 / 0 | 858 / 6,532 / 8,923 | 2,982 / 11,293 / 15,552 |
| total | 5 | **7** | 673 / 717 | | 17 / 0 | | |

- **Throughput** — actions 673 vs 717 (ratio 0.94, bar ≥ 1.5): not up. bp35 / r11l did 2.4× MORE actions without the cap.
- **Levels** — 5 vs 7: the control cleared lp85 L4 and L5 inside 1,800 s where the capped run stopped at L3 with 423 actions —
  the shape the pre-registration named as FAIL ("the thinking was buying the level"). Its uncapped lp85 turns ran p95 11.3 k /
  max 15.6 k chars: those long turns were the ones that solved the level.
- **Cost** — the cap produced 17 `length` stops (dead turns) against 0.

Reading: the cap **does not** convert generation seconds into actions on this serving — turns are not generation-bound at
3-way (the control's r11l turned 227 times in 1,800 s, 8 s a turn), and where a turn is long it is doing the work. The 270–320 s
per action seen in V2 at 25-way is queueing on a saturated server plus the unbounded python tool loop (`LOCAL_ANALYZER_TOOL_STEPS=0`
in his env), not completion length. n = 1 per arm at 3-way, so the level counts carry the smoke's own variance (bp35's action
count differs 2.4× between two runs of the same mechanic); the throughput and dead-turn reads do not depend on it.

Verdict: **B75 closed — negative.** No full build. What survives: the persisted env now documented (`LOCAL_ANALYZER_MAX_OUTPUT=0`,
`LOCAL_ANALYZER_TOOL_STEPS=0`, yield 60, seed −1 on his base) and the `--control` pattern for any 3-way smoke — a smoke's actions
are only readable against a smoke.
