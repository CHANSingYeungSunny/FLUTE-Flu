#!/usr/bin/env python
"""
cdc_calendar.py — authoritative abs_week -> calendar-date mapping for CDC ILINet
================================================================================

WHY THIS MODULE EXISTS (Advisor Question 2a)
-------------------------------------------
`scripts/make_miflu_evaluation_figure.py::_week_to_epiweek()` Built the X axis by
assuming the raw CSV is a perfectly regular weekly grid:

    d = datetime.fromisocalendar(2002, 1, 1) + pd.Timedelta(weeks=abs_week)

That assumption is FALSE. `data/raw/national_illness_raw.csv` (1025 rows,
epiweek 200201..202152) contains **7 calendar irregularities**:

  * 2002 weeks 21-39 are ABSENT  -> one 20-week jump (200220 -> 200240)
  * three Y53/(Y+1)01 label pairs collide on the same calendar week
  * three Y52/(Y+1)01 pairs are 2 weeks apart (the Y53 label got attached to
    the PREVIOUS year)

Consequence: by row 820 the synthetic axis is ~19 weeks (4.4 months) EARLIER
than reality (2017-09-17 synthetic vs 2018-01-28 real). Every published figure
built on the old helper carries that drift.

WHAT THIS MODULE DOES
---------------------
1. Reads the raw CSV's `epiweek` column (YYYYWW, the only absolute time anchor
   the file has).
2. Canonicalises the 53-week label offset so that every row maps to a unique
   Sunday-start MMWR week.
3. Emits a strictly increasing date series that PRESERVES the real 19-week hole
   in 2002 (the hole is a property of the data and must remain visible).
4. Reports every irregularity via `list_anomalies()` so a figure caption can
   disclose it.

MMWR convention used (Sunday-start; identical calendar weeks to ISO, different
weekday anchor):
    MMWR week 1 of year Y = the Sunday-start week containing January 4 of Y.

Verified anchors:
    mmwr_week1_start(2020) == 2019-12-29
    mmwr_week1_start(2021) == 2021-01-03
    mmwr_year_has_53_weeks(2020) is True   (2020 is a genuine 53-week year)
    mmwr_year_has_53_weeks(2003) is False  (2003 has 52 weeks)

Pure stdlib + pandas. No network, no model.
"""

from __future__ import annotations

import datetime as _dt
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
DEFAULT_RAW = os.path.join(PROJECT_ROOT, "data", "raw", "national_illness_raw.csv")


# --------------------------------------------------------------------------- #
# MMWR primitives
# --------------------------------------------------------------------------- #
def mmwr_week1_start(year: int) -> _dt.date:
    """Start date (Sunday) of MMWR week 1 of `year`.

    MMWR week 1 is the Sunday-start week containing January 4 of that year.
    """
    jan4 = _dt.date(year, 1, 4)
    # date.weekday(): Monday=0 ... Sunday=6. Sunday on/before Jan 4:
    return jan4 - _dt.timedelta(days=jan4.weekday() + 1)


def mmwr_year_has_53_weeks(year: int) -> bool:
    """True iff MMWR year `year` contains 53 weeks.

    A year has 53 MMWR weeks exactly when week 1 of the NEXT year starts
    53*7 days after week 1 of this year.
    """
    return (
        mmwr_week1_start(year) + _dt.timedelta(weeks=53)
        == mmwr_week1_start(year + 1)
    )


def mmwr_week_start(year: int, week: int) -> _dt.date:
    """Start date (Sunday) of MMWR week `week` of `year` (week is 1-based)."""
    return mmwr_week1_start(year) + _dt.timedelta(weeks=week - 1)


# --------------------------------------------------------------------------- #
# Canonicalisation
# --------------------------------------------------------------------------- #
def canonicalize_epiweeks(epiweeks):
    """Fix the 'week 53 attached to the wrong year' labelling quirk.

    CMU Delphi's fluview rows label the 53rd week of a 52-week MMWR year as
    `Y53` instead of `(Y+1)01`. When that happens, every label of year Y+1 is
    also shifted down by one (Y+1 has 52 rows instead of 53). Both label sets
    describe the SAME calendar weeks, so we renormalise:

        (Y, 53)      -> (Y+1, 01)
        (Y+1, w)     -> (Y+1, w+1)      for every w in year Y+1

    `2020` is a genuine 53-week MMWR year, so its labels need no shift.

    Args:
        epiweeks: iterable of int YYYYWW, ascending.
    Returns:
        (canonical: list[(year, week)], anomalies: list[dict])
    """
    ew = [int(e) for e in epiweeks]
    canon = [(e // 100, e % 100) for e in ew]

    years = []
    for y, _ in canon:
        if not years or years[-1] != y:
            years.append(y)

    anomalies: list[dict] = []

    # Walk years in DESCENDING order so a shift applied to year Y+1 never
    # invalidates a not-yet-processed earlier year.
    for y in reversed(years):
        if not mmwr_year_has_53_weeks(y):
            has_53_label = any((yy == y and ww == 53) for yy, ww in canon)
            if not has_53_label:
                continue
            # This year only has 52 MMWR weeks, yet a (y,53) row exists.
            n_shifted = 0
            for i, (yy, ww) in enumerate(canon):
                if yy == y and ww == 53:
                    canon[i] = (y + 1, 1)
                    n_shifted += 1
                elif yy == y + 1:
                    canon[i] = (yy, ww + 1)
                    n_shifted += 1
            anomalies.append({
                "kind": "week53_label_offset",
                "year_labelled_53": y,
                "true_mmwr_53_week_year": y + 1,
                "rows_relabelled": n_shifted,
                "detail": (f"rows labelled {y}53 / {y+1}w were re-mapped to "
                           f"{y+1}01 / {y+1}w+1; calendar dates unchanged"),
            })
    return canon, anomalies


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def load_week_calendar(raw_csv: str = DEFAULT_RAW) -> pd.DataFrame:
    """Build the authoritative abs_week -> calendar mapping.

    Returns a DataFrame indexed by `abs_week` (0-based row index, identical to
    the `abs_week` column written by `train_miflu.export_prediction_csv`) with:

        abs_week         int   0-based row index into the raw CSV
        epiweek          int   canonical YYYYWW (unique, strictly increasing)
        epiweek_raw      int   YYYYWW as it appears in the raw file
        year             int
        week             int
        week_start_date  datetime64[ns]  Sunday on which the epiweek begins
    """
    raw = pd.read_csv(raw_csv)
    if "epiweek" not in raw.columns:
        # The author's released national_illness.csv names the time column `date`
        # (a datetime) rather than an integer `epiweek`. The profile
        # `author_repo_966` reads that file byte-for-byte, so synthesise the
        # epiweek code from the date instead of failing the export.
        if "date" not in raw.columns:
            raise KeyError(
                f"{raw_csv} has neither 'epiweek' nor 'date'; cannot build a calendar")
        _d = pd.to_datetime(raw["date"])
        raw = raw.assign(
            epiweek=(_d.dt.isocalendar().year.astype(int) * 100
                     + _d.dt.isocalendar().week.astype(int)))
    raw_epi = raw["epiweek"].astype(int).tolist()

    canon, anomalies = canonicalize_epiweeks(raw_epi)
    dates = [mmwr_week_start(y, w) for y, w in canon]
    epi = [y * 100 + w for y, w in canon]

    cal = pd.DataFrame({
        "abs_week": range(len(canon)),
        "epiweek": epi,
        "epiweek_raw": raw_epi,
        "year": [y for y, _ in canon],
        "week": [w for _, w in canon],
        "week_start_date": pd.to_datetime(pd.Series(dates)),
    })

    # Hard invariants.
    assert cal["epiweek"].is_unique, "canonical epiweeks must be unique"
    assert cal["week_start_date"].is_monotonic_increasing, "dates must ascend"
    assert cal["week_start_date"].diff().dropna().min() >= pd.Timedelta(weeks=1), \
        "no two rows may share a calendar week"

    cal.attrs["anomalies"] = anomalies + list_anomalies(cal)
    return cal


def list_anomalies(cal: pd.DataFrame) -> list[dict]:
    """Calendar gaps / duplicate-week irregularities in the raw series.

    Returns a list of dicts with keys: kind, from_epiweek, to_epiweek,
    gap_weeks, at_abs_week. These are PROPERTIES OF THE CDC FILE, not bugs in
    our code, and must be disclosed in the figure caption.
    """
    out: list[dict] = []
    gaps = cal["week_start_date"].diff().dt.days
    for i in range(1, len(cal)):
        d = int(gaps.iloc[i])
        if d <= 7:
            continue
        out.append({
            "kind": "missing_weeks",
            "from_epiweek": int(cal["epiweek"].iloc[i - 1]),
            "to_epiweek": int(cal["epiweek"].iloc[i]),
            "gap_weeks": d // 7 - 1,
            "at_abs_week": int(cal["abs_week"].iloc[i]),
        })
    return out


def week_calendar_as_dict(raw_csv: str = DEFAULT_RAW) -> dict:
    """{abs_week: (epiweek:int, week_start_date:pd.Timestamp)} for O(1) joins."""
    cal = load_week_calendar(raw_csv)
    return {
        int(r.abs_week): (int(r.epiweek), r.week_start_date)
        for r in cal.itertuples()
    }


def attach_calendar(df: pd.DataFrame, abs_week_col: str = "abs_week",
                    raw_csv: str = DEFAULT_RAW) -> pd.DataFrame:
    """Add `epiweek` and `week_start_date` columns to a prediction DataFrame.

    This is the single replacement for the buggy `_week_to_epiweek()` helper.
    Rows whose `abs_week` is outside the raw file are dropped with a warning
    rather than silently mis-dated.
    """
    cal = load_week_calendar(raw_csv)[["abs_week", "epiweek", "week_start_date"]]
    out = df.merge(cal, left_on=abs_week_col, right_on="abs_week", how="left")
    n_bad = int(out["week_start_date"].isna().sum())
    if n_bad:
        import warnings
        warnings.warn(
            f"attach_calendar: {n_bad} rows had an abs_week outside the raw "
            "calendar and were dropped", RuntimeWarning)
        out = out[out["week_start_date"].notna()].copy()
    return out


# --------------------------------------------------------------------------- #
def _self_check() -> None:
    assert mmwr_week1_start(2020) == _dt.date(2019, 12, 29)
    assert mmwr_week1_start(2021) == _dt.date(2021, 1, 3)
    assert mmwr_year_has_53_weeks(2020) is True
    assert mmwr_year_has_53_weeks(2003) is False
    assert mmwr_year_has_53_weeks(2004) is True
    assert mmwr_year_has_53_weeks(2009) is True
    assert mmwr_year_has_53_weeks(2015) is True

    cal = load_week_calendar()
    assert len(cal) == 1025, len(cal)
    assert int(cal["epiweek"].iloc[0]) == 200201
    assert int(cal["epiweek"].iloc[-1]) == 202152
    # The drift that motivated this module: row 820 is 2018-01-28, not 2017-09-17.
    d820 = cal.loc[cal["abs_week"] == 820, "week_start_date"].iloc[0]
    assert d820 == pd.Timestamp("2018-01-28"), d820
    # The 2002 hole must survive.
    an = list_anomalies(cal)
    big = [a for a in an if a["gap_weeks"] >= 19]
    assert len(big) == 1 and big[0]["gap_weeks"] == 19, an
    print("[cdc_calendar] self-check OK")
    print(f"  rows={len(cal)}  first={cal['week_start_date'].iloc[0].date()}  "
          f"last={cal['week_start_date'].iloc[-1].date()}")
    print(f"  abs_week 820 -> {d820.date()}  (old synthetic helper said 2017-09-17)")
    print(f"  anomalies: {len(an)}  (19-week hole in 2002 + {len(an)-1} minor)")


if __name__ == "__main__":
    _self_check()
