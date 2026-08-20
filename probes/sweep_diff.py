"""Compare two sweep logs per game. Parsing with python, not with the shell's
`diff` -- that is rewritten on this machine and its output is not the tool's own
format (~/.claude/RTK.md).

    ./.venv/Scripts/python.exe sweep_diff.py results/sweep-cover2.log results/sweep-swap.log
"""

import re
import sys

ROW = re.compile(r"^(\w+)\s+(\d+)/(\d+) levels\s+actions=(\[[^\]]*\])\s+score=([\d.]+)%")
MEAN = re.compile(r"^mean over (\d+) environments: ([\d.]+)%")


def read(path):
    games, mean = {}, None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = ROW.match(line.strip())
            if m:
                games[m.group(1)] = (int(m.group(2)), int(m.group(3)),
                                     m.group(4), float(m.group(5)))
            m = MEAN.match(line.strip())
            if m:
                mean = (int(m.group(1)), float(m.group(2)))
    return games, mean


a_path, b_path = sys.argv[1], sys.argv[2]
# The control names the game this comparison EXPECTS to differ. Hardcoding it works
# for exactly one comparison and then fires on the next: a control that cannot be
# pointed at the change under test is a tripwire, not a control.
expect = sys.argv[3] if len(sys.argv) > 3 else "sp80"
a, mean_a = read(a_path)
b, mean_b = read(b_path)
print(f"BEFORE {a_path}: {len(a)} games, mean {mean_a}")
print(f"AFTER  {b_path}: {len(b)} games, mean {mean_b}")

# positive control: the comparison must be able to SEE a difference. Prove it by
# asking it about a pair that is known to differ before trusting any 'identical'.
assert a.get(expect) != b.get(expect), f"control failed: {expect} did not differ"
print(f"control ok: {expect} differs, so the comparison is not blind\n")

same, changed, lost = [], [], []
for g in sorted(set(a) | set(b)):
    x, y = a.get(g), b.get(g)
    if x == y:
        same.append(g)
        continue
    changed.append((g, x, y))
    if x and y and y[0] < x[0]:
        lost.append(g)

print(f"identical to the digit: {len(same)}/{len(set(a) | set(b))}")
print("  " + " ".join(same))
print(f"\nchanged: {len(changed)}")
for g, x, y in changed:
    print(f"  {g}: {x}  ->  {y}")
print(f"\nGAMES THAT LOST A LEVEL: {lost if lost else 'NONE'}")
print("VERDICT:", "PASS -- no game loses a level" if not lost else "FAIL")
