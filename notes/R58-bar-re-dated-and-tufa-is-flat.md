# R58 — the bar re-dated: it moved 28% in five days, and Tufa did not move at all

**2026-09-13, 0 slots, 0 GPU, 0 credentials.** Read off the **signed-out public leaderboard page**
(`kaggle.com/competitions/arc-prize-2026-arc-agi-3/leaderboard`, Public tab) in the in-app browser.
This is the free action R57 left on the table: the bar was the only load-bearing number in the whole
campaign and it was five days old.

**Control that the read is of the right rows:** our own team row reproduces two values this repo
recorded independently before the page was opened — **`Thuitanium`, score 3.74, 28 entries** against
the LEDGER's *"Kaggle keeps the MAXIMUM … 3.74"* and *"the record holds 28 rows on 28 distinct UTC
dates"*. Rank **160**, last entry 1 d ago (the 3.41 draw of 09-12, which did not move the max).

## 1. The bar

| date | 5th place | source |
|---|---|---|
| 2026-08-24 | 2.88 | LEDGER (not re-verified today) |
| 2026-09-08 | 5.96 | LEDGER (not re-verified today) |
| **2026-09-13** | **7.63** (`Daniel Franzen`) | **this read** |

Today's top five: `Tufa Labs` 11.04 · `Ebi` 8.68 · `NVARC3` 8.40 · `Third Intelligence` 8.21 ·
`Daniel Franzen` 7.63. **The 5.96 that was the bar on 09-08 is now rank 13.**

## 2. The growth rate held out of sample — the first time it has been tested

- 08-24 → 09-08 (15 d): **4.9680 %/day** — the figure R57 carried
- 09-08 → 09-13 (5 d): **5.0644 %/day** — measured after, on data the first did not see
- 08-24 → 09-13 (20 d): **4.9921 %/day**

R57's rate came from two readings, i.e. one interval, which is a line through two points and not yet
a rate. It now survives a five-day out-of-sample interval to within 0.1 pp.

⚠️ **And it must still not be extrapolated to the close.** 7.63 compounded at 5.0644 %/day for the
50 days to 2026-11-02 gives **90.2**, on a scale where the best team on earth is at 11.04. So this is
a short-horizon rate over a bounded quantity near its floor; it prices the next fortnight, never
11-02. Anything computed from it about the finish is unsupported.

## 3. Tufa Labs is FLAT, and the divergence framing inverts

**11.04 → 11.04 over five days**, with **136 entries** and a submission **12 h** before this read — so
this is a team actively submitting and not moving, not a team that stopped. R56/R57's *"Tufa
6.041 %/day"* is therefore **dead as a forward rate**; it was one interval and it did not continue.

What did move is the field behind them: five days ago 5th place was 5.96, today ranks 2–5 are
8.68 / 8.40 / 8.21 / 7.63. **The pack is closing on Tufa while Tufa stands still.** The premise this
campaign has carried since arena 1 — *upstream is pulling away, we must catch a moving leader* — is
refuted on the leader and true only of the pack.

## 4. The gap, which got worse

| | 2026-09-08 | 2026-09-13 |
|---|---|---|
| bar / our board score | 5.96 / 3.74 = **1.594×** | 7.63 / 3.74 = **2.040×** |
| excess growth needed to close it by 11-02 | 0.8508 %/day over 55 d | **1.4362 %/day over 50 d** |

Every pricing in R56 and R57 that stood against 1.594× is stale **in the harder direction**. R57's
verdict is unchanged in kind — the distance to the bar is still unknown in *public* terms, because
nothing here crosses the forbidden public→hidden conversion — but the hidden-side distance is now
measured larger.

⚠️ **The fork's own growth rate is deliberately NOT computed here.** R57's 3.575 is a two-draw
**mean**; the leaderboard column is a **max**. Dividing one by the other is the same class of error
as the ratio R57 spent its verdict refuting, in a new costume.

## 5. Three facts from the competition page nobody in this campaign had read

Verified from the rendered overview, `document.querySelectorAll('li')`:

- **Final Submission Deadline = November 2, 2026**, 11:59 PM UTC; winners announced December 4. The
  notes' assumed 11-02 was correct, and is now sourced. **50 days left.**
- **Milestone prizes are scored on the leaderboard at two fixed dates**, and **Milestone 2 is
  September 30, 2026** — **17 days away**, $25,000 / $7,500 / $5,000 for the top three. Top three
  today is **8.40**. Out of reach from 3.74 by any lever in this repo; recorded so the date is not
  discovered late.
- **Final leaderboard prizes run 1st–5th** ($40k / $15k / $10k / $5k / $5k). So *"the top-5 bar"*,
  which this campaign has treated as a moving target to be tracked continuously, is really **one
  reading on one day** — 5th place on 2026-11-02. Today's 7.63 is a trajectory input, not the target.
- Prize eligibility **requires open-sourcing the solution**.

## 6. What this does not change

The NEXT ACTION is unchanged and still blocked. Credentials re-probed this session with controls
(`command -v` over `kaggle` / `python3` / a name known absent; `kaggle` **ABSENT**, both token paths
**MISSING**, `KAGGLE_USERNAME` / `KAGGLE_KEY` unset), so the per-level harvest for the four
Flash-Next runs still cannot start, and every pricing instrument stays blind to the shipped chassis.

No ticket closed, no MAP row added, no slot endorsed.

## Reproduce

Open `https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/leaderboard` signed out and read
rank 5; search the board for `yocyber` to get the `Thuitanium` row as the control.

```bash
python3 -c 'd=lambda a,b,n:(b/a)**(1.0/n)-1.0
print("%.4f %.4f %.4f" % (100*d(2.88,5.96,15), 100*d(5.96,7.63,5), 100*d(2.88,7.63,20)))'
```
→ `4.9680 5.0644 4.9921`
