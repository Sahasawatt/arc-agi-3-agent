"""Splice the per-request usage probe into a duck notebook's cell 12.

Destination: `duckvNN/build_notebook.py` in the agent repo, beside
`duckvNN/request_usage_probe.py`. Written here because the submodule is not checked out
in this worktree and the version number is the maintainer's call — see
docs/audit/2026-08-23-request-usage-probe.md §5.

WHAT IT PRODUCES

A notebook **byte-identical to its source except cell 12**. That is the point, and the
self-check asserts it: an instrument must not move the thing it measures, so the diff
against the build that scored hidden 1.70 has to be exactly one cell, and that cell has to
be one that only observes.

Cell 12 is the patch slot. It runs after `bm`/`bm.solver` are unpickled (cell 10) and
before `bm.run(...)` (cell 14), so every ToolAgent the run builds is already wrapped —
the analyzer is constructed per game inside `bm.run` (`solver.py:1339 _make_analyzer`).
`duckv10` voids that cell with a `print`; `duckmod` used it to splice `duck_tools.py`.
This follows the same idiom: the module source is inlined verbatim, then `install()` is
called. Two modes, and the builder says which one fired:

  REPLACE — the source's cell 12 is a placeholder (duckv10's print). The probe takes it.
  APPEND  — the source's cell 12 already carries a patch. The probe is appended after it,
            and the builder warns if that patch also touches `_chat_completion`, because
            two wrappers on one method is a real conflict and not one this can resolve.

APPEND is the mode that matters. The cheap path is not a standalone instrument kernel —
that spends a slot of 13 for zero score. It is folding the probe into whatever build runs
next, which is what `--src` is for.

USAGE

    python3 build_notebook.py                       # duckv10 -> thuiv1, sibling probe
    python3 build_notebook.py --src ../duckv16/taaf-duck-v16.ipynb --out ../duckv18/x.ipynb

Run from this file's directory, or pass absolute paths.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# duckv10's cell 12, verbatim. Its presence means the slot is free.
PLACEHOLDER_MARK = "duckmod's patches are dropped"

PROBE_MARK = "# === per-request usage probe:"

HEADER = """# === per-request usage probe: completion_tokens + finish_reason + wall time ===
# Runs after `bm`/`bm.solver` are unpickled (cell 10) and before `bm.run(...)` (cell 14),
# so every ToolAgent built during the run is already wrapped -- the analyzer is
# constructed per game inside bm.run (solver.py:1339 _make_analyzer).
#
# NOT `bm.solver.save_request_logs = True`: that flag writes the full message list on
# both the request and the response event (~150-215 MB for this run) and never writes
# `usage`, which is the one field that can place an output-token cap. duckv9 capped at
# 768 without that distribution and scored 0.22 (finish_reason `length` 704 against
# `tool_calls` 68). See docs/audit/2026-08-23-request-usage-probe.md.

from inference.agent import tool_agent

"""

FOOTER = """

_installed = install(tool_agent)
print(f"request-usage probe installed: {_installed}")
"""


def assert_probe_is_spliceable(source: str, path: Path) -> None:
    """The module must define install() and do nothing at import time.

    Same constraint duckmod documents for `duck_tools.py`: this text is spliced into a
    larger script, so a top-level side effect would fire in the notebook at a moment
    nobody chose. Anything other than imports, constants, and defs is rejected.
    """
    tree = ast.parse(source, filename=str(path))
    names = {
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "install" in names, f"{path}: no install() to call after the splice"
    assert "if __name__" not in source, f"{path}: strip the __main__ block before splicing"
    allowed = (
        ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign,
        ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
    )
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue  # the module docstring
        assert isinstance(node, allowed), (
            f"{path}: top-level side effect at line {node.lineno} "
            f"({type(node).__name__}) — the splice would execute it"
        )


def build_cell12(existing: str, probe_source: str) -> tuple[str, str]:
    """Return (new cell 12 source, mode)."""
    payload = HEADER + probe_source.rstrip("\n") + FOOTER
    if PLACEHOLDER_MARK in existing:
        return payload, "REPLACE"
    for method in ("_chat_completion", "analyze"):
        if f"{method} =" in existing or f"def {method}" in existing:
            print(
                f"  CONFLICT: cell 12 already rebinds ToolAgent.{method}, which this probe\n"
                f"            also wraps. Two wrappers on one method is not something this\n"
                f"            builder can resolve — merge them by hand or drop one.",
                file=sys.stderr,
            )
            break
    else:
        if "ToolAgent" in existing:
            print(
                "  note: cell 12 already patches ToolAgent, but not a method this probe\n"
                "        wraps. Appending. Read both patches before running.",
                file=sys.stderr,
            )
    return existing.rstrip("\n") + "\n\n" + payload, "APPEND"


def build_metadata(
    src_meta: Path,
    out_nb: Path,
    *,
    owner: str | None = None,
    title: str | None = None,
) -> dict:
    meta = json.loads(src_meta.read_text(encoding="utf-8"))
    if owner is None:
        owner = str(meta["id"]).split("/", 1)[0]
    meta["id"] = f"{owner}/{out_nb.stem}"
    meta["title"] = out_nb.stem if title is None else title
    meta["code_file"] = out_nb.name
    return meta


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", default=str(HERE.parent / "duckv10" / "taaf-duck-v10.ipynb"))
    ap.add_argument("--out", default=str(HERE / "taaf-thui-v1.ipynb"))
    ap.add_argument("--probe", default=str(HERE / "request_usage_probe.py"))
    ap.add_argument("--owner")
    ap.add_argument("--title")
    args = ap.parse_args(argv)

    src_nb, out_nb, probe = Path(args.src), Path(args.out), Path(args.probe)
    for p in (src_nb, probe):
        assert p.is_file(), f"missing: {p}"

    probe_source = probe.read_text(encoding="utf-8")
    assert_probe_is_spliceable(probe_source, probe)

    nb = json.loads(src_nb.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) > 12, f"{src_nb}: only {len(cells)} cells, no cell 12"
    assert cells[12]["cell_type"] == "code", f"{src_nb}: cell 12 is {cells[12]['cell_type']}"

    before = ["".join(c["source"]) for c in cells]
    new12, mode = build_cell12(before[12], probe_source)
    compile(new12, "<cell12>", "exec")          # a cell that will not parse is not a build
    cells[12]["source"] = new12

    out_nb.parent.mkdir(parents=True, exist_ok=True)
    out_nb.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"wrote {out_nb} ({out_nb.stat().st_size} bytes) — cell 12 mode: {mode}")

    src_meta = src_nb.parent / "kernel-metadata.json"
    if src_meta.is_file():
        meta = build_metadata(src_meta, out_nb, owner=args.owner, title=args.title)
        (out_nb.parent / "kernel-metadata.json").write_text(
            json.dumps(meta, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote {out_nb.parent / 'kernel-metadata.json'} — kernel id {meta['id']}")

    # --- self-check: re-read what was written, not what is in memory ---
    src_cells = [
        "".join(c["source"]) for c in json.loads(src_nb.read_text(encoding="utf-8"))["cells"]
    ]
    out_cells = [
        "".join(c["source"]) for c in json.loads(out_nb.read_text(encoding="utf-8"))["cells"]
    ]
    assert len(src_cells) == len(out_cells), "cell count changed"
    diff = [i for i in range(len(src_cells)) if src_cells[i] != out_cells[i]]
    assert diff == [12], f"the instrument moved more than cell 12: {diff}"
    assert PROBE_MARK in out_cells[12], "probe header missing from the written cell"
    assert "install(tool_agent)" in out_cells[12], "install() call missing"
    compile(out_cells[12], "<cell12>", "exec")
    if mode == "REPLACE":
        assert PLACEHOLDER_MARK not in out_cells[12], "placeholder survived a REPLACE"
    else:
        assert out_cells[12].startswith(src_cells[12].rstrip("\n")), "APPEND clobbered the patch"
    if src_meta.is_file():
        src_m = json.loads(src_meta.read_text(encoding="utf-8"))
        out_m = json.loads((out_nb.parent / "kernel-metadata.json").read_text(encoding="utf-8"))
        for key in ("dataset_sources", "competition_sources", "docker_image", "machine_shape"):
            assert src_m.get(key) == out_m.get(key), (
                f"kernel-metadata {key} changed — an instrument must not change the build"
            )
        assert out_m["id"] != src_m["id"], "kernel id must be new or the push overwrites the source"
    print(f"self-check OK: diff == [12], mode {mode}, build inputs unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
