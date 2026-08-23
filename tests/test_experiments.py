"""Tests for the search chains in `experiments/`.

Nothing imported these files. Every chain has zero importers outside its own directory,
so the 330-test suite ran green over them the whole time they sat in the repo root, and
would have kept running green if a rename had broken all seven at once. That is what
happened on 2026-08-23: the chains moved from the root into `experiments/`, and four of
them import a driver that stayed behind (`swap`, `haul`) while three import siblings that
live in `probes/`. A suite that never touches a file cannot report that the file stopped
resolving.

So these tests assert the one property the chains actually have: **each one can find its
imports under the search path its README documents.** They resolve imports statically and
never execute a chain — a chain is a multi-hour search job that reads and writes its own
checkpoints, and importing one for a test would be a side effect, not a check.

The bundler invariant is here for the same reason. `kaggle/bundle.py` embeds engine
modules by bare name from the repo root, so moving a file it lists breaks the Kaggle
submission with nothing in the suite to say so.
"""

import ast
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS = ROOT / "experiments"

# Each chain needs exactly ONE directory besides its own on the path, because a script's
# own directory is sys.path[0]. `experiments/README.md` publishes this same table.
CHAIN_PATH = {
    "dc22_c4_hidden": "probes",
    "dc22_c5_soundchain": "probes",
    "re86_b2_l6chain": "probes",
    "sp80_s11": ".",
    "sp80_s12": ".",
    "sp80_s13": ".",
    "wa30_b2_l3chain": ".",
}

# Installed by uv, not files in this repo. Kept explicit: an import that is neither stdlib
# nor listed here is a repo module and must resolve to a file, which is the whole point.
THIRD_PARTY = {"numpy", "arcengine", "arc_agi", "pytest"}


def imported_module_names(path):
    """Top-level names this file imports, minus stdlib and installed packages."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
    return {n for n in names if n not in sys.stdlib_module_names and n not in THIRD_PARTY}


def unresolved(chain, search_dirs):
    """Repo modules `chain` imports that no directory in `search_dirs` provides."""
    return sorted(
        name
        for name in imported_module_names(EXPERIMENTS / f"{chain}.py")
        if not any((d / f"{name}.py").exists() or (d / name / "__init__.py").exists()
                   for d in search_dirs)
    )


def bundled_modules():
    """The module list `kaggle/bundle.py` splices into the submission, in file order."""
    src = (ROOT / "kaggle" / "bundle.py").read_text(encoding="utf-8")
    block = re.search(r"MODULES\s*=\s*\[(.*?)\]", src, re.S)
    assert block, "kaggle/bundle.py no longer declares MODULES = [...]"
    return re.findall(r'"([a-z0-9_]+)"', block.group(1))


# --- the collection must not be empty ----------------------------------------------
# Every test below is "for each chain ...". With an empty mapping or an empty directory
# they all pass having checked nothing, so the count is asserted before anything else.

def test_every_chain_on_disk_is_covered_by_the_path_table():
    on_disk = {p.stem for p in EXPERIMENTS.glob("*.py")}
    assert on_disk, f"no chains found in {EXPERIMENTS} — the glob or the directory moved"
    assert on_disk == set(CHAIN_PATH), (
        "experiments/ and CHAIN_PATH disagree. "
        f"only on disk: {sorted(on_disk - set(CHAIN_PATH))}; "
        f"only in the table: {sorted(set(CHAIN_PATH) - on_disk)}"
    )


# --- the property that broke when the files moved -----------------------------------

@pytest.mark.parametrize("chain", sorted(CHAIN_PATH))
def test_chain_resolves_every_import_under_its_documented_path(chain):
    extra = ROOT / CHAIN_PATH[chain]
    missing = unresolved(chain, [EXPERIMENTS, extra])
    assert not missing, (
        f"experiments/{chain}.py cannot find {missing} with PYTHONPATH={CHAIN_PATH[chain]}. "
        "Either the import moved or experiments/README.md is now wrong."
    )


def test_the_resolver_reports_a_chain_that_cannot_find_its_imports():
    """Positive control: a resolver that never fails cannot detect a broken chain.

    `sp80_s13` imports `swap`, which lives at the repo root and not in `probes/`, so
    pointing it at `probes/` must come back unresolved. If this ever passes as resolved,
    the failure is in `unresolved()` and every assertion above is decoration.
    """
    missing = unresolved("sp80_s13", [EXPERIMENTS, ROOT / "probes"])
    assert "swap" in missing, (
        "sp80_s13 resolved 'swap' from probes/ — either swap.py was copied there, "
        "or unresolved() stopped detecting anything"
    )


# --- the chains must never reach the submission -------------------------------------

def test_no_chain_is_spliced_into_the_kaggle_bundle():
    modules = bundled_modules()
    assert modules, "MODULES parsed as empty — the regex no longer matches bundle.py"
    leaked = sorted(set(modules) & set(CHAIN_PATH))
    assert not leaked, (
        f"{leaked} are experiment chains and are being embedded in kaggle/my_agent.py. "
        "Chains are dated spikes; only drivers and engine modules ship."
    )


def test_every_bundled_module_still_sits_at_the_repo_root():
    """`bundle.py` reads `ROOT / f'{name}.py'`, so a module it lists cannot move.

    This is the guard the 2026-08-23 move needed and did not have: moving a *driver*
    into a subdirectory raises FileNotFoundError at build time, long after the commit.
    """
    absent = [m for m in bundled_modules() if not (ROOT / f"{m}.py").exists()]
    assert not absent, (
        f"kaggle/bundle.py lists {absent}, which are no longer at the repo root. "
        "Either move them back or teach bundle.py a path."
    )


# --- the documented invocation must stay documented ---------------------------------

def test_readme_names_every_chain_and_its_path():
    readme = EXPERIMENTS / "README.md"
    assert readme.exists(), "experiments/README.md is gone; the invocations live nowhere else"
    text = readme.read_text(encoding="utf-8")
    unnamed = sorted(c for c in CHAIN_PATH if c not in text)
    assert not unnamed, f"experiments/README.md does not mention {unnamed}"
    for chain, path in CHAIN_PATH.items():
        assert f"PYTHONPATH={path}" in text, (
            f"README never shows PYTHONPATH={path}, which {chain} needs"
        )
