# REPRODUCIBILITY.md

**MIFlu reproduction & multimodal time-series forecasting — complete reproduction guide.**

This document tells a reviewer exactly how to rebuild our environment, obtain the
data, and regenerate every number and figure in the submission. Every command
below is copy-paste runnable.

---

## 0. The three non-negotiable constraints (and where they are enforced)

| Constraint | Value | Enforced by |
|---|---|---|
| **Dual-track metrics** | Table V/VIII use **z-space** MSE/MAE; figures & supplementary use **physical units** (patient counts) via inverse transform | `scripts/scaler_utils.py` (`ScalerBundle.inverse`), `train_ablation.py::evaluate` (returns both tracks) |
| **Full 1025-row window** | 2002–2021, `train_end=717`, `val_end=819` (717 train + 102 val + 206 test) | `scripts/configs.py::assert_full_window` + `derive_split` — **both raise**, they do not warn |
| **Priority subset** | Only `full`, `no_lora`, `no_text_ln`, `gated_inject` | `configs.CORE_VARIANTS`; the four `hpc_scripts/submit_*.sh` |

If the CSV is not exactly 1025 rows, the run **crashes** rather than silently
producing a 966-row (COVID-trimmed) result. That is deliberate: the 2020–2021
distribution shift is the paper's core evidence.

---

## 1. Environment setup

### 1.1 Software versions

| Component | Version |
|---|---|
| Python | **3.9.25** |
| PyTorch | **2.5.1 (CUDA 11.8 build)** |
| Transformers | GPT2-small weights via `transformers` (see §1.3) |
| numpy / pandas | present in `mlflu_hpc` |
| matplotlib / scipy / scikit-learn | matplotlib, scipy, **scikit-learn 1.6.1** |
| Other verified deps | `sentencepiece`, `protobuf 6.33.6`, `datasets 4.5.0`, `accelerate`, `huggingface-hub`, `gdown 5.2.2` |

Conda environment name: **`mlflu_hpc`**.

### 1.2 HPC (Burgundy) — activation

> Activate by **PATH-prepend, not `conda activate`** (`conda activate` fails on
> the GPU nodes).

```bash
module unload default && module load old_modules          # MUST run first on any node
export PATH="/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH"
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
```

Optional deps (only needed by `similarity_screen.py`, not by the journal runs):

```bash
pip install --no-deps statsmodels
pip install --no-deps patsy
```

### 1.3 Model weights

GPT2-small (`gpt2`) is downloaded on first use into `HF_HOME` and cached
afterwards. **No manual download is required.** The `ModalityAligner`
(`gated_inject` variant) adds no new pretrained weights — it is trained from
scratch.

### 1.4 Local (CPU) sanity check — no GPU required

```bash
python scripts/configs.py        # verifies 1025 -> 717/819 and all invariants
python scripts/scaler_utils.py   # leakage proof + z-space vs physical ranges
```

Expected output:

```
[configs] self-check OK
  window: FULL_ROWS=1025 train_end=717 val_end=819
  national: T=104 N=7 Lp=24 S=2 K=6 D=768
  core variants: full, no_lora, no_text_ln, gated_inject

[scaler_utils] self-check OK
  train_end=717 val_end=819
  ILITOTAL train mean=9368.3 std=8853.4
  ILITOTAL z-range: [-1.022, 11.809]  <- the 0..12 axis the advisor saw
  ILITOTAL physical range: [318, 113921] patients
```

---

## 2. Data preparation

The dataset is the **CDC National Illness (ILINet) + influenza-like illness**
set used by MIFlu §V-A: 7 channels, weekly, **1025 rows covering 2002 w01 →
2021 w52**.

Place it at:

```
data/raw/national_illness_raw.csv
```

Expected columns (order matters — it defines the channel indices):

```
% WEIGHTED ILI, % UNWEIGHTED ILI, AGE 0-4, AGE 5-24,
ILITOTAL, NUM. OF PROVIDERS, OT
```

`ILITOTAL` is channel index **4** — this is the channel all headline ILI
metrics are computed on.

If you need to (re)download it:

```bash
python scripts/download_national_illness.py
python scripts/verify_dataset.py     # sanity-checks shape/columns
```

> **Do not truncate.** Any preprocessing that drops the 2020–2021 tail
> (yielding 966 rows) will make `configs.assert_full_window` raise.

---

## 3. Reproducing Table VIII — the 4 core ablation variants

Each variant runs **10 repetitions** at horizon **L=24** with **20 epochs**,
batch size **16**, base seed **42** (repetition *r* uses seed `42 + r - 1`).

### 3.1 Direct CLI (single variant)

```bash
python scripts/train_ablation.py --variant full          --horizon 24 --reps 10 --epochs 20 --batch 16 --seed 42 \
    --export-dir hpc_results/journal_evidence/full/reps_1_to_10

python scripts/train_ablation.py --variant no_lora       --horizon 24 --reps 10 --epochs 20 --batch 16 --seed 42 \
    --export-dir hpc_results/journal_evidence/no_lora/reps_1_to_10

python scripts/train_ablation.py --variant no_text_ln    --horizon 24 --reps 10 --epochs 20 --batch 16 --seed 42 \
    --export-dir hpc_results/journal_evidence/no_text_ln/reps_1_to_10

python scripts/train_ablation.py --variant gated_inject  --horizon 24 --reps 10 --epochs 20 --batch 16 --seed 42 \
    --export-dir hpc_results/journal_evidence/gated_inject/reps_1_to_10
```

### 3.2 HPC (recommended — 4×A100 in parallel, ~40 min wall clock)

Submit **from the project root** so that logs land in
`hpc_results/journal_evidence/logs/job<id>_<variant>.out`:

```bash
sbatch hpc_scripts/submit_full.sh
sbatch hpc_scripts/submit_no_lora.sh
sbatch hpc_scripts/submit_no_text_ln.sh
sbatch hpc_scripts/submit_gated_inject.sh
```

Each script requests `--partition=gpu_a100 --gres=gpu:a100:1 --time=04:00:00`.
QOS permits 4 concurrent jobs per user, so all four run simultaneously.

### 3.3 Verification gate — PARAM AUDIT

Within ~2 minutes of each job starting, its log must contain a `[PARAM AUDIT]`
line. These are the **expected** values; a mismatch means the variants have
contaminated each other:

| Variant | Total Trainable | LoRA Tensors | LoRA Params | Notes |
|---|---|---|---|---|
| `full` | **≈1,030,056** | 12 | > 0 | Baseline; must NOT be ≈17M |
| `no_lora` | **≈956,328** | **0** | **0** | Zero LoRA modules, not merely frozen |
| `no_text_ln` | **1,028,520** | 12 | > 0 | `text_ln` → Identity (−1,536) |
| `gated_inject` | **17,537,449** | 8 | > 0 | 2 layers fully unfrozen + `ModalityAligner` |

```bash
grep -h "PARAM AUDIT" hpc_results/journal_evidence/logs/job*_*.out
```

> The `LoRA Tensors` / `LoRA Params` columns are the decisive check. An earlier
> revision created the LoRA tensors for `no_lora` and merely *froze* them, so
> the trainable total alone could not distinguish "no LoRA" from "frozen LoRA".

### 3.4 Building the table

```bash
python scripts/aggregate_journal_tables.py --root hpc_results/journal_evidence
```

Writes `journal_table_viii.csv/.md` (z-space, primary) and
`journal_table_physical.csv/.md` (patient counts, supplementary).

**Purity rules the aggregator enforces automatically:**

- reps with non-finite or `discarded` metrics are dropped;
- a variant with **fewer than 10 valid reps** is labelled `[INCOMPLETE]` and
  **excluded entirely** (partial runs must not skew mean/std);
- each `rep_N/` must contain the full artifact set
  (`metrics.csv` + prediction CSV + `checkpoints/best_model.pt`), or the
  variant is excluded.

---

## 4. Reproducing Table V (main MIFlu, multi-horizon)

Table V trains each horizon **independently** (L=24/36/48/60 — *not* a single
rolling L=52 walk-forward):

```bash
python scripts/train_miflu.py --horizon 24 --reps 10 --epochs 20 --batch 16 --seed 42
python scripts/train_miflu.py --horizon 36 --reps 10 --epochs 20 --batch 16 --seed 42
python scripts/train_miflu.py --horizon 48 --reps 10 --epochs 20 --batch 16 --seed 42
python scripts/train_miflu.py --horizon 60 --reps 10 --epochs 20 --batch 16 --seed 42
```

Or via the HPC array/paper-protocol script:

```bash
sbatch hpc_scripts/submit_miflu_paper_protocol.sh
```

The unimodal GPT4TS baseline (Table V / "w/o multimodality"):

```bash
python scripts/train_baseline.py
```

---

## 5. Reproducing the figures (physical units + real CDC calendar)

```bash
python scripts/make_miflu_evaluation_figure.py \
    --pred_csv hpc_results/journal_evidence/full/reps_1_to_10/predictions_miflu_L24_paper_protocol.csv \
    --L 24 \
    --lead_mode fixed_step --lead_step 0 \
    --fig_dir hpc_results/journal_evidence/figures
```

- `--lead_mode fixed_step --lead_step 0` keeps the **1-week-ahead** column of
  every window, so the plotted curve has a **constant lead time** instead of
  mixing forecast steps 1…L. See `compute_miflu_indicators.py::aggregate_lead_time`.
- The figure uses the **real CDC epiweek calendar** (`scripts/cdc_calendar.py`),
  which corrects the ~19-week X-axis drift of the naive "row index + start date"
  approach and handles the 2002 19-week gap.
- Y-axis is **physical units (patient counts)** via the persisted scaler
  (`data/scaler_miflu_national.json`) — this is the dual-track "figures" branch.

Indicators (PTE = peak timing error, PIE = peak intensity error; peak hit rate and
directional accuracy were removed in 2026-09):

```bash
python scripts/compute_miflu_indicators.py \
    --pred_csv hpc_results/journal_evidence/full/reps_1_to_10/predictions_miflu_L24_paper_protocol.csv \
    --L 24 --lead_mode fixed_step
```

---

## 6. Determinism

`set_seed()` in `scripts/configs.py` is called at the **start of every training
script** and seeds `random`, `numpy`, `torch`, `torch.cuda`, plus
`cudnn.deterministic = True` / `cudnn.benchmark = False`.

> **Trade-off:** `cudnn.deterministic=True` disables non-deterministic
> convolution algorithms and costs roughly **10–20% throughput**. This is
> deliberate — bit-reproducibility is worth more than speed for a journal
> artefact.

Per-repetition seeding uses `seed + L` with the base seed 42, preserving the
original scheme.

---

## 7. Artifact tree

```
hpc_results/journal_evidence/
├── {variant}/                      # full | no_lora | no_text_ln | gated_inject
│   └── reps_1_to_10/
│       ├── metrics.csv             # ONE ROW PER REP (summary; feeds the table)
│       ├── predictions_miflu_L24_paper_protocol.csv   # best-rep, for figures
│       └── rep_NN/
│           ├── metrics.csv                            # epoch-by-epoch trace
│           ├── predictions_miflu_L24_paper_protocol.csv  # dual-track
│           ├── checkpoint_meta.json                   # provenance
│           └── checkpoints/best_model.pt
├── figures/
│   ├── fig_miflu_eval_continuous_L24.png
│   └── fig_attention_heatmap.png
└── logs/
    └── job<id>_<variant>.out
```

Two files are named `metrics.csv` at different levels, deliberately:
`reps_1_to_10/metrics.csv` is the **per-rep summary** (10 rows) consumed by the
aggregator; `rep_NN/metrics.csv` is that repetition's **epoch-by-epoch trace**.

`checkpoint_meta.json` records whether `best_model.pt` came from
`PeakAwareEarlyStopping` or is simply the **final epoch** (the default
fixed-20-epoch protocol), so the checkpoint's meaning is never ambiguous.

---

## 8. Command cheat-sheet

| Goal | Command |
|---|---|
| Verify invariants | `python scripts/configs.py` |
| Scaler leakage proof | `python scripts/scaler_utils.py` |
| One ablation variant | `python scripts/train_ablation.py --variant <v> --horizon 24 --reps 10 --epochs 20 --batch 16 --seed 42` |
| All 4 variants (HPC) | `sbatch hpc_scripts/submit_{full,no_lora,no_text_ln,gated_inject}.sh` |
| Build Table VIII | `python scripts/aggregate_journal_tables.py --root hpc_results/journal_evidence` |
| Figures (physical) | `python scripts/make_miflu_evaluation_figure.py --pred_csv <csv> --L 24 --lead_mode fixed_step --lead_step 0 --fig_dir hpc_results/journal_evidence/figures` |
| Check audit gate | `grep -h "PARAM AUDIT" hpc_results/journal_evidence/logs/job*_*.out` |
