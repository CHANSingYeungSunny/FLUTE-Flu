# F1 TARGET CONTRACT

Generated 2026-10-06. The contract is **chosen explicitly**, not inherited silently
from the released code and not presented as recovered Table V behaviour.

---

## 1. Why a choice is required

The paper-contract audit (`../postrun_audit_20261006/PAPER_EVALUATION_CONTRACT_AUDIT.md`)
established three facts that make silence impossible:

| Fact | Evidence | Status |
|---|---|---|
| the released code evaluates **one channel only** | `data_loader.py:305` slices `feat_id:feat_id+1`; `__len__` omits `× enc_in` for Test (L312-317) | `CODE_EXPLICIT` |
| the released code builds **univariate windows in every split** | the same slice applies to train/val/Test | `CODE_EXPLICIT`, re-verified this round |
| the paper's **pooling axis is undisclosed** | Q12 | `UNRECOVERED` |

So "do what the released code does" and "do what the paper did" are **different
instructions**, and the second one is not fully knowable. F1 therefore declares a
contract and states its justification.

---

## 2. The selected F1 target contract

> **F1 evaluates all seven channels jointly, on the same seven forecast keys for every
> model, in StandardScaler space, with metrics pooled over
> (origins × leads × 7 variables), and a four-horizon equal-weight average.**

Formally, for model `m`, horizon `L`:

```
mse_all(m, L)  =  mean over ( origin o ) × ( lead 1..L ) × ( 7 channels ) of (y - yhat)^2
average_MSE_4L =  mean over L in {24,36,48,60} of mse_all(m, L)
```

### The seven channels (keys taken from the project's own `scripts/configs.py`)

| # | key | role |
|---:|---|---|
| 1 | `% WEIGHTED ILI` | population-weighted ILI share |
| 2 | `% UNWEIGHTED ILI` | unweighted ILI share |
| 3 | `AGE 0-4` | ILI count, ages 0–4 |
| 4 | `AGE 5-24` | ILI count, ages 5–24 |
| 5 | `ILITOTAL` | total ILI count |
| 6 | `NUM. OF PROVIDERS` | reporting-provider count |
| 7 | `OT` | total patient visits (the ILI-percentage denominator) |

---

## 3. The five questions the brief requires

### 3.1 What is the selected contract?

All-seven-channel, equal-weight-over-channels, StandardScaler space, strict containment,
validation-selected checkpoints, one seed, metrics recomputed by an independent scorer.

### 3.2 Why is it the fairest contract for the project objective?

The objective is *"determine the best-performing model under one fair and consistent
evaluation contract."* Fairness here means **every model is scored on exactly the same
quantity**. Three options existed:

| Option | Verdict |
|---|---|
| **A. one channel (`% WEIGHTED ILI`), as the released code does** | ❌ rejected — it would discard six declared variables, and a single-channel score cannot distinguish a multivariate model from a univariate one. It would also make the comparison depend on an implementation defect. |
| **B. `ILITOTAL` only** | ❌ rejected — single-target, and the project's primary estimand has been the seven-variable aggregate throughout. |
| **C. all seven channels** | ✅ **selected** — it matches the paper's declared task scope (national ILI "plus several sub-indicator variables"), it is the contract the project's own A2 basis already used, and it treats every model identically. |

**Decisive point**: option C is the only choice under which the six models are being
asked the same question. Options A and B answer a different question for different
models depending on their implementation quirks.

### 3.3 Does it predict one target or multiple variables?

**Multiple: all seven jointly.** Each model emits `(N=7, L)` per origin.

### 3.4 Do all six models use the exact same target keys?

**Yes — and this is enforced, not assumed.** `f1_score_all.py` calls
`scorer_f1.cross_check_keys()` against the declared list in §2, and gate **G4** fails
if any model's `var_cols` differ. The check was validated on real artefacts this round:
after correcting a wrong alias list of my own, all eight naive artefacts passed with
`forecast-key violations: 0`.

### 3.5 Why must this NOT be described as recovered Table V behaviour?

Because **Q12 is `UNRECOVERED`**. The paper does not state how it pooled origins, leads,
variables, horizons or seeds, and it never states which variable(s) the Table V scalar
covers. Therefore:

- the paper's aggregation axis is **unknown**, so matching it is not something F1 can
  claim to have done;
- the released code's axis is a **single channel**, so matching *it* is a different thing
  again;
- additionally, the paper states its **baseline** columns are quoted from [9]/[14]
  (`paper_text.txt` L582-583), so even the comparison structure is not a re-run.

**Mandatory wording**:

> F1 is a **corrected fair comparison** under a **declared** contract. It is **not** a
> reproduction of Table V, and it makes **no** claim about the paper's own pooling.

**Prohibited wording**: "F1 reproduces Table V", "F1 uses the paper's metric",
"F1 matches the paper's aggregation".

---

## 4. Known departures from the released code — declared, not hidden

| Item | Released code | F1 | Why |
|---|---|---|---|
| evaluated channels | 1 (`% WEIGHTED ILI`) | **7** | §3.2 |
| window shape | univariate `(T,1)` | **multivariate `(T,7)`** | the paper's task is multivariate |
| checkpoint selection | Test MSE | **validation MSE** | Test selection is leakage |
| Test evaluation | every epoch | **once, after freezing** | S12 |
| predictions saved | no (`np.save` commented) | **yes (NPZ)** | independent scoring |
| seasonal naive at L>52 | reads target rows (verified, 8 leads) | **repeats the last cycle** | leakage |
| hyperparameters | 1 epoch / 1e-4 default | **20 epochs / 5e-4** | declared `RECONSTRUCTED_ASSUMPTION` |

Every row is a **declared deviation** from the released implementation. F1 is a corrected
benchmark, and calling it anything else would be false.