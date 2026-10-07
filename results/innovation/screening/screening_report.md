# Stage D — no-text backbone Screening report

Expected cells: **24** (models ['dlinear', 'nlinear', 'patchtst', 'itransformer'] x horizons [24, 60] x seeds [42, 43, 44])
Completed: **24** | failed: 0 | missing: 0 | duplicate: 0
Metadata-chain OK: 24 | checkpoint-restore OK: 24
Test access count: 0 | Test artifact count: 0
Stage D complete: **True**

## Per-(model,horizon) mean validation MSE

| model | horizon | n | mean val MSE | std |
|---|---|---|---|---|
| dlinear | 24 | 3 | 1.067293 | 0.002609 |
| dlinear | 60 | 3 | 1.270109 | 0.000672 |
| nlinear | 24 | 3 | 0.982466 | 0.003916 |
| nlinear | 60 | 3 | 1.167582 | 0.010634 |
| patchtst | 24 | 3 | 0.986381 | 0.013473 |
| patchtst | 60 | 3 | 1.117612 | 0.008053 |
| itransformer | 24 | 3 | 1.128073 | 0.007385 |
| itransformer | 60 | 3 | 1.334034 | 0.009569 |

Preliminary validation-only observed ranking (3 seeds) — not journal-level.
