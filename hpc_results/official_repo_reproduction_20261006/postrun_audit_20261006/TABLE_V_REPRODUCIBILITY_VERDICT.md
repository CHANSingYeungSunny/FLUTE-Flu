# TABLE V REPRODUCIBILITY VERDICT

Generated 2026-10-06. Append-only.

## Verdict

**NOT REPRODUCED — and not currently reproducible from the released artefacts.**

Table V reports MIFlu MSE/MAE of 1.542/0.726, 1.422/0.779, 1.414/0.757 and
1.364/0.719 at L = 24/36/48/60 (equal-weight mean 1.4355/0.74525, rounded in Table VIII
to 1.436/0.745).

**No MIFlu result produced in this project is commensurable with those four pairs.**

---

## 1. Why nothing produced so far can be compared

| Requirement | Paper | What exists | Commensurable? |
|---|---|---|---|
| evaluated variables | national task defined over **seven** variables | released code evaluates **one channel** (`% WEIGHTED ILI`) | ✗ |
| window shape | multivariate | released code builds **univariate (T,1)** windows in every split | ✗ |
| checkpoint rule | unstated | released code selects on **Test** MSE | ✗ |
| repetitions | **10**, averaged | **1** per horizon in the four runs; 3 in the project's own protocol | ✗ |
| seeds | unstated | seed fixed once (2021); project uses 42–51 | ✗ |
| epochs / lr | **not disclosed** | 1 / 1e-4 (code default) or 20 / 5e-4 (project choice) | ✗ |
| metric space | standardized (national) | standardized | ✓ **the one matchable item** |
| four-horizon mean | equal-weight arithmetic | matches | ✓ |
| predictions persisted | — | **not saved by the released code** | ✗ (no re-scoring possible) |

Eight of nine contract items do not match, and the two that do (metric space; the
equal-weight horizon average) are the least discriminating.

---

## 2. What the four A0-R runs actually measured

| L | author `mse_mean` (final-epoch Test MSE, itr=1) | best-epoch MSE |
|---:|---:|---:|
| 24 | 0.5793 | 0.5344 |
| 36 | 0.5920 | 0.5387 |
| 48 | 0.6088 | 0.6069 |
| 60 | 0.6361 | 0.5933 |

These are **lower** than the paper's 1.5 / 1.42 / 1.41 / 1.36 — which is **not** evidence
of a better reproduction. They are a different quantity: one channel, Test-selected,
single repetition, in a regime the paper does not describe and the released code does
not intend.

**A smaller number here means "different measurement", not "better model".**
Any statement of the form "our 0.53 beats the paper's 1.54" is a category error and must
not appear in the thesis.

---

## 3. The decisive obstacle

From the contract audit (`PAPER_EVALUATION_CONTRACT_AUDIT.md`, Q3) and re-verified in the
loader this session:

```python
data_loader.py:305   seq_x = self.data_x[s_begin:s_end, feat_id:feat_id+1]   # one channel
data_loader.py:312   if self.set_type == 2: length = ...                     # no * enc_in
                     else:                  length = ... * self.enc_in
```

The released code **cannot produce a seven-variable score**, because it never builds a
seven-variable window. The paper's national task is multivariate. This is a gap in the
artefacts, not a tuning problem, and no amount of extra training on the released code
closes it.

---

## 4. What would be required to attempt Table V

1. A **multivariate** formulation — necessarily a declared reconstruction (the A2
   implementation already is one), replacing the single-channel slice with all channels.
2. A **validation-selected** checkpoint rule, or direct evidence that the paper used Test
   selection.
3. **10 repetitions**, aggregated as the paper states.
4. A recovered **epochs / lr / optimizer / scheduler** configuration, or a declared
   reconstruction that is never tuned toward 1.4355.
5. **Persisted predictions and targets**, so the numbers can be independently scored.
6. The metric computed in the paper's space, over the paper's pooling axes — if those can
   be recovered. They currently cannot (Q12 `UNRECOVERED`).

Items 1–5 are engineering work of the kind A1-P is specified to do. Item 6 may remain
partly unrecoverable.

---

## 5. Status labels

| Item | Label |
|---|---|
| Table V (MIFlu column) | `NOT_STARTED` |
| Table V (baseline columns) | `NOT_APPLICABLE` — the paper states they are taken from [9]/[14], not re-run |
| Tables VI, VII, IX | `NOT_STARTED` |
| Table VIII | `NOT_STARTED` (the project's `notext` is a different protocol) |
| Figures 3–7 | `NOT_STARTED` |
| **Overall paper reproduction** | **`PARTIAL` for released-code behaviour documentation; NOT achieved for any paper number** |

---

## 6. The one honest positive statement

Four horizons of the author's released code have now been executed on the author's own
data, on an A100, and its measured behaviour is documented, artefact-backed, and
reproducible across devices. That is a **released-code behaviour audit (A0-R)** and is a
genuine contribution to a reproducibility study.

It is **not** a reproduction of Table V, and the two must be reported separately.