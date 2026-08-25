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

THE SEED ARM  --  thui-v1-1  (MAP B37, notes/B37-v25-kernel-read-2026-08-25.md)

`--seed` adds ONE thing to cell 8: `LOCAL_ANALYZER_SEED` in the harness's setup_env dict.
Everything else is duckv10 exactly -- same anim bundle, same Qwen3.8-27B-FP8, output
UNCAPPED, upscale 4, no KV flag, v10's clock, temperature LEFT AT 0.6.

ATTRIBUTION.  The baseline for this build is `thui-v1-0`, not v10: the probe is already in
cell 12 and is measured inert -- 3.20 public, `rank_runs.py` p=0.3027 vs v10cal and p=0.7579
vs v19, both NOT-DISTINGUISHABLE.  So thui-v1-1 vs thui-v1-0 is exactly one changed variable,
and the probe carries forward as the instrument that makes the run readable.

WHY IT IS WORTH A SLOT.  Every run of this campaign sampled at temperature 0.6 with NO seed
(`tool_agent.py` defaults seed=-1, and `openai_compat.build_chat_payload` only sends the key
when `seed >= 0`).  The same-build public band `[2.82, 4.71]` is what makes every candidate
NOT-DISTINGUISHABLE and what B30 uses to forbid spending a hidden draw.  This is a META-lever:
a null result on score is still a win if the SPREAD shrinks, because a narrower band is what
makes every other candidate measurable.

WHY SEED ONLY.  Temperature 0 is a DIFFERENT agent, not a quieter one -- v21/B31 halved levels
28 -> 12 at p=0.0052 WORSE by changing how the model deliberates.  Pinning the seed changes no
reasoning behaviour: the same distribution, from a fixed starting point.

WHY NOT duckv25.  That kernel was built from duckmod and shipped duckmod's 14,355-char cell 12,
so it ran as `duckmod + seed` -- adoption 8 executed `hud_mask(history)` calls in 4 of 25 games.
B37 is UNTESTED.  This build sources duckv10 and asserts the block is absent.

PREDICTIONS, written before the run

  P1  VALIDITY, read before any score.  The kernel log must echo
      `'LOCAL_ANALYZER_SEED': '<seed>'` in the setup command.  Absent -> the injection missed,
      the run is plain thui-v1-0 and MEASURES NOTHING whatever it scores.
  P2  public lands inside [2.82, 4.71].  That is the EXPECTED outcome, not a failure: pinning
      a seed has no reason to move the mean.  `rank_runs.py` vs v10cal should read
      NOT-DISTINGUISHABLE.
  P3  the actual hypothesis, and ONE RUN CANNOT TEST IT: a second run of this build lands
      within a narrower gap of the first than the 1.89 the unpinned build spans.  Treat run 1
      as banking a sample.
  P4  25 `*_usage.jsonl` files land again (the probe), so the seed arm is readable per request.
  P5  free rider (peer session, v25): `ft09` and `bp35` emitted 0 and 1 actions under duckmod's
      cell 12 against a minimum of 9 anywhere in 125 game-runs.  If both are normal here, the
      stall belongs to that prompt -- a MAP line for zero extra cost.

WHAT THIS CANNOT DO, stated before the run

  (a) It cannot show DETERMINISM.  Batched vLLM is not bit-reproducible across differing batch
      compositions and 25 games share one server.  The seed is proven SENT, never more.
  (b) The 7,920s wall cuts each game at a different point regardless of sampling, so some
      run-to-run variance survives any sampler setting.
  (c) `rank_runs.py` ranks a PAIR; it does not measure a band.

USAGE

    python3 build_notebook.py                       # duckv10 -> thuiv1, sibling probe
    python3 build_notebook.py --seed 20260825 --slug thui-v1-1 --out v1-1/taaf-thui-v1-1.ipynb
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

# --- the seed arm (thui-v1-1 / MAP B37) -------------------------------------------
# `LOCAL_ANALYZER_SEED` exists ONLY in inference/agent/tool_agent.py (`_get_env_int(...,-1)`
# at :159, handed to build_chat_payload at :1536, sent at openai_compat.py:65-70 inside the
# `vllm` branch).  It is absent from framework/kaggle.py, so nothing adds it on its own --
# the builder has to write it into the harness's setup_env dict, which is what these two
# splices do.  Anchored on the TEMPERATURE line the bundle always renders right after where
# the seed belongs; verified against the real echoed command of two runs on disk (clock2x
# has no SEED key and one TEMPERATURE line, v25seed has both).

CELL8_SWAP_ANCHOR = """            "SERVED_MODEL_NAME = 'vrfai/Qwen3.8-27B-FP8'",
        )
    )
"""

CELL8_SEED_REPLACE = """            "SERVED_MODEL_NAME = 'vrfai/Qwen3.8-27B-FP8'",
        )
        .replace(
            "    'LOCAL_ANALYZER_TEMPERATURE':",
            "    'LOCAL_ANALYZER_SEED': '__SEED__',\\n    'LOCAL_ANALYZER_TEMPERATURE':",
        )
    )
"""

CELL8_ASSERT_ANCHOR = (
    '    assert "\'LOCAL_ANALYZER_MAX_OUTPUT\': \'0\'" in command,'
    ' "duckv10: output must stay UNCAPPED"\n'
)

CELL8_TEETH = '''    # thui-v1-1 TEETH, in-kernel, before the benchmark starts. The seed IS this
    # build: if the anchor moved in a newer bundle the replace is a silent no-op and the
    # run would score normally while measuring nothing.
    assert "'LOCAL_ANALYZER_SEED': '__SEED__'" in command, (
        "thui-v1-1 TEETH FAIL: seed injection missed -- the setup_env anchor "
        "\\"    'LOCAL_ANALYZER_TEMPERATURE':\\" is not in this bundle's setup command"
    )
    assert command.count("'LOCAL_ANALYZER_SEED'") == 1, (
        "thui-v1-1 TEETH FAIL: seed key injected more than once"
    )
    assert "'LOCAL_ANALYZER_TEMPERATURE': '0.6'" in command, (
        "thui-v1-1 TEETH FAIL: temperature is not 0.6 -- this arm must not touch it"
    )
    assert "'MULTIMODAL_UPSCALE': '4'" in command, (
        "thui-v1-1 TEETH FAIL: upscale must stay 4 (v10 exact, B23 measured in-noise)"
    )
    print("thui-v1-1: sampler pinned, seed=__SEED__, temperature untouched", flush=True)
'''


def seed_cell8(existing: str, seed: str) -> str:
    """Add LOCAL_ANALYZER_SEED to the setup_env dict, and the teeth that guard it."""
    assert existing.count(CELL8_SWAP_ANCHOR) == 1, "cell 8: model-swap block not found (one copy)"
    assert existing.count(CELL8_ASSERT_ANCHOR) == 1, "cell 8: UNCAPPED assert not found (one copy)"
    assert "LOCAL_ANALYZER_SEED" not in existing, "cell 8 already injects a seed"
    out = existing.replace(CELL8_SWAP_ANCHOR, CELL8_SEED_REPLACE.replace("__SEED__", seed))
    out = out.replace(
        CELL8_ASSERT_ANCHOR, CELL8_ASSERT_ANCHOR + CELL8_TEETH.replace("__SEED__", seed)
    )
    assert "__SEED__" not in out, "seed placeholder left unrendered"
    return out


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
    slug: str | None = None,
) -> dict:
    meta = json.loads(src_meta.read_text(encoding="utf-8"))
    if owner is None:
        owner = str(meta["id"]).split("/", 1)[0]
        # `--out`/`--slug` name OUR build; the source metadata names whoever owns the SOURCE
        # kernel. Inheriting it silently is how a push lands on a colleague's account.
        print(
            f"  note: --owner not given, inherited '{owner}' from {src_meta.name}",
            file=sys.stderr,
        )
    # The kernel slug is the Kaggle identity and it is NOT the file stem: thui-v1-0 shipped
    # as `yocybercode/thui-v1-0` from `taaf-thui-v1.ipynb`. Hyphen, never a dot.
    stem = out_nb.stem if slug is None else slug
    assert "." not in stem, f"kernel slug must not contain a dot: {stem}"
    meta["id"] = f"{owner}/{stem}"
    meta["title"] = stem if title is None else title
    meta["code_file"] = out_nb.name
    return meta


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", default=str(HERE.parent / "duckv10" / "taaf-duck-v10.ipynb"))
    ap.add_argument("--out", default=str(HERE / "taaf-thui-v1.ipynb"))
    ap.add_argument("--probe", default=str(HERE / "request_usage_probe.py"))
    ap.add_argument("--owner", help="Kaggle account for the kernel id. REQUIRED with --slug.")
    ap.add_argument("--title")
    ap.add_argument("--slug", help="Kaggle kernel slug (defaults to the notebook stem)")
    ap.add_argument(
        "--seed",
        help="pin LOCAL_ANALYZER_SEED in cell 8 (MAP B37). Omit for the inert v1.0 instrument.",
    )
    args = ap.parse_args(argv)

    assert not (args.slug and not args.owner), (
        "--slug names a new kernel: pass --owner too, or the id inherits the SOURCE kernel's "
        "account and the push lands on someone else's profile"
    )
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

    # The seed arm is the ONE behavioural change; without --seed this stays the inert
    # instrument whose diff against its source is cell 12 alone.
    expected_diff = [12]
    if args.seed:
        new8 = seed_cell8(before[8], args.seed)
        compile(new8, "<cell8>", "exec")
        cells[8]["source"] = new8
        expected_diff = [8, 12]

    out_nb.parent.mkdir(parents=True, exist_ok=True)
    out_nb.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"wrote {out_nb} ({out_nb.stat().st_size} bytes) — cell 12 mode: {mode}")

    src_meta = src_nb.parent / "kernel-metadata.json"
    if src_meta.is_file():
        meta = build_metadata(
            src_meta, out_nb, owner=args.owner, title=args.title, slug=args.slug
        )
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
    assert diff == expected_diff, f"unexpected diff cells: {diff} (want {expected_diff})"
    assert PROBE_MARK in out_cells[12], "probe header missing from the written cell"
    assert "install(tool_agent)" in out_cells[12], "install() call missing"
    compile(out_cells[12], "<cell12>", "exec")
    if mode == "REPLACE":
        assert PLACEHOLDER_MARK not in out_cells[12], "placeholder survived a REPLACE"
    else:
        assert out_cells[12].startswith(src_cells[12].rstrip("\n")), "APPEND clobbered the patch"
    # Cell 12 must be THIS build's probe and nothing inherited. duckv25 shipped duckmod's
    # 14,355-char patch block into a run advertised as "v10 + seed" and its own assertion
    # passed by construction; adoption came back 8, so that run answered another question.
    assert "duckmod: inject HUD auto-flag" not in out_cells[12], (
        "duckmod's patch block is in cell 12 -- this build is duckmod-based, not v10-based"
    )
    assert len(out_cells[12]) < 20000, f"cell 12 is {len(out_cells[12])} chars"

    if args.seed:
        o8 = out_cells[8]
        assert f"'LOCAL_ANALYZER_SEED': '{args.seed}'" in o8, "seed literal missing from cell 8"
        assert "TEETH FAIL" in o8, "in-kernel teeth missing from cell 8"
        # The levers that already cost a slot, both poles. v9 = 0.22 capped; v18/v23 upscale
        # measured in-noise; v21/B31 halved levels by touching how the model deliberates.
        assert "'LOCAL_ANALYZER_MAX_OUTPUT': '0'" in o8, "output must stay UNCAPPED (v9 = 0.22)"
        assert "'LOCAL_ANALYZER_MAX_OUTPUT': '768'" not in o8, "the v9 cap is back"
        assert "'MULTIMODAL_UPSCALE': '4'" in o8, "upscale must stay 4"
        assert "'MULTIMODAL_UPSCALE': '8'" not in o8, "the v18 upscale change is back"
        # Strip the one legitimate literal (the teeth ASSERT that it is 0.6), then any
        # surviving "TEMPERATURE': '<n>" is a rewrite that SETS it -- which is B31, not B37.
        assert "LOCAL_ANALYZER_TEMPERATURE': '0" not in o8.replace("'0.6'", ""), (
            "this arm asserts temperature, it must never SET it (B31)"
        )
        assert "max_runtime_s_per_game" not in o8, "the clock is v10's; B34 closed that axis"
        print(f"seed arm OK: LOCAL_ANALYZER_SEED={args.seed}, temperature untouched")

    if src_meta.is_file():
        src_m = json.loads(src_meta.read_text(encoding="utf-8"))
        out_m = json.loads((out_nb.parent / "kernel-metadata.json").read_text(encoding="utf-8"))
        for key in ("dataset_sources", "competition_sources", "docker_image", "machine_shape"):
            assert src_m.get(key) == out_m.get(key), (
                f"kernel-metadata {key} changed — an instrument must not change the build"
            )
        assert out_m["id"] != src_m["id"], "kernel id must be new or the push overwrites the source"
    print(f"self-check OK: diff == {expected_diff}, mode {mode}, build inputs unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
