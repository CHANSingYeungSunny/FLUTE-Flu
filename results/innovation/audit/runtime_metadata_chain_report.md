# Runtime metadata chain report

- run_id: `national-ili__dlinear__none__identity__L24__seed42__20260914T210119Z__1f6563f`
- model_key: `dlinear`
- complete: **True**

| field | pilot_specs.json | config_resolved.yaml | run_status.json | checkpoint_manifest.json | registry_v2.csv | agree |
|---|---|---|---|---|---|---|
| `experiment_stage` | pilot | smoke | smoke | smoke | smoke | OK |
| `purpose` | infrastructure_verification_only | runtime_metadata_contract_verification | runtime_metadata_contract_verification | runtime_metadata_contract_verification | runtime_metadata_contract_verification | OK |
| `selection_eligible` | false | false | false | false | false | OK |
| `paper_result_eligible` | false | false | false | false | false | OK |
| `test_access_allowed` | false | false | false | false | false | OK |
| `protocol_version` | innov-v2.0 | innov-v2.0 | innov-v2.0 | innov-v2.0 | innov-v2.0 | OK |
| `implementation_source_version` | innov-v2.4 | innov-v2.4 | innov-v2.4 | innov-v2.4 | innov-v2.4 | OK |
| `source_snapshot_sha256` | 5a4c32473e293e8ab01b116e72c7326188b1844a1a84952b72bc2ec5f5eae25d | 5a4c32473e293e8ab01b116e72c7326188b1844a1a84952b72bc2ec5f5eae25d | 5a4c32473e293e8ab01b116e72c7326188b1844a1a84952b72bc2ec5f5eae25d | 5a4c32473e293e8ab01b116e72c7326188b1844a1a84952b72bc2ec5f5eae25d | 5a4c32473e293e8ab01b116e72c7326188b1844a1a84952b72bc2ec5f5eae25d | OK |
| `authoritative_plan_sha256` | aa4ab1c8842e893a4690787e17add0ca193c86825fff9fd89f46952c7f9e7961 | aa4ab1c8842e893a4690787e17add0ca193c86825fff9fd89f46952c7f9e7961 | aa4ab1c8842e893a4690787e17add0ca193c86825fff9fd89f46952c7f9e7961 | aa4ab1c8842e893a4690787e17add0ca193c86825fff9fd89f46952c7f9e7961 | aa4ab1c8842e893a4690787e17add0ca193c86825fff9fd89f46952c7f9e7961 | OK |
| `model_key` | dlinear | dlinear | dlinear | dlinear | dlinear | OK |
| `display_name` | DLinear | DLinear | DLinear | DLinear | DLinear | OK |
| `architecture_fidelity` | REFERENCE_FAITHFUL | REFERENCE_FAITHFUL | REFERENCE_FAITHFUL | REFERENCE_FAITHFUL | REFERENCE_FAITHFUL | OK |

> complete only if every required field is present and equal across the layers that can legitimately be equal, the pilot-spec layer carries exactly the values a pilot run would emit, and no conclusion is drawn from run_status.json alone
