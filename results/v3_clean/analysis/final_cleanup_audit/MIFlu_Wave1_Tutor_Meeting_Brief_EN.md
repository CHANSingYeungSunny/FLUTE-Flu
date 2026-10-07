# Tutor Meeting Brief (EN) — Wave-1 Analysis

**One-line conclusion:** under the frozen selection rule, the Wave-1 winner is `gpt2_miflu` (avg MSE 4L = 0.771) and the best Non-LLM is `nlinear` (1.070); but the "LLMs beat classical models" narrative must be handled carefully — the LLM family as a whole is *worse*, and the winner's short-horizon edge is erased by a zero-parameter seasonal baseline.

---

## Three facts the tutor must see

### Fact 1: the win belongs to ONE model, not the LLM paradigm

| family | avg MSE 4L |
|---|---:|
| Non-LLM group (nlinear / dlinear / patchtst / itransformer) | **1.142** |
| LLM group (gpt2_miflu / qwen / calf / timecma) | 1.243 |

Paired t = −11.15, **p = 1.44×10⁻⁶**. The Non-LLM family is **significantly more accurate**. The LLM's top rank is carried entirely by `gpt2_miflu`; the other three LLMs all lose to the best Non-LLM. A manuscript framed as "LLM > classical forecasters" will be caught by reviewers.

### Fact 2: at short horizons, a "repeat last year" baseline beats the winning LLM

| horizon | seasonal_naive (0 params) | gpt2_miflu |
|---:|---:|---:|
| L24 | **0.719** | 0.732 |
| L36 | **0.732** | 0.778 |
| L48 | **0.746** | 0.760 |
| L60 | 0.885 | **0.813** |

`seasonal_naive` is **more accurate at L24/L36/L48**. Most of `gpt2_miflu`'s short-horizon accuracy is explained by seasonality, not by the text/LLM machinery. This is the honesty point to stress most.

### Fact 3: the only useful text component is the "dataset description"; LoRA/multimodality do ~nothing

| ablated component | relative harm | p-value |
|---|---:|---:|
| dataset information | **+12.85%** | **0.004** |
| input variable description | +5.80% | 0.079 |
| task instruction | +2.82% | 0.40 |
| multimodal fusion | +1.95% | 0.47 |
| LoRA | +0.26% | 0.95 |

The headline innovations (LoRA fine-tuning + multimodal alignment) are statistically inert. Only the prompt text describing the ILI dataset matters.

---

## Questions to discuss / decide with the tutor

1. **Framing:** should the paper claim "`gpt2_miflu` (a specific LLM adapter) beats baselines" rather than "LLM methods beat classical methods"?
2. **Seasonal baseline:** should `seasonal_naive` be promoted to a formal baseline in the main table (not an appendix)?
3. **Contribution crisis:** ablations show LoRA + multimodality ≈ 0 gain. The "innovation" needs re-argument — keep and explain (text info comes from dataset description), or adjust the storyline?
4. **Cost transparency:** gpt2_miflu is 409× params / 28× training time of nlinear. Show this trade-off table explicitly?
5. **Deferred controls (Wave-2):** 18 negative controls are not yet run — wait for them before finalizing conclusions?

---

## Quick numbers (citable)

- Winner vs runner-up: paired t = −13.33, **p = 3.13×10⁻⁷**, Cohen's d = −5.94.
- Seed stability: `gpt2_miflu` SD = 0.071 (least stable), `nlinear` SD = 0.0029 (very stable).
- Endpoint robustness: ILITOTAL full horizon still ranks gpt2_miflu first (1.608), nlinear best Non-LLM (2.333).
- Test/holdout sealed (0/0); champion not frozen. Peak metrics now computed (PTE/PIE): `nlinear` leads PIE (17.7%), `patchtst` leads PTE (1.61 wk); `gpt2_miflu` is mid-table (PTE 2.12 wk, PIE 41.5%).

**Artifact paths:** full report `Wave1_Final_Analysis_Supervisor_Report.md` (EN) / `_ZH.md` (ZH); data and figures under `results/v3_clean/analysis/`.
