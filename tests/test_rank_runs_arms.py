"""The baseline is a choice, and until MAP B57 nothing recorded that one was made.

`rank_runs.py` pairs a candidate against *a* baseline. Four runs of the v10 build are banked, and
which one is passed moves the p-value by 1.7x-7.1x -- `clock2x` reads 0.2761 against `v10cal` and
0.0828 against `v19`. B34 was closed on the first of those with no artifact naming the other five.

`--selftest` cannot cover this on its own: it calls `compare()` directly, so a guard wired only
into `main()` would be invisible to it, and a guard wired nowhere would still let every control
pass. The wiring tests below are the half that sees that, and the two published-pairing tests are
the control that the guard did not move the arithmetic it stands in front of.
"""

import importlib.util
import json
from pathlib import Path

_RR = Path(__file__).resolve().parent.parent / "eval" / "rank_runs.py"
_spec = importlib.util.spec_from_file_location("rank_runs", _RR)
rank_runs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rank_runs)

FIXTURES = _RR.parent / "fixtures"
V10CAL = str(FIXTURES / "v10cal.json")
CLOCK2X = str(FIXTURES / "clock2x.json")
REASON = "reproducing B34's published v10cal pairing"


# --- the manifest itself -------------------------------------------------------------------

def test_the_manifest_declares_a_multi_run_arm():
    """Positive control: a manifest that resolved nothing would pass every negative below."""
    arms = rank_runs.load_arms()
    found = rank_runs.arm_of("v10cal", arms)
    assert found is not None
    assert len(found[1]) >= 2


def test_a_run_of_its_own_build_is_claimed_by_no_arm():
    """Negative control. Membership is declared, never inferred: v20 is NOT-DISTINGUISHABLE from
    plenty of things, and a manifest built from p-values would swallow it."""
    assert rank_runs.arm_of("v20", rank_runs.load_arms()) is None


def test_every_declared_member_is_actually_banked():
    """A ghost member exempts nothing and pools nothing -- it just makes the arm look bigger."""
    arms = rank_runs.load_arms()
    missing = [m for members in arms.values() for m in members
               if not (FIXTURES / f"{m}.json").exists()]
    assert missing == []


# --- the escape hatch ----------------------------------------------------------------------

def test_the_printed_placeholder_is_not_a_reason():
    """The refusal prints `--single-baseline PASTE_YOUR_REASON_HERE`, and a guard's own
    remediation line is the exact string an operator pastes back."""
    assert rank_runs.check_reason("PASTE_YOUR_REASON_HERE") is not None
    assert rank_runs.check_reason("<one sentence: why this run>") is not None
    assert rank_runs.check_reason("{{reason}}") is not None
    assert rank_runs.check_reason("TODO") is not None


def test_a_short_token_is_not_a_reason():
    assert rank_runs.check_reason("ok") is not None


def test_a_real_reason_is_accepted():
    """Polarity control: a checker that rejected everything would pass the four asserts above."""
    assert rank_runs.check_reason(REASON) is None


# --- the wiring, which no --selftest control can see ---------------------------------------

def test_main_refuses_a_single_run_of_a_banked_arm(capsys):
    assert rank_runs.main([V10CAL, CLOCK2X]) == 4
    out = capsys.readouterr().out
    assert "REFUSED" in out
    assert "pool_runs.py" in out          # the remediation, not just the complaint
    assert "VERDICT" not in out           # a refusal prints no verdict to read past


def test_main_accepts_a_pooled_baseline(tmp_path, capsys):
    with open(V10CAL, encoding="utf-8") as fh:
        games = json.load(fh)["games"]
    p = tmp_path / "pooled.json"
    p.write_text(json.dumps({"label": "pool(v10cal+v19)", "games": games}), encoding="utf-8")
    assert rank_runs.main([str(p), CLOCK2X]) == 0
    assert "VERDICT" in capsys.readouterr().out


def test_main_accepts_a_stated_reason_and_prints_it_into_the_report(capsys):
    """The reason has to ride inside the block a reader copies, or the artifact B57 wants
    does not exist."""
    assert rank_runs.main([V10CAL, CLOCK2X, "--single-baseline", REASON]) == 0
    out = capsys.readouterr().out
    assert REASON in out
    assert "SINGLE-BASELINE" in out


def test_main_refuses_the_placeholder_as_usage(capsys):
    assert rank_runs.main([V10CAL, CLOCK2X, "--single-baseline", "PASTE_YOUR_REASON_HERE"]) == 2
    assert "VERDICT" not in capsys.readouterr().out


def test_a_pair_with_no_banked_siblings_is_untouched(capsys):
    """The guard must not become a tax on every comparison."""
    assert rank_runs.main([str(FIXTURES / "v18.json"), str(FIXTURES / "v20.json")]) == 0
    assert "REFUSED" not in capsys.readouterr().out


def test_a_blind_arm_check_says_so_in_the_report(monkeypatch, capsys):
    """A missing manifest must not fail silently: a gate cannot report its own skip."""
    def boom(path=None):
        raise OSError("no manifest")
    monkeypatch.setattr(rank_runs, "load_arms", boom)
    assert rank_runs.main([V10CAL, CLOCK2X]) == 0
    out = capsys.readouterr().out
    assert "ARM CHECK DID NOT RUN" in out
    assert "ARM CHECK BLIND" in out       # inside the report, not only on a line above it


# --- the guard did not move the arithmetic it stands in front of ---------------------------

def test_the_published_single_baseline_number_is_unchanged():
    r = rank_runs.compare(rank_runs.load(V10CAL), rank_runs.load(CLOCK2X))
    assert r["p_score"] == 0.2761
    assert r["verdict"] == "NOT-DISTINGUISHABLE"


def test_the_published_pooled_number_is_unchanged(tmp_path):
    """B57's own figure, reached through the command the refusal prints."""
    import importlib.util as _u
    pr_path = _RR.parent / "pool_runs.py"
    spec = _u.spec_from_file_location("pool_runs", pr_path)
    pool_runs = _u.module_from_spec(spec)
    spec.loader.exec_module(pool_runs)

    members = rank_runs.load_arms()["v10"]
    out = tmp_path / "arm.json"
    pool_runs.write(str(out), [pool_runs.load(str(FIXTURES / f"{m}.json")) for m in members],
                    [m for m in members])
    r = rank_runs.compare(rank_runs.load(str(out)), rank_runs.load(CLOCK2X))
    assert r["mean_a"] == 4.28
    assert r["p_score"] == 0.2095
