# solo probe (B41/B42) -- ONE game gets the whole clock. DIAGNOSTIC ONLY, NEVER SUBMIT.
#
# WHERE THIS GOES, and why not cell 12. The documented customization hook is cell 11/12, and
# B41's ticket said the change was "one line in cell 12". That is WRONG and would have been a
# silent no-op: cell 14 REPLACES bm.games wholesale on both paths -- the TRUE_SUBMISSION branch
# rebuilds it from the gateway, the else branch rebuilds it from the offline environment files
# (the two assignments are the lines just above this block; they are NOT quoted here verbatim,
# because the builder anchors its splice on that exact text and a second copy of it inside a
# comment makes the builder's own placement assert measure the comment instead of the code --
# caught by solo/prove_teeth.py's placement mutation, 2026-08-26)
# -- so anything cell 12 does to bm.games is discarded before the run. Same class as duckv21's
# lesson that tool_agent binds build_chat_payload by name. The filter is therefore injected into
# cell 14, anchored on the offline assignment, and runs between that line and bm.run().
#
# WHAT IT PROVES -- and the three figures this comment has now carried, in order, so nobody
# copies the dead one forward again.
#
#   1,099 actions (B41, predicted). From "6.8 s of generation x 25 = 170 s of wall". That identity
#   cannot support it: aggregate = N x per-request is the DEFINITION of aggregate throughput, so
#   it reproduces the observed wall in a world where vLLM batches perfectly and solo gains nothing.
#
#   136-238 actions (PR #52, measured throughput). Aggregate vLLM generation throughput at one
#   running request is 40.4 tok/s against 341.3 at twenty-five -- 40.4 vs 13.7 per request, a 3.0x
#   speedup, not 25x. Right about the direction; still an over-prediction, because it converted a
#   throughput ratio into an action count.
#
#   80 and 14 actions (B42, RUN). sk48 took 80 against a human level-1 count of 61 (1.31x) and
#   lp85 took 14 against 17 (0.82x). Both land inside that game's own nine-run shared spread, so
#   dropping concurrency 25 -> 1 moved the per-game action count nowhere outside historical noise.
#   B45 names part of the gap: 24.1% (sk48) and 50.8% (lp85) of generated tokens were still in
#   flight when the clock expired, and a throughput measurement counts those while an action
#   counter does not.
#
# B42/B43 both read NO and the NO is not trusted -- the probe never delivered the budget the
# answer rule assumed. This block is kept buildable for a re-run at a budget that does.
_SOLO_TARGET = "__TARGET__"

# The never-submit guard is NOT here -- it is in solo/solo_guard.py, injected at module level
# above `if TRUE_SUBMISSION:`. Everything in THIS file runs inside the else branch, so a guard
# placed here is unreachable whenever TRUE_SUBMISSION is true, which is the only case it is for.
# The comment that used to sit here also had the mechanism backwards: under TRUE_SUBMISSION this
# filter does not "run against 110 live games", it does not run at all.

# FILTER ON env_name, NOT game_id. `taaf.game.Game` declares
#     game_id: str = field(default="", init=False)          (game.py:446)
# and only `_start_game()` populates it (asserted at game.py:473), so at this point every
# game_id is the EMPTY STRING and a prefix test on it matches nothing. Cell 14 builds these as
# GameAPI(env_name=<id>), so env_name is the field carrying the target here. Learned the
# expensive way: the game_id version matched 0 of 25 and fired this assert 483 s in
# (sahasawatt/taaf-solo-sk48 v2, 2026-08-26). The rig could not have caught it -- taaf.game_api
# needs `arcengine`, which is not installed off-Kaggle, so the fake carried whatever shape the
# author believed. The assert now PRINTS what it saw, so the next mismatch diagnoses itself.
_solo_before = list(bm.games)
_solo_ids = [getattr(_g, "env_name", None) or getattr(_g, "game_id", "") for _g in _solo_before]
bm.games = [_g for _g, _i in zip(_solo_before, _solo_ids) if str(_i).startswith(_SOLO_TARGET)]
assert len(bm.games) == 1, (
    f"solo: expected exactly 1 game matching {_SOLO_TARGET!r}, got {len(bm.games)} "
    f"from {len(_solo_before)}; ids seen = {sorted({str(_i) for _i in _solo_ids})}"
)
# game_weights must stay parallel to games (benchmark.py:101). The notebook nulls it two lines
# below, but assert rather than rely on that: a newer bundle could stop doing it.
assert not getattr(bm, "game_weights", None), (
    "solo: bm.game_weights is set; filtering games alone would desync its length"
)
print(
    f"solo: {_SOLO_TARGET} only -- {len(_solo_before)} games -> 1 ({bm.games[0].game_id}); "
    f"the whole per-game clock now belongs to this game",
    flush=True,
)
