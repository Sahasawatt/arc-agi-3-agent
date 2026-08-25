"""A non-finite score must be a data error, never a verdict.

Before the guard in `load()`, a NaN was laundered into a confident directional answer rather
than a crash: one NaN poisons `sum(d_score)`; inside `perm_test` every `abs(m) >= obs - 1e-12`
is a NaN comparison and therefore False, so `hits` stays 0 and `p` is exactly 0.0; back in
`compare()`, `p < ALPHA` is True and `sum(d_score) > 0` is False, selecting "WORSE".
`json.load` parses a bare unquoted `NaN` token by default, so it arrives silently, and
`--selftest` cannot see it -- it loads three known-clean fixtures and only checks the labels.
"""

import importlib.util
import json
from pathlib import Path

import pytest

_RR = Path(__file__).resolve().parent.parent / "eval" / "rank_runs.py"
_spec = importlib.util.spec_from_file_location("rank_runs", _RR)
rank_runs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rank_runs)

FIXTURES = _RR.parent / "fixtures"


def _clean_games() -> dict:
    with open(FIXTURES / "v10cal.json", encoding="utf-8") as fh:
        return json.load(fh)["games"]


def _write(tmp_path, games) -> str:
    p = tmp_path / "run.json"
    p.write_text(json.dumps({"label": "under-test", "games": games}), encoding="utf-8")
    return str(p)


def test_a_clean_fixture_still_loads():
    """Positive control: a load() that rejected everything would pass every test below."""
    assert len(rank_runs.load(str(FIXTURES / "v10cal.json"))["games"]) == 25


def test_nan_score_is_a_data_error(tmp_path):
    games = _clean_games()
    games[next(iter(games))]["score"] = float("nan")
    with pytest.raises(SystemExit, match="non-finite"):
        rank_runs.load(_write(tmp_path, games))


def test_bare_nan_token_in_json_is_a_data_error(tmp_path):
    """This is the arrival path: an unquoted NaN, which json.load accepts by default."""
    p = tmp_path / "raw.json"
    p.write_text(
        '{"label": "x", "games": {"aa11": {"score": NaN, "levels": 1, "actions": 5}}}',
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="non-finite"):
        rank_runs.load(str(p))


def test_infinite_levels_is_a_data_error(tmp_path):
    games = _clean_games()
    games[next(iter(games))]["levels"] = float("inf")
    with pytest.raises(SystemExit, match="non-finite"):
        rank_runs.load(_write(tmp_path, games))


def test_null_score_is_a_data_error(tmp_path):
    """None reaches `None > 0` and raises TypeError -- loud, but not the file's own error code."""
    games = _clean_games()
    games[next(iter(games))]["score"] = None
    with pytest.raises(SystemExit, match="non-finite"):
        rank_runs.load(_write(tmp_path, games))
