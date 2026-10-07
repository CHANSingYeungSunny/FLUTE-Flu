# Restoration verification (compute node)

Generated 2026-09-17T01:30:36Z · job 566246 · node gpu-a100-06 · device cuda

**8/8 families passed** (`max_abs <= 1e-05`, `rel_mse <= 1e-06`).

| run_key | rows | max_abs_diff | rel MSE diff | passed |
|---|---|---|---|---|
| `screening_nlinear_L24_seed42` | 2472 | 8.882e-16 | 0.000e+00 | True |
| `screening_dlinear_L24_seed42` | 2472 | 8.882e-16 | 0.000e+00 | True |
| `screening_patchtst_L24_seed42` | 2472 | 4.441e-16 | 0.000e+00 | True |
| `screening_itransformer_L24_seed42` | 2472 | 4.441e-16 | 0.000e+00 | True |
| `screening_gpt2_miflu_L24_seed42` | 2472 | 8.882e-16 | 0.000e+00 | True |
| `screening_qwen_time_llm_L24_seed42` | 2472 | 4.441e-16 | 0.000e+00 | True |
| `screening_calf_llm_L24_seed42` | 2472 | 2.220e-16 | 0.000e+00 | True |
| `screening_timecma_llm_L24_seed42` | 2472 | 4.441e-16 | 0.000e+00 | True |

Only ACCEPTED durable checkpoints were restored; no Screening cell was re-run. Test/holdout access counts remain 0/0.
