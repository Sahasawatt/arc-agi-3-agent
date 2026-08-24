"""B26, offline: is a transition model learnable from what the agent is shown?

R29 sec.9 answered "no" -- a recorded (level, board, action) reproduces the board 58.7% and
the harness's own board_changed flag 77.8%, so "abort on first prediction miss" would fire
on half of all correct repeats. That number is reproduced here as CONTROL 1 and then
REFUTED by changing one field.

sec.9 keyed the action on `action_name`, which is ACTION1..ACTION6/RESET. Every mouse click
is ACTION6 regardless of where it landed, and the corpus holds 662 distinct (game, click
cell) pairs. So a click at (58,35) and a click at (29,22) from the same board were recorded
as the same (state, action) and compared to each other. `action_display` carries the cell
-- "MOUSE(row=58, col=35)" -- and it is what the AGENT sees: its own transitions render as
ActionTransitionView(action='MOUSE(row=58, col=35)', ...) in tool output, and its user turn
reads "Executed actions: MOUSE(row=38, col=15)."

Swapping that one field is surgical rather than a shrink: name and display are in bijection
for keyboard actions (CONTROL 2), so the 311 keyboard repeats are IDENTICAL under both keys,
and only the click population moves -- 135 repeats to 13, because 122 of them were different
actions wearing one symbol.

Controls, in the order they gate:
  1. reproduce sec.9's published 446 / 58.7% / 77.8% under action_name  (loader is theirs)
  2. action_name <-> action_display is a bijection on keyboard actions  (change is surgical)
  3. board_ascii is a bijection with the numeric board                  (the key is not lossy)
  4. positive controls: a corrupted key must score WORSE
  5. null baseline: majority-class ("always changed") is what 98.1% must beat

NOT a control: dropping `level` from the key. Measured vacuous -- the 64x64 board hash
already determines the level, so the corrupted key scores identically and discriminates
nothing. Dropping the ACTION or the BOARD does bite.
"""
import collections
import hashlib
import json
import sys

from corpus import RUNS5, game_files, load_game, game_key

PUBLISHED = (446, 58.7, 77.8)  # R29 sec.9's headline, under action_name


def h(s):
    return hashlib.md5(s.encode()).hexdigest()[:12] if s else None


def scan(keyfield="action_display", only=None, drop=None):
    """Walk every run-game and count exact (level, prev board, action) repeats.

    only: None | "kbd" | "mouse"      drop: None | "action" | "board"
    """
    per = collections.defaultdict(collections.Counter)
    anim = collections.Counter()
    flags = collections.Counter()
    misses = []
    for r in RUNS5:
        for f in game_files(r):
            g, prev, rec = game_key(f)[:4], None, {}
            for e in load_game(f):
                if e.get("type") not in ("initial", "action"):
                    continue
                if e.get("type") == "action":
                    disp = str(e.get("action_display"))
                    is_mouse = disp.startswith("MOUSE")
                    keep = only is None or (only == "mouse") == is_mouse
                    act = e.get(keyfield)
                    k = ((e.get("level"), prev) if drop == "action" else
                         (e.get("level"), act) if drop == "board" else
                         (e.get("level"), prev, act))
                    cur, ch = h(e.get("board_ascii")), bool(e.get("board_changed"))
                    an = bool(e.get("animation"))
                    if prev is not None and k in rec:
                        pb, pch, pan = rec[k]
                        if keep:
                            per[g]["rep"] += 1
                            per[g]["board_ok"] += (pb == cur)
                            per[g]["flag_ok"] += (pch == ch)
                            per[g]["mouse"] += is_mouse
                            flags[ch] += 1
                            anim[f"{int(pan)}{int(an)}_t"] += 1
                            anim[f"{int(pan)}{int(an)}_ok"] += (pb == cur)
                            if pch != ch:
                                misses.append((g, "mouse" if is_mouse else "kbd"))
                    if prev is not None:
                        rec.setdefault(k, (cur, ch, an))
                prev = h(e.get("board_ascii"))
    tot = collections.Counter()
    for c in per.values():
        tot.update(c)
    return tot, per, anim, flags, misses


def pct(a, b):
    return 100.0 * a / b if b else 0.0


def line(label, t):
    print(f"  {label:38s} repeats={t['rep']:5d}  board {pct(t['board_ok'], t['rep']):5.1f}%"
          f"  flag {pct(t['flag_ok'], t['rep']):5.1f}%")


def main():
    # ---- CONTROL 1: reproduce R29 sec.9 exactly, with their key ----
    name_tot, name_per, _, _, _ = scan("action_name")
    got = (name_tot["rep"], round(pct(name_tot["board_ok"], name_tot["rep"]), 1),
           round(pct(name_tot["flag_ok"], name_tot["rep"]), 1))
    ok1 = got == PUBLISHED
    print(f"CONTROL 1  reproduces R29 sec.9 ({PUBLISHED[0]} / {PUBLISHED[1]}% / "
          f"{PUBLISHED[2]}%): {ok1}   got {got}")
    if not ok1:
        print("  loader does not reproduce the published numbers -- STOP, read nothing below")
        return 1

    # ---- CONTROL 2: the swap can only touch clicks ----
    n2d, d2n, cells = collections.defaultdict(set), collections.defaultdict(set), set()
    for r in RUNS5:
        for f in game_files(r):
            g = game_key(f)[:4]
            for e in load_game(f):
                if e.get("type") != "action":
                    continue
                d, n = str(e.get("action_display")), e.get("action_name")
                if d.startswith("MOUSE"):
                    cells.add((g, d))
                else:
                    n2d[(g, n)].add(d)
                    d2n[(g, d)].add(n)
    bij = (sum(len(v) > 1 for v in n2d.values()) == 0
           and sum(len(v) > 1 for v in d2n.values()) == 0)
    print(f"CONTROL 2  action_name <-> action_display bijective on keyboard: {bij}"
          f"   ({len(cells)} distinct click cells the name key discards)")
    if not bij:
        print("  the swap is not surgical -- STOP")
        return 1

    # ---- CONTROL 3: the board key itself is not lossy ----
    a2b, b2a = collections.defaultdict(set), collections.defaultdict(set)
    for r in RUNS5:
        for f in game_files(r):
            g = game_key(f)[:4]
            for e in load_game(f):
                b, a = e.get("board"), e.get("board_ascii")
                if b is None or a is None:
                    continue
                hb = hashlib.md5(json.dumps(b, sort_keys=True).encode()).hexdigest()[:12]
                a2b[(g, h(a))].add(hb)
                b2a[(g, hb)].add(h(a))
    lossless = (sum(len(v) > 1 for v in a2b.values()) == 0
                and sum(len(v) > 1 for v in b2a.values()) == 0)
    print(f"CONTROL 3  board_ascii <-> numeric board bijective: {lossless}"
          f"   ({len(a2b)} distinct boards)  -> the key is not lossy")
    if not lossless:
        print("  the ascii key collides -- sec.9's number could be an artifact of THAT instead")
        return 1

    # ---- the corrected reading ----
    tot, per, anim, flags, misses = scan("action_display")
    print("\nTHE KEY, ONE FIELD APART")
    line("(level, board, action_NAME)   sec.9", name_tot)
    line("(level, board, action_DISPLAY)", tot)
    print()
    for pop in ("kbd", "mouse"):
        t_n, _, _, _, _ = scan("action_name", only=pop)
        t_d, _, _, _, _ = scan("action_display", only=pop)
        line(f"{pop}-only, name key", t_n)
        line(f"{pop}-only, display key", t_d)
    print("  -> keyboard population identical (bijection); only clicks move, 135 -> 13,"
          "\n     because 122 of them were different actions wearing one symbol")

    # ---- CONTROL 4: positive controls ----
    print("\nCONTROL 4  a corrupted key must score WORSE")
    worse = True
    for d, lab in ((None, "full key"), ("action", "ACTION dropped"), ("board", "BOARD dropped")):
        t, _, _, _, _ = scan("action_display", drop=d)
        line(lab, t)
        if d and pct(t["board_ok"], t["rep"]) >= pct(tot["board_ok"], tot["rep"]):
            worse = False
    print(f"  both corruptions score worse: {worse}")
    if not worse:
        print("  the instrument does not respond to corruption -- STOP")
        return 1

    # ---- CONTROL 5: null baseline ----
    n = sum(flags.values())
    kb, _, _, kflags, _ = scan("action_display", only="kbd")
    print("\nCONTROL 5  null baseline for the flag claim")
    print(f"  board_changed among the {n} repeats: True={flags[True]} False={flags[False]}")
    print(f"  majority-class predictor          {pct(max(flags.values()), n):5.1f}%")
    print(f"  recorded-transition predictor     {pct(tot['flag_ok'], tot['rep']):5.1f}%"
          f"   <- must beat the line above")
    print(f"  keyboard only: majority {pct(max(kflags.values()), sum(kflags.values())):5.1f}%"
          f"   recorded {pct(kb['flag_ok'], kb['rep']):5.1f}%  (n={kb['rep']})")
    print(f"  residual flag misses: {len(misses)} -> {dict(collections.Counter(misses))}")

    print("\nPER GAME, corrected key")
    print(f"  {'game':6s}{'rep':>6s}{'board':>9s}{'flag':>9s}")
    for g, c in sorted(per.items(), key=lambda x: -x[1]["rep"]):
        print(f"  {g:6s}{c['rep']:6d}{pct(c['board_ok'], c['rep']):8.1f}%"
              f"{pct(c['flag_ok'], c['rep']):8.1f}%")

    print("\nANIMATION, corrected key (present-then, present-now) -> board reproduced")
    for k in ("00", "01", "10", "11"):
        if anim[f"{k}_t"]:
            print(f"  {k}: {anim[f'{k}_ok']}/{anim[f'{k}_t']} = "
                  f"{pct(anim[f'{k}_ok'], anim[f'{k}_t']):5.1f}%")
    print("  -> the 01/10 flip cases sec.9 reported were themselves click artifacts")

    # ---- coverage: reliable is not the same as available ----
    seen = collections.Counter()
    known = collections.Counter()
    cov = collections.defaultdict(collections.Counter)
    dec = 0
    for r in RUNS5:
        for f in game_files(r):
            g, prev = game_key(f)[:4], None
            acts, boards = collections.defaultdict(set), set()
            for e in load_game(f):
                if e.get("type") not in ("initial", "action"):
                    continue
                if e.get("type") == "action":
                    if prev is not None:
                        dec += 1
                        bk = (e.get("level"), prev)
                        known[min(len(acts[bk]), 5)] += 1
                        seen[bk in boards] += 1
                        cov[g]["tot"] += 1
                        cov[g]["rev"] += (bk in boards)
                        boards.add(bk)
                        acts[bk].add(str(e.get("action_display")))
                prev = h(e.get("board_ascii"))
    print("\nCOVERAGE -- a prediction that is reliable is not one that is available")
    print(f"  decisions with a prior board            {dec}")
    print(f"  taken from a board seen before          {seen[True]} = {pct(seen[True], dec):.1f}%")
    for k in sorted(known):
        lab = ">=5" if k >= 5 else str(k)
        print(f"    {lab:>3s} recorded actions from it: {known[k]:6d} = {pct(known[k], dec):5.1f}%")
    print(f"  exact (level, board, action) repeats    {tot['rep']}/7938 = "
          f"{pct(tot['rep'], 7938):.1f}%   (B19's separate argument, untouched by this fix)")
    print("\n  per game, >=100 decisions:")
    for g, c in sorted(cov.items(), key=lambda x: -x[1]["tot"]):
        if c["tot"] < 100:
            continue
        print(f"  {g:6s}{c['tot']:6d} decisions   board revisited {pct(c['rev'], c['tot']):5.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
