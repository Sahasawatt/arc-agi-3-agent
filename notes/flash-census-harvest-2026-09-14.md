# The shipped chassis is in the census now — R57's "next action", done at 0 slots and 0 GPU

**2026-09-14, from the Windows box that holds the `sahasawatt` Kaggle token.** R57 / `next-session-prompt.md`
established that every pricing instrument in `eval/` was blind to the Flash-Next chassis we actually submit
(`per-level-census.json` held 21 runs and zero Flash rows; `oracle_ceiling.py`'s `LEDGER_PUBLIC` 19 runs, none
Flash) and named the harvest as the one action three independent axes converged on — then recorded it as blocked
for want of credentials. The block was machine-specific: the handoff's credential probe ran on a box with no token.
This one has it (used the same night for three kernel pushes and every `kernels_logs` read below).

No ticket id is minted here: MAP's highest id on `origin/master` (`4a565e2`) is B79 and the maintainer's LEDGER row
calls B80 "PROPOSED and unminted", so this note carries no number and adds no MAP row.

## What was harvested

Five full-25 Flash-Next runs, into `eval/fixtures/per-level-census.json` under the same schema as the 21 banked rows,
by the new `eval/flash_census_harvest.py`:

| run | owner | actions (audit = LEDGER) | levels | public | hidden |
|---|---|---|---|---|---|
| `thui-fast-v0-d2` | sahasawatt | 3,553 | 41 | 9.32 | 3.21 |
| `thui-a7-v1-d2` | sahasawatt | 3,466 | 37 | 8.23 | — |
| `thui-a7-full25-r1` | yocybercode | 3,843 | 38 | 8.2491 | 3.32 |
| `thui-l1-v0-full25-r1` | yocybercode | 3,522 | 44 | 10.9337 | 3.60 |
| `thui-l1-ctl-full25-r1` | yocybercode | 3,528 | 41 | 8.6427 | — |

Of the four runs the handoff asked for, two are here (`thui-fast-v0` draw 2, `thui-a7-full25-r1`) and two are not:
**`yocybercode/thui-animfast-b71` and `yocybercode/thui-fast-b78-mtp0` answer 403 to every read endpoint** — they
are private on the owner's account, so the remedy is his (make them public, or push their `<slug>.log` and
`*_p0_events.jsonl`). `thui-fast-v0` **draw 1** (3,925 actions) is the version trap the handoff named, confirmed
real: the slug serves only its latest version, which is draw 2. The L1 pair was not asked for and is included because
it is the same chassis and the maintainer had already banked its LEDGER rows.

### Controls, all in the script, all fail-closed, all passed

- **P (positive, 49 pairs):** on every game present in both a run's log and its per-game events, the SPENT vector
  re-derived from events equals the log's exactly. Zero pairs would have refused the write.
- **A (audit):** every run's 25-game action sum equals its own `PUBLIC25_AUDIT` line AND the LEDGER column, 5/5.
- **S (schema):** per game, `len(per_level) == total` and `sum(SPENT) == actions`; HUMAN baselines equal the
  fixture's per-game constants (asserted identical across all 21 banked runs before use).
- **I (identity):** after the write, the 21 pre-existing rows are byte-identical; B52's original
  `per_level_census.py` prints the same 38 lines over the new fixture as over the old.
- **The scorer:** `oracle_ceiling.py`'s control now reproduces **24 of 24** published public means within 0.05,
  including all five Flash rows (10.93 / 9.32 / 8.64 / 8.25 / 8.23). That is the instrument validated on the
  shipped chassis, which is what the harvest was for.

### The trap that actually bit, which the handoff did not name

`KaggleApi().kernels_logs()` returned a copy **short one `[finished]` line** in three of four full-25 runs (fast-v0
d2 lost cd82, l1-v0 lost tu93, l1-ctl lost lp85 — 24/25, no duplicated blocks). The kernel's own `<slug>.log`
inside its output directory (`kernels_output`) carries all 25 for every one of them with the same audit total, so
the drop is an artefact of the logs endpoint. The harvest reads the output-dir log; the events path exists as
control P and as the fallback for a run with no output-dir log. The two traps the handoff did name (no version
argument; 14 repeated blocks) — the first is real and cost draw 1, the second did not occur on any of these logs.

## What the instruments say about the shipped chassis (first reading — public side only)

`python eval/per_level_census.py --family flash` (5 runs × 25 games = 125 game-runs):

| | Flash-Next (5 runs) | anim/v10 family (17 runs, B52) |
|---|---|---|
| levels cleared per game-run | **1.61** (201 / 125) | 0.89 (377 / 425) |
| STARVED / STUCK / ZERO | 51.2 % / 48.8 % / **0** | (B52's split; ZERO was B40's population) |
| cleared levels, spent/human median | 0.80 (p25 0.59, p75 1.06) | — |
| stalls BEHIND the family frontier (a sibling draw cleared that level) | **68 = 54 %** | — |
| stalls AT the frontier (no draw ever cleared it) | 57 = 46 % | — |
| best-ever oracle vs best single run | 59 vs 44 levels | 47 vs 30 (B52) |

- **ZERO games are gone.** Every one of the 125 game-runs executed actions; the old stack's zero-action population
  (B40) does not exist on this serving.
- **Half of every stall is draw variance.** 54 % of the 125 stalls sit at a level a sibling draw of the same chassis
  cleared. R57/A4 priced the hidden re-draw lottery as closed; this is the public-side shape of the same fact — the
  draws differ by which levels they happen to clear, not by how deep the chassis can go.
- **Pooling five draws reaches no deeper than the deepest single draw, in any game.** The Flash-only pointwise
  oracle is **16.05 public / 59 levels** against the best single run's 10.93 / 44 (+5.12, +15) — and per game the
  oracle depth equals the deepest single run's depth in **25 of 25**. The +15 is the sum of per-game maxima across
  runs that are each best somewhere; it is not a level nobody reached. ⚠️ The mixed-family oracle `oracle_ceiling.py`
  now prints (17.82 / 63, "19 levels of headroom") pools the old stack's reach with this one and should not be read
  as attainable on the shipped chassis; that script has no family switch yet.
- **The three games no Flash draw has ever cleared past L1 or at all:** sk48 (0/0/0 across five draws), sp80 (0/0/1),
  g50t (0/0/1). bp35, cn04, lf52, ls20 max out at 1.

⚠️ Nothing above crosses the public→hidden conversion the LEDGER forbids. The hidden column in the table is the
LEDGER's own draws, quoted, not derived.

## What this does not do

No ticket closed, no MAP row added, no slot spent, no build proposed. `abandoned_tokens.py`'s API-side `RUNS`/
`LEDGER_ACTIONS` tables were not extended (it fetches by slug and the harvest already checks actions). The two 403
runs are the owner's to unblock.

## Reproduce

```bash
ARC_SCRATCH=<scratchpad holding kout-*/> python eval/flash_census_harvest.py --dry-run
python eval/per_level_census.py --family flash
python eval/oracle_ceiling.py          # CONTROL block: 24 of 24 within 0.05
```

## Addendum 2026-09-14 21:5x — Watchara's two runs folded in (Flash family 5 -> 7)

`yocybercode/thui-animfast-b71-full25-r1` and `thui-fast-b78-mtp0-full25-r1` answered 403 on every read endpoint at 15:1x
and 200 (status / pull-metadata / list_files) at 21:45 from the same token; Watchara had said at 08:45Z he would flip them
public in the web UI, and his `kernels_pull(metadata=True)` already read `is_private=False` for both — so the earlier 403 has
no body to report. Output dirs fetched to `kout-wa-<slug>/` (25 `[finished]` lines each in the output-dir log, 25 event files).

Harvest (`--only` the two keys): CONTROL P 50/50 log-vs-events pairs exact, CONTROL A audit == LEDGER (2008 / 4049),
CONTROL I 26 pre-existing rows byte-identical; fixture now 28 runs. Scorer CONTROL 26 of 26 within 0.05 (was 24 of 24).
`FLASH` list in `eval/per_level_census.py` and `LEDGER_PUBLIC` in `eval/oracle_ceiling.py` carry the two keys; the default
census path is still byte-identical to B52's (md5 e5aa4699…, 38 lines). Watchara wrote NO fixture rows (relay 08:45Z), so
no conflict on his side.

Family read at 7 runs (175 game-runs, 280 levels): STARVED 52% / STUCK 48%; stalls behind the family frontier 60% (was 54%);
oracle 61 levels vs best single 44. Wipe-heavy games the wm A/B pre-registered: r11l 1/1/2 (7 draws, never >2), tu93 2/3/4
(b78 cleared 4), sp80 0/0/1, bp35 0/1/1, tn36 0/1/2. Per-run: b78-mtp0 40 levels (r11l 2, tu93 4, sp80 1, tn36 2) at public
6.96 — the most levels-per-point in the family, i.e. depth and the score diverge on where the levels land.
