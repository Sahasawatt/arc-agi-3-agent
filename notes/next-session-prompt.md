# ARC-AGI-3 breadth campaign — standing session brief (rewritten 2026-08-08)

Repo `Desktop\projects\arc-agi-3-agent` · python `./.venv/Scripts/python.exe` (always; never bare `python`).
This brief is meant to be reused. Update the GOAL numbers and the QUEUE after every session; leave the rest.

## GOAL — CHANGED 2026-08-18 11:30 by user: KAGGLE SCORE FIRST, target TOP 5

**The local clear-all-levels campaign is now SECONDARY.** Primary = Kaggle public score.
Leaderboard 2026-08-18: top5 = 2.35+, #1 = 2.81, rank ~17 = 1.98. Us: 0.11 (v1). The public
sample base (StochasticGoose) ≈ 1.56 alone ≈ rank ~25-30.

**Score ladder (execute in order, one submission per UTC day, NEVER spend quota on an
unreproduced fix):**
1. **Rung 1 — establish the goose floor (~1.56)**: our hybrid died mid-run (0.05, COMPLETE in
   ~1.6h vs ~7h). Crash-test running locally. If the death is OUR bundling → fix + verify locally
   (full 17-game double-pass, RSS flat) → submit fixed hybrid. If ambiguous → submit the PURE
   unmodified sample first (proves the 7h envelope + banks ~1.56).
2. **Rung 2 — goose + surgical adds**: drivers only where signatures match (harmless), tune
   goose's own knobs (time allocation per game/level, exploration).
3. **Rung 3 — close 1.56 → 2.35**: study top public notebooks/discussions; port our measured
   generic mechanics (click-then-ACT probing, level-clock budgeting, phase/lattice detection) into
   goose's exploration policy. Every candidate change A/B'd locally on the 17 games before quota.

BFS chains for the local campaign are PARKED (checkpoints intact) — do not relaunch while the
score push is active unless RAM is free and the user OKs.

## OLD GOAL (secondary now)

Clear ≥1 level in EVERY game (user's standing order 2026-08-14: clear ALL levels of ALL games). Standing: **16/17 games with a level, mean 24.051% (wave-14); g50t L1 fell 2026-08-18 to the domain-blind squirrel agent through a FALSE exhaustion proof (26-action line, glide.py); 2026-08-17 gave sp80 L3 + m0r0 L2. Only sc25 remains at 0**
(tu93 100.0 · sb26 100.0 · ls20 43.629 · re86 41.477 · sp80 28.571 · ar25 27.778 · tr87 14.286 · m0r0 14.286 · cd82 10.514 · wa30 6.667 · cn04 4.762 · dc22 4.762 · ka59 3.571 · g50t 3.571 · sk48 2.778 · bp35 2.222 · sc25 0)
← **results/sweep-wave14.log** is the current clean gate (wave-14 = glide.py g50t L1, 0/7→1/7; wave-13 = twin.py m0r0 L2; wave-12 = swap.py sp80 L3) (chain: wave-6 → wave-8 [haul's wa30 L2 guards] → wave-9 [mirror L2] → wave-10 [mirror L3] → wave-11 [mirror L4]; every hop diffed with `sweep_diff.py <before> <after> <control>`, a control that DIFFERS, 16 of 17 identical to the digit, no game ever losing a level; pytest 330 throughout). ⚠️ `sweep-tu93win.log` = an aborted MemoryError run — ignore it. Remaining 0-level: sc25 (closed) — and **g50t is REOPENED 2026-08-18: squirrel.py cleared L1 (5th false exhaustion — the proof was single-life; the win uses resets). Landing in flight, see recon tail.**

## STATE AT 2026-08-21 05:00 Thai — v10 IS THE CANDIDATE (public band [4.55, 4.71]); GPU quota exhausted; awaiting user's go to submit

**One decision is open and it is the user's:** submit **duckv10** (kernel
`sahasawatt/taaf-duck-v10`, version 2 is the confirmed one) or keep iterating. User's standing
rule 2026-08-20: **submit only when THEY are satisfied** — never submit unasked; the daily
auto-resubmit is CANCELLED.

**Submit command (only on explicit user go), run from `Desktop\ARC-AGI-3-Kaggle-Starter`:**
`competitions submit -c arc-prize-2026-arc-agi-3 -f submission.parquet -k sahasawatt/taaf-duck-v10 -v 2 -m "duck-v10: anim bundle + Qwen3.8-27B-FP8, uncapped; public band [4.55, 4.71]"`
with `KAGGLE_API_TOKEN=$(cat .kaggle/access_token) ./.venv/Scripts/kaggle.exe` in front.
Verify with `competitions submissions` — **NEVER** read success from error text: a
"0 submissions remaining" line prints after a SUCCESSFUL submit, and that misread cost a
quota day on 2026-08-18.

### What v10 is

`duckv10/` = the duckmod notebook shell with three cells changed (6, 8, 12): dataset swapped to
Tufa's public **animation-awareness bundle** `jakobbrggen/taaf-kaggle-source-anim-20260807-anim`
(the "duck v12" lineage the whole public field runs) + model swapped to **Qwen3.8-27B-FP8**
(`jakobbrggen/qwen3-8-27b-fp8-hf-snapshot`) via a setup-command string rewrite, **output left
UNCAPPED**, duckmod's own patches dropped. Verified live in its kernel log:
`SERVED_MODEL_NAME='vrfai/Qwen3.8-27B-FP8'`, `LOCAL_ANALYZER_MAX_OUTPUT='0'`,
`hard_noop_guard=True animation_awareness=True`.

### Public ladder (each number is a commit-run mean over the 25 public games)

| build | mean(s) | scoring | levels | note |
|---|---|---|---|---|
| **v10** | **4.55, 4.71** | 14, 18 /25 | 22, 28 | band 0.16 = tightest measured |
| v12 = v10 + brevity prompt | 3.72 | 17 | 24 | below band → rejected |
| v8 = old bundle + 3.8 | 3.31, 2.87 | 15, 13 | 22, 19 | model swap alone |
| v5 | 2.43, 2.37 | — | — | hidden draw 0.84 |
| duck-mod | 2.41, 2.16 | 13 | 17, 19 | hidden draw 1.00 = current LB |
| v6 | 1.85 | — | 24 | warnings taxed actions |
| v4 | 1.73 | — | — | levers measured inert (R7) |
| v9 = v10 + cap 768 | 0.22 | — | — | cap truncates tool calls |

Hidden draws so far: duck-mod **1.00** (rank 585/2409), v5 **0.84**, pre-duck agent 0.11.
Leaderboard 2026-08-19: #1 3.57, top-5 bar 2.57.

### Rules whose violation breaks something (restated, not linked)

- **NEVER read/grep/list `environment_files/`** — it is the answer key for the 25 public games.
- **NEVER cap total output.** v9 proved `LOCAL_ANALYZER_MAX_OUTPUT=768` truncates the tool call
  that CARRIES the action: finish_reason `length` 704 vs `tool_calls` 68, 87 vLLM parser errors,
  score 0.22. Uncapped controls: 326/4 and 673/2, zero `length`. v7/v7b are dead by the same
  mechanism — do not run them.
- **Never log the Kaggle token**; read it from its file straight into the CLI env.
- **Stage by explicit path** — never `git add -A`, never `git add <dir>/`.
- Agent-repo commits happen in `Desktop\projects\arc-agi-3-agent` — NOT inside the arc-agi-pub
  submodule checkout (detached-HEAD trap, hit once; recovery was a cherry-pick into the real repo).
- Kaggle caps **2 concurrent GPU sessions** and **30 GPU-h/week**; the weekly quota is EXHAUSTED
  as of 2026-08-20 21:40 UTC, so no commit-run eval is possible until it resets.

### UNPROVEN — carry forward as unproven

- **v10's HIDDEN score.** Both runs are public-set only. duck-mod shrank 2.4x public→hidden and
  v5 2.9x; the same shrink would put v10 at ~1.6-1.9 (still above our 1.00) — but nothing
  measured says the shrink ratio is stable across designs.
- **duckv13 (v10 + animation-retrieval discipline) has NEVER RUN.** Built and bundle-verified
  only. R18's prediction is on the record: retrievals 669 → ≤167, no depth loss on
  ft09/sb26/sc25, ≥1 new level among tn36/sp80/sk48/cd82. Blocked purely by GPU quota.
- **Whether a submission consumes the weekly GPU quota.** Reasoned no (three prior 9h submissions
  coexisted with a full local eval schedule) but never tested against an exhausted quota. A
  refusal with a quota error refutes it and costs nothing.
- **Whether v10 beats v8 with statistical confidence.** v10's band sits clear of v8's, but that
  is 2 runs each, not a paired test. The harness ships `significance.py` (paired t / permutation
  / Bayes, multi-pass native) and it has STILL never been used — the notebook hardcodes
  `bm.n_passes=1` in cell 14 AFTER the customization hook.

### Where everything is written down

- `results/breadth-recon.md` — the campaign log in time order; every number above has its entry
  with the evidence that produced it. **Do not re-derive; read it.**
- `results/wayfinder/R1`–`R18` — research reports (R9 variance/stability, R10 throughput, R13
  anim-bundle diff + rebase decision, R16 v8 forensics, R17 thinking-budget infeasibility, R18
  v10 headroom + the animation-loop finding).
- `notes/wayfinder/MAP.md` — decisions and open tickets (B13 = run v13 when quota returns).
- Workspace `Desktop\projects\arc-agi-pub` (docs + this repo as a git submodule) has a docs
  commit waiting for the user to publish it themselves.

### Review status

Pipeline (d) review fan-out over the 42-file / 5,485-LOC diff `ce63b7e..2ccd155`: **SHIP**.
One CONFIRMED finding, LOW, at `duckv6/duckv6_digest.py:138` (a `reset` outcome is counted in the
`noop` bucket) — duckv6 is a rejected build (1.85), so it does not touch the candidate. Two
findings REFUTED by the verify pass: a MEDIUM grid-shape claim that is dead code on the real
path, and a `shell=True` pattern inherited from upstream.


## (superseded) STATE AT 2026-08-20 16:50 Thai — v5 hidden = 0.84 (leaderboard stays 1.00); v6 public eval running

v6 public eval: **1.85 out-of-band low, HELD** (warnings fired but suppressed actions
30%; hud hint never fired). **SUBMISSION CADENCE CHANGED by user 2026-08-20 19:45 Thai:
no more automatic daily submits — spend a slot only on (a) a candidate that beat the
eval bar, or (b) a deliberate probe (e.g. the baseline hidden-shrink probe in MAP.md).
The Aug-21 duck-mod auto-resubmit is CANCELLED.** v5 (55633845) drew hidden **0.84** vs duck-mod's 1.00 — two designs with near-identical
public bands ([2.37,2.43] vs [2.16,2.41]) drew 0.84 and 1.00: the public->hidden gap is the
dominant unknown, single draws cannot rank designs. Next: v6 public eval (~11:00 UTC) →
Aug-21 slot = duck-mod v1 resubmit (safe second draw) unless v6 is in-band+ with warnings
demonstrably CHANGING behavior in transcripts. R7's hidden-behavior hypotheses are the
mandated reading before shipping new designs (tree branch <1.0).

## (superseded) STATE AT 2026-08-20 07:05 Thai — WAITING ON: submission 55633845 (duck-v5) hidden score

**Live thread: 55633845 (taaf-duck-v5 v1) PENDING since 00:02 UTC Aug 20** — expect COMPLETE
~09:00-12:00 UTC. Check: cd Desktop/ARC-AGI-3-Kaggle-Starter; KAGGLE_API_TOKEN=$(cat
.kaggle/access_token) ./.venv/Scripts/kaggle.exe competitions submissions -c
arc-prize-2026-arc-agi-3 | head -4. v5 = state channel (accumulating world model + auto
transition digest + reset banner), public 2.43 = top of the duck-mod band [2.16, 2.41].
Wayfinder map: notes/wayfinder/MAP.md (R1-R7 + v4 postmortem + v5 build all recorded).
Next after the score: v5 >= ~1.3 hidden → state channel shrinks less than duck-mod's 2.4x,
double down (v6 = deepen digest / per-action hypotheses); v5 ~1.0 → variance-equal, pick next
lever from R6 modes 3-4; v5 << 1.0 → read the hidden-run behavior hypotheses in R7 first.

## STATE AT 2026-08-19 19:15 — SCORE LANDED: duck-mod hidden = 1.00, rank 585/2409

**Submission 55613165 (taaf-duck-mod v1) COMPLETE at ~12:05 UTC: publicScore 1.00** — our best
ever (prior max 0.11), first score above the field median (0.26). Rank 585/2409; 581 teams above,
11 tied at 1.00. Public 2.41 → hidden 1.00 confirms the forensics read (results/
duckmod-transcripts-20260819.md): the 2.41 was a 2-game public effect (ft09+ar25), priming/
variance — it does not transfer. Leaderboard moved: **top5 bar now 2.57** (#1 = 3.57 cstl).
**Decision taken (tree branch 1.0-1.5): resubmit duck-mod v1 at 2026-08-20 00:00 UTC (07:00
Thai)** — Kaggle keeps best score, so a second hidden draw is free upside; baseline fork
(public 1.25) offers no edge; duck-v3 (0.80) still barred as-is. From
Desktop\ARC-AGI-3-Kaggle-Starter:

    KAGGLE_API_TOKEN=$(cat .kaggle/access_token) ./.venv/Scripts/kaggle.exe competitions submit -c arc-prize-2026-arc-agi-3 -f submission.parquet -k sahasawatt/taaf-duck-mod -v 1 -m "duck-mod v1 resubmit: second hidden sample (first draw 1.00, public 2.41)"

Verify via `competitions submissions`, never error text.
**Strategic read: re-rolls of a ~1.0-mean design cannot reach 2.57 — top-5 needs a design
improvement on the duck harness** (seeded A/B locally first; the seeded-runs question for duck-v3
is still open). **Public-set means (all SINGLE runs; ⚠️ R5 corrected the old "σ≈0.4 per game"
label — 0.4 is the σ of the AGGREGATE 25-game mean, real per-game SD is 2.15-4.88, single runs
cannot rank designs):** duck baseline 1.25 ·
duck-mod 2.41 (hidden 1.00) · duck-v3 0.80. Kernels ready: sahasawatt/taaf-duck-fork v1 ·
taaf-duck-mod v1 · taaf-duck-v3 v1 (do not submit as-is).
**Local campaign:** 16/17 games hold a level (wave-14, mean 24.051%); BFS chains STOPPED at user
request, checkpoints intact (resume commands in the 19:15 block below — no --fresh). Duck source +
TAAF study + all build reports committed through `a7d6d2b`.

## STATE AT 2026-08-18 17:15 — STRATEGY PIVOT: the milestone winner's code is PUBLIC; the road to top-5 is a Duck fork with our tools

Primary-source intel (recon tail "KAGGLE INTEL 2"): milestone-1 winner = **Tufa's Duck Harness**
(Qwen 3.6 27B FP8 in a Python REPL, context eviction, multimodal frames), official 1.21, **code
open**: kaggle.com/code/jeroencottaar/taaf-duck-harness-kaggle-share (the recommended fork base;
agent code attached as a Kaggle dataset). Kaggle env = RTX Pro 6000 / 96GB / 9h (our
build_notebook still pins t4 — revisit). Today's top5 (2.35+) ≈ improved Duck forks.
**Plan: (1) tonight 07:00 submit v12 as planned (validates our adapter fix); (2) fork
duck-harness-share + its dataset, get it running (commit-run), bank ~1.0-1.2; (3) differentiate
toward 2.35+ by injecting this campaign's measured mechanics as REPL tools for the LLM (component
click enumeration, transition-graph builder, budget/absorption awareness).** Goose/hybrid line =
superseded baseline; keep v12's result as the adapter-fix validation, not the future.

## STATE AT 2026-08-18 14:00 — ADAPTER LEAK FOUND+FIXED, KERNEL v12 READY; submit at 07:00 Thai

**GOAL IS NOW SCORE-FIRST (top 5 = 2.35+; see the GOAL section).** The decisive bug is found and
fixed: both Kaggle adapters leaked one permanently-blocked worker thread per game (terminal reply
never delivered; un-timed Queue.get; adapter.py leaked on EVERY game — it has no claimed-gate), RSS
climbing to 2.6GB per sweep — this killed the hybrid run at 0.05 and suppressed every prior
driver-carrying submission (v1 no-drivers = 0.11 is our max, consistent). Fix verified: threads
bounded (max 5 vs 1→29 climb), pytest 330, hybrid rebuilt sha 2ee18d9… (237,218B), v9-lite bundle
kaggle/my_agent.py also rebuilt with the fixed adapter. **Kernel v12 = the FIXED HYBRID, COMPLETE,
submission.parquet verified.** At 00:00 UTC (07:00 Thai) from Desktop\ARC-AGI-3-Kaggle-Starter:

    KAGGLE_API_TOKEN=$(cat .kaggle/access_token) ./.venv/Scripts/kaggle.exe competitions submit -c arc-prize-2026-arc-agi-3 -f submission.parquet -k sahasawatt/arc-prize-2026-arc-agi-3-starter -v 12 -m "hybrid + adapter leak fix: terminal reply delivered, timed queue, worker joined"

Verify via `competitions submissions`. What it tests: the goose base surviving the full run
(expect >=1.0 if the leak was the whole story; ~0.05-0.1 = a second mechanism remains).
Intel (results/kaggle-intel-20260818.md): top-5 path = deterministic transition-graph agents (the
preview's 2nd place) — OUR instrument family; scoring rewards levels completed over efficiency; NO
internet during scoring. Next build after the floor is banked: port the campaign's graph-search
machinery into a generic agent.
BFS chains stay PARKED (user RAM request; checkpoints intact, resume commands in the 19:15 block).

## STATE AT 2026-08-17 19:15 — MACHINE RESTART: everything checkpointed, three chains resume with one command each

**Standing: mean 23.841% (wave-13 gate, results/sweep-wave13.log). TWO levels fell today** — sp80 L3
(swap.py L3_LINE, wave-12) + m0r0 L2 (twin.py L2_LINE, wave-13). All committed+pushed to `9947445`.

**Resume after restart (cd Desktop/projects/arc-agi-3-agent; each chain resumes from its atomic
checkpoint — do NOT pass --fresh):**

    PYTHONUTF8=1 ./.venv/Scripts/python.exe sp80_s13.py --budget-seconds 3300   # L4, ckpt @160k expanded
    PYTHONUTF8=1 ./.venv/Scripts/python.exe wa30_b2_l3chain.py --budget-seconds 3300   # L3, ckpt @64k, divergence 0
    PYTHONUTF8=1 ./.venv/Scripts/python.exe re86_b2_l6chain.py --budget-seconds 3300   # L6, ckpt @976k expanded

Chain each in a loop until FINAL shows exhausted=True or win=True (the 12x3300s wrapper pattern is
in this session's bash history / recon). On win=True: independent replay (pattern
results/sp80-win-replay.txt), land in the driver, pytest, full sweep, sweep_diff vs wave-13 —
one driver change per wave.

**dc22 L2: do NOT resume dc22_c2** — its exhaustion is VOID (73/100 collision pairs diverge; hidden
state; results/dc22-c3-verify-20260817.md). Next step = respawn the hidden-state identification
agent (spec in the recon tail section "the EXHAUSTION IS VOID"): characterize divergent pairs →
sound key (candidates: per-button press counters; or the discarded frame PLANES — dc22 returns up
to 15) → zero-divergence validation → only then re-run exhaustion as dc22_c5.

**KAGGLE — at 07:00 Thai (00:00 UTC): submit the HYBRID, kernel v11 (COMPLETE, parquet verified).**
From Desktop\ARC-AGI-3-Kaggle-Starter:

    KAGGLE_API_TOKEN=$(cat .kaggle/access_token) ./.venv/Scripts/kaggle.exe competitions submit -c arc-prize-2026-arc-agi-3 -f submission.parquet -k sahasawatt/arc-prize-2026-arc-agi-3-starter -v 11 -m "hybrid: sample base + 14 measured drivers, mirror L3/L4 current (rebuilt 2026-08-17)"

Verify via `competitions submissions` (the resource), never the submit command's error text.
v9-lite answered yesterday's question: 0.10 — v8's 0.01 was v8's own changes.

**Parked (do not respawn without a structurally new idea):** ka59 L2 (fill model closed), ar25 L5
(position family closed board-wide). cn04 L2 = 4-body product space, needs a sound reduced key or
directed search. Agents must run searches FOREGROUND (a subagent's background job dies with it —
three agents hit this today).

## STATE AT 2026-08-17 09:05 — HYBRID IS PUSHED AS KERNEL v11; tomorrow = ONE submit command

Hybrid rebuilt (one-line mirror-payload diff, sha 56aa957f…, 5/5 checks incl. L3/L4 in the decoded
mirror — results/kaggle-hybrid-rebuild-20260817.md), swapped into starter agent/my_agent.py
(v9-lite backup in the session scratchpad + kernel v10 history), notebook rebuilt, **kernel VERSION
11 pushed** (commit run RUNNING at push time — verify COMPLETE + submission.parquet in the output
before submitting; a ~21s COMPLETE is the normal commit run). At the 00:00 UTC quota window run,
from Desktop\ARC-AGI-3-Kaggle-Starter:

    KAGGLE_API_TOKEN=$(cat .kaggle/access_token) ./.venv/Scripts/kaggle.exe competitions submit -c arc-prize-2026-arc-agi-3 -f submission.parquet -k sahasawatt/arc-prize-2026-arc-agi-3-starter -v 11 -m "hybrid: sample base + 14 measured drivers, mirror L3/L4 current (rebuilt 2026-08-17)"

Verify against `competitions submissions` (the resource), never the submit command's error text.
What it tests: sample-base ~1.56 + driver overrides vs v9-lite's 0.10 — the first submission whose
predicted score comes from the sample's own baseline rather than our drivers.

## STATE AT 2026-08-17 08:40 — KAGGLE ANSWERED: v9-lite = 0.10, v8's 0.01 WAS v8 (read this first)

**The discriminating experiment already ran**: submission 55559497 (2026-08-16 17:40 UTC, v9-lite)
is COMPLETE with **publicScore 0.10** — yesterday's "quota-blocked" reading was wrong; the 400 came
AFTER that submit had landed. Reverting v8's two changes restored 0.01 → 0.10: **the drop was v8
itself** (60s slice + qstate bandit). Today's quota got spent on an accidental byte-identical
duplicate (55567678, PENDING — expect ~0.10). **Next lever = the HYBRID bundle** (sample base ~1.56
+ driver overrides, <starter>/agent/my_agent_hybrid.py via kaggle/bundle_hybrid.py): REBUILD it
(it predates current mirror.py), verify like kaggle/bundle_check.py, push as a new kernel version,
submit at tomorrow's 00:00 UTC window. Verify any "blocked" reading against `competitions
submissions`, never against the submit command's error text.

Local campaign same-day: **ka59 L2 fill model CLOSED** (3-simultaneous-fill achieved — first ever —
all NOT_FINISHED; dot2's kick rectangle can never reach box2 → "3 filled + piece in box2"
unreachable; parked like re86 L6) · **ar25 L5 position×phase×click family CLOSED board-wide**
(5,674 arms, zero wins; parked) · **sp80 L3 long run in progress** (sp80_s11.py chained background,
checkpointed, resolver multi-match→size fixed, watch results/sp80-s11-run1.txt FINAL lines).
Details + censuses: results/breadth-recon.md tail sections dated 2026-08-17.

## OLD STATE 2026-08-17 (superseded — kept for the submit-command reference)

**v9-lite is pushed as kernel VERSION 10, commit run COMPLETE, submission BLOCKED on quota until
00:00 UTC = 07:00 Thai.** The API body (dug via requests spy -- the CLI prints a bare 400) said:
"daily Submission allowance (1) today, try again tomorrow UTC". Run this from
`Desktop\ARC-AGI-3-Kaggle-Starter` after 07:00 Thai:

    KAGGLE_API_TOKEN=$(cat .kaggle/access_token) ./.venv/Scripts/kaggle.exe competitions submit       -c arc-prize-2026-arc-agi-3 -f submission.parquet       -k sahasawatt/arc-prize-2026-arc-agi-3-starter -v 10       -m "v9-lite: play owns the whole 240s clock; bundle rebuilt with current mirror.py"

Facts behind it, all verified this session:
- **The committed bundle was STALE and would have shipped without ar25's L3/L4** -- rebuilding changed
  exactly one line, the `mirror` payload. Fixed in `4de4923`; starter's `agent/my_agent.py` now
  sha-matches the repo bundle (230,211 B). `kaggle/bundle_check.py` passes 5/5 (needs
  `PYTHONPATH=<starter>/vendor/ARC-AGI-3-Agents`, else a false ModuleNotFoundError).
- **A ~21s COMPLETE on the kernel is NORMAL** -- that is the commit run (wheels + notebook convert, no
  play). The real ~7.3h run happens server-side after `competitions submit`.
- **What this submission tests**: v9-lite reverts v8's two changes (60s unclaimed slice + qstate
  bandit) and is the first bundle carrying current mirror.py. Back to ~0.10-0.11 => the cause was in
  v8. Still 0.01 => neither of v8's changes was the cause -- and note BOTH written explanations are
  already refuted by measurement: ls20 clears 5 of 7 levels inside 60s (LEVELCLOCK 0.8/2.4/6.4/16.1/
  47.8s, `results/kaggle-yield.txt`) and levels 6-7 don't arrive within 240s anyway, so the v8 slice
  change was worth ZERO levels on ls20 locally. The 10x drop is still unexplained; leading suspect is
  a silent worker death (the repo has a recorded case: 120s timeout killed the worker, 5/7, no error
  anywhere).
- **Why local levels don't move the Kaggle number** (measured, not theory): v1 no drivers = 0.11, v7
  fourteen drivers = 0.10 -- driver signatures match ~nothing on the hidden 110. And locally we keep
  ~100% of the completion cap on 7 of 8 scoring games (`scoring.py` decode) -- we are not slow, we are
  capped by levels. The score lever for Kaggle is the HYBRID (sample base ~1.56 + driver overrides),
  which still needs a REBUILD before any submission -- it predates current mirror.py too.

## STATE AT 2026-08-16 (read this first; the 08-15 block below is still valid)

⚠️ **SESSION ENDED ON THE WEEKLY AGENT LIMIT** (`resets 9pm Asia/Bangkok`). The last agent died
mid-run; nothing is lost, because both long searches checkpoint a **path-based** frontier. Resume
points, ready to continue rather than re-derive:
- **ar25 L5** — `ar25_t4.py` (has a `--report` mode reproducing the curve from the checkpoint alone).
  At the cut: **8,885 expanded, 11,215 distinct keys, frontier 2,330, divergence 0**, under the
  corrected key that represents `sel_phase`. The model predicts ~18,000 states, so it is ~62% explored.
  **Stop rule to use** (mine, after getting it wrong once — see below): exhausted at frontier 0;
  MODEL REFUTED if keys pass ~36,000 with new-keys-per-node still >= ~1.2; otherwise report the curve.
- **sp80 L3** — `sp80_s9.py`/`sp80_s10.py`. Needs **checkpointing added** (both restart from the L3
  root each call) and the `transfer_multi_match` tie-break resolved before any null counts.
- **Nothing is ungated, nothing is half-applied**: no driver `.py` was edited on disk all session,
  the tree is still the wave-11 gate, pytest 330.
- ⚠️ **The committed explanation for Kaggle v8's 0.01 is UNSUPPORTED — do not quote it.**
  `kaggle/adapter.py`'s docstring says *"the mop-up is actively harmful relative to `compete.play`"*,
  and that is an inference from one score, not a measurement. **Measured today** (`kaggle_yield_probe.py`,
  a shadow-module patch of `compete.py` printing wall-clock at every level-up — the file on disk is
  untouched, so no sweep): on **ls20**, the only local game the GENERIC rungs clear with no driver and
  therefore the honest proxy for the hidden 110, levels land at
  **0.8s · 2.4s · 6.4s · 16.1s · 47.8s** — **5 of 7 inside 60 seconds**. The run was then killed at a
  900s cap with levels 6 and 7 still unreached, so **they need >850 further seconds** (level 6 is the
  patrol planner that "thinks for MINUTES on one round"). **With `GAME_SECONDS = 240` those two levels
  are unreachable under EVERY variant** — so v8 (60s), v7 (180s) and v9-lite (240s) all score ls20 at
  **5 levels. The play-slice change is worth ZERO levels here.**
  Both standing explanations predict a PROPORTIONAL loss and the score fell **ten-fold** (0.10 → 0.01),
  so neither survives. The untested candidate that fits a 10x drop is **the run not finishing**: v8's
  other change was a per-`(frame-hash, action)` `_qstate` table accumulating across 110 games and
  thousands of frames each, against a notebook memory ceiling — and a kernel that dies partway scores
  zero for every game after it. Same shape as the `deepcopy(env)` frontier that hit **6.3 GB at 12,000
  nodes** today: *a per-unit cost measured cheap is a claim about TIME, never about SPACE.*
  Next step, cheap and decisive: measure `_qstate`'s growth rate per game locally.


**Nothing landed and nothing needs a sweep — the tree is unchanged and still gated at wave-11.**
The session's whole product is measurement, and three walls moved from "exhausted" to "proven",
which is what lets them stop consuming rounds. Full write-ups: `results/breadth-recon.md` §2026-08-16.

- **wa30 L3 is ARITHMETIC, not planning.** The level runs a **100-action clock** (28 byte-identical
  lives), its frame's interior proper is **84 cells**, `_slots` tiles it with **8 windows** worth
  12,12,12,12,9,9,9,9 — and **only 5 crates exist**, with 300 idle actions spawning none and the
  conveyor delivering nothing here (unlike L2). A 4x4 crate on a step-4 lattice in an 8-wide frame
  occupies exactly one window, so five crates cover at most **57 of 84**. Either the win is not
  "empty the interior" and `haul.py`'s target is wrong on this board, or L3 is unwinnable as modelled.
  **The two `_plan` changes the 08-15 block proposed are retired unwritten** — they were answers to
  the wrong question, as were the nine rounds of plan-invalidation fixes before them.
- **re86 L6: box-covering is closed BY PROOF, both groups.** The ring's ceiling is also **2 of 4**
  (reach ±9, its boxes' pairs 27 apart), the 40-cell wall is fully inert and is the only thing L6
  adds over L5, and — the arm that settles it — partial coverage consumes **nothing on L1 either**,
  with a natural L1 win in the same invocation proving consumption is detectable. So the
  all-or-nothing rule is the GAME's, not L6's. No placement, ordering or combination can win L6 by
  covering. What L6's win IS remains unknown — the "what change is PERMANENT here" enumeration found
  exactly one and it does not open the level: **a press refused by the WALL desyncs the shape's drawn
  arm from its own marker** by the denied displacement (marker frozen, arm walking 18→21→24→27 over
  five refused DOWNs), it survives a toggle, and only `reset()` clears it — but it is capped at the
  shape's natural reach, so it reaches no box `candidates()` could not already reach. **It corrects a
  CLAUDE.md claim** (a refusal is "the marker did not move", NOT "the frame did not change") and that
  narrowing is now in the traps list.
- **ar25 L5 — a SEARCH is finally possible, and two attempts died on the KEY** (`ar25_s1..s3.py`).
  Exhaustion is available because **A5 is a measured byte-identical alias for the click**, so 4,096
  targets collapse into one verb already in the plain set and `[1,2,3,4,5,7]` is a COMPLETE action set.
  `s1` board-keyed BFS: every control passed (deepcopy fidelity; **a death REVERTS**, 321-cell positive
  control firing, so dropping GAME_OVER children is sound) and it still did not converge — boards
  **+1.73 per node expanded, frontier +0.73, dead straight** at branching six. *A search converging on
  a finite space does not do that*; the key was enumerating action SEQUENCES. `s2` masked row 63 on my
  HUD-ticker theory → **4,263 KEYS vs 4,263 raw boards, mask changed nothing, refuted.** `s3` found it:
  pressing the same verb twice and intersecting the deltas gives **181 cells changing on BOTH, bbox
  (0,12)-(62,14), colour 9** — **a full-width 3-row band advancing every action**, the "moving comb"
  the level's own notes name when explaining colour 4. Free facts: **actions 3, 4 and 7 change NOTHING
  from the L5 entry**; action 1 moves 318 cells, action 2 moves 345 (and introduces colour 4), action 5
  moves 36. Next key: `(board with the comb's rows masked, comb phase)` — or `(masked board, depth mod
  period)` if the comb advances with the action count. An agent is running it.
  *Two failed searches whose useful output was a growth CURVE. A search that will not converge is
  telling you about your key, and straight-line growth at full branching means "every child is novel",
  which is a statement about the state function and not about the game.*
  **UPDATE — a search with a phase-aware key reports EXHAUSTED at 21 states, 0 divergence, no win.
  ⚠️ HELD, NOT BANKED.** Solid parts: **the comb steps 3 rows per real press, has 21 phases, and
  CLAMPS rather than wrapping** (a press at phase 0 or 60 is itself blocked); **it does not advance on
  blocked presses** (action 3 x60 → 0 diffs); a **second HUD counter at COLUMN 63** was found by
  round-trip validation, twin of the row-63 one; and a false lead was killed inside the round (colour
  11's count dropping 1 per press looked like the band eroding a target — the target blob, 207 cells,
  never changes; it was the column-63 tick). Key validation: 0 divergence over 21x6, and **21 keys
  against 80 raw boards** so the mask is not over-collapsing.
  **But 21 is exactly the band's phase count** — i.e. nothing else changes anywhere in the graph — and
  that contradicts the standing numbers (W 441 positions, S 289). **Main-thread check `ar25_v1.py` does
  not refute it**: raw centroids over 12 presses of each verb show actions 3/4/7 move nothing, colour
  10's apparent motion is PAINT (count 288→328 for *both* action 1 and 2, centroids opposite), colour
  11's is the column-63 HUD, and **no compact colour translates rigidly**. Unreconciled: **colour 5 has
  exactly 151 cells** and the old note reads *"the joint (W row x S phase) surface maxes at 99/151"* —
  so colour 5 is very likely what every earlier round was measuring, and it was **never seen to move**;
  and A5 (the click alias) is inside the action set, so selection should have been reachable and should
  have grown the graph. Being settled: identify W and S on **level 4** where `L4_LINE` demonstrably
  moves them, check whether that colour sits in the band rows the key zeroes, and test whether A5
  changes any arrow's subsequent effect on L5 at all.
  *An exhaustion proof is only as good as the claim that its key preserves every mobile object, and
  "mask keeps signal" proves SOME signal survives — never that the PIECE does. What made this
  suspicious was not an error in the output: it was 21 matching another 21 that had no reason to be
  the same number.*
  **RESOLVED — the 21-state proof is RETRACTED, and the reason is the session's biggest lesson.** The
  key could not see a **board-invisible SELECTION state**: A5 runs a strict **period-3 cycle in the raw
  press count** — `n mod 3 == 0` arrows drive the **band**, `== 1` **nothing moves**, `== 2` arrows
  drive the **piece** by 3px with the band held. Selection survives an intervening non-A5 action, so it
  is HISTORY, not board state, and no board-derived key could represent it. **The piece is colour 5**,
  identified properly by driving `L4_LINE` on level 4 (a 48-cell colour-5 component translating rigidly
  3px) and matched at L5 to an **88-cell blob at rows 36-50, cols 42-56**; it becomes selectable exactly
  at `sel_phase == 2`, matching `A5x2 = click(S)`, so **colour 5 = S**. W was never found as a separate
  object — the standing hypothesis (flagged as such) is that **W is the band**, whose 21 phases match
  the 21 in "441 = 21x21".
  ⚠️ **Why every control passed anyway: the `seen`-set collision dropped the node BEFORE its successors
  were computed, so the divergence counter never got the chance to fire.** A divergence check
  downstream of a dedup cannot detect a merging key — **zero divergence under a merging key is the
  merge working.** The identical shape hit sp80 the same day under a completely different key. **A
  search cannot audit its own state function from the inside**; what caught both was external — a
  positive control on a win already possessed, and a challenge to a number that matched another for no
  reason. Now in `CLAUDE.md`'s traps.
  **Corrected key** = board (colour-0 dashes and colour-10 wall undone, deliberately NOT row-windowed
  since a windowed mask erases the piece whenever it sits in the band's rows; HUD row and column
  zeroed) **+ `band_phase` + `sel_phase`** carried like depth. Validated by the two assertions that
  matter: `selected-then-action1` != `unselected-action1`, and `A5x3-then-action1` == `unselected-
  action1`. Re-run: **5,396 nodes, 6,712 keys vs 18,022 raw boards, frontier 1,316, 0 divergence, no
  win, NOT exhausted** — budget-bound, not stuck.
  **UPDATE — SEVEN chained runs later the POSITION MODEL IS REFUTED, by a factor of two.** 28,627
  expanded, **34,909 distinct keys against a model predicting 18,207** (289 x 21 x 3), frontier 6,282
  and **growing in every one of the seven runs** (+1,224, +985, +955, +588, +678, +746 — a BFS past its
  widest shell shrinks, and that never started). Rate stable 8-9 nodes/s; **divergence 0, deaths 0**
  across all 28,627 expansions; C1, C2 and both `sel_phase` identities re-verified fresh every process.
  ⚠️ **The gate I wrote would NOT have fired** — I set `MODEL_REFUTED` as "keys past ~36,000 **and**
  ratio >= 1.2", and by run 7 the ratio had drifted to 1.16 with keys 1,091 short of a threshold picked
  by eye. *A compound gate fires on its weakest clause, so every extra condition is another way for a
  true verdict to be withheld — and the clause that withholds it looks like diligence.* Second stop
  rule I have gotten wrong on this game in two rounds.
  **The missing state is almost certainly the MIRROR.** The game's mechanic is *player and MIRROR move
  in lockstep, vertical the same and horizontal opposite*, and only ONE movable object has ever been
  found on L5. A derived mirror adds no state and the model would fit; it does not fit. If the lockstep
  **BREAKS** (one of the pair blocked by a wall while the other is not) the state is a PAIR and the
  space is ~(piece x mirror x band x sel) = **millions, not BFS-exhaustible at all** — which would mean
  L5 needs a hand solve or a goal-directed search, not this one. Being tested now by locating both
  objects on level 4 (where `L4_LINE` moves them) and trying to decouple them against a wall.
  Operational: the checkpoint is **690 MB** and grows linearly with keys; the BFS is not being resumed
  while that question is open.
  **FINAL — BFS IS THE WRONG INSTRUMENT FOR L5. Do not resume it.** Six more chained runs from the main
  thread (`ar25_run_to_exhaust.py`): **56,701 expanded, 66,325 keys, frontier 9,624**, 340,207 raw
  boards, deaths 0 and divergence 0 throughout (the key stayed sound the whole way). **The +633 → +382
  "deceleration" that justified the run was NOISE from two points** — across six runs the frontier delta
  is flat and jittery (+270, +525, +222, +383, +363), no downward trend at all. Keys are **90% past**
  the corrected model's 34,902, itself the second refuted estimate. *The space is larger than every
  estimate produced for it.* L5 needs a **hand solve or a goal-directed search**, not completeness.
  The loop's own stop rule — *stop if three consecutive runs fail to decelerate* — is what ended it, and
  it saved ~70 minutes of futile compute. **Encoding "two data points are not a trend" as a CONDITION IN
  THE SCRIPT rather than as an intention is the transferable part**, on a day when two
  order-of-magnitude extrapolations (sp80's 40-55k nodes, ar25's 554 positions) were each quoted with
  their caveats and then spent as if they were midpoints. *A caveat only protects you if it is
  executable.* Checkpoint left intact at 56,701 expanded.
- **ar25 L5's CLICK space is closed** — +114,688 click-then-ACT arms across four INTERIOR configurations, bringing
  the level to **13 distinct non-entry configurations plus entry, zero wins**. A5 was verified to be a
  byte-identical alias for the click (not assumed), and the one new component found in an interior
  config turned out to be the known deselect mechanic relocated with W's body. Named gaps, honestly:
  only 2 points of the 441x289 joint interior were sampled, both in one quadrant; a truly ALTERNATING
  W/S interleave inside one life was never run; the reverse selection order was not tried.
- **sp80: L2 already falls in the shipped agent** (`L2_LINE`, 7 actions — see the ⚠️ under §GATE for
  how a stale block sent an agent at it anyway). **L3's multi-life hypothesis is closed for a reason**:
  nothing persists across an L3 death (byte-identical reset, with a 34-cell pre-death diff as the
  positive control), so chaining lives is provably equivalent to restarting the same single-life
  search. The BFS wall reproduced independently (5,778 expanded, frontier still growing, not
  exhausted). Untested levers: **block-relative offsets** and **block2-as-final-actor**.
- **tr87 L3: both named-open directions are dead.** The 343-triple has no board-native structure to
  brute-force, and "an unframed display exists" is refuted by **exhaustive pixel accounting — all
  4,096 cells classified, zero unaccounted**. The one unframed candidate tracks the clamp 1:1, so it
  is a cursor. `tr87_q80.py`'s reader fix still correct, still inert, still unlanded.

- **g50t level 1 is PROVEN unwinnable — the campaign's first closure by EXHAUSTION** (`g50t_r1.py`,
  `g50t_r2.py`). Real-engine BFS on deepcopy nodes: **1,854 distinct boards, frontier 0**, 110s of a
  900s budget, **zero hidden-state divergence** over all 9,270 (board, action) pairs, and a deepcopy
  fidelity control passing in the same run. The action set is COMPLETE — g50t has no click at all —
  so nothing is missing from the sweep the way click edges were missing from sp80's early BFS. The
  40 dropped GAME_OVER children were then justified rather than assumed: a death reverts to L1 entry
  (arm A 0, arm B pre-death **51** cells then 0). **g50t is 0/7 and stays 0/7; spend no more rounds
  on it.**
  ⚠️ **QUALIFIED an hour later by `framestack.py`, and the qualification is mine to state:** g50t's
  actions 2 and 4 return a **7-plane** frame stack, and the search — like every reader in this repo —
  keyed on `f[-1]`. So it is a proof over END-STATE boards, resting on two assumptions now written
  down instead of assumed: that `f[-1]` is the true post-action state (it is what the engine settles
  to, and sb26 is cleared 8/8 while returning 42 planes, so reading the last plane is sound for play),
  and that the board carries the whole state (evidence: 1,854 distinct boards, zero divergence over
  9,270 pairs). Win detection is unaffected — wins come from `levels_completed`, never from a frame.
  The claim stands; it is a proof about end states, not about animations.
- **bp35 L2's closure now holds for a reason** (`bp35_r1.py`). Its "one ride per life, doors 4-5 rides
  away" argument rested on an asserted "board reverts"; measured, arm A 0/0 and arm B **8 cells then
  0**, control fired. Nothing persists, so chaining lives is equivalent to restarting one. bp35 is the
  one game that cannot be deepcopy'd at all (its code recurses infinitely), and a die-and-compare
  needs no deepcopy — which is why this question was answerable there and a BFS is not.

- **EIGHT of seventeen games return a MULTI-PLANE frame and the whole repo reads only `f[-1]`**
  (`framestack.py` → `results/framestack.txt`). sb26 **42** planes on its run action, sp80 **22** on
  its fire, **sc25 22 on all four of its verbs**, cd82 15, tu93 8, g50t 7, bp35 5, sk48 2; the other
  nine are single-plane. **Sound for play** (sb26 is cleared 8/8 through 42-plane frames; wins come
  from `levels_completed`) and a **keyhole for discovery** — any probe that pressed once and concluded
  "that action did nothing" measured the END of an animation. On **sc25** the first press of any verb
  animates `9 → 18 → 27 → 36` changed cells and snaps back to entry, so it reads as a no-op; that is
  why my own `sc25_r1.py` "exhausted" its keyboard graph at **one node** (verdict VOID, file kept as a
  worked example). **ANSWERED**: the animation is a title-screen **flourish** — four of box B's own
  9-cell edge blocks flashing colour 0 → 14 cumulatively, then snapping back — byte-identical across
  all four verbs AND the click, and its 36-cell peak is **exactly 4 of the flood fill's own 22
  components**, so the 22/22 was explained rather than a missed structure. **The trigger is
  action-index 1 of the life — absorbed regardless of type, verb or click — with everything from
  index 2 onward committing normally.** ⚠️ I first recorded the trigger as "the board equals the
  level's entry frame" and that was **WRONG**; the separating arm is a verb at index 1 (absorbed) then
  a click on a real target at index 2, which commits immediately even though the board is still
  entry-equal. The two rules had been observationally identical because index-1 and entry-equality
  coincided in every arm run until one was built to make them disagree.
  ✅ **sc25 is CLOSED and retired — 0 of 479 transitions affected.** `sc25_q16.py` fires a plain-verb
  **warmup press immediately after every reset**, before any click, so the life's one absorption slot
  is always consumed and no click in the file is ever action-index 1. Confirmed independently against
  the historical run's own artifact: `results/sc25-q16.txt` has **zero `MISMATCH` lines** across all
  13 rebuilds and finishes `patterns_visited=480/480`. *The safety was accidental* — nothing knew
  about an absorption rule discovered today — so a NEW sc25 probe will not have it unless someone puts
  it there deliberately.
- **cd82 L3 survives a stronger instrument**: the roller's tumble graph is EXHAUSTIVE at **8 states**
  keyed on the full pixel mask (not bbox), so there is no hidden face and **order can never matter**;
  every state paints the same 50/55 wedge. New fact: cd82 L3 also runs a **100-action life budget**
  and `reset()` keeps `levels_completed=2` with a byte-identical board — the same shape and the same
  number as wa30 L3, measured the same day on a different game.
- **sp80 L3 — ⚠️ the offset re-key's "exhausted, no win" is a SUSPECTED FALSE NEGATIVE.** It keyed on
  (offsets to the 3 castles, ammo, driver identity), collapsed the space ~10x and drained its frontier
  (1,860 states, 145s) where the board-keyed search never did. **The collapse was real; the exhaustion
  was not.** That key **omits the other three bodies' absolute positions**, and any of them can have
  been driven and moved earlier — so different boards **ALIAS to the same key**. Proven live by a
  positive control: blind BFS for level 2's *known* 7-action win reported **full exhaustion at depth 7
  with NO win** under the offset key, while a scripted replay of that exact line through the identical
  transition code succeeded at every step; re-keying on the **absolute positions of all four bodies**
  made the blind BFS find it. *A key that omits part of the mutable state does not lose states, it
  MERGES them — and a merged search reports EXHAUSTION, the most confident possible negative, while
  pruning the answer. Only a positive control on a win you already possess can catch that.*
  **The occlusion subgraph is now RECOVERED, 2,972 of 2,987**: non-driven bodies provably never move,
  and a covered body's bbox shrinks from the covered side / vanishes at full overlap / reappears on
  separation, while the driver's own blob is never occluded — so stop re-reading them, bootstrap each
  position once and carry it forward, resolving transfers by matching the post-action colour-9 position
  against the four stored ones. **The 330 `multimove` cases were never real** — in all 8 sampled, a
  *static* body's reported x0 shifted one lattice step perpendicular, exactly the partial-occlusion
  pixel effect. With the sound key and the recovered subgraph: **25,644 states, frontier 17,723 and
  still growing, no win** — ⚠️ **and that number is now DEAD too, for a second instrument reason.**
  **The search treated FIRE (action 5) as pure movement** on a game whose own model says FIRE can
  **TRANSFER control** — so every real FIRE-transfer silently corrupted the tracked state **and flagged
  nothing**. Fixed to resolve like CLICK (match post-action colour-9 against all four stored positions):
  **0 `transfer_no_match` anomalies in 5,124 expansions**, so the 15 unexplained cases were fallout,
  not a third mechanism. The 25,644-state run was measuring a **different transition function** — do
  not quote it. The `transfer_multi_match` fork is real and small: opposite tie-breaks give **3,704
  states in common, 12 only in A, 1 only in B** (~0.35%), so that caveat does not dissolve, though
  neither run exhausted so part may be BFS-order noise.
  **FINAL for this session — a 2h main-thread run REFUTES the exhaustion estimate** (`sp80_s10.py` =
  `s9` with `TIME_BUDGET_S` 7200): **72,684 expanded, 192,247 states, frontier 118,643 and STILL
  GROWING, 10.09 nodes/s, replay 19.5% of wall-clock, exhausted=False, no win.** The priced figure was
  40-55k nodes ≈ 1-1.7h; at 72,684 the frontier is climbing by ~2,683 per 2,000. Re-derived from the
  real tail: new-states-per-node runs 2.585 → 2.341, falling ~0.06 per 2,000-node window, and the
  frontier only stops growing when it reaches **1.0** — ~90,000 more nodes just to peak, so a realistic
  total is **300,000-500,000 expanded ≈ 8-14 hours**. *An order-of-magnitude range quoted WITH its own
  caveat still gets spent as if it were the midpoint — I sized a 2-hour run from it. Size from the
  pessimistic end, or run until the RATIO crosses a threshold rather than until a predicted node count.*
  Strong confirmations at scale: **`transfer_no_match` 0 and `driver_blob_count` 0 across 72k
  expansions** (the FIRE fix holds), and all four driver ids reached and fired from (18,390 / 19,493 /
  14,890 / 19,353), so "a specific body fires last" stays refuted. ⚠️ **But `transfer_multi_match` is
  now 3,730 with 2,254 having the driver id NOT among the matches** — the tie-break heuristic is
  load-bearing at a scale the earlier 12-vs-1 fork no longer bounds. **Resolve that before any future
  null on this level means anything**, and add checkpointing (s9/s10 restart from the L3 root each call).
  **The property worth carrying off this game: every wrong version of this search still runs to
  completion and still reports a number.** A merged key reports EXHAUSTED; a corrupted transition
  reports states and a frontier. Neither errors, stalls, or produces a shape a reader would question.
  The only two things that have ever caught them are **a positive control on a win already possessed**
  and **reading the transition code against the game's own documented model**.

- **ka59 L2: THE MOAT IS CROSSED — the one level that moved from "closed" to "live" today.** The
  closure ("moat min thickness 9, no 3-step crossing") argued about WALKING, and this game's click is
  a teleporting swap. Found: a **KICK** — walking into a dot from certain angles launches it a fixed
  distance, **permeable to the moat**. dot0 at x=34 kicks west to **x=19, past the far edge at 21**;
  clicking the relocated dot teleports the piece across. **box0 and box1, previously "unreachable
  under every possible sequence", are proven reachable and were both filled.** The life ended at ~138
  actions with box2/box3 unconfirmed.
  **UPDATE — the budget diagnosis was refuted by its own fix.** An exact 3-lattice BFS router reached
  dot0's kicking region in **3 actions where the greedy walker took 50 and missed**, and the whole
  line — kick dot0, kick dot1, fill box3, cross, fill box0, return — costs **36 actions of a ~127
  clock, >90 to spare**. `levels_completed` stayed at 1 through both fills, so **two boxes is not the
  win**. Death re-measured here with the kick as a positive control: `reset()` returns the board
  **byte-for-byte** to L2 entry, so the line must fit in one life.
  **The real wall is a SECOND, INTERNAL moat**: a colour-15 band **6 rows thick (y=24-29, full width
  x=0-21)** splitting box1 (y=8-15) from box0 (y=41-48). Kicks tested so far do not cross it.
  **Kick geometry is now aimable and the flight distance is NOT a constant** — dot0 from due east goes
  **west −15**, dot1 from due east goes **west −24**, dot1 from the south goes only **−3**, and dot2
  from the same relative approach goes **east**. Direction is a property of the APPROACH, not of the
  button. (The earlier "dot1 cannot cross, 41−15=26" arithmetic was wrong exactly as flagged.)
  **UPDATE 2 — THE PHASE LAW, and it is the most useful thing this game has produced.** box2 was never
  obstructed: a flood fill from (44,48) **converged at 88 cells** (so not a node cap) with box2 absent,
  and the arithmetic settled it — (44,48) mod 3 = (2,0) while box2's interior is (1,1) = **spawn's own
  phase**. *Movement changes one axis by a multiple of 3 per press, so `(x mod 3, y mod 3)` is
  INVARIANT under walking, and the only phase-changing verb is the CLICK.* **The ORDER of clicks is
  therefore part of the solution** — the third game after ar25 L3/L4 where that is the whole puzzle.
  **box1 is REQUIRED, measured**: box2 visited + box3 filled + box0 filled + box1 empty → still
  `NOT_FINISHED` at action 45. **A CHAINED kick crosses the internal band**: dot1 kicked west to
  (17,34) is still active, and approached from the south there it kicks again to **(17,19)**, past
  y=24. Flight is **slide-until-blocked**, not a fixed distance (−3 to −24 measured).
  **UPDATE 3 — the full line ASSEMBLES in 45 actions, and phase is a KNOB, not an obstacle.** One life:
  box2 visited at spawn phase (17) → dot0 and dot1 both kicked west (35) → box3 filled by dot0 with a
  **free crossing**, the click made from inside box3 (41) → dot1 **chain-kicked north** (17,34) →
  (17,19), clearing the internal band (44) → dot1 clicked, piece crosses to (18,19) free (45). Of
  ~127. Flood fill from (19,38) converged at **70 cells** with box1 absent — again not a budget.
  **Third phase mismatch, and the three are one mechanic:** *the click swaps the piece onto the clicked
  dot's canonical cell, so the piece's post-crossing PHASE is a property of where the DOT is — and the
  dot's position is set by the KICK.* Phase is therefore set BEFORE clicking, by choosing where to kick
  the dot. That turns "find a route to box1" into "which reachable dot landing has a canonical cell of
  phase (1,2)?" — an **enumeration**, not a search. dot1's two westward flights (−24 from one region,
  −3 from another) are direct evidence the approach row is a real degree of freedom.
  ⚠️ **The canonical cell is NOT always the dot's own coordinate** — dot at (17,19), piece landed at
  **(18,19)**. Phase arithmetic must use the cell the PIECE lands on, measured.
  **UPDATE 4 — the knob WORKS, and it is a CONSERVATION LAW.** dot0's west kick lands at **(19,44),
  phase (1,2)** = box1's own phase; chain-kicking it north **preserves that phase**, because kick
  distances are multiples of 3 exactly like walking. Clicking it put the piece at **(19,20), phase
  (1,2), confirmed live**, and box1 opened at once — reached (10,14) at action 59 after two flood
  fills had called it unreachable. *So each dot has a FIXED phase-class it can deliver, decided at its
  spawn, and the kick only chooses where along that class it lands* — which constrains the dot→box
  assignment before any planning starts.
  **⚠️ AND "FILL ALL FOUR BOXES" IS FALSIFIED, not merely unconfirmed.** Three arms in one life: box1
  visited empty-handed → `NOT_FINISHED` (59); box1 with a dot placed → `NOT_FINISHED` (60); full
  zero-waste assembly with box2 visited, dot1→box3, dot0→box0, dot2→box1 and **no dot spent as bare
  ferry fare** → **`NOT_FINISHED` at 64** of ~127. Budget is emphatically not the wall.
  Leading hypothesis, never run: **the pairing is SIZE-MATCHED.** The zero-waste routing produced
  dot0→box0 and dot2→box1 — the **reverse** of the recon's ring-size guess (dot0↔box1, dot2↔box0). If
  the level pairs by an observable property, every line so far has put the right number of dots in the
  wrong boxes, which reads from outside exactly as it does. Being chased: measure what distinguishes
  the dots and the boxes at all, check whether the matched assignment is even phase-FEASIBLE from the
  table before spending actions, then the remaining permutations. Plus two non-pairing questions —
  whether the PIECE must END somewhere (r20 left it at (44,48)) and **whether box2 needs a DOT rather
  than the visit it has always been given**; box2 is the one target only ever *visited*, and the one
  that forced the whole spawn-phase-first ordering.
  Gap: **dot2's kick geometry has never been cleanly measured** — only dot0 and dot1 have kick+chain
  data, and dot2 is the dot a matched pairing may need to move.
  **UPDATE 5 — the SIZE-MATCHED PAIRING IS MEASURED FACT, and box2 matches the PIECE.** Each dot's
  footprint is tiny but sits in a **colour-14 HALO** whose bbox matches one box's interior exactly,
  one-to-one, no dot matching two: **dot0 3x6 ↔ box1** · **dot1 6x3 ↔ box3** · **dot2 6x6 ↔ box0** ·
  and **box2's interior is 3x3 = the PIECE itself**. That fourth row answers the loose end: box2 is
  the piece's own station, so **the piece almost certainly has to END there** — every run so far left
  it wherever the last click dropped it. Running the matched pairing (box3←dot1, box0←dot2, box1
  visited only) still gave `NOT_FINISHED` at 64 actions.
  ⚠️ **The reported 4-demands-vs-3-dots deadlock rests on an unmeasured premise** — that a dot clicked
  onto open floor is SPENT. If a dot is consumed only when it lands in a BOX, an open-floor click
  merely RELOCATES it, it stays clickable, and there is no deadlock at all (cross via dot0, walk into
  box1, click dot0 again from inside). The round's own data leans that way: dot1 was chain-kicked from
  its new position while described as active and unconsumed, and **clicks have no proximity
  requirement**, so only the PIECE needs to be in the box. One arm settles it and is running. If dots
  really are one-click-only, the named escape is a **third kick** — dot0 sits at (19,20)/(19,21) and a
  third kick west might land it *inside* box1's interior (x9-11), making one click both cross the
  piece and place dot0 correctly. Every chain so far stopped at two deep only because nobody tried.
  *A resource-counting impossibility argument is only as good as its consumption rule, and consumption
  rules are exactly the premise that gets asserted in passing while the arithmetic gets the scrutiny.*
  **UPDATE 6 — the consumption rule was RIGHT and my doubt was wrong: dots are ONE-CLICK-ONLY.** Clicked
  a dot, walked one step off, clicked the identical coordinate again — piece did not move, no dot cells
  changed. **But the ACCOUNTING double-counts.** Clicking a dot *while standing inside a box* fills that
  box AND teleports the piece to the dot — a trick `r14`/`r20` used and then stopped using. So it is not
  4 demands against 3 dots; it is **3 dots → 3 clicks → 3 boxes filled AND 3 crossings**, exactly
  enough, and the problem is SEQUENCING not shortage. The plan being run: pre-kick every dot while the
  piece is still on the right side, then box3←dot1 (piece lands past the main moat), box0←dot2
  (pre-kicked north of the internal band on phase (1,2), which a chained north kick preserves),
  box1←dot0 (pre-kicked toward box2, where the piece should end).
  **A COMPOUND SWEEP is the enabler and was left untested**: one westward press near dot2, on a route
  deliberately avoiding dot0, relocated **both** — dot0 (34,44)→**(13,44)** and dot2 (44,47)→**(17,47)**,
  both past the moat. Seen three times now across independent branches, so not an approach artifact.
  Two dots pre-positioned per approach is exactly what the sequencing plan needs.
  The third-kick escape is **dead and circular**: reaching east of dot0's chained position requires
  already being north of the internal band, which is the crossing dot0 was meant to provide.
  Still untested after five rounds: **does box2 need a DOT or only a VISIT** (under this plan it is
  where the piece ends, so a visit is what it gets).
  *An impossibility argument built on counting needs a consumption rule AND a correct account of what
  each expenditure BUYS. Here the consumption rule was right and I doubted it; the accounting was wrong
  and nobody checked it — because a click that does two jobs looks like one job in a ledger.*
  **UPDATE 7 — THE MODEL IS WRONG, and here are the five premises that prove it.** (1) box1's interior
  is walkable **only from phase (1,2)** — two bounded, converged flood fills (70 cells from (19,38), 88
  from (44,48)), both excluding it. (2) Each dot's click-phase is **fixed by identity**: dot0 (1,2),
  dot1 (0,1), dot2 (2,0). (3) **Kicks preserve phase** (flights are multiples of 3). (4) **Dots are
  one-click-only.** (5) The halo↔interior match is exact and one-to-one, dot0↔box1.
  → the only click that puts the piece INTO box1 is a click on dot0; that click spends dot0; and box1's
  correct occupant IS dot0. **Box1 can never be correctly filled under the measured model.** Meanwhile
  the fill-permutation space is **exhausted** — box3 matched + box1 visited (59) · box3 matched + box1
  mismatched (60) · box3 + box0 matched, box1 visited (64) · **all three boxes filled, only box3
  correct (64)** — so a pure "N dots placed" count is refuted too. Something in the model is wrong, and
  re-sequencing inside it cannot find what. **Same place re86 L6 reached.**
  **The unswept surface, and it is the obvious candidate: every click in this game's history has been
  aimed at a DOT, and level 2 has never had a click sweep at all.** The whole model is built from those
  clicks. The structures it treats as scenery are exactly the ones carrying its information — box
  interiors and frames, the **colour-14 HALOS** (which carry the size-matching and have never once been
  clicked), the moat columns, the internal band, box2 itself. Being swept click-then-ACT now, together
  with the three-rounds-flagged **does box2 need a DOT or a VISIT** (if a dot: four boxes need four
  dots against three, falsifying the model outright).
  **Open and uninterpreted: the COMPOUND SWEEP** — one westward press near dot2 relocates dot0 too,
  reproducibly, on routes built to avoid dot0 (`r7`, `r9`, `r25`). Set aside as moot for the phase plan;
  *an unexplained mechanic on a board whose model is known to be wrong is not a detail to leave lying.*
  **FINAL — ka59 L2 is CLOSED, STRUCTURAL, and the useful output is which premise to attack.** The
  non-dot click sweep (19 candidates, click-then-ACT) found **nothing**: box frames, box interiors,
  moat columns and the internal band are click-inert, and all six colour-14 halo cells "responded" only
  because clicking **(33,42)** — one cell outside dot0's footprint — lands the piece on dot0's own
  canonical cell **(34,44)**, i.e. the known swap re-firing through its proximity tolerance. *A response
  is not a new mechanism until you check whether the old one explains it.* And **box2 wins nothing
  either way** — dot placed inside, `levels_completed` still 1, closing a question flagged three rounds.
  **ATTACK ORDER for a future session — do not re-derive the board:** premise **2 or 3** first (a dot's
  phase fixed for life / every kick preserving mod 3) — **one counter-example collapses the whole
  deadlock**, because the click-does-two-jobs plan otherwise writes itself from the halo tables; then
  premise **1** (only two flood fills ever ran, both from origins dot0 or its chain produced, so a fill
  from a genuinely different phase is untried). Premises **4 and 5 are the most solidly measured** and
  the least likely to be wrong. **The compound sweep is exactly where a premise-2/3 counter-example
  would live** — it is the one mechanic on this board that moves a dot by means nobody has characterised.
  Also unswept: the click sweep was 19 hand-picked cells not 4,096; the halo's full extent beyond two
  corners; and "one-click-only" was measured for an open-floor click and *assumed* for a box-placed one.
  **UPDATE 8 — THE WHOLE LEVEL IS NOW ONE MAP, and a win candidate falls out of it**
  (`ka59_x2/x3/x4.py`, all controls passing). The walk graph splits into **27 PHASE-PURE connected
  components** in three regions: **RIGHT** = 18-26 (the piece starts at **22**, and **box3** and
  **box2** are here), **LEFT-TOP** = 0,1,2,6,7,8,12,13,14 (**box1**), **LEFT-BOTTOM** =
  3,4,5,9,10,11,15,16,17 (**box0**). Each box interior spans all nine phases of its own region, so
  standing in a box is a question about REGION, not phase. **Without a kick the piece can never leave
  the RIGHT region** — which is why the kick is required, not a shortcut.
  **Premise 1 is now STRUCTURAL rather than empirical**: components are phase-pure, box1's centre
  (10,11) is phase (1,2), so box1 is reachable only from phase (1,2) by construction. Sharper still:
  **box3 sits on the SAME side of both barriers as the piece and is still unreachable** (component 25
  vs 22) — the lattice partitions the board even where no wall does.
  **Mapping the 13 measured kick landings onto the components** (each verified phase-preserving):
  dot0 → {LEFT-BOTTOM, RIGHT} · **dot1 → {LEFT-BOTTOM, LEFT-TOP, RIGHT}** · dot2 → {LEFT-BOTTOM, RIGHT}.
  **dot1 is the ONLY dot measured reaching LEFT-TOP**, via the chained kick (41,34)→(17,34)→(17,19).
  **The candidate line, satisfiable with no new search** — pre-kick dot1 west then north to (17,19),
  dot0 west to (19,44), leave dot2 on the right; then box3 ← click dot0 (fills + crosses to
  LEFT-BOTTOM), box0 ← click dot1 (fills + crosses to LEFT-TOP), box1 ← click dot2 (fills; proximity is
  irrelevant, and the piece is thrown back RIGHT), then walk into box2 and stop.
  ⚠️ **It violates the size-match pairing on all three — deliberately, because the matched pairing is
  UNREACHABLE under every measured kick** (it needs the piece to arrive in LEFT-TOP by clicking dot2,
  and only dot1 has ever reached LEFT-TOP). If the line wins, the pairing was never required and
  `r20`'s all-three-filled failure is explained by **its piece ending at (44,48) instead of box2** —
  *no experiment here has ever controlled the fill set and the final position at once.* If it loses
  with all four satisfied, the pairing is real and the next question is already sharp: **can dot0 or
  dot2 chain a second kick north** from their LEFT-BOTTOM landing? Only dot1's chain was ever tried.
  **RESULT — ALL THREE BOXES FILLED IN ONE LIFE, AND IT STILL DOES NOT WIN** (`ka59_y1/y2.py`). The
  first drive failed because I assigned dot1 to carry the piece into box1 and **dot1's canonical phase
  is (0,1)** — premise 2 reconfirmed by execution rather than argument. Reassigned so **dot0 CARRIES
  and is never the cargo**, and it worked exactly as reasoned: box3←dot1 (crossed), dot0 chain-kicked
  north to (19,20), box0←dot0 landing the piece at **phase (1,2)**, and **box1 opened by a straight
  route with no search** after two earlier rounds called it unreachable. box1←dot2. **All three filled,
  54 of the ~127 clock, `levels_completed` never left 1, zero compound-sweep side effects.**
  ⚠️ **Then a STRUCTURAL wall at the last step, deduced not searched:** box2 is component 22, phase
  **(1,1)** — the piece's spawn phase. Walking preserves phase; only a click changes it, to that dot's
  fixed canonical phase (dot0→(1,2), dot1→(0,1), dot2→(2,0), zero exceptions in 156 arms). **None is
  (1,1)**, so once three dots are spent the piece can NEVER return to box2 — for all six assignments.
  `r20` corroborates: it also ended at (44,48).
  **So the FILL MODEL is exhausted, not unsolved**: box2-first + three filled (`r20`) → no win · three
  filled without box2 (`y2`) → no win · the matched pairing → **structurally impossible** (box1 needs
  phase (1,2), only dot0 delivers it, box1 must be filled BY dot0, dots are one-click-only). *"Fill the
  boxes, visit box2" is not the win condition in any arrangement* — the same place re86 L6 reached.
  **Now sweeping the one untouched surface**: every click in this game's history was aimed at a DOT,
  and the whole model is built from those. A real click-then-ACT sweep on a 3-cell lattice (~450
  candidates) is running over the colour-14 halos in full, box interiors and frames, the moat and the
  internal band, and **box2 itself** — never filled, matches the PIECE rather than any dot, and
  unreachable after any complete fill line.
  ✅ **Verified in the main thread** (`ka59_v1.py`): the moat's geometry was re-derived rather than
  relayed — columns **x=21..29 hold 64 non-background cells each, the full board height**, while
  x=15..20 hold 7 and x=30+ hold 31-37, so the nine-column thickness the closure claimed is real.
  Against that measured boundary the piece goes x=37 → x=19 → x=7. **The closure's arithmetic was
  never wrong; it was answering "can the piece WALK across nine columns", and that answer is still
  no.** A closure is scoped to the verbs its author knew about, and that scope is invisible in the
  sentence it is written as.
- **cn04: colour3 is the WRONG-ANSWER signature.** The true L1 win renders **no dock overlay at all**
  — the board jumps straight to the L2 layout — while colour3 appears only in the FALSE dock. Every
  L2 round has been ranking candidates by a counter of wrong answers. The pad-ASSIGNMENT axis I then
  proposed was **refuted on L1 in one arm and for a structural reason**: with two landmark points
  under a pure translation the two pairings are negatives of each other, so at most one is ever
  self-consistent — it is a derived fact of rotation, not a second dimension. cn04 L2 rests at 191
  live-driven placements across eight criteria.
- **The discarded planes were opened, and the finding NARROWS** (`planes_r1.py`): sk48, bp35, cd82,
  g50t and sp80 all animate MONOTONICALLY to a settled end state, so `f[-1]` loses only the rendering.
  **sc25 alone is non-monotone** (returns to entry), so it alone has a conclusion at risk. Two
  specific worries retired: cd82's paint never dips below 50 cells in any intermediate plane (its L3
  impossibility premise holds), and g50t's action-2 planes rise monotonically 0 → 48 with an identical
  colour histogram throughout (pure movement), so `g50t_r1.py` keyed on the settled state.

**A move worth reusing, which produced three results today:** *when a level is closed by an argument,
find the clause in it that is a claim about the WORLD rather than about arithmetic, and measure that
one clause.* On sp80 L3, bp35 L2 and g50t L1 the clause was the same — "the board reverts" — and all
three held. On g50t it was not even in the original closure: it was an assumption introduced by MY
search when it dropped death children, which is the kind nobody audits because nobody wrote it down.

**The instrument lesson of the day, and it cost three probes before a control caught each one:** on
wa30 I measured the same quantity three times and was wrong three different ways — reading a census
through the PREVIOUS level's cached rectangle (a driver's geometry belongs to the last level it RAN
on, and the tell was `inner=2` in a frame whose interior held no colour 2), counting cells with the
piece standing on them (caught by a step of **-12**: consumption cannot restore a cell), and
accumulating a "gone" set with no upper bound (caught by **92 of a possible 84**). *A monotonicity
check and a bound check are different instruments, and the bound is the cheap one.*

## STATE AT 2026-08-15 21:15 (still valid)

**THE TREE IS FULLY GATED — nothing is ungated. Standing: 15/17 games with a level, mean 22.441%.**
Four sweeps landed today, each with `sweep_diff.py <before> <after> <control>` and a control that
DIFFERS, 16 of 17 games identical to the digit every time, and no game ever losing a level:
- wave-8 → `haul.py`'s three wa30 L2 guards: **wa30 1/9 → 2/9**, 20.709% → 20.970%
- wave-9 → `mirror.py` L2_LINE: **ar25 1/8 → 2/8**, → 21.297%
- wave-10 → `mirror.py` L3_LINE: **ar25 2/8 → 3/8**, → 21.787%
- wave-11 → `mirror.py` L4_LINE: **ar25 3/8 → 4/8** `[15, 25, 40, 29]`, → **22.441%**

**ar25 went 1/8 → 4/8 in one day (2.778% → 27.778%)**, and the reason generalises — see
`breadth-recon.md` §"ar25 LEVEL 3 FALLS" and §"ar25 LEVEL 4 FALLS": *a win can depend on a control
surface that engaging the puzzle's own pieces locks you out of, so the ORDER of engagement is part
of the solution.* L3's peg selection is a one-way door (the piston's row must be set first); L4's
piston click permanently forfeits the wall (its row must be set first, and exactly one of 18 works).
A search that starts by touching the pieces can be exhaustive — 116,640 states on L3 — and blind.
**Ask of every condition: is this a one-way door?** If yes it belongs in FRONT of the search.

- `sp80_q52_long.py` BFS FINISHED with a bounded non-result: `NO WIN: expanded=107,581
  states=269,723 frontier=162,142 t=9,145s **exhausted=False**`. The frontier was still growing —
  this rules nothing out, it only says 2.5h of BFS did not reach it.
- **ar25 L5 is a measured WALL** (25 probe files, `breadth-recon.md` §"ar25 L5"). Carry forward so
  it is not re-derived: a **real-move life budget of ~127 non-blocked presses** (blocked presses do
  not count); W's position space is **441** (21 rows × 21 columns), not 21; the joint (W row × S
  phase) surface maxes at **99/151** with no win; and **colour 4 is universal occlusion paint**, not
  a gauge — it fires wherever the moving comb overlaps any non-background object, and it is
  reversible. The one gap left is that every click sweep ran at the ENTRY configuration only.
- **Walls closed today with completeness evidence** (do not re-probe without a NEW idea): sk48 L2
  (20,480 click-then-ACT arms, zero), cd82 L3 (click axis and condition axis both exhaustive; the
  colour selection is reversible, so there is no one-way door there), tr87 L3 (ten rounds; three
  mutually disjoint 7-symbol alphabets, every shape and position rule refuted, four live null
  hypotheses dead), ar25 L5 (see above), **wa30 L3** (four reactive guards A/B'd, none beats the
  control), and **re86 L6 — now an IMPOSSIBILITY PROOF, not a tally of failures**: the plus cannot
  cover all four colour-9 boxes in one placement (max 2 of 4), and **sequential coverage is illegal**
  — coverage is occlusion, not deletion, so a box reverts the instant the shape leaves (verified with
  a positive control on level 1, which the driver clears). No ordering, no multi-visit plan and no
  `group_plan` change can clear L6 by covering; the win is not box-covering at all.

**Two "defects" that are LOAD-BEARING — found by fixing them and watching earlier levels break.**
This is the session's most transferable result and it cost two A/Bs:
- `cover.py`'s `boxes()` returns the colour-0 marker as a phantom ninth box (no `f != bg` test).
  Fixing it **regresses the level before L6**: the phantom's coordinate MOVES on every re-detection,
  and that changing key is what defeats the wave loop's `sig == prev_sig` stagnation check, buying an
  extra wave the earlier level needs. A bug the driver depends on.
- `haul.py`'s planner has no time dimension, and the two obvious repairs both break level 2:
  blocking non-background cells as terrain **seals the board** (so the dither is passable — the L3
  refusal is not terrain), and re-deriving movement every round also fails L2, so the queue itself is
  load-bearing on a board whose conveyor moves every action.
**Before shipping any "obvious fix" to a driver here, A/B it against the levels that already pass.**
The shadow-module harness (`wa30_q90.py`/`wa30_q91.py`/`re86_q60.py` — patch the source as TEXT, exec
it as a module beside the original) makes this cost two minutes and never touches the file on disk.

**Three corrected numbers that every future probe depends on — do not re-derive, do not trust the
older figures if you find them elsewhere:**
- **re86 L6's budget is 199 actions**, not the "<100" the original note guessed, and **GAME_OVER
  there re-enters at L6 for FREE** with a byte-identical board. So L6 rounds burn budget freely and
  never repay the 421-action climb. Both were measured, both had shaped every earlier round's caution.
- **ar25 L5's real-move budget is ~127 non-blocked presses per life**; blocked/no-op presses do not
  count. Any search path longer than that in one continuous env must be split across fresh deepcopies.
- **wa30 L3's control ceiling is `filled_hi = 4`, not 3** — the 3 came from a GLOBAL filled counter
  that conflated L2's leftover book with L3's own progress.

**Two instrument laws earned today, both cheap and both already wrong-footed a round:**
- **A click sweep that only LOOKS answers the wrong question in both directions.** A per-action
  counter can make every cell read responsive (cd82: all 4,096), and a click can set real state that
  changes nothing until a VERB reads it. Sweep **click-then-ACT** — click, then press each verb, and
  compare against that verb with no click.
- **A quantity that moves dramatically can still be decoration.** ar25 L4's colour-4 walked
  18 → 117 → 0 and looked destroyed forever (reversible artifact keyed to a row); L5's hit 243 and
  was universal occlusion paint. Read CELLS and components, and do the round trip, before calling
  anything a mechanic.

**TWO driver patches exist, both measured, NEITHER applied** (`breadth-recon.md` §Two proposed
driver patches). Shadow-module A/B: patch the source text, exec as a separate module, drive it
beside the unpatched original — no driver file is edited and no sweep is spent.
- `haul.py` queue-refusal guard — **REJECTED, measured**: patched = 0 levels cleared / 3,000
  actions burned, control = L1 at 43, L2 at 113 (`wa30-q70.txt`). Haul's pickup presses into
  refusals on purpose, so a blanket "refusal means stale plan" kills every delivery. The
  DIAGNOSIS still stands (see the section); the guard must exclude the deliberate-refusal cases.
- `dial.py` reader fix — **CORRECT AND INERT, held** (`tr87-q80.txt`): L1 combination dict `==`
  the shipped one, L1=28 / L2=58 under both readers, L2 pairs 0→6 and L3 pairs 0→8 — but
  `combination()` is still `{}` on both, so the level count does not move (2 → 2). Patch text
  lives in `tr87_q80.py`; land it with whatever decodes L3, not on its own sweep.

**Kaggle — TWO candidates are built and locally exec'd; the user's call is WHICH to submit**
(asked 2026-08-15, answered "ทําไปก่อนค่อยตัดสินใจ" — build both, decide at the window).
1. **v9-lite** = `kaggle/my_agent.py`, rebuilt from `kaggle/adapter.py`. Reverts v8's two
   additions (the claim-gated 60s `play` slice and the state-aware `_qstate` bandit); `play`
   now owns the whole 240s game clock and the mop-up is v7's plain global bandit. pytest 330,
   bundle 226,417 B, exec'd clean, all 14 driver modules asserted present. Expected ≈0.10-0.11.
2. **hybrid** = `<starter>/agent/my_agent_hybrid.py`, built by `kaggle/bundle_hybrid.py` from
   `kaggle/adapter_hybrid.py` + `kaggle/goose_extract.py`. The competition's own sample agent
   is the base class and plays every game; `compete.play` pre-empts it only where a driver
   signature claims the reset frame. 231,388 B, exec'd clean (torch 2.13.0+cpu now installed
   in the starter venv), MRO `MyAgent → _goose.MyAgent → Agent`, 14 signatures wired.
   ⚠️ **Written OUTSIDE this repo on purpose** — it embeds a third party's MIT source and this
   repo is MIT-0; writing it in would relicense their work. ⚠️ And the honest caveat: the
   drivers claim ~nothing on the hidden 110 (v1 without them 0.11 ≈ v7 with fourteen 0.10), so
   its expected score is close to the SAMPLE's own — a better score, not a better agent.
   Its `GAME_SECONDS` is the one unmeasurable knob (the sample's own `is_done` is WIN-or-8h
   PER GAME, so it never visits all 110 and still scores 1.56; ours trades that for coverage).

**Why v9 exists at all — the v8 bet is REFUTED, and it inverts the standing hypothesis.**
Scores: v1 = **0.11**, v7 = **0.10**, v8 (ref 55520866, state-aware bandit + claim-gated slice)
= **0.01**. v8's only behavioural change was giving the cheap bandit mop-up 3× more clock
(`PLAY_SECONDS_UNCLAIMED=60` vs `GAME_SECONDS=240`) — and it scored 10× WORSE. So **the mop-up is
actively harmful relative to `compete.play`**, which is the opposite of what v8 assumed. The
cheap-fix v9 is therefore "give `play` the whole game clock, delete the bandit", expected ≈0.10.
That still loses to the official sample by 15×. The sample (`reference/stochastic-goose/` in the
starter repo, Tufa Labs `DriesSmit/ARC3-solution`) is a **torch CNN that learns online per game**
which of ACTION1-5 and which of the 4096 click COORDINATES change the frame — the coordinate head
is why it scores ~1.56 while uniform random clicking earns nothing. The real move is a hybrid:
goose as the base agent, driver signatures as an override on claimed games. Blocker to note before
building it: **torch is not installed in either local venv**, so a hybrid bundle cannot be
exec-verified locally without a ~200MB CPU wheel — and "exec the built bundle before every push"
is the rule a forgotten `roller` already cost us. **Today's slot is USED** (v8 landed
2026-08-15 05:36 UTC = 12:36 Thai); the next window is 00:00 UTC = 07:00 Thai.

**Games CLOSED with evidence this session** (do not re-probe without a new idea): sc25 (full-grid
flood fill: 22 components, all four structures individually refuted), g50t (live DFS of every
direction at every reachable cell: 12 cells, gate reverts on the first departure press), bp35 L2
(reel arithmetic: one ride/life, doors 4-5 rides away, A7 is a plain -6 move, board reverts),
m0r0 L2 (both regions click-swept, meeting cell unreachable), cn04 L2 geometry (119 single-pad + 48
interlock placements with EVERY shape as mover, plus a 4-shape assembly), dc22 L2 (exhaustive joint
position x toggle BFS), ka59 L2 (moat min thickness 9, no 3-step crossing).

**Still open with live leads**: tr87 L3 (147 combos killed "one of 29/36/43 is wrong"; next is the
343-combo triple or a target outside the 7-station AND), sp80 L3 (transfer is shooter-gated: non-D→D,
D→B2; BFS not exhausted), re86 L6 (box-covering geometrically capped at 2/4 per group — the mechanic
must be something else), cd82 L3 (impossibility proof: every wedge >=50 cells, every legend region
<50 — a sub-50 verb must exist and 17 candidates are dead).

## THE PATTERN THAT WORKS — five games have fallen to it, follow it

1. `probe_found.py <game>` — determinism, step rate, census, board dump, baselines.
2. `probe_acts.py <game> 8` — per-action diffs, guarded against empty frames.
3. Hypothesis probes until the mechanic is MEASURED.
4. **Solve level 1 BY HAND** with a scripted action list, verified forward-only.
5. Only then build a rung, shaped like `cover.py` / `swap.py` / `haul.py` / `maze.py` /
   `dial.py` / `skewer.py` / `tape.py`,
   and measure its signature with `sigs.py` (every SHIPPED predicate x 17 reset frames)
   BEFORE wiring. Signatures are no longer all disjoint: `cover`'s fires on four games,
   so a contested game is settled by CASCADE ORDER and `sigs.py` checks that.

`bfs_solve.py <game> <depth> <nodes> [clock_rows]` searches real engine states with
deepcopy nodes; an action the engine answers None 25x in a row is retired for the run
(bp35/cn04's click answered KeyError while the coordinates were being attached the way
the local wrapper ignores -- see QUEUE 1; the latch is still right, since a click can be
answered with None for other reasons). ⚠️ **bp35 cannot be BFS'd at all**: its own
game code recurses infinitely on a deepcopied env (RecursionError persists at limit
20000 -- deepcopy likely breaks an object-identity invariant, e.g. a visited set). The
instrument is dead there, not the game; bp35 needs forward-only hand probes
(`bp35_p1.py` started: the 9/11 piece slides on A3/A4, a 1141-cell global event fires
under the x43-47 chute, A7 is context-dependent).
Validated: sp80 L1 `[4,4,4,5]` in 38 expansions, ls20 L1 in 13 actions, tu93 L1 in 18
← results/bfs-control.txt, bfs-control-ls20.txt, tu93-bfs.txt. **A null means nothing
unless it reports `exhausted=True` AND the depth covers a whole life.** Not rules-legal
(it rewinds, like `play.py`) — use it to learn IF a level is winnable and what the line is.

## GATE

Any change to `compete.py`/`cover.py`/`swap.py`/`haul.py`/`maze.py`/`dial.py`/`skewer.py`/
`tape.py`/`bridge.py`/`sorter.py`/`discover.py`/`gate.py` =
full 17-game sweep before commit, per-game, no game loses a level ← CLAUDE.md.

```bash
./.venv/Scripts/python.exe compete.py > results/sweep-<name>.log 2>&1
```
~100 min (bp35's level 2 alone spends 2,202 actions). Compare with the parser, never by eye and never with `diff` (rewritten here):
```bash
./.venv/Scripts/python.exe sweep_diff.py <before.log> <after.log> <game-expected-to-change>
```
The third argument is the positive control — it refuses to report "identical" until it has
SEEN a difference in the game the change was aimed at. Hardcoding it worked for exactly one
comparison and then fired on the next.

Values that must not move ← **results/sweep-wave11.log** (refreshed 2026-08-16):
- ls20 **7/7** `[23, 45, 99, 178, 292, 209, 526]` · tu93 **9/9** `[31, 14, 19, 17, 29, 28, 14, 21, 29]`
  · sb26 **8/8** `[9, 15, 15, 15, 17, 19, 17, 17]` · re86 **5/8** `[31, 56, 66, 80, 188]`
- ar25 **4/8** `[15, 25, 40, 29]` · sp80 **2/6** `[16, 7]` · tr87 **2/6** `[28, 30]`
  · cd82 **2/6** `[6, 11]` · wa30 **2/9** `[43, 70]`
- sk48 **1/8** `[24]` · cn04 **1/6** `[14]` · m0r0 **1/6** `[27]` · dc22 **1/6** `[25]`
  · ka59 **1/7** `[11]` · bp35 **1/9** `[20]` · sc25 **0/6** · g50t **0/7**
- pytest **330 passed** — run redirected to a file and READ THE FILE (rtk rewrites pytest).

⚠️ **This block WAS stale and it cost an agent a whole run (2026-08-16).** It carried
`sweep-sorter4.log`'s numbers — sp80 `1/7 [16]`, tr87 `1/6 [28]`, cd82 `[1306]`, cn04 `[131]`,
m0r0 `[53]`, tu93 `2/9`, sb26 `4/8` — while the GOAL line at the top of this file had been
kept current. A brief written from this block sent an agent to crack **sp80 level 2, which
already falls in the shipped sweep** (`swap.py`'s `L2_LINE`, gated, 7 actions). The agent's
work was correct and its target was not. **Refresh this block in the same edit as the GOAL
line, every sweep** — one number updated and its twin left behind reads as fresh, because
they sit in the same document and one of them is right.

Recon-only work needs no sweep.

## QUEUE (highest value first)

0a. **Kaggle SCORED: 0.11 vs baseline cluster ~1.56 — diagnosis done, budgeted
   adapter READY, resubmit awaits the user.** ref 55479472 scored publicScore
   0.11 (unit = % of levels over the 110 hidden games). The leaderboard's
   thick cluster at 1.56-1.61 is the official sample "Stochastic Goose"
   (CNN frame-change learner, NOT pure random), top is 2.70 — so v1 lost to
   the sample. Cause, read from the sample's own source
   (Desktop\ARC-AGI-3-Kaggle-Starter\reference\stochastic-goose\): it sets
   MAX_ACTIONS = float('inf') and bounds the RUN with an 8h clock in
   is_done, while our adapter self-capped at 2,600 actions of SLOW thinking
   (play's wander burns minutes/game; 110 games would also graze the kernel
   wall clock). Fix implemented 2026-08-13 in `kaggle/adapter.py` (bundle +
   starter-kit copy rebuilt, pytest 330, smoke ls20 L1 in 61 actions):
   per-game clocks — play gets PLAY_SECONDS=180 of wall time (queue-get
   timeout shrinks to the slice), then cheap random mop-up until
   GAME_SECONDS=240 ends the game via is_done, global RUN_SECONDS=8h-300s
   drains the tail; MAX_ACTIONS=200_000 is now just a backstop. 110×240s ≈
   7.3h. UNPROVEN: the budgets are sized by arithmetic, not measured on a
   110-game run; and whether 180s of play beats 240s of goose-style play on
   hidden games is an open question — the sample LEARNS which actions move
   frames, our mop-up is uniform random. DONE 2026-08-13 21:45: the mop-up is
   now a frame-change bandit — weight (changes+1)/(tries+2) per action, the
   click included as a candidate aiming at a random cell; unit-driven 400
   rounds, responders picked 274/400, click path exercised (pytest 330,
   bundle v3 pushed as kernel version 3; superseded same night by kernel v4 =
   v3 + driver #10 ferry.py (ka59) + the tu93 L3 playbook, MODULES gained
   "ferry", smoke ka59 L1 via starter harness. SUBMIT v4 at the reset.
   RESUBMIT STATE 2026-08-13 20:45 (superseded by v3 above): kernel v2 (budgeted adapter) pushed + run
   COMPLETE, but the CLI submit answered 400 — the error BODY (dug out via a
   requests spy; the CLI swallows it) says the real quota: **1 submission per
   day per team, NOT 5**; v1 used today's. Resets midnight UTC = 07:00 Thai.
   Ready-to-run after reset (from Desktop\ARC-AGI-3-Kaggle-Starter):
   `KAGGLE_API_TOKEN=$(cat .kaggle/access_token) ./.venv/Scripts/kaggle.exe
   competitions submit -c arc-prize-2026-arc-agi-3 -f submission.parquet
   -k sahasawatt/arc-prize-2026-arc-agi-3-starter -v 4 -m "time-budgeted
   adapter + bandit mop-up + ferry driver + tu93 L3"`.

0. **Kaggle: SUBMITTED 2026-08-13, ref 55479472, status PENDING at submit time** —
   kernel sahasawatt/arc-prize-2026-arc-agi-3-starter v1, bundle rebuilt WITH
   tape/bridge/sorter (kaggle/bundle.py MODULES updated), verified through the starter
   harness ls20 7/7 in 1,376 actions ← results/kaggle-ls20-v3.txt. Starter kit lives at
   Desktop\ARC-AGI-3-Kaggle-Starter (venv + framework set up; token in .kaggle/, NOT in
   git). Check score: `kaggle competitions submissions -c arc-prize-2026-arc-agi-3`.
   Quota 1/day (measured from the 400 body). Windows gotcha paid twice: slim_framework + play_local both write/print
   cp1252 — re-encode vendor agents/__init__.py to utf-8 after setup. Original checklist: The FULL agent (compete.play,
   rungs + all nine drivers) runs unchanged on a worker thread behind a queue-backed
   proxy env: `kaggle/adapter.py` + `kaggle/bundle.py` -> generated `kaggle/my_agent.py`
   (rebuild after ANY module change). Verified through the official starter kit's own
   harness: **ls20 7/7 WIN 43.59%**, per-level transitions identical to the local sweep
   ← results/kaggle-ls20-v2.txt; driver games identical ← results/kaggle-local*.txt.
   Starter kit = github.com/arcprize/ARC-AGI-3-Kaggle-Starter (clone fresh; scratchpad
   copy dies with the session). Human steps: accept rules → username into
   notebooks/kernel-metadata.json + kaggle.json → copy kaggle/my_agent.py to
   agent/my_agent.py → `make submit` → Save & Run All → Submit to Competition.
   Traps already paid for: `GameAction(v)` raises on every int (map {int(a.value): a})
   · exec'd modules must enter sys.modules BEFORE exec (dataclasses) · the adapter's
   per-round timeout must dwarf the slowest planning round — ls20 L6 thinks for MINUTES
   on one round; a 120s timeout killed the worker and the silent 5/7 that resulted had
   no error anywhere (tell: acct file truncated at the 32KB OS buffer = never closed,
   + fallback resets every ~130 actions). Local-only: play_local SSL-fails on the
   SECOND game per process; slim_framework.py writes cp1252 on Windows.
   ⚠️ Pipe is ~20x slower per action than raw local (framework validate+log) — before
   submitting for real, estimate 110-game rerun wall clock; MAX_ACTIONS=2600 may need
   trimming.

1. **DONE 2026-08-11 — the click is aimed now, and it is INERT.** Fix in `compete.py`
   (both ways) + `kaggle/adapter.py`'s proxy `step(action, data=None)`; sweep
   `results/sweep-click-aimed.log` is identical to `sweep-skewer.log` in all 17 games,
   mean 6.320% (`sweep_diff.py`'s control fails on purpose — nothing differs), pytest 330.
   **Next lever, its own gated change:** `poke-click` picks the SMALLEST unprobed object
   first; dc22's only two responding targets are 40 and 47 cells, so the rung never
   reaches them. Order by response, or sweep large objects too. Rebuild the Kaggle bundle
   before any submission — `kaggle/adapter.py` changed. The original finding, kept because
   the reasoning is what generalises:
   `compete.py:1965` set the
   coordinates with `clicker.set_data({...})`; the local wrapper reads only its own `data`
   kwarg (`local_wrapper.py:234`), so every click ever made arrived empty and cn04/bp35
   answered `KeyError: 'x'` — the crash CLAUDE.md filed as cn04's own bug. Measured both
   ways, same coordinates ← results/click-probe.txt. Aimed, dc22 has exactly two live
   targets of 35 components ((48,19) n=129, (48,36) n=97 ← results/dc22-click.txt) and
   bp35's whole second verb appears. The fix is `env.step(clicker, data={...})` plus
   widening `kaggle/adapter.py:83`'s proxy `step(self, action)` (or the bundle breaks on
   the first click), then the full 17-game sweep — cn04 is the positive control for
   `sweep_diff.py` (its clicker stops being retired) and its 1/6 `[131]` is what to watch.

2. **bp35 LEVEL 1: SHIPPED. `tape.py` is the seventh driver; bp35 is 1/9 [20], 2.222%,
   and the sweep is clean — 16/17 identical to the digit, mean 6.320% -> 6.451%
   (results/sweep-tape.log). What is left there is LEVEL 2, which nobody has seen and
   which currently swallows 2,202 actions of `wander`.** The driver
   rediscovers the line from the frame — `1/9 levels actions=[20]`, score 2.222%, the hand
   line's own count ← results/tape-try2.txt, results/smoke-bp35-tape.txt. `sigs.py` PASSES
   with it (fires on bp35 alone; cascade `dial → tape → cover → …`, because cover's loose
   signature claims bp35 too) ← results/sig-sweep-tape.txt. pytest 330. It is the first
   driver that drives with CLICKS, so it is built only where a complex action exists and
   dropped if the clicker is retired. ⚠️ bp35 now takes ~10 minutes per run: its level 2
   swallows 2,202 actions of `wander`, so the whole sweep is ~100 min, not ~90. Level 2 is
   unseen and is the next bp35 question. Below is the hand line's own write-up:
   20 actions against a baseline
   of 21, forward-only, two identical runs ← results/bp35-solution.txt (the full line and
   the mechanic behind every step), bp35-p17.txt/bp35-p17b.txt. The win is **walking onto
   a colour-7 object**; it lives in the room the THIRD ride reaches, which is why fourteen
   probes never saw it. Verbs: a click turns a block into floor; a click on the block over
   the piece's own columns rides one room up; A7 at a shaft column rides down; the flood
   is an action timer (8 + ~8 per ride). Next per the repo's own pattern: a `bp35` driver
   shaped like `cover`/`swap`/`haul`/`maze`/`dial`/`skewer`, its signature measured by
   `sigs.py` over all 17 reset frames BEFORE wiring, cascade order re-checked, then the
   gated sweep. Level 2 is unseen.

3. **dc22 LEVEL 1: SHIPPED too — `bridge.py` is the eighth driver.** 1/6 `[25]` against a
   baseline of 59, sweep clean (16/17 identical, mean 6.451% -> 6.731%,
   results/sweep-bridge.log), sigs PASS, pytest 330. Hand line 20 actions ←
   results/dc22-solution.txt; the driver finds its own route ← results/bridge-try3.txt.
   Its policy: walk if the board has a route, else stand at the reachable position
   NEAREST the goal and press an untried button from there — pressing them all from
   the start square is what made this level look unsolvable. Level 2 is where it now
   stops (it already finds that board's two buttons).

4. **sb26 DONE — WHOLE GAME, 8/8, WIN in 123 actions (2026-08-13, sweep-sorter5.log
   PASS 16/17 identical, pytest 330, PENDING COMMIT).** L5-L8 all fell to one idea:
   a hollow block is a REFERENCE to the box wearing its frame colour, recipe = a
   box's contents flattened, refs expanding recursively — L5 child called twice
   (winner at leaf 1,211 of the 10,080-assignment DFS, sb26-l5-dfs/solve.txt), L6
   fixtures in expansions, L7 nested 2-deep + per-RUN hollowness + wall-pair box
   grouping, L8 doubled recipe row = 2 unrollings of a SELF/mutually-referencing
   box, PREFIX-matched (boards randomise per episode — two L8 variants measured).
   Solver = enumerate block→slot assignments against a pure flatten, engine never
   stepped; drop unpointed slotless boxes (frame artifacts steal the root).
   Full story ← breadth-recon §sb26 FALLS COMPLETELY + CLAUDE.md drivers paragraph.
   The L1-L4 story, kept: Levels 1-4 SHIPPED, 4/8
   `[9,15,15,15]` 27.778% — the tree-walk story: 3/8 `[9, 15, 15]`,
   16.667% (sweep-sorter3.log, 16/17 identical, mean 7.221% -> 7.711%). L3 = two pipes
   into two framed sub-boxes; each pipe splices in only ITS OWN box's slots, homed by
   x-nearness never colour; pipes read from the row ABOVE the slot row; run-button hunt
   once per level (the A7-undo infinite loop is fixed) ← breadth-recon §sb26 L3. Level 4
   is unseen; the driver answers None there cleanly. The L2 story, kept: 2/8 `[9, 15]`,
   8.333% (sweep-sorter2.log, 16/17 identical, mean 6.894% -> 7.221%). Level 2's slot
   order is the upper row L2R with the whole lower row spliced in at the pipe — found by
   exhausting 5,040 slot assignments with insertion order pinned to the recipe, sound
   because A5 is position-pure and A7 is an UNDO (insertion stack ⇒ frame-dedup search
   would merge different histories, the sp80 law) ← breadth-recon §sb26 L2, CLAUDE.md
   drivers paragraph. Level 3 unseen. The level-1 story, kept:
   1/8 `[9]` against a
   baseline of 18, sweep clean (16/17 identical, mean 6.731% -> 6.894%,
   results/sweep-sorter.log), sigs PASS, pytest 330. The click is half a DRAG (select a
   stock block, click a slot); loaded in the recipe row's order, ACTION5 runs the machine
   — the action §sb26 called a pure timer burn, measured on an empty machine because no
   click could land. The driver finds the run button by TRYING the plain actions.

5. **ka59 REOPENED — the click is a pickup-and-ferry** ← breadth-recon §ka59 2026-08-12.
   The aimed click moves the piece ONTO the dot (consuming it); kick east then click the
   landing crosses the bar, so the 74-state BFS was the state space of a game missing its
   second verb. Right room walked from inside: nothing new. Still unmeasured: the DROP —
   dead so far are stand/click-self/click-destination/bump/two-timers. Next instruments in
   the recon note. sc25's clicks are truly dead (0 of 22 components answer ←
   click-sweep-all.txt) and g50t has no complex action, so their walls stand unchanged.

6. **Next 0-level game.** Remaining: ka59, sc25, g50t — and the walls
   have piled up: dc22 (sealed room, click sequences), ka59 (74-state BFS exhausted),
   sb26 (EVERY channel dead ← breadth-recon §sb26), g50t (search says L1 unwinnable).
   Fresh ground: **sc25** (metronome game, br-sc25-*.txt exist; its election problem is a
   known repo-wide blocker). bp35 has left this list — see item 2. What its fall is worth
   to the others: the click verb now works everywhere (item 1), and a reachability claim
   expired TWICE in one session on the same board, both times because it had been measured
   before something was cleared.
2. **sk48 level 2 — the rearrange puzzle.** `skewer.py` clears L1 (1/8 `[24]`); level 2
   has four blocks in ONE row, recipe [8,12,9,14] vs forced row order 14,9,12,8 —
   ploughing through threads all four and does NOT win ← breadth-recon §sk48. Find the
   reorder mechanic (unload? re-pierce partial? push out the far side?). `bfs_solve` from
   a cleared-L1 process is the cheap instrument (deepcopy after the L1 line, then search).
3. **tr87 level 2 — same family, different geometry.** `dial.py` clears level 1 in 28
   actions and correctly declines level 2 ← results/tr87-l2.txt: SEVEN stations rather
   than five, and the hint band sits on its OWN lattice offset (band x18-45 against
   stations at x8,15,...,50), so a hint no longer names a station by POSITION -- which is
   the assumption level 1's reading rests on. Its top region also loses the (icon, block)
   tiles the level-1 combination is read from. Find what names a station there before
   writing any code; the driver's reading is otherwise geometry-free and should transfer.
4. **tu93 level 3 — a MOVING hazard, its own project.** The driver is wired and clears
   2/9 `[31, 14]` (5.946%, ← results/sweep-dial.log). It stops at level 3 because the only
   route to that goal passes a cell patrolled by a moving colour-8 body, and `maze.py` has
   no phase model — it blacklists a square only after dying there ← results/tu93-death.txt.
   Same class of mechanic ls20's levels 6-7 needed (`gate.mover_period` / `route_moving`
   are the built precedent). ⚠️ **tu93's GAME_OVER is NOT budget exhaustion** — it fires
   with 60 of 64 bar cells left, on collision ← results/tu93-budget-trace.txt.
5. g50t's open contradiction ← results/breadth-recon.md §g50t · re86 L6 · cn04 L2 trigger ·
   ar25 walls-during-planning.

## TRAPS — each has cost this repo a real session, most of them twice

- **An action that looks like a no-op usually says something about the STARTING POSITION.**
  g50t: only 2 of 5 actions move anything at reset (piece in a corner). tu93: three actions
  look dead and one looks like a one-shot; from a moved position they are four ordinary
  directions. g50t's action 5 is a RECALL and read as "no change" for eight presses because
  the piece was already at its destination. Always retry from somewhere else.
- **A reading taken while the piece stands on something is OCCLUSION.** Four games now.
  Step away and re-read before believing a count changed.
- **The piece is often not a solid block.** g50t's is a ring with a hole; wa30's carries a
  one-row edge naming its HEADING that moves to whichever side it walked; tu93's has a
  rotating notch. Reading a piece by its body colour reports a position that shifts when it
  turns, and measuring displacement from one colour reads the step minus one.
- **A detector that works at reset can stop working once the board changes.** wa30's frame
  became undetectable the moment the first crate slotted in; swap.py's clock is a band only
  while it is full. A signature function and a per-round tracker are not the same instrument.
- **A byte-identical run after a code change proves the change never executed.**
- **A signature you were told was measured may never have been.** The brief said
  `maze.signature()` had been run against all 17 reset frames; no run file held it, and
  what existed was a CANDIDATE table whose two predicates each fire on five games. Run
  `sigs.py` (every shipped predicate x 17 frames, own controls) before wiring anything.
- **Driver signatures are no longer disjoint, so CASCADE ORDER is load-bearing.**
  `cover`'s fires on ar25, re86, bp35 AND tr87 while only ever engaging re86 -- a driver
  handed a board it cannot read answers None on its first round. `dial` is asked before
  it; `sigs.py` fails if a contested game has the wrong driver first.
- **Put a positive control in the SAME invocation as any probe.** A probe that "ran" is not
  a probe that "measured".
- **Something measured but never COMPARED against anything is where the answer hides.**
  tr87's key sat in a region a whole session had dumped and never matched to anything.
- `rtk` rewrites grep, diff and pytest output. Never gate control flow on a grep exit code.
- Windows console is cp1252 — keep probe output ASCII or set `PYTHONUTF8=1`.
- Background bash starts at `Desktop` — `cd` into the repo in every backgrounded command.
- The engine returns EMPTY frames mid-level and at transitions — guard every frame read.
- ⚠️ Running `compete.py <one-game>` OVERWRITES `results/compete.json`, which holds the
  17-game sweep. It is tracked; `git checkout --` it afterwards.
- ⚠️ A backtick inside `git commit -m "…"` is command substitution: the word is executed and
  silently deleted from the message. Write the message to a file and use `-F`.

## RULES

- NEVER read/grep/list `environment_files/` — the answer key ← CLAUDE.md §The one rule.
- NEVER `git add -A`; stage by name, `git commit -F <file> -- <paths>`.
- Ask before every commit.
- One change at a time; a claim needs the run that produced it, named.
- Delegated agent results are INTENT, not fact — re-verify the artifact in the main thread
  (re-run a claimed solution forward-only; check the file set with git, not the summary).
