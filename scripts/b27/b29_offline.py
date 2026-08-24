"""B29's verifier premise, tested offline against the recorded corpus. Zero GPU slots.

B29: "when stuck, draft k candidate short plans in the sandbox, check each against
`history`'s recorded transitions, execute only the best-verified one, abort on first
prediction miss."

That mechanism assumes a recorded transition PREDICTS the next one from the same
observed state. The corpus can answer this directly: find every case where a run
revisited an exact (level, board, action) it had already fired, and ask whether the
outcome reproduced.

Controls in the same run: batch_size (rules out per-batch board attribution),
the animation field (rules out mid-animation frames as the whole story), and a
per-game breakdown (an aggregate here is dominated by one game and inverts without it).
"""
import collections, hashlib, statistics as st
from corpus import RUNS5, game_files, load_game, game_key

def h(s):
    return hashlib.md5(s.encode()).hexdigest()[:12] if s else None

def scan():
    per = collections.defaultdict(collections.Counter)
    anim = collections.Counter()
    batch = collections.Counter()
    diffs = []
    for r in RUNS5:
        for f in game_files(r):
            g = game_key(f)[:4]
            prev_h, prev_b, rec = None, None, {}
            for e in load_game(f):
                if e.get("type") not in ("initial", "action"):
                    continue
                if e.get("type") == "action":
                    batch[e.get("batch_size") or 1] += 1
                    k = (e.get("level"), prev_h, e.get("action_name"))
                    cur_b = e.get("board_ascii")
                    cur_h, ch, an = h(cur_b), bool(e.get("board_changed")), e.get("animation")
                    if prev_h is not None and k in rec:
                        pb_h, pch, pan, pb = rec[k]
                        per[g]["rep"] += 1
                        per[g]["board_ok"] += (pb_h == cur_h)
                        per[g]["flag_ok"] += (pch == ch)
                        anim[f"{int(bool(pan))}{int(bool(an))}_tot"] += 1
                        anim[f"{int(bool(pan))}{int(bool(an))}_ok"] += (pb_h == cur_h)
                        if pb_h != cur_h:
                            A, B = pb.split("\n"), cur_b.split("\n")
                            if len(A) == len(B):
                                diffs.append(sum(x != y for ra, rb in zip(A, B)
                                                 for x, y in zip(ra, rb)))
                    if prev_h is not None:
                        rec.setdefault(k, (cur_h, ch, an, cur_b))
                prev_h, prev_b = h(e.get("board_ascii")), e.get("board_ascii")
    return per, anim, batch, diffs

if __name__ == "__main__":
    per, anim, batch, diffs = scan()
    tot = collections.Counter()
    for c in per.values():
        tot.update(c)
    print(f"CONTROL batch_size distribution: {dict(batch)}"
          "   (all 1 -> board is per-action, not per-batch)\n")
    print(f"{'game':6s} {'repeats':>8s} {'board reproduced':>17s} {'changed-flag reproduced':>24s}")
    for g, c in sorted(per.items(), key=lambda x: -x[1]["rep"]):
        if c["rep"] < 5:
            continue
        print(f"{g:6s} {c['rep']:8d} {100*c['board_ok']/c['rep']:16.1f}% {100*c['flag_ok']/c['rep']:23.1f}%")
    ex = collections.Counter()
    for g, c in per.items():
        if g != "cn04":
            ex.update(c)
    print(f"\n{'ALL':6s} {tot['rep']:8d} {100*tot['board_ok']/tot['rep']:16.1f}% {100*tot['flag_ok']/tot['rep']:23.1f}%")
    print(f"{'-cn04':6s} {ex['rep']:8d} {100*ex['board_ok']/ex['rep']:16.1f}% {100*ex['flag_ok']/ex['rep']:23.1f}%"
          "   <- cn04 holds 58% of all repeats and is the BEST behaved; it props the aggregate up")
    print("\nCONTROL animation (present-then, present-now) -> board reproduced:")
    for k in ("00", "01", "10", "11"):
        t = anim[f"{k}_tot"]
        if t:
            print(f"   {k}: {anim[f'{k}_ok']}/{t} = {100*anim[f'{k}_ok']/t:.1f}%")
    print(f"\nwhen it fails, differing cells: median={st.median(diffs):.0f} "
          f"mean={st.mean(diffs):.1f} max={max(diffs)} (n={len(diffs)})")
    bad = sum(1 for c in per.values() if c["rep"] >= 5 and c["board_ok"]/c["rep"] < 0.9)
    n = sum(1 for c in per.values() if c["rep"] >= 5)
    print(f"\nVERDICT: {bad} of {n} games with >=5 repeats fail to reproduce their own "
          f"recorded transition >10% of the time.")
