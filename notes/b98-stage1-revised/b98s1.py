"""B98 stage 1 on the REVISED bar -- extraction, predictor and scoring (stdlib only).

Implements notes/b98-stage1-revised/PREDICTIONS.md (registered 2026-09-27T16:49Z). The peer tooling it reuses is
imported unchanged from notes/b98-stage01/ (branch b98-stage01-artifacts @ 6400779): stage0_extract.py for the
sentence extractor, stage1/checker.py for action matching and per-transition verdicts.

One adaptation, stated because the registration says "exactly stage1/SPEC.md's definition": SPEC.md documents event
values as STRINGS ("True"/"False", "3"), and checker.parse_events compares against the string "True". The B81-chassis
primary run stores them as JSON bool/int, so that comparison is never true and the terminal-skip rule would silently
never fire. `transitions()` below implements the SAME definition with the value normalised (True or "True"); the
test file proves the peer parser misses the skip on this data and this one does not.

CLI:
  python b98s1.py extract <run-dir> <out.json>        # decisions + candidate/rule sentences per game (no compile)
  python b98s1.py filter-controls                      # the three registered rule-filter controls
  python b98s1.py score <extract.json> <compiled-dir> <out.json>
"""
import json
import math
import os
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PEER = HERE.parent / "b98-stage01"
sys.path.insert(0, str(PEER / "stage0"))
sys.path.insert(0, str(PEER / "stage1"))
import stage0_extract as s0  # noqa: E402  (unchanged peer extractor)
import checker  # noqa: E402  (unchanged peer checker)

CUES = ("always", "every time", "each time", "whenever", "any time", "causes", "makes", "moves by", "rule",
        "means that")
CAP_PER_GAME = 60
AVAIL_PASS, AVAIL_REFUTE, GAMES_PASS, ALPHA = 0.30, 0.12, 12, 0.05
COST_CEILING, NEAR_LINE = 10007, 5004
SEED_NULL, SEED_NULL2 = 20260927, 20260928
SPECIFIC = {"move", "recolor", "disappear"}  # appear / count_delta are specific only with a target.region


def truthy(v):
    return v is True or v == "True"


def is_specific(h):
    kind = h["effect"]["type"]
    if kind in SPECIFIC:
        return True
    return kind in ("appear", "count_delta") and h["target"].get("region") is not None


def turns_of(text):
    """stage0_extract.turns() applied to one transcript STRING (it takes a path); same split, same fields."""
    out, cur = [], None
    for b in s0.SPLIT.split(text):
        head = b.split("\n", 1)[0]
        if head == "[USER PROMPT]":
            m = s0.STATE.search(b)
            cur = {"level": int(m.group(2)) if m else None, "text": []}
            out.append(cur)
        elif cur is not None and head in ("[THINKING]", "[ASSISTANT]"):
            cur["text"].append(b.split("\n", 1)[1] if "\n" in b else "")
    return out


def is_rule(sentence):
    low = sentence.lower()
    return any(c in low for c in CUES)


# ---- v2 DRAFT (2026-09-28, NOT registered): v1 failed its control because the model states rules without cue
# words. v2 adds four grammatical markers of a GENERAL statement and one exclusion for plans / questions /
# hypotheticals. Drafted after reading the 10 judged B99 rules, so its figures on those 96 sentences are not evidence.
V2_PLAN = re.compile(r"\?|\b(what if|maybe|might|perhaps|let me|let's|i'll|i will|i need|i should|should i|"
                     r"i'm going|going to|try(?:ing)? to|need to|plan)\b", re.I)
V2_QUANT = re.compile(r"\b(each|every|per)\s+(press|click|step|move|action|tap|push|turn)\b", re.I)
V2_WHEN = re.compile(r"(?:^|[.;:]\s*|\s)when\b", re.I)
V2_HABIT = re.compile(r"\b(UP|DOWN|LEFT|RIGHT|SPACE|ACTION[1-7]|click(?:ing|s)?|press(?:ing|es)?)\b[^.;:]{0,40}?"
                      r"\b(moves|toggles|shifts|rotates|removes|fills|flips|swaps|changes|turns|pushes|slides|"
                      r"recolou?rs|expands|shrinks|grows|extends|increases|decreases|mirrors|cycles|advances)\b", re.I)
V2_STEP = re.compile(r"\b\d+[- ]?(?:cell|col|column|row|unit)s?[- ]steps?\b|\bin\s+\d+\S*\s+steps\b|"
                     r"\bby\s+[+-]?\d+\b", re.I)


def is_rule_v2(sentence):
    if V2_PLAN.search(sentence):
        return False
    return bool(is_rule(sentence) or V2_QUANT.search(sentence) or V2_WHEN.search(sentence)
                or V2_HABIT.search(sentence) or V2_STEP.search(sentence))


def cap_even(items, cap=CAP_PER_GAME):
    """Even spacing in file order; deterministic, chosen before any effect is seen."""
    n = len(items)
    if n <= cap:
        return list(items)
    return [items[(i * n) // cap] for i in range(cap)]


def read_game(path):
    """File-ordered rows of one game: ('decision', ...) for every scored transition and ('sentence', ...) for
    every deduplicated stage-0 candidate, each with its file row index."""
    rows, seen_keys, seen_text = [], set(), set()
    prev = None          # previous initial/action event (SPEC's "preceding" event)
    last_after = None    # after-board of the last action row (board the model was looking at)
    game = os.path.basename(path).split("_p0_")[0]
    with open(path, encoding="utf-8") as fh:
        for idx, line in enumerate(fh):
            e = json.loads(line)
            t = e.get("type")
            if t == "initial":
                prev, last_after = e, e.get("board_ascii")
                continue
            if t == "action":
                if prev is not None:
                    before, after = prev.get("board_ascii"), e.get("board_ascii")
                    terminal = truthy(prev.get("level_completed")) or truthy(prev.get("game_over"))
                    if before is not None and after is not None and not terminal:
                        level = int(prev["level"])
                        key = (level, before, e.get("action_display"))
                        rows.append({"kind": "decision", "row": idx, "level": level, "held_out": key not in seen_keys,
                                     "action_name": e.get("action_name"), "action_display": e.get("action_display"),
                                     "before": before, "after": after, "board_changed": e.get("board_changed")})
                        seen_keys.add(key)
                prev, last_after = e, e.get("board_ascii")
                continue
            if t == "analysis":
                for turn in turns_of(e.get("transcript") or ""):
                    if not turn["level"]:
                        continue
                    for s in s0.sentences("\n".join(turn["text"])):
                        if s in seen_text:
                            continue
                        seen_text.add(s)
                        rows.append({"kind": "sentence", "row": idx, "level": turn["level"], "text": s,
                                     "rule": is_rule(s), "board": last_after})
    return game, rows


def extract(run_dir, out_path):
    art = Path(run_dir) / "artifacts"
    games = {}
    for f in sorted(art.glob("*_p0_events.jsonl")):
        game, rows = read_game(str(f))
        sents = [r for r in rows if r["kind"] == "sentence"]
        rules = [r for r in sents if r["rule"]]
        chosen = cap_even(rules)
        for k, r in enumerate(chosen):
            r["id"] = f"{game[:4]}-{k:03d}"
            r["compile"] = True
        games[game] = {"rows": rows, "n_candidates": len(sents), "n_rules": len(rules), "n_compile": len(chosen)}
    json.dump({"run": str(run_dir), "games": games}, open(out_path, "w", encoding="utf-8"))
    tot = lambda k: sum(g[k] for g in games.values())
    dec = [r for g in games.values() for r in g["rows"] if r["kind"] == "decision"]
    ho = sum(r["held_out"] for r in dec)
    print(f"games {len(games)}; decisions {len(dec)}, held-out {ho}, excluded repeats {len(dec) - ho} "
          f"({(len(dec) - ho) / max(len(dec), 1):.1%}); candidates {tot('n_candidates')}, rules {tot('n_rules')}, "
          f"to compile {tot('n_compile')}")
    return games


# ---------------------------------------------------------------- filter controls (registered, run first)
def filter_controls():
    obs = "clicking (23,61) made M(23,55) disappear"
    syn = "pressing LEFT always moves the yellow block 3 cells left"
    items = [c for b in range(4) for c in json.load(open(PEER / "stage0" / f"stage0_batch{b}.json", encoding="utf-8"))
             if not c.get("neg_control")]
    share = sum(is_rule(c["text"]) for c in items) / len(items)
    ref = 10 / 96
    ok = (not is_rule(obs)) and is_rule(syn) and len(items) == 96 and ref / 2 <= share <= ref * 2
    print(f"observation rejected: {not is_rule(obs)}; synthetic rule passed: {is_rule(syn)}; "
          f"rule share on the {len(items)} judged B99 sentences {share:.3f} (band {ref / 2:.3f}..{ref * 2:.3f})")
    print("FILTER CONTROLS:", "PASS" if ok else "FAIL -> VOID-as-instrument")
    return ok


def sample_control(run_dir, out_path, seed=20260929, per_game=4):
    """Rev-5 fresh control: `per_game` extractor candidates per game (seeded shuffle, sorted game order) plus the
    3 stage-0 negative controls, in one seeded order. Frozen as a file before any judging."""
    rng = random.Random(seed)
    items = []
    for f in sorted((Path(run_dir) / "artifacts").glob("*_p0_events.jsonl")):
        game, rows = read_game(str(f))
        sents = [r for r in rows if r["kind"] == "sentence"]
        rng.shuffle(sents)
        for r in sents[:per_game]:
            items.append({"game": game, "level": r["level"], "row": r["row"], "text": r["text"]})
    for s in s0.CONTROLS_NEG:
        items.append({"game": "CONTROL", "level": 0, "row": -1, "text": s, "neg_control": True})
    rng.shuffle(items)
    for i, c in enumerate(items):
        c["id"] = f"c{i:03d}"
    json.dump(items, open(out_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"control sample: {len(items)} items ({sum(1 for c in items if c.get('neg_control'))} negatives) -> {out_path}")
    return items


# ---------------------------------------------------------------- predictor + scoring
def as_transition(d):
    return (d["before"].splitlines(), d["after"].splitlines(),
            {"action_name": d["action_name"], "action_display": d["action_display"]}, d["level"])


def emits(h, d, t=None):
    """A SPECIFIC hypothesis emits on decision d iff its action matches (SPEC rules) and its verdict would not be
    `na` -- decided from the BEFORE board alone (every `na` condition in SPEC depends only on the before board)."""
    if not is_specific(h):
        return False
    t = t or as_transition(d)
    return checker.match(h, t) and checker.verdict_one(h, t[0], t[0]) != "na"


def mcnemar_one_sided(b, c):
    """Exact one-sided McNemar: P(X >= b), X ~ Binomial(b + c, 1/2)."""
    n = b + c
    if n == 0:
        return 1.0
    return sum(math.comb(n, k) for k in range(b, n + 1)) / 2 ** n


def score(extract_path, compiled_dir, out_path=None):
    ext = json.load(open(extract_path, encoding="utf-8"))
    comp = Path(compiled_dir)
    hyps, generic, invalid, none, cost_calls = {}, 0, 0, 0, []
    for game, g in ext["games"].items():
        for r in g["rows"]:
            if r.get("compile"):
                f = comp / f"{r['id']}.json"
                if not f.exists():
                    raise SystemExit(f"missing compile output {f}")
                c = json.load(open(f, encoding="utf-8"))
                cost_calls.append(c.get("generated_tokens"))
                h = c.get("hypothesis")
                if h is None:
                    none += c.get("status") == "NONE"
                    invalid += c.get("status") == "INVALID"
                    continue
                h = dict(h, id=r["id"], game=game, level=r["level"])
                if is_specific(h):
                    hyps[r["id"]] = (r["row"], h)
                else:
                    generic += 1
    pool = [h for _, h in hyps.values()]

    held, emit_rows, games_emit, bc_true = 0, [], set(), 0
    for game, g in ext["games"].items():
        active = [(hyps[r["id"]][0], hyps[r["id"]][1]) for r in g["rows"] if r.get("id") in hyps]
        seen_keys = set()
        for d in (r for r in g["rows"] if r["kind"] == "decision"):
            key = (d["level"], d["before"], d["action_display"])
            if not d["held_out"]:
                seen_keys.add(key)
                continue
            if key in seen_keys:
                raise SystemExit(f"VOID: clause (i) broken in {game} at row {d['row']}")
            seen_keys.add(key)
            held += 1
            t = as_transition(d)
            cands = [(row, h) for row, h in active if row < d["row"] and h["level"] == d["level"] and emits(h, d, t)]
            if not cands:
                continue
            _, h = max(cands, key=lambda x: x[0])  # most recent sentence wins; file order is total
            outcome = checker.verdict_one(h, t[0], t[1])
            emit_rows.append({"game": game, "row": d["row"], "id": h["id"], "right": outcome == "support", "t": t,
                              "board_changed": d["board_changed"]})
            games_emit.add(game)
            bc_true += d["board_changed"] is True

    def draw(seed, oracle=False):
        rng, picks = random.Random(seed), []
        for er in emit_rows:
            others = [h for h in pool if h["game"] != er["game"] and checker.match(h, er["t"])
                      and checker.verdict_one(h, er["t"][0], er["t"][0]) != "na"]
            if not others:
                picks.append(None)
                continue
            if oracle:
                sup = [h for h in others if checker.verdict_one(h, er["t"][0], er["t"][1]) == "support"]
                picks.append(bool(sup))
            else:
                h = others[rng.randrange(len(others))]
                picks.append(checker.verdict_one(h, er["t"][0], er["t"][1]) == "support")
        return picks

    null1, null2, orac = draw(SEED_NULL), draw(SEED_NULL2), draw(SEED_NULL, oracle=True)

    def test(a, b):
        keep = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
        bb = sum(1 for x, y in keep if x and not y)
        cc = sum(1 for x, y in keep if y and not x)
        return {"rows": len(keep), "b": bb, "c": cc, "p": mcnemar_one_sided(bb, cc)}

    pred = [er["right"] for er in emit_rows]
    kept_pred = [p if n is not None else None for p, n in zip(pred, null1)]
    t_iii = test(kept_pred, null1)
    t_neg = test(null2, null1)
    t_pos = test(orac, null1)
    dropped = sum(1 for n in null1 if n is None)

    avail = len(emit_rows) / held if held else 0.0
    rules_per_game = [g["n_rules"] for g in ext["games"].values()]
    toks = [x for x in cost_calls if isinstance(x, (int, float))]
    mean_tok = sum(toks) / len(toks) if toks else float("nan")
    proj = sorted(n * mean_tok for n in rules_per_game)
    med = (proj[len(proj) // 2] + proj[(len(proj) - 1) // 2]) / 2 if proj else float("nan")

    res = {"held_out": held, "emitting": len(emit_rows), "availability": avail, "games_emitting": len(games_emit),
           "iii": t_iii, "iii_dropped_no_null": dropped, "teeth_negative": t_neg, "teeth_positive": t_pos,
           "specific_hyps": len(pool), "generic_hyps": generic, "none": none, "invalid": invalid,
           "compile_calls": len(cost_calls), "mean_generated_tokens_per_call": mean_tok,
           "projected_cost_median_per_game": med,
           "board_changed_true_share_on_emitting_rows": bc_true / len(emit_rows) if emit_rows else None}
    res["verdict"] = verdict(res)
    if out_path:
        json.dump(res, open(out_path, "w", encoding="utf-8"), indent=1)
    return res


def verdict(r, filter_ok=True, clause_i_ok=True):
    """Primary-run partition rows 1-3 (rows 4-6 need the replication run and the cost figure)."""
    if not filter_ok or not clause_i_ok or r["teeth_negative"]["p"] < ALPHA or r["teeth_positive"]["p"] >= ALPHA:
        return "VOID"
    if r["availability"] <= AVAIL_REFUTE:
        return "REFUTED-PREMISE"
    if r["availability"] < AVAIL_PASS or r["iii"]["p"] >= ALPHA or r["games_emitting"] < GAMES_PASS:
        return "FAIL"
    return "PASSES-(i)-(iv)"


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "extract":
        extract(sys.argv[2], sys.argv[3])
    elif cmd == "sample-control":
        sample_control(sys.argv[2], sys.argv[3])
    elif cmd == "filter-controls":
        sys.exit(0 if filter_controls() else 1)
    elif cmd == "score":
        print(json.dumps(score(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None), indent=1,
                         default=str))
    else:
        print(__doc__)
        sys.exit(2)
