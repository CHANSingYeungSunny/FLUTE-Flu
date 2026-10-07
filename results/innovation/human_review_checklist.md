# Human review checklist — pre-pilot source freeze

Generated `2026-09-14T21:01:46Z` · scientific protocol `innov-v2.0` · implementation source `innov-v2.4` · HEAD `1f6563f` (dirty=True)

## 1. Failed-run resolution
- [x] All 5 failed registry entries documented with root cause; 5 have a same-spec replacement (`audit/failed_runs_resolution.md`).
- [x] Failed runs are ineligible by construction (status != ok / no eligibility fields / legacy annotation).

## 2. Environment identity
- [x] CUDA devices `1`, name `NVIDIA GeForce GTX 1650 with Max-Q Design`; nvidia-smi captured (`audit/environment_report.md`).
- [x] Requested vs actual device recorded per run; the earlier "CPU smoke" wording is corrected (runs actually used cuda:0).

## 3. Aggregation regression
- [x] Same-CSV re-aggregation agrees row-by-row incl. date index, y_true/y_pred, MSE, MAE, PTE, PIE (`audit/aggregation_regression_report.json`).

## 4. End-to-end pipeline regression
- [x] Old MIFlu path vs innovation runner, same checkpoint + inputs; z and physical differences are 0.0 (`audit/pipeline_regression_report.json`).

## 5. GPT-2 adapter reproduction
- [x] Synthetic checkpoint: `torch.equal=True`, max_abs_diff=0.0 (`audit/gpt2_control_repro_report.json`).
- [ ] Real HPC-trained checkpoint validation — PENDING until the pilot stage (deliberately not done here).

## 6. Architecture fidelity disclosures
- [x] Three levels used; per-model fidelity + component-level file:line `dlinear`=REFERENCE_FAITHFUL; `nlinear`=REFERENCE_FAITHFUL; `patchtst`=INSPIRED_SIMPLIFICATION; `itransformer`=REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS; `fusion_forecaster`=None; `gpt2_miflu`=REFERENCE_FAITHFUL (`audit/architecture_equivalence.md`).

## 7. Eligibility gate
- [x] Selector is validation-only, `test_accessed=false`; smoke/pilot/failed/legacy runs excluded by construction (`results/innovation/model_selection_audit.json`).
- [x] All pilot specs carry `selection_eligible=false`.

## 8. Slurm safety
- [x] Structural + `bash -n` validation passed; confirmation guards present on every submit script; `submission_attempted=false`, `sbatch_invoked=false` (`audit/slurm_validation_report.json`).

## 9. Source snapshot integrity
- [x] Snapshot `aggregate_sha256=5a4c32473e293e8ab01b116e72c7326188b1844a1a84952b72bc2ec5f5eae25d` over `77` files; carried into every pilot spec.
- [ ] HPC source deployment verification — **UNVERIFIED** (`blocker=UNVERIFIED_HPC_SOURCE_DEPLOYMENT`). Pilot startup check aborts on any drift.

## 10. Test-set sealing
- [x] `frozen_winners.json` absent, `test_evaluations/` empty, zero test artifacts under `runs/`.

## Overall
- `pilot_generation_ready` = **True**
- `pilot_submission_ready` = **False** (blocker: `UNVERIFIED_HPC_SOURCE_DEPLOYMENT`)
- `full_sweep_submission_ready` = **False**
- `submission_attempted` = **False**; `sbatch_invoked` = **False**

> Pilot runs remain `selection_eligible=false`. No winner, no ranking, no test artifact, no journal performance conclusion.