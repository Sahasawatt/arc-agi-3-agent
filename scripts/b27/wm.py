"""Extract the carried world model block from a transcript turn.

The block runs from the re-injection marker to the literal 'end of world model.'
Everything after that line is fixed harness boilerplate — including a sentence that
NAMES every prefix ('World model:', 'Goal model:', 'Action model:', ...), so failing to
trim makes every prefix appear on 100% of turns and makes any similarity measure ~1.0.
"""
MARK = "Working world model carried from earlier turns:"
STOP = "end of world model."

def carried(turn):
    i = turn.find(MARK)
    if i < 0:
        return None
    i += len(MARK)
    j = turn.find(STOP, i)
    return turn[i:j if j >= 0 else len(turn)].strip()
