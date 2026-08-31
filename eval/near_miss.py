r"""Is a failed level a NEAR MISS or a WALL? The question that decides whether an
efficiency-for-depth trade exists at all.

B35 priced the trade and found it worth taking at almost any price: one more level per game at
twenty times the human baseline still lifts clock2x 6.40 -> 6.88, because the completion cap binds
and the per-level term does not. What it could not say is whether any mechanism could buy that
level. Spending more only pays if the level was reachable and the run lost it; if the run never
found the path at all, more of the same is the clock2x result (+65% actions for +2 levels).

THE TEST, which needs trajectories and nothing else. Per-level success is a coin flip -- 47.3% over
493 levels entered -- so the same (game, level) is usually cleared by some runs and failed by
others. Take a WINNER's ordered board states on that level and ask how far along them a LOSER got:

  overlap  share of the winner's distinct states the loser also visited
  reach    the deepest prefix of the winner's ORDERED path the loser COVERED -- the boundary state
           must be one the loser visited AND it must have seen at least COVER of everything before
           it. The obvious definition, deepest matching index, is broken and `selftest()` says why.

A loser with high reach was on the path and lost it -- retry, backtrack, or a wider search buys the
level, and the trade is real. A loser with low reach never found the path, and no amount of budget
spent the same way finds it either.

CONTROLS, because this metric is only as good as the state identity behind it:
  C-pos  winner vs winner on the SAME (game, level) -- two runs that both solved it must share
         states, or `board_ascii` is not identifying states at all
  C-neg  loser vs a winner of a DIFFERENT game -- must be ~0. Boards are mostly background, so if
         generic states collide across games every number above is inflated and meaningless. This
         is the control that can kill the instrument, and it is the one worth reading first.

`board_ascii` cannot see hidden counters, so two genuinely different states can collide. That
inflates overlap and reach, which is the UNSAFE direction here -- a near-miss reading is what would
justify spending a slot. Treat a high reach as a hypothesis, not a finding.

    python eval/near_miss.py <traj-root> [--emit states.json]
    python eval/near_miss.py states.json
"""
from __future__ import annotations

import collections
import glob
import hashlib
import json
import os
import random
import statistics as st
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _h(s: str) -> str:
    return hashlib.blake2b(s.encode("utf-8"), digest_size=8).hexdigest()


def read_game(path: str) -> dict[int, dict]:
    """{level: {"states": [hash, ...], "cleared": bool}} for one game of one run.

    Level attribution matches eval/trajectory_probe.py: `level` on an action event is the level
    AFTER it, so the clearing action arrives carrying N+1 and is credited back to N.
    """
    acts, start = [], None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            e = json.loads(line)
            if e.get("type") == "action":
                acts.append(e)
            elif e.get("type") == "initial" and start is None:
                start = e.get("board_ascii") or ""

    out: dict[int, dict] = {}
    cur = object()
    prev = _h(start) if start is not None else None
    for e in acts:
        lv = e.get("level")
        if e.get("level_completed") and isinstance(lv, int):
            lv -= 1
        if lv != cur:
            cur = lv
            out[lv] = {"states": ([prev] if prev else []), "cleared": False}
        st_ = _h(e.get("board_ascii") or "")
        out[lv]["states"].append(st_)
        if e.get("level_completed"):
            out[lv]["cleared"] = True
        prev = st_
    return out


def load(root: str) -> dict:
    """{run: {game: {level: {...}}}}"""
    runs = {}
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d)
        if not os.path.isdir(p):
            continue
        games = {}
        for f in glob.glob(os.path.join(p, "**", "*_p0_events.jsonl"), recursive=True):
            games[os.path.basename(f).split("-")[0]] = read_game(f)
        if games:
            runs[d] = games
    return runs


COVER = 0.5  # a prefix counts as reached only if the loser visited this share of it


def reach(loser: list[str], winner: list[str]) -> tuple[float, float]:
    """(overlap, reach) of a loser against one winner's ordered path.

    `reach` is the deepest prefix of the winner's path that the loser COVERED, not the deepest
    single state it happened to touch. The naive form -- deepest matching index -- was measured
    2026-08-31 and is broken: winners revisit states, so a winner returning late to a state near
    its start hands every loser a high score for free. Its tell was a row reading
    `sc25 L2 reach 0.853` for a loser that had spent ONE action, which no definition of progress
    can support. Requiring COVER of the prefix kills that; `selftest()` pins both behaviours.
    """
    ls = set(loser)
    if not winner:
        return 0.0, 0.0
    distinct = set(winner)
    overlap = len(ls & distinct) / len(distinct)
    hits = 0
    deepest = 0
    for i, s in enumerate(winner):
        if s not in ls:
            continue
        hits += 1
        # the boundary state itself must be one the loser visited, and the prefix up to it must
        # be COVERED. Without the first clause a loser that saw half the states scores the whole
        # path; without the second, one late coincidence does.
        if hits >= (i + 1) * COVER:
            deepest = i + 1
    return overlap, deepest / len(winner)


def selftest() -> int:
    """The metric's own positive and negative controls, on paths whose answer is known."""
    w = [f"s{i}" for i in range(10)]
    cases = [
        ("full follower",      w,                      1.0, 1.0),
        ("first half",         w[:5],                  0.5, 0.5),
        ("one late state",     ["s9"],                 0.1, 0.0),
        ("one early state",    ["s0"],                 0.1, 0.1),
        ("nothing in common",  ["zzz"],                0.0, 0.0),
        ("every other state",  w[::2],                 0.5, 0.9),
    ]
    bad = []
    for name, loser, want_ov, want_re in cases:
        ov, re_ = reach(loser, w)
        if abs(ov - want_ov) > 1e-9 or abs(re_ - want_re) > 1e-9:
            bad.append(f"{name}: got overlap {ov:.3f} reach {re_:.3f}, want {want_ov} / {want_re}")
    for b in bad:
        print("  [FAIL] selftest", b)
    if bad:
        return 1
    print("selftest OK -- a loser that walked half the path scores 0.5, and one that touched only "
          "the LAST state scores 0.0")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python eval/near_miss.py <traj-root|states.json> [--emit out.json]",
              file=sys.stderr)
        return 2
    if sys.argv[1] == "--selftest":
        return selftest()
    if selftest():
        print("  refusing to report: the metric failed its own control", file=sys.stderr)
        return 1
    src = sys.argv[1]
    emit = sys.argv[sys.argv.index("--emit") + 1] if "--emit" in sys.argv else None
    if src.endswith(".json"):
        runs = json.loads(open(src, encoding="utf-8").read())["runs"]
        runs = {r: {g: {int(k): v for k, v in lv.items()} for g, lv in gs.items()}
                for r, gs in runs.items()}
        print(f"states from fixture {src}")
    else:
        runs = load(src)
    if emit:
        with open(emit, "w", encoding="utf-8") as fh:
            json.dump({"source": "board_ascii hashes per run/game/level from the kernel-output "
                                 "raw-event sidecars, by eval/near_miss.py", "runs": runs}, fh)
        print(f"emitted {emit}")

    print(f"runs: {len(runs)}  {sorted(runs)}")

    # index (game, level) -> winners / losers
    cells: dict[tuple[str, int], dict[str, list[str]]] = {}
    for r, games in runs.items():
        for g, lvs in games.items():
            for lv, d in lvs.items():
                c = cells.setdefault((g, lv), {"win": [], "lose": []})
                c["win" if d["cleared"] else "lose"].append(r)
    mixed = {k: v for k, v in cells.items() if v["win"] and v["lose"]}
    print(f"(game, level) cells entered: {len(cells)}   with BOTH a winner and a loser: {len(mixed)}")

    def path(r, g, lv):
        return runs[r][g][lv]["states"]

    # ---- C-neg first: it is the one that can kill the instrument
    rng = random.Random(20260831)
    neg = []
    keys = sorted(mixed)
    for (g, lv), c in ((k, mixed[k]) for k in keys):
        for lr in c["lose"]:
            for _ in range(2):
                g2, lv2 = rng.choice([k for k in keys if k[0] != g])
                w2 = rng.choice(mixed[(g2, lv2)]["win"])
                neg.append(reach(path(lr, g, lv), path(w2, g2, lv2)))
    if not neg:
        print("  [FAIL] no cross-game pairs to control with")
        return 1
    n_ov, n_re = [x[0] for x in neg], [x[1] for x in neg]
    print(f"\nC-neg  loser vs a winner of a DIFFERENT game, n={len(neg)}")
    print(f"       overlap median {st.median(n_ov):.4f} mean {st.mean(n_ov):.4f} "
          f"max {max(n_ov):.4f}   reach median {st.median(n_re):.4f} mean {st.mean(n_re):.4f}")
    if st.mean(n_ov) > 0.02:
        print("  [FAIL] states collide across games -- board_ascii is not identifying states, "
              "and every number below is inflated. Stop here.")
        return 1
    print("       OK -- states do not collide across games")

    # ---- C-pos: two winners on the same cell
    # Computed EXACTLY as the losers are below -- each winner against its BEST-matching other
    # winner, max over candidates. A control taken as a median while the subject is a max is a
    # comparison between two different statistics, and it reads as a real difference.
    pos = []
    for (g, lv), c in mixed.items():
        ws = c["win"]
        for i in range(len(ws)):
            others = [ws[j] for j in range(len(ws)) if j != i]
            if not others:
                continue
            pos.append(max((reach(path(ws[i], g, lv), path(w, g, lv)) for w in others),
                           key=lambda t: t[1]))
    if pos:
        p_ov, p_re = [x[0] for x in pos], [x[1] for x in pos]
        print(f"\nC-pos  winner vs winner, same cell, n={len(pos)}")
        print(f"       overlap median {st.median(p_ov):.3f}   reach median {st.median(p_re):.3f}")
        if st.median(p_ov) <= st.mean(n_ov):
            print("  [FAIL] two runs that BOTH solved the level share no more state than two "
                  "unrelated games do -- the metric cannot see a shared path")
            return 1
        print("       OK -- solving the same level does share states")

    # ---- the measurement
    res = []
    for (g, lv), c in mixed.items():
        for lr in c["lose"]:
            best = max((reach(path(lr, g, lv), path(w, g, lv)) for w in c["win"]),
                       key=lambda t: t[1])
            res.append((g, lv, lr, best[0], best[1], len(path(lr, g, lv))))
    r_ov = [x[3] for x in res]
    r_re = [x[4] for x in res]
    print(f"\nLOSERS against the best-matching winner of the same cell, n={len(res)}")
    print(f"   overlap  median {st.median(r_ov):.3f}  mean {st.mean(r_ov):.3f}")
    print(f"   reach    median {st.median(r_re):.3f}  mean {st.mean(r_re):.3f}")
    for t in (0.25, 0.50, 0.75, 0.90):
        n = sum(1 for x in r_re if x >= t)
        print(f"   reach >= {t:.2f}: {n:4d} of {len(res)}  ({100.0*n/len(res):5.1f}%)")

    print("\n   the deepest near-misses (reach, then overlap)")
    for g, lv, lr, ov, re_, n in sorted(res, key=lambda x: -x[4])[:12]:
        print(f"     {g} L{lv}  {lr:16s} reach {re_:.3f}  overlap {ov:.3f}  "
              f"loser spent {n - 1:4d} actions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
