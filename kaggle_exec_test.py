"""Exec the built Kaggle bundle and assert it is complete. (2026-08-16)

The repo's own rule: **exec the built bundle before every push** — a bundle built
without a module `compete` imports dies at exec with an ImportError, and a
forgotten `roller` in the v8 build was caught by exactly this and nothing else.

`kaggle/my_agent.py` is a build artifact: every module is embedded zlib+base64
and registered in `sys.modules` BEFORE being exec'd (dataclasses resolve their
module at class creation, so the order is load-bearing).

What this asserts, in order of how loudly each would fail on Kaggle rather than
here:
  1. the file exec's at all, in a fresh namespace
  2. every module named in `bundle.py`'s MODULES list is actually in
     `sys.modules` afterwards — the ImportError-on-Kaggle case
  3. all fourteen whole-game DRIVERS are among them, by name
  4. the agent class the starter kit splices in exists and is constructible-ish
  5. each driver still exposes the `signature` predicate the play loop wires on

    ./.venv/Scripts/python.exe kaggle_exec_test.py
"""

import io
import re
import sys

BUNDLE = "kaggle/my_agent.py"
DRIVERS = ["cover", "swap", "haul", "maze", "dial", "skewer", "tape",
           "bridge", "sorter", "ferry", "claw", "mirror", "twin", "roller"]

src = io.open(BUNDLE, encoding="utf-8").read()
print(f"bundle: {BUNDLE}  {len(src)} chars")

want = re.search(r"MODULES\s*=\s*\[(.*?)\]",
                 io.open("kaggle/bundle.py", encoding="utf-8").read(), re.S)
declared = re.findall(r'"([a-z_]+)"', want.group(1)) if want else []
print(f"MODULES declared in bundle.py: {len(declared)} -> {declared}")

before = set(sys.modules)
ns = {"__name__": "__main__bundle__"}
try:
    exec(compile(src, BUNDLE, "exec"), ns)
except Exception as e:                                   # noqa: BLE001
    print(f"FAIL 1: bundle did not exec -- {type(e).__name__}: {e}")
    raise SystemExit(1)
print("PASS 1: bundle exec'd")

added = set(sys.modules) - before
missing = [m for m in declared if m not in sys.modules]
print(f"PASS 2: every declared module registered"
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

nosig = [d for d in DRIVERS if not hasattr(sys.modules[d], "signature")]
print(f"PASS 5: every driver exposes signature()"
      if not nosig else f"FAIL 5: no signature() on -> {nosig}")
if nosig:
    raise SystemExit(1)

print(f"\nmodules pulled in by the exec: {len(added)}")
print("ALL CHECKS PASSED -- the bundle is complete and loadable.")
