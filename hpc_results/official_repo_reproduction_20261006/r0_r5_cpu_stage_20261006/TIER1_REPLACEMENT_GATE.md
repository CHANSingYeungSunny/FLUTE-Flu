# TIER-1 REPLACEMENT GATE

Generated 2026-10-06. Defines the gate that must close before the controlled historical
MIFlu replacement may start.

# GATE STATUS: **NOT CLOSED**

Reason: Tier-1 items T1-06 (LoRA on the R1-B subclass), T1-09/T1-10 (the four horizons),
T1-15 (a reproduction verdict) are `NOT_YET_RUN` or `PARTIAL`. **No Tier-1 item has FAILED.**

---

## 1. The gate rule

> The controlled historical MIFlu replacement cannot start until Tier 1 has a
> **documented verdict**.
>
> **The verdict does not have to be success.** It may be: reproduced · partially
> reproduced · executable but not reproduced · not reproducible from released artifacts.

So the gate is about having a **verdict**, not about having a good number. What it forbids
is beginning the replacement while the MIFlu being inserted is undefined.

---

## 2. Tier-1 status (15 items)

| Status | Count | Items |
|---|---:|---|
| ✅ COMPLETE | 6 | T1-01 data identity · T1-03 architecture · **T1-04 functional text pathway** · T1-05 fusion · **T1-07 effective freeze** · T1-12 prediction saving · T1-13 independent scoring |
| ⚠️ PARTIAL | 4 | T1-02 task · T1-06 LoRA · T1-11 selection rule · T1-14 mechanism validation |
| ⚠️ CONFLICTING | 1 | T1-08 target contract |
| ⏳ NOT_YET_RUN | 3 | T1-09 main MSE/MAE · T1-10 four horizons · T1-15 reproduction verdict |
| ❌ FAILED | **0** | — |

### The two Tier-1 items that improved this round

| Item | Before | Now |
|---|---|---|
| **T1-01 data identity** | inferred | **measured**: Table II verifies the 966-row file **7/7** (max dev 0.02 %) while the 1025-row snapshot matches only **1/7** (up to 7.04 % off) → `COMPLETE` |
| **T1-04 — T1-07 mechanism** | asserted | **measured**: text `inert → active`; trainable `100 % → 1.93 %` → `COMPLETE` |

### The one Tier-1 item that is permanently conflicted

**T1-08 target contract.** The paper declares a seven-variable task but never states which
variable(s) the Table V scalar covers; the released code evaluates channel 0 only. This is
`CONFLICTING_EVIDENCE` and **cannot be closed by any amount of work** on the released
artifacts. It is a permanent disclosed limitation, not a blocker to running.

---

## 3. What must happen to close the gate

| # | Action | Needs GPU? |
|---|---|---|
| 1 | run a **CPU-only HPC job** importing the R1-B subclass with `PEFT=1`; report the LoRA tensor count, the trainable count and a checkpoint reload round-trip → closes T1-06 | **no** |
| 2 | obtain a **new reproduction-specific GPU authorization** (neither sealed remainder may be used) | — |
| 3 | run the **R1-B pilot** (4 horizons × 1 repetition) → closes T1-09, T1-10, T1-14 | yes |
| 4 | apply the predeclared tolerance and issue a **reproduction verdict** → closes T1-15 | — |
| 5 | `STORAGE_READY` from the S-track | — |

**Step 1 needs no authorization and no GPU.** It is the cheapest unblocking action
available and should be taken first.

---

## 4. What the gate must NOT be used for

| Prohibited |
|---|
| closing the gate with a *number* rather than a *verdict* |
| treating a one-repetition pilot as a paper-level reproduction (it cannot exceed `PARTIAL_REPRODUCTION`) |
| declaring success from one horizon |
| widening the tolerance to make a horizon pass |
| substituting F1 for this gate — F1 is a different contract on a different question |

---

## 5. Consequence if the gate never closes

If Tier-1 ends as `NOT_REPRODUCIBLE_FROM_RELEASED_ARTIFACTS`, the replacement experiment
still proceeds — **but on the fallback the brief already authorises**:

> the **best-evidence official-repository-based reconstruction**, clearly labelled as such

That run is then labelled

> **official-repository-based MIFlu transferred to the historical comparison contract
> (reconstruction)**

and is **never** called the paper reproduction. The primary scientific question — *does
replacing MIFlu change the ranking?* — remains answerable either way, because the
comparison only requires **a defined, documented MIFlu**, not a reproduced one.

---

## 6. Summary

| Question | Answer |
|---|---|
| is the Tier-1 gate closed? | **NO** |
| has any Tier-1 item failed? | **no** — 0 failures |
| what blocks it? | LoRA-on-subclass (needs a CPU-only HPC job), the pilot (needs GPU authorization), and the verdict |
| what can be done now, with no GPU? | **step 1** |
| does a failed gate block the primary objective? | **no** — a labelled reconstruction is the authorised fallback |