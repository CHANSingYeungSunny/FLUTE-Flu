# Revision 9.2 execution record

Executed locally from the project root:

```bash
python scripts/split_internal_qa_zh.py
python render_support/write_fontconfig.py
FONTCONFIG_FILE="$PWD/render_support/fonts.conf" python /root/.codex/skills/builtins/documents/render_docx.py 01_最终报告/report_internal_zh.docx --output_dir /workspace/scratch/3ee30e2684d1/work/r9_2/render_main --emit_pdf
FONTCONFIG_FILE="$PWD/render_support/fonts.conf" python /root/.codex/skills/builtins/documents/render_docx.py 01_最终报告/report_internal_qa_zh.docx --output_dir /workspace/scratch/3ee30e2684d1/work/r9_2/render_qa --emit_pdf
python 01_最终报告/_build2/verify_docs.py
python presentation/verify_presentation.py
```

The main Chinese report is 12 pages instead of 25. The standalone Q&A is 11 pages, preserving all 150 original question/answer paragraphs and all 25 bibliography entries verbatim. The main report has zero Q headings; all 11 scientific tables and six original figure assets remain. Final page images were reviewed. A final small-table flow fix changes only main pages 5–6; those were inspected again and the other ten pages render identically to the prior inspected pass. Document verification has zero failures and presentation verification has no failures. No forecasting result changed.

The integrated build now invokes the split after the Chinese update. The PDF converter includes the companion; verifiers resolve Chinese Q&A from the new file. Syntax checks were executed on these entry points. A single end-to-end full-pipeline rerun was NOT_EXECUTED in this editorial change; the individual split, conversion and verification commands above were executed. Exact full rebuild command: `python scripts/build_delivery_v9.py`, followed by `python 01_最终报告/_build2/to_pdf.py`.

No model/pytest assertion, GPU training, live Burgundy access, cloud Overleaf, human rehearsal or native Microsoft Office inspection was executed in this editorial update. The exact supplied model-test/HPC/aggregation commands remain in audit/revision9/EXECUTION_RECORD.md and handoff_revision9/PROMPT_TO_DEEPSEEK.md. The existing historical dates/counts remain snapshots; the split does not refresh them.

Earlier combined Chinese DOCX/PDF files are preserved in archive/internal_with_qa_revision9. The main/companion shared reference numbering is unchanged, distinct from the English manuscript's first-citation numbering. On future new-result returns, update both documents without reinserting Q&A into the main report or retaining obsolete numerical answers.
