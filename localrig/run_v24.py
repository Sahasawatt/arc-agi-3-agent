"""Rig runner: apply the duckv24 untried-ledger patch, then run the harness.

Usage (from localrig/ARC3-Inference, with the LOCAL_ANALYZER_* env block):
    ../.venv/Scripts/python.exe ../run_v24.py --game ft09 --max-actions 30 ...
All argv after the script name pass straight to inference.framework.run.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "duckv24"))
import ledger_patch  # noqa: E402  (teeth run at import)

print(ledger_patch.apply(), flush=True)

from inference.framework import run  # noqa: E402

if __name__ == "__main__":
    sys.argv = [sys.argv[0], *sys.argv[1:]]
    run.main()
