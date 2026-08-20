# v6 design ledger (think-research, 2026-08-20)

Scope: SYNTHESIZE→STRESS over local corpus (R1-R8); exit = build spec. No web pull needed.

## CLAIMS
- Digest arithmetic/last-5/milestones are trustworthy; keep them — H — R8 §Verdict (15/15).
- Binary `changed` misleads strategy (HUD/timer flips count as progress) — H — R8 Imp1
  (dc22 ~10,450-58; m0r0 ~12,220-49).
- A raw ledger does not invite strategic use; the two best games referenced it 0 times;
  warnings must be decision-shaped — H — R8 Imp2 + adoption table.
- Thrash is the largest recoverable pool (14 games >=2x baseline, 9 zeros) — H — R1
  bucket C; m0r0 608 actions/4 resets on one cycle — R8 (~12,803-48).
- Append-only world model keeps refuted beliefs and enters levels empty — H — R8 Imp3
  (ft09 ~6,690; re86 ~6,550; dc22 ~10,390).
- hud_semantics is built, self-tested, stdlib-only, ready to inject beside the digest —
  H — duckv6/hud_semantics.py + README-hud (risk: false positives on monotone play areas,
  confidence-gated).
- Latency budget allows ~30 more prompt lines (games end on wall clock; prompt already
  ~70k tokens/game; marginal lines are noise vs eviction dynamics) — M — R1+R7.
- A "stop retrying" prohibition can KILL a game whose winning line IS repetition (cd82's
  productive grind happens on byte-identical frames) — H — CLAUDE.md sc25/cd82 traps +
  local measurements. Warnings must be advisory + fire only at zero level progress.

## OPEN QUESTIONS
- v5 hidden score (PENDING) — decides whether the state channel generalizes; <<1.0 would
  demand R7's hidden-behavior reading before any build ships.
- Does Qwen comply with "acknowledge warning before similar batch" prompting? Unknown until
  a commit run; phrase as instruction, do not build a hard gate.
- Imp3 (typed revised state) — LLM compliance + structural rewrite risk; too big to ride
  along. DEFERRED to v7.

## WORKING ANSWER — v6 spec
v6 = v5 base + three bounded changes (all in the existing digest/prompt layer):
1. **Intervention warnings** (R8 Imp2): derived lines in the digest when (a) same-action
   noop streak >= threshold in current state family, (b) an action cycle repeats >= 8x
   with zero level progress, (c) actions-since-level-up approaches a previously observed
   reset threshold, (d) last sequence duplicates a previously failed one. ADVISORY wording
   ("consider switching family"), never prohibitive; conditions all include
   levels_progress==0 to protect cd82-style grinds.
2. **hud_semantics wiring**: inject render_hint() (<=6 lines, confidence-gated) beside the
   digest; feeds Mode 4 (timer-as-goal) directly.
3. **`changed` split, conservative** (R8 Imp1): classify per-action outcome as
   gameplay_changed / hud_only / uncertain using hud_semantics' confident regions as the
   HUD mask; where no confident region exists, label `uncertain` — never assert progress.
Eval bar: commit run vs v5 band [2.37, 2.43]; ship to the daily slot only if in-band+ and
log clean. Attribution across the 3 changes accepted as muddy (same trade v5 made);
postmortem recovers it later if needed.
DEFERRED: R8 Imp3 typed state (v7), any reallocator revival (R7), new callable tools (R6).
