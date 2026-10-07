# PAIRED-STATISTICS CORRECTION — VERIFICATION

Generated 2026-10-06. Append-only. **The old Stage-6 report was not modified.**

## Verdict

**The correction is verified and stands.** The original `paired_stats.py` win counter
incremented on the opposite condition from the one its own header describes.

---

## 1. The convention, stated once

```
diff_c   = mse(A, cell) - mse(B, cell)
lower MSE wins
=> A wins cell c   iff   diff_c < 0
=> invariant: wins_A + wins_B + ties == n_cells
```

Verified for every row of `paired_stats_corrected_v2.csv` (the `partition_ok` column is
`True` throughout — asserted in code, not merely printed).

---

## 2. The four required tests

Full transcript: `paired_stats_unit_test_results.txt` (exit code 0).

| # | Test | Expected | Observed | Result |
|---|---|---|---|---|
| 1 | A lower than B in **every** cell (`diffs = [-1,-2,-0.5,-3]`) | A wins all cells | `wins_A=4, wins_B=0, ties=0` | ✅ PASS |
| 2 | A higher than B in **every** cell (`diffs = [1,2,0.5,3]`) | A wins zero cells | `wins_A=0, wins_B=4, ties=0` | ✅ PASS |
| 3 | Mixed, hand-computed (`diffs = [-0.4,+0.6,-0.2,+0.1,-3.0,0.0]`) | by hand: A 3, B 2, tie 1, mean −0.483333 | `wins_A=3, wins_B=2, ties=1, mean=-0.483333` | ✅ PASS |
| 4 | **Regression guard** on the real `miflu − nlinear` cell differences | correct = 7; the inverted counter = 5 | `wins_A=7`, inverted count `=5` | ✅ PASS |

**Tie handling is explicit** (test 3): a zero difference is counted as a tie and
excluded from both win counts, with the partition assertion guaranteeing the three
counts always sum to the cell count.

---

## 3. Verification of the two specific reported corrections

Both claims in the brief are **supported by the stored cells**.

| Comparison | Claim | Verified | Evidence |
|---|---|---|---|
| **MIFlu vs NLinear** | MIFlu wins **7/12**, not 5/12 | ✅ | `paired_stats_corrected_v2.csv`, row `miflu − nlinear`: `wins_A=7, wins_B=5, ties=0, n=12` |
| **no-text vs NLinear** | no-text wins **11/12**, not 1/12 | ✅ | row `notext − nlinear`: `wins_A=11, wins_B=1, ties=0, n=12` |

Both satisfy `wins_A + wins_B = 12`, and in both cases `n − old_count == new_count`
(12−5=7 and 12−1=11), consistent with a simple polarity inversion.

---

## 4. What was and was not affected

| Quantity | Affected by the bug? |
|---|---|
| per-cell MSE / MAE | ✗ no |
| `average_MSE_4L` | ✗ no |
| model ranking | ✗ no |
| mean difference | ✗ no |
| t statistic | ✗ no |
| **win count `n_win`** | ✅ **yes — inverted** |
| narrative quoting the win count | ✅ yes — one §0 sentence in the Stage-6 report |

The mean differences and t statistics in the original file are numerically correct; only
the win-count column is wrong. The corrected table therefore differs from the original
**only** in that column.

---

## 5. Corrections to downstream prose

| Where | Written | Correct |
|---|---|---|
| `recovery/stage6/results_report_zh.md` §0 | "MIFlu 与 NLinear … 不可分（t = −0.11，**5/12 胜**）" | **7/12 胜** |
| same report §4.3 | "no-text 优于 NLinear（t=−2.28，**11/12**）" | already correct — the report contradicts itself between §0 and §4.3 |
| `paired_stats.txt` header | claims `n_win = cells where A beats B` | the counter measures the opposite |

**Not edited**: `recovery/stage6/results_report_zh.md`, `hpc_results/stage6/scoring/paired_stats.py`
and `paired_stats.txt` all remain byte-identical to their original state. The correction is
carried by this document and by the new v2 tables.

---

## 6. New outputs (all new files; nothing overwritten)

| File | Content |
|---|---|
| `paired_stats_corrected_v2.csv` | 12 pairwise comparisons, corrected counts, per-horizon win counts, `partition_ok` invariant |
| `paired_stats_corrected_v2.md` | same as a readable table |
| `paired_stats_unit_test_results.txt` | full unit-test transcript |
| `PAIRED_STATS_CORRECTION_VERIFICATION.md` | this document |
| `../paired_stats_corrected.csv` / `.md` | the first-round corrected tables (unchanged) |
| `../SCORING_CORRECTION_NOTE.md` | the first-round correction note (unchanged) |

---

## 7. Recommended reporting wording

> MIFlu wins **7 of 12** paired cells against NLinear, but the mean paired difference is
> only −0.0080 (t = −0.11) — **statistically indistinguishable**. The sign flips across
> horizons: all three L=24 cells go to NLinear, while most L=36/48/60 cells go to MIFlu.
> **No single-horizon result may be extrapolated.**

Do **not** use "5/12 win".