# A2 TEXT-ACTIVE MAGNITUDE AUDIT

Generated 2026-10-06. Append-only. **No retraining, no GPU job.**

## Classification

Two questions were separated, as required.

| Question | Answer |
|---|---|
| **1. Does text content influence the A2 prediction?** | **YES** — confirmed under both the flawed and the corrected probe |
| **2. Is the magnitude numerically stable and scientifically interpretable?** | **The previously reported magnitude was NOT.** The corrected magnitude is interpretable |

**Overall: `TEXT_ACTIVE_BUT_MAGNITUDE_REQUIRES_CAUTION`** — with the specific finding
that the *originally reported* figures (59.7 and 7.13e+08) were a **probe defect**,
not a property of the model.

---

## 1. Root cause: the v1 probe fed out-of-distribution input

`miflu_model.MIFlu.forward` documents its first argument as:

> `x: time-series input (batch, N, T)` — **ALREADY in StandardScaler space**

The v1 probe (`probe_a2_text_path.py`) built `x` from the **raw** CSV columns, so the
model received `OT ≈ 176 569` and `ILITOTAL ≈ 2 000` where it was trained on values
in roughly `[-1, +4]`. That is 3–5 orders of magnitude out of distribution.

The forward pass ends with reversible instance normalisation:

```python
y_hat_rev = y_hat_norm * stdevs + means     # stdevs/means come from the INPUT's instance norm
```

so the output scale is driven by the input scale. Feeding raw data therefore
**scaled the whole output — and every difference measured on it — by the same
enormous factor**, and put the network in a regime where its activations (and hence
the text gradient) explode.

### The fix

`probe_a2_text_path_v2.py` applies the project's own persisted train-only scaler
first:

```
data/scaler_miflu_author966.json   mean/std, train_end=676, var_cols = the 7 columns
Xz = (X - mean) / std
```

Nothing else changed: same checkpoint, same eval mode, same variants, same
equal-length control.

---

## 2. Measured result — v1 vs v2

| Quantity | **v1 (raw input — defective)** | **v2 (StandardScaler input — correct)** | Factor |
|---|---:|---:|---:|
| input range | ≈ 0 … 1.8e5 (raw) | **[-0.816, +3.827]** (z) | — |
| prediction range | scale-driven by raw input | **[-0.828, +1.717]**, mean abs 0.732 | — |
| `max\|Δpred\|`, different prompt, same length | 5.968750e+01 | **6.518e-04** | **≈ 9.2e4×** |
| `max\|Δpred\|`, row-permuted (same multiset) | 6.308312e+03 | **6.525e-02** | **≈ 9.7e4×** |
| mean `\|Δpred\|`, different prompt | 3.619 | **1.925e-04** | ≈ 1.9e4× |
| `\|grad_text\|` | 7.130076e+08 | **0.025178** | ≈ 2.8e10× |
| `max\|grad_text\|` | 8.736e+07 | **3.387e-03** | ≈ 2.6e10× |
| verdict | `text_active` | **`text_active`** | unchanged |

**The verdict is unchanged; the magnitude is not.** This is the important
distinction: the qualitative claim survived the correction, the quantitative claim
did not.

---

## 3. Is the corrected magnitude interpretable?

Yes.

| Reading | Value | Interpretation |
|---|---|---|
| typical prediction magnitude | mean abs ≈ **0.73** (z-space) | sane |
| a *different real prompt* of the same length | max 6.5e-04, mean 1.9e-04 | ≈ **0.09 %** of the signal — small but non-zero |
| *row-permuting* the same tokens | max 6.5e-02, mean 2.2e-02 | ≈ **9 %** — an order of magnitude larger |

That ordering is exactly what one should expect: permuting the token order destroys
the sequence structure the transformer reads, while swapping in a different
well-formed prompt changes the content only. So the corrected numbers behave like a
real, modest text effect rather than like an instability.

---

## 4. Checklist from the brief

| Item | Finding |
|---|---|
| model checkpoint identity | `hpc_results/checkpoints/best_miflu_L24.pth`; 106 tensors loaded, 0 unexpected |
| the 12 "missing" keys | `forecasting_llm.blocks.{0..5}.attn.{bias,masked_bias}` — GPT-2 **causal-mask buffers**, deterministic constants, not trained values → the real trained weights were used |
| model-weight equality | single load for both probes; identical file |
| prediction scale | v1 meaningless (raw-input driven); v2 [-0.83, 1.72] |
| standardized vs inverse-transformed | v2 measures the **StandardScaler-space** output (`y_hat_rev`), which the model documents as the canonical metric space |
| target range | z-space, consistent with the prediction range |
| `model.eval()` status | **True**, recorded |
| dropout state | **all modules `training=False`**, recorded |
| autocast state | not used (no `torch.cuda.amp` anywhere in the probe) |
| dtype | float32 throughout |
| loss function / reduction | `loss = (y ** 2).mean()` — **mean**, not sum; consistent across v1 and v2, so it does not explain the difference |
| batch size | 1 in both |
| sequence length | 369 tokens + 294 patches, identical in v1 and v2 |
| gradient accumulation | none |
| `zero_grad` called | not applicable — a single forward/backward on a fresh graph; `E` is a fresh leaf in each run |
| gradients normalized | no |
| loss summed rather than averaged | no — `.mean()` |
| replacement text length | **identical** (1552 chars → (1,369,768)); the probe aborts otherwise |
| replacement text distribution | (a) a different real prompt for another horizon; (b) a row permutation of the original — same multiset |
| attention-mask preservation | no mask is used; unchanged between variants |
| text-embedding normalization | the model's own `text_ln` is applied inside `forward`, identically in all variants |
| activation ranges | the v1 run was out of distribution; v2 is in range |
| exploding activation possibility | **yes, in v1** — the cause |
| exploding gradient possibility | **yes, in v1** — consequence of the same cause |
| inverse-scaling amplification | yes — RevIN multiplies by the input's instance std, which is what magnified v1 |
| anything besides text content changed | in v2, **no**: same weights, same input tensor, same shape, same eval mode |

---

## 5. Consequence for the earlier reports

The figures **59.7** and **7.13e+08** appear in `../TEXT_PATH_RESOLUTION.md` §6 and in
`../REPORT_ZH.md` / `../REPORT_EN.md` §E.2. Those files are **not modified** (append-only
rule). A correction addendum records the superseded values:

→ `STATUS_CORRECTION_ADDENDUM.md`

**Superseded**: `max|Δpred| = 59.6875`, `|grad_text| = 7.13e+08`
**Corrected**: `max|Δpred| = 6.518e-04` (different prompt) / `6.525e-02` (row permutation),
`|grad_text| = 0.0252`

The *conclusion* those sections drew — that A2's text path is functional while the
released code's is not — **stands**.

## 6. Artifacts

| File | Content |
|---|---|
| `../probe_a2_text_path.py` | v1 probe (raw input; kept unmodified as the record of the defect) |
| `../probe_a2_text_path_v2.py` | v2 probe (corrected input space) |
| `../a2_text_path_probe.json` | v1 output |
| `../a2_text_path_probe_v2.json` | v2 output |
| `A2_TEXT_PROBE_PROVENANCE.csv` | field-by-field comparison |