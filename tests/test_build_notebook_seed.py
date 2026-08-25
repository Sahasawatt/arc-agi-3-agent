"""`--seed` must reject a value the runtime would silently drop.

`openai_compat.build_chat_payload` sets `payload["seed"]` only under
`seed is not None and seed >= 0`, and `-1` is the runtime's own default for "no seed"
(`tool_agent._get_env_int("LOCAL_ANALYZER_SEED", -1)`). So before this gate, `--seed -1`
produced a notebook that passed the builder's own post-build self-check AND the four
in-kernel teeth -- both of which test for the literal string, never the sign -- and printed
"sampler pinned" over inference that was never seeded.
"""

import importlib.util
from pathlib import Path

import pytest

_BN = Path(__file__).resolve().parent.parent / "thuiv1" / "build_notebook.py"
_spec = importlib.util.spec_from_file_location("thuiv1_build_notebook", _BN)
build_notebook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_notebook)

# A source that cannot exist, so every case below stops before anything is written.
MISSING = str(Path(__file__).resolve().parent / "no-such-source.ipynb")


def test_negative_seed_is_rejected():
    with pytest.raises(AssertionError, match=">= 0"):
        build_notebook.main(["--seed", "-1", "--src", MISSING])


def test_non_integer_seed_is_rejected():
    with pytest.raises(AssertionError, match=">= 0"):
        build_notebook.main(["--seed", "later", "--src", MISSING])


def test_a_valid_seed_reaches_the_source_check():
    """Positive control: it must fail on the MISSING source, i.e. downstream of the seed gate.

    Without this, a gate that rejected every seed would pass both tests above.
    """
    with pytest.raises(AssertionError, match="missing:"):
        build_notebook.main(["--seed", "20260825", "--src", MISSING])


def test_omitting_the_seed_reaches_the_source_check():
    with pytest.raises(AssertionError, match="missing:"):
        build_notebook.main(["--src", MISSING])
