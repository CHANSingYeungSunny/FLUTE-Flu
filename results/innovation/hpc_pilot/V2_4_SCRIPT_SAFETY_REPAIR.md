# innov-v2.4 — Pilot script safety repair

`scientific_protocol_version = innov-v2.0` · `implementation_source_version = innov-v2.3 → innov-v2.4`

## 1. Root cause

`scripts/innovation/hpc_specs.py::_HEADER` contained a hardcoded

```bash
cd /home/sychan552/scratch/CHATTIME/Chattime
```

—a legacy line inherited from the original ablation workflow, predating the isolated-deployment
policy and never revisited in innov-v2.1 / v2.2 / v2.3. Every generated script inherited it, so the
four pilots, the worker and the submit driver would all have executed from the **forbidden original
reproduction repository**.

**Affected scripts:** the four `pilot_*.sh`, `innovation_worker.sh`, `submit_innovation_pilot.sh`.

## 2. Why the runtime guard was right

`runtime_guard.py` runs with `--deployment-root "${INNOVATION_DEPLOYMENT_ROOT:-$(pwd)}"`. With the
forbidden `cd`, `$(pwd)` resolved to the banned root → **1 violation → exit 2** → the pilot would
have aborted with `FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT` before any training. The guard was
fail-closed and correct; the defect was in the generated scripts.

Consequence: **no v2.3 pilot was ever submitted, so no erroneous training result exists.** The v2.3
failure evidence (`pilot_precheck_failure.json`, `PILOT_PRECHECK_FAILURE.md`) is preserved unchanged.

## 3. Files changed

| file | change |
|---|---|
| `scripts/innovation/hpc_specs.py` | new safe `_HEADER`; new `_STARTUP_PY`; rewritten `_pilot_script` / `_WORKER`; new `_submit_pilot_driver` + `_pilot_script_name` |
| `scripts/innovation/slurm_check.py` | accepts `set -euo pipefail` as equivalent to `set -u` |
| `scripts/innovation/paths.py` | `IMPLEMENTATION_SOURCE_VERSION → innov-v2.4` |
| `tests/innovation/test_script_safety.py` | **new** — 14 test functions |
| `tests/innovation/test_metadata_chain.py` | version assertion now reads the constant |

No scientific content was touched: split, scaler, prompt statistics, horizons, seeds, model
implementations, architecture fidelity, early stopping, MSE/MAE/PTE/PIE, the literature peak
criterion, model selection, test isolation and the canonical indicator are unchanged.

## 4. New deployment-root behaviour

```bash
set -euo pipefail
: "${INNOVATION_DEPLOYMENT_ROOT:?INNOVATION_DEPLOYMENT_ROOT must be set to the isolated deployment root}"
DEPLOYMENT_ROOT="$(cd "$INNOVATION_DEPLOYMENT_ROOT" && pwd -P)"
FORBIDDEN_ROOT_RAW="/home/sychan552/scratch/CHATTIME/Chattime"      # constant only
FORBIDDEN_ROOT="$(readlink -f "$FORBIDDEN_ROOT_RAW" 2>/dev/null || true)"   # never cd into it
if [ -n "$FORBIDDEN_ROOT" ]; then
  if [ "$DEPLOYMENT_ROOT" = "$FORBIDDEN_ROOT" ] || [ "${DEPLOYMENT_ROOT#"$FORBIDDEN_ROOT/"}" != "$DEPLOYMENT_ROOT" ]; then
    echo "FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT" >&2; exit 2
  fi
fi
cd "$DEPLOYMENT_ROOT"
```

No silent `${INNOVATION_DEPLOYMENT_ROOT:-$(pwd)}` fallback anywhere. Verified on HPC: with the
variable unset the submit driver exits **1** with the required message *before* any submission;
without `CONFIRM_INNOVATION_SUBMIT=YES` it reports `submission_attempted=false` and exits 0.

Every pilot and the worker additionally re-run at job start: `runtime_guard.py`,
`verify_source_snapshot.py --deployment-root "$DEPLOYMENT_ROOT"`, and a governance assertion that
compares the deployed manifest aggregate with the hash in `pilot_specs.json` and re-asserts
`test_access_allowed / selection_eligible / paper_result_eligible = false` plus
`experiment_stage=pilot`, `purpose=infrastructure_verification_only`.

## 5. Submit driver: serial, afterok, fail-stop

`submit_innovation_pilot.sh` now references **only** the four authorized pilot scripts (never the
generic worker), waits for each predecessor to reach a **terminal** state before submitting the next
(stingy: 1 running + 1 pending), and additionally chains with `--dependency=afterok:` (never
`afterany`). If the predecessor is not `COMPLETED` with `ExitCode 0:0` the driver prints `FAIL-STOP`
and exits 1. No retry, no self-recursion, and the `CONFIRM_INNOVATION_SUBMIT=YES` guard is retained.

Proven behaviourally with fake `sbatch`/`sacct` on PATH: success scenario → **4** submissions;
`FAILED` predecessor → **1** submission and a non-zero exit.

## 6. Hashes and deployment

| item | value |
|---|---|
| runtime files | **77** |
| runtime aggregate | `5a4c32473e293e8ab01b116e72c7326188b1844a1a84952b72bc2ec5f5eae25d` |
| archive (two builds identical) | `bc6e8bff6f77c8b5e23634466f8d09b13927dd74198c67194c6befe28c4375ae` |
| previous v2.3 aggregate | `9bc1503c2ee7ad99019200108f990df72aa4e8e8cb37d3ecba13965e8ee431e0` (do not mix) |
| new isolated root | `/home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.4_5a4c3247` |
| explicit-root verification | **77/77**, `actual == expected`, exit 0 |
| runtime guard | 0 violations |
| `bash -n` | 4 pilots + worker + submit, all OK |
| strict offline GPT-2 | `gpt2_offline_load=OK` |

## 7. Metadata-contract smoke

A smoke was **needed**: the frozen source hash changed, so the five-layer chain evidence had to be
regenerated under the v2.4 hash (the repair itself did not touch the runner). One additional
dlinear/L24/seed42 run (1 epoch, limited rows, `…20260914T210119Z__1f6563f`) is the chain evidence and
is **permanently ineligible** (`selection_eligible=false`, `paper_result_eligible=false`,
`test_access_allowed=false`). `registry_v2.csv` now has 6 rows, 1 of which carries the v2.4 hash.

## 8. Claims explicitly not made

* no v2.4 model job has run on an A100 (job `556143` was observed under **innov-v2.2**);
* no pilot has been submitted in this turn;
* no model ranking, no screening, no full sweep, no test evaluation.
