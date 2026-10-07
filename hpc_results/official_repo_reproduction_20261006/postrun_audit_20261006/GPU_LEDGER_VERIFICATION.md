# GPU LEDGER VERIFICATION

Generated 2026-10-06. **Independent recalculation**: every figure below is derived
from `sacct -S 2026-09-26 -X -P -o JobID,JobName,Partition,State,Elapsed,AllocTRES`,
captured live in a CPU-only Slurm job (606430), not taken from any saved summary.
Raw capture: `hpc_out/sacct_gpu_jobs.psv` (45 GPU jobs).
Per-job table: `GPU_LEDGER_VERIFICATION.csv`.

---

## 1. Rule used

```
gpu_count  = the gres/gpu:<type>=N value in AllocTRES   (1 for every job here)
gpu_hours  = gpu_count * elapsed_seconds / 3600
```

Only jobs holding `gres/gpu` are counted. CPU-only jobs (probe CPU half, PEFT
diagnostic, comparison job, both audit jobs) hold **no** GPU and contribute
**exactly 0** — they cannot consume GPU quota by construction.

---

## 2. Verified totals

| Phase | Jobs | GPU-hours |
|---|---:|---:|
| stage5 (within the 2026-09-26 window) | 6 | 0.16583 |
| stage6 | 33 | **1.12555** |
| 2026-10-06 continuation | 6 | **1.11806** |
| **stage6 + continuation** | 39 | **2.24361** |

### Reconciliation with the previously reported figure

| | Value |
|---|---|
| Previously reported | **2.24366** |
| Independently recomputed | **2.24361** |
| Difference | **0.00005 GPU-h** (0.18 seconds) |

**The prior figure is confirmed.** The 0.00005 gap is rounding to 5 decimals
across 39 jobs.

### stage6 decomposition

| Category | GPU-hours |
|---|---:|
| COMPLETED | 1.04999 |
| FAILED | 0.07556 |
| **total** | **1.12555** |

---

## 3. What the 2.24366 figure does and does not include

The brief asks this explicitly. The answer:

| Category | Included? | Detail |
|---|---|---|
| **Successful runs** | ✅ yes | the 26 completed stage6 fits + scoring, and the 5 completed continuation jobs |
| **Failed runs** | ✅ **yes** | stage6 FAILED jobs (587048/587054/587059/587068/587070/587373/587385) = 0.07556; the failed A1 attempt 606361_0 = 0.00194 |
| **A100 probes** | ✅ yes | job 606358 (text-path probe, A100 half) = 0.00833 |
| **Array elements** | ✅ counted individually | 606361_0, 606365_0, 606378_1, 606385_2, 606412_3 — each its own `sacct` row |
| **Retries** | ✅ yes | e.g. the three DLinear-L48 re-runs inside job 587190 are inside that job's elapsed time |
| **Cancelled jobs** | ➖ no charge | 606363_0 was cancelled while still PENDING and never started; Slurm allocated no GPU, so it contributes 0. The same holds for stage6's 587243 |
| **stage5 jobs inside the window** | ❌ **NO** | 585865/585874/585875/585876/585878/585883 = **0.16583 GPU-h** belong to the earlier stage5 round with its own 2.0 GPU-h cap, and are excluded from the 2.3 total |

> **This is a real reporting boundary worth stating**: the 2.3 GPU-h cap covers
> *stage6 + continuation only*. The 0.16583 GPU-h of stage5 work inside the same
> calendar window is charged against the **earlier** stage5 cap, not this one.

---

## 4. Remaining allowance

```
cap                   2.30000 GPU-h
used (verified)       2.24361 GPU-h
remaining             0.05639 GPU-h   (= 3 min 23 s of one A100)
```

**That is why no further GPU work was submitted**, and why this continuation
submits none either.

---

## 5. Costs of the full 40-fit A1 set

The four completed A1 fits (L=24/36/48/60 on the author's released entry point)
give four direct measurements of the per-fit cost:

```
942 s, 978 s, 1014 s, 1054 s
```

| Estimator | per fit | 40 fits | remaining 36 fits |
|---|---:|---:|---:|
| **mean** (0.2769 h) | 0.2769 | **11.08** | **9.97** |
| median (0.2767 h) | 0.2767 | 11.07 | 9.96 |
| max (0.2928 h) | 0.2928 | 11.71 | 10.54 |

**This supersedes the earlier "≈11.27 GPU-h" figure.** That earlier estimate used
0.2817 h/fit, which averaged in the 7-second failed attempt; it was therefore
slightly **high** by about 0.19 GPU-h.

**Method statement**: the estimate uses the **mean** of four horizon-specific
measured times, all four horizons being represented. It is *not* extrapolated
from a single run, and *not* derived from the much cheaper A2 LoRA configuration.

> ⚠️ **Why 40 fits is the honest number**: the paper asks for the mean of
> **10 repetitions**. 4 horizons × 10 = 40 fits. The earlier "11.27" figure
> refers to **all 40**, not the remaining 36. Section 6 separates them.

## 6. Budget options (no quota requested here — options only)

Additional allowance needed = cost − remaining 0.05639.

| Target | Estimator | +0% | +5% retry | +10% retry | +20% retry |
|---|---|---:|---:|---:|---:|
| **remaining 36 fits** | mean | 9.91 | **10.41** | 10.91 | 11.91 |
| remaining 36 fits | max | 10.48 | 11.01 | 11.54 | 12.59 |
| **all 40 fits** | mean | 11.02 | **11.53** | 12.03 | 13.02 |
| all 40 fits | max | 11.66 | 12.18 | 12.70 | 13.76 |

*(all figures are **additional** GPU-hours required on top of the 0.05639 left)*

**Recommended allowance if the full A1-P set is ever approved: 11.6 GPU-hours**
(40 fits at the mean, +5% retry buffer). See `NEXT_GPU_BUDGET_OPTIONS.md` for why
this may still not be the best use of quota.

---

## 7. Cross-check against the on-cluster ledger

The A1 sbatch appends each fit to `a1/GPU_LEDGER_A1.tsv`. Its four rows
(`606365_0 … 606412_3`) match the `sacct` elapsed times exactly, and the fifth
row (`606361_0`, 7 s) is the failed attempt. No row is missing and none is
fabricated.

## 8. Conclusion

- The previously reported **2.24366 / 2.3 GPU-h is verified** (recomputed 2.24361).
- **0.05639 GPU-h remains.**
- The full 40-fit A1 set costs **11.08 GPU-h** at the mean per-fit time; the
  remaining 36 fits cost **9.97 GPU-h**.
- No GPU job was submitted during this continuation.