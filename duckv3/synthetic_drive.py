"""Synthetic multi-turn drive of GameObservation.render(), simulating how
tool_agent.py actually calls it: once per turn, with history_entries growing
by however many actions were taken that turn (analyze() reloads the full
history from disk each call -- see runtime_state.load_runtime_state).

Reports per-turn OBSERVATION block size (chars, and both the repo's usual
chars/4 token estimate and the harness's own cruder chars/3 estimate from
tool_agent.py's _estimate_tokens), plus the one-time system-prompt paragraph
cost, for a like-for-like comparison against duckmod's measured ~450-500
chars/turn system-prompt tax (results/duckmod-transcripts-20260819.md).

Run: python duckv3/synthetic_drive.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from duckv3_observer import GameObservation  # noqa: E402


class _F:
    def __init__(self, grid):
        self.grid = grid


class _H:
    def __init__(self, action, grid):
        self.action = action
        self.frame = _F(grid)


def synth_board(rng, w, h, clock, agent_pos, seen_positions):
    """8x8-ish board: a corner clock cell ticks every step (HUD), an agent
    cell moves around a handful of positions (so it revisits states), and a
    couple of fixed obstacle cells never move -- a plausible small ARC board."""
    grid = [[1 for _ in range(w)] for _ in range(h)]
    grid[0][0] = clock
    grid[3][3] = 5  # fixed obstacle
    ar, ac = agent_pos
    grid[ar][ac] = 8
    return tuple(tuple(row) for row in grid)


def main() -> None:
    rng = random.Random(1234)
    w, h = 8, 8
    actions = ["UP", "DOWN", "LEFT", "RIGHT"]
    positions = [(1, 1), (1, 2), (2, 2), (2, 1)]  # a small loop -> guarantees revisits

    obs = GameObservation()
    history = []
    clock = 0
    pos_idx = 0

    history.append(_H("", synth_board(rng, w, h, clock, positions[pos_idx], set())))

    n_turns = 60
    sizes = []
    for t in range(n_turns):
        clock = 1 - clock
        pos_idx = (pos_idx + rng.choice([-1, 1])) % len(positions)
        action = rng.choice(actions)
        history.append(_H(action, synth_board(rng, w, h, clock, positions[pos_idx], set())))
        current = history[-1].frame
        block = obs.render(history, current, actions)
        sizes.append(len(block))
        if t in (0, 1, 2, 9, 29, 59):
            print(f"--- turn {t} (chars={len(block)}) ---")
            print(block)
            print()

    avg = sum(sizes) / len(sizes)
    print(f"turns={n_turns} min={min(sizes)} avg={avg:.1f} max={max(sizes)} chars")
    print(f"as tokens (chars/4): min={min(sizes)/4:.1f} avg={avg/4:.1f} max={max(sizes)/4:.1f}")
    print(f"as tokens (chars/3, harness's own _estimate_tokens): min={min(sizes)/3:.1f} avg={avg/3:.1f} max={max(sizes)/3:.1f}")

    system_paragraph_chars = 272  # measured in verify_notebook.py: STRUCTURED_RUNTIME_STATE_ADDENDUM +272
    total_avg_chars = system_paragraph_chars + avg
    total_max_chars = system_paragraph_chars + max(sizes)
    print()
    print(f"system-prompt paragraph (resent every turn, same accounting duckmod used): {system_paragraph_chars} chars")
    print(f"TOTAL per-turn cost (system paragraph + block), avg case: {total_avg_chars:.0f} chars "
          f"= {total_avg_chars/4:.1f} tok (chars/4) / {total_avg_chars/3:.1f} tok (chars/3)")
    print(f"TOTAL per-turn cost (system paragraph + block), worst case seen: {total_max_chars:.0f} chars "
          f"= {total_max_chars/4:.1f} tok (chars/4) / {total_max_chars/3:.1f} tok (chars/3)")
    print(f"duckmod's own measured system-prompt tax: 1,835 chars once (~450-500 tok/turn per their report)")


if __name__ == "__main__":
    main()
