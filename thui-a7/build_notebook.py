"""Reproduce the banked B76 full-25 notebook without executing it.

Follows thui-fast/build_notebook.py: pin source, assert changed cell indices,
parse code and preserve upstream attribution. The recovered notebook's header
still says smoke; preserve that historical defect for byte-exact reproduction.
Cell 1 changes source representation only (list to string), not its text.
"""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / 'thui-fast/taaf-thui-fast-v0.ipynb'
OUT_NB = HERE / 'thui-a7-full25-r1.ipynb'


def build(source=SRC_NB):
    spec = json.loads((HERE / 'banked-cell-edits.json').read_text())
    raw = Path(source).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == spec['source_sha256'], 'source drift'
    nb = json.loads(raw)
    assert len(nb['cells']) == 18
    before = json.loads(raw)['cells']
    for index, cell in spec['cells'].items():
        nb['cells'][int(index)] = cell
    after = nb['cells']
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    text_changed = [i for i, (a, b) in enumerate(zip(before, after))
                    if ''.join(a['source']) != ''.join(b['source'])]
    assert changed == spec['changed_cells'] == [0, 1, 3, 5, 9, 15]
    assert text_changed == spec['changed_source_cells'] == [0, 3, 5, 9, 15]
    for i, cell in enumerate(after):
        if cell['cell_type'] == 'code':
            compile(''.join(cell['source']), f'cell{i}', 'exec',
                    flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    assert 'Thuitanium / Knowless Crew' in ''.join(after[0]['source'])
    payload = json.dumps(nb, ensure_ascii=False, separators=(',', ':')).encode()
    assert hashlib.sha256(payload).hexdigest() == spec['output_sha256'], 'output drift'
    return payload


if __name__ == '__main__':
    OUT_NB.write_bytes(build())
    print('PASS: 18 cells; changed [0,1,3,5,9,15]; exact banked SHA-256')
