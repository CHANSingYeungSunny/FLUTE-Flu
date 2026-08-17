# Supplementary: StandardScaler Fit Convention — Train-Only vs Pooled

**Context.** MIFlu paper (MIFlu_paper.md, Section V-B) states National ILI forecasting
metrics are computed on StandardScaler-normalized data, but does **not** specify
whether the scaler is fit on the **train split only** or on the **whole series
(train+val+test)**. Our pipeline (`scripts/train_miflu.py::load_and_normalize`) fits
StandardScaler on the **train split only** (leakage-audit compliant, see
`docs/leakage_audit_report.md`).

**Primary numbers (train-only fit, leakage-safe — USE THESE EVERYWHERE):**
L=24 National ILITOTAL (10-rep mean, StandardScaler train-only space):
- MSE = 5.056 ± 1.583
- MAE = 1.500 ± 0.121

**Supplementary comparison (pooled-fit rescaling — DO NOT use as primary):**

The same predictions, linearly rescaled from the train-only StandardScaler space to
a hypothetical pooled (whole-series) StandardScaler space, give:
- MSE ≈ 1.61  (×0.318 vs train-only)
- MAE ≈ 0.85  (×0.564 vs train-only)

For reference, the paper reports L=24 National: MSE = 1.542, MAE = 0.726.

| Space | MSE | MAE | vs paper MSE | vs paper MAE |
|---|---|---|---|---|
| Train-only (primary) | 5.056 | 1.500 | 3.28× | 2.07× |
| Pooled-rescaled (supp) | ~1.61 | ~0.85 | ~1.04× | ~1.17× |
| Paper (Table V) | 1.542 | 0.726 | — | — |

**CAVEAT (exact scope — do not overstate):**
- This pooled column is **diagnostic rescaling only**. It applies the linear
  StandardScaler mapping (affine) between the two normalization conventions to the
  already-trained predictions; it does **NOT** re-train or re-evaluate the model.
- MSE lands within **~4%** of the paper value; MAE is **off by ~17%**.
  IMPORTANT (math correction): StandardScaler is a *linear* transform, so the same
  rescaling factor applies to **every** error point uniformly — it does NOT
  "contract large errors more than small ones." Concretely, if the train-only std is
  σ_t and the pooled std is σ_p, then for any error e: e' = e·(σ_t/σ_p), so
  MSE' = MSE·(σ_t/σ_p)² and MAE' = MAE·(σ_t/σ_p). All errors shrink by the same
  ratio; there is no non-linear compression. The MAE residual (17%) is simply a
  consequence of the uniform linear mapping, not evidence of "large errors being
  contracted more."
- The pooled-fit convention is **NOT confirmed as the root cause** of the gap. The
  paper does not state its fit range. It is **not used for training or evaluation**
  of our model — only shown as a possible explanation of the absolute-number
  difference.
- The CDC-vintage question (below) is **NOT fully closed** — see the corrected
  conclusion below; 2002–2021 retrospective revisions remain an unexcluded candidate.

**Bottom line:** Report train-only-fit MSE/MAE as the primary result. The pooled-rescaled
numbers are a **supplementary note only** with the caveat above. Status (2026-08-18, corrected):
- **MSE gap:** PARTIALLY consistent with a StandardScaler fit-convention difference
  (train-only vs pooled) — pooled rescale lands within ~4% of paper MSE, a hint but
  NOT a confirmed root cause (the paper does not state its fit range).
- **MAE gap (~17% residual):** under the uniform linear rescaling, MAE shrinks by the
  same ratio as every error point, so it lands ~17% off paper — this residual is
  **unexplained** by the fit convention alone and is NOT evidence of "large errors
  contracted more."
- **CDC data-vintage:** **NOT ruled out.** We only excluded 2024+ incremental weeks;
  CDC's small retrospective revisions *within* the 2002–2021 span remain an unexcluded
  candidate (see Option 3 below). No protocol change is implied — train-only stays
  primary regardless.

---

## CDC Data-Vintage Check (Option 3)

**Question:** Does our downloaded CDC data differ from the paper's ~2021 snapshot in
a way that could explain the residual MAE gap?

**Finding (local `data/raw/national_illness_raw.csv`):**
- Shape 1025 × 9; `epiweek` range **200201 … 202152** — identical nominal coverage to
  the paper (2002–2021, per MIFlu_paper.md V-A).
- **No 2024+ weeks present.** The "2024–2026" in the original hypothesis referred to
  our *download date*, not to newer surveillance data — CDC ILINet national data for
  2002–2021 is final and stable; our file covers exactly the paper's range.
- ILITOTAL: n=1025, mean≈14190, std≈15700, min=318, max=113921 (max consistent with
  the documented COVID Wave-1 peak at epiweek 202006 ≈ 111,361).

**Conclusion (corrected 2026-08-18):** The specific "2024→2026 retroactive CDC revision"
hypothesis is **invalid and retracted** — there are **no 2024+ weeks** in our file, and both
our data and the paper cover 2002–2021. HOWEVER, this does **NOT** close the CDC-vintage
question entirely: CDC's routine **retrospective revisions *within* the 2002–2021 span**
(e.g., ILINet weekly data are periodically re-weighted/revised even years later) are still a
plausible, **unexcluded** source of small data-definition differences versus the paper's
~2021 snapshot. We have not verified our snapshot matches the paper's exact revision state,
so CDC-vintage remains an open candidate for part of the residual gap — it is **not** "ruled
out / moot."

**Reconciliation (2026-08-18, corrected):**
- **Pooled-fit is a PARTIAL, UNCONFIRMED explanation** of the MSE gap (train-only 5.056 →
  pooled ≈1.61, within ~4% of paper 1.542); it does **NOT** explain the MAE gap (train-only
  1.500 → pooled ≈0.85, still ~17% off paper 0.726). The uniform linear rescaling means all
  errors shrink by the same ratio — no non-linear compression.
- **CDC-vintage is NOT ruled out** — only 2024+ weeks are excluded; 2002–2021 retrospective
  revisions remain an unexcluded candidate (Option 3).
- **Residual gap (MAE ~17%, and the ~2–3× on primary train-only numbers) is unexplained** by
  the available evidence — the most likely remaining causes are the paper's undisclosed scaler
  fit convention and/or architecture/hyperparameter differences (lr, epochs not disclosed per
  MIFlu_paper.md V-C). Neither is resolvable without the paper's code/data snapshot. This is
  stated honestly; it is **not** claimed as a perfect reproduction.
