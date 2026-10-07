# STATUS AFTER CONTINUATION — V2 (revised timestamped copy)

Generated 2026-10-06. **This is a NEW file. `../STATUS_AFTER_CONTINUATION.md` is unchanged.**

Supersedes the original as the current status. Read together with
`STATUS_CORRECTION_ADDENDUM.md` (corrections C-1 … C-8) and
`FINAL_EXECUTION_REPORT_ZH.md` / `_EN.md`.

## 1. What changed since the original status report

| # | Original said | Now |
|---|---|---|
| 1 | `mse_mean` for the four runs = 0.6044/0.6028/0.6571/0.6545 | those are **means over 20 epochs**; the author's `mse_mean` is the **final-epoch** value: **0.5793/0.5920/0.6088/0.6361** |
| 2 | A2 text influence `max\|Δpred\|` = 59.7, `\|grad_text\|` = 7.13e8 | **6.518e-04 / 6.525e-02, grad 0.0252** — the old figures were a probe defect (raw, unstandardized input). Verdict still `text_active` |
| 3 | LR schedule "type1 exponential decay, decay_fac=0.75" | **hard-coded 0.9 from epoch 4**; `decay_fac` is inert (`5e-4 × 0.9⁹` matches the log exactly) |
| 4 | "Test covers feature 0 only" | **all splits are univariate `(T,1)`**; the released code never builds a seven-variable window; Test evaluates channel 0 only |
| 5 | the four runs tagged `A1_reconstructed_paper_config` | reclassified **A0-R released-code feature-0 replay, single run per horizon** |
| 6 | "10 repetitions would cost ~11.27 GPU-h" | **11.08** (mean) / 11.71 (max); 11.27 averaged in a 7-second failed attempt |
| 7 | `innovation_deploy_root_v3_*` ≈ 190-219 GB, dedup potential implied | **204.6 GiB, of which only 66.7 MiB (0.032 %) is byte-identical.** The naive 186.7 GiB estimate is refuted |
| 8 | — | **NEW**: the seed is set once but the RNG advances, so `--itr 10` would NOT produce duplicates |
| 9 | — | **NEW**: the released code saves **no predictions** (`np.save` commented out), so its scores cannot be independently re-scored |
| 10 | — | **NEW**: the historical family contains **0 symlinks and 0 hard links**, so apparent size == actual size |

## 2. Current status of every track

| Track | Label |
|---|---|
| A0-R released-code behaviour audit | `PARTIAL` |
| Released-code text-path resolution | **`COMPLETE`** (CPU + A100 agree; positive control included) |
| A1-P paper reconstruction | `BLOCKED_BY_MISSING_INFORMATION` |
| A1-P 10 repetitions | `BLOCKED_BY_GPU_QUOTA` |
| A2-F fair benchmark | `NOT_STARTED` (contract complete) |
| Historical Track B preservation | `COMPLETE` for inventory; recovery **not** executed |
| Paper Tables V–IX, Figures 3–7 | `NOT_STARTED` |
| **Paper reproduction** | **NOT ACHIEVED — 0 paper numbers reproduced** |

## 3. GPU state (unchanged)

```
cap 2.30000   used 2.24361 (verified)   remaining 0.05639
```

This continuation submitted **2 CPU-only jobs** (606430, 606432) → **0 GPU-hours**.
Queue empty.

## 4. Next action

Recommended: **Option F1**, the core A2-F benchmark, **~0.35 GPU-h**.
Scripts prepared, not submitted: `slurm_r2/`.

## 5. Preservation

66/66 pre-existing deliverables byte-identical; five historical result trees unchanged;
19 `innovation_deploy_root_v3_*` directories unchanged; git state identical.
See `FILE_INTEGRITY_AND_NONDELETION_CONFIRMATION.md`.
