# Question to paper evidence map

Reference IDs match the internal report. Local measurements come from the frozen CSVs. Literature supplies the reason, method or relevant comparison; it does not certify the local result.

| Question | References | Reading location |
|---|---|---|
| Q01 | [13], [5] | Tan et al. [13], §3.3 Datasets and Evaluation Metrics; iTransformer [5], Appendix A.1. |
| Q02 | [13] | Tan et al. [13], §3.1 Reproducibility Note; local eval_windows.py. |
| Q03 | [22] | Kapoor and Narayanan [22], Results, leakage taxonomy L1 and L1.2. |
| Q04 | [3], [5], [19] | PatchTST [3], Appendix A.6.1; iTransformer [5], Appendix A.2 and Table 5; Bouthillier et al. [19], Appendix C.3. |
| Q05 | [22] | Kapoor and Narayanan [22], taxonomy L1, clean separation through modelling and evaluation. |
| Q06 | [21], [2] | Hyndman and Koehler [21], §2.1; Kramer and Shaman [2], Forecast accuracy and comparison. |
| Q07 | [19] | Bouthillier et al. [19], §§2–3, benchmark estimators and sources of variation. |
| Q08 | [21] | Hyndman and Koehler [21], §2.1, MSE/MAE and sensitivity to large residuals. |
| Q09 | [19], [22] | Bouthillier et al. [19], variance analysis; Kapoor and Narayanan [22], model info sheets. |
| Q10 | [4], [3], [5], [7], [8] | Zeng et al. [4], §4; PatchTST [3], §3.1; iTransformer [5], §3; CALF [7] and TimeCMA [8], author abstracts. |
| Q11 | [2], [18] | Kramer and Shaman [2], Forecast accuracy and comparison; Bracher et al. [18], §§3–4. |
| Q12 | [2] | Kramer and Shaman [2], Forecast accuracy and comparison, separate timing/intensity tolerances. |
| Q13 | [2], [18] | Kramer and Shaman [2], Forecast accuracy and comparison / Fig. 2; Bracher et al. [18], §4.2. |
| Q14 | [4], [21] | Zeng et al. [4], §4 NLinear; Hyndman and Koehler [21], §2.1. |
| Q15 | [5] | iTransformer [5], Appendix D Model Efficiency; local BENCH_EFFICIENCY.csv. |
| Q16 | [5] | iTransformer [5], Appendix D, Fig. 10, matched speed/memory measurements. |
| Q17 | [3] | PatchTST [3], Appendix A.6.2, Fig. 5, layers/width and ILI sensitivity. |
| Q18 | [20] | Demšar [20], §3.2.2 Post-hoc tests; local raw-p rank. |
| Q19 | [20] | Demšar [20], §3.2.2 Holm step-down; local exact-enumeration derivation. |
| Q20 | [25] | Lakens [25], Introduction and Testing for Equivalence. |
| Q21 | [6], [9] | Time-LLM [6], author abstract; Chronos [9], §3. |
| Q22 | [24] | Vaswani et al. [24], §3.1 Decoder; local ForecastingLLM.forward and archived assertions. |
| Q23 | [13] | Tan et al. [13], §3.2 Proposed Ablations, w/o LLM / LLM2Attn / LLM2Trsf. |
| Q24 | [4], [13], [14], [23] | Zeng et al. [4], §4; Tan et al. [13], §3.2; Qiu et al. [14], abstract and §§3–5 (preprint); Tashman [23], publisher-indexed abstract. |
| Q25 | [22] | Kapoor and Narayanan [22], model info sheets; EXECUTION_STATUS.md and NO_TEXT_VERIFICATION.md. |

## Corrections to the original rationale

- Illness 70/10/20 is explicitly supported by Tan et al. §3.3, with chronological separation supported by iTransformer Appendix A.1. The exact row counts are local arithmetic.
- PatchTST Appendix A.6.1 has fixed-seed main results and five-seed supervised robustness; iTransformer Appendix A.2/Table 5 has five runs. They do not establish a common three-seed convention.
- PatchTST Appendix A.6.2 specifically reports ILI hyperparameter sensitivity; a cross-model low R² cannot establish tuning is unimportant.
- Complete-batch cropping and the joint threshold after averaging are local choices, not requirements of the cited papers.
- Tashman is used only at publisher-indexed abstract depth; direct publisher access was blocked. Unseen upstream defects and archived runtime outcomes remain unverified.
