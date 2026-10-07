# Wave-1 resume instructions (controller NOT launched)

## State
- Gate **570846** = COMPLETED 0:0, **19/19 passed** (version `innov-v3.12-gate-validator-schema-alignment`).
- Wave-1 controller is **prepared but NOT launched**. Formal submissions
  remain **0/598**.

## Authorizing a launch (a SEPARATE, future authorization)
1. Create `results/v3_clean/runs/wave1_authorization.token` containing the
   one-time authorization token.
2. Export the same value: `export WAVE1_AUTHORIZATION_TOKEN=<token>`.
3. Run on the login node:
   `bash results/v3_clean/runs/wave1_controller.sh`
4. The controller refuses to start unless BOTH match.

## What the controller does
- takes a single-instance lock (`.wave1_controller.lock`)
- reads the **580 ordered immediate run keys** from
  `formal_execution_order_wave1.txt`
- submits **one** `stingy` job at a time, records the job id immediately in
  `wave1_ledger.csv` (append-only)
- polls `sacct` for terminal state, then accepts only when `COMPLETED` + `0:0`
  AND all required artifacts exist AND the durable copy is verified
- is resumable: already-accepted keys are skipped, never resubmitted
- fail-stops on any deterministic error; stops after 580 accepted rows

## Hard ceilings
- never more than **one** active or pending Slurm job
- login node: submission, polling, small-file checks and `cp` only — **no**
  python, Torch, Transformers, model loading, preprocessing, evaluation,
  checkpoint restoration or bulk hashing
- never discovers superseded archives; never touches Test/holdout
