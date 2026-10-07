# Final one-time Test report

**Test evaluation ID:** `final_nlinear_20260915T145710Z`
**Generated:** 2026-09-15T17:37:53Z UTC
**Champion:** `nlinear` (frozen before Test access, never changed)
**Baseline:** `gpt2_miflu`

## 1. Receipt and immutable-manifest reconciliation

- One receipt only, bound to `final_nlinear_20260915T145710Z`.
- Manifest: 52 cells; champion `nlinear`;
  frozen model manifest sha256 `558d2e388225bc143e2e48b99b8ae796cab0f18dff3f7a9eacff03f60c7485b5`;
  cohort manifest sha256 `8695b8ea6151c5dd350411449141e4e547c7bd0aaa263e402695279477e0327d`.
- Scientific protocol `innov-v2.0`; implementation
  source `innov-v2.10`; source aggregate
  `47a1404c8151539578d596f83742b2a7cc2d74607436a705a303e3c7d0d27fa4`.
- All identifiers mutually consistent; no second manifest or receipt exists.

## 2. Background-process reconciliation

- The original process (PID 3032070) was launched with `nohup` on the login node and
  was found in **D state** at 41/52 cells after 01:14:20 elapsed.
- It was terminated with `kill -9`; orphaned workers were cleared with `pkill -9 -f`.
- No second Test process was ever started.

## 3. Resume actions actually taken

- Reused the existing receipt and `test_eval_id`; the manifest was **not** rewritten.
- Submitted the remaining 11 cells as **sbatch job 560659** (`stingy`, `gpu:a100:1`,
  `02:00:00`), which completed in 00:01:00 with exit `0:0` on `gpu-a100-03`.
- The 41 already-completed cells were skipped by the driver's create-only logic and
  were **not** overwritten or recomputed.

## 4. Final 52-cell coverage

- expected 52 / completed 52 / valid 52 / missing 0 / duplicate 0
- completion gate passed: **True**

## 5. Failures and resumes

- One mechanical failure: the login-node process hung in D state (see §2).
- One resume: sbatch job 560659 completed the 11 missing cells.
- No scientific, checkpoint, data-integrity or manifest defect occurred after Test access.

## 6. Checkpoint-hash verification

- verified 52/52; failures: 0
- Every evaluated cell traces to its frozen checkpoint SHA-256.

## 7. Per-horizon and aggregate MSE / MAE (Test)

| Model | L | n | MSE mean | MSE 95% CI | MAE mean | MAE 95% CI |
|---|---|---|---|---|---|---|
| gpt2_miflu | 24 | 3 | 444,951,612.95 | [328,062,033.03, 609,822,904.36] | 14,330.04 | [12,912.01, 15,436.39] |
| gpt2_miflu | 36 | 3 | 485,841,664.57 | [444,442,412.15, 510,899,769.59] | 14,814.62 | [14,737.88, 14,951.93] |
| gpt2_miflu | 48 | 3 | 453,946,781.74 | [422,622,442.32, 498,887,120.58] | 14,135.14 | [14,087.75, 14,174.29] |
| gpt2_miflu | 60 | 3 | 519,090,819.58 | [459,530,485.61, 594,432,121.63] | 15,004.71 | [14,651.10, 15,403.66] |
| nlinear | 24 | 10 | 336,782,610.35 | [335,295,210.16, 338,308,672.44] | 12,406.29 | [12,323.34, 12,488.45] |
| nlinear | 36 | 10 | 389,782,114.15 | [388,400,543.53, 391,243,420.95] | 13,491.73 | [13,430.91, 13,561.28] |
| nlinear | 48 | 10 | 423,632,711.70 | [422,662,214.35, 424,567,050.81] | 14,216.81 | [14,178.33, 14,254.34] |
| nlinear | 60 | 10 | 439,611,123.66 | [437,514,844.90, 441,498,344.04] | 14,551.78 | [14,492.44, 14,609.34] |

## 8. Literature peak outcomes

| Model | L | PTE (w) | PIE (%) | hit ratio | criterion |
|---|---|---|---|---|---|
| gpt2_miflu | 24 | 4.67 | 72.18 | 0.111 | not met |
| gpt2_miflu | 36 | 5.33 | 77.34 | 0.000 | not met |
| gpt2_miflu | 48 | 2.00 | 25.29 | 0.167 | not met |
| gpt2_miflu | 60 | 2.00 | 23.27 | 0.333 | not met |
| nlinear | 24 | 1.67 | 9.50 | 0.700 | not met |
| nlinear | 36 | 2.00 | 10.57 | 0.667 | not met |
| nlinear | 48 | 0.35 | 3.33 | 1.000 | MET |
| nlinear | 60 | 0.15 | 2.08 | 1.000 | MET |

- `nlinear` meets the literature criterion (PTE<=1 week AND PIE<=25%) at L=48 and
  L=60, where the peak-hit ratio reaches 1.00. It does not meet it at L=24/L=36,
  where mean PTE is 1.67 and 2.00 weeks.
- `gpt2_miflu` does not meet the criterion at any horizon.

## 9. Frozen champion versus MIFlu baseline

- L=24: nlinear MSE 336,782,610.35 vs gpt2_miflu MSE 444,951,612.95 (-24.31%)
- L=36: nlinear MSE 389,782,114.15 vs gpt2_miflu MSE 485,841,664.57 (-19.77%)
- L=48: nlinear MSE 423,632,711.70 vs gpt2_miflu MSE 453,946,781.74 (-6.68%)
- L=60: nlinear MSE 439,611,123.66 vs gpt2_miflu MSE 519,090,819.58 (-15.31%)

`nlinear` has lower Test MSE than `gpt2_miflu` at every horizon. On MAE the two are
effectively tied at L=48 (14,216.8 vs 14,135.1, baseline marginally lower).

## 10. Statistical findings

- Paired comparisons use the 3 seeds present in both arms (42/43/44).
- After Holm correction, only MAE at L=36 reaches significance (p_holm=0.0251, dz=-10.29).
- All other comparisons are non-significant; effect sizes are reported but not
  interpreted as evidence of superiority.
- **No claim of statistical superiority is made.** `observed best` is reported.

## 11. Resource findings

- Resume job 560659: `stingy`, 1x A100, 4 CPUs, 16 GB, limit 02:00:00, actual 00:01:00,
  exit 0:0, node gpu-a100-03.
- Checkpoint verification job 560692: `stingy`, 2 CPUs, 8 GB, limit 00:20:00.

## 12. Artifact-integrity verification

- Per-cell prediction CSVs and metric JSONs: 52 + 1 aggregate, all parseable.
- Figures: 6 file(s) hashed in `manuscript_figures_manifest.json`.
- Traceability: summary -> cell -> prediction -> checkpoint SHA-256 -> frozen model
  manifest -> Stage-F cohort manifest -> source hash -> plan hash.

## 13. Final report paths

- `results/innovation/final/plan_completion_matrix.md`
- `results/innovation/final/plan_completion_audit.json`
- `results/innovation/final/final_results_summary.csv`
- `results/innovation/final/final_statistics.csv`
- `results/innovation/final/final_resource_summary.csv`
- `results/innovation/final/final_peak_results.csv`
- `results/innovation/final/final_test_report.md`
- `results/innovation/final/manuscript_tables.md`
- `results/innovation/final/manuscript_figures_manifest.json`
- `results/innovation/final/reproducibility_manifest.json`
- `results/innovation/final/limitations_and_incidents.md`
- `results/innovation/final/final_paired_tests.json`
- `results/innovation/final/final_common_date_comparison.csv`

## 14. Completion-matrix status

- Stages A-M: COMPLETED. Stage N (EvoForecast): NOT_COMPLETED (optional, not attempted).
- The plan is therefore **not** declared wholly complete.

## 15. Deferred, unavailable or incomplete items

- EvoForecast (optional, stage N).
- Pre-COVID/COVID analysis (not pre-registered, not reported).
- Historic original-repository byte identity for one script remains unresolved.

## 16. Champion immutability

- `nlinear` was frozen on validation-only evidence before any Test access and was
  never reselected, retuned or retrained after Test results were seen.

## 17. Single Test confirmation

- Exactly one receipt, one immutable manifest and one `test_eval_id` exist.

```
ONE_TIME_TEST_COMPLETED_PROJECT_AUDIT_READY
```

---

## Appendix — final-audit addendum (added after independent recomputation)

- **Primary metric口径 corrected**: per MIFlu (IEEE JBHI 2025, §V-B), MSE/MAE in the
  normalised **z-space** are PRIMARY; the physical-unit values above are supplementary.
  See `manuscript_results_en.md` / `manuscript_results_zh.md` for the z-space tables.
- **Independent recomputation**: all 52 cells were re-scored from their raw prediction
  CSVs with the frozen `innovation.metrics` implementation — **0 discrepancies**
  (`final_audit/metric_recomputation.csv`, `metric_discrepancies.md`).
- **One-time Test integrity**: PASSED (`final_audit/one_time_test_integrity.json`).
- **All seven reported conclusions re-verified as SUPPORTED**
  (`final_audit/conclusion_verification.json`).
- **Statistics**: effective paired n = 3 (baseline seeds 42/43/44); Holm family = 8
  comparisons; only L36 MAE survives correction. `observed best` wording retained.
- **AUC-Best-so-far** = 0.8701 over 160 eligible validation runs (0.1317 GPU-hours) —
  a model-discovery-efficiency measure, not prediction accuracy.
- **Not completed**: EvoForecast; several unavailable/deferred model families;
  COVID/pre-COVID split analysis (not pre-registered). See `final_audit/unresolved_items.md`.
