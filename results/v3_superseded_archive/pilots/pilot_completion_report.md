# v3 Pilot completion report

Generated 2026-09-16T17:24:50Z.

**8/8 pilots completed.** Gate `565869` COMPLETED 0:0 (8/8), compute node `gpu-a100-03`, `gpu-a100-05` excluded.

Pilot stage is **infrastructure verification only**. Results are **not rankable** and are **not** paper results; `selection_eligible=false`, `paper_result_eligible=false`, `test_access_allowed=false`. Test and holdout access counts remain **0**.

| # | model | horizon | seed | job | state | exit | best_epoch | best_val_mse | audit |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `nlinear` | 24 | 42 | 565871 | COMPLETED | 0:0 | 18 | 0.9920 | pass |
| 2 | `dlinear` | 24 | 42 | 565875 | COMPLETED | 0:0 | 20 | 1.0700 | pass |
| 3 | `patchtst` | 24 | 42 | 565879 | COMPLETED | 0:0 | 12 | 0.9451 | pass |
| 4 | `itransformer` | 24 | 42 | 565880 | COMPLETED | 0:0 | 3 | 1.1621 | pass |
| 5 | `gpt2_miflu` | 24 | 42 | 565882 | COMPLETED | 0:0 | 6 | 0.9046 | pass |
| 6 | `qwen_time_llm` | 24 | 42 | 565900 | COMPLETED | 0:0 | 5 | 1.2217 | pass |
| 7 | `calf_llm` | 24 | 42 | 565903 | COMPLETED | 0:0 | 13 | 1.6682 | pass |
| 8 | `timecma_llm` | 24 | 42 | 565911 | COMPLETED | 0:0 | 14 | 1.0687 | pass |

## Artifact audit

- required artefacts per run: **15**
- runs audited: **8/8**
- runs with any missing artefact: **0**

## Weights

Full checkpoints remain on scratch. Provenance is preserved without transferring them: each run records `checkpoint_sha256_file` and `state_dict_sha256` in `checkpoints/checkpoint_manifest.json`.

## Stopped here

Per instruction, the run stops after the eight pilots: **no Screening, no Full Validation, no negative controls, no champion selection, no Test**. `results/innovation/test_evaluations/` is empty.

## Figures

Pilot figures were produced by the frozen runner using the approved style; any cross-model v3 figure set must still use `q1_step_sweep.py` and the approved template, and is not generated at this stage.
