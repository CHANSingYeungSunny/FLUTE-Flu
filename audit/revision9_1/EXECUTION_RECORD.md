# Administrative update 9.1 execution record

Scope: Part A of both FYP progress reports only, plus supporting metadata, README, journal and handoff records. No scientific results changed.

Executed from the project root:

```bash
python scripts/fyp_student_details.py --reports-dir 01_最终报告
python render_support/write_fontconfig.py
FONTCONFIG_FILE="$PWD/render_support/fonts.conf" python /root/.codex/skills/builtins/documents/render_docx.py 01_最终报告/progress_report_en.docx --output_dir /workspace/scratch/3ee30e2684d1/work/r9_1/render_en --emit_pdf
FONTCONFIG_FILE="$PWD/render_support/fonts.conf" python /root/.codex/skills/builtins/documents/render_docx.py 01_最终报告/progress_report_zh.docx --output_dir /workspace/scratch/3ee30e2684d1/work/r9_1/render_zh --emit_pdf
python 01_最终报告/_build2/verify_docs.py
```

Both PDFs have eight pages. Final page images were inspected; document verification reports FAILURES: 0. Body paragraphs, all 11 scientific tables per report and both figure assets per report are unchanged. Metadata is confirmed against the owner's summary page 1. Required blank fields are confirmed against the official progress-report template page 2. The newly supplied PDF's older scientific protocol/results have not been imported.

The current manuscript, Chinese internal report, PPTX/PDF, English notes and timed script are byte-identical to revision 9. All 83 frozen historical CSVs are byte-identical. Earlier revision-9 execution receipts remain dated history. The administrative change is reproduced by the updated scripts/fyp_student_details.py and FYP_STUDENT_DETAILS.json.

Not executed in this administrative update:

- Native Word/PowerPoint inspection: NOT_EXECUTED. Open the delivered DOCX/PPTX in the corresponding native application for that manual check.
- Model assertions / archived pytest suite: NOT_EXECUTED. Exact commands remain in audit/revision9/EXECUTION_RECORD.md, including `python -m pytest tests_archive --collect-only -q` and the three-test no-text command.
- HPC, new prediction aggregation, training, cloud Overleaf and human rehearsal: NOT_EXECUTED. The exact supplied monitoring/aggregation commands and boundaries remain in audit/revision9/EXECUTION_RECORD.md and handoff_revision9/PROMPT_TO_DEEPSEEK.md.
- The integrated full document build and unchanged LaTeX/deck builds were not rerun in this metadata update. Current evidence is carried forward from revision 9. The stable full rebuild entry remains `python scripts/build_delivery_v9.py`.
