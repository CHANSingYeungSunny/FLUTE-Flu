"""
download_us_region.py
=====================
Download the US-Region dataset (10 HHS regions, ILI absolute counts) from
CDC FluView via the CMU Delphi Epidata API.

Data: Week 40, 1997 – Week 18, 2020, weekly, 10 HHS regions.
Variable: num_ili (absolute ILI patient count) — matches Table III (counts).
Reference: MIFlu paper, Section V-A, Table III.

HARDENING (2026-11-01) — check before downloading
-------------------------------------------------
The file this script produces is the **input of Table VI** (`scripts/
train_regional.py`). Before 2026-11-01 the script unconditionally re-fetched
~1 084 weeks x 10 regions from the API on every invocation, which is slow, rate
limited, and — worse — makes the artefact non-reproducible if the upstream API
later revises a value. It now:

* **checks first**: if `data/raw/us_region_raw.csv` already carries all ten HHS
  columns with no missing values, it says so and exits **without** downloading
  anything (that is the normal case in this repo — the file is on disk);
* exposes `--check` for a pure presence report (exit 0 = all ten present,
  exit 2 = something is missing), which is what the queue's preflight uses;
* `--force` re-downloads (the only way to overwrite);
* `--per-region-dir DIR` additionally writes one file per region
  (`us_region_hhs<N>.csv`) for consumers that want a single series;
* `--out` lets a caller write elsewhere, so a test never touches `data/raw/`.

Usage:  python scripts/download_us_region.py            # check, then no-op or fetch
        python scripts/download_us_region.py --check    # presence report only
        python scripts/download_us_region.py --force    # re-fetch
Output: data/raw/us_region_raw.csv (wide: epiweek, release_date, HHS1..HHS10)
"""

import argparse
import os

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUTPUT_CSV = os.path.join(DATA_DIR, "us_region_raw.csv")
CLASSIC_API = "https://delphi.cmu.edu/epidata/api.php"

# 10 HHS regions
HHS_REGIONS = [f"hhs{i}" for i in range(1, 11)]
REGION_STR = ",".join(HHS_REGIONS)
HHS_COLS = [f"HHS{i}" for i in range(1, 11)]

# The Table VI epiweek window (week 40 1997 – week 18 2020), the same filter the
# regional training scripts apply.
EPIWEEK_MIN, EPIWEEK_MAX = 199740, 202018

# Field: absolute ILI patient counts (not percentage)
VAR_FIELD = "num_ili"


def region_presence(path: str = OUTPUT_CSV) -> dict:
    """Report which of the ten HHS region series are present at `path`.

    Returns `{"path", "exists", "n_rows", "present": [...], "missing": [...],
    "empty": [...], "all_present": bool}`. `empty` lists columns that exist but
    carry at least one NaN inside the Table VI epiweek window, which would make a
    regional cell silently drop windows.
    """
    out = {"path": path, "exists": os.path.exists(path), "n_rows": 0,
           "present": [], "missing": list(HHS_COLS), "empty": [],
           "all_present": False}
    if not out["exists"]:
        return out
    df = pd.read_csv(path)
    out["n_rows"] = int(len(df))
    out["missing"] = [c for c in HHS_COLS if c not in df.columns]
    sub = df
    if "epiweek" in df.columns:
        sub = df[(df["epiweek"] >= EPIWEEK_MIN) & (df["epiweek"] <= EPIWEEK_MAX)]
        out["n_weeks_in_window"] = int(len(sub))
    for c in HHS_COLS:
        if c not in df.columns:
            continue
        if sub[c].isna().any():
            out["empty"].append(c)
        else:
            out["present"].append(c)
    out["all_present"] = (not out["missing"] and not out["empty"]
                          and len(out["present"]) == len(HHS_COLS))
    return out


def report_presence(path: str = OUTPUT_CSV) -> bool:
    """Print the per-region presence table; return True iff all ten are usable."""
    p = region_presence(path)
    if not p["exists"]:
        print(f"[CHECK] {path}: absent -> the regional dataset must be downloaded")
        return False
    print(f"[CHECK] {path}: {p['n_rows']} rows, "
          f"{p.get('n_weeks_in_window', 'n/a')} weeks inside "
          f"{EPIWEEK_MIN}-{EPIWEEK_MAX}")
    for c in HHS_COLS:
        state = ("present" if c in p["present"]
                 else ("MISSING COLUMN" if c in p["missing"] else "ALL-NULL"))
        print(f"  {c:<6} {state}")
    print(f"[CHECK] {len(p['present'])}/10 regions usable -> "
          f"{'ALREADY PRESENT, nothing to download' if p['all_present'] else 'INCOMPLETE'}")
    return p["all_present"]


def write_per_region(df: pd.DataFrame, out_dir: str) -> list:
    """Write one `us_region_hhs<N>.csv` per region; returns the written paths."""
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for c in HHS_COLS:
        if c not in df.columns:
            continue
        p = os.path.join(out_dir, f"us_region_{c.lower()}.csv")
        df.loc[:, ["epiweek", c]].to_csv(p, index=False)
        paths.append(p)
    print(f"[INFO] wrote {len(paths)} per-region files -> {out_dir}")
    return paths


def fetch_with_retry(params, max_retries=5):
    """Fetch with exponential backoff for rate limiting."""
    import time
    import requests          # imported lazily: `--check` must work offline

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
    import time
    import requests          # imported lazily: `--check` must work offline

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


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Fetch the 10 HHS regional ILI series (Table VI input). "
                    "Checks first and does NOT re-download when they are present.")
    ap.add_argument("--check", action="store_true",
                    help="Presence report only; nothing is downloaded. Exit 0 iff "
                         "all ten HHS regions are present and non-null.")
    ap.add_argument("--force", action="store_true",
                    help="Re-download even when the file is already complete.")
    ap.add_argument("--out", default=OUTPUT_CSV, help="Output CSV path.")
    ap.add_argument("--per-region-dir", default=None,
                    help="Also write one us_region_hhs<N>.csv per region here.")
    a = ap.parse_args(argv)

    if a.check:
        ok = report_presence(a.out)
        return 0 if ok else 2

    # ── check FIRST: the normal case is that the file is already on disk ────
    if os.path.exists(a.out) and not a.force:
        if report_presence(a.out):
            print("[DONE] the 10 HHS region series are already present — "
                  "nothing was downloaded (pass --force to re-fetch)")
            if a.per_region_dir:
                write_per_region(pd.read_csv(a.out), a.per_region_dir)
            return 0
        print("[WARN] existing file is incomplete -> re-downloading")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    records = fetch_all()

    if not records:
        raise RuntimeError(
            "No records fetched. API may be unavailable.\n"
            "Try again later or use the pre-verified data/US_region_raw.csv."
        )

    df = build_dataframe(records)
    validate(df)

    df.to_csv(a.out, index=False)
    print(f"\n[DONE] Saved {len(df)} rows x {len(df.columns)} cols -> {a.out}")
    print(f"[INFO] Columns: {list(df.columns)}")
    if a.per_region_dir:
        write_per_region(df, a.per_region_dir)

    return df


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() is not None else 1)
