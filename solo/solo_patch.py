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
# WHAT IT PROVES. Every game today shares one vLLM server, so solo removes contention -- it does
# not lengthen the clock. HOW MUCH it removes is measured, not assumed: aggregate vLLM generation
# throughput at one running request is 40.4 tok/s against 341.3 at twenty-five, i.e. 40.4 vs 13.7
# per request, a 3.0x speedup (5.2x on the most generous reading). See MAP B41 and PR #52. That
# is ~136-238 actions per game on the full 7,920 s clock, against 46 today.
#
# The identity "6.8 s of generation x 25 = 170 s of wall" that first motivated this probe cannot
# support a 25x figure: aggregate = N x per-request is the DEFINITION of aggregate throughput, so
# it reproduces the observed wall in a world where vLLM batches perfectly and solo gains nothing.
# B43 reads whether the measured 3x budget converts to levels.
_SOLO_TARGET = "__TARGET__"

# The never-submit guard is NOT here -- it is in solo/solo_guard.py, injected at module level
# above `if TRUE_SUBMISSION:`. Everything in THIS file runs inside the else branch, so a guard
# placed here is unreachable whenever TRUE_SUBMISSION is true, which is the only case it is for.
# The comment that used to sit here also had the mechanism backwards: under TRUE_SUBMISSION this
# filter does not "run against 110 live games", it does not run at all.

_solo_before = list(bm.games)
bm.games = [_g for _g in _solo_before if _g.game_id.startswith(_SOLO_TARGET)]
assert len(bm.games) == 1, (
    f"solo: expected exactly 1 game matching {_SOLO_TARGET!r}, got {len(bm.games)} "
    f"from {len(_solo_before)} -- prefix wrong, or the offline env set changed"
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
