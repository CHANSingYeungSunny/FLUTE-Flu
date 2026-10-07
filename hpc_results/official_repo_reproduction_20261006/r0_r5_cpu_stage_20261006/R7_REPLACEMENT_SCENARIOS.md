# R7 — REPLACEMENT SCENARIOS

Two scenarios. **Only one will be executed**, and which one is decided by the compatibility
verdict already issued: **`MIFLU_RETRAIN_ON_OLD_CONTRACT_REQUIRED`**.

## Scenario S1 — direct MIFlu replacement

Usable **only if exact compatibility is proven**.

| Requirement | Status |
|---|---|
| the reproduced MIFlu's forecast keys identical to the historical ones | ❌ **FAILS** — 966-row origins vs 1025-row origins |
| the same scorer usable on both | possible, but the keys differ |
| the seven historical results reusable unchanged | ✅ yes |
| **verdict** | **`DIRECT_REPLACEMENT_VALID` is NOT available for Stages C/D** |

**S1 is therefore not the scenario that will run**, except in one narrow sense: the seven
historical results **are** re-aggregated with a new MIFlu row, which is a partial S1.

## Scenario S2 — controlled rerun (the scenario that WILL run)

| Element | Decision |
|---|---|
| model identities | **unchanged** — the same 4 LLM + 4 non-LLM strings |
| the seven non-MIFlu models | **historical implementations and predictions retained** |
| the MIFlu slot | **official-repository-based MIFlu retrained on the historical 1025-row contract** |
| evaluation contract | the **historical** one: 1025 rows, 717/102/206, seeds 42–51, strict containment |
| what changes | **only the MIFlu weights** |
| what must be recorded | every unavoidable change, with its reason |

### The exact label the replacement run must carry

> **official-repository-based MIFlu transferred to the historical comparison contract**

If R1-B cannot be validated and the fallback is used, add `(reconstruction)`. It is
**never** called "the paper reproduction" — it is trained on data the paper did not use.

## What must not happen in either scenario

| Prohibited |
|---|
| inserting an author-966 metric into the 1025-row ranking |
| retraining the other seven "for consistency" — that destroys the control |
| silently redesigning the model set or the metric |
| presenting the replacement as a paper reproduction |
| treating the exposed historical Test as fresh |
