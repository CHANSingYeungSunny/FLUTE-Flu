# R1B STATIC AND CPU TEST REPORT

## 1. Local CPU (synthetic tensors)

| Check | Observed | Verdict |
|---|---|---|
| B-1 output shape | `(2, 24, 7)` | ✅ |
| B-2 text influence | `max|d| = 5.8775e-02`, `grad = 1.0405e-03`, `text_active` | ✅ (released: exactly 0.0) |
| B-4 trainable fraction | `1,599,768 / 82,705,944 = 1.93 %` | ✅ (released: 100 %) |
| no-text control | shape `(2, 24, 7)`, no text influence | ✅ |
| dead-import shim | `transformers.models.llama.LlamaModel` absent locally; the shim **raises if instantiated** | ✅ never on the executed path |

## 2. HPC CPU-only (job 607887, real `peft` 0.17.1, 9 s, ZERO GPU-hours)

| Check | Observed | Verdict |
|---|---|---|
| T19 LoRA modules exist and target `c_attn` | **12 tensors, 73,728 params**, `h.{0..5}.attn.c_attn.lora_{A,B}` | ✅ |
| T20 LoRA trainable and intended base frozen | 31 non-LoRA trainable, **49 frozen**, fraction **2.02 %** | ✅ |
| T29 save → reload → prediction equivalence | **`max|Δ| = 0.000e+00`** | ✅ |
| the `PEFT` flag changes the architecture | PEFT=1 → +12 LoRA; PEFT=0 → 0 LoRA | ✅ |
| text pathway with PEFT=1 | `max|d| = 4.63e-02`, `grad = 1.16e-03`, `text_active` | ✅ |

## 3. Scorer acceptance (independent of the model)

**20/20 checks pass** — see `f1_preflight_20261006/logs/scorer_acceptance_tests.txt`.

## 4. Storage guard (synthetic, CPU-only)

**24/24 checks pass** — see `logs/storage_guard_tests.txt`.

## 5. Summary

| Suite | Result |
|---|---|
| R1-B acceptance tests | **30 PASS / 1 NOT_YET_RUN / 0 FAIL** |
| scorer acceptance | 20/20 |
| storage guard | 24/24 |
| author source tree integrity | `git diff --stat` = 0 insertions, 0 deletions |

**No gate has failed at any point.**
