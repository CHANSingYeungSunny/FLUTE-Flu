# FINAL DOCX UPDATE PLAN

Generated 2026-10-06.

## 1. The rule that governs everything here

| | |
|---|---|
| **original** | `results/v3_clean/analysis/reports/MIFlu_非LLM与LLM流感预测最终报告_中文版.docx` (SHA-256 `9c573f48fb65e590c7973223d6cb5e0ab74e2dfa4f6df11ec936f980a6b50ead`) |
| **this stage** | **read-only**. The original is **not modified, not moved, not renamed, not converted.** |
| **future output** | `MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库替换版.docx` — a **new** file, produced in the same directory |

## 2. The five preconditions for generating the new DOCX

**None is satisfied yet.** The new DOCX may be generated only when:

| # | Precondition | Status |
|---|---|---|
| 1 | Tier-1 reproduction has a documented verdict | ⚠️ the R1-B **verdict** exists (`READY_TO_PILOT`) but **no result** — the pilot has not run |
| 2 | the replacement compatibility verdict is complete | ✅ `MIFLU_RETRAIN_ON_OLD_CONTRACT_REQUIRED` |
| 3 | the controlled replacement experiment has completed | ❌ not started |
| 4 | affected leakage results have been corrected | ✅ the leakage audit is complete and the historical track is **unaffected** |
| 5 | the required metrics and figures exist | ❌ the new MIFlu metrics and figures do not exist |

**Therefore: no DOCX is generated now.** Doing so would require fabricating the very numbers
the report is about.

## 3. The report's actual structure (extracted read-only)

**228 non-empty paragraphs · 9 sections · 5 tables · 12 images.**

| # | Section |
|---|---|
| 一 | 这份报告如何评估模型性能（零基础导读） |
| 二 | 研究方法与冻结选型规则 |
| 三 | Wave-1 验证阶段：8 个架构的筛选 |
| 四 | 机制发现：LLM 的"创新点"到底有没有用 |
| 五 | 一次性 Test/Holdout 最终评估 |
| 六 | 统计方法与确认性检验 |
| 七 | 最终工作流与证据完整性 |
| 八 | 诚实结论 |
| 九 | 局限性 |

**Figures**: I (workflow overview), A (Wave-1 validation ranking of 8), B (final
Test/Holdout of 3 frozen models), C (validation vs Test), D (Test MSE/MAE by horizon),
E (peak-timing / peak-intensity error), F (prediction vs ground truth), G (deferred
controls), H (final workflow).

**The report's headline, quoted**: the frozen selection rule made `gpt2_miflu` the Wave-1
validation winner (**avg MSE 4L = 0.771**), but the one-time Test/Holdout **reversed** it:
**NLinear 2.739 [2.731, 2.747] · GPT-2 MIFlu 3.051 [2.922, 3.179] · Seasonal-Naive 4.279**.

## 4. What the new edition must present, separately

1. the original historical results (unchanged);
2. the paper-reproduction verdict;
3. the official-repository-based MIFlu identity;
4. the **transferred** historical-contract MIFlu identity, if needed;
5. old-versus-new MIFlu results;
6. old and new validation rankings;
7. old and new Test/Holdout results;
8. LLM-side and non-LLM-side summaries, **labelled descriptive**;
9. F1 as a supplementary corrected-contract pilot;
10. the seasonal-naive leakage correction **and the fact that the historical report is unaffected by it**;
11. compatibility limitations;
12. unreproduced paper results;
13. computational-cost changes;
14. the final answer to whether replacing MIFlu changes the historical conclusion.

## 5. What must never happen in the new edition

| Prohibited |
|---|
| editing, renaming or converting the original file |
| overwriting it in place |
| presenting the transferred run as a paper reproduction |
| presenting the group mean as the sole conclusion, or the best-in-group as the sole conclusion |
| publishing a ranking that mixes the 966-row and 1025-row tracks |
| populating any cell with a number that does not yet exist |
