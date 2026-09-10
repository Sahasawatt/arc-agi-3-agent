# ACTION7 banking and promotion-gate investigation — 2026-09-08

Scope: local branch only; no push, PR, merge, Kaggle compute or submission. No version tag bump. Observed game artifacts only; no environment source inspected. The user's job-specific authorization covers this local banking commit in the agent repository. Historical public-to-hidden ratios and other-chassis noise bands are not promotion thresholds for ACTION7.

## Job 1 — reproduced and banked

Source artifacts: `/Users/yocyber-code/Claude/arc-artifacts/_src/a7-full25-r1-2026-09-08/`. Full-run notebook SHA-256 `f35f95ac9417ef95c0bd959e04854ba7f88da3e0e347f1bf60eb0b2ceaf4c969`. Builder source is `thui-fast/taaf-thui-fast-v0.ipynb` at branch base `a92b72344dfe8d3eae7736b60c103d592a81f6fe`; SHA-256 `0fb65add1490e39d317ce265acd0cb6b5eecd11919bc0bb9092d78635c041804`.

Read `thui-fast/build_notebook.py` first. The recovery follows its pinned-source, exact-changed-cells and code-validation convention. Changed cell objects: [0,1,3,5,9,15]; changed source text: [0,3,5,9,15]. Cell 1's text is identical but its representation changes from list to string. Changed cell objects are banked explicitly, not reverse-engineered at runtime from the target notebook. Source and target hashes fail closed on drift.

Commands:

```sh
python3 thui-a7/build_notebook.py
python3 notes/probe-rank-floor-2026-09-08.py /private/tmp/a7-rank-pinned
```

Builder positive control: byte-identical banked output. Negative control: `build_notebook.build()` on a temporary `{}` source raises `AssertionError` for source drift. All code cells compile with top-level-await support without executing the notebook.

The archived cell 0 still describes a three-game smoke; actual cell 15 selects 25 games and actual budget is 7,920 seconds. This historical documentation defect is preserved to reproduce the run exactly, not endorsed as current build instructions. Metadata is archived as retrieved; it does not pin mutable dataset versions or verify weight payloads.

Fixture re-derived from `score.json` game scores plus benchmark `levels_completed` and `len(history)`, keyed using unique game prefixes. Asserted exact equality with all 25 entries of the supplied fixture, not just an aggregate. Results: public mean **8.249096629847058**, **38 levels**, **3,843 actions**. Raw score and benchmark are banked under `thui-a7/evidence/`.

Pinned `rank_runs.compare` comparisons reproduce:

| baseline | means | levels | p | verdict |
|---|---|---|---|---|
| thui-fast-pool | 8.69 → 8.25 | 38.5 → 38 | 0.7672 | NOT-DISTINGUISHABLE |
| thuiv3-pool | 4.39 → 8.25 | 24.25 → 38 | 0.0786 | NOT-DISTINGUISHABLE |

B76 disposition: **NOT MEASURABLE at n=1 on public**, never “no worse”. No hidden result is established by this investigation. The earlier run report's ACTION7 count 107 is not independently rederived here because this banked bundle does not include events; the supplied log retains the patch marker.

Collision audit commands: `git ls-remote --heads origin`; fetch remote heads; `git for-each-ref --format='%(objectname) %(refname)' refs/remotes/origin`; `git show <resolved-sha>:notes/wayfinder/MAP.md` for every ref. Result: 65 remote heads; 66 local remote refs including origin/HEAD, 0 unreadable, ceiling B70, B76 absent. Positive control B69 appears in 4 refs. Full resolved refs in `a7-branch-audit-2026-09-08.json`. B71 peer claim is preserved; no existing ticket renumbered.

## Job 2 — examples reproduced; universal sign-only claim refuted

Pinned tool: `ea62ff548ee95a0edc2324680864f4afcdd7da82:eval/rank_runs.py`. Extracted with `git show`; fixtures enumerated using `git ls-tree --name-only ea62ff5:eval/fixtures`, then each JSON extracted with `git show ea62ff5:eval/fixtures/<name>`. No shared submodule checkout changed.

One invocation of `probe-rank-floor-2026-09-08.py` first runs `rank_runs.py --selftest`, then runs the subject and controls. Selftest poles: v10cal/v19 p=0.2127 NOT-DISTINGUISHABLE; v10cal/v20 p=0.0001 WORSE; arm guards pass. Full output: `rank-floor-results-2026-09-08.txt`.

| planted effect | p | verdict |
|---|---|---|
| A/A | 1.0 | NOT-DISTINGUISHABLE |
| +0.01 on 25 games | 0.0 | BETTER |
| +100 on 5 games | 0.0585 | NOT-DISTINGUISHABLE |
| +0.01 on 5 games | 0.0585 | NOT-DISTINGUISHABLE |
| +0.01 on 6 games | 0.0295 | BETTER |
| +100 on 6 games | 0.0295 | BETTER |
| +1 on 24 games, −1 on one | 0.0 | BETTER |
| +1 on 24 games, −100 on one | 1.0 | NOT-DISTINGUISHABLE |

The all-same-sign special case is invariant to positive common rescaling. Five nonzero same-sign deltas have exact two-sided extremal probability 2/2^5=0.0625; six have 0.03125. Tool values above are 20,000 deterministic Monte Carlo draws, not exact enumeration. A reported p=0 means zero sampled exceedances, not mathematical probability zero.

Thus a universal +4.07 effect floor is unsupported, and statistical significance alone is not a minimum useful improvement. However, the actual implementation permutes **magnitudes**, not just signs: retaining the sign pattern while changing one negative magnitude changes the result from p=0 to p=1. The blanket claim “counts how many, not by how much” is **refuted**. A 39x p-ratio between different noisy comparisons does not establish a mechanism. No CLAUDE.md, B35 or promotion code edited from this result.

## Job 3 — patches prepared, not applied to PR branches

`notes/patches-2026-09-08/bases.json` pins each patch base and file list. All three pass `git apply --check` against temporary copies extracted from that base; after applying once, the same check rejects reapplication (negative control in the same invocation).

- #143: reproduced incorrect B66 attribution in two files; patch changes only the serving-result attribution to B69.
- #145: reproduced categorical status wording; patch makes hidden transfer provisional at n=1.
- #142: reproduced internal arithmetic inconsistency: four named games at one level each versus five total. Proposed patch uses four consistently in five files (one more propagation site than the handoff counted), and updates directly dependent level difference/action-per-level arithmetic. **Actual Gemma total could not be independently measured**: the reviewed branch lacks its full-run fixture and this supplied artifact bundle contains ACTION7 only. The proposed four-level repair is conditional on the itemised breakdown being correct; Claude should check raw Gemma output before applying it. No measured p-value is recalculated from that proposed count.

All verdicts above are scoped to observed artifacts and pinned code. No external publication or runtime action is part of delivery.
