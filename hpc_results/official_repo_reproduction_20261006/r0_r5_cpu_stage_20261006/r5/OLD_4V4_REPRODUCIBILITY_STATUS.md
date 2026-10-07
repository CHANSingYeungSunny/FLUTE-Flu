# OLD 4-vs-4 — Reproducibility Status

Read-only reconstruction. Assesses how far the historical 4-LLM-vs-4-non-LLM comparison can be re-derived from what survives locally. `UNRECOVERED` is used wherever a fact is not recoverable rather than guessed.

---

## 1. What is fully recovered

| Item | Status | Evidence |
|---|---|---|
| Exact model strings (4+4) | **RECOVERED** | `frozen_analysis_protocol.json`, `selection_outcome.json`, `complete_specs_598.csv` |
| Model implementation paths + classes | **RECOVERED** | `scripts/innovation/backbones/{dlinear,itransformer,patchtst,llm_inspired,gpt2_miflu_adapter}.py`, `scripts/miflu_model.py` |
| Historical MIFlu identity (own vs author) | **RECOVERED** | `scripts/miflu_model.py` (byte-identical to frozen snapshot); provenance audits |
| Dataset profiles + hashes + splits | **RECOVERED** | `scripts/configs.py:90-112`; both CSVs present on disk (1025 / 966 rows) |
| Metric / aggregation / checkpoint rule | **RECOVERED** | `clean_metrics.py`, `frozen_analysis_protocol.json`, `paper_aligned_selection_rule.json` |
| Stage C validation results (8 models × 4 L) | **RECOVERED** | `analysis/primary_summary_statistics.csv`, `model_ranking.csv`, `analysis_dataset.csv` (580 rows) |
| Stage D final Test results (3 models) | **RECOVERED** | `final/final_test_metrics.json`, `final_test_seed_level.csv` |
| Stage E results (author-966) | **RECOVERED (scores)** | `stage5_a2/scoring/average_mse_4L.csv`, `stage6/scoring/average_mse_4L.csv`, `recovery/stage5/results_tables_zh.md`, `recovery/stage6/results_report_zh.md` |
| Chinese DOCX report + SHA-256 | **RECOVERED** | `results/v3_clean/analysis/reports/MIFlu_非LLM与LLM流感预测最终报告_中文版.docx`, SHA-256 `9C573F48FB65E590C7973223D6CB5E0AB74E2DFA4F6DF11EC936F980A6B50EAD` |
| Stage D predictions | **RECOVERED + RE-SCORABLE** | 84 × `test_eval/results/*/predictions/test_predictions.csv`; tarball mirrors them; 52/52 bit-exact recompute |
| Stage E A2 predictions | **RECOVERED** | 44 `.npz` in `stage5_a2/scoring/predictions/` |
| As-run code snapshot (Wave-1) | **RECOVERED** | `results/innovation/source_snapshot/` (256 hash manifest) |

## 2. Exact-hash verifications performed this audit

| File | Current SHA-256 | Frozen snapshot SHA-256 | Verdict |
|---|---|---|---|
| `scripts/miflu_model.py` | `0e6bdb61213bfdcc72e6a5b2733fc891a613baeb3dc52b514997c1507bfc15ef` | same | **byte-identical** |
| `scripts/scaler_utils.py` | `efac4e58…` | same | byte-identical |
| `scripts/innovation/backbones/dlinear.py` | `b4868652…` | same | byte-identical |
| `scripts/innovation/backbones/itransformer.py` | `40dcc869…` | same | byte-identical |
| `scripts/innovation/backbones/patchtst.py` | `fb0db916…` | same | byte-identical |
| `scripts/innovation/backbones/gpt2_miflu_adapter.py` | `7170c37b…` | same | byte-identical |
| `scripts/configs.py` | `06eb39cd…` | `5b64ad54…` | **DIFFERS** — `author_966` profile added (Stage-4 adapter), additive |
| `scripts/textual_embedder.py` | `13b51b34…` | `55022ebb…` | **DIFFERS** — post-snapshot edits |
| `scripts/innovation/backbones/llm_inspired.py` | `e435133e…` | `5c1e744b…` | **DIFFERS** — `text_mode="removed"` short-circuit refactor (deferred-control patch), behaviour-preserving for the historical runs |

The Wave-1 as-run code is therefore preserved by the snapshot; the `llm_inspired.py` edit is the only one that touches a 4-vs-4 backbone, and it only adds the `removed` control branch.

## 3. Gaps and UNRECOVERED items

| Item | Status | Why |
|---|---|---|
| `gpt2_miflu` / `notext` `total_parameters` | **UNRECOVERED** | only `trainable_parameters` was recorded; the A2/966 metric files omit totals. (Supporting: `hpc_results/checkpoints/best_miflu_L24.pth` = 328,585,240 B.) |
| Stage C per-run raw predictions for the 8 primary models | **UNRECOVERED** | only aggregated metric rows survive locally (`wave1_analysis_dataset.jsonl`); raw Wave-1 prediction arrays were not mirrored (compact checkpoints only) |
| Stage 6 (author-966 8-model) prediction arrays | **UNRECOVERED locally** | `results/stage6/scoring/predictions/` (116 npz) exists only on HPC scratch; scores retained locally |
| Original Stage C/D model checkpoints | **UNRECOVERED (source hash)** | `final_candidate_freeze.json` records `source_full_checkpoint_sha256: not_recorded` (deleted in the v3.15 compact migration); compact `.safetensors` hashes recorded but the blobs live on HPC |
| Exact training-time code for the earliest (Aug-2026) runs | **UNRECOVERED** | repository has a single git commit (`1f6563f`); `scripts/miflu_model.py` is byte-stable since the 2026-09-19 snapshot but earlier edits are untraceable via git |
| `seasonal_naive` semantic consistency across stages | **NOT CONSISTENT** | Formula 1 (Stages A–D) never reads future rows; Formula 2 (Stage E) reads target rows `ts+0..ts+7` at L=60 (verified `pred[:,:,52]==target[:,:,0]`). See Map Q9. |
| Wave-1 `variable` label vs index in `test_predictions.csv` | **DATA CORRECT / LABEL SHIFTED +2** | re-score by `variable_index`; do not trust the `variable` string |

## 4. Cross-lineage hygiene (must be respected)

- `project_1025` (Stages A–D) and `author_966` (Stage E) absolute MSEs **must not** be ranked together, averaged, or used to fill each other.
- The historical self-built lineage (Stages A–E) and the official-repository lineage (`hpc_results/official_repo_reproduction_20261006/`, from 2026-09-24) **must not** share a ranking table or be cross-scored (`EXPERIMENT_AND_REPOSITORY_LINEAGE.md` §4).
- The author's released code (A0-R) is **not** the model used in this comparison; it is separately documented as defective (LoRA never applied, `freeze` no-op, Test used for checkpoint selection).

## 5. Net verdict

The historical 4-vs-4 comparison is **reconstructable to a high degree**: the exact model identities, code, data contract, evaluation contract, headline validation and final-Test numbers, the DOCX report (hash-pinned), the Stage-D predictions (re-scorable bit-exact) and the Stage-E A2 predictions are all present. The **principal unrecoverable items** are: `gpt2_miflu`/`notext` total parameter counts, the Stage-C raw per-run prediction arrays, the Stage-6 prediction npz (HPC-only), original checkpoint source hashes, and the exact training-time code for pre-snapshot runs. The **principal correctness caveat** is the Stage-E L=60 `seasonal_naive` future-row leak, which makes the author-966 seasonal-naive L=60 value (2.1035) not comparable to its B-track counterparts.