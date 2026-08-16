"""Extract the official sample agent's source out of the starter kit's notebook.

    ./.venv/Scripts/python.exe kaggle/goose_extract.py

The competition ships its baseline ("StochasticGoose", Tufa Labs --
github.com/DriesSmit/ARC3-solution, MIT) as a `%%writefile` cell inside
`reference/stochastic-goose/arc3-sample-submission-stochastic-goose.ipynb` in
the starter kit.  `kaggle/bundle_hybrid.py` needs it as a plain module.

**The extracted file is written into the STARTER KIT, never into this repo.**
This repo is MIT-0 and vendoring a third party's MIT source into it would
relicense their work; the starter kit is a local working copy of someone
else's repository, which is where their code belongs.  Its own attribution
header travels with it either way.

Why the sample matters here: our submissions score 0.01-0.11 against its
~1.56, and the shape of the gap is legible in its code -- it learns online,
per game, which of ACTION1-5 *and which of the 4,096 click coordinates* change
the frame.  A uniform random click is worth ~nothing on a click-driven game;
a learned coordinate head is not.
"""
from __future__ import annotations

import json
from pathlib import Path

STARTER = Path(r"C:\Users\Vampi\Desktop\ARC-AGI-3-Kaggle-Starter")
NB = (STARTER / "reference" / "stochastic-goose"
      / "arc3-sample-submission-stochastic-goose.ipynb")
OUT = STARTER / "reference" / "stochastic-goose" / "goose_agent.py"
MAGIC = "%%writefile"


def main() -> None:
    nb = json.loads(NB.read_text(encoding="utf-8"))
    cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
    hits = [c for c in cells if c.lstrip().startswith(MAGIC) and "class MyAgent" in c]
    if len(hits) != 1:
        raise SystemExit(
            f"expected exactly one {MAGIC} cell defining MyAgent, found {len(hits)} "
            "-- the notebook's shape changed; read it before trusting this script")
    body = hits[0].split("\n", 1)[1]        # drop the %%writefile line itself
    if "class MyAgent(Agent)" not in body:
        raise SystemExit("the extracted cell does not define MyAgent(Agent)")
    OUT.write_text(body, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    print(f"  defines: {[l for l in body.splitlines() if l.startswith('class ')]}")


if __name__ == "__main__":
    main()
