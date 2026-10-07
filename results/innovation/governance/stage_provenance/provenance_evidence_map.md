# Stage F provenance evidence map

1. `stage_plan.json` — pre-execution Stage F expansion (4 models x 4 horizons x 10 seeds).
2. `job_ledger.csv` — append-only rows with `stage=F` (job_id, spec, submitted_utc).
3. Slurm worker logs `hpc_results/innovation/logs/slurm_<job_id>_innovation_worker.sh.out`
   — the `[runner] <run_id>` line is the EXACT job->run artifact link.
4. `registry_v2.csv` — checkpoint / source hashes per run.

No MSE/MAE/PTE/PIE/epoch or any performance value is used for membership.

- jobs with a resolved job->run mapping: 218
- Stage F ledger rows: 160; resolved to runs: 160; unresolved: 0