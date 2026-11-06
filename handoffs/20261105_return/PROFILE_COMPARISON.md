# Data profile comparison (measured 2026-11-04)

| profile | path | sha256 | rows x cols |
|---|---|---|---|
| author_966 | `/gpfs1/scratch/sychan552/stage5_a2_durable/data/raw/national_illness_raw_paper_exact.csv` | `31ffc1693de205ca8de5e966d40c93252e0a0076a212fffc54d1418e1a13b87a` | 966 x 9 |
| author_repo_966 | `/gpfs1/scratch/sychan552/stage5_a2_durable/data/raw/national_illness_author_repo_966.csv` | `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5` | 966 x 8 |

The two files have DIFFERENT byte hashes and different column names:
`author_966` has `epiweek`, `release_date` and 7 named channels; `author_repo_966`
has `date` and 7 numerically-named channels (`1`..`6`, `OT`). Both are 966 rows.

**Aligned 7-channel numeric comparison (measured, not assumed):** mapping
`['% WEIGHTED ILI','% UNWEIGHTED ILI','AGE 0-4','AGE 5-24','ILITOTAL','NUM. OF PROVIDERS','OT']`
to `['1','2','3','4','5','6','OT']` gives per-channel max |diff|
`[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]`, overall **0.0**. The two profiles are
numerically IDENTICAL on all 7 model channels; only metadata columns and column
names differ. This supports treating the panel as same-input.

MIFlu cells use `--profile author_repo_966`; backbone/classical/encoder cells use
`--profile author_966`. The `epiweek`/`date` labels are synthetic and the real
CDC calendar/epiweek mapping is NOT verified, so no per-season inference is made.
