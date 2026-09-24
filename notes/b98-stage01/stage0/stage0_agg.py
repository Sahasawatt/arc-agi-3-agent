"""Aggregate the b98-stage0-judge workflow per the rule registered in LEDGER.md (Stage 0 for D).
usage: python stage0_agg.py <workflow-output.json>
"""
import collections, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
res = json.load(open(sys.argv[1], encoding="utf-8"))
res = res.get("result", res) if isinstance(res, dict) else res
items = {c["id"]: c for b in range(4) for c in json.load(open(HERE / f"stage0_batch{b}.json", encoding="utf-8"))}
votes = collections.defaultdict(dict)
for r in res:
    for l in r["labels"]:
        if l["id"] in items:
            votes[l["id"]][r["judge"]] = l
complete = lambda l: l["checkable"] and all(l["predicate"].get(k, "").strip() for k in ("action", "target", "effect"))
both = {i for i, v in votes.items() if len(v) == 2 and all(complete(x) for x in v.values())}
neg = [i for i, c in items.items() if c.get("neg_control")]
neg_ok = all(len(votes[i]) == 2 and not any(x["checkable"] for x in votes[i].values()) for i in neg)
games = {items[i]["game"] for i in both if items[i]["game"] != "CONTROL"}
dead = sum(items[i]["dead_time"] for i in both)
agree = sum(1 for v in votes.values() if len(v) == 2 and v[0]["checkable"] == v[1]["checkable"])
kinds = collections.Counter(v[0]["kind"] for i, v in votes.items() if i in both and 0 in v)
print(f"items {len(items)}; judged by both {sum(len(v) == 2 for v in votes.values())}; checkable-agreement {agree}")
print(f"checkable by BOTH with complete predicate: {len(both)} sentences ({dead} in dead time), kinds {dict(kinds)}")
print(f"games with >= 1: {len(games)}/25 -> {sorted(g[:4] for g in games)}")
print(f"negative controls rejected by both judges: {neg_ok}")
verdict = "VOID" if not neg_ok else ("PASS" if len(games) >= 12 else "FAIL")
print("STAGE 0 VERDICT:", verdict)
