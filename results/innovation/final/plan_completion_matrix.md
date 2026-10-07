# Plan completion matrix

Generated 2026-09-15T18:02:45Z UTC.

Status vocabulary: `COMPLETED`, `VALID_REUSE`, `UNAVAILABLE_DEPENDENCY`,
`DEFERRED_COMPUTE_BUDGET`, `EXCLUDED_WITH_JUSTIFICATION`, `NOT_COMPLETED`.

| Requirement | Status | Evidence |
|---|---|---|
| DLinear/NLinear | **COMPLETED** | both evaluated in Screening and Stage F |
| TimesNet | **NOT_COMPLETED** | not implemented; not present in any run |
| PatchTST | **COMPLETED** | evaluated in Screening and Stage F |
| iTransformer | **COMPLETED** | evaluated in Screening and Stage F |
| TimeMixer or ModernTCN | **NOT_COMPLETED** | neither implemented |
| text encoder: none | **COMPLETED** | used by all non-LLM runs |
| text encoder: TF-IDF+SVD | **NOT_COMPLETED** | not implemented |
| text encoder: fastText | **NOT_COMPLETED** | not implemented |
| text encoder: BERT/MiniLM | **NOT_COMPLETED** | not implemented |
| text encoder: GPT-2 | **COMPLETED** | frozen gpt2_miflu / MIFlu arm |
| fusion: concat projection | **COMPLETED** | Stage G fusion ablation |
| fusion: FiLM/gating | **COMPLETED** | Stage G fusion ablation |
| fusion: cross-attention | **COMPLETED** | Stage G fusion ablation |
| negative control: zero-text | **NOT_COMPLETED** | not run |
| negative control: shuffled-text | **NOT_COMPLETED** | not run |
| LLM/TSFM: Time-LLM-style | **NOT_COMPLETED** | not implemented |
| LLM/TSFM: CALF/TimeCMA-style | **NOT_COMPLETED** | not implemented |
| TSFM: Chronos | **NOT_COMPLETED** | unavailable locally |
| TSFM: TimesFM | **NOT_COMPLETED** | unavailable locally |
| TSFM: Moirai | **NOT_COMPLETED** | unavailable locally |
| robustness analysis | **COMPLETED** | Stage I seed-repeat sweep (4 models x L24/60 x 3 seeds) |
| common-date analysis | **COMPLETED** | final_common_date_comparison.csv |
| COVID-period analysis | **NOT_COMPLETED** | not separately pre-registered or reported |
| pre-COVID analysis | **NOT_COMPLETED** | not pre-registered; must not be retroactively presented as confirmatory |
| resource analysis | **COMPLETED** | this audit (parameters, train time, GPU-hours) |
| AUC-Best-so-far | **COMPLETED** | computed in this audit from Stage-F validation runs |
| validation-only freeze | **COMPLETED** | freeze_audit.json passed=true |
| one-time Test | **COMPLETED** | 52/52 cells, single receipt |
| EvoForecast | **NOT_COMPLETED** | optional extension; deferred, not attempted |
| implementation completed | **COMPLETED** | frozen innovation source v2.10 |
| Smoke completed | **COMPLETED** | smoke runs present and annotated |
| formal evaluation completed | **COMPLETED** | Stage F: 160 unique cells |
| final Test completed | **COMPLETED** | 52/52, integrity passed |
| optional extension deferred | **NOT_COMPLETED** | EvoForecast |

Counts: {'COMPLETED': 18, 'NOT_COMPLETED': 16}

**The whole broad plan is NOT declared complete.** Mandatory main-study items
(formal evaluation, validation-only freeze, one-time Test) are complete; several
candidate families are unavailable/deferred and EvoForecast was not attempted.
