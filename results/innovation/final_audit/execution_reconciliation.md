# Execution reconciliation

- Slurm jobs in `sacct` since 2026-09-15: **283** (completed 279)
- Ledger rows: **276** (includes local gates, which are not Slurm jobs)

| Stage | Name | Mode | Slurm jobs | Completed | Failed |
|---|---|---|---|---|---|
| A | verify_gate | local | 0 | 1 | 0 |
| B | four_pilots | slurm | 4 | 4 | 0 |
| C | candidate_readiness | local | 0 | 1 | 0 |
| CONTROLLER |  | slurm | 1 | 0 | 0 |
| D | screening | slurm | 24 | 24 | 0 |
| E | select_candidates | local | 0 | 1 | 0 |
| F | full_evaluation | slurm | 160 | 160 | 0 |
| G | ablations | slurm | 24 | 24 | 0 |
| H | llm_tsfcrm | slurm | 12 | 12 | 0 |
| I | robustness | slurm | 24 | 24 | 0 |
| J | auc | slurm | 24 | 24 | 0 |

## Final Test execution

- resume job **560659** (`stingy`, `gpu:a100:1`, limit 02:00:00) → COMPLETED, elapsed 00:01:00, exit 0:0, node gpu-a100-03
- checkpoint verification job **560692** (`stingy`, 2 CPU, 8 GB) → COMPLETED
- Neither created a second Test evaluation; both reused the same receipt.

## Discrepancies

- Stage L appears with 0 Slurm jobs in the ledger: the one-time Test ran first as a **prohibited login-node `nohup` process** (not a job) and then as job 560659, which was submitted outside the controller and therefore is absent from `job_ledger.csv`. This is explained, not an unexplained discrepancy.
