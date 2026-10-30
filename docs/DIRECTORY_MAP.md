# DIRECTORY MAP — 目录地图（读什么 / 忽略什么）

> 每个顶层目录/文件是什么、是否 canonical、要不要看。重构迁移对照表也在本文件末尾。

## 1. 顶层目录 Top-level directories

| Directory | What it is | Status | Read? |
|-----------|-----------|--------|-------|
| `data/` | Datasets + scalers. `data/raw/national_illness_raw_paper_exact.csv` (966 rows) = author data in project schema; `data/raw/national_illness_raw.csv` (1025 rows) = different vintage snapshot | ✅ canonical | Yes (small) |
| `docs/` | Guides: glossary, this map, evidence index, status, roadmap, paper & author-repo explained | ✅ canonical | **Start here** |
| `reports/concise_final/` | ★ **The authoritative final report** (DOCX) + changelog + render audit + SHA + source manifest | ✅ canonical | Yes |
| `results/v3_clean/analysis/peak_criteria/` | ★ **The current 8-model benchmark**: frozen contract, per-model/per-event results, PTE/PIE peak audit, COVID/temporal audits, the 12 MIFlu prediction CSVs, figures | ✅ canonical | Yes |
| `hpc_results/official_repo_reproduction_20261006/` | Paper-reproduction evidence: R1-C 24 fits, verdicts, paper-gap analysis, repository provenance | ✅ canonical (evidence) | Selectively |
| `audit_20260930/` | Independent audit (report + recomputation scripts + artifacts) | ✅ canonical (evidence) | Selectively |
| `recovery/` | Recovery-stage evidence: `author_repo/` (author's GitHub clone), `data_identity_report.md`, `dataset_manifest.json`, stage logs | ✅ canonical (evidence) | Selectively |
| `scripts/` | Runnable Python/shell code (report builders, audits, QA) | ✅ canonical | Yes (for development) |
| `tests/` | Test suite (incl. leakage audit tests) | ✅ canonical | As needed |
| `hpc_scripts/` | SLURM/HPC job scripts used for the GPU/CPU runs | 📦 historical infra | Only if re-running HPC |
| `slurm/` | SLURM logs/configs | 📦 historical infra | No |
| `analysis/` | Early analysis scripts (providers/moe explorations) | 📦 historical | No |
| `audit_20260930/` | (above) | | |
| `rerun_20261006/` | Rerun staging area | 📦 historical | No |
| `archive/` | Archived prompts & planning drafts (moved from root) | 🗄 archive | No |
| `hpc_results/` (other subdirs: `stage5_a2/`, `stage6/`, `hpc_a1*`, `r0_r5_cpu_stage_20261006/`, `r1_*`) | Earlier reproduction stages & HPC logs | 📦 historical/evidence | Only when tracing provenance |
| `results/` (other subdirs: `v2_legacy_archive/`, `v3_superseded_archive/`, `innovation/`, `ili/`, `v3_clean/` rest) | Earlier experiment outputs (superseded or supplementary) | 📦 historical/evidence | No (except `v3_clean/analysis/peak_criteria/`) |
| `reference_papers/` | The paper PDF/MD (gitignored) | ✅ reference | Yes |

## 2. 顶层文件 Top-level files (after reorg)

| File | What it is | Read? |
|------|-----------|-------|
| `README.md` | Project overview & navigation | Yes |
| `START_HERE.md` | Zero-foundation entry point | **Read first** |
| `CURRENT_OFFICIAL_REPORT.txt` | Pointer + SHA of the authoritative report | Yes |
| `HPC_GUIDE.md` | HPC run guide (4-hour budget interpretation etc.) | If re-running HPC |
| `MIFlu_innovation_plan_v2.md`, `MIFlu_innovation_plan_v3.md` | Innovation plan drafts (frozen; scripts read & hash them) | For Phase C |
| `MIFlu_导师五大疑问_回复报告.md/.docx/.pdf` | Tutor five-question report (frozen deliverable; generator scripts read it) | If asked about tutor Q&A |

> ⚠️ The last three groups stay at repo root **on purpose**: multiple scripts read/hash them at
> those exact paths (see `docs/REORG_MIGRATION_NOTE.md`). Everything else was moved into
> `docs/` and `archive/`.

## 3. What to ignore / 可以完全忽略

- `results/v2_legacy_archive/`, `results/v3_superseded_archive/`, `results/ili/` — superseded experiments
- `hpc_results/stage5_a2/`, `stage6/`, `hpc_a1*/` — earlier HPC stages
- `archive/`, `rerun_20261006/`, `analysis/`, `slurm/` — historical
- All `*.pyc`, `__pycache__/`, `*.tgz`, `s1es_runs/`, `r1c_logs/`

## 4. 重构迁移对照表 / Reorg migration map (root → new location)

**→ `docs/paper_and_analysis/`**
`MIFlu_论文完整解析与答辩解答.md` · `MIFlu_paper_analysis_and_defense_EN.md` ·
`MIFlu_paper_analysis_and_defense_ZH.md` · `MIFlu_paper_analysis_and_defense_ZH.pdf` ·
`MIFlu_paper.md` · `Rethinking_the_Role_of_LLMs_in_TSF.md` · `Related_Work_with_Code.md` ·
`导师_5大疑问_零基础解答报告.md` · `导师五大疑问_零基础解答报告_最终版.md` ·
`Advisor_Questions_Resolution_Report.md`

**→ `docs/planning/`**
`Innovation-Proof.md` · `Innovation_HPC_Run.md` · `plan.md` · `PROJECT_STATUS.md`(历史版) ·
`REPRODUCIBILITY.md` · `EE4080_MIFlu_Research_Recovery_Plan.md` · `EE4080_MIFlu_Research_Recovery_Plan.pdf`

**→ `archive/prompts/`**
`CodeBuddy_Authorization_and_Final_Execution_ZH.md` · `CodeBuddy_MIFlu_Complete_Recovery_Plan_ZH.md` ·
`CodeBuddy_MIFlu_Current_Progress_Audit_Prompt.md` · `CodeBuddy_MIFlu_Master_Execution_Prompt.md` ·
`CodeBuddy_MIFlu_New_Chat_Handoff_ZH.md` · `CodeBuddy_MIFlu_Recovery_Prompt.md` ·
`CodeBuddy_MIFlu_Stage3_Execution_Prompt.md` · `CodeBuddy_MIFlu_Stage4_Execution_Prompt.md` ·
`CodeBuddy_MIFlu_Stage5_Execution_Prompt_ZH.md` · `ChatTime.md` · `CLEANUP_PLAN.md` ·
`CHANGELOG_2026-09-02_导师报告更新.md`

**→ `archive/planning_docx/`**
`58324980_CHAN_Sing_Yeung_Project_Summary_and_Planning_Chart_202627A.docx/.pdf` 及其
`_BEFORE_BEN_FINAL` / `_BEFORE_DATA_SOURCE_CORRECTION` / `_BEFORE_HYPHEN_EDIT` /
`_BEFORE_SCHEDULE_UPDATE` / `_OLD` 五个变体

**留在根目录（脚本按路径读取/哈希，勿移动）**
`HPC_GUIDE.md` · `MIFlu_innovation_plan_v2.md` · `MIFlu_innovation_plan_v3.md` ·
`MIFlu_导师五大疑问_回复报告.md/.docx/.pdf`
