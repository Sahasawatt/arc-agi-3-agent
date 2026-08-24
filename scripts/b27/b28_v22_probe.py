"""B28, offline: v22 does NOT change the axis B28 says it changes -- and the right probe
for what it DOES change, with its baseline, before the run.

B28's row reads: "v22's ported addendum carries the rank-21 team's explicit BFS
instruction ... re-run the v17 search-construct probe over its transcripts."

That is a claim about a file, and it is false. The BFS bullet is BYTE-IDENTICAL in the
stock addendum and in the port, and every one of the five baseline runs already ships it
(`BFS` x2, plus flood fill / beam search / shortest-path). So a search-construct probe over
v22 measures a prompt difference that does not exist, and whatever it returns -- up, down or
flat -- cannot be attributed to a BFS instruction.

`duckv22/cell12_prompt_port.py`'s own comment is accurate and says so: "Their two genuinely
new bullets" are (1) a tried-checklist in `Recent findings:` and (2) never transcribe ASCII
rows in your own REASONING. The cell's teeth assert only on (1) -- `"already tried"` -- so a
run whose BFS half is unchanged still passes them. The teeth are right; the ticket is wrong.

This checks the claim and then builds the two probes v22's real diff needs, each with the
five-run baseline the comparison will be made against. Both are offline, 0 slots.

Controls, in the order they gate:
  1. present/absent token pair on the system-prompt reader (`current_frame` >0, `zzqq` 0)
  2. the addendum is isolated by its own header and re-found in all five runs
  3. the ASCII-row detector is proved on a REAL board row and on prose, same invocation
  4. every rate carries its denominator
"""
import collections
import re
import sys

from corpus import RUNS5, game_files, load_game

SEC = re.compile(r"^(\[SYSTEM PROMPT\]|\[USER PROMPT\]|\[MODEL RESPONSE META\]|"
                 r"\[THINKING\]|\[ASSISTANT\]|\[ANALYZER STATUS\])$", re.M)
PORT = "../../duckv22/cell12_prompt_port.py"
# the ARC colour alphabet the prompt's own legend defines; a transcribed board row is a long
# run of it and nothing else.
ROW = re.compile(r"^[WwgGcBMPRbSYOrNn ]{40,}$")


def sections(t):
    ms = [(m.start(), m.end(), m.group()) for m in SEC.finditer(t)]
    out = collections.defaultdict(str)
    for i, (s, e, name) in enumerate(ms):
        nxt = ms[i + 1][0] if i + 1 < len(ms) else len(t)
        out[name] += t[e:nxt]
    return out


def turns(run):
    for f in game_files(run):
        for e in load_game(f):
            if e.get("type") == "analysis" and e.get("transcript"):
                yield e["transcript"]


def addendum(sp):
    i = sp.find("Python tool guidance:")
    if i < 0:
        return None
    lines = sp[i:].split("\n")
    out = [lines[0]]
    for l in lines[1:]:
        if l.startswith("- ") or not l.strip():
            out.append(l)
        else:
            break
    return "\n".join(out).rstrip()


def bullets(s):
    return [l.strip() for l in s.split("\n") if l.startswith("- ")]


def main():
    src = open(PORT).read()
    theirs = (re.search(r"THEIR_PYTHON_ADDENDUM = '(.*)'\n", src, re.S)
              .group(1).encode().decode("unicode_escape").strip())

    print("1. IS THE BFS INSTRUCTION NEW IN v22?")
    stock = {}
    for run in RUNS5:
        t = next(turns(run))
        sp = sections(t)["[SYSTEM PROMPT]"]
        a = addendum(sp)
        stock[run] = a
        print(f"   {run:8s} sysprompt {len(sp):6d}ch  addendum {len(a) if a else 0:5d}ch"
              f"  BFS={sp.count('BFS')}  flood-fill={sp.count('flood fill')}"
              f"  beam={sp.count('beam search')}"
              f"  |  'already tried'={sp.count('already tried')}"
              f"  CTRL current_frame={sp.count('current_frame')} zzqq={sp.count('zzqq')}")
    bad = [r for r, a in stock.items() if not a]
    if bad or any(sections(next(turns(r)))["[SYSTEM PROMPT]"].count("current_frame") == 0
                  for r in RUNS5):
        print("   the system-prompt reader is broken -- STOP")
        return 1

    a = bullets(stock["v10cal"])
    b = bullets(theirs)
    bfs_a = [l for l in a if "BFS" in l]
    bfs_b = [l for l in b if "BFS" in l]
    same = bfs_a == bfs_b and len(bfs_a) == 1
    print(f"\n   stock addendum {len(a)} bullets, port {len(b)} bullets, "
          f"{len([l for l in b if l in a])} verbatim-identical")
    print(f"   the BFS bullet is BYTE-IDENTICAL on both sides: {same}")
    print(f"   'already tried' present in stock: "
          f"{any('already tried' in l for l in a)}  in port: "
          f"{any('already tried' in l for l in b)}")
    print("   -> B28's premise ('v22 carries the BFS instruction') is FALSE; the instruction"
          "\n      has shipped in every run of this campaign. v22's real diff is the"
          "\n      tried-checklist and the no-ASCII-in-reasoning bullets.")

    print("\n2. PROBE A -- does the agent keep a tried-checklist? (v22's bullet 1)")
    print("   baseline: `Recent findings:` in the model's own output, five runs")
    # CONTROL: a token known present in the model's own output and one known absent, so a
    # small count below is read as a small count and not as a dead reader.
    for run in RUNS5:
        n = rf = ctrl = zz = 0
        for t in turns(run):
            n += 1
            own = sections(t)["[THINKING]"] + sections(t)["[ASSISTANT]"]
            ctrl += (" the " in own)
            zz += own.count("zzqq")
            rf += ("Recent findings" in own)
        print(f"   {run:8s} {rf:5d}/{n:5d} turns = {100*rf/n:5.2f}%"
              f"   CTRL present {ctrl} absent {zz}")

    print("\n3. PROBE B -- does it transcribe ASCII rows in its REASONING? (v22's bullet 2)")
    # CONTROL 3: prove the detector on a real board row and on prose, in this invocation.
    real = next(e["board_ascii"] for f in game_files("v10cal") for e in load_game(f)
                if e.get("board_ascii")).split("\n")[0]
    prose = "- Use `current_frame.segmentation` as your primary view of the board"
    hit_real, hit_prose = bool(ROW.match(real)), bool(ROW.match(prose))
    print(f"   CONTROL detector on a real board row: {hit_real}  on prose: {hit_prose}"
          f"   (must be True / False)")
    if not hit_real or hit_prose:
        print("   the row detector is broken -- STOP")
        return 1
    for run in RUNS5:
        n = t3 = rows = 0
        for t in turns(run):
            n += 1
            th = sections(t)["[THINKING]"]
            r = sum(1 for l in th.split("\n") if ROW.match(l))
            rows += r
            if r >= 3:
                t3 += 1
        print(f"   {run:8s} {t3:5d}/{n:5d} turns with >=3 transcribed rows = "
              f"{100*t3/n:5.2f}%   rows total {rows}")

    print("\n   -> these two are what a v22 run can be read against. The search-construct"
          "\n      probe B28 names should still be run as a NEGATIVE control: the BFS text"
          "\n      is unchanged, so a moved search rate would be evidence the probe drifts,"
          "\n      not evidence the prompt worked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
