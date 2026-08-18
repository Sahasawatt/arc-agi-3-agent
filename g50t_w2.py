"""g50t_w2.py -- replay the extracted g50t win line RAW (no agent), twice, on
fresh envs. Verifies the sequence recorded by g50t_w1.py is deterministic and
reaches levels_completed==1 at the same event index both times.
"""
import json
import sys

import numpy as np
import arc_agi

SEED = 0


def replay(events, run_label):
    arc = arc_agi.Arcade()
    env = arc.make("g50t", seed=SEED)
    action_lookup = {a.value: a for a in env.action_space}
    clicker = next((a for a in env.action_space if a.is_complex()), None)

    obs = None
    win_idx = None
    for i, ev in enumerate(events):
        if ev == "RESET":
            obs = env.reset()
        elif isinstance(ev, list) and ev[0] == "click":
            _, y, x = ev
            data = {"x": int(x), "y": int(y)}
            if clicker is not None:
                try:
                    clicker.set_data(data)
                except Exception:
                    pass
            obs = env.step(clicker, data=data)
        else:
            obs = env.step(action_lookup[int(ev)], data=None)

        if obs is None:
            print(f"[{run_label}] obs=None at event idx {i}, aborting replay")
            return None
        if obs.levels_completed >= 1:
            win_idx = i
            print(f"[{run_label}] WIN at event idx {i} (levels_completed={obs.levels_completed})")
            break

    if win_idx is None:
        print(f"[{run_label}] did NOT reach levels_completed>=1 "
              f"(final levels_completed={obs.levels_completed if obs else '?'})")
    return win_idx


def main():
    with open("results/g50t-win-events.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    events = data["events"]
    expected_idx = data["win_event_idx"]
    print(f"loaded {len(events)} events, expected win idx {expected_idx}")

    idx1 = replay(events, "run1")
    idx2 = replay(events, "run2")

    ok = (idx1 == expected_idx and idx2 == expected_idx)
    print(f"run1_idx={idx1} run2_idx={idx2} expected={expected_idx} "
          f"MATCH={ok}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
