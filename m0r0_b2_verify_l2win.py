"""m0r0 L2 WIN verify -- the deepcopy BFS in m0r0_b1_l2bfs.py found levels_completed
>= 2 at depth 23 from the L2 root: (2,3,3,3,2,2,2,4,4,1,4,4,2,2,2,2,2,2,4,4,4,1,3).
This CONTRADICTS results/breadth-recon.md's "m0r0 L2 CLOSED for the campaign"
verdict (the diagonal-meeting-cell hypothesis was unreachable, but that was a
hypothesis about the win condition, not an exhaustive search for one).

Campaign standard before trusting a BFS win: verify x2 fresh, plus a one-action-
short control that must NOT complete. All three runs fresh envs, full replay
from reset (no deepcopy in the verify -- this is the ground-truth check).

    ./.venv/Scripts/python.exe m0r0_b2_verify_l2win.py > results/m0r0-b2-verify.txt
"""
import numpy as np
import arc_agi

from twin import L1_LINE

L2_LINE = (2, 3, 3, 3, 2, 2, 2, 4, 4, 1, 4, 4, 2, 2, 2, 2, 2, 2, 4, 4, 4, 1, 3)
FULL_LINE = L1_LINE + L2_LINE


def run(actions, label):
    arc = arc_agi.Arcade()
    env = arc.make("m0r0")
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    for i, act in enumerate(actions):
        obs = env.step(A[act])
    print(f"{label}: {len(actions)} actions -> levels_completed={obs.levels_completed} "
          f"state={obs.state}")
    return obs


if __name__ == "__main__":
    print(f"FULL_LINE length = {len(FULL_LINE)} (L1={len(L1_LINE)} + L2={len(L2_LINE)})")

    o1 = run(FULL_LINE, "RUN1 (full line)")
    assert o1.levels_completed >= 2, "RUN1 did not confirm the win"

    o2 = run(FULL_LINE, "RUN2 (full line, repeat)")
    assert o2.levels_completed >= 2, "RUN2 did not confirm the win"

    o3 = run(FULL_LINE[:-1], "CONTROL (one action short)")
    print(f"CONTROL levels_completed={o3.levels_completed} "
          f"(expect 1, i.e. NOT yet cleared L2)")

    print("\n=== VERDICT ===")
    ok = (o1.levels_completed >= 2 and o2.levels_completed >= 2
          and o3.levels_completed == 1)
    print("WIN CONFIRMED x2 + one-short control holds" if ok
          else "!! NOT CONFIRMED -- do not report as a win")
