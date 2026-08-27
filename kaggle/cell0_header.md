# Thuitanium — ARC-AGI-3 (a fork of the Tufa Labs duck harness)

**This is a Knowless Crew / Thuitanium submission, and it is a fork.** The ARC-AGI-3 **solver is
Tufa Labs' work** — it is mounted as an attached dataset and executed unmodified. What is ours is
the harness configuration in this notebook: the environment flags, the clock, and the diagnostics.

## Credit

The solver was written by the Tufa Labs team; in alphabetical order: Harold Bessis, Jeroen Cottaar,
Isaiah Pressman, Andries Smit, Michal Tesnar, and Stefano Viel.

- The notebook this one descends from: https://www.kaggle.com/code/jeroencottaar/taaf-duck-harness-kaggle
- Their writeup, which explains what the solver actually does: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/717133
- Machine Learning Street Talk interview by Tim Scarfe about the duck harness: https://x.com/MLStreetTalk/status/2072326433922297975?s=20

⚠️ **The milestone-winning 1.21 described in the original notebook is Tufa Labs' result, not ours.**
No score on this page is theirs, and none of theirs is reported here.

## What we modified

**The solver is untouched.** Our changes are confined to the notebook's own configuration surface,
measured by diffing this fork against the upstream template rather than recalled:

- **cell 8** — the solver setup command: which model the run uses, and the environment flags that
  set its clock, its analyzer budget and its diagnostics.
- **cell 12** — the benchmark-customisation hook Tufa provides for exactly this purpose (*"make
  one-off changes to `bm`, `bm.games`, or `bm.solver` here before the run starts"*).
- **cells 2, 4, 6 and 14** — Tufa's own `__TAAF_*__` template placeholders filled in with this
  competition's wheelhouse path, working directory and dataset slugs. Every fork of the template
  does this; it is substitution, not modification.

Which lever a given build moves is stated in that build's own cell 8 / cell 12 comment and in the
`build_notebook.py` that produced it.

## What this notebook is

Infrastructure and diagnostics only — the solver code lives in the attached dataset. It installs the
ARC runtime from the competition wheelhouse, makes the bundled source snapshot importable, runs any
solver setup commands, loads the pickled benchmark, plays the competition games, and writes results
to `/kaggle/working`. Diagnostics are minimised during a real competition rerun
(`KAGGLE_IS_COMPETITION_RERUN`) and kept full otherwise.

**Note**: if you copy this notebook you must manually select the proper GPU (RTX Pro 6000).
