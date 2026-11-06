# Final visual review and execution scope revision 3

The final deck is byte-identical to the user-corrected PowerPoint upload (SHA-256 d6d25afa551a6bc2bac97ba5b6911fa7616f816a32036c954e96ee6bc440ab10). Its PDF was exported from that file. All thirteen rendered slide images were inspected individually. The owner's cover name, author textbox, closing line removal, theme and slide dimensions are preserved. Small slide footers are exactly as uploaded. No slide was reconstructed from the older generator. The four-axis table has tight text spacing in row 3, retained from the supplied source. Package and geometry checks have zero findings against the new source's dimensions.

All six current report pairs were regenerated and rendered with the packaged DOCX renderer. Page counts remain internal EN/ZH 16/17, progress 8/8, manuscript 8/9. Paragraph/table comparison permits only the formal author substitution CHAN Sing Yeung Sunny to CHAN Sing Yeung; figures and scientific content are unchanged. Pixel comparison found only page 1 changed in each report. Those six changed page images were inspected individually; the other 60 pages are pixel-identical to the previously reviewed outputs. Prior review is retained in VISUAL_QA_REVISION2.md. Both internal reports still contain Q01–Q25 in the actual DOCX and PDF. No missing CJK glyphs or clipping were detected on changed pages.

The bilingual notes DOCX/PDF has fourteen pages. Every final page image was inspected. English script, Chinese guidance, follow-up answers and evidence locators match the uploaded deck's semantic notes. The spoken script remains 608 whitespace-delimited words, with a 300-second pacing budget. Actual human delivery is not executed. CJK font substitutions remain Noto Serif/Sans CJK SC for declared SimSun/Microsoft YaHei.

Both native charts and their embedded Excel workbooks were checked against the frozen source-derived specification. Excel serialisation is compared at absolute tolerance 1e-12; chart caches match the specification. The checksum-verified restore was executed and its output is byte-identical to the owner master. This proves preservation of the uploaded file, not regeneration of its manual formatting from authored code. The separate programmatic alternative is retained for future deliberate editing only.

Executed commands, from project root:

```bash
python presentation/build_deck.py --out repeat.pptx
python presentation/render_presentation.py --only deck
python 01_最终报告/_build2/build_revised.py
python presentation/build_notes.py
python 01_最终报告/_build2/verify_docs.py
python presentation/verify_presentation.py --repeat repeat.pptx
python scripts/verify_snapshot.py
python scripts/refresh_delivery_docs.py
python scripts/package_review.py
```

All seven current DOCX files were also rendered with the packaged render_docx.py --emit_pdf command and an explicit fontconfig file. PDF page images were visually checked as described above. DOCX/PDF and presentation verification have zero failures. Historical record_for_journal files were preserved.

**Not executed:** native Microsoft Office inspection, human rehearsal, archived no-text assertions, GPU training and live HPC. Scientific commands remain in EXECUTION_STATUS.md and NO_TEXT_VERIFICATION.md. Native inspection from the project root on Windows:

```powershell
Start-Process .\presentation\Week12_Progress_Presentation.pptx
Start-Process .\presentation\Presentation_Notes_EN_ZH.docx
Start-Process .\01_最终报告\report_internal_en.docx
Start-Process .\01_最终报告\report_internal_zh.docx
```

Record an uninterrupted talk including slide changes to measure actual delivery time. Chinese preparation and follow-up answers are outside the five-minute script.
