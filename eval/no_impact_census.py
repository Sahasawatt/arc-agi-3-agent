"""no_impact_census.py -- L1 pre-read (B80): how many of our actions change ONLY the HUD / counter band?

  python eval/no_impact_census.py <events_dir> [<events_dir> ...]      # dirs holding <game>_p0_events.jsonl

sonpham-org/arc-3 reports +55% levels at equal action budget from refusing to count an action whose only board change is
the deterministic HUD / moves-counter band ("no-impact detection"). Before building that on our base, measure whether our
runs even contain such actions. Per game, from the harness's own per-action boards:
  - HUD mask = ROWS touched by >= HUD_FRAC of the board-changing actions (a counter/timer strip ticks on every action,
    but at a DIFFERENT cell each time -- a per-cell frequency misses it entirely; measured on tn36 row 1 and sp80 row 0,
    100% of actions, top cell 14%). Derived per game, never assumed; capped at MASK_ROWS rows.
  - an action is NO-IMPACT when it changed the board (board_changed) but every changed cell lies inside the HUD mask.
  - reported per game: actions, board-changing, no-impact (count, share), no-impact on the LAST (unfinished) level, and
    the mask rows; more than MASK_ROWS rows is refused as "no HUD found" (then no-impact = 0 by construction).
Controls: games whose transcripts name a timer/moves strip (tn36 row 63, tr87 row 63) must show a non-empty mask; a game
with board_changed=False on every action must show 0 no-impact (nothing to classify).
"""
import glob, json, os, sys

sys.stdout.reconfigure(encoding="utf-8")
HUD_FRAC = 0.9      # a ROW is HUD if it is touched on >= 90% of board-changing actions (a counter ticks every action)
MASK_ROWS = 4       # more than 4 such rows is a playfield that redraws every action, not a HUD -> refused


def read(path):
    prev = None; rows = []
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        if d.get("type") not in ("initial", "action"):
            continue
        b = d.get("board")
        if b is None:
            continue
        if d["type"] == "action":
            changed = set()
            if prev is not None and len(prev) == len(b):
                for r in range(len(b)):
                    pr, br = prev[r], b[r]
                    if pr != br:
                        for c in range(len(br)):
                            if pr[c] != br[c]:
                                changed.add((r, c))
            rows.append({"level": int(d.get("level", 0)), "changed": changed,
                         "flag": d.get("board_changed") in (True, "True"), "num": int(d.get("action_num", 0))})
        prev = b
    return rows


def census(rows):
    chg = [r for r in rows if r["changed"]]
    n_chg = len(chg)
    rowf = {}
    for r in chg:
        for row in {c[0] for c in r["changed"]}:
            rowf[row] = rowf.get(row, 0) + 1
    mask = {row for row, k in rowf.items() if n_chg and k / n_chg >= HUD_FRAC}
    refused = len(mask) > MASK_ROWS
    if refused:
        mask = set()
    last_lv = max((r["level"] for r in rows), default=0)
    noimp = [r for r in chg if mask and {c[0] for c in r["changed"]} <= mask]
    noimp_last = [r for r in noimp if r["level"] == last_lv]
    flag_mismatch = sum(1 for r in rows if bool(r["changed"]) != r["flag"])
    return dict(actions=len(rows), changing=n_chg, mask=len(mask), refused=refused, noimp=len(noimp),
                noimp_last=len(noimp_last), last_lv=last_lv, flag_mismatch=flag_mismatch,
                mask_rows=sorted(mask))


def main(argv):
    if not argv:
        print(__doc__); return 2
    tot = dict(actions=0, changing=0, noimp=0, games_with_mask=0)
    print(f"{'game':5} {'actions':>7} {'changing':>8} {'mask':>5} {'noimp':>6} {'share':>6} {'noimp@last':>10} {'mask rows'}")
    for d in argv:
        for p in sorted(glob.glob(os.path.join(d, "*_p0_events.jsonl"))):
            g = os.path.basename(p)[:4]
            c = census(read(p))
            share = c["noimp"] / c["changing"] if c["changing"] else 0.0
            tot["actions"] += c["actions"]; tot["changing"] += c["changing"]; tot["noimp"] += c["noimp"]
            tot["games_with_mask"] += 1 if c["mask"] else 0
            note = " REFUSED(mask>cap)" if c["refused"] else ""
            fm = f" flag-mismatch={c['flag_mismatch']}" if c["flag_mismatch"] else ""
            print(f"{g:5} {c['actions']:>7} {c['changing']:>8} {c['mask']:>5} {c['noimp']:>6} {share:>6.1%} {c['noimp_last']:>10} {c['mask_rows']}{note}{fm}")
    print(f"\nTOTAL actions {tot['actions']}, board-changing {tot['changing']}, no-impact {tot['noimp']} "
          f"({tot['noimp'] / max(1, tot['changing']):.1%} of changing), games with a HUD mask {tot['games_with_mask']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
