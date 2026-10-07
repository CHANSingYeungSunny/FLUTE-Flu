# Deferred Controls — Finalized Statistical Interpretation

Generated after `DEFERRED_CONTROLS_PROTOCOL_AMENDMENT_2026-09-21` closure. Matched-parent paired comparisons only. Families A and B are never pooled.

## Family A — gpt2_miflu zero_text / shuffled_text (DESCRIPTIVE / EXPLORATORY)

12 deferred specifications satisfied by exactly equivalent Wave-1 accepted rows. No rerun, no duplicated statistical observation. Parent = `gpt2_miflu`.

| control | horizon | n | mean delta | median delta | sample SD | 95% CI | Cohen d_z | paired-t | p |
|---|---|---|---|---|---|---|---|---|---|
| zero_text | L24 | 3 | -0.0325 | +0.0262 | 0.1113 | [-0.3090, 0.2440] | -0.292 | -0.506 | 0.6631 |
| zero_text | L60 | 3 | -0.0932 | -0.1710 | 0.1432 | [-0.4490, 0.2626] | -0.651 | -1.127 | 0.3767 |
| zero_text | pooled (24+60) | 6 | -0.0629 | -0.0673 | 0.1194 | [-0.1882, 0.0625] | -0.526 | -1.289 | 0.2538 |
| shuffled_text | L24 | 3 | +0.1184 | +0.2592 | 0.2441 | [-0.4881, 0.7248] | +0.485 | +0.840 | 0.4894 |
| shuffled_text | L60 | 3 | +0.0431 | -0.0683 | 0.2255 | [-0.5172, 0.6034] | +0.191 | +0.331 | 0.7721 |
| shuffled_text | pooled (24+60) | 6 | +0.0807 | +0.0954 | 0.2142 | [-0.1441, 0.3055] | +0.377 | +0.923 | 0.3983 |

Family A is reported descriptively: these are Wave-1 negative controls already accepted in the primary matrix, not newly executed confirmatory tests.

## Family B — timecma_llm llm_removed_or_alignment_only (CONFIRMATORY)

6 newly executed + ACCEPTED rows (L24/L60 x seed 42/43/44). Parent = `timecma_llm`.

| comparison | n | mean delta | median delta | sample SD | 95% CI | Cohen d_z | paired-t | p |
|---|---|---|---|---|---|---|---|---|---|
| L24 | 3 | +0.0235 | +0.0042 | 0.0486 | [-0.0973, 0.1444] | +0.484 | +0.838 | 0.4902 |
| L60 | 3 | +0.0938 | +0.0946 | 0.0063 | [0.0781, 0.1094] | +14.872 | +25.759 | 0.0015 |
| pooled (24+60) | 6 | +0.0587 | +0.0830 | 0.0494 | [0.0068, 0.1105] | +1.187 | +2.907 | 0.0335 |

### Multiple-comparison treatment (confirmatory family)

Holm-Bonferroni step-down across the two Family B horizon-specific paired t-tests (m=2), alpha=0.05:

| test | raw p | Holm-adjusted p |
|---|---|---|
| familyB_L60 | 0.0015 | 1.0000 |
| familyB_L24 | 0.4902 | 1.0000 |

### Interpretation

- **L24**: Removing the LLM/text branch does not significantly change short-horizon 7-variable z-space MSE (small, non-significant positive delta).
- **L60**: Removing the LLM/text branch significantly increases long-horizon 7-variable z-space MSE; interpreted as evidence supporting a long-horizon contribution of the text/LLM branch, NOT proof of a universal causal mechanism.
- **Caveat**: n=3 per horizon; paired t-tests have low power. Treat as supporting evidence, not conclusive causal proof.
