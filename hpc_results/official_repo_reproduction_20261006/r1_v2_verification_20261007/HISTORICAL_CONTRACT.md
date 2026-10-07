# HISTORICAL 1025-ROW COMPARISON CONTRACT — RECOVERED

Phase B of the historical MIFlu replacement. Every field below was **read out of
the released historical tooling**, not inferred from a summary. Sources are
named per field so each can be re-checked.

This contract is what the transferred model must honour. It is **not** the
author-966 paper contract, and results from the two must never be mixed.

---

## 1. Data

| field | value | source |
|---|---|---|
| file | `data/raw/national_illness_raw.csv` | `innovation/paths.py:36` |
| **canonical sha256** | **`0a0648000066e12fe499f98693885b88ed3bc29fc8daca7f3af171b1bac86088`** | `innovation_deploy_root_v3_clean{6,13,14}` |
| rows | 1025 (+1 header) | verified |
| columns | 9 = `epiweek`, `release_date` + the 7 model variables | verified |

### ⚠️ dual-hash finding (resolved)

The same content exists in two byte-forms:

| lineage | sha256 | line endings |
|---|---|---|
| **`v3_clean*`** (the frozen Wave-1 / 4-vs-4 track) | `0a064800…6088` | **LF** |
| `v3_4`, `v3_5` (older pre-clean track) | `c2b983af…4c70d` | CRLF |

`diff` after `sed 's/\r$//'` on both sides reports **no differences** — they are
identical in content. The **`v3_clean` copy is canonical**, because that is the
lineage that produced the frozen comparison. The transfer reads that file.

## 2. Variables

```
VAR_COLS = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
            "ILITOTAL", "NUM. OF PROVIDERS", "OT"]
ILI_CHANNEL = 4          # "ILITOTAL" inside VAR_COLS
```
Source: `scripts/configs.py:61-65`, asserted by `configs._self_check`.

### ⚠️ variable-label defect in the OLD artefacts (does not affect metrics)

The OLD `validation_predictions.csv` files carry **shifted label strings**:

| index | OLD label (wrong) | TRUE `VAR_COLS` name |
|---:|---|---|
| 0 | `epiweek` | `% WEIGHTED ILI` |
| 1 | `release_date` | `% UNWEIGHTED ILI` |
| 2 | `% WEIGHTED ILI` | `AGE 0-4` |
| 3 | `% UNWEIGHTED ILI` | `AGE 5-24` |
| 4 | `AGE 0-4` | **`ILITOTAL`** |
| 5 | `AGE 5-24` | `NUM. OF PROVIDERS` |
| 6 | `ILITOTAL` | `OT` |

The old code took `var_names` from the raw CSV's leading columns, which include
`epiweek`/`release_date`, and dropped the last two true channels.

**Proven, not assumed.** At `forecast_origin = 613`, `step = 0`, `variable_index = 0`,
the old file records `y_true_physical = 2.8003499366606377`; raw row 717
(`613 + T`, `T = 104`) has `% WEIGHTED ILI = 2.80035` — an exact match. An
`epiweek` value would be ≈201606.

**Impact: none on any metric.** `mse_all_7vars_full_horizon_z` is computed over
the 7 **array** channels by index, so every published MSE/MAE is unaffected.
The defect is cosmetic-but-real: any consumer keying on the `variable` *name*
would mis-attribute. Corroborated by the metrics themselves — index 4 (labelled
`AGE 0-4`) carries `mse_z = 1.9014`, which is the project's known ILITOTAL-only
value, and the project's own rule is that ILITOTAL-only MSE ≈ 1.9–2.0× the
7-variable average.

The transferred model emits **truthful** labels and preserves the
`variable_index` keys exactly.

## 3. Split and windows

| field | value | source |
|---|---|---|
| split | **717 / 102 / 206** — a hard-coded constant | `clean_runner.py:52` |
| `TRAIN_END` / `VAL_END` | 717 / 819 | `configs.py:78-79` |
| T | **104** | `clean_runner.py:51`, `data_pipeline.py` |
| window stride | 1 | `data_pipeline.build_windows` |
| **split rule** | **by TARGET START**: `ts = i + T`; train if `ts < 717`, val if `ts <= 819`, else test | `data_pipeline.build_windows` |
| X / Y shape | `X[i] = data[i:i+T].T` → `(N,T)`; `Y[i] = data[i+T:i+T+L].T` → `(N,L)` | same |

Note this is **not** `int(N*0.7)`/`int(N*0.2)` arithmetic. `int(1025*0.2) = 205`,
but the contract is **206** — the split is a literal constant, which is why the
"obvious" recomputation gives the wrong answer.

Derived window counts (L=24: `nw = 1025 − 104 − 24 + 1 = 898`):

| split | rule | windows (L=24) | confirmed |
|---|---|---:|---|
| train | `ts < 717` | 613 | |
| val | `717 ≤ ts ≤ 819` | **103** | ✅ durable `validation_predictions.csv` has exactly **103** distinct origins, spanning **613–715** |
| test | `ts > 819` | 182 | |

## 4. Scaler

Per-column **float32** mean/std, fitted on `data[:717]` ONLY.
Source: `data/scaler_miflu_national.json`, re-verified identical in
`innovation_deploy_root_v3_clean14`.

```
mean = [1.755405306816101, 1.7133967876434326, 2658.326416015625,
        3699.761474609375, 9368.2890625, 1320.093505859375, 491997.59375]
std  = [1.2095322608947754, 1.1299502849578857, 2113.183837890625,
        4152.29541015625, 8853.4345703125, 504.9544982910156, 234443.296875]
```

`ScalerBundle.fit_from_train` warns explicitly that `dtype` MUST stay float32 —
normalising from float64 would move every reported MSE/MAE in the last decimal.

## 5. Training configuration

| field | value | source |
|---|---|---|
| epochs | 20 | `config_resolved.yaml` |
| batch size | 16 | same |
| learning rate | 5e-4 | same |
| patience | 7 | `clean_runner.py:368` |
| device | cuda | same |
| **checkpoint selection** | **best VALIDATION MSE** (`best_val_mse.pt`) | `clean_runner.py:380-384` |

The historical rule is already validation-based — it does **not** replicate the
author's released test-based selection. The transferred model therefore keeps
validation-only selection with no contract change on this axis.

## 6. Run matrix

| field | value | source |
|---|---|---|
| horizons | 24 / 36 / 48 / 60 | registry |
| seeds | **42 … 51** (10) | registry |
| primary models | 8 | `PRIMARY_MODELS` |
| run_key | `primary__<model>__L<H>__seed<S>__w1` | registry |
| primary runs | 320 = 8 × 4 × 10 | `complete_specs_598.json` |

The seven models held fixed: `qwen_time_llm`, `calf_llm`, `timecma_llm`
(LLM side) and `nlinear`, `dlinear`, `patchtst`, `itransformer` (non-LLM side).
The replaced slot is `gpt2_miflu`.

## 7. Prediction schema and scoring

Schema (`clean_metrics.PREDICTION_COLUMNS`), one row per
(origin, variable, step):

```
model_key, horizon, seed_or_rep, split, forecast_origin, target_date, step,
lead_weeks, variable, variable_index, y_true_z, y_pred_z,
y_true_physical, y_pred_physical
```

Primary metric: **`mse_all_7vars_full_horizon_z`** — over every valid element of
the complete 7-variable, complete-L output in z-space.
`mae_all_7vars_full_horizon_z` is the secondary.
Champion selector: **`average_MSE_4L`** = mean of the four per-L values.
Source: `clean_metrics.py` module docstring and the per-run
`paper_aligned_full_output_metrics.json`.

## 8. Declared deviations of the transferred model

| id | deviation | why unavoidable |
|---|---|---|
| **D1** | architecture = the official repository's MIFlu (corrected) | this IS the intervention |
| **D2** | text asset = the author's `text_emb_label_0507_<L>.txt` | the official repository's own horizon prompt embedding; the old self-built model used a project-built prompt encoder. **This is a non-MIFlu change and must be reported as such.** |
| **D3** | variable labels emitted truthfully | the old files' labels are shifted by two (§2) |

Everything else — dataset, split, window rule, scaler, z-space, T, horizons,
seeds, selection rule, prediction schema, scorer — is held identical.