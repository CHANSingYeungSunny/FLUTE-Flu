# MIFlu Reproduction — IEEE JBHI 2025

Reproduction of *MIFlu: Large Language Model-Based Multimodal Influenza
Forecasting Scheme* (Moon et al., IEEE JBHI 2025) on the US CDC national
influenza dataset, plus a Phase 2 ChatTime-backbone comparison.

## Current authoritative result source

**The only current conclusion source is the four independent per-horizon tables
produced under the paper protocol** (`scripts/train_miflu.py`, `L ∈ {24,36,48,60}`
trained and evaluated separately):

- `data/results_miflu_paper_protocol_*.csv` — raw per-rep results
- `data/results_miflu_paper_protocol_table_*.csv` — tidy table (MSE / MAE / RMSE /
  PCC, mean ± std over 10 repetitions, English headers)
- `data/predictions_miflu_L{L}_paper_protocol.csv` — per-horizon test predictions
  with an explicit `split` column (train / val / test)

Protocol: `T=104`, `L ∈ {24,36,48,60}` evaluated **independently** (four separate
runs, not a rolling window), static `70:10:20` time-ordered split (`shuffle=False`),
`Lp=24, S=2`, GPT2 first `K=6` layers + LoRA `r=4` on attention only, positional
embeddings and LayerNorm frozen, StandardScaler fit on the **train split only**,
10 repetitions averaged.

## Deprecated artifacts (DO NOT USE as conclusions)

The previous **ChatTime-style L=52 walk-forward** pipeline is **deprecated** and
isolated under `scripts/chattime_variant/`. Its outputs
(`results/ili/miflu_fulltest_walkforward.csv` and any `*_DEPRECATED.png` figures)
use a *different* evaluation protocol and are **NOT comparable** to the paper's
Table V. They are retained only for the Phase 2 ChatTime comparison.

| Artifact | Status |
|----------|--------|
| `data/results_miflu_paper_protocol_*.csv` | ✅ CURRENT (paper protocol) |
| `results/ili/miflu_fulltest_walkforward.csv` | ⚠️ DEPRECATED (ChatTime L=52) |

## Known limitations (honest disclosure)

1. **Learning rate / epoch counts were not disclosed** by the paper ("set
   empirically", Section V-C). Exact digit-for-digit reproduction is therefore
   **not claimed**; the target is matching order of magnitude and qualitative
   trends per horizon.
2. **No official code or data snapshot** was released. Our pipeline is rebuilt
   from the paper text (see `MIFlu_paper.md`, the sole cross-reference — the direct
   markdown conversion of the IEEE JBHI 2025 PDF).
3. **Distribution shift in the test period (2020–2021, COVID-19 NPIs)** causes an
   atypical near-flat influenza season absent from the 2002–2019 training data.
   This is a legitimate generalization failure, **not** data leakage (proven in
   `docs/leakage_audit_report.md` and `tests/test_leakage_audit.py`).
4. Reported short-horizon (L=24/36/48) magnitudes remain higher than the paper's;
   this is documented in `PROJECT_STATUS.md`, not hidden.

## Deliverables (all in English)

- [x] Four per-horizon result tables (MSE / MAE / RMSE / PCC, 10-run mean ± std).
- [x] Prediction CSVs with an explicit `split` column.
- [x] Leakage-audit report — `docs/leakage_audit_report.md`.
- [x] Fixed peak / Timing metrics — `scripts/compute_miflu_indicators.py`
      (Peak Hit count always co-reported with Timing; unmatched peaks recorded as
      "Missed", never Timing = 0).
- [x] Feature-importance report with causal caveat — `scripts/feature_verification.py`
      (Granger labeled as "temporal precedence + statistical association";
      NUM. OF PROVIDERS / OT caveat on reporting-scale effects).
- [x] Unit tests — `tests/test_leakage_audit.py`, `tests/test_timing_metric.py`.

## Reproduce

```bash
# 1. Train + evaluate the four horizons (needs GPU/CPU torch + transformers).
python scripts/train_miflu.py            # default: L ∈ {24,36,48,60}, 10 reps

# 2. Peak / trend indicators on the test split (per L).
python scripts/compute_miflu_indicators.py \
    --pred_csv data/predictions_miflu_L24_paper_protocol.csv --prefix miflu_L24_

# 3. Evaluation figures (test split only, with COVID shift annotation).
python scripts/make_miflu_evaluation_figure.py \
    --pred_csv data/predictions_miflu_L24_paper_protocol.csv --L 24

# 4. Run the leakage + timing audit.
python -m pytest tests/ -v
```

## Phase 2 (planned, not yet implemented)

Substitute the LLM backbone with **ChatTime** (Wang et al., AAAI 2025) using its
native foreign-language-tokenization protocol, compared against the MIFlu
reproduction above. Isolated under `scripts/chattime_variant/`; the MIFlu
architecture is left unchanged.
