# RELEASED-CODE TEXT-PATH: FINAL CONCLUSION

Generated 2026-10-06. Append-only. Supersedes nothing; it *verifies* the earlier
finding (`../TEXT_PATH_RESOLUTION.md`) requirement by requirement.

## Classification

# `RELEASED_TEXT_PATH_INACTIVE`

---

## 1. The claim, stated carefully

> The author's released implementation **did not show functional dependence on
> textual content under deterministic equal-length intervention testing.**

That is the whole claim. The following are **NOT** claimed and are explicitly
outside this conclusion:

- ✗ "text is never useful in forecasting"
- ✗ "the paper's conceptual method can never work"
- ✗ "all multimodal forecasting is ineffective"
- ✗ "the paper's authors did not train with text" — the released code and the
  paper may differ; this conclusion is about **this released code only**

---

## 2. Requirement-by-requirement verification

The brief lists twelve things the saved evidence must support. Each is checked
against the raw probe JSON, not against the earlier prose.

| # | Requirement | Verified? | Evidence |
|---|---|---|---|
| 1 | Same checkpoint | ✅ | For the released-code probes: no checkpoint is loaded at all — all runs use a **deterministic seeded random init** (`init_seed=42`). The three released-code runs therefore share *identical weights by construction*, confirmed by (2). The A2 probe **does** load a real checkpoint (`hpc_results/checkpoints/best_miflu_L24.pth`) |
| 2 | Same parameter hash | ✅ | `all_parameters_sha256` = `d7ad42ee6f7d3ad9bc152f960cdef210cf02f7c7df2d58f39d7a558deb6a3a20` **identical** for HPC CPU (606357) and HPC A100 (606358). The local Windows run gives `ebaaabd3441f…` — different because torch differs (2.6.0 vs 2.5.1); this is disclosed, not hidden |
| 3 | Same model weights | ✅ | follows from (1)+(2) on the cluster; the local run is a separate-environment replication, labelled as such |
| 4 | Same input | ✅ | `input.sha256` = `0c15781a87fb2d372e2db74614be1c91cf35cdcb657c5cd99b1f8b04a752fdc5` identical on HPC CPU and A100 (real data: last 104 rows of the training block) |
| 5 | Same equal-length text replacement | ✅ | `shape=(317,768)` for all variants; the probe **aborts** if the control differs in shape, so an unequal-length substitution cannot silently occur |
| 6 | Same masks | ✅ | no attention mask is passed by the released forward; both devices run the identical code path |
| 7 | `model.eval()` state | ✅ | `model_eval_mode: true` recorded in every JSON |
| 8 | Dropout disabled during evaluation | ✅ | `any_dropout_training: false`, with a full per-module inventory in `dropout_modules` |
| 9 | Same prediction indices | ✅ | output shape `(8, L, 1)` identical across variants and devices; the comparison is elementwise on the same tensor positions |
| 10 | Same output scale | ✅ | predictions compared in the model's native output space on identical inputs; no rescaling is applied between variants |
| 11 | Positive-control validity | ✅ | the control rewrites the released `forward` source by exactly two substitutions and **aborts if either fails to apply**; it produced `5.34e-05` (CPU) and `5.29e-05` (A100), both far above the `1e-06` tolerance → **the probe can detect text influence when text is reachable** |
| 12 | CPU/GPU comparison logic | ✅ | job **606360** runs `slurm/probe_text_path_compare.py`, which reads both JSONs and prints `CPU/GPU verdicts AGREE`; it exits non-zero on disagreement, so agreement is machine-checked, not eyeballed |

**All twelve verified.** See `RELEASED_CODE_TEXT_PATH_EVIDENCE.csv` for the raw values.

---

## 3. The measured result

| Run | Device | Equal-length swap `max\|Δpred\|` | `\|grad_text\|` | `\|grad_ts\|` (control) | Verdict |
|---|---|---:|---:|---:|---|
| local | Windows CPU | **0.0** | **0.0** | 0.032782 | `text_inert` |
| local L=60 | Windows CPU | **0.0** | **0.0** | 0.021277 | `text_inert` |
| 606357 | HPC CPU | **0.0** | **0.0** | 0.040392 | `text_inert` |
| 606358 | HPC **A100-80GB** | **0.0** | **0.0** | 0.040393 | `text_inert` |
| positive control | CPU / A100 | **5.34e-05 / 5.29e-05** | — | — | detectable |
| (A2 model, for contrast) | Windows CPU | 6308.3 | 7.13e+08 | — | `text_active` |

**Four independent runs, two operating systems, two device types → the same verdict.**

The non-zero time-series gradient is the crucial control: it proves the gradient
measurement chain works, so the text gradient being exactly zero is a **real
zero**, not a broken measurement.

---

## 4. Why the A0 GPU evidence previously suggested otherwise

The A0 comparison was `--multimodal 0` vs `--multimodal 1` (jobs 587091 / 587068),
giving Test MSE 0.9685 vs 0.8581. That comparison **changes the sequence length**
(42 → 359) and therefore the dropout random-number stream during training, so it
never isolated text *content*.

Measured at fixed weights in eval mode:

| Comparison | Seq len | `max\|Δpred\|` |
|---|---|---|
| `multimodal=0` vs `1` | 42 vs 359 | **2.384185791015625e-07** |
| equal-length different content | 359 vs 359 | **0.0** |

2.384e-07 = exactly 2·ε for float32 (ε = 1.19e-07). The two flag settings are
**mathematically equivalent** at fixed weights — which is precisely what the
static causal-mask analysis predicts, since the 42 retained patch positions all
precede the text and cannot attend to it.

**Therefore the A0 GPU difference is attributable to sequence-length-dependent
dropout randomness during training, not to text content.**

---

## 5. Scope and limits of this conclusion

| Applies to | Does not apply to |
|---|---|
| author repo `GPT4TS_lora.py` at commit `6ed2101` | the paper's conceptual method |
| `PEFT=0`, released argparse defaults | the A2 corrected reconstruction (which is `text_active`) |
| the recorded compatibility layer (`hpc_compat/`) | any other implementation |
| deterministic equal-length substitution at fixed weights | claims about training-time dynamics |

**Mandatory reporting wording**: this is a statement about **the released code's
functional dependence on text**, established by deterministic intervention.
It is **not** evidence that the paper's method is invalid, and it must never be
used to dismiss multimodal forecasting in general.

## 6. Related

- A2's contrasting `text_active` result and its magnitude audit:
  `A2_TEXT_ACTIVE_MAGNITUDE_AUDIT.md`
- Full narrative: `../TEXT_PATH_RESOLUTION.md`
- Raw evidence: `RELEASED_CODE_TEXT_PATH_EVIDENCE.csv`