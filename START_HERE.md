# START HERE — MLFlu Reproduction Guide

> **中文**：这是 MIFlu 论文复现项目的入口导读。从这里开始，三步复现全部结果。

## 1. What is this?

A **partial reproduction** of MIFlu (Moon et al., IEEE JBHI 2025) for influenza forecasting in Hong Kong. From the official 966-row ILI surveillance data to frozen predictions, authoritative MSE ranking tables, and a manuscript-ready report.

## 2. Quick Start

```bash
pip install -r requirements.txt
python reproduce_all.py
```

## 3. Key Numbers

| | Paper | Reproduction |
|--|------:|-------------:|
| MIFlu MSE (Table V) | 1.4355 | **1.8652** (+29.9%) |
| Peak criteria | 15/36 | 36/36 |
| Verdict | — | **PARTIAL_REPRODUCTION** |

## 4. Where to look

| I want to... | Go to |
|-------------|-------|
| See the authoritative report | `reports/concise_final/REPORT_精简终版.docx` |
| See the MSE ranking table | `paper_tables/TRACK_C_TEST_MSE_RANKING.csv` |
| Run scoring manually | `python scripts/score_predictions_independent.py` |
| Verify report integrity | `python scripts/verify_report_parity.py` |
| Understand terminology | `docs/GLOSSARY.md` |
| Find evidence for a claim | `docs/EVIDENCE_INDEX.md` |
| See the seven hard constraints | `README.md` "Reproducibility & Honesty Notes" |
| Check data integrity | `python scripts/verify_metrics.py` |

## 5. Honest Limitations

- **PARTIAL_REPRODUCTION**: Our MIFlu MSE (1.8652) is 29.9% higher than the paper (1.4355). The reproduction is **not** a success claim.
- **Text pathway contradiction unresolved**: Text embeddings are constant vectors, yet the paper claims text pathway influence. This contradiction is **not** resolved.
- **8-model predictions**: Per-cell predictions for 8 models are packaged in `test_eval_download.tar.gz` (not extracted locally).

## 6. For Reviewers

1. Verify official data SHA256: `2a96dfed…` (see `CURRENT_OFFICIAL_REPORT.txt`)
2. Run `python reproduce_all.py` — all 7 stages must PASS
3. Check MUST_CONTAIN strings in report: `1.8652`, `1.4355`, `+29.9%`, `PARTIAL_REPRODUCTION`, `36/36`, `15/36`
4. Verify report DOCX SHA256: `73f97cc2…`
