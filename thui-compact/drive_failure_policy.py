"""Drive the real compaction payload without a model or game files."""
import contextlib
import io
from drive_block_counter import BUILDER, CONFIGS, StubAgent, StubResult, load


def check_empty(config):
    ns, _ = load(BUILDER.read_text(), config)
    a = StubAgent("unit", ["[assistant] observed move"])
    ns["_compact_memento"](a, "K")
    old = a._compact_state["memento"]
    a._compact_state["pending_check"] = False
    a._compact_state["buffer"] = ["[assistant] new observation"]
    a._chat_completion = lambda *args, **kw: StubResult("  ")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        ns["_compact_memento"](a, "K")
    assert a._compact_state["memento"] == old
    assert a._compact_state["errors"] == 1, "empty output must advance circuit breaker"
    assert not a._compact_state["pending_check"], "empty output is not a new memento"
    assert "outcome=empty" in out.getvalue()
    assert "labels=5/5" not in out.getvalue(), "must not credit stale labels"
    assert a._max_output_tokens == 4096
    assert ns["_COMPACT_THINK"].local.v is None


def check_sequence(config, source=None):
    ns, _ = load(source or BUILDER.read_text(), config)
    a = StubAgent("unit", [])
    fire = ns["_compact_memento"]
    def fail(*args, **kw):
        raise TimeoutError("test endpoint")
    for response, errors in [(fail, 1), (lambda *a, **k: StubResult("Rules: recovered"), 0),
                             (lambda *a, **k: StubResult(""), 1), (fail, 2)]:
        a._compact_state["buffer"] = ["[assistant] observation"]
        a._chat_completion = response
        with contextlib.redirect_stdout(io.StringIO()):
            fire(a, "K")
        assert a._compact_state["errors"] == errors
        assert a._compact_state["buffer"] == [], "failure buffer remains bounded"
        assert a._max_output_tokens == 4096
        assert ns["_COMPACT_THINK"].local.v is None
    assert a._compact_state["disabled"]
    assert ns["_COMPACT_STATS"]["disabled_games"] == 1
    assert ns["_COMPACT_STATS"]["failed_block_chars"] == 3 * len("[assistant] observation")
    assert a._compact_state["memento"] == "Rules: recovered"


if __name__ == "__main__":
    for name, config in CONFIGS.items():
        check_empty(config)
        check_sequence(config)
        print(name.strip(), "empty/exception/recovery/circuit/accounting PASS")
        source = BUILDER.read_text()
        for old, new in [('_COMPACT_STATS["failed_block_chars"] += len(block)', 'pass'),
                         ('st["errors"] = st.get("errors", 0) + 1', 'st["errors"] = 0'),
                         ('st["errors"] = 0\n    st["memento"]', 'st["errors"] = 1\n    st["memento"]')]:
            assert old in source
            try:
                check_sequence(config, source.replace(old, new))
            except AssertionError:
                print("mutation detected:", old.splitlines()[0])
            else:
                raise AssertionError("mutation escaped: " + old)
