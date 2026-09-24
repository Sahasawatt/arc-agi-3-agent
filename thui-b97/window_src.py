# thui-b97: rewrite the setup commands BEFORE any of them runs, so a missing anchor costs no vLLM start.
# The serving bundle embeds its whole python program in the setup command string (B54 read it the same way),
# so the two window numbers are plain assignments inside that text.
_THUI_B97_REPLACEMENTS = (
    ("VLLM_MAX_MODEL_LEN = 32768", "VLLM_MAX_MODEL_LEN = 65536"),        # the server's ceiling on prompt PLUS completion
    ("ANALYZER_CONTEXT_WINDOW = 32768", "ANALYZER_CONTEXT_WINDOW = 49152"),  # the agent's prompt budget (49152 - 1024 = 48128)
)


def _thui_b97_rewrite(commands):
    out, hits = [], 0
    for command in commands:
        for old, new in _THUI_B97_REPLACEMENTS:
            n = command.count(old)
            assert n <= 1, f"THUI_B97 anchor {old!r} appears {n} times in one command"
            if n:
                command = command.replace(old, new)
                hits += 1
        out.append(command)
    assert hits == len(_THUI_B97_REPLACEMENTS), f"THUI_B97 window anchors: {hits} of {len(_THUI_B97_REPLACEMENTS)} -- re-derive"
    # 48128 prompt budget + the worst completion ever observed (11989, B54) = 60117, under the 65536 ceiling.
    print("THUI_B97_WINDOW ok server=65536 analyzer=49152 budget=48128 kv=13.5GiB", flush=True)
    return out
