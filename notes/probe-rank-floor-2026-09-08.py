"""One invocation: pinned instrument controls, then planted decision surface."""
import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
subprocess.run([sys.executable, str(root / 'rank_runs.py'), '--selftest'], check=True)
spec = importlib.util.spec_from_file_location('rank', root / 'rank_runs.py')
rank = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rank)
base = rank.load(str(root / 'fixtures/v10cal.json'))
results = [rank.compare(base, base)]
for count, delta in [(25, .01), (5, 100), (5, .01), (6, .01), (6, 100)]:
    arm = copy.deepcopy(base)
    arm['label'] = f'planted-{count}-games-plus-{delta}'
    for key in sorted(arm['games'])[:count]:
        arm['games'][key]['score'] += delta
    results.append(rank.compare(base, arm))
# Same sign pattern, different magnitudes: distinguishes mean test from sign-only test.
for scale in [1, 100]:
    arm = copy.deepcopy(base)
    arm['label'] = f'mixed-sign-one-negative-magnitude-{scale}'
    for i, key in enumerate(sorted(arm['games'])):
        arm['games'][key]['score'] += 1 if i < 24 else -scale
    results.append(rank.compare(base, arm))
assert results[0]['p_score'] == 1 and results[0]['verdict'] == 'NOT-DISTINGUISHABLE'
assert results[1]['verdict'] == 'BETTER'
assert results[2]['verdict'] == 'NOT-DISTINGUISHABLE'
print(json.dumps(results, indent=2))
