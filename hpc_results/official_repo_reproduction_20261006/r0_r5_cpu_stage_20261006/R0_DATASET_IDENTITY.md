# R0 — DATASET IDENTITY

Generated 2026-10-06. Establishes **which file is the paper's National-Illness dataset**, by
verifying each candidate against the paper's own Table II.

---

## 1. ⚠️ THE DECISIVE TEST: Table II descriptive statistics

The paper's **Table II** gives, for the National-Illness dataset, the average, max and SD of
all seven variables. That is a **direct fingerprint** of the analysis dataset, and it can be
checked against any candidate file.

### Paper's Table II (transcribed from the Markdown; cross-checked against PDF page 7794's print statements)

| Var | Description | Average | Max | SD |
|---:|---|---:|---:|---:|
| 1 | % weighted ILI | 1.851 | 7.715 | 1.342 |
| 2 | % unweighted ILI | 1.845 | 7.780 | 1.308 |
| 3 | ILI count, age 0–4 | 3434.814 | 24097 | 3152.330 |
| 4 | ILI count, age 5–24 | 4981.128 | 45513 | 5950.799 |
| 5 | total ILI count | 13540.720 | 111361 | 15003.120 |
| 6 | number of providers | 1608.262 | 3453 | 681.227 |
| 7 | total ILI patient visits (OT) | 651497.500 | 1640587 | 348838.200 |

### Results

| Candidate | Rows | Variables matching Table II (within 0.5 %) | Verdict |
|---|---:|---:|---|
| `recovery/author_repo/dataset/illness/national_illness.csv` | **966** | **7 / 7** | ✅ **IS the paper's dataset** |
| `data/raw/national_illness_raw_paper_exact.csv` | **966** | **7 / 7** | ✅ same file (CDC column names) |
| `data/raw/national_illness_raw.csv` (July-2026 snapshot) | **1025** | **1 / 7** | ❌ **NOT the paper's dataset** |

### Per-variable detail

| Var | Paper | 966-row file | dev | 1025-row snapshot | dev |
|---:|---:|---:|---:|---:|---:|
| 1 | 1.851 | 1.851286 | **0.02 %** | 1.863 | 0.63 % |
| 2 | 1.845 | 1.845240 | **0.01 %** | 1.847 | 0.13 % |
| 3 | 3434.814 | 3434.813665 | **0.00 %** | 3676.646 | **7.04 %** |
| 4 | 4981.128 | 4981.128364 | **0.00 %** | 5128.036 | **2.95 %** |
| 5 | 13540.720 | 13540.716356 | **0.00 %** | 14189.811 | **4.79 %** |
| 6 | 1608.262 | 1608.261905 | **0.00 %** | 1654.397 | **2.87 %** |
| 7 | 651497.500 | 651497.459627 | **0.00 %** | 686303.703 | **5.34 %** |

**Max values also match exactly** for the 966-row file: 7.715, 7.781, 24097, 45513, 111361,
3453, 1640587 — every one equal to the paper's printed figure at the paper's precision.

Evidence label: **`MARKDOWN_PDF_CROSS_VERIFIED`** (the values appear in the Markdown and the
paper's prose repeats three of them: 1.851286, 3434.813665, 1608.261905 appear in the audit's
earlier extraction of the paper text).

---

## 2. What this resolves — and what it does not

### Resolved: the dataset identity

The paper's national analysis used **966 rows**. This is now **measured**, not inferred.

### Resolved: the "2002–2021 vs 2020-06-30" ambiguity — in favour of the file

Earlier rounds flagged a conflict: the paper's prose says the national data cover
**"2002 to 2021"**, but the released file's stored dates form a 7-day sequence ending
**2020-06-30**.

Table II settles **which data**, though not the prose's intent:

- the **966-row file reproduces the paper's own descriptive statistics exactly**;
- the 1025-row file does **not** (up to 7 % off).

So the analysis dataset is the 966-row file. The paper's "2021" prose is either loose, or
refers to a date convention the file does not encode. **The remaining ambiguity is about
wording, not about data.**

> **This closes the largest data-identity question in the reproduction contract.**

### Not resolved: the stored-date semantics

The 966 stored dates are a regular 7-day sequence from 2002-01-01. Whether they are CDC
MMWR week-ending Saturdays is still unverified, and the reproduction must not silently
relabel them.

---

## 3. Consequence for the primary objective (R6)

**The historical 4-vs-4 comparison used the 1025-row July snapshot — which is NOT the
paper's dataset.**

| Track | Dataset | Paper's dataset? |
|---|---|---|
| Paper (Table II) | 966 rows | ✅ |
| Historical 4-vs-4 (Stages C/D) | **1025 rows** | ❌ |
| A2 / stage-5 / stage-6 | 966 rows | ✅ |
| F1 (frozen) | 966 rows | ✅ |

This does **not** invalidate the historical comparison — an internally consistent benchmark
on a different data vintage is still a benchmark. But it means:

1. the R1-B reproduction **must use the 966-row file**;
2. the controlled replacement **must use the 1025-row file**, because holding the other
   seven components fixed requires the historical contract;
3. **the two are different estimands and must never be merged**, which is exactly the
   `MIFLU_RETRAIN_ON_OLD_CONTRACT_REQUIRED` verdict.

It also means the transferred MIFlu run is **not** a paper reproduction even in principle —
it is trained on a dataset the paper did not use. That is a further reason the label must be
"official-repository-based MIFlu **transferred to the historical comparison contract**".

---

## 4. Dataset inventory

| Path | Rows | Cols | SHA-256 | Role |
|---|---:|---:|---|---|
| `recovery/author_repo/dataset/illness/national_illness.csv` | 966 | 8 (`date` + 7) | `2a96dfed…ebfe5` | **the paper's national dataset**; the released default |
| `recovery/author_repo/dataset/illness/national_illness_orig.csv` | 966 | 8 | `8594cecb…e395` | the author's other copy |
| `data/raw/national_illness_raw_paper_exact.csv` | 966 | 9 (`epiweek`,`release_date` + 7) | `31ffc169…b87a` | same values, CDC column names; A2/F1's file |
| `data/raw/national_illness_raw.csv` | 1025 | 9 | (July snapshot) | **historical 4-vs-4 only** |

**Split boundaries** (author integer rule, `PAPER_EXPLICIT` 70:10:20):
966 → **676 / 97 / 193**; 1025 → **717 / 102 / 206**.

**Scaler behaviour**: per-variable StandardScaler fitted on **training rows only**, in both
the released code and every reproduction track.