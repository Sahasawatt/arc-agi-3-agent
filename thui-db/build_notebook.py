"""thui-db -- the fast base with a DEATH BLACKLIST grafted into the harness (2026-09-15, from the frontier-5 diagnosis).

Why. The harness wipes the six summarized-knowledge fields on every in-level `game_over` (tool_agent.py:1117-1126), and the
wipe-guard A/B (thui-wm, r1) showed that keeping them is not the answer: on bp35 the kept plan replayed the fatal click
`MOUSE(row=33, col=21)` 7 times in 10 deaths, and on sp80 level 2 every death (12/12 across b78 + v0) was SPACE while the
model's own tool printed `game_over True` and it kept sweeping. In the control arm the model dies once per idea because the
wipe erases the idea; in the guard arm it dies repeatedly because the idea survives. Neither arm carries the one fact that
should survive a death: WHICH ACTION killed you, on WHICH level. notes/frontier-5-stall-diagnosis-2026-09-15.md §2-3.

What the graft does (cell 9, applied to the IMPORTED module after his serving setup; solver tree on disk untouched):
  TWO wrappers, one ledger. `_thui_db` on the agent instance: {level: {action_display: count}}, outside `_summarized_knowledge`,
  so the harness's wipe never touches it and a level change never needs a reset (keyed by level).
  1. `ToolAgent._summarize_step_sequence(action_results)`: after the original returns, every executed item whose
     `game_over` is true records its last executed action (`executed_actions[-1]`, else `action_display`) under `item["level"]`
     and prints `THUI_DB_RECORD level=<n> action=<a> n=<count>`.
  2. `ToolAgent._build_user_prompt(...)`: after the original returns the prompt text, if the ledger has entries for
     `current_frame.level` a block is inserted before the harness's own `end of world model. ` line:
        - Fatal actions on THIS level, each ended the game (do not repeat them; treat cells adjacent to a fatal MOUSE cell as
          suspect and test them last): MOUSE(row=33, col=21) x7, SPACE x2
     and prints `THUI_DB_INJECT level=<n> distinct=<k> deaths=<m>`. Nothing else in the prompt, model, actions or knowledge
     changes. --control: identical notebook, no wrapper (marker THUI_DB_GRAFT control).

v1 (2026-09-15, after the v0 smoke FAILED rule 3 -- notes/db-smoke-verdict-2026-09-15.md): the ledger now keeps, per level, every
life that ended in death as {total actions, count per action TYPE, the type that came last}, counted from the executed actions
themselves (a RESET or a level change starts a new life). Two budgets are read from those lives: an ACTION budget (>= 3 lives whose
totals agree within +-1: sp80 L1 = 30, tn36 = 61, sp80 L2 = 45) and a per-TYPE budget (>= 3 lives ending on type T with the same
count M >= 2 of T in >= 2/3 of them: sp80 L2 = 5 SPACE -- b78 died on the 5th-6th SPACE in 7/7 lives, and v0's fatal list "SPACE
x3" taught the model to stop shooting, after which it died on the move budget instead). A type budget is rendered as "T is a
LIMITED RESOURCE of M-1 safe uses per life, keep using it", never as a fatal action; the fatal list keeps only actions no budget
explains; the v0 clause "do not spend lives on exploration" is gone (it did nothing on tn36, which already knew its 61 ticks, and
it could suppress the shooting sp80 needs). Markers now carry `budget_actions=` and `budget_types=`.

Pre-registered read (smoke: bp35 / sp80 / tn36 at 1,800 s -- the three games with the most in-level deaths -- treatment vs
--control), oracle = thui-db/repeat_fatal_read.py over the events (0 GPU, also run on the 4 existing draws as the baseline):
  1. THUI_DB_GRAFT ok; >= 1 THUI_DB_RECORD AND >= 1 THUI_DB_INJECT in the treatment log. Zero = no death happened inside the
     clock on three games chosen for dying -> VOID, not a result.
  2. REPEAT-FATAL RATE: among deaths that are not the first death on their level, the share whose action was already fatal on
     that level. Baseline from the 4 full-25 draws is printed by the reader; smoke PASS needs v0's repeat count < ctl's on the
     games where both arms died >= 2 times, AND levels >= control on all three (the blacklist must not lose a level).
  3. What a PASS buys: a full-25 A/B (v0 vs ctl, same day; rank_runs.py primary; secondary = deaths and repeat-fatal per game).
     Expectation stated now: the effect is confined to death games (9-12 of 25 per draw); MDE ~4 public points per single draw,
     so the smoke reads mechanism + no-regression and the full-25 reads repeat-fatal count, not the score gap.

Build:  PYTHONUTF8=1 python thui-db/build_notebook.py             -> taaf-thui-db-v0.ipynb  (smoke, treatment)
        PYTHONUTF8=1 python thui-db/build_notebook.py --control   -> taaf-thui-db-ctl.ipynb (smoke, no wrapper)
        PYTHONUTF8=1 python thui-db/build_notebook.py --full           -> taaf-thui-db-v0-full25-r1.ipynb
        PYTHONUTF8=1 python thui-db/build_notebook.py --full --control -> taaf-thui-db-ctl-full25-r1.ipynb
Teeth:  python thui-db/test_db_graft.py   (0 GPU: executes the notebook's own cell-9 source against a stub)
Push:   python scripts/kaggle_push_kernel.py <this dir>   (from arc-agi-pub; rebuild the variant first -- code_file is shared)
"""
from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAST = HERE.parent / "thui-fast"
L1 = HERE.parent / "thui-l1" / "build_notebook.py"
SRC_NB = FAST / "upstream-keithtyser-duck-qwen3-8-flash-next-nvfp4-mtp.ipynb"
SRC_META = FAST / "upstream-kernel-metadata.json"
OWNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), "sahasawatt")
FULL = "--full" in sys.argv
CONTROL = "--control" in sys.argv
VERSION = "v1"   # v0 = fatal list + gap-based budget (smoke FAIL rule 3, 2026-09-15); v1 = per-life counts, per-action-type budgets
# the second control draw gets its own slug so the v0-era control output (kout-sa-thui-db-ctl/) stays on disk as draw 1
SLUG = (("thui-db-ctl-full25-r1" if CONTROL else f"thui-db-{VERSION}-full25-r1") if FULL
        else ("thui-db-ctl-r2" if CONTROL else f"thui-db-{VERSION}"))
OUT_NB = HERE / f"taaf-{SLUG}.ipynb"
SMOKE_GAMES = ("bp35-0a0ad940", "sp80-589a99af", "tn36-ef4dde99")   # most in-level deaths in the 9-draw Flash census
SMOKE_CLOCK_S = 1800

sys.path.insert(0, str(FAST))
import build_notebook as fast  # noqa: E402
_spec = importlib.util.spec_from_file_location("thui_l1_builder", L1)
l1 = importlib.util.module_from_spec(_spec)
_argv, sys.argv = sys.argv, sys.argv[:1]   # the L1 builder reads its own flags at import; we only want its constants
_spec.loader.exec_module(l1)
sys.argv = _argv

CELL0_MD = f"""# {SLUG} (Thuitanium / Knowless Crew) — the fast base with a death blacklist

**This is a Knowless Crew / Thuitanium fork, and the solver is not ours.** Same two upstreams as `thui-fast-v0`, executed as they ship:

- **Serving**: Keith Tyser's [Duck Qwen3.8 Flash Next NVFP4 MTP](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp)
  — his pinned `RadixArk/Qwen3.8-Flash-Next-NVFP4` asset, offline vLLM runtime, NVFP4 PLE patch, MTP-3 profile, watchdog.
- **Solver**: the Tufa Labs duck harness (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
  Michal Tesnar, Stefano Viel) — his source bundle, unmodified on disk.
- **Weights**: RadixArk's NVFP4 quantisation of Qwen/Qwen3.8-Flash-Next (Qwen licence terms apply).

⚠️ Every score quoted by any upstream is theirs.

## What we changed

- **cell 0 / 1** — this header; Tufa's header reworded in the third person.
- **cell 3** — full diagnostics on an interactive public run, minimal in a real rerun.
- **cell 5 / 15** — the competition mount resolved (Kaggle serves two layouts).
- **cell 9** — {"CONTROL arm: the harness module is imported and asserted untouched (no wrapper)." if CONTROL else "two wrappers on the imported harness: `ToolAgent._summarize_step_sequence` records, per level, the action that ended the game; `ToolAgent._build_user_prompt` lists those actions in the next prompt as fatal-do-not-repeat. The ledger lives outside the summarized knowledge, so the harness's own wipe on game_over leaves it intact. Model, actions and knowledge untouched."}
{"- **cell 15** — smoke: " + ", ".join(SMOKE_GAMES) + f" at {SMOKE_CLOCK_S} s each." if not FULL else "- **cell 15** — all 25 public games, upstream clock (full-25 A/B draw r1)."}

Build script: `thui-db/build_notebook.py` in our agent repo (asserts exactly those cells changed). Lever from notes/frontier-5-stall-diagnosis-2026-09-15.md.
"""

CELL9_COMMON = '''
# ---- thui-db: death blacklist. Pure functions first, so the teeth drive them in-kernel.
assert "inference" not in sys.modules, "solver imported before the DB graft"

def _thui_db_fatal_of(item):
    """The action that ended the game in one executed result item, or None."""
    if not item or not item.get("executed") or not item.get("game_over"):
        return None
    acts = item.get("executed_actions")
    if isinstance(acts, list) and acts:
        return str(acts[-1]).strip() or None
    a = item.get("action_display") or item.get("action_name")
    return str(a).strip() if a else None

def _thui_db_kind(action):
    """Action TYPE for budget counting: MOUSE(row=.., col=..) -> MOUSE, everything else verbatim."""
    a = str(action or "").strip()
    return "MOUSE" if a.startswith("MOUSE") else a

def _thui_db_budgets(lives):
    """Budgets a level enforces, read from the lives that ENDED IN DEATH there. Each life = {"total": n, "counts": {type: c},
    "last": type}. Returns {"actions": N|None, "types": {type: M}}:
      actions: >= 3 lives whose totals agree within +-1 -> the median total (sp80 L1 = 30, tn36 = 61, sp80 L2 = 45).
      types:   a type T with >= 3 lives ending on T where >= 2/3 of them hold the same count M >= 2 of T -> M (sp80 L2 = 5 SPACE).
    A type budget is NOT a fatal action: the M-th use ends the life whatever it does; only the count is the mechanic."""
    lives = [l for l in (lives or []) if l and isinstance(l.get("total"), int)]
    out = {"actions": None, "types": {}}
    if len(lives) >= 3:
        totals = sorted(l["total"] for l in lives)
        if totals[-1] - totals[0] <= 1:
            out["actions"] = totals[len(totals) // 2]
    by_last = {}
    for l in lives:
        by_last.setdefault(l.get("last"), []).append(int((l.get("counts") or {}).get(l.get("last"), 0)))
    for t, cs in by_last.items():
        if t and len(cs) >= 3:
            mode = max(set(cs), key=cs.count)
            # >= 3 lives must AGREE (2 of 3 called "13 DOWN/life" and "2 LEFT/life" budgets on real draws) and be >= 2/3 of all
            if mode >= 2 and cs.count(mode) >= 3 and cs.count(mode) * 3 >= len(cs) * 2:
                out["types"][t] = mode
    return out

def _thui_db_lines(ledger, level):
    """Prompt lines for one level's ledger, [] when nothing is recorded. Budgets first, then the fatal list for actions no
    budget explains (a level with an action budget lists no fatal actions at all: the last move before such a death is just
    the N-th move)."""
    per = (ledger or {}).get(level) or {}
    fatal, lives = per.get("fatal") or {}, per.get("lives") or []
    b = _thui_db_budgets(lives)
    lines = []
    if b["actions"] is not None:
        lines.append(f"- THIS level has ended the game after ~{b['actions']} actions per life, {len(lives)} lives in a row, "
                     f"regardless of which action came last: an action BUDGET, not a fatal move. Every reset gives {b['actions']} "
                     "actions; make them count toward the goal.")
    for t, m in sorted(b["types"].items()):
        lines.append(f"- THIS level ends the game on the {m}th {t} of a life (seen in every life that ended on {t}): {t} is a "
                     f"LIMITED RESOURCE of {m - 1} safe uses per life, not a killer. Keep using it, but never the {m}th time "
                     "without having reached the goal.")
    rest = {a: n for a, n in fatal.items() if b["actions"] is None and _thui_db_kind(a) not in b["types"]}
    if rest:
        shown = ", ".join(f"{a} x{n}" for a, n in sorted(rest.items(), key=lambda kv: (-kv[1], kv[0])))
        lines.append("- Fatal actions on THIS level, each ended the game (do not repeat them; treat cells adjacent to a fatal "
                     "MOUSE cell as suspect and test them last): " + shown)
    return lines

def _life(total, last, **counts):
    return {"total": total, "counts": counts, "last": last}

assert _thui_db_fatal_of({"executed": True, "game_over": True, "executed_actions": ["UP", "MOUSE(row=33, col=21)"]}) == "MOUSE(row=33, col=21)"
assert _thui_db_fatal_of({"executed": True, "game_over": True, "action_display": "SPACE"}) == "SPACE"
assert _thui_db_fatal_of({"executed": True, "game_over": False, "action_display": "SPACE"}) is None
assert _thui_db_fatal_of({"executed": False, "game_over": True, "action_display": "SPACE"}) is None
assert _thui_db_fatal_of(None) is None
assert _thui_db_kind("MOUSE(row=3, col=4)") == "MOUSE" and _thui_db_kind("SPACE") == "SPACE" and _thui_db_kind(None) == ""
_sp80L1 = [_life(30, "RIGHT", RIGHT=12, DOWN=18), _life(30, "DOWN", RIGHT=10, DOWN=20), _life(31, "LEFT", LEFT=31)]
assert _thui_db_budgets(_sp80L1) == {"actions": 30, "types": {}}
_sp80L2 = [_life(23, "SPACE", SPACE=6, LEFT=17), _life(29, "SPACE", SPACE=5, LEFT=24), _life(32, "SPACE", SPACE=5, UP=27),
           _life(19, "SPACE", SPACE=5, UP=14)]
assert _thui_db_budgets(_sp80L2) == {"actions": None, "types": {"SPACE": 5}}
assert _thui_db_budgets(_sp80L2[:2]) == {"actions": None, "types": {}} and _thui_db_budgets([]) == {"actions": None, "types": {}}
assert _thui_db_budgets([_life(10, "SPACE", SPACE=1), _life(12, "SPACE", SPACE=1), _life(14, "SPACE", SPACE=1)]) == {"actions": None, "types": {}}
assert _thui_db_lines({}, 2) == [] and _thui_db_lines({2: {}}, 2) == [] and _thui_db_lines({1: {"fatal": {"SPACE": 1}}}, 2) == []
assert _thui_db_lines({2: {"fatal": {"SPACE": 2, "MOUSE(row=33, col=21)": 7}, "lives": []}}, 2)[0].endswith("MOUSE(row=33, col=21) x7, SPACE x2")
_bl = _thui_db_lines({1: {"fatal": {"RIGHT": 1, "DOWN": 1, "LEFT": 1}, "lives": _sp80L1}}, 1)
assert len(_bl) == 1 and "BUDGET" in _bl[0] and "~30 actions" in _bl[0] and "RIGHT" not in _bl[0] and "exploration" not in _bl[0]
_tl = _thui_db_lines({2: {"fatal": {"SPACE": 4, "MOUSE(row=1, col=2)": 1}, "lives": _sp80L2}}, 2)
assert len(_tl) == 2 and "5th SPACE" in _tl[0] and "4 safe uses" in _tl[0] and "Keep using it" in _tl[0]
assert _tl[1].endswith("MOUSE(row=1, col=2) x1") and "SPACE x4" not in _tl[1]
print("thui-db: ledger teeth ok", flush=True)
'''

CELL9_WRAP = '''
import inference.agent.tool_agent as _ta
_orig_db_summarize = _ta.ToolAgent._summarize_step_sequence
_orig_db_prompt = _ta.ToolAgent._build_user_prompt

def _thui_db_summarize(self, action_results):
    summary = _orig_db_summarize(self, action_results)
    try:
        ledger = getattr(self, "_thui_db", None)
        if ledger is None:
            ledger = self._thui_db = {}
        life = getattr(self, "_thui_db_life", None)
        if life is None:
            life = self._thui_db_life = {"total": 0, "counts": {}, "level": None}
        for item in action_results or []:
            if not isinstance(item, dict) or not item.get("executed"):
                continue
            level = item.get("level")
            if life["level"] is not None and level != life["level"] and not item.get("game_over"):
                life.update({"total": 0, "counts": {}})      # a level change starts a new life
            life["level"] = level
            acts = item.get("executed_actions")
            if not (isinstance(acts, list) and acts):
                acts = [item.get("action_display") or item.get("action_name")]
            for a in acts:
                k = _thui_db_kind(a)
                if k == "RESET":
                    life.update({"total": 0, "counts": {}})   # the agent reset on its own: new life, no death
                    continue
                if k:
                    life["total"] += 1
                    life["counts"][k] = life["counts"].get(k, 0) + 1
            fatal = _thui_db_fatal_of(item)
            if fatal:
                per = ledger.setdefault(level, {"fatal": {}, "lives": []})
                per["fatal"][fatal] = per["fatal"].get(fatal, 0) + 1
                per["lives"].append({"total": life["total"], "counts": dict(life["counts"]), "last": _thui_db_kind(fatal)})
                b = _thui_db_budgets(per["lives"])
                print(f"THUI_DB_RECORD level={level} action={fatal} n={per['fatal'][fatal]} life_total={life['total']} "
                      f"deaths={len(per['lives'])} budget_actions={b['actions']} budget_types={b['types']}", flush=True)
                life.update({"total": 0, "counts": {}})       # the solver auto-RESETs after a death: new life
    except Exception as exc:  # never let the graft kill a step
        print(f"thui-db: record error {exc!r}", flush=True)
    return summary

def _thui_db_prompt(self, action_num, *args, **kwargs):
    text = _orig_db_prompt(self, action_num, *args, **kwargs)
    try:
        frame = kwargs.get("current_frame")
        level = getattr(frame, "level", None) if frame is not None else None
        lines = _thui_db_lines(getattr(self, "_thui_db", None), level)
        if lines:
            block = "\\n".join(lines) + "\\n"
            anchor = "end of world model. "
            text = text.replace(anchor, block + anchor, 1) if anchor in text else text + "\\n" + block
            per = self._thui_db.get(level) or {}
            b = _thui_db_budgets(per.get("lives"))
            print(f"THUI_DB_INJECT level={level} distinct={len(per.get('fatal') or {})} deaths={len(per.get('lives') or [])} "
                  f"budget_actions={b['actions']} budget_types={b['types']} lines={len(lines)}", flush=True)
    except Exception as exc:
        print(f"thui-db: inject error {exc!r}", flush=True)
    return text

_ta.ToolAgent._summarize_step_sequence = _thui_db_summarize
_ta.ToolAgent._build_user_prompt = _thui_db_prompt
assert _ta.ToolAgent._summarize_step_sequence is _thui_db_summarize and _ta.ToolAgent._build_user_prompt is _thui_db_prompt
print(f"THUI_DB_GRAFT ok agent={Path(_ta.__file__)}", flush=True)
'''

CELL9_CTL = '''
import inference.agent.tool_agent as _ta
assert _ta.ToolAgent._summarize_step_sequence.__name__ == "_summarize_step_sequence"
assert _ta.ToolAgent._build_user_prompt.__name__ == "_build_user_prompt"
print("THUI_DB_GRAFT control (no wrapper installed)", flush=True)
'''

CELL15_SELECT_SMOKE = (l1.CELL15_SELECT_OLD +
                       f'    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-db smoke clock\n'
                       f'    print(f"thui-db: smoke {{len(bm.games)}} games @ {{bm.solver.max_runtime_s_per_game}} s", flush=True)\n')


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 18, f"{SRC_NB.name}: expected 18 cells, found {len(cells)}"
    before = ["".join(c["source"]) for c in cells]
    assert before[0].startswith("## About this fork") and before[1].startswith("# Tufa Labs ARC3 submission")

    def rep(i: int, old: str, new: str) -> None:
        s = "".join(cells[i]["source"])
        assert s.count(old) == 1, f"cell {i}: anchor not found exactly once ({s.count(old)}): {old[:70]!r}"
        cells[i]["source"] = s.replace(old, new).splitlines(keepends=True)

    cells[0]["cell_type"] = "markdown"; cells[0]["source"] = CELL0_MD.splitlines(keepends=True)
    cells[1]["source"] = fast.CELL1_MD.splitlines(keepends=True); cells[1].pop("attachments", None)
    rep(3, fast.CELL3_OLD, fast.CELL3_NEW.replace("thui-fast", "thui-db"))
    rep(5, l1.CELL5_ANCHOR, "        _WHEELS,\n")
    cells[5]["source"] = (l1.CELL5_RESOLVER.replace("thui-l1", "thui-db") + "".join(cells[5]["source"])).splitlines(keepends=True)
    cells[9]["source"] = ("".join(cells[9]["source"]) + CELL9_COMMON + (CELL9_CTL if CONTROL else CELL9_WRAP)).splitlines(keepends=True)
    rep(15, l1.CELL15_MOUNT_OLD, l1.CELL15_MOUNT_NEW.replace("thui-l1", "thui-db"))
    if not FULL:
        s = "".join(cells[15]["source"])
        m = re.search(r"PUBLIC_GAME_IDS = tuple\(\[\n(?:    \"[a-z0-9]{4}-[0-9a-f]{8}\",?\n){25}\]\)\n", s)
        assert m, "cell 15: the 25-game PUBLIC_GAME_IDS tuple not found"
        for g in SMOKE_GAMES:
            assert f'"{g}"' in m.group(0), f"{g} is not one of the 25 public ids"
        s = s.replace(m.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-db smoke subset\n")
        assert s.count("!= 25") == 2, s.count("!= 25")
        s = s.replace("!= 25", "!= len(PUBLIC_GAME_IDS)")
        assert s.count(l1.CELL15_EXTRA_OLD) == 1 and s.count(l1.CELL15_SELECT_OLD) == 1
        s = s.replace(l1.CELL15_EXTRA_OLD, l1.CELL15_EXTRA_NEW.replace("thui-l1", "thui-db")).replace(l1.CELL15_SELECT_OLD, CELL15_SELECT_SMOKE)
        cells[15]["source"] = s.splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert changed == [0, 1, 3, 5, 9, 15], f"cells changed {changed}"
    assert "attachments" not in cells[1] and "tufa_labs.png" not in json.dumps(nb)
    for i, c in enumerate(cells):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]), filename=f"cell{i}")
    assert after[0].startswith(f"# {SLUG} (Thuitanium / Knowless Crew)")
    for bad in ("Tufa Labs ARC3 submission", "our milestone-winning", "attachment:"):
        assert bad not in after[1]
    assert after[9].count("THUI_DB_GRAFT") == 1 and after[9].count("ledger teeth ok") == 1
    assert ("_thui_db_summarize" in after[9]) == (not CONTROL)
    assert "THUI_L1" not in after[9] and "THUI_WM" not in after[9] and "thui-l1" not in after[5] and "thui-l1" not in after[15]
    assert after[7] == before[7] and after[11] == before[11] and after[13] == before[13]
    assert l1.WHEELS_NESTED not in after[5] and l1.WHEELS_NESTED not in after[15]
    assert ("smoke" in after[15]) == (not FULL)

    # the ledger functions run here too: the same source the kernel executes, on the same teeth
    exec(CELL9_COMMON.replace('assert "inference" not in sys.modules, "solver imported before the DB graft"\n', ""), {"sys": sys, "Path": Path})

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(SRC_META.read_text(encoding="utf-8")); meta.pop("id_no", None)
    assert meta["model_sources"] == ["keithtyser/qwen3-8-flash-next-nvfp4/PyTorch/radixark-modelopt-fp4/1"]
    assert meta["machine_shape"] == "NvidiaRtxPro6000" and meta["enable_gpu"] is True
    meta["id"] = f"{OWNER}/{SLUG}"; meta["title"] = SLUG; meta["code_file"] = OUT_NB.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}, smoke={not FULL}, control={CONTROL}")


if __name__ == "__main__":
    main()
