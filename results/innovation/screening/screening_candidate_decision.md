# Stage E — Screening candidate decision (validation-only, preliminary)

**Label:** preliminary validation-only observed Screening rank (3 seeds). No journal-level superiority is claimed.

## Observed ranking (mean best-validation MSE, lower is better)

| rank | model | display name | mean val MSE | fidelity |
|---|---|---|---|---|
| 1 | patchtst | PatchTST-inspired | 1.051997 | INSPIRED_SIMPLIFICATION |
| 2 | nlinear | NLinear | 1.075024 | REFERENCE_FAITHFUL |
| 3 | dlinear | DLinear | 1.168701 | REFERENCE_FAITHFUL |
| 4 | itransformer | iTransformer-aligned | 1.231054 | REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS |

## Candidates sent to Stage F (pre-registered Full-Evaluation matrix)

The pre-registered controller matrix advances ALL four no-text backbones to Stage F: dlinear, nlinear, patchtst, itransformer.

Observed top-3 by Screening validation MSE: patchtst, nlinear, dlinear.

The original MIFlu control (`gpt2_miflu`) is advanced separately as the baseline arm (controller stage H) even though it is not part of the no-text Screening matrix.

## Defect found while verifying this stage

`scripts/innovation/select_best_model.py::build_audit` compares the baseline by the UN-SLUGGED key `gpt2_miflu`, but `parse_run_id` returns the SLUGGED `gpt2-miflu`; the baseline lookup is therefore always empty, `candidates` is empty, and `status` is `no_eligible_candidate`. This is what also blocked controller stage K (champion freeze). It is a naming/comparison defect in the SELECTION script only (no effect on any run's training or artifacts). Fixing it requires a frozen-source change + cascade and is submitted for authorization (see the final response).
