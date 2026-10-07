# Remediation plan (PREPARED — NOT EXECUTED)

Per audit §15, this plan is prepared but **not executed** during the read-only
audit. The findings do not require any figure regeneration or metric change; the
only recommended change is **caption wording**.

## Root issue (wording only)

The individual NLinear L24/L60 panel captions in the Chinese report read:

> NLinear L24: solid = ground truth, dashed = prediction.

This is technically true but omits that the curve is a **lead-1 (1-week-ahead)
rolling seed-mean**, which could be misread as the official full-L performance.
The report's §5.4 already carries the "代表曲线" (representative-curve) caveat, so
the semantics are disclosed; only the per-panel caption lacks the qualifier.

## Proposed wording

Replace the two NLinear captions (and, for consistency, the two GPT-2 MIFlu
captions) with an explicit lead-1 statement:

- NLinear L24 → "NLinear L24: 1-week-ahead (lead-1) rolling seed-mean prediction (dashed) vs ground truth (solid), ILITOTAL."
- NLinear L60 → "NLinear L60: 1-week-ahead (lead-1) rolling seed-mean prediction (dashed) vs ground truth (solid), ILITOTAL."
- GPT-2 MIFlu L24/L60 → same pattern.

Optionally add one line under Figure F (gallery): "Each panel shows the lead-1
(1-week-ahead) seed-mean curve, not a single fixed-origin full-horizon forecast."

## Steps (when executed)

1. Edit the caption strings in `results/v3_clean/analysis/final_cleanup_audit/MIFlu_非LLM与LLM流感预测最终报告_中文版.md`.
2. Regenerate DOCX/PDF (preserving the existing 12 embedded figures and the split-count sentence already corrected).
3. Update `final_minimal_deliverables_manifest.json` / `final_minimal_deliverables_qa.json` with the new file hashes.
4. Re-run the visual QA (12 embedded images, English captions, PTE/PIE joint-hit answer, split sentence).

## Explicitly NOT required

- No figure regeneration (figures are already semantically correct and byte-verified).
- No metric recomputation (official `average_MSE_4L` and full-L metrics are unchanged).
- No retraining / no re-running Test.
