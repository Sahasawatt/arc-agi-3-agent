# thui-daq (Depth-Aging Queue) — DRAFT registration 2026-09-23, NOT registered until the user's GPU GO. All times UTC.

Requested by Watchara (relay 01M36NYT3743A103PWHQDE0N8A, 08:26Z; 08:32Z "push to collect data, decide after").
Answered 01M36QQ52Z7TADPDAZY3E8HKQ0 (09:0xZ): 0-GPU build now, six spec changes, GPU after teeth + our quota check.
Option A (this external gate) chosen over vLLM native priority (01M36SDAPCR8ZV7JBV4ANDKMDV); Watchara OK 09:30Z.
Evaluation behind the changes: scratchpad `daq/EVAL.md`.

## Change vs B81 (`thui-a5-mtp0k7s28-full25-r1`)
One graft at the end of cell 9 (`thui-daq/graft_src.py`): a process-wide admission gate on `ToolAgent._chat_completion`.
Admitted-and-unfinished requests ≤ cap = max(10, vLLM `num_requests_running` + 2) — i.e. at most ~2 requests queue inside
vLLM's FCFS queue, and the rest wait in OUR queue, ordered deeper-level first, with any waiter older than 60 s promoted
ahead of all (FIFO among the aged). Fail-open if `/metrics` is unreadable. Gate wait is not charged to the 180 s yield
budget, and the request timeout is reduced by the wait. Control = the same notebook with `_THUI_DAQ_ENFORCE = False`
(computes and logs, admits immediately), so both arms carry the same metrics polling.

## VALID (else VOID)
`THUI_DAQ_GRAFT ok enforce=<arm>` once; `THUI_DAQ_METRICS ok root=http://127.0.0.1:1234 running=..` once (else the gate
was fail-open all run and the arm is B81); ≥ 1 `THUI_DAQ_STATS` line; `max_active ≤ cap` in every STATS line; no permit
leak (the run finishes all 25 games; no game crashed with a gate-related traceback); profile = B81; 25 games; no OOM.
Arm only: ≥ 1 `THUI_DAQ_WAIT` line (the gate bound at least once — otherwise the arm is B81 and the read is VOID).

## SMOKE (matched pair, 25 games @ 1,800 s, ~1.2 GPU-h) — KILL if any
- Mechanism (Watchara's): median gate wait of L3+ requests not ≥ 25 % below L1's, within the arm.
- Throughput: arm generation tokens < 90 % of control → KILL; 90-95 % → reported as a cost, not a kill. Agreed by
  Watchara (relay 09:30Z): the three B81 full controls read 2.60 / 2.43 / 2.57 M generation tokens (CV 3.6 %), a one-pair
  ratio has SD ~5.1 %, so a neutral arm is killed ~16 % of the time at 95 % and ~2.4 % at 90 %.
- Concurrency floor: arm median vLLM Running more than 1 below control's.
- Starvation (agreed 09:30Z): L1's wait at p90 (gate wait; the arm's own vLLM queue is bounded by the +2 headroom) more
  than 2x the control's vLLM queue time at p90 (`vllm:request_queue_time_seconds` histogram). An absolute bar would be
  wrong: under saturation FIFO requests already wait ~41 s on average (B87), and aging at 60 s bounds a waiter's rank,
  not how long every slot stays busy.
- Clock: arm end-of-run wall time > control's + 2 % (the clamp must stop per-game overrun).

## FULL PAIR (only after the smoke passes; ~4.4 GPU-h; 0 slots) — Watchara's gate
PASS only with ≥ 12/25 games up in levels AND ≤ 6 down vs a same-day B81 control, read per game.

## Prediction (confidence L), stated before any GPU
The gate binds (vLLM Waiting median 15 on B81, B87) and the wait order moves (L3+ waits ≥ 25 % below L1). Throughput
90-100 % of control. Levels within ±3 of control, per-game 7-11 up / 6-10 down → the full-pair gate FAILS.
Reason: B87 cut queue share 0.509 → 0.232 and added +21 % generation, and levels read 18/18/18; DAQ adds no throughput,
it only reorders it. B36 (reallocating clock across games) was closed as measured-too-small.

## Build status (0 GPU, 2026-09-23 ~09:45Z)
`thui-daq/` on local branch `thui-daq` (from master 6069938), not committed, not pushed. Written by codex (gpt-5.6-terra,
codex-run.js) to a written spec, then reviewed and fixed in the main thread and by an adversarial 3-lens review
(wf_a31ac277-760). Fixes after review: permit released on every path after admission (record/print inside the finally),
waiter registration inside the cleanup, /metrics fetched outside the lock and single-flight, a missing gauge reads as
unavailable (fail-open) rather than 0, and an install-time /metrics self-check marker. `test_daq_graft.py`: 23/23 against
both localrig and the anim bundle Kaggle runs; `--mutants`: 14/14 red, every mutant asserted to apply exactly once.
Builder arms: thui-daq-v0-smoke25 / thui-daq-ctl-smoke25 (cells [0, 9, 15]), thui-daq-full25-rN / thui-daq-ctl-full25-rN
(cells [0, 9]); arm vs control differ only in `_THUI_DAQ_ENFORCE`, the header and the smoke print.
