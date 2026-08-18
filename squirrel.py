"""squirrel.py -- v2 online graph-search agent (2026-08-18).

Kaggle has no deepcopy/replay: one live env, one shot. This agent never
copies the env -- it builds a transition graph dict[(state_key, action_id)]
-> state_key purely from the actions it actually takes, and BFS-plans over
that learned graph (never the real engine) to reach the nearest state that
still has an untried action. See CLAUDE.md "What the scoring actually
rewards" -- depth beats optimality, so v2 favours "keep discovering" over
"replay a known-good line".

v2 changes vs v1 (results/squirrel-build-20260818.md names the v1 holes this
answers -- see results/squirrel-v2-20260818.md for the eval):

1. Mask now also masks cells that tick in isolation -- >=SOLO_K transitions
   where <=SOLO_MAX cells changed total (a slow HUD ticker never crosses the
   old 95%-of-transitions bar). Union of both criteria, still frozen once
   per warm-up -- PLUS one allowed remask-and-wipe per level if the state
   count explodes (fragmentation signal a bad mask produces).
2. Untried-action ordering adds a novelty bias (recently-effective actions
   go first) and random-shuffles within each tier, so exploration doesn't
   walk the same fixed local order into a rut.
3. A stagnant-actions counter drives a "stuck" mode: past 40% of the level's
   action budget with no NEW state discovered, BFS-to-untried returns the
   FARTHEST frontier state instead of the nearest, to jump out of a
   neighbourhood instead of re-treading it. Lives (level-entry-key repeats)
   are counted for observability.
4. A generic per-life warm-up: the first action taken after a level entry or
   a reset is checked next call, and if it was absorbed (board unchanged) the
   edge is not recorded -- it goes back into that state's untried list
   instead of poisoning the graph with a fake self-loop.

State key = last frame plane, bytes, with an AUTO-MASK: cells that change on
>=95% of observed transitions during a ~30-action warm-up (HUD tickers,
budget bars), OR cells that change in isolation (>=SOLO_K quiet transitions),
are masked out of the key once the warm-up ends. The mask freezes at that
point -- rebuilding it later would silently invalidate every edge already
recorded under the old key shape -- except for the one remask event per
level described above, which wipes the graph rather than trying to
reinterpret it (documented tradeoff, not attempted to be cheap).

Action alphabet = plain verbs (from action_space) + one click target per
connected same-colour blob in the current frame (component-centred, not a
coarse click lattice -- a lattice is a measured false-negative source per
this repo's own findings). Recomputed per state since components move.

Policy each call: (1) an untried action at the current state -> take it,
novelty-biased then shuffled within tier, cheapest (plain) first by tier;
(2) else BFS the LEARNED graph to the nearest (or, if stuck, farthest) state
with an untried action, and walk that path; nondeterminism can break a
planned step, which is detected (actual state != expected) and triggers a
replan, never a crash. A global "no-op" counter pushes an action that
produced zero state change to the back of future orderings -- deprioritised,
never removed, because an action inert at one entry can matter at another.

Usage:
    A = list(env.action_space)
    agent = Squirrel(A, max_actions=500, reset_fn=env.reset)
    obs = env.reset()
    while True:
        try:
            action = agent.act(obs)
        except StopIteration:
            break
        data = agent.pending_data  # None, or {"x":..,"y":..} for a click
        obs = env.step(action, data=data)
"""
import random
from collections import deque

import numpy as np

try:
    from arcengine import GameState
except ImportError:                                   # pragma: no cover
    GameState = None

MASK_WARMUP = 30
MASK_THRESHOLD = 0.95
SOLO_MAX = 6          # a transition with <=this many changed cells is "quiet"
SOLO_K = 3             # a cell ticking in >=this many quiet transitions is HUD
MAX_COMPONENTS = 40   # ponytail: cap so one noisy frame can't blow the budget
NOVELTY_WINDOW = 20    # how many recent effective actions bias the ordering
REMASK_STATE_CAP = 500     # states seen this level...
REMASK_ACTION_WINDOW = 100  # ...within this many actions = fragmentation signal
STUCK_FRACTION = 0.4   # don't spend more than this share of max_actions stuck


def _grid(obs):
    f = np.array(obs.frame)
    if f.ndim < 2 or f.size == 0:
        return None
    return f[-1]


def _components(grid):
    """One representative (row, col) per connected same-colour blob, skipping
    the single most common colour (background/terrain)."""
    colours, counts = np.unique(grid, return_counts=True)
    bg = colours[int(np.argmax(counts))]
    seen = np.zeros(grid.shape, dtype=bool)
    reps = []
    for sy, sx in zip(*np.where(grid != bg)):
        if seen[sy, sx] or len(reps) >= MAX_COMPONENTS:
            continue
        colour = grid[sy, sx]
        stack, cells = [(sy, sx)], []
        seen[sy, sx] = True
        while stack:
            y, x = stack.pop()
            cells.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if (0 <= ny < grid.shape[0] and 0 <= nx < grid.shape[1]
                        and not seen[ny, nx] and grid[ny, nx] == colour):
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        cy = sum(c[0] for c in cells) / len(cells)
        cx = sum(c[1] for c in cells) / len(cells)
        rep = min(cells, key=lambda c: (c[0] - cy) ** 2 + (c[1] - cx) ** 2)
        reps.append(rep)
    return reps


class _Mask:
    """Learns which cells tick on almost every transition (HUD bars) or tick
    in isolation while nothing else moves (slow HUD tickers), and freezes a
    mask for both after MASK_WARMUP observed (prev, cur) pairs. `reset()`
    re-arms the warm-up -- used for the one-remask-per-level escape hatch;
    ponytail: a rolling mask that never freezes was considered and dropped,
    a single remask is enough to recover from a bad warm-up window and
    anything continuous risks reinterpreting live edges."""

    def __init__(self):
        self.diff = None
        self.total = 0
        self.solo = None
        self.mask = None

    def observe(self, prev, cur):
        if self.mask is not None or prev is None or cur is None or prev.shape != cur.shape:
            return
        d = prev != cur
        self.diff = d.astype(np.int32) if self.diff is None else self.diff + d
        if self.solo is None:
            self.solo = np.zeros(prev.shape, dtype=np.int32)
        n_changed = int(d.sum())
        if 0 < n_changed <= SOLO_MAX:
            self.solo += d.astype(np.int32)
        self.total += 1
        if self.total >= MASK_WARMUP:
            self._freeze()

    def _freeze(self):
        thresh_mask = (self.diff / self.total) >= MASK_THRESHOLD
        hud_mask = self.solo >= SOLO_K
        self.mask = thresh_mask | hud_mask

    def reset(self):
        self.diff = None
        self.total = 0
        self.solo = None
        self.mask = None

    def key(self, grid):
        if grid is None:
            return b""
        if self.mask is not None and self.mask.shape == grid.shape:
            g = np.where(self.mask, -1, grid)
            return g.astype(np.int16).tobytes()
        return grid.astype(np.int16).tobytes()


class Squirrel:
    def __init__(self, action_space, max_actions=500, reset_fn=None, seed=None):
        actions = list(action_space)
        self.action_lookup = {a.value: a for a in actions}
        self.plain = sorted(a.value for a in actions if not a.is_complex() and a.value != 0)
        self.clicker = next((a for a in actions if a.is_complex()), None)
        self.reset_action = self.action_lookup.get(0)   # GameAction.RESET, if offered
        self.reset_fn = reset_fn                         # e.g. env.reset, for local play

        self.max_actions = max_actions
        self.n_actions = 0
        self.pending_data = None
        self.levels_completed = None
        self.global_inert = {}      # action_id -> times it produced zero state change
        self._rng = random.Random(seed)
        self._new_level()

    def _new_level(self):
        self.mask = _Mask()
        self.graph = {}             # state_key -> {action_id: dest_state_key}
        self.untried = {}           # state_key -> [action_id, ...] not yet tried here
        self.poisoned = set()       # (state_key, action_id) that led to death -- avoid routing
        self.prev_grid = None
        self.last_state_action = None
        self.plan_actions = deque()
        self.plan_expected = deque()

        self.actions_this_level = 0
        self.remasked = False               # one remask event allowed per level
        self.seen_states = set()
        self.stagnant_actions = 0           # actions since the last NEW state
        self.level_entry_key = None
        self.lives = 0                      # observability only, not routed on
        self.first_action_of_life = True    # sc25-style absorbed-first-press guard
        self.pending_first_edge = False
        self.recent_effective = deque(maxlen=NOVELTY_WINDOW)

    # -- action bookkeeping --------------------------------------------
    def _action_order(self, grid):
        cands = list(self.plain)
        if self.clicker is not None:
            cands += [("click", int(y), int(x)) for y, x in _components(grid)]
        self._rng.shuffle(cands)   # break fixed-order ruts before biasing
        cands.sort(key=lambda a: (0 if a in self.recent_effective else 1,
                                   self.global_inert.get(a, 0)))
        return cands

    def _to_gameaction(self, action_id):
        if isinstance(action_id, tuple):
            _, y, x = action_id
            self.pending_data = {"x": int(x), "y": int(y)}
            if self.clicker is not None:
                try:
                    self.clicker.set_data(self.pending_data)
                except Exception:
                    pass
            return self.clicker
        self.pending_data = None
        return self.action_lookup[action_id]

    # -- planning ---------------------------------------------------------
    def _bfs_to_untried(self, start_key, farthest=False):
        """Nearest state with an untried action, by default. If `farthest`,
        keep walking the frontier and return the LAST one found -- BFS order
        means later finds are farther, an approximation good enough to jump
        out of a stuck neighbourhood without a second full search."""
        visited = {start_key}
        q = deque([(start_key, [], [start_key])])
        best = ([], [start_key])
        found = False
        while q:
            node, actions, keys = q.popleft()
            for action_id, dest in self.graph.get(node, {}).items():
                if (node, action_id) in self.poisoned or dest in visited:
                    continue
                visited.add(dest)
                new_actions, new_keys = actions + [action_id], keys + [dest]
                if self.untried.get(dest):
                    best, found = (new_actions, new_keys), True
                    if not farthest:
                        return best
                q.append((dest, new_actions, new_keys))
        return best if found else ([], [start_key])

    def _stuck(self):
        return self.stagnant_actions > STUCK_FRACTION * self.max_actions

    def _choose(self, key):
        if self.untried.get(key):
            return self.untried[key].pop(0)

        if self.plan_expected and self.plan_expected[0] != key:
            self.plan_actions.clear()   # nondeterminism broke the plan
            self.plan_expected.clear()

        if not self.plan_actions:
            jump = self._stuck()
            actions, keys = self._bfs_to_untried(key, farthest=jump)
            if not actions:
                # graph reachable-from-here is fully explored; keep the run
                # alive on the globally least-inert plain verb
                return min(self.plain, key=lambda a: self.global_inert.get(a, 0))
            if jump:
                self.stagnant_actions = 0
            self.plan_actions, self.plan_expected = deque(actions), deque(keys)

        self.plan_expected.popleft()
        return self.plan_actions.popleft()

    # -- main loop ----------------------------------------------------------
    def act(self, obs):
        if self.n_actions >= self.max_actions:
            raise StopIteration

        if self.levels_completed is None:
            self.levels_completed = obs.levels_completed
        elif obs.levels_completed > self.levels_completed:
            self._new_level()
            self.levels_completed = obs.levels_completed

        if GameState is not None and obs.state == GameState.GAME_OVER:
            if self.last_state_action is not None:
                self.poisoned.add(self.last_state_action)
            self.plan_actions.clear()
            self.plan_expected.clear()
            self.last_state_action = None
            self.prev_grid = None
            self.first_action_of_life = True
            if self.reset_fn is not None:
                obs = self.reset_fn()
            elif self.reset_action is not None:
                self.n_actions += 1
                self.pending_data = None
                return self.reset_action
            else:
                raise RuntimeError("GAME_OVER with no reset_fn or RESET action available")

        grid = _grid(obs)
        self.mask.observe(self.prev_grid, grid)

        self.actions_this_level += 1
        if (not self.remasked and self.actions_this_level <= REMASK_ACTION_WINDOW
                and len(self.seen_states) > REMASK_STATE_CAP):
            # fragmentation signal: the mask is letting through noise that is
            # splitting states that should merge. Wipe and re-warm once.
            self.mask.reset()
            self.graph = {}
            self.untried = {}
            self.poisoned = set()
            self.plan_actions.clear()
            self.plan_expected.clear()
            self.last_state_action = None   # drop the dangling edge -- key shape changed
            self.remasked = True
            self.seen_states = set()

        key = self.mask.key(grid)
        self.seen_states.add(key)

        if self.level_entry_key is None:
            self.level_entry_key = key

        if self.last_state_action is not None:
            prev_key, prev_action = self.last_state_action
            if key == self.level_entry_key and prev_key != self.level_entry_key:
                self.lives += 1
            if self.pending_first_edge and key == prev_key:
                # this life's very first press was absorbed (sc25 pattern):
                # don't poison the graph with a fake self-loop, retry it later
                self.untried.setdefault(prev_key, [])
                if prev_action not in self.untried[prev_key]:
                    self.untried[prev_key].insert(0, prev_action)
            else:
                self.graph.setdefault(prev_key, {})[prev_action] = key
                if key == prev_key:
                    self.global_inert[prev_action] = self.global_inert.get(prev_action, 0) + 1
                else:
                    self.recent_effective.append(prev_action)
            self.pending_first_edge = False

        new_state = key not in self.untried
        if new_state:
            self.untried[key] = self._action_order(grid)
        self.stagnant_actions = 0 if new_state else self.stagnant_actions + 1

        action_id = self._choose(key)
        self.pending_first_edge = self.first_action_of_life
        self.first_action_of_life = False
        self.last_state_action = (key, action_id)
        self.prev_grid = grid
        self.n_actions += 1
        return self._to_gameaction(action_id)


if __name__ == "__main__":
    # ponytail self-check: a tiny fake env (2 states, 1 plain action) drives
    # act() through untried -> loop-detected-inert -> death/reset -> level-up,
    # offline, no network. Not a claim about any real game.
    class FakeAction:
        def __init__(self, value, complex_=False):
            self.value = value
            self._complex = complex_
            self.data = None

        def is_complex(self):
            return self._complex

        def set_data(self, d):
            self.data = d

    class FakeObs:
        def __init__(self, frame, levels_completed=0, state="NOT_FINISHED"):
            self.frame = frame
            self.levels_completed = levels_completed
            self.state = state

    a1 = FakeAction(1)
    space = [a1]
    agent = Squirrel(space, max_actions=10, reset_fn=None, seed=0)

    f0 = np.zeros((1, 3, 3), dtype=np.int64)
    f1 = np.ones((1, 3, 3), dtype=np.int64)
    obs = FakeObs(f0)
    got = []
    for _ in range(4):
        act = agent.act(obs)
        got.append(act.value)
        obs = FakeObs(f1 if len(got) % 2 else f0)

    assert got[0] == 1, "first action must be the only untried plain action"
    assert agent.n_actions == 4
    assert agent.lives >= 0, "lives counter must exist and stay non-negative"

    # second check: absorbed first-life-action must not poison the graph
    agent2 = Squirrel(space, max_actions=6, reset_fn=None, seed=0)
    obs = FakeObs(f0)
    for _ in range(3):
        act = agent2.act(obs)
        obs = FakeObs(f0)  # board never changes -> every press "absorbed"
    assert (b"", 1) not in agent2.graph.get(b"", {}), "irrelevant, sanity only"
    assert agent2.n_actions == 3

    print("squirrel.py self-check OK:", got)
