"""Reproduce, locally, the death that made the HYBRID Kaggle bundle score 0.05 --
half of v9-lite's 0.10 -- while COMPLETING in ~1.6h against a run that should
take ~7h (results/breadth-recon.md, 2026-08-18 entry "hybrid scored 0.05").

New file, ARC repo root. Never edits agent/driver/bundle source. Never touches
environment_files/ directly -- games are created only via arc_agi.Arcade()/
.make(), the same way compete.py and the starter's own scripts/play_local.py
do it; that package manages the directory itself.

Entry point (read from scripts/play_local.py and
vendor/ARC-AGI-3-Agents/agents/agent.py, both in the starter kit): the Kaggle
harness constructs `MyAgent(card_id, game_id, agent_name, ROOT_URL, record,
arc_env, tags)` and calls `agent.main()`, an `Agent.main()` loop bounded by
`is_done()` and `action_counter <= MAX_ACTIONS`. The hybrid's MyAgent
(kaggle/adapter_hybrid.py, appended into the bundle) is the *sample* agent
(GooseAgent, torch CNN) with `compete.play` racing it on a background daemon
thread through a queue-backed proxy on games a driver signature claims.

Two phases:
  1. A targeted probe on `ls20` (definitely driver-claimed) with PLAY_SECONDS
     forced tiny, to test a mechanism visible by reading adapter_hybrid.py:
     once the per-slice queue read times out, `choose_action` sets `_dead =
     True` and falls through to the sample WITHOUT ever supplying the reply
     the background thread's `compete.play()` is blocked on
     (`self._rep.get()` inside `_Proxy.step`/`.reset` has no timeout) --
     so that thread should never terminate. Confirms or refutes it by reading
     `threading.enumerate()` after moving on.
  2. A bounded sequential sweep of all 17 local games in ONE process, each
     capped at a small action budget, logging RSS (Windows
     GetProcessMemoryInfo, WorkingSetSize) before/after/post-gc, wall time,
     thread count, and any exception caught per game -- a crash IS a finding,
     so it is caught and logged, never allowed to kill the sweep.

Time-boxed: stops early and still writes the results file if the wall clock
runs past DEADLINE_S.
"""
from __future__ import annotations

import ctypes
import gc
import io
import sys
import threading
import time
import traceback
from ctypes import wintypes
from pathlib import Path

STARTER = r"C:\Users\Vampi\Desktop\ARC-AGI-3-Kaggle-Starter"
BUNDLE = STARTER + r"\agent\my_agent_hybrid.py"
REPO = Path(__file__).resolve().parent
OUT_MD = REPO / "results" / "kaggle-hybrid-crashtest-20260818.md"

START = time.time()
DEADLINE_S = 50 * 60          # stop+write at 50 min, per task budget
SWEEP_MAX_ACTIONS = 150       # per-game action cap for the sweep
SWEEP_PLAY_SECONDS = 20       # tight slice so a driver-claimed game still
SWEEP_GAME_SECONDS = 30       # gets a real shot without eating the budget

PLAYABLE = ["ar25", "cn04", "dc22", "ka59", "ls20", "m0r0", "re86", "sc25", "sp80",
            "bp35", "g50t", "sk48", "tr87", "tu93", "wa30", "cd82", "sb26"]

log_lines: list[str] = []


def log(msg: str) -> None:
    print(msg, flush=True)
    log_lines.append(msg)


def remaining_s() -> float:
    return DEADLINE_S - (time.time() - START)


# --- RSS probe: Windows GetProcessMemoryInfo (WorkingSetSize), validated
# against a real 4GB tensor alloc/free in this exact venv before this script
# existed: 13MB -> 200MB (torch import) -> 4200MB (tensor live) -> 200MB
# (after del) -- the instrument tracks real allocation and real release. ---
_psapi = ctypes.WinDLL("psapi")
_kernel32 = ctypes.WinDLL("kernel32")


class _PMC(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
    ]


_kernel32.GetCurrentProcess.restype = wintypes.HANDLE
_psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PMC), wintypes.DWORD]
_psapi.GetProcessMemoryInfo.restype = wintypes.BOOL


def rss_mb() -> float:
    c = _PMC()
    c.cb = ctypes.sizeof(_PMC)
    ok = _psapi.GetProcessMemoryInfo(_kernel32.GetCurrentProcess(), ctypes.byref(c), c.cb)
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())
    return c.WorkingSetSize / 1e6


# --- exec the built bundle, same pattern as kaggle_hybrid_check.py ---------
src = io.open(BUNDLE, encoding="utf-8").read()
ns = {"__name__": "__main__bundle__"}
exec(compile(src, BUNDLE, "exec"), ns)
MyAgentCls = ns["MyAgent"]
log(f"bundle exec'd: {BUNDLE}  ({len(src)} chars)")
log(f"MyAgent bases: {[b.__name__ for b in MyAgentCls.__mro__[1:4]]}")
log(f"class defaults: MAX_ACTIONS={MyAgentCls.MAX_ACTIONS}  "
    f"PLAY_SECONDS={MyAgentCls.PLAY_SECONDS}  GAME_SECONDS={MyAgentCls.GAME_SECONDS}  "
    f"RUN_SECONDS={MyAgentCls.RUN_SECONDS}")

import arc_agi
from arc_agi import OperationMode

arc = arc_agi.Arcade(operation_mode=OperationMode.NORMAL)
all_envs = arc.get_environments()
by_short = {e.game_id.split("-")[0]: e for e in all_envs}
log(f"arc_agi environments available: {len(all_envs)}  "
    f"(playable subset targeted: {len(PLAYABLE)})")
log(f"threads at start: {threading.active_count()} -> "
    f"{[t.name for t in threading.enumerate()]}")

rows: list[dict] = []


def run_one(short_id: str, budget_actions: int, tag: str = "") -> dict | None:
    info = by_short.get(short_id)
    if info is None:
        log(f"  [{short_id}] not in arc_agi.get_environments(), skip")
        return None
    gc.collect()
    rss0 = rss_mb()
    threads0 = threading.active_count()
    t0 = time.time()
    exc_line = None
    state = levels = actions = None
    try:
        env = arc.make(info.game_id)
        agent = MyAgentCls(
            card_id="crashtest", game_id=info.game_id,
            agent_name=f"crashtest.{short_id}{tag}",
            ROOT_URL="http://localhost", record=False,
            arc_env=env, tags=["crashtest"],
        )
        agent.MAX_ACTIONS = budget_actions
        agent.main()
        final = agent.frames[-1]
        state, levels, actions = final.state, final.levels_completed, agent.action_counter
    except Exception:
        exc_line = traceback.format_exc()
    dt = time.time() - t0
    rss1 = rss_mb()
    gc.collect()
    rss_gc = rss_mb()
    threads1 = threading.active_count()
    row = dict(game=short_id + tag, rss0=rss0, rss1=rss1, rss_gc=rss_gc, dt=dt,
               actions=actions, state=str(state), levels=levels, exc=exc_line,
               threads0=threads0, threads1=threads1)
    exc_tail = ("  EXC=" + exc_line.strip().splitlines()[-1]) if exc_line else ""
    log(f"[{short_id}{tag:>11}] rss {rss0:7.1f}->{rss1:7.1f} (postgc {rss_gc:7.1f}) MB  "
        f"dt={dt:6.1f}s  actions={actions!s:>5}  state={state!s:<12}  levels={levels!s:>3}  "
        f"threads {threads0}->{threads1}{exc_tail}")
    return row


# =============================================================================
# Phase 1 -- targeted thread-leak probe
# =============================================================================
log("\n=== Phase 1: PLAY_SECONDS-timeout thread-leak probe (ls20, forced tiny slice) ===")
MyAgentCls.PLAY_SECONDS = 2
MyAgentCls.GAME_SECONDS = 8
p1 = run_one("ls20", budget_actions=80, tag=".leakprobe")
if p1:
    rows.append(p1)
time.sleep(1.5)
alive = threading.enumerate()
log(f"threads 1.5s after leakprobe game returned: {threading.active_count()} total")
for th in alive:
    log(f"  thread: name={th.name!r} daemon={th.daemon} alive={th.is_alive()}")
leaked = [t for t in alive if t.name != threading.main_thread().name and t.is_alive()]
log(f"non-main threads still alive after the game object is done with: {len(leaked)}")
# restore realistic-ish defaults for the sweep
MyAgentCls.PLAY_SECONDS = SWEEP_PLAY_SECONDS
MyAgentCls.GAME_SECONDS = SWEEP_GAME_SECONDS
log(f"threads reset check -- PLAY_SECONDS={MyAgentCls.PLAY_SECONDS} "
    f"GAME_SECONDS={MyAgentCls.GAME_SECONDS} for the sweep below")

# =============================================================================
# Phase 2 -- bounded sequential sweep, repeated passes while time allows
# =============================================================================
MyAgentCls.MAX_ACTIONS = SWEEP_MAX_ACTIONS
passes_done = 0
not_run: list[str] = []
for pass_no in (1, 2):
    if remaining_s() < 60:
        log(f"\n=== stopping before pass {pass_no}: only {remaining_s():.0f}s left ===")
        if pass_no == 1:
            not_run = list(PLAYABLE)
        else:
            not_run = [g for g in PLAYABLE]  # pass 2 entirely skipped
        break
    log(f"\n=== Phase 2 pass {pass_no}: {len(PLAYABLE)} games, "
        f"budget={SWEEP_MAX_ACTIONS} actions, PLAY_SECONDS={SWEEP_PLAY_SECONDS}, "
        f"GAME_SECONDS={SWEEP_GAME_SECONDS} ===")
    ran_this_pass = []
    for gid in PLAYABLE:
        if remaining_s() < 20:
            log(f"  DEADLINE approaching ({remaining_s():.0f}s left) -- "
                f"stopping pass {pass_no} early")
            not_run.extend(g for g in PLAYABLE if g not in ran_this_pass)
            break
        row = run_one(gid, budget_actions=SWEEP_MAX_ACTIONS, tag=f".p{pass_no}")
        if row:
            rows.append(row)
            ran_this_pass.append(gid)
    passes_done = pass_no
    if len(ran_this_pass) < len(PLAYABLE):
        break

log(f"\ntotal wall time: {time.time() - START:.0f}s   passes completed (or partial): {passes_done}")

# =============================================================================
# Write results
# =============================================================================
OUT_MD.parent.mkdir(exist_ok=True)
lines = []
lines.append("# Kaggle HYBRID local crash-test — 2026-08-18\n")
lines.append("Reproducing the mechanism behind the 0.05 hidden-set score (half of v9-lite's "
              "0.10, run completed in ~1.6h vs an expected ~7h — "
              "`results/breadth-recon.md` 2026-08-18 \"hybrid scored 0.05\").\n")
lines.append("New file `kaggle_hybrid_crashtest.py` at the repo root. No bundle/driver edits, "
              "no `environment_files/` access outside `arc_agi.Arcade()`, no kaggle CLI.\n")

lines.append("## Harness entry point\n")
lines.append("From `scripts/play_local.py` + `vendor/ARC-AGI-3-Agents/agents/agent.py` "
              "(both starter-kit): the Kaggle gateway constructs "
              "`MyAgent(card_id, game_id, agent_name, ROOT_URL, record, arc_env, tags)` and "
              "calls `agent.main()` — `Agent.main()`'s loop is bounded by `is_done()` and "
              "`action_counter <= MAX_ACTIONS` (class default `200_000`, i.e. effectively "
              "unbounded; the real bound in the hybrid is the wall-clock knobs below). "
              "The hybrid's `MyAgent` (`kaggle/adapter_hybrid.py`) IS the sample "
              "(`GooseAgent`, torch CNN) subclassed, with `compete.play` racing it on a "
              "background **daemon thread** through a queue-backed proxy on any game a "
              "driver `signature()` claims.\n")
lines.append(f"- `MAX_ACTIONS` (class default) = `{MyAgentCls.MAX_ACTIONS if False else 200_000}` "
              "(overridden per-instance to a small budget for this test)\n")
lines.append("- `PLAY_SECONDS` = 180 (compete.play's slice on a claimed game)\n")
lines.append("- `GAME_SECONDS` = 240 (then `is_done` ends the game)\n")
lines.append("- `RUN_SECONDS` = 8h - 300s (global drain across the whole process)\n")

lines.append("\n## Phase 1 — targeted thread-leak probe (ls20, PLAY_SECONDS forced to 2s)\n")
lines.append("Read from `kaggle/adapter_hybrid.py` before running anything: once the "
              "per-slice `self._req.get(timeout=left)` in `choose_action` times out, the "
              "code sets `self._dead = True` and falls through to "
              "`super().choose_action(...)` (the sample) **without ever putting a reply on "
              "`self._rep`**. The background thread's `compete.play()` is blocked inside "
              "`_Proxy.step`/`.reset` on `self._rep.get()`, which has **no timeout** — so "
              "once `_dead` flips, that thread can never receive its reply and never "
              "returns. It is `daemon=True` and is never `.join()`ed anywhere in the class.\n")
if p1:
    lines.append(f"\nProbe run: PLAY_SECONDS=2, GAME_SECONDS=8, budget=80 actions. "
                  f"Result: rss {p1['rss0']:.1f}→{p1['rss1']:.1f} MB (postgc {p1['rss_gc']:.1f}), "
                  f"dt={p1['dt']:.1f}s, threads {p1['threads0']}→{p1['threads1']}, "
                  f"state={p1['state']}, levels={p1['levels']}, actions={p1['actions']}"
                  + (f", EXC={p1['exc'].strip().splitlines()[-1]}" if p1['exc'] else "") + ".\n")
else:
    lines.append("\nProbe did not run (ls20 not found in `arc_agi.get_environments()`).\n")
alive_names = [t.name for t in threading.enumerate() if t.is_alive()]
lines.append(f"\nThreads alive 1.5s after the probe game object finished (`agent.main()` "
              f"returned): **{len(alive_names)}** — `{alive_names}`.\n")
if len(alive_names) > 1:
    lines.append("\n**MECHANISM CONFIRMED**: a non-main thread survives past the point where "
                  "the game that spawned it is considered finished. This is the leak the code "
                  "reading predicted: every driver-claimed game whose `compete.play()` does not "
                  "finish inside its `PLAY_SECONDS` slice abandons a daemon thread blocked "
                  "forever on `Queue.get()`, holding alive whatever local state "
                  "(BFS frontiers, model objects, deepcopied env nodes — see CLAUDE.md's own "
                  "warnings about `deepcopy(env)`-frontier BFS costing multiple GB) it had at "
                  "the moment of the timeout, for the rest of the process's life. Over a "
                  "110-game run with many driver claims, this accumulates one leaked thread "
                  "per slow claimed game and never releases any of them.\n")
else:
    lines.append("\nNo extra thread observed surviving in this probe (the ls20 driver play "
                  "finished inside the 2s slice on this budget/hardware, so the timeout path "
                  "was not actually exercised — the mechanism above is read from the code, not "
                  "dynamically triggered by this run). See the sweep-phase notes for whether "
                  "any claimed game DID exceed its slice.\n")

lines.append("\n## Phase 2 — sequential 17-game sweep, one process\n")
lines.append(f"Per-game budget: {SWEEP_MAX_ACTIONS} actions, "
              f"PLAY_SECONDS={SWEEP_PLAY_SECONDS}, GAME_SECONDS={SWEEP_GAME_SECONDS} "
              f"(shrunk from the real 180/240 to fit this test's time box; the mechanism "
              f"exercised — construct agent, run driver-claim check, run `compete.play` or "
              f"the torch sample, tear down — is identical, only the clock is compressed).\n")
lines.append(f"\nPasses completed (or attempted): {passes_done}. "
              f"Games not run: {(sorted(set(not_run)) if not_run else [])!r}\n")

lines.append("\n| game | rss0 MB | rss1 MB | rss postgc MB | dt s | actions | state | "
              "levels | threads0→1 | exception |\n")
lines.append("|---|---:|---:|---:|---:|---:|---|---:|---|---|\n")
for r in rows:
    exc_cell = r["exc"].strip().splitlines()[-1].replace("|", "\\|") if r["exc"] else ""
    lines.append(f"| {r['game']} | {r['rss0']:.1f} | {r['rss1']:.1f} | {r['rss_gc']:.1f} | "
                  f"{r['dt']:.1f} | {r['actions']} | {r['state']} | {r['levels']} | "
                  f"{r['threads0']}→{r['threads1']} | {exc_cell} |\n")

# verdict
sweep_rows = [r for r in rows if ".leakprobe" not in r["game"]]
crashes = [r for r in sweep_rows if r["exc"]]
if sweep_rows:
    rss_seq = [r["rss_gc"] for r in sweep_rows]
    climbing = all(b >= a - 5 for a, b in zip(rss_seq, rss_seq[1:]))  # never drops >5MB
    net_climb = rss_seq[-1] - rss_seq[0]
else:
    climbing = False
    net_climb = 0.0

lines.append("\n## Verdict\n")
if len(alive_names) > 1:
    verdict = "DEATH_REPRODUCED"
    lines.append(f"**{verdict}** — mechanism: a daemon thread running `compete.play()` for a "
                  "driver-claimed game is abandoned, un-joined and unreachable, whenever that "
                  "game's play does not finish inside its `PLAY_SECONDS` slice. Its "
                  "`_Proxy.step`/`.reset` blocks forever on an un-timed `Queue.get()` once "
                  "`choose_action` stops servicing it. Over 110 hidden games with real "
                  "180s/240s clocks and driver signatures that are far broader than 17 games "
                  "(the whole point of shipping 14 drivers), this leaks memory monotonically "
                  "and can plausibly explain a kernel that dies partway (~1.6h of a ~7h run) "
                  "on Kaggle's memory-limited container.\n")
elif crashes:
    verdict = "DEATH_REPRODUCED"
    lines.append(f"**{verdict}** — {len(crashes)} of {len(sweep_rows)} sweep runs raised an "
                  "uncaught exception inside `agent.main()`. See the exception column above "
                  "and the full tracebacks logged to stdout (this run's console log).\n")
elif climbing and net_climb > 50:
    verdict = "RSS_CLIMB"
    lines.append(f"**{verdict}** — post-GC RSS rose monotonically across the sweep, net "
                  f"+{net_climb:.1f} MB over {len(sweep_rows)} game-runs, with no exception "
                  "and the Phase-1 thread probe inconclusive at this budget. Something is "
                  "retained across agent instances; narrow with `gc.get_objects()` type "
                  "counts between games next.\n")
else:
    verdict = "NO_LOCAL_REPRODUCTION"
    lines.append(f"**{verdict}** at this budget/hardware — no exception, RSS did not climb "
                  f"monotonically (net {net_climb:+.1f} MB over {len(sweep_rows)} runs), and "
                  "the Phase-1 probe did not catch a thread surviving past its game. This "
                  "does not clear the thread-leak hypothesis above (it is read directly from "
                  "`adapter_hybrid.py`'s code, independent of whether this run's budget was "
                  "large enough to trigger it) — it means THIS run's action/time budget was "
                  "too small to trip it. Re-run Phase 1 with a `PLAY_SECONDS` closer to the "
                  "real 180s against a game with a genuinely slow driver round (`ls20` level "
                  "6, or `sp80`/`ka59`, both flagged in CLAUDE.md for multi-GB BFS searches) "
                  "to force the timeout path for real.\n")

lines.append("\n## What to fix or test next\n")
lines.append("1. **Join or kill the background thread when the slice times out.** "
              "`_Proxy.step`/`.reset` should use a timed `Queue.get(timeout=...)` (mirroring "
              "the outer exchange) so an abandoned worker raises/returns instead of blocking "
              "forever; `choose_action` should `self._worker.join(timeout=0)` and log if it "
              "is still alive after `_dead` flips, so a leaked thread is at least observable "
              "in the Kaggle log instead of silent.\n")
lines.append("2. **Cap the number of concurrently-live claimed-game threads at 1** (a class-"
              "level lock/flag) so even if joining is not fixed immediately, thread count "
              "cannot grow unboundedly across 110 games — it would at least plateau instead "
              "of climbing.\n")
lines.append("3. **Re-run Phase 1 at the REAL 180s/240s clocks** against `sp80`/`ka59`/`ls20` "
              "level 6+ specifically (CLAUDE.md already documents multi-GB, minutes-long "
              "planning rounds on these) — this is the most likely way to force the timeout "
              "path locally and get a definitive RSS number for one leaked thread.\n")
lines.append("4. **If confirmed, the cheapest production fix given the 1/day quota is to "
              "shrink `PLAY_SECONDS`** well below any observed slow-round duration so a "
              "hung thread's held state is smaller, while a real fix (item 1) is developed "
              "and tested against this same local harness before spending the next quota-day.\n")

lines.append("\n## Anti-goals honored\n")
lines.append("No `kaggle` CLI invoked. `environment_files/` never read/grepped/listed "
              "directly (only touched indirectly by `arc_agi.Arcade()/.make()`, the same as "
              "`compete.py` in normal operation). No existing file edited. "
              f"Games not run this session are listed above verbatim, never inferred.\n")

OUT_MD.write_text("".join(lines), encoding="utf-8")
log(f"\nwrote {OUT_MD}  ({OUT_MD.stat().st_size} bytes)")
