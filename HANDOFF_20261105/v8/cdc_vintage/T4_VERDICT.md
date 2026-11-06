# T4_VERDICT — CDC calendar / vintage (TASK 4) — CORRECTED 2026-11-06

> **CORRECTION (2026-11-06) — THIS VERDICT SUPERSEDES THE PREVIOUS ONE.**
> The earlier verdict on this file (`status: PARTIAL`, primary label
> `BLOCKED: no release-calendar/vintage source found`, peak re-scoring `BLOCKED`) was
> **WRONG** and is **SUPERSEDED**. TASK 4 is **COMPLETED**. The complete CDC ILINet
> vintage reconstruction and the re-scored season peaks already existed in the frozen
> project directory `02_数字表格/` before this task ran; the earlier run failed to inspect
> it. The authoritative dated record is `T4_CORRECTION.md`. The original commands, exit
> codes and SHA-256 ledger are retained verbatim in §B / §C below as a historical record
> of the verification work.

```
status: COMPLETED
corrected_utc: 2026-11-06
start_utc: 2026-11-06T13:19:57Z   (original verification work, unchanged)
end_utc:   2026-11-06T13:33:59Z   (original verification work, unchanged)
scope:     HANDOFF_20261105/v8/cdc_vintage/   (write ONLY here; directory created)
task:      TASK 4 of HANDOFF_20261105/NEXT_DEEPSEEK_PROMPT.md
supersedes: prior `status: PARTIAL` / `BLOCKED: no release-calendar/vintage source found`
```

**COMPLETED.** TASK 4 asked for "either a vintage table and re-scored peaks, or a
documented BLOCKED". The project ALREADY contains a complete, frozen CDC ILINet vintage
reconstruction AND a re-scored season-peak table, both built from the **Delphi Epidata
`fluview` endpoint — the SAME source** the original verification work queried. The
acceptance criterion "a vintage table and re-scored peaks" is therefore satisfied on
disk. No result is fabricated; no frozen CSV, raw prediction, or peak CSV was modified;
no file outside the allowed v8 set was written by this correction.

---

## A. Corrected evidence — frozen project artifacts (read + hash-verified 2026-11-06)

All paths relative to project root `C:\Users\Asus\Desktop\FYP code\MLFlu`. SHA-256
values re-computed on 2026-11-06 and match the project-owner-verified values exactly.

| Frozen artifact | Size / rows | SHA-256 | What it is |
|---|---|---|---|
| `02_数字表格/cdc_vintage_raw.csv` | 7192 data rows (7193 lines) | `e0c5512b2b6889780f345927708fee3ac3006ff59d78881dc6b55fa31fc7e9c8` | per-`(epiweek, issue)` release records, `lag<=8`; columns `epiweek,issue,release_date,lag,ili,wili,num_ili,num_patients,num_providers` |
| `02_数字表格/cdc_vintage.csv` | 848 data rows (849 lines) | `5a49e6be748aed251e82084a2b83d8c2f92ca23ef72ef8f442b10481c611b2c9` | per-epiweek summary: first/last issue + release date + first/final ILITOTAL + revision; columns `epiweek,n_issues,first_issue,first_release_date,first_lag,last_issue,last_release_date,ilitotal_first,ilitotal_final,ilitotal_abs_revision,ilitotal_rel_revision_pct,revision_observed` |
| `02_数字表格/cdc_vintage_report.md` | — | `e2da6b377abc318a311535cd593180d5ea62cd11ee03c31c3ee3fb2e67afd2d7` | documents coverage, revisions, season-peak FINAL vs AS-OF table, and interpretation limits |
| `02_数字表格/cdc_peak_revintage.csv` | 21 seasons | `7c9b5df808a1f78cb2e097aec114b3a735b075f6c2a991c24ae3db3883d7a504` | season peaks re-scored on AS-OF (first print) vs FINAL, with `peak_week_shift` / `peak_shifted` |
| `05_程序代码/cdc_vintage_build.py` | 16273 bytes, mtime 2026-11-06 19:51 | `8c1e4b1e31a4339e8d30d6c8f9e62fc181996d47fcea1cb9a5f2d2bceb2a079f` | the reproducible builder; docstring states it rebuilds `cdc_vintage_raw.csv`, `cdc_vintage.csv`, `cdc_peak_revintage.csv`; season boundary = MMWR week 40 of Y .. week 20 of Y+1 from `05_程序代码/innovation/metrics.py`; peak = argmax ILITOTAL, ties → earliest week |

Verified first row of frozen `02_数字表格/cdc_vintage.csv`:
`200340,2,200347,2003-11-28,7,200348,2003-12-05,2108.0,2115.0,7.0,0.332...,True`.

Key verified facts (from `02_数字表格/cdc_vintage_report.md` and
`02_数字表格/cdc_peak_revintage.csv`, re-checked 2026-11-06):

- **1025** panel epiweeks; **848** with weekly release records; **177** without
  (2002:33, 2003:39, 2004:19, 2005:19, 2006:19, 2007:19, 2008:19, 2010:9, 2013:1).
- **7192** `(epiweek, issue)` rows with `lag<=8`.
- **836 / 848** epiweeks revised (98.6%); |ILITOTAL revision| as % of first print:
  p10 **5.2%**, median **21.8%**, p90 **51.8%**.
- Season-peak table comparing FINAL vs AS-OF: **18 seasons scored**, **7 peak weeks
  move = 38.9%** (2003-04, 2005-06, 2006-07, 2007-08, 2008-09, 2014-15, 2020-21).
- The archived `06_原始数据集/raw/national_illness_raw.csv` `release_date` column has
  only **8 distinct values** (2013-12-31, 2017-10-24, 2018-10-05, 2019-10-04,
  2020-10-02, 2021-10-08, 2022-10-07, 2023-10-06; 1025 rows) — annual bulk snapshot
  dates, **NOT a vintage**. The Delphi per-`(epiweek, issue)` `release_date` is what
  makes a real-time reconstruction possible.

---

## ERROR CORRECTION — why the previous BLOCKED verdict was wrong

1. **The source WAS found and already used.** The earlier subagent fetched **only 20
   sample `(epiweek, issue)` rows** from `https://api.delphi.cmu.edu/epidata/fluview/`
   (region `nat`) and then declared `BLOCKED: no release-calendar/vintage source found`
   / `PARTIAL` (with peak re-scoring `BLOCKED`). That same Delphi `fluview` endpoint is
   the data source of `05_程序代码/cdc_vintage_build.py`, which had **already** produced
   the complete frozen reconstruction in `02_数字表格/`. The "no vintage source found"
   conclusion was therefore factually wrong: the source existed and was in active use
   inside the project.
2. **`02_数字表格/` was not inspected.** The previous run did not check the project's own
   `02_数字表格/` directory. Its §E.5 (and `CDC_VINTAGE_REPORT.md` §9) listed the frozen
   filenames but explicitly declined to read their contents and dismissed them as
   out-of-scope / frozen without inspecting them. Had `02_数字表格/cdc_vintage_report.md`
   been opened, the 848/7192-row tables, the 18-season peak re-scoring and the written
   interpretation limits would have been found. The `BLOCKED` verdict is the direct result
   of that omission. The project owner caught the error.
3. **The 20-row table here is a verification sample, NOT the deliverable.**
   `HANDOFF_20261105/v8/cdc_vintage/cdc_vintage.csv` (20 rows, 6 epiweeks from 2015,
   sha256 `ffc960e5654291d0b5517ec894f59aad02ebbf463392aa280fe5eae97fa870f2`) is only a
   verification sample of the Delphi endpoint. It is **NOT** a replacement for the
   frozen **7192-row** `02_数字表格/cdc_vintage_raw.csv`, nor for the frozen **848-row**
   `02_数字表格/cdc_vintage.csv`, nor for `02_数字表格/cdc_peak_revintage.csv`. Treating the
   20-row sample as "the" vintage and concluding the rest was impossible was the error.
4. **Peak re-scoring WAS already done.** `02_数字表格/cdc_peak_revintage.csv` re-scores
   the REFERENCE season-peak assignment on AS-OF first-print data vs FINAL and reports the
   7/18 peak-week moves. The earlier claim that peak re-scoring is `BLOCKED` for lack of a
   `step → MMWR epiweek` mapping conflated two different things: the frozen reconstruction
   re-scores the **reference peak assignment** (by MMWR epiweek, from the builder's
   `season_of`/`recess`), not the 1120-cell model panel (which remains retrospective —
   see "Remaining scientific limits" below). The reference re-scoring is complete on disk.

**Old verdict is SUPERSEDED, not deleted.** The original URL/status ledger, commands and
hashes (§B/§C/§D) are retained as useful provenance that the Delphi endpoint is live
and returns successive issues; only the `PARTIAL` / `BLOCKED` *conclusions* are corrected.

---

## Remaining scientific limits (MUST be kept — do not overclaim)

1. **Delphi `release_date` is a Delphi-ingest proxy.** It is NOT a CDC-issued official
   revision number and there is no CDC release calendar / official revision id. Do NOT
   claim an official CDC vintage or revision number was reconstructed. The reconstruction
   is explicitly a Delphi `(epiweek, issue)` vintage.
2. **Re-scoring is of the REFERENCE peak assignment, NOT the 1120-cell model panel.**
   `02_数字表格/cdc_vintage_report.md` §Interpretation limits states it "does not
   re-score the 1120-cell model panel; it re-scores the *reference* peak assignment on
   as-of data and quantifies peak-week instability". **Model peak metrics remain
   retrospective**; no real-time / clinical claim is added.
3. **2002 weeks have no real-time vintage.** 2002 epiweeks (and parts of 2003-04) have no
   weekly release record in the archive (177 epiweeks missing overall); they first appear
   in the 2013-12-31 bulk reload, so their `first_lag` is large and those weeks have NO
   real-time vintage. The AS-OF series is the FIRST PRINT (lag 0), i.e. the value at the
   end of week W, not the value at forecast issue W+1.
4. **Archived final CSVs are NOT a vintage** (8 annual bulk snapshot dates only).
5. The manuscript is **NOT** called submission-ready.

---

## B. Commands + exit codes (ORIGINAL WORK — RETAINED VERBATIM)

All commands ran in Git Bash on Windows from
`C:/Users/Asus/Desktop/FYP code/MLFlu`. Every Bash tool call returned **exit code 0**;
every inner `curl` returned `curl_rc=0`; `python build_cdc_vintage.py` returned
**exit code 0**. No command failed; no error had to be recorded. curl version:
`curl 8.21.0 (Windows) libcurl/8.21.0 Schannel`.

Common fetch helper used in commands 1–4 (verbatim):

```bash
fetch() {
  name="$1"; url="$2"
  meta=$(curl -sS --connect-timeout 6 -m 15 -o "$OUT/$name.body" \
         -w "%{http_code}\t%{time_total}\t%{size_download}" "$url" 2>"$OUT/$name.err")
  rc=$?
  printf "%s\t%s\t%s\t%s\n" "$name" "$meta" "$rc" "$url" >> "$LOG"
}
```

**Command 1 — start time, directory structure, raw dataset (exit 0):**
```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
ls -la "HANDOFF_20261105/v8/"
ls -la "06_原始数据集/" "06_原始数据集/raw/"
```

**Command 2 — live Delphi API fetches (exit 0):**
```bash
OUT="HANDOFF_20261105/v8/cdc_vintage/http_evidence"; mkdir -p "$OUT"
LOG="$OUT/http_status_api.tsv"
fetch delphi_vintage_201501 "https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201501&issues=201501-201510"
fetch delphi_issue_201501   "https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201501&issues=201501"
cat "$LOG"; cat "$OUT/delphi_vintage_201501.body"; cat "$OUT/delphi_issue_201501.body"
```

**Command 3 — CDC / Delphi documentation URL verification (exit 0):**
```bash
LOG="$OUT/http_status_docs.tsv"
fetch delphi_docs         "https://cmu-delphi.github.io/delphi-epidata/api/fluview.html"
fetch epidatr_pub_fluview "https://cmu-delphi.github.io/epidatr/dev/reference/pub_fluview.html"
fetch cdc_past_reports    "https://www.cdc.gov/fluview/surveillance/past-reports.html"
fetch cdc_fluview_index   "https://www.cdc.gov/fluview/index.html"
fetch cdc_stacks_120452   "https://stacks.cdc.gov/view/cdc/120452"
fetch cdcepi_data         "https://cdcepi.github.io/flu/data.html"
fetch cdcepi_ili_1415     "https://cdcepi.github.io/flu/data/ILI_2014_2015.csv"
cat "$LOG"
```

**Command 4 — extra vintage query + Wayback / SWH / GitHub mirror (exit 0):**
```bash
LOG="$OUT/http_status_extra.tsv"
fetch delphi_multiweek "https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201449-201501&issues=201501,201502"
fetch wayback_cdx      "https://web.archive.org/cdx/search/cdx?url=cdc.gov/fluview/surveillance/past-reports.html&output=json&limit=3&filter=statuscode:200"
fetch swh_search       "https://archive.softwareheritage.org/api/1/origin/search/ILINet/?limit=3"
fetch github_mirror    "https://raw.githubusercontent.com/Emergent-Epidemics/US_influenza_data_1998_09-2019/master/README.md"
cat "$LOG"; cat "$OUT/delphi_multiweek.body"
```

**Command 5 — V5 `report_time` / freeze verification (exit 0):**
```bash
LOG="$OUT/http_status_v5.tsv"
fetch v5_fluview_docs     "https://cmu-delphi.github.io/delphi-epidata/api/fluview_v5.html"   # 404, attempted
fetch epidatr_fluview_meta "https://cmu-delphi.github.io/epidatr/dev/reference/pub_fluview.html"
LOG="$OUT/http_status_v5b.tsv"
fetch v5_ilinet_signal "https://cmu-delphi.github.io/delphi-epidata/api/v5-signals/fluview_ilinet.html"
fetch v5_migration     "https://cmu-delphi.github.io/delphi-epidata/api/v5_migration.html"
tr '\n' ' ' < "$OUT/v5_ilinet_signal.body" | grep -o -i -E ".{0,140}(report_time|ingested the CDC weekly file).{0,200}"
```

**Command 6 — local read-only provenance / mapping checks (exit 0):**
```bash
head -3 "06_原始数据集/raw/national_illness_author_repo_966.csv" / "national_illness_raw.csv" / "national_illness_raw_paper_exact.csv" / "us_region_raw.csv"
awk -F, 'NR>1{print $2}' "06_原始数据集/raw/national_illness_raw.csv" | sort -u | wc -l
find . -iname "*peak*" -not -path "./.git/*"
head -2 "02_数字表格/BENCH_PTE_PIE_BY_STEP.csv" "HANDOFF_20261105/final/PEAK_BY_STEP.csv" "HANDOFF_20261105/final/PEAK_EVENTS.csv"
git log --oneline -5 -- "02_数字表格/cdc_peak_revintage.csv"
```

**Command 7 — build the table (exit code 0):**
```bash
cd "HANDOFF_20261105/v8/cdc_vintage" && python build_cdc_vintage.py; echo "EXIT_CODE=$?"
```
stdout:
```
rows=20
distinct_epiweeks=6
distinct_issues=10
affected_weeks=201449;201450;201451;201452;201453;201501
duplicate_cross_checks=2 [(201501, 201501), (201501, 201502)]
q3_single_issue_cross_check=PASS
wrote ...\cdc_vintage.csv
EXIT_CODE=0
```

**Command 8 — hashes + end UTC (exit 0):**
```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
find . -type f ! -name "T4_VERDICT.md" | sort | while read -r f; do sha256sum "$f"; done
```

---

## C. Output paths + SHA-256 (ORIGINAL WORK — RETAINED VERBATIM)

All paths relative to `HANDOFF_20261105/v8/cdc_vintage/`.

| Path | SHA-256 |
|---|---|
| `cdc_vintage.csv` | `ffc960e5654291d0b5517ec894f59aad02ebbf463392aa280fe5eae97fa870f2` |
| `build_cdc_vintage.py` | `cb399b79e9672d4e39ee4242a458f85b9a21f80b23906ce92c5ed10decf14a36` |
| `CDC_VINTAGE_REPORT.md` | `fe139859a3cb74f470a1316d9bd894e785965c1acb1c5e292eeee0b6c2ef1bdf` |
| `T4_VERDICT.md` | self-hash omitted (self-referential); computed after file close and reported in the final answer |
| `http_evidence/http_status_api.tsv` | `9bec8248b08ff87ceaa5d056620419af0e1b13f834763f8eb13d1dcb978e34eb` |
| `http_evidence/http_status_docs.tsv` | `e28b6b946b53f9c7624d1489fde50e4f4b627b30f5d98b261fb4cee234695ff3` |
| `http_evidence/http_status_extra.tsv` | `437caae03be9a759abeaa265ae5b68e6348973a434f16857c2684b43bdcd3ec9` |
| `http_evidence/http_status_v5.tsv` | `71fcffaf6a3a5eebc6e0a70376ffff611dd5c7bc52f9ce6cd7507ddb59987bf4` |
| `http_evidence/http_status_v5b.tsv` | `9cf5e5eb778d3fa6816006c0d5b137a3558fe337535c8e030114d335056b74c1` |
| `http_evidence/delphi_vintage_201501.body` | `dbf6be6b631d97c8a641f8e08541dfccfff653ac616fcef5b7c0a3b2b0ae3dac` |
| `http_evidence/delphi_multiweek.body` | `f3245673d40df544230ed3e112eb0655fbe85bebb73af217b631751b7cfb8d56` |
| `http_evidence/delphi_issue_201501.body` | `235b7c67eb5fb41a874e7e8a91fd667ba4c5e3537084913734de4d9dbfdc7ba9` |
| `http_evidence/delphi_docs.body` | `d23442384653cf3575caf8e2a504b6b4bd25b7f99ac9a9e335cc62acd80ae3f1` |
| `http_evidence/cdc_past_reports.body` | `7611232b94b95f577e1a2bd706ba3b0e8d0c005d6d8f78fd1827b991e4d336d5` |
| `http_evidence/cdc_fluview_index.body` | `9eff47e9d5155347c0ca82c9a111818a417f9dfdb7084113d8baf207e52a7986` |
| `http_evidence/cdc_stacks_120452.body` | `7ae65bfc44d7ac81ebe3768065414fdccc165f2b33c9a1d1e6ffbcf68edace1b` |
| `http_evidence/cdcepi_data.body` | `d6f36c7f52ea8c4d881953860a35d2919f553feb6cfc676f5ba78c1e28510a67` |
| `http_evidence/cdcepi_ili_1415.body` | `46feff3a529605bb681ab34b7bb408db354fbac4fbb862899782807dc1b1e3f1` |
| `http_evidence/epidatr_pub_fluview.body` | `a1a8c88fcada691f888dd0c3be808ba9006f2f7e45dc0a8d3139b0f18ba939e1` |
| `http_evidence/epidatr_fluview_meta.body` | `a1a8c88fcada691f888dd0c3be808ba9006f2f7e45dc0a8d3139b0f18ba939e1` |
| `http_evidence/wayback_cdx.body` | `98a7ab848beb662dc1e1a897a7655a9f11630bcee2f4ca10a38f2546aea63d10` |
| `http_evidence/swh_search.body` | `bf94320e822a3ff53d33f1303a4a5a8c0a19750d8576386fd91b54893b7d9bd4` |
| `http_evidence/github_mirror.body` | `d1016447269cb450ef4fa7373c673175d82d7a8fda0c4b0e52ee968b0da1c13f` |
| `http_evidence/v5_fluview_docs.body` | `cc0b9256332dbc94ce1dc09f61a77ba88a8b28bd34433e303fda15943a1cb14b` |
| `http_evidence/v5_ilinet_signal.body` | `92be4bc591fc7b9273178af01cf8a77cf5460562dd2b62148e66c59a8101f0d7` |
| `http_evidence/v5_migration.body` | `16dddc154145dddb59deecbd1751a3c2b2cd6ba48b66574dce2f2924320d9a01` |
| all `http_evidence/*.err` (empty) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (SHA-256 of empty file, 16 files) |

> **Note (2026-11-06 correction):** `CDC_VINTAGE_REPORT.md` and `T4_VERDICT.md` in this
> directory are edited by this correction, so their on-disk SHA-256 values now differ from
> the two values recorded above. The hashes above are the ORIGINAL values at
> `end_utc 2026-11-06T13:33:59Z`, retained verbatim as the original work record. The
> frozen artifacts in §A are unchanged.

---

## D. Evidence (original fetch work — retained as Delphi-endpoint provenance)

3 live Delphi Epidata `fluview` queries, all HTTP 200, `result:1 / message:"success"`:

| URL | HTTP | rows | release_dates |
|---|---:|---:|---|
| `https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201501&issues=201501-201510` | 200 | 10 | 2015-01-16 → 2015-03-20 |
| `https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201449-201501&issues=201501,201502` | 200 | 12 | 2015-01-16, 2015-01-23 |
| `https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201501&issues=201501` | 200 | 1 | 2015-01-16 |

`v8/cdc_vintage/cdc_vintage.csv` = 20 unique `(epiweek, issue)` rows (6 epiweeks × up to
10 issues), `region=nat`, `cdc_official_revision_id = NOT_AVAILABLE`,
`source_type = delphi_epidata_fluview_v4_issue_proxy`,
`affected_weeks = 201449;201450;201451;201452;201453;201501`. This is a verification
sample only (see ERROR CORRECTION §3).

Reproduced the handoff's verified research: `wili` for epiweek 201501 across issues
201501→201504 = 4.36093931545351 → 4.33436754449044 → 4.2909178182273 →
4.26820164804898 at release dates 2015-01-16 / 2015-01-23 / 2015-01-30 /
2015-02-06. Q1/Q2 duplicates and the Q3 single-issue response were asserted
field-identical before dedup (PASS).

16 unique URLs checked with status codes (200 except the deliberately attempted
non-existent `.../api/fluview_v5.html` = 404). Full ledger and verified quotes are in
`CDC_VINTAGE_REPORT.md` §3 (retained as provenance). Key verified limits: CDC EPI
`Release_Week` covers **2009/10–2014/15**; Delphi scope starts **1997w40**; V3/V4
stopped receiving new data **2026-09-22**; V5 `report_time` = "the date Delphi
ingested the CDC weekly file". No API was unreachable. No error had to be recorded.

---

## E. Remaining (corrected)

1. TASK 4 is **COMPLETED**. Deliverables are the frozen artifacts in §A. No further
   reconstruction is required.
2. Scientific limits to honour in any write-up (see "Remaining scientific limits"):
   Delphi `release_date` is a Delphi-ingest proxy, NOT a CDC-issued official revision
   number; only the REFERENCE peak assignment is re-scored on as-of data (the 1120-cell
   model panel peak metrics remain retrospective); 2002 weeks have no real-time vintage;
   archived final CSVs are not a vintage. No official CDC release calendar / revision id
   is claimed.
3. This correction updates the v8 CDC/T4 records (`T4_VERDICT.md`,
   `CDC_VINTAGE_REPORT.md`, `T4_CORRECTION.md`, `v8/TASK_LOG.md` T4 section,
   `v8/SCIENTIFIC_AUDIT.md`, `v8/BLOCKED_AND_UNVERIFIED.md`,
   `v8/DOCUMENT_UPDATE_MAP.csv`, `v8/docs/V8_SCIENTIFIC_ADDENDUM.md`,
   `v8/docs/V8_CHANGELOG.md`, `v8/MESSAGE_TO_CHATGPT.md`). Other copies in
   `HANDOFF_20261105/final/*`, `v7/*`, `01_最终报告/*`, `v8/RETURN_V8/*`,
   `v8/T7_VERDICT.md`, `v8/T8_VERDICT.md` and the packaged ZIPs are explicitly OUT OF
   SCOPE for this correction and may still carry the old wording; the owner must
   reconcile those separately.
4. `02_数字表格/*` is FROZEN — not modified. The 20-row `v8/cdc_vintage/cdc_vintage.csv`
   is a verification sample, NOT a replacement for the frozen 7192-row table.

**Honest bottom line (corrected 2026-11-06):** TASK 4 is `COMPLETED`. The complete CDC
ILINet vintage reconstruction (7192 release records / 848 epiweek summaries) and the
re-scored season-peak table (18 seasons, 7 peak weeks moved) already existed in
`02_数字表格/`, built from the same Delphi `fluview` endpoint. The earlier
`PARTIAL` / `BLOCKED: no release-calendar/vintage source found` verdict was erroneous
because it inspected only a 20-row sample and never inspected `02_数字表格/`; it is
SUPERSEDED. The retained scientific limits (Delphi proxy, reference-peak-only re-scoring,
retrospective model peak metrics, no 2002 real-time vintage) still apply. The manuscript
is NOT called submission-ready.
