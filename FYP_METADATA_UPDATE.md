# FYP Part A metadata update revision 9.1

The owner-supplied Project Summary and Planning Chart confirms on page 1, Part A: BEng — Computer and Data Engineering; course EE4080; academic year/term 2026/27 A. These values now appear in both FYP progress-report languages. Existing student name, number, email, project code, supervisor, assessor and current influenza title remain intact.

The planning-summary form and the progress-report form are different. Page 2 of Requirements_ProjectProgressReport_2627A (1).pdf explicitly lists Number of meetings with supervisor / assessor and Average number of hours spent on the project on weekly basis. Both fields are therefore retained blank. No meeting/hour values are invented. The user requested deletion only if the fields were not required; the official progress template resolves that condition.

The newly supplied planning PDF is preserved in source_snapshots/Project_Summary_and_Planning_Chart_owner_20261105.pdf. It is used here only to confirm administrative metadata. Its older dataset/protocol/results are not merged into the retained historical benchmark. Its original upload date and signature are not independently authenticated by this administrative edit.

Both reports remain eight pages. Body paragraphs, all scientific table cells and figure bytes are unchanged. LibreOffice PDF rendering and final page-image review were executed. Native Word inspection, model tests and HPC access were not executed in this administrative update. See audit/revision9_1 for evidence and commands.

To reapply confirmed metadata after a document rebuild:

```bash
python scripts/fyp_student_details.py --reports-dir 01_最终报告
```

The integrated scripts/build_delivery_v9.py pipeline already calls this metadata function through scripts/build_current_documents.py. Its filename remains stable to avoid breaking existing commands. The manuscript, Chinese internal report, deck and notes retain their revision-9 scientific contents. This administrative patch does not claim a new scientific result or live HPC status.
