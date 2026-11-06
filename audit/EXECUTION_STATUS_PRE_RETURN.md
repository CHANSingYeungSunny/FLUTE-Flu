# Execution status

| Check | Status | Evidence / exact command |
|---|---|---|
| Corrected CSV and one raw-cell CPU audit | Executed, passed | `python scripts/verify_snapshot.py --raw-smoke` |
| New CPU audit tests | Executed, seven passed | `python -m pytest tests/test_snapshot_audit.py -q` |
| Archived suite collection | Executed, failed on imports/dependencies | `python -m pytest tests_archive --collect-only -q`; ARCHIVE_COLLECTION_LOG.txt. Partial collection is not a reliable suite total. |
| Archived no-text runtime assertions | Not executed | Exact POSIX/PowerShell commands and required files are in NO_TEXT_VERIFICATION.md. |
| GPU training and live HPC | Not executed | No scheduler session or credentials used. Owner command to inspect the known job: `sacct -j 722968 --format=JobID,State,Elapsed,NodeList`; this reads job status only and does not verify scientific completion. Per-cell exports are still required. |
| Training rerun | Not executed | Use the owner's pinned working environment and run `python 05_程序代码/train_miflu.py --help` first. A complete corrected training recipe cannot be certified from a help command. Do not invent absent CLI settings or expected metrics. |
| Revised DOCX/PDF build | Executed using available runtime | `python 01_最终报告/_build2/build_revised.py`; portable conversion: `python 01_最终报告/_build2/to_pdf.py` |
| DOCX/PDF QA | Executed as recorded in DOCUMENT_VERIFICATION.json and VISUAL_QA.md | `python 01_最终报告/_build2/verify_docs.py` |
| Current artefact manifest | Executed, measured current files | `python 01_最终报告/_build2/make_manifest.py` |
| Deck generation | Executed | `python presentation/build_deck.py` |
| Byte-identical deck repeat | Executed, identical on two builds | `python presentation/build_deck.py --out repeat.pptx`, then compare SHA-256 against the first build |
| Native Microsoft Word / PowerPoint | Not executed | Open final files in native applications and verify fonts, notes and layout |
| Human five-minute delivery | Not executed | Record an uninterrupted rehearsal including slide changes; target 5:00, task tolerance ±20 seconds |

## Revision 2 execution record

The six report DOCX/PDF pairs were regenerated. Both internal reports now contain 25 embedded explanatory questions, checked in the actual DOCX and PDF. The deck was rebuilt around four evaluation axes with two editable charts. The bilingual notes DOCX/PDF, script, live Q&A and full explanation guide were regenerated. `python presentation/verify_presentation.py --repeat repeat.pptx` passed with 13 matching notes parts, 608 script words, 300 planned seconds and identical repeat bytes. Both embedded chart workbooks were independently checked against the source-derived spec. `python -m pytest tests/test_snapshot_audit.py -q` again reported seven passed. No archived model/runtime or HPC execution was added.

## Revision 3 execution record

The owner-corrected PPTX was preserved byte for byte and exported to PDF. All six current DOCX/PDF report pairs and bilingual notes were regenerated for the formal author correction. All scientific paragraphs, tables, figures, 25 internal questions per language and spoken script remain unchanged. Current checks are in PRESENTATION_VERIFICATION.json, DOCUMENT_VERIFICATION.json and USER_PPTX_UPDATE.md. No archived model test, training, HPC or native Office execution was added. The seven-test pass record belongs to the previous revision; no new model result is implied.

## Revision 4

Targeted primary-source research strengthened all 25 internal Q&As. Both internal report pairs and external bilingual preparation notes were rebuilt and rendered. All scientific CSVs, the corrected owner deck/PDF, the English speech and school/manuscript reports remain unchanged. Citation-resolution and document consistency checks were executed. No new model assertions, GPU training or live HPC commands were executed; their exact commands remain in NO_TEXT_VERIFICATION.md and this execution record. The earlier seven CPU tests are not presented as a new run.
