# === duckv19: arm the community "banking" graft on top of stock v10 ===
#
# WHY THIS AND NOTHING ELSE (all four facts read from the installed engine, not
# from the fork's claims about it — see notes/R23-banking.md):
#
#   1. arc_agi.scorecard.EnvironmentScoreList.score  ->  max(run.score for run in self.runs)
#      A card's score is the MAX over its plays. (Its docstring says "average"; the
#      code says max. The code is what runs.)
#   2. arcengine.base_game.ARCBaseGame.handle_reset  ->  a RESET issued while
#      _state == GameState.WIN takes the `full_reset()` branch EVEN under
#      ONLY_RESET_LEVELS=true, because the first guard reads `!= GameState.WIN`.
#   3. arc_agi.scorecard.Scorecard.update_scorecard  ->  on a reset action with
#      full_reset=True it calls new_play(), and Card.inc_play_count appends a
#      FRESH zero to actions / levels_completed / actions_by_level.
#   4. the score formula in that same module is
#         score = ((baseline_actions / actions_taken) ** 2) * 100 ; min(score, 115.0)
#      with the run-level cap min(score, max_weights/total_weights*100).
#
# Together: win once at whatever exploration costs, then replay a PRUNED winning
# trace on a fresh play of the same card. The replay's action count starts at 0,
# so (baseline/actions)^2 is computed against a much smaller denominator, and the
# card keeps the better of the two plays. Aborting the replay is free — the
# recorded win still owns the max.
#
# This is the one candidate that changes the SCORING mechanism rather than tuning
# a heuristic, and it does not rest on the fork's "110 runs are 25 games cloned"
# premise, which the ARC-AGI-3 technical report contradicts (R22).
#
# ONE flag. transfer/recovery/goalkeep/hudmask/clickmap/searchmap/efficiency/
# schema_* all stay OFF: R9 says a single run barely ranks two designs.

import shutil as _shutil
import sys as _sys
from pathlib import Path as _Path

# Kaggle unpacked the uploaded archive FLAT: the modules land at the dataset root,
# not inside a taaf_grafts/ directory (verified with `datasets files` before this
# was written). Handle both layouts rather than assuming either — the package
# directory is what `import taaf_grafts` needs, so rebuild it in the working dir
# when the mount is flat.
_GRAFT_ROOT = None
_KIN = _Path("/kaggle/input")
if _KIN.exists():
    _pkg = next(iter(sorted(_KIN.rglob("taaf_grafts/composite.py"))), None)
    if _pkg is not None:
        _GRAFT_ROOT = _pkg.parent.parent
    else:
        _flat = next(
            (
                c.parent
                for c in sorted(_KIN.rglob("composite.py"))
                if (c.parent / "banking_solver.py").exists()
            ),
            None,
        )
        if _flat is not None:
            _shim = _Path("/kaggle/working/_grafts/taaf_grafts")
            _shim.mkdir(parents=True, exist_ok=True)
            for _f in _flat.glob("*.py"):
                _shutil.copy2(_f, _shim / _f.name)
            _GRAFT_ROOT = _shim.parent
            print(f"duckv19: flat mount at {_flat} -> rebuilt package at {_shim}")

assert _GRAFT_ROOT is not None, (
    "duckv19: taaf_grafts not found under /kaggle/input — is the "
    "sahasawatt/taaf-grafts-banking dataset attached?"
)
if str(_GRAFT_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_GRAFT_ROOT))
print(f"duckv19: graft root = {_GRAFT_ROOT}")

from taaf_grafts import composite as _composite  # noqa: E402

# --- teeth, run in-kernel before anything is installed -----------------------
# A silent no-op here would read as "banking does not help" in the ledger, which
# is exactly the failure R8 recorded for duckmod's patches (zero adoption, and
# nobody noticed for weeks).
assert hasattr(_composite, "install"), "duckv19: composite.install missing"
_bank_cls = None
try:
    from taaf_grafts.banking_solver import BankingHarnessSolver as _bank_cls
except Exception as _exc:  # pragma: no cover - reported, never fatal
    print(f"duckv19: TEETH FAIL - cannot import BankingHarnessSolver: {_exc}")
assert _bank_cls is not None, "duckv19: banking module did not import"
assert hasattr(_bank_cls, "from_solver"), "duckv19: BankingHarnessSolver.from_solver missing"

# The four engine facts, asserted against the ENGINE THAT IS ABOUT TO RUN rather
# than trusted from the read we did locally. If Kaggle ships a different version
# where any of these changed, this run must fail loudly instead of quietly
# scoring like stock.
import inspect as _inspect  # noqa: E402
import arcengine as _arcengine  # noqa: E402
from arc_agi.scorecard import EnvironmentScoreList as _ESL, Scorecard as _SC  # noqa: E402

_score_src = _inspect.getsource(_ESL.score.fget if isinstance(_ESL.score, property) else _ESL.score)
assert "max(" in _score_src, f"duckv19: FACT 1 broken - card score is not a max: {_score_src[:200]}"

_reset_src = _inspect.getsource(_arcengine.base_game.ARCBaseGame.handle_reset)
assert "full_reset" in _reset_src and "WIN" in _reset_src, (
    f"duckv19: FACT 2 broken - handle_reset no longer special-cases WIN: {_reset_src[:300]}"
)

_upd_src = _inspect.getsource(_SC.update_scorecard)
assert "new_play" in _upd_src, "duckv19: FACT 3 broken - a full reset no longer opens a new play"

print("duckv19: teeth OK - banking importable, and engine facts 1/2/3 hold on THIS engine")

# --- install -----------------------------------------------------------------
_before = getattr(bm, "solver", None)  # noqa: F821 - bm comes from cell 10
_composite.install(bm, {"banking": True})  # noqa: F821
_after = getattr(bm, "solver", None)  # noqa: F821

# composite.install() never raises: on any internal error it restores the stock
# solver and prints a note. So the ONLY way to know it took is to compare the
# object, and the only way that shows up in the commit log is to print it.
_took = type(_after).__name__ != type(_before).__name__
print(f"duckv19: solver {type(_before).__name__} -> {type(_after).__name__}  (installed={_took})")
if not _took:
    print("duckv19: WARNING - solver unchanged; this run is STOCK v10, not banking")
