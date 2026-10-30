# EVIDENCE INDEX — 证据索引（每个数字从哪来）

> For every headline number in the authoritative report: where the evidence lives and how it is
> verified. 中文提示随附。**Do not recompute or "fix" evidence files; they are frozen records.**

## 1. Hash chain / 哈希链

| What | sha256 | File |
|------|--------|------|
| **Author dataset** (official, 966 rows) | `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5` | `recovery/author_repo/dataset/illness/national_illness.csv` |
| Author dataset, readable-header variant | `8594cecb98c6f2f9dc014eca11c4d5d1e38ad5ce6ed0592d4abe65b146fce395` | `recovery/author_repo/dataset/illness/national_illness_orig.csv` |
| Project-schema copy (966 rows, value-identical) | `31ffc1693de205ca8de5e966d40c93252e0a0076a212fffc54d1418e1a13b87a` | `data/raw/national_illness_raw_paper_exact.csv` |
| 2026-07 FluView snapshot (1025 rows, ⚠ different vintage) | `c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d` | `data/raw/national_illness_raw.csv` |
| **Authoritative DOCX report** | `73f97cc2439f56950b37fa9a8726cac1f84e375b54553700f93b2f196b2ea5f6` | `reports/concise_final/MIFlu_..._精简终版.docx` (see `CURRENT_OFFICIAL_REPORT.txt`) |
| Test key (seed,horizon,origin) digest | computed at report build (`TEST_KEY_SHA`) | printed on the DOCX cover; recomputed by `scripts/build_concise_final_report.py` from `results/v3_clean/analysis/peak_criteria/miflu/*/test_predictions_*.csv` |
| Author repo identity | remote `https://github.com/Jmoon3108/MIFlu.git`, verified non-fork | `recovery/manifest.json`, `hpc_results/official_repo_reproduction_20261006/REPOSITORY_PROVENANCE.md` |

> 中文：正式数据 = 作者 966 行 CSV（2a96dfed…）；1025 行快照是另一 vintage，数值不同，绝不可混比。

## 2. Where each headline number comes from / 数字出处

| Number | Value | Evidence |
|--------|-------|----------|
| Paper target avg MSE | 1.4355 (per-L: 1.542/1.422/1.414/1.364) | paper Table V (`docs/01_paper/PAPER_EXPLAINED.md` §7) |
| Our MIFlu Test `average_MSE_4L` | **1.8652** (SD 0.0916), MAE 0.8842 | frozen contract + 12 prediction CSVs in `results/v3_clean/analysis/peak_criteria/miflu/`; ranked in the championship table of the authoritative report |
| 8-model ranking | MIFlu 1.8652 > NLinear 2.0495 > DLinear 2.3478 > TimeCMA-LLM 2.6700 > PatchTST 3.9205 > iTransformer 3.9847 > Qwen-Time-LLM 5.2196 > CALF-LLM 5.5153 | authoritative report §5 (frozen championship contract) |
| Group means | non-LLM 3.0756 / LLM-side 3.8175 | same (4 vs 4; MIFlu counts as LLM-side) |
| Reproduction verdict | PARTIAL_REPRODUCTION, +29.9% (1.8652 vs 1.4355), 5% not met | `hpc_results/official_repo_reproduction_20261006/r1_v2_verification_20261007/R1C_FINAL_VERDICT.md`, `R1C_PAPER_GAP_ANALYSIS.md`, `.../r0_r5_cpu_stage_20261006/PAPER_LEVEL_REPRODUCTION_VERDICT.md` |
| PTE/PIE peak hits (literature criterion) | NLinear 36/36, DLinear 31/36, MIFlu 15/36, Qwen 1/36, TimeCMA/PatchTST/iTransformer/CALF 0/36 (denominator 36 true peaks/model) | `results/v3_clean/analysis/peak_criteria/TRACK_C_PTE_PIE_PASS_MATRIX.csv`, `TRACK_C_PTE_PIE_PER_EVENT.csv`, `TRACK_C_PEAK_CONTRACT.md` |
| PTE/PIE definitions & criterion | PTE = \|pred−true\| peak week; PIE = relative peak intensity error; hit iff PTE≤1wk & PIE≤25% | `TRACK_C_PEAK_CONTRACT.md` + `TRACK_C_PTE_PIE_REPORT_ZH.md` |
| Stop-rule sensitivity (Track S) | 11/12 fits identical; 1 fit +0.144; rankings unchanged | `TRACK_S_FINAL_REPORT_DECISION.md` |
| COVID-period error spike | documented in peak-criteria audit | `TRACK_C_COVID_PERIOD_ANALYSIS.md`, `TRACK_C_TEMPORAL_ALIGNMENT_AUDIT.csv` |
| Data identity (966 vs 1025 vintages) | identical pre-2016, revised from MMWR 2016w40 | `recovery/data_identity_report.md` |
| Tutor five-question status | see matrix | `results/v3_clean/analysis/peak_criteria/TUTOR_FIVE_QUESTIONS_CURRENT_STATUS.csv` + root `MIFlu_导师五大疑问_回复报告.md` |

## 3. Authority labels / 报告权威等级

| Label | Meaning | Where |
|-------|---------|-------|
| `CURRENT_AUTHORITATIVE_FINAL_REPORT` | The only source of conclusions | `reports/concise_final/…_精简终版.docx` |
| `COMPREHENSIVE_EVIDENCE_REPORT` | Full evidence dig (supporting) | v2 report under `results/v3_clean/analysis/reports/` |
| `SUPERSEDED_HISTORICAL_REPORT` | Old 1025-row era; background only | historical reports |

## 4. Rules when citing evidence / 引用规则

1. Never edit files under `results/`, `hpc_results/`, `recovery/`, `audit_20260930/` — frozen records.
2. Quote track + seeds + space with any score (see `docs/GLOSSARY.md` §6).
3. The text-path mechanism contradiction stays "unresolved" — both sides' evidence is listed in
   `hpc_results/` (GPU replay vs CPU replay) and `results/` (ablation `notext` vs full model).
