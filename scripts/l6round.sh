#!/usr/bin/env bash
# One batch: suite + the AB door experiment, queued while the harness was down.
set -uo pipefail
cd "$(dirname "$0")/.."

uv run python -m pytest -q > results/pytest-movers.txt 2>&1
tail -3 results/pytest-movers.txt

uv run python probes/l6drive.py results/prefix963.txt AB > results/l6-driveAB2.txt 2>&1
echo "=== AB ==="
grep -E "leg1|leg2|NO PLAN|LEVEL|GAME OVER|stopping" results/l6-driveAB2.txt | head -8
tail -8 results/l6-driveAB2.txt | grep -v -E "^(INFO|2026|\[rtk)" || true
