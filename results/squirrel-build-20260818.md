# squirrel v1 -- build notes + eval (2026-08-18)

Files: `squirrel.py` (agent), `squirrel_eval.py` (17-game runner). Both new,
repo root, no edits to `compete.py` or any driver. `squirrel.py` has a
`__main__` self-check (offline, no network) exercising untried-action pickup
and the no-op counter on a 2-state fake env -- passes.

## What was implemented vs the spec

All six spec points landed as written, no deviation:

1. **Interface** -- `Squirrel(action_space, max_actions=500, reset_fn=None)`,
   `act(obs) -> action`, plus `agent.pending_data` for the caller to pass to
   `env.step(action, data=agent.pending_data)` on a click. The spec's own
   one-liner (`env.step(agent.act(obs))`) can't carry click coordinates
   through `local_wrapper` on its own -- confirmed against `compete.py`'s own
   fix note (the `set_data`-alone-arrives-empty bug at `compete.py:2074`) --
   so `pending_data` is the minimal addition needed to keep `act()`'s
   contract to "one action" while still supporting clicks correctly. Smoke
   tested on `dc22` (a click game): 28 of 40 actions were clicks, all landed.

2. **State key** -- `f[-1]` bytes, auto-masked. The mask is **built once**
   when the 30-action warm-up completes and then **frozen** (not
   re-derived every step) -- rebuilding it later would silently reinterpret
   every edge already recorded under the old key shape, which would corrupt
   the graph rather than improve it. Deviation from the letter of the spec
   ("re-derive the mask per level") in one respect: re-derivation happens
   *once per level* (at warm-up-complete), not continuously -- continuous
   re-derivation was considered and dropped as a correctness risk for a v1
   with a 500-action budget, where the warm-up already consumes 6% of it.

3. **Transition graph** -- `dict[state_key] -> {action_id: dest_key}`
   (adjacency-indexed rather than a flat `(state,action)->dest` dict, for
   O(1) BFS neighbour lookup -- same information, cheaper to walk). Click
   targets come from a self-contained connected-component scan (4-neighbour
   flood fill, background = single most common colour), capped at 40
   components per frame so one noisy board can't blow the action-ordering
   list -- `ponytail:` this cap exists, raise it if a real component list is
   ever seen truncated by it (no evidence of that yet).

4. **Policy** -- untried-first (cheapest first: plain before clicks, via
   stable sort), else BFS over the *learned* graph to the nearest
   untried-having state, walked one action at a time with the expected key
   checked every step (`plan_expected`); a mismatch clears the plan and
   forces a replan next call, never a crash. No-op deprioritization is a
   **global** counter (`global_inert[action_id]`), matching the spec's own
   wording ("global") -- an action's future *ordering* (not eligibility) at
   any newly-seen state is sorted by how often it has been a no-op anywhere,
   so it's tried later, never excluded.

5. **Level-up** -- wipes `graph`/`untried`/`poisoned`/mask/plan on
   `levels_completed` increase; keeps `global_inert` (a property of the
   *action*, not the board) across levels -- undocumented in the spec either
   way, kept as the smaller diff.

6. **Death** -- `GAME_OVER` poisons `(last_state, last_action)` (BFS treats
   a poisoned edge as unroutable, but the edge stays in `graph` -- knowledge
   isn't deleted, only avoided) and then either calls the injected
   `reset_fn` (used for local eval, wired to `env.reset`) or falls back to
   returning the `RESET` `GameAction` for a caller that offers it in
   `action_space` (the Kaggle case per the task brief -- untested here, no
   Kaggle harness in this budget).

No lookahead beyond the graph BFS, no learned model, nothing else added.

## Eval: squirrel vs wave13, all 17 games, 500 actions each

Foreground run, `results/squirrel-eval-1.txt` (raw log with per-game engine
init lines); table below is the same numbers. Wall clock for the full sweep:
~43s (500-action budget, most games use noticeably fewer before
`StopIteration`; no game hit the 120s per-game wall cap, no exception, no
`obs=None`).

| game | squirrel | wave13 | verdict |
|---|---|---|---|
| ar25 | 0/8 | 4/8 | loses |
| cn04 | 0/6 | 1/6 | loses |
| dc22 | 0/6 | 1/6 | loses |
| ka59 | 0/7 | 1/7 | loses |
| ls20 | 0/7 | 7/7 | loses |
| m0r0 | 0/6 | 2/6 | loses |
| re86 | 0/8 | 5/8 | loses |
| sc25 | 0/6 | 0/6 | **matches** |
| sp80 | 0/6 | 3/6 | loses |
| bp35 | 0/9 | 1/9 | loses |
| g50t | **1/7** | 0/7 | **beats** |
| sk48 | 0/8 | 1/8 | loses |
| tr87 | 0/6 | 2/6 | loses |
| tu93 | 0/9 | 9/9 | loses |
| wa30 | 0/9 | 2/9 | loses |
| cd82 | 0/6 | 2/6 | loses |
| sb26 | 0/8 | 8/8 | loses |

**beats=1, matches=1, loses=15.** Mean squirrel score: 0.053% (vs wave13's
23.841%, `results/sweep-wave13.log`).

## Honest verdict

v1 loses badly, on every game the wave13 driver stack has an engineered
answer for, and beats it exactly once (g50t, where wave13 scored 0 and
squirrel completed 1 level in 156 actions -- wave13's own log shows `g50t
0/7 actions=[] score=0.0%`, so this is a real gap, not noise). This is the
expected shape for a domain-blind graph search competing against ~30 driver
files built from months of per-game measurement (the m0r0/ls20/sb26/tu93
write-ups above alone are thousands of lines of "what actually happened").
It is **not** evidence the graph-BFS design from the Kaggle-intel brief is
wrong -- it's evidence that raw pixel-frame state keys, with no perceptual
model, are the wrong granularity for games whose winning line is 20+
precisely-sequenced actions deep in a huge reachable set.

First hypotheses for the losses, **unverified, first-pass**:

- **ls20 / tu93 / sb26 (all 7-9/9 under wave13, 0 under squirrel):** these
  three are exactly the games whose wave13 solution required building a
  perceptual model (HUD clock rate, machine-tree DFS, quarter-turn ring
  discovery) on top of the raw frame -- CLAUDE.md's own ls20 section runs to
  dozens of measured iterations to get there. A flat pixel-byte state key
  fragments what a human would call "the same board state" into many
  distinct keys (piece position alone multiplies the state count), so BFS
  reuse across the graph is far weaker than it looks from 310 distinct
  states (measured on cd82) -- state count is not exploration *coverage*.
- **ar25 / m0r0 (mirror/twin, two pieces on shared controls):** win
  condition is a specific joint configuration of two independently-visible
  pieces (m0r0_b1_l2bfs.py: L2's reachable set is one 37-cell diagonal).
  Untried-first exhausts every action at every newly-seen state before ever
  planning toward a specific target, which is the right policy for
  *discovery* but not for *hitting one narrow joint state* inside a 500-step
  budget with no bias toward it.
- **cd82 (hidden "facing" state, same-action-twice = no-op):** exploration
  diversity looked healthy in isolation (310 distinct states, 500/500
  actions used, no stall) yet level 1 (wave13 baseline 55 actions) was never
  reached -- open, not diagnosed; needs a per-action trace against wave13's
  own `roller` win line to say more.
- **Click-heavy games (dc22/bp35/sk48/ka59):** the component scan's
  single-most-common-colour background heuristic and the 40-component cap
  are both plausible false-negative sources on busy or multi-terrain boards
  -- untested against any specific board here, flagged as a design risk, not
  a measured cause.
- **HUD-ticking games generally:** the 95%-of-transitions mask threshold
  will not suppress a slow-advancing element (CLAUDE.md documents ls20's
  clock as 2-4 cells per action out of an 84-cell bar -- well under 95% in
  any 30-action warm-up window), so some non-informative pixels likely leak
  into the key and fragment states that should merge. Not measured directly
  here; the mask's `.mask` array was not dumped per game in this run.

None of the above were chased further -- out of scope for a v1 build-and-measure
pass under the time budget, and the brief's own framing is "A/B against
compete.py", not "iterate squirrel to beat wave13".
