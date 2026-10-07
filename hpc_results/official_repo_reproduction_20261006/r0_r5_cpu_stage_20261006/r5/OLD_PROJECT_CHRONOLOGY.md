# OLD PROJECT — Chronology

Read-only reconstruction. Ordering is built from **file mtimes** (filesystem-proven) and **ledger/UTC stamps** inside evidence files. No file was modified.

## 0. The hard boundary

> **The author's official repository was cloned on 2026-09-24 09:54:29 +0800** — from `https://github.com/Jmoon3108/MIFlu.git`, HEAD `6ed210150b8819313947cf607eb1821c87b1bee3`.
> Evidence: `recovery/author_repo/.git/logs/HEAD` line 1 (`"clone: from https://github.com/Jmoon3108/MIFlu.git"`), working tree mtimes on `recovery/author_repo/models/` = 2026-09-24 09:54 (filesystem-verified).

**Everything at or before 2026-09-22 is the historical self-built project ("Historical Track B"). Everything from 2026-09-24 on belongs to the official-repository lineage.** (This matches `hpc_results/official_repo_reproduction_20261006/postrun_audit_20261006/EXPERIMENT_AND_REPOSITORY_LINEAGE.md` §0-1.)

---

## 1. Ordered timeline (mtime / evidence order)

| # | Date (Asia/HK, filesystem or ledger) | Stage / artefact | Evidence | Pre-2026-09-24? |
|---|---|---|---|---|
| 1 | 2026-06-29 … 2026-07-22 | Reference papers collected (`reference_papers/MIFlu_Large_Language_…pdf`, ChatTime, etc.) | dir mtimes | YES |
| 2 | 2026-07-16 / 2026-07-18 | **July-2026 dataset snapshot** written: `data/raw/us_region_raw.csv` (07-16), `data/raw/national_illness_raw.csv` (07-18, 1025 rows) | mtimes | YES |
| 3 | 2026-08-05 … 2026-08-17 | **B1 — self-built MIFlu implementation.** `analysis/` scripts, `scripts/miflu_model.py`, dual-track configs; 1025-row checkpoints `hpc_results/checkpoints/best_miflu_L{24,36,48,60}.pth` (2026-08-17) | `EXPERIMENT_AND_REPOSITORY_LINEAGE.md` §1.B1 | YES |
| 4 | 2026-08-17 … 2026-08-28 | **Early paper-protocol runs.** `hpc_results/data/` result tables (0817), `paper_exact` MIFlu runs, `control966/` (2026-08-28) | mtimes; `results_miflu_paper_protocol_table_20260817_*.csv` | YES |
| 5 | 2026-08-28 19:20 | **Author-966 data file created:** `data/raw/national_illness_raw_paper_exact.csv` (966 rows) — exists before the clone, sourced from the paper/TSLib, not from the author repo | mtime; `REPOSITORY_PROVENANCE.md` §3 | YES |
| 6 | 2026-09-01 … 2026-09-07 | **`results/ili/` — own-MIFlu journal-evidence track.** `journal_evidence/{full, gated_inject, no_lora_multi, no_multi, full__adamw_cosine, full__earlystop, full__huber_clip}`; `National_Table_V_summary` | dir/file mtimes (09-02 … 09-07) | YES |
| 7 | 2026-09-14 18:27 | `MIFlu_innovation_plan_v2.md` | mtime | YES |
| 8 | 2026-09-15 02:14 → 22:48 | **`results/innovation/` — v2 screening (superseded precursor).** `registry.csv` (02:14) → selection freeze `frozen_winners.json` champion = **nlinear** (22:47) → `freeze_audit.json` (22:48) | mtimes; `frozen_utc 2026-09-15T14:47:32Z` / `T14:48:28Z` | YES |
| 9 | 2026-09-15 14:57:10Z | **v2 one-time Test** `final_nlinear_20260915T145710Z` (52 cells) | `test_evaluations/ONE_TIME_TEST_ACCESS_RECEIPT.json` (`receipt_created_utc`), `final_audit/one_time_test_integrity.json` | YES |
| 10 | 2026-09-16 01:30–02:02 | **`results/innovation/final/`** v2 final report, stats, manuscript drafts | mtimes | YES |
| 11 | 2026-09-17 23:10 | **`results/v3_clean/` — clean-v3 reset & preregistration.** `clean_reset_report.json`, `paper_aligned_selection_rule.json`, `complete_experiment_matrix.csv` | mtimes | YES |
| 12 | 2026-09-18 … 2026-09-19 18:40 | **Wave-1 gates + frozen source snapshot.** gate jobs 569016/570452/570846/571800/571855; `results/innovation/source_snapshot/` (2026-09-19 18:40, as-run code) | gate reports; `source_snapshot_manifest.json` | YES |
| 13 | 2026-09-19 23:54 … 2026-09-20 | **Wave-1 execution (580 rows)** via `wave1_controller_v319.sh` | `results/v3_clean/analysis/analysis_dataset.csv` (2026-09-20 15:21) | YES |
| 14 | 2026-09-20 15:21 | **Wave-1 analysis produced:** `analysis_dataset.csv`, `model_ranking.csv`, `primary_summary_statistics.csv`, `baseline_comparison.csv`, `ablation_effects.csv` | mtimes | YES |
| 15 | 2026-09-21 06:54 | `selection_outcome.json` — champion `gpt2_miflu` (0.771), runner `nlinear` (1.070) | mtime | YES |
| 16 | 2026-09-21 05:36 → 13:50 | **Final one-time Test/Holdout (84 runs).** driver jobs 577227–577388; `final_test_metrics.json` (13:49); `test_eval_download.tar.gz` (13:40) | `test_eval_ledger.jsonl`; `final_test_artifact_manifest.json` | YES |
| 17 | 2026-09-21 17:16 | Chinese report markdown `MIFlu_非LLM与LLM流感预测最终报告_中文版.md` | mtime | YES |
| 18 | **2026-09-22 02:24** | **`MIFlu_非LLM与LLM流感预测最终报告_中文版.docx`** (the Chinese final report) | mtime | YES |
| 19 | **2026-09-24 09:54:29** | **AUTHOR OFFICIAL REPO CLONED** | `recovery/author_repo/.git/logs/HEAD`; `EXPERIMENT_AND_REPOSITORY_LINEAGE.md` §0 | **boundary** |
| 20 | 2026-09-24 11:22–11:35 | `scripts/configs.py` gains `DATA_PROFILES` (`author_966` adapter); `scripts/textual_embedder.py` edited; author scalers written | mtimes; `configs.py:90-112` | no |
| 21 | 2026-09-24 23:43 | `recovery/stage5/` frozen Stage-5 protocol, run matrix | mtimes | no |
| 22 | 2026-09-25 00:13 | `scripts/train_naive_966.py` (A2 deterministic baselines; `ref = ts+s-52`) | mtime | no |
| 23 | 2026-09-25 16:13:29Z | **A2 checkpoints locked** (36) — before any Test inference | `stage5_a2/scoring/CHECKPOINT_LOCK_first_20260925T161329Z.json` | no |
| 24 | 2026-09-25 22:36 → 2026-09-26 00:25 | `scripts/train_nlinear_966.py`; A2 36 fits + 8 baselines run; recompute PASS (4.44e-16) | `stage5_a2/logs/run_ledger.csv`; `per_run/miflu/training_miflu_log_20260925_*.txt` | no |
| 25 | 2026-09-26 17:48 → 21:28 | `scripts/train_backbone_966.py`; **Stage 6 eight-model author-966** (jobs 587075–587373; A0 GPU 587068/587091), 116 artefacts | `stage6/ledgers/run_ledger.csv`; `results_report_zh.md` | no |
| 26 | 2026-09-30 16:36 | `audit_20260930/` independent audit | mtimes | no |
| 27 | 2026-10-05 / 2026-10-06 | **Official-repository reproduction / A0-R / A1 / F1** (`hpc_results/official_repo_reproduction_20261006/`) | job logs 606357–607691 | no |

---

## 2. Ledger / UTC cross-checks

| Stage | Ledger stamp | Source |
|---|---|---|
| innovation v2 | `2026-09-15T14:47:32Z` (freeze), `14:57:10Z` (Test receipt) | `frozen_winners.json`, `ONE_TIME_TEST_ACCESS_RECEIPT.json` |
| clean-v3 Wave-1 | `2026-09-20T06:10:00Z` protocol; accept 580 rows | `frozen_analysis_protocol.json` |
| clean-v3 Test | runs started `2026-09-21T05:00:21Z` (gpt2_miflu L24 s42); jobs 577227–577388 | `test_eval_ledger.jsonl`, `test_manifest.json` |
| A2 (author-966) | checkpoint lock `2026-09-25T16:13:29Z`; fits from `2026-09-25 22:39` HK | `CHECKPOINT_LOCK*.json`, `per_run/miflu/*` |
| Stage 6 | report generated `2026-09-26 21:30` HK (=13:30 UTC) | `recovery/stage6/results_report_zh.md` |
| Author clone | `2026-09-24 09:54:29 +0800` | `recovery/author_repo/.git/logs/HEAD` |

---

## 3. Ordering conclusion

1. The complete historical 4-vs-4 story (self-built MIFlu, Wave-1 validation ranking, frozen 3-model set, one-time Test/Holdout, deferred controls, and the Chinese DOCX) **finished 2026-09-22**, which is **two days BEFORE the author repo was pulled (2026-09-24)**.
2. Therefore **the entire historical comparison predates the author repository.** It cannot be "an author-repo reproduction"; it used the project's own `scripts/miflu_model.py` and own re-implementations of DLinear/NLinear/PatchTST/iTransformer/Time-LLM/CALF/TimeCMA.
3. The `author_966` 8-model work (`hpc_results/stage5_a2`, `hpc_results/stage6`) is **post-clone (2026-09-25/26)** and, although the *data* vintage predates the clone (the 966-row CSV existed 2026-08-28), the *protocol/code* that ran on it is post-clone.
4. Git history is unusable for ordering (single commit `1f6563f`, per `REPOSITORY_PROVENANCE.md` §1); all ordering above rests on filesystem mtimes and embedded ledger stamps.