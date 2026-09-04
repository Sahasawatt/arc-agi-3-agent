#!/usr/bin/env python3
"""thui-rank-v0 -- B61 smoke: the frame-change prior as a VETO over the LLM's own proposed actions.

Design: notes/B61-prior-as-ranker-design.md. Successor to B60 (closed: the same prior as a
fallback that SPENT actions netted -3.5 levels/run). B61 never issues an action -- it only
refuses proposals it predicts inert, using the harness's own invalid-action payload so the
LLM re-picks in the same turn.

thui-v1-1 byte-for-byte except three cells: cell 0 markdown, cell 12 appended payload
(wrap ToolAgent.analyze -> rec_step_env scores every proposal), cell 14 smoke filter
(tr87 / sk48 / sc25, 900 s/game). `--full` drops the cell-14 filter; `--suffix=-r2` names a
second run.

    python3 build_notebook.py [--full] [--suffix=-r2] [--owner=yocybercode] [--base=v3|v1]   # owner must match the pushing token (G4); base defaults to the B48 build
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
# Base chassis: "v3" = thui-v3-0 (the B48 build: thui-v1-1 + LOCAL_ANALYZER_YIELD_SECONDS 180, the build that
# drew the standing best 2.03 and has a 4-run public baseline pool 4.01 / 4.52 / 5.17 / 3.85); "v1" = thui-v1-1.
BASE = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--base=")), "v3")
SRC_NB = {"v3": REPO / "thuiv3" / "taaf-thui-v3-0.ipynb", "v1": REPO / "thuiv1" / "v1-1" / "taaf-thui-v1-1.ipynb"}[BASE]
META_SRC = {"v3": REPO / "thuiv3" / "kernel-metadata.json", "v1": REPO / "thuiv1" / "v1-1" / "kernel-metadata.json"}[BASE]
OWNER = "sahasawatt"

SMOKE_GAMES = ("tr87", "sk48", "sc25")
GAME_CLOCK_S = 900
VETO_P = 0.15          # veto when predicted change-probability is below this
VETO_MIN_OBS = 20      # a cold prior vetoes nothing
VETO_PER_STEP = 2      # third proposal in a step always executes

CELL0_MD_SMOKE = """# thui-rank-v0 — B61 smoke: frame-change prior as a VETO over the LLM's proposals

**Infrastructure smoke, not a scoring run.** `thui-v3-0` (the B48 build: thui-v1-1 + yield 180, the standing-best chassis) byte-for-byte except cells 12 and 14.
Cell 12 wraps the analyzer so every action the LLM proposes is scored by a small CNN trained
online on this game's own executed actions; a proposal predicted inert (p < 0.15, after ≥ 20
observations, ≤ 2 vetoes per step) is answered with the harness's own invalid-action payload and
the LLM re-picks. **The prior never issues an action.** Cell 14 filters to tr87 / sk48 / sc25 at
900 s each. Numbers are meaningless and must never be quoted. Design: `notes/B61-prior-as-ranker-design.md`.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

CELL0_MD_FULL = """# thui-rank-v1 — B61: frame-change prior as a VETO over the LLM's proposals, full 25 games

`thui-v3-0` (the B48 build: thui-v1-1 + yield 180, the standing-best chassis) byte-for-byte except cell 12: every action the LLM proposes is scored by a small CNN
trained online on the game's own executed actions, and a proposal predicted inert (p < 0.15, after
≥ 20 observations, ≤ 2 vetoes per step) is refused with the harness's own invalid-action payload so
the LLM re-picks in the same turn. The prior never issues an action. Seed, temperature, clock and
games inherited unchanged. Oracle: paired **levels** vs the same-seed base pair (`thui-v1-1`,
`thui-v1-1-r2`), ≥ 2 runs per arm. Design + record: `notes/B61-prior-as-ranker-design.md`.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""

CELL12_SUFFIX = r'''

# === thui-rank-v0 (B61): frame-change prior as a VETO over the LLM's proposals ==========
# Seam: same class-level wrap of ToolAgent.analyze as B60. Every step_env call carries the
# LLM's proposal; the prior scores it BEFORE the engine sees it. The prior never issues an
# action -- a vetoed single proposal gets the harness's own invalid-action payload shape.
import math as _math
import hashlib as _hashlib
import random as _random
import torch as _torch
import torch.nn as _nn
import torch.nn.functional as _F
from inference.agent import tool_agent as _ta
from inference.framework import solver as _solver
from inference.agent.action_names import to_engine_action as _to_engine, to_model_actions as _to_model

_RANK_DEV = "cpu"
_RANK_TYPES = ("ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5")
_RANK_VETO_P = @VETO_P@
_RANK_MIN_OBS = @VETO_MIN_OBS@
_RANK_PER_STEP = @VETO_PER_STEP@
_RANK_STATS = {"proposals": 0, "scored": 0, "vetoes": 0, "batch_drops": 0, "false_veto_proxy": 0,
               "updates": 0, "observed": 0, "games": 0, "wrapper_errors": 0}


def _rank_onehot(grid):
    t = _torch.zeros(16, 64, 64)
    for r, row in enumerate(grid[:64]):
        for c, v in enumerate(row[:64]):
            t[max(0, min(15, int(v))), r, c] = 1.0
    return t


def _rank_sig(grid):
    return _hashlib.blake2b(repr(grid).encode(), digest_size=8).hexdigest()


class _RankNet(_nn.Module):
    def __init__(self):
        super().__init__()
        self.c1 = _nn.Conv2d(16, 32, 3, padding=1)
        self.c2 = _nn.Conv2d(32, 64, 3, padding=1)
        self.c3 = _nn.Conv2d(64, 128, 3, padding=1)
        self.c4 = _nn.Conv2d(128, 256, 3, padding=1)
        self.act_head = _nn.Linear(256, len(_RANK_TYPES))
        self.coord_head = _nn.Conv2d(256, 1, 1)

    def forward(self, x):
        h = _F.relu(self.c1(x)); h = _F.relu(self.c2(h))
        h = _F.relu(self.c3(h)); h = _F.relu(self.c4(h))
        return self.act_head(h.mean(dim=(2, 3))), self.coord_head(h).squeeze(1)


def _rank_key(name, data):
    if name == "ACTION6":
        return f"ACTION6:{int(data.get('y', 0))},{int(data.get('x', 0))}"
    return name


class _Ranker:
    """Per-game: observe executed actions -> train; score a proposal -> p(change)."""

    def __init__(self):
        self.net = _RankNet().to(_RANK_DEV)
        self.opt = _torch.optim.Adam(self.net.parameters(), lr=1e-3)
        self.buf = []
        self.seen = set()
        self.changed = set()          # (sig, key) observed to CHANGE the board -- never vetoed
        self.observed = 0
        self.vetoed_last = None       # (sig, key) of the last veto, for the false-veto proxy

    def observe(self, grid, payload):
        if not isinstance(payload, dict) or not payload.get("executed"):
            return
        name = str(payload.get("action_name") or "").upper()
        data = payload.get("action_data") or {}
        if name == "ACTION6":
            rc = (int(data.get("y", 0)), int(data.get("x", 0))); tidx = None
        elif name in _RANK_TYPES:
            rc = None; tidx = _RANK_TYPES.index(name)
        else:
            return
        sig = _rank_sig(grid); key = (sig, _rank_key(name, data))
        label = bool(payload.get("board_changed")) or int(payload.get("frame_count") or 0) > 1
        if label:
            self.changed.add(key)
        if self.vetoed_last == key and label:
            _RANK_STATS["false_veto_proxy"] += 1
            print(f"thui-rank: FALSE-VETO proxy -- {key[1]} re-proposed, executed, changed", flush=True)
        self.vetoed_last = None
        self.observed += 1; _RANK_STATS["observed"] += 1
        if key in self.seen:
            return
        self.seen.add(key)
        self.buf.append((_rank_onehot(grid), tidx, rc, 1.0 if label else 0.0))
        if len(self.buf) > 20000:
            self.buf = self.buf[-20000:]
        self._train(steps=2)

    def _train(self, steps):
        if len(self.buf) < 4:
            return
        self.net.train()
        for _ in range(steps):
            batch = _random.sample(self.buf, min(32, len(self.buf)))
            x = _torch.stack([b[0] for b in batch]).to(_RANK_DEV)
            act_logits, coord_map = self.net(x)
            loss = _torch.zeros((), device=_RANK_DEV); n = 0
            for i, (_, tidx, rc, y) in enumerate(batch):
                tgt = _torch.tensor(y, device=_RANK_DEV)
                if tidx is not None:
                    loss = loss + _F.binary_cross_entropy_with_logits(act_logits[i, tidx], tgt)
                else:
                    loss = loss + _F.binary_cross_entropy_with_logits(coord_map[i, rc[0], rc[1]], tgt)
                n += 1
            loss = loss / max(1, n)
            self.opt.zero_grad(); loss.backward(); self.opt.step()
            _RANK_STATS["updates"] += 1
            if _RANK_STATS["updates"] % 25 == 0:
                print(f"thui-rank: update n={_RANK_STATS['updates']} buf={len(self.buf)} loss={loss.item():.4f}", flush=True)
        assert _math.isfinite(loss.item()), "thui-rank: non-finite loss"

    def score(self, grid, name, data):
        """p(change) for one proposal, or None when the prior must not judge."""
        if self.observed < _RANK_MIN_OBS:
            return None
        key = (_rank_sig(grid), _rank_key(name, data))
        if key in self.changed:
            return None
        self.net.eval()
        with _torch.no_grad():
            act_logits, coord_map = self.net(_rank_onehot(grid).unsqueeze(0).to(_RANK_DEV))
        if name == "ACTION6":
            r = max(0, min(63, int(data.get("y", 0)))); c = max(0, min(63, int(data.get("x", 0))))
            return float(_torch.sigmoid(coord_map[0, r, c]).item())
        if name in _RANK_TYPES:
            return float(_torch.sigmoid(act_logits[0, _RANK_TYPES.index(name)]).item())
        return None


def _rank_proposals(arguments):
    """Return list of (name, data, raw) for the proposal, or None if not an action call."""
    if not isinstance(arguments, dict):
        return None
    if str(arguments.get("query") or "").strip():
        return None
    raws = arguments.get("actions") if arguments.get("actions") is not None else [arguments]
    if not isinstance(raws, list):
        return None
    out = []
    for raw in raws:
        if not isinstance(raw, dict):
            return None
        name = _to_engine(raw.get("action"))
        if not name:
            return None
        data = {}
        if name == "ACTION6":
            try:
                data = {"x": int(raw["col"]), "y": int(raw["row"])}
            except Exception:
                return None
        out.append((name, data, raw))
    return out


_rankers = {}
_orig_analyze = _ta.ToolAgent.analyze


def _rank_analyze(self, state_path, action_count, *args, valid_actions=None, step_env=None, **kwargs):
    session = getattr(step_env, "__self__", None)
    if session is None or not hasattr(session, "game"):
        return _orig_analyze(self, state_path, action_count, *args, valid_actions=valid_actions, step_env=step_env, **kwargs)
    ranker = _rankers.get(id(session))
    if ranker is None:
        ranker = _rankers[id(session)] = _Ranker()
        _RANK_STATS["games"] += 1
        print(f"thui-rank: new ranker for game #{_RANK_STATS['games']}", flush=True)
    vetoes_this_step = [0]

    def rec_step_env(arguments):
        grid = _solver._grid_from_state(session.game.current_state)
        try:
            props = _rank_proposals(arguments)
            if props and vetoes_this_step[0] < _RANK_PER_STEP:
                _RANK_STATS["proposals"] += len(props)
                scored = [(n, d, r, ranker.score(grid, n, d)) for (n, d, r) in props]
                _RANK_STATS["scored"] += sum(1 for s in scored if s[3] is not None)
                inert = [s for s in scored if s[3] is not None and s[3] < _RANK_VETO_P and s[0] != "RESET"]
                if inert:
                    if len(props) == 1:
                        n, d, r, p = inert[0]
                        vetoes_this_step[0] += 1; _RANK_STATS["vetoes"] += 1
                        ranker.vetoed_last = (_rank_sig(grid), _rank_key(n, d))
                        print(f"thui-rank: VETO #{_RANK_STATS['vetoes']} {_rank_key(n, d)} p={p:.3f} obs={ranker.observed} step_vetoes={vetoes_this_step[0]}", flush=True)
                        return {"executed": False,
                                "error": f"prior: {r.get('action')} predicted inert here (p={p:.2f}); pick a different action",
                                "valid_actions": _to_model(_solver._engine_action_names(session.game)),
                                **session.timing_payload()}
                    keep = [s[2] for s in scored if s not in inert]
                    if keep:
                        vetoes_this_step[0] += 1
                        _RANK_STATS["batch_drops"] += len(inert); _RANK_STATS["vetoes"] += 1
                        print(f"thui-rank: BATCH-DROP {len(inert)}/{len(props)} inert (min p={min(s[3] for s in inert):.3f}) obs={ranker.observed}", flush=True)
                        arguments = dict(arguments); arguments["actions"] = keep
        except Exception as exc:  # the ranker must never break the harness path
            _RANK_STATS["wrapper_errors"] += 1
            print(f"thui-rank: wrapper error (pass-through): {type(exc).__name__}: {exc}", flush=True)
        payload = step_env(arguments)
        try:
            ranker.observe(grid, payload)
        except Exception as exc:
            _RANK_STATS["wrapper_errors"] += 1
            print(f"thui-rank: observe skipped: {type(exc).__name__}: {exc}", flush=True)
        return payload

    return _orig_analyze(self, state_path, action_count, *args, valid_actions=valid_actions, step_env=rec_step_env, **kwargs)


_ta.ToolAgent.analyze = _rank_analyze
assert _ta.ToolAgent.analyze is _rank_analyze, "thui-rank: analyze wrap did not land"
print(f"thui-rank-v0: ToolAgent.analyze wrapped (veto p<{_RANK_VETO_P} after {_RANK_MIN_OBS} obs, <= {_RANK_PER_STEP}/step; never issues an action)", flush=True)
# ======================================================================================
'''.replace("@VETO_P@", str(VETO_P)).replace("@VETO_MIN_OBS@", str(VETO_MIN_OBS)).replace("@VETO_PER_STEP@", str(VETO_PER_STEP))

CELL14_ANCHOR = "    bm.games = _offline_games(competition_env_files)\n"
CELL14_FILTER = (
    "    # thui-rank-v0 smoke: three games, at the REAL seam.\n"
    "    _SMOKE = " + repr(SMOKE_GAMES) + "\n"
    "    _n0 = len(bm.games)\n"
    "    bm.games = [g for g in bm.games if any(g.env_name.startswith(h) for h in _SMOKE)]\n"
    "    print(f\"thui-rank-v0: smoke filter {_n0} -> {len(bm.games)} games\", flush=True)\n"
    "    assert len(bm.games) == " + str(len(SMOKE_GAMES)) + ", f\"thui-rank-v0: expected " + str(len(SMOKE_GAMES)) + " games, got {len(bm.games)}\"\n"
    "    bm.solver.max_runtime_s_per_game = " + str(GAME_CLOCK_S) + ".0\n"
)


def main(full: bool = False, slug_suffix: str = "", owner: str = OWNER) -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 17, f"{SRC_NB.name}: expected 17 cells, found {len(cells)}"
    if BASE == "v3":  # teeth: the base must carry the yield-180 injection AND its own assert, or it is not the B48 build
        _c8 = "".join(cells[8]["source"])
        assert _c8.count("'LOCAL_ANALYZER_YIELD_SECONDS': '180'") == 2, "base v3: yield-180 injection/assert not found twice in cell 8"
    print(f"base = {BASE} ({SRC_NB.relative_to(REPO)})", flush=True)
    before = ["".join(c["source"]) for c in cells]
    slug = ("thui-rank-v1" if full else "thui-rank-v0") + slug_suffix
    out_nb = HERE / f"taaf-{slug}.ipynb"

    cells[0]["source"] = (CELL0_MD_FULL if full else CELL0_MD_SMOKE).splitlines(keepends=True)
    c12 = "".join(cells[12]["source"])
    assert "thui-rank" not in c12, "cell 12 already carries the ranker -- double build?"
    assert "@VETO" not in CELL12_SUFFIX, "placeholder not substituted"
    cells[12]["source"] = (c12 + CELL12_SUFFIX).splitlines(keepends=True)
    if not full:
        c14 = "".join(cells[14]["source"])
        assert c14.count(CELL14_ANCHOR) == 1, "offline bm.games assignment not found once in cell 14"
        cells[14]["source"] = c14.replace(CELL14_ANCHOR, CELL14_ANCHOR + CELL14_FILTER).splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    expected = [0, 12] if full else [0, 12, 14]
    assert changed == expected, f"cells changed {changed}, expected {expected}"

    out_nb.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(META_SRC.read_text(encoding="utf-8"))
    meta["id"] = f"{owner}/{slug}"; meta["title"] = slug; meta["code_file"] = out_nb.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"built {out_nb.name}: cells changed {changed}, id {meta['id']}")


if __name__ == "__main__":
    _suf = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--suffix=")), "")
    _own = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), OWNER)
    main(full="--full" in sys.argv, slug_suffix=_suf, owner=_own)
