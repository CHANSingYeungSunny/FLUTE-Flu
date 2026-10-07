# FILE INTEGRITY AND NON-DELETION CONFIRMATION

Generated 2026-10-06. This document is the evidence that the append-only and
preservation rules were obeyed.

---

## 1. Confirmation

> **No protected file was deleted, moved, renamed, compressed, truncated, overwritten or
> modified by this continuation.**
>
> **The 19 `innovation_deploy_root_v3_*` directories are untouched.**
>
> **No GPU job was submitted. No GPU-hour was consumed.**

---

## 2. Byte-level proof for the official-reproduction deliverables

Before any work began, a hash snapshot of every pre-existing file under
`hpc_results/official_repo_reproduction_20261006/` was written to
`PRE_AUDIT_DELIVERABLE_HASHES.csv` (66 files: the 49 top-level deliverables plus nested
`hpc_probe/`, `hpc_a1/`, `hpc_a1_runs/`, `hpc_compat/`, `local_compat/` contents).

Comparison after all work:

| | Count |
|---|---:|
| files tracked in the snapshot | 66 |
| **byte-identical (unchanged)** | **66** |
| changed | **0** |
| missing / deleted | **0** |

**Every one of the 66 files has an identical SHA-256 to its pre-audit value.**

---

## 3. Older result trees — file counts unchanged

| Tree | Files now | Recorded before this continuation | Status |
|---|---:|---:|---|
| `results/v3_clean` | 1,485 | 1,485 | ✅ unchanged |
| `hpc_results/stage6` | 60 | 60 | ✅ unchanged |
| `hpc_results/stage5_a2` | 148 | 148 | ✅ unchanged |
| `audit_20260930` | 171 | 171 | ✅ unchanged |
| `recovery` | 212 | 212 | ✅ unchanged |

---

## 4. Protected trees that were deliberately NOT edited

These carry known errors that were corrected **in new files only**:

| File | Known issue | Why untouched |
|---|---|---|
| `hpc_results/stage6/scoring/paired_stats.py` / `paired_stats.txt` | win counter inverted | correction carried by `PAIRED_STATS_CORRECTION_VERIFICATION.md` |
| `recovery/stage6/results_report_zh.md` | §0 says "5/12 win" | corrected in the addendum, not in place |
| `../a1_results_per_run.csv`, `../a1_results_aggregate.csv` | label `mse_mean_over_epochs` presented as `mse_mean`; track tagged `A1_reconstructed_paper_config` | corrected by `STATUS_CORRECTION_ADDENDUM.md` C-1 and C-5 |
| `../REPORT_ZH.md`, `../REPORT_EN.md`, `../STATUS_AFTER_CONTINUATION.md` | A2 magnitude 59.7/7.13e8; decay_fac label; A1-P naming | corrected by C-2/C-3/C-5 and superseded by the V2 reports |
| `../TEXT_PATH_RESOLUTION.md` | A2 magnitude row | corrected by C-2 |
| `EE4080_MIFlu_Research_Recovery_Plan.md` L161, `CodeBuddy_MIFlu_Recovery_Prompt.md` L63 | label 20 ep / 5e-4 as "Paper:" | corrected by `HYPERPARAMETER_PROVENANCE_V2.md` E-1 |

**All of the above remain byte-identical to their original state.**

---

## 5. Historical Track-B deployment family — verified unchanged

Live check after all work (19 lightweight `stat` calls, no scanning):

```
ls -d /gpfs1/scratch/sychan552/innovation_deploy_root_v3_* | wc -l   ->  19
```

All 19 present, none renamed. Their latest file mtimes remain within
**2026-09-16 … 2026-09-21**, i.e. unchanged and still strictly before the
2026-09-24 clone. Directory mtimes are likewise unchanged (e.g. `v3_clean14` still
`2026-09-21 09:00:03 +0800`).

**Nothing was deleted, moved, renamed, compressed, truncated, edited, overwritten,
repaired, restructured, deduplicated, relinked, loaded or inferred on.**

All duplicate candidates are recorded as `NOT_AUTHORIZED_FOR_DELETION`; all directories as
`UNSAFE_TO_DELETE`.

---

## 6. Why the audit jobs could not have modified anything

Both audit jobs (606430 metadata, 606432 hashing):

- opened files **read-only** (`sha256sum`, `stat`, `du`, `find -printf`, `ls`);
- contain **no** `rm`, `mv`, `cp`, `truncate`, `chmod`, `ln`, `tar`, `gzip`, `>` redirect
  or `tee` aimed at `/gpfs1/scratch`;
- write **only** into
  `/gpfs1/home/sychan552/official_repo_reproduction_20261006/postrun_audit_20261006/out/`;
- refuse to run if `hostname` matches `hpclogin*`.

---

## 7. GPU non-submission evidence

| Check | Result |
|---|---|
| `squeue -u $USER` at the end | **empty** |
| jobs submitted by this continuation | **2**: `606430` `audit_readonly`, `606432` `audit_hash` |
| `gres/gpu` in either job's `AllocTRES` | **absent** → **0 GPU-hours by construction** |
| GPU jobs in the window since 2026-10-05T22:00Z | 6 — **all from the earlier round** (606358, 606361_0, 606365_0, 606378_1, 606385_2, 606412_3), none submitted now |
| remaining allowance | **0.05639 GPU-h**, untouched |

---

## 8. Local repository state

```
git status --porcelain | awk '{print $1}' | sort | uniq -c
    179 ??      (untracked: new scripts, result trees, this audit directory)
     49 M       (modified — all pre-existing, none touched here)
      9 D       (deleted — all pre-existing)
```

Identical to the counts observed at the start of the previous continuation round. **No
tracked file was modified by this work.**

---

## 9. New files created by this continuation

All new files live under
`hpc_results/official_repo_reproduction_20261006/postrun_audit_20261006/` (plus the
`hpc_out/` subdirectory of raw Slurm outputs, `slurm_r2/` scripts, and three new
`scripts/` and one new `probe_*_v2.py` at the repository level).

Nothing was written over an existing path.

---

## 10. Summary

| Rule | Status |
|---|---|
| append-only output directory | ✅ |
| no deletion / modification of protected artifacts | ✅ verified by 66 SHA-256 comparisons + 5 tree counts + 19 live `stat` checks |
| no scratch cleanup | ✅ not performed |
| no GPU submission | ✅ 2 CPU-only jobs, 0 GPU-hours |
| no login-node compute | ✅ both jobs ran on compute nodes; `ps` showed no stray processes |