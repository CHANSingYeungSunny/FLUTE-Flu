# MIFlu Paper-Protocol Results กX Regional/Table VI Summary

**Primary metrics (MIFlu paper protocol, Section V-B): MSE / MAE only.**

The PTE / PIE columns are **supplementary diagnostics** computed by this project (compute_miflu_indicators.py), NOT part of the MIFlu paper's reported metrics. Listed for insight only.

| Horizon (L) | MSE_ILI | MAE_ILI | PTE (wk) | PIE (%) | Matched peaks | Missed peaks |
|---|---|---|---|---|---|---|
| 24 | 5.0559กำ1.5832 | 1.5004กำ0.1210 | 1.5000 (thr 2.0) | 19.4899 (thr 20.0) | 2/3 | 1 |
| 36 | 6.8340กำ0.9366 | 1.6798กำ0.0927 | 1.0000 (thr 2.0) | 6.5358 (thr 20.0) | 2/3 | 1 |
| 48 | 6.4049กำ0.9117 | 1.6505กำ0.0810 | 1.0000 (thr 2.0) | 20.3754 (thr 20.0) | 2/2 | 0 |
| 60 | 7.0704กำ0.7236 | 1.7009กำ0.0739 | 1.5000 (thr 2.0) | 26.1073 (thr 20.0) | 2/2 | 0 |

## Verdicts (supplementary thresholds)
- PTE <= 2.0 wk, PIE <= 20.0 %
- 'not accurate' on PTE / PIE reflects missed peaks and magnitude error at matched peaks (see Matched peaks / Missed peaks).
