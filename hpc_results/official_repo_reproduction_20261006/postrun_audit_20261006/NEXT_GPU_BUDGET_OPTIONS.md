# NEXT GPU BUDGET OPTIONS

Generated 2026-10-06. **Options only — no quota is being requested, and no GPU job was
submitted.**

All costs use the **measured** per-fit times from the four completed A1 runs
(`942, 978, 1014, 1054 s`), so:
**mean 0.2769 GPU-h/fit · median 0.2767 · max 0.2928**. Remaining allowance:
**0.05639 GPU-h**.

---

## 1. The four options

| Option | Content | Fits | Seeds | Horizons | GPU-h (mean) | +10 % retry | Wall clock @ MaxJobsPU=1 | Storage |
|---|---|---:|---:|---:|---:|---:|---|---:|
| **P1** | minimum A1-P pilot | 4 | 1 | 4 | **1.11** | 1.22 | 4 × ~17 min ≈ **1.2 h** | ~4 × 331 MB ≈ 1.3 GB |
| **P2** | expanded A1-P pilot | 8 | 2 | 4 | **2.22** | 2.44 | ≈ **2.4 h** | ≈ 2.6 GB |
| **P3** | full A1-P repetitions | **40** | 10 | 4 | **11.08** | 12.18 | ≈ **11.6 h** | ≈ 13 GB |
| **F1** | core A2-F benchmark | 6 models × 4 horizons × 1 seed = **24** | 1 | 4 | **0.35** | 0.39 | ≈ **25 min** | ≈ 0.2 GB |

> **F1 is dramatically cheaper** because the corrected A2 implementation trains only
> LoRA + head (1.03 M trainable) while the author's released configuration trains the
> whole 82.7 M-parameter stack. Measured: **0.0146 GPU-h/fit** for A2-LoRA vs
> **0.2769** for the released configuration — a **19×** difference.

Additional allowance needed in each case = cost − 0.05639.

| Option | at +0 % | at +10 % |
|---|---:|---:|
| P1 | 1.06 | 1.16 |
| P2 | 2.17 | 2.38 |
| P3 | 11.02 | 12.12 |
| **F1** | **0.30** | **0.34** |

---

## 2. What each option can and cannot support

| Option | Supports | **Does not** support |
|---|---|---|
| **P1** | a feasibility run of a reconstructed paper contract; per-horizon numbers at 1 seed; a discrepancy report | any reproduction claim; any uncertainty estimate (1 seed) |
| **P2** | the above, plus a first seed-dispersion estimate | the paper's 10-repetition aggregate |
| **P3** | the paper's repetition *count* — **but only if the contract is first recovered** | anything about Table V unless the contract audit's obstacles are resolved first |
| **F1** | **the fair LLM vs non-LLM comparison**, which is the project's stated objective | a paper reproduction |

---

## 3. The recommendation, and why

### Recommended: **F1 first**, then a decision on P1.

The brief asks for a comparison of three spending choices. Applying its own priority logic:

| Choice | Scientific value |
|---|---|
| **A. More repetitions of the released-code protocol (P3, ~11 GPU-h)** | **Low.** 40 fits would characterise a protocol that the contract audit shows is *not the paper's*: univariate windows, one evaluated channel, Test-selected checkpoints, undisclosed hyperparameters. It would produce a precise estimate of the wrong quantity. |
| **B. A corrected A1-P pilot (P1/P2, ~1.1–2.2 GPU-h)** | **Medium-high**, *but currently blocked*: the reconstruction contract has unresolved items (Q12 pooling axes `UNRECOVERED`; whether Table V's MIFlu column is quoted is `UNRECOVERED`). Running now would bake in assumptions. |
| **C. The core A2-F benchmark (F1, ~0.35 GPU-h)** | **Highest value per GPU-hour.** It answers the project's stated final objective — *which model is best under one fair contract* — and it can be run **today's contract-complete**: the implementation identities are documented, the text path is verified active, the scorer is independent, and the contract in `A2F_FAIR_COMPARISON_CONTRACT.md` is fully specified. |

**Recommendation: C (F1) as the immediate next GPU spend, at ~0.35 GPU-h** (6 models ×
4 horizons × 1 seed, A2-LoRA configuration). It is cheap enough to be requested without
disrupting anything, it directly serves the stated objective, and its result is
interpretable regardless of how the paper-contract questions resolve.

**Then**, with the paper-contract audit complete, decide between P1 and P2 — not P3.
P3 should be considered **only** after (i) a recovered contract exists, (ii) a validation
selection rule replaces Test selection, and (iii) predictions are persisted so the result
can be independently scored. Without those, extra repetitions add precision to a
measurement of the wrong thing.

### Explicitly not recommended

**Spending ~11 GPU-h on 10 repetitions of the defective released-code protocol and calling
it paper reproduction.** The brief forbids exactly this, and the contract audit supplies
the evidence for why: 8 of 9 contract items fail to match (see
`TABLE_V_REPRODUCIBILITY_VERDICT.md` §1).

---

## 4. Ordering if all were approved

```
1. F1  core A2-F benchmark        ~0.35 GPU-h    immediate, contract-complete
2. P1  A1-P minimum pilot         ~1.11 GPU-h    after the contract audit closes
3. P2  A1-P expanded pilot        ~2.22 GPU-h    only if P1 is valid and dispersion matters
4. P3  A1-P 10 repetitions       ~11.08 GPU-h    only if a defensible contract exists
```

`MaxJobsPU=1` means **strictly sequential** execution; the wall-clock column above already
assumes that.

---

## 5. Risks common to all options

| Risk | Mitigation |
|---|---|
| scratch is over quota (413/300 GB) | write all outputs to `/gpfs1/home/…` (current practice) |
| `MaxSubmit=1` rejects arrays | submit one element at a time and await |
| per-fit time may drift | budgets use the **max** as a sensitivity column (`NEXT_GPU_RUN_MATRIX.csv`) |
| contract ambiguity (A1-P) | resolved by the audit before P1, not during it |
| Test leakage in the released harness | A2-F uses validation-only selection by contract (S11) |

## 6. No request is made here

This document defines options. **No quota request is made, and no GPU job was
submitted.**