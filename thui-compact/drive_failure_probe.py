#!/usr/bin/env python3
"""B67/B68 forced-failure probe — 0 GPU, 0 slot, no Kaggle, no network.

B67 closes on "a non-zero failure count, or when someone forces one deliberately".
169 fires across four banked runs produced zero, so the FAILURE print at
_compact_memento's except branch has never executed. This forces it.

B68's third question -- how much history follows a trip -- is asked of a quantity
the wrapper already computes one line above the discard and throws away.

Every printed number is checked against an independently computed ground truth in
the same run, so a pass means the instrument agrees with arithmetic, not that it ran.
"""
import ast, io, sys, types, contextlib, pathlib

BUILD = pathlib.Path(sys.argv[1])

# --- extract CELL12_SUFFIX without importing the builder (it has side effects) ---
src = BUILD.read_text()
tree = ast.parse(src)
# CELL12_SUFFIX is r'''...''' followed by a .replace() chain that injects build-time
# constants, so it is a Call, not a literal. Resolve the FULL (v1) variant -- that is the
# build that ran at width and produced the 169 fires this probe exists because of.
consts = {"FULL": True, "str": str}
for node in tree.body:
    if isinstance(node, ast.Assign) and node.lineno < 84:
        for tgt in node.targets:
            if isinstance(tgt, ast.Name):
                try:
                    consts[tgt.id] = eval(compile(ast.Expression(node.value), "<c>", "eval"), dict(consts))
                except Exception:
                    pass
cell = None
for node in tree.body:
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "CELL12_SUFFIX" for t in node.targets):
        cell = eval(compile(ast.Expression(node.value), "<cell>", "eval"), dict(consts))
assert cell, "CELL12_SUFFIX not found"
print("resolved build constants:",
      {k: consts.get(k) for k in ("FULL","COMPACT_K","WINDOW_TURNS","COMPACT_BLOCK_CHARS",
                                  "COMPACT_TURN_CHARS","MEMENTO_MAX_CHARS")})
print(f"extracted CELL12_SUFFIX: {len(cell)} chars")

# --- stub the harness package the cell imports and patches ---
# Exactly the five attributes the cell touches (enumerated from its own source), nothing more:
# a wider stub would let a missing dependency pass silently.
_ta = types.ModuleType("inference.agent.tool_agent")
class ToolAgent:
    _last_step_summary = {}
    def _persistent_history_messages(self, messages, *a, **k): return messages
    def analyze(self, *a, **k): return None
_ta.ToolAgent = ToolAgent
_ta._LOCAL_ANALYZER_ENABLE_THINKING = True      # the cell asserts this is True
_ta._PERSISTENT_HISTORY_ASSISTANT_TURNS = 30
def _norm(c):
    """Flatten the harness's content shape: str, or a list of {"type","text"} parts.
    The cell's own teeth 2 (line 380) rejects a stub that returns "" for the list form."""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "".join(p.get("text", "") for p in c if isinstance(p, dict))
    return ""
_ta._normalize_message_content = _norm
_ta._extract_reasoning_text = lambda m: ""
_pkg = types.ModuleType("inference"); _agent = types.ModuleType("inference.agent")
_agent.tool_agent = _ta; _pkg.agent = _agent
sys.modules.update({"inference": _pkg, "inference.agent": _agent,
                    "inference.agent.tool_agent": _ta})

ns = {"__name__": "compactcell"}
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    exec(compile(cell, "<CELL12_SUFFIX>", "exec"), ns)
print("cell executed; its own teeth printed:")
for line in buf.getvalue().splitlines():
    print("   ", line)

_compact_memento = ns["_compact_memento"]
STATS          = ns["_COMPACT_STATS"]
CAP            = ns["_COMPACT_BLOCK_CHARS"]
MAX_ERRORS     = ns["_MEMENTO_MAX_ERRORS"]
print(f"\n_COMPACT_BLOCK_CHARS={CAP}  _MEMENTO_MAX_ERRORS={MAX_ERRORS}")

class FakeAgent:
    """Minimal agent whose chat call always raises, as a stalled endpoint would."""
    _max_output_tokens = 1024
    def __init__(self, st): self.__dict__["_compact_state"] = st
    def _chat_completion(self, *a, **k):
        raise TimeoutError("probe: forced failure (no endpoint was contacted)")

def make_buffer(n_turns, chars_per_turn):
    """n_turns assistant lines; the label line is what _compact_game reads."""
    lines = ["[label] tr87"]
    for i in range(n_turns):
        body = f"t{i:03d}" + "x" * max(0, chars_per_turn - 4)
        lines.append("[assistant] " + body)
    return lines

fails = []
def check(name, got, want):
    ok = got == want
    fails.append(name) if not ok else None
    print(f"   {'ok  ' if ok else 'FAIL'} {name}: got {got!r} want {want!r}")

# ===================== B67 =====================
print("\n" + "=" * 72)
print("B67 -- force the exception branch; does the never-executed print tell the truth?")
print("=" * 72)

for n_turns, cpt in [(4, 500), (12, 1000)]:
    lines = make_buffer(n_turns, cpt)
    joined = "\n".join(lines)
    want_lost = max(0, len(joined) - CAP)
    want_chars = min(len(joined), CAP)
    st = {"buffer": list(lines), "memento": "prev memento", "pending_check": True,
          "game": "tr87", "errors": 0}
    before = dict(STATS)
    agent = FakeAgent(st)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        _compact_memento(agent, "k")
    printed = out.getvalue().strip()
    print(f"\n-- buffer {n_turns} turns x {cpt} chars, joined={len(joined)} chars (cap {CAP})")
    print(f"   PRINT: {printed[:190]}")
    if not printed:
        fails.append("B67 print emitted nothing"); print("   FAIL: the failure print emitted NOTHING")
        continue
    kv = dict(p.split("=", 1) for p in printed.split() if "=" in p and not p.startswith("("))
    check("block_chars == min(joined, cap)", int(kv["block_chars"]), want_chars)
    check("block_lost  == max(0, joined-cap)", int(kv["block_lost"]), want_lost)
    check("outcome", kv["outcome"], "exception")
    check("failed_block_chars == block_chars", int(kv["failed_block_chars"]), want_chars)
    check("buffer discarded by the failure policy", st["buffer"], [])
    check("memento preserved (last good)", st["memento"], "prev memento")
    check("STATS.failed_block_chars delta",
          STATS["failed_block_chars"] - before["failed_block_chars"], want_chars)
    check("STATS.block_lost_chars delta",
          STATS["block_lost_chars"] - before["block_lost_chars"], want_lost)

# ===================== B68 =====================
print("\n" + "=" * 72)
print("B68 -- trip the breaker, then measure what the disabled branch discards")
print("=" * 72)

lines = make_buffer(6, 800)
st = {"buffer": list(lines), "memento": "prev memento", "pending_check": True,
      "game": "tr87", "errors": 0}
agent = FakeAgent(st)
before_disabled = STATS["disabled_games"]
for fire in range(1, MAX_ERRORS + 1):
    st["buffer"] = list(lines)          # the game keeps producing history between fires
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        _compact_memento(agent, "k")
    kv = dict(p.split("=", 1) for p in out.getvalue().split() if "=" in p and not p.startswith("("))
    print(f"   fire {fire}: consecutive={kv.get('consecutive')} disabled={kv.get('disabled')}")
check("breaker tripped after MAX_ERRORS", st.get("disabled"), True)
check("disabled_games incremented once", STATS["disabled_games"] - before_disabled, 1)

print("\n-- ten post-trip discards through _compact_post_disable, the helper the")
print("   wrapper calls on the disabled branch (the real path, not a replay):")
TURNS_AFTER, CPT_AFTER, CALLS = 5, 900, 10
post_disable = ns.get("_compact_post_disable")
if post_disable is None:
    fails.append("no _compact_post_disable -- B68 counter not present in this build")
    print("   FAIL: this build has no _compact_post_disable; the discard is still uncounted")
else:
    before = dict(STATS)
    want_turns = want_chars = 0
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        for _ in range(CALLS):
            st["buffer"] = make_buffer(TURNS_AFTER, CPT_AFTER)
            want_turns += TURNS_AFTER
            want_chars += len("\n".join(st["buffer"]))
            post_disable(st)
    check("post_disable_turns delta",
          STATS["post_disable_turns"] - before["post_disable_turns"], want_turns)
    check("post_disable_chars delta",
          STATS["post_disable_chars"] - before["post_disable_chars"], want_chars)
    check("buffer cleared on the disabled path", st["buffer"], [])
    check("empty buffer counts nothing and prints nothing", post_disable({"buffer": []}), 0)
    lines = [l for l in out.getvalue().splitlines() if "post_disable_discard" in l]
    check("one readback line per non-empty discard", len(lines), CALLS)
    print(f"   LAST LINE: {lines[-1][:150]}" if lines else "   (no readback line)")
    print(f"   {want_turns} assistant turns / {want_chars} chars now counted AND printed;")
    print(f"   _COMPACT_STATS is never dumped, so the print is the readback route")

print("\n" + "=" * 72)
print("FAILURES:", fails if fails else "none")
print("=" * 72)
sys.exit(1 if fails else 0)
