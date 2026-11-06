# AGENT HARD RULE (read AGENTS.md first)

---

## HARD RULE — Burgundy login node (2026-11-05 incident, applies to EVERY agent)

**All model work must run via `sbatch` on a compute node.** Never run inference,
`torch.load`, `import torch/transformers`, recursive `du -sh` or downloads on the
login node — that caused a ~2-hour outage on 2026-11-05. Login node is only for
`squeue`/`sacct`/`scontrol`/`mmlsquota`/short `ls`/`cat`.

If ssh authenticates but returns zero bytes: disable
`ServerAliveInterval/CountMax`, open ONE connection with no retry loop, and issue
`pkill` as the **FIRST** command in the first shell window (a `D`-state task keeps
`SIGKILL` pending; `ps` first lost a real window). Never `scancel`.

Full rules: **`AGENTS.md`** (root). SOP: `04_详细说明文档/HPC_LOGIN_NODE_DSTATE_RECOVERY.md`.
Incident: `HANDOFF_20261105/INCIDENT_20261105_LOGIN_NODE_DSTATE.md`.
Tool: `05_程序代码/hpc_login_node_recover.py`.
Also: a `legacy_done.tsv` row is NOT a validated cell, and `squeue -h` prints a
`Last update ...` line so `grep -q .` is not a valid job-existence guard.


# Current code and evidence map revision 9.2

| Entry point | Purpose | Boundary |
|---|---|---|
| scripts/build_delivery_v9.py | Rebuild baseline documents, journal English manuscript, Chinese addendum and English notes in order | Current authoring entry |
| scripts/build_current_documents.py | Hash-pinned baseline plus execution patches and FYP metadata | Intermediate; do not stop here and call the old English manuscript current |
| manuscript/article_source.json | Journal paragraphs and inherited table evidence | Historical snapshot, no new run |
| manuscript/build_manuscript.py | Same text/tables into editable Word and LaTeX; regenerate two plots | Source-CSV arithmetic, not model training |
| manuscript/build_pdf.py | Two pdflatex passes and canonical manuscript PDF | Local compilation executed; cloud Overleaf not executed |
| manuscript/TEMPLATE_PROVENANCE.json | Official-page retrieval and publisher class provenance | Exact current selector file unverified |
| scripts/add_revision9_internal.py | Append current analysis while preserving Q01–Q25 and tables | Chinese internal only |
| presentation/build_status_deck.py | Owner-package status editing with native chart/workbook preservation | Current delivered deck unchanged from revision 8 |
| presentation/build_english_notes.py | English script, full paper-based follow-up reasoning and English Q&A | 606 words, 300 planned seconds; rehearsal not executed |
| scripts/verify_snapshot.py | Frozen CSV arithmetic and optional one-cell raw scoring smoke | Exported Holm column ignored for inference |
| tests_archive/test_miflu_ablations.py | Three named fixed-weight CPU checks | Supplied record has three passed/zero skipped; not rerun here |
| handoff_revision9/validate_result_handoff.py | New return manifest and required status/file checks | Integrity only, never scientific certification |

Older layouts and operational drivers remain in dated folders for provenance. Broad refactoring is deferred while comparable scientific evidence is incomplete. The complete current source inputs are hash-pinned by audit/INPUT_SHA256.json. Frozen historical CSVs must not be overwritten with new-panel results.

FYP administrative source: scripts/FYP_STUDENT_DETAILS.json and scripts/fyp_student_details.py. Revision 9.1 fills the confirmed programme, EE4080 and 2026/27 A while preserving the two required blank fields. Source evidence and render checks are in audit/revision9_1.

| scripts/split_internal_qa_zh.py | Separate Chinese technical report and Q&A companion after the integrated baseline/addendum build | All 150 Q&A paragraphs and 25 reference entries preserved; science tables/figures retained in main |

qa/INTERNAL_QA_ZH.json records the extracted question groups and shared bibliography. The integrated builder runs the split automatically; document/presentation verification now resolves Chinese Q&A from the companion. The old combined report is archived under archive/internal_with_qa_revision9.
