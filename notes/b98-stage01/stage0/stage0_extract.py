"""B98 stage 0 (0 GPU): does B99's run contain transition hypotheses a harness could compile and check?

Extraction is recall-oriented and mechanical: a sentence (split on newlines and ". ") from a [THINKING] or [ASSISTANT]
block that names an action AND an effect verb. Each candidate keeps its game, level, turn index and whether the turn
lies in the game's dead time (after its last level clear). Judges (workflow) decide which are checkable.
Also checks data availability: every game's events.jsonl must carry per-action boards (before/after = consecutive).
Positive control: the round-38 quote "LEFT moved the divider 3 left" style must be found in ar25 of b99ap's run.
usage: python stage0_extract.py [run-dir]   -> stage0_candidates.json, stage0_batch{0..3}.json
"""
import glob, json, random, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = HERE.parent
RUN = S / (sys.argv[1] if len(sys.argv) > 1 else "kout-yo-thui-b99-rungpin-full25-r1")
SPLIT = re.compile(r"\n(?=\[(?:SYSTEM PROMPT|USER PROMPT|MODEL RESPONSE META|THINKING|ASSISTANT|ANALYZER STATUS)\]\n)")
STATE = re.compile(r"Current state: step (\d+), level (\d+)")
ACT = re.compile(r"\b(UP|DOWN|LEFT|RIGHT|SPACE|ACTION[1-7]|RESET|click(?:s|ed|ing)?|MOUSE)\b", re.I)
EFF = re.compile(r"\b(mov(?:e|es|ed|ing)|shift(?:s|ed)?|toggl\w*|rotat\w*|chang\w*|turn(?:s|ed)|becom\w*|swap\w*|"
                 r"increas\w*|decreas\w*|fill\w*|remov\w*|appear\w*|disappear\w*|push\w*|slid\w*|flip\w*|mirror\w*|"
                 r"recolou?r\w*|expand\w*|shrink\w*|grow\w*|extend\w*)\b", re.I)
PER_GAME, N_BATCH = 4, 4
CONTROLS_NEG = ["Let me look at the current board carefully before deciding.",
                "I need to think about what the goal of this level might be.",
                "The board is 64x64 and mostly black with a few colored regions."]


def turns(path):
    out, cur = [], None
    for b in SPLIT.split(open(path, encoding="utf-8", errors="replace").read()):
        head = b.split("\n", 1)[0]
        if head == "[USER PROMPT]":
            m = STATE.search(b)
            cur = {"level": int(m.group(2)) if m else None, "text": []}
            out.append(cur)
        elif cur is not None and head in ("[THINKING]", "[ASSISTANT]"):
            cur["text"].append(b.split("\n", 1)[1] if "\n" in b else "")
    return out


def sentences(t):
    for s in re.split(r"\n+|(?<=[.!?])\s+", t):
        s = s.strip()
        if 25 <= len(s) <= 400 and ACT.search(s) and EFF.search(s):
            yield s


def main():
    random.seed(98)
    bench = {g["game_id"][:13]: g for g in json.load(open(RUN / "benchmark.json", encoding="utf-8"))["game_runs"]}
    cands, avail = [], {}
    for f in sorted(glob.glob(str(RUN / "transcripts" / "*.txt"))):
        game = Path(f).name[:13]
        g = bench[game]
        last_clear_level = g["levels_completed"]            # levels 1..N cleared; dead time = turns at level > N
        ts = [t for t in turns(f) if t["level"]]
        seen = set()
        for i, t in enumerate(ts):
            dead = t["level"] > last_clear_level
            for s in sentences("\n".join(t["text"])):
                if s not in seen:
                    seen.add(s)
                    cands.append({"game": game, "level": t["level"], "turn": i, "dead_time": dead, "text": s})
        ev = glob.glob(str(RUN / "artifacts" / f"{game}*_events.jsonl"))
        n_act = n_board = 0
        if ev:
            for line in open(ev[0], encoding="utf-8"):
                e = json.loads(line)
                if e.get("type") == "action":
                    n_act += 1
                    n_board += bool(e.get("board"))
        avail[game] = (n_act, n_board)
    games = sorted(bench)
    per = {g: [c for c in cands if c["game"] == g] for g in games}
    print(f"run {RUN.name}: candidates {len(cands)}; games with >= 1 candidate {sum(bool(v) for v in per.values())}/25")
    print("per game:", {g[:4]: (len(v), sum(c['dead_time'] for c in v)) for g, v in per.items()})
    ok_avail = all(a > 0 and a == b for a, b in avail.values())
    print(f"data availability: every game's action events carry a board: {ok_avail}; "
          f"actions {sum(a for a, _ in avail.values())}, with board {sum(b for _, b in avail.values())}")
    # sample: up to PER_GAME per game, dead-time candidates first (B98's target), then others
    sample = []
    for g, v in per.items():
        d = [c for c in v if c["dead_time"]]; o = [c for c in v if not c["dead_time"]]
        random.shuffle(d); random.shuffle(o)
        sample += (d[:PER_GAME // 2] + o)[:PER_GAME] if d else o[:PER_GAME]
    for k, s in enumerate(CONTROLS_NEG):
        sample.append({"game": "CONTROL", "level": 0, "turn": -1, "dead_time": False, "text": s, "neg_control": True})
    random.shuffle(sample)
    for i, c in enumerate(sample):
        c["id"] = f"h{i:03d}"
    json.dump(cands, open(HERE / "stage0_candidates.json", "w", encoding="utf-8"), indent=0, ensure_ascii=False)
    for b in range(N_BATCH):
        json.dump(sample[b::N_BATCH], open(HERE / f"stage0_batch{b}.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"sampled {len(sample)} (incl. {len(CONTROLS_NEG)} negative controls) into {N_BATCH} batches")


if __name__ == "__main__":
    main()
