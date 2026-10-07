# Phase 0.6 holdout source candidates

Metadata-only review; no raw holdout values were downloaded or inspected.

| source | status | geography | granularity | target compatibility |
|---|---|---|---|---|
| CDC FluView / ILINet | CANDIDATE_METADATA_ONLY | national/HHS/state | weekly epiweek | target/units must be frozen; not direct ILITOTAL identity |
| CMU Delphi FluView | PREFERRED_METADATA_CANDIDATE_NOT_ACQUIRED | national/HHS/state | weekly epiweek | `ili`/`wili` percentage plus counts; transformation or reduced target required |
| CDC NHSN HRD | EXTERNAL_VALIDATION_DIFFERENT_TARGET | national/region/state | weekly week-ending | hospital target, incompatible with outpatient ILI |

The known v2 Test is excluded and is not an untouched holdout.
