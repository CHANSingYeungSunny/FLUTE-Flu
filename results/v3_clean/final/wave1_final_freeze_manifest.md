# Wave-1 Final Freeze Manifest

**Freeze package:** `wave1_final_freeze` (append-only)
**Generated (UTC):** 2026-09-21T00:09:30Z
**Status:** Wave-1 evidence reconciled and frozen. No new scientific result is created by this freeze step.

---

## 1. Wave-1 completion status

| Check | Value |
|---|---|
| Wave-1 accepted | **580 / 580** |
| Immutable Wave-1 order | 580 unique keys |
| Durable packages | 580 |
| Primary rows | 320 |
| Baseline rows | 8 |
| Ablation rows | 240 |
| Executed Wave-1 negative-control rows | 12 |
| Deferred controls (pending Wave 2) | 18 |
| Ledger final FAIL events | **0** |
| Controller termination | normal (after 580/580 accepted) |
| Controller process absent | true |
| Lock free | true |
| Formal queue empty | true |
| **Test access** | **0** |
| **Holdout access** | **0** |

### Durable forms

| Form | Count |
|---|---|
| Stochastic checkpoint-applicable (`compact_manifest.json` + `compact.safetensors`) | 572 |
| Deterministic no-checkpoint baseline (`finalize_manifest.json`, `compact_bytes = 0`) | 8 |

### Controller completion

- `controller_completion_utc` = `2026-09-20T05:27:50Z`
- `controller_last_accepted_utc` = `2026-09-20T05:27:50Z`
- Exit: normal — controller terminated after 580/580 accepted; fail-stop triggered only once for a pre-repair transient.

### The single transient FAIL (already repaired and ACCEPTED)

| Field | Value |
|---|---|
| run_key | `baseline__last_value_naive__L24__seedna__w1` |
| event | `FINALIZE_FAILED` |
| job_id | 572650 |
| utc | 2026-09-19T06:41:30Z |
| cause | D15 defect: deterministic baseline has no checkpoint; the finalize driver did not guard the arm and attempted `export_compact`. |
| resolution | v3.19 `REPAIR_FINALIZE_SKIP_TRAINING` reused job 572649; re-finalized via job 573391. |
| final state | **ACCEPTED** (included in 580/580) |

This is not a scientific failure; it is the documented, repaired D15 defect. Final ledger FAIL events = 0.

---

## 2. Identities

| Identity | Value |
|---|---|
| HPC guide SHA-256 | `1cd21a655907d137914c695bf04637d8da2f09358a0732c961e739dd8e74c167` |
| Source version | `innov-v3.19-baseline-no-checkpoint-finalization` |
| Source files | 139 |
| Source aggregate SHA-256 | `ae75b958b750e97c1ec9c0317ac80bf6fdc94ef979cfa280570540b0d889efaa` |
| Deployment members | 766 |
| Deployment aggregate SHA-256 | `05581a557158c0c19bb8e6caa1a5fb35fad889b774195616632cf62d9f4bcff6` |
| Canonical raw-data SHA-256 prefix | `0a0648000066e12f` |
| Scaler SHA-256 prefix | `6b28b2d101309a80` |
| Specs total / Wave 1 / Wave 2 | 598 / 580 / 18 |
| Deploy root | `/gpfs1/scratch/sychan552/innovation_deploy_root_v3_clean14` |
| Durable root | `/home/sychan552/innovation_durable/screening` |
| Deployment audit | 29 / 29 passed |

---

## 3. Artifact paths and hashes

### HPC governance artifacts (SHA-256)

| Artifact | SHA-256 |
|---|---|
| `accepted_keys.txt` | `cb2f0c120053faad561052dc703d0ea9bfe556102e42afb770610ba565c63007` |
| `formal_execution_order_wave1.txt` | `f037ae5b78e8ac37a9583bd3b5ae9f9639bf6333324477f7544d6396ee2f3262` |
| `wave1_ledger_v319.jsonl` | `45527ff09badb7c67b3bbe701c310e41ac13100b89c7de0be288ea2c019d70b6` |
| `wave1_ledger_v318.jsonl` | `7394faa1d0d0cc238260f178db4a7450f341c630bbac04679d6958129769d241` |
| `verify205_verification_ledger.jsonl` | `03084d444783ce41877295ee18f73feafbc4141aa4ced658d30a06359d578483` |
| `migration_ledger.jsonl` | `8b5188b388f88783d467dedcac352e8d2d65b41748b8e47d99f81525bfc5a0c8` |
| `bundle.zip` | `0e0b9275fe092b0b4bf8846bab6d762642713a9637d1cea1c25697a12cfee9ca` |
| `deployment_manifest.json` | `f10f81f66857f40d7ff1a0e453bfad5b68064666f4609901b57010b8933e5f40` |
| `controller_manifest.json` | `0b1c7b1f241054a7ce2699bd9a8f79bee8f857024cedaa94a5e1c08976d757ec` |
| `deploy_audit_v319.json` | `1ca29a13a0f8f06d9e96e823fcd34d349c947d9db509d158a7b0481b6dc08420` |

### Local governance artifacts (SHA-256)

| Artifact | SHA-256 |
|---|---|
| `results/v3_clean/implementation/source_manifest.json` | `95e30137f53d3d3a10a6453f0912883e7361afaada24593bd4bce4db3ac5b313` |
| `results/v3_clean/runs/complete_specs_598.json` | `a44aedce01e8c37a02792dea113ff2b3f118b37e236871f24dfbae896e4bcd0b` |
| `results/v3_clean/preregistration/paper_aligned_selection_rule.json` | `afa7a780010aeed20fd7a2d361300ae2ce4411baeed1d458581538d3df359325` |
| `results/v3_clean/analysis/frozen_analysis_protocol.json` | `cd229790fd0693334d79a1d63a38f06be8faf8cf30d83eb45c70603bc580fb6f` |

Per-run artifact paths, forms, `compact_bytes`, and per-package SHA-256 for all 580 durable packages are recorded in `wave1_final_artifact_inventory.csv`.

---

## 4. Reconcile summary

| Check | Result |
|---|---|
| Accepted set == immutable order set (580 identical keys) | **true** |
| Accepted sequence == order sequence | false (expected, see note) |
| Accepted == durable (580/580) | true |
| Arm breakdown matches (320/8/240/12) | true |
| Durable forms match (572 compact + 8 no-checkpoint) | true |

**Sequence note:** `accepted_keys.txt` is appended in execution order (205 earlier + 115 v3.18 + 260 v3.19). `formal_execution_order_wave1.txt` is the frozen matrix order. **Set equality (580 identical keys, no additions/removals/substitutions) is the binding invariant**; the sequence differs only because the v3.18 fail-stop + v3.19 repair of the D15 baseline row shifted its execution position.

---

## 5. Freeze declaration

- This step records **governance identity and provenance only**.
- **No new scientific result** is produced, and no Wave-1 scientific result is modified.
- Test access = 0; holdout access = 0 (unchanged).
- The complete list of 580 run keys is in `wave1_final_freeze_manifest.json` (`run_keys`) and cross-referenced in `wave1_final_artifact_inventory.csv`.
