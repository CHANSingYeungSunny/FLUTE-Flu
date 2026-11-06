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


# MIFlu influenza forecasting evaluation revision 9.2

Revision 9.2 separates the Chinese technical report from its 25-question literature-backed companion. Scientific tables and figures remain in the concise report; the complete questions, answers, paper explanations, reading locators and bibliography are preserved separately.

Administrative update 9.1 fills the FYP programme, EE4080 course and 2026/27 A term from the newly supplied planning summary. The progress-report template explicitly requires meetings and weekly hours, which remain blank. See FYP_METADATA_UPDATE.md.

This release integrates the journal-style English manuscript with the latest Chinese internal report, English FYP progress report, owner-layout presentation and English speaking notes. Scientific tables retain the audited historical snapshot. The release adds no newly trained model or completed national matrix. **For the current, later experimental status see [Current verified status](#current-verified-status--fresh-capture-2026-11-07-0028-hkt-2026-11-06-1628-utc) below** — the 1120-cell panel and the seven-channel MIFlu recovery were completed after this revision-9.2 description was written.

## Start with the requested files

| Role | Current file | State |
|---|---|---|
| Chinese internal report | 01_最终报告/report_internal_zh.docx and .pdf | Concise technical report; scientific tables and figures retained; Q&A moved to separate companion |
| Chinese Q&A companion | 01_最终报告/report_internal_qa_zh.docx and .pdf | Q01–Q25, complete cited explanations, reading locators and shared 25-reference bibliography |
| English FYP progress report | 01_最终报告/progress_report_en.docx and .pdf | Revision 9.1 confirmed programme, course and term; required meetings/hours fields retained blank; eight pages |
| English journal manuscript | 01_最终报告/ieee_manuscript_en.docx and .pdf | New journal prose; five scientific tables, two source-derived plots; canonical PDF compiled from LaTeX |
| Presentation | presentation/Week12_Progress_Presentation.pptx and .pdf | Current 13-slide owner-layout deck retained, two editable chart workbooks preserved |
| English speaking notes | presentation/Presentation_Notes_EN.docx and .pdf | English script, full cited paper explanations and evidence locators |
| Timed script | presentation/TALKING_SCRIPT.md | 606 whitespace-delimited spoken words; 300 planned seconds; rehearsal not executed |
| English Q&A | presentation/QA_SHEET_EN.md and SUPERVISOR_EXPLANATION_GUIDE_EN.md | Ten live questions and all 25 extended paper-based explanations |
| Journal record | journal/JOURNAL_RECORD_REV9.md | What changed, what did not and what remains blocked |
| DeepSeek task | handoff_revision9/PROMPT_TO_DEEPSEEK.md | Current scientific priorities and return requirements |

The current Chinese companion and main report must be updated together on future evidence returns. Keep Q&A separate rather than reinserting it into the main report.

The other bilingual reports and earlier journal records remain available for context. Their earlier scientific snapshot is not a new run. The English manuscript is the current journal-style edition; the Chinese manuscript remains an earlier working translation. See DELIVERY_INDEX.json rather than assuming every file has the same editorial revision. The original owner slide master and old English manuscript are preserved in source/archive folders.

## Current verified status — fresh capture 2026-11-07 00:28 HKT (2026-11-06 16:28 UTC)

Measured directly on Burgundy (`cellok.py count`, `squeue`, `sacct`, `mmlsquota`, NPZ validation), not from an older handoff:

| Item | Verified |
|---|---|
| Core artefacts | **160 / 160** |
| National 28 x 4 x 10 panel | **1120 / 1120** (`BY_REASON {}`) |
| Seven-channel MIFlu recovery | **40 / 40 NPZ** from existing checkpoints; all finite, shapes `(N,7,L)`, window counts 170/158/146/134 at L=24/36/48/60, `target_start_row` starts 773; **0 bad files** |
| Slurm queue | **empty** — no jobs running or pending at capture; 739549 / 739626 / 739628 / 740183 no longer in `scontrol` |
| Walk-forward (legacy N=3 panel) | `final/WF_RECOMPUTED.csv` **1020 / 1020 `ok`** (the notes describing 218 missing cells are superseded) |
| Regional Table VI | **53 / 53** valid `mse_z` rows (10-variable regional metric, not the 7-channel national metric) |
| Quota | home 23.9 GB / 50 GB soft; scratch 342 GB / 300 GB soft, **grace 8 days**, hard 1024 GB — cleanup is due but nothing was deleted |

The O1 scoring repair is complete. `final/` holds harmonised scores on **two identical-target-population panels**: `all_valid` (all valid test windows) and `crop` (historical crop). Both give the same leading MSE order MIFlu < PatchTST < NLinear (all-valid 1.7944 / 1.9521 / 2.0782; crop 1.4994 / 1.6352 / 1.9027). The crop panel reproduces the historical MIFlu mean (1.4994 vs 1.4995), which validates the recovery from checkpoints.

**Verification is not agreement with the old manuscript.** On the new harmonised panel the historical peak conclusion changes: step-level passes MIFlu 252/1680, PatchTST 215/1680, NLinear 57/1680; event-level analysis (181,868 events) separates detection from timing/height (iTransformer 99.1% detection but PIE 71.2%; MIFlu 98.8%, PIE 30.4%). The 60-cell ablation ladder is non-monotonic (K4 best, K12 worst). The frozen 28-arm snapshot, the new 1120 panel, the legacy 5-fold N=3 walk-forward panel, the CDC ILINet vintage reconstruction and the foundation-model roster are **separate populations** and must never be pooled. See `HANDOFF_20261105/final/FINAL_RESULTS.md`, `HANDOFF_20261105/final/SCIENTIFIC_AUDIT.md` and `HANDOFF_20261105/v8/SCIENTIFIC_AUDIT.md`.

### Still blocked / not verified (do not write as findings)

- Foundation models (Chronos / TimesFM): provenance, separate roster and **8 zero-shot pilot cells** are real (`COMPLETED_WITH_DOCUMENTED_SCOPE`), but the 80-cell matrix is `NOT_EXECUTED_BY_PROTOCOL`; they are NOT part of the 28-arm family.
- Resource measurements: `PARTIAL`, one cell (L=36, seed=2023), six model rows; MIFlu peak VRAM 4816 MiB on A100 measured, five rows still `NOT_MEASURED`. No full-1120 Pareto claim.
- CDC vintage reconstruction is complete, but Delphi `release_date` is an ingest **proxy**, not a CDC-issued revision number; only the reference peak assignment was re-scored.
- JBHI: dated guidance verification is complete (14/16 pages incl. supplementary, ≤250-word abstract, APC US$2,800 for 2026). The official template-selector download is **UNVERIFIED** (404 / WAF 418 / 302→502). `manuscript_submission_ready: NO`.
- The original expansion protocol was unfrozen when submitted — a disclosed **retrospective** deviation, not prospective confirmation. Ten seeds estimate training variation, not independent epidemics; the four lengths reuse overlapping targets.
- A structural validator `PASS` is `scientific_readiness: NOT_ASSESSED`; it is not scientific certification.

`HANDOFF_20261105/v8/` holds the T1–T8 task log, per-task verdicts, `MESSAGE_TO_CHATGPT.md`, `BLOCKED_AND_UNVERIFIED.md`, evidence and the two return ZIPs. `05_程序代码/hpc_login_node_recover.py` and `04_详细说明文档/HPC_LOGIN_NODE_DSTATE_RECOVERY.md` record the 2026-11-05 login-node D-state incident and its recovery rule; see also root `AGENTS.md`.

## Historical scientific snapshot (frozen, separate)

Historical roster: 13 conventional + 4 LLM-based + 11 frozen encoders = 28. The paired family is 17 non-encoder models INCLUDING MIFlu, excluding DLinear and encoders, with 136 pairs. Correct Holm gives 0/136 rejections versus 128/136 raw p<0.05, minimum adjusted p about 0.0664, and NLinear–PatchTST 0.1172. Recompute from raw p-values; the original adjusted column is defective. The three leading MSE and PIE orders are inverted at both ends, a descriptive local change rather than evidence of independence. Frozen-feature findings do not cover all LLM forecasting. These are old-snapshot facts in `02_数字表格/*.csv`; never overwrite them with new panels.

O1 remains the default for any further work; O2 (validation-only peak-height calibration) is optional and unexecuted. RESULT_UPDATE_POLICY.md remains the standing instruction for coordinated scientific rewrites on each new handoff.

## Manuscript format and readiness

The official JBHI author page was retrieved directly on 5 November 2026. It specifies single-spaced double-column manuscripts with embedded tables/figures, abstract at most 250 words, and a 14-page regular-paper limit including supplementary material. The exact current template-selector download returned HTTP 418. The included unmodified ieeecolor/generic files came from the publisher package linked by the official IEEE EMBS BHI 2024 page. review_layout.sty removes sample masthead/LOGO material corrects the author paragraph and restores the omitted References heading without changing body dimensions or columns. See manuscript/TEMPLATE_PROVENANCE.json for source URLs and hashes.

The English PDF is a real local LaTeX compilation, not a Word export presented as Overleaf. Cloud Overleaf execution and exact-current-selector equivalence are not verified. The Word copy is an editable two-column version of the same text/tables, not a claim of pixel-identical LaTeX typography. Formatting does not establish submission readiness or acceptance. Scientific limitations remain in the paper; scheduler details stay in the internal record/handoff.

## Rebuild and verify

```bash
python scripts/build_delivery_v9.py
python 01_最终报告/_build2/to_pdf.py
python manuscript/build_pdf.py
python presentation/build_english_notes.py
python presentation/render_presentation.py --only deck
python scripts/verify_snapshot.py --raw-smoke
python 01_最终报告/_build2/verify_docs.py
python presentation/verify_presentation.py
```

English notes PDF conversion requires LibreOffice, as do the report Word copies. The canonical English manuscript PDF must come from manuscript/build_pdf.py; the old converter now delegates that file to LaTeX. Required tools: Python with python-docx, NumPy, pandas, SciPy and matplotlib; pdflatex with standard LaTeX packages; LibreOffice and suitable fonts. Do not treat renderer/font differences as scientific changes. Exact executed and not-executed commands are in audit/revision9/EXECUTION_RECORD.md.

## Packages and the next result handoff

The full ZIP retains historical code/data/predictions and the dated original return evidence. The compact review ZIP omits large raw predictions but contains the current documents, CSVs, code and evidence records. The Overleaf ZIP is a self-contained LaTeX source/preview package. The focused DeepSeek ZIP contains the prompt, contract, analysis and current requested documents. Give DeepSeek the focused handoff and, where file-size limits permit, the full project; otherwise make the full folder available on disk and record its path/hash. The Overleaf and review ZIPs are not additionally required if their contents are already accessible through the full project.

DeepSeek must return readable and raw evidence ZIPs into the same extraction root, with fresh capture times, per-cell configs, compatible scoring panels and raw tensors for new claims. handoff_revision9/validate_result_handoff.py checks structure/hashes/declarations only and always labels scientific readiness NOT_ASSESSED. ChatGPT then verifies raw evidence and updates the whole scientific narrative. There is no unattended HPC monitoring in this instruction.
