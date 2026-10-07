# FINAL EXECUTION REPORT (English)

Generated 2026-10-06. Directory: `hpc_results/official_repo_reproduction_20261006/postrun_audit_20261006/`
This continuation: **read-only inspection + CPU-only Slurm audits + new files only.**
**Nothing was deleted. No GPU job was submitted.**

---

## A. Executive conclusion

| Item | Label | Note |
|---|---|---|
| **A0-R** released-code behaviour audit | `PARTIAL` | four horizons ran on the author's entry point (1 repetition each); text-path inertness proven on two device types; full 10-repetition replay not done |
| **A1-P** paper reconstruction | `BLOCKED_BY_MISSING_INFORMATION` | contract audited, but **no A1-P run exists**; Q12 (pooling axes) is `UNRECOVERED` |
| **A1-P 10 repetitions** | `BLOCKED_BY_GPU_QUOTA` | measured 0.2769 GPU-h/fit; 40 fits ≈ 11.08 GPU-h; 0.05639 remains |
| **A2-F** fair comparison | `NOT_STARTED` | contract written in full (S1–S20); no run |
| **Historical Track B** | inventory complete | recoverability verdict: **not recoverable as a runnable deployment** |
| **Paper reproduction** | **NOT ACHIEVED** | Tables V–IX and Figures 3–7: **0 reproduced** |
| **Best-model question** | answerable only within the A2 basis | see §H and `../benchmark_best_model_summary.csv` |

**In one line**: this round settled what can and cannot be done, and why — including a
storage finding that **overturns an earlier estimate by ~2,900×** (§G) and a seed finding
that **overturns an earlier claim** (§D).

---

## B. Repository lineage

The single hard boundary (filesystem-proven, not recalled):

```
2026-09-24 09:54:29 +0800   clone: from https://github.com/Jmoon3108/MIFlu.git
                            HEAD = 6ed210150b8819313947cf607eb1821c87b1bee3
```

| Lineage | Window | Basis |
|---|---|---|
| **Historical Track B** (self-built) | 2026-08-05 … **2026-09-21** | mtimes of `analysis/`, `results/innovation`, `results/v3_clean`, and **all 19 `innovation_deploy_root_v3_*` directories have latest mtimes ≤ 2026-09-21** |
| **Official-repository lineage** | 2026-09-24 → 2026-10-06 | clone log + job records |

**The Track-B classification is therefore filesystem-proven** — every directory predates
the clone by at least 2 days 21 hours. Facts resting on recollection alone are labelled
`USER_CONFIRMED` in `HISTORICAL_AND_OFFICIAL_TIMELINE.csv`.

---

## C. Released-code text-path result

### Classification: `RELEASED_TEXT_PATH_INACTIVE`

**Wording, verbatim**: the author's released implementation **did not show functional
dependence on textual content under deterministic equal-length intervention testing.**

| Run | Device | Equal-length swap `max\|Δpred\|` | `\|grad_text\|` | `\|grad_ts\|` (control) | Verdict |
|---|---|---:|---:|---:|---|
| local | Win CPU | **0.0** | **0.0** | 0.0328 | `text_inert` |
| 606357 | HPC CPU | **0.0** | **0.0** | 0.0404 | `text_inert` |
| **606358** | **A100-80GB** | **0.0** | **0.0** | 0.0404 | `text_inert` |
| positive control | CPU / A100 | 5.34e-05 / 5.29e-05 | — | — | **detects** |

- HPC CPU and A100 produce **identical parameter SHA-256** (`d7ad42ee…`) → bit-reproducible
  across devices
- comparison job **606360** machine-checked `CPU/GPU verdicts AGREE`
- the **non-zero time-series gradient is the key control**: the measurement chain works, so
  the zero text gradient is a **real zero**

**The earlier A0 GPU "text works" signal is explained**: `multimodal 0→1` changes the
sequence length (42→359) and therefore the **training-time dropout random stream**; at fixed
weights in eval mode the two differ by **2.384185791015625e-07** = 2·ε(float32), i.e.
**mathematically equivalent**.

**Must not be overstated** as: text never useful · the paper's method cannot work ·
multimodal forecasting is generally ineffective.

---

## D. The four completed runs, reclassified

**Correct label: `A0-R released-code feature-0 replay, single run per horizon`. NOT A1-P.**

| L | author `mse_mean` (**final-epoch** Test MSE, itr=1) | best-epoch MSE | Wall | Job |
|---:|---:|---:|---:|---|
| 24 | **0.5793** | 0.5344 @ep8 | 17:34 | 606365_0 |
| 36 | **0.5920** | 0.5387 @ep10 | 16:54 | 606378_1 |
| 48 | **0.6088** | 0.6069 @ep16 | 16:18 | 606385_2 |
| 60 | **0.6361** | 0.5933 @ep5 | 15:42 | 606412_3 |

> ⚠️ The earlier report printed the **mean over 20 epochs** (0.6044/0.6028/0.6571/0.6545)
> under the label `mse_mean`. **They are different quantities**
> (`STATUS_CORRECTION_ADDENDUM.md` C-1).

**Why it is not a Table V reproduction**: one channel only (`% WEIGHTED ILI`),
**Test-selected checkpoint**, 1 of 10 repetitions, undisclosed epochs/lr, and **the released
code saves no predictions** (`np.save` commented out → independent re-scoring impossible).

**Two new findings, each independently re-verified**:

1. **`feat_id=[0]` is worse than "Test is broken"**: `__getitem__` slices
   `feat_id:feat_id+1`, so **every sample in every split is a univariate `(T,1)` window**;
   `__len__` omits the `× enc_in` factor for Test, so Test always covers channel 0 only.
   **The released code never forms a seven-variable window** (A0 log: `test shape: (160,24,1)`).
2. **`--itr 10` would NOT be duplicate runs**: the seed is fixed once at module level
   (L27-30), but the global RNG advances → each iteration gets a **different**
   initialisation (measured locally: `itr0 == itr1 → False`). The real limitation is that
   repetitions are **not addressable by seed**, not that they are identical.

---

## E. Paper contract

Full audit: `PAPER_EVALUATION_CONTRACT_AUDIT.md` (15 questions + §V-C).

| Classification | Items |
|---|---|
| `PAPER_EXPLICIT` | Q1 seven-variable task, Q2 variable roles, Q5 arithmetic mean of 10 repetitions, Q13 equal-weight four-horizon mean (1.542+1.422+1.414+1.364)/4 = 1.4355 ✓ |
| `CODE_EXPLICIT` | Q11 standardized space throughout, Q14 `mse_mean` semantics |
| `CONFLICTING_EVIDENCE` | Q3 feat_id, Q8 the "Paper: 20 epochs / 5e-4" mislabel, Q10 aggregation vs Table V, Q15 contract matchability |
| `UNRECOVERED` | Q4 checkpoint rule, Q6 the 10 seeds, Q12 pooling axes, §V-C provenance of MIFlu's own column |
| `LOG_INFERRED` | Q9 LR decay (measured `0.00019371…` = 5e-4 × **0.9**⁹) |

**Two errors that must be stated**:

- "20 epochs / lr 5e-4 = paper settings" has **no source**. The paper says only "set
  empirically" (L298) with **no numbers**; the released defaults are 1 epoch / 1e-4. The
  values originate in the project's own `scripts/configs.py`.
- the LR schedule uses a **hard-coded 0.9** (`tools.py` L26-27); **`--decay_fac 0.75` is
  inert on that path**.

---

## F. Historical deployment (Track B)

19 directories, all `UNSAFE_TO_DELETE`.

| Property | Value |
|---|---|
| total apparent size | **204.6 GiB** (219,722,194,209 B) |
| actual disk usage | **204.6 GiB — identical**, because there are **0 symlinks and 0 hard links** |
| files | 27,019 |
| checkpoint-like files | 594 (447 `.pt` + 147 `.safetensors`) = **201.7 GiB** |
| largest consumer | **qwen 138.07 GiB** (33 files) |
| **Qwen reduction** | full checkpoint **5.75 GiB** → compact export **1.41 MiB** = **4,167×** |
| Qwen dependencies | the compact export is too small to contain a 1.5 B base → **the base must be external**; tokenizers and configs: **0 files each** inside the family |
| predictions | **0 `.npy`** → Track B **cannot be independently re-scored** |
| entry command | **absent** (no launch script, README or CI config) |
| strongest final candidates | `v3_clean14` (**latest mtime in the family**, 2026-09-21T04:56:42Z), `v3_clean6` (largest, 52 GiB), `v3_5` (50 GiB) |

**Reduction techniques**: 10 `EVIDENCE_SUPPORTED`, 2 `RULED_OUT` (**symlinks and hard
links — both measured at 0**), 6 `NOT_EVIDENCED` (**INT8 / INT4 / GPTQ / AWQ /
bitsandbytes all unsupported**), 6 `UNKNOWN` (including fp16/bf16 conversion, which would
require reading tensor headers — deliberately not done).

---

## G. Storage accounting — **the finding that overturns an earlier estimate**

| Method | Basis | Estimated reclaimable | Verdict |
|---|---|---:|---|
| naive | same size **and** same basename | **186.7 GiB** | ❌ **wrong by ~2,900×** |
| **full SHA-256** | byte-identical content | **66.7 MiB** | ✅ verified |

**All 594 checkpoint files hashed**: 565 distinct SHA-256, only **28** identical-content
groups, **66.7 MiB reclaimable = 0.032 % of the family**.

The single strongest piece of evidence:

```
files larger than 5 GB        : 24
distinct SHA-256 among them   : 24   -> ALL DIFFERENT
combined size                 : 138.06 GiB
```

Those 24 files *are* the entire Qwen footprint — **not one is a duplicate**.

Small files (< 4 MiB; 20,792 of them) yield a further **245.9 MiB**.
**Total reclaimable ≈ 312.6 MiB.**

> **Consequence**: scratch is at **413 GB against a 300 GB quota (grace expired)**, and
> deduplication would recover **0.1 % of the overage**. Relieving the quota requires
> deleting **real historical runs** — a scientific and authorization decision, not
> housekeeping. **Nothing was deleted.**

---

## H. GPU ledger (independently recalculated)

Source: `sacct` captured live inside CPU-only job 606430. Per-job table:
`GPU_LEDGER_VERIFICATION.csv`.

| Phase | Jobs | GPU-h |
|---|---:|---:|
| stage5 (in-window; charged to the earlier 2.0 cap) | 6 | 0.16583 |
| stage6 | 33 | **1.12555** (COMPLETED 1.04999 + FAILED 0.07556) |
| previous continuation (2026-10-06) | 6 | **1.11806** |
| **prior total** | 39 | **2.24361** |
| authorised cap | — | 2.30000 |
| **remaining** | — | **0.05639** |

**The previously reported 2.24366 is confirmed** (recomputed 2.24361; gap 0.00005 =
rounding).

**Inclusion**: ✅ successful runs · ✅ failed runs · ✅ A100 probes · ✅ array elements
(counted individually) · ✅ retries; ➖ cancelled-before-start jobs charge 0; ❌ **the
0.16583 of in-window stage5 work is NOT part of the 2.3** (it belongs to the earlier cap).

**Cost of 40 fits** (from the four measured times 942/978/1014/1054 s):

| Estimator | per fit | 40 fits | remaining 36 |
|---|---:|---:|---:|
| **mean** 0.2769 h | 0.2769 | **11.08** | **9.97** |
| median 0.2767 h | 0.2767 | 11.07 | 9.96 |
| max 0.2928 h | 0.2928 | 11.71 | 10.54 |

**This corrects the earlier "≈11.27 GPU-h"**, which averaged in a 7-second failed attempt
and was therefore **~0.19 high**. The 11.27 figure referred to **all 40 fits**, not the
remaining 36.

**Retry-buffer budgets (additional allowance needed)**:

| Target | +0 % | +5 % | +10 % | +20 % |
|---|---:|---:|---:|---:|
| remaining 36 fits (mean) | 9.91 | **10.41** | 10.91 | 11.91 |
| all 40 fits (mean) | 11.02 | **11.53** | 12.03 | 13.02 |

---

## I. A2 text-active magnitude audit

**Classification: `TEXT_ACTIVE_BUT_MAGNITUDE_REQUIRES_CAUTION`** — specifically, the
**previously reported magnitude was a probe defect**.

| Quantity | v1 (raw input — defective) | **v2 (standardized input — correct)** | Factor |
|---|---:|---:|---:|
| different prompt, same length, `max\|Δpred\|` | 59.6875 | **6.518e-04** | ≈9.2e4 |
| row-permuted, `max\|Δpred\|` | 6308.3 | **6.525e-02** | ≈9.7e4 |
| `\|grad_text\|` | 7.13e+08 | **0.025178** | ≈2.8e10 |
| prediction range | set by the raw input scale | **[-0.828, +1.717]** (z-space) | — |

**Root cause**: `MIFlu.forward` requires `x` **already in StandardScaler space**, but the v1
probe fed **raw values** (OT ≈ 176 569). The forward pass ends in RevIN
(`y_hat_rev = y_hat_norm × stdevs + means`), so the input scale amplified everything.

**The two questions, answered separately**:
1. **Does text influence the A2 prediction?** **YES** — v1 and v2 agree (`text_active`).
2. **Is the magnitude stable and interpretable?** **v1's was not; v2's is** — a different
   prompt moves the output ~0.09 % of the signal, a row permutation ~9 %, an ordering that
   behaves as expected.

**The conclusion is not reversed**: A2's text path is functional, so the benchmark's
full-vs-no-text contrast is a genuine text-content contrast. Only the **magnitude** is
corrected.

---

## J. Paired-statistics correction

**The correction is verified.** The original `paired_stats.py` win counter incremented on
the opposite condition from the one its own header describes.

Four unit tests pass (`paired_stats_unit_test_results.txt`, exit 0): A better everywhere →
wins all; A worse everywhere → wins none; a mixed hand-computed case matches; and a
**regression guard** on the real `miflu − nlinear` cell differences (correct 7, inverted
counter 5).

| Comparison | Originally written | **Correct** |
|---|---|---|
| MIFlu vs NLinear | 5/12 | **7/12** |
| no-text vs NLinear | 1/12 | **11/12** |

Every row asserts `wins_A + wins_B + ties == n_cells`. **Mean differences and t statistics
are unaffected**; the old report **was not modified**.

---

## K. Next GPU decision

| Option | Content | Fits | GPU-h (mean) | Verdict |
|---|---|---:|---:|---|
| **A** | 10 repetitions of the released-code protocol (P3) | 40 | ~11.08 | ❌ **not recommended**: 8 of 9 contract items fail to match — it would measure the wrong quantity precisely |
| **B** | corrected A1-P pilot (P1/P2) | 4 / 8 | ~1.11 / 2.22 | ⚠️ **currently blocked**: gates G2/G3/G4 open (validation selection, multivariate formulation, prediction persistence) |
| **C** | **core A2-F benchmark (F1)** | 24 | **~0.35** | ✅ **recommended first**: highest scientific value per GPU-hour, contract-complete, answers the stated objective |

**Recommendation: do C (F1) first, at ~0.35 GPU-h** (6 models × 4 horizons × 1 seed). It is
cheap enough to request immediately and does not depend on resolving the paper-contract
questions.

**Then** choose between P1 and P2 — **not P3**. P3 becomes meaningful only once
(a) a recovered contract exists, (b) validation selection replaces Test selection, and
(c) predictions are persisted.

Scripts **prepared, not submitted**: `slurm_r2/F1_a2f_core.sbatch`,
`slurm_r2/P1_a1p_pilot.sbatch` (**self-blocking; it refuses to run**),
`slurm_r2/run_one_at_a_time.sh` (accommodates `MaxSubmit=1`).

---

## L. Claims still not supported

- ❌ "the paper was reproduced" — **0 paper numbers reproduced**
- ❌ "A0-R's 0.53 beats the paper's 1.5" — **different measurement** (1 channel vs 7,
  Test-selected, 1 vs 10 repetitions)
- ❌ "20 epochs / 5e-4 are the paper's settings" — **no source**; they are
  `RECONSTRUCTED_ASSUMPTION`
- ❌ "text adds value" (of the released code); ❌ "text is irrelevant" (of A2)
- ❌ "LLMs are better/worse overall" — the two tracks point in opposite directions and the
  group mean contradicts the best individual
- ❌ any cross-track absolute MSE comparison (Track A / Track B / A0-R / July-2026)
- ❌ "Historical Track B is official-repository output", or usable as an A2-F result
- ❌ "the historical Qwen checkpoints were quantized" — **no evidence** (INT8/INT4/GPTQ/AWQ
  all absent)
- ❌ "adding 10 repetitions would reproduce Table V"

---

## M. Preservation confirmation

**No protected file was deleted, moved, renamed, compressed, truncated, overwritten or
modified.**

| Evidence | Result |
|---|---|
| SHA-256 snapshot of 66 pre-existing deliverables taken before any work | **66/66 byte-identical**, 0 changed, 0 missing |
| five historical result trees, file counts | `results/v3_clean` 1485, `stage6` 60, `stage5_a2` 148, `audit_20260930` 171, `recovery` 212 — **all unchanged** |
| 19 `innovation_deploy_root_v3_*` directories | **still 19**, none renamed, mtimes unchanged (all ≤ 2026-09-21) |
| local git | 49 M / 9 D / 179 ?? — **identical to before this work** |
| GPU jobs this continuation | **2, both CPU-only** (606430, 606432), **0 GPU-hours** |
| queue | `squeue` **empty** |
| scratch cleanup | **not performed** |

Full detail: `FILE_INTEGRITY_AND_NONDELETION_CONFIRMATION.md`.