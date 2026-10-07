# Run eligibility policy (pre-HPC)

A run may enter `select_best_model.py` **only** when its `run_status.json`
explicitly carries ALL of:

| Field | Required value |
|---|---|
| `protocol_version` | `innov-v2.0` |
| `experiment_stage` | `screening` or `full` |
| `selection_eligible` | `true` |
| `smoke_only` | `false` |
| `status` | `ok` |

Everything else is excluded **by construction**:

* `smoke` / `pilot` / `adhoc` / `validation` stages;
* failed or blocked runs;
* runs predating this schema (missing eligibility fields);
* runs produced under a different protocol version;
* any run force-excluded by `legacy_runs_eligibility.json`.

`legacy_runs_eligibility.json` annotates existing runs **without mutating**
their artifacts (create-only principle preserved).
