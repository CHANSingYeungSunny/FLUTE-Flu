# R1 — MINIMAL REPRODUCTION PILOT PLAN

Generated 2026-10-06. **Prepared, not submitted.** Requires a new reproduction-specific GPU
authorization.

---

## 1. Principle

Do **not** spend GPU resources on 40 fits first. Run **four fits** — one recovered
configuration, four horizons, one repetition — to establish that the R1-B reconstruction
produces the **correct kind of output** and is **numerically near** the paper, *before*
expanding to the paper's repetition count.

**Stop rule**: if the pilot is not valid, it is not expanded. Reporting an invalid pilot is
a legitimate outcome.

---

## 2. Pilot specification

| Item | Value |
|---|---|
| track | **R1-B** (paper-intended reconstruction) |
| configurations | **1** — the declared reconstruction |
| horizons | 24, 36, 48, 60 |
| repetitions | **1** |
| **GPU fits** | **4** |
| device | stingy, 1× A100, one job at a time |
| data | author 966-row file, SHA-256 `2a96dfed…ebfe5` |
| split | 676 / 97 / 193 chronological |
| scaler | fitted on train rows only |
| target contract | **seven channels** (B-1) |
| text pathway | **functional** — text prefixed, patches read after it (B-2, declared change) |
| LoRA | `PEFT=1`, `c_attn`, r=4, `--target_modules` **not passed** (B-3) |
| freeze | effective, with the trainable count reported (B-4) |
| checkpoint selection | **validation-only** (B-5, declared repair) |
| predictions | persisted per (origin, lead, variable) (B-6) |
| scoring | independent — `scorer_f1.py` arithmetic, no training-code metric path |
| configuration | declared, from `R1_HYPERPARAMETER_EVIDENCE.csv` (B-7) |
| **not included** | R1-A (already done) · R1-C sensitivity · the ten repetitions · the 4-vs-4 rerun |

---

## 3. Why this is a *pilot* and not a reproduction

| The pilot can establish | The pilot cannot establish |
|---|---|
| the reconstruction runs and emits 7-channel predictions | a paper-level reproduction result |
| the text pathway is functional (re-probe each checkpoint) | seed stability (one repetition) |
| the checkpoint rule is validation-only and Test is untouched | the paper's ten-repetition aggregate |
| the per-horizon numbers and their distance from the paper | any verdict better than `PARTIAL_REPRODUCTION` |
| whether the reconstruction is *directionally* right | — |

**A single repetition cannot satisfy item 6 of the brief** ("a paper-level success claim
must address ten repetitions"). The pilot exists to decide **whether** spending the
ten-repetition budget is justified.

---

## 4. Sequence

```
1. CPU preflight   — contract assertions, dataset hash, scorer acceptance tests   (0 GPU-h)
2. GPU: 4 fits     — R1-B reconstruction, L=24/36/48/60, repetition 1
3. CPU: evaluation — reload, evaluate Test ONCE, persist predictions/targets,
                     independent scoring, text-path probe on each checkpoint     (0 GPU-h)
4. Gate check      — R1_REPRODUCTION_SUCCESS_GATES.md
5. Decision        — expand to the paper's repetition count, or report why not
```

Only step 2 needs GPU.

---

## 5. What must be true before the pilot may be submitted

| # | Precondition | Status |
|---|---|---|
| 1 | the reproduction contract is written and per-setting classified | ✅ done |
| 2 | the four structural conflicts are documented | ✅ done |
| 3 | the unrecovered items are named | ✅ done |
| 4 | a **runnable R1-B trainer exists** that implements B-1…B-7 | ❌ **NOT DONE — the largest remaining dependency** |
| 5 | success gates and a tolerance are predeclared | ✅ done (`R1_REPRODUCTION_SUCCESS_GATES.md`) |
| 6 | a reproduction-specific GPU authorization exists | ❌ **NOT GRANTED** |

### Precondition 4 is the real work

The released `main_ILI_lora.py` cannot be used as-is: B-1, B-2, B-3, B-4, B-5 and B-6 all
require code changes. Two options:

| Option | Description | Cost |
|---|---|---|
| **4a** | patch a copy of the author's entry point with the six required changes, each recorded in a deviation ledger | moderate; keeps the author's code as the basis |
| **4b** | use the project's existing corrected implementation (`scripts/train_miflu.py` / `miflu_model.py`), which already satisfies B-1, B-2, B-4, B-5 and B-6 | low; but then the run is on the *project's* code, which weakens the "official repository" basis |

**Recommendation: 4a.** The whole point of R1 is to reproduce on the **author's** code.
Option 4b would repeat the mistake this correction is fixing — substituting the project's
own implementation for the author's.

Under 4a the deviations are exactly six, each individually documented, which is a far
cleaner story than "we used our own implementation".

---

## 6. What the pilot will produce

| Output | Purpose |
|---|---|
| 4 checkpoints (best validation) | reproducible artefacts |
| 4 prediction NPZs with 7-channel targets | independent re-scoring |
| per-horizon MSE/MAE | comparison against Table V |
| the distance from the paper, per horizon | the pilot's central number |
| 4 text-path probe verdicts | confirm the restored pathway is active |
| a contract-compliance report | every B-item verified or not |

---

## 7. Explicitly not in this plan

- ten repetitions (decided **after** the pilot)
- R1-C sensitivity (only if the pilot's configuration is defensible)
- R3–R6 (the old-comparison inspection, the MIFlu swap, the 4-vs-4 rerun)
- any F2 work (cancelled)
- any use of the F1 authorization's unspent 0.35 GPU-h