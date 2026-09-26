# ---- thui-cp: play COMMUNITY games (dataset poonszesen/arc-interactive-community) instead of the public 25.
# Installed ONLY in the offline branch. Copies ONLY the allow-listed game dirs into a private environments dir, so the
# three quarantined official games in the pack (ft09 / ls20 / vc33) are never enumerated, loaded or played.
import importlib.metadata as _cp_md
import os as _cp_os
import shutil as _cp_shutil
import taaf.game_api as _cp_game_api

_CP_IDS = tuple(__THUI_CP_IDS__)
_CP_QUARANTINE = ("ft09", "ls20", "vc33")
assert _CP_IDS and len(set(_CP_IDS)) == len(_CP_IDS), "thui-cp: empty or duplicate allow-list"
assert not any(g.split("-")[0] in _CP_QUARANTINE for g in _CP_IDS), "thui-cp: quarantined official game in the allow-list"
_cp_roots = [r for r in _cp_os.environ.get("THUI_CP_ROOTS", "").split(_cp_os.pathsep) if r] or [
    "/kaggle/input/arc-interactive-community", "/kaggle/input/datasets/poonszesen/arc-interactive-community"]
_cp_src = next((r for r in _cp_roots if _cp_os.path.isdir(_cp_os.path.join(r, "environment_files"))), None)
if _cp_src is None:
    raise RuntimeError(f"thui-cp: community dataset not mounted; tried {_cp_roots}")
_cp_env = _cp_os.path.join(str(WORKING_DIR), "thui_cp_env")
for _cp_g in _CP_IDS:
    _cp_name, _cp_ver = _cp_g.split("-", 1)
    _cp_from = _cp_os.path.join(_cp_src, "environment_files", _cp_name, _cp_ver)
    if not _cp_os.path.isdir(_cp_from):
        raise RuntimeError(f"thui-cp: {_cp_g} missing at {_cp_from}")
    _cp_shutil.copytree(_cp_from, _cp_os.path.join(_cp_env, _cp_name, _cp_ver), dirs_exist_ok=True)
_cp_games = _offline_games(_cp_env)
_cp_by_id = {g.env_name: g for g in _cp_games}
_cp_missing, _cp_extra = sorted(set(_CP_IDS) - set(_cp_by_id)), sorted(set(_cp_by_id) - set(_CP_IDS))
if _cp_missing or _cp_extra:
    raise RuntimeError(f"thui-cp: community game set changed; missing={_cp_missing}, extra={_cp_extra}")
bm.games = [_cp_by_id[g] for g in _CP_IDS]
_cp_orig_start = _cp_game_api.GameAPI._start_game


def _cp_start_game(self, session):
    initial = _cp_orig_start(self, session)
    # the pack's baseline_actions field holds ACTION IDS, not human baselines (round 44), and its length breaks
    # taaf's per-level assert; None is taaf's documented "no baselines" mode. Metric here = levels cleared.
    self.base_actions_per_level = None
    print(f"THUI_CP game={self.game_id} n={self.number_of_levels}", flush=True)
    return initial


_cp_start_game.__wrapped__ = _cp_orig_start
_cp_game_api.GameAPI._start_game = _cp_start_game
print(f"THUI_CP_GRAFT ok games={len(bm.games)} src={_cp_src} arc-agi={_cp_md.version('arc-agi')} "
      f"arcengine={_cp_md.version('arcengine')}", flush=True)
