# B63 — prefix caching: the headroom measured from vLLM's own logs, and why it is not the binding constraint

**Measurement, 2026-09-03 ($0, no build).** Lever 4 of
`arc-agi-pub/notes/deep-research-arc3-sota-now-2026-09-03.md`: Tufa flag prefix caching as *"not
optimally used"* in the duck harness. Before building anything, read what the engine already reports.
Instrument: `vllm-openai-server.log` in each kernel's output (vLLM v0.19.0 `loggers.py` line every 10 s:
prompt/generation throughput, running/waiting reqs, KV usage, **cumulative prefix-cache hit rate**), plus
`history_messages: N` from every `ANALYZER STATUS` block in the `_p0_events.jsonl` sidecars.

Proposed MAP row:

> | B63 | measure | **Prefix caching is ON (`--enable-prefix-caching`, `framework/kaggle.py:330`) and hits 25 % — the history prefix is invalidated almost every turn by front-eviction once the context saturates (turn ~5). Pinning the prefix could roughly double the hit rate, worth ≈ 15 % of engine time. But B54 already showed a 31 % throughput LOSS with levels flat (28 → 28), so throughput is not binding at this clock; a throughput-only lever has no path to levels. Closed without a build.** | closed |

## What the logs say

| run | engine windows | prompt tokens prefilled | generated tokens | prefix hit (cumulative, final) | max hit seen | KV usage max |
|---|---|---|---|---|---|---|
| thui-prior-v1 (32k window) | 796 (~2.2 h) | ~19.0 M | ~2.6 M | **24.7 %** | 72 % (early) | 83 % |
| thui-v3-1 (32k) | 800 | ~19.8 M | ~2.6 M | **25.9 %** | 77 % | 87 % |
| thui-v6-0 (49k window, B54) | 793 | ~23.1 M | ~1.7 M | **0.0 %** | 74 % (early) | **100 %** |

Prefill is **7–14× the generated volume**. At the observed prefill ceiling (~8 k tok/s) 19 M prompt tokens
is ≈ 40 min of engine time inside a 2.2 h run — so the cache is worth measuring. It is on, and it hits a
quarter of the time.

**Why a quarter.** `history_messages` per turn saturates by turn ~5 and then oscillates (+3 per turn,
then a drop): e.g. `7, 10, 13, 16, 14, 17, 17, 17, 17, 20, 18, 21, 18, …` (prior-v1), modes 15–18. That is
`_drop_oldest_history_block` (`tool_agent.py:1608`) firing on most turns once the 32 k budget is full —
and dropping the OLDEST block shifts every later token, so the only stable prefix is the system prompt +
tool schema (≈ a quarter of a ~22 k-token request). The 72–77 % maxima are the first few turns of each
game, before saturation, when nothing has been evicted yet.

**B54's mechanism, found by accident.** thui-v6-0 raised the window to 49 152; its history plateaus at
36–42 messages, KV usage peaks at **100 %**, and the cumulative prefix hit rate is **0.0 %** at the end of
the run — the larger contexts pushed cached blocks out of the KV pool, so every request re-prefilled
everything. That is the 0.69× throughput B54 recorded, with a cause: not "longer prompts" alone, but the
cache collapsing under them.

## The lever, priced

A middle-eviction policy (pin the system prompt + the first K turns, evict the block after them) keeps
a stable prefix through saturation. Ceiling = the early-turn hit rates, 72–77 %; a realistic pinned
fraction (half the budget) lands around 50–60 %. Saving ≈ 6–8 M prefill tokens per run ≈ 15 % of engine
time → more turns per game inside the clock.

## Why it closes without a build

Throughput has already been varied on this harness and levels did not move: B54 paid **0.69×** (requests
1306 → 905, generated tokens 1.39 M vs 2.0–2.2 M band) and cleared **28 → 28** levels, `p = 0.4333`, hidden
1.26 inside the family pool. If losing 31 % of throughput costs zero levels, gaining 15 % cannot be read on
the level instrument either — the clock is not what stops the agent (B52: 67 % STARVED / 31 % STUCK are
decision failures, not budget failures). The lever stays on file for a future build where the clock
binds (a larger model, a shorter clock, or a per-game step cap that today's runs never reach).

## Where the extra turns would land — measured

Every one of the 75 games in the three runs ends with the agent **still playing** (last action event:
no `run_complete`, no `game_over`) — the clock ends every game, so a throughput gain does buy turns.
The question is what a late turn is worth. Position of each level clear inside its game, as a fraction
of that game's executed actions:

| run | clears | p25 | median | p75 | in the last quarter | in the last 10 % |
|---|---|---|---|---|---|---|
| thui-prior-v1 | 20 | 0.24 | 0.42 | 0.53 | 2 (10 %) | — |
| thui-v3-1 | 26 | 0.21 | 0.35 | 0.67 | 5 (19 %) | — |
| thui-v6-0 | 18 | 0.23 | 0.38 | 0.61 | 2 (11 %) | — |
| **pooled** | **64** | | **0.40** | | **14 %** | **6 %** |

A 15 % throughput gain extends every game by roughly its last 15 % of actions — the band where **~6 %
of all clears** happen: ≈ 1.3 expected extra clears per 25-game run, under the B35 floor (+1 level in
≥ 6 games) by a wide margin. That is the arithmetic behind B54's flat 28 → 28 at 0.69×, and it is why
this closes without a build.

## What would reopen it

A build whose clears move late — if a future arm's median clear position rises past ~0.6, or the
last-quarter share past ~30 %, turns at the end of the clock start to matter and this lever is worth a
smoke. Re-run the census above (`action` events, `level_completed`, position / total) on that arm's
sidecars before spending GPU on it.
