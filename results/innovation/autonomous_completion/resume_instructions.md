# Resume instructions — innovation autonomous controller (innov-v2.8)

**STATUS: `AUTONOMOUS_STATE_RECONCILIATION_REQUIRED`** (2026-09-15, morning).

The overnight autonomous run executed A→J (272 Slurm jobs, all `COMPLETED 0:0`) and then
**STOPPED at local stage K** (champion freeze) with `LOCAL_STAGE_FAILED: K`, because
`select_best_model` could not form a baseline (see the defect below). The controller process is
no longer running; `squeue` is empty; there is **no second controller** and **no duplicate job**
(ledger 276 rows / 275 unique job ids).

## Live state

- Isolated deployment root: `/scratch/sychan552/innovation_deploy_root_v2_8`
  (physical path `/gpfs1/scratch/sychan552/innovation_deploy_root_v2_8`).
- Controller: **stopped** (was pid 129024), log `controller.log`.
- Machine-readable state: `results/innovation/autonomous_completion/current_state.json`
  (`status=STOPPED`, `current_stage=J`, `stop_reason=LOCAL_STAGE_FAILED: K`).
- Stage D (Screening) is **COMPLETE and audited** — see `results/innovation/screening/`
  (24/24 cells, metadata chain 24/24, checkpoint-restore 24/24, Test sealed).
- **Blocking defect:** `scripts/innovation/select_best_model.py::build_audit` looks up the
  baseline with the un-slugged key `"gpt2_miflu"` while `parse_run_id` returns the slugged
  `"gpt2-miflu"` → baseline empty → `status=no_eligible_candidate` → no winner → stage K fails
  and the Stage E Screening ranking is empty. Fixing it requires a frozen-source cascade and is
  awaiting explicit authorization before any re-run of E or K.
- Append-only job ledger: `results/innovation/autonomous_completion/job_ledger.csv`.
- Per-stage budget ledger: `results/innovation/autonomous_completion/budget_ledger.csv`.
- Durable copy-back (GPFS home, backed up): `/home/sychan552/innovation_durable/runs/<run_id>`
  and `/home/sychan552/innovation_durable/logs/`.

## Source freeze for this run

- Implementation source: `innov-v2.8` (see `scripts/innovation/paths.py`).
- Snapshot manifest `results/innovation/source_snapshot_manifest.json` → aggregate
  `ff9e3d8f74e2527567e29ac9f5d6bbf3c1cd338ab9e4a7a0a46b161b3112f8e6` (78 files).
- Bundle `results/innovation/hpc_deployment/innovation_hpc_bundle.tar.gz` →
  archive_sha256 `5851de8f607a7707f8fcbbd218841a3c145d49fb2fea483b2c06a69e441be12a`
  (double-build deterministic; local extraction verify 78/78).

## Deploy + launch (idempotent; run from a host WITH HPC access)

The helper `hpc_scripts/autonomous/deploy_and_launch.sh` performs every step below
(fresh isolated root, ship bundle + controller + controller config, **provision the
dataset**, extract, explicit-root verify, dry-run, launch):

```bash
REMOTE_ROOT=/scratch/sychan552/innovation_deploy_root_v2_8 \
  bash hpc_scripts/autonomous/deploy_and_launch.sh --launch
```

### IMPORTANT — the dataset is NOT in the bundle
`runner.py` reads `data/raw/national_illness_raw.csv` (and the scaler/predictions under
`data/`). Data files are intentionally **outside** the frozen source hash and are
provisioned by the deploy helper via `scp -r data …`. The raw CSV sha256 is
`c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d` (identical in the
local repo, `/gpfs1/scratch/sychan552/MLFLU/data/raw/`, and the reproduction repo).
If a root is missing the dataset the pilot aborts with
`FileNotFoundError: …/data/raw/national_illness_raw.csv`.

Launch the controller (login node, NOT an `#SBATCH` job):

```bash
ssh -f sychan552@burgundy.hpc.cityu.edu.hk \
  "export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:\$PATH; \
   cd /scratch/sychan552/innovation_deploy_root_v2_8 && \
   INNOVATION_DEPLOYMENT_ROOT=/scratch/sychan552/innovation_deploy_root_v2_8 \
   nohup bash hpc_scripts/autonomous/controller.sh > controller.log 2>&1 & \
   echo \$! > controller.pid"
```

## Resume after any interruption

The controller is a login-node background loop (not a Slurm job): it does not occupy the
single `stingy` slot and is unaffected by the scheduler. If its process is killed (node
reboot, etc.), re-run the launch command above. On restart it:
1. acquires the single-instance `flock` (regenerated `current_state.json` sets `status=running`);
2. reads `job_ledger.csv`;
3. returns the first job whose `KEY=<…>` has no terminal `COMPLETED` row and continues —
   it never re-submits an already completed job.

## Hard guarantees enforced by the controller

- One job at a time; waits for a terminal Slurm state before the next.
- Records the job id **before** polling.
- Resolves each run's directory by the deterministic run-id PREFIX **and** the expected
  `experiment_stage` (the runner's dir name carries an unpredictable timestamp/git suffix,
  and the same spec can exist at several stages).
- FAIL-STOPs (exit 1, `status=STOPPED` in `current_state.json`) on: non-zero job exit,
  source/metadata mismatch, Test-access violation, stage mismatch, or missing artifacts.
- Never silently retries.
- The one-time Test evaluation (stage `L`) is excluded by `authorization_ceiling="K"` and
  additionally gated by `state.py test_gate_open`: it runs only after the completion
  matrix has no unresolved mandatory item AND the validation-only freeze audit passes.
  It never runs merely because time remains.

## Repairs applied this session (see `decision_log.md` D5/D6)

Source-version cascades performed (frozen files ⇒ version bump + snapshot + bundle):
`v2.5 → v2.6` (generator `{{`/`}}` defect), `v2.6 → v2.7` (worker startup check: missing
`import os`; pilot-only assertions made stage-aware), `v2.7 → v2.8` (stage-scoped
`--skip-if-done` so a pilot run cannot satisfy a screening/full job). Controller-side
(not frozen): run-dir resolution by prefix+stage, `squeue` banner-proof empty check,
data provisioning, local-gate ledger recording, heartbeat status reset.
