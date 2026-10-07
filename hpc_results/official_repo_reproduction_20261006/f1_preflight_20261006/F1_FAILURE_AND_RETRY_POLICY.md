# F1 FAILURE AND RETRY POLICY

Generated 2026-10-06. Predeclared so that no retry decision is made after seeing a result.

## 1. Failure taxonomy

| Class | Symptom | Retry? | Rationale |
|---|---|---|---|
| **T1 transient infrastructure** | `NODE_FAIL`, `TIMEOUT` before any epoch, `OUT_OF_MEMORY` on a node that previously succeeded | ✅ **yes, once** | not attributable to the experiment |
| **T2 deterministic environment** | import error, missing file, missing HF cache, wrong dataset SHA | ❌ no | will recur identically; fix the cause first |
| **T3 data-contract violation** | `A2_REQUIRE_STRICT` exit, scaler assertion, containment error | ❌ **never** | the run was off-contract; retrying would produce an invalid artefact |
| **T4 runtime numerical** | NaN/Inf loss, divergence | ✅ yes, once, with the same seed | if it recurs, record as a genuine failure rather than tuning around it |
| **T5 artefact rejection at scoring** | `scorer_f1` rejects the NPZ | ❌ no — investigate | a rejected artefact indicates a real defect |
| **T6 gate failure (missing cell)** | G1/G2/G6 fail | ✅ re-run only the missing cell | never re-run a completed cell to improve a number |

## 2. Hard rules

1. **Never silently replace a failed run.** A failure is a recorded outcome.
2. **Never change the seed to get past a failure.** One pilot seed is the contract.
3. **Never change hyperparameters in response to a result.** That is accuracy hunting.
4. **Never delete a failed run's logs.** They are part of the record.
5. **Maximum two attempts per (model, horizon) cell.** A third attempt requires a written
   justification in the ledger.
6. **A retry uses byte-identical configuration.** Only the Slurm job id differs.

## 3. Stop rules

| Trigger | Action |
|---|---|
| any GPU element exceeds **1.5×** expected elapsed (288 s for a GPU fit) | stop the wave, report, do not continue |
| two consecutive elements fail | stop, diagnose, report |
| `f1_score_all.py` returns `FAILED_INTEGRITY` | stop; do not present a ranking |
| home headroom falls below 1 GB | stop; the storage guard should already have prevented this |
| GPU-hour consumption within 10 % of the approved cap | stop and request before continuing |

## 4. Failure record

Every attempt appends to `f1/manifests/GPU_LEDGER_F1.tsv` with
`job · index · arm · horizon · seed · elapsed · exit code`, and every failure additionally
gets a row in the eventual `f1_failures.csv` carrying the **class (T1–T6)**, the observed
error, the action taken, and whether the cell remains missing.

## 5. Consequence for the pilot status

If any trained arm cannot be completed within the retry policy, F1 is reported
**PARTIAL**, and the ranking is shown only with the missing cells named beside it. Per the
brief, a partial pilot is **not** presented as the completed pilot result.
