# MIFlu reproduction and influenza forecasting evaluation

Current integrated delivery: revision 8, 5 November 2026 Hong Kong time. Author: CHAN Sing Yeung. All eight English/Chinese report and journal-record DOCX/PDF pairs are current full documents. The owner-edited deck layout is retained with authorised status/notes edits. The source owner master is preserved.

## Scientific and execution snapshots

Scientific tables remain the audited historical results: 28 = 13 conventional + 4 LLM-based + 11 frozen encoders; Holm 0/136 (128/136 before correction), minimum adjusted p about 0.0664 and NLinear–PatchTST 0.1172. The 17-model paired family includes MIFlu and excludes DLinear/encoders. These are not new ten-seed inference results.

Returned core artefacts are complete at 160/160. The national 1120 matrix remains in progress: ledger 117 at 4 Nov 23:35 HKT, a later report 139, owner report 141 at 5 Nov 00:15 HKT. No live Burgundy read was made in this review. Supplied no-text CPU record: 3 passed, 0 skipped. Ablation queue: 60/60 DONE, aggregate analysis pending. New stored metrics still mix cropped MIFlu and all-window other-model panels, and full seven-channel MIFlu predictions were not attached. The protocol lock remains unfrozen after submission.

## Current files

`01_最终报告/` contains internal, FYP progress, IEEE manuscript and journal-record reports in EN/ZH, each DOCX/PDF. Internal and journal records retain Q01–Q25 with literature arguments and reading locators. The older journal record is retained under `archive/journal_record_before_audit`; its obsolete scientific narrative is not the current record.

`presentation/` contains the updated 13-slide PPTX/PDF, bilingual notes DOCX/PDF, TALKING_SCRIPT.md, QA_SHEET.md and the full supervisor guide. The English script has 606 whitespace-delimited words and a 300-second plan; human timing and native Office inspection remain not executed. Two native charts and their embedded workbook data are preserved.

`handoffs/20261105_return/` retains the dated return evidence. `audit/return_review_20261105/` records independent checks. As received, the return validator flags one unlisted transient file; quarantining it in a review copy yields PASS. All manifest-listed hashes match. The original uploaded ZIPs are unchanged. Integrity PASS does not establish scientific validity.

## Rebuild current documents and notes

```bash
python scripts/build_current_documents.py
python 01_最终报告/_build2/to_pdf.py
python 01_最终报告/_build2/verify_docs.py
python presentation/make_deck_spec.py
python presentation/build_deck.py
python presentation/build_notes.py
python presentation/render_presentation.py
python presentation/verify_presentation.py
```

LibreOffice and suitable fonts are required for conversion. This review used Carlito as a metrically compatible Calibri substitute, Noto Serif CJK SC for SimSun and Noto Sans CJK SC for Microsoft YaHei. Inspect every output page after rendering in another environment.

## Audit the historical scientific arithmetic

```bash
python -m pip install -r requirements-audit.txt
python scripts/verify_snapshot.py --raw-smoke
python -m pytest tests/test_snapshot_audit.py -q
```

The full ZIP includes raw predictions; the compact ZIP excludes them. These commands do not train models or certify all archived tests.

## New results

Follow RESULT_UPDATE_POLICY.md at each new result handoff. Harmonise scoring before a new common ranking. Complete regional/rolling-origin, numerical-foundation and event-level peak controls and valid inference before stronger publication claims. O1 remains the default; O2 remains conditional validation-only height recalibration with no new GPU training only if suitable exports exist, CPU cost unmeasured.

No git push, journal submission or live HPC action is part of this document delivery.
