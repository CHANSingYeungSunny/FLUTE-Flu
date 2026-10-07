# NEXT GPU SCRIPT MANIFEST

Generated 2026-10-06. **Every script below is PREPARED and NOT SUBMITTED.**

---

## 1. Scripts written this round

| File | Option | Fits | Purpose | Syntax-checked | Submitted |
|---|---|---:|---|---|---|
| `slurm_r2/F1_a2f_core.sbatch` | **F1** | 24 (4 models × 4 horizons) + 8 deterministic | core A2-F fair benchmark | ✅ | **NO** |
| `slurm_r2/P1_a1p_pilot.sbatch` | **P1** | 4 | A1-P minimum pilot — **refuses to run** until gates G2–G4 close | ✅ | **NO** |
| `slurm_r2/run_one_at_a_time.sh` | helper | — | sequential submitter for `MaxSubmit=1`; submits nothing on its own | ✅ | **NO** |

Pre-existing scripts, for reference only (from the previous round, already executed):
`slurm/miflu_a1_array.sbatch` (A0-R), `slurm/probe_text_path_{cpu,gpu}.sbatch`,
`slurm/probe_text_path_compare.sbatch`, `slurm/diag_peft_lora.sbatch`.

---

## 2. Wiring steps still required before F1 can be submitted

`F1_a2f_core.sbatch` currently pins the contract and the provenance block but **does not
call a trainer** — deliberately, so that an unverified invocation cannot run.

To make it submittable:

1. **Point it at the trainer.** The A2 protocol already exists in
   `scripts/train_backbone_966.py` (`--containment strict`, validation selection,
   seven variables). Confirm the exact flags for `miflu_fixed`, `notext`, `nlinear`,
   `dlinear`.
2. **Add prediction persistence (contract S15).** The trainer must write, per run,
   arrays of `(origin, lead, variable)` predictions and targets. **Without this the run
   is not A2-F** — the released code does not persist predictions, and the whole point of
   the contract is that the result can be independently re-scored.
3. **Point the scaler at train rows only** (`[0,676)`), which is contract S3.
4. **Declare the seed list** (S10) — F1 uses `seed=42`; F2 would add 43, 44.
5. **Verify `drop_last=False`** on the validation and Test loaders (S14).
6. **Copy the author 966-row file** into the run root or reference it by absolute path
   (`/scratch/sychan552/a0_replay/dataset/illness/national_illness.csv`, currently
   referenced read-only; note scratch is over quota but **reads** are unaffected).

Each step is a small edit to an existing, tested script. None requires new model code.

---

## 3. Wiring steps still required before P1 can be submitted

| Gate | Step |
|---|---|
| G2 | implement validation-only checkpoint selection in a runnable A1-P trainer (the released harness selects on Test) |
| G3 | use a **multivariate** formulation — the released loader slices a single channel (`data_loader.py:305`) |
| G4 | persist predictions and targets |

Until these close, P1 stays blocked; the script enforces that by exiting immediately.

---

## 4. Conventions every future submission must follow

1. **One array element per submission** (`MaxSubmit=1`). Multi-element arrays are rejected.
2. **All outputs under `/gpfs1/home/sychan552/…`** (scratch is over quota).
3. **Append a ledger row per element**: job id, index, model, horizon, seed, start, end,
   exit, checkpoint path, prediction path.
4. **Reconcile against `sacct`** afterwards, as in `GPU_LEDGER_VERIFICATION.md`.
5. **Never run anything on a login node.** Every script here refuses if
   `hostname` matches `hpclogin*`.
6. **Never label an A0-R output as A1-P or A2-F.** See `TRACK_SEPARATION_RULES.md`.

---

## 5. Confirmation

Three scripts prepared, zero submitted. No GPU-hour was consumed in this continuation.