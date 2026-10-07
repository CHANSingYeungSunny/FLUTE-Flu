# Plan compliance matrix — round 1 (infrastructure + local smoke)

Authoritative plan: `MIFlu_innovation_plan_v2.md`
SHA-256: `AA4AB1C8842E893A4690787E17ADD0CA193C86825FFF9FD89F46952C7F9E7961`
(recomputed at runtime by `scripts/innovation/audit_repo.py` →
`plan_sha256.json`; `matches == true`).

## The 12 required deliverables for THIS round

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Repo audit + plan compliance matrix | DONE | `audit.md`, this file, `plan_sha256.json`, `dependency_probe.json` |
| 2 | ForecastBackbone / TextEncoder / FusionModule interfaces | DONE | `scripts/innovation/interfaces.py` |
| 3 | gpt2_miflu control adapter | DONE | `backbones/gpt2_miflu_adapter.py` (wraps existing MIFlu) |
| 4 | DLinear/NLinear, PatchTST, iTransformer | DONE | `backbones/{dlinear,patchtst,itransformer}.py`; `test_backbone_shapes.py` |
| 5 | none / TF-IDF+SVD / GPT-2 text encoders | DONE | `encoders/{none_encoder,tfidf_svd,gpt2_encoder}.py` |
| 6 | concat_projection / film_gate / cross_attention | DONE | `fusion/{concat_projection,film_gate,cross_attention}.py` (+identity) |
| 7 | run_id, independent checkpoint/prediction/metric/figure, registry | DONE | `run_id.py`, `run_artifacts.py`; `test_no_overwrite.py`; 14 registry rows |
| 8 | val-MSE early stopping + best checkpoint restoration | DONE | `trainer.py`; reused audited `early_stopping.py`; `restore_ok=True` in smoke |
| 9 | PTE, PIE and the single literature peak criterion | DONE | `metrics.py`; `peak_criteria_spec.md`; `test_peak_criteria.py` |
| 10 | validation-only select_best_model + test-access failure test | DONE | `select_best_model.py`; `test_test_gate.py` (`test_accessed=false`) |
| 11 | smoke test per implemented candidate (L=24, seed=42, 1 epoch) | DONE | `smoke.py`; 8/8 combos passed, `restore_ok=True` |
| 12 | generate (do NOT submit) HPC screening + full-sweep scripts | DONE | `hpc_specs.py` → `hpc_scripts/{innovation_worker,submit_innovation_smoke,submit_innovation_screening,submit_innovation_full}.sh` |

## Scientific constraints (§2)

| Constraint | Status |
|---|---|
| text encoder / backbone / fusion recorded separately | DONE — per-run `config_resolved.yaml.components` + `architecture_report` |
| data / split / scaler / prompt stats / L / step aggregation / seeds fixed | DONE — read from `configs.py` + `scaler_utils.py`; train-only fitting |
| stop on validation MSE only, patience=7, save+restore best | DONE — `trainer.py` (+ `early_stopping_audit.md`) |
| compute PTE/PIE after training; only literature criterion | DONE — `metrics.py`, `peak_criteria_spec.md` |
| test not used for tuning/stopping/selection/budget/thresholds | DONE — runner writes no test artifacts; selector is validation-only + guarded |
| each horizon evaluated independently | DONE — one run per (…, L, seed) |

## Revisions 1–10 requested by the user

| # | Revision | Where implemented |
|---|---|---|
| 1 | no test artifacts in validation runs; test only under `test_evaluations/{test_eval_id}/` after freezing | `runner.run_one` (validation-only), `runner.run_test_evaluation` (gated by `frozen_winners.json`), `run_artifacts.create_test_eval_dir` |
| 2 | audit `early_stopping.py` before reuse | `early_stopping_audit.md` → REUSED (val-loss only) |
| 3 | numerical regression vs existing pipeline | `tests/innovation/test_numeric_regression.py` (PASSED: 182 weeks, MSE/PTE/PIE agree) |
| 4 | split smoke into component shapes + few E2E combos; no Cartesian product; no ranking | `test_backbone_shapes.py` (shapes) + `smoke.py` (8 representative combos, "NOT for ranking") |
| 5 | architecture-equivalence reports; label "inspired" if deviating | `architecture_report()` in every backbone; `test_architecture_equivalence.py` |
| 6 | audit prompt variation before TF-IDF+SVD | `prompt_variation_report.json` → 4 unique prompts, within-horizon 0 ⇒ fixed contextual embedding baseline |
| 7 | check sklearn; else `UNAVAILABLE_LOCAL_DEPENDENCY`, no install | `dependency_probe.json` → sklearn 1.6.1 available; `TfidfSvdEncoder.is_available()` |
| 8 | one-run-per-job resumable Slurm; timeout/preemption/resume | `hpc_specs.py` → worker + auto-submit chains; runner `--skip-if-done`, `--max-seconds` |
| 9 | define season/target/tie/incomplete/zero-denominator before PTE/PIE | `peak_criteria_spec.md`; enforced in `metrics.py`; `test_peak_criteria.py` |
| 10 | `results/innovation/audit/` + runtime plan hash | `AUDIT_DIR`; `paths.plan_sha256()` recomputed per run, blocks on mismatch |

## Explicitly OUT OF SCOPE this round

TimesNet, TimeMixer, ModernTCN, fastText, BERT, MiniLM, TSFM
(Chronos/TimesFM/Moirai) → batch 2. EvoForecast → deferred until the main
infrastructure, test gate, budget recording and standard-search baseline are
all validated in a separate protocol.

**No performance ranking or paper conclusion is produced from smoke runs.**
