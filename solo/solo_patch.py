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
# WHAT IT PROVES. Every game today shares one vLLM server: an action costs 6.8 s of generation
# but 170 s of wall, and 6.8 x 25 = 170.7 s reproduces the observed 170.0 s. Solo, the same clock
# buys ~1,099 actions instead of 46. B43 reads whether that budget converts to levels.
_SOLO_TARGET = "__TARGET__"

# A solo notebook must never play the competition. It would not even do what its name says --
# cell 14's TRUE_SUBMISSION branch rebuilds bm.games from the gateway and this filter would run
# against 110 live games -- but the run would still burn the day's submission on a diagnostic.
assert not TRUE_SUBMISSION, (
    "solo probe: TRUE_SUBMISSION is set. This build is diagnostic and must never be submitted."
)

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
