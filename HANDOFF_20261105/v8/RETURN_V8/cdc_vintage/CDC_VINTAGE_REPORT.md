# CDC ILINet release-calendar / vintage — TASK 4 report

**Date (UTC): 2026-11-06**
**Scope: `HANDOFF_20261105/v8/cdc_vintage/` only. No other file was written; no frozen CSV, raw prediction, or peak CSV was modified.**
**Companion verdict: `T4_VERDICT.md` (status `PARTIAL`, with one BLOCKED sub-step).**

---

## 1. Dated verdict

**The ACTUAL CDC release date / CDC-issued revision id for ILINet cannot be reconstructed.**
CDC does not publish a release calendar and does not attach a revision/version identifier
to its weekly ILINet values. The primary TASK 4 sub-goal therefore keeps the label:

> `BLOCKED: no release-calendar/vintage source found`

with the exact limitation in §4–§5 and the full URL ledger in §3.

A **reproducible proxy** vintage does exist and WAS fetched and built here: CMU Delphi
Epidata's `fluview` endpoint returns successive `(epiweek, issue)` versions with a
`release_date` field. `cdc_vintage.csv` is a 20-row **proxy** table built only from rows
actually fetched with HTTP 200. It is **not** a CDC vintage table: every row carries
`cdc_official_revision_id = NOT_AVAILABLE` and `source_type =
delphi_epidata_fluview_v4_issue_proxy`.

**Peak re-scoring with as-of data is BLOCKED** (§8): there is no authoritative
`row-index / step → CDC MMWR epiweek` mapping in the local raw dataset or any
manifest/scaler JSON, and no official CDC release date with which to define "as-of".
I did not invent a mapping and did not rewrite any peak CSV.

Overall status is therefore `PARTIAL`, not `COMPLETED` — see `T4_VERDICT.md`.

---

## 2. What was actually fetched (exact commands, status, raw snippets)

All requests were made from Windows with `curl 8.21.0 (Windows) libcurl/8.21.0 Schannel`,
`--connect-timeout 6 -m 15 -sS`, bodies written to `http_evidence/<name>.body`, and
status/time/size written to `http_evidence/http_status_*.tsv`. Full commands are in
`T4_VERDICT.md`; the fetch helper was:

```bash
fetch() {
  name="$1"; url="$2"
  meta=$(curl -sS --connect-timeout 6 -m 15 -o "$OUT/$name.body" \
         -w "%{http_code}\t%{time_total}\t%{size_download}" "$url" 2>"$OUT/$name.err")
  rc=$?
  printf "%s\t%s\t%s\t%s\n" "$name" "$meta" "$rc" "$url" >> "$LOG"
}
```

### 2.1 Live vintage query Q1 — 10 successive issues of one target week (HTTP 200)

```
https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201501&issues=201501-201510
```

Raw response (`http_evidence/delphi_vintage_201501.body`, 2977 bytes, `result:1,
message:"success"`), verbatim opening and closing records:

```json
{ "epidata": [{"release_date":"2015-01-16","region":"nat","issue":201501,"epiweek":201501,"lag":0,...,"wili":4.36093931545351,"ili":4.24896309621967},{"release_date":"2015-01-23","region":"nat","issue":201502,"epiweek":201501,"lag":1,...,"wili":4.33436754449044,"ili":4.16231013307611}, ... {"release_date":"2015-03-20","region":"nat","issue":201510,"epiweek":201501,"lag":9,...,"wili":4.25309128348005,"ili":4.0867269319238}], "result": 1, "message": "success" }
```

Successive `release_date` / `wili` for target epiweek `201501` (all 10 are in
`cdc_vintage.csv`):

| issue | release_date | lag | wili |
|---|---|---|---:|
| 201501 | 2015-01-16 | 0 | 4.36093931545351 |
| 201502 | 2015-01-23 | 1 | 4.33436754449044 |
| 201503 | 2015-01-30 | 2 | 4.2909178182273 |
| 201504 | 2015-02-06 | 3 | 4.26820164804898 |
| 201505 | 2015-02-13 | 4 | 4.26121025051186 |
| 201506 | 2015-02-20 | 5 | 4.25632564628214 |
| 201507 | 2015-02-27 | 6 | 4.2769655436662 |
| 201508 | 2015-03-06 | 7 | 4.2622683012929 |
| 201509 | 2015-03-13 | 8 | 4.24927494256504 |
| 201510 | 2015-03-20 | 9 | 4.25309128348005 |

This reproduces and confirms the handoff's verified research (2015-01-16 /
2015-01-23 / 2015-01-30 / 2015-02-06 with `wili` 4.360939 → 4.334367 → 4.290917 →
4.268201).

### 2.2 Live vintage query Q2 — multiple target weeks across two issues (HTTP 200)

```
https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201449-201501&issues=201501,201502
```

Raw response (`http_evidence/delphi_multiweek.body`, 3569 bytes, 12 records), verbatim
first record:

```json
{"release_date":"2015-01-16","region":"nat","issue":201501,"epiweek":201449,"lag":5,"num_ili":22653,"num_patients":853899,"num_providers":2057,"wili":2.59380451190583,"ili":2.65288986168153}
```

Between issue `201501` and `201502` the `wili` of **all six** sampled target weeks changed:

| epiweek | wili @201501 (2015-01-16) | wili @201502 (2015-01-23) | changed |
|---|---:|---:|---|
| 201449 | 2.59380451190583 | 2.58120134781119 | yes |
| 201450 | 3.6847615030355 | 3.68466242414721 | yes |
| 201451 | 5.00969065911973 | 4.97979938393317 | yes |
| 201452 | 6.07954820613866 | 6.04244192737391 | yes |
| 201453 | 5.54929460779644 | 5.57959786218603 | yes |
| 201501 | 4.36093931545351 | 4.33436754449044 | yes |

These six epiweeks are the **`affected_weeks`** set recorded in `cdc_vintage.csv`
(`201449;201450;201451;201452;201453;201501`).

### 2.3 Cross-check query Q3 (HTTP 200) — single issue

```
https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201501&issues=201501
```

Full raw response (`http_evidence/delphi_issue_201501.body`, 344 bytes):

```json
{ "epidata": [{"release_date":"2015-01-16","region":"nat","issue":201501,"epiweek":201501,"lag":0,"num_ili":27209,"num_patients":640368,"num_providers":1601,"num_age_0":5995,"num_age_1":8210,"num_age_2":null,"num_age_3":7240,"num_age_4":3179,"num_age_5":2585,"wili":4.36093931545351,"ili":4.24896309621967}], "result": 1, "message": "success" }
```

`build_cdc_vintage.py` asserts this is field-for-field identical to the Q1 row for
`(201501, 201501)`, and asserts the two `(epiweek, issue)` pairs returned by both Q1
and Q2 agree. Both assertions passed (`q3_single_issue_cross_check=PASS`,
`duplicate_cross_checks=2 [(201501, 201501), (201501, 201502)]`).

### 2.4 Other raw snippets kept as evidence

- `cdcepi_ili_1415.body` header (HTTP 200):
  `"Release_Week","Region","Week","Sites_Reporting",...,"Perc_Weighted_ILI"` followed by
  `"1441","National",201440,1638,...,1.28,1.28` — `Release_Week` is a `YYWW`
  publication-epiweek proxy, not a calendar release date or CDC revision id.
- `wayback_cdx.body` (HTTP 200):
  `[["urlkey","timestamp","original",...],["gov,cdc)/fluview/surveillance/past-reports.html","20240926175508",...],["...","20240929133101",...],["...","20241021105809",...]]`
  — these are **crawl timestamps**, not publication dates.
- `swh_search.body` (HTTP 200): returns unrelated origins (e.g. a
  `VALOrANt-aimboT-BYpASs` GitHub repo) for the query `ILINet`; no dated CDC ILINet CSV
  origin was found.
- `github_mirror.body` (HTTP 200): `## Code and data for influenza in the United States
  (1998- Jan 2020)` ... `1. ILINet.csv - US CDC FluView ...` — a single-time final CSV
  snapshot, not a vintage.

---

## 3. URL ledger — every URL checked, with HTTP status

| # | URL | HTTP | Evidence file |
|---:|---|---:|---|
| 1 | `https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201501&issues=201501-201510` | 200 | `delphi_vintage_201501.body` |
| 2 | `https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201501&issues=201501` | 200 | `delphi_issue_201501.body` |
| 3 | `https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201449-201501&issues=201501,201502` | 200 | `delphi_multiweek.body` |
| 4 | `https://cmu-delphi.github.io/delphi-epidata/api/fluview.html` | 200 | `delphi_docs.body` |
| 5 | `https://cmu-delphi.github.io/delphi-epidata/api/fluview_v5.html` | **404** | `v5_fluview_docs.body` (attempted, does not exist; nav pointed to `/api/v5-signals/fluview_ilinet.html` instead) |
| 6 | `https://cmu-delphi.github.io/delphi-epidata/api/v5-signals/fluview_ilinet.html` | 200 | `v5_ilinet_signal.body` |
| 7 | `https://cmu-delphi.github.io/delphi-epidata/api/v5_migration.html` | 200 | `v5_migration.body` |
| 8 | `https://cmu-delphi.github.io/epidatr/dev/reference/pub_fluview.html` | 200 | `epidatr_pub_fluview.body` (also re-fetched as `epidatr_fluview_meta.body`, 200) |
| 9 | `https://www.cdc.gov/fluview/surveillance/past-reports.html` | 200 | `cdc_past_reports.body` |
| 10 | `https://www.cdc.gov/fluview/index.html` | 200 | `cdc_fluview_index.body` |
| 11 | `https://stacks.cdc.gov/view/cdc/120452` | 200 | `cdc_stacks_120452.body` |
| 12 | `https://cdcepi.github.io/flu/data.html` | 200 | `cdcepi_data.body` |
| 13 | `https://cdcepi.github.io/flu/data/ILI_2014_2015.csv` | 200 | `cdcepi_ili_1415.body` |
| 14 | `https://web.archive.org/cdx/search/cdx?url=cdc.gov/fluview/surveillance/past-reports.html&output=json&limit=3&filter=statuscode:200` | 200 | `wayback_cdx.body` |
| 15 | `https://archive.softwareheritage.org/api/1/origin/search/ILINet/?limit=3` | 200 | `swh_search.body` |
| 16 | `https://raw.githubusercontent.com/Emergent-Epidemics/US_influenza_data_1998_09-2019/master/README.md` | 200 | `github_mirror.body` |

All `curl` exit codes were 0. Raw status/time/size tables:
`http_evidence/http_status_api.tsv`, `http_status_docs.tsv`, `http_status_extra.tsv`,
`http_status_v5.tsv`, `http_status_v5b.tsv`. No request failed; no error had to be
recorded. (The single non-200 result is the deliberately attempted, non-existent
V5 URL #5.)

Verified quotes from those bodies:

- `#4` — "The `issues` and `lag` parameters in the API allow you to access historical
  versions of the data as they were reported on specific dates."; field
  `epidata[].release_date`; temporal scope `1997w40`.
- `#10` — "A weekly influenza surveillance report prepared by the Influenza Division.
  **All data are preliminary**".
- `#11` — "The data presented each week are preliminary and may change as more data are
  received."
- `#9` — no `release calendar`, `revision`, `revised` or `preliminary` string matched the
  page body; it lists "week ending" + final/archived values only.
- `#12` — "historical data including data that was available during each epidemiological
  week **from 2009/10 to 2014/15**"; "data in the 2013/14 file with `Release_Week = 1342`
  includes all data for the 2013/14 season that was available during at week 42 of that
  season".
- `#8` — "**As of September 22, 2026, the V3 and V4 APIs no longer receive new data.**
  They still serve the historical data they already have, but current data is only added
  to the V5 API".
- `#6` — "`report_time` is the release date when Delphi ingested the weekly CDC
  snapshot. Revisions update past weeks as delayed provider reports arrive." and
  "The date Delphi ingested the CDC weekly file".
- `#7` — V5 migration maps `issue → report_time` and removes `lag` ("Removed in V5.
  Compute client-side as `report_time - reference_time`").

---

## 4. Archived final CSV snapshots are NOT a vintage (explicit statement)

> **An archived final CSV snapshot is not a vintage.** A vintage requires, for a given
> target week W, the value that a real-time system would have seen at the time W was
> first published, together with the date/identifier of that publication. An archived
> CSV contains one final value per week and one bulk "release_date" for the whole file;
> it cannot answer "what was known at week W".

Concrete local evidence:

- `06_原始数据集/raw/national_illness_raw.csv` has an `epiweek` and a `release_date`
  column, but `release_date` has only **8 distinct values** measured here:
  `2013-12-31, 2017-10-24, 2018-10-05, 2019-10-04, 2020-10-02, 2021-10-08, ...`
  — annual bulk snapshot dates, not per-week publication dates.
- `06_原始数据集/raw/national_illness_raw_paper_exact.csv` has `release_date` equal to
  the week's own calendar date (`2002-01-01 00:00:00` for its first row), i.e. it is a
  restatement of the target week, not a publication date.
- `06_原始数据集/raw/us_region_raw.csv` has `epiweek` 199740..202053 with a constant
  `release_date` per block (tail `2022-10-07`).
- The paper's main 966-week file `06_原始数据集/raw/national_illness_author_repo_966.csv`
  has **no `epiweek` and no `release_date`** — only a synthetic weekly `date` column
  (`2002-01-01 0:00` ... `2020-06-30 0:00`, 7-day cadence).
- `99_旧文件存档/recovery/dataset_manifest.json` records `author_dates` first/last and
  `all_7day_cadence: true`, plus `paper_exact_epiweeks` 200240..202113 and
  `project_epiweeks` 200201..202152 — **summary ranges only, no per-row mapping**.
  It also shows `overlap_per_variable ... first_diff_row: 201640` with nontrivial
  differences, i.e. two different snapshots of the same epiweeks, still without any
  per-week publication date.
- Wayback CDX (`#14`) yields crawl timestamps; Software Heritage (`#15`) yielded no
  dated CDC ILINet CSV origin; the GitHub mirror (`#16`) is a single-time final CSV.

Therefore the frozen/archived CSVs cannot be used to reconstruct a real-time vintage.

---

## 5. Official CDC revision id vs Delphi proxy (the distinction that decides TASK 4)

| | Official CDC release / revision | Delphi Epidata `issue` / `release_date` (used here) |
|---|---|---|
| Exists? | **No.** Verified on #9/#10/#11: no release calendar, no revision/version id, only "week ending" + final values and the statements that data are preliminary and may change. | **Yes**, as a reproducible archive of `(epiweek, issue)` versions. |
| What the date means | Would be the date CDC published each weekly file (not published). | The date of the Delphi issue / the date Delphi ingested the CDC weekly file. V4 `release_date` and V5 `report_time` are Delphi-side, not CDC-issued. |
| Revision identifier | Would be a CDC version/revision number (not published). | `issue` (`YYYYWW`) and `lag` are Delphi's own indexing; V5 omits `issue` in responses and computes lag client-side. |
| Legal status for "as-of" claim | The only thing that could support a strict CDC-as-of claim. | A **proxy**; sufficient to show that values were revised over time, insufficient to claim an official CDC release calendar or revision number. |

Consequently `cdc_vintage.csv` sets `cdc_official_revision_id = NOT_AVAILABLE` on
**every** row and `source_type = delphi_epidata_fluview_v4_issue_proxy`. The
`cdc_vintage.csv` built here is a **proxy vintage table**, not a CDC vintage table.
The prior out-of-scope script `05_程序代码/cdc_vintage_build.py` describes Delphi
`release_date` as "the CDC release calendar" / "the exact calendar date of that
release"; that framing conflates the Delphi proxy with an official CDC revision id and
is not adopted here.

---

## 6. Coverage limits

- **CDC official pages (#9/#10/#11):** no release calendar and no revision id at all;
  only "week ending" + final/archived values and "All data are preliminary".
- **CDC EPI GitHub Pages (`https://cdcepi.github.io/flu/data.html`, #12):** provides
  `Release_Week` (`YYWW`) historical files for **2009/10–2014/15 only**. `Release_Week`
  is a publication-epiweek proxy ("data available during week 42 of that season"), NOT
  a calendar release date and NOT a CDC revision number. `ILI_2014_2015.csv` (#13, 200)
  confirms the column.
- **CMU Delphi Epidata `fluview` (#1–#4):** temporal scope starts **1997w40**; fields
  `release_date`, `issue`, `lag`, `epiweek`. This is the strongest reproducible vintage
  source, but it is a proxy. The `issues`/`lag` parameters "allow you to access
  historical versions of the data as they were reported on specific dates".
- **V3/V4 frozen on 2026-09-22 (#8):** "As of September 22, 2026, the V3 and V4 APIs
  no longer receive new data. They still serve the historical data they already have,
  but current data is only added to the V5 API". The live queries in §2 succeeded
  because the requested 2015 historical data are still served.
- **V5 (#6/#7):** `report_time` = "the release date when Delphi ingested the weekly CDC
  snapshot" / "The date Delphi ingested the CDC weekly file"; `issue` is omitted in V5
  responses and `lag` is removed. Even in V5 this is a Delphi ingest date, **not** a
  CDC-issued revision id.
- **Wayback CDX (#14):** returns crawl timestamps, not publication dates.
- **Software Heritage (#15):** no dated CDC ILINet CSV origin found for query `ILINet`.
- **GitHub mirrors (#16):** single-time final CSV snapshots, not vintages.
- **This build's own sample:** deliberately small — 20 unique `(epiweek, issue)` rows,
  6 target epiweeks (`201449, 201450, 201451, 201452, 201453, 201501`), 10 issues
  (`201501..201510`), all `region=nat`, all from 2015. It is a demonstrator of a real
  vintage, not a full 1997w40→2026 reconstruction.

---

## 7. `cdc_vintage.csv` (proxy vintage table built here)

Built by `build_cdc_vintage.py` (exit 0) which parses **only** the saved HTTP 200 bodies;
no value is hand-typed. 20 data rows, deduplicated by `(epiweek, issue)`; Q1/Q2
duplicates and the Q3 single-issue response are asserted identical before collapsing.

Columns (all required columns present):

`epiweek, issue, release_date, region, wili, lag, affected_weeks, source_url,
source_type, cdc_official_revision_id`

- `affected_weeks` = `201449;201450;201451;201452;201453;201501` — the sample epiweeks
  computed (not hardcoded) to have ≥2 issues **and** ≥2 distinct `wili` values, i.e. the
  weeks actually revised in the fetched sample. The per-row target week is `epiweek`.
- `cdc_official_revision_id` = `NOT_AVAILABLE` for every row (§5).
- `source_url` = the exact URL that returned that row.
- `source_type` = `delphi_epidata_fluview_v4_issue_proxy`.

---

## 8. Peak re-scoring determination — **BLOCKED**

**Can peak assignment be re-scored with as-of data? No — BLOCKED.** No peak CSV was
rewritten and no mapping was invented.

Exact evidence checked:

1. **Scaler / manifest JSONs contain no row→week mapping.**
   - `06_原始数据集/scaler_miflu_national.json`: keys `mean, std, train_end(717),
     val_end(819), var_cols` only.
   - `06_原始数据集/scaler_miflu_author966.json`: keys `mean, std, train_end(676),
     val_end(773), var_cols` only.
   `train_end`/`val_end` are row-index split boundaries, not calendar weeks or epiweeks.
   `99_旧文件存档/recovery/dataset_manifest.json` has only `first`/`last`/`n` summary
   ranges, no per-row array.
2. **Frozen peak tables are step-indexed, with no epiweek/date column.**
   - `02_数字表格/BENCH_PTE_PIE_BY_STEP.csv` header:
     `model,family,L,step,weeks_ahead,PTE_wk,PIE_pct,kramer_shaman_pass,...`
   - `HANDOFF_20261105/final/PEAK_BY_STEP.csv` header:
     `model,L,seed,step,pte,pie,passed,n`
   - `HANDOFF_20261105/final/PEAK_EVENTS.csv` header:
     `model,L,seed,step,kind,gt_week,gt_value,pred_week,pred_value,pte,pie` — `gt_week`
     is a numeric **row index** (e.g. `801`, `798`), not a `YYYYWW` epiweek.
   No `step → absolute row → CDC MMWR epiweek` mapping exists locally. The scoring
   scripts that would define it (`score_common.py`, `peak_events.py`) are **not present**
   in the Windows tree; only `05_程序代码/innovation/metrics.py` exists.
3. **The local `epiweek` labels are not CDC MMWR epiweeks.** `dataset_manifest.json`
   gives `paper_exact_epiweeks` first `200240` for calendar date `2002-01-01`
   (`author_dates.first`), and the label year rolls over in April
   (`200252` → `200301` at `2002-03-26` → `2002-04-02`). Delphi MMWR epiweeks follow a
   different convention (e.g. `200201` is the first week of 2002). Joining the paper's
   966 rows to Delphi `epiweek`/`issue` would require **inventing an offset/alignment**,
   which is explicitly forbidden.
4. **The `release_date` columns are bulk snapshot dates / target-week dates, not CDC
   publication dates** (§4), so "as-of" cannot be anchored to an official CDC release.
5. **Peak metric definition is final-vintage retrospective.** Per
   `HANDOFF_20261105/build_v7_manuscript.py` / `build_v7_internal_zh.py`, peaks use
   `ILITOTAL` in patient units reconstructed with the train-fit scaler, detected with
   `find_peaks(prominence=0.15×range, distance=15)` and matched ±8 weeks. The Delphi
   rows fetched here are national `wili`/`ili` percentages, not the scaled ILITOTAL
   channel of the 966-week panel, and the 1120-cell predictions were trained/evaluated
   on final-vintage values. Re-scoring the model peak panel would additionally require
   the raw NPZ predictions and the window→week alignment, which are not in scope.

**Exact missing input:** an authoritative `step (test-window index) → absolute row index
→ CDC MMWR epiweek (YYYYWW)` mapping linking the frozen peak ground truth to the Delphi
`issue`/`release_date` vintage, plus an official CDC-issued release date / revision id
(which does not exist, §5).

**Smallest next action:** recover the scoring provenance (`score_common.py` /
`peak_events.py` and their `test_window → absolute row → date` alignment from the HPC
return package / `RAW_EVIDENCE.zip` provenance), confirm the epiweek convention, then
join that alignment to a full Delphi `issues` pull. Until that mapping exists, any
row→epiweek join would be an invented mapping, and rewriting the frozen peak CSVs is
prohibited by AGENTS.md RULE 4 and by this task's scope.

---

## 9. Prior out-of-scope artifacts (honesty note)

Files `05_程序代码/cdc_vintage_build.py` and `02_数字表格/cdc_peak_revintage.csv`,
`02_数字表格/cdc_vintage.csv`, `02_数字表格/cdc_vintage_raw.csv`,
`02_数字表格/cdc_vintage_report.md` already exist (mtime 2026-11-06 19:50–19:51,
untracked in git). They were produced by an earlier out-of-scope attempt. I did **not**
execute, read as input, modify, or validate them as my results. They live in
`02_数字表格/`, which is frozen under AGENTS.md RULE 4 and is outside my write scope.
Two factual observations about that script, from reading its source only:

- Its own report text states it "**does not re-score the 1120-cell model panel; it
  re-scores the *reference* peak assignment on as-of data**" — so even that earlier
  artifact does not re-score the model peak assignment.
- It labels Delphi `release_date`/`issue` as "the CDC release calendar", which is the
  proxy/official conflation corrected in §5 above.

`cdc_peak_revintage.csv` is a **peak CSV** and was not rewritten.

---

## 10. What remains

1. `BLOCKED: no release-calendar/vintage source found` — retained for the primary
   sub-goal. No CDC-issued release calendar or revision id exists in the checked
   sources; `cdc_official_revision_id` remains `NOT_AVAILABLE`.
2. `BLOCKED` peak re-scoring — missing `step → CDC MMWR epiweek` mapping and official
   CDC release dates (§8). Smallest next action listed above.
3. Optional extension (NOT done, would need a new task): a full Delphi `issues` pull
   for 1997w40→2026 covering the whole panel, using V3/V4 (frozen 2026-09-22) or a V5
   `report_time`-based archive, still labelled as a **proxy** and never as a CDC
   revision id.
4. `HANDOFF_20261105/v7/BLOCKED_AND_UNVERIFIED.md` line "CDC calendar / vintage —
   BLOCKED" and `HANDOFF_20261105/final/SCIENTIFIC_AUDIT.md` line "not reconstructed;
   peaks are retrospective" remain accurate and were deliberately left untouched
   (outside my scope). The v8 document-update task (TASK 7) may cite this report.
5. Per `NEXT_DEEPSEEK_PROMPT.md` DELIVERABLE FORMAT, `HANDOFF_20261105/v8/TASK_LOG.md`
   would normally receive a T4 append; that file is **outside my write scope**, so no
   append was made here. `T4_VERDICT.md` carries the equivalent structured record.

---

## 11. Files in this scope

| Path | Role |
|---|---|
| `cdc_vintage.csv` | 20-row proxy vintage table (only actually-fetched rows) |
| `build_cdc_vintage.py` | reproducible builder (parses saved bodies only) |
| `CDC_VINTAGE_REPORT.md` | this report |
| `T4_VERDICT.md` | structured verdict (`status: PARTIAL`) |
| `http_evidence/*.body`, `*.err`, `http_status_*.tsv` | raw HTTP evidence (bodies, stderr, status/time/size ledgers) |

SHA-256 of each output is recorded in `T4_VERDICT.md` and in the final answer.
