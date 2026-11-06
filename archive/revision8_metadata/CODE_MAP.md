# Code and evidence map

Use README.md for the tested CPU commands. The original training tree is retained. Broad restructuring is deferred until after the school submission.

| Entry point | Purpose | Verification state |
|---|---|---|
| scripts/verify_snapshot.py | Recompute exported headline facts, corrected Holm and optional raw one-cell MSE | Executed |
| tests/test_snapshot_audit.py | New pure CPU audit tests | Executed, separate from archive |
| 01_最终报告/_build2/build_revised.py | Six bilingual current DOCX reports and tables | Executed |
| 01_最终报告/_build2/build_docs.py | Delegates to current revision builder | Audited delegation |
| 01_最终报告/_build2/to_pdf.py | Portable LibreOffice conversion | Available runtime used for rendering |
| 01_最终报告/_build2/verify_docs.py | Native DOCX plus independent PDF text checks | Results in audit/DOCUMENT_VERIFICATION.json |
| 01_最终报告/_build2/make_manifest.py | Measure current pages, native objects, sizes and hashes | Executed; stale scientific prose removed |
| presentation/build_deck.py | Restore checksum-verified owner-corrected PPTX | Executed, byte-identical to upload |
| tests_archive/test_miflu_ablations.py | Archived flags and three no-text model assertions | Static inspection only; runtime not executed |
| 05_程序代码/miflu_model.py | Forecast model and causal fusion paths | Static source inspection |
| 05_程序代码/train_miflu.py | Training CLI and ablation-flag resolution | Training not executed |
| 05_程序代码/eval_windows.py | Shared crop and tensor layout contract | Source read and one-cell smoke |
| 05_程序代码/analysis_postprocess.py | Historical aggregate/uncertainty/paired pipeline | Holm line fixed; whole pipeline not rerun |
| 05_程序代码/verify_miflu_oracle.py | Historical reproduction-seed oracle | Seed-contract mismatch with benchmark noted; not used as universal gate |
| reproduce_all.py | Historical orchestration | Not the validated public quickstart |

The authoritative current inputs are the frozen unsuffixed CSVs, with the defective exported adjusted-p column explicitly quarantined. The audit stores hashes and separate corrected outputs. See DATA_DICTIONARY.md under 02_数字表格 for CSV columns, and audit/NUMERICAL_AUDIT.md for scope limits.

## Revision 2 reading and rebuild paths

- `01_最终报告/_build2/internal_qa.py`: Q01–Q25, English/Chinese questions, answers and evidence locators. The internal report renderer inserts them beside the relevant evidence.
- `presentation/build_pareto_figure.py`: legible plot of the exact eleven-model exported parameter subset.
- `presentation/make_deck_spec.py`: frozen CSV values, authored script and bilingual guidance.
- `presentation/build_deck.py`: restores the exact thirteen-slide owner-edited master. `build_generated_deck.py` retains the earlier generated alternative under a different output filename.
- `presentation/build_notes.py`: planned 5:00 script, ten-question sheet, full explanation guide and bilingual notes DOCX.
- `presentation/render_presentation.py`: portable deck/notes PDF conversion.
- `presentation/verify_presentation.py`: actual chart values, notes/script consistency, timing budget, restored question coverage and optional repeat comparison.
- `scripts/refresh_delivery_docs.py`: measured inventories, complete current diffs and README/manifest refresh.

Revision 3 presentation source: `presentation/source/Week12_User_Corrected.pptx` is the exact owner-edited master. `build_deck.py` restores it with a checksum check. `build_generated_deck.py` is a separate programmatic alternative, not a recreation of manual Office formatting.

Revision 4: `_build2/qa_literature.py` stores bilingual paper arguments, reading locations and short answers. `audit/QA_CITATION_MAP.md/.json` maps their evidence. `build_revised.py --internal-only` rebuilds the affected reports.


Revision 8 current paths: scripts/build_current_documents.py builds eight integrated reports from hash-pinned source_snapshots/v6 plus the anchored status patch. presentation/build_status_deck.py preserves the owner master package while applying the current edit plan. presentation/build_notes.py builds the status-aware notes/script/Q&A from deck_spec.json and the updated QA sources. Older builders are explicitly historical. RESULT_UPDATE_POLICY.md governs every later evidence handoff.
