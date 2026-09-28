You compile ONE sentence, written by an AI agent playing a 64x64 grid puzzle game, into ONE transition hypothesis in a
fixed JSON language, or into NONE.

The board below is what the agent was looking at when it wrote the sentence. Use it ONLY to resolve what the
sentence refers to ("the piece", "the block", "the red bar") into a colour and a region. Do not add a claim the
sentence does not make.

Board: 64 rows of 64 characters, row 0 at the top, column 0 at the left. Each character is one cell's colour:
W white, w light gray, g gray, G dark gray, c charcoal, B black, M magenta, P pink, R red, b blue, S sky blue,
Y yellow, O orange, r dark red, N light green, p purple.
Actions: UP, DOWN, LEFT, RIGHT, SPACE, RESET, ACTION1..ACTION7, and clicks. A click is logged as MOUSE(row=R, col=C).

Output language (JSON):
{"action": {"name": "UP"|"DOWN"|"LEFT"|"RIGHT"|"SPACE"|"RESET"|"ACTION1".."ACTION7"} | {"name": "CLICK"} | {"name": "CLICK", "at": [row, col]},
 "target": {"color": "<one colour letter>", "region": [r0, r1, c0, c1]},
 "effect": {"type": "move", "dr": <int>, "dc": <int>}
         | {"type": "recolor", "from": "<letter>", "to": "<letter>"}
         | {"type": "appear"} | {"type": "disappear"}
         | {"type": "no_change"} | {"type": "any_change"}
         | {"type": "count_delta", "delta": <int>}}
- "region" is optional, with inclusive bounds; omit it to mean the whole board. Cells of the target colour inside
  the region are the object. For recolor, "from" is the colour looked at and "to" is the colour after.
- move dr/dc is the displacement in cells per action (dr > 0 is down, dc > 0 is right).
- Use {"name": "CLICK", "at": [row, col]} only if the sentence gives or clearly implies a click position.

Answer NONE when the sentence states no checkable rule about what an action does to the board: a plan, a question,
a single past event with no general claim, or a claim whose action, target or effect cannot be tied to the board.

Return ONLY the JSON object, or the single word NONE. No prose, no code fence.

GAME: {game}
LEVEL: {level}
SENTENCE: {sentence}
BOARD:
{board}
