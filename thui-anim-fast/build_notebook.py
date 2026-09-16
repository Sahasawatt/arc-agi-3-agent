"""thui-animfast-b71-full25-r1 -- the ANIM solver on Keith Tyser's Flash-Next serving stack, on our slug.

WHAT THIS SCRIPT IS, AND WHAT IT IS NOT. It is not Sahasawat's build script. His notebook
(`sahasawatt/thui-animfast-v1`) was authored elsewhere and its own cell 0 cites a
`thui-anim-fast/build_notebook.py` that does not exist in this repo -- searched 2026-09-11 for
`animfast`, `anim-fast` and `anim_fast` across all 69 remote branch tips, 0 hits in paths and 0 in
contents, against a control that found `notes/wayfinder/MAP.md` on 69 of 69. So this script does not
reconstruct his authoring. It VENDORS the two upstreams, asserts every link in the provenance chain,
applies the only edits that are ours, and reproduces byte-for-byte the notebook that was actually
pushed and ran. That is a weaker claim than "this is how it was built" and a stronger artifact than a
transcription would be, because every assertion below is checkable against the vendored files.

THE CHAIN.

  keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp        (vendored: upstream-keithtyser-*.ipynb + its metadata)
    Tufa Labs' June duck bundle with ONLY the serving replaced -- the pinned
    RadixArk/Qwen3.8-Flash-Next-NVFP4 checkpoint, his offline vLLM runtime, NVFP4 PLE patch,
    MTP-3 speculative decoding profile, server watchdog. 18 cells. This is also the base of
    `thui-fast/`, and the two vendored copies are asserted byte-identical below.
        |
        |  Sahasawat's graft -- 8 cells: 0, 1, 3, 5, 7, 9, 11, 15.
        |  MEASURED against the vendored upstream, not taken from his cell 0's prose; the two
        |  agree exactly, which is the one claim on that page that does hold.
        v
  sahasawatt/thui-animfast-v1                         (vendored: upstream-sahasawatt-*.ipynb + its metadata)
    The anim SOLVER bundle `jakobbrggen/taaf-kaggle-source-anim-20260807-anim`
    (Jakob Bruggen's feature/animation-awareness) replaces Keith's June copy on sys.path, plus the
    thui-v3 knobs LOCAL_ANALYZER_SEED=20260825 and LOCAL_ANALYZER_YIELD_SECONDS=180. So the arm is
    B69's own chassis with the SOLVER swapped -- NOT the anim-base lineage, which is a different
    branch. Its comparator is therefore the Flash-Next family's own hidden draws.
    v0 and v1 differ at cells 0 and 15 only (header, and the competition mount resolved instead of
    hardcoded because Kaggle serves two layouts); v1 is the corrected one and is what is vendored.
        |
        |  OURS, and it is one cell: cell 0 only.
        v
  yocybercode/thui-animfast-b71-full25-r1             (emitted: thui-animfast-b71-full25-r1.ipynb)

WHAT IS OURS. Cell 0, twice:
  1. the H1's kernel name, so the page names the kernel it is. The "(Thuitanium / Knowless Crew)"
     clause is kept verbatim in the H1 because that is what the submit gate's G2 position lane reads.
  2. the provenance footer. His read "Build script: thui-anim-fast/build_notebook.py in our agent
     repo ... Ticket B71." Both were false when the notebook was pushed -- the script was absent (see
     above) and no B71 row existed on any of the 69 tips, whose id ceiling was B79 -- so rather than
     republish two wrong citations on a public page they were replaced with what is measurable.
  NOTHING ELSE. No solver, serving, budget or settings cell is touched, and the assert below fails if
  one is.

  NOTE, because a published notebook cannot be edited without minting a version: the footer's
  "Ticket B71 is likewise PROPOSED, not minted" is a DATED reading, true at 2026-09-11 when the
  kernel was pushed. If the B71 MAP row this branch proposes is merged, the row supersedes it and the
  notebook's sentence stays correct as a record of what was true at push time. Its other sentence --
  that the build script which produced the UPSTREAM notebook is not in this repo -- is unaffected by
  this file existing, because this file does not produce that notebook.

TEETH, and what they do NOT cover. Eight one-file mutations of the vendored inputs all exit non-zero
with the clean build green between every round and the inputs restored byte-identical, but only SEVEN
fire on the assert they were written for: the anim bundle (cell 7), the MTP-3 profile (cell 3), the
upstream base identity (cell 0), the seed pin (cell 9, and only once EVERY occurrence is mutated --
`20260825` appears twice, so a first-occurrence replace slips past it and is caught later by the
reproduction check), the vendored-copy drift against thui-fast, the metadata graft control against
his own file, and the byte reproduction of the notebook that ran.
  Two groups are NOT independently reachable by mutation and are defence-in-depth, not proved:
  - the cell-13 full25 asserts. Mutating the graft moves the grafted-cell set and that assert fires
    first; mutating the upstream trips the thui-fast twin check first. They can only speak if BOTH
    vendored copies are re-vendored consistently AND the settings change with them -- which is the
    exact scenario they exist for, and is not a one-file edit.
  - the two G2 index asserts (`Thuitanium` before `Tufa Labs` / `Keith Tyser`). The H1 anchor contains
    `Thuitanium`, so removing it to violate the ordering destroys the anchor and fails earlier. Kept
    because the anchor is what would be relaxed first if the header is ever reworded.

Build:  PYTHONUTF8=1 python thui-anim-fast/build_notebook.py
Push:   python scripts/kaggle_push_kernel.py repos/arc-agi-3-agent/thui-anim-fast
        (from arc-agi-pub; the destination is decided by the TOKEN, never by the id -- ours is
        yocybercode, and the gate refuses when the two disagree)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_UP = HERE / "upstream-keithtyser-duck-qwen3-8-flash-next-nvfp4-mtp.ipynb"
SRC_GRAFT = HERE / "upstream-sahasawatt-thui-animfast-v1.ipynb"
SRC_META = HERE / "upstream-kernel-metadata.json"                        # Keith Tyser's
SRC_GRAFT_META = HERE / "upstream-sahasawatt-thui-animfast-v1-kernel-metadata.json"
OWNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), "yocybercode")
SLUG = "thui-animfast-b71-full25-r1"
OUT_NB = HERE / f"{SLUG}.ipynb"
OUT_META = HERE / "kernel-metadata.json"

GRAFTED_CELLS = [0, 1, 3, 5, 7, 9, 11, 15]
# The graft is not only cells: the anim SOURCE BUNDLE is a metadata attachment the upstream does not
# carry. Building the metadata from HIS file would inherit it silently, so it is built from KEITH's
# and this one line is added explicitly, asserted both before and after.
ANIM_BUNDLE = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"

OLD_H1 = "# thui-animfast-v1 (Thuitanium / Knowless Crew) —"
NEW_H1 = f"# {SLUG} (Thuitanium / Knowless Crew) —"

OLD_FOOT = """Build script: `thui-anim-fast/build_notebook.py` in our agent repo (diffs this notebook against the vendored
upstream copy and asserts exactly those cells changed). Ticket B71."""
NEW_FOOT = """Provenance of THIS version: the source of `sahasawatt/thui-animfast-v1` re-pushed unmodified under
`yocybercode/`, with only this header changed (its kernel name, and this paragraph). No solver, serving or
settings cell was touched. The build script that produced the upstream notebook is not in our agent repo —
searched for `animfast`, `anim-fast` and `anim_fast` across all 69 branch tips, 0 hits in paths and contents,
against a control that found `notes/wayfinder/MAP.md` on 69 of 69. Ticket B71 is likewise PROPOSED, not
minted: no `B71` row exists on any of those tips and the id ceiling is `B79`."""


def src(cell) -> str:
    return "".join(cell["source"])


def main() -> None:
    up = json.loads(SRC_UP.read_text())["cells"]
    gr = json.loads(SRC_GRAFT.read_text())

    # --- link 1: the vendored base is the notebook it claims to be -------------
    assert len(up) == 18, f"{SRC_UP.name}: expected 18 cells, found {len(up)}"
    assert src(up[0]).startswith("## About this fork"), "cell 0 is not Keith's fork note -- upstream changed"
    assert src(up[1]).startswith("# Tufa Labs ARC3 submission"), "cell 1 is not Tufa's header -- upstream changed"
    assert "bm.solver.max_runtime_s_per_game = 7920.0" in src(up[13]), "cell 13 budget line moved"
    # ...and it is the SAME base thui-fast vendors. A pruned neighbour only skips the check; two
    # copies of one frozen snapshot silently drifting apart is what it exists to catch.
    twin = HERE.parent / "thui-fast" / SRC_UP.name
    if twin.exists():
        assert twin.read_bytes() == SRC_UP.read_bytes(), (
            f"{SRC_UP.name} differs from thui-fast's copy of the same upstream -- one was re-vendored")

    # --- link 2: the graft touches exactly the cells it is documented to -------
    cells = gr["cells"]
    assert len(cells) == 18, f"{SRC_GRAFT.name}: expected 18 cells, found {len(cells)}"
    grafted = [i for i in range(18) if src(up[i]) != src(cells[i])]
    assert grafted == GRAFTED_CELLS, f"graft touches {grafted}, expected {GRAFTED_CELLS}"
    # the three things that MAKE it this arm rather than thui-fast
    assert "taaf-kaggle-source-anim-20260807-anim" in src(cells[7]), "cell 7 no longer names the anim bundle"
    assert "LOCAL_ANALYZER_SEED" in src(cells[9]) and "20260825" in src(cells[9]), "cell 9 lost the seed pin"
    assert "LOCAL_ANALYZER_YIELD_SECONDS" in src(cells[9]) and "180" in src(cells[9]), "cell 9 lost the yield pin"
    # ...and the serving stack is still Keith's MTP-3 profile, i.e. this is a SOLVER swap
    assert '"TAAF_VLLM_MTP_TOKENS": "3"' in src(cells[3]), "cell 3 is no longer the MTP-3 profile"
    assert "kv5-bf16-mtp3-c8-cg32" in src(cells[3]), "cell 3 lost the measured vLLM profile name"
    # ...at the full-25 settings, asserted rather than assumed
    assert "bm.solver.max_runtime_s_per_game = 7920.0" in src(cells[13]), "cell 13: not the full25 budget"
    assert "bm.solver.concurrency = 28" in src(cells[13]), "cell 13: not the full25 concurrency"
    assert "bm.solver.max_actions_per_game = None" in src(cells[13]), "cell 13: an action cap appeared"

    # --- link 3: our edit, and it is one cell ---------------------------------
    c0 = src(cells[0])
    assert c0.count(OLD_H1) == 1, "H1 anchor is not unique in cell 0"
    assert c0.count(OLD_FOOT) == 1, "footer anchor is not unique in cell 0"
    new_c0 = c0.replace(OLD_H1, NEW_H1).replace(OLD_FOOT, NEW_FOOT)
    nb = json.loads(SRC_GRAFT.read_text())
    nb["cells"][0]["source"] = new_c0.splitlines(keepends=True)
    moved = [i for i in range(18) if src(cells[i]) != src(nb["cells"][i])]
    assert moved == [0], f"expected only cell 0 to move, got {moved}"

    # --- G2: the submit gate's position lane ----------------------------------
    first_md = src(nb["cells"][0])
    assert first_md.splitlines()[0] == NEW_H1 + " our solver chassis on Keith Tyser's Flash-Next serving stack", first_md.splitlines()[0]
    assert "(Thuitanium / Knowless Crew)" in first_md.splitlines()[0], "G2: team name left the H1"
    assert first_md.index("Thuitanium") < first_md.index("Tufa Labs"), "G2: a brand precedes our identity"
    assert first_md.index("Thuitanium") < first_md.index("Keith Tyser"), "G2: a brand precedes our identity"

    # --- metadata: ours by id, his by everything that decides the run ---------
    meta = json.loads(SRC_META.read_text())
    meta.pop("id_no", None)
    meta["id"] = f"{OWNER}/{SLUG}"
    meta["title"] = SLUG
    meta["code_file"] = OUT_NB.name
    assert meta["enable_gpu"] is True and meta["enable_internet"] is False
    assert meta["machine_shape"] == "NvidiaRtxPro6000"
    assert meta["competition_sources"] == ["arc-prize-2026-arc-agi-3"]
    assert ANIM_BUNDLE not in meta["dataset_sources"], (
        "the vendored UPSTREAM metadata already attaches the anim bundle -- it should not, and if "
        "upstream now does, this graft step is no longer ours to add")
    assert len(meta["dataset_sources"]) == 2, meta["dataset_sources"]
    meta["dataset_sources"] = [*meta["dataset_sources"], ANIM_BUNDLE]
    assert len(meta["dataset_sources"]) == 3, meta["dataset_sources"]
    # CONTROL on the whole metadata graft: everything except the three fields that are ours by
    # definition must equal HIS metadata. Adding the bundle by hand and never checking it against the
    # file that actually ran is how a source list drifts without any assert noticing.
    his = json.loads(SRC_GRAFT_META.read_text())
    mine_cmp = {k: v for k, v in meta.items() if k not in ("id", "title", "code_file")}
    his_cmp = {k: v for k, v in his.items() if k not in ("id", "title", "code_file", "id_no")}
    assert mine_cmp == his_cmp, (
        "emitted metadata differs from sahasawatt/thui-animfast-v1's outside id/title/code_file: "
        f"{ {k: (his_cmp.get(k), mine_cmp.get(k)) for k in set(his_cmp) | set(mine_cmp) if his_cmp.get(k) != mine_cmp.get(k)} }")
    assert meta["model_sources"] == ["keithtyser/qwen3-8-flash-next-nvfp4/PyTorch/radixark-modelopt-fp4/1"], meta["model_sources"]
    # ⚠️ is_private comes down with the pulled metadata and is a PUBLISHING decision. It is asserted
    # here so a re-push cannot change it silently in either direction: the kernel that ran on
    # 2026-09-11 is public because this value was false, and only the web Share dialog can move it.
    assert meta["is_private"] is False, (
        "is_private changed: the kernel that ran was PUBLIC. Changing it here does nothing on Kaggle "
        "(push is the CLI's only write verb) -- use the Share dialog, and update this assert with it.")

    out = json.dumps(nb, indent=1) + "\n"
    # --- the emitted notebook must BE the one that ran ------------------------
    if OUT_NB.exists():
        assert OUT_NB.read_text() == out, (
            f"{OUT_NB.name} on disk is not what this script emits -- the vendored graft, the edits "
            f"above, or the pushed notebook have diverged. Do not push until they agree.")
    OUT_NB.write_text(out)
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n")
    print(f"{OUT_NB.name}: 18 cells, graft {GRAFTED_CELLS} from upstream, cell 0 ours")
    print(f"{OUT_META.name}: id {meta['id']}, is_private {meta['is_private']}, {meta['machine_shape']}")
    print(f"asserts: chain links, arm identity, full25 settings, G2 position, metadata graft "
          f"({len(meta['dataset_sources'])} dataset sources incl. the anim bundle, checked field by "
          f"field against his), and byte reproduction of the notebook that ran")


if __name__ == "__main__":
    main()
