# B98 stage 0 + stage 1 artifacts (0 GPU, 2026-09-24, sahasawat session)

Sent at Watchara's request (relay 01M399W3514E14HBD8T7F461HH, "send the stage-0 extractor, the judge outputs, and
the checker + SPEC.md"). Run on B99's public run `kout-yo-thui-b99-rungpin-full25-r1`, against the B98 bar as it
stood BEFORE the 2026-09-24 revision (the revised bar measures availability on unseen transitions, not accuracy).
Registered rules and results, written before each output existed: `LEDGER.md` sections "Stage 0 for D" and
"Stage 1 for D" (paths there say `b99next/` and `b98-stage1/`; here they are `stage0/` and `stage1/`).

## Results in one line each
- Stage 0 PASS: 8,146 mechanical candidate sentences; 96 sampled + 3 negative controls; 2 sonnet judges per item;
  agreement on "checkable" 93/98; 33 sentences checkable by both, in 21/25 games (bar: 12); all 3 negative
  controls rejected by both judges. `stage0_agg.py` reproduces this verdict on this branch.
- Stage 1 FAIL on both registered conditions. The wall is COMPILE: 5 of the 33 sentences both judges called
  checkable compile faithfully to the DSL from text alone. The rest are ungrounded without the board (for example a
  rotation stated as a translation, or "the clicked tiles" compiled as every blue cell).

## Files
| file | what it is |
|---|---|
| `stage0/stage0_extract.py` | mechanical extractor: transcripts + events of a run -> candidate sentences + seeded sample batches |
| `stage0/stage0_batch{0..3}.json` | the exact 99 items the judges saw (96 sampled + 3 negative controls) |
| `stage0/stage0_judge.json` | raw judge outputs (workflow wf_600bee69-8ea, sonnet) |
| `stage0/stage0_agg.py` | the registered aggregation: `python stage0_agg.py stage0_judge.json` |
| `stage1/SPEC.md` | checker spec: DSL, transition definition, verdict rules |
| `stage1/checker.py` | checker, stdlib only; written by codex to SPEC.md, patch reviewed and applied by hand |
| `stage1/test_checker.py` | `python test_checker.py` from `stage1/` -> ALL OK, including mutants (re-run on this branch) |
| `stage1/stage1_compile_input.json` | the 33 sentences both judges called checkable (compiler input) |
| `stage1/compiled_raw.json`, `stage1/hyp_compiled.json` | one sonnet compile pass: raw output, and the hypotheses that compiled |
| `stage1/stage1_verdicts.json` | checker verdicts per hypothesis and its negated twin |

## Rerunning
- `stage0_extract.py <run-dir>`: pass an ABSOLUTE path to the kernel output directory (a relative one resolves
  against `notes/b98-stage01/`). It rewrites `stage0_batch*.json` (seeded sample) and writes
  `stage0_candidates.json` (1.5 MB), which is left out here.
- `checker.py <hypotheses.json> <run-dir>/artifacts` reads `<game>_p0_events.jsonl` per SPEC.md.
- Not included: the judge and compile prompts (they lived in workflow scripts in this session), and any kernel output.
