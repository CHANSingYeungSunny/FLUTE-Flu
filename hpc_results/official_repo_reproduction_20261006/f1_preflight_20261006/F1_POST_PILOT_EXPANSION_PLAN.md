# F1 POST-PILOT EXPANSION PLAN

Generated 2026-10-06. **Prepared, not submitted.** All costs use the measured
**0.0533 GPU-h per MIFlu fit** (192 s) established in `F1_RESOURCE_ESTIMATE_BY_MODEL.csv`.

---

## 1. The expansion ladder

| Stage | Models | Seeds | Horizons | GPU fits | Base GPU-h | +20 % buffer |
|---|---|---:|---:|---:|---:|---:|
| **F1** (this pilot) | 6 | 1 | 4 | **8** | **0.427** | 0.512 |
| **F2** | 6 | **3** | 4 | 24 | **1.280** | 1.536 |
| **F3** | 6 | **10** | 4 | 80 | **4.267** | 5.120 |
| **F2+** (optional models) | 10 | 3 | 4 | 80 | **5.973** | 7.167 |

*GPU fits count only the MIFlu and no-text MIFlu arms; NLinear, DLinear, Last Value and
Seasonal Naive remain CPU-only at every stage — that is why the fit counts are 8/24/80
rather than 24/72/240.*

### F2 — three seeds

- same six models, same four horizons, same contract;
- seeds **42, 43, 44** (the project's declared list), applied identically to every model
  so that pairing is real;
- **incremental** cost over F1: 16 additional GPU fits = **0.853 GPU-h** (1.024 with a
  20 % buffer);
- delivers per-seed dispersion, a first stability estimate, and the ability to say whether
  the one-seed ordering survives.

### F3 — ten seeds

Only if scientifically and computationally justified, and **only after F2**:

- 80 GPU fits = **4.267 GPU-h** (5.120 with a 20 % buffer);
- justification is required because the paper's own "10 repetitions" came from a harness
  whose repetitions are **not addressable by seed** and whose protocol is not the paper's
  (`../postrun_audit_20261006/A0R_METRIC_SEMANTICS.md`). Ten seeds here would be a
  **project-defined robustness study**, not a paper reproduction — a legitimate goal, but
  a different one, and it must be named as such.

### Optional model expansion (after F2)

| Model | Status | Condition to include |
|---|---|---|
| canonical **PatchTST** | ❌ not implemented — the current one is **INSPIRED** (its own `architecture_report()` lists three deviations) | needs a new implementation before it may be called canonical |
| accurately identified **iTransformer** | own re-implementation | needs a fidelity review before identity claims |
| **Qwen Time-LLM**, **CALF**, **TimeCMA** | adaptations, not official implementations | only with documented provenance and the adaptation label retained throughout |

Adding these four to F2 costs **+56 GPU fits ≈ 4.69 GPU-h** — more than the entire F1+F2
core programme. That must be weighed against the fact that they answer a secondary
question.

**Excluded**: DeepSeek (per the brief).

---

## 2. Minimum seed count for each claim

This is the question the brief asks most directly.

| Claim | Minimum seeds | Why |
|---|---|---|
| "F1 executed and the contract held" | **1** | the claim is about execution, not about a model |
| "model X ranked first in the pilot" | **1**, with the word *pilot* | a ranking of one draw is a ranking of one draw |
| "model X appears to outperform Y under this contract" | **1**, hedged | still descriptive |
| **"best-performing model"** | **≥ 3 (F2)** | three seeds let one show the ordering is not a single-seed artefact and report dispersion |
| **"consistently outperforms"** | **≥ 3, and only if the sign is stable across all seeds *and* all horizons** | "consistently" is a frequency claim and needs more than one draw |
| **"robust improvement"** | **≥ 10 (F3)**, or ≥ 3 with an explicit interval and a predeclared margin | robustness is a variance claim |
| **"LLM advantage" / "non-LLM advantage"** | **≥ 3 across the full model set, plus the pairing design** — and even then only about the *selected implementations* | the models per family are a **fixed selection, not a random sample** |
| statistical **significance** | ≥ 3 with a predeclared test and multiplicity control | one seed provides no within-model variance to test against |

**Standing rule**: even at F3, no statement may generalise from the selected
implementations to "LLMs" or "non-LLMs" as categories. The models are deliberately chosen
and heterogeneous; group means describe *those models*, not a population.

---

## 3. Recommended sequence

```
1. F1  one seed     0.60 GPU-h   contract validation + preliminary ordering   <- requested now
2. F2  three seeds  1.03 GPU-h   dispersion + stability                      <- only if F1 COMPLETE
3. review whether the one-seed ordering survived F2
4. F3 / optional models - decide on the resulting evidence, not in advance
```

**Do not start F2 until F1 reports `COMPLETE`.** If F1 is `FAILED_INTEGRITY`, the contract
is wrong and more seeds would multiply a broken measurement.