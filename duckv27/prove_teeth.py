"""Teeth for duckv27's two edits, run against the REAL vendored source.

Edit 2 (the prompt) is tested behaviourally end to end, because it is the edit with a
silent failure mode: `tool_agent` imports the addendum BY VALUE, so the obvious patch --
rebinding `prompts.STRUCTURED_RUNTIME_STATE_ADDENDUM` -- changes nothing and says nothing.
Case 5 is that trap, asserted to still be a trap; without it cases 1-4 could all pass
against a patch that happens to work for the wrong reason.

Edit 1 (`animation_record` -> None) is asserted STRUCTURALLY, not behaviourally:
`inference.framework.solver` cannot be imported on this machine (it needs `arcengine`,
`taaf` and a plotting stack), and stubbing deep enough to instantiate a game session would
mean testing the stub. The patch body carries its own runtime asserts for the same two
facts, which fail loudly in the kernel where the real module is present.
"""
import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RIG = REPO / "localrig" / "ARC3-Inference"
SOLVER = RIG / "inference" / "framework" / "solver.py"
PATCH = REPO / "duckv27" / "retrieval_off_patch.py"
sys.path.insert(0, str(RIG))

ok = 0


def check(n, cond, msg):
    global ok
    if not cond:
        raise AssertionError(f"case {n} FAILED: {msg}")
    ok += 1
    print(f"  case {n} ok: {msg}")


# ---------------------------------------------------------------- edit 2, behavioural
import inference.agent.prompts as prompts          # noqa: E402
import inference.agent.tool_agent as ta            # noqa: E402

# ⚠️ Read the prefixes OUT OF THE PATCH, never restated here. A rig that keeps its own
# copy is a second implementation of the thing it tests: an earlier cut scored 13/13
# against a patch whose advertisement prefix had a typo, because only the rig's copy was
# correct. AST, so nothing in the patch is executed (it imports solver, which cannot load
# on this machine).
_ptree_early = ast.parse(PATCH.read_text(encoding="utf-8"))


def _const_tuple(name):
    for n in ast.walk(_ptree_early):
        if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == name for t in n.targets):
            return tuple(ast.literal_eval(n.value))
    raise AssertionError(f"{name} not found in the patch")


ADVERT = _const_tuple("_ADVERT")
AWARE = _const_tuple("_AWARE")

before = ta.STRUCTURED_RUNTIME_STATE_ADDENDUM
prompt_before = ta._build_system_prompt(tool_output_tokens=1024)

# CONTROL first: the thing being removed has to be there, or removing it proves nothing.
check(0, sum(1 for ln in before.split("\n") if ln.startswith(ADVERT)) == 3,
      "control: the stock addendum carries exactly 3 animation() advertisement lines")
check(1, all(p in prompt_before for p in AWARE) and "animation(" in prompt_before,
      "control: the stock BUILT prompt carries both halves")

# case 5 BEFORE we patch for real: the by-value trap is real.
saved_prompts = prompts.STRUCTURED_RUNTIME_STATE_ADDENDUM
prompts.STRUCTURED_RUNTIME_STATE_ADDENDUM = "REBOUND VIA THE WRONG MODULE"
check(5, ta._build_system_prompt(tool_output_tokens=1024) == prompt_before,
      "anti-tautology: rebinding prompts.X leaves the built prompt UNCHANGED "
      "(so a patch that targets `prompts` ships a run measuring nothing)")
prompts.STRUCTURED_RUNTIME_STATE_ADDENDUM = saved_prompts

# now apply the real patch's edit 2, exactly as the patch file spells it
lines = before.split("\n")
kept = [ln for ln in lines if not any(ln.startswith(p) for p in ADVERT)]
check(2, len(lines) - len(kept) == 3, "edit 2 removes exactly 3 lines")
after = "\n".join(kept)
ta.STRUCTURED_RUNTIME_STATE_ADDENDUM = after
prompt_after = ta._build_system_prompt(tool_output_tokens=1024)

check(3, "animation(" not in prompt_after,
      "the BUILT prompt no longer advertises animation()")
check(4, all(p in prompt_after for p in AWARE),
      "all 3 awareness lines survive -- the good half is not collateral")
check(6, len(prompt_before) - len(prompt_after) == len(before) - len(after) > 0,
      f"the prompt actually shrank, by {len(prompt_before) - len(prompt_after)} chars")

ta.STRUCTURED_RUNTIME_STATE_ADDENDUM = before   # leave the module as we found it

# ---------------------------------------------------------------- edit 1, structural
tree = ast.parse(SOLVER.read_text(encoding="utf-8"))
cls = next((n for n in ast.walk(tree)
            if isinstance(n, ast.ClassDef) and n.name == "_HarnessGameSession"), None)
check(7, cls is not None, "solver.py defines _HarnessGameSession")
meth = next((n for n in cls.body
             if isinstance(n, ast.FunctionDef) and n.name == "animation_record"), None)
check(8, meth is not None, "_HarnessGameSession defines animation_record")

# the seam claim: outside animation_record, animation_history is only APPENDED to, so
# gating the reader is equivalent to gating the writer.
src = SOLVER.read_text(encoding="utf-8").split("\n")
lo, hi = meth.lineno, meth.end_lineno
outside = [(i + 1, ln) for i, ln in enumerate(src)
           if "animation_history" in ln and not (lo <= i + 1 <= hi)]
reads = [(i, ln) for i, ln in outside if ".append(" not in ln and "deque[" not in ln
         and not ln.strip().startswith("animation_history:")]
check(9, not reads, f"animation_history is only written outside animation_record "
                    f"(outside refs: {[i for i, _ in outside]}, non-append: {reads})")

# and the patch file really performs both edits + targets the right module.
# ⚠️ Parsed, never grepped: a substring test passes on a COMMENTED-OUT assignment, which
# is how the first cut of this rig scored 13/13 against a patch with edit 1 disabled.
body = PATCH.read_text(encoding="utf-8")
ptree = ast.parse(body)
assigned = {(t.value.id, t.attr)
            for n in ast.walk(ptree) if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name)}
imported = {a.name for n in ast.walk(ptree) if isinstance(n, ast.Import) for a in n.names}
check(10, ("_sess", "animation_record") in assigned,
      "patch installs edit 1 as a real assignment (not a comment)")
check(11, ("_ta", "STRUCTURED_RUNTIME_STATE_ADDENDUM") in assigned,
      "patch rebinds the addendum on tool_agent as a real assignment")
check(12, not any(m.startswith("inference.agent.prompts") for m in imported),
      "patch never imports inference.agent.prompts -- the module that does nothing")

print(f"\nTEETH OK: {ok} cases")
