# Statistical audit

- **Pairing unit**: one trained run per (model, horizon, seed).
- **Matched seeds**: [42, 43, 44] → effective paired n = **3** (NOT ten).
- Champion seeds available: 10; baseline seeds: {'gpt2_miflu': 3}.
- **Bootstrap**: percentile, 10000 resamples, `numpy.random.default_rng(20260916)`, 95% CI.
- **Effect size**: Cohen's dz (paired, ddof=1).
- **Holm family**: 8 comparisons (4 horizons x MSE/MAE).
- **Significant after Holm**: ['L36 mae_ili_phys'].

## Limitations

- With three matched seeds the paired tests are severely underpowered and are reported for completeness only.
- Champion seeds 45-51 have no baseline counterpart and are excluded from pairing; they must not be described as paired observations.
- No broad statistical-superiority claim is made.
