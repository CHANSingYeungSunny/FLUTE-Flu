# Data identity audit — Stage 1 (independent verification)

Date: 2026-09-24. Auditor: independent research engineer (CodeBuddy). Method: CPU-only, read-only.

## Classification (headline)

The project's July-2026 snapshot and the paper's author data are **the same seven-variable
national ILINet series at two different vintages and two different window lengths**:

| Property | Author data (paper) | Project snapshot (July 2026) |
| --- | --- | --- |
| Rows | 966 | 1,025 |
| MMWR epiweek range | 200240 – 202113 | 200201 – 202152 (with a 19-week hole) |
| Calendar coverage | 2002-09-29 → 2021-03-28 | 2001-12-30 → 2021-12-26 (minus 2002w21–w39) |
| Value vintage | ~2023 (paper submission) | 2026-07-18 (retrieved 2026-07-15) |

Relationship: **revised values + range extension** — *not* a clean range-only extension.
Values are identical (to rounding) for the pre-2016 period, then diverge by historical
revision from MMWR 2016w40 onward.

---

## 1. Author CSV identity — VERIFIED

- Both author files have **966 rows** and **7 numeric columns**.
- `national_illness.csv` header: `date,1,2,3,4,5,6,OT`.
- `national_illness_orig.csv` header: `date,% WEIGHTED ILI,%UNWEIGHTED ILI,AGE 0-4,AGE 5-24,ILITOTAL,NUM. OF PROVIDERS,OT` (note the author's own inconsistent `%UNWEIGHTED` without a space).
- **Parsed numeric identity: 0 cell differences across 966×7 cells** — confirms the earlier
  review's "identical parsed values" finding independently.
- Byte hashes differ (headers + date-string formatting only):
  - processed `sha256 2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5`
  - orig `sha256 8594cecb98c6f2f9dc014eca11c4d5d1e38ad5ce6ed0592d4abe65b146fce395`

## 2. Author date labels are SYNTHETIC — VERIFIED (important)

- Stored `date` runs **2002-01-01 → 2020-06-30** at an exact **7-day cadence** (all 965 deltas == 7 days).
- These are generated index labels, **not** CDC observation weeks. The first label
  `2002-01-01` is a Tuesday; MMWR week 1 of 2002 begins `2001-12-30` (Sunday).
- The project's reformatted copy `data/raw/national_illness_raw_paper_exact.csv` carries a
  derived `epiweek` column (200240–202113). Value-alignment proves this mapping correct:
  **893 of 966 weighted-ILI weeks match within ±1e-5, median absolute difference 0.0**.
- **Actual observation span:** MMWR 2002w40 = **2002-09-29** → MMWR 2021w13 = **2021-03-28**.
  The paper's "2002–2021" description overstates the tail by ~9 months; its "2002-01-01" start
  understates the true start by ~9 months.

## 3. Project snapshot coverage — VERIFIED

- 1,025 rows, epiweeks 200201–202152, strictly increasing, **0 duplicates**.
- **A genuine 19-week hole: MMWR 2002w21–2002w39 are absent.** This is a property of the
  national ILINet data in FluView, not a truncation choice (confirmed by the project's own
  `scripts/cdc_calendar.py`, which documents this hole and three week-53 label collisions).
- Relative to the author data, the project snapshot adds **20 weeks at the head**
  (200201–200220) and **39 weeks at the tail** (202114–202152) = 59 extra weeks; 966 + 59 = 1025.

## 4. Overlap comparison (author vs July-2026 snapshot) — REVISIONS localized

Joined on epiweek (966 overlapping weeks), per-variable (author value vs project value):

| Variable | exact | ≤1e-5 | nontrivial (>1e-4) | max |diff| | first revised epiweek |
| --- | ---: | ---: | ---: | ---: | --- |
| % WEIGHTED ILI | 342 | 893 | 72 | 0.01122 | 201640 |
| % UNWEIGHTED ILI | 347 | 892 | 71 | 0.00323 | 201640 |
| AGE 0-4 | 928 | 928 | 38 | 161 | 201640 |
| AGE 5-24 | 920 | 920 | 46 | 246 | 201640 |
| ILITOTAL | 913 | 913 | 53 | 687 | 201640 |
| NUM. OF PROVIDERS | 887 | 887 | 79 | 274 | 201640 |
| OT | 889 | 889 | 77 | 92,675 | 201640 |

**Revision clusters (weighted ILI, 72 revised weeks):**
- **2016w40–2017w32 (45 weeks)** — the 2016-17 season revision; largest single revision
  201705: author 4.50313 → project 4.43601 (|Δ| 0.067).
- **2020–2021w13 (27 weeks)** — pandemic-period revision.

Integer counts (AGE/ILITOTAL/providers/OT) are exact-equal for ~90% of weeks and diverge only
in the same two revision windows. This is the signature of **CDC FluView historical
backfill/revision**, not a field or calendar mismatch (a calendar mismatch would shift the
whole series, not a localized tail).

## 5. Variable mapping & denominator identity — VERIFIED

| author col | orig header | FluView field | unit |
| --- | --- | --- | --- |
| 1 | % WEIGHTED ILI | `wili` | % visits, population-weighted |
| 2 | %UNWEIGHTED ILI | `ili` | % visits, unweighted |
| 3 | AGE 0-4 | `num_age_0` | ILI count, ages 0-4 |
| 4 | AGE 5-24 | `num_age_1` | ILI count, ages 5-24 |
| 5 | ILITOTAL | `num_ili` | total ILI count |
| 6 | NUM. OF PROVIDERS | `num_providers` | reporting providers |
| OT | OT | `num_patients` | total patient visits (denominator) |

`100 × ILITOTAL / OT` reproduces `%UNWEIGHTED ILI` with **max residual 5.0e-6** over all 966
rows (median 1.6e-6). Confirms `OT = total patients` (the ILI-percentage denominator) and
`OT ≠ ILITOTAL`. ILI is a surveillance syndrome, not laboratory-confirmed influenza.

## 6. Provenance timestamps (filesystem)

- `data/raw/national_illness_raw.csv`: birth 2026-07-15 23:27 (retrieval), modified
  2026-07-18 19:24 (local update) — matches the planning PDF's stated 15/18 July 2026.
- `data/raw/national_illness_raw_paper_exact.csv`: created 2026-08-28 19:20 (author data
  reformatted into project schema; the epiweek column was derived, release_date = author's
  synthetic `date` label).

## 7. Verdict per variable/period

- **Semantically identical, precision-equivalent** for 200240–201639 (all seven variables).
- **Revised values** for 201640–202113 (all seven variables, two clusters).
- **Range-only extension** at head (200201–200220) and tail (202114–202152) in the project
  snapshot only.
- **Unresolved (non-blocking):** exact MMWR week-53 canonicalisation for the three colliding
  label pairs — documented, not yet needed for the reproduction decision.
