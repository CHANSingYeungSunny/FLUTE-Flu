# R1 — REPRODUCTION SLURM PLAN

Generated 2026-10-06. **Prepared, not submitted.** No GPU work has been submitted.

---

## 1. Scheduler constraints (verified live)

| Constraint | Value | Consequence |
|---|---|---|
| `MaxSubmitJobs` / `MaxJobsPU` on `partition-stingy` | **1 / 1** | one job at a time; multi-element arrays are **rejected** (`QOSMaxSubmitJobPerUserLimit`, observed on job 606363) |
| `MaxWall` on the stingy QOS | **06:00:00** live (the guide's 04:00:00 is outdated) | 1-hour jobs are far inside the limit |
| account GPU-minute allocation | **none** | no system budget to exceed; the constraint is the user's grant |
| scratch quota | **over** (413 / 300 GB, grace expired) | all output must go to `$HOME` |

---

## 2. Scripts (prepared, not submitted)

| File | Phase | Device | GPU-h |
|---|---|---|---|
| `slurm/r1_rb_preflight.sbatch` | CPU preflight — contract assertions, dataset hash, scorer tests | CPU | 0 |
| `slurm/r1_rb_pilot.sbatch` | GPU — R1-B reconstruction, 4 horizons, repetition 1 | a100 | ~0.21 total |
| `slurm/r1_rb_evaluate.sbatch` | CPU — reload, Test once, persist predictions, independent scoring, text-path probes | CPU | 0 |

**One array element per submission.** The GPU script is submitted as
`--array=i-i` for i = 0…3, sequentially.

---

## 3. Sequence

```
1. r1_rb_preflight.sbatch          (CPU, 0 GPU-h)  -> the preflight gate
2. r1_rb_pilot.sbatch, i = 0..3    (GPU)           -> 4 fits, one at a time
3. r1_rb_evaluate.sbatch           (CPU, 0 GPU-h)  -> scoring + probes
4. gate report                     (CPU)           -> expand / stop decision
```

---

## 4. Preflight gate (must pass before step 2)

| # | Check |
|---|---|
| 1 | `squeue -u $USER` empty |
| 2 | repository commit and git status recorded |
| 3 | the R1-B trainer exists and implements B-1…B-7 |
| 4 | the declared configuration is written and matches `R1_HYPERPARAMETER_EVIDENCE.csv` |
| 5 | all output paths under `$HOME`; none on scratch |
| 6 | ≥ 1 GB safe home-quota margin |
| 7 | no Historical Track B path in any input |
| 8 | no `innovation_deploy_root_v3_*` reference anywhere |
| 9 | the projected GPU use is within the granted tranche |
| 10 | `scorer_f1.py` acceptance tests pass (20/20) and the duplicate-key gate fires on a synthetic duplicate |
| 11 | the text probe's dataset-selection check picks the CDC-column file |

---

## 5. GPU budget enforcement

| Rule | Implementation |
|---|---|
| cap = the granted tranche (T1 = 0.30 GPU-h) | the launcher sums `sacct` GPU-hours over R1 job ids **before every submission** |
| `AllocTRES` must be read with an explicit width | `-o AllocTRES%80` — the default width truncates and silently yields an empty GPU count (this defeated the F1 launcher's guard) |
| failed, cancelled and retried jobs all count | the sum is over every recorded job id regardless of state |
| stop rule | any GPU element exceeding **1.5×** its expected elapsed time halts the wave |
| no carry-over | the F1 remainder (0.35 GPU-h) is **not** added to the R1 tranche |

---

## 6. Output layout

```
$HOME/official_repo_reproduction_20261006/r1/
  logs/          slurm stdout/stderr, per-fit logs
  ckpt/<horizon>/best_<...>.pth
  preds/         prediction NPZs (7-channel), one per (horizon, repetition)
  scoring/       independent scores, gate report, text-path probe JSONs
  manifests/     per-job ledger, run manifests
```

**Nothing is written to scratch.** The project code root on scratch is read-only.

---

## 7. Failure handling

| Failure | Action |
|---|---|
| CPU preflight fails | **do not submit GPU work**; report the failure; wait |
| a GPU fit fails | diagnose before retrying; retry only if the cumulative total stays inside the tranche; never silently retry |
| a contract gate fails | report; do not proceed to the gate report |
| the text-path probe returns `text_inert` | the B-2 restoration failed — stop, do not expand |
| the trainable count equals the total | the B-4 freeze failed — stop; this also invalidates the budget basis |
| the pilot is invalid | report it as invalid; **do not** re-run with tuned settings |

---

## 8. Preservation rules

- F1 and every earlier artifact remain **unchanged**.
- Nothing is deleted.
- The 19 `innovation_deploy_root_v3_*` directories are never read or written by any R1 script.
- All new files go into the R1 append-only directory.

---

## 9. Status

| Item | Status |
|---|---|
| scripts prepared | ✅ (stubs with the contract pinned in provenance blocks) |
| scripts **wired to a trainer** | ❌ — the R1-B trainer does not exist yet (option 4a still to be built) |
| submitted | ❌ **none** |
| GPU authorization for R1 | ❌ **not granted** |

**The Slurm plan cannot be executed until the R1-B trainer exists and a
reproduction-specific GPU authorization is given.**