# OLD 4-vs-4 — Data and Evaluation Contract

Read-only reconstruction. All values quoted from the repository; nothing modified.

There are **two dataset vintages** and **three historical evaluation code-paths**. They are kept separate below because the project's own rule forbids conflating them
(`scripts/configs.py:84-89`: "`author_966` is a SEPARATE profile so track A (author 966-row vintage) and track B (July 1025 snapshot) can never be silently conflated").

---

## 1. The two dataset profiles (single source of truth: `scripts/configs.py:90-112`)

| Field | `project_1025` (a.k.a. July-2026 snapshot) | `author_966` (author vintage) |
|---|---|---|
| `data_path` | `data/raw/national_illness_raw.csv` | `data/raw/national_illness_raw_paper_exact.csv` |
| `sha256` | `c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d` | `31ffc1693de205ca8de5e966d40c93252e0a0076a212fffc54d1418e1a13b87a` |
| `n_rows` | **1025** | **966** |
| `split_rule` | `project_70_10_20` | `author_676_97_193` |
| `train_end` / `val_end` | **717 / 819** | **676 / 773** |
| `date_range_string` | "between 2002 and 2021" | "between 2002 and 2020" |
| `scaler_path` | `data/scaler_miflu_national.json` | `data/scaler_miflu_author966.json` |

Verified on disk: `data/raw/national_illness_raw.csv` = 1025 data rows (mtime 2026-07-18); `data/raw/national_illness_raw_paper_exact.csv` = 966 data rows (mtime 2026-08-28).
7 variables, fixed order: `["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24", "ILITOTAL", "NUM. OF PROVIDERS", "OT"]`; `ILI_CHANNEL = 4` (`configs.py:61-66`).

---

## 2. Stage-by-stage data contract

### 2.1 `wave1_validation_v3clean` — the headline 4-vs-4 (historical)

| Item | Value |
|---|---|
| Dataset | `data/raw/national_illness_raw.csv` (`project_1025`), sha `c2b983af…` |
| Rows | 1025 |
| Split | train `[0,717)`, validation `[717,819)` = 102, test `[819,1025)` = 206 |
| Test target weeks | absolute weeks **820 … 1024** (2018-01-28 … 2021-12-26) |
| Horizons | `[24, 36, 48, 60]` (trained independently) |
| Seeds | `[42,43,44,45,46,47,48,49,50,51]` (10) |
| Lookback / IO contract | T=104 → L, 7 → 7 variables (`results/v3_clean/preregistration/seven_variable_io_contract.json`) |
| Scaler | StandardScaler, **train-only** (`data[:717]`, ddof=0, +1e-8), float32 — `scripts/scaler_utils.py`, `scripts/configs.py:24-31` |
| Window rule | **legacy target-start** (`ts < train_end → train`, etc.) — `scripts/innovation/clean_runner.py` |
| Episodes | 580 accepted rows = primary 8×4×10 = 320, baselines 2×4 = 8, ablations 6×4×10 = 240, negative controls 12. Test/holdout access = 0 during Wave-1 (`frozen_analysis_protocol.json`) |
| Source | `results/v3_clean/analysis/analysis_dataset.csv` (580 rows), `wave1_analysis_dataset.jsonl` |

### 2.2 `final_test_holdout_v3clean` — the one-time Test

| Item | Value |
|---|---|
| Same profile/split/scaler as 2.1 | yes; checkpoint = Wave-1 validation-selected |
| Models entering | exactly 3 (frozen): `gpt2_miflu`, `nlinear`, `seasonal_naive` |
| Runs | **84** = gpt2_miflu 40 + nlinear 40 + seasonal_naive 4 (`test_eval/test_eval_keys.txt`, `terminal_test_audit.json`) |
| Test windows | 182/170/158/146 for L=24/36/48/60 |
| Access discipline | released **exactly once**; 25/25 terminal audit; no 85th job; `pre_test_freeze_audit.json` all-green (`pre_test_authorization_record.json`) |
| Source | `results/v3_clean/final/final_test_metrics.json`, `final_test_seed_level.csv`, `test_eval/results/*` |

### 2.3 `a2_author966_stage5` and `stage6_author966_8model` (post-clone)

| Item | Value |
|---|---|
| Dataset | `data/raw/national_illness_raw_paper_exact.csv` (`author_966`), sha `31ffc169…` |
| Rows | 966 |
| Split | train `[0,676)` / validation `[676,773)` = 97 / test `[773,966)` = 193 |
| Window rule | **`--containment strict`**: the WHOLE target block `[o+1, o+L]` must lie inside its split; straddlers dropped. Window counts L24 **549/74/170**, L36 **537/62/158**, L48 **525/50/146**, L60 **513/38/134** |
| Horizons / seeds | `[24,36,48,60]` / `[42,43,44]` (3) |
| Scaler | train-only `[0,676)` (`data/scaler_miflu_author966.json`) |
| Runs | A2 = 36 fits (3 models: miflu, notext, nlinear) + 8 baselines = 44; Stage 6 = 96 fits (8 models) + A2's notext control; 116 Test artefacts |
| Source | `hpc_results/stage5_a2/`, `hpc_results/stage6/`, `recovery/stage5/`, `recovery/stage6/` |

### 2.4 `innovation_v2_screening` (superseded precursor)

`results/innovation/` — 1025-row July snapshot, legacy target-start split, seeds 42–51 for nlinear and 42–44 for the gpt2_miflu champion; one-time Test (52 cells, `final_nlinear_20260915T145710Z`). Retained as history, superseded by clean-v3.

---

## 3. Metric definition (identical across all three code paths)

**Primary:** `mse_all_7vars_full_horizon_z` — mean squared error over **every valid element** of the complete 7-variable, complete-horizon output, in **StandardScaler (z) space** (train-only scaler), lower is better.
**Aggregation:** per-horizon point estimate = mean over the frozen seeds; **`average_MSE_4L` = arithmetic mean of the four per-L means.**
**Secondary:** `mae_all_7vars_full_horizon_z`; reported alongside, never combined into a weighted score.

Quoted (`results/v3_clean/analysis/frozen_analysis_protocol.json`):
> `"primary_champion_selector": {"metric": "mse_all_7vars_full_horizon_z", "per_L": "mean across frozen 10 repetitions (seeds 42..51) for each L in {24,36,48,60}", "aggregate": "average_MSE_4L = arithmetic mean of the four per-L means"}`

**Forbidden by the frozen rule** (`paper_aligned_selection_rule.json`, `frozen_analysis_protocol.json`):
> `"forbidden": ["peak_hit_ratio tie-breaker", "PTE/PIE tie-breaker", "baseline-relative ratio", "(r24+r60)/2"]`

**PTE/PIE (secondary application metrics only, never used in selection):**
PTE = |predicted peak week − observed peak week| (weeks), threshold ≤ 1 week;
PIE = |predicted peak intensity − observed peak intensity| / observed peak intensity (%), threshold ≤ 25% (`scripts/innovation/clean_metrics.py:172-229`).

Per-horizon `average_MSE_4L` note in every test metric file:
> `"primary_selector_role": "average_MSE_4L is the arithmetic mean of the four per-L values of mse_all_7vars_full_horizon_z"`

---

## 4. Forecast keys / output schema

Test predictions are stored in one **long** schema (`scripts/innovation/clean_metrics.py:41-46`):

```
model_key, horizon, seed_or_rep, split, forecast_origin, target_date, step, lead_weeks, variable, variable_index, y_true_z, y_pred_z, y_true_physical, y_pred_physical
```

- `step` = 0..L-1 (lead `k`), `lead_weeks = step+1`; fixed-step metrics use steps 0/1/2/3 (leads 1–4), each reported **independently** (never averaged).
- `y_true_physical` / `y_pred_physical` = inverse-transformed to original units via the train-only scaler.
- **Caveat (found during this audit):** in `test_predictions.csv` the `variable` string is shifted by +2 relative to `variable_index` (label `ILITOTAL` sits on index 6 while the ILITOTAL data sits on index 4). The **data and index are correct**; re-score by `variable_index`, never by the `variable` label.
- A2/966 predictions are stored instead as `.npz` with keys `pred, target, target_start_row, L, seed, var_cols, train_mean, train_std, model, profile, containment, space`.

---

## 5. Checkpoint-selection rule and Test discipline

- **Selection = lowest VALIDATION `mse_all` per (model, horizon, seed)** within a fixed 20-epoch fit (`train_backbone_966.py:209-219`, `train_nlinear_966.py:176-183`, `configs.py` regression gate). Ordinary validation loss — **never peak-aware** (`original_miflu_protocol_manifest.json`: "checkpoint: lowest validation loss (NOT peak-aware)").
- **Test was NOT accessed during selection.** Wave-1 evidence: `frozen_analysis_protocol.json` → `"test_holdout_never_accessed": true`, `"test_access": 0, "holdout_access": 0`. A2/Stage-6: `DEFER_TEST=1` runs train only and write per-(L,seed) best-val checkpoints; a single later scoring pass does all Test inference (`MEMORY.md`; `train_backbone_966.py:225-235`).
- Optimiser/hyper-params (all stages): **Adam, lr 5e-4, no scheduler, wd 0, batch 16, fixed 20 epochs, no early stopping, fp32** (`recovery/stage6/results_report_zh.md` §2; `train_backbone_966.py:190`; `configs.py`).
- Seed convention: `set_seed(seed + L)` (`train_nlinear_966.py:148`, `train_backbone_966.py:167`).

## 6. Statistical contract (v3_clean final)

- 95% CI = seed-level t-interval (df = 9) for the 10-seed models.
- Matched-seed paired t-tests; C2/C3 are one-sample t-tests against the deterministic Seasonal-Naive reference (zero variance).
- Multiple comparison: Holm-Bonferroni step-down across the 3 pre-registered primary tests (`final_statistical_analysis_plan.json`; report §六).
- Equivalence policy: report a top-equivalence set instead of manufacturing a unique champion when leaders are indistinguishable.

---

## 7. What must never be mixed

- `project_1025` and `author_966` absolute MSEs may **not** be ranked together, averaged, or used to fill each other (project rule; `configs.py`; `REPOSITORY_PROVENANCE.md` §3).
- The **author's released code** (A0-R lineage) is a different lineage from this historical self-built one and may not share a ranking table (`EXPERIMENT_AND_REPOSITORY_LINEAGE.md` §4).