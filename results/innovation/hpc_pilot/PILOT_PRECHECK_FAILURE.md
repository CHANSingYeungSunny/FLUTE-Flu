# Pilot precheck failure — no job submitted

**Status: `PILOT_PRECHECK_FAILED` · sbatch invoked: no · pilots submitted: 0**

## What passed (13/14 mandated prechecks)

| # | check | result |
|---|---|---|
| 1 | entered the isolated innov-v2.3 root | PASS |
| 2-4 | explicit deployment-root verification, 76/76, `actual == expected == 9bc1503c…` | PASS |
| 5-6 | `runtime_guard.py`: 11 paths checked, **0 violations** | PASS |
| 7 | strict offline GPT-2: `gpt2_offline_load=OK` | PASS |
| 8 | `bash -n` on 4 pilots + submit + worker (6/6) | PASS |
| 9-10 | `pilot_specs.json` has exactly the four definitions, all `selection_eligible / paper_result_eligible / test_access_allowed = false` | PASS |
| 11-13 | no `frozen_winners.json`, `test_evaluations` empty, no test artifacts under runs | PASS |
| 14 | `full_sweep_submission_ready = false` | PASS |

## What failed (blocking)

Every generated script — including all four authorized pilots — begins with:

```bash
cd /home/sychan552/scratch/CHATTIME/Chattime
```

That is the **original reproduction repository**, which this authorization forbids as an execution
path. Consequences, all verified on HPC:

* the pilot would not run from the isolated deployment root;
* `runtime_guard.py --deployment-root "$(pwd)"` would see the banned path → **1 violation → exit 2**
  → the pilot aborts with `FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT`;
* `scripts/innovation/` does not exist in Chattime (`ls …` → *No such file or directory*), so even
  bypassing the guard the startup source check would abort.

All four pilots would therefore fail deterministically. The guard is behaving exactly as designed
(fail-closed); the defect is in the deployment scripts, not in the guard.

Origin: `scripts/innovation/hpc_specs.py::_HEADER` — a legacy line inherited from the original
ablation workflow, unchanged through innov-v2.1 / v2.2 / v2.3.

## Submit-script contract review (preferred command not usable)

`hpc_scripts/submit_innovation_pilot.sh` submits `innovation_worker.sh` once per spec (the four
definitions are correct), never screening/full/test, and it serialises on the stingy slot — but:

* it does **not** reference the four authorized `pilot_*.sh` scripts;
* it does **not** stop when a predecessor fails (it only waits for the queue slot to free).

So the prescribed fallback — submitting the four `pilot_*.sh` one at a time — is also impossible,
because those scripts carry the same forbidden `cd`.

## Decision

Do not submit. Report `PILOT_PRECHECK_FAILED`.

## Minimal fix (requires separate authorization)

In `scripts/innovation/hpc_specs.py::_HEADER`, replace the hardcoded `cd …/CHATTIME/Chattime` with
`cd "${INNOVATION_DEPLOYMENT_ROOT:-$(pwd)}"`, and make the chain driver call the four `pilot_*.sh`
scripts and stop on a predecessor failure.

`scripts/innovation/**` is inside the frozen source snapshot, so this changes the runtime aggregate
and requires an **innov-v2.4** cascade: snapshot rebuild → manifest → pilot_specs → script
regeneration → tests → bundle ×2 → deployment to a new isolated root. The current authorization
covers only *running* the four pilots, not a source cascade.
