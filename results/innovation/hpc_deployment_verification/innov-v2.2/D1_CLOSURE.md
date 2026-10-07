# D1 closure — pilot-spec metadata repair (implementation source `innov-v2.2`)

Scientific protocol: **`innov-v2.0` (unchanged)**
Implementation source: **`innov-v2.1` → `innov-v2.2` (bumped)**
Authoritative plan: `MIFlu_innovation_plan_v2.md`, SHA-256 `aa4ab1c8842e893a4690787e17add0ca193c86825fff9fd89f46952c7f9e7961` (recomputed at runtime, matches)

## What D1 was

The pilot-definition audit found that each of the four entries in `hpc_scripts/pilot_specs.json` was missing
`experiment_stage`, `test_access_allowed` and `protocol_version`, and that the top-level object carried
`scientific_protocol_version` but no `protocol_version`.

## What changed (source, `innov-v2.2`)

| file | change |
|---|---|
| `scripts/innovation/paths.py` | `IMPLEMENTATION_SOURCE_VERSION = "innov-v2.2"`; new single-source-of-truth contract `pilot_spec_metadata()` returning `{experiment_stage:"pilot", test_access_allowed:False, protocol_version:PROTOCOL_VERSION}` plus the `TEST_ACCESS_ALLOWED` constant |
| `scripts/innovation/hpc_specs.py` | emits those three fields at the **top level** and inside **every individual spec** of `pilot_specs.json` |
| `scripts/innovation/source_snapshot.py` | `stamp_pilot_specs()` re-stamps the same contract, so the snapshot cascade alone can never strip the fields |
| `scripts/innovation/runner.py` | `_eligibility()` now writes `test_access_allowed: false` into **every** `run_status.json` |
| `tests/innovation/test_pilot_spec_metadata.py` | new 7-case regression test; fails if any mandated field disappears, if model keys/horizons/seeds drift, if a pilot spec becomes selection-eligible, or if any stage's run status allows test access |
| `scripts/innovation/reproduce.sh` | runs the new test as part of the one-command reproduction |

## Explicitly NOT changed

`dataset split`; `scaler`; `prompt-statistics policy`; `horizons {24,36,48,60}`; `seeds 42..51`; `early stopping` (val-MSE + patience, best-checkpoint restore);
`PTE` / `PIE` and the single literature criterion (PTE ≤ 1 week **and** PIE ≤ 25 %); `literature peak criterion`; `model implementations`; `architecture fidelity`
and the disclosed deviations; `model keys`; `selection logic`; `test-isolation policy`. `scientific_protocol_version` stays `innov-v2.0`.

## Evidence

* **Local generation** — `python scripts/innovation/hpc_specs.py`: top level and all 4 specs carry `experiment_stage=pilot`, `test_access_allowed=false`, `protocol_version=innov-v2.0`.
* **Runtime** — `results/innovation/runs/national-ili__dlinear__none__identity__L24__seed42__20260914T181420Z__1f6563f/run_status.json`
  carries `experiment_stage=smoke`, `selection_eligible=false`, `protocol_version=innov-v2.0`, **`test_access_allowed=false`**.
* **Frozen source** — new snapshot aggregate `06b83e18e4bb66d69ae457087fa5024bb4a50884bca3c080ca51af35de575e86` over **70** files (v2.1: `dc7ee964…` / 69 files); `verify_source_snapshot.py` returns 70/70, exit 0, aggregate match.
* **Deployed source** — `/home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.2_06b83e18`, `verification_mode=explicit_root`, 70/70, `expected == actual`, exit 0; `grep` on the deployed `pilot_specs.json` shows all three fields at both levels.
* **Environment (login node)** — python 3.9.25 / torch 2.5.1 / transformers 4.57.6 / sklearn 1.6.1, `gpt2_offline_load=OK`, `bash -n` ok on all pilot scripts, no GPU on the login node (expected).
* **Gate** — `submission_attempted=false`, `sbatch_invoked=false`, `squeue` empty; test split sealed (`frozen_winners.json` absent, `test_evaluations/` empty, zero `test_*` artifacts under `runs/`).
* **Tests** — all 13 innovation unit tests green, including the new D1 test and the old-pipeline-vs-innovation-runner regression (`all_agree=true`, `max_abs_diff=0.0`).

## Known residual / disclosed incident

The first extraction used the path printed by the *regenerated* `DEPLOY_AND_VERIFY.md` (the original reproduction repo
`Chattime`) rather than the isolated deployment root used at v2.1. The additions were removed and the rewritten
dependency files were proven content-identical via the residual `__pycache__` headers (recorded source size == current
size for all but the intentionally-updated `compute_miflu_indicators.py`, whose mtime was therefore left unrestored).
Full detail in `transfer_report.json → INCIDENT_AND_RECOVERY`. The bundle generator now prints the isolated root.

## Still open

* **D2** (cosmetic) — recorded display labels are semantically equivalent but not byte-identical to the requested labels. Unchanged, not part of D1.
* **Pilot submission** — requires a separate, explicit authorization plus a verified A100 inside an allocated job. **Nothing was submitted in this turn.**
* Smoke/pilot results remain infrastructure evidence only: no ranking, no winner, no test access, no journal performance conclusion.
