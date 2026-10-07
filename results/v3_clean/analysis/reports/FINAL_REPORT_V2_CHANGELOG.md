# FINAL REPORT v2 — CHANGELOG

Generated 2026-10-07. Supersedes nothing by deletion; supersedes by authority.

Three documents are in scope:

| id | document | track | size | SHA-256 |
|---|---|---|---|---|
| **A** | `MIFlu_..._中文版.docx` (historical) | Track H | 1,372,896 B | `9c573f48…50ead` |
| **B** | `MIFlu_..._官方仓库966行严格测试冠军版.docx` (first championship) | Track R + C | 44,675 B | `f41652ff…f57ef` |
| **C** | `MIFlu_..._官方仓库966行严格测试冠军版_v2.docx` (this report) | Track R + C | 670,113 B | `d9f14d3a…cbd68` |

---

## 1. From **A** (historical report, Track H) to **C**

A is **not false**. It is reclassified as `SUPERSEDED_HISTORICAL_REPORT`
because its conclusions apply to a different dataset, a different MIFlu
implementation, a different split/window contract and a different Test scope.

| dimension | A (Track H) | C (Track R + C) |
|---|---|---|
| dataset | 1025-row July-2026 snapshot | **966-row author file** (`2a96dfed…ebfe5`) |
| Table II check | 1 / 7 variables matched | **7 / 7 matched, max deviation ≈ 0.02 %** |
| MIFlu implementation | project **self-built** | **official repository + R1-B corrections** |
| split / window contract | historical; later found to contain **boundary contamination** | **strict containment**, 676 / 97 / 193 |
| where models were compared | 8 models on **Validation** only | 8 models on a **one-time Test** |
| final Test scope | **3** frozen models | **8** models, 96 cells |
| ranking basis | Validation | **Test only** |
| champion claim | none (no Test-wide ranking) | MIFlu, 1.8652 |

**What changed in substance**

1. The whole 1025-row result set is no longer presented as the project's
   conclusion. It is retained as a historical record of the pre-official-
   repository phase, the self-built MIFlu, the Wave-1 Validation ranking, the
   three-model Test/Holdout experiment and the earlier NLinear conclusion.
2. All 1025-row numbers are removed from any comparative framing against the
   author data or the paper.
3. The document that carried those numbers is archived to
   `reports/archive/MIFlu_..._旧版_历史1025行实验.docx`, byte-identical
   (`9c573f48…50ead`), and its original is preserved in place.
4. A new authority note, `REPORT_AUTHORITY_AND_ARCHIVAL_NOTE.md`, states which
   report is current, which is historical, why, and the SHA-256 of both.

---

## 2. From **B** (first championship report) to **C**

B was an **eight-page abbreviated summary**. C is the **complete report**. B's
verified content is preserved; nothing verified in B was changed.

### 2.1 Preserved unchanged from B

- The champion identity and value: official-repository-based corrected MIFlu,
  mean Test `average_MSE_4L` = **1.8652**, SD **0.0916**, mean Test
  `average_MAE_4L` = **0.8842**.
- The eight-model ranking, the per-horizon and per-seed first places, the
  group means (non-LLM 3.0756 vs LLM-side 3.8175) and the pairwise MIFlu vs
  NLinear result (mean diff −0.1844, 11 wins / 1 loss / 0 ties).
- The pinned identities: author data SHA-256, strict Test key-set SHA-256,
  676/97/193 split, seeds 42/43/44, one-time Test.
- The cost figures: 12 MIFlu GPU jobs, 1.5083 GPU-h, all rc 0, home 31/50 GB,
  scratch 285/300 GB.

### 2.2 Added in C

| # | addition |
|---:|---|
| 1 | Cover page with generated date, repository commit, data SHA-256, Test-key SHA-256, result directory, report version and archival statement |
| 2 | Table of contents (real Word field, populated in the shipped file) |
| 3 | Project chronology and explicit Track H / R / C / F1 separation (**图 3-1, 图 3-2**) |
| 4 | Official-repository reproduction section: Table V targets vs R1-B, the gap arithmetic, the ±0.10 band result (0 / 4) and a **table of gap sources graded by evidence level** |
| 5 | Released-code defect section (eight conflicts, four permanently unresolvable) |
| 6 | R1-B correction summary |
| 7 | **Paper-gap comparability audit** — new; establishes that the old-vs-new improvement percentage is *not* claimable as stated |
| 8 | Why 966 rows (Table II 7/7 test) |
| 9 | Strict containment and the leakage correction, with the three-set usage table |
| 10 | Model identities, including the explicit statement that Qwen / CALF / TimeCMA are inspired simplifications, not full reproductions |
| 11 | Championship method (96 cells, 84 re-scored, 12 retrained, seed-42 gate 22/22, no missing/duplicate keys) |
| 12 | Full eight-model ranking **with SD and MAE**, per-horizon and per-seed tables, pairwise table |
| 13 | Computation and storage section, including why filesystem free space is not a user quota and that `mmlsquota` is authoritative |
| 14 | Engineering corrections and incidents (11 entries) with the mandated honest login-node wording |
| 15 | Limitations section, including the corrected Table III status (`VERIFIED_AVAILABLE` via markdown transcription, not "unreadable") |
| 16 | Appendices: evidence paths and hashes; per-figure source-data map |
| 17 | Eight new figures (**图 4-1, 9-1, 10-1, 10-2, 10-3, 10-4, 11-1, 12-1, 13-1**) in addition to the two chronology diagrams |

### 2.3 Corrected in C

| # | item | was | now |
|---:|---|---|---|
| 1 | old-vs-new improvement percentage | B-era material treated the two runs as fully comparable | **`NOT_SUFFICIENTLY_COMPARABLE`**; three blocking violations (3 seeds vs 1 repetition; old checkpoint policy unrecorded; R1-B SD = `n/a`). The mandated sentence is used: *"A numerical reduction percentage cannot be presented without qualification because the old and new runs used different contracts."* |
| 2 | Table III status | `UNREADABLE` | `VERIFIED_AVAILABLE` via `MARKDOWN_TRANSCRIPTION`; not directly machine-extracted from the PDF image. Table VI remains `BLOCKED_BY_MISSING_DATA` |
| 3 | login-node wording | — | *"One initial heavy scorer was mistakenly run on the login node. After the incident, all scoring and substantial computation were moved to Slurm compute nodes, and the violation did not recur."* |
| 4 | SSH incident scope | — | No `fail2ban` record exists anywhere in the repository; the recorded incident is an SSH connection reset, followed by migration of scoring to Slurm. Stated as found, not embellished |
| 5 | gap-source causality | — | No single source is asserted as causal; sources are graded by evidence level |

### 2.4 Render and layout work performed for C

Four render rounds; nine defects found and fixed (TOC field population, cover
spill, title wrap, figure/header overlap, table width overrun, orphan table
row, long-hash cell widening, Letter→A4 page size, table frame fitting).
Final audit: **19 pages, 0 flagged, 0 blank pages**. See
`FINAL_REPORT_V2_RENDER_AUDIT.md`.

---

## 3. What did **not** change

- **Track C is frozen.** The champion, the ranking, the seeds, the Test keys,
  the predictions, the scorer and the model set are untouched.
- **Track R's verdict** remains `PARTIAL_REPRODUCTION`.
- **A is preserved.** Not deleted, not modified, archived byte-identically.
- **B is preserved.** Not deleted, not modified.

---

## 4. File authority after this changelog

| document | status | notes |
|---|---|---|
| **C** — `…_官方仓库966行严格测试冠军版_v2.docx` | **CURRENT** | takes authority once this changelog and the render audit are in place |
| **B** — `…_官方仓库966行严格测试冠军版.docx` | **CURRENT_UNTIL_V2_ACCEPTED**, then `SUPERSEDED_BY_V2` | preserved unmodified; retained as the first accepted championship report |
| **A** — `…_中文版.docx` + PDF | **SUPERSEDED_HISTORICAL_REPORT** | archived to `reports/archive/` byte-identically; original kept in place |

Neither B nor A may be deleted. A must never be presented as the current final
conclusion; B must not be presented once C is accepted.

---

## 5. Companion documents

| file | purpose |
|---|---|
| `REPORT_AUTHORITY_AND_ARCHIVAL_NOTE.md` | which report is current / historical, why, and both hashes |
| `FINAL_REPORT_V2_RENDER_AUDIT.md` | per-page render measurements and the defect log |
| `FINAL_REPORT_V2_SOURCE_MANIFEST.csv` | every table and figure mapped to its source artifact |
| `FINAL_REPORT_V2_SHA256.txt` | hashes of all reports, current and historical |
| `PAPER_GAP_COMPARABILITY_AUDIT.csv` | 11-criterion contract comparison |
| `PAPER_GAP_REDUCTION_CALCULATION.md` | gap arithmetic and the comparability verdict |
| `R1C_FINAL_VERDICT.md` | bounded reproduction-gap verdict |
| `scripts/build_final_report_v2.py` | the generator (tables and figures regenerated from frozen CSVs) |
| `scripts/finalize_docx_v2.py` | TOC/field update, save, PDF export, page rendering |
| `scripts/audit_render_v2.py` | the render audit |
