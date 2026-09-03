#!/usr/bin/env python3
"""thui-prior-v0 -- B60 smoke: a per-game learned exploration prior as the no-action fallback.

Design: notes/B60-exploration-prior-design.md. This file is the build; the ticket is the
argument. thui-v1-1 byte-for-byte except three cells:

  cell 0   markdown
  cell 12  appended AFTER the inherited usage probe: wraps `ToolAgent.analyze` so that
           (a) every `step_env` call is observed as (grid_before, action, board_changed) and
               trains a small CNN on the CPU, and
           (b) a turn that returns step_executed=False (not retryable, not yielded) gets ONE
               action proposed by the prior and executed through the same `step_env`.
  cell 14  the REAL game-selection seam: filter to g50t / sk48 / tr87 after
           `bm.games = _offline_games(...)`, clock 900 s/game.

P1 fallback fires (>=1 `thui-prior: fallback fired` with executed=True) · P2 the prior
trains (`thui-prior: update` lines, finite loss) · P3 run COMPLETE with 3 games in
summary.txt. Numbers are smoke, never score.

    python3 build_notebook.py    # writes taaf-thui-prior-v0.ipynb + kernel-metadata.json
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SRC_NB = REPO / "thuiv1" / "v1-1" / "taaf-thui-v1-1.ipynb"
OUT_NB = HERE / "taaf-thui-prior-v0.ipynb"
OWNER = "sahasawatt"
SLUG = "thui-prior-v0"

SMOKE_GAMES = ("g50t", "sk48", "tr87")   # the census's three deadest games
GAME_CLOCK_S = 900

CELL0_MD = """# thui-prior-v0 — B60 smoke: learned exploration prior as the no-action fallback

**Infrastructure smoke, not a scoring run.** `thui-v1-1` byte-for-byte except cells 12 and
14. Cell 12 wraps the analyzer so a turn that produces no action gets ONE action from a small
CNN trained online (StochasticGoose-class: which actions change the board), executed through
the harness's own `step_env`. Cell 14 filters to three games (g50t, sk48, tr87) at 900 s each.
Numbers are meaningless and must never be quoted. Design: `notes/B60-exploration-prior-design.md`.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

CELL12_SUFFIX = r'''

# === thui-prior-v0 (B60): learned exploration prior as the no-action fallback =========
# Seam: ToolAgent.analyze(state_path, action_count, *, valid_actions, step_env, ...) is
# called once per turn by _HarnessGameSession.play(); step_env is the SESSION's bound
# method, so step_env.__self__.game is the live game and every LLM action also flows
# through it. Wrapping analyze at class level keeps the upstream flow intact.
import math as _math
import time as _time
import hashlib as _hashlib
import random as _random
import torch as _torch
import torch.nn as _nn
import torch.nn.functional as _F
from inference.agent import tool_agent as _ta
from inference.framework import solver as _solver

_PRIOR_DEV = "cpu"          # never touch vLLM's VRAM reservation in the smoke
_PRIOR_TYPES = ("ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5")
_PRIOR_YIELD_K = @K@        # fire on the K-th consecutive yield without an action
_PRIOR_QUIET_S = @QUIET@    # v1.1: and only after this many seconds without PROGRESS (0 = no gate)
_PRIOR_STATS = {"fires": 0, "fired_executed": 0, "updates": 0, "observed": 0, "games": 0}


def _prior_onehot(grid):
    t = _torch.zeros(16, 64, 64)
    for r, row in enumerate(grid[:64]):
        for c, v in enumerate(row[:64]):
            t[max(0, min(15, int(v))), r, c] = 1.0
    return t


def _prior_sig(grid):
    return _hashlib.blake2b(repr(grid).encode(), digest_size=8).hexdigest()


class _PriorNet(_nn.Module):
    def __init__(self):
        super().__init__()
        self.c1 = _nn.Conv2d(16, 32, 3, padding=1)
        self.c2 = _nn.Conv2d(32, 64, 3, padding=1)
        self.c3 = _nn.Conv2d(64, 128, 3, padding=1)
        self.c4 = _nn.Conv2d(128, 256, 3, padding=1)
        self.act_head = _nn.Linear(256, len(_PRIOR_TYPES))
        self.coord_head = _nn.Conv2d(256, 1, 1)   # spatial map for ACTION6, never flattened

    def forward(self, x):
        h = _F.relu(self.c1(x)); h = _F.relu(self.c2(h))
        h = _F.relu(self.c3(h)); h = _F.relu(self.c4(h))
        return self.act_head(h.mean(dim=(2, 3))), self.coord_head(h).squeeze(1)


class _Prior:
    """Per-game: observe (grid, action) -> changed, train, propose one action."""

    def __init__(self):
        self.net = _PriorNet().to(_PRIOR_DEV)
        self.opt = _torch.optim.Adam(self.net.parameters(), lr=1e-3)
        self.buf = []                 # (onehot, type_idx or None, (r, c) or None, label)
        self.seen = set()             # (board_sig, action_sig) already observed
        self.no_change = set()        # (board_sig, action_sig) observed with no change
        self.yields_since_action = 0  # consecutive turn_time_budget yields with no action
        self.last_progress = _time.monotonic()  # last level-up or board-changing LLM action
        self.from_prior = False       # set while the prior's own action is executing

    def observe(self, grid, arguments, payload):
        if not isinstance(payload, dict) or not payload.get("executed"):
            return
        self.yields_since_action = 0
        _changed = bool(payload.get("board_changed")) or int(payload.get("frame_count") or 0) > 1
        if bool(payload.get("level_completed")) or (_changed and not self.from_prior):
            self.last_progress = _time.monotonic()
        name = str(payload.get("action_name") or "").upper()
        sig = _prior_sig(grid)
        data = payload.get("action_data") or {}
        if name == "ACTION6":
            rc = (int(data.get("y", 0)), int(data.get("x", 0)))
            asig = f"ACTION6:{rc[0]},{rc[1]}"
            tidx = None
        elif name in _PRIOR_TYPES:
            rc = None; asig = name; tidx = _PRIOR_TYPES.index(name)
        else:
            return
        key = (sig, asig)
        label = bool(payload.get("board_changed")) or int(payload.get("frame_count") or 0) > 1
        if not label:
            self.no_change.add(key)
        if key in self.seen:
            return
        self.seen.add(key)
        self.buf.append((_prior_onehot(grid), tidx, rc, 1.0 if label else 0.0))
        if len(self.buf) > 20000:
            self.buf = self.buf[-20000:]
        _PRIOR_STATS["observed"] += 1
        self._train(steps=2)

    def _train(self, steps):
        if len(self.buf) < 4:
            return
        self.net.train()
        for _ in range(steps):
            batch = _random.sample(self.buf, min(32, len(self.buf)))
            x = _torch.stack([b[0] for b in batch]).to(_PRIOR_DEV)
            act_logits, coord_map = self.net(x)
            loss = _torch.zeros((), device=_PRIOR_DEV); n = 0
            for i, (_, tidx, rc, y) in enumerate(batch):
                tgt = _torch.tensor(y, device=_PRIOR_DEV)
                if tidx is not None:
                    loss = loss + _F.binary_cross_entropy_with_logits(act_logits[i, tidx], tgt)
                else:
                    loss = loss + _F.binary_cross_entropy_with_logits(coord_map[i, rc[0], rc[1]], tgt)
                n += 1
            loss = loss / max(1, n)
            self.opt.zero_grad(); loss.backward(); self.opt.step()
            _PRIOR_STATS["updates"] += 1
            if _PRIOR_STATS["updates"] % 25 == 0:
                print(f"thui-prior: update n={_PRIOR_STATS['updates']} buf={len(self.buf)} loss={loss.item():.4f}", flush=True)
        assert _math.isfinite(loss.item()), "thui-prior: non-finite loss"

    def propose(self, grid, valid_engine):
        sig = _prior_sig(grid)
        valid = [v for v in valid_engine if v in _PRIOR_TYPES or v == "ACTION6"]
        if not valid:
            return None
        self.net.eval()
        with _torch.no_grad():
            act_logits, coord_map = self.net(_prior_onehot(grid).unsqueeze(0).to(_PRIOR_DEV))
        p_act = _torch.sigmoid(act_logits[0]); p_map = _torch.sigmoid(coord_map[0])
        cands = []
        for v in valid:
            if v == "ACTION6":
                cands.append(("ACTION6", float(p_map.max().item()) + 0.05))
            else:
                if (sig, v) in self.no_change:
                    continue
                cands.append((v, float(p_act[_PRIOR_TYPES.index(v)].item()) + 0.05))
        if not cands:
            cands = [(v, 1.0) for v in valid]
        total = sum(w for _, w in cands); r = _random.random() * total
        for v, w in cands:
            r -= w
            if r <= 0:
                break
        if v != "ACTION6":
            return {"action": _ta.to_model_action(v) if hasattr(_ta, "to_model_action") else v}
        flat = p_map.flatten() + 0.02
        for _ in range(8):
            idx = int(_torch.multinomial(flat / flat.sum(), 1).item())
            rr, cc = divmod(idx, 64)
            if (sig, f"ACTION6:{rr},{cc}") not in self.no_change:
                break
        return {"action": "MOUSE", "row": rr, "col": cc}


_priors = {}                      # id(session) -> _Prior
_orig_analyze = _ta.ToolAgent.analyze


def _prior_analyze(self, state_path, action_count, *args, valid_actions=None, step_env=None, **kwargs):
    session = getattr(step_env, "__self__", None)
    if session is None or not hasattr(session, "game"):
        return _orig_analyze(self, state_path, action_count, *args, valid_actions=valid_actions, step_env=step_env, **kwargs)
    prior = _priors.get(id(session))
    if prior is None:
        prior = _priors[id(session)] = _Prior()
        _PRIOR_STATS["games"] += 1
        print(f"thui-prior: new prior for game #{_PRIOR_STATS['games']}", flush=True)

    def rec_step_env(arguments):
        grid_before = _solver._grid_from_state(session.game.current_state)
        payload = step_env(arguments)
        try:
            prior.observe(grid_before, arguments, payload)
        except Exception as exc:  # the prior must never break the harness path
            print(f"thui-prior: observe skipped: {type(exc).__name__}: {exc}", flush=True)
        return payload

    result = _orig_analyze(self, state_path, action_count, *args, valid_actions=valid_actions, step_env=rec_step_env, **kwargs)
    if result is None or result.retryable_failure or session.should_stop():
        return result
    # v0 (2026-09-02) fired 0 times in 58 actions: a turn that has not acted does not come
    # back as step_executed=False -- it comes back as yielded_control (turn_time_budget,
    # yield 60 s) and the SAME step re-enters on the next loop iteration, again and again,
    # until the clock dies (g50t: 1 action in 900 s). So the no-action signal IS the yield.
    # Fire on the K-th consecutive yield since the last executed action (K=2 -> >=120 s of
    # silence), execute ONE prior action, and hand the yield back unchanged so the harness
    # re-enters the step on the new frame exactly as it would have.
    yielded = bool(getattr(result, "yielded_control", False))
    if yielded:
        prior.yields_since_action += 1
    quiet = _time.monotonic() - prior.last_progress
    fire = (
        ((not result.step_executed and not yielded) or (yielded and prior.yields_since_action >= _PRIOR_YIELD_K))
        and quiet >= _PRIOR_QUIET_S
    )
    if fire:
        grid_now = _solver._grid_from_state(session.game.current_state)
        act = prior.propose(grid_now, _solver._engine_action_names(session.game))
        if act is not None:
            _PRIOR_STATS["fires"] += 1
            prior.from_prior = True
            try:
                payload = rec_step_env(act)
            finally:
                prior.from_prior = False
            ok = isinstance(payload, dict) and bool(payload.get("executed"))
            if ok:
                _PRIOR_STATS["fired_executed"] += 1
                prior.yields_since_action = 0
            _gid = session.game.game_run.game_id if getattr(session.game, "game_run", None) else "?"
            print(f"thui-prior: fallback fired #{_PRIOR_STATS['fires']} game={_gid} via={'yield' if yielded else 'no-step'} quiet={quiet:.0f}s "
                  f"act={act} executed={ok} "
                  f"changed={payload.get('board_changed') if isinstance(payload, dict) else None} "
                  f"level_completed={payload.get('level_completed') if isinstance(payload, dict) else None}", flush=True)
            if ok and not yielded:
                return _ta.AnalyzerTurnResult(step_executed=True, reasoning="thui-prior fallback")
    return result


_ta.ToolAgent.analyze = _prior_analyze
assert _ta.ToolAgent.analyze is _prior_analyze, "thui-prior: analyze wrap did not land"
print("thui-prior-v0: ToolAgent.analyze wrapped (fallback on no-action turns, CPU prior)", flush=True)
# ======================================================================================
'''

CELL14_ANCHOR = "    bm.games = _offline_games(competition_env_files)\n"
CELL14_FILTER = (
    "    # thui-prior-v0 smoke: the three deadest games, at the REAL seam.\n"
    "    _SMOKE = " + repr(SMOKE_GAMES) + "\n"
    "    _n0 = len(bm.games)\n"
    "    bm.games = [g for g in bm.games if any(g.env_name.startswith(h) for h in _SMOKE)]\n"
    "    print(f\"thui-prior-v0: smoke filter {_n0} -> {len(bm.games)} games\", flush=True)\n"
    "    assert len(bm.games) == " + str(len(SMOKE_GAMES)) + ", f\"thui-prior-v0: expected " + str(len(SMOKE_GAMES)) + " games, got {len(bm.games)}\"\n"
    "    bm.solver.max_runtime_s_per_game = " + str(GAME_CLOCK_S) + ".0\n"
)


CELL0_MD_V11 = """# thui-prior-v1-1 — B60 v1.1: the same prior, progress-gated (K=3, quiet ≥300 s)

`thui-prior-v1` with one change in cell 12: the fallback fires only when the turn has yielded
three times without acting AND nothing has progressed for 300 s (no level-up, no board-changing
action by the LLM). v1 fired inside games the LLM was mid-plan on (ft09 lost a level on both
draws) while waking dead games (cn04/m0r0/wa30 0→1 on both draws); the gate keeps the second and
removes the first by construction. Oracle unchanged: paired levels vs the same-seed base pair.
Design + record: `notes/B60-exploration-prior-design.md`.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

CELL0_MD_FULL = """# thui-prior-v1 — B60: learned exploration prior as the no-action fallback, full 25 games

`thui-v1-1` byte-for-byte except cell 12: the analyzer is wrapped so that a turn which has
yielded twice without acting (≥120 s silent) gets ONE action from a small CNN trained online
on the run's own actions (which actions change the board), executed through the harness's own
`step_env`; the LLM's own actions are never overridden. Seed, temperature, clock and games are
inherited unchanged. Oracle: paired **levels** against the same-seed base runs (`thui-v1-1`,
`thui-v1-1-r2`), ≥2 runs per arm. Design + smoke record: `notes/B60-exploration-prior-design.md`.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""


def main(full: bool = False, slug_suffix: str = "", v11: bool = False) -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 17, f"thui-v1-1 source expected 17 cells, found {len(cells)}"
    before = ["".join(c["source"]) for c in cells]

    slug = (("thui-prior-v1-1" if v11 else "thui-prior-v1") + slug_suffix) if full else SLUG
    k, quiet = (3, 300) if v11 else (2, 0)
    cell12 = CELL12_SUFFIX.replace("@K@", str(k)).replace("@QUIET@", str(quiet))
    out_nb = HERE / f"taaf-{slug}.ipynb"

    cells[0]["source"] = (CELL0_MD_V11 if v11 else CELL0_MD_FULL if full else CELL0_MD).splitlines(keepends=True)

    c12 = "".join(cells[12]["source"])
    assert "thui-prior" not in c12, "cell 12 already carries the prior -- double build?"
    cells[12]["source"] = (c12 + cell12).splitlines(keepends=True)

    if not full:
        c14 = "".join(cells[14]["source"])
        assert c14.count(CELL14_ANCHOR) == 1, "offline bm.games assignment not found once in cell 14"
        assert "smoke filter" not in c14, "cell 14 already filtered -- double build?"
        cells[14]["source"] = c14.replace(CELL14_ANCHOR, CELL14_ANCHOR + CELL14_FILTER).splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    expected = [0, 12] if full else [0, 12, 14]
    assert changed == expected, f"cells changed {changed}, expected {expected}"

    out_nb.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads((REPO / "thuiv1" / "v1-1" / "kernel-metadata.json").read_text(encoding="utf-8"))
    meta["id"] = f"{OWNER}/{slug}"
    meta["title"] = slug
    meta["code_file"] = out_nb.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"built {out_nb.name}: cells changed {changed}, id {meta['id']}")
    print("push with: python3 scripts/kaggle_push_kernel.py repos/arc-agi-3-agent/thui-prior  (from arc-agi-pub)")


if __name__ == "__main__":
    import sys as _sys
    _full = "--full" in _sys.argv
    _suf = next((a.split("=", 1)[1] for a in _sys.argv if a.startswith("--suffix=")), "")
    main(full=_full or "--v11" in _sys.argv, slug_suffix=_suf, v11="--v11" in _sys.argv)
