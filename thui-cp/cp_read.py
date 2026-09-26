"""Read a thui-cp run: validity first, then levels on unseen community games. 0 GPU, stdlib.
usage: python cp_read.py <kout dir> <set: smoke|A|B>
VOID (exit 2) unless: the log carries THUI_CP_GRAFT ok exactly once and one THUI_CP line per game, and benchmark.json
holds exactly the allow-listed games (none public, none quarantined)."""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SETS = json.loads((HERE / "cp_sets.json").read_text(encoding="utf-8"))
QUARANTINE = ("ft09", "ls20", "vc33")


def main():
    out, which = Path(sys.argv[1]), sys.argv[2]
    ids = SETS["smoke"] if which == "smoke" else SETS[which]
    logs = [p for p in out.glob("*.log") if not p.name.startswith("vllm")]   # the output also holds vllm-openai-server.log
    log = logs[0].read_text(encoding="utf-8", errors="replace") if logs else ""
    runs = json.loads((out / "benchmark.json").read_text(encoding="utf-8"))["game_runs"]
    got = sorted(g["game_id"] for g in runs)
    problems = []
    if log.count("THUI_CP_GRAFT ok") != 1:
        problems.append(f"THUI_CP_GRAFT ok printed {log.count('THUI_CP_GRAFT ok')}x (need 1)")
    seen = set(re.findall(r"THUI_CP game=([a-z0-9]+-[0-9a-z]+)", log))
    if seen != set(ids):
        problems.append(f"THUI_CP game lines {len(seen)} != allow-list {len(ids)}")
    if got != sorted(ids):
        problems.append(f"benchmark games differ from allow-list: extra {sorted(set(got) - set(ids))[:4]}, "
                        f"missing {sorted(set(ids) - set(got))[:4]}")
    if any(g.split("-")[0] in QUARANTINE for g in got):
        problems.append("a quarantined official game was played")
    if problems:
        print("VOID:\n  " + "\n  ".join(problems))
        sys.exit(2)
    lv = {g["game_id"]: g["levels_completed"] for g in runs}
    n = {g["game_id"]: g["number_of_levels"] for g in runs}
    l1 = sum(v >= 1 for v in lv.values()); l2 = sum(v >= 2 for v in lv.values())
    print(f"VALID {which}: {len(lv)} games, levels {sum(lv.values())} (per game {sum(lv.values()) / len(lv):.2f}), "
          f"P(L1) {l1 / len(lv):.2f}, P(L2+|L1) {l2 / max(1, l1):.2f}")
    for g in sorted(lv):
        print(f"   {g}: {lv[g]}/{n[g]}")


if __name__ == "__main__":
    main()
