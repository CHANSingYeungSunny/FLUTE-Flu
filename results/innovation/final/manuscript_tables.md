# Manuscript tables — one-time final Test evaluation

Test evaluation ID: `final_nlinear_20260915T145710Z` (single-use; one receipt, one manifest).
Champion: **nlinear** (frozen, never reselected). Baseline: **gpt2_miflu**.
Metrics are computed on the held-out Test split only; the champion was selected on
validation before any Test access.

## Table 1 — Test MSE / MAE by model and horizon (physical ILI units)

| Model | L | n seeds | MSE mean | MSE 95% CI | MAE mean | MAE 95% CI |
|---|---|---|---|---|---|---|
| gpt2_miflu | 24 | 3 | 444,951,612.95 | [328,062,033.03, 609,822,904.36] | 14,330.04 | [12,912.01, 15,436.39] |
| gpt2_miflu | 36 | 3 | 485,841,664.57 | [444,442,412.15, 510,899,769.59] | 14,814.62 | [14,737.88, 14,951.93] |
| gpt2_miflu | 48 | 3 | 453,946,781.74 | [422,622,442.32, 498,887,120.58] | 14,135.14 | [14,087.75, 14,174.29] |
| gpt2_miflu | 60 | 3 | 519,090,819.58 | [459,530,485.61, 594,432,121.63] | 15,004.71 | [14,651.10, 15,403.66] |
| nlinear | 24 | 10 | 336,782,610.35 | [335,295,210.16, 338,308,672.44] | 12,406.29 | [12,323.34, 12,488.45] |
| nlinear | 36 | 10 | 389,782,114.15 | [388,400,543.53, 391,243,420.95] | 13,491.73 | [13,430.91, 13,561.28] |
| nlinear | 48 | 10 | 423,632,711.70 | [422,662,214.35, 424,567,050.81] | 14,216.81 | [14,178.33, 14,254.34] |
| nlinear | 60 | 10 | 439,611,123.66 | [437,514,844.90, 441,498,344.04] | 14,551.78 | [14,492.44, 14,609.34] |

## Table 2 — Peak timing / intensity and literature criterion

| Model | L | PTE (weeks) | PIE (%) | Peak hit ratio | Criterion (PTE<=1w & PIE<=25%) |
|---|---|---|---|---|---|
| gpt2_miflu | 24 | 4.67 | 72.18 | 0.111 | not met |
| gpt2_miflu | 36 | 5.33 | 77.34 | 0.000 | not met |
| gpt2_miflu | 48 | 2.00 | 25.29 | 0.167 | not met |
| gpt2_miflu | 60 | 2.00 | 23.27 | 0.333 | not met |
| nlinear | 24 | 1.67 | 9.50 | 0.700 | not met |
| nlinear | 36 | 2.00 | 10.57 | 0.667 | not met |
| nlinear | 48 | 0.35 | 3.33 | 1.000 | MET |
| nlinear | 60 | 0.15 | 2.08 | 1.000 | MET |

## Table 3 — Paired champion vs baseline comparison (matched seeds)

| L | Metric | Champion mean | Baseline mean | Diff | % | t | p | p (Holm) | dz |
|---|---|---|---|---|---|---|---|---|---|
| 24 | mse_ili_phys | 338,914,826.05 | 444,951,612.95 | -106,036,786.90 | -23.83 | -1.257 | 0.3356 | 0.9615 | -0.726 |
| 24 | mae_ili_phys | 12,455.43 | 14,330.04 | -1,874.61 | -13.08 | -2.320 | 0.1461 | 0.7307 | -1.339 |
| 36 | mse_ili_phys | 389,712,525.44 | 485,841,664.57 | -96,129,139.13 | -19.79 | -4.686 | 0.0426 | 0.2985 | -2.706 |
| 36 | mae_ili_phys | 13,399.14 | 14,814.62 | -1,415.47 | -9.55 | -17.817 | 0.0031 | 0.0251 | -10.287 |
| 48 | mse_ili_phys | 423,555,543.38 | 453,946,781.74 | -30,391,238.36 | -6.69 | -1.310 | 0.3205 | 0.9615 | -0.756 |
| 48 | mae_ili_phys | 14,188.38 | 14,135.14 | 53.24 | 0.38 | 1.037 | 0.4088 | 0.9615 | 0.599 |
| 60 | mse_ili_phys | 441,239,326.95 | 519,090,819.58 | -77,851,492.63 | -15.00 | -1.962 | 0.1887 | 0.7548 | -1.133 |
| 60 | mae_ili_phys | 14,554.52 | 15,004.71 | -450.20 | -3.00 | -2.976 | 0.0968 | 0.5809 | -1.718 |

> Paired tests use only the seeds present in BOTH arms (42, 43, 44).
> With n=3 matched seeds these tests are severely underpowered; they are
> reported for completeness and must not be read as evidence of superiority.
