# Methods (manuscript-ready, English)

## Data and splitting
National ILI series. One fixed chronological split (train/validation/test) shared by all
arms. The scaler and prompt statistics are fitted on the training split only. Test never
participates in early stopping, hyper-parameter choice, model selection or thresholding.

## Protocol
Four horizons L in {24, 36, 48, 60} are trained and scored independently; predictions are
never merged across lead times. Ten seeds (42-51) for the champion arm; the frozen MIFlu
baseline provides three seeds (42-44).

## Two-level criteria
Level 1 (when to stop training): validation MSE only, patience=7, best-validation-MSE
checkpoint restored. Level 2 (post-hoc accuracy): PTE and PIE against the literature
criterion PTE <= 1 week AND PIE <= 25%. No project-defined acceptance threshold is
implemented or reported.

## Champion selection and Test isolation
Selection uses validation only, on the pre-registered Stage-F cohort of 160 unique cells.
The champion is frozen before any Test access. A single-use receipt authorises exactly one
Test evaluation, whose 52-cell manifest is immutable and created before access. Test results
never influenced selection, retraining or thresholding.

## Statistics
Per-horizon means, standard deviations and percentile bootstrap 95% CIs
(10,000 resamples, fixed RNG seed). Paired comparisons use identical (horizon, seed) pairs;
effect size is Cohen's dz; multiplicity is controlled with Holm across the whole family of
paired comparisons. Where a corrected p-value does not support a claim, the wording is
"observed best".
