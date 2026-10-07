# F1 SUCCESS GATES

Generated 2026-10-06. Implemented in `f1_score_all.py` and reported in
`f1_gate_report.json`. A gate is a machine check, not a judgement call.

## 1. The seven gates

| Gate | Checks | Failure means |
|---|---|---|
| **G1** | all six models present | at least one arm produced nothing |
| **G2** | all four horizons present for every model | an incomplete matrix |
| **G3** | zero rejected artefacts | malformed, off-contract, Track-B, or Test-selected input |
| **G4** | forecast keys consistent across models | models are not being scored on the same quantity |
| **G5** | exactly the one pilot seed present | seed mixing, or a seed leaked in from another track |
| **G6** | no missing (model, horizon) cell | same as G1/G2 but reported numerically |
| **G7** | pairwise partition invariant holds (`wins_A + wins_B + ties == n_cells`) | the paired statistics are unsound |

## 2. Status values

| Status | Meaning |
|---|---|
| `COMPLETE` | G1–G7 **all** pass |
| `INCOMPLETE_INTEGRITY_OK` | G3/G4/G5 pass but the matrix is incomplete — partial results may be reported, F1 is **not** complete |
| `PARTIAL_DRY_RUN_INTEGRITY_OK` | a deliberate dry run over a subset (`--allow-partial`) |
| `FAILED_INTEGRITY` | at least one of G3/G4/G5 failed — **no ranking should be relied on** |

## 3. Completion criteria from the brief, mapped

The brief lists ten conditions for marking F1 COMPLETE. Each maps to a gate or a
separate check:

| Brief condition | Covered by |
|---|---|
| all six models produce required outputs | G1 |
| all four horizons covered | G2, G6 |
| all models use the same forecast keys | G4 |
| prediction and target files saved | S15/S16 — verified because scoring reads them; absence shows up as a missing cell |
| no Test data selects checkpoints | S12 (`DEFER_TEST=1`) + the Test-selection rejection in `scorer_f1` (acceptance test A13) |
| independent scoring succeeds | `f1_score_all.py` exit code 0 |
| corrected MIFlu text pathway remains active | separate check on the selected checkpoint — see §4 |
| no-text MIFlu correctly classified | `F1_MODEL_IDENTITY.csv` labels it **LLM-based unimodal**; category 2 |
| no Historical Track B artifact mixed in | `scorer_f1` rejects Track-B profiles (acceptance test A10) |
| all job IDs and resource usage recorded | `f1/manifests/GPU_LEDGER_F1.tsv`, reconciled against `sacct` |
| no output written to over-quota scratch | every path points at `$HOME`; documented in `F1_STORAGE_BUDGET.md` |
| no missing or duplicate key | G6 + the duplicate-key check in the scorer (acceptance test A6) |

## 4. The one check that is not a gate

**Text-path activity** is verified by re-running the deterministic probe on the
selected corrected-MIFlu checkpoint. This is a *separate* step (submission step 10 in the
brief's list) because it needs a fitted checkpoint. It reuses
`../probe_a2_text_path_v2.py`, which was corrected this round to feed **StandardScaler
space** input — the v1 probe fed raw values and inflated every magnitude by 5–10 orders.

Gate G1 does not depend on it, but the COMPLETE claim does, so it is listed here as a
post-run requirement.

## 5. If a trained model fails

Per the brief: **mark F1 PARTIAL and do not present a final pilot ranking as complete.**

Concretely:
- if a GPU arm fails, its checkpoint is absent, its artefact is absent, and G1/G2/G6 fail;
- the correct report is `INCOMPLETE_INTEGRITY_OK` (if integrity checks still pass) or
  `FAILED_INTEGRITY`;
- a ranking computed over the surviving arms may be shown **only** with the missing cells
  named beside it, and must not be described as the pilot result.

## 6. What even a fully passing F1 does NOT support

This is the most important section. One seed means:

| Claim | Supported by F1? |
|---|---|
| F1 is executable and contract-compliant | ✅ yes |
| forecast keys are consistent across the six models | ✅ yes |
| the independent scorer is correct | ✅ yes |
| the corrected MIFlu text path is active | ✅ yes |
| a **preliminary** one-seed ordering | ✅ yes, labelled preliminary |
| statistically reliable best model | ❌ **no** |
| stable model superiority | ❌ **no** |
| significance of any difference | ❌ **no** |
| seed robustness | ❌ **no** |
| final LLM-versus-non-LLM superiority | ❌ **no** |

**Title**: "A2-F Core Fair-Benchmark Pilot, One Seed". **Never** "the final A2-F
comparison".
