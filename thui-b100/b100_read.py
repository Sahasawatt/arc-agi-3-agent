"""Read the thui-b100 smoke pair per thui-b100/PREDICTIONS.md (both arms carry the same logging wrapper).

usage: python b100_read.py <ctl-output-dir> <ctl-log> <arm-output-dir> <arm-log> [--selftest]
Exit 0 PASS (go to the full pair), 5 KILL, 3 VOID, 1 reader error.
"""
import glob, json, os, re, sys

STATS = re.compile(r"THUI_B100_STATS strip=(True|False) (.*)")
MARK = re.compile(r"Current state: step \d+, level (\d+)")
CODE = re.compile(r"<parameter=code>\n(.*?)</parameter>", re.S)
DEF = re.compile(r"^[ \t]*def ([A-Za-z_]\w*)\(", re.M)
PROMPT_DROP_MIN = 0.02       # (a): post-clear prompt tokens / request must fall >= 2 % vs control (revised 2026-09-22, real payloads)
MECH_MIN = 0.05              # within-arm: stripped share of post-clear history reasoning >= 5 % (revised 2026-09-22)
ACTIONS_PER_MIN_MIN = 0.95   # arm actions/min >= 95 % of control
REDEF_RISE_MAX = 1.50        # our guard: final-level redefs/call <= 1.5 x control (two same-family smokes differ 1.25x on noise)


def read(d, log, strip):
    out = dict(games=None, levels=None, l2plus=None, actions=None, minutes=None, stats=None, marker_ok=False,
               final_calls=0, final_redefs=0, transcripts=0)
    bj = os.path.join(d, "benchmark.json")
    if os.path.exists(bj):
        gr = json.load(open(bj, encoding="utf-8")).get("game_runs", [])
        out["games"] = len(gr)
        out["levels"] = sum(int(g["levels_completed"]) for g in gr)
        out["l2plus"] = sum(max(0, int(g["levels_completed"]) - 1) for g in gr)
        out["actions"] = sum(len(g["history"]) if isinstance(g["history"], list) else 0 for g in gr)
        out["minutes"] = sum(float(g.get("final_wallclock_seconds") or 0) for g in gr) / 60
    for p in glob.glob(os.path.join(d, "transcripts", "*.txt")):
        t = open(p, encoding="utf-8", errors="replace").read()
        out["transcripts"] += 1
        marks = list(MARK.finditer(t))
        cut = min((m.start() for m in marks if int(m.group(1)) == max(int(x.group(1)) for x in marks)), default=0) if marks else 0
        seen = set(DEF.findall("\n".join(CODE.findall(t[:cut]))))
        for code in CODE.findall(t[cut:]):
            out["final_calls"] += 1
            for name in DEF.findall(code):
                out["final_redefs"] += name in seen
                seen.add(name)
    nb = open(log, encoding="utf-8", errors="replace").read() if log and os.path.exists(log) else ""
    out["marker_ok"] = (f"THUI_B100_GRAFT ok strip={strip}" in nb and "THUI_B100_SMOKE arm=" in nb)
    m = STATS.findall(nb)
    if m and m[-1][0] == str(strip):
        out["stats"] = {k: int(v) for k, v in (kv.split("=") for kv in m[-1][1].split())}
    return out


def verdict(c, a):
    lines = []
    for name, x in (("control", c), ("arm", a)):
        if not (x.get("games") == 25 and x.get("transcripts", 0) >= 25 and x.get("marker_ok") and x.get("stats")
                and x["stats"].get("requests", 0) > 0):
            lines.append(f"FAIL {name} not VALID (25 games/transcripts, graft marker with the right strip flag, STATS line)")
            return "VOID", lines
    s, cs = a["stats"], c["stats"]
    if s["stripped_msgs"] == 0:
        lines.append("FAIL arm wrapper stripped nothing at all -- VOID per B100 validity")
        return "VOID", lines
    if not s["post_clear_requests"] or not cs["post_clear_requests"]:
        lines.append("FAIL no post-clear requests in one arm -- the (a) metric cannot be read")
        return "VOID", lines
    pa = s["post_clear_prompt_tokens"] / s["post_clear_requests"]
    pc = cs["post_clear_prompt_tokens"] / cs["post_clear_requests"]
    drop = 1 - pa / pc
    mech = s["post_clear_stripped_chars"] / max(1, s["post_clear_stripped_chars"] + s["post_clear_sent_reasoning_chars"])
    apm_a, apm_c = a["actions"] / max(1e-9, a["minutes"]), c["actions"] / max(1e-9, c["minutes"])
    rd_a = a["final_redefs"] / max(1, a["final_calls"]); rd_c = c["final_redefs"] / max(1, c["final_calls"])
    lines.append(f"post-clear prompt tokens/request ctl {pc:.0f} arm {pa:.0f} (drop {drop:+.3f}, bar >= {PROMPT_DROP_MIN}) | "
                 f"stripped share of post-clear reasoning {mech:.3f} (bar >= {MECH_MIN}) | actions/min ctl {apm_c:.2f} "
                 f"arm {apm_a:.2f} | L2+ clears ctl {c['l2plus']} arm {a['l2plus']} | final-level redefs/call ctl "
                 f"{rd_c:.3f} arm {rd_a:.3f} | levels ctl {c['levels']} arm {a['levels']} | post-clear requests "
                 f"ctl {cs['post_clear_requests']} arm {s['post_clear_requests']}")
    kills = []
    if drop < PROMPT_DROP_MIN:
        kills.append("prompt-token drop below bar")
    if mech < MECH_MIN:
        kills.append("mechanism share below bar")
    if apm_a < ACTIONS_PER_MIN_MIN * apm_c:
        kills.append("actions/min below 95 % of control")
    if a["l2plus"] < c["l2plus"]:
        kills.append("L2+ clears down")
    if rd_a > REDEF_RISE_MAX * rd_c and rd_c > 0:
        kills.append("final-level redefinitions rose")
    if kills:
        lines.append("KILL: " + "; ".join(kills))
        return "KILL", lines
    return "PASS", lines


def selftest():
    st = dict(requests=500, post_clear_requests=200, post_clear_prompt_tokens=200 * 18000, all_prompt_tokens=0,
              stripped_msgs=300, stripped_chars=0, kept_clear_msgs=20, sent_reasoning_chars=0,
              post_clear_stripped_chars=200000, post_clear_sent_reasoning_chars=800000)
    ctl = dict(games=25, transcripts=25, marker_ok=True, levels=18, l2plus=6, actions=700, minutes=750,
               final_calls=400, final_redefs=100, stats=dict(st, stripped_msgs=300, post_clear_prompt_tokens=200 * 20000))
    arm = dict(ctl, stats=st)
    cases = [("pass", arm, "PASS"),
             ("prompt barely moves", dict(arm, stats=dict(st, post_clear_prompt_tokens=200 * 19800)), "KILL"),
             ("mechanism thin", dict(arm, stats=dict(st, post_clear_stripped_chars=20000)), "KILL"),
             ("slower", dict(arm, actions=600), "KILL"),
             ("L2+ down", dict(arm, l2plus=5), "KILL"),
             ("redefs rose", dict(arm, final_redefs=160), "KILL"),
             ("wrapper stripped nothing", dict(arm, stats=dict(st, stripped_msgs=0)), "VOID"),
             ("wrong flag / no marker", dict(arm, marker_ok=False), "VOID"),
             ("short of games", dict(arm, games=20), "VOID")]
    ok = True
    for name, a, want in cases:
        got, _ = verdict(ctl, a)
        print(f"{'ok  ' if got == want else 'FAIL'} selftest {name}: {got} (want {want})")
        ok &= got == want
    return ok


def main():
    if not selftest():
        print("reader selftest FAILED -- nothing below is meaningful"); sys.exit(1)
    if "--selftest" in sys.argv:
        sys.exit(0)
    cdir, clog, adir, alog = sys.argv[1:5]
    c, a = read(cdir, clog, False), read(adir, alog, True)
    print("CONTROL", c); print("ARM    ", a)
    v, lines = verdict(c, a)
    print("\n".join(lines)); print("VERDICT", v)
    sys.exit({"PASS": 0, "KILL": 5, "VOID": 3}[v])


if __name__ == "__main__":
    main()
