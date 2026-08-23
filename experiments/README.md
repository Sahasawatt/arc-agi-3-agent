# experiments/

Dated search chains. Write-once: each one records how a particular level fell (or did not), and
none of them is imported by `compete.py`, by a driver, or by the Kaggle bundle. They are kept as
evidence, not as library code — a result here is cited by a driver's comment, and that citation is
the reason the file still exists.

Nothing in this directory is on `MODULES` in `kaggle/bundle.py`, so moving it here changed no
submission artifact.

## Running one

Each script's own directory goes on `sys.path` automatically, so a chain only needs the *one* other
directory its siblings live in. No chain needs both.

| chain | needs | run from repo root |
|---|---|---|
| `sp80_s11` `sp80_s12` `sp80_s13` | `swap` at the repo root | `PYTHONPATH=. python experiments/sp80_s13.py` |
| `wa30_b2_l3chain` | `haul` at the repo root | `PYTHONPATH=. python experiments/wa30_b2_l3chain.py` |
| `dc22_c4_hidden` `dc22_c5_soundchain` | `probes/dc22_c2_l2chain`, `probes/dc22_c3_verify` | `PYTHONPATH=probes python experiments/dc22_c5_soundchain.py` |
| `re86_b2_l6chain` | `probes/re86_b1_bfs` | `PYTHONPATH=probes python experiments/re86_b2_l6chain.py` |

On Windows the venv python is `./.venv/Scripts/python.exe` and the chains want `PYTHONUTF8=1`; see
`notes/next-session-prompt.md` for the resume invocations with their budget flags.

⚠️ **Three of these could not be run by a bare `python <file>.py` before the move either.** The
`dc22_*` and `re86_*` chains have always imported from `probes/`, and `dc22_c5_soundchain` imported
one sibling from the root and another from `probes/`, so no single working directory resolved it.
What changed here is that the invocation is now uniform and written down, not that it got harder.

Each chain resumes from its own atomic checkpoint. Do not pass `--fresh` unless you mean to discard
one.
