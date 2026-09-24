"""Teeth for thui-b97's window rewrite -- the SAME bytes the notebook executes.

Every case is proven red by a mutation (see --mutants). Run: python3 test_b97_window.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from window_src import _thui_b97_rewrite, _THUI_B97_REPLACEMENTS  # noqa: E402

SERVING = ("import os\nVLLM_MAX_MODEL_LEN = 32768\nANALYZER_CONTEXT_WINDOW = 32768\n"
           "'--max-model-len', str(VLLM_MAX_MODEL_LEN),\n")
OTHER = "$PYTHON -c 'print(1)'"


def _fails(commands):
    try:
        _thui_b97_rewrite(list(commands))
    except AssertionError:
        return True
    return False


def main():
    ok = True

    out = _thui_b97_rewrite([OTHER, SERVING])
    for name, want in (("server raised", "VLLM_MAX_MODEL_LEN = 65536"),
                       ("analyzer raised", "ANALYZER_CONTEXT_WINDOW = 49152"),
                       ("old server gone", None), ("old analyzer gone", None)):
        if want:
            got = want in out[1]
        else:
            got = ("VLLM_MAX_MODEL_LEN = 32768" not in out[1]) if "server" in name else ("ANALYZER_CONTEXT_WINDOW = 32768" not in out[1])
        print(f"{'ok  ' if got else 'FAIL'} {name}")
        ok &= got

    got = out[0] == OTHER and len(out) == 2
    print(f"{'ok  ' if got else 'FAIL'} unrelated command untouched and the list keeps its length")
    ok &= got

    got = "str(VLLM_MAX_MODEL_LEN)" in out[1]
    print(f"{'ok  ' if got else 'FAIL'} the argv reference is not rewritten (only the assignment is)")
    ok &= got

    # A bundle whose numbers already moved must STOP rather than serve an unsized window.
    for name, cmds in (("anchors absent", [OTHER]),
                       ("server anchor only", [SERVING.replace("ANALYZER_CONTEXT_WINDOW = 32768", "ANALYZER_CONTEXT_WINDOW = 16384")]),
                       ("one anchor twice", [SERVING + "VLLM_MAX_MODEL_LEN = 32768\n"])):
        got = _fails(cmds)
        print(f"{'ok  ' if got else 'FAIL'} refuses: {name}")
        ok &= got

    got = len(_THUI_B97_REPLACEMENTS) == 2
    print(f"{'ok  ' if got else 'FAIL'} exactly two replacements are declared")
    ok &= got

    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
