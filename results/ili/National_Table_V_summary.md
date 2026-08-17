# MIFlu Paper-Protocol Results กX Regional/Table VI Summary

**Primary metrics (MIFlu paper protocol, Section V-B): MSE / MAE only.**

The four Peak/Timing/Intensity/Direction columns are **supplementary diagnostics** computed by this project (compute_miflu_indicators.py), NOT part of the MIFlu paper's reported metrics. Listed for insight only.

| Horizon (L) | MSE_ILI | MAE_ILI | Peak Hit | Timing (wk) | Peak Int. (%) | Direction | Peak Hit count | Missed peaks |
|---|---|---|---|---|---|---|---|---|
| 24 | 5.0559กำ1.5832 | 1.5004กำ0.1210 | 0.5000 (thr 0.75) | 0.5000 (thr 2.0) | 31.7334 (thr 20.0) | 0.6961 (thr 0.60) | 2/4 | 2 |
| 36 | 6.8340กำ0.9366 | 1.6798กำ0.0927 | 0.5000 (thr 0.75) | 1.0000 (thr 2.0) | 24.3729 (thr 20.0) | 0.6667 (thr 0.60) | 2/4 | 2 |
| 48 | 6.4049กำ0.9117 | 1.6505กำ0.0810 | 0.5000 (thr 0.75) | 1.5000 (thr 2.0) | 32.3747 (thr 20.0) | 0.6961 (thr 0.60) | 2/4 | 2 |
| 60 | 7.0704กำ0.7236 | 1.7009กำ0.0739 | 0.5000 (thr 0.75) | 1.5000 (thr 2.0) | 35.4329 (thr 20.0) | 0.6618 (thr 0.60) | 2/4 | 2 |

## Verdicts (supplementary thresholds)
- Peak Hit >= 0.75, Timing <= 2.0 wk, Peak Intensity <= 20.0%, Direction >= 0.60
- 'not accurate' on Peak Hit / Peak Intensity reflects missed peaks and magnitude error at matched peaks (see Peak Hit count / Missed peaks).
