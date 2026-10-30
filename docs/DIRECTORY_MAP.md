# Directory Map (Publication Version)

> **中文**：本仓库目录结构说明。核心原则：**仓库本身即发表物**——最小文件集合承载完整复现链。

## Top-Level

| Path | Purpose | Status |
|------|---------|--------|
| `reproduce_all.py` | One-click reproduction entry (7 stages) | **START HERE** |
| `README.md` | English-led + Chinese overview | Publication |
| `START_HERE.md` | Quick-start guide | Publication |
| `LICENSE` | MIT License | Publication |
| `requirements.txt` | Locked Python dependencies | Publication |
| `CITATION.cff` | Machine-readable citation | Publication |
| `CURRENT_OFFICIAL_REPORT.txt` | Authoritative report SHA256 record | Keep |
| `HPC_GUIDE.md` | HPC training/evaluation guide | Keep |
| `final_test_analysis_dataset.csv` | 966-row official dataset (mirror) | Keep |
| `test_eval_download.tar.gz` | 8-model per-cell predictions (packaged) | Keep |

## Data & Evidence (all preserved)

| Path | Purpose |
|------|---------|
| `data/` | Official 966-row dataset, scaler, frozen predictions |
| `checkpoints/` | Trained model checkpoints (best_miflu_L*.pth) |
| `results/v3_clean/` | Frozen predictions, peak criteria, figures |
| `hpc_results/official_repo_reproduction_20261006/` | Training logs + authoritative tables |
| `hpc_results/checkpoints/` | HPC-trained checkpoints |
| `audit_20260930/` | Audit evidence (frozen) |
| `rerun_20261006/` | Re-verification evidence |
| `recovery/author_repo/` | Author's original code + text embeddings |

## Scripts & Tests

| Path | Purpose |
|------|---------|
| `scripts/` | Reproduction chain scripts (~111 files) |
| `tests/` | Regression test suite (342 cases) |
| `reproduce_all.py` | Orchestrator: score → tables → report |

## Presentation

| Path | Purpose |
|------|---------|
| `paper_tables/` | Flat copies of authoritative TRACK_C tables |
| `reports/concise_final/` | Authoritative report (DOCX/PDF/MD) |
| `docs/GLOSSARY.md` | Terminology |
| `docs/EVIDENCE_INDEX.md` | Evidence pointer index |
| `docs/protocol_freeze/` | SHA-anchored protocol freeze docs |
| `handoff/` | Compact handoff package builder |
