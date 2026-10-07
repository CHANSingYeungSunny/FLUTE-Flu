# Preprocessing lineage (Stage 1 scope)

## What is established now (data-level)

1. **Author → project "paper_exact" reformat** (`data/raw/national_illness_raw_paper_exact.csv`):
   - Values are byte-for-byte the author's `national_illness.csv` (966 rows, 0 cell diffs).
   - Headers renamed 1→`% WEIGHTED ILI`, 2→`% UNWEIGHTED ILI`, 3→`AGE 0-4`, 4→`AGE 5-24`,
     5→`ILITOTAL`, 6→`NUM. OF PROVIDERS`, OT→`OT`.
   - `release_date` column = author's synthetic `date` label (2002-01-01 … 2020-06-30).
   - `epiweek` column = **derived** MMWR week (200240–202113). The derivation is value-verified
     correct (893/966 weighted-ILI weeks match within ±1e-5; a shift by even one week would
     destroy this).
   - No imputation, filtering, deduplication or rescaling is visible in this copy — it is a
     schema alignment, not a value transformation.

2. **Author raw → author processed** (within the pinned repo):
   - The two author CSVs are numerically identical; only headers and date-string formatting
     differ. No transformation beyond column relabelling is implied.

3. **Project July snapshot** (`data/raw/national_illness_raw.csv`):
   - Raw FluView `nat` response, epiweek 200201–202152, 9 columns
     (`epiweek, release_date` + 7 variables). The `release_date` here is the API issue/release
     date (e.g. 200201 → 2013-12-31), **not** an observation date.
   - 19-week hole (2002w21–w39) is intrinsic to the national ILINet series.

## Deferred to Stage 2 (code-level, read-only)

- The author loader's normalization/scaling path (`data_provider/data_loader.py`) — StandardScaler
  fit scope, instance vs per-variable scaling, and the exact window/split construction.
- The project's own preprocessing (`scripts/scaler_utils.py`, `scripts/configs.py`) and how it
  produced the 1,025-row processed matrix from the raw snapshot.
- Whether any row drop / imputation / interpolation occurred beyond the raw hole.
