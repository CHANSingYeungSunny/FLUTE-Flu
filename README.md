# MLFlu — Influenza Forecasting Reproduction & Innovation (FYP)

**Author**: CHAN Sing Yeung Sunny (Final Year Project, 2026)

This repository is an independent reproduction and innovation study of the MIFlu method, referencing *MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme* (Moon, Shim, Kim & Hwang, IEEE JBHI 29(10):7790–7801, 2025, DOI [10.1109/JBHI.2025.3561214](https://doi.org/10.1109/JBHI.2025.3561214)).

This repository contains the complete pipeline from the official US CDC National-Illness 966-row dataset to a fully reproducible manuscript-ready report, including frozen predictions, authoritative tables, and audit trails.

> **中文说明**：本仓库是 CHAN Sing Yeung 的毕业设计（FYP）成果，独立复现并创新扩展了 Moon et al. (IEEE JBHI 2025) 的 MIFlu 方法。从官方 966 行 US CDC National-Illness 数据集出发，产出训练模型、独立评分、权威排名表、论文图集与一份权威报告。所有数字可追溯、可核验。

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the full reproduction chain (scoring → tables → report)
python reproduce_all.py

# 3. Verify report integrity
python scripts/verify_report_parity.py
```

> **Note**: The 8-model per-cell prediction files (14 `.npz` files) are packaged in `test_eval_download.tar.gz` / `r1c_logs.tgz` for size reasons. If missing, the scoring stage will report exactly what is absent — it will not silently skip.

---

## Key Results (Table V, 36 cells, MSE ↓)

| Model | Paper | Reproduction | Δ |
|-------|------:|-------------:|--:|
| **MIFlu** (best) | 1.4355 | **1.8652** | **+29.9%** |
| LLM baselines mean | — | 3.861596 | — |
| Non-LLM baselines mean | — | 3.075638 | — |

**Verdict: PARTIAL_REPRODUCTION**

- Peak criteria (15 of 36 cells best): Paper 15/36 → Reproduction 36/36
- All comparisons use strict 966-row data with **zero tolerance** for missing values
- Text pathway mechanism contradiction **unresolved** — see honesty notes below

> **中文**：MIFlu MSE 1.8652 vs 论文 1.4355（+29.9%），结论 PARTIAL_REPRODUCTION。峰判据 36/36 vs 论文 15/36。

---

## Repository Structure

```
MLFlu/
├── reproduce_all.py              # One-click reproduction entry (7 stages)
├── data/                         # Official 966-row dataset + scaler + predictions
├── checkpoints/                  # Trained model checkpoints (best_miflu_L*.pth)
├── results/v3_clean/             # Frozen predictions, peak criteria, figures
├── hpc_results/
│   ├── official_repo_reproduction_20261006/   # Training logs + authoritative tables
│   └── checkpoints/               # HPC-trained checkpoints
├── reports/concise_final/        # AUTHORITATIVE report (DOCX/PDF/MD)
├── scripts/                      # Reproduction chain scripts (scoring, tables, report)
├── paper_tables/                 # Flat copies of authoritative tables
├── docs/                         # Glossary, evidence index, protocol freeze
├── audit_20260930/               # Audit evidence (frozen)
├── tests/                        # Regression test suite (342 cases)
└── handoff/                      # Compact handoff package builder
```

---

## Data Availability

| Asset | Location | SHA256 |
|-------|----------|--------|
| Official 966-row data | `data/official_merged_ili_966.csv` | `2a96dfed…` |
| Scaler params | `data/train_966_std_scaler.csv` | `bcb95d55…` |
| Predictions (14 files) | `test_eval_download.tar.gz` / `r1c_logs.tgz` | see `AUDIT_TABLE_IV_TRACEABILITY.md` |
| Model checkpoints | `checkpoints/best_miflu_L{24,36,48,60}.pth` | see manifests |
| Authoritative report | `reports/concise_final/REPORT_精简终版.docx` | `73f97cc2…` |

---

## Reproducibility & Honesty Notes

> **Seven hard constraints (原文中文保留)**:
>
> 1. **A/B 轨数字不可比**：官方 V4.1 九步（1.4355）vs 官方 strict966 十步（1.8652）是两条数据链，数字不可比。
> 2. **文本通路机制矛盾未决**：文本嵌入为常向量 vs 文本通路有影响——两者矛盾，未解决。禁止"复现成功"表述。
> 3. **峰判据**（文献准则 PTE≤1周 & PIE≤25%）：NLinear 36/36 (100%)、DLinear 31/36 (86.1%)、MIFlu 15/36 (41.7%)。此前文档误将 DLinear 的 31/36 归给 MIFlu，已修正。Peak 分析测的是 k=1（一周前预测），非 L=24-60 周峰值预测。
> 4. **统一 pair**：`UNIFIED_PAIR_KEY=966|L24|seed42`，仅匹配 966/L24/seed42。
> 5. **唯一权威报告**：`REPORT_精简终版.docx` + MD 镜像。
> 6. **官方数据 SHA256**：`2a96dfed…`，不做静默修正。
> 7. **MSE≠accuracy**：MSE 排名与 accuracy 衡量不可互换。
>
> **English summary**: (1) Table V numbers from two data chains are not comparable. (2) The text-pathway mechanism contradiction (constant text embedding vs. claimed text influence) is **unresolved** — no "reproduction success" claim is made. (3) Peak criteria (PTE≤1wk & PIE≤25%): NLinear 36/36, DLinear 31/36, MIFlu 15/36. Earlier docs misattributed DLinear's 31/36 to MIFlu — corrected. Peak analysis uses k=1 (one-week-ahead), not L=24–60 week lead forecasts. (4) Unified pair is fixed to 966|L24|seed42. (5) There is one authoritative report. (6) Official data SHA256 is verified. (7) MSE ranking is not interchangeable with accuracy metrics.

---

## Citation

If you use this work, please cite this repository:

```bibtex
@misc{chan2026mlflu,
  title        = {MLFlu: Influenza Forecasting Reproduction \& Innovation},
  author       = {CHAN, Sing Yeung Sunny},
  year         = {2026},
  howpublished = {\url{https://github.com/CHANSingYeungSunny/FLUTE-Flu}},
  note         = {Final Year Project}
}
```

The reference paper being reproduced:

```bibtex
@article{moon2025miflu,
  title   = {MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme},
  author  = {Moon, Jinha and Shim, Seongjun and Kim, Minha and Hwang, Jae-Hyun},
  journal = {IEEE Journal of Biomedical and Health Informatics},
  volume  = {29},
  number  = {10},
  pages   = {7790--7801},
  year    = {2025},
  doi     = {10.1109/JBHI.2025.3561214}
}
```

See [CITATION.cff](CITATION.cff) for machine-readable citation metadata.

---

## License

MIT License — see [LICENSE](LICENSE).

---

## Author

**CHAN Sing Yeung Sunny** — Final Year Project (2026). Sole author of this reproduction and innovation study.
