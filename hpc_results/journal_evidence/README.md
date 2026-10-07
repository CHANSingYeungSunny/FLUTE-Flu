# Journal-Reproducibility Evidence Package (MIFlu)

This directory holds the **re-runnable, reviewer-auditable** evidence for the
five concerns raised by the advisor. Every number a journal reviewer can ask
about now has a script, a deterministic input, and a persisted artifact.

---

## 1. What changed (and why)

| # | Advisor concern | Fix | Module / script |
|---|-----------------|-----|-----------------|
| Q1 | Overlapping windows averaged into one non-stationary curve | Explicit lead-time policy via `aggregate_lead_time` (3 modes). Figures declare the policy on the plot. | `compute_miflu_indicators.py`, `make_miflu_evaluation_figure.py` |
| Q1c | "Timing = 0.5" misread as lead time | Renamed `mean_abs_delta_t` → `peak_timing_error_weeks` (it is a peak-timing **error** in weeks, not a lead). | `compute_miflu_indicators.py` |
| Q2a | Y-axis "0–12" unreadable to clinicians | Figures + CSVs emit **physical patient counts** (`*_ili_phys`). Table V primary metric stays z-space (MIFlu §V-B). | `train_miflu.py`, `cdc_calendar.py`, `scaler_utils.py` |
| Q2b | X-axis drifted ~19 weeks | Real CDC epiweek calendar (handles 2002's 19-week hole + 53-week offsets) replaces the buggy synthetic `2002w01 + i weeks`. | `cdc_calendar.py` |
| Q3 | Scaler not reproducible at test time | `ScalerBundle` persists `mean_/scale_` to `data/scaler_miflu_national.json`; inverse-transform lives in one module. | `scaler_utils.py` |
| Q4 | Optimizer/wd/scheduler/loss/clip never disclosed | `recipes.py` with 3 explicit recipes (incl. the published baseline). | `recipes.py` |
| Q5 | Early-stopping could pick a peak-blind model | `EarlyStopping` — plain validation-loss monitoring with patience. The former peak-gate / dual-gate design (loss **and** Peak Hit Rate ≥ 0.7) was REMOVED with the peak_hit_rate indicator in 2026-09. | `early_stopping.py` |

**Decision record (approved by user):**
- National MSE/MAE primary = **z-space** (matches paper 1.542 / 0.726). Physical columns are **supplementary**.
- Main experiment data window = **full 1025 rows** (200201–202152).
- HPC re-run scope = priority subset (full / no_multi / no_lora / no_lora_multi) × L=24 × 10 reps, plus recipe sweep + early-stop study.

---

## 2. How to run

Single experiment (manual):
```bash
python scripts/train_ablation.py --variant full --horizon 24 --reps 10 \
    --epochs 20 --batch 16 --export-dir hpc_results/journal_evidence/full/reps_1_to_10
```

All experiments, sequentially (resume-safe):
```bash
python scripts/run_journal_experiments.py          # priority subset
python scripts/run_journal_experiments.py --full-l  # also L=24,36,48,60
```

Submit one chained job to the `stingy` partition (1 job, 4h cap; resumes on re-submit):
```bash
sbatch scripts/hpc_submit.sh
```

Aggregate into tables:
```bash
python scripts/aggregate_journal_tables.py
```

Build the evaluation figure (physical Y, real X, declared lead policy):
```bash
python scripts/make_miflu_evaluation_figure.py \
    --pred_csv hpc_results/journal_evidence/full/reps_1_to_10/predictions_miflu_L24_paper_protocol.csv \
    --L 24 --fig_dir results/ili/figures --met_dir results/ili/metrics
```

Compute the supplementary indicators (PTE and PIE):
```bash
python scripts/compute_miflu_indicators.py \
    --pred_csv hpc_results/journal_evidence/full/reps_1_to_10/predictions_miflu_L24_paper_protocol.csv
```

---

## 3. Output layout

```
hpc_results/journal_evidence/
├── <exp>/reps_1_to_10/
│   ├── metrics.csv                      # per-(L,rep) rows
│   ├── summary.csv                      # mean±std per L
│   ├── rep_NN/checkpoint.pth            # best-rep checkpoint
│   ├── rep_NN/early_stopping.json      # early-stopping decisions (if --early-stop)
│   └── predictions_miflu_L24_paper_protocol.csv  # dual-track + real epiweek
├── journal_table_viii.csv / .md        # aggregated Table VIII (z-space)
└── journal_table_physical.csv / .md    # SUPPLEMENTARY physical units
```
Experiments: `full`, `no_multi`, `no_lora`, `no_lora_multi`,
`full__adamw_cosine`, `full__huber_clip`, `full__earlystop`.

---

## 4. Reproducibility guarantees

- **No train/test leakage in inversion**: the scaler is fit on the TRAIN split
  only (`train_miflu.load_and_normalize` → `ScalerBundle`), persisted to JSON,
  and every later process inverts from that file — identical statistics.
- **X-axis is anchored to CDC epiweek labels**, not a count of rows, so the
  19-week hole in 2002 is preserved and visible; `cdc_calendar.self_check()`
  asserts `abs_week 820 == 2018-01-28`.
- **Peak metrics use ONE definition** (`compute_miflu_indicators.compute_peak_indicators`);
  the figure, the indicator CLI, and the early-stopper all call it.
- **Recipes are explicit** (`recipes.py`); `baseline` reproduces the published
  MIFlu numbers byte-for-byte in numerics.
- **Self-checks**: every new module has a `_self_check()` runnable via `__main__`.
