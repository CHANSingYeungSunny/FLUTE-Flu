# V8 PDF conversion log — TASK 7 (2026-11-06)

Exact toolchain: `python-docx 1.2.0` builds the DOCX; the prepared LibreOffice-kit CLI converts DOCX->PDF; the same kit's `render` subcommand (pdfium) reports the total `pageCount` even with `--pages 1`. Conversion was re-run here with full stdout/stderr capture so any failure is logged with the exact error. A structural validator PASS is `scientific_readiness: NOT_ASSESSED`.

- NODE: `C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime\primary-runtime\dependencies\node\bin\node.exe`
- CLI: `C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js`
- convert command pattern: `node cli.js convert --input <docx> --output <pdf>`
- page-count command pattern: `node cli.js render --input <pdf> --output-dir <fresh-dir> --pages 1 --dpi 36`
- generated_utc: 2026-11-06T14:49:32Z

## Per-document results

### ieee_manuscript_en_v8

- DOCX: `01_最终报告/v8/ieee_manuscript_en_v8.docx` — bytes 46880, sha256 `672cb12d046f5711ae700a358a8accaf10656113bd50650b9aa4c34e0c2e0443`, paragraphs 63, tables 6, headings 15
- convert command: `C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime\primary-runtime\dependencies\node\bin\node.exe C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js convert --input C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v8\ieee_manuscript_en_v8.docx --output C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v8\ieee_manuscript_en_v8.pdf`
- convert exit code: **0**; stdout: `{"backend":"native","missingFonts":["Courier"],"outputPath":"C:\\Users\\Asus\\Desktop\\FYP code\\MLFlu\\01_最终报告\\v8\\ieee_manuscript_en_v8.pdf"}`; stderr: ``
- PDF: `01_最终报告/v8/ieee_manuscript_en_v8.pdf` — bytes 339735, sha256 `9f7b52fe233a9782883077179805068f2ea31e7d4a98d80d8642bf5f7af44a07`
- page-count command: `C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime\primary-runtime\dependencies\node\bin\node.exe C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js render --input C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v8\ieee_manuscript_en_v8.pdf --output-dir C:\Users\Asus\AppData\Local\Temp\mlflu_v8_pages_ieee_manuscript_en_v8 --pages 1 --dpi 36`
- **PDF page count: 7** (backend pdfium, rc=0)

### report_internal_zh_v8

- DOCX: `01_最终报告/v8/report_internal_zh_v8.docx` — bytes 44433, sha256 `6c597a751f8874ca70677c7e03906a047ab15cc3cc7aafb81bfca713460900af`, paragraphs 46, tables 6, headings 13
- convert command: `C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime\primary-runtime\dependencies\node\bin\node.exe C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js convert --input C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v8\report_internal_zh_v8.docx --output C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v8\report_internal_zh_v8.pdf`
- convert exit code: **0**; stdout: `{"backend":"native","missingFonts":["Courier"],"outputPath":"C:\\Users\\Asus\\Desktop\\FYP code\\MLFlu\\01_最终报告\\v8\\report_internal_zh_v8.pdf"}`; stderr: ``
- PDF: `01_最终报告/v8/report_internal_zh_v8.pdf` — bytes 396939, sha256 `b8c255263efef5160a71ad2e7eab78628fe93fa61e569575ea3bf203077bd4fb`
- page-count command: `C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime\primary-runtime\dependencies\node\bin\node.exe C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js render --input C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v8\report_internal_zh_v8.pdf --output-dir C:\Users\Asus\AppData\Local\Temp\mlflu_v8_pages_report_internal_zh_v8 --pages 1 --dpi 36`
- **PDF page count: 6** (backend pdfium, rc=0)

### report_internal_qa_zh_v8

- DOCX: `01_最终报告/v8/report_internal_qa_zh_v8.docx` — bytes 59621, sha256 `c40253ecc2aa29b0d6b212748ac171ae80345d4a966fde74602ed86b5a8e4db3`, paragraphs 226, tables 0, headings 39
- convert command: `C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime\primary-runtime\dependencies\node\bin\node.exe C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js convert --input C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v8\report_internal_qa_zh_v8.docx --output C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v8\report_internal_qa_zh_v8.pdf`
- convert exit code: **0**; stdout: `{"backend":"native","missingFonts":["Courier"],"outputPath":"C:\\Users\\Asus\\Desktop\\FYP code\\MLFlu\\01_最终报告\\v8\\report_internal_qa_zh_v8.pdf"}`; stderr: ``
- PDF: `01_最终报告/v8/report_internal_qa_zh_v8.pdf` — bytes 678584, sha256 `5fb7be2347ee1f8ef69e4b9ff23321a516d12e0010c55e16c7d442b2000351ed`
- page-count command: `C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\runtime\primary-runtime\dependencies\node\bin\node.exe C:\Users\Asus\AppData\Local\Programs\DeepSeek Harness\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js render --input C:\Users\Asus\Desktop\FYP code\MLFlu\01_最终报告\v8\report_internal_qa_zh_v8.pdf --output-dir C:\Users\Asus\AppData\Local\Temp\mlflu_v8_pages_report_internal_qa_zh_v8 --pages 1 --dpi 36`
- **PDF page count: 14** (backend pdfium, rc=0)

## Summary

| Document | DOCX bytes | PDF bytes | convert rc | PDF pages |
|---|---:|---:|---:|---:|
| ieee_manuscript_en_v8 | 46880 | 339735 | 0 | 7 |
| report_internal_zh_v8 | 44433 | 396939 | 0 | 6 |
| report_internal_qa_zh_v8 | 59621 | 678584 | 0 | 14 |

No PDF was faked. If a conversion had failed, the exact error above would name the reason and no PDF page count would be reported. The manuscript is NOT called submission-ready.
