# START HERE — MLFlu 项目零基础入口

> **How to use / 用法**：10 分钟从上读到下即可接手本项目。English body; key verdicts &
> constraints also in Chinese. 本文件是唯一入口，其余一切细节见 `docs/`。

---

## 1. What is this project? / 这个项目是什么？

We reproduce **MIFlu** (*Large Language Model-Based Multimodal Influenza Forecasting Scheme*,
Moon et al., **IEEE JBHI 2025**, DOI 10.1109/JBHI.2025.3561214) — a model that fuses a **text
prompt** (dataset statistics + expert knowledge) with **time-series ILI data** through two
LLMs (a frozen GPT-2 text embedder + a GPT-2-with-LoRA forecasting head) — and benchmark it
against 7 other models on the author's **966-row US National-Illness** dataset.
Goal (final-year project): **innovate on top of MIFlu** and target a top-tier journal.

> 中文：复现 IEEE JBHI 2025 的 MIFlu（文本+时序双模态流感预测，两个 GPT-2），在作者 966 行
> National-Illness 数据上与另外 7 个模型做严格基准对比；最终目标是在 MIFlu 之上创新并发表顶刊。

## 2. Where we are today / 当前进度

**Done**: frozen 8-model benchmark (4 non-LLM: NLinear, DLinear, PatchTST, iTransformer;
4 LLM-side: MIFlu, TimeCMA-LLM, Qwen-Time-LLM, CALF-LLM) under a strict 966-row contract
(3 seeds × 4 horizons, one-time Test, single canonical scorer) + paper-reproduction study
(R1-C) + peak-accuracy audit (PTE/PIE) + independent audit + tutor Q&A.
**Result**: MIFlu is the **Test-MSE champion** but paper reproduction is only **PARTIAL**.
**Now**: optimize this benchmark (via ChatGPT), then add models, then innovate.

> 中文：8 模型冻结基准、论文复现、峰值审计、独立审计、导师问答均已完成；MIFlu 是 Test MSE 冠军，
> 但论文复现只是部分复现。下一步：先优化现有基准，再扩模型，再创新。

## 3. The seven numbers/rules you must not get wrong / 不可出错的数字与规则

| # | Item | Value |
|---|------|-------|
| 1 | Paper target (Table V, avg MSE over L=24/36/48/60) | **1.4355** |
| 2 | Our MIFlu final Test `average_MSE_4L` | **1.8652** (SD 0.0916) |
| 3 | Reproduction verdict | **PARTIAL_REPRODUCTION** (+29.9%; 5% tolerance not met) |
| 4 | Championship | MIFlu 1.8652 (champion, best non-LLM) > NLinear 2.0495 > … ; best LLM-side = TimeCMA-LLM 2.6700 |
| 5 | Group means | non-LLM **3.0756** < LLM-side **3.8175** (lower = better) |
| 6 | Peak accuracy (literature PTE/PIE) | NLinear **36/36** peak champion; MIFlu **15/36** |
| 7 | Official dataset | author 966 rows, sha256 **2a96dfed…ebfe5** (github.com/Jmoon3108/MIFlu) |

### The seven hard constraints / 七条硬约束（违反即产生错误结论）

1. **A-track vs B-track scores are NEVER comparable.**
   A-track = author 966 rows / 3 seeds (42,43,44) / z-space MSE (MIFlu 2.0415). B-track =
   July-2026 1025-row snapshot / 10 seeds (42–51) (gpt2_miflu 0.7709). Different data vintage,
   different seed count, different convention. The paper's 1.4355 is a *third* convention
   (10 repetitions + LoRA + paper scaling). **Any quoted score must state track + seeds + space.**
   > A 轨与 B 轨数字绝不可比（数据、种子数、口径均不同）；引用必须写明轨道/种子数/空间口径。
2. **The text-path mechanism question is UNRESOLVED — report it as such, never pick a side.**
   GPU replay shows non-zero text-embedder gradients; CPU replay measured exactly zero effect.
   Ablation evidence points both ways (A-track `notext` 1.9222 beats full 2.0415; B-track
   10-seed `gpt2_miflu` ranks #1). **Do NOT claim the text path helps, and do NOT claim it is
   useless.**
   > 文本通路机制矛盾未决，两侧证据相反；不得宣称有效或无效。
3. **PTE/PIE uses the literature criterion ONLY: PTE ≤ 1 week AND PIE ≤ 25%**
   (Kramer & Shaman 2019, DOI 10.1371/journal.pcbi.1006742). A peak is a hit only when both
   conditions hold simultaneously, judged per peak (never on an average).
   > 峰值判定只用文献标准（PTE≤1周且PIE≤25%），按峰逐一判定。
4. **Paper reproduction is one unified pair: 1.4355 (paper) ↔ 1.8652 (our MIFlu final Test),
   +29.9%, PARTIAL_REPRODUCTION.** No other variant comparisons appear in the report.
   > 论文复现只呈现这一组统一对比。
5. **Exactly one authoritative report**: `reports/concise_final/MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库966行严格测试冠军版_精简终版.docx`
   (SHA recorded in `CURRENT_OFFICIAL_REPORT.txt`). Older reports are superseded/evidence-only.
   > 权威报告唯一，以 CURRENT_OFFICIAL_REPORT.txt 为准。
6. **Dataset identity matters**: the official data is the author's 966-row
   `national_illness.csv` (sha 2a96dfed…). `data/raw/national_illness_raw.csv` (1025 rows) is a
   DIFFERENT vintage (CDC-revised values from MMWR 2016w40) — never mix the two. The author CSV's
   `date` column is a synthetic 7-day index, not real CDC weeks.
   > 正式数据=作者966行；1025行快照是另一 vintage，绝不可混用；date 列是合成标签。
7. **MSE ≠ accuracy.** MSE champion (MIFlu) and peak champion (NLinear) are different models;
   report them separately.
   > MSE 冠军与峰值冠军不同，分开报告。

## 4. Reading order / 阅读顺序

1. `START_HERE.md`（本文件）
2. `docs/PROJECT_STATUS.md` — current results & verdicts
3. `docs/01_paper/PAPER_EXPLAINED.md` — how MIFlu works
4. `docs/01_paper/AUTHOR_REPO_EXPLAINED.md` — the author's code layout
5. `docs/GLOSSARY.md` → `docs/DIRECTORY_MAP.md` → `docs/EVIDENCE_INDEX.md`
6. `docs/ROADMAP.md` — what to do next
7. The authoritative report (DOCX above; Markdown mirror in the handoff package)

## 5. Repository in one screen / 仓库一屏看懂

| Path | What it is |
|------|-----------|
| `data/` | datasets + scalers (official 966-row copy + 1025-row snapshot) |
| `recovery/author_repo/` | the author's GitHub repo clone (read-only reference) |
| `results/v3_clean/analysis/peak_criteria/` | ★ current 8-model benchmark + PTE/PIE peak audit |
| `reports/concise_final/` | ★ the authoritative DOCX + its manifest/SHA |
| `hpc_results/official_repo_reproduction_20261006/` | paper-reproduction (R1-C) evidence |
| `audit_20260930/` | independent audit report + recomputation scripts |
| `scripts/`, `tests/` | runnable code |
| `docs/` | guides, glossary, map, evidence index, roadmap |
| `archive/` | historical prompts & planning drafts (safe to ignore) |

Full detail: `docs/DIRECTORY_MAP.md`.

## 6. Next steps / 下一步

See `docs/ROADMAP.md`: **Phase A** optimize the current benchmark → **Phase B** add more
models → **Phase C** innovate on top of MIFlu (publication target).
