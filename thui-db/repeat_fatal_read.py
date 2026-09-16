"""repeat_fatal_read.py -- the death-blacklist oracle, read from a run's event files (0 GPU).

For every game, lives are cut at RESET rows (the solver's auto-RESET after a death, or the agent's own). For each level:
  ACTION budget  -- >= 3 death-ended lives whose action totals agree within +-1 (sp80 L1 = 30, tn36 = 61, sp80 L2 = 45).
  TYPE budget    -- >= 3 death-ended lives ending on type T with the same count M >= 2 of T in >= 2/3 of them (sp80 L2 = 5 SPACE).
  A death on a budget level, or on the M-th T of a type-budget level, is a BUDGET death: the last action is the N-th move, not a
  killer, so it is neither a repeat nor blacklist input. Among the remaining deaths, a REPEAT is one whose action had already
  ended the game on that level (the quantity the graft's fatal list exists to reduce). Same rules as the graft's own
  _thui_db_budgets, so the oracle and the kernel agree on what a budget is.

    python thui-db/repeat_fatal_read.py <run-dir> [<run-dir> ...]      # each dir holds artifacts/*_p0_events.jsonl
    python thui-db/repeat_fatal_read.py --games bp35,sp80,tn36 <dirs>  # smoke subset
"""
import collections
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")


def kind(a):
    a = str(a or "").strip()
    return "MOUSE" if a.startswith("MOUSE") else a


def budgets(lives):
    out = {"actions": None, "types": {}}
    if len(lives) >= 3:
        totals = sorted(l["total"] for l in lives)
        if totals[-1] - totals[0] <= 1:
            out["actions"] = totals[len(totals) // 2]
    by_last = collections.defaultdict(list)
    for l in lives:
        by_last[l["last"]].append(l["counts"].get(l["last"], 0))
    for t, cs in by_last.items():
        if t and len(cs) >= 3:
            mode = max(set(cs), key=cs.count)
            if mode >= 2 and cs.count(mode) >= 3 and cs.count(mode) * 3 >= len(cs) * 2:
                out["types"][t] = mode
    return out


def read_run(run_dir, games=None):
    rows_out = []
    for path in sorted(glob.glob(os.path.join(run_dir, "artifacts", "*_p0_events.jsonl"))):
        g = os.path.basename(path)[:4]
        if games and g not in games:
            continue
        acts = [json.loads(l) for l in open(path, encoding="utf-8")]
        acts = [r for r in acts if r.get("type") == "action"]
        # pass 1: lives that ended in death, per level
        lives = collections.defaultdict(list)
        deaths_seq = []            # (level, action_display, life snapshot) in order
        life = {"total": 0, "counts": collections.Counter(), "level": None}
        for r in acts:
            k = kind(r.get("action_display") or r.get("action_name"))
            if k == "RESET":
                life = {"total": 0, "counts": collections.Counter(), "level": None}
                continue
            level = r.get("level")
            if life["level"] is not None and level != life["level"]:
                life = {"total": 0, "counts": collections.Counter(), "level": None}
            life["level"] = level
            life["total"] += 1; life["counts"][k] += 1
            if r.get("game_over") in (True, "True"):
                snap = {"total": life["total"], "counts": dict(life["counts"]), "last": k}
                lives[level].append(snap)
                deaths_seq.append((level, str(r.get("action_display") or r.get("action_name")), snap))
                life = {"total": 0, "counts": collections.Counter(), "level": None}
        bud = {level: budgets(ls) for level, ls in lives.items()}
        # pass 2: classify deaths
        seen = collections.defaultdict(collections.Counter)
        deaths = repeats = budget_deaths = 0
        detail = collections.Counter()
        for level, action, snap in deaths_seq:
            deaths += 1
            b = bud[level]
            is_budget = b["actions"] is not None or (snap["last"] in b["types"] and snap["counts"].get(snap["last"]) == b["types"][snap["last"]])
            if is_budget:
                budget_deaths += 1
                continue
            if seen[level][action]:
                repeats += 1
                detail[(level, action)] += 1
            seen[level][action] += 1
        shown = {level: b for level, b in bud.items() if b["actions"] is not None or b["types"]}
        rows_out.append((g, deaths, repeats, dict(detail), budget_deaths, shown))
    return rows_out


def main(argv):
    games = None
    if argv and argv[0] == "--games":
        games = set(argv[1].split(",")); argv = argv[2:]
    if not argv:
        print(__doc__); return 2
    for d in argv:
        rows = read_run(d, games)
        if not rows:
            print(f"{os.path.basename(d.rstrip('/\\\\'))}: no event files"); continue
        deaths = sum(r[1] for r in rows); repeats = sum(r[2] for r in rows); bud = sum(r[4] for r in rows)
        eligible = sum(max(0, (r[1] - r[4]) - 1) for r in rows)
        print(f"{os.path.basename(d.rstrip('/\\\\')):40s} games={len(rows)} deaths={deaths} budget-deaths={bud} "
              f"repeat-fatal={repeats} (of {eligible} non-first non-budget deaths = {repeats / eligible if eligible else 0:.0%})")
        for g, dth, rep, det, bd, budget in rows:
            if rep or budget:
                parts = []
                if budget:
                    parts.append("budget " + ", ".join(
                        f"L{lv} " + " ".join(([f"{b['actions']} actions/life"] if b["actions"] is not None else []) +
                                             [f"{m} {t}/life" for t, m in sorted(b["types"].items())])
                        for lv, b in sorted(budget.items())) + f" ({bd} deaths)")
                if rep:
                    parts.append(f"repeats {rep}: " + ", ".join(f"L{lv} {a} x{n}" for (lv, a), n in sorted(det.items(), key=lambda kv: -kv[1])))
                print(f"    {g}: deaths {dth}; " + "; ".join(parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
