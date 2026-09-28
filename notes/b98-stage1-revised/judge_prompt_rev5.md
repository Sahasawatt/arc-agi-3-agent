You are labelling sentences an AI agent wrote while playing grid puzzle games (ARC-AGI-3). Each sentence comes from
the agent's own reasoning. For EACH item decide, independently of the others:

kind — exactly one of:
- "rule": a GENERAL claim about what an action, or a kind of action, does in this game. It is meant to hold
  beyond one occasion. Examples of the shape: "RIGHT moves the block 3 cells", "clicking toggles the tile and its
  neighbours", "each press shifts the column up by one", "when SPACE is pressed the box turns white".
- "observation": a report of what happened on one specific past occasion ("that click removed the red cell").
- "prediction": a claim about what one specific upcoming action will do ("the next UP should reach the door").
- "plan_or_question": an intended action, a question, a hypothetical, a guess being considered, or musing.

checkable — true only if the sentence names an action, a target on the board, and an effect precise enough to be
checked against stored before/after 64x64 colour boards of that game's transitions; otherwise false.

predicate — when checkable is true, fill "action", "target", "effect" with short phrases taken from the sentence;
otherwise use empty strings.

Judge only the sentence text. You have no board and no game; do not guess what the game is. Some items are control
sentences that state nothing about any action; label them honestly like any other.

OUTPUT: a JSON array, one object per input item, in any order:
[{"id": "<item id>", "kind": "rule|observation|prediction|plan_or_question", "checkable": true|false,
  "predicate": {"action": "", "target": "", "effect": ""}, "why": "<= 20 words"}]
Return ONLY the JSON array: no prose, no code fence. Every input id must appear exactly once.

ITEMS (JSON, fields id and text only):
