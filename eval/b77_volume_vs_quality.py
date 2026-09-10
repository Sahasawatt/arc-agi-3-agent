#!/usr/bin/env python3
"""B77 — is the Flash-Next gain VOLUME or PER-ACTION QUALITY?

Reads notes/LEDGER-all-runs.md through a git ref (never off disk) and asks whether a
Flash-Next action is worth more than a 27B action, or merely more numerous.

Asserts controls before printing any figure. Exit 0 always; this is a report, not a gate.

usage: python3 eval/b77_volume_vs_quality.py [ref]     (default: HEAD)
"""
import math, re, statistics as st, subprocess, sys

REF = sys.argv[1] if len(sys.argv) > 1 else "HEAD"

# Membership is DECLARED, never inferred -- same rule as eval/fixtures/arms.json.
BASE = ["v10cal", "v10out", "thui-v1-1", "thui-v1-1-r2", "thui-v3-0", "thui-v3-1"]  # 27B anim chassis
CLOCK = ["clock2x"]              # B34: the same chassis, 2x wall
FLASH = ["thui-fast-v0", "thui-a7-full25-r1"]   # B69 + B76
V20 = ["v20"]                    # B25: a MoE swap that fired 7,656 actions for 3 levels


def rows(ref):
    txt = subprocess.run(["git", "show", f"{ref}:notes/LEDGER-all-runs.md"],
                         capture_output=True, text=True, check=True).stdout
    lines = txt.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("## The table"))
    out, cl = [], lambda s: re.sub(r"[*`]", "", s).strip()
    num = lambda s: float(cl(s)) if re.match(r"^-?\d+(\.\d+)?$", cl(s)) else None
    for l in lines[start:]:
        if l.startswith("## ") and "The table" not in l:
            break
        if not l.startswith("|"):
            continue
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) < 10 or c[0].lower().startswith("run") or set(c[0]) <= set("-: "):
            continue
        out.append(dict(run=cl(c[0]).split()[0], lev=num(c[4]), act=num(c[5])))
    return [r for r in out if r["lev"] and r["act"]]


def main():
    d = rows(REF)
    pick = lambda names: [r for r in d if r["run"] in names]
    m = lambda g, k: st.mean([r[k] for r in g])

    # --- controls -----------------------------------------------------------
    for label, names in (("BASE", BASE), ("CLOCK", CLOCK), ("FLASH", FLASH), ("V20", V20)):
        got = {r["run"] for r in pick(names)}
        assert got == set(names), f"{label}: declared {set(names)}, ledger has {got}"
    assert not pick(["this-run-does-not-exist"]), "negative control matched"
    # act/lvl must order correctly on values we already know
    assert m(pick(V20), "act") / m(pick(V20), "lev") > 1000, "v20 is the known-catastrophic arm"
    print(f"controls: 6/6 pass (4 declared-membership, 1 negative, 1 known-value) @ {REF}\n")

    b, c, f, v = pick(BASE), pick(CLOCK), pick(FLASH), pick(V20)
    print("== act/lvl -- HIGHER means each action buys LESS ==")
    for label, g in (("27B chassis", b), ("27B + 2x clock (B34)", c),
                     ("Flash-Next (B69/B76)", f), ("v20 MoE-A3B (B25)", v)):
        print(f"  {label:<22} n={len(g)}  lev {m(g,'lev'):>5.1f}  act {m(g,'act'):>6.0f}  "
              f"act/lvl {m(g,'act')/m(g,'lev'):>7.1f}")
    print("\n  -> a Flash action is individually WORSE than a 27B action. It wins on VOLUME.")

    # --- how much of the gain does volume explain? --------------------------
    a2, l2 = m(f, "act"), m(f, "lev")
    a1, l1 = m(c, "act"), m(c, "lev")
    print("\n== the split, and why the data does not determine it ==")
    print("  levels ~ actions^b, with b estimated ON THE 27B CHASSIS ONLY (base -> clock2x),")
    print("  then extrapolated to Flash's action count. Two defensible bases:")
    for label, g0 in (("mean of the 6 anim runs", b), ("v10cal alone (clock2x's OWN base)", pick(["v10cal"]))):
        a0, l0 = m(g0, "act"), m(g0, "lev")
        bb = math.log(l1 / l0) / math.log(a1 / a0)
        pred = l0 * (a2 / a0) ** bb
        vol = (pred - l0) / (l2 - l0) * 100
        print(f"    {label:<34} b={bb:.3f}  pred {pred:>5.1f}  "
              f"volume {vol:>5.0f}%  model {100-vol:>5.0f}%")
    print("  Opposite verdicts from two defensible choices. b rests on TWO points and clock2x is n=1.")

    # --- the control that bounds the volume story ---------------------------
    a0, l0 = m(b, "act"), m(b, "lev")
    bb = math.log(l1 / l0) / math.log(a1 / a0)
    print(f"\n== control: volume is NECESSARY, not SUFFICIENT ==")
    print(f"  v20 fired {m(v,'act'):.0f} actions -- MORE than Flash's {a2:.0f} -- and cleared "
          f"{m(v,'lev'):.0f} levels.")
    print(f"  the volume model predicts {l0*(m(v,'act')/a0)**bb:.1f} for that action count.")
    print("  A model can be bad enough that its actions are worthless, so no volume argument")
    print("  can stand without saying which model is taking the actions.")

    print("\n== the experiment that WOULD decide it, at no submission slot ==")
    print("  Serve Flash-Next with MTP-3 speculative decoding OFF. Same weights, same NVFP4")
    print("  quant, same scheduler; speculative decoding is distribution-preserving, so the")
    print("  POLICY is held fixed while VOLUME moves. A kernel push spends GPU quota, not the")
    print("  daily submission slot.")


if __name__ == "__main__":
    main()
