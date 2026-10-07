# innov-v2.3 governance closure

`scientific_protocol_version = innov-v2.0` (unchanged) · `implementation_source_version = innov-v2.3`

## 1. Historical integrity — retained, not rewritten

```text
historical_original_repository_integrity_verified = false
original_repository_used_for_innovation_execution = false
isolated_deployment_required                       = true
```

> The pre-incident byte identity of `scripts/compute_miflu_indicators.py` could not be established.

No claim is made that the original repository was fully unaffected, that the current file is
byte-identical to the pre-incident remote copy, or that size / mtime / pyc-header /
bytecode equality proves byte identity. All v2.1 and v2.2 incident reports are preserved
unchanged. `/home/sychan552/scratch/CHATTIME/Chattime` was not touched in this turn.

## 2. Prospective canonical indicator

| item | value |
|---|---|
| path | `scripts/compute_miflu_indicators.py` |
| SHA-256 | `bf72d37ce9eaa21cb052f18568764d913163caf237ba9ce0cf76f15d98f46c0f` |
| adopted from | innov-v2.3 onwards (before adoption: innov-v2.2) |
| matches local working copy | true |
| matches innov-v2.2 frozen copy | true |
| copy verified | true (`results/innovation/governance/canonical_indicator_script.py`) |

> The adopted script is the canonical metric implementation from innov-v2.3 onwards. No claim is
> made that it is byte-identical to the pre-incident remote working copy.

This converts an unprovable historical question into a reproducible forward baseline.

## 3. Regression against trusted predictions

Reference: `data/predictions_miflu_L24_paper_protocol.csv` (preserved reproduction export,
2026-09-01, predates the incident; provenance recorded with SHA-256). No model was trained; no
innovation test artifact was created. 11/11 comparisons PASS (rtol 1e-9, atol 1e-12).

| metric | value |
|---|---|
| MSE | 244345300.3600282 |
| MAE | 9904.792338276957 |
| PTE | 1.5 weeks |
| PIE | 19.489857508005123 % |
| literature peak hit (PTE ≤ 1 week AND PIE ≤ 25 %) | **false** (PTE 1.5 > 1) |
| fixed-step aggregation | `fixed_step:step=0` |
| rows / dates | 182 / 2018-01-28 → 2021-07-18 |

Only the single literature criterion is implemented or reported.

## 4. Runtime isolation

`scripts/innovation/runtime_guard.py` fails with `FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT`
if any resolved source path lands under the original repository. The check uses `os.path.realpath`
(directory containment as `<banned>/…`), not a raw string prefix. It runs at the start of every
pilot and worker script; 0 violations on the deployed v2.3 root.

## 5. Metadata chain, registry, deployment

* 12 governance fields present and equal across pilot_specs.json, config_resolved.yaml,
  run_status.json, checkpoint_manifest.json and registry_v2.csv → `runtime_metadata_chain_complete = true`
  (evidence run `…20260914T192836Z__1f6563f`).
* `registry.csv` (14 legacy rows) frozen; `registry_v2.csv` (schema 2) append-only, no duplicates.
* New isolated root `innov-v2.3_9bc1503c`: explicit-root verification **76/76**,
  `actual == expected == 9bc1503c2ee7ad99019200108f990df72aa4e8e8cb37d3ecba13965e8ee431e0`, exit 0.
* Archive `75fbdf311956c2a8aa193b9b6e0468c063232f0ad7542b5d2de276d21226f315`, two consecutive
  builds byte-identical, 101 members, local extraction re-verified 76/76.
* Strict offline GPT-2: `OK`. `bash -n`: 4 pilots + worker OK. 16/16 unit tests pass.

## 6. Disclosed discrepancy

The brief asks for `architecture_fidelity = WRAPPER_FAITHFUL` for `gpt2_miflu`. That level is not
in the declared taxonomy `innovation.fidelity.LEVELS`; adding it would change architecture-fidelity
classification, which the same brief forbids. The model's declared level
(`REFERENCE_FAITHFUL`) is recorded instead. Adding the level requires separate authorization.

## 7. A100 caveat

`hpc_a100_allocation_previously_verified = true` refers to job **556143**, observed under
**innov-v2.2** (node `gpu-a100-03`, NVIDIA A100-SXM4-80GB, exactly one GPU). No v2.3 model job has
run on an A100; no such claim is made.

## 8. Gate

```text
canonical_indicator_adopted                     = true
canonical_indicator_regression_passed           = true
prospective_innovation_metric_baseline_verified = true
runtime_metadata_chain_complete                 = true
source_deployment_verified                      = true
hpc_base_environment_verified                   = true
hpc_a100_allocation_previously_verified         = true   # under innov-v2.2
pilot_submission_ready                          = true
full_sweep_submission_ready                     = false
test_sealed                                     = true
frozen_winner_exists                            = false
historical_original_repository_integrity_verified = false
```

`pilot_submission_ready = true` does **not** authorise submission: no pilot was submitted in this
turn, and no `sbatch` was invoked.
