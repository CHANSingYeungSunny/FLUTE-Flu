# LEDGER APPEND — 2026-11-01 (MIFlu 10-rep / 7-var / hardware provenance)

These rows belong at the **end of `AGENTS.md` §10 LEDGER** (append, never rewrite).
They are kept here because `AGENTS.md` was being modified concurrently by another
agent while they were written, and a mid-table edit risked corrupting it.

---

| 2026-11-01 | 🐞 **AUTHOR-CODE DEFECT FOUND (new, publishable): `drop_last=True` on the TEST loader discards 10 of the 170 test windows.** `train_miflu.train_L` builds `el = DataLoader(TensorDataset(Xte, Yte), batch_size=16, shuffle=False, drop_last=True)` → 10 batches × 16 = **160 windows**, so every reported test metric in §1.1 (1.3045 / 1.3561 / 1.6543 / 1.6829) is computed on **91% of the test set**. Proven by recomputing the 7-variable aggregate from the new per-window exports: L24 seeds 2022–2025 give **1.201078 / 1.284212 / 1.259462 / 1.464643 on the first 160 windows**, matching the logged oracle to **≤4.3e-07**, while the full 170 windows give 1.686578 / 1.804358 / 1.816547 / 2.040191 (≈ +0.5). **This simultaneously validates the new 7-var exporter.** POLICY (approved 2026-11-01): report **two clearly-named metrics** — `mse_7var_z_author160` (Table V, author-faithful) and `mse_7var_z_full170` (benchmark axis, comparable with the 16 arms whose cells cover 170). Same weights, two evaluation sets; never presented as two models | `_hpc/blockA.sh` output; `train_miflu.py` test loader |
| 2026-11-01 | ✅ **Blocker B resolved — the two L24 seed-2021 checkpoints are BIT-IDENTICAL, so the legacy ILI-only CSV is the outlier, not the new export.** `md5sum` of `ckpt_L24_s2021/_rep_miflu_L24_seed2021.pth` and `ckpt_L24_s2021_pred/best_miflu_L24.pth` → both **`7cad20b30763f65b3b091f00109b02e7`**; state-dict bisection (job 719042): 104 tensors, same keys, **104/104 bit-identical**, top per-tensor `max|delta| = 0.000000e+00`, identical per-tensor sha256 → `VERDICT: SAME WEIGHTS`. Earlier the new export vs the legacy CSV gave `dGT=1.776e-15` (alignment perfect) but `dPRED=1.993`; since the weights are identical **and** the new export reproduces the logged oracle to ≤4.3e-07, the legacy file `author_runs/L24_s2021_pred/predictions_miflu_L24_paper_protocol.csv` is the suspect — it was written on 2026-10-31 by a run that was cancelled/restarted four times (logs 18:57, 19:30, 19:45, 19:57). **Retire it from the merge path** (do not delete). The all-7 export is authoritative | `_hpc/submit_bisect.sh` (job 719042) output |
| 2026-11-01 | ⏳ **NLinear A100 re-run scripted but QOS-blocked.** `code/submit_nlinear_a100.sh` re-runs the 12 NLinear cells on `stingy` A100, **preserving the old V100 cells** to `expanded_runs_v100_nlinear/` first, and aborts unless `torch.cuda.get_device_name(0)` contains `A100`. `sbatch` currently returns `QOSMaxSubmitJobPerUserLimit` because controller **719030** holds the slot; resubmit between requeues. After it lands: regenerate `BENCH_GPU_PROVENANCE.csv` and assert **204/204 A100, 0 non-A100**, recording the NLinear before/after deltas here | `code/submit_nlinear_a100.sh`; `sbatch` stderr |
| 2026-11-01 | **A100 controller 719030 hardware gate passes on every requeue**: `[a100] MEASURED gpu=NVIDIA A100-SXM4-80GB capability=(8, 0) vram=79.2GiB`; L24 export pass runs on GPU so its manifests carry A100 provenance too (no CPU-forward numbers in the table) | `slurm-miflu-a100-719030.out` |

---

## Also to record in §2 rule 13 (publication-grade runtime policy)

Rule 13 was added by the parent while this work was in flight. Its operative
consequence for this task: **every MIFlu rep must be A100/`stingy`**, the 12
NLinear cells on V100 are invalid and must be re-run, and any diagnostic run on
another partition is `probe_only=True` and may never enter `paper_tables/*`.

## Outstanding before any MIFlu number is publishable

1. Controller **719030** must finish the 27 fresh reps (L36 9, L48 9, L60 9) and
   export all four rule-11 artefacts per cell.
2. Implement the dual metric `mse_7var_z_author160` / `mse_7var_z_full170` and
   recompute the MIFlu row on both bases.
3. Re-run the 12 NLinear cells on A100; regenerate `BENCH_GPU_PROVENANCE.csv`;
   assert 204/204 A100.
4. Then and only then: `import_miflu_predictions.py --check` (must report
   **7/7 channels, partial=False**), `analysis_expanded.py`,
   `verify_bench_unchanged.py` (must print `RESULT: PASS`), `plot_bench.py`.
5. Do **not** use `author_runs/L24_s2021_pred/predictions_miflu_L24_paper_protocol.csv`
   as the L24 row.

---

## DECISIONS RECORDED 2026-11-01 ~19:10 (HKT)

1. **`docs/STATE.md` §1.1 stands unchanged** (160-window, like-for-like with the
   paper). One disclosure block added after the MAE line, not a restatement.
2. **`docs/AUTHOR_REPO_FIDELITY.md` §3 gained the `drop_last` defect entry** with the
   measured severity: final 10 of 170 windows are ~1.41x harder (ratio 1.3929-1.4423
   over four L24 seeds, mean 1.4111), so published MIFlu numbers are optimistic by
   ~40% relative to a full-test-set evaluation.
3. **The MIFlu benchmark row uses `mse_7var_z_full170`** (mandatory, because the 16
   arms cover 170 windows). The table note must state BOTH numbers with their window
   counts: `mse_7var_z_author160` (Table V, author-faithful) and
   `mse_7var_z_full170` (benchmark axis).
4. The legacy `author_runs/L24_s2021_pred/predictions_miflu_L24_paper_protocol.csv`
   is SUPERSEDED and must not enter the merge path (evidence in
   `docs/MIFLU_MERGE_BLOCKED_20261101.md`). Do not delete it.
5. This file is the temporary ledger target while another agent restructures
   `AGENTS.md` into an index with `docs/LEDGER.md`; **do not edit `AGENTS.md` §10
   while that runs.** Merge these rows after the restructure lands.

### PROJECTION (NOT A RESULT) — MIFlu on the 170-window benchmark axis

Applying the single measured ratio 1.4111 to the author-160 10-rep means gives a
**placeholder projection only**:

| L | author160 (measured, 10 reps) | full170 (PROJECTED) |
|---|---:|---:|
| 24 | 1.3045 | ~1.84 |
| 36 | 1.3561 | ~1.91 |
| 48 | 1.6543 | ~2.33 |
| 60 | 1.6829 | ~2.38 |
| mean | 1.4995 | ~2.11 |

**This must not be quoted as a result.** Extrapolating with one ratio assumes the
last-10-window difficulty is constant across horizons, which has NOT been measured —
only four L24 seeds were available. The real per-horizon `full170` means must come
from the finished 10-rep exports.

**If the projection holds**, the consequence changes the paper's story and must be
stated, not softened: on the benchmark axis MIFlu (~2.11) would **not** beat
PatchTST (1.9613) or NLinear (2.0495) — the paper's own method would finish
**third**. The exact ranking position will be reported from the real numbers.
