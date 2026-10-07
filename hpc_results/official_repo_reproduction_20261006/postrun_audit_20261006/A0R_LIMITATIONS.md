# A0-R LIMITATIONS — why these four runs are neither a Table V reproduction nor `A1-P` results

Generated 2026-10-06. Append-only; nothing existing was modified.

**Subject.** Jobs `606365_0` (L24), `606378_1` (L36), `606385_2` (L48), `606412_3` (L60) —
four single-repetition runs of the author's released entry point at commit `6ed2101`.
The runner tagged them `A1_reconstructed_paper_config`; the lineage audit re-classifies the
family as **A0-R (released-code replay)** and distinguishes it from **`A1-P`**, the
paper-faithful A1 set. This file lists, with evidence, every reason the archived numbers may
**not** be presented as a Table V reproduction and may **not** be presented as `A1-P` results.

Evidence base: `provenance.txt` per run; the archived per-epoch CSVs; `slurm/miflu_a1_array.sbatch`;
`recovery/author_repo/main_ILI_lora.py` + `utils/tools.py` + `utils/metrics.py` +
`models/GPT4TS_lora.py` + `data_provider/data_loader.py`; `HYPERPARAMETER_PROVENANCE.md`;
`DEVIATION_LEDGER.md`; `a1_evidence_table_zh.md`; `cost_summary.csv`; `REMAINING_RUN_MATRIX.csv`.

---

## 1. Why these are NOT a reproduction of Table V

### 1.1 The quantity measured is not the paper's quantity

| # | Reason | Evidence |
|---|---|---|
| R1 | **Feature 0 only.** The paper's national task is 7-variable; the released Test path evaluates only `feat_id = 0` (column `"1"`, weighted ILI). The other 6 variables are never scored. | `data_loader.py` L312-316 (`__len__` omits `×enc_in` for `set_type==2`) ⇒ `feat_id = index//tot_len = 0`; `a1_evidence_table_zh.md` §6 |
| R2 | **Different space.** MSE/MAE are computed on z-scored feature-0 values (scaler fitted on the train slice), not on ILI counts. Table V's 1.542 / 1.422 / 1.414 / 1.364 are on a different scale and a different variable set. | `data_loader.py` L275-278 (`StandardScaler` fit on `df_data[0:676]`, `transform` on all); `metrics.MSE = np.mean((pred-true)**2)` |
| R3 | **Reduced to a single global scalar.** The harness averages over all origins and leads of one channel and keeps no per-lead/per-variable breakdown, so it cannot produce the per-horizon table structure the paper reports. | `A0R_METRIC_SEMANTICS.md` §1.2 |

### 1.2 The evaluation protocol leaks and is not paper-conformant

| # | Reason | Evidence |
|---|---|---|
| R4 | **The Test set selects the checkpoint (leakage).** Test MSE is computed every epoch and the minimum chooses the saved/loaded weights, so the reported Test number is not a clean holdout. | `main_ILI_lora.py` L211 (`test()` in-loop), L225-227 (`if mse_temp < min_mse`), L260-264 (load/save that state) |
| R5 | **Tail origins are discarded.** `DataLoader(drop_last=True)` drops the incomplete final test batch (10 / 14 / 2 / 6 windows for L24/36/48/60), so "Test" is a non-deterministic-to-describe subset. | `data_factory.py` L19-20 (`drop_last = drop_last_test = True`); counts from `A0R_FOUR_HORIZON_RUN_AUDIT.md` field 32 |
| R6 | **No containment rule.** The released loader defines no `strict` window-membership rule, so window overlap across splits is unconstrained — a further reason the split is not the paper's. | `data_loader.py` `Dataset_Custom` (no containment logic); contrast `DEVIATION_LEDGER.md` D-07 ("窗口归属 / containment strict" is an A2 correction) |

### 1.3 The training recipe is reconstructed, not paper-reported

| # | Reason | Evidence |
|---|---|---|
| R7 | **Epochs and learning rate are undisclosed by the paper.** The paper says only "set empirically"; `20 epochs / 5e-4` is a project assumption, and the author's own defaults are `1` and `1e-4` — three different values, none of them the paper's. | `HYPERPARAMETER_PROVENANCE.md` §0-§3; `provenance.txt` `epochs_provenance=RECONSTRUCTED_paper_discloses_no_value`, `lr_provenance=RECONSTRUCTED_paper_discloses_no_value` |
| R8 | **Optimizer / scheduler / weight decay are undisclosed.** The run uses Adam with a `lradj=type1` decay; the paper never states these. | entry point L159 (`torch.optim.Adam`); `utils/tools.py` L26-27; paper: `HYPERPARAMETER_PROVENANCE.md` §1 ("未披露") |
| R9 | **The released scheduler is described incorrectly by the project's own tables.** Effective decay is a hard-coded **0.9** in `type1`; `--decay_fac 0.75` is inert. Any claim that these ran "decay_fac=0.75" is wrong. | `utils/tools.py` L26-27 (0.9); measured step 0.00019371024450000004 = 5e-4·0.9⁹ (`DEVIATION_LEDGER.md` D-13) |
| R10 | **`freeze` is a no-op.** `--freeze 1` never sets `requires_grad=False`; the paper's "only PE and layer-norm are fine-tuned" is not what this run did. | `GPT4TS_lora.py` L58-61 / L87-90 (only sets `True`); measured 82,705,944/82,705,944 = 100 % trainable in the released default (`a1_evidence_table_zh.md` §3) |
| R11 | **Early stopping is disabled.** It is instantiated but its call is commented out, so training always runs the full 20 epochs; `--patience 3` is inert. | entry point L161 (instantiate), L235-238 (calls commented out) |

### 1.4 The "multimodal" claim is not exercised

| # | Reason | Evidence |
|---|---|---|
| R12 | **The released text path is inert.** In the author's `forward`, text tokens are concatenated *after* the patches and then truncated away under causal attention, so the text **content has exactly zero effect** on the forecast. These four "multimodal=1" runs therefore do not test the paper's multimodal mechanism. | `GPT4TS_lora.py` L130-145; `REPORT_EN.md` §E (equal-length swap `max|Δpred| = 0.0`, text gradient `0.0`); `a1_evidence_table_zh.md` §4 |
| R13 | **The paper's own token order cannot be determined**, so "which order is correct" is unresolved from the paper itself; the released order is only one of two readings. | `a1_evidence_table_zh.md` §4 (L205 vs L219 contradiction) |

### 1.5 The run set and the paper's aggregation differ by an order of magnitude

| # | Reason | Evidence |
|---|---|---|
| R14 | **One repetition vs the paper's ten.** The paper reports a mean of 10 repetitions; here each horizon is a single fit (`itr=1`). Stated in the run's own `itr_provenance=paper_says_mean_of_10_repetitions_author_harness_implements_itr`. | `provenance.txt`; `a1_results_aggregate.csv` `status = "PARTIAL - 1 of the paper's 10 repetitions"` |
| R15 | **"Repetitions" in this harness would not produce the paper's variance anyway.** The seed is fixed once (`fix_seed = 2021`) and never re-seeded inside the `itr` loop, so additional repetitions would be deterministic duplicates, not independent draws. | `main_ILI_lora.py` L27-30 (single seed), `L122` (`for ii in range(args.itr)` with no reseed) |

### 1.6 The comparison target itself is not a clean rerun

| # | Reason | Evidence |
|---|---|---|
| R16 | **The paper's Table V baseline columns are imported from refs [9]/[14]**, and the paper does not state whether MIFlu's own column is a rerun. So "reproducing Table V" is not a well-defined target. | paper §V-C via `HYPERPARAMETER_PROVENANCE.md` §4; `author_paper_targets.csv` `caveat` column |
| R17 | **Absolute scale mismatch.** The archived numbers (0.579–0.636 feature-0 z-MSE) and Table V (1.542–1.364) are different measurements; placing them in one table would be a category error. | direct comparison of `a1_results_per_run.csv` with `author_paper_targets.csv` |

---

## 2. Why these are NOT `A1-P` results

`A1-P` denotes the paper-faithful A1 configuration (the full paper-protocol A1 set). The four
A0-R runs fail that definition on several counts:

| # | Reason | Evidence |
|---|---|---|
| P1 | **They are 1/10 of the repetitions.** A1-P requires 4 horizons × 10 repetitions = **40 fits**; these four runs are **4 fits** (one each). | `REMAINING_RUN_MATRIX.csv` (7 missing repetitions per horizon, seeds 45-51); `a1_results_aggregate.csv` `n_repetitions_completed=1, n_repetitions_paper=10` |
| P2 | **They carry the released code's defects forward** (Test-selected checkpoint, feature-0-only Test, no-op freeze, early stopping off). A1-P must be a correctly-configured paper-protocol run, not a replay of the released defects. | `slurm/miflu_a1_array.sbatch` header comment "KNOWN DEFECTS KEPT"; `DEVIATION_LEDGER.md` D-03/D-08 |
| P3 | **The lineage audit classifies them as A0-R, explicitly "NOT A1-P".** | `HISTORICAL_AND_OFFICIAL_TIMELINE.csv` row `O8_A0R_four_horizon_released_code_runs … A0-R NOT A1-P`; `EXPERIMENT_AND_REPOSITORY_LINEAGE.md` §2 |
| P4 | **They were never the approved `A1-P` cost.** The full A1-P set is estimated at **11.27 GPU-h** (40 × 0.2817 measured); the round stopped with ≈0.056 GPU-h of headroom, so A1-P was not run. | `cost_summary.csv` ("estimated cost of the full A1 run (4 horizons × 10 repetitions), 11.27"); `postrun_audit_20261006/GPU_LEDGER_VERIFICATION.md` |
| P5 | **Non-zero exit on every run** — all four returned `author_exit_code = 1`; they are not clean completions and cannot be treated as finished A1-P fits. | `provenance.txt` `author_exit_code=1` (all four); `A0R_FOUR_HORIZON_RUN_AUDIT.md` §3 |

> **Allowed phrasing:** "four A0-R single-repetition runs of the released entry point
> (jobs 606365/606378/606385/606412), 1 of the paper's 10 repetitions each."
> **Disallowed phrasing:** "A1-P results", "the A1 reproduction", or any ranking/averaging of
> these four numbers with Table V or with A2.

---

## 3. Verified defect: predictions and targets were never saved in a re-scorable form

This was checked directly, not assumed:

1. **`test()` writes nothing.** It keeps `preds`/`trues` as local lists and returns only
   `(mse, mae)`; the arrays are dropped when the function returns.
   (`utils/tools.py` L290-331, esp. L316-320, L331.)
2. **The only `np.save` calls are commented out.**
   (`main_ILI_lora.py` L299-302, inside `test()`.)
3. **The only writer crashes.** `test_vis` is the sole function that persists predictions, but
   the call site passes a `torch.device` where `setting` is expected, so `setting + 'results.csv'`
   raises `TypeError` at L368 — before any file is written; this matches the observed
   `author_exit_code = 1`. Even if it ran, it would save only the *last lead* of *feature 0*
   (`pred[:,-1,0]`), not the full prediction tensor. (`utils/tools.py` L333-378; caller L267.)
4. **No prediction/target array exists for any horizon.** A workspace-wide search finds no
   `.npy` and no `*results.csv` produced by `test_vis` for these runs; the only numeric output
   is the per-epoch summary CSV of **20 scalar `(MSE, MAE)` pairs per horizon**.
5. **No checkpoint is in the local archive.** `torch.save(...checkpoint.pth)` (L264) runs
   before the crash, so a checkpoint should exist on HPC, but none was downloaded; the archived
   run directories contain only the CSV and `provenance.txt`.

**Consequence.** Independent re-scoring is **impossible** from what was archived: there are no
per-sample predictions to re-score, no targets to re-score against, and no checkpoint to
re-run inference from. Any independent verification must start from a new run (or from the
on-HPC checkpoint and data), not from these artifacts. This is the single largest
reproducibility gap in the A0-R deliverable, and it is why the four numbers can be reported as
"what the released entry point printed" but not independently confirmed.

---

## 4. What a genuine `A1-P` / Table V reproduction would require

1. Repair the evaluation: score all 7 variables, remove the Test-selection (use a
   validation-only or fixed-epoch rule), and stop discarding tail origins.
2. Save per-sample predictions and targets (and a checkpoint) in a documented space so the
   scores can be independently reproduced.
3. Run all 10 repetitions per horizon (40 fits) with a declared, re-seeded seed set.
4. Resolve the undisclosed hyperparameters explicitly (declare them reconstructed, or obtain
   them from the authors) rather than presenting 20/5e-4 as the paper's values.
5. Decide and document the text-path token order, then verify the text path is actually active.
6. State plainly that Table V's baseline columns are imported from refs [9]/[14], so it is the
   *contract*, not the *measurement*, that is being targeted.