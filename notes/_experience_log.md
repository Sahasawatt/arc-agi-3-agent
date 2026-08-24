# Experience Log — arc-agi-3-agent

## Distillation @ 2026-08-11 · after the tu93/tr87/sk48 + Kaggle-port marathon

### Lessons captured

#### L1: An artifact from CHOOSING a signature is not an artifact OF the signature chosen
- **Tier:** universal (verification-layers) — routed via task chip, not edited live
- **What:** The brief claimed `maze.signature()` "was run for real against all 17 reset
  frames". An artifact existed (`results/maze-sig.txt`) and it attested to a CANDIDATE
  TABLE — two candidate predicates, both firing on five games — while the function
  actually wired in was neither of them. The claim read as verified because a file with
  the right name existed.
- **Why:** `sigs.py` now runs every SHIPPED predicate over all 17 frames with its own
  controls; the sweep would have caught a collision eventually, but only after a wired
  driver misfired on a foreign game mid-run.
- **Routed to:** repo CLAUDE.md (drivers section) + brief TRAPS, this session. Global
  case → task chip for claude-ops (shared-repo ceremony: sahasawat branch, ratchet,
  mirror membership — not this session's repo).
- **Action:** project docs done; global deferred to chip.

#### L2: A per-round timeout on a worker thread is a fail-open kill switch, and the kill is SILENT
- **Tier:** universal candidate (long-running-job-discipline §deadline design) — task chip
- **What:** The Kaggle adapter's 120s queue timeout killed `compete.play` in the middle
  of a level-6 planning round that legitimately thinks for minutes. The random fallback
  played the rest; the run reported 5/7 with no error anywhere. The tells: the
  accounting file truncated at exactly the 32KB OS buffer (never closed = worker still
  blocked) and resets every ~130 actions in the tail (the fallback dying to the lives
  clock). PROJECT_PATTERNS §5C already holds "a timeout that bounds a guaranteed run is
  a fail-open boundary" — this narrows it: a timeout between a HARNESS and a WORKER must
  dwarf the slowest legitimate unit of think-time, and a graceful fallback is what makes
  the kill invisible.
- **Routed to:** repo README §Kaggle port + CLAUDE.md, this session. Global narrowing →
  chip.

#### L3: Control inversion by thread+queue proxy beats a state-machine rewrite
- **Tier:** project (candidate for universal later)
- **What:** `compete.play` (700 measured lines, drives env directly) runs unchanged on a
  worker thread against a proxy env whose `reset`/`step` block on queues; the
  callback-driven harness answers the queues. ls20 7/7 byte-identical through the pipe.
  Two mechanics: exec'd modules must enter `sys.modules` BEFORE exec (dataclasses), and
  enum lookup-by-value can be a lie (`GameAction(v)` raises; `.value` is a property).
- **Routed to:** README + CLAUDE.md §Kaggle bundle. Leave as project until a second
  harness needs the pattern.

#### L4: bp35 kills the deepcopy instrument (infinite recursion in the game's own code)
- **Tier:** project — breadth-recon §bp35 + brief. Not general: 16 other games deepcopy
  cleanly.

#### L5: The no-op trap keeps recruiting (A7-at-left-wall, heading marker 4th game)
- **Tier:** project — already the brief's top trap; two new instances recorded in
  breadth-recon.

### Candidates (not yet patterns)
- "Signature exclusivity by cascade order instead of disjointness" (sigs.py CASCADE
  check) — if a THIRD contested game appears, consider general form.
- The 1-game-per-process SSL flake in play_local — environment quirk, watch whether it
  reproduces elsewhere.

## Distillation @ 2026-08-25 · v22-v24 + reconciliation phase

### Lessons captured

#### L1: Negative asserts must target runtime VALUES, not source text
- **Tier:** principle-evidence (confirms verification-layers "matcher counts its own prose" — third instance: v16 'fp8', v22 'reasoning_effort', resolved in v23.1 by asserting on runtime strings which comments cannot satisfy)
- **Routed to:** already indexed globally; repo-local precedent lives in duckv23/v24 teeth. No new global entry (headline exists).

#### L2: A port's claimed mechanism needs the STOCK side read, not just the port applied
- **What:** B28 close attributed v22's probe delta to "the explicit BFS instruction" — the instruction was byte-identical in stock (R33). Teeth proved the port APPLIED; nobody diffed port-vs-stock for the claimed mechanism.
- **Tier:** unchecked-givens instance. Routed: memory + MAP B28 integration line + PR #31 body. claude-ops evidence line deferred to a claude-ops session.

#### L3: Workflow args invalid JSON passes as a silent string
- **Routed to:** auto-memory `workflow_args_invalid_json.md`.

#### L4: Cancelled Kaggle kernels expose no runner log; artifacts strip PNGs
- **Tier:** project. Verification substitute: run-reached-cell-N implies teeth passed (structural), and setup env JSON is read-back evidence for cell-8 changes.

### Candidates (not distilled — revisit on recurrence)
- local-eval-rig as a Tier-2 skill (vendor bundle + ollama + mechanics-verify before paid compute) — n=1; team's arc-agi-pub `.claude/skills/arc-agi-ops` may already own this space, check before creating.
- rtk merge-state output noise (fake "N files changed" during unresolved merge) — ground-truth re-read pattern sufficed.
