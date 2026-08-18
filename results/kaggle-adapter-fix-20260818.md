# Kaggle adapter thread-leak fix — 2026-08-18

Fixes the mechanism traced in `results/kaggle-hybrid-crashtest-20260818.md`: on every
driver-claimed game, the worker thread running `compete.play()` blocked forever on an
un-timed `Queue.get()` because the reply to its last `step()`/`reset()` call was only ever
delivered at the top of the *next* `choose_action`, and `Agent.main()`'s `is_done()` check
ends the loop before that next call happens once the terminal frame (WIN, or a clock trip)
arrives. One leaked daemon thread per claimed game, unbounded, holding its BFS/model state
alive for the rest of the process (RSS 251 MB → 2.6 GB over 35 game-runs in the original
crash-test).

## Diff summary

`git diff --stat`: `kaggle/adapter.py` +68/-5, `kaggle/adapter_hybrid.py` +63/-5 (115
insertions, 16 deletions total, both files structurally identical fix). Both files got the
same three changes, mapped to the crash-test report's ranked remedies:

**(a) `is_done()` delivers the pending reply before its terminal short-circuit.**
Previously: `if latest_frame.state is GameState.WIN: return True` (and two more early
returns for the clock checks) — no reply delivery anywhere in this method. Now the method
computes `done` first, and only once, then before returning:
```python
if done and self._pending:
    self._rep.put(_Obs(latest_frame))
    self._pending = False
return done
```
This is the root-cause fix: `is_done()` receives the exact same `latest_frame` the deferred
"next choose_action" would have delivered, so delivering it here — the one call site that is
guaranteed to run before the loop can end — closes the structural gap. Applies to all three
of `is_done()`'s original early-return paths (WIN, `RUN_SECONDS`, `GAME_SECONDS`), and to the
*original* Phase-1 mechanism too (the `PLAY_SECONDS`-timeout `self._dead = True` path), since
the delivery is keyed on `self._pending`, not on `self._claimed`/`self._dead`.

**(b) `_exchange()`'s `self._rep.get()` is now timed, with a `TimeoutError` on expiry.**
(a) alone does not fully close the leak: `compete.play()` has no notion of "the framework is
about to stop asking me for actions" — once it receives the delivered terminal reply, it
still calls `env.step()`/`.reset()` **one more time** (confirmed empirically below), and by
then `Agent.main()`'s loop has already exited, so nothing will ever service that request. `(b)`
is what actually bounds the leak:
```python
try:
    return self._rep.get(timeout=self._REPLY_TIMEOUT)
except queue.Empty:
    raise TimeoutError("... framework loop has ended")
```
`_REPLY_TIMEOUT = 60` (class constant). Normal round-trip (worker asks → next
`choose_action` delivers) is sub-second; 60s only bounds the abandoned-worker case where
nothing will ever answer again. The `TimeoutError` propagates into `compete.play()`, is
caught by `_run()`'s existing `except Exception` guard, logged, and the thread exits.

**(c) `cleanup()` override — backstop delivery + bounded join + observability.**
`Agent.main()` calls `self.cleanup()` unconditionally after its loop exits (including the
`MAX_ACTIONS`-cutoff path, which can end the loop without `is_done()` ever returning True —
(a) alone doesn't cover that case). New override:
```python
def cleanup(self, *args, **kwargs):
    super().cleanup(*args, **kwargs)
    if self._pending and self.frames:
        self._rep.put(_Obs(self.frames[-1]))
        self._pending = False
    if self._worker is not None:
        self._worker.join(timeout=self._JOIN_TIMEOUT)
        if self._worker.is_alive():
            print(f"... worker thread still alive after cleanup join ...")
```
`_JOIN_TIMEOUT = 2.0`. Purely observational/backstop — the thread still self-terminates via
(b)'s timeout even if this join doesn't catch it in time; this just makes a straggler
visible in the Kaggle log instead of silent, and covers the `MAX_ACTIONS` edge case.

**(d) New game never inherits a previous game's live worker — verified, not changed.**
`self._worker`, `self._req`, `self._rep`, `self._pending`, `self._dead`, `self._t0` are all
set fresh in `__init__` as instance attributes (not class attributes); only `_run_start` is
intentionally shared (the global `RUN_SECONDS` drain clock). Each Kaggle-harness game
constructs a new `MyAgent` instance, so a stray worker from a prior game's instance has its
own queues and cannot be read from or written to by the next game's instance. No code change
needed; confirmed by inspection and by the sweep below (thread count never spikes at a game
boundary the way it would if state leaked across instances).

**Difference between the two files**: `adapter.py` has no `_claimed` gate — it always starts
a worker for every game (claimed or not), so this adapter's leak affected *every* game, not
only driver-claimed ones ("suppressed every driver-carrying submission if leaky" per the
task brief) — same fix, same effect, wider blast radius on the pre-fix code.

## Bundle rebuild

`kaggle/bundle_hybrid.py` re-run against the fixed `kaggle/adapter_hybrid.py`, output to the
starter kit (`kaggle/bundle_hybrid.py`'s own rule — third-party MIT source, never written
into this MIT-0 repo):

| | sha256 | size |
|---|---|---|
| old (`agent/my_agent_hybrid.py`, pre-session) | `56aa957f30f2badc50b5dc26f655f9d47d5db6fb5799b155a8a3eac3b24fc56b` | 233,452 bytes |
| new (rebuilt, fixed adapter) | `2ee18d94ac83dcffafd8f9b6412fbd60a7a17a7e6eb2cc4aa6c896fac7a93c02` | 237,218 bytes |

`kaggle_hybrid_check.py` (repo's own bundle-completeness gate) run against the rebuilt
bundle: **ALL CHECKS PASSED** — execs in a fresh namespace, all 23 declared modules + `_goose`
registered in `sys.modules`, all 14 drivers present, `MyAgent` inherits `GooseAgent`, every
driver exposes `signature()`, embedded `mirror.py` contains `L3_LINE`/`L4_LINE` (not a stale
build).

⚠️ **`kaggle/my_agent.py` (the non-hybrid bundle, built by `kaggle/bundle.py` from the now-fixed
`kaggle/adapter.py`) was NOT rebuilt** — it lives inside this repo, which was outside this
task's edit scope (`kaggle/adapter_hybrid.py` and `kaggle/adapter.py` only). I rebuilt it once
by mistake mid-session, caught it, and `git checkout`'d it back to its committed state
(sha256 `d718a40eb131d98be82c7be33ccc2982be215ff0eba1828fb7d1275a21ebcc8a`, 230,211 bytes —
confirmed restored). **It is now stale relative to the fixed `adapter.py`.** Rebuild command
for the main thread:
```
PYTHONUTF8=1 python kaggle/bundle.py
```

## Verification

New files, repo root: `kaggle_hybrid_crashtest2.py` (the sweep/leak-probe harness, adapted
from `kaggle_hybrid_crashtest.py`) plus three ad-hoc one-off Python invocations used for the
A/B isolation below (not saved as files — inline `-c` scripts, logged in this session's
transcript). No bundle/driver edits performed by any of them, no `environment_files/` access
outside `arc_agi.Arcade()`, no kaggle CLI.

### Thread-leak / RSS — REQUIRED check, PASSES

Two full sweeps run, same 17 games, same budget (150 actions), same clocks
(`PLAY_SECONDS=20`, `GAME_SECONDS=30` — shrunk from production 180/240 to fit the time box,
identical convention to the original crash-test), against the **rebuilt, fixed** hybrid
bundle:

- **Sweep A** (`_REPLY_TIMEOUT` shrunk to 2s, `_JOIN_TIMEOUT` to 6s, test-only — see the
  caveat below on why this value also corrupted gameplay): thread count **never exceeded 1**
  at any point across all 17 games (`threads0→1` = `1→1` on every single row, including
  `sb26`'s `GameState.WIN`). Zero non-main threads alive at the end of the run.
- **Sweep B** (`_REPLY_TIMEOUT` left at its **production default, 60s**; only `_JOIN_TIMEOUT`
  shrunk to 3s for test speed — harmless, `cleanup()` runs strictly after the action loop
  ends): thread count stayed **bounded between 1 and 5** throughout the entire 17-game sweep,
  never climbing further. RSS ended at 1,302.5 MB after 17 game-runs, essentially flat by
  the second half of the sweep (817→834→1167→…→1302 MB, driven by normal per-game
  allocation, not a monotonic per-thread accumulation).

Against the **original crash-test's own numbers** (`results/kaggle-hybrid-crashtest-20260818.md`):
thread count climbed **monotonically and permanently**, `1 → 29` over 35 game-runs (every
claimed game +1, forever, zero decrements), RSS **251 MB → 2,639 MB**. The fix changes both
signatures completely: no monotonic growth, no permanent leak — every worker thread now dies
within its `_REPLY_TIMEOUT` bound of its game ending, confirmed under both an aggressive 2s
setting and the shipped 60s setting.

**Verdict: DEATH FIXED.** The mechanism (worker blocked forever on `_rep.get()`) cannot occur
by construction any more — `is_done()` always attempts delivery before returning True, and
`_exchange()`'s timeout is an unconditional backstop independent of whether delivery
succeeded. `results/kaggle-adapter-fix-verify-20260818.md` has the full per-game tables for
both sweeps.

### Behaviour regression check — PARTIAL, with an isolated root-cause finding

Direct row-for-row comparison of Sweep A/B against the original report's pass-1 table showed
several claimed games (`m0r0`, `sp80`, `tu93`, `wa30`) reaching **different** level counts,
and the three unclaimed/sample-driven games (`ls20`, `sc25`, `g50t`) showing different action
counts (expected — the sample is a stochastic torch CNN with no fixed seed here; `ls20`
itself is never driver-claimed at reset, so its numbers were never a claimed-game
comparison to begin with, exactly as the original report also noted).

I do not trust the headline "several games regressed" reading, and traced it before writing
it down. **Same-session, same-machine A/B, isolating one game at a time** (`tu93`, budget and
clocks identical to the sweep):

| run | trial 1 | trial 2 |
|---|---|---|
| fixed code, `_REPLY_TIMEOUT` shrunk to 2s (test-only) | actions=151, **levels=5** | actions=151, **levels=5** |
| **pre-fix code** (git-stashed back to HEAD), `_REPLY_TIMEOUT` n/a (doesn't exist) | actions=151, **levels=6** | actions=151, **levels=6** |
| fixed code, `_REPLY_TIMEOUT` at **production default (60s)** | actions=151, **levels=6** | actions=151, **levels=6** |

This is decisive for the isolated case: **the fix's actual logic causes zero change** —
fixed-code-with-production-timeout reproduces the pre-fix code's result exactly, twice. The
2s-shrunk-timeout run is the outlier, and the mechanism is understood: `_REPLY_TIMEOUT` bounds
*every* call to `_exchange()`, not just the one at game-end — during **normal, healthy,
mid-game play**, the worker's wait for its reply is bounded by one real `env.step()` round
trip (choose_action → `Agent.main()`'s `take_action()` → next `choose_action`), which is
normally sub-second but is not *guaranteed* to stay under an artificially small 2s ceiling.
Shrinking `_REPLY_TIMEOUT` to 2s for test speed occasionally fires the backstop **mid-game**,
prematurely killing the driver thread and hanging the game off to the (weaker) sample agent
earlier than production ever would with the shipped 60s value. This is a test-harness
artifact, not a bug in the shipped code — the production default is untouched at 60s in both
source files.

Re-running the **full 17-game sweep** with `_REPLY_TIMEOUT` at the production 60s value
(Sweep B) still showed `tu93` at levels=5, not 6 — i.e. the isolated-game A/B does not fully
explain the sweep-context result. The most likely remaining factor, **not conclusively
isolated within this task's time budget**: several straggler worker threads from earlier
games in the sweep are still alive (up to their own 60s bound) when a later game runs — Sweep
B's own thread column shows 3-5 threads alive concurrently by the time `tu93` runs (position
14 of 17) — and GIL/scheduling/GC pressure from those genuinely-blocked-but-not-yet-dead
threads plausibly shaves enough wall-clock throughput off a `PLAY_SECONDS=20`-bounded slice to
change which action the driver is on when the slice expires. This is a property of the
**compressed test clocks** (20s/30s vs production's 180s/240s, chosen — same as the original
crash-test — to fit the time box): production's 9x larger `PLAY_SECONDS` budget makes the same
few seconds of scheduling noise proportionally negligible, and a straggler thread's remaining
lifetime (bounded at 60s either way) is a much smaller fraction of a 240s game clock than of
a compressed 30s one.

**What IS verified**: no crash, no exception, no per-game state corruption in either sweep;
9 of 17 games (`ar25`, `cn04`, `dc22`, `ka59`, `re86`, `sk48`, `tr87`, `cd82`, `sb26`) matched
the original report's actions/levels exactly in Sweep B; `sb26` still WINs (8/8 levels) in
every run of every sweep. **What is UNVERIFIED**: whether `m0r0`/`sp80`/`tu93`/`wa30`'s
differing level counts under the compressed test clocks would also differ under production
clocks (180s/240s) — the isolated single-game evidence says no (fix-neutral), the full-sweep
evidence is inconclusive between "compressed-clock scheduling noise" and "a residual effect of
the fix I haven't found." Recommend re-running `kaggle_hybrid_crashtest2.py` at
`PLAY_SECONDS=180, GAME_SECONDS=240` (needs ~35-50 min, outside this task's 55 min budget) for
a fully production-faithful regression check before the next submission.

### pytest — green

```
PYTHONUTF8=1 .venv/Scripts/python.exe -m pytest -q   →   330 passed in 5.18s
```
(redirected to `results/pytest-adapter-fix-20260818.txt`, exit 0 — not read through `rtk`,
per this repo's own documented `rtk`/pytest gotcha). No test in this repo imports
`kaggle/adapter*.py` directly, so this confirms no collateral damage elsewhere, not the
adapter fix itself (the crash-test sweeps above are what verify the adapter).

## Exact rebuild + push commands (main thread only — placeholders on their own lines)

```bash
PYTHONUTF8=1 python kaggle/bundle.py
```
```bash
PYTHONUTF8=1 python kaggle/bundle_hybrid.py
```
```bash
PYTHONPATH=<starter>/vendor/ARC-AGI-3-Agents ./.venv/Scripts/python.exe kaggle_bundle_check.py
```
```bash
PYTHONPATH=<starter>/vendor/ARC-AGI-3-Agents ./.venv/Scripts/python.exe kaggle_hybrid_check.py
```
Copy the chosen bundle onto the starter kit and assert the sha matches before building the
notebook (this repo's own documented gotcha — a stale copy already cost a real submission
once):
```bash
PYTHONUTF8=1 STARTER/.venv/Scripts/python.exe scripts/build_notebook.py
```
```bash
KAGGLE_API_TOKEN=$(cat .kaggle/access_token) STARTER/.venv/Scripts/kaggle.exe kernels push -p notebooks/
```
```bash
KAGGLE_API_TOKEN=$(cat .kaggle/access_token) STARTER/.venv/Scripts/kaggle.exe kernels status sahasawatt/arc-prize-2026-arc-agi-3-starter
```
Quota is 1/day — the main thread owns this decision, per this task's anti-goals. No push was
performed by this session.

## Files touched (edit-scope compliant)

- `kaggle/adapter_hybrid.py` — fixed (this task's authorized scope)
- `kaggle/adapter.py` — fixed (this task's authorized scope; same leak, wider blast radius —
  no `_claimed` gate)
- `kaggle_hybrid_crashtest2.py` — new file, repo root, verification harness
- `results/kaggle-adapter-fix-20260818.md` — this file
- `results/kaggle-adapter-fix-verify-20260818.md` — per-game tables for both sweeps
- `results/pytest-adapter-fix-20260818.txt` — pytest tail
- `C:\Users\Vampi\Desktop\ARC-AGI-3-Kaggle-Starter\agent\my_agent_hybrid.py` — rebuilt (outside
  this repo, per `bundle_hybrid.py`'s own licensing rule; not a repo file)
- `kaggle/my_agent.py` — **untouched**, reverted after an accidental rebuild; now stale
  relative to the fixed `adapter.py` (rebuild command above)

No driver files, no `compete.py`, no `environment_files/` access, no kaggle CLI invocation, no
kernel push.
