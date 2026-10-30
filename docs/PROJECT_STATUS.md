# PROJECT STATUS — 当前状态（2026-10-30）

> Snapshot of what is done, what the results are, and what is still open. 中文要点随附。
> Historical status snapshots live in `docs/planning/PROJECT_STATUS.md` (moved from root).

## 1. What is complete / 已完成

| Workstream | Status | Where |
|------------|--------|-------|
| Paper study & repo study | ✅ | `docs/01_paper/` |
| Author-repo reproduction (R1-C: 24 fits, 3 seeds × 4 horizons × 2 scheduler configs, all rc 0) | ✅ | `hpc_results/official_repo_reproduction_20261006/r1_v2_verification_20261007/` |
| Strict 966-row **8-model championship** (frozen contract, one-time Test, canonical scorer) | ✅ | `results/v3_clean/analysis/peak_criteria/` |
| Peak-accuracy audit (PTE/PIE, literature criterion) | ✅ | `TRACK_C_PTE_PIE_*` + `TRACK_C_PEAK_CONTRACT.md` |
| COVID-period / temporal alignment / variable-label audits | ✅ | `TRACK_C_COVID_PERIOD_ANALYSIS.md` etc. |
| Stop-rule sensitivity (Track S) | ✅ (supplementary) | `TRACK_S_FINAL_REPORT_DECISION.md` |
| Independent audit (2026-09-30) | ✅ | `audit_20260930/` |
| Authoritative report (DOCX) + QA + manifest | ✅ | `reports/concise_final/` |
| Tutor five-question reply + evidence map | ✅ | root `MIFlu_导师五大疑问_回复报告.*` + `TUTOR_FIVE_QUESTIONS_*` |
| Repo restructure + docs layer + ChatGPT handoff package | ✅ (this pass) | `docs/`, `archive/`, `handoff/` |

## 2. The current benchmark / 当前基准结果（canonical）

**Contract**: author 966 rows · Train/Val/Test 676/97/193 · strict containment · Train-only
scaler · z-space canonical scorer · seeds 42/43/44 · horizons L=24/36/48/60 · one-time Test.

| Rank | Model | Group | Test avg_MSE_4L | SD | Peak hits (PTE≤1wk & PIE≤25%) |
|-----:|-------|-------|----------------:|-----:|------------------------------:|
| 1 | **MIFlu (official-repo corrected)** | LLM-side | **1.8652** | 0.0916 | 15/36 |
| 2 | NLinear | non-LLM | 2.0495 | 0.0299 | **36/36** |
| 3 | DLinear | non-LLM | 2.3478 | 0.0040 | 31/36 |
| 4 | TimeCMA-LLM | LLM-side | 2.6700 | 0.0177 | 0/36 |
| 5 | PatchTST | non-LLM | 3.9205 | 0.0543 | 0/36 |
| 6 | iTransformer | non-LLM | 3.9847 | 0.0317 | 0/36 |
| 7 | Qwen-Time-LLM | LLM-side | 5.2196 | 0.0701 | 1/36 |
| 8 | CALF-LLM | LLM-side | 5.5153 | 0.0307 | 0/36 |

- Group means: non-LLM **3.0756** vs LLM-side **3.8175** (4 vs 4; MIFlu is LLM-side).
- MIFlu wins every horizon and every seed; 11/12 matched seed–horizon cells vs NLinear.
- **MSE champion ≠ peak champion**: NLinear captures every literature peak; MIFlu misses most.
- Paper reproduction: **1.4355 ↔ 1.8652 = +29.9% → PARTIAL_REPRODUCTION** (5% band not met).

> 中文：MIFlu 是 MSE 冠军（1.8652）但只命中 15/36 个峰；NLinear 峰值 36/36 全中。论文复现差距
> +29.9%，仅部分复现。**MSE ≠ 准确率。**

## 3. Open issues / 未决问题（诚实披露）

1. **Text-path mechanism contradiction (UNRESOLVED)** — GPU replay: text-embedder gradients
   non-zero; CPU replay: effect exactly zero. Ablations disagree (A-track `notext` better than
   full model; B-track 10-seed `gpt2_miflu` ranks #1). Must stay reported as unresolved.
   > 文本通路是否有效存在矛盾，两侧证据相反，不得擅自下结论。
2. **Reproduction gap of +29.9%** — optimizer/scheduler/seed list/pooling axis not fully
   disclosed by paper+repo; repo argparse defaults differ from paper Table IV (lr 1e-4 vs 5e-4,
   epochs 1 vs 20). MSE is not accuracy; the gap is not purely numerical error.
3. **Only 3 seeds** in the championship (power is limited); 4 horizons are correlated.
4. **Simplified LLM-side baselines** (TimeCMA/Qwen/CALF are informed simplifications, not the
   papers' exact implementations).
5. **Regional (US-Region) part not reproduced** — author artifact unavailable.
6. **2021 anomaly excluded** — the Test window (2016-10 → 2020-06) avoids the 2021 high-ILI
   hallucination peak; peak metrics exclude it by design (`TRACK_C_COVID_PERIOD_ANALYSIS.md`).
7. Champion claim is **contract-specific** (this strict 966-row Test contract), not a global
   statement of model superiority.

## 4. What is deliberately NOT in the report / 报告刻意不包含

- Any custom peak threshold — literature criterion only (PTE≤1wk & PIE≤25%).
- Any scheduler-variant comparison — only the unified paper-vs-ours pair is shown.
- A-track vs B-track cross-comparisons (different data/seeds/convention).
- Superseded 1025-row-era numbers (except as labeled historical background).
