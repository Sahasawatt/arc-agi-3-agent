"""level_loss_census.py — where does each game LOSE score, on one or more draws of one arm?

  python eval/level_loss_census.py <run_dir> [<run_dir> ...]      # each dir holds benchmark.json + score.json

The ARC-AGI-3 score (taaf/game.py `_compute_final_score`, mirroring arc_agi.scorecard v0.9.8) weights level k by k
(1-indexed), scores a cleared level min(115, (baseline/actions)^2 * 100), and caps the game at
sum(weights of scored levels) / sum(all weights) * 100. So a game's score splits cleanly into
  unreached  = 100 - cap                      (levels never cleared; weight grows with depth)
  eff_loss   = cap - score                    (cleared levels scoring under 100 -- the quadratic action cost)
and `next` = (lv+1)/sum(weights)*100 is what ONE more level would pay on that game.
Per draw it also reads the history: actions spent on the level never cleared (`burned`), seconds on it (`stuck`),
the dominant action id there and its share (a click-only stall is `ACTION6+xy` at >= 90%), seconds and generated
tokens per action there (a thinking-bound stall is > 200 s/action), and when each cleared level landed (`tclear`).
No LLM, no network: a pure read of the run's own artifacts. Written for B72 (the fast base, 2026-09-08).
"""
import collections, json, os, sys

WALL = 7920.0


def read(run_dir: str) -> dict:
    b = json.load(open(os.path.join(run_dir, "benchmark.json"), encoding="utf-8"))
    sc = json.load(open(os.path.join(run_dir, "score.json"), encoding="utf-8"))["games"]
    out = {}
    for r in b["game_runs"]:
        gid = r["game_id"]; g = gid.split("-")[0]
        apl, base, n, lv, hist = r["actions_per_level"], r["base_actions_per_level"], r["number_of_levels"], r["levels_completed"], r["history"]
        wsum = n * (n + 1) // 2
        cap = (lv * (lv + 1) // 2) / wsum * 100
        cum, tclear = 0, []
        for i in range(lv):
            cum += apl[i]
            tclear.append(round(hist[cum - 1]["wallclock_seconds"]))
        tail = hist[cum:]
        t0 = hist[cum - 1]["wallclock_seconds"] if cum else 0.0
        if tail:
            ids = collections.Counter(a["action"]["id"] + ("+xy" if a["action"].get("data") else "") for a in tail)
            top, cnt = ids.most_common(1)[0]
            span = tail[-1]["wallclock_seconds"] - t0
            dom = f"{top} {cnt / len(tail):.0%}"
            s_per = span / len(tail)
            tok = sum(a["generated_tokens"] for a in tail) / len(tail)
        else:
            dom, s_per, tok = "-", 0.0, 0.0
        out[g] = dict(n=n, lv=lv, score=sc[gid]["score"], cap=cap, unreached=100 - cap, eff_loss=cap - sc[gid]["score"],
                      next=(lv + 1) / wsum * 100 if lv < n else 0.0, burned=len(tail), stuck=round(WALL - (tclear[-1] if tclear else 0)),
                      dom=dom, s_per=s_per, tok=tok, tclear=tclear, actions=len(hist))
    return out


def main(argv):
    if not argv:
        print(__doc__); return 2
    draws = [read(d) for d in argv]
    games = sorted(draws[0])
    k = len(draws)
    print(f"| game | N | levels ({'/'.join(f'd{i+1}' for i in range(k))}) | score | unreached | eff-loss | next lvl pays | burned | stuck s | dominant action on the failed level | s/act | tok/act | tclear (last draw) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    tot_u = tot_e = tot_s = 0.0
    for g in games:
        rs = [d[g] for d in draws]
        u = sum(r["unreached"] for r in rs) / k; e = sum(r["eff_loss"] for r in rs) / k; s = sum(r["score"] for r in rs) / k
        tot_u += u; tot_e += e; tot_s += s
        last = rs[-1]
        print(f"| {g} | {rs[0]['n']} | {'/'.join(str(r['lv']) for r in rs)} | {'/'.join(f'{r['score']:.2f}' for r in rs)} | {u:.1f} | {e:.1f} | "
              f"{last['next']:.1f} | {'/'.join(str(r['burned']) for r in rs)} | {'/'.join(str(r['stuck']) for r in rs)} | "
              f"{' ; '.join(r['dom'] for r in rs)} | {'/'.join(f'{r['s_per']:.0f}' for r in rs)} | {'/'.join(f'{r['tok']:.0f}' for r in rs)} | {last['tclear']} |")
    print(f"\nmean score {tot_s / len(games):.2f}; mean loss per game: unreached {tot_u / len(games):.1f}, efficiency {tot_e / len(games):.1f} (of 100)")
    late = [(g, i + 1, t) for d in draws for g in games for i, t in enumerate(d[g]["tclear"]) if t >= WALL - 1900]
    print(f"level-clears in the last 1,900 s of the wall: {len(late)} of {sum(d[g]['lv'] for d in draws for g in games)} -> {late}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
