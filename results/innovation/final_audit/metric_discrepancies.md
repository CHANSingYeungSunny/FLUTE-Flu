# Metric recomputation discrepancy report

- Test evaluation: `final_nlinear_20260915T145710Z`
- Cells: 52; recomputed: 52
- Source: raw `predictions/*.csv` re-scored with the **frozen** `innovation.metrics.evaluate_predictions` (step=0, seasonal literature peak).
- Relative tolerance: 1e-09

**Discrepancies found: 0**

All 52 cells reproduce bit-for-bit (within tolerance) from their raw 
prediction files, including seasonal PTE/PIE and the literature peak hit ratio.

Note: `mse_all_z`/`mae_all_z` are the **primary** metrics (MIFlu paper §V-B);
physical-unit MSE/MAE are supplementary.
