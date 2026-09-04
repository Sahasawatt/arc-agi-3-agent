# B65 — Compaction of the dropped history block: the vendor's mechanism, ported at the seam duck actually loses history

**Design ticket, 2026-09-05 (Sahasawat).** From `arc-agi-pub/notes/deep-research-astra-source-level-2026-09-05.md`
(round two, 46 claims, 37 confirmed) on top of `deep-research-astra-mechanism-2026-09-04.md` (round one) and the B62
v1-1 read. The Provider Adapter harness that takes Astra from 54.8 → 99.9 is two mechanisms: replayed reasoning state
(duck already has it — `deep-research-arc3-astra-claim` §Code read) and **compaction instead of truncation**. Round two
found the compaction half as SOURCE: Codex CLI's prompt is six lines (`codex-rs/core/templates/compact/prompt.md`, c#16),
the rebuilt context is `summary + COMPACT_USER_MESSAGE_MAX_TOKENS = 20_000` of verbatim recent messages (`compact.rs`,
c#1), the trigger is a threshold (`min(user_limit, 0.9 × window)`, c#4), and the template's known defect is that it
carries no rule to preserve a prior summary (issue 14347, c#31). Evidence strength for *the mechanism*: **strong,
source-level**. Evidence that it moves *this* harness: **none** — no open-weight replication exists anywhere (round one
§3, round two §6), and B62 just landed on the base's mean.

Proposed MAP row:

> | B65 | build | **Compaction of the dropped history block.** duck loses history at `_PERSISTENT_HISTORY_ASSISTANT_TURNS = 30`, not at the token budget: on `thui-v3-1` the budget binds on 0.2% of requests while the turn window drops **22.2 turns per game** (requests − 30, 22 of 25 games exceed 30). B62 rewrote seven slots from the last 12 messages every 10 steps and read `p = 0.9978`; B65 instead summarises **what is being deleted**, when it is deleted, into a memento that is re-injected ahead of the surviving window — the shape Codex CLI ships (c#1, c#2, c#16) plus the cumulative rule its template lacks (c#31, c#32). One call per K=10 dropped turns ≈ 2 per game, priced by B62's measured 29.6 s at 25-game contention. Oracle: paired levels vs `thuiv3-pool`, B35 floor. | open |

## What is measured before a line is written ($0)

| fact | source |
|---|---|
| Context budget `31,744 = 32,768 − reply_reserve 512 − safety 512`; estimator `max(1, (len(json)+2)//3)` = chars/3 | `duck/bundle/.../tool_agent.py:945-948`, `:462-467` (localrig copy: `:149/:160/:611`) |
| History kept = last **30 assistant turns** (`_PERSISTENT_HISTORY_ASSISTANT_TURNS`), applied AFTER the token trim in `_persistent_history_messages`, called in `analyze`'s `finally` after every turn | `tool_agent.py:151`, `:1653-1670`, `:2017` |
| Token-budget truncation (`_trim_messages_for_context` → `_drop_oldest_history_block`) fires when the estimate exceeds 31,744; on `thui-v3-1` only **2 of 1,291 requests** carried prompt ≥ 30k (0.2%), peak per game median 27,501 | `:1672-1690`, `:1608-1622`; usage sidecars pulled 2026-09-04 |
| The turn window is the loss site: `thui-v3-1` requests per game median 50 / mean 51.6 / max 94; **22 of 25 games exceed 30**; implied drops Σ(requests − 30)⁺ = **555 = 22.2 per game** | usage sidecars; each request appends one assistant message, so requests ≈ assistant turns |
| An extra local call at 25-game contention costs **29.6 s mean / 50.8 s max**, and 105 such calls were **1.6%** of the clock with 0 failures | `thui-reflect-v1-1` v2 log (B62 §v1-1 paired read) |
| Thinking must be switched off **per thread** for a capped side-call (module global shared by 25 game threads) | B62 v1 post-mortem, `_ReflectThinkFlag` in `thui-reflect/build_notebook.py` |
| Codex CLI's compaction prompt (six lines: stop, write a memento — done vs owed, repeat the plan verbatim, TODOs with locations, what needs tests, bugs/quirks for the next agent); no "carry the previous summary" rule; users add one | round two c#16, c#31, c#32 |
| Codex rebuilds context as summary + up to 20k tokens of verbatim recent user messages; mid-turn compaction re-injects world state before the last user message | c#1, c#2 |
| The Foundation's reference agent resets both histories at level transition — the same choice as duck's six-of-seven slot wipe | c#46 |

## Why B62's null does not close this axis

B62 changed the **content** of the seven slots (rewritten from the last 12 messages, i.e. from turns that were still in
the window) and never touched what was dropped. B65 changes what happens to the **deleted** turns. The two are
different memory policies at the same seam; the B62 null says the slot rewrite adds nothing to a window that still
holds those turns, and says nothing about turns the window has already lost. It is also the last untested member of
the family Astra's evidence points at: after B65, "more context / better memory" has been tried as frames (B17), window
(B54), yield (B48), slot rewrite (B62) and compaction (B65), and the family closes on measurement either way.

## Seam (builder `thui-compact/build_notebook.py`, base = B48 chassis, cells 0 / 12 / 14)

Cell 12 appends after the chassis's own block; nothing in cells 6/8 changes (same model, wheelhouse, seed, yield):

1. **Class-level wrap of `ToolAgent._persistent_history_messages`.** Before delegating, snapshot the assistant turns in
   `messages`; after, diff against the returned history — the assistant turns (with their tool results) no longer
   present are the dropped block. Append them to `self._compact_buffer` (per game; the instance is per game, reset on
   `_session_runtime_dir` change like the rest of the state).
2. **Trigger:** `len(buffer) >= K` (K = 10 dropped turns ⇒ ≈ 2 fires per game on the base's 22.2 drops) **or** a level
   transition with a non-empty buffer. Fire AFTER the turn's `analyze` returned (the B62 placement — the call never
   blocks an action and never issues one).
3. **The call:** one tool-free chat completion, thinking OFF on this thread (`_ReflectThinkFlag`, reused verbatim),
   cap 600 tokens, timeout 90 s. Prompt = the memento template below over (a) the current memento, (b) the buffered
   dropped turns rendered as text (assistant content + tool result text, images stripped, per-turn cap 600 chars).
   Then clear the buffer.
4. **Injection:** the memento is a single user message `MEMENTO (turns older than the window; carried forward):` …
   placed as the **first** history message, re-inserted by the same wrap on every call (strip any previous memento
   first, so it is never counted as a turn by `_keep_recent_history_turns` and never dropped as "oldest"). ≤ 600
   estimator-tokens of every request = ≤ 1.9% of the budget.
5. **The seven slots are untouched** — B65 is not B62 stacked; the memento is a separate channel.

**Memento template** (Codex's six lines with game nouns, plus the cumulative rule; c#16 + c#32):

> The turns below are about to be deleted from your context. Write a short MEMENTO for the next turns of this game.
> Keep every entry of the previous memento unless the turns below contradict it. Then add, from the turns below only:
> (1) what was established about this level's rules and what is still unknown; (2) actions proven no-op or harmful, with
> the situation they were tried in; (3) hypotheses that still need one decisive test; (4) if a `Plan:` line appears,
> repeat it verbatim. Never invent evidence. Output only the memento, under 120 words.

## Smoke oracle (thui-compact-v0: tr87 / sk48 / sc25, 900 s each — ⚠️ a 900 s smoke may never exceed 30 turns)

Because the trigger needs 30+ turns and then 10 drops, the smoke sets `_PERSISTENT_HISTORY_ASSISTANT_TURNS` to **8**
and K to **4** for the smoke build only (asserted in cell 0's text and in-kernel), so the mechanism fires inside 900 s.
The full build restores 30 / 10. Both values are printed by the in-kernel teeth line.

- **P1 fired** — `thui-compact: game=… reason=k|level dropped_turns=N latency=… completion=… memento_chars=…` at least
  twice per game; memento non-empty in ≥ half of fires (B62's v0 failed exactly here).
- **P2 landed** — the request AFTER a fire carries `MEMENTO (` as its first history message (read from the prompt-log
  snapshot / usage `prompt_tokens` rising by the memento's size), and the previous memento's entries survive into the
  next one (the cumulative rule; grep one distinctive phrase across consecutive mementos).
- **P3 harness** — 3 games finish, `wrapper error` 0, `call FAILED` 0, thinking control: main-analyzer completion mean
  in the base band (≥ 1,000; v1's confound read 318).
- Kill: mean latency > 60 s at 3 games (would be worse at 25), or memento empty ≥ half, or P2 absent.

## Full-run oracle (thui-compact-v1)

Paired **levels** vs `eval/fixtures/thuiv3-pool.json` (`rank_runs.py`), B35 floor **+1 level in ≥ 6 of 25 games on both
draws**; a second draw (`--suffix=-r2`) before any hidden slot. Pre-registered readings: (a) floor cleared on both →
`thui-stack --arms=compact` becomes the draw candidate; (b) NOT-DISTINGUISHABLE → the more-context family closes on
measurement (five members on the base's mean) and the next lever is not a memory policy; (c) WORSE → the memento is
misleading the model, read the mementos before killing (a wrong memento is a prompt bug, not a mechanism verdict).
Kill rule as B62: ≥ 2 runs per arm, no hidden draw before the paired read.

## Not in scope

- B65-b (token-budget keep-rule replacing the 30-turn constant): a keep-rule, not compaction; likeliest to repeat B54's
  null; run only if B65-a reads positive and the question becomes how much verbatim tail to keep.
- B65-c (fold the six wiped slots into `cross_level_notes` at level-up): mostly covered by B62's `reason=level`
  reflections (24 in v1-1, null); park unless B65-a's mementos show level-N facts helping level N+1.
- Stacking with B62's slot rewrite: two memory policies in one arm cannot be attributed.

## Status

- 2026-09-05: design.
- 2026-09-05 ~20:20Z: **builder written** (`thui-compact/build_notebook.py`, base v3, cells 0/12/14 smoke, 0/12 full; every rewrite anchored, cell 12 parses; smoke = window 8 / K 4, full = window 30 / K 10). **In-kernel teeth** (run at import, before the benchmark): thread-local thinking flag (worker False / main True), diff / fold / strip helpers on synthetic messages, window constant landed. **Offline drive** against a stub harness with a realistic 30-turn loop: fires at turns 12 / 16 / 20 / 24 exactly (window 8 + K 4, then every K), memento folded into the first user message once (marker count 1), previous memento carried into the next summariser prompt, dropped tool-call code carried, 8 assistant turns kept, `wrapper_errors` 0, P2 `landed=True` on every post-fire turn. Notebooks built: `taaf-thui-compact-v0.ipynb` (smoke, sahasawatt) and `taaf-thui-compact-v1.ipynb` (full, yocybercode). **Not pushed** — GPU is Watchara's call after the 09-05 slot decision. Evidence file for
  the numbers above: `thui-v3-1` usage sidecars (`Desktop/archive/arc-traj/thui-v3-1/`, Windows box) and
  `thui-reflect-v1-1` v2 log.

### Push record

- **2026-09-04 ~20:40Z — the smoke cannot be pushed from this box: `sahasawatt`'s weekly GPU quota is exhausted.**
  `kaggle kernels push -p thui-compact` (metadata id `sahasawatt/thui-compact-v0`, correct for this token under G4)
  answers `Kernel push error: Maximum weekly GPU quota of 30.00 hours reached.` — **and exits 0**, which is the trap
  `scripts/kaggle_push_kernel.py` exists to catch: it read the post-push `kernels status` back, found it empty
  (`404` on the slug), and refused to report success. Same blocker as B61 / B62 / B64 on this account.
  So **both** the smoke and the full run are Watchara's GPU (`yocybercode`), not just the full run:
  rebuild with `python3 thui-compact/build_notebook.py --owner=yocybercode` for the smoke (the committed metadata
  says `sahasawatt` because that is this box's token) and push from the mac. Nothing was created on Kaggle.

### Memento prompt v2 (2026-09-05, before anything ran) — from `arc-agi-pub/notes/think-research-memento-prompt-2026-09-05.md`

A narrow research pass (10 pinned agents, 44 sources, 24 claims: 16 confirmed / 5 refuted / 3 unverified) asked one
question: does any measured evidence justify changing this prompt's wording? Its verdict was **"ship it close to as
written"** — every claim carrying an efficacy number is refuted or was measured at frontier tier, and the strongest
datapoint in the packet is ours (B62's seven-slot graft at this cadence, 105/105 filled, `p = 0.9978`). Two edits were
adopted anyway because their cost if wrong is near zero, and one was dropped.

- **Adopted — labelled output lines with per-line item caps**: `Rules:` ≤4, `Unknown:` ≤3, `No-op/harmful:` ≤6,
  `Hypotheses:` ≤2, `Plan:` verbatim, 120 words total. The evidence for the shape is descriptive (checkpoint schemas,
  Reflexion's episode caps), and the reason that decides it is instrumentation: **a labelled memento is parseable**, so
  P1 counts filled labels the way B62 counted its seven fields instead of reading a length. The log line now carries
  `labels=N/5` and names the missing ones, and `_COMPACT_STATS["labels"]` totals them.
- **Adopted — every claim names the action or step that established it, drop the claim otherwise.** *Never invent
  evidence* is unenforceable as a prohibition; this is its checkable form, at ~10-15% of the character budget.
- **Dropped — a `Repeated mistake:` self-critique line.** One claim behind it (Reflexion's EPM ablation 67% → 75%),
  and the transfer lens objected: frontier model, multi-hop QA, against a 27B model under a 600-token cap with thinking
  off. Under 120 words it displaces a fact.
- **Rejected with reasons worth keeping**: an `Active State` / current-position field is *stale by construction* here
  (written at drop time, refolded for many turns while the live board sits in the surviving window); 1-2 sentence
  budgets cannot hold the no-op list; importance scoring and two-stage synthesis are extra calls, not wording.

**Third in-kernel teeth added**: every counted label must appear in the prompt (a counter for a field the model was
never asked for reports a failure that is the harness's, not the model's), and the step-id requirement must be present
exactly once. Offline drive re-run after the edit: fires at turns 12 / 16 / 20 / 24, `labels=5/5` on labelled replies
and `0/5` with every name listed on a deliberately unlabelled one, memento folded once, `wrapper_errors` 0.

**Smoke oracle P1 is now**: ≥ 2 fires per game, memento non-empty in ≥ half, and **`labels` ≥ 3 of 5 on at least half
the fires** — a 27B model under a 600-token cap with thinking off is exactly the case where a five-field format may not
survive, and if it does not, the finding is the format's, not the mechanism's.
