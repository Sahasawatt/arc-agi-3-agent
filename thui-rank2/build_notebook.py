#!/usr/bin/env python3
"""thui-rank2 -- B61 v2: the frame-change prior as a VETO over the LLM's proposals, on the Flash-Next chassis.

WHY v2 (2026-09-16). thui-rank-v1 (B48 chassis, 2026-09-05) fired 22 vetoes on ~2,400 proposals (0.9%) and
read NOT-DISTINGUISHABLE; KILLER-1 read 0 immediate false vetoes. Reading v1's seams against the harness
source (localrig, and the two Flash-Next bundles downloaded 2026-09-16) found two defects that shrink reach
and are not the lever's fault:

  D1 ACTION6 keys never matched. observe() keyed a click by payload["action_data"]["y"/"x"], but the harness
     emits {"row", "col"} (`_model_mouse_action_data`), so every observed click trained the coordinate head
     at (0,0) and the "observed to change" exemption never matched a click. score() used the proposal's
     row/col. The coordinate head that vetoed 5 clicks in v1 was untrained everywhere else.
  D2 labels were per BATCH. observe() ran on step_env's final payload, whose board_changed is OR'ed over the
     whole batch and whose action is only the LAST one, against the grid from BEFORE the batch. Any batch
     that moved anything labelled its last action "changed" from the wrong state.

v2 = one lever, changed in three places, all toward reach:
  1. observation moves to `_HarnessGameSession._execute_action` (one call per executed action, prev and new
     grid both in hand) -- fixes D2; keys use row/col on both sides -- fixes D1 (teeth below go RED on the
     v1 key function).
  2. label is HUD-aware (B80 L1's band rule, learned online per game): an action whose changed rows all lie
     in the counter strip is INERT. frame_count > 1 (animation, anim bundle only) and level_completed count
     as change.
  3. veto_p 0.15 -> 0.30, min_obs 20 -> 10. A multi-action batch is vetoed whole when its FIRST action is
     predicted inert (later actions start from states the prior cannot see, so they are never scored).
Unchanged: the prior never issues an action; <= 2 vetoes per LLM step; RESET never vetoed; the refusal is
the harness's own `_error_payload`, so the model re-picks inside the same turn.
The false-veto proxy now remembers EVERY vetoed key per game (v1's single slot lost 3 of 22).

BASES (--base):
  anim  thui-anim-fast/thui-animfast-b71-full25-r1.ipynb -- the B71 build that ran and drew hidden 3.74/3.41/2.90.
  fast  thui-l1 builder --full --control, regenerated in a temp tree -- the June duck on Flash-Next with L1's
        wrappers NOT installed (the arm yocybercode/thui-l1-ctl-full25-r1 ran as).
Edits: cell 0 (header), cell 13 (graft appended after the settings), and for smoke cell 15 (game subset + clock,
the thui-l1 smoke recipe). Nothing else; asserted.

Build:  python3 thui-rank2/build_notebook.py --base=anim|fast [--full] [--suffix=-r1] [--owner=yocybercode]
Push:   python3 scripts/kaggle_push_kernel.py <this dir>   (from kc-arc-agi-pub; token must resolve to yocybercode)
"""
from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ARG = {a.split("=", 1)[0]: (a.split("=", 1)[1] if "=" in a else True) for a in sys.argv[1:]}
BASE = ARG.get("--base")
assert BASE in ("anim", "fast"), "--base=anim|fast is required"
FULL = bool(ARG.get("--full"))
OWNER = ARG.get("--owner", "yocybercode")
SUFFIX = ARG.get("--suffix", "")
SLUG = f"thui-rank2-{BASE}-" + ("full25" if FULL else "smoke") + SUFFIX
OUT_DIR = HERE / "out" / SLUG          # one push dir per kernel: two bases must not share a kernel-metadata.json
OUT_NB = OUT_DIR / f"{SLUG}.ipynb"

VETO_P, MIN_OBS, PER_STEP = 0.30, 10, 2
HUD_FRAC, HUD_MIN, HUD_MAX_ROWS = 0.9, 20, 4
SMOKE_GAMES = ("tn36-ef4dde99", "vc33-5430563c", "bp35-0a0ad940")   # thui-l1's HUD smoke set: inert actions exist here
SMOKE_CLOCK_S = 1800


def load_base():
    if BASE == "anim":
        nb = json.loads((REPO / "thui-anim-fast" / "thui-animfast-b71-full25-r1.ipynb").read_text(encoding="utf-8"))
        meta = json.loads((REPO / "thui-anim-fast" / "kernel-metadata.json").read_text(encoding="utf-8"))
        assert meta["id"] == "yocybercode/thui-animfast-b71-full25-r1"
        assert "jakobbrggen/taaf-kaggle-source-anim-20260807-anim" in meta["dataset_sources"]
        return nb, meta
    with tempfile.TemporaryDirectory() as t:
        for d in ("thui-l1", "thui-fast"):
            shutil.copytree(REPO / d, Path(t) / d)
        # thui-l1's builder refuses --full with --control (it never emitted a full control); lift that one assert
        # in the TEMP copy only. With it gone the control branch already does the right thing: cell 9 = control
        # asserts, cell 15 = mount resolver only, no smoke subset.
        l1 = Path(t) / "thui-l1" / "build_notebook.py"
        src = l1.read_text(encoding="utf-8")
        assert src.count("assert not (FULL and CONTROL)\n") == 1
        l1.write_text(src.replace("assert not (FULL and CONTROL)\n", ""), encoding="utf-8")
        subprocess.run([sys.executable, str(Path(t) / "thui-l1" / "build_notebook.py"), "--full", "--control",
                        "--owner=yocybercode"], check=True, env={"PYTHONUTF8": "1", "PATH": "/usr/bin:/bin"})
        nb = json.loads((Path(t) / "thui-l1" / "taaf-thui-l1-v1.ipynb").read_text(encoding="utf-8"))
        meta = json.loads((Path(t) / "thui-l1" / "kernel-metadata.json").read_text(encoding="utf-8"))
    assert "THUI_L1_GRAFT control" in "".join(nb["cells"][9]["source"]) and "_thui_exec" not in "".join(nb["cells"][9]["source"])
    assert "smoke" not in "".join(nb["cells"][15]["source"]) and "_COMP_DIR" in "".join(nb["cells"][15]["source"])
    return nb, meta


CELL0 = f"""# {SLUG} (Thuitanium / Knowless Crew) — B61 v2: frame-change prior as a VETO over the LLM's proposals

**This is a Knowless Crew / Thuitanium fork, and neither the solver nor the serving is ours.** Base:
{"`yocybercode/thui-animfast-b71-full25-r1` (Jakob Bruggen's anim solver bundle on Keith Tyser's Flash-Next NVFP4 + MTP-3 serving)" if BASE == "anim" else "`thui-l1-ctl` (the Tufa Labs June duck harness on Keith Tyser's Flash-Next NVFP4 + MTP-3 serving, no wrappers)"},
unchanged except the cells below. Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman,
Andries Smit, Michal Tesnar, Stefano Viel). Serving credit: Keith Tyser. Weights: RadixArk NVFP4 of
Qwen/Qwen3.8-Flash-Next (Qwen licence). HUD band rule: Son Pham's no-impact lever, our implementation.
⚠️ Every score quoted by any upstream is theirs.

## What we changed

- **cell 13** — a small CNN per game, trained online on this game's own executed actions, scores every
  action the model proposes; a proposal predicted inert (p < {VETO_P}, after ≥ {MIN_OBS} observations, ≤ {PER_STEP}
  vetoes per step) is refused with the harness's own error payload and the model re-picks. **The prior
  never issues an action.** An action that only changed the counter strip is labelled inert.
{"- **cell 15** — smoke: " + ", ".join(SMOKE_GAMES) + f" at {SMOKE_CLOCK_S} s each. Numbers are not a score." if not FULL else ""}

Build script: `thui-rank2/build_notebook.py` in our agent repo. Ticket B61.
"""

# Pure half: no torch, no harness. Executed locally by this builder (teeth) and in-kernel.
PURE = f'''
# ==== thui-rank2 (B61 v2) pure half: keys, HUD band, labels. Teeth run locally AND in-kernel. ====
_R2_TYPES = ("ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5")
_R2_HUD_FRAC, _R2_HUD_MIN, _R2_HUD_MAX = {HUD_FRAC}, {HUD_MIN}, {HUD_MAX_ROWS}

def _r2_key(name, row=None, col=None):
    return f"ACTION6:{{int(row)}},{{int(col)}}" if name == "ACTION6" else name

def _r2_key_payload(payload):
    """key of one EXECUTED action from its harness payload (action_data is row/col for ACTION6)."""
    name = str(payload.get("action_name") or "").upper()
    d = payload.get("action_data") or {{}}
    return _r2_key(name, d.get("row", 0), d.get("col", 0)) if name == "ACTION6" else _r2_key(name)

def _r2_key_proposal(engine_name, raw):
    """key of one PROPOSED action from the model's normalized action dict (row/col for MOUSE)."""
    return _r2_key(engine_name, raw.get("row", 0), raw.get("col", 0)) if engine_name == "ACTION6" else _r2_key(engine_name)

def _r2_hud_new():
    return {{"n": 0, "rows": {{}}, "band": None}}

def _r2_changed(st, prev, new, level_completed, frame_count, learn):
    """True = the action changed something that counts. Learns the HUD band from board-changing actions."""
    if level_completed or int(frame_count or 0) > 1:
        return True
    rows = {{r for r in range(min(len(prev), len(new))) if prev[r] != new[r]}} if prev and new else set()
    if not rows:
        return False
    if learn:
        st["n"] += 1
        for r in rows:
            st["rows"][r] = st["rows"].get(r, 0) + 1
        if st["n"] >= _R2_HUD_MIN:
            band = {{r for r, k in st["rows"].items() if k / st["n"] >= _R2_HUD_FRAC}}
            st["band"] = band if 0 < len(band) <= _R2_HUD_MAX else None
    band = st["band"]
    return not (band and rows <= band)

# teeth 1 (D1): an executed click and the same proposed click must share one key
assert _r2_key_payload({{"action_name": "ACTION6", "action_data": {{"row": 3, "col": 5}}}}) == _r2_key_proposal("ACTION6", {{"action": "MOUSE", "row": 3, "col": 5}}) == "ACTION6:3,5"
assert _r2_key_payload({{"action_name": "ACTION6", "action_data": {{"row": 3, "col": 5}}}}) != _r2_key_proposal("ACTION6", {{"action": "MOUSE", "row": 5, "col": 3}})
assert _r2_key_payload({{"action_name": "ACTION2", "action_data": {{}}}}) == _r2_key_proposal("ACTION2", {{"action": "DOWN"}})
# teeth 2: HUD band -- row 0 ticks every action plus a wandering row -> a row-0-only action is inert
_s = _r2_hud_new(); _g = lambda rows: [[1 if r in rows else 0] for r in range(12)]
for _i in range(24):
    assert _r2_changed(_s, _g(set()), _g({{0, 4 + (_i % 7)}}), False, 1, True) is True
assert _s["band"] == {{0}}, _s
assert _r2_changed(_s, _g(set()), _g({{0}}), False, 1, True) is False
assert _r2_changed(_s, _g(set()), _g({{0, 2}}), False, 1, True) is True
assert _r2_changed(_s, _g(set()), _g(set()), False, 1, True) is False
assert _r2_changed(_s, _g(set()), _g(set()), True, 1, True) is True and _r2_changed(_s, _g(set()), _g(set()), False, 3, True) is True
# teeth 3: a playfield redrawing 6 rows every action never forms a band
_s = _r2_hud_new()
for _i in range(30):
    assert _r2_changed(_s, _g(set()), _g(set(range(6))), False, 1, True) is True
assert _s["band"] is None, _s
print("thui-rank2: pure teeth ok", flush=True)
'''

WRAP = f'''
# ==== thui-rank2 (B61 v2) harness half ====
import hashlib as _r2_hash, inspect as _r2_inspect, math as _r2_math, random as _r2_random, time as _r2_time
import torch as _r2_torch, torch.nn as _r2_nn, torch.nn.functional as _r2_F
from inference.agent import tool_agent as _r2_ta
from inference.framework import solver as _r2_sol
from inference.agent.action_names import to_engine_action as _r2_to_engine
_r2_torch.set_num_threads(2)
_r2_log_dev = lambda: print(f"thui-rank2: torch default device probe = {{_r2_torch.zeros(1).device}}", flush=True)
_r2_log_dev()   # {BASE} runs 28 games concurrently; the prior must not oversubscribe the CPU
_R2_VETO_P, _R2_MIN_OBS, _R2_PER_STEP = {VETO_P}, {MIN_OBS}, {PER_STEP}
_R2 = {{"proposals": 0, "scored": 0, "vetoes": 0, "batch_vetoes": 0, "false_veto_proxy": 0, "observed": 0,
        "inert_labels": 0, "updates": 0, "games": 0, "wrapper_errors": 0, "train_s": 0.0, "score_s": 0.0}}

def _r2_onehot(grid):
    t = _r2_torch.zeros(16, 64, 64, device="cpu")
    for r, row in enumerate(grid[:64]):
        for c, v in enumerate(row[:64]):
            t[max(0, min(15, int(v))), r, c] = 1.0
    return t

def _r2_sig(grid):
    return _r2_hash.blake2b(repr(grid).encode(), digest_size=8).hexdigest()

class _R2Net(_r2_nn.Module):
    def __init__(self):
        super().__init__()
        # smoke r1 (2026-09-16): the 16/32/64/128/256 net cost 1.6 s per observed action inline on the game thread.
        self.c1 = _r2_nn.Conv2d(16, 16, 3, padding=1); self.c2 = _r2_nn.Conv2d(16, 32, 3, padding=1)
        self.c3 = _r2_nn.Conv2d(32, 32, 3, padding=1); self.c4 = _r2_nn.Conv2d(32, 64, 3, padding=1)
        self.act_head = _r2_nn.Linear(64, len(_R2_TYPES)); self.coord_head = _r2_nn.Conv2d(64, 1, 1)
    def forward(self, x):
        h = _r2_F.relu(self.c1(x)); h = _r2_F.relu(self.c2(h)); h = _r2_F.relu(self.c3(h)); h = _r2_F.relu(self.c4(h))
        return self.act_head(h.mean(dim=(2, 3))), self.coord_head(h).squeeze(1)

class _R2Ranker:
    def __init__(self):
        self.net = _R2Net().to("cpu"); self.opt = _r2_torch.optim.Adam(self.net.parameters(), lr=1e-3)
        self.buf, self.seen, self.changed, self.vetoed = [], set(), set(), set()
        self.hud = _r2_hud_new(); self.observed = 0

    def observe(self, prev, new, payload):
        name = str(payload.get("action_name") or "").upper()
        if name != "ACTION6" and name not in _R2_TYPES:
            return
        key = (_r2_sig(prev), _r2_key_payload(payload))
        label = _r2_changed(self.hud, prev, new, bool(payload.get("level_completed")), payload.get("frame_count"), learn=True)
        if label:
            self.changed.add(key)
        else:
            _R2["inert_labels"] += 1
        if key in self.vetoed:
            self.vetoed.discard(key)
            if label:
                _R2["false_veto_proxy"] += 1
                print(f"thui-rank2: FALSE-VETO proxy -- {{key[1]}} vetoed earlier, executed later, changed", flush=True)
        self.observed += 1; _R2["observed"] += 1
        if _R2["observed"] % 200 == 0:
            print(f"thui-rank2: STATS {{_R2}}", flush=True)
        if key in self.seen:
            return
        self.seen.add(key)
        if name == "ACTION6":
            d = payload.get("action_data") or {{}}
            tidx, rc = None, (max(0, min(63, int(d.get("row", 0)))), max(0, min(63, int(d.get("col", 0)))))
        else:
            tidx, rc = _R2_TYPES.index(name), None
        self.buf.append((_r2_onehot(prev), tidx, rc, 1.0 if label else 0.0))
        self.buf = self.buf[-20000:]
        t0 = _r2_time.monotonic(); self._train(1); _R2["train_s"] += _r2_time.monotonic() - t0

    def _train(self, steps):
        if len(self.buf) < 4:
            return
        self.net.train()
        for _ in range(steps):
            batch = _r2_random.sample(self.buf, min(16, len(self.buf)))
            act, coord = self.net(_r2_torch.stack([b[0] for b in batch]))
            loss = sum(_r2_F.binary_cross_entropy_with_logits(act[i, t] if t is not None else coord[i, rc[0], rc[1]], _r2_torch.tensor(y, device="cpu"))
                       for i, (_, t, rc, y) in enumerate(batch)) / len(batch)
            self.opt.zero_grad(); loss.backward(); self.opt.step()
            _R2["updates"] += 1
            if _R2["updates"] % 50 == 0:
                print(f"thui-rank2: update n={{_R2['updates']}} buf={{len(self.buf)}} loss={{loss.item():.4f}} train_s={{_R2['train_s']:.1f}}", flush=True)
        assert _r2_math.isfinite(loss.item()), "thui-rank2: non-finite loss"

    def score(self, grid, engine_name, raw):
        if self.observed < _R2_MIN_OBS or (engine_name != "ACTION6" and engine_name not in _R2_TYPES):
            return None
        key = (_r2_sig(grid), _r2_key_proposal(engine_name, raw))
        if key[1] and key in self.changed:
            return None
        t0 = _r2_time.monotonic()
        self.net.eval()
        with _r2_torch.no_grad():
            act, coord = self.net(_r2_onehot(grid).unsqueeze(0).to("cpu"))
        if engine_name == "ACTION6":
            p = _r2_torch.sigmoid(coord[0, max(0, min(63, int(raw.get("row", 0)))), max(0, min(63, int(raw.get("col", 0))))]).item()
        else:
            p = _r2_torch.sigmoid(act[0, _R2_TYPES.index(engine_name)]).item()
        _R2["score_s"] += _r2_time.monotonic() - t0
        return float(p), key

def _r2_ranker(session):
    rk = session.__dict__.get("_thui_rank2")
    if rk is None:
        rk = session.__dict__["_thui_rank2"] = _R2Ranker(); _R2["games"] += 1
        print(f"thui-rank2: new ranker for game #{{_R2['games']}}", flush=True)
    return rk

_r2_orig_exec = _r2_sol._HarnessGameSession._execute_action
def _r2_exec(self, action, **kw):
    prev = _r2_sol._grid_from_state(self.game.current_state)
    payload = _r2_orig_exec(self, action, **kw)
    try:
        if isinstance(payload, dict) and payload.get("executed") and action.id.name != "RESET":
            _r2_ranker(self).observe(prev, _r2_sol._grid_from_state(self.game.current_state), payload)
    except Exception as exc:
        _R2["wrapper_errors"] += 1
        print(f"thui-rank2: observe error (pass-through): {{type(exc).__name__}}: {{exc}}", flush=True)
    return payload

_r2_orig_analyze = _r2_ta.ToolAgent.analyze
_R2_SIG = _r2_inspect.signature(_r2_orig_analyze)
def _r2_analyze(self, *args, **kwargs):
    ba = _R2_SIG.bind(self, *args, **kwargs)
    step_env = ba.arguments.get("step_env")
    session = getattr(step_env, "__self__", None)
    if session is None or not hasattr(session, "game"):
        _R2["wrapper_errors"] += 1
        print("thui-rank2: analyze without a bound step_env -- veto OFF for this call", flush=True)
        return _r2_orig_analyze(*ba.args, **ba.kwargs)
    ranker = _r2_ranker(session)
    step_vetoes = [0]

    def rec_step_env(arguments):
        try:
            raws = arguments.get("actions") if isinstance(arguments, dict) else None
            if isinstance(raws, list) and raws and isinstance(raws[0], dict) and step_vetoes[0] < _R2_PER_STEP:
                _R2["proposals"] += 1
                eng = _r2_to_engine(raws[0].get("action"))
                if eng and eng != "RESET":
                    grid = _r2_sol._grid_from_state(session.game.current_state)
                    s = ranker.score(grid, eng, raws[0])
                    if s is not None:
                        _R2["scored"] += 1
                        p, key = s
                        if p < _R2_VETO_P:
                            step_vetoes[0] += 1; _R2["vetoes"] += 1; ranker.vetoed.add(key)
                            if len(raws) > 1:
                                _R2["batch_vetoes"] += 1
                            print(f"thui-rank2: VETO #{{_R2['vetoes']}} {{key[1]}} p={{p:.3f}} obs={{ranker.observed}} batch={{len(raws)}} step_vetoes={{step_vetoes[0]}}", flush=True)
                            what = raws[0].get("action") + (f"(row={{raws[0].get('row')}}, col={{raws[0].get('col')}})" if eng == "ACTION6" else "")
                            return session._error_payload(
                                f"prior: {{what}} is predicted to have no effect here (p={{p:.2f}}); nothing was executed -- choose a different action")
        except Exception as exc:
            _R2["wrapper_errors"] += 1
            print(f"thui-rank2: veto error (pass-through): {{type(exc).__name__}}: {{exc}}", flush=True)
        return step_env(arguments)

    ba.arguments["step_env"] = rec_step_env
    return _r2_orig_analyze(*ba.args, **ba.kwargs)

_r2_sol._HarnessGameSession._execute_action = _r2_exec
_r2_ta.ToolAgent.analyze = _r2_analyze
assert _r2_sol._HarnessGameSession._execute_action is _r2_exec and _r2_ta.ToolAgent.analyze is _r2_analyze
assert list(_R2_SIG.parameters)[:5] == ["self", "state_path", "action_num", "valid_actions", "step_env"], list(_R2_SIG.parameters)
assert callable(getattr(_r2_sol._HarnessGameSession, "_error_payload", None))
print(f"THUI_RANK2_GRAFT ok base={BASE} veto_p={{_R2_VETO_P}} min_obs={{_R2_MIN_OBS}} per_step={{_R2_PER_STEP}} solver={{_r2_sol.__file__}}", flush=True)
'''

C15_EXTRA_OLD = "    if missing or extra:\n"
C15_EXTRA_NEW = "    if missing or (extra and len(PUBLIC_GAME_IDS) == 25):   # thui-rank2 smoke: a subset leaves extras by design\n"
C15_SELECT = "    bm.games = [offline_by_id[game_id] for game_id in PUBLIC_GAME_IDS]\n"


def main() -> None:
    ns: dict = {}
    exec(PURE, ns)   # the kernel's own teeth, run here first
    nb, meta = load_base()
    cells = nb["cells"]
    assert len(cells) == 18, len(cells)
    before = ["".join(c["source"]) for c in cells]
    assert before[13].startswith("# Exact public-25 and competition settings.") and "concurrency = 28" in before[13]
    assert "thui-rank" not in before[13]

    cells[0]["cell_type"] = "markdown"; cells[0]["source"] = CELL0.splitlines(keepends=True)
    cells[13]["source"] = (before[13].rstrip("\n") + "\n" + PURE + WRAP).splitlines(keepends=True)
    if not FULL:
        s = before[15]
        m = re.search(r"PUBLIC_GAME_IDS = tuple\(\[\n(?:    \"[a-z0-9]{4}-[0-9a-f]{8}\",?\n){25}\]\)\n", s)
        assert m, "cell 15: the 25-game PUBLIC_GAME_IDS tuple not found"
        assert all(f'"{g}"' in m.group(0) for g in SMOKE_GAMES)
        s = s.replace(m.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-rank2 smoke subset\n")
        assert s.count("!= 25") == 2 and s.count(C15_EXTRA_OLD) == 1 and s.count(C15_SELECT) == 1
        s = s.replace("!= 25", "!= len(PUBLIC_GAME_IDS)").replace(C15_EXTRA_OLD, C15_EXTRA_NEW).replace(
            C15_SELECT, C15_SELECT + f"    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-rank2 smoke clock\n"
            f'    print(f"thui-rank2: smoke {{len(bm.games)}} games @ {{bm.solver.max_runtime_s_per_game}} s", flush=True)\n')
        cells[15]["source"] = s.splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert changed == ([0, 13] if FULL else [0, 13, 15]), changed
    for i, c in enumerate(cells):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]), filename=f"cell{i}")
    a0 = after[0]
    assert a0.startswith(f"# {SLUG} (Thuitanium / Knowless Crew)") and a0.index("Thuitanium") < min(a0.index("Tufa Labs"), a0.index("Keith Tyser"))
    assert after[13].count("THUI_RANK2_GRAFT ok") == 1 and after[13].count("pure teeth ok") == 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta.pop("id_no", None)
    meta.update(id=f"{OWNER}/{SLUG}", title=SLUG, code_file=OUT_NB.name, is_private=True)
    assert meta["machine_shape"] == "NvidiaRtxPro6000" and meta["enable_gpu"] is True
    (OUT_DIR / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"built {OUT_NB.name}: base={BASE} cells changed {changed}, id {meta['id']}, private, datasets={meta['dataset_sources']}")


if __name__ == "__main__":
    main()
