"""
download_national_illness.py
============================
Download the National-Illness dataset (7 variables) from CDC FluView
via the CMU Delphi Epidata API.

Data: 2002–2021, weekly, national (US) level.
Reference: MIFlu paper, Section V-A, Table II, Appendix Table X.

API docs: https://cmu-delphi.github.io/delphi-epidata/api/fluview.html
"""

import requests
import pandas as pd
import time
import os
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUTPUT_CSV = os.path.join(DATA_DIR, "national_illness_raw.csv")

# CMU Delphi Epidata API endpoints
CLASSIC_API = "https://delphi.cmu.edu/epidata/api.php"
# Epidata API params
API_PARAMS = {
    "source": "fluview",
    "regions": "nat",
    "epiweeks": "200201-202152",  # 2002 week 1 to 2021 week 52
}

# Fields we need (7 variables from Table II / Appendix Table X)
# API field name → output column name
# Delphi API fluview field mapping (verified via API response inspection):
#   wili          = weighted ILI %
#   ili           = unweighted ILI %
#   num_age_0     = ILI count, age 0-4
#   num_age_1     = ILI count, age 5-24
#   num_ili       = total ILI count
#   num_providers = number of reporting providers
#   num_patients  = total patient visits
FIELD_MAP = {
    "wili":           "% WEIGHTED ILI",
    "ili":            "% UNWEIGHTED ILI",
    "num_age_0":      "AGE 0-4",
    "num_age_1":      "AGE 5-24",
    "num_ili":        "ILITOTAL",
    "num_providers":  "NUM. OF PROVIDERS",
    "num_patients":   "OT",
}

# Metadata columns to keep
META_COLS = ["epiweek", "release_date"]

# Expected number of weeks
EXPECTED_WEEKS = 20 * 52  # ~1040 for 20 years


def fetch_delphi_classic():
    """Fetch data from the classic CMU Delphi API (GET request)."""
    params = {**API_PARAMS}
    print(f"[INFO] Fetching from classic API: {CLASSIC_API}")
    print(f"[INFO] Params: {params}")

    resp = requests.get(CLASSIC_API, params=params, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    if data.get("result") != 1:
        raise RuntimeError(f"API returned error: {data.get('message', 'unknown')}")

    records = data.get("epidata", [])
    print(f"[INFO] Got {len(records)} records from classic API")
    return records


def fetch_delphi_by_year():
    """Fetch data year-by-year (fallback if single request fails or truncates)."""
    all_records = []
    for year in range(2002, 2022):  # 2002 through 2021
        epiweek_range = f"{year}01-{year}52"
        params = {**API_PARAMS, "epiweeks": epiweek_range}
        print(f"[INFO] Fetching year {year}: {epiweek_range}")

        resp = requests.get(CLASSIC_API, params=params, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        if data.get("result") != 1:
            print(f"[WARN] Year {year}: API message: {data.get('message', 'unknown')}")
            # Some weeks may not exist (e.g., week 53 in non-53-week years)
            continue

        records = data.get("epidata", [])
        print(f"[INFO] Year {year}: {len(records)} records")
        all_records.extend(records)
        time.sleep(0.2)  # Be polite to the API

    return all_records


def build_dataframe(records):
    """Convert raw API records into a clean DataFrame."""
    rows = []
    for r in records:
        row = {}
        # Keep metadata
        for mc in META_COLS:
            row[mc] = r.get(mc, None)
        # Map & rename fields
        for api_field, col_name in FIELD_MAP.items():
            val = r.get(api_field, None)
            # Keep None as NaN — we'll check for missing values later
            row[col_name] = val if val is not None else float("nan")
        rows.append(row)

    df = pd.DataFrame(rows)

    # Sort by epiweek
    df = df.sort_values("epiweek").reset_index(drop=True)

    # Remove duplicate epiweeks (keep latest release_date)
    df = df.drop_duplicates(subset="epiweek", keep="last").reset_index(drop=True)

    return df


def validate_dataframe(df):
    """Basic sanity checks on the downloaded data."""
    issues = []

    n_rows = len(df)
    print(f"[CHECK] Total weeks: {n_rows}")
    if n_rows < EXPECTED_WEEKS * 0.9:
        issues.append(f"Fewer weeks than expected: {n_rows} vs ~{EXPECTED_WEEKS}")
    if n_rows > EXPECTED_WEEKS * 1.1:
        issues.append(f"More weeks than expected: {n_rows} vs ~{EXPECTED_WEEKS}")

    # Check epiweek range
    print(f"[CHECK] Epiweek range: {df['epiweek'].min()} – {df['epiweek'].max()}")

    # Check for missing values
    target_cols = list(FIELD_MAP.values())
    missing = df[target_cols].isnull().sum()
    if missing.sum() > 0:
        issues.append(f"Missing values found:\n{missing[missing > 0]}")

    # Check for reasonable value ranges
    for col in target_cols:
        n_zeros = (df[col] == 0).sum()
        n_neg = (df[col] < 0).sum()
        if n_neg > 0:
            issues.append(f"Negative values in {col}: {n_neg}")
        if col in ("% WEIGHTED ILI", "% UNWEIGHTED ILI"):
            if df[col].max() > 50:
                issues.append(f"Unusually high percentage in {col}: max={df[col].max()}")

    if issues:
        print("\n[WARN] Issues detected:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("[CHECK] All basic sanity checks passed.")

    return len(issues) == 0


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # ── Attempt 1: Classic API single request ──
    records = None
    try:
        records = fetch_delphi_classic()
        if len(records) < EXPECTED_WEEKS * 0.8:
            print(f"[WARN] Single request only returned {len(records)} records. "
                  f"Trying year-by-year fallback...")
            records = None
    except Exception as e:
        print(f"[WARN] Classic API single request failed: {e}")
        print("[INFO] Trying year-by-year fallback...")

    # ── Attempt 2: Year-by-year fallback ──
    if records is None:
        try:
            records = fetch_delphi_by_year()
        except Exception as e:
            raise RuntimeError(f"Year-by-year fallback also failed: {e}") from e

    if not records:
        raise RuntimeError("No records retrieved. The API may be unavailable.")

    # ── Build DataFrame ──
    df = build_dataframe(records)
    validate_dataframe(df)

    # ── Save ──
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n[DONE] Saved {len(df)} rows × {len(df.columns)} columns to: {OUTPUT_CSV}")
    print(f"[INFO] Columns: {list(df.columns)}")
    print(f"[INFO] First date: {df['epiweek'].iloc[0]}")
    print(f"[INFO] Last date:  {df['epiweek'].iloc[-1]}")

    return df


if __name__ == "__main__":
    df = main()
