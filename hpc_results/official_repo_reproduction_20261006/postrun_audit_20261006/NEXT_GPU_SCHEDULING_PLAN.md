# NEXT GPU SCHEDULING PLAN

Generated 2026-10-06. **Nothing here has been submitted.**

---

## 1. The two hard scheduler constraints

| Constraint | Source | Consequence |
|---|---|---|
| `MaxSubmit=1`, `MaxJobsPU=1` | `sacctmgr show qos partition-stingy` | **one job at a time**; a multi-element `--array` is rejected with `QOSMaxSubmitJobPerUserLimit` (observed on 606363) |
| scratch over quota, grace expired | `mmlsquota` | all outputs must go to `/gpfs1/home/sychan552/…` |

Both were encountered and worked around in the previous round, so the plan assumes them.

---

## 2. Submission pattern

```
for i in <from>..<to>; do
  sbatch --array=${i}-${i} <script>.sbatch     # exactly ONE element
  wait for that job to reach a terminal state
done
```

Helper prepared (not run): `slurm_r2/run_one_at_a_time.sh`.

**Do not** submit `--array=0-23`. It will be rejected and the round will be recorded as a
failed submission, which pollutes the run ledger for no benefit.

---

## 3. Option F1 — proposed schedule (24 GPU fits + 8 deterministic evals)

| Wave | Array indices | Content | Fits | Est. wall |
|---|---|---:|---:|---:|
| 1 | 0–3 | corrected text-active MIFlu, L=24/36/48/60 | 4 | ~40 min |
| 2 | 4–7 | matched no-text MIFlu, L=24/36/48/60 | 4 | ~40 min |
| 3 | 8–11 | NLinear, L=24/36/48/60 | 4 | ~10 min (linear models are fast) |
| 4 | 12–15 | DLinear, L=24/36/48/60 | 4 | ~10 min |
| 5 | — | Last-Value + Seasonal-Naive, 4 horizons each | 0 (deterministic, CPU) | ~2 min CPU |
| 6 | — | independent scoring + paired statistics | 0 | ~5 min CPU |

**Total ≈ 0.35 GPU-h, ≈ 0.42 h wall clock** including queue gaps.

Front-loading the two MIFlu arms is deliberate: the matched mechanism contrast
(full vs no-text) is the primary comparison, so if the round is interrupted the most
informative cells already exist.

---

## 4. Option P1 — proposed schedule (BLOCKED)

| Gate | Requirement | Status |
|---|---|---|
| G1 | reconstructed contract declared, per-parameter provenance labelled | ⚠️ partially — `HYPERPARAMETER_PROVENANCE_V2.md` exists, but Q12 pooling axes are `UNRECOVERED` |
| G2 | validation-only checkpoint selection replacing Test selection | ❌ not implemented in a runnable trainer |
| G3 | multivariate formulation (not the released single-channel slice) | ❌ the A2 implementation must be pointed at the author's entry point, or a corrected trainer used |
| G4 | predictions and targets persisted | ❌ not yet wired |
| G5 | independent scorer ready | ✅ `scripts/score_predictions_independent.py` |

**G2, G3 and G4 are all open.** P1 therefore must not be scheduled yet; the script
`slurm_r2/P1_a1p_pilot.sbatch` refuses to run and says so.

---

## 5. Ordering and stop rules

1. Run **F1** first (contract-complete, ~0.35 GPU-h).
2. Score F1 independently; confirm `wins_A + wins_B + ties == n_cells` on every pair.
3. Review F1's per-horizon winners for sign flips before drawing any conclusion.
4. Only then decide on P1 — and only after G2–G4 close.
5. **Stop rule**: if any array element exceeds **1.5×** the max measured per-fit time
   (i.e. > 0.44 GPU-h), stop the wave and report before continuing.

---

## 6. Ledger discipline for the next round

Every submission must append, per element:
`job id · array index · model · horizon · seed · start · end · exit code · checkpoint
path · prediction path`, and be reconciled against `sacct` afterwards (the method used in
`GPU_LEDGER_VERIFICATION.md`).

## 7. Confirmation

**No job was submitted in this continuation.** See
`FILE_INTEGRITY_AND_NONDELETION_CONFIRMATION.md` for the `squeue`/`sacct` evidence.