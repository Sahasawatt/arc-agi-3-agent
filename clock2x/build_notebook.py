"""Build clock2x/taaf-clock-2x-v1.ipynb — v10 plus ONE change: the per-game clock 2x.

`bm.solver.max_runtime_s_per_game` 7920.0 -> 15840.0, gated so it can never apply on a
real competition rerun. Nothing else differs from `duckv10`: same anim bundle, same
Qwen3.8-27B-FP8, output UNCAPPED, no KV flag, no upscale change, no patch.

WHY THIS IS THE CHANGE WORTH A SLOT  (MAP B33, scripts/b27/censoring.py)

Every one of the 125 run-games on record ends at the wall — per-game wallclock min
7920.2 / median 7920.5 / max 7970.3 against a cap of 7920, zero games under 98% of it.
No game has ever stopped on its own logic, so the corpus is RIGHT-CENSORED on depth and
"finished" and "cut" are indistinguishable in every score this campaign holds.

Inside the observed window the level-up rate does not decay: 50.9% / 49.1% across each
game's halves, and the hazard of levelling up within the next 20 actions is 31.9% /
34.4% / 30.4% at K=10/20/30, halving to 14.3% / 15.0% at K=40/60 but never reaching
zero. **None of that shows the rate continues past 7,920s.** That is exactly what
censoring means: it is unobservable from every artifact we hold, which is why it needs
a run and not another probe.

WHY 2x AND NOT 3.64x

Cost is linear on the public 25 — `ceil(25/28) = 1 wave`, so wall == the cap. 2x is
4.4h; the 28,800s figure on record is 8.0h. The hazard above says the second and third
extra windows a 4x run would buy are worth about half the first, and the effect size
below says 2x already clears the noise band by a wide margin if the effect exists at
all. A NOT-DISTINGUISHABLE result at 2x is therefore a real negative, not the
underpowered non-answer v18/B23 produced (p=0.51).

PREDICTIONS — written before the run, as population statistics (the B16 "D-pred" bar)

  P1  wall clock ~4.4h.  If it comes back ~2.2h the field did not propagate to the
      per-game session and THE RUN IS VOID — read this first, before any score.
  P2  actions/game roughly doubles: 63.5 corpus mean (7,938 / 125) -> ~120-130.
  P3  levels.  Baseline is v10cal's 28 over 25 games.  Corpus rate is 1 level-up per
      70.9 actions = 0.896 per run-game.
        rate continues at the corpus average -> ~+0.90/game  -> ~50 levels
        rate continues at the tail hazard    -> ~+0.46/game  -> ~39 levels
        rate stops at the wall               -> 28, unchanged
  P4  public score.  +1 level/game is worth 12.07 public (B20).  A result inside the
      same-build spread [2.82, 4.71] means the rate does NOT continue.
  TEST  eval/rank_runs.py against v10cal, paired per-game sign-flip.  A mean is not a
      rank; p < 0.05 or this run concluded nothing.

WHAT THIS RUN CANNOT DO

It cannot ship. On the hidden 110 games the same setting is `ceil(110/28) = 4 waves x
15840s = 17.6h` against a 9h budget, and `results/wayfinder/R2-levers.md:24-33` shows
`TRUE_SUBMISSION` creates no deadline task at all — the run would be killed mid-wave by
Kaggle with no drain and no partial write. Its whole value is diagnostic: it separates
"the agent is clock-limited" from "the agent is capability-limited", and that
distinction governs every remaining ticket. The one deployable route to a longer
per-game clock is raising concurrency to cut the wave count, which is B16 — v14 raised
effective serving concurrency 11.32x -> 21.23x and turned it into actions 1,285 -> 1,633
with levels 22 -> 19. Closed.

The gate in cell 12 is the enforcement, not a note asking someone to remember: on a real
rerun the bundle's own value is left untouched, so a submitted copy degrades to v10
rather than dying and wasting the slot.

UNVERIFIED, and stated as such: that assigning `bm.solver.max_runtime_s_per_game` reaches
`_HarnessGameSession`. The harness source is not in this repo — it ships as a Kaggle
dataset — so this rests on `R2-levers.md:24-33`'s reading of `solver.py:213-217, 745`
plus cell 11's own instruction to tweak `bm.solver` here. P1 is the check.

Run:  python clock2x/build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_NB = REPO / "duckv10" / "taaf-duck-v10.ipynb"
OUT_NB = REPO / "clock2x" / "taaf-clock-2x-v1.ipynb"

BASELINE_S = 7920.0
MULTIPLE = 2.0

CELL12 = '''# clock-2x-v1 - B34: does the level-up rate continue past the 7,920s wall?
#
# v10 in every respect except ONE: the per-game clock is doubled. See
# clock2x/build_notebook.py for the evidence (MAP B33 - all 125 run-games end at the
# wall, so the corpus is right-censored on depth) and for the predictions, which were
# written before this ran.
#
# NEVER ON A SUBMISSION. On the hidden 110 games this setting is 4 waves x 15840s =
# 17.6h against a 9h budget, and TRUE_SUBMISSION creates no deadline task at all
# (results/wayfinder/R2-levers.md:24-33), so the run would be killed mid-wave with no
# drain and no partial write. The gate below IS the enforcement: on a real rerun the
# bundle's own value is left alone, so a submitted copy degrades to v10 rather than
# dying and wasting the slot.

_BASELINE_S = 7920.0
_MULTIPLE = 2.0

_before = bm.solver.max_runtime_s_per_game
assert _before == _BASELINE_S, (
    "clock-2x: bundle per-game clock is %r, expected %r - the multiple this run would "
    "report is wrong and the envelope arithmetic with it; refusing to guess"
    % (_before, _BASELINE_S)
)

# The clock is only the binding limit while nothing else binds first. R2-levers records
# max_actions_per_game as None (unbounded, "currently never binds - only the clock
# does"); if a bundle ever sets it, doubling the clock measures nothing.
_cap = getattr(bm.solver, "max_actions_per_game", None)
assert _cap is None, (
    "clock-2x: max_actions_per_game is %r, not None - an action cap would bind before "
    "the clock and this run could not test the clock at all" % (_cap,)
)

print("clock-2x: solver=%s concurrency=%r max_actions_per_game=%r"
      % (type(bm.solver).__name__,
         getattr(bm.solver, "concurrency", "?"), _cap), flush=True)

if TRUE_SUBMISSION:
    print("clock-2x: TRUE_SUBMISSION - per-game clock LEFT AT %.1fs. This build must "
          "never run the longer clock on hidden; it is now behaving as v10."
          % _before, flush=True)
else:
    bm.solver.max_runtime_s_per_game = _BASELINE_S * _MULTIPLE
    _after = bm.solver.max_runtime_s_per_game
    assert _after == 15840.0, "clock-2x: assignment did not stick, read back %r" % (_after,)
    print("clock-2x: max_runtime_s_per_game %.1f -> %.1f (%gx). 25 public games, "
          "ceil(25/28)=1 wave, so expect ~4.4h wall. A ~2.2h wall means the field did "
          "not reach the per-game session and THE RUN IS VOID."
          % (_before, _after, _MULTIPLE), flush=True)
'''


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))

    c12 = "".join(nb["cells"][12]["source"])
    assert "duckv10: anim bundle" in c12, "cell 12: not the v10 notebook we expect"
    assert len(c12) < 400, "cell 12 is %d chars - v10's is a 253-char comment; wrong base" % len(c12)
    nb["cells"][12]["source"] = CELL12

    OUT_NB.parent.mkdir(parents=True, exist_ok=True)
    OUT_NB.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"wrote {OUT_NB} ({OUT_NB.stat().st_size} bytes)")

    # --- self-check ---
    src = json.loads(SRC_NB.read_text(encoding="utf-8"))
    out = json.loads(OUT_NB.read_text(encoding="utf-8"))
    diff = [i for i in range(len(src["cells"])) if src["cells"][i]["source"] != out["cells"][i]["source"]]
    assert diff == [12], f"unexpected diff cells: {diff}"

    # Ask the parser, not only the text. duckv14 version 1 passed every content assert
    # and then died on Kaggle with `IndentationError: unexpected indent`.
    cell_src = "".join(out["cells"][12]["source"])
    try:
        compile(cell_src, "cell12", "exec")
    except SyntaxError as exc:
        raise AssertionError(
            f"cell 12 is not valid Python: {type(exc).__name__}: {exc.msg} "
            f"at line {exc.lineno} -> {(exc.text or '').rstrip()!r}"
        ) from None
    print("syntax OK: cell 12 compiles")

    # The inherited v10 configuration must survive untouched - this is a one-variable run.
    o8 = "".join(out["cells"][8]["source"])
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '0'" in o8, "clock-2x: output must stay UNCAPPED (v9)"
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '768'" not in o8, "clock-2x: v9's cap must not be present"
    assert "'fp8'" not in o8, "clock-2x: must not carry v14's KV flag"
    assert "'MULTIMODAL_UPSCALE': '8'" not in o8, "clock-2x: must not carry v18's upscale"
    assert "Qwen3.8-27B-FP8" in o8, "clock-2x: v10's model swap is missing"

    # Teeth on the gate, run against the REAL cell text rather than a hand-written
    # fixture: exec it twice with a stub solver, once as a submission and once not, and
    # assert the value moves in exactly one of them. duckv18 shipped a "teeth" block that
    # asserted a tautology because its fixture was written to match the search string;
    # this one cannot, because the subject IS the string being written to disk.
    class _Stub:
        max_runtime_s_per_game = 7920.0
        max_actions_per_game = None
        concurrency = 28

    class _BM:
        def __init__(self):
            self.solver = _Stub()

    for true_submission, expected in ((True, 7920.0), (False, 15840.0)):
        bm_stub = _BM()
        env = {"bm": bm_stub, "TRUE_SUBMISSION": true_submission, "print": lambda *a, **k: None}
        exec(compile(cell_src, "cell12", "exec"), env)
        got = bm_stub.solver.max_runtime_s_per_game
        assert got == expected, (
            f"teeth: TRUE_SUBMISSION={true_submission} left the clock at {got}, expected {expected}"
        )
    print("teeth OK: gate holds the clock at 7920.0 on TRUE_SUBMISSION, 15840.0 otherwise")

    # And the guards must actually fire, or the two asserts above are decoration.
    for attr, bad, want in (("max_runtime_s_per_game", 3600.0, "refusing to guess"),
                            ("max_actions_per_game", 500, "would bind before")):
        bm_stub = _BM()
        setattr(bm_stub.solver, attr, bad)
        env = {"bm": bm_stub, "TRUE_SUBMISSION": False, "print": lambda *a, **k: None}
        try:
            exec(compile(cell_src, "cell12", "exec"), env)
        except AssertionError as exc:
            assert want in str(exc), f"guard for {attr} fired with the wrong message: {exc}"
        else:
            raise AssertionError(f"guard for {attr} did NOT fire on {bad!r}")
    print("teeth OK: both guards fire (wrong baseline clock, and a non-None action cap)")

    print("self-check OK: cell [12] only; v10 config inherited intact; 7920 -> 15840 gated")


if __name__ == "__main__":
    main()
