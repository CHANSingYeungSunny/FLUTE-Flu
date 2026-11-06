# Final visual review and execution scope — revision 2

The final English internal report has 16 PDF pages and the Chinese internal report 17. All 33 page images were inspected individually after the final DOCX render. Q01–Q25 appear in order in each language, beside the relevant tables and explanations. The Word/PDF verification also checks that every question survives. No missing CJK glyphs, page-edge clipping, overlapping tables or unexplained blank pages were detected. Continuing tables repeat their headers. The twelve numbered internal sections remain intact.

The bilingual presentation notes have 14 pages, all individually inspected after the final render. A timing overview precedes one preparation page per slide. Each page separates the spoken English script, Chinese understanding, likely follow-up answer and evidence locator. The spoken script contains 608 whitespace-delimited words, including written-out key numerical readings. Per-slide budgets total 300 seconds. Actual human timing is not executed.

All four other report PDFs were rebuilt. Pixel comparison against the previously reviewed delivery found only progress-report EN page 1 and ZH pages 1, 2, 3, 7, 8 changed. These six changed pages were individually inspected. The remaining 27 pages, including both complete manuscript PDFs, are pixel-identical to the prior visually reviewed versions. Progress reports remain 8/8 EN/ZH pages; manuscripts 8/9.

All thirteen deck slides were visually reviewed individually at slide size. Final local repairs were re-rendered and checked: separated close reproduction-chart labels, kept the text-position label inside its shape, and shortened the final NLinear line. The new parameter plot retains all eleven measured points with larger frontier labels. The passing-cell grid is generated from the model/horizon/lead records. Structure and geometry checks have zero findings. Two editable charts and their embedded workbooks match the source-derived specification. Actual notes match the script and Chinese guidance on every slide.

Final PPTX SHA-256: bf569115a2c5a79b0ce1902204a682b411fc9ff8cdbd6bf5266a0017786f4cbb. Two local builds are byte-identical, including normalised embedded workbook dates. This is reproducibility in this environment, not an assertion that every renderer or software version produces identical pixels.

Executed document and deck commands:

```bash
python 01_最终报告/_build2/build_revised.py --tables-json
python 01_最终报告/_build2/to_pdf.py
python 01_最终报告/_build2/verify_docs.py
python presentation/build_pareto_figure.py
python presentation/make_deck_spec.py
python presentation/build_deck.py
python presentation/build_deck.py --out repeat.pptx
python presentation/build_notes.py
python presentation/render_presentation.py
python presentation/verify_presentation.py --repeat repeat.pptx
python scripts/refresh_delivery_docs.py
```

The packaged DOCX renderer was also executed for both internal DOCX files and the bilingual notes with an explicit fontconfig file for CJK substitution. The final reports retain SimSun/Microsoft YaHei declarations, rendered with Noto CJK substitutes here. Embedded fonts and actual glyphs were checked. verify_docs.py reports FAILURES: 0. Seven separate CPU audit tests passed again in this revision. These results do not certify the archived model suite or GPU training.

Imported forecast panels in the internal report were retained as labelled illustrations and were not independently reconstructed from all raw predictions. The full source figures remain in the reports; the presentation-specific Pareto figure only changes label density, not membership or values.

**Not executed:** native Microsoft Office inspection, human rehearsal, archived no-text model assertions, GPU training and live HPC. Scientific follow-up commands are in EXECUTION_STATUS.md and NO_TEXT_VERIFICATION.md. Native inspection on Windows, from the project root:

```powershell
Start-Process .\presentation\Week12_Progress_Presentation.pptx
Start-Process .\presentation\Presentation_Notes_EN_ZH.docx
Start-Process .\01_最终报告\report_internal_en.docx
Start-Process .\01_最终报告\report_internal_zh.docx
```

Record an uninterrupted rehearsal including slide changes before claiming actual 5:00 ±20 seconds. The notes' Chinese material and follow-up answers are outside the five-minute script.
