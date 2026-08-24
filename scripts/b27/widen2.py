"""R29 §2 widened: does 'the transition model is what is wrong' survive the corpus?

§1 and §3 were widened to five runs; §2 never was, and R29 says B29's justification
rests on §2 alone. §3 flipped sign under exactly this widening, so §2 is the one
remaining claim in R29 standing on three hand-picked games.

Unit: the stuck/cleared pair on the same (game, level), same as §1 — 115 pairs.
Test: paired sign-flip permutation, two-sided, 100k draws, fixed seed.
Every signal ships with a positive control (§1's own turn-count, known 97/115 p=1.9e-16)
and a negative control (game-name hash parity, must be null).
"""
import random, difflib, statistics as st
from attempts import load_all, pairs
from wm import carried

SEED, NPERM = 20260824, 100_000

def blocks(a):
    return [b for b in (carried(t) for t in a["turns"]) if b]

def m_action_model(a):   return float(any("Action model:" in b for b in blocks(a)))
def m_open_q(a):
    bs = blocks(a)
    return sum("Open questions:" in b for b in bs) / len(bs) if bs else 0.0
def m_stasis(a):
    bs = blocks(a)
    if len(bs) < 2: return None
    return st.mean(difflib.SequenceMatcher(None, x, y).ratio() for x, y in zip(bs, bs[1:]))
def m_wm_present(a):
    return len(blocks(a)) / len(a["turns"]) if a["turns"] else 0.0
def c_pos(a):            return float(len(a["turns"]))          # §1's signal

_noise, _rnd = {}, random.Random(99)
def c_neg(a):
    """Negative control: random per attempt. Null, but WITH variance -- a constant
    yields zero non-zero diffs and so cannot show the test declining to fire.
    One draw of this is itself noise (two seeds gave p=0.43 and p=0.088); the
    positive control is what carries the table."""
    return _noise.setdefault(id(a), _rnd.random())

def perm(diffs):
    """Paired sign-flip permutation on non-zero diffs; two-sided."""
    d = [x for x in diffs if x != 0]
    if not d: return float("nan"), 0
    obs = sum(d) / len(d)
    rnd = random.Random(SEED); hits = 0
    for _ in range(NPERM):
        s = sum(x if rnd.random() < .5 else -x for x in d) / len(d)
        if abs(s) >= abs(obs) - 1e-12: hits += 1
    return (hits + 1) / (NPERM + 1), len(d)

if __name__ == "__main__":
    ALL = load_all(); P = pairs(ALL)
    print(f"pairs = {len(P)}\n")
    print(f"{'signal':22s} {'stuck':>8s} {'cleared':>8s} {'stuck>cl':>9s} {'n≠0':>5s} {'p':>9s}")
    for name, fn in [("CONTROL+ turns/attempt", c_pos),
                     ("CONTROL- random/attempt", c_neg),
                     ("has Action model:", m_action_model),
                     ("Open questions: rate", m_open_q),
                     ("carried-WM present", m_wm_present),
                     ("stasis (consec sim)", m_stasis)]:
        rows = [(fn(sa), fn(ca)) for k, sr, sa, cr, ca in P]
        rows = [(s, c) for s, c in rows if s is not None and c is not None]
        d = [s - c for s, c in rows]
        p, n = perm(d)
        gt = sum(1 for s, c in rows if s > c)
        print(f"{name:22s} {st.mean(x for x,_ in rows):8.3f} {st.mean(y for _,y in rows):8.3f}"
              f" {gt:4d}/{len(rows):<4d} {n:5d} {p:9.2e}")
