"""Build B99 RungPin from the B81 notebook without running it.

Full:  /opt/homebrew/bin/python3.12 thui-b99/build_notebook.py
Smoke: /opt/homebrew/bin/python3.12 thui-b99/build_notebook.py --smoke
"""
import ast
import copy
import json
import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "thui-a5" / "out" / "thui-a5-mtp0k7s28-full25-r1"
SRC_NB = BASE / "thui-a5-mtp0k7s28-full25-r1.ipynb"
SRC_META = BASE / "kernel-metadata.json"
SMOKE = "--smoke" in sys.argv[1:]
assert set(sys.argv[1:]) <= {"--smoke"}, f"unknown arguments: {sys.argv[1:]}"
SLUG = "thui-b99-rungpin-smoke" if SMOKE else "thui-b99-rungpin-full25-r1"
OUT = HERE / "out" / SLUG
SMOKE_GAMES = ("tn36-ef4dde99", "vc33-5430563c", "bp35-0a0ad940")
SMOKE_CLOCK_S = 1800
IMPORT_ANCHOR = "import inference.agent.tool_agent as _tool_agent\n"
C15_EXTRA_OLD = "    if missing or extra:\n"
C15_SELECT = "    bm.games = [offline_by_id[game_id] for game_id in PUBLIC_GAME_IDS]\n"


GRAFT = r'''# ---- thui-b99: pin the verified trace that cleared the previous rung.
import inspect as _inspect
import json as _b99_json
import sys as _b99_sys
from pathlib import Path as _B99Path

_B99_CAP = 2048
_B99_TITLE = "VERIFIED PREVIOUS RUNG"
_B99_CLS = _tool_agent.ToolAgent
_b99_dispatch_src = _inspect.getsource(_B99_CLS._dispatch_tool)
_b99_analyze_src = _inspect.getsource(_B99_CLS.analyze)
_b99_summary_src = _inspect.getsource(_B99_CLS._summarize_step_sequence)

# Hook evidence in localrig tool_agent.py: clear predicate at 1289; dispatch/result at 2338-2347.
assert _b99_summary_src.count('any(bool(item.get("level_completed")) for item in executed_results)') == 1, \
    "thui-b99: level_completed predicate moved -- re-derive"
assert _b99_analyze_src.count("dispatch = self._dispatch_tool(state_path, tool_name, arguments)") == 1, \
    "thui-b99: dispatch call moved -- re-derive"
# Request construction/windowing is at 2037-2054 and 2140-2144; send boundary is at 2206.
assert _b99_analyze_src.count("result = self._chat_completion(messages, **request_kwargs)") == 1, \
    "thui-b99: analyzer request boundary moved -- re-derive"

_b99_orig_ensure = _B99_CLS._ensure_session
_b99_orig_dispatch = _B99_CLS._dispatch_tool
_b99_orig_chat = _B99_CLS._chat_completion


def _b99_game_id(state_path):
    path = _B99Path(state_path)
    for value in (path.parent.name, path.stem):
        match = __import__("re").search(r"[a-z0-9]{4}-[0-9a-f]{8}", value)
        if match:
            return match.group(0)
    return path.parent.name or path.stem or "unknown"


def _b99_ensure_session(self, state_path):
    prior = getattr(self, "_session_runtime_dir", None)
    out = _b99_orig_ensure(self, state_path)
    current = getattr(self, "_session_runtime_dir", None)
    if prior != current:
        self._b99_verified_previous_rung = ""
        self._b99_game_id = _b99_game_id(state_path)
    return out


def _b99_compact_result(agent):
    source = getattr(agent, "_last_action_result", None) or {}
    keys = (
        "executed", "action_num", "level", "score", "reward", "state",
        "board_changed", "done", "level_completed", "game_over", "run_complete",
        "stop_reason", "executed_count",
    )
    compact = {key: source.get(key) for key in keys if key in source}
    return _b99_json.dumps(compact, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _b99_make_pin(reasoning, action, result):
    prefix = _B99_TITLE + "\nReasoning: "
    suffix = "\nAction: " + action + "\nResult: " + result
    room = _B99_CAP - len(prefix) - len(suffix)
    assert room >= 0, "thui-b99: compact action/result exceed pin cap"
    reasoning = str(reasoning or "")
    if len(reasoning) > room:
        marker = "... [reasoning truncated]"
        reasoning = reasoning[:max(0, room - len(marker))] + marker[:room]
    pin = prefix + reasoning + suffix
    assert len(pin) <= _B99_CAP
    return pin


def _b99_dispatch(self, state_path, name, arguments):
    out = _b99_orig_dispatch(self, state_path, name, arguments)
    summary = getattr(self, "_last_step_summary", None) or {}
    if out.step_executed and summary.get("level_transition"):
        caller = _b99_sys._getframe(1).f_locals
        reasoning = caller.get("reasoning", "")
        actions = summary.get("executed_actions") or []
        action = _b99_json.dumps(actions, separators=(",", ":"), ensure_ascii=True)
        result = _b99_compact_result(self)
        self._b99_verified_previous_rung = _b99_make_pin(reasoning, action, result)
        self._b99_game_id = _b99_game_id(state_path)
        level = summary.get("level")
        print(
            f"THUI_B99_PIN game={self._b99_game_id} level={level} "
            f"chars={len(self._b99_verified_previous_rung)}",
            flush=True,
        )
    return out


def _b99_chat(self, messages, **kwargs):
    pin = getattr(self, "_b99_verified_previous_rung", "")
    if not pin:
        return _b99_orig_chat(self, messages, **kwargs)
    # Copy both list and dicts: raw/history messages are never edited (tool_agent.py:2138-2144).
    request_messages = [dict(message) for message in messages]
    request_messages.insert(1 if request_messages and request_messages[0].get("role") == "system" else 0,
                            {"role": "user", "content": pin})
    return _b99_orig_chat(self, request_messages, **kwargs)


_b99_ensure_session.__wrapped__ = _b99_orig_ensure
_b99_dispatch.__wrapped__ = _b99_orig_dispatch
_b99_chat.__wrapped__ = _b99_orig_chat
_B99_CLS._ensure_session = _b99_ensure_session
_B99_CLS._dispatch_tool = _b99_dispatch
_B99_CLS._chat_completion = _b99_chat
print("THUI_B99_GRAFT ok", flush=True)
'''


CELL0 = f"""# {SLUG} (Thuitanium / Knowless Crew) — B81 plus RungPin

{"**Smoke: 3 games at 1800 s. Numbers are not a score.**" if SMOKE else "Full public 25."}

**This is a Knowless Crew / Thuitanium experiment notebook.** Solver, prompts, clock, games and the vLLM
profile (KV 7 GiB / MTP 0 / max_num_seqs 28) are exactly `thui-a5-mtp0k7s28-full25-r1`, except for the
registered smoke subset/clock when applicable. One change: a cell-9 graft pins the trace that cleared the
previous level into a capped per-game `VERIFIED PREVIOUS RUNG` block prepended to later analyzer requests.

Serving stack by [Keith Tyser](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp),
harness by [Tufa Labs](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner),
anim solver bundle `jakobbrggen/taaf-kaggle-source-anim-20260807-anim`.
"""


def patch_cell9(source):
    assert source.count(IMPORT_ANCHOR) == 1, "cell 9 import anchor moved -- re-derive"
    return source.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + GRAFT)


def patch_smoke_cell15(source):
    match = re.search(
        r"PUBLIC_GAME_IDS = tuple\(\[\n(?:    \"[a-z0-9]{4}-[0-9a-f]{8}\",?\n){25}\]\)\n",
        source,
    )
    assert match, "cell 15: 25-game PUBLIC_GAME_IDS tuple not found"
    assert all(f'"{game}"' in match.group(0) for game in SMOKE_GAMES)
    source = source.replace(
        match.group(0),
        "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-b99 smoke subset\n",
    )
    assert source.count("!= 25") == 2
    assert source.count(C15_EXTRA_OLD) == 1
    assert source.count(C15_SELECT) == 1
    source = source.replace("!= 25", "!= len(PUBLIC_GAME_IDS)")
    source = source.replace(
        C15_EXTRA_OLD,
        "    if missing or (extra and len(PUBLIC_GAME_IDS) == 25):   # smoke subset leaves extras\n",
    )
    source = source.replace(
        C15_SELECT,
        C15_SELECT
        + f"    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-b99 smoke clock\n"
        + '    print(f"thui-b99: smoke {len(bm.games)} games @ {bm.solver.max_runtime_s_per_game} s", flush=True)\n',
    )
    return source


def main():
    notebook = json.loads(SRC_NB.read_text())
    original = copy.deepcopy(notebook)
    cells = notebook["cells"]
    assert "Knowless Crew" in "".join(cells[0]["source"])
    cells[0]["source"] = CELL0.splitlines(keepends=True)
    cells[9]["source"] = patch_cell9("".join(cells[9]["source"])).splitlines(keepends=True)
    if SMOKE:
        smoke_source = patch_smoke_cell15("".join(cells[15]["source"]))
        compile(smoke_source, "cell15", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells[15]["source"] = smoke_source.splitlines(keepends=True)

    changed = [index for index, pair in enumerate(zip(original["cells"], cells)) if pair[0] != pair[1]]
    expected = [0, 9, 15] if SMOKE else [0, 9]
    assert changed == expected, (changed, expected)
    assert len(original["cells"]) == len(cells)
    compile("".join(cells[9]["source"]), "cell9", "exec")

    source_meta = json.loads(SRC_META.read_text())
    metadata = copy.deepcopy(source_meta)
    metadata.update(
        id=f"yocybercode/{SLUG}",
        title=SLUG,
        code_file=f"{SLUG}.ipynb",
        is_private=True,
    )
    meta_changes = {key for key in metadata if metadata[key] != source_meta.get(key)}
    assert meta_changes == {"id", "title", "code_file"}, meta_changes
    for key in source_meta:
        if key not in meta_changes:
            assert metadata[key] == source_meta[key], key
    assert metadata["id"] == f"yocybercode/{SLUG}"
    assert metadata["is_private"] is True

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{SLUG}.ipynb").write_text(json.dumps(notebook, indent=1))
    (OUT / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2))
    print(f"built {SLUG}: cells changed {changed}, id={metadata['id']}, private={metadata['is_private']}")


if __name__ == "__main__":
    main()

