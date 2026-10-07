# Results (manuscript-ready, English)

## Primary metric

Following MIFlu (IEEE JBHI 2025, §V-B), MSE and MAE in the normalised (z) space are the
primary accuracy metrics; physical-unit values are reported as supplementary.

## Test-set accuracy

| Horizon | NLinear MSE (z) | MIFlu (GPT-2) MSE (z) | Reduction | NLinear MAE (z) | MIFlu MAE (z) |
|---|---|---|---|---|---|
| L=24 | 4.2966 | 5.6766 | 24.31% | 1.4013 | 1.6186 |
| L=36 | 4.9728 | 6.1983 | 19.77% | 1.5239 | 1.6733 |
| L=48 | 5.4046 | 5.7914 | 6.68% | 1.6058 | 1.5966 |
| L=60 | 5.6085 | 6.6225 | 15.31% | 1.6436 | 1.6948 |

The frozen champion **nlinear** shows a *lower* Test MSE than the frozen MIFlu baseline **gpt2_miflu** at all four horizons, with observed reductions of 6.68%--24.31% in z-space MSE. On MAE the two arms are effectively tied at L=48, where the baseline is marginally lower.

## Statistical caveat (mandatory wording)

The baseline provides three seeds, so the effective paired sample size is **3** per horizon, not ten. After Holm correction across all paired comparisons, only one comparison reaches significance. Accordingly we report **observed best** and make **no broad claim of statistical superiority**.

## Peak criterion

The only acceptance criterion implemented and reported is the literature criterion
**PTE <= 1 week AND PIE <= 25%** (seasonal peak timing error and peak intensity error).

| Model | L | mean PTE (weeks) | mean PIE (%) | criterion |
|---|---|---|---|---|
| nlinear | 24 | 1.67 | 9.50 | not met |
| nlinear | 36 | 2.00 | 10.57 | not met |
| nlinear | 48 | 0.35 | 3.33 | MET |
| nlinear | 60 | 0.15 | 2.08 | MET |
| gpt2_miflu | 24 | 4.67 | 72.18 | not met |
| gpt2_miflu | 36 | 5.33 | 77.34 | not met |
| gpt2_miflu | 48 | 2.00 | 25.29 | not met |
| gpt2_miflu | 60 | 2.00 | 23.27 | not met |

NLinear meets the literature criterion at L=48 and L=60 and does not meet it at
L=24 or L=36. The frozen MIFlu baseline does not meet it at any evaluated horizon.

## Naming fidelity

PatchTST- and iTransformer-based backbones are re-implementations **inspired by** the
published architectures; they are described as `PatchTST-inspired` and
`iTransformer-aligned`, not as official reference implementations.

## Unavailable or deferred families

TimesNet, TimeMixer/ModernTCN, TF-IDF+SVD, fastText, BERT/MiniLM, zero-text and
shuffled-text negative controls, Time-LLM-style reprogramming, CALF/TimeCMA-style
alignment, and Chronos/TimesFM/Moirai were **not** available or **not** completed and
are therefore not reported as results.
