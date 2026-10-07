# Final project audit

Generated 2026-09-15T18:02:06Z UTC.
Test evaluation: `final_nlinear_20260915T145710Z` (single-use, already consumed).

## 1. One-time Test integrity

- passed: **True**; receipt_count=1, test_eval_id_count=1, declared_access_count=1, checkpoint_hash_failures=0
- cells: champion 40 + baseline 12 = 52; missing 0; duplicate 0

## 2. Independent metric recomputation

- 52/52 cells re-scored from raw prediction CSVs with the frozen `innovation.metrics` implementation: **0 discrepancies**.
- MSE/MAE and seasonal PTE/PIE reproduce exactly (rel. tol 1e-9).

## 3. Verified scientific conclusions

| # | Claim | Verdict |
|---|---|---|
| 1 | nlinear Test MSE lower than gpt2_miflu at all four horizons | **SUPPORTED** |
| 2 | relative MSE reduction lies within ~6.7% to 23.8% | **SUPPORTED** |
| 3 | nlinear meets the literature criterion at L48/L60 but not L24/L36 | **SUPPORTED** |
| 4 | gpt2_miflu does not meet the criterion at any evaluated horizon | **SUPPORTED** |
| 5 | baseline seed availability is three, limiting paired power | **SUPPORTED** |
| 6 | only L36 MAE remains significant after Holm correction | **SUPPORTED** |
| 7 | wording is 'observed best' unless a comparison is statistically supported | **SUPPORTED** |

All seven supported: **True**

## 4. Primary metrics (z-space, MIFlu §V-B)

| L | NLinear MSE(z) | MIFlu MSE(z) | reduction | NLinear MAE(z) | MIFlu MAE(z) |
|---|---|---|---|---|---|
| 24 | 4.2966 | 5.6766 | 24.31% | 1.4013 | 1.6186 |
| 36 | 4.9728 | 6.1983 | 19.77% | 1.5239 | 1.6733 |
| 48 | 5.4046 | 5.7914 | 6.68% | 1.6058 | 1.5966 |
| 60 | 5.6085 | 6.6225 | 15.31% | 1.6436 | 1.6948 |

## 5. Peak outcomes (PTE<=1w AND PIE<=25%)

| Model | L | PTE (w) | PIE (%) | met |
|---|---|---|---|---|
| nlinear | 24 | 1.667 | 9.504 | no |
| nlinear | 36 | 2.000 | 10.568 | no |
| nlinear | 48 | 0.350 | 3.329 | YES |
| nlinear | 60 | 0.150 | 2.076 | YES |
| gpt2_miflu | 24 | 4.667 | 72.177 | no |
| gpt2_miflu | 36 | 5.333 | 77.344 | no |
| gpt2_miflu | 48 | 2.000 | 25.294 | no |
| gpt2_miflu | 60 | 2.000 | 23.269 | no |

## 6. Statistics

- effective paired n = **3** (baseline seeds [42, 43, 44])
- Holm family = 8 comparisons; significant: ['L36 mae_all_z']
- no broad superiority claim; `observed best` wording retained.

## 7. AUC-Best-so-far

- AUC = **0.8700909236319055** over 160 eligible validation runs, 0.1317 GPU-hours
- This measures MODEL-DISCOVERY EFFICIENCY under a fixed validation budget, not final disease-prediction accuracy. It does not replace MSE/MAE/PTE/PIE.

## 8. Resource audit

- Slurm jobs since 2026-09-15: 283 (completed 279)
- Final Test: job 560659, stingy, 1x A100, limit 02:00:00, elapsed 00:01:00, exit 0:0
- Checkpoint verification: job 560692, stingy, 2 CPU / 8 GB, limit 00:20:00
- No model computation was run on a login node during this audit phase.

## 9. Login-node incident closure

- date: 2026-09-16
- symptom: SSH authentication succeeded but new shell creation hung
- root cause: one-time Test inference running via nohup on the login node entered D state (uninterruptible I/O wait) and contributed to process/resource blockage
- evidence: PID 3032070, stat D, elapsed 01:14:20, stalled cells 41
- recovery: exact-process termination from an already-open shell (kill -9 3032070), then narrow pkill -9 -f run_one_time_test / controller.sh
- lawful continuation: same receipt, same manifest, same test_eval_id; missing cells only; submitted through sbatch job 560659
- preventive rule: all future model computation through Slurm compute allocation only
- **not attributable to**: the cluster or the network

## 10. Plan completion

- {'COMPLETED': 18, 'NOT_COMPLETED': 16}
- whole plan complete: **False**
- reason: Unavailable/deferred candidate families (TimesNet, TimeMixer/ModernTCN, TF-IDF+SVD, fastText, BERT/MiniLM, zero-text/shuffled-text, Time-LLM-style, CALF/TimeCMA-style, Chronos, TimesFM, Moirai), unreported COVID/pre-COVID splits, and the optional EvoForecast arm are not completed.

## 11. Conclusion

```
Main empirical study and one-time Test completed; optional EvoForecast and specified unavailable/deferred model families remain incomplete.
```
