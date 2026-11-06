# T4_VERDICT — CDC calendar / vintage (TASK 4)

```
status: PARTIAL
start_utc: 2026-11-06T13:19:57Z
end_utc:   2026-11-06T13:33:59Z
scope:     HANDOFF_20261105/v8/cdc_vintage/   (write ONLY here; directory created)
task:      TASK 4 of HANDOFF_20261105/NEXT_DEEPSEEK_PROMPT.md
```

**PARTIAL, not COMPLETED — one sub-step is BLOCKED.** A real Delphi-proxy vintage
table WAS built from actually-fetched rows, but peak re-scoring with as-of data could
NOT be completed, and the primary sub-goal (reconstruct the ACTUAL CDC release date /
revision id) is genuinely impossible from the checked sources. Both are stated
explicitly below. No result is fabricated; no frozen CSV, raw prediction, or peak CSV
was modified; no file outside `HANDOFF_20261105/v8/cdc_vintage/` was written.

---

## A. Sub-step status

| # | Sub-step | Status |
|---:|---|---|
| 1 | Fetch a small set of real vintage rows from Delphi Epidata (HTTP status, raw snippet, exact command) | **COMPLETED** (3 live API queries, all HTTP 200; 20 unique rows) |
| 2 | Build `cdc_vintage.csv` with required columns, `cdc_official_revision_id = NOT_AVAILABLE`, affected weeks | **COMPLETED** |
| 3 | Re-score peak assignment with as-of data | **BLOCKED** — exact missing input below |
| 4 | Write `CDC_VINTAGE_REPORT.md` | **COMPLETED** |
| 5 | Write `T4_VERDICT.md` | **COMPLETED** (this file) |
| P | Reconstruct the **ACTUAL** CDC release date / CDC-issued revision id | **BLOCKED: no release-calendar/vintage source found** |

### Retained primary BLOCKED label

> `BLOCKED: no release-calendar/vintage source found`

Exact limitation: CDC publishes **no release calendar** and **no revision/version
identifier** for ILINet. Verified on
`https://www.cdc.gov/fluview/surveillance/past-reports.html` (200; no
`release calendar` / `revision` / `revised` string in body, only "week ending" +
final/archived values),
`https://www.cdc.gov/fluview/index.html` (200; "All data are preliminary"),
`https://stacks.cdc.gov/view/cdc/120452` (200; "The data presented each week are
preliminary and may change as more data are received.").
Archived final CSVs are single-snapshot values, **not a vintage**.
CDC EPI `Release_Week` (2009/10–2014/15) is a publication-epiweek proxy, not a calendar
release date or CDC revision number. Delphi `issue`/`release_date`/V5 `report_time`
are Delphi-side proxies ("the date Delphi ingested the CDC weekly file"), not CDC-issued
revision ids. Hence `cdc_official_revision_id = NOT_AVAILABLE` on every row.

### BLOCKED sub-step 3 — peak re-scoring

**Exact missing input:** an authoritative
`step (test-window index) → absolute row index → CDC MMWR epiweek (YYYYWW)` mapping
linking the frozen peak ground truth to the Delphi `issue`/`release_date` vintage,
together with an official CDC-issued release date / revision id (which does not exist).

Evidence (all read-only checks):
- `06_原始数据集/scaler_miflu_national.json` and `scaler_miflu_author966.json` contain
  only `mean, std, train_end (717/676), val_end (819/773), var_cols`. The split
  boundaries are row indices, not weeks. No row→week mapping.
- `99_旧文件存档/recovery/dataset_manifest.json` has only `first`/`last`/`n` summary
  ranges (`author_dates` 2002-01-01→2020-06-30, `paper_exact_epiweeks` 200240..202113,
  `project_epiweeks` 200201..202152), no per-row array.
- Frozen peak tables are step-indexed with no epiweek/date column:
  `02_数字表格/BENCH_PTE_PIE_BY_STEP.csv` (`model,family,L,step,weeks_ahead,...`),
  `HANDOFF_20261105/final/PEAK_BY_STEP.csv` (`model,L,seed,step,pte,pie,passed,n`),
  `HANDOFF_20261105/final/PEAK_EVENTS.csv` (`gt_week` is a numeric row index, e.g.
  `801`/`798`, not `YYYYWW`). Scoring scripts `score_common.py` / `peak_events.py` are
  **not present** in the Windows tree; only `05_程序代码/innovation/metrics.py` exists.
- `06_原始数据集/raw/national_illness_author_repo_966.csv` (the paper's main 966-week
  file) has no `epiweek`, only a synthetic 7-day `date` column. The reprocessed files'
  `epiweek` labels are NOT CDC MMWR weeks (2002-01-01 ↔ `200240`; label year rolls over
  in April), so joining them to Delphi MMWR epiweeks would require inventing an
  alignment — forbidden.
- The `release_date` columns in `national_illness_raw.csv` (8 distinct annual bulk
  snapshot dates) and `national_illness_raw_paper_exact.csv` (target-week calendar
  dates) are not CDC publication dates.

**Smallest next action:** recover the scoring provenance (`score_common.py` /
`peak_events.py` and their `test_window → absolute row → date` alignment from the HPC
return package / `RAW_EVIDENCE.zip`), confirm the epiweek convention, then join that
alignment to a full Delphi `issues` pull. No peak CSV was rewritten; no mapping was
invented.

---

## B. Commands + exit codes

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

## C. Output paths + SHA-256

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

---

## D. Evidence (what was actually fetched)

3 live Delphi Epidata `fluview` queries, all HTTP 200, `result:1 / message:"success"`:

| URL | HTTP | rows | release_dates |
|---|---:|---:|---|
| `https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201501&issues=201501-201510` | 200 | 10 | 2015-01-16 → 2015-03-20 |
| `https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201449-201501&issues=201501,201502` | 200 | 12 | 2015-01-16, 2015-01-23 |
| `https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201501&issues=201501` | 200 | 1 | 2015-01-16 |

`cdc_vintage.csv` = 20 unique `(epiweek, issue)` rows (6 epiweeks × up to 10 issues),
`region=nat`, `cdc_official_revision_id = NOT_AVAILABLE`,
`source_type = delphi_epidata_fluview_v4_issue_proxy`,
`affected_weeks = 201449;201450;201451;201452;201453;201501`.

Reproduced the handoff's verified research: `wili` for epiweek 201501 across issues
201501→201504 = 4.36093931545351 → 4.33436754449044 → 4.2909178182273 →
4.26820164804898 at release dates 2015-01-16 / 2015-01-23 / 2015-01-30 /
2015-02-06. Q1/Q2 duplicates and the Q3 single-issue response were asserted
field-identical before dedup (PASS).

16 unique URLs checked with status codes (200 except the deliberately attempted
non-existent `.../api/fluview_v5.html` = 404). Full ledger and verified quotes are in
`CDC_VINTAGE_REPORT.md` §3. Key verified limits: CDC EPI `Release_Week` covers
**2009/10–2014/15**; Delphi scope starts **1997w40**; V3/V4 stopped receiving new
data **2026-09-22** ("As of September 22, 2026, the V3 and V4 APIs no longer receive
new data"); V5 `report_time` = "the date Delphi ingested the CDC weekly file".

No API was unreachable. No error had to be recorded. The raw bodies, stderr and
status/time/size TSVs are preserved under `http_evidence/`.

---

## E. Remaining

1. `BLOCKED: no release-calendar/vintage source found` — no CDC-issued release
   calendar or revision id exists in the checked sources;
   `cdc_official_revision_id` stays `NOT_AVAILABLE`.
2. `BLOCKED` peak re-scoring — missing `step → CDC MMWR epiweek` mapping and official
   CDC release dates; smallest next action in §A. No peak CSV rewritten.
3. Optional (new task, not done): full Delphi `issues` pull for 1997w40→2026 (V3/V4
   frozen 2026-09-22, or V5 `report_time` archive), still labelled **proxy** only.
4. `HANDOFF_20261105/v8/TASK_LOG.md` and the v7 blocked/audit docs were NOT appended —
   outside my write scope. TASK 7 (v8 documents) may cite this report.
5. Prior out-of-scope artifacts `05_程序代码/cdc_vintage_build.py` and
   `02_数字表格/cdc_peak_revintage.csv` (+ `cdc_vintage*.csv` / `_report.md`) exist but
   were not run, modified, or adopted as my results; `02_数字表格/` is frozen under
   AGENTS.md RULE 4. That script's own text states it does not re-score the 1120-cell
   model panel, and it conflates Delphi `release_date` with "the CDC release calendar".

**Honest bottom line:** a proxy vintage table was built and documented, but the
ACTUAL CDC release date / revision id is not reconstructable and peaks were NOT
re-scored. Therefore `PARTIAL` with one explicitly BLOCKED sub-step, never
`COMPLETED`.
