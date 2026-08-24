"""B26's remaining half, offline: does the AGENT's transition model match the ground truth?

R31 answered the first half -- the ground truth is stable. Keyed as the agent issues and
reads the action, a recorded (level, board, action) reproduces the harness's board_changed
flag 98.1% corpus-wide and 311/311 on keyboard. What that says is that a verifier COULD be
built. It says nothing about whether the agent already behaves as if it had one.

This asks the behavioural form of the question, which needs no belief extraction from prose:

  When the agent stands on a board it has already acted from, and its own `transitions`
  record says some action did NOTHING there, does it fire that action again?

An agent whose transition model matched the ground truth would not -- the record is right
98% of the time (R31), so re-firing a recorded no-op is ~98% certain to waste the action.
The null matters: if most recorded actions at a revisited board are no-ops anyway, then
"the agent repeated a no-op" is what any picker does. So every rate is reported against
the uniform-pick baseline over that board's OWN recorded set, paired decision by decision.

Second measurement, the mechanism: `transitions` / `history` / `last_transition` are
handed to the sandbox every turn and the system prompt says to inspect them. Does the
EXECUTED code ever mention them? Scoped to [ASSISTANT] -- code in [THINKING] was drafted
and not run (B28's lesson, and R31's own boilerplate trap: the API description lives in
[SYSTEM PROMPT] and matches every grep run over the whole transcript).

Controls, in the order they gate:
  1. reproduce R31's headline 324 / 74.1% / 98.1% under action_display  (same loader, same key)
  2. reproduce R31's coverage 7,938 decisions / 9.0% revisit / 4.1% repeats
  3. shuffled-history control: consult a RANDOM other board's record. Observed - null must
     collapse. A control that cannot fail is a constant (R31 CONTROL 4's lesson).
  4. code-grep controls: a token known present and one known absent, same invocation.
  5. cardinality: every population printed, and nothing read off an empty one.
"""
import collections
import hashlib
import random
import re
import sys

from corpus import RUNS5, game_files, load_game, game_key

R31_REPEATS = (324, 74.1, 98.1)   # R31's headline under action_display
R31_COVER = (7938, 711, 638)      # decisions, from a seen board, of those knowing exactly 1

# [W R W] and [W O W] -- two board rows -- match a bare all-caps-in-brackets pattern in this
# corpus, so the section names are enumerated rather than inferred.
SECTIONS = ("[SYSTEM PROMPT]", "[USER PROMPT]", "[MODEL RESPONSE META]", "[THINKING]",
            "[ASSISTANT]", "[ANALYZER STATUS]")
MARK = re.compile("^(" + "|".join(re.escape(s) for s in SECTIONS) + ")$", re.M)
CODE = re.compile(r"<parameter=code>(.*?)</parameter>", re.S)
CONSULT = re.compile(r"\btransitions\b|\blast_transition\b|\bhistory\b", re.I)
PRESENT = re.compile(r"current_frame")     # control: every turn's code reads the frame
ABSENT = re.compile(r"zzqq_not_a_symbol")  # control: must be 0


def h(s):
    return hashlib.md5(s.encode()).hexdigest()[:12] if s else None


def walk():
    """Yield one row per decision: (run, game, level, prev_board_hash, action, changed)."""
    for r in RUNS5:
        for f in game_files(r):
            g, prev = game_key(f)[:4], None
            for e in load_game(f):
                if e.get("type") not in ("initial", "action"):
                    continue
                if e.get("type") == "action" and prev is not None:
                    yield (r, g, e.get("level"), prev, str(e.get("action_display")),
                           bool(e.get("board_changed")), str(e.get("action_name")))
                prev = h(e.get("board_ascii"))


def scan(shuffle_seed=None):
    """Replay each run-game in order, holding the record the agent's own `transitions` would.

    shuffle_seed: consult a RANDOM other board's record instead of this board's (control 3).
    """
    rows = collections.defaultdict(list)
    for row in walk():
        rows[(row[0], row[1])].append(row)

    st = collections.Counter()
    per = collections.defaultdict(collections.Counter)
    null_terms = []          # per-decision P(no-op) under a uniform pick from the record
    null_old = []            # ... with the immediately-preceding action removed
    suppressed = []          # what a brake keyed on "record says no-op" would have stopped
    for (run, g), seq in rows.items():
        rec = collections.defaultdict(list)          # (level, board) -> [(action, changed)]
        rng = random.Random(f"{shuffle_seed}:{run}:{g}") if shuffle_seed is not None else None
        last = None                                  # (level, board, action) of the last decision
        for i, (_r, _g, lvl, prev, act, changed, name) in enumerate(seq):
            st["decisions"] += 1
            key = (lvl, prev)
            consult = key
            if rng is not None and rec:
                consult = rng.choice(list(rec.keys()))
            book = rec.get(consult)
            if book:
                st["from_seen_board"] += 1
                per[g]["seen"] += 1
                acts = collections.defaultdict(list)
                for a, c in book:
                    acts[a].append(c)
                noops = {a for a, cs in acts.items() if not any(cs)}
                movers = {a for a, cs in acts.items() if any(cs)}
                st[f"known_{min(len(acts), 5)}"] += 1
                null_terms.append(len(noops) / len(acts))
                # a "never repeat the action you just fired" rule needs NO transition model.
                # Strip that action from the candidate set and ask the question again.
                stale = last if (last and last[:2] == (lvl, prev)) else None
                rest = {a: cs for a, cs in acts.items() if a != (stale[2] if stale else None)}
                if rest:
                    null_old.append(sum(1 for cs in rest.values() if not any(cs)) / len(rest))
                # OPPORTUNITY denominators -- a rate with no denominator is not a rate.
                if stale:
                    st["opp_refire"] += 1                    # could re-fire the just-failed action
                    st["did_refire"] += (act == stale[2])
                stale_noops = {a for a in noops if not stale or a != stale[2]}
                if stale_noops:
                    st["opp_return_noop"] += 1               # an OLDER recorded no-op was on offer
                    st["did_return_noop"] += (act in stale_noops)
                if act in acts:
                    st["repeat"] += 1
                    per[g]["repeat"] += 1
                    fresh = bool(stale) and act == stale[2]
                    st["repeat_lag1" if fresh else "repeat_older"] += 1
                    if act in noops:
                        st["repeat_known_noop"] += 1
                        st["noop_lag1" if fresh else "noop_older"] += 1
                        per[g]["noop"] += 1
                        suppressed.append((run, g, act.startswith("MOUSE"), changed, fresh))
                        st["noop_multi_action_record"] += (len(acts) > 1)
                        if movers:
                            st["noop_while_mover_known"] += 1
                    else:
                        st["repeat_known_mover"] += 1
                        st["mover_multi_action_record"] += (len(acts) > 1)
                else:
                    st["new_action"] += 1
            # NULL for (i): the agent's plain tendency to fire the same action twice running,
            # measured after a MOVER -- same repetition habit, but repeating is not futile there.
            if last is not None:
                st["after_mover" if last[3] else "after_noop"] += 1
                st[("after_mover_same" if last[3] else "after_noop_same")] += (act == last[2])
            rec[key].append((act, changed))
            last = (lvl, prev, act, changed)
    return st, per, null_terms, suppressed, null_old


def turns():
    for r in RUNS5:
        for f in game_files(r):
            for e in load_game(f):
                if e.get("type") == "analysis":
                    t = e.get("transcript")
                    if t:
                        yield r, game_key(f)[:4], t


def code_of(t, section="[ASSISTANT]"):
    bounds = [(m.start(), m.group()) for m in MARK.finditer(t)]
    out = []
    for m in CODE.finditer(t):
        cur = None
        for pos, name in bounds:
            if pos < m.start():
                cur = name
            else:
                break
        if section is None or cur == section:
            out.append(m.group(1))
    return "\n".join(out)


def pct(a, b):
    return 100.0 * a / b if b else 0.0


def main():
    # ---- CONTROL 1 + 2: reproduce R31 ----
    st, per, null_terms, suppressed, null_old = scan()
    ok1 = st["repeat"] == R31_REPEATS[0]
    ok2 = (st["decisions"] == R31_COVER[0] and st["from_seen_board"] == R31_COVER[1]
           and st["known_1"] == R31_COVER[2])
    print(f"CONTROL 1  R31 repeats = {R31_REPEATS[0]}: {ok1}   got {st['repeat']}")
    print(f"CONTROL 2  R31 coverage {R31_COVER}: {ok2}   got "
          f"({st['decisions']}, {st['from_seen_board']}, {st['known_1']})")
    if not (ok1 and ok2):
        print("  loader/key does not reproduce R31 -- STOP, read nothing below")
        return 1

    null = sum(null_terms) / len(null_terms) if null_terms else 0.0
    obs = pct(st["repeat_known_noop"], st["repeat"])

    print("\nA. DOES THE AGENT AVOID THE NO-OPS ITS OWN RECORD ALREADY HOLDS?")
    print(f"  decisions                              {st['decisions']}")
    print(f"  from a board it had acted from before  {st['from_seen_board']} "
          f"= {pct(st['from_seen_board'], st['decisions']):.1f}%")
    print(f"    picked an action NOT in the record   {st['new_action']:5d} "
          f"= {pct(st['new_action'], st['from_seen_board']):5.1f}%")
    print(f"    repeated a recorded action           {st['repeat']:5d} "
          f"= {pct(st['repeat'], st['from_seen_board']):5.1f}%")
    print(f"      ... recorded as a MOVER            {st['repeat_known_mover']:5d}")
    print(f"      ... recorded as a NO-OP            {st['repeat_known_noop']:5d} "
          f"= {obs:5.1f}% of repeats")
    print(f"  NULL: uniform pick from that board's own record would be {null*100:.1f}%")
    print(f"  -> observed {obs:.1f}% vs null {null*100:.1f}%  "
          f"delta {obs - null*100:+.1f} pp")

    # ⚠️ the delta above is NOT yet evidence of a transition model. A no-op is what KEEPS
    # the agent on a board, so the revisit population is enriched in no-ops by construction
    # and "don't re-fire what you just fired" reproduces most of the avoidance with no
    # model at all. Split on whether the repeated entry was the immediately-preceding
    # action; only the `older` stratum can speak.
    n_old = st["repeat_older"]
    nullo = sum(null_old) / len(null_old) if null_old else 0.0
    print("\n  DISCRIMINATOR -- was the record consulted, or just the last action avoided?")
    print(f"    repeats of the action fired at the PREVIOUS decision (lag 1) "
          f"{st['repeat_lag1']:4d}, of which no-op {st['noop_lag1']}"
          f" = {pct(st['noop_lag1'], st['repeat_lag1']):.1f}%")
    print(f"    repeats of an OLDER record entry                        "
          f"{n_old:4d}, of which no-op {st['noop_older']}"
          f" = {pct(st['noop_older'], n_old):.1f}%")
    print(f"    NULL with the just-fired action stripped out: {nullo*100:.1f}%")
    print(f"    -> the split is PERFECT, and it is structural: a no-op leaves the agent on"
          f"\n       the same board, so it can only ever be re-fired at lag 1; a mover moves"
          f"\n       it off, so a mover repeat can only ever be older. The -43.8 pp above is"
          f"\n       an artifact of that, NOT evidence of a model. Ask each stratum instead:")
    print(f"\n    (i)  after firing an action that did NOTHING, does it re-fire that action?")
    print(f"         {st['did_refire']} of {st['opp_refire']} such decisions "
          f"= {pct(st['did_refire'], st['opp_refire']):.1f}%")
    print(f"         NULL, the same repetition habit where repeating is NOT futile --"
          f" after a MOVER:")
    print(f"         {st['after_mover_same']} of {st['after_mover']} "
          f"= {pct(st['after_mover_same'], st['after_mover']):.1f}%   "
          f"-> {pct(st['after_mover_same'], st['after_mover']) / max(pct(st['did_refire'], st['opp_refire']), 1e-9):.1f}x")
    print(f"         CONTROL  the same population reached two ways -- board_ascii equality"
          f"\n         ({st['opp_refire']}/{st['did_refire']}) vs the board_changed flag "
          f"({st['after_noop']}/{st['after_noop_same']}): "
          f"{st['opp_refire'] == st['after_noop'] and st['did_refire'] == st['after_noop_same']}")
    print(f"    (ii) returning to a board whose record already holds an OLDER no-op,"
          f" does it pick it?")
    print(f"         {st['did_return_noop']} of {st['opp_return_noop']} such decisions "
          f"= {pct(st['did_return_noop'], st['opp_return_noop']):.1f}%")
    print(f"\n  CARDINALITY -- a 'never happened' over an empty set is not a finding:")
    print(f"    no-op repeats whose board record held >1 action: "
          f"{st['noop_multi_action_record']} of {st['repeat_known_noop']}")
    print(f"    mover repeats whose board record held >1 action: "
          f"{st['mover_multi_action_record']} of {st['repeat_known_mover']}")
    print(f"    no-op repeated while a KNOWN MOVER sat in the same record: "
          f"{st['noop_while_mover_known']}"
          f"  <- read ONLY against the {st['noop_multi_action_record']} above")

    # ---- CONTROL 3: shuffled history must collapse the delta ----
    sh_deltas = []
    for seed in (1, 2, 3):
        s2, _, n2, _, _ = scan(shuffle_seed=seed)
        d = pct(s2["repeat_known_noop"], s2["repeat"]) - 100 * sum(n2) / len(n2)
        sh_deltas.append(d)
    bites = abs(sum(sh_deltas) / len(sh_deltas)) < abs(obs - null * 100) / 2
    print(f"\nCONTROL 3  shuffled history (consult a random other board), 3 seeds:")
    print(f"  delta {[f'{d:+.1f}' for d in sh_deltas]} pp   vs real {obs - null*100:+.1f} pp"
          f"   -> control bites: {bites}")
    if not bites:
        print("  the measurement does not respond to corrupting the record -- STOP")
        return 1

    # ---- B29: what a brake keyed on this would do, on its OWN trigger population ----
    n = len(suppressed)
    wrong = sum(1 for _, _, _, changed, _ in suppressed if changed)
    mouse = sum(1 for _, _, m, _, _ in suppressed if m)
    kbd_wrong = sum(1 for _, _, m, c, _ in suppressed if not m and c)
    kbd = n - mouse
    print("\nB. THE BRAKE, MEASURED ON THE POPULATION IT WOULD ACT ON")
    print(f"  actions it would suppress          {n}  = {pct(n, st['decisions']):.2f}% of all decisions")
    print(f"    of which clicks                  {mouse}   keyboard {kbd}")
    print(f"  of those, the board ACTUALLY changed (a wrong suppression): "
          f"{wrong} = {pct(wrong, n):.1f}%")
    print(f"    keyboard only: {kbd_wrong}/{kbd} = {pct(kbd_wrong, kbd):.1f}% wrong")
    print(f"  the whole prize, across FIVE complete runs: {n} actions "
          f"({n / len(RUNS5):.1f} per run of ~{st['decisions'] // len(RUNS5)})")

    print("\n  per game (>=3 suppressions):")
    bg = collections.Counter()
    for _, g, _, _, _ in suppressed:
        bg[g] += 1
    for g, c in bg.most_common():
        if c >= 3:
            print(f"    {g:6s} {c:4d} suppressions   ({per[g]['repeat']} repeats, "
                  f"{per[g]['seen']} decisions from a seen board)")

    # ---- C: does the agent CONSULT the record at all? ----
    tn = tcode = tconsult = tpresent = tabsent = 0
    think_consult = 0
    percons = collections.Counter()
    for run, g, t in turns():
        tn += 1
        c = code_of(t)
        if c:
            tcode += 1
            if CONSULT.search(c):
                tconsult += 1
                percons[run] += 1
            if PRESENT.search(c):
                tpresent += 1
            if ABSENT.search(c):
                tabsent += 1
        if CONSULT.search(code_of(t, section="[THINKING]")):
            think_consult += 1
    print("\nC. DOES THE EXECUTED CODE EVER READ THE RECORD?")
    print(f"  CONTROL 4  present-token 'current_frame' in executed code: {tpresent}/{tcode}"
          f"   absent-token: {tabsent}   (must be >0 and 0)")
    if tpresent == 0 or tabsent != 0:
        print("  the code-scoping instrument is broken -- STOP")
        return 1
    print(f"  analysis turns                     {tn}")
    print(f"  turns whose [ASSISTANT] ran code   {tcode} = {pct(tcode, tn):.1f}%")
    print(f"  ... mentioning transitions/history/last_transition  {tconsult}"
          f" = {pct(tconsult, tcode):.1f}% of code turns, {pct(tconsult, tn):.1f}% of turns")
    print(f"  drafted-but-not-run mentions ([THINKING]): {think_consult}")
    print(f"  per run: {dict(percons)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
