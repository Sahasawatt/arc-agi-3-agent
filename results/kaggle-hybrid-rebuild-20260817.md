# Kaggle HYBRID bundle rebuild — 2026-08-17

Rebuild + verify only. **No push, no submit, no `.kaggle/` access.**

## 1. What `kaggle/bundle_hybrid.py` produced

Per its own docstring, **output goes to the STARTER KIT, not into this repo** — the
bundle embeds a third party's MIT source (StochasticGoose, Tufa Labs) verbatim, and
this repo is MIT-0, so a repo-side copy would relicense someone else's work. There is
therefore no separate "repo bundle" to diff against a "starter copy" — the script
writes `<starter>\agent\my_agent_hybrid.py` directly and only there. This differs
from the task brief's assumed shape (step 3 asked to "copy the rebuilt hybrid into
the starter"); flagging the discrepancy rather than inventing a repo-side copy that
doesn't exist. `kaggle/bundle.py` and `kaggle/my_agent.py` (the v9-lite bundle) are
confirmed untouched by this script (git status: no changes under those paths).

Backed up the pre-rebuild starter file to the scratch dir before running anything:

| | size (bytes) | sha256 |
|---|---|---|
| OLD (backed up, pre-rebuild) | 231,388 | `f84adb3e555442d328f4197ea814b9af84eef633bed1f14e31fea213c331c4c7` |
| NEW (`bundle_hybrid.py` output) | 233,452 | `56aa957f30f2badc50b5dc26f655f9d47d5db6fb5799b155a8a3eac3b24fc56b` |

```
$ PYTHONUTF8=1 ./.venv/Scripts/python.exe kaggle/bundle_hybrid.py
wrote C:\Users\Vampi\Desktop\ARC-AGI-3-Kaggle-Starter\agent\my_agent_hybrid.py (233452 bytes)
```

Line-level diff (Python `difflib`, not `diff`/`grep` — `rtk` rewrites both, see
`~/.claude/RTK.md`): **251 lines both sides, exactly ONE opcode changed** — line 53,
the embedded `mirror = _load("mirror", "<blob>")` payload. This is exactly what the
docstring's mechanism predicts (23 modules embedded as static blobs; only the one
whose source changed since the last build gets a new blob) and matches the same
"exactly one line, the mirror payload" shape `CLAUDE.md` records for the v9-lite
rebuild on 2026-08-16 (that one fixed a bundle missing ar25's L3/L4 driver lines).

## 2. Checker output — `kaggle_hybrid_check.py` (new file, repo root)

Adapted from the repo's existing `kaggle_bundle_check.py` (which checks the v9-lite
bundle). Same 5-assertion shape plus one hybrid-specific check: exec in a fresh
namespace → every declared module (+ `_goose`, the extracted sample agent) reaches
`sys.modules` → all 14 whole-game drivers present → the agent class exists and
inherits `GooseAgent` (the sample base — confirms this is actually a *hybrid*, not
a driver-only bundle) → every driver exposes `signature()`, **and** the embedded
`mirror` module's source — decoded zlib+base64 in memory the same way the bundle's
own `_load()` decodes it at exec time, never by grepping the compressed bytes —
contains `L3_LINE` and `L4_LINE`. Takes an optional bundle-path argument (defaults
to the starter copy, since that's the only artifact that exists).

**Run 1 — repo's own venv** (`./.venv/Scripts/python.exe`, `PYTHONPATH` set to the
starter's vendored agents package): **FAILS at step 1**, and correctly so — this is
an environment fault, not a bundle fault, and it is itself a useful finding:

```
bundle: C:\Users\Vampi\Desktop\ARC-AGI-3-Kaggle-Starter\agent\my_agent_hybrid.py  233201 chars
MODULES declared in bundle_hybrid.py: 23 -> [...]  (+_goose)
FAIL 1: bundle did not exec -- ModuleNotFoundError: No module named 'torch'
```

The embedded sample agent (`GooseAgent`, StochasticGoose) depends on `torch` for its
learned coordinate head. `torch` lives in the **starter kit's own venv**
(`2.13.0+cpu`, confirmed), not in this repo's venv (confirmed absent). This is a real
constraint on the earlier "step 2 verify from the ARC repo" framing — the v9-lite
checker never hits this because `kaggle/my_agent.py` has no sample-agent dependency
on torch; the hybrid does, unavoidably, because it embeds the sample.

**Run 2 — starter kit's own venv** (`<starter>\.venv\Scripts\python.exe`, same
`PYTHONPATH`), against the same file: **ALL CHECKS PASS**, this is the run that
matters (task step 4):

```
bundle: C:\Users\Vampi\Desktop\ARC-AGI-3-Kaggle-Starter/agent/my_agent_hybrid.py  233201 chars
MODULES declared in bundle_hybrid.py: 23 -> ['identity', 'perception', 'signals', 'trace', 'discover', 'plan', 'gate', 'cover', 'swap', 'haul', 'maze', 'dial', 'skewer', 'tape', 'bridge', 'sorter', 'ferry', 'claw', 'mirror', 'twin', 'roller', 'scoring', 'compete']  (+_goose)
PASS 1: bundle exec'd
PASS 2: every declared module registered (incl. _goose)
PASS 3: all 14 drivers present
PASS 4: agent class = MyAgent
      -- inherits GooseAgent (sample base): True
PASS 5a: every driver exposes signature()
PASS 5b: embedded mirror.py decodes and contains L3_LINE and L4_LINE

modules pulled in by the exec: 1585
ALL CHECKS PASSED -- the hybrid bundle is complete, loadable, and current.
```

Commands, exactly as run:

```bash
# Run 1 (repo venv — informative failure, not the gate)
cd C:\Users\Vampi\Desktop\projects\arc-agi-3-agent
PYTHONUTF8=1 PYTHONPATH="C:\Users\Vampi\Desktop\ARC-AGI-3-Kaggle-Starter\vendor\ARC-AGI-3-Agents" ./.venv/Scripts/python.exe kaggle_hybrid_check.py

# Run 2 (starter venv — the real gate; passes 5/5)
cd C:\Users\Vampi\Desktop\projects\arc-agi-3-agent
PYTHONUTF8=1 PYTHONPATH="C:\Users\Vampi\Desktop\ARC-AGI-3-Kaggle-Starter\vendor\ARC-AGI-3-Agents" "C:\Users\Vampi\Desktop\ARC-AGI-3-Kaggle-Starter\.venv\Scripts\python.exe" kaggle_hybrid_check.py "C:\Users\Vampi\Desktop\ARC-AGI-3-Kaggle-Starter\agent\my_agent_hybrid.py"
```

## 3. "Copy into starter" / byte-compare

There is no separate repo-side bundle to copy (see §1) — `bundle_hybrid.py` writes
the rebuilt file directly and only to `<starter>\agent\my_agent_hybrid.py`. The
meaningful byte-compare actually done is OLD (pre-rebuild, backed up to scratch)
vs NEW (post-rebuild, in place at the starter) — table and diff above in §1. They
differ (sha256 mismatch, as expected — the mirror payload changed), and the diff
is exactly the one line the mechanism predicts, nothing else.

## 4. What was NOT done (explicit)

- **No `kaggle` CLI command was run.** No `kernels push`, no `kernels status`, no
  `competitions submit`.
- **`.kaggle/` was never read, grepped, or listed**, and its contents were never
  logged.
- **No push, no submit.**
- **No driver files were edited.** `git status --short` shows only
  `kaggle_hybrid_check.py` as new under this task's scope; `kaggle/bundle.py` and
  `kaggle/my_agent.py` (v9-lite) are unmodified. (Other pre-existing modified/
  untracked files in the tree — `CLAUDE.md`, `notes/next-session-prompt.md`,
  `results/breadth-recon.md`, two `results/pytest-final*.txt`, and a long list of
  `ar25_q*.py` / other scratch scripts — predate this task and were not touched by
  it; several are consistent with the background sp80 job the hard rules say not to
  kill.)
- **UNVERIFIED / open for the main thread:** `<starter>\scripts\build_notebook.py`
  hardcodes `AGENT_SRC = ROOT / "agent" / "my_agent.py"` (the v9-lite bundle) with
  no CLI override — it does **not** reference `my_agent_hybrid.py`. Submitting the
  HYBRID tomorrow therefore needs one more decision this task was not scoped to
  make: either point `AGENT_SRC` at `agent/my_agent_hybrid.py` (a one-line edit to
  a tracked starter-kit file) or temporarily copy `my_agent_hybrid.py` over
  `my_agent.py` before building (destructive to the v9-lite source unless backed up
  first, the same way this task backed up before overwriting). Neither was decided
  or done here.

## 5. Commands for the main thread to run tomorrow

Decide the `AGENT_SRC` question in §4 first — the commands below assume it has been
resolved (i.e. `scripts/build_notebook.py` will splice whichever agent file is now
pointed at). Run from `C:\Users\Vampi\Desktop\ARC-AGI-3-Kaggle-Starter`, its own venv:

```bash
PYTHONUTF8=1 ./.venv/Scripts/python.exe scripts/build_notebook.py
KAGGLE_API_TOKEN=$(cat .kaggle/access_token) ./.venv/Scripts/kaggle.exe kernels push -p notebooks/
KAGGLE_API_TOKEN=$(cat .kaggle/access_token) ./.venv/Scripts/kaggle.exe kernels status sahasawatt/arc-prize-2026-arc-agi-3-starter
```

Then, after the kernel run completes (background `wait_for_kernel.py`, polled from
the **main thread** — a subagent-started background job dies with the subagent) and
its log has been read (a fast `COMPLETE` can mean a silent worker death, not a real
7+ hour play run — `CLAUDE.md` already documents this trap):

```bash
KAGGLE_API_TOKEN=$(cat .kaggle/access_token) ./.venv/Scripts/kaggle.exe competitions submit -c arc-prize-2026-arc-agi-3 -f submission.parquet -k sahasawatt/arc-prize-2026-arc-agi-3-starter -m "hybrid: sample base + 14 measured drivers, mirror L3/L4 current (rebuilt 2026-08-17)" -v <next-version>
```

(This submit command stands alone — not chained with `&&` after the push/status
commands above, so a stray placeholder cannot cascade into something else running.
`<next-version>` is a placeholder: fill in the actual next kernel version number
before running.) Quota is 1/day — verify any "blocked" reading against
`competitions submissions`, never against the submit command's bare error text
(`CLAUDE.md`, `kaggle_api_token` section already documents the 400-hides-the-reason
trap).
