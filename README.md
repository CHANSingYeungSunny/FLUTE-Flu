# MLFlu — Influenza Forecasting Reproduction & Innovation (FYP)

**Author**: CHAN Sing Yeung Sunny (Final Year Project, 2026)

This repository is an independent **reproduction and innovation** study of the MIFlu method, based on *MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme* (Moon, Shim, Kim & Hwang, IEEE JBHI 29(10):7790–7801, 2025, DOI [10.1109/JBHI.2025.3561214](https://doi.org/10.1109/JBHI.2025.3561214)).

We reproduced the paper's **Table V** on the official US CDC National-Illness 966-row dataset, then ran a **28-model benchmark** with four sub-benchmarks (accuracy, peak skill, efficiency, statistical significance). The reproduction is honest: we fixed two defects discovered in the original code (data leakage via test-set checkpoint selection, and a test-loader bug) and report them as deliberate deviations.

> **中文说明**：本仓库是 CHAN Sing Yeung 的毕业设计（FYP）成果，独立复现并创新扩展了 Moon et al. (IEEE JBHI 2025) 的 MIFlu 方法。在官方 966 行 US CDC National-Illness 数据集上复现 Table V，并跑了一个 28 模型基准（含四个子基准）。复现过程诚实标注了两处修复的缺陷（验证集选检查点修复数据泄漏、7 变量指标修复 test-loader bug）。

---

## Headline Results

### Reproduction of Table V (MIFlu, 10-seed mean, 2021–2030, validation-selected checkpoints)

| Horizon L | Paper MSE | Our MSE | Δ | Paper MAE | Our MAE | Δ |
|----------:|----------:|--------:|--:|----------:|--------:|--:|
| 24 | 1.5420 | 1.3045 | **−15.4%** | 0.7260 | 0.7482 | +3.1% |
| 36 | 1.4220 | 1.3561 | **−4.6%** | 0.7790 | 0.7712 | −1.0% |
| 48 | 1.4140 | 1.6543 | +17.0% | 0.7570 | 0.8381 | +10.7% |
| 60 | 1.3640 | 1.6829 | +23.4% | 0.7190 | 0.8596 | +19.6% |
| **4L mean** | **1.4355** | **1.4995** | **+4.5%** | **0.7452** | **0.8043** | +7.9% |

**Sign crossover 2–2**: we *beat* the paper at L=24 and L=36 but *lose* at L=48 and L=60 (longer horizons are harder for our run). Net **+4.5%** on the 4-horizon mean — a close, credible reproduction. **Defensible claim only**: reproduced within 4.5% with a horizon-dependent sign — *not* a claim of superiority, and *not* "the paper is wrong". Every MIFlu cell is gated against the 40-run per-seed oracle at |Δ| ≤ 1e-5, so the numbers trace to individual runs, not a summary file.

### 28-Model Benchmark — Core Finding

| Sub-benchmark | Champion | Key number |
|---------------|----------|-----------|
| **1. MSE/MAE** (accuracy) | **MIFlu** | 1.5574 (4-horizon mean) |
| **2. PTE/PIE** (peak skill, Kramer & Shaman) | **NLinear** | 4/16 passes; step-0 PTE 0.21 wk, PIE 3.2% |
| **3. Pareto** (accuracy vs params) | NLinear is Pareto-optimal | 2,520 params vs PatchTST 531,878 (211× fewer, only 11% worse MSE, non-significant) |
| **4. Statistical significance** | NLinear ≈ PatchTST (Holm p=0.114, n.s.) | paired sign-flip test, 136 pairs |

> **The single most important result**: **the MSE champion (MIFlu) is NOT the peak-skill champion (NLinear).** For public-health deployment where catching the epidemic peak matters, NLinear is the better choice. This decoupling is the central message of the study.

### Frozen LLM encoders (negative result)

11 frozen LLM encoders (Qwen2.5, DeepSeek-R1-distill ×5 sizes, Tencent Hunyuan ×3, Tencent ContextPilot ×2) were merged into the benchmark as feature extractors + a shared linear head. **All are poor**: best Tencent-Hunyuan-1.8B (MSE 4.7374), worst Qwen2.5-1.5B (5.2049) — every one ~3× worse than MIFlu (1.5574); **none pass the Kramer & Shaman peak criterion**. Pre-trained LLM representations do **not** transfer to influenza forecasting — the paper's most novel negative result.

### Notable findings (from the 28-model benchmark)

- **A linear model is #2.** NLinear reaches MSE 1.8716 with only **2,520 parameters**, versus PatchTST's 531,878. Architecture sophistication does *not* buy accuracy on a 966-row series.
- **Published LLM forecasters do badly.** Qwen-Time-LLM (5.2557) and CALF-LLM (5.5785) are both large, published models — and both are beaten by a nearest-neighbour baseline (KNN, 3.7854).
- **Model choice dominates.** The MSE spread is **3.4×** (1.6621 → 5.6155); which model you pick matters far more than any hyper-parameter tuning reported in the compared papers.
- **More parameters ≠ better.** Regressing 4-horizon MSE on log₁₀(parameters) across the 11 parametric arms gives slope **+0.1171** and **R² = 0.0223** — i.e. more parameters trend *worse*, and the relationship is ~pure noise. Parameter count is not a selection criterion here.
- **Significance is mostly established.** Of 136 model pairs, **109 are significant** after Holm–Bonferroni correction (NLinear vs PatchTST is the notable exception: p_holm = 0.114, not significant).

---

## Deviations from the Paper (reported honestly)

| # | Deviation | Original code | Why necessary |
|---|-----------|--------------|---------------|
| 1 | **Checkpoint selection** | paper/test config uses **test set** to pick best checkpoint → data leakage | we select on the **validation** set only. Top-tier venues forbid test-set selection. |
| 2 | **Metric aggregation** | 7-variable normalized aggregation | we use **7-variable z-space MSE/MAE** to match Table V exactly; PTE/PIE use **ILITOTAL** (de-normalized to patient counts) because the 7 variables differ in scale by ~283,650× (OT mean 493,629 vs %ILI 1.74) and cannot be de-normalized. |

Both deviations are flagged `[DEVIATION]` in the reports.

---

## Why These Protocol Choices (for reviewers)

- **Reproduction uses 10 seeds (2021–2030); benchmark uses 3 seeds (42/43/44).** Reproduction follows the original protocol (10 runs); the benchmark follows top-venue convention (PatchTST ICLR 2023 / iTransformer ICLR 2024 use 3 seeds) — **flagged `[to verify]`** because the claim about those papers' seed counts should be checked against the original PDFs.
- **70/10/20 train/val/test split (676/97/193 weeks), chronological.** This is the standard split of the LTSF benchmark family (Informer → PatchTST → MIFlu); scaler fit on train only.
- **`(W//16)*16` test windows (160/144/144/128).** NOT a journal requirement — a side-effect of the original code's `batch_size=16, drop_last=True` (incomplete tail batches dropped). We keep it for comparability with the paper.
- **Pareto frontier**: the set of models where no other model is both more accurate *and* more efficient. A standard ML-efficiency analysis (e.g., used in Neural Architecture Search literature).

---

## Repository Structure

```
MLFlu/
├── README.md                      # This file
├── HPC_GUIDE.md                   # How to run experiments on the CityU HPC cluster
├── reproduce_all.py               # One-click reproduction entry
├── requirements.txt
├── CITATION.cff  /  LICENSE
├── 01_最终报告/                   # Generated reports (DOCX + PDF) + build pipeline (_build2/)
│   ├── report_internal_zh.pdf     # Internal technical report (Sections 1–10, ~20 pp)
│   ├── report_internal_en.pdf
│   ├── progress_report_zh.pdf     # FYP progress report (school template, ~8 pp)
│   ├── progress_report_en.pdf
│   ├── ieee_manuscript_zh.pdf     # IEEE JBHI-style manuscript (I–X, ~8 pp)
│   ├── ieee_manuscript_en.pdf
│   ├── record_for_journal_zh.pdf  # Full archive for journal submission (~20 pp)
│   ├── record_for_journal_en.pdf
│   ├── figures/                   # All charts (per-model forecast, K&S ranking, Pareto…)
│   ├── chatgpt_prompt.md          # Task brief for ChatGPT handoff
│   └── PROJECT_HANDOFF.zip        # Everything ChatGPT needs (173 MB, gitignored)
├── 02_数字表格/                   # Authoritative CSV tables (BENCH_*, ESSAY_VS_REPRODUCTION_TABLE_V…)
├── 03_预测数据_证据/              # Frozen predictions (expanded_runs/) + audit evidence
├── 04_详细说明文档/               # Glossary, methodology notes, evidence index
├── 05_程序代码/                   # Reproduction + benchmark pipeline (configs, analysis, tables)
├── 06_原始数据集/                 # Official 966-row CDC dataset + scaler
└── hpc_experiments/               # HPC driver scripts, queue diagnostics, remote helpers
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the full reproduction + benchmark + report pipeline
python reproduce_all.py

# 3. Verify report integrity (content + CJK round-trip)
python 01_最终报告/_build2/build_docs.py
python 01_最终报告/_build2/to_pdf.py
python 01_最终报告/_build2/verify_docs.py   # expect: FAILURES: 0
```

---

## Key Definitions (used throughout the reports)

- **Horizon L**: input is a fixed **T=104**-week history; output is **L weeks** of forecast (L=24/36/48/60). L is the *lead* (how far ahead), not the history length.
- **Step s** within an L-week forecast: step 0 = the **1st week ahead** (1 week early), step 3 = the 4th week ahead.
- **PTE (Peak Timing Error)** = |predicted peak week − actual peak week| (weeks). **PIE (Peak Intensity Error)** = relative error of predicted peak intensity. **Kramer & Shaman (2019, PLoS Comput Biol 15(2):e1006742)** criterion: PTE ≤ 1 week **and** PIE ≤ 25% ⇒ peak captured. *Attribution to K&S is flagged `[to verify]` — the exact thresholds should be confirmed against the original paper.*

---

## Deliverables — Reports (in `01_最终报告/`)

All three report types are produced in **both Chinese (zh) and English (en)** variants (6 PDFs + 6 DOCXs), built from the same pipeline (`_build2/`) so numbers are identical across languages.

| File (zh shown; `.en` also exists) | Pages | Purpose |
|------|------:|---------|
| `report_internal_zh.pdf` / `.docx` | ~20 | **Internal technical report** — full results briefing for supervisor. Sections 1–10 (continuous numbering), every method/number explained inline right after the content it refers to. |
| `progress_report_zh.pdf` / `.docx` | ~8 | **FYP progress report** — follows school template `Requirements_ProjectProgressReport_2627A` (Part A cover + Part B items 1–7). Submitted via FYP InfoNet. |
| `ieee_manuscript_zh.pdf` / `.docx` | ~8 | **IEEE JBHI-style manuscript** — I–X sections, submission-ready draft of the reproduction + benchmark study. |
| `record_for_journal_zh.pdf` / `.docx` | ~20 | **Full archive** — expanded version kept for journal submission / audit (superset of the internal report). |
| `figures/` | — | All charts: per-model forecast lines (28 models × 4 horizons), K&S ranking, Pareto frontier, ablation ladder. |

**Key content shared by all reports** (so the README, reports, and tables never disagree):
- Table V reproduction: **+4.5%** mean (sign crossover 2–2: beat paper at L24/L36, lose at L48/L60).
- 28-model benchmark with **per-horizon MSE *and* MAE** (Table 5, L24/36/48/60).
- **Peak-skill ranking (Table 6) by PTE/PIE/K&S** — **NLinear champion** (4/16 passes, step-0 PTE 0.21 wk, PIE 3.2%), *not* by MSE. MIFlu is the MSE champion but only peak-skill #2.
- Four sub-benchmarks: accuracy (MSE/MAE), peak skill (PTE/PIE), efficiency (Pareto), significance (Holm-corrected paired test).

**Handoff package**: `PROJECT_HANDOFF.zip` (in `01_最终报告/`, ~173 MB, gitignored) — full project for ChatGPT (reports, tables, code, figures, prompt). For a slimmer context-only package see `PROJECT_PROGRESS_SNAPSHOT.zip` at the repo root.

**Presentation**: Progress presentation is in Week 12 (Nov 16–20, 2026); report submission deadline **20 Nov 2026 (11:59 pm)** via FYP InfoNet. A PPT + talking script is generated from the internal report by ChatGPT (see `chatgpt_prompt.md`).

---

## Status (as of 2026-11-03)

- ✅ Table V reproduction (10-seed, +4.5%, sign crossover 2–2)
- ✅ 28-model benchmark, 4 sub-benchmarks
- ✅ Table VIII ablation (60/60 cells), MIFlu is the logarithmic-ladder champion
- ✅ 11 frozen LLM encoders added (negative result)
- 🔄 Table VI (regional, 10-seed × 7 regions = 70 cells) running on HPC; Table IX (regional training time) gated behind it
- 🔄 Rolling-origin evaluation queued on HPC (lower priority)

---

## Citation

If you use this work, please cite:

```bibtex
@misc{chan2026mlflu,
  title        = {MLFlu: Influenza Forecasting Reproduction \& Innovation},
  author       = {CHAN, Sing Yeung Sunny},
  year         = {2026},
  howpublished = {\url{https://github.com/CHANSingYeungSunny/FLUTE-Flu}},
  note         = {Final Year Project}
}
```

The paper being reproduced:

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

See [CITATION.cff](CITATION.cff) for machine-readable metadata.

---

## License

MIT License — see [LICENSE](LICENSE).

---

## Author

**CHAN Sing Yeung Sunny** — Final Year Project (2026). Sole author of this reproduction and innovation study.
