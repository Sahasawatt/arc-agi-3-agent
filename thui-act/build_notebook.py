"""thui-act -- the ACT-NOW breaker ported from the AVO arm (#135) onto the duck chassis (thui-v3-0).

Why here and not on AVO: the AVO arm shrinks 3.8x public->hidden (4.40 -> 1.15) against the duck line's
2.7x, so a breaker that works costs more there than it earns. The failure it targets exists on duck too:
B40 measured ~30% of analyze() turns ending with no executed action, and the 25-game replay of the AVO
transcripts (2026-09-07, local qwen3-8b, `scratchpad/avo_directive_all.py`) moved first-call action from
21/50 to 35/50 with the directive (paired sign test p = 0.049, n = 25 games) -- an 8B result, not a 27B one.

Score arithmetic that fixes the ORDER of the two stages (taaf GameRun._compute_final_score): a level's score
is min(115, (baseline/actions)^2 * 100) and only COMPLETED levels count, so an action spent on a level the
model later clears costs score quadratically, while a game with no level scores 0 whatever it spent. Hence:

  stage 1  ACT-NOW directive on top of the next user prompt after K dead turns (K = 2 with no level cleared,
           6 once one is) -- costs no action;
  stage 2  ONE simple action executed for the model through the session's step_env only if two further turns
           under the directive still execute nothing; at most 3 per level and 25 per game; a withheld action
           leaves the directive on.

Seams (anim bundle tool_agent.py, the revision Kaggle runs): class-level wraps of ToolAgent.analyze (the
after-turn read of result.step_executed; valid_actions / step_env arrive as keyword arguments from
solver.py) and ToolAgent._build_user_prompt (the directive prefix; called with keyword-only valid_actions /
current_frame). State lives in agent.__dict__['_act_state'] keyed by the game read from the state path's
stem (the #127 rule) and resets when the game changes. _last_step_summary persists across turns
(tool_agent.py), so every per-turn read is gated on step_executed.

Build (from the agent repo root):
  PYTHONUTF8=1 python thui-act/build_notebook.py            -> taaf-thui-act-v0.ipynb  (smoke: m0r0 / tr87 / sk48, 1800 s each)
  PYTHONUTF8=1 python thui-act/build_notebook.py --full     -> taaf-thui-act-v2.ipynb  (25 games; v1 = the stage-2-dead draw)
The last build writes kernel-metadata.json; build v1 last for the full push.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BASE = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--base=")), "v3")
SRC_NB = {"v3": REPO / "thuiv3" / "taaf-thui-v3-0.ipynb", "v1": REPO / "thuiv1" / "v1-1" / "taaf-thui-v1-1.ipynb"}[BASE]
META_SRC = {"v3": REPO / "thuiv3" / "kernel-metadata.json", "v1": REPO / "thuiv1" / "v1-1" / "kernel-metadata.json"}[BASE]
OWNER = "sahasawatt"

SMOKE_GAMES = ("m0r0", "tr87", "sk48")   # the 0-action game of the AVO draw, plus two never-clear games
GAME_CLOCK_S = 1800                      # yield 180 on the v3 chassis -> ~10 turns per game, enough for K=2 + 2
FULL = "--full" in sys.argv

CELL0_MD_SMOKE = """# thui-act-v0 (Thuitanium / Knowless Crew) — smoke: the ACT-NOW breaker on the duck chassis (3 games)

**Infrastructure smoke, not a scoring run.** `thui-v3-0` (the B48 chassis: thui-v1-1 + yield 180, the standing-best
build) byte-for-byte except cells 4, 12 and 14 (4 + one line of 14: the competition mount is resolved, not assumed —
version 1 died at 6.5 s on Kaggle's flat `/kaggle/input/<comp>` layout). Cell 12 wraps `ToolAgent.analyze` and `ToolAgent._build_user_prompt`:
after 2 analyze() calls in a row that execute no action (6 once the game has cleared a level) the next prompt opens
with an ACT-NOW directive (costs no action); if two more turns under it still execute nothing, ONE simple action is
executed for the model through the session's `step_env`, at most 3 per level and 25 per game. Cell 14 filters to
m0r0 / tr87 / sk48 at 1800 s each. Numbers are meaningless and must never be quoted.
Design: `notes/B70-act-now-breaker-on-duck-design.md`; the AVO original is #135 (`thui-avo/build_notebook.py --v1`).

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

CELL0_MD_FULL = """# thui-act-v2 (Thuitanium / Knowless Crew) — the ACT-NOW breaker on the duck chassis, full 25 games (stage 2 wired)

`thui-v3-0` (the B48 chassis: thui-v1-1 + yield 180, the standing-best build) byte-for-byte except cell 12 (plus the competition-mount resolver in cell 4 and one line of 14), which
wraps `ToolAgent.analyze` and `ToolAgent._build_user_prompt`: after 2 analyze() calls in a row that execute no
action (6 once the game has cleared a level) the next prompt opens with an ACT-NOW directive (costs no action); if
two more turns under it still execute nothing, ONE simple action is executed for the model through the session's
`step_env`, at most 3 per level and 25 per game. **v2**: v1 (public 5.51, in the band) never armed stage 2 — the
solver passes engine action names (`ACTION1`…) and the wrapper filtered them against model names; v2 maps through the
bundle's `to_model_action` first and logs a withheld action when no simple action exists. Seed, temperature, clock, window
and games inherited unchanged.
Oracle: paired **levels** vs the B48 build's public pool (`eval/fixtures/thuiv3-pool.json`), B35 floor on both draws;
forced actions must be rare on games that score (they cost score quadratically) and the directive must fire on the
games that never act. Design: `notes/B70-act-now-breaker-on-duck-design.md`; the AVO original is #135.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

CELL12_SUFFIX = r'''

# ======================================================================================
# thui-act: the ACT-NOW breaker (ported from thui-avo v1, #135) on the duck ToolAgent.
# Score = sum over COMPLETED levels of min(115, (baseline/actions)^2 * 100) (taaf GameRun._compute_final_score):
# an action spent on a level the model later clears costs score quadratically; a game with no level scores 0
# whatever it spent. So the directive (0 actions) comes first and an executed action only when it changed nothing,
# capped per level so the denominator cannot run away on a level the model then clears.
from inference.agent import tool_agent as _ta
from inference.agent.action_names import to_model_action as _act_to_model
from pathlib import Path as _ActPath

_ACT_DIRECTIVE_NO_LEVEL = 2    # dead analyze() calls in a row (step_executed False) before the directive; no level cleared
_ACT_DIRECTIVE_SCORING = 6     # same once the game has cleared a level (a scoring game needs room to think)
_ACT_FORCED_AFTER = 2          # dead turns UNDER the directive before an action is executed for the model
_ACT_FORCED_PER_LEVEL = 3      # (b/(b+3))^2 on a 30-action level is -17%; on a dead game it is +everything
_ACT_FORCED_CAP = 25           # per game, so a dead game cannot become a random walk
_ACT_SIMPLE = ("UP", "DOWN", "LEFT", "RIGHT", "SPACE")   # never MOUSE (needs coordinates), never RESET
_ACT_STATS = {"games": 0, "dead_turns": 0, "directive_turns": 0, "forced": 0, "forced_executed": 0,
              "forced_capped": 0, "wrapper_errors": 0}
_ACT_QUIET = [False]           # teeth drive the breaker on a fake agent; their log lines must not reach the run log
_orig_act_analyze = _ta.ToolAgent.analyze
_orig_act_prompt = _ta.ToolAgent._build_user_prompt


def _act_log(msg):
    if not _ACT_QUIET[0]:
        print(msg, flush=True)


def _act_game(state_path):
    try:
        return _ActPath(str(state_path)).stem.split("_")[0][:4]   # the #127 rule: the runtime dir is flat on Kaggle
    except Exception:
        return "????"


def _act_state(agent, game=None):
    st = agent.__dict__.get("_act_state")
    if st is None or (game is not None and st.get("game") not in (None, game)):
        st = agent.__dict__["_act_state"] = {"game": game, "dead": 0, "forced": 0, "forced_at_level": {}, "cleared": 0,
                                             "acts": [], "directive": False}
        _ACT_STATS["games"] += 1
    if st.get("game") is None and game is not None:
        st["game"] = game
    return st


def _act_simple(valid_actions):
    # v1 defect: the solver hands analyze() ENGINE names (ACTION1..ACTION7, via _engine_action_names) and this filtered
    # them against MODEL names -> an empty list -> stage 2 never armed, silently. Map through the bundle's own table first.
    names = []
    for a in (valid_actions or []):
        raw = str(getattr(a, "name", a)).upper()
        try:
            name = str(_act_to_model(raw) or raw).upper()
        except Exception:
            name = raw
        if name not in names:
            names.append(name)
    return [a for a in names if a in _ACT_SIMPLE]


def _act_pick(valid_actions, n):
    cand = _act_simple(valid_actions)
    return cand[n % len(cand)] if cand else None


def _act_directive(st):
    acts = ", ".join(st.get("acts") or list(_ACT_SIMPLE))
    return ("ACT NOW. You have ended " + str(st["dead"]) + " turns in a row without executing a single action: each turn "
            "is cut at the yield while you are still inspecting, and a game with no completed level scores 0 no matter "
            "how well it is understood. Your FIRST tool call this turn must be `action([...])` with one action from: "
            + acts + ". Inspect the board AFTER it has changed, not before. If you truly cannot choose, take the first "
            "one; a wrong action teaches more than another inspection.")


def _act_prompt(self, action_num, **kwargs):
    base = _orig_act_prompt(self, action_num, **kwargs)
    try:
        st = self.__dict__.get("_act_state")
        if st is not None:
            frame = kwargs.get("current_frame")
            lvl = int(getattr(frame, "level", 0) or 0) if frame is not None else 0
            if lvl > 1:
                st["cleared"] = max(st["cleared"], lvl - 1)
            va = _act_simple(kwargs.get("valid_actions"))
            if va:
                st["acts"] = va
            if st.get("directive"):
                _ACT_STATS["directive_turns"] += 1
                return _act_directive(st) + "\n\n" + base
    except Exception as exc:
        _ACT_STATS["wrapper_errors"] += 1
        print(f"thui-act: wrapper error (prompt) {type(exc).__name__}: {str(exc)[:160]}", flush=True)
    return base


def _act_after_turn(agent, result, state_path, valid_actions, step_env):
    """The breaker. Pure function of the turn's result and the agent's own bookkeeping; drivable by teeth."""
    gid = _act_game(state_path)
    st = _act_state(agent, gid)
    executed = bool(getattr(result, "step_executed", False))
    summ = agent._last_step_summary or {}
    if valid_actions:
        st["acts"] = _act_simple(valid_actions)
    if executed:
        try:
            lvl = int(summ.get("level") or 0)
            if lvl > 1:
                st["cleared"] = max(st["cleared"], lvl - 1)
        except (TypeError, ValueError):
            pass
        st["dead"] = 0
        st["directive"] = False
    else:
        st["dead"] += 1
        _ACT_STATS["dead_turns"] += 1
    k = _ACT_DIRECTIVE_SCORING if st["cleared"] > 0 else _ACT_DIRECTIVE_NO_LEVEL
    if st["dead"] >= k and not st["directive"]:
        st["directive"] = True
        _act_log(f"thui-act: game={gid} ACT-NOW directive on after {st['dead']} dead turns (cleared {st['cleared']})")
    at_level = st["forced_at_level"].get(st["cleared"], 0)
    if st["dead"] >= k + _ACT_FORCED_AFTER and step_env is not None:
        if st["forced"] >= _ACT_FORCED_CAP or at_level >= _ACT_FORCED_PER_LEVEL:
            if st["dead"] == k + _ACT_FORCED_AFTER:
                _ACT_STATS["forced_capped"] += 1
                _act_log(f"thui-act: game={gid} forced action withheld (level {st['cleared']}: {at_level}/{_ACT_FORCED_PER_LEVEL}, "
                         f"game {st['forced']}/{_ACT_FORCED_CAP}); directive stays on")
        else:
            act = _act_pick(valid_actions, st["forced"])
            if act is None:
                if st["dead"] == k + _ACT_FORCED_AFTER:
                    _ACT_STATS["forced_capped"] += 1
                    _act_log(f"thui-act: game={gid} forced action withheld: no simple action among {list(valid_actions or [])[:8]}")
            else:
                payload = step_env({"actions": [act]})
                ok = isinstance(payload, dict) and bool(payload.get("executed"))
                st["forced"] += 1
                st["forced_at_level"][st["cleared"]] = at_level + 1
                st["dead"] = 0
                st["directive"] = False
                _ACT_STATS["forced"] += 1
                _ACT_STATS["forced_executed"] += int(ok)
                _act_log(f"thui-act: game={gid} forced #{st['forced']} act={act} after {k + _ACT_FORCED_AFTER} dead turns "
                         f"(level {st['cleared']}: {at_level + 1}/{_ACT_FORCED_PER_LEVEL}) executed={ok} "
                         f"changed={payload.get('board_changed') if isinstance(payload, dict) else None} "
                         f"level_completed={payload.get('level_completed') if isinstance(payload, dict) else None}")
    return st


def _act_analyze(self, state_path, action_num, valid_actions=None, step_env=None, **kwargs):
    try:
        _act_state(self, _act_game(state_path))   # bind the game BEFORE the turn so the prompt wrap sees this game's state
    except Exception:
        pass
    result = _orig_act_analyze(self, state_path, action_num, valid_actions=valid_actions, step_env=step_env, **kwargs)
    if result is None or getattr(result, "retryable_failure", False):
        return result
    try:
        _act_after_turn(self, result, state_path, valid_actions, step_env)
    except Exception as exc:   # the breaker must never break the harness path
        _ACT_STATS["wrapper_errors"] += 1
        print(f"thui-act: wrapper error {type(exc).__name__}: {str(exc)[:160]}", flush=True)
    return result


_ta.ToolAgent.analyze = _act_analyze
_ta.ToolAgent._build_user_prompt = _act_prompt
assert _ta.ToolAgent.analyze is _act_analyze and _ta.ToolAgent._build_user_prompt is _act_prompt, "thui-act: wraps did not land"

# teeth: drive the breaker on a fake agent with a stub step_env, before any game runs
class _ActFake:
    def __init__(self):
        self._last_step_summary = None
_ACT_QUIET[0] = True
_calls = []
def _stub_step_env(arguments):
    _calls.append(arguments); return {"executed": True, "board_changed": True, "level_completed": False}
_R = type("R", (), {"step_executed": False, "retryable_failure": False})
_Rx = type("R", (), {"step_executed": True, "retryable_failure": False})
_fa = _ActFake(); _sp = "/kaggle/working/artifacts/m0r0-492f87ba_p0_tool_runtime_state.json"; _VA = ["UP", "DOWN", "MOUSE"]
_act_after_turn(_fa, _R(), _sp, _VA, _stub_step_env)
assert not _fa.__dict__["_act_state"]["directive"] and _calls == [], "thui-act TEETH: fired before the directive threshold"
_act_after_turn(_fa, _R(), _sp, _VA, _stub_step_env)
assert _fa.__dict__["_act_state"]["directive"] and _calls == [], "thui-act TEETH: directive must come before any forced action"
_d = _act_directive(_fa.__dict__["_act_state"])
assert _d.startswith("ACT NOW") and "UP, DOWN" in _d and "MOUSE" not in _d, f"thui-act TEETH: directive text: {_d[:80]}"
_act_after_turn(_fa, _R(), _sp, _VA, _stub_step_env)
assert _calls == [], "thui-act TEETH: forced one turn too early under the directive"
_act_after_turn(_fa, _R(), _sp, _VA, _stub_step_env)
assert _calls == [{"actions": ["UP"]}], f"thui-act TEETH: forced action wrong: {_calls}"
assert _fa.__dict__["_act_state"]["dead"] == 0 and not _fa.__dict__["_act_state"]["directive"] and _ACT_STATS["forced"] == 1
_fa._last_step_summary = {"level": 1, "executed_count": 1}
_act_after_turn(_fa, _Rx(), _sp, ["UP"], _stub_step_env)
assert _fa.__dict__["_act_state"]["dead"] == 0 and _fa.__dict__["_act_state"]["cleared"] == 0, "thui-act TEETH: an executed turn on level 1 must reset dead and clear nothing"
for _i in range(2):
    for _j in range(_ACT_DIRECTIVE_NO_LEVEL + _ACT_FORCED_AFTER):
        _act_after_turn(_fa, _R(), _sp, _VA, _stub_step_env)
assert [c["actions"][0] for c in _calls] == ["UP", "DOWN", "UP"], f"thui-act TEETH: round-robin: {_calls}"
for _j in range(_ACT_DIRECTIVE_NO_LEVEL + _ACT_FORCED_AFTER + 3):
    _act_after_turn(_fa, _R(), _sp, _VA, _stub_step_env)
assert len(_calls) == 3 and _fa.__dict__["_act_state"]["directive"] and _ACT_STATS["forced_capped"] == 1, "thui-act TEETH: per-level cap not enforced"
# a level completion (summary level 2 on an executed turn) moves the game to the scoring thresholds
_fa._last_step_summary = {"level": 2, "executed_count": 1, "level_transition": True}
_act_after_turn(_fa, _Rx(), _sp, ["UP"], _stub_step_env)
assert _fa.__dict__["_act_state"]["cleared"] == 1 and not _fa.__dict__["_act_state"]["directive"]
for _i in range(_ACT_DIRECTIVE_NO_LEVEL + _ACT_FORCED_AFTER):
    _act_after_turn(_fa, _R(), _sp, ["UP"], _stub_step_env)
assert len(_calls) == 3 and not _fa.__dict__["_act_state"]["directive"], "thui-act TEETH: a scoring game must use the 6-turn threshold, not 2"
for _i in range(_ACT_DIRECTIVE_SCORING - (_ACT_DIRECTIVE_NO_LEVEL + _ACT_FORCED_AFTER)):
    _act_after_turn(_fa, _R(), _sp, ["UP"], _stub_step_env)
assert _fa.__dict__["_act_state"]["directive"] and len(_calls) == 3, "thui-act TEETH: scoring-game directive threshold"
for _i in range(_ACT_FORCED_AFTER):
    _act_after_turn(_fa, _R(), _sp, ["UP"], _stub_step_env)
assert len(_calls) == 4 and _fa.__dict__["_act_state"]["forced_at_level"] == {0: 3, 1: 1}, "thui-act TEETH: level-1 forced action / per-level ledger"
# a new game on the same agent resets the state; a stale summary on a no-action turn changes nothing
_act_after_turn(_fa, _R(), "/kaggle/working/artifacts/tr87-cd924810_p0_tool_runtime_state.json", ["UP"], _stub_step_env)
assert _fa.__dict__["_act_state"]["game"] == "tr87" and _fa.__dict__["_act_state"]["dead"] == 1 and _fa.__dict__["_act_state"]["cleared"] == 0, "thui-act TEETH: state did not reset on a new game"
# the prompt wrap: directive on -> prefixed and the frame's level/valid actions are read; off -> base untouched
_fp = _ActFake(); _act_state(_fp, "m0r0")["directive"] = True; _fp.__dict__["_act_state"]["dead"] = 2
_orig_act_prompt_saved = _orig_act_prompt
_orig_act_prompt = lambda self, n, **kw: "BASE PROMPT"
try:
    _Fr = type("F", (), {"level": 3})()
    _out = _act_prompt(_fp, 1, valid_actions=["LEFT", "MOUSE"], current_frame=_Fr)
    assert _out.startswith("ACT NOW") and _out.endswith("BASE PROMPT") and "LEFT" in _out and "MOUSE" not in _out.split("\n\n")[0]
    assert _fp.__dict__["_act_state"]["cleared"] == 2, "thui-act TEETH: the prompt wrap must read cleared levels from the frame"
    _fp.__dict__["_act_state"]["directive"] = False
    assert _act_prompt(_fp, 1, valid_actions=["LEFT"], current_frame=_Fr) == "BASE PROMPT", "thui-act TEETH: prompt touched while the directive is off"
finally:
    _orig_act_prompt = _orig_act_prompt_saved
assert _act_game(_sp) == "m0r0" and _act_pick(["MOUSE"], 0) is None
assert _act_simple(["ACTION1", "ACTION2", "ACTION6", "ACTION7"]) == ["UP", "DOWN"], f"thui-act TEETH: engine names must map to model names: {_act_simple(['ACTION1', 'ACTION2', 'ACTION6', 'ACTION7'])}"
assert _act_pick(["ACTION3", "ACTION4"], 1) == "RIGHT", "thui-act TEETH: round-robin over mapped engine names"
_fe = _ActFake(); _n0 = _ACT_STATS["forced_capped"]
for _i in range(_ACT_DIRECTIVE_NO_LEVEL + _ACT_FORCED_AFTER):
    _act_after_turn(_fe, _R(), _sp, ["ACTION6"], _stub_step_env)   # MOUSE-only game: nothing simple to force
assert _ACT_STATS["forced_capped"] == _n0 + 1 and _fe.__dict__["_act_state"]["directive"], "thui-act TEETH: empty candidate list must be logged as withheld, not skipped"
del _fe, _n0
_ACT_QUIET[0] = False
for _k in _ACT_STATS: _ACT_STATS[_k] = 0
del _fa, _fp, _calls, _R, _Rx, _sp, _VA, _d, _Fr, _out
print(f"thui-act: ToolAgent.analyze + _build_user_prompt wrapped; ACT-NOW directive at {_ACT_DIRECTIVE_NO_LEVEL}/{_ACT_DIRECTIVE_SCORING} dead turns, "
      f"forced action {_ACT_FORCED_AFTER} dead turns later (cap {_ACT_FORCED_PER_LEVEL}/level, {_ACT_FORCED_CAP}/game); teeth ok", flush=True)
# ======================================================================================
'''

# ---- cells 4 + 14: the competition mount -- Kaggle serves TWO /kaggle/input layouts and which one a run gets varies
# between runs (sahasawatt/thui-act-v0 v1 and thui-gemma-v0 v1 both died at 6.5 s on the flat layout, 2026-09-07:
# "No matching distribution found for arc-agi" with the wheels one path segment away). Ported from solo/build_notebook.py.
COMP = "arc-prize-2026-arc-agi-3"
WHEELS_NESTED = "/kaggle/input/competitions/" + COMP + "/arc_agi_3_wheels"
CELL4_ANCHOR = '        "' + WHEELS_NESTED + '",'
CELL4_REPLACEMENT = "        _WHEELS,"
CELL4_RESOLVER = """# thui-act: resolve the competition mount instead of assuming its layout -- Kaggle serves either
# /kaggle/input/competitions/<comp> or /kaggle/input/<comp>, and which one varies between runs.
_COMP_CANDIDATES = ["/kaggle/input/competitions/__COMP__", "/kaggle/input/__COMP__"]
_COMP_DIR = next((_p for _p in _COMP_CANDIDATES if os.path.isdir(_p)), None)
assert _COMP_DIR is not None, (
    "thui-act: no competition mount found. Tried " + repr(_COMP_CANDIDATES)
    + "; /kaggle/input holds "
    + repr(sorted(os.listdir("/kaggle/input")) if os.path.isdir("/kaggle/input") else "MISSING")
)
_WHEELS = os.path.join(_COMP_DIR, "arc_agi_3_wheels")
assert os.path.isdir(_WHEELS), "thui-act: resolved wheels dir is not a directory: " + _WHEELS
print("thui-act: competition mount = " + _COMP_DIR, flush=True)
""".replace("__COMP__", COMP)
CELL14_MOUNT_ANCHOR = 'competition_env_files = str(Path("' + WHEELS_NESTED + '").parent / "environment_files")'
CELL14_MOUNT_REPLACEMENT = 'competition_env_files = str(Path(_COMP_DIR) / "environment_files")'

CELL14_ANCHOR = "    bm.games = _offline_games(competition_env_files)\n"
CELL14_FILTER = (
    "    # thui-act-v0 smoke: three games, at the REAL seam.\n"
    "    _SMOKE = " + repr(SMOKE_GAMES) + "\n"
    "    _n0 = len(bm.games)\n"
    "    bm.games = [g for g in bm.games if any(g.env_name.startswith(h) for h in _SMOKE)]\n"
    "    print(f\"thui-act-v0: smoke filter {_n0} -> {len(bm.games)} games\", flush=True)\n"
    "    assert len(bm.games) == " + str(len(SMOKE_GAMES)) + ", f\"thui-act-v0: expected " + str(len(SMOKE_GAMES)) + " games, got {len(bm.games)}\"\n"
    "    bm.solver.max_runtime_s_per_game = " + str(GAME_CLOCK_S) + ".0\n"
)


def main(full: bool = False, slug_suffix: str = "", owner: str = OWNER) -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 17, f"{SRC_NB.name}: expected 17 cells, found {len(cells)}"
    if BASE == "v3":
        _c8 = "".join(cells[8]["source"])
        assert _c8.count("'LOCAL_ANALYZER_YIELD_SECONDS': '180'") == 2, "base v3: yield-180 injection/assert not found twice in cell 8"
    print(f"base = {BASE} ({SRC_NB.relative_to(REPO)})", flush=True)
    before = ["".join(c["source"]) for c in cells]
    slug = ("thui-act-v2" if full else "thui-act-v0") + slug_suffix   # v1 = the stage-2-dead draw (LEDGER); v2 = mapping fixed
    out_nb = HERE / f"taaf-{slug}.ipynb"

    cells[0]["source"] = (CELL0_MD_FULL if full else CELL0_MD_SMOKE).splitlines(keepends=True)
    c4 = "".join(cells[4]["source"])
    assert c4.count(CELL4_ANCHOR) == 1, f"cell 4 does not name the nested wheels path exactly once ({c4.count(CELL4_ANCHOR)})"
    cells[4]["source"] = (CELL4_RESOLVER + c4.replace(CELL4_ANCHOR, CELL4_REPLACEMENT)).splitlines(keepends=True)
    c14m = "".join(cells[14]["source"])
    assert c14m.count(CELL14_MOUNT_ANCHOR) == 1, f"cell 14 does not name the nested env-files path exactly once ({c14m.count(CELL14_MOUNT_ANCHOR)})"
    cells[14]["source"] = c14m.replace(CELL14_MOUNT_ANCHOR, CELL14_MOUNT_REPLACEMENT).splitlines(keepends=True)
    c12 = "".join(cells[12]["source"])
    assert "thui-act" not in c12, "cell 12 already carries the breaker -- double build?"
    # thui-v3-0's cell 12 (the per-request usage probe) already wraps ToolAgent.analyze; our wrap goes on top of it.
    # That is safe only because the probe forwards every argument untouched -- assert that shape, not its absence.
    assert "return orig_analyze(self, state_path, action_num, *args, **kwargs)" in c12, "cell 12's analyze wrapper no longer passes arguments through"
    assert "ToolAgent._build_user_prompt =" not in c12 and "_build_user_prompt =" not in c12, "cell 12 already rebinds _build_user_prompt"
    cells[12]["source"] = (c12 + CELL12_SUFFIX).splitlines(keepends=True)
    if not full:
        c14 = "".join(cells[14]["source"])
        assert c14.count(CELL14_ANCHOR) == 1, "offline bm.games assignment not found once in cell 14"
        cells[14]["source"] = c14.replace(CELL14_ANCHOR, CELL14_ANCHOR + CELL14_FILTER).splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    expected = [0, 4, 12, 14]
    assert changed == expected, f"cells changed {changed}, expected {expected}"
    for i in (4, 12, 14):
        ast.parse("".join(cells[i]["source"]), filename=f"cell{i}")
    o4 = "".join(cells[4]["source"]); o14 = "".join(cells[14]["source"])
    assert "_COMP_DIR = next(" in o4 and WHEELS_NESTED not in o4 and o4.count(CELL4_REPLACEMENT) == 1 and o4.count("assert _COMP_DIR is not None") == 1, "cell 4 mount resolver incomplete"
    assert WHEELS_NESTED not in o14 and "Path(_COMP_DIR)" in o14, "cell 14 still assumes the nested layout for environment_files"
    assert after[0].startswith("# thui-act-v"), "G2: cell 0 must open with our identity"

    out_nb.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(META_SRC.read_text(encoding="utf-8"))
    meta["id"] = f"{owner}/{slug}"; meta["title"] = slug; meta["code_file"] = out_nb.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"built {out_nb.name}: cells changed {changed}, id {meta['id']}")
    print("push with: python scripts/kaggle_push_kernel.py repos/arc-agi-3-agent/thui-act  (from arc-agi-pub)")


if __name__ == "__main__":
    _suf = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--suffix=")), "")
    _own = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), OWNER)
    main(full=FULL, slug_suffix=_suf, owner=_own)
