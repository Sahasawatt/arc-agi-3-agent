# HUD semantics

`hud_semantics.py` classifies confident edge bars and counters from frame history.
It reports timers, progress indicators, action-cost counters, and reset-correlated budgets.
The module is pure Python standard library and accepts ordinary grids or multi-plane frames.
Later, the harness will inject `render_hint()` beside the duckv5 digest in each observation.
The model will receive the hint directly and will not need to call a tool.
Open risk: heuristic false positives remain possible when the PLAY AREA itself has monotone regions.
Confidence gating and frame-variation checks reduce, but do not eliminate, that risk.
