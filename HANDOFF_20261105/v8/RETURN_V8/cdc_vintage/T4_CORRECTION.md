# T4_CORRECTION — authoritative dated correction record

**Date (UTC): 2026-11-06**
**Task:** TASK 4 (CDC calendar / vintage) of `HANDOFF_20261105/NEXT_DEEPSEEK_PROMPT.md`
**Project root:** `C:\Users\Asus\Desktop\FYP code\MLFlu`
**Corrected status:** `COMPLETED`
**Supersedes:** the earlier `HANDOFF_20261105/v8/cdc_vintage/T4_VERDICT.md` verdict
(`status: PARTIAL`, primary label `BLOCKED: no release-calendar/vintage source found`,
peak re-scoring `BLOCKED`) and the corresponding `PARTIAL / BLOCKED` claims across the v8
document set.

This is the authoritative record of the correction. It is written because the project
owner caught an error in the previous TASK 4 verdict.

---

## 1. The error, exactly

A previous subagent, executing TASK 4 on 2026-11-06
(`start_utc 2026-11-06T13:19:57Z` → `end_utc 2026-11-06T13:33:59Z`), fetched **only 20
sample `(epiweek, issue)` rows** from the Delphi Epidata `fluview` endpoint
(`https://api.delphi.cmu.edu/epidata/fluview/`, region `nat`) and declared TASK 4
`PARTIAL` with the primary label `BLOCKED: no release-calendar/vintage source found`
and peak re-scoring `BLOCKED`.

**Root cause:** it did **not inspect the project's own `02_数字表格/` directory**, which
ALREADY contained a complete CDC ILINet vintage reconstruction and a re-scored
season-peak table, built by `05_程序代码/cdc_vintage_build.py` from **the very same**
Delphi Epidata `fluview` endpoint. The old verdict's §E.5 and `CDC_VINTAGE_REPORT.md`
§9 listed the frozen filenames but explicitly declined to read their contents and
dismissed them as out-of-scope / frozen without inspecting them — i.e. functionally the
directory was never checked. Had `02_数字表格/cdc_vintage_report.md` been opened, the
848/7192-row tables, the 18-season peak re-scoring and the written interpretation
limits would have been found.

**Consequence of the error:** "no release-calendar/vintage source found" was factually
wrong — the source existed, was actively used inside the project, and had already produced
the deliverable. "Peak re-scoring BLOCKED" was also wrong: the frozen
`cdc_peak_revintage.csv` re-scores the **reference** season-peak assignment on as-of data
(the 1120-cell model panel is a separate, still-retrospective matter). The 20-row
`v8/cdc_vintage/cdc_vintage.csv` produced by that run is **only a verification sample**,
NOT a replacement for the frozen 7192-row `02_数字表格/cdc_vintage_raw.csv`, the frozen
848-row `02_数字表格/cdc_vintage.csv`, or `02_数字表格/cdc_peak_revintage.csv`.

TASK 4 acceptance is "either a vintage table and re-scored peaks, or a documented
BLOCKED". Both artifacts already exist on disk → TASK 4 is **COMPLETED**.

---

## 2. Frozen artifacts (read + SHA-256 verified 2026-11-06; NOT modified)

All paths relative to project root. `02_数字表格/*` is frozen under AGENTS.md RULE 4.

| Artifact | Rows / size | SHA-256 |
|---|---|---|
| `02_数字表格/cdc_vintage_raw.csv` | 7192 data rows (7193 lines); columns `epiweek,issue,release_date,lag,ili,wili,num_ili,num_patients,num_providers` | `e0c5512b2b6889780f345927708fee3ac3006ff59d78881dc6b55fa31fc7e9c8` |
| `02_数字表格/cdc_vintage.csv` | 848 data rows (849 lines); columns `epiweek,n_issues,first_issue,first_release_date,first_lag,last_issue,last_release_date,ilitotal_first,ilitotal_final,ilitotal_abs_revision,ilitotal_rel_revision_pct,revision_observed` | `5a49e6be748aed251e82084a2b83d8c2f92ca23ef72ef8f442b10481c611b2c9` |
| `02_数字表格/cdc_vintage_report.md` | — | `e2da6b377abc318a311535cd593180d5ea62cd11ee03c31c3ee3fb2e67afd2d7` |
| `02_数字表格/cdc_peak_revintage.csv` | 21 seasons; columns `season,scored_final,scored_asof,peak_week_final,peak_ilitotal_final,peak_week_asof,peak_ilitotal_asof,peak_week_shift,peak_shifted` | `7c9b5df808a1f78cb2e097aec114b3a735b075f6c2a991c24ae3db3883d7a504` |
| `05_程序代码/cdc_vintage_build.py` | 16273 bytes, mtime 2026-11-06 19:51 | `8c1e4b1e31a4339e8d30d6c8f9e62fc181996d47fcea1cb9a5f2d2bceb2a079f` |
| `06_原始数据集/raw/national_illness_raw.csv` | 1025 rows; `release_date` has exactly 8 distinct values | (archived final CSV; NOT a vintage) |

Verified first row of frozen `02_数字表格/cdc_vintage.csv`:
`200340,2,200347,2003-11-28,7,200348,2003-12-05,2108.0,2115.0,7.0,0.332...,True`.

The `cdc_vintage_build.py` docstring states it rebuilds `cdc_vintage_raw.csv`,
`cdc_vintage.csv` AND `cdc_peak_revintage.csv`, with season boundary MMWR week 40 of
year Y .. week 20 of Y+1 from `05_程序代码/innovation/metrics.py`, peak = argmax
ILITOTAL, ties → earliest week. Data source = Delphi Epidata `fluview` endpoint
(region `nat`, public, no key) — the SAME source the previous subagent queried.

### Verified key facts (from the frozen report + peak table)

- 1025 panel epiweeks; **848** with weekly release records; **177** without
  (2002:33, 2003:39, 2004:19, 2005:19, 2006:19, 2007:19, 2008:19, 2010:9, 2013:1).
- **7192** `(epiweek, issue)` rows with `lag<=8`.
- **836 / 848** epiweeks revised (98.6%); |ILITOTAL revision| as % of first print:
  p10 **5.2%**, median **21.8%**, p90 **51.8%**.
- Season-peak FINAL vs AS-OF table: **18 seasons scored**, **7 peak weeks move = 38.9%**
  (2003-04, 2005-06, 2006-07, 2007-08, 2008-09, 2014-15, 2020-21).
- `06_原始数据集/raw/national_illness_raw.csv` `release_date` = 8 distinct annual bulk
  snapshot dates (2013-12-31, 2017-10-24, 2018-10-05, 2019-10-04, 2020-10-02,
  2021-10-08, 2022-10-07, 2023-10-06) — **NOT a vintage**.

---

## 3. Retained evidence from the original (superseded) work

The original verification work is retained verbatim in `T4_VERDICT.md` §B/§C/§D and
in `CDC_VINTAGE_REPORT.md` because it is still useful provenance that the Delphi
endpoint is live and returns successive issues. Original hashes (at
`end_utc 2026-11-06T13:33:59Z`) of the v8 sample artifacts:

| Path (relative to `v8/cdc_vintage/`) | Original SHA-256 |
|---|---|
| `cdc_vintage.csv` (20-row verification sample) | `ffc960e5654291d0b5517ec894f59aad02ebbf463392aa280fe5eae97fa870f2` |
| `build_cdc_vintage.py` | `cb399b79e9672d4e39ee4242a458f85b9a21f80b23906ce92c5ed10decf14a36` |
| `CDC_VINTAGE_REPORT.md` | `fe139859a3cb74f470a1316d9bd894e785965c1acb1c5e292eeee0b6c2ef1bdf` |
| `T4_VERDICT.md` | `180f383ee2f09e2aa4a252a4adad821e1116a0a9a5a84b32cff1d664e837faf1` |

`T4_VERDICT.md` and `CDC_VINTAGE_REPORT.md` are edited by this correction, so their
current on-disk hashes differ from the two values above; the values above are the
original, retained as the historical work record. All `http_evidence/*` bodies / TSVs
and their hashes are unchanged.

The earlier work's conclusions (`PARTIAL`, `BLOCKED: no release-calendar/vintage source
found`, peak re-scoring `BLOCKED`, `cdc_official_revision_id = NOT_AVAILABLE` as the
headline result) are **SUPERSEDED**. `CDC_VINTAGE_REPORT.md` is kept untouched below its
new correction header so the Delphi URL/status evidence remains available.

---

## 4. Scientific limits that MUST be kept (do NOT overclaim)

1. **Delphi `release_date` is a Delphi-ingest proxy**, NOT a CDC-issued official
   revision number. There is no CDC release calendar / official revision id. This
   reconstruction is a Delphi `(epiweek, issue)` vintage; no official CDC vintage or
   revision number is claimed.
2. **Re-scoring is of the REFERENCE peak assignment on as-of data, NOT the 1120-cell
   model panel.** `02_数字表格/cdc_vintage_report.md` §Interpretation limits explicitly
   says it "does not re-score the 1120-cell model panel; it re-scores the *reference*
   peak assignment on as-of data". **Model peak metrics remain retrospective.** No
   real-time / clinical claim.
3. **2002 weeks (and parts of 2003-04) have no real-time vintage** (177 epiweeks have no
   weekly release record; they first appear in the 2013-12-31 bulk reload). The AS-OF
   series is the FIRST PRINT (lag 0) — the value at the end of week W, not at forecast
   issue W+1.
4. **Archived final CSVs are NOT a vintage** (8 annual bulk snapshot dates only).
5. The manuscript is **NOT** called submission-ready.

---

## 5. Files changed by this correction (2026-11-06)

| File | Change |
|---|---|
| `v8/cdc_vintage/T4_VERDICT.md` | rewritten to `status: COMPLETED` + ERROR CORRECTION; original UTC/commands/exit codes/hashes retained |
| `v8/cdc_vintage/CDC_VINTAGE_REPORT.md` | prominent correction header added; existing URL/status evidence kept |
| `v8/cdc_vintage/T4_CORRECTION.md` | this authoritative record (new) |
| `v8/TASK_LOG.md` | ONLY the `## T4` section changed to `COMPLETED` |
| `v8/SCIENTIFIC_AUDIT.md` | only CDC/vintage rows/claims corrected |
| `v8/BLOCKED_AND_UNVERIFIED.md` | only CDC/vintage rows/claims corrected |
| `v8/DOCUMENT_UPDATE_MAP.csv` | only CDC/vintage rows/claims corrected |
| `v8/docs/V8_SCIENTIFIC_ADDENDUM.md` | only CDC/T4 passages corrected |
| `v8/docs/V8_CHANGELOG.md` | only CDC/T4 passage corrected |
| `v8/MESSAGE_TO_CHATGPT.md` | only CDC/T4 passages corrected |

### Explicitly NOT edited (frozen or out of scope)

`02_数字表格/*`, `HANDOFF_20261105/final/*`, `HANDOFF_20261105/v7/*`, `01_最终报告/*`,
`v8/packaging/*`, `v8/RETURN_V8/*`, `v8/T7_VERDICT.md`, `v8/T8_VERDICT.md`,
`v8/foundation/*`, `v8/T5_VERDICT.md`, `v8/T6_VERDICT.md`, `AGENTS.md`, and the
packaged `RETURN_TO_CHATGPT.zip` / `RAW_EVIDENCE.zip`. Copies of the old T4 wording in
those files remain and must be reconciled by the owner separately (see §6).

---

## 6. Known remaining inconsistency (reported, not silently resolved)

Because the DO-NOT-EDIT list is strict, other v8/v7/final/packaged artifacts still carry
the pre-correction `PARTIAL / BLOCKED` T4 wording — notably `v8/T7_VERDICT.md`,
`v8/T8_VERDICT.md`, the `v8/RETURN_V8/*` copies of `MESSAGE_TO_CHATGPT.md` /
`SCIENTIFIC_AUDIT.md` / `BLOCKED_AND_UNVERIFIED.md`, the packaged ZIPs, and the v8
DOCX/PDF bodies under `01_最终报告/v8/`. This correction does NOT edit them. The owner
should rebuild/repackage those from the corrected sources so the record is consistent;
until then, `T4_CORRECTION.md` + the corrected `T4_VERDICT.md` are authoritative for T4.

---

## 7. Bottom line

TASK 4 = **COMPLETED**. The complete CDC ILINet vintage reconstruction (7192 release
records / 848 epiweek summaries) and the re-scored season-peak table (18 seasons, 7 peak
weeks moved = 38.9%) already existed in `02_数字表格/`, built from the same Delphi
`fluview` endpoint. The earlier `BLOCKED: no release-calendar/vintage source found`
verdict was erroneous (20-row sample only; `02_数字表格/` never inspected) and is
SUPERSEDED. Retained limits: Delphi proxy (not a CDC official revision number),
reference-peak-only re-scoring (model peak metrics retrospective), no 2002 real-time
vintage, archived final CSVs are not a vintage. Nothing is fabricated; frozen CSVs are
untouched; the manuscript is NOT called submission-ready.
