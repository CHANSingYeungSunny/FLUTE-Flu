"""
download_us_region.py
=====================
Download the US-Region dataset (10 HHS regions, ILI absolute counts) from
CDC FluView via the CMU Delphi Epidata API.

Data: Week 40, 1997 – Week 18, 2020, weekly, 10 HHS regions.
Variable: num_ili (absolute ILI patient count) — matches Table III (counts).
Reference: MIFlu paper, Section V-A, Table III.

Usage:  python download_us_region.py
Output: data/us_region_raw.csv
"""

import requests
import pandas as pd
import os
import time

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUTPUT_CSV = os.path.join(DATA_DIR, "us_region_raw.csv")
CLASSIC_API = "https://delphi.cmu.edu/epidata/api.php"

# 10 HHS regions
HHS_REGIONS = [f"hhs{i}" for i in range(1, 11)]
REGION_STR = ",".join(HHS_REGIONS)

# Field: absolute ILI patient counts (not percentage)
VAR_FIELD = "num_ili"


def fetch_with_retry(params, max_retries=5):
    """Fetch with exponential backoff for rate limiting."""
    for attempt in range(max_retries):
        try:
            resp = requests.get(CLASSIC_API, params=params, timeout=120)
            if resp.status_code == 429:
                wait = 2 ** attempt
                print(f"(rate-limited, retrying in {wait}s)", end=" ", flush=True)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"(HTTP {e}, retrying in {wait}s)", end=" ", flush=True)
                time.sleep(wait)
            else:
                raise
    return None


def fetch_all():
    """Fetch data for all 10 HHS regions, batched by year with rate limiting."""
    all_records = []
    years = list(range(1997, 2021))  # 1997 through 2020

    for year in years:
        epiweek_range = f"{year}01-{year}53"
        params = {
            "source": "fluview",
            "regions": REGION_STR,
            "epiweeks": epiweek_range,
        }
        print(f"[INFO] Year {year} ({epiweek_range}) ...", end=" ", flush=True)

        data = fetch_with_retry(params)
        if data is None:
            print("FAILED after retries")
            continue

        if data.get("result") != 1:
            msg = data.get("message", "")
            if "too many" in msg.lower():
                # Split into 2 batches of 5 regions
                print(f"splitting into region groups...")
                for i in range(0, 10, 5):
                    sub_regions = ",".join(HHS_REGIONS[i:i+5])
                    params["regions"] = sub_regions
                    time.sleep(0.5)
                    sub_data = fetch_with_retry(params)
                    if sub_data and sub_data.get("result") == 1:
                        count = len(sub_data.get("epidata", []))
                        all_records.extend(sub_data["epidata"])
                        print(f"    HHS{i+1}-{i+5}: {count} records")
                continue
            else:
                print(f"no data ({msg})")
                continue

        count = len(data.get("epidata", []))
        print(f"{count} records")
        all_records.extend(data["epidata"])
        time.sleep(0.5)  # Polite pacing

    print(f"\n[INFO] Total records: {len(all_records)}")
    return all_records


def build_dataframe(records):
    """Convert raw API records into wide-format DataFrame (weeks × regions)."""
    rows = []
    for r in records:
        rows.append({
            "epiweek": r["epiweek"],
            "region": r["region"],
            "num_ili": r.get("num_ili"),
            "num_patients": r.get("num_patients"),
            "num_providers": r.get("num_providers"),
            "release_date": r.get("release_date"),
        })

    df = pd.DataFrame(rows)

    # Pivot: each region → column
    pivoted = df.pivot_table(
        index="epiweek", columns="region", values=VAR_FIELD, aggfunc="last"
    )
    # CRITICAL: sort numerically (hhs1, hhs2, ..., hhs10) NOT alphabetically
    pivoted = pivoted.reindex(
        columns=sorted(pivoted.columns, key=lambda x: int(x.replace("hhs", ""))),
    )
    pivoted.columns = [f"HHS{i}" for i in range(1, 11)]
    pivoted = pivoted.reset_index()
    pivoted = pivoted.sort_values("epiweek").reset_index(drop=True)

    # Attach metadata
    meta = df.groupby("epiweek").agg(
        release_date=("release_date", "last"),
    ).reset_index()
    pivoted = pivoted.merge(meta, on="epiweek", how="left")

    cols = ["epiweek", "release_date"] + [f"HHS{i}" for i in range(1, 11)]
    pivoted = pivoted[cols]
    return pivoted


def validate(df):
    """Basic data quality checks for absolute ILI counts."""
    issues = []
    n_weeks = len(df)
    print(f"[CHECK] Total weeks: {n_weeks}")
    print(f"[CHECK] Epiweek range: {df['epiweek'].min()} – {df['epiweek'].max()}")

    if n_weeks < 1000:
        issues.append(f"Fewer weeks than expected: {n_weeks} (expected ~1084)")

    hhs_cols = [f"HHS{i}" for i in range(1, 11)]
    missing = df[hhs_cols].isnull().sum()
    if missing.sum() > 0:
        for col in hhs_cols:
            if missing[col] > 0:
                print(f"  {col}: {missing[col]} missing")
        issues.append("Missing values present")

    # Absolute counts should be ≥0 and < 100,000 per region-week
    for col in hhs_cols:
        if (df[col] < 0).any():
            issues.append(f"{col} has negative values")
        if df[col].max() > 100000:
            issues.append(f"{col} max={df[col].max():.0f} unusually high")

    if issues:
        print(f"\n[WARN] {len(issues)} issue(s):")
        for i in issues:
            print(f"  - {i}")
    else:
        print("[CHECK] All quality checks passed.")

    return len(issues) == 0


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    records = fetch_all()

    if not records:
        raise RuntimeError(
            "No records fetched. API may be unavailable.\n"
            "Try again later or use the pre-verified data/US_region_raw.csv."
        )

    df = build_dataframe(records)
    validate(df)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n[DONE] Saved {len(df)} rows x {len(df.columns)} cols → {OUTPUT_CSV}")
    print(f"[INFO] Columns: {list(df.columns)}")

    return df


if __name__ == "__main__":
    df = main()
