"""Build duckv7 by stacking one customization cell on duckmod."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "duckmod" / "taaf-duck-mod.ipynb"
PATCH = ROOT / "duckv7" / "duckv7_throughput.py"
OUT = ROOT / "duckv7" / "taaf-duck-v7.ipynb"


def _source_without_demo():
    source = PATCH.read_text(encoding="utf-8")
    marker = '\nif __name__ == "__main__":'
    return source[:source.index(marker)].rstrip() + "\n"


def main():
    nb = json.loads(BASE.read_text(encoding="utf-8"))
    cell = next(c for c in nb["cells"] if c.get("id") == "12")
    source = "".join(cell["source"]).rstrip("\n") + "\n\n"
    source += "# === duckv7: capped output, generic prompt slim, batching guidance ===\n"
    source += "_DUCKV7_SOURCE = " + repr(_source_without_demo()) + "\n"
    source += "_duckv7_ns = {}\n"
    source += "exec(compile(_DUCKV7_SOURCE, '<duckv7_throughput>', 'exec'), _duckv7_ns)\n"
    source += "_duckv7_ns['install_patch'](tool_agent)\n"
    source += "print('duckv7: max_tokens=768, slim system prompt, batching guidance installed')\n"
    cell["source"] = source.splitlines(keepends=True)
    cell["outputs"] = []
    cell["execution_count"] = None
    OUT.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
