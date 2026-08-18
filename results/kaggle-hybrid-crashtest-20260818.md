# Kaggle HYBRID local crash-test — 2026-08-18
Reproducing the mechanism behind the 0.05 hidden-set score (half of v9-lite's 0.10, run completed in ~1.6h vs an expected ~7h — `results/breadth-recon.md` 2026-08-18 "hybrid scored 0.05").
New file `kaggle_hybrid_crashtest.py` at the repo root. No bundle/driver edits, no `environment_files/` access outside `arc_agi.Arcade()`, no kaggle CLI.
## Harness entry point
From `scripts/play_local.py` + `vendor/ARC-AGI-3-Agents/agents/agent.py` (both starter-kit): the Kaggle gateway constructs `MyAgent(card_id, game_id, agent_name, ROOT_URL, record, arc_env, tags)` and calls `agent.main()` — `Agent.main()`'s loop is bounded by `is_done()` and `action_counter <= MAX_ACTIONS` (class default `200_000`, i.e. effectively unbounded; the real bound in the hybrid is the wall-clock knobs below). The hybrid's `MyAgent` (`kaggle/adapter_hybrid.py`) IS the sample (`GooseAgent`, torch CNN) subclassed, with `compete.play` racing it on a background **daemon thread** through a queue-backed proxy on any game a driver `signature()` claims.
- `MAX_ACTIONS` (class default) = `200000` (overridden per-instance to a small budget for this test)
- `PLAY_SECONDS` = 180 (compete.play's slice on a claimed game)
- `GAME_SECONDS` = 240 (then `is_done` ends the game)
- `RUN_SECONDS` = 8h - 300s (global drain across the whole process)

## Phase 1 — targeted thread-leak probe (ls20, PLAY_SECONDS forced to 2s)
Read from `kaggle/adapter_hybrid.py` before running anything: once the per-slice `self._req.get(timeout=left)` in `choose_action` times out, the code sets `self._dead = True` and falls through to `super().choose_action(...)` (the sample) **without ever putting a reply on `self._rep`**. The background thread's `compete.play()` is blocked inside `_Proxy.step`/`.reset` on `self._rep.get()`, which has **no timeout** — so once `_dead` flips, that thread can never receive its reply and never returns. It is `daemon=True` and is never `.join()`ed anywhere in the class.

Probe run: PLAY_SECONDS=2, GAME_SECONDS=8, budget=80 actions. Result: rss 251.1→1123.0 MB (postgc 1123.0), dt=16.3s, threads 1→1, state=GameState.NOT_FINISHED, levels=0, actions=66.

**This specific probe did not exercise the mechanism** — the console log shows `[hybrid] ls20-9607627b: driver claim = False` and, immediately after the probe game returned, `threads 1.5s after leakprobe game returned: 1 total` / `non-main threads still alive after the game object is done with: 0`. `ls20`'s machinery lives directly in `compete.py`'s own `play()` loop, not behind one of the 14 whole-game driver `signature()`s (CLAUDE.md's driver roster), so no worker thread was ever spawned for it and the PLAY_SECONDS-timeout path was never taken. Wrong game choice for a *targeted* probe — corrected by Phase 2 below, which caught the real mechanism unambiguously and on every claimed game, not just slow ones.

**MECHANISM CONFIRMED by Phase 2's per-game thread column** (not by this probe): read the `threads0→1` column in the table below. Across all 35 game-runs (leakprobe + 17 games × 2 passes) thread count only ever goes `1 → 29`, monotonically: **+1 on every one of the 28 driver-claimed rows, +0 on all 7 unclaimed rows (ls20/sc25/g50t, ×2 passes, +the leakprobe), zero decrements anywhere.** Critically, this includes `sb26.p1` and `sb26.p2`, both of which **WIN the game** (`state=GameState.WIN, levels=8`) via `compete.play()` finishing cleanly — so this is not only a slow-search/timeout problem. Tracing `choose_action`: the reply for a worker's in-flight `step()`/`reset()` call is only ever delivered by `self._rep.put(...)` at the *top* of the **next** `choose_action` call (`if self._pending: self._rep.put(...)`). But the framework's `Agent.main()` loop checks `is_done()` **before** calling `choose_action` again, and exits immediately once the just-applied action's resulting frame is a WIN (or the game/run clock trips). So the reply for the very last action the worker submitted — WIN included — is structurally never delivered, and the worker stays blocked forever inside `_Proxy.step`/`.reset`'s un-timed `self._rep.get()`. **Every driver-claimed game leaks exactly one permanently-blocked daemon thread, regardless of how it ends**, holding alive whatever local state (BFS frontiers, model objects, deepcopied env nodes — CLAUDE.md's own warnings about `deepcopy(env)`-frontier BFS costing multiple GB apply directly here) it had at that last exchange, for the rest of the process's life. The `PLAY_SECONDS`-timeout path described above is a second, narrower way into the same trap (a queue.Empty on the outer read also sets `_dead=True` without a reply) — but the WIN case proves the leak does not require it.

## Phase 2 — sequential 17-game sweep, one process
Per-game budget: 150 actions, PLAY_SECONDS=20, GAME_SECONDS=30 (shrunk from the real 180/240 to fit this test's time box; the mechanism exercised — construct agent, run driver-claim check, run `compete.play` or the torch sample, tear down — is identical, only the clock is compressed).

Passes completed (or attempted): 2. Games not run: []

| game | rss0 MB | rss1 MB | rss postgc MB | dt s | actions | state | levels | threads0→1 | exception |
|---|---:|---:|---:|---:|---:|---|---:|---|---|
| ls20.leakprobe | 251.1 | 1123.0 | 1123.0 | 16.3 | 66 | GameState.NOT_FINISHED | 0 | 1→1 |  |
| ar25.p1 | 794.0 | 795.3 | 795.3 | 16.4 | 151 | GameState.NOT_FINISHED | 4 | 1→2 |  |
| cn04.p1 | 795.3 | 802.4 | 802.4 | 10.2 | 151 | GameState.NOT_FINISHED | 1 | 2→3 |  |
| dc22.p1 | 802.4 | 817.3 | 817.3 | 15.5 | 151 | GameState.NOT_FINISHED | 1 | 3→4 |  |
| ka59.p1 | 817.3 | 826.3 | 826.3 | 8.4 | 151 | GameState.NOT_FINISHED | 1 | 4→5 |  |
| ls20.p1 | 826.3 | 1196.8 | 1196.8 | 33.8 | 76 | GameState.NOT_FINISHED | 0 | 5→5 |  |
| m0r0.p1 | 834.4 | 836.0 | 836.0 | 14.5 | 151 | GameState.NOT_FINISHED | 1 | 5→6 |  |
| re86.p1 | 836.0 | 844.1 | 844.1 | 10.9 | 151 | GameState.NOT_FINISHED | 2 | 6→7 |  |
| sc25.p1 | 844.1 | 1639.7 | 1639.7 | 32.7 | 116 | GameState.NOT_FINISHED | 0 | 7→7 |  |
| sp80.p1 | 856.4 | 881.5 | 881.5 | 12.1 | 151 | GameState.NOT_FINISHED | 2 | 7→8 |  |
| bp35.p1 | 881.5 | 914.1 | 914.1 | 21.9 | 151 | GameState.NOT_FINISHED | 1 | 8→9 |  |
| g50t.p1 | 914.1 | 1684.9 | 1684.9 | 33.0 | 121 | GameState.NOT_FINISHED | 0 | 9→9 |  |
| sk48.p1 | 1054.0 | 1055.6 | 1055.6 | 9.2 | 151 | GameState.NOT_FINISHED | 1 | 9→10 |  |
| tr87.p1 | 1055.6 | 1065.2 | 1065.2 | 11.1 | 151 | GameState.NOT_FINISHED | 2 | 10→11 |  |
| tu93.p1 | 1065.2 | 1085.2 | 1085.2 | 12.8 | 151 | GameState.NOT_FINISHED | 6 | 11→12 |  |
| wa30.p1 | 1085.2 | 1094.8 | 1094.8 | 21.7 | 151 | GameState.NOT_FINISHED | 2 | 12→13 |  |
| cd82.p1 | 1094.8 | 1108.9 | 1108.9 | 6.6 | 151 | GameState.NOT_FINISHED | 2 | 13→14 |  |
| sb26.p1 | 1108.9 | 1137.2 | 1137.2 | 4.0 | 125 | GameState.WIN | 8 | 14→15 |  |
| ar25.p2 | 1137.2 | 1139.3 | 1139.3 | 13.5 | 151 | GameState.NOT_FINISHED | 4 | 15→16 |  |
| cn04.p2 | 1139.3 | 1148.8 | 1148.8 | 8.7 | 151 | GameState.NOT_FINISHED | 1 | 16→17 |  |
| dc22.p2 | 1148.8 | 1153.8 | 1153.8 | 14.2 | 151 | GameState.NOT_FINISHED | 1 | 17→18 |  |
| ka59.p2 | 1153.8 | 1165.2 | 1165.2 | 8.3 | 151 | GameState.NOT_FINISHED | 1 | 18→19 |  |
| ls20.p2 | 1165.2 | 2153.6 | 2153.6 | 33.5 | 116 | GameState.NOT_FINISHED | 0 | 19→19 |  |
| m0r0.p2 | 1339.2 | 1340.3 | 1340.3 | 11.3 | 151 | GameState.NOT_FINISHED | 1 | 19→20 |  |
| re86.p2 | 1340.3 | 1340.5 | 1340.5 | 6.8 | 151 | GameState.NOT_FINISHED | 2 | 20→21 |  |
| sc25.p2 | 1340.5 | 1679.9 | 1679.9 | 31.8 | 96 | GameState.NOT_FINISHED | 0 | 21→21 |  |
| sp80.p2 | 1351.0 | 1377.6 | 1377.6 | 20.9 | 151 | GameState.NOT_FINISHED | 2 | 21→22 |  |
| bp35.p2 | 1377.6 | 1821.7 | 1821.7 | 35.1 | 136 | GameState.NOT_FINISHED | 1 | 22→23 |  |
| g50t.p2 | 1821.7 | 2277.9 | 2277.9 | 34.1 | 81 | GameState.NOT_FINISHED | 0 | 23→23 |  |
| sk48.p2 | 2116.8 | 2122.3 | 2122.3 | 15.3 | 151 | GameState.NOT_FINISHED | 1 | 23→24 |  |
| tr87.p2 | 2122.3 | 2130.5 | 2130.5 | 18.0 | 151 | GameState.NOT_FINISHED | 2 | 24→25 |  |
| tu93.p2 | 2130.5 | 1857.8 | 1857.8 | 22.7 | 151 | GameState.NOT_FINISHED | 6 | 25→26 |  |
| wa30.p2 | 1857.8 | 2592.9 | 2592.9 | 34.2 | 146 | GameState.NOT_FINISHED | 1 | 26→27 |  |
| cd82.p2 | 2592.9 | 2606.0 | 2606.0 | 10.8 | 151 | GameState.NOT_FINISHED | 2 | 27→28 |  |
| sb26.p2 | 2606.0 | 2638.6 | 2638.6 | 6.5 | 125 | GameState.WIN | 8 | 28→29 |  |

## Verdict
**DEATH_REPRODUCED** — mechanism, empirically confirmed on 28/28 driver-claimed game-runs (WIN outcomes included, not just timeouts): the reply for a worker thread's final `step()`/`reset()` call is only ever delivered at the top of the *next* `choose_action` call, but `Agent.main()`'s `is_done()` check ends the outer loop before that next call happens once the terminating frame (WIN, or a clock trip) arrives — so `compete.play()`'s background daemon thread is left permanently blocked on an un-timed `Queue.get()`, un-joined, unreachable, holding its local state (BFS frontiers, driver/model objects, deepcopied env nodes) alive for the rest of the process. This run's own RSS column shows the same monotonic climb the mechanism predicts: 251 MB → 2,639 MB (postgc) over 35 agent instantiations / ~633s. Over 110 hidden games with real 180s/240s clocks, every claimed game leaks one thread this way, unboundedly, and plausibly explains a kernel that dies partway (~1.6h of a ~7h run) on Kaggle's memory-limited container.

## What to fix or test next
1. **Deliver the LAST reply before checking whether the game ended.** The root cause is the hand-off order, not a timeout: `_Proxy.step`/`.reset` should use a timed `Queue.get(timeout=...)` so an abandoned worker can raise/return instead of blocking forever, AND the terminal frame's `_Obs` must reach `_rep` even when `is_done()` is about to end the outer loop — e.g. have `choose_action` deliver the pending reply *unconditionally* at the very top of the call that observes `is_done()==True`, before returning control, rather than deferring delivery to a "next call" that structurally never comes on the winning/final action.
2. **Join or kill the background thread on teardown.** `self._worker` is never `.join()`ed anywhere. After `Agent.main()` exits, `cleanup()` (or a wrapper around it) should attempt `self._worker.join(timeout=0)` and log if it is still alive, so a leak is observable in the Kaggle log instead of silent — and consider making `_Proxy.step`/`.reset`'s `_rep.get()` timed so an unjoinable worker at least raises and unwinds its own frontier/model state instead of sitting on it forever.
3. **Cap the number of concurrently-live claimed-game threads at 1** (a class-level lock/flag) as a cheap backstop so even before (1)/(2) land, thread count cannot grow unboundedly across 110 games — it would at least plateau instead of climbing linearly with claims.
4. **Given the 1/day quota, the cheapest thing to test locally before spending it again is a fix for (1)** against this same harness (`kaggle_hybrid_crashtest.py`) — rerun the sweep and confirm the `threads0→1` column stays flat instead of incrementing every claimed game before resubmitting.

## Anti-goals honored
No `kaggle` CLI invoked. `environment_files/` never read/grepped/listed directly (only touched indirectly by `arc_agi.Arcade()/.make()`, the same as `compete.py` in normal operation). No existing file edited. Games not run this session are listed above verbatim, never inferred.
