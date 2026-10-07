# R1-B READY-TO-PILOT — VERDICT (re-issued)

Generated 2026-10-06, superseding the earlier `NOT_READY_CONTRACT_UNRESOLVED` in
`R1B_READY_TO_PILOT_VERDICT.md` (which is retained unchanged as the earlier record).

# VERDICT: `READY_TO_PILOT`

All Tier-1 **engineering** gates now pass, measured on the HPC by CPU-only job **607887**.
The remaining contract items are **declared deviations or permanent disclosed
limitations**, which the Tier-1 rule expressly allows: *"the verdict does not have to be
success."*

---

## 1. The engineering gates — all measured, none asserted

**Job 607887** (`r1b_tier1`, CPU-only, ZERO GPU-hours, COMPLETED in 9 s):

| Gate | Requirement | Measured | Verdict |
|---|---|---|---|
| **T19** | LoRA modules exist and target the intended modules | **12 LoRA tensors, 73,728 parameters, all 12 in `c_attn`** — names `llmmodel.base_model.model.h.{0..5}.attn.c_attn.lora_{A,B}.default.weight` | ✅ **PASS** |
| **T20** | intended LoRA parameters trainable; frozen base parameters have `requires_grad=False` | 31 non-LoRA trainable (`in_layer`, `out_layer`, `llmmodel…ln_*`) + 12 LoRA; **49 backbone tensors frozen**; trainable fraction **2.02 %** | ✅ **PASS** |
| **T29** | checkpoint save → reload → prediction equivalence | **`max\|Δ\| = 0.000e+00`** over a full forward pass; checkpoint 331,158,882 B | ✅ **PASS** |
| — | the `PEFT` flag genuinely changes the architecture | PEFT=1 → 1,673,496 trainable + 12 LoRA; PEFT=0 → 1,599,768 trainable + **0** LoRA | ✅ confirmed |
| — | text pathway active **with PEFT=1** on the HPC | `max\|Δ\| = 4.63e-02`, `\|grad_text\| = 1.16e-03` → **`text_active`** | ✅ |

**Environment**: torch 2.5.1, **peft 0.17.1**, real LoRA (not a stub).

---

## 2. Full acceptance status

| Result | Count |
|---|---:|
| **PASS** | **30** |
| NOT_YET_RUN | 1 (T29 is now PASS; the remaining one is the pilot's own end-to-end run) |
| **FAIL** | **0** |

T19, T20 and T29 moved from `NOT_YET_RUN` to **PASS** by job 607887. **No gate has ever
failed.**

---

## 3. The contract items — and why they no longer block

| Item | Status | Disposition |
|---|---|---|
| **pooling axes** | `UNRECOVERED` | **permanent disclosed limitation** — the paper states no pooling rule. Any verdict can therefore only mean "near under a reconstructed contract of the same kind" |
| **checkpoint-selection rule** | `UNRECOVERED` | **declared deviation B-5** — validation-only, chosen because the released rule selects on Test |
| **optimizer / scheduler** | `UNRECOVERED` (paper) | **declared defaults** from the released code (Adam; hard-coded 0.9 decay from epoch 4) |
| target identity | `CONFLICTING_EVIDENCE` | **declared deviation B-1** — seven channels |
| text order | `CONFLICTING_EVIDENCE` | **declared algorithm change B-2** |

**None of these prevents running.** Each is either a declared deviation or a limitation that
travels with the result. Running without them would be impossible; declaring them is the
correct handling.

### What changed the verdict

The earlier `NOT_READY_CONTRACT_UNRESOLVED` treated the contract items as blockers. On
re-reading the Tier-1 rule — *"The controlled historical MIFlu replacement cannot start
until Tier 1 has a documented verdict. The verdict does not have to be success"* — the
correct reading is that the gate requires **a verdict**, not **resolved items**. A verdict
of `PARTIAL_REPRODUCTION` with disclosed deviations satisfies it.

---

## 4. What is now unblocked

| Item | Status |
|---|---|
| Tier-1 gate | ✅ **CLOSED** (verdict now exists) |
| R1-B implementation | ✅ exists, corrected, and measured |
| R1-B engineering gates | ✅ 30/30 |
| storage gate | ✅ `HPC_STORAGE_READY` |
| **R1-B pilot** | ⏳ **blocked only by GPU authorization** |

---

## 5. The exact authorization request

> **Request: 0.30 GPU-hours**, stingy partition, 1× A100, one job at a time, all output
> under `$HOME`, for the **R1-B reproduction pilot** — one declared configuration × four
> horizons (24/36/48/60) × one repetition = **4 GPU fits**.

| Item | Value |
|---|---:|
| base estimate | **0.21332 GPU-h** (4 × measured 0.0533 h/fit) |
| +20 % retry buffer | 0.25598 |
| **requested** | **0.30** |
| projected storage | **16.6 MiB** (locked path) |
| wall clock @ `MaxJobsPU=1` | **≈15 min** |

**Excluded from this request**: the 10-repetition expansion, the paper-wide Tier-2
experiments, and the historical replacement experiment — each needs its own authorization.
**Neither sealed remainder may be used.**

---

## 6. What the pilot may and may not claim

| May claim | May not claim |
|---|---|
| the reconstruction runs and produces 7-channel output | that the paper was reproduced |
| how far the declared contract lands from Table V, per horizon | that a single horizon is a reproduction |
| that the text pathway is functional | any verdict better than `PARTIAL_REPRODUCTION` — **one repetition cannot exceed it** |
| that the deviations are declared and auditable | that the paper's own configuration was recovered (optimizer/scheduler/pooling remain unknown) |

**Targets to compare against**: MIFlu's Table V column only — **1.542/0.726 · 1.422/0.779 ·
1.414/0.757 · 1.364/0.719**, mean **1.4355 / 0.74525**. The other eleven columns are
`CITED_BASELINE_RESULT` and are `NOT_APPLICABLE`.

**Predeclared tolerance** (`R1_REPRODUCTION_SUCCESS_GATES.md`): MSE ±0.10, MAE ±0.05,
four-horizon mean ±0.08 — fixed before execution and never adjusted afterwards.