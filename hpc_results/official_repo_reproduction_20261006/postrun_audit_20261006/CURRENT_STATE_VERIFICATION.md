# CURRENT STATE VERIFICATION

Generated 2026-10-06. This is an **append-only** document: it records the state as
measured, and nothing it describes was modified to produce it.

Verification order follows §7 of the continuation brief.

---

## 1. Working directory

```
pwd = C:\Users\Asus\Desktop\FYP code\MLFlu   (local Windows workspace)
      /gpfs1/home/sychan552/official_repo_reproduction_20261006  (HPC writable root)
```

## 2. `git remote -v`

```
origin  https://github.com/CHANSingYeungSunny/FLUTE-Flu.git (fetch)
origin  https://github.com/CHANSingYeungSunny/FLUTE-Flu.git (push)
```

## 3. `git status --short` — summary

| Code | Count | Meaning |
|---|---:|---|
| `??` | **179** | untracked (new scripts, result trees, logs, the audit directory) |
| `M ` / ` M` | **49** | modified tracked files |
| `D ` / ` D` | **9** | deleted tracked files (8 staged/unstaged deletions predating this work) |

**No file was modified by this continuation.** The 49/9/179 counts are identical to
the counts observed at the *start* of the previous continuation round
(see `../STATUS_BEFORE_CONTINUATION.md` §2, which recorded 49 modified files and
the same deletion set).

### Deleted tracked files (pre-existing, NOT performed by this work)

```
D  HPC_GUIDE.md                                    (staged)
 D data/results_miflu_20260814_204437.csv
 D data/training_miflu_log_20260816_173454.txt
 D results/ili/figures/FIGURE_CAPTION_L24.md
 D results/ili/figures/deprecated/fig_miflu_eval_continuous_OLD_PROTOCOL.png
 D results/ili/figures/deprecated/fig_miflu_eval_diagnostics_OLD_PROTOCOL.png
 D results/ili/figures/q4_granger_bidirectional.png
 D results/ili/figures/q4_ilittotal_vs_providers_scatter.png
 D results/ili/figures/q4_overlay_ilitotal_vs_providers.png
```

### `git diff --stat`

```
57 files changed, 149959 insertions(+), 148767 deletions(-)
```
The bulk is regenerated figures/CSVs and the `scripts/miflu_model.py` family. These
modifications **predate this continuation** and were not touched here.

## 4. Branch and HEAD

```
branch = recovery-stage4
HEAD   = 1f6563f7ea52620354a4fa0666b813b6a9f9cc51
```

## 5. `git log -5 --oneline`

```
1f6563f FLUTE-Flu: MIFlu reproduction docs, scripts, figures (checkpoints excluded)
```

**The project repository has exactly one commit.** Consequence, restated because it
governs several later conclusions: experiment ordering cannot be reconstructed from
git history, and the code version used at training time cannot be recovered from git
because `scripts/miflu_model.py` carries uncommitted changes.

## 6. `squeue -u $USER` (2026-10-05T21:58Z, hpclogin02)

```
JOBID PARTITION NAME USER ST TIME NODES NODELIST(REASON)
             (no rows)
```

**Queue empty.** No user jobs were running or pending at the time of the check.

## 7. Slurm accounting

Verified live this session (not taken from a saved file). See
`GPU_LEDGER_VERIFICATION.csv` for the full recalculation.

## 8. Existence of the 49 official-reproduction deliverables

`hpc_results/official_repo_reproduction_20261006/` contains **50 top-level entries**
(the 49 deliverables plus the new `postrun_audit_20261006/` directory).

A byte-level snapshot of **66 pre-existing files** (top level plus nested
`hpc_probe/`, `hpc_a1/`, `hpc_a1_runs/`, `hpc_compat/`, `local_compat/`) was taken
before any work began, into:

```
PRE_AUDIT_DELIVERABLE_HASHES.csv   (path, bytes, sha256)
```

This is the reference used by `FILE_INTEGRITY_AND_NONDELETION_CONFIRMATION.md`.

## 9. `innovation_deploy_root_v3_*` absolute paths

**19 directories matched** under `/gpfs1/scratch/sychan552/`:

```
innovation_deploy_root_v3_1  v3_2  v3_3  v3_4  v3_5
innovation_deploy_root_v3_clean1 .. clean14   (14 directories)
```

Full listing: `HISTORICAL_TRACK_B_DEPLOYMENT_INVENTORY.csv`.
All are classified **UNSAFE_TO_DELETE**.

## 10. Quota (as measured, `mmlsquota -u sychan552`)

| Filesystem | Used | Quota | Limit | Grace | Status |
|---|---:|---:|---:|---|---|
| home | 28,166,800 KB ≈ **26.9 GB** | 52,428,800 KB = 50 GB | 100 GB | none | OK |
| **scratch** | 433,264,576 KB ≈ **413.2 GB** | 314,572,800 KB = **300 GB** | 1000 GB | **expired** | **OVER QUOTA** |

`/gpfs1/scratch` is therefore **read-only in practice** for this account: writes fail
intermittently with `Disk quota exceeded`. All outputs of this continuation are
written under `/gpfs1/home/sychan552/`.

**Scratch cleanup is NOT authorized, and was not performed.**

## 11. Non-Slurm processes on the login node

```
ps -u sychan552 -o pid,ppid,etime,pcpu,pmem,args | grep -iE "python|train|infer"
→ (no matches)
```

**No improperly running process was found.** No PID needed recording or stopping.
The login-node rules are being observed.

## 12. Summary of verification

| Check | Result |
|---|---|
| Repository remote resolves to the project's own GitHub repo | ✅ |
| Working tree unchanged by this continuation | ✅ |
| Slurm queue empty at start | ✅ |
| All 49 prior deliverables present | ✅ (50 entries incl. the new dir) |
| Pre-audit hash snapshot taken | ✅ 66 files |
| 19 `innovation_deploy_root_v3_*` directories identified | ✅ |
| Scratch over quota, grace expired | ⚠️ recorded |
| Non-Slurm compute on the login node | ✅ none found |