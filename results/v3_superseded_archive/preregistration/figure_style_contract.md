# v3 unified figure-style and fixed-step contract

Generated 2026-09-15T19:25:49Z.

- style guide: `docs/FIGURE_STYLE_GUIDE.md`  SHA-256 `4e2ee958bb1561e41155e735c8b2bdd6a2c6ee2270e66e06568077c6de070741`
- reference figure: `results/ili/figures/fig_q1_step_sweep_L24_L60_step0.png`  SHA-256 `06d8622152ef2bf00017278fb6925283445e8c604d7973a6d35a4798b1399d70`
- shared module: `scripts/v3/figure_style.py`  SHA-256 `c604b4718403fd4dedd9640735d5580cdf5752f820516d438886d00055df2b78`
- shared-module API check: **PASSED**

## Canvas / DPI / fonts

- canvas by kind: {'hero': (7.0, 4.2), 'diagnostics': (13.0, 4.2), 'step_sweep': (13.0, 4.2), 'group': (11.0, 4.2), 'resource': (7.0, 4.6), 'square': (7.0, 7.0)}
- export DPI 300, screen DPI 100, backend Agg
- fonts: {'font.size': 9, 'axes.titlesize': 11, 'axes.labelsize': 9, 'legend.fontsize': 8, 'xtick.labelsize': 8, 'ytick.labelsize': 8, 'figure.titlesize': 11, 'axes.titleweight': 'bold'}

## Stable model identities

| model_key | colour | linestyle | marker | label |
|---|---|---|---|---|
| `nlinear` | #0072B2 | `-` | o | NLinear |
| `dlinear` | #56B4E9 | `-` | s | DLinear |
| `patchtst` | #009E73 | `--` | ^ | PatchTST-inspired |
| `itransformer` | #E69F00 | `-.` | D | iTransformer-aligned |
| `gpt2_miflu` | #D55E00 | `-` | v | MIFlu GPT-2 |
| `qwen_time_llm` | #CC79A7 | `--` | P | Qwen2.5-1.5B Time-LLM-inspired |
| `calf_llm` | #8C564B | `-.` | X | CALF-inspired Cross-Modal LLM |
| `timecma_llm` | #6A3D9A | `(0, (3, 1, 1, 1))` | * | TimeCMA-inspired LLM |
| `last_value_naive` | #7F7F7F | `:` | x | Last-value naive |
| `seasonal_naive` | #4D4D4D | `(0, (1, 2))` | + | Seasonal naive |
| `zero_text` | #D55E00 | `(0, (1, 3))` | o | zero-text control |
| `shuffled_text` | #D55E00 | `(0, (3, 1, 1, 1, 1, 1))` | s | shuffled-text control |
| `llm_removed_or_alignment_only` | #6A3D9A | `(0, (5, 2))` | ^ | LLM-removed / alignment-only |

## Fixed-step contract

| step | lead time | label | linestyle | marker | role |
|---|---|---|---|---|---|
| 0 | 1 weeks | 1-week ahead | `-` | o | PRIMARY |
| 1 | 2 weeks | 2-week ahead | `--` | s | supplementary |
| 2 | 3 weeks | 3-week ahead | `-.` | ^ | supplementary |
| 3 | 4 weeks | 4-week ahead | `:` | D | supplementary |

Rules: steps are never averaged; step 0 is the primary endpoint; the champion is
selected on step 0 only; cross-model comparisons use the identical target-date
intersection; figures are generated from saved artifacts only.
