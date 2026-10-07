# Final Development Evidence Freeze (Deferred-Control Closure)

Generated UTC: `2026-09-21T02:52:38Z` — append-only closure package. No scientific result is changed.

## 1. Global reconcile — CLOSED

```text
Wave-1 accepted          = 580 / 580
Wave-1 durable packages  = 580
  primary                = 320
  baseline               = 8
  ablation               = 240
  negative controls      = 12
Wave-1 ledger final FAIL = 0
```

```text
Original deferred specs  = 18
Defect-A equivalents     = 12 / 12   (no rerun)
Defect-B newly executed  = 6 / 6     (timecma_llm llm_removed_or_alignment_only)
Defect-B finalized       = 6 / 6
deleted specs            = 0
silently skipped specs   = 0
duplicate observations   = 0
unresolved specs         = 0
Test access              = 0
Holdout access           = 0
```

```text
FINAL RECONCILE: 598 = 580 (w1 durable) + 12 (defect-A equivalent) + 6 (w2 durable)
```

## 2. Two evidence families (kept separate)

### Family A — gpt2_miflu zero_text / shuffled_text (12)
The 12 deferred `zero_text`/`shuffled_text` rows are **exact equivalents** of already-ACCEPTED
Wave-1 negative-control rows (identical `(control, parent_model=gpt2_miflu, horizon, seed)`).
Resolution: re-scoped as equivalents — **no rerun, no duplicated statistical observation**.

### Family B — timecma_llm llm_removed_or_alignment_only (6)
The 6 `llm_removed_or_alignment_only` rows were re-bound to `timecma_llm` (a lawful member of the
control's `applies_to` set, and the lowest `average_MSE_4L` among candidates), executed, finalized,
and ACCEPTED. L24/L60 x seeds 42/43/44.

**Rule: use matched-parent comparisons only; never pool Family A and Family B into one effect estimate.**

## 3. Six accepted amendment-B jobs (link to original runner jobs)

| horizon | seed | job_id | compact_sha256 | canonical_tensor_sha256 |
|---|---|---|---|---|
| L24 | 42 | 576502 | fc6ac24fee1ae2c3… | 05721beaf284cf8c… |
| L24 | 43 | 576507 | 83ece9d90fd97526… | 5f8e6efa76907d40… |
| L24 | 44 | 576509 | 5c651dcf73c67840… | 85b86c81a04fb861… |
| L60 | 42 | 576510 | a1b032354c1514f3… | 0e2e672268a1634c… |
| L60 | 43 | 576512 | 35a67868638fb7de… | 453fe86a255c2657… |
| L60 | 44 | 576513 | c7939ad75f03dcc4… | bb03680806d2bb36… |

All six packages carry: `parent_model=timecma_llm`, `control=llm_removed_or_alignment_only`,
amendment provenance, `compact.safetensors`, compact manifest, file SHA-256, canonical tensor
SHA-256, strict restoration evidence, prediction/metric equivalence, storage-verification OK,
atomic durable publication, and full redundant checkpoint removed only after acceptance.

## 4. Identities (unchanged)

```text
source_version          = innov-v3.19-baseline-no-checkpoint-finalization
source_n_files          = 139
source_aggregate_sha256 = ae75b958b750e97c1ec9c0317ac80bf6fdc94ef979cfa280570540b0d889efaa
deployment_member_count = 766
deployment_aggregate    = 05581a557158c0c19bb8e6caa1a5fb35fad889b774195616632cf62d9f4bcff6
canonical_raw_data      = 0a0648000066e12f…
scaler                  = 6b28b2d101309a80…
specs_total             = 598 (580 wave1 + 18 deferred)
deploy_root             = /gpfs1/scratch/sychan552/innovation_deploy_root_v3_clean14
durable_root            = /home/sychan552/innovation_durable/screening
```

## 5. Package files

- `final_development_evidence_freeze.json` — machine-readable closure record.
- `final_development_evidence_freeze.md` — this document.
- `final_development_artifact_inventory.csv` — 598 rows (580 wave1 + 12 defect-A + 6 defect-B).
- `final_development_hash_manifest.json` — SHA-256 of this package + upstream governance hashes.
