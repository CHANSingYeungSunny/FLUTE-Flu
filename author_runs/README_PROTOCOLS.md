# `author_runs/` — TWO PROTOCOLS, NEVER MIXED

This directory holds two different experiments. They have different seeds,
different numbers of repetitions, and different purposes. A file from one must
never be used as a row of the other. This note exists because mixing them caused
a multi-turn confusion on 2026-11-01 (see `AGENTS.md` §10 and HARD RULE 10).

---

## 1. REPRODUCTION protocol — `AGENTS.md` §1.1, Table V

* **Purpose**: reproduce the paper's Table V (MIFlu, 7-variable aggregate
  MSE/MAE, z-space).
* **Seeds**: 2021–2030 (the author's `fix_seed = 2021` plus a 10-repetition loop).
* **Repetitions**: 10. The reported number is the **mean over the 10 reps**.
* **Location**: `author_runs/L{L}_s2021/`, checkpoints in `ckpt_L{L}_s2021/`.
* **Numbers**: 1.3045 / 1.3561 / 1.6543 / 1.6829 at L = 24/36/48/60
  (4-horizon mean 1.4995 vs paper 1.4355, +4.5%).

### The `_s2021_pred` directories are REPRODUCTION-protocol only
`author_runs/L{L}_s2021_pred/` contains a **single-rep (seed 2021)** export whose
per-window prediction CSV was written so the per-step / PTE-PIE / figure
machinery had a representative curve to draw. It is **not** a benchmark cell:

* it is one seed, not the benchmark's three (42/43/44);
* its checkpoint is a validation-selected `best_miflu_L{L}.pth` of a
  reproduction run, i.e. selected under a different protocol.

**It must never be imported as the MIFlu benchmark row.** Because of that, the
CSVs here are named `repro_pred_L{L}.csv`, not `pred_L{L}.csv`, so that a
`--csv-pattern` aimed at benchmark cells cannot pick them up by accident.

| file | protocol | seed(s) | use |
|---|---|---|---|
| `L{L}_s2021_pred/repro_pred_L{L}.csv` | reproduction | 2021, 1 rep | per-step / figure support for Table V only |
| `L{L}_s2021_pred/results_L{L}.csv` | reproduction | 2021, 1 rep | the run's own ILITOTAL MSE/MAE |

---

## 2. BENCHMARK protocol — `AGENTS.md` §1.2, HARD RULE 9

* **Purpose**: compare MIFlu against the other 16 arms on equal terms.
* **Seeds**: **42, 43, 44** — identical to every other arm.
* **Repetitions**: 1 fit per (L, seed); each fit contributes its own
  validation-selected best-epoch checkpoint, exactly like
  `best_<arm>_L{L}_seed{S}.pth` for the 16 arms.
* **Reported number**: the **mean over the 3 seeds** (± sd), with `n_seeds = 3`
  stated in the caption.
* **Location**: `author_runs/L{L}_s{S}/`, checkpoints in `ckpt_L{L}_s{S}/`.

| file | protocol | use |
|---|---|---|
| `L{L}_s{S}/predictions_miflu_L{L}_s{S}_paper_protocol.csv` | benchmark | the only source the MIFlu benchmark row may be built from |
| `L{L}_s{S}/results_miflu_paper_protocol_*.csv` | benchmark | that seed's own ILITOTAL MSE/MAE |
| `L{L}_s{S}/training_miflu_log_*.txt` | benchmark | checkpoint-selection (`best val_mse`) and test metrics |

Convert them with:

```
python scripts/import_miflu_predictions.py \
  --seeds 42 43 44 \
  --csv-pattern "author_runs/L{L}_s{S}/predictions_miflu_L{L}_s{S}_paper_protocol.csv"
```

which writes one `hpc_results/expanded_runs/miflu_L{L}_s{S}/pred_miflu_L{L}_s{S}.npz`
cell per (L, seed) — 12 cells total — stamped `partial=True` because the export
carries ILITOTAL (channel 4) only. `analysis_expanded.py` then averages the three
seeds exactly as it does for the other 16 arms.

---

## 3. Training-budget parity

| item | 16 benchmark arms | MIFlu benchmark cells |
|---|---|---|
| runtime seed | `set_seed(seed + L)` | `set_seed(seed + L)` (same function, same call site) |
| epochs | 20 | 20 |
| batch | 16 | 16 |
| learning rate | 1e-4 | 1e-4 (author's code default) |
| checkpoint selection | best validation epoch, per seed | best validation epoch, per seed |
| seeds | 42/43/44 | 42/43/44 |

Differences that remain and must be disclosed: MIFlu's `--reps 1` invocation
means each (L, seed) is a separate process rather than a loop, which does not
change the RNG stream (`train_L` re-seeds at entry); and MIFlu's LoRA adapters +
text branch are part of its architecture, not a budget choice.
