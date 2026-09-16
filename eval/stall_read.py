"""stall_read.py — on the level a game never cleared, what did the agent actually do? (B73 / B74)

  python eval/stall_read.py <events_dir> [game ...]        # <run>/diag/artifacts holding *_p0_events.jsonl

Reads the harness's own per-game events (`type=action`: level, action_display, board_changed, level_completed;
`type=analysis`: the analyzer turn's transcript). For the LAST level the game reached it prints: actions and analysis
turns on it, the action mix, how many actions changed the board, distinct click cells and the most-repeated cell, the
valid-action set the prompt offered on that level and which of those were NEVER tried, and the agent's last stated
world model there. The valid set is what separates "never tries a non-click action" (action-space) from "clicks the
wrong place" (perception/plan): a game whose only valid action is MOUSE cannot be the former.
"""
import collections, glob, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")


def read(path):
    acts, ana = [], []
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        if d.get("type") == "action":
            acts.append(d)
        elif d.get("type") == "analysis":
            ana.append(d)
    return acts, ana


def main(argv):
    if not argv:
        print(__doc__); return 2
    d, only = argv[0], set(argv[1:])
    for p in sorted(glob.glob(os.path.join(d, "*_p0_events.jsonl"))):
        g = os.path.basename(p)[:4]
        if only and g not in only:
            continue
        acts, ana = read(p)
        last_lv = max(int(a["level"]) for a in acts) if acts else 1
        # a level_completed event already carries the NEXT level number, so the level cleared is one less
        cleared = [int(a["level"]) - 1 for a in acts if a.get("level_completed") in (True, "True")]
        top_cleared = max(cleared) if cleared else 0
        lv = last_lv  # the level the run ended on
        tail = [a for a in acts if int(a["level"]) == lv]
        turns = [a for a in ana if int(a["level"]) == lv]
        mix = collections.Counter(re.sub(r"\(.*\)", "", a["action_display"]) for a in tail)
        changed = sum(1 for a in tail if a.get("board_changed") in (True, "True"))
        clicks = collections.Counter(a["action_display"] for a in tail if a["action_display"].startswith("MOUSE"))
        valid = set()
        for t in turns:
            m = re.search(r"Valid actions right now: ([^\n]+)\.", t["transcript"])
            if m:
                valid |= {v.strip() for v in m.group(1).split(",")}
        tried = {re.sub(r"\(.*\)", "", a["action_display"]) for a in tail}
        untried = sorted(valid - tried)
        wm = ""
        for t in reversed(turns):
            j = t["transcript"].find("[ASSISTANT]")
            if j >= 0:
                wm = t["transcript"][j + 11:j + 700].strip().replace("\n", " | ")
                if wm:
                    break
        ended = "level " + str(lv) + (" (cleared it, ran out of wall)" if top_cleared >= lv else "")
        topc = clicks.most_common(1)[0] if clicks else ("-", 0)
        print(f"\n### {g}  ended on {ended}; cleared {top_cleared}; {len(tail)} actions / {len(turns)} turns on it; board changed {changed}/{len(tail)}")
        print(f"mix: {dict(mix.most_common(6))} | distinct click cells {len(clicks)}, top {topc[0]} x{topc[1]}")
        print(f"valid on this level: {sorted(valid)} | NEVER tried: {untried}")
        print(f"last world model: {wm[:600]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
