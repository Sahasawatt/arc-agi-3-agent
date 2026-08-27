#!/usr/bin/env python3
"""Rewrite cell 0 of our notebooks so the page says whose work it is.

Every build copies its base notebook and patches one cell, so cell 0 has been inherited
verbatim from Tufa Labs' published notebook all the way down the chain.  The result is a
public page titled "Tufa Labs ARC3 submission", carrying their logo, their author list and
their first-person claim to a 1.21 milestone score -- on a Thuitanium submission.

The fix is attribution, not removal: every name and every link Tufa put there survives in
kaggle/cell0_header.md.  What changes is the title, the logo attachment, and the first person.

Idempotent.  Skips localrig/ -- those notebooks are Tufa's own vendored files and are not ours
to retitle.  Run with --check to verify without writing.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
HEADER = HERE / "cell0_header.md"

OLD_TITLE = "# Tufa Labs ARC3 submission"
NEW_TITLE = "# Thuitanium — ARC-AGI-3 (a fork of the Tufa Labs duck harness)"
LOGO = "tufa_labs.png"
# Tufa's own vendored framework -- their file, their title.  Retitling it would be the same
# error in the other direction.
SKIP_PREFIX = "localrig/"


def tracked_notebooks() -> list[pathlib.Path]:
    out = subprocess.run(
        ["git", "ls-files", "*.ipynb"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split()
    return [REPO / p for p in out if not p.startswith(SKIP_PREFIX)]


def main() -> int:
    check_only = "--check" in sys.argv
    header = HEADER.read_text(encoding="utf-8").rstrip("\n")
    source = [ln + "\n" for ln in header.split("\n")]
    source[-1] = source[-1].rstrip("\n")

    changed, already, untouched = [], [], []
    for path in tracked_notebooks():
        nb = json.loads(path.read_text(encoding="utf-8"))
        cell = nb["cells"][0]
        text = "".join(cell["source"])
        if text.startswith(NEW_TITLE):
            already.append(path)
            continue
        if not text.startswith(OLD_TITLE):
            # A notebook whose cell 0 is neither shape: leave it and say so, rather than
            # overwriting something nobody looked at.
            untouched.append(path)
            continue
        cell["source"] = source
        attach = cell.get("attachments") or {}
        attach.pop(LOGO, None)
        if attach:
            cell["attachments"] = attach
        else:
            cell.pop("attachments", None)
        if not check_only:
            path.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
        changed.append(path)

    verb = "would rewrite" if check_only else "rewrote"
    print(f"{verb}: {len(changed)}   already correct: {len(already)}   left alone: {len(untouched)}")
    for p in untouched:
        print(f"  LEFT ALONE (cell 0 is neither shape): {p.relative_to(REPO)}")
    # A run that finds nothing is a broken selector, not a clean repo -- say so loudly.
    if not changed and not already:
        print("NOTHING MATCHED -- selector is broken, not the corpus", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
