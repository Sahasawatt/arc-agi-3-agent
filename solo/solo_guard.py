# solo probe (B41/B42) -- NEVER-SUBMIT guard. Injected at MODULE level in cell 14, immediately
# before `if TRUE_SUBMISSION:`.
#
# WHY IT IS NOT IN solo_patch.py. The filter must live in cell 14's `else` branch, because that is
# the only place bm.games survives being reassigned. A guard spliced there is spliced into the
# branch that runs when TRUE_SUBMISSION is FALSE -- i.e. it is unreachable in exactly the case it
# names. Measured on the first build of this probe, and still true on master until this file
# existed: with the if/else intact and only the two game-list builders faked, TRUE_SUBMISSION=True
# took the gateway branch, skipped the whole solo block, and left bm.games holding all 110 live
# games with no exception raised. The run would have looked entirely normal and burned the day's
# submission on a diagnostic build.
#
# prove_teeth.py could not see this: it dedents the injected block out of its branch before
# exec'ing it, so the block's own TRUE_SUBMISSION mutation passed while the notebook skipped it.
#
# The guard therefore goes ABOVE the branch, where both paths must pass through it.
assert not TRUE_SUBMISSION, (
    "solo probe: TRUE_SUBMISSION is set. This build plays ONE game and is diagnostic; "
    "it must never be submitted. Rebuild from duckv10 if a real submission is intended."
)
