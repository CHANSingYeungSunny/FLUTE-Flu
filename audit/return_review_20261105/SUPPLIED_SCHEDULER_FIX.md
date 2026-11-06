# Scheduler defects found and repaired (2026-11-04T15:35:00Z)

Read-only audit of the live chain found **six** concrete defects. All fixes are
new files (`*_v2`); the originals are preserved in
`trackB_20261104/v2_backup/` on HPC. Sources are in `code/trackB_v2/`.

| # | Defect (observed) | Fix |
|---|---|---|
| 1 | `controller2.sh` counted `results_*.csv` FILES and required >=160. Only the MIFlu runner emits those (2 per cell, max 80); backbone emits `metrics.csv`+npz, classical `metrics.json`+npz. The counter could never reach 160, so both controllers self-renewed forever — the ~112 zero-second tiny jobs. | `cellok.py` validates each cell by runner type (finite metrics, valid npz, matched results pair, predictions, manifest, training log). Controller counts VALIDATED CELLS. |
| 2 | `SKIP` also matched only `results_*.csv`, so every backbone/classical cell was re-trained on each lane restart. | Lane skips only when `cellok.py check` passes; partial cells are quarantined to `partial/` and re-run. |
| 3 | 200 of 1120 rows (5 classical models) were routed to `train_backbone_966.py --backbone <name>`; those names are not in `BACKBONES`, so argparse would fail deterministically. | Routed to `train_classical_966.py --model <name>` (verified `--help` choices). |
| 4 | `lane_all.sh` used `flock` on a shared cursor across 3 lanes on different GPFS nodes; the project's own audit (Table A5) records that GPFS `flock` is not a reliable cross-node mutex. Three duplicate `trackB_all_ctl` controllers were live. | Static stripe partition (`idx %% NLANES == LANE`) removes the shared cursor entirely; per-cell atomic `mkdir` claims with dead-owner reclamation; controller singleton also via `mkdir`. |
| 5 | `lane1` had a 6h wall while `stingy` QOS allows 6h but `gpu_a100` allows 5 days; `lane0.done`/`lane1.done` sentinels never both existed, so `lane_all.sh` waited forever. `retry.tsv` was written but never read. | Wall 24h on gpu_a100 / 6h on stingy; 3 in-lane passes re-execute incomplete cells (max 2 attempts per cell); `retry.tsv` and `blocked.tsv` are surfaced in controller STATUS; `phase.done` is written only after validated completion or when all remaining cells are permanently blocked. |
| 6 | `controller_all.sbatch` submitted an `afterany` successor at job START; each successor immediately spawned another and exited on the singleton lock (0-second churn). `post_all.sh` would `sbatch persistent_driver.sh` blindly, risking GPU contention and duplicate submission. | One successor per generation, submitted only at the 23h renewal with `afterany`. `post_all_v2.sh` waits for `all/phase.done`, snapshots legacy TODOs to `LEGACY_TODO.tsv`, waits for Track-B GPU lanes to finish, then submits the legacy driver exactly once behind a `mkdir` guard. |

Also fixed: quota guard now warns >450G / pauses >900G (was >900G only, with no
prune wired); checkpoint pruning is OPT-IN to honour RETURN_CONTRACT's
requirement to retain per-seed checkpoints; `stingy` lane wall corrected to the
QOS-valid 06:00:00; the `all` phase is gated on validated core completion per
protocol L; encoder cells preflight their pinned revision weights before using a
GPU; HF cache overrides are scoped to encoder runs so MIFlu keeps its cached
GPT-2; offline flags are scoped likewise.

## Measured evidence

- `logs/trackB_v2/validated_counts.txt`: COMPLETE 160 / 160 (core), 117 / 1120 (all).
- `logs/trackB_v2/syntax_check.log`: all 12 shell files + cellok.py pass syntax.
- `logs/trackB_v2/cancel_verification.log`: 21 old jobs confirmed CANCELLED.
- `HPC_VALIDATED_CELLS.tsv`, `RUN_METRICS.csv`: real per-cell outputs.

## What is NOT claimed

This repair makes the chain terminate correctly and avoid duplicate writes. It
does NOT make the 1120 matrix complete, does NOT validate the science, does NOT
implement Track C, and does NOT guarantee a finish date — queue wait on the
6-node `gpu_a100` partition remains the binding constraint.
