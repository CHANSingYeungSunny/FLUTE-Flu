# REORG MIGRATION NOTE — 2026-10-30 根目录重组说明

> On 2026-10-30 the repo root was de-cluttered: 36 loose planning/report files were moved into
> `docs/` and `archive/` (via `git mv`, history preserved). **No data, results, scripts or
> hash-frozen evidence were touched.** This note is the old→new resolution key.

## 1. Where things moved / 迁移对照

See the full table in [`DIRECTORY_MAP.md`](DIRECTORY_MAP.md) §4. Summary:
- `docs/paper_and_analysis/` — paper analyses, tutor reports, related-work notes (10 files)
- `docs/planning/` — planning/innovation/reproducibility docs (7 files, incl. the historical
  root `PROJECT_STATUS.md`; the CURRENT status is `docs/PROJECT_STATUS.md`)
- `archive/prompts/` — agent prompts, session notes, changelogs (12 files)
- `archive/planning_docx/` — project-summary DOCX/PDF drafts (7 files)

## 2. Why 6 files stayed at root / 为什么 6 个文件留在根目录

These are read/hashed **by path** from scripts; moving them would break code, and the plan
forbids modifying scripts or frozen evidence:

| File | Read by |
|------|---------|
| `MIFlu_导师五大疑问_回复报告.md` / `.docx` | `scripts/build_report_docx.py:20-21`, `scripts/md_to_docx.py:521-531` (`find_report()` scans root only), `scripts/verify_report_parity.py:42` |
| `MIFlu_innovation_plan_v2.md` | `scripts/v3_clean/build_clean_v3_prereg.py:58`, `scripts/v3/build_preregistration.py:64,142`, `scripts/innovation/paths.py:60`, `scripts/innovation/source_snapshot.py:56`, `scripts/audit_original_repo_integrity.py:89,104`, `hpc_scripts/autonomous/audit_recompute.py:89` |
| `MIFlu_innovation_plan_v3.md` | `scripts/v3/build_protocol_correction.py:105`, `build_prereg_status_and_reconcile.py:100`, `build_preregistration.py:560`, `build_phase06.py:32`, `build_phase05b.py:491`, `build_phase05.py:114` |
| `HPC_GUIDE.md` | `scripts/v3/build_screening_freeze.py:50,147,165` (reads + SHA), `hpc_scripts/autonomous/audit_recompute.py:90` |

## 3. Stale absolute paths in FROZEN evidence — do NOT edit them / 冻结证据里的旧绝对路径（勿改）

These historical records embed the pre-reorg absolute paths. Editing them would falsify frozen
evidence; the correct handling is this note. If a tool ever needs to re-locate these files, use
the mapping above.

| Recorded absolute path | Recorded in (frozen) | File now lives at |
|------------------------|----------------------|-------------------|
| `C:\Users\Asus\Desktop\FYP code\MLFlu\MIFlu_innovation_plan_v2.md` | `results/innovation/runs/*/plan_sha256.json` (21+), `results/innovation/audit/plan_sha256.json` | **unchanged** (stayed at root) |
| `C:\Users\Asus\Desktop\FYP code\MLFlu\HPC_GUIDE.md` | `results/innovation/hpc_deployment_verification/hpc_guide_compliance.{json,md}` | **unchanged** (stayed at root) |
| `C:\Users\Asus\Desktop\FYP code\MLFlu\MIFlu_paper.md` | `hpc_results/official_repo_reproduction_20261006/r0_r5_cpu_stage_20261006/paper/PAPER_SOURCE_IDENTITY_AND_CROSSCHECK.json:49` | `docs/paper_and_analysis/MIFlu_paper.md` |
| `…\MIFlu_导师五大疑问_回复报告.md` (root) | generator scripts' `SRC`/`DST` constants | **unchanged** (stayed at root) |
| basenames inside `results/v3_clean/analysis/final_cleanup_audit/*` | evidence pack (project-summary docx) | `archive/planning_docx/` |

## 4. Textual links fixed in living docs / 已修正的文档链接

`docs/Tutor_QA_Draft_2026-08-17.md`, `docs/scaler_convention_supplement.md`,
`docs/ILI_FOUR_INDICATORS.md`, `docs/REGIONAL_TABLE_VI_GAP_ANALYSIS.md` (pointing to
`MIFlu_paper.md` / tutor reports). `docs/full_repo_audit_report.md` received a banner only
(its tree is a 2026-08-16 audit snapshot, intentionally unedited).

**Not edited (by design)**: `MIFlu_导师五大疑问_回复报告.md` (md↔docx parity check depends on
its exact content), anything under `results/`, `hpc_results/`, `recovery/`, `audit_20260930/`,
`scripts/`, `tests/` (frozen evidence / code), and archived prompts (historical).
