# Paired statistics - CORRECTED, v2

Convention: `diff = mse(A) - mse(B)`; lower MSE is better; **A wins iff diff < 0**.
Invariant asserted for every row: `wins_A + wins_B + ties == n_cells`.

| A | B | mean MSE A | mean MSE B | mean diff | t | A wins | B wins | ties | n |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| miflu | nlinear | 2.0415 | 2.0495 | -0.0080 | -0.11 | **7** | 5 | 0 | 12 |
| notext | nlinear | 1.9222 | 2.0495 | -0.1274 | -2.28 | **11** | 1 | 0 | 12 |
| notext | miflu | 1.9222 | 2.0415 | -0.1194 | -1.50 | **7** | 5 | 0 | 12 |
| miflu | dlinear | 2.0415 | 2.3478 | -0.3063 | -3.36 | **9** | 3 | 0 | 12 |
| dlinear | nlinear | 2.3478 | 2.0495 | +0.2983 | +8.51 | **0** | 12 | 0 | 12 |
| timecma_llm | nlinear | 2.6700 | 2.0495 | +0.6205 | +10.94 | **0** | 12 | 0 | 12 |
| patchtst | nlinear | 3.9205 | 2.0495 | +1.8709 | +39.16 | **0** | 12 | 0 | 12 |
| itransformer | nlinear | 3.9847 | 2.0495 | +1.9351 | +31.47 | **0** | 12 | 0 | 12 |
| qwen_time_llm | nlinear | 5.2196 | 2.0495 | +3.1700 | +21.66 | **0** | 12 | 0 | 12 |
| calf_llm | nlinear | 5.5153 | 2.0495 | +3.4658 | +46.63 | **0** | 12 | 0 | 12 |
| miflu | timecma_llm | 2.0415 | 2.6700 | -0.6285 | -5.22 | **10** | 2 | 0 | 12 |
| miflu | patchtst | 2.0415 | 3.9205 | -1.8790 | -21.03 | **12** | 0 | 0 | 12 |

## Per-horizon win counts (A wins / n)

| A | B | L=24 | L=36 | L=48 | L=60 |
|---|---|---|---|---|---|
| miflu | nlinear | 0/3 | 2/3 | 3/3 | 2/3 |
| notext | nlinear | 3/3 | 3/3 | 3/3 | 2/3 |
| notext | miflu | 3/3 | 2/3 | 1/3 | 1/3 |
| miflu | dlinear | 0/3 | 3/3 | 3/3 | 3/3 |
| dlinear | nlinear | 0/3 | 0/3 | 0/3 | 0/3 |
| timecma_llm | nlinear | 0/3 | 0/3 | 0/3 | 0/3 |
| patchtst | nlinear | 0/3 | 0/3 | 0/3 | 0/3 |
| itransformer | nlinear | 0/3 | 0/3 | 0/3 | 0/3 |
| qwen_time_llm | nlinear | 0/3 | 0/3 | 0/3 | 0/3 |
| calf_llm | nlinear | 0/3 | 0/3 | 0/3 | 0/3 |
| miflu | timecma_llm | 1/3 | 3/3 | 3/3 | 3/3 |
| miflu | patchtst | 3/3 | 3/3 | 3/3 | 3/3 |
