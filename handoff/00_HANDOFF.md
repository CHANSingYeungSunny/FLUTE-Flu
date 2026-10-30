# 00 — HANDOFF BRIEF / 项目总交接书

> **For the receiving AI (e.g. ChatGPT) with zero prior context.** Read this file completely
> first; it is the single source of orientation. English body; key verdicts and constraints are
> bilingual. **Any number you quote must satisfy the seven hard constraints in §4.**
>
> 给接手 AI 的总交接书：先完整读完本文件，再按 §6 顺序读包内其他文件。引用任何数字前必读 §4 硬约束。

---

## 0. Paste-ready opening prompt / 可直接粘贴的开场白

> I am reproducing and extending **MIFlu** (Moon et al., IEEE JBHI 2025,
> DOI 10.1109/JBHI.2025.3561214), an LLM-based multimodal influenza forecasting model.
> This zip is a complete handoff of my project (MLFlu). Please first read `00_HANDOFF.md`
> fully, then `07_docs/PROJECT_STATUS.md` and `01_paper/PAPER_EXPLAINED.md`. The seven hard
> constraints in §4 of the handoff are non-negotiable — especially: never compare the
> 966-row track with the 1025-row track numbers; the text-path mechanism question is
> **unresolved** and must stay so; peak accuracy uses the literature criterion only
> (PTE ≤ 1 week & PIE ≤ 25%); the paper comparison is the single unified pair
> 1.4355 ↔ 1.8652. Current phase: **optimize the existing 8-model benchmark first**
> (Phase A), then add models (Phase B), then innovate on top of MIFlu (Phase C), targeting
> a top-tier journal. Start by assessing Phase A and proposing a concrete work plan.

---

## 1. Project identity / 项目身份

| Item | Value |
|------|-------|
| Project | **MLFlu** — reproduction + benchmark + planned innovation on MIFlu |
| Paper | *MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme*, Moon, Shim, Kim, Hwang — **IEEE J. Biomed. Health Inform., Vol. 29, No. 10, Oct 2025** (DOI 10.1109/JBHI.2025.3561214) |
| Author code | `https://github.com/Jmoon3108/MIFlu` (verified non-fork; included here as `02_author_repo/code/`) |
| Official data | author `national_illness.csv`, **966 rows**, 7 variables, sha256 `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5` |
| Task | National ILI forecasting: input 7 vars × 104 weeks → predict 7 vars × L weeks, L ∈ {24, 36, 48, 60} |
| Our goal | (FYP) innovate on top of MIFlu → top-tier journal |
| Current phase | **Phase A** — optimize the current 8-model benchmark |

## 2. What has been done / 已完成工作

| Workstream | Outcome |
|------------|---------|
| Paper study + author-repo study | Summaries in `01_paper/` |
| Paper reproduction (R1-C: 24 fits, 3 seeds × 4 horizons, both scheduler configs, all rc 0) | **PARTIAL_REPRODUCTION** (+29.9% vs paper) |
| Strict 966-row **8-model championship** (frozen contract, one-time Test, single canonical scorer, seeds 42/43/44) | MIFlu = Test-MSE champion |
| Peak-accuracy audit (PTE/PIE, literature criterion, 36 true peaks/model) | NLinear = peak champion (36/36); MIFlu 15/36 |
| COVID-period / temporal / variable-label / stop-rule audits | Excluded the 2021 anomaly; stop-rule sensitivity harmless |
| Independent audit (2026-09-30) | Report in `05_reproduction_audit/` |
| Authoritative report (DOCX) + QA + manifest | `04_benchmark/` (DOCX + Markdown mirror) |
| Repo restructure (docs layer + root de-clutter) | See `07_docs/DIRECTORY_MAP.md`, `07_docs/REORG_MIGRATION_NOTE.md` |

## 3. Canonical numbers / 必须记住的数字

| Item | Value |
|------|-------|
| Paper target (Table V avg MSE, L=24/36/48/60) | **1.4355** (per-L: 1.542 / 1.422 / 1.414 / 1.364) |
| Our MIFlu final Test `average_MSE_4L` | **1.8652** (SD 0.0916; MAE 0.8842) |
| Reproduction verdict | **PARTIAL_REPRODUCTION**, +29.9%, 5% band not met |
| 8-model ranking (Test avg_MSE_4L) | MIFlu 1.8652 > NLinear 2.0495 > DLinear 2.3478 > TimeCMA-LLM 2.6700 > PatchTST 3.9205 > iTransformer 3.9847 > Qwen-Time-LLM 5.2196 > CALF-LLM 5.5153 |
| Group means (4 vs 4) | non-LLM **3.0756** < LLM-side **3.8175** (MIFlu counts as LLM-side) |
| Peak hits (literature PTE/PIE) | NLinear 36/36 · DLinear 31/36 · MIFlu 15/36 · Qwen 1/36 · TimeCMA/PatchTST/iTransformer/CALF 0/36 |
| Contract | 966 rows · 676/97/193 · strict containment · Train-only scaler · z-space scorer · seeds 42/43/44 · one-time Test |

## 4. SEVEN HARD CONSTRAINTS / 七条硬约束（违反即错误结论，不可谈判）

1. **A-track vs B-track numbers are NEVER comparable.**
   A-track = author 966 rows / 3 seeds (42,43,44) / z-space MSE (MIFlu 2.0415). B-track =
   July-2026 1025-row snapshot / 10 seeds (42–51) (gpt2_miflu 0.7709). The paper's 1.4355 is a
   *third* convention (10 repetitions + LoRA + paper scaling). **Any quoted score must state
   track + seed count + space.** Never present cross-track differences as improvements.
   > A 轨与 B 轨数字绝不可比；引用必须写明轨道/种子数/空间口径；不得制造虚假改进叙事。
2. **The text-path mechanism question is UNRESOLVED — never pick a side.**
   GPU replay shows non-zero text-embedder gradients; CPU replay measured exactly zero effect.
   Ablations disagree both ways (A-track `notext` 1.9222 beats full 2.0415; B-track 10-seed
   `gpt2_miflu` ranks #1). Report as an open contradiction. Do NOT claim the text path helps,
   and do NOT claim it is useless.
   > 文本通路机制矛盾未决（GPU 梯度非零 vs CPU 效应为零）；两侧证据相反，不得擅自下结论。
3. **Peak accuracy uses the LITERATURE criterion only: PTE ≤ 1 week AND PIE ≤ 25%**
   (Kramer & Shaman 2019, DOI 10.1371/journal.pcbi.1006742). Hit only when both hold at once,
   judged per peak, never on averages.
   > 峰值判定仅用文献标准 PTE≤1周 且 PIE≤25%，按峰逐一判定。
4. **Paper comparison is one unified pair: 1.4355 (paper) ↔ 1.8652 (our MIFlu final Test),
   +29.9%, PARTIAL_REPRODUCTION.** No scheduler-variant comparisons in any report.
   > 论文对比只保留这一组统一对比，不提调度变体。
5. **Exactly one authoritative report**: `04_benchmark/MIFlu_..._精简终版.docx` (SHA in
   `04_benchmark/CURRENT_OFFICIAL_REPORT.txt`). Older reports are superseded/evidence-only.
   > 权威报告唯一，以 CURRENT_OFFICIAL_REPORT.txt 指向的 DOCX 为准。
6. **Dataset identity matters**: official data = author 966 rows (sha `2a96dfed…`). The
   1025-row snapshot (`03_data/`) is a different vintage (CDC-revised values from MMWR 2016w40)
   — never mix scores across them. The author CSV's `date` column is a synthetic 7-day index,
   not real CDC weeks.
   > 正式数据=作者966行；1025行快照不同 vintage 绝不可混比；date 列为合成标签。
7. **MSE ≠ accuracy.** MSE champion (MIFlu) and peak champion (NLinear) are different models;
   report them separately.
   > MSE 冠军与峰值冠军不同，分开报告。

## 5. Package map / 包结构

```
00_HANDOFF.md              ← you are here
01_paper/                  ← paper text (MIFlu_paper.md) + PAPER_EXPLAINED.md
02_author_repo/            ← AUTHOR_REPO_EXPLAINED.md + code/ (author's repo) + data/ (966-row csv, text_emb/)
03_data/                   ← our data dir: 966-row project copy + scalers + 1025-row snapshot (⚠ different vintage)
04_benchmark/              ← ★ current 8-model benchmark: peak_criteria/ (results + 12 prediction CSVs),
                             the authoritative DOCX + REPORT mirror + CURRENT_OFFICIAL_REPORT.txt
05_reproduction_audit/     ← R1-C reproduction evidence + paper-level verdict + independent audit + data identity
06_scripts/                ← runnable code (report builders, audits, QA, tests)
07_docs/                   ← START_HERE, GLOSSARY, DIRECTORY_MAP, EVIDENCE_INDEX, PROJECT_STATUS, ROADMAP, REORG note
```

## 6. Your task brief / 给接手 AI 的任务书

**Phase A — optimize the current benchmark (start here)**
1. Read `07_docs/PROJECT_STATUS.md` + `04_benchmark/REPORT_精简终版.md`, then audit the
   benchmark pipeline in `06_scripts/` for reproducibility gaps (unified runner? seeds?
   pinned hyperparameters? statistical tests?).
2. Design **one decisive experiment** for the text-path contradiction (identical seeds/code
   path; gradient probe + ablation). If truly undecidable, rigorously document the boundary
   conditions instead of picking a side.
3. Strengthen statistics: more seeds (5–10), paired tests on matched seed–horizon cells,
   confidence intervals; per-horizon/per-seed breakdowns.
4. Clean code: one documented entry point to reproduce the championship table; type hints;
   tests for the scorer and split/containment logic; pinned `requirements.txt`.

**Phase B — add models** (same frozen contract only; include a `notext` ablation for every
LLM-side model; report text contribution neutrally per constraint #2).

**Phase C — innovate** (prompt-knowledge study, fusion alternatives, reliability/clinical
framing) and package for submission.

## 7. Ground rules while working here / 工作规则

- **Never edit** the evidence trees (`04_benchmark/peak_criteria/`, `05_reproduction_audit/`,
  `03_data/`, anything marked frozen) — they are records. Improve code and add new evidence.
- One authoritative report at a time; regenerate via `06_scripts/build_concise_final_report.py`
  + `finalize_concise_report_qa.py` and refresh `CURRENT_OFFICIAL_REPORT.txt` if conclusions change.
- Quote numbers with track + seeds + space. MSE ≠ accuracy. Keep the unresolved contradiction
  labelled as such in every deliverable.
- The repo root also holds files that code reads by path (`HPC_GUIDE.md`,
  `MIFlu_innovation_plan_v2/v3.md`, `MIFlu_导师五大疑问_回复报告.*`) — see `07_docs/REORG_MIGRATION_NOTE.md`.

## 8. Environment / 环境

- Windows + PowerShell; Python 3.x with `python-docx 1.2.0`, `matplotlib`, `numpy`, `pandas`, `torch` (training).
- No LibreOffice / pandoc / pptx in the original environment (DOCX→MD done via
  `06_scripts/extract_docx_to_md.py`).
- HPC: CityU Burgundy cluster (SLURM); scripts under `hpc_scripts/` in the full repo.

## 9. Quick verification / 快速校验

```powershell
# official data identity (must equal 2a96dfed…)
Get-FileHash "02_author_repo\data\national_illness.csv" -Algorithm SHA256
# authoritative report identity (must match CURRENT_OFFICIAL_REPORT.txt)
Get-FileHash "04_benchmark\MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库966行严格测试冠军版_精简终版.docx" -Algorithm SHA256
```

Full hash chain: `07_docs/EVIDENCE_INDEX.md`.
