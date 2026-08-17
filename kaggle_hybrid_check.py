"""Exec the built HYBRID Kaggle bundle and assert it is complete. (2026-08-17)

Adapted from the repo's own `kaggle_bundle_check.py` (which checks
`kaggle/my_agent.py`, the v9-lite bundle) for the HYBRID bundle built by
`kaggle/bundle_hybrid.py`. Same rule, same reason: exec the built bundle
before every push -- a bundle missing a module `compete` imports dies at
exec with an ImportError on Kaggle, not locally.

One structural difference from the v9-lite checker, load-bearing for where
this file lives: `bundle_hybrid.py`'s own docstring says its **output goes
to the STARTER KIT, not into this repo** -- the bundle embeds a third
party's MIT source (StochasticGoose, Tufa Labs) verbatim, and this repo is
MIT-0, so writing that payload into the repo would relicense someone else's
work. There is therefore no repo-side copy of the hybrid bundle to check by
default; this script's BUNDLE path points at the starter kit unless a path
is given on the command line (so the same file also serves step 4 of the
rebuild task: re-running it against the starter copy is re-running it
against the only copy).

What this asserts, in order of how loudly each would fail on Kaggle rather
than here:
  1. the file exec's at all, in a fresh namespace
  2. every module named in `bundle_hybrid.py`'s MODULES list (plus the
     extracted sample agent, `_goose`) is actually in `sys.modules`
     afterwards -- the ImportError-on-Kaggle case
  3. all fourteen whole-game DRIVERS are among them, by name
  4. the agent class (`MyAgent`, inheriting the sample's `GooseAgent`)
     exists in the bundle's namespace
  5. each driver still exposes the `signature()` predicate the play loop
     wires on, AND the embedded `mirror` module's own source -- decoded
     the same zlib+base64 way the bundle decodes it at exec time, not by
     grepping the compressed bytes -- contains `L4_LINE`. This is the
     regression this rebuild exists to fix: a stale hybrid build shipped
     without ar25's L3/L4 driver lines once already (README.md, 2026-08-16).

Needs the starter kit's vendored agents package on the path (arcengine is
already in this repo's venv; `agents.agent` is not):

    PYTHONPATH=<starter>/vendor/ARC-AGI-3-Agents ./.venv/Scripts/python.exe kaggle_hybrid_check.py [bundle_path]

Without it this fails at step 1 with `ModuleNotFoundError: No module named
'agents'` -- an environment fault, not a bundle fault (same caveat as
`kaggle_bundle_check.py`).
"""

import base64
import io
import re
import sys
import zlib

STARTER = r"C:\Users\Vampi\Desktop\ARC-AGI-3-Kaggle-Starter"
DEFAULT_BUNDLE = STARTER + r"\agent\my_agent_hybrid.py"
BUNDLE_HYBRID_PY = "kaggle/bundle_hybrid.py"
DRIVERS = ["cover", "swap", "haul", "maze", "dial", "skewer", "tape",
           "bridge", "sorter", "ferry", "claw", "mirror", "twin", "roller"]

BUNDLE = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BUNDLE

src = io.open(BUNDLE, encoding="utf-8").read()
print(f"bundle: {BUNDLE}  {len(src)} chars")

want = re.search(r"MODULES\s*=\s*\[(.*?)\]",
                 io.open(BUNDLE_HYBRID_PY, encoding="utf-8").read(), re.S)
declared = re.findall(r'"([a-z_]+)"', want.group(1)) if want else []
declared_plus_goose = declared + ["_goose"]
print(f"MODULES declared in bundle_hybrid.py: {len(declared)} -> {declared}  (+_goose)")

before = set(sys.modules)
ns = {"__name__": "__main__bundle__"}
try:
    exec(compile(src, BUNDLE, "exec"), ns)
except Exception as e:                                   # noqa: BLE001
    print(f"FAIL 1: bundle did not exec -- {type(e).__name__}: {e}")
    raise SystemExit(1)
print("PASS 1: bundle exec'd")

added = set(sys.modules) - before
missing = [m for m in declared_plus_goose if m not in sys.modules]
print(f"PASS 2: every declared module registered (incl. _goose)"
      if not missing else f"FAIL 2: missing from sys.modules -> {missing}")
if missing:
    raise SystemExit(1)

missing_drv = [d for d in DRIVERS if d not in sys.modules]
print(f"PASS 3: all {len(DRIVERS)} drivers present"
      if not missing_drv else f"FAIL 3: drivers missing -> {missing_drv}")
if missing_drv:
    raise SystemExit(1)

agent_cls = ns.get("MyAgent") or next(
    (v for k, v in ns.items() if k.endswith("Agent") and isinstance(v, type)), None)
print(f"PASS 4: agent class = {agent_cls.__name__}"
      if agent_cls else "FAIL 4: no agent class in the bundle's namespace")
if not agent_cls:
    raise SystemExit(1)
goose_cls = ns.get("GooseAgent")
is_hybrid = bool(goose_cls) and issubclass(agent_cls, goose_cls)
print(f"      -- inherits GooseAgent (sample base): {is_hybrid}")
if not is_hybrid:
    print("FAIL 4b: MyAgent does not inherit the sample GooseAgent -- not a hybrid bundle")
    raise SystemExit(1)

nosig = [d for d in DRIVERS if not hasattr(sys.modules[d], "signature")]
print(f"PASS 5a: every driver exposes signature()"
      if not nosig else f"FAIL 5a: no signature() on -> {nosig}")
if nosig:
    raise SystemExit(1)

# Decode the embedded "mirror" payload the same way `_load` does at exec
# time (zlib+base64), and grep the DECODED source -- not the compressed
# bytes, which never contain the literal string -- for L4_LINE. This is
# the exact regression the 2026-08-16 README entry describes: a stale
# hybrid build embedding an old mirror.py with no L3/L4 driver lines.
blob_m = re.search(r'mirror\s*=\s*_load\("mirror",\s*"([^"]+)"\)', src)
if not blob_m:
    print("FAIL 5b: could not find the embedded mirror payload in the bundle source")
    raise SystemExit(1)
mirror_src = zlib.decompress(base64.b64decode(blob_m.group(1))).decode("utf-8")
has_l3 = "L3_LINE" in mirror_src
has_l4 = "L4_LINE" in mirror_src
print(f"PASS 5b: embedded mirror.py decodes and contains L3_LINE and L4_LINE"
      if has_l3 and has_l4 else
      f"FAIL 5b: embedded mirror.py missing L3_LINE={not has_l3} L4_LINE={not has_l4}"
      " -- STALE BUILD (predates ar25 L3/L4)")
if not (has_l3 and has_l4):
    raise SystemExit(1)

print(f"\nmodules pulled in by the exec: {len(added)}")
print("ALL CHECKS PASSED -- the hybrid bundle is complete, loadable, and current.")
