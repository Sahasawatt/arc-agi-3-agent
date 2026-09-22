"""Apply the B100 keep rule to REAL request payloads: each run's prompts/<game>.log holds the LAST model call of that game
("LATEST MODEL CALL SNAPSHOT"). Measures the real history window (assistant turns kept) and the share of reasoning / of
all input chars the rule would strip. Last calls sit on each game's final level, so this is the END-of-game view.
"""
import glob, re, statistics as st, sys
S = sys.argv[1]
SEC = re.compile(r"^\[(SYSTEM|USER|ASSISTANT|REASONING|ASSISTANT TOOL CALL: [^\]]+|TOOL RESULT: [^\]]+)\]\n", re.M)
MARK = re.compile(r"Current state: step \d+, level (\d+)")
wins, shares, inshares, post = [], [], [], 0
n = 0
for p in glob.glob(f"{S}/kout-*/prompts/*.log"):
    t = open(p, encoding="utf-8", errors="replace").read()
    i = t.find("[MODEL INPUT]")
    if i < 0:
        continue
    body = t[i:]
    parts = SEC.split(body)[1:]
    secs = list(zip(parts[0::2], parts[1::2]))
    level, turns = None, []            # per assistant turn: [level, reasoning_chars]
    for name, text in secs:
        if name == "USER":
            m = MARK.findall(text)
            if m:
                level = int(m[-1])
        elif name == "ASSISTANT":
            turns.append([level, 0, None])
        elif name == "REASONING" and turns:
            turns[-1][1] += len(text)
    if not turns:
        continue
    n += 1
    cur = level
    # clearing = last assistant turn before a higher level
    clear = {k for k in range(len(turns) - 1) if turns[k][0] is not None and turns[k + 1][0] is not None
             and turns[k + 1][0] > turns[k][0]}
    tot = sum(r for _, r, _ in turns)
    strip = sum(r for k, (l, r, _) in enumerate(turns) if l is not None and cur is not None and l != cur and k not in clear)
    wins.append(len(turns))
    if cur and cur >= 2:
        post += 1
        shares.append(strip / tot if tot else 0)
        inshares.append(strip / len(body))
print(f"snapshots {n}; history window (assistant turns) median {st.median(wins)} p10 {sorted(wins)[len(wins)//10]} "
      f"p90 {sorted(wins)[9*len(wins)//10]}")
print(f"post-clear snapshots {post}: stripped share of reasoning mean {st.mean(shares):.3f} median {st.median(shares):.3f}; "
      f"of all input chars mean {st.mean(inshares):.3f}; snapshots with anything to strip {sum(s > 0 for s in shares)}")
