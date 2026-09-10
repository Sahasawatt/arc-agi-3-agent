#!/usr/bin/env python3
"""Offline drive for B65's block-overflow counter -- runs the REAL cell-12 payload.

The payload text is lifted out of build_notebook.py and exec'd with the one foreign
import (inference.agent.tool_agent) stubbed, so every in-kernel assert runs here and
the fire path is driven end to end against a stub endpoint. Nothing is copied or
re-typed: grading a transcription would grade the transcription.

    python3 drive_block_counter.py            # drive
    python3 drive_block_counter.py --teeth    # + mutate the counter away, expect RED

Cases
  0  control      the in-kernel teeth executed at all (a payload that exec'd but skipped
                  its asserts would pass every case below)
  1  under cap    counters stay 0 and the block is unaltered
  2  over cap     block_truncated == 1 and block_lost_chars is EXACT
  3  log line     the fire prints block_lost= -- a stat that never reaches stdout cannot be
                  read back off a Kaggle log, which is how every other number here was got
  4  accumulates  a second over-cap fire adds, never overwrites
"""
from __future__ import annotations

import ast
import io
import contextlib
import re
import subprocess
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILDER = HERE / "build_notebook.py"
# Both shipped configurations. The smoke runs K=4, where K x TURN_CHARS (2400) is BELOW the
# 6000-char cap -- an earlier draft asserted reachability here and would have killed the smoke
# notebook at import. Driving both configs is what caught it; one config cannot.
CONFIGS = {
    "full ": {"@WINDOW@": "30", "@K@": "10", "@MAXTOK@": "600", "@TIMEOUT@": "90",
              "@TURNCHARS@": "600", "@BLOCKCHARS@": "6000", "@MEMCHARS@": "1600"},
    "smoke": {"@WINDOW@": "8", "@K@": "4", "@MAXTOK@": "600", "@TIMEOUT@": "90",
              "@TURNCHARS@": "600", "@BLOCKCHARS@": "6000", "@MEMCHARS@": "1600"},
}
SUBS = CONFIGS["full "]


def builder_constants(src: str) -> dict:
    """The builder's own module-level constants, read from its AST.

    CONFIGS above restates these by hand so the drive can compile the payload twice. That
    duplication is only safe if it is CHECKED: a bump to COMPACT_K or COMPACT_BLOCK_CHARS in
    build_notebook.py would otherwise leave every case here passing against numbers the shipped
    payload no longer uses. `X = a if FULL else b` is read as both of its branches.
    """
    out = {}
    for node in ast.parse(src).body:
        if not isinstance(node, ast.Assign) or not isinstance(node.targets[0], ast.Name):
            continue
        name, v = node.targets[0].id, node.value
        if isinstance(v, ast.Constant) and isinstance(v.value, int):
            out[name] = (v.value, v.value)
        elif (isinstance(v, ast.IfExp) and isinstance(v.body, ast.Constant)
              and isinstance(v.orelse, ast.Constant)):
            out[name] = (v.body.value, v.orelse.value)   # (FULL, smoke)
    return out


def assert_configs_match_builder(src: str) -> None:
    c = builder_constants(src)
    want = {
        "@WINDOW@": "WINDOW_TURNS", "@K@": "COMPACT_K", "@MAXTOK@": "COMPACT_MAX_TOKENS",
        "@TIMEOUT@": "COMPACT_TIMEOUT_S", "@TURNCHARS@": "COMPACT_TURN_CHARS",
        "@BLOCKCHARS@": "COMPACT_BLOCK_CHARS", "@MEMCHARS@": "MEMENTO_MAX_CHARS",
    }
    missing = [n for n in want.values() if n not in c]
    assert not missing, f"drive: builder no longer defines {missing} -- CONFIGS cannot be checked"
    bad = []
    for i, cfg in enumerate(("full ", "smoke")):
        for tok, name in want.items():
            got, exp = int(CONFIGS[cfg][tok]), c[name][i]
            if got != exp:
                bad.append(f"{cfg.strip()}/{tok}: drive says {got}, build_notebook.py says {exp}")
    assert not bad, "drive: CONFIGS is out of date with build_notebook.py --\n  " + "\n  ".join(bad)


def payload_text(src: str, subs=None) -> str:
    body = max((n.value for n in ast.walk(ast.parse(src))
                if isinstance(n, ast.Constant) and isinstance(n.value, str)), key=len)
    for k, v in (subs or SUBS).items():
        body = body.replace(k, v)
    return body


def stub_tool_agent():
    mod = types.ModuleType("inference.agent.tool_agent")

    class ToolAgent:
        def _persistent_history_messages(self, messages, *, tools=None):
            return list(messages)

        def analyze(self, *a, **k):
            return None

    mod.ToolAgent = ToolAgent
    # every _ta.<attr> the payload touches, enumerated from the payload itself
    mod._PERSISTENT_HISTORY_ASSISTANT_TURNS = 30
    mod._LOCAL_ANALYZER_ENABLE_THINKING = True
    def _norm(c):
        """Mirror the real one closely enough for the payload's OWN teeth to pass:
        a user message carries content as a list of {"type":"text","text":...} parts.
        A stub that returned "" for those made teeth 2 read 2 dropped lines, not 3."""
        if isinstance(c, str):
            return c
        if isinstance(c, list):
            return "\n".join(p.get("text", "") for p in c if isinstance(p, dict))
        return ""

    mod._normalize_message_content = _norm
    mod._extract_reasoning_text = lambda m: ""
    pkg = types.ModuleType("inference"); apkg = types.ModuleType("inference.agent")
    apkg.tool_agent = mod; pkg.agent = apkg
    sys.modules["inference"] = pkg
    sys.modules["inference.agent"] = apkg
    sys.modules["inference.agent.tool_agent"] = mod
    return mod


class StubResult:
    def __init__(self, text):
        self.usage = {"total_tokens": 120, "completion_tokens": 40}
        self.message = {"content": text}


class StubAgent:
    """Only what _compact_memento touches."""
    _max_output_tokens = 4096

    def __init__(self, game, buffer):
        self.__dict__["_compact_state"] = {
            "game": game, "buffer": list(buffer), "memento": "", "errors": 0}

    def _chat_completion(self, messages, tools=None, request_timeout_seconds=None):
        return StubResult("Rules: r (step 1)\nUnknown: u (step 2)\nNo-op/harmful: n (step 3)\n"
                          "Hypotheses: h (step 4)\nPlan: p (step 5)")

    def _accumulate_usage_tokens(self, usage):
        pass


def load(src_text, subs=None):
    stub_tool_agent()
    ns = {"__name__": "cell12"}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(payload_text(src_text, subs), "<cell12>", "exec"), ns)
    return ns, buf.getvalue()


def drive(src_text, subs=None):
    fails = []

    def check(name, ok, detail=""):
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}{('  -- ' + detail) if detail else ''}")
        if not ok:
            fails.append(name)

    ns, import_out = load(src_text, subs)
    cap = ns["_COMPACT_BLOCK_CHARS"]
    stats = ns["_COMPACT_STATS"]
    fire = ns["_compact_memento"]

    # 0 -- positive control. Without this, a payload whose asserts were stripped passes
    #      cases 1-4 by doing nothing, and the run reads green.
    check("0 control: in-kernel teeth ran", "block-cap teeth ok" in import_out,
          repr(import_out.strip()[-70:]))

    # 1 -- under the cap
    a = StubAgent("g1", ["[assistant] " + "x" * 50, "[assistant] " + "y" * 50])
    with contextlib.redirect_stdout(io.StringIO()):
        fire(a, "K")
    check("1 under cap: not counted",
          stats["block_truncated"] == 0 and stats["block_lost_chars"] == 0,
          f"truncated={stats['block_truncated']} lost={stats['block_lost_chars']}")

    # 2 -- over the cap, by a known amount. "\n".join adds 1 char between the two entries.
    over = 137
    lines = ["[assistant] " + "a" * (cap - 12), "[assistant] " + "b" * (over - 13)]
    expect = len("\n".join(lines)) - cap
    b = StubAgent("g2", lines)
    out2 = io.StringIO()
    with contextlib.redirect_stdout(out2):
        fire(b, "K")
    check("2 over cap: counted, exact",
          stats["block_truncated"] == 1 and stats["block_lost_chars"] == expect,
          f"truncated={stats['block_truncated']} lost={stats['block_lost_chars']} expect={expect}")

    # 3 -- and it is PRINTED. Parsed as an integer, not matched as a substring: "block_lost=137"
    #      is a prefix of "block_lost=1370", so an unanchored match passes on a value wrong by 10x.
    line = out2.getvalue()
    m = re.search(r"\bblock_lost=(\d+)\b", line)
    check("3 fire line carries block_lost=, parsed exact",
          bool(m) and int(m.group(1)) == expect,
          f"parsed={m.group(1) if m else None} expect={expect}")

    # 4 -- accumulates across fires
    c = StubAgent("g3", lines)
    with contextlib.redirect_stdout(io.StringIO()):
        fire(c, "level")
    check("4 accumulates over fires",
          stats["block_truncated"] == 2 and stats["block_lost_chars"] == expect * 2,
          f"truncated={stats['block_truncated']} lost={stats['block_lost_chars']}")

    # 5 -- a zero block_lost has two readings and the import note must send the reader to the
    #      OBSERVED maximum, not to a formula. The earlier draft printed a REACHABLE/UNREACHABLE
    #      verdict from K x TURN_CHARS; that ignores the user/tool lines sharing the buffer and
    #      could label an overflowing config impossible, so the note must not claim a verdict.
    note = next((l for l in import_out.splitlines() if "block cap" in l), "")
    lower = ns["_COMPACT_K"] * ns["_COMPACT_TURN_CHARS"]
    check("5 import note points at the observed max, claims no verdict",
          bool(note) and "LOWER bound" in note and f"= {lower} is a LOWER bound" in note
          and "largest block_chars=" in note
          and "REACHABLE" not in note and "UNREACHABLE" not in note,
          note.strip()[-100:] or "NO block-cap note printed")

    # 6 -- the failure path must print the block fields too: the counters are incremented before
    #      the call, and _COMPACT_STATS is never dumped, so a truncation on a failed fire would be
    #      counted into a total nothing can read back.
    class Boom(StubAgent):
        def _chat_completion(self, messages, tools=None, request_timeout_seconds=None):
            raise RuntimeError("endpoint down")

    d = Boom("g4", lines)
    out6 = io.StringIO()
    with contextlib.redirect_stdout(out6):
        fire(d, "K")
    fl = out6.getvalue()
    m6 = re.search(r"\bblock_lost=(\d+)\b", fl)
    check("6 failed fire still prints block_lost",
          "call FAILED" in fl and bool(m6) and int(m6.group(1)) == expect,
          fl.strip()[-110:])

    return fails


def main():
    src = BUILDER.read_text()
    assert_configs_match_builder(src)   # C: fail loudly rather than grade stale numbers
    fails = []
    for name, subs in CONFIGS.items():
        print(f"drive [{name}]: real payload from build_notebook.py  "
              f"(window={subs['@WINDOW@']} K={subs['@K@']})")
        fails += [f"[{name.strip()}] {f}" for f in drive(src, subs)]
        print()

    if "--teeth" in sys.argv:
        # Two mutations, because they are caught by different cases and a single one leaves
        # the control unproven. Each names the cases that MUST go red and the ones that must
        # NOT -- a mutation that reddens everything proves the payload broke, not the case.
        # One mutation per case. A case with no mutation naming it has never been shown able to
        # fail, and a control that cannot fail is a constant. Each names the cases that MUST go
        # red; extra reds are allowed (a mutation can legitimately trip more than its own case).
        muts = [
            ("counter increments disabled",
             ("    if _blk_lost:\n        _COMPACT_STATS[\"block_truncated\"]",
              "    if False:\n        _COMPACT_STATS[\"block_truncated\"]"),
             {"2 over cap: counted, exact", "4 accumulates over fires"}),
            # Mutating _compact_block itself trips the IN-KERNEL teeth at import, which case 0
            # catches -- correct, but it never reaches case 1. Mutate the FIRE-path guard instead
            # so the helper stays honest and only the "did it count when it should not" case moves.
            ("counter fires even under the cap",
             ("    if _blk_lost:\n        _COMPACT_STATS[\"block_truncated\"]",
              "    if True:\n        _COMPACT_STATS[\"block_truncated\"]"),
             {"1 under cap: not counted"}),
            ("block_lost dropped from the SUCCESS print",
             ('f"block_chars={len(block)} block_lost={_blk_lost} "\n          f"missing=',
              'f"missing='),
             {"3 fire line carries block_lost=, parsed exact"}),
            ("block_lost dropped from the FAILURE print",
             ('f"block_chars={len(block)} block_lost={_blk_lost} outcome=exception failed_block_chars={len(block)} "\n              f"consecutive=',
              'f"consecutive='),
             {"6 failed fire still prints block_lost"}),
            ("import note reverted to a verdict",
             ("is a LOWER bound on the buffer", "is REACHABLE against the buffer"),
             {"5 import note points at the observed max, claims no verdict"}),
            # Case 0 asserts the in-kernel teeth RAN. It can only see that because the banner now
            # prints _BLK_TEETH_PROBE, a value ONLY the teeth compute -- deleting the teeth block
            # makes the banner raise NameError at import. That is what this mutation exercises.
            ("in-kernel block-cap teeth deleted, banner kept",
             ("_BLK_TEETH_PROBE = _lo", "pass  # teeth deleted"),
             {"0 control: in-kernel teeth ran"}),
        ]
        rc = 0
        for name, (old_s, new_s), must_red in muts:
            print(f"\nteeth [full]: {name} -- expect RED on {sorted(must_red)}")
            mutated = src.replace(old_s, new_s)
            assert mutated != src, f"teeth: mutation {name!r} did not land -- the anchor moved"
            try:
                mfails = set(drive(mutated, CONFIGS["full "]))
            except Exception as exc:
                # Any import-time failure IS case 0 doing its job -- and it is not always an
                # AssertionError: deleting the teeth block makes the banner's _BLK_TEETH_PROBE
                # reference raise NameError, which is precisely the coupling that gives case 0
                # its teeth. Catching AssertionError alone let that mutation crash the run.
                mfails = {"0 control: in-kernel teeth ran"}
                print(f"  (import-time {type(exc).__name__}: {str(exc)[:70]})")
            missed = must_red - mfails
            if missed:
                print(f"  TEETH FAILED: {sorted(missed)} stayed green under this mutation")
                rc = 1
            else:
                print(f"  teeth ok -- caught by {sorted(mfails & must_red)}")
        if rc:
            return rc

    if fails:
        print(f"\nFAILED: {fails}")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
