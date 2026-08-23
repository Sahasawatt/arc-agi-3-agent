# === duckv22: swap PYTHON_ADDENDUM for the rank-21 team's version ===
#
# PROVENANCE (notes/R26-reasoning-effort.md, notes/R27-git-sweep.md): team "Ya Xu",
# leaderboard rank 21 at hidden 2.37 (us: 212 at 1.70), published bundle
# arc3-qwen38-colab-v29. Against the same June-era base their whole diff is six
# files; v21 measured their reasoning_effort flag alone as WORSE (p=0.0052), which
# leaves their PROMPT work as the last unmeasured piece. This cell ports their
# PYTHON_ADDENDUM verbatim — extracted from their prompts.py by AST, not retyped.
#
# Their two genuinely new bullets:
#   1. keep a tried-checklist in `Recent findings:` — "before you declare a
#      'completely different approach', read that checklist"
#   2. never transcribe ASCII rows in your own REASONING — write code for diffs
#      instead ("burns real wall-clock time on long boards")
# The rest of their addendum rewords ours; the swap ships their whole unit so the
# run measures THEIR design, not my paraphrase of it.
#
# tool_agent.py imports PYTHON_ADDENDUM by name (`from inference.agent.prompts
# import (...)`), so both bindings are patched — same two-place pattern v21 used.

THEIR_PYTHON_ADDENDUM = '\n\nPython tool guidance:\n- Use `current_frame.segmentation` as your primary view of the board -- objects, colors, containment, adjacency, and cross-frame object hashes.\n- Use `current_frame.ascii` only to read a small, specific region of the board when `segmentation` is not enough; never use it to scan or summarize the whole board.\n- Every `python` tool call starts fresh. Re-import modules or re-define any custom utility logic you need.\n- The only importable standard-library modules are: bisect, collections, copy, fractions, functools, heapq, itertools, json, math, operator, random, re, statistics, string.\n- The only tool is `python`; call it with one ephemeral `code` string.\n- Always inspect `current_frame`, `history`, and `valid_actions` from Python instead of reasoning from the raw board by eye.\n- Maintain a compact working world model: what entities or regions exist, what actions seem to do, what the goal likely is, what remains uncertain, and what plan best fits the evidence so far.\n- IMPORTANT: Especially when the game is about making an agent navigate to a target, it is usually safer to write an explicit search algorithm such as BFS. More generally, when the objective is understood but the best action order is unclear, pathfinding, flood fill, BFS, DFS, beam search, shortest-path search, limited action-sequence search, or custom heuristics are all valid.\n- Keep an explicit record of what you have already tried on the CURRENT level. In your `Recent findings:` block, maintain a compact checklist of each distinct action/object you tested and its observed effect (e.g. "clicked gray square #3 -> no change", "RIGHT twice from start -> player moved to col 28"). Before you declare a \'completely different approach\', read that checklist: if you cannot point to a specific untested hypothesis or action, you are about to repeat past work. Listing what you tried in `Recent findings:` is cheap and prevents redundant probing.\n- Never print or echo full board frames; return only compact derived summaries (object lists, diffs, coordinates, counts, or tiny local crops) and keep tool-output context minimal and decision-oriented -- it\'s fine to write a lot of python code, just make the output short and interpretable.\n- The same rule applies to your own reasoning text: do NOT transcribe raw ASCII rows or compare region boundaries character-by-character in your thinking. If you catch yourself listing more than a few ASCII rows or manually diffing rows in your reasoning, stop and write Python code to compute that diff or summary instead (e.g. compare `previous_frame` to `current_frame` via code, or print only the changed cells). Manual row-by-row transcription in your own reasoning is exactly as wasteful and error-prone as printing it, and it burns real wall-clock time on long boards.\n- A strong default loop is: summarize the board, infer the desired environment change, write a small scorer or search over candidate sequences, execute the best probe or plan with `action(...)`, then inspect again. Optimize for the shortest reliable sequence; if confidence is low, program a discriminating probe and revise the world model from the result. Once the important state variables and action effects are sufficiently understood, stop probing and search in the inferred state space.\n- For object tracking, match objects by color, overlap, bounding box proximity, area change, and edge contact rather than by exact coordinates alone.\n- For frame diffs, summarize changed cells, color transitions, appearing/disappearing components, movement candidates, and small local row slices around the changed region.\n- After every action, verify whether gameplay objects changed or whether only a timer, progress bar, or remaining-step bar moved. Do not treat HUD-only changes as evidence that the move worked.\n- Call `action(...)` inside Python rather than returning action text in the chat.\n- `action(...)` accepts an ordered list of one or more actions; batch a reliable sequence in one call, or call it multiple times in one snippet (including inside loops) -- each call refreshes the preloaded variables before execution continues.\n- If an action result reports `game_over`, `run_complete`, `level_completed`, or `done`, stop the current snippet immediately and re-ground on the next turn. The stop applies only to the current tool call; if you are called again, the level has likely been auto-reset, so probe the new state with a fresh `action(...)` call. Refusing to call `action(...)` for more than one consecutive turn is itself a failure mode.\n'

OUR_MARKER = "Use `print(...)` for compact summaries"   # unique to the OLD addendum

from inference.agent import prompts as _prompts  # noqa: E402
from inference.agent import tool_agent as _tool_agent  # noqa: E402

_STOCK = _prompts.PYTHON_ADDENDUM
_prompts.PYTHON_ADDENDUM = THEIR_PYTHON_ADDENDUM
_tool_agent.PYTHON_ADDENDUM = THEIR_PYTHON_ADDENDUM

# --- teeth, in-kernel, before any game starts (R8: a silent no-op reads as
# --- "the idea does not help") ---
assert "already tried" in THEIR_PYTHON_ADDENDUM and "The same rule applies" in THEIR_PYTHON_ADDENDUM
assert "already tried" not in _STOCK, (
    "duckv22: TEETH FAIL - the stock addendum already carries the bullet; this run would measure nothing"
)
_sys_prompt = _tool_agent._build_system_prompt(tool_output_tokens=1024)
assert "already tried" in _sys_prompt, (
    "duckv22: TEETH FAIL - the built system prompt does not contain the ported bullet"
)
assert OUR_MARKER not in _sys_prompt, (
    "duckv22: TEETH FAIL - the old addendum still reaches the system prompt"
)
print(f"duckv22: PYTHON_ADDENDUM swapped ({len(_STOCK)} -> {len(THEIR_PYTHON_ADDENDUM)} chars); "
      f"both bindings patched; teeth OK")
