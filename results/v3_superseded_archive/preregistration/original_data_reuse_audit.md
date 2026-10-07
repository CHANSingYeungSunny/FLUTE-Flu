# Original GPT-2/MIFlu data reuse audit

Status: **FROZEN_PENDING_PHASE1_AUTHORIZATION**.

The active v3 protocol reuses `data/raw/national_illness_raw.csv`, SHA-256 `c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d`, 72,100 bytes, 1,025 rows, epiweeks `200201..202152`. The file contains the seven verified channels and `ILITOTAL` is the target column.

The GPT-2/MIFlu run manifest at `results/innovation/runs/national-ili__gpt2-miflu__gpt2__concat-projection__L24__seed42__20260914T110754Z__1f6563f/split_manifest.json` links this exact canonical path to the experiment and records `train_end=717`, `val_end=819`, `test_end=1025`, `T=104`, seven channels, train-only scaler fitting, and train-only prompt statistics. The companion scaler metadata points to `data/scaler_miflu_national.json` and records the same boundaries and columns.

No external source, `ili`/`wili` target, reduced feature set, new holdout, or rolling-origin redesign is active. The completed Phase 0.5/0.6 external-data investigations remain preserved as `SUPERSEDED_V3_HOLDOUT_FEASIBILITY_HISTORY`.
