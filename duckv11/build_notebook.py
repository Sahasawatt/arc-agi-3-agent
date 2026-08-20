"""Build duckv11/taaf-duck-v11.ipynb — v8 (Qwen3.8, uncapped) + a PROMPT-LEVEL brevity
instruction. The safe form of R16's recommendation.

R16 measured the diagnosis: 90.2% of generated characters are reasoning, tokens/action is
2.71x the Qwen3.6 baseline and seconds/action 2.13x, so deliberation is what spends the
7,920s clock. R16 then recommended a thinking-only token budget — and R17 proved the stack
has no such knob (vLLM 0.19 exposes only `chat_template_kwargs.enable_thinking` on/off plus
a TOTAL `max_tokens`, and a total cap is what collapsed v9 to 0.22 by truncating the tool
call). So the only intervention that cannot truncate an action is to ASK for shorter
reasoning in the system prompt.

Falsifiable prediction: actions rise above v8's 1,946 with levels >= 22 and no rise in
malformed tool calls (v8: 264/266 tool_calls, 2 stop, zero `length`).

Run:  python duckv11/build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_NB = REPO / "duckv8" / "taaf-duck-v8.ipynb"
OUT_NB = REPO / "duckv11" / "taaf-duck-v11.ipynb"

BREVITY = (
    "\\n- Keep deliberation SHORT. Aim for under ~300 words of reasoning per turn: state the"
    "\\n  hypothesis you are testing and the action that tests it, then act. The environment"
    "\\n  answers questions faster than analysis does, and every game ends on a wall clock"
    "\\n  that reasoning shares with acting. Never shorten the tool call itself."
)

# Appended to the same global duckmod already extends, for the same documented reason:
# _build_system_prompt resolves the bare name against tool_agent's globals.
CELL12 = (
    "# duckv11: v8 + prompt-level brevity (R16 diagnosis, R17 feasibility).\n"
    "import inference.agent.tool_agent as tool_agent\n"
    "\n"
    f'_BREVITY_TEXT = "{BREVITY}"\n'
    "\n"
    "assert isinstance(getattr(tool_agent, 'PYTHON_ADDENDUM', None), str), (\n"
    "    'duckv11: tool_agent.PYTHON_ADDENDUM missing or not a str - patch point moved'\n"
    ")\n"
    "assert 'Keep deliberation SHORT' not in tool_agent.PYTHON_ADDENDUM, 'duckv11: already patched'\n"
    "tool_agent.PYTHON_ADDENDUM = tool_agent.PYTHON_ADDENDUM + _BREVITY_TEXT\n"
    "print(f'duckv11: brevity addendum +{len(_BREVITY_TEXT)} chars; output stays UNCAPPED')\n"
)


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    base = json.loads((REPO / "duckmod" / "taaf-duck-mod.ipynb").read_text(encoding="utf-8"))

    c8 = "".join(nb["cells"][8]["source"])
    assert "jakobbrggen" in c8 and "Qwen3.8-27B-FP8" in c8, "v8 base: model swap missing"
    assert "'LOCAL_ANALYZER_MAX_OUTPUT': '768'" not in c8, "v11 must stay uncapped"

    nb["cells"][12]["source"] = CELL12
    OUT_NB.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"wrote {OUT_NB} ({OUT_NB.stat().st_size} bytes)")

    out = json.loads(OUT_NB.read_text(encoding="utf-8"))
    diff = [i for i in range(len(base["cells"])) if base["cells"][i]["source"] != out["cells"][i]["source"]]
    assert diff == [6, 8, 12], f"unexpected diff vs duckmod: {diff}"
    o12 = "".join(out["cells"][12]["source"])
    assert "Keep deliberation SHORT" in o12 and "PYTHON_ADDENDUM" in o12
    print("self-check OK: v8 model swap intact, cell 12 = brevity addendum, no cap")


if __name__ == "__main__":
    main()
