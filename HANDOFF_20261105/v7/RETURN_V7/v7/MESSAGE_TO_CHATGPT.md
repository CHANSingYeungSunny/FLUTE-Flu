# Message to ChatGPT — v7 evidence handoff (2026-11-06)

The national common panel is complete and rescored. Use `v7/V7_SCIENTIFIC_ADDENDUM.md` as the
authoritative new-results note; keep the historical revision-9.2 numbers as the old snapshot.

## What is now supported

- 1120/1120 national cells (28 models × 4 lengths × 10 seeds 2021–2030).
- MIFlu seven-channel recovery 40/40; targets exactly equal the NLinear targets.
- Harmonised panels: all-valid and crop. Crop reproduces the historical MIFlu mean 1.4994
  (old 1.4995).
- Leading MSE order on both panels: MIFlu < PatchTST < NLinear.
- Peak: MIFlu 252/1680 step passes (15.0%), PatchTST 215 (12.8%), NLinear 57 (3.4%).
  **The old NLinear peak-champion claim is not reproduced.**
- Event-level: iTransformer 99.1% detection but PIE 71.2%; MIFlu 98.8% and PIE 30.4%;
  PatchTST 97.6% and PIE 34.6%; NLinear 92.6% and PIE 40.6%.
- Ablation: non-monotonic; K4 1.4989 best, K6 1.5457 (n=10), K2 1.5813, K8 1.6124,
  no_lora 1.6330, K12 1.7604.
- Regional Table VI: 51/53 valid `mse_z` rows; 2 missing.
- Walk-forward: only 473/1020 valid MSE rows; 329 non-finite, 218 missing — **not complete**.
- Exploratory paired Wilcoxon/Holm: 349/378 rejections, min adjusted p ≈ 6.9e-10; cells are not
  independent.

## What must change in the documents

Apply `DOCUMENT_UPDATE_MAP.csv` to the manuscript, Chinese internal report, Q&A companion, FYP
report, README, slides (propose-only) and notes:

1. Add the new 1120 panel as a separate result; do not overwrite the historical CSVs.
2. Replace the NLinear peak-champion conclusion with the step/event tables above.
3. Remove any monotonic-depth claim.
4. State walk-forward is partial and Table VI has 2 missing cells.
5. Label the paired statistics exploratory.
6. Do not call the manuscript submission-ready or promise acceptance.

## What is not done

- v7 DOCX/PDF rebuild of the six documents (only the addendum and update map are supplied).
- Strict `RETURN_TO_CHATGPT.zip` rebuild is not yet produced; use the CSV/audit files here and the
  previous return package for structure.
- Numerical foundation models, CDC vintage, JBHI guidance and resource measurements remain
  BLOCKED/UNVERIFIED.

## Files

- `V7_SCIENTIFIC_ADDENDUM.md`
- `DOCUMENT_UPDATE_MAP.csv`
- `../final/` (all scoring CSVs, event table, ablation, regional/WF, audit, FINAL_RESULTS.md)
