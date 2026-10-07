# R1B DATA CONTRACT

| Field | Value | Evidence |
|---|---|---|
| dataset | `dataset/illness/national_illness.csv` from the author release | OFFICIAL_CODE_EXPLICIT |
| SHA-256 | `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5` | verified at every job start; the trainer **exits 4** on mismatch |
| rows | **966** | |
| numeric columns | **7**, named `1..6` plus `OT` in the release; CDC names in the paper_exact copy | |
| **identity proof** | the 966-row file reproduces the paper's **Table II** 7/7 (max deviation 0.02 %), while the 1025-row July snapshot matches only 1/7 (up to 7.04 % off) | **`MARKDOWN_PDF_CROSS_VERIFIED`** |
| date labels | a stored 7-day sequence from 2002-01-01; **end 2020-06-30** | semantics NOT verified; must not be relabelled |
| split | **676 / 97 / 193** (70:10:20, the author integer rule) | PAPER_EXPLICIT |
| scaler | per-variable StandardScaler fitted on **training rows only** | CODE_EXPLICIT |
| missing values | none observed | |
| duplicates | none observed | |
| windows | T=104; strict target containment — the block `[o+1, o+L]` must lie inside its split | |
| origins (strict) | L=24 → 170 · L=36 → 158 · L=48 → 146 · L=60 → 134 | matches the recorded contract exactly |

**Declared deviation B-1**: the released loader slices `feat_id:feat_id+1` (one channel)
and its `__len__` omits `x enc_in` for Test, so Test covers channel 0 only. R1-B evaluates
**all seven channels** on **one common origin set**.
