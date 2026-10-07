# R1 — REPRODUCTION GPU BUDGET

Generated 2026-10-06. **A request, not a submission.** No GPU work has been submitted.

---

## 1. The ask

| Item | Value |
|---|---|
| **requested (pilot only)** | **0.30 GPU-h** |
| requested (pilot + 10-repetition expansion) | **2.50 GPU-h** |
| requested (pilot + expansion + R1-C sensitivity) | **6.00 GPU-h** |
| **recommended** | **2.50 GPU-h**, released in two tranches |

**Do not grant the full amount up front.** The pilot answers whether the expansion is
justified; granting both at once recreates the spend-first-decide-later pattern this
correction is fixing.

---

## 2. Cost derivation

Basis: the **measured** per-fit cost from the F1 execution and the A0-R runs.

| Measurement | Value | Source |
|---|---|---|
| MIFlu fit, 20 epochs, author config | **162 s** | `recovery/stage3/resource_estimate.md`, recorded as measured |
| MIFlu fit, F1 (corrected, 20 epochs) | 0.0533 h/fit measured from 8 jobs | F1 execution report §2 |
| A0-R MIFlu fit (author config) | 1054 / 1014 / 978 / 942 s | jobs 606365 / 606378 / 606385 / 606412 |
| per-job startup | ~30 s | observed |

**Note the spread**: the F1 corrected implementation costs **0.0533 h/fit** because it
trains only LoRA + head; the A0-R author configuration costs **0.28 h/fit** because the
release's freeze is a no-op so all 82.7 M parameters train. **R1-B freezes the backbone
(B-4), so the cheaper figure applies** — but B-4 is a *reconstruction*, and if the freeze
proves ineffective the cost moves toward the expensive figure. The budget below uses the
cheap figure and carries a caution.

| Tranche | Content | Fits | GPU-h | Wall @ MaxJobsPU=1 |
|---|---|---:|---:|---|
| **T1 — pilot** | R1-B, 1 configuration × 4 horizons × 1 repetition | 4 | **0.21332** | ~15 min |
| **T2 — expansion** | same configuration × 4 horizons × 10 repetitions, i.e. **+36 fits** | 36 | **1.92** | ~2.2 h |
| T3 — sensitivity (optional) | R1-C, 4 predeclared combos × 4 horizons × 1 rep | 16 | **0.85** | ~1.0 h |

| Tranche | Base | +20 % retry buffer | **request** |
|---|---:|---:|---:|
| T1 | 0.21332 | 0.25598 | **0.30** |
| T1 + T2 | 2.13332 | 2.55998 | **2.50** |
| T1 + T2 + T3 | 2.98665 | 3.58398 | **4.00** (a 6.00 upper bound if the freeze is ineffective) |

---

## 3. Why not 11 GPU-h

An earlier plan proposed **≈11.08 GPU-h** for 40 fits. That figure came from the **author's
released configuration** (0.2769 h/fit, measured), in which the ineffective freeze trains
the entire GPT-2 stack.

R1-B implements an **effective freeze** (B-4), so the LoRA-only cost applies and 40 fits
cost **≈2.13 GPU-h**, not 11.08.

**Caveat, stated plainly**: if the freeze does not take effect in the reconstruction, the
cost reverts toward 0.28 h/fit and 40 fits would need ≈11.2 GPU-h. The pilot measures this
directly — it reports the trainable-parameter count — so **the T2 request can be re-costed
before T2 is submitted**. That is precisely why the tranches are separated.

---

## 4. Budget separation

| Round | Cap | Used | Remaining | May fund R1? |
|---|---:|---:|---:|---|
| A2 (round 1) | 2.00 | 1.1536 | — | ❌ closed |
| Stage-6 (round 2) | 2.30 | 2.24361 | 0.05639 | ❌ closed |
| **F1** | 0.60 | 0.25000 | 0.35000 | ❌ **exclusive to the F1 contract; parked** |
| **R1 (this request)** | **2.50** | 0 | 2.50 | ✅ if granted |

**The F1 remainder of 0.35 GPU-h may not be spent on R1.** The authorizations are separate
and the brief requires them kept separate for auditability.

---

## 5. What must be true before any R1 GPU work is submitted

| # | Precondition | Status |
|---|---|---|
| 1 | the R1-B trainer exists and implements B-1…B-7 | ❌ **not done** |
| 2 | the reproduction contract is written and classified | ✅ done |
| 3 | success gates and a **predeclared tolerance** exist | ✅ done |
| 4 | the pilot's run matrix is frozen | ✅ done |
| 5 | **a reproduction-specific GPU authorization exists** | ❌ **not granted** |

**Precondition 1 is the blocker that matters.** No GPU time should be requested for
execution until the R1-B trainer exists, because otherwise the run would either use the
released code (which is R1-A, already done) or the project's own implementation (which
would betray the purpose of R1).

---

## 6. Recommendation

1. **Build the R1-B trainer** (option 4a in the pilot plan — patch a copy of the author's
   entry point with the six recorded changes). This is CPU-only work.
2. **Request 0.30 GPU-h (T1)** and run the pilot.
3. Review the pilot's gate report **and its measured trainable-parameter count**.
4. **Only then** request T2, re-costed from the pilot's actual per-fit time.

This keeps every GPU-hour decision behind an evidence gate.