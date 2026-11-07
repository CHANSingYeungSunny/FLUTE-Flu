## V8 evidence update — 2026-11-07

Keyed to the requested document surfaces:

- `01_最终报告/v8/ieee_manuscript_en_v8.docx/.pdf`: updated manuscript body
  with the 1,120-cell national panel, separate 1,020-cell legacy walk-forward
  panel, 80/80 foundation rolling-origin roster, non-monotonic ablation,
  retrospective CDC vintage scope, six-model resources, and dated JBHI limits.
- `01_最终报告/v8/report_internal_zh_v8.docx/.pdf`: Chinese internal report
  rebuilt with the same old-snapshot/new-panel separation and explicit
  superseded claims.
- `01_最终报告/v8/report_internal_qa_zh_v8.docx/.pdf`: Q01–Q25 companion
  retained as a separate document and updated with the v8 superseded-claims
  index.
- `01_最终报告/v8/progress_report_en_v8.docx/.pdf`: English FYP progress
  report update; blank meeting and hours fields remain blank.
- `presentation/V8_PROPOSED_UPDATE.md` and
  `presentation/Presentation_Notes_EN_v8.docx/.pdf`: proposed slide/notes
  changes only; owner-edited PPTX was not overwritten.
- `README.md`, `JOURNAL_RECORD_REV9.md`, and `PAPER_TO_CODE.md`: current
  evidence pointers and provenance/T5 guidance update.
- `HANDOFF_20261105/v8/DOCUMENT_UPDATE_MAP.csv`,
  `HANDOFF_20261105/v8/docs/V8_SCIENTIFIC_ADDENDUM.md`,
  `HANDOFF_20261105/v8/docs/V8_CHANGELOG.md`, and
  `HANDOFF_20261105/v8/BLOCKED_AND_UNVERIFIED.md`: final package map,
  addendum, change log, and remaining blocked/unverified register.

Frozen CSVs under `02_数字表格/` and the owner-edited PPTX were preserved.
Validator PASS remains structural only (`scientific_readiness: NOT_ASSESSED`).

# Revision 9.2 Chinese report and Q&A separation

- Moved all Q01–Q25 into report_internal_qa_zh.docx / .pdf as requested by the owner.
- Preserved all 150 question/answer paragraphs, paper reasoning, reading locations and all 25 references verbatim in the companion.
- Retained scientific narrative, 11 scientific tables and six figures in the concise Chinese internal report; cover/navigation wording now points to the companion.
- Added a reproducible split builder and source JSON. The integrated build and PDF converter include the companion; verification resolves the new layout.
- Updated README, journal, delivery index, result-update policy and DeepSeek prompts so future edits preserve the separation.
- FYP 9.1 details, English manuscript, PPT, English notes and frozen scientific CSVs are unchanged. No new training, model tests or live HPC access occurred.

# Revision 9.1 administrative changes

- Filled FYP Part A programme, course and academic year/term from the newly supplied summary, page 1.
- Retained the two blank meetings/hours fields because the official progress-report template explicitly lists them on page 2.
- Updated the reproducible metadata function/JSON and included the owner-supplied source PDF.
- Regenerated both FYP PDFs; body paragraphs, scientific tables and figure assets remain unchanged.
- Updated README, delivery index, journal entry and DeepSeek prompts to preserve the metadata and distinguish the older summary protocol from current scientific evidence.
- Manuscript, Chinese internal report, deck, English notes and scientific source CSVs are unchanged from revision 9. No model/HPC execution was performed.

# Revision 9 changes

- Rewrote the English journal manuscript in authorial scientific prose, separating exploratory findings, functional checks and limitations. Removed queue statuses/job IDs, CLI-flag status tables and F0–F5 audit labels from the paper. Predictive ablation effects remain unreported because compatible per-variant aggregation is unverified.
- Built a real two-column PDF using the unmodified publisher ieeecolor class, with a small documented header/author compatibility file. The exact current selector package and cloud Overleaf execution are not claimed. The abstract has 211 whitespace-delimited words. The paper has five scientific tables, two source-derived plots and 21 references renumbered by first use.
- Preserved historical numerical evidence. Main accuracy tables show the same 28 model means; full per-length source data remain in CSVs. Reproduction comparisons, peak endpoints, proper Holm and parameter conclusions are unchanged. Old trajectory illustrations and operational ablation table remain in the archived revision-8 manuscript rather than being treated as new verified results.
- Added a Chinese internal-report update on manuscript role, verified guidance, O1/O2 and future handoff priorities. All Q01–Q25, named-paper reasons, scientific table cells and original figures are preserved. The FYP report carries forward revision 8.1 student/project details and blanks for unknown fields.
- Retained the exact current owner-layout deck and its chart workbooks. Added English-only notes with full cited explanations, an English live Q&A and full 25-question English companion. The 606-word/300-second planned script is unchanged.
- Added an executable DeepSeek handoff/return contract and integrity validator. The handoff prioritises full seven-channel MIFlu exports, aligned full/cropped panels, compatible ablation references, duplicate-cell control and dependence-aware inference. It records incomplete national/legacy stages and the protocol deviation without inventing new completion counts.
- Corrected one stale hard-coded ablation status in scripts/verify_snapshot.py, which otherwise could reintroduce an obsolete snapshot into verified_facts.json. Source CSVs remain unchanged. Old defective exported p_holm values are retained only as source evidence, not used as the corrected inference.

No new GPU training, live Burgundy query, independent model-test rerun or predictive-variant aggregation was executed in this release. Existing counter values are dated observations. Human rehearsal and native Office inspection are not executed. See audit/revision9/EXECUTION_RECORD.md for exact commands and recorded checks. Publication readiness is not inferred from editing, typesetting, controller completion or integrity PASS.
