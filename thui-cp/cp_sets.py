"""Pick the thui-cp game sets from round 44's random-agent results (testbed/rand200.jsonl — OUTPUT rows, no game source
is read). Pool = loads without error, random 3x200 never clears L1, > 3 distinct frames, and not one of the three
QUARANTINED official games (notes QUARANTINE 2026-09-24). Writes cp_sets.json. usage: python cp_sets.py"""
import json, random
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAND = HERE.parent / "testbed" / "rand200.jsonl"
QUARANTINE = ("ft09", "ls20", "vc33")
SEED = 20260925
N_SET = 25


def main():
    rows = [json.loads(line) for line in open(RAND, encoding="utf-8")]
    pool = sorted(r["game"] for r in rows if r["err"] is None and r["l1_clears"] == 0 and r["distinct_frames"] > 3
                  and r["game"].split("-")[0] not in QUARANTINE)
    assert len(pool) == 139, f"pool {len(pool)} != 139 (round 44 / QUARANTINE note)"
    assert all(g.count("-") == 1 for g in pool), "a game id with more than one '-' breaks the name/version split"
    rng = random.Random(SEED)
    order = pool[:]
    rng.shuffle(order)
    a, b = sorted(order[:N_SET]), sorted(order[N_SET:2 * N_SET])
    assert not set(a) & set(b)
    levels = {r["game"]: r.get("n_levels") for r in rows}
    out = {"seed": SEED, "source": "testbed/rand200.jsonl (round 44)", "pool": pool, "A": a, "B": b, "smoke": a[:3],
           "n_levels": {g: levels[g] for g in a + b}}
    json.dump(out, open(HERE / "cp_sets.json", "w", encoding="utf-8"), indent=1)
    for k in ("A", "B"):
        from collections import Counter
        print(k, len(out[k]), "levels", dict(Counter(levels[g] for g in out[k])), "sum", sum(levels[g] for g in out[k]))
    print("smoke", out["smoke"])


if __name__ == "__main__":
    main()
