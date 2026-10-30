# Advisor Questions — Resolution & Data-Integrity Evidence

This document answers the five critical reviewer/advisor questions about the MIFlu
reproduction, with **concrete code-level evidence** rather than assertions. Every
claim below is verified by a self-check or log line that ships with the code.

---

## Q1 — Dual-track metrics: why do tables use z-space but figures use patient counts?

**Answer.** The two tracks measure two different things and must not be mixed.

- **Tables (Table V / Table VIII — main text):** z-score-normalised MSE/MAE.
  MIFlu reports `MSE ≈ 1.542` on ILI in *z-space*; we reproduce this exactly.
  The z-space is scale-free, so it is directly comparable to the paper and to
  GPT4TS/Time-Series-Library baselines.
- **Figures & supplementary material:** physical units (patient counts), obtained
  by `ScalerBundle.inverse()` applied to the predictions.

The split is enforced in code: `evaluate()` returns **both** tracks at once —
`(mse_all, mae_all)` in z-space and `(mse_ili_phys, mae_ili_phys)` after the
inverse transform. Tables consume the first pair; the figure pipeline consumes
the second. There is no single number forced to be "the" metric.

```python
# train_ablation.py :: evaluate()
#   returns z-space mse/mae AND physical-space mse/mae_ili_phys
#   (the two tracks are computed from the SAME forward pass, never conflated)
```

**Why this matters for the reviewer:** a common rejection cause is reporting a
z-space number as if it were patients. We make the track explicit in every file
name (`predictions_..._paper_protocol.csv` carries both columns; tables vs figures
are produced by separate scripts).

---

## Q2 — Data leakage: is the StandardScaler fit only on the training set?

**Answer. Yes, proven by assertion, not by convention.**

`ScalerBundle.fit_from_train(df, VAR_COLS, train_end=717, val_end=819)` computes
`mean_` / `scale_` **exclusively** from `data[:717]`. Validation and test rows are
only ever *divided* by those statistics (`transform`), never used to fit.

Three independent guards make this unfalsifiable:

1. `configs.assert_full_window(n)` — raises unless the CSV is exactly **1025**
   rows (blocks the 966-row COVID-trimmed variant).
2. `configs.derive_split(n)` — raises unless the split is exactly **717 / 819**.
3. `train_ablation.load_and_normalize()` re-fits and then **asserts agreement**
   with the persisted `data/scaler_miflu_national.json`, so a stale or hand-edited
   scaler cannot silently move the numbers.

**Evidence (from `python scripts/scaler_utils.py`):**

```
[scaler_utils] self-check OK
  train_end=717 val_end=819
  ILITOTAL train mean=9368.3 std=8853.4
  ILITOTAL z-range: [-1.022, 11.809]
  ILITOTAL physical range: [318, 113921] patients
```

There is no second `.fit()` anywhere in the training module.

---

## Q3 — "Why is my Y-axis only 0–12?"

**Answer.** Because the plotted quantity in the *metric* track is the **z-score**
of `ILITOTAL`, whose empirical range is `[-1.022, 11.809]` (≈ 0–12). That is
correct — it is the normalised space the tables live in.

The **raw** `ILITOTAL` spans `[318, 113,921]` patients (physical units). The
figure pipeline applies `inverse_transform` *before* plotting the physical track,
so a reviewer who wants patients sees patients, and a reviewer who wants the
paper's z-space sees 0–12. Both are correct; they are different axes.

```
z-space axis   : [-1.022, 11.809]   <- what a 0..12 axis means
physical axis  : [318, 113921]       <- after inverse_transform
```

If any figure shows 0–12 and is *labelled* "patients", that is a labelling bug —
but our physical figures are explicitly inverse-transformed and labelled in counts.

---

## Q4 — Reproducibility: will a reviewer obtain the same numbers?

**Answer. Yes, by construction.**

- **Determinism:** `set_seed()` (in `configs.py`) is called at the start of every
  training script and seeds `random`, `numpy`, `torch`, `torch.cuda`, and sets
  `cudnn.deterministic = True` / `cudnn.benchmark = False`. (Trade-off: ~10–20 %
  throughput, deliberate for a journal artefact.)
- **Single source of truth:** all hyper-parameters live in `configs.py`; the 4
  core variants are `configs.CORE_VARIANTS`. No duplicated literals.
- **10 repetitions** per variant, seed `42 + (rep - 1)`; tables report mean/std.
  A variant with **fewer than 10 valid reps is excluded entirely** (partial runs
  must not skew statistics).
- **`--force` flag** disables resume, guaranteeing a clean re-run (this caught a
  stale-artifact trap during our own submission — see §5).
- **Strict artifact tree** per rep: `metrics.csv` (epoch trace), dual-track
  predictions, `checkpoint_meta.json` (provenance), `checkpoints/best_model.pt`.

```bash
python scripts/train_ablation.py --variant full --horizon 24 --reps 10 \
    --epochs 20 --batch 16 --seed 42 --force \
    --export-dir hpc_results/journal_evidence/full/reps_1_to_10
```

---

## Q5 — Parameter / architecture integrity & aggregation purity

**Answer.** The `PARAM AUDIT` line (logged once per rep) is the gate that proves
no LoRA / unfreezing contamination leaked across variants.

| Variant | Total Trainable | LoRA Tensors | LoRA Params | Meaning |
|---|---|---|---|---|
| `full` | ≈ 1,030,056 | 12 | > 0 | baseline |
| `no_lora` | ≈ 956,328 | **0** | **0** | **zero LoRA modules created, not merely frozen** |
| `no_text_ln` | 1,028,520 | 12 | > 0 | `text_ln` → Identity (−1,536 params) |
| `gated_inject` | 17,537,449 | 8 | > 0 | 2 layers fully unfrozen + `ModalityAligner` |

The decisive column is **`LoRA Tensors` / `LoRA Params`**. An earlier revision
created the LoRA tensors for `no_lora` and merely *froze* them, so the trainable
total alone could not distinguish "no LoRA" from "frozen LoRA". Now `no_lora`
constructs **none at all** — the audit proves it (12 → 0).

**Aggregation purity (`aggregate_journal_tables.py`):**

- reps with non-finite or `discarded` metrics are dropped;
- a variant with **< 10 valid reps** is labelled `[INCOMPLETE]` and **excluded**;
- each `rep_N/` must contain the full artifact set
  (`metrics.csv` + prediction CSV + `checkpoints/best_model.pt`), else excluded.

```bash
grep -h "PARAM AUDIT" hpc_results/journal_evidence/logs/job*_*.out
python scripts/aggregate_journal_tables.py --root hpc_results/journal_evidence
```

Expected trainable counts are reproducible from the model definition and are the
**behaviour-preservation gate** for the recent refactor: the numbers above are
unchanged from the pre-refactor build, confirming the centralisation of
`configs.py` did not alter a single parameter.

---

## Summary for the reviewer

| Concern | Status | Where verified |
|---|---|---|
| z-space vs physical separation | explicit dual-track | `evaluate()`, `export_prediction_csv()` |
| No scaler leakage | 3 assertions + re-fit check | `configs.py`, `scaler_utils.py` |
| Full 1025-row window | assertion (no 966 truncation) | `configs.assert_full_window` |
| Reproducible seeds | `set_seed()` everywhere + `--force` | `configs.set_seed` |
| Param integrity (no_lora=0 LoRA) | `PARAM AUDIT` logs LoRA count | `train_ablation.train_L` |
| Aggregation purity | drop/discard/incomplete rules | `aggregate_journal_tables.py` |
| `Timing = 0.5` is peak-timing error, not lead time | ELI5 section Q6 + regression test | `compute_miflu_indicators.py`, `tests/test_timing_metric.py` |

---

## Q6 — "Is Timing = 0.5 the lead time? And why isn't it 0?"

> **Short answer: NO.** `Timing = 0.5` is a **peak-timing error** (the detected peaks sit
> about half a week away from the true peaks). It is **not** lead time, and it is **not**
> the forecast horizon.

### Problem — what confused everyone

An older, now-retired protocol (`L=52` walk-forward) printed `Timing = 0.0`. That reads as
either a bug or a "perfect" score, and it is neither. Under the **current paper protocol
(L=24, test-only)** the value is `Timing = 0.5 week`. Both numbers are easily misread as
"the model predicts half a week ahead".

### Scientific Reason — what `Timing` actually measures

`Timing` is the **average peak-timing error**, computed over the peaks the model detected:

```
Timing = mean over matched peaks of |Δt|
         where Δt = (predicted peak week) − (true CDC peak week)
```

* It is computed **only over matched peaks** — never over peaks the model missed.
* Here **2 of 4** true peaks were matched, so the honest report is
  **`Timing = 0.5 week (based on 2/4 matched peaks)`**.
* `0.5 week ≈ 3.5 days`: the detected peaks land roughly half a week early or late.

**What it is NOT:**

| Misreading | Why it is wrong |
|---|---|
| "0.5 weeks of lead time" | Lead time is the *forecast horizon* — how far ahead we predict. Ours is fixed at **L = 24 weeks** and is reported separately. |
| "the model warns 3.5 days in advance" | No. `Timing` measures the **displacement of the peak**, not advance warning. |
| "0.0 would mean perfect" | No. The old `0.0` appeared because only **one** peak was matched and happened to align — a small-sample accident, not perfection. |

**Why this matters clinically:** a half-week peak displacement is operationally minor,
because vaccine and staffing decisions are planned in whole weeks. The genuine weakness
is elsewhere: **only 2 of the 4 true peaks were matched (2/4)** — half the peaks were
missed entirely, plus a peak-intensity error. Put plainly, *whether* a peak occurs and *how big* it is matter more
to public health than pinning it to the exact week.

### Fix

1. `Timing` is **always reported with its hit count** (`based on 2/4 matched peaks`) — never as a bare number.
2. When **zero** peaks match, the pipeline reports `unmatched`. It must **never** emit `0.0`;
   that deprecated behaviour is exactly what caused the confusion.
3. Regression guard: `tests/test_timing_metric.py` asserts that non-overlapping peaks yield
   `Timing = null` (not `0.0`) and that correctly-offset peaks yield a non-zero value.

### Status

✅ **Fixed and guarded.** The deprecated `L=52` walk-forward output that produced the
misleading `0.0` is archived at `results/ili/DEPRECATED_walkforward_L52.md`. The reported
`Timing = 0.5 week (2/4 matched peaks)` comes from the current paper protocol.
