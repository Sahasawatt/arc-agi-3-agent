"""How much does `compete.play` earn per SECOND? (2026-08-16)

Kaggle scores: v1 = 0.11, v7 = 0.10, **v8 = 0.01**. v8's only behavioural change
was `PLAY_SECONDS_UNCLAIMED = 60` — on games no driver signature claims, `play`
got 60s of the 240s game clock instead of 180s, and the bandit mop-up got the
rest. The per-game total never changed. So the ten-fold drop is entirely about
what `play` does with 60s versus 180s.

The committed explanation is *"the mop-up is actively harmful relative to
`compete.play`"*. There is a sharper candidate, and this repo's own notes support
it: **`play` has a fixed STARTUP COST.** It cannot plan until the movement model
is coherent, and `CLAUDE.md` records the warm-up costing ls20 level 1 sixteen of
the thirty-nine actions it spends on a goal box seven steps away. If that cost is
real in WALL-CLOCK terms, `play`'s yield against time is a **step function**, and
cutting its budget to a third lands below the step — clearing nothing rather than
clearing proportionally less.

The two readings predict different curves and only one run separates them:
  - **mop-up harmful** -> yield is roughly linear in time; 60s should earn about
    a third of what 180s earns.
  - **fixed startup cost** -> yield is a step; 60s earns ~nothing, and most
    levels land well after it.

**On the hidden 110 no driver signature claims anything** (v1 without drivers
scored 0.11, v7 with fourteen scored 0.10), so every hidden game is an "unclaimed"
game and got the 60s slice. Locally the honest proxy is a game the GENERIC rungs
clear with no driver: `ls20` is the only one that clears levels at all (7 of 7),
which makes it the exact case v8 starved.

This runs `play` once per game and prints the WALL CLOCK at every level-up, so
the 60 / 180 / 240 second answers are all read off a single run rather than
guessed. `compete.py` is patched as TEXT and exec'd as a separate module — the
file on disk is never touched, so this needs no sweep.

    ./.venv/Scripts/python.exe kaggle_yield_probe.py > results/kaggle-yield.txt
"""

import sys
import time
import types

import arc_agi

GAMES = sys.argv[1:] or ["ls20"]

SRC = open("compete.py", encoding="utf-8").read()

A_DEF = "def play(env, budget=BUDGET, rows=HUD_ROW):"
A_LVL = """        if obs.levels_completed > done:
            per_level.append(spent_at_level)"""
for a in (A_DEF, A_LVL):
    assert SRC.count(a) == 1, "anchor moved -- refusing to patch"

PATCHED = SRC.replace(
    A_DEF,
    A_DEF + "\n    _T0 = __import__('time').time()",
).replace(
    A_LVL,
    A_LVL + "\n            print('LEVELCLOCK lvl=%d t=%.1fs actions=%d'"
            " % (obs.levels_completed, __import__('time').time() - _T0,"
            " sum(per_level)), flush=True)",
)

m = types.ModuleType("compete_yield")
sys.modules["compete_yield"] = m
exec(compile(PATCHED, "compete_yield.py", "exec"), m.__dict__)
print("patched compete loaded (file on disk untouched)")

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

for game in GAMES:
    print(f"\n{'=' * 62}\n=== {game} ===", flush=True)
    env = arc.make(envs[game].game_id)
    t0 = time.time()
    try:
        res = m.play(env)
    except Exception as e:                        # noqa: BLE001
        print(f"  play raised {type(e).__name__}: {e}")
        continue
    el = time.time() - t0
    lvl = res[0] if isinstance(res, tuple) else res
    print(f"  play returned after {el:.1f}s -> {lvl}")

print("\n" + "=" * 62)
print("READ each LEVELCLOCK line against the two candidate budgets:")
print("  levels with t <=  60s  -> what v8 got on every hidden game")
print("  levels with t <= 180s  -> what v7 got")
print("  levels with t <= 240s  -> what v9-lite gets (play owns the whole clock)")
print()
print("If the 60s count is ~0 while the 180s count is most of them, the drop is a")
print("STARTUP COST and v9-lite should recover v7's score and a little more. If the")
print("counts scale roughly with time, the mop-up really was doing damage and")
print("giving play the last 60s back buys correspondingly little.")
