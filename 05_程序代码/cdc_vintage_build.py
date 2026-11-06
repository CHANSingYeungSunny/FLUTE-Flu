#!/usr/bin/env python
"""
cdc_vintage_build.py — reconstruct the CDC ILINet release calendar (vintage)
===========================================================================

WHY THIS MODULE EXISTS (handoff TASK 4)
---------------------------------------
`06_原始数据集/raw/national_illness_raw.csv` carries a `release_date` column, but
that column has only **8 distinct values** (2013-12-31, 2017-10-24, then the first
Friday of October 2018..2023). Those are ANNUAL BULK SNAPSHOT dates, not the date
each weekly value was first published. An archived final CSV is therefore NOT a
vintage: it cannot tell us what a real-time system would have seen at week W.

The real weekly release calendar IS recoverable from the Delphi Epidata API
(`fluview` endpoint), which stores every (epiweek, issue) pair together with the
exact `release_date`. This module rebuilds:

  1. `cdc_vintage_raw.csv`   — every (epiweek, issue) row for 200201..202152,
                               restricted to lag <= MAX_LAG weeks.
  2. `cdc_vintage.csv`       — per-epiweek summary: first issue / first release
                               date / first-print value / final value / revision.
  3. `cdc_peak_revintage.csv`— season peak re-scored on the AS-OF series
                               (first print) vs the FINAL series.

Season boundary follows the frozen project definition
(`05_程序代码/innovation/metrics.py`): MMWR week 40 of year Y .. week 20 of Y+1.
Peak = argmax of ILITOTAL inside that window; ties -> earliest week.

Data source
-----------
Delphi Epidata, fluview endpoint, region `nat`, public, no key.
  https://api.delphi.cmu.edu/epidata/fluview/
Field semantics used here:
  issue        = ISO week (YYYYWW) in which CDC released that revision
  release_date = the exact calendar date of that release
  lag          = issue - epiweek, in weeks (0 = same-week first print)
  num_ili      = ILITOTAL (the project's peak target variable, channel 4)
  ili          = % WEIGHTED ILI

Usage
-----
    python 05_程序代码/cdc_vintage_build.py            # fetch + build all three
    python 05_程序代码/cdc_vintage_build.py --cache    # rebuild from cached raw
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = os.path.join(ROOT, "02_数字表格")
RAW_CSV = os.path.join(ROOT, "06_原始数据集", "raw", "national_illness_raw.csv")

API = "https://api.delphi.cmu.edu/epidata/fluview/"
REGION = "nat"
EPI_START, EPI_END = 200201, 202152
MAX_LAG = 8          # keep the first print plus the following 8 revisions
CHUNK_WEEKS = 26     # weeks per HTTP request (keeps the response well under 10 MB)

RAW_OUT = os.path.join(TABLES, "cdc_vintage_raw.csv")
SUM_OUT = os.path.join(TABLES, "cdc_vintage.csv")
PEAK_OUT = os.path.join(TABLES, "cdc_peak_revintage.csv")
REPORT_OUT = os.path.join(TABLES, "cdc_vintage_report.md")


# --------------------------------------------------------------------- weeks --
def epi_to_ord(epiweek: int) -> int:
    """YYYYWW -> a strictly increasing integer (year*100 + week is enough here)."""
    return epiweek


def add_weeks(epiweek: int, n: int) -> int:
    """Advance a YYYYWW label by n MMWR weeks using a 53-week-safe iteration."""
    y, w = divmod(epiweek, 100)
    for _ in range(n):
        w += 1
        # 53-week years exist; the API tolerates week 53 labels, and a wrong
        # week-53 label is harmless here because results are keyed by the API's
        # own `epiweek` field, not by our label arithmetic.
        if w > 53:
            y, w = y + 1, 1
    return y * 100 + w


def week_range(a: int, b: int):
    out, cur = [], a
    while cur <= b:
        out.append(cur)
        cur = add_weeks(cur, 1)
    return out


# --------------------------------------------------------------------- fetch --
def _get(url: str, tries: int = 4):
    last = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=90) as fh:
                return json.loads(fh.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last = e
            time.sleep(2 + 3 * k)
    raise RuntimeError("fetch failed after %d tries: %s" % (tries, last))


def fetch_vintage() -> list[dict]:
    weeks = week_range(EPI_START, EPI_END)
    rows: dict[tuple[int, int], dict] = {}
    for i in range(0, len(weeks), CHUNK_WEEKS):
        block = weeks[i:i + CHUNK_WEEKS]
        a, b = block[0], block[-1]
        q = urllib.parse.urlencode({
            "regions": REGION,
            "epiweeks": "%d-%d" % (a, b),
            "issues": "%d-%d" % (a, add_weeks(b, MAX_LAG + 1)),
        })
        payload = _get(API + "?" + q)
        # result == -2 means "no results" (legitimate: early epiweeks were only
        # ever released inside a later annual bulk issue, so no issue label in
        # this window exists). Only unexpected codes are fatal.
        if payload.get("result") == -2:
            print("  chunk %d-%d -> no results (pre-archive epoch)" % (a, b),
                  flush=True)
            time.sleep(0.4)
            continue
        if payload.get("result") != 1:
            raise RuntimeError("API result=%s msg=%s for %s"
                               % (payload.get("result"), payload.get("message"), q))
        for r in payload.get("epidata", []):
            if r.get("region") != REGION:
                continue
            if r["epiweek"] < EPI_START or r["epiweek"] > EPI_END:
                continue
            if r["lag"] is None or r["lag"] > MAX_LAG:
                continue
            rows[(r["epiweek"], r["issue"])] = {
                "epiweek": r["epiweek"], "issue": r["issue"],
                "release_date": r["release_date"], "lag": r["lag"],
                "ili": r.get("ili"), "wili": r.get("wili"),
                "num_ili": r.get("num_ili"), "num_patients": r.get("num_patients"),
                "num_providers": r.get("num_providers"),
            }
        print("  chunk %d-%d -> %d rows (total %d)"
              % (a, b, len(payload.get("epidata", [])), len(rows)), flush=True)
        time.sleep(0.4)
    return [rows[k] for k in sorted(rows)]


def write_csv(path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ------------------------------------------------------------------ vintage ---
def build_summary(raw: list[dict]) -> list[dict]:
    by: dict[int, list[dict]] = {}
    for r in raw:
        by.setdefault(int(r["epiweek"]), []).append(r)
    out = []
    for wk in sorted(by):
        rs = sorted(by[wk], key=lambda r: int(r["issue"]))
        first, last = rs[0], rs[-1]
        f_val = float(first["num_ili"]) if first.get("num_ili") not in (None, "") else None
        l_val = float(last["num_ili"]) if last.get("num_ili") not in (None, "") else None
        if f_val is not None and l_val is not None:
            abs_rev = l_val - f_val
            rel_rev = (abs_rev / f_val * 100.0) if f_val else None
        else:
            abs_rev = rel_rev = None
        out.append({
            "epiweek": wk,
            "n_issues": len(rs),
            "first_issue": int(first["issue"]),
            "first_release_date": first["release_date"],
            "first_lag": int(first["lag"]),
            "last_issue": int(last["issue"]),
            "last_release_date": last["release_date"],
            "ilitotal_first": f_val,
            "ilitotal_final": l_val,
            "ilitotal_abs_revision": abs_rev,
            "ilitotal_rel_revision_pct": rel_rev,
            "revision_observed": (abs(abs_rev) > 1e-9) if abs_rev is not None else None,
        })
    return out


# --------------------------------------------------------------------- peaks --
def season_of(epiweek: int) -> str:
    """MMWR 40..20 season label, e.g. 201240 -> '2012-13'. Off-season -> ''."""
    y, w = divmod(epiweek, 100)
    if w >= 40:
        return "%d-%02d" % (y, (y + 1) % 100)
    if w <= 20:
        return "%d-%02d" % (y - 1, y % 100)
    return ""


def recess(series: dict[int, float]) -> list[dict]:
    seasons: dict[str, list[tuple[int, float]]] = {}
    for wk, v in series.items():
        s = season_of(wk)
        if s and v is not None:
            seasons.setdefault(s, []).append((wk, v))
    out = []
    for s in sorted(seasons):
        pts = sorted(seasons[s])
        if len(pts) < 26:            # frozen rule: <26 observed weeks -> not scored
            out.append({"season": s, "n_weeks": len(pts), "scored": False,
                        "peak_week": "", "peak_value": ""})
            continue
        wk, v = max(pts, key=lambda p: (p[1], -p[0]))   # argmax, ties -> earliest
        out.append({"season": s, "n_weeks": len(pts), "scored": True,
                    "peak_week": wk, "peak_value": v})
    return out


def build_peaks(vintage_summary: list[dict]) -> list[dict]:
    final: dict[int, float] = {}
    asof: dict[int, float] = {}
    with open(RAW_CSV, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            try:
                wk = int(r["epiweek"])
                final[wk] = float(r["ILITOTAL"])
            except (KeyError, ValueError):
                continue
    for r in vintage_summary:
        if r["ilitotal_first"] is not None:
            asof[int(r["epiweek"])] = r["ilitotal_first"]

    f_peaks = {d["season"]: d for d in recess(final)}
    a_peaks = {d["season"]: d for d in recess(asof)}
    rows = []
    for s in sorted(set(f_peaks) | set(a_peaks)):
        f = f_peaks.get(s, {})
        a = a_peaks.get(s, {})
        fw, aw = f.get("peak_week", ""), a.get("peak_week", "")
        shift = "" if (fw == "" or aw == "") else int(aw) - int(fw)
        rows.append({
            "season": s,
            "scored_final": f.get("scored", False),
            "scored_asof": a.get("scored", False),
            "peak_week_final": fw,
            "peak_ilitotal_final": f.get("peak_value", ""),
            "peak_week_asof": aw,
            "peak_ilitotal_asof": a.get("peak_value", ""),
            "peak_week_shift": shift,
            "peak_shifted": (shift != "" and shift != 0),
        })
    return rows


# -------------------------------------------------------------------- report --
def write_report(summary: list[dict], peaks: list[dict], raw_n: int) -> None:
    scored = [r for r in peaks if r["scored_final"] and r["scored_asof"]]
    shifted = [r for r in scored if r["peak_shifted"]]
    rev = [r for r in summary if r["revision_observed"]]
    rel = [abs(float(r["ilitotal_rel_revision_pct"])) for r in summary
           if r["ilitotal_rel_revision_pct"] not in (None, "")]
    rel.sort()

    def pct(p: float) -> float:
        return rel[min(len(rel) - 1, int(p * len(rel)))] if rel else 0.0

    # panel weeks (the 1025 epiweeks actually used by the project)
    panel = set()
    with open(RAW_CSV, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            try:
                panel.add(int(r["epiweek"]))
            except (KeyError, ValueError):
                pass
    have = {int(r["epiweek"]) for r in summary}
    miss = sorted(panel - have)
    from collections import Counter
    miss_years = Counter(w // 100 for w in miss)

    lines = [
        "# CDC ILINet vintage / release-calendar reconstruction",
        "",
        "Generated by `05_程序代码/cdc_vintage_build.py` from the Delphi Epidata",
        "`fluview` endpoint (region `nat`, public, no key):",
        "`https://api.delphi.cmu.edu/epidata/fluview/`",
        "",
        "## Coverage",
        "",
        "- panel epiweeks (from `national_illness_raw.csv`): **%d**" % len(panel),
        "- epiweeks with a weekly-release record: **%d**" % len(have),
        "- epiweeks with NO weekly-release record: **%d** (%s)"
        % (len(miss), ", ".join("%d:%d" % kv for kv in sorted(miss_years.items()))),
        "- (epiweek, issue) rows kept (lag <= %d): **%d**" % (MAX_LAG, raw_n),
        "",
        "## Revisions",
        "",
        "- epiweeks revised at least once within lag<=%d: **%d / %d** (%.1f%%)"
        % (MAX_LAG, len(rev), len(summary), 100.0 * len(rev) / max(1, len(summary))),
        "- |ILITOTAL revision| as %% of first print: p10 **%.1f%%**, median **%.1f%%**,"
        " p90 **%.1f%%**" % (pct(0.10), pct(0.50), pct(0.90)),
        "",
        "## Season peaks: final snapshot vs as-of (first print)",
        "",
        "| season | peak wk (final) | ILITOTAL (final) | peak wk (as-of) | ILITOTAL (as-of) | shift (wk) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in peaks:
        if not (r["scored_final"] and r["scored_asof"]):
            continue
        lines.append("| %s | %s | %.0f | %s | %.0f | %s |" % (
            r["season"], r["peak_week_final"], float(r["peak_ilitotal_final"]),
            r["peak_week_asof"], float(r["peak_ilitotal_asof"]),
            r["peak_week_shift"]))
    lines += [
        "",
        "- seasons scored on both series: **%d**" % len(scored),
        "- seasons whose peak week MOVES between final and as-of: **%d** (%.1f%%)"
        % (len(shifted), 100.0 * len(shifted) / max(1, len(scored))),
        "",
        "## Why the archived CSV is not a vintage",
        "",
        "`national_illness_raw.csv` has only 8 distinct `release_date` values —",
        "2013-12-31, 2017-10-24, then the first week of October 2018..2023. Those are",
        "annual bulk snapshot dates, not publication dates of individual weeks.",
        "The Delphi archive instead carries a per-(epiweek, issue) `release_date`,",
        "which is what makes a real-time reconstruction possible at all.",
        "",
        "## Interpretation limits",
        "",
        "1. The as-of series is the FIRST PRINT (issue = epiweek, lag 0). It is the",
        "   value a real-time system would have had at the end of week W, not the",
        "   value it would have had at forecast issue W+1.",
        "2. 2002 weeks (and parts of 2003-04) have no weekly release record in the",
        "   archive; they first appear in the 2013-12-31 bulk reload, so their",
        "   `first_lag` is large and those weeks have NO real-time vintage.",
        "3. This does not re-score the 1120-cell model panel; it re-scores the",
        "   *reference* peak assignment on as-of data and quantifies peak-week",
        "   instability. Model peak metrics remain retrospective.",
        "",
    ]
    with open(REPORT_OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return len(miss)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", action="store_true",
                    help="reuse the cached cdc_vintage_raw.csv instead of fetching")
    a = ap.parse_args()

    if a.cache and os.path.exists(RAW_OUT):
        raw = read_csv(RAW_OUT)
        print("cached raw rows: %d" % len(raw))
    else:
        print("fetching %d..%d from Delphi Epidata ..." % (EPI_START, EPI_END))
        raw = fetch_vintage()
        write_csv(RAW_OUT, raw)
        print("wrote %s (%d rows)" % (RAW_OUT, len(raw)))

    summary = build_summary(raw)
    write_csv(SUM_OUT, summary)
    print("wrote %s (%d epiweeks)" % (SUM_OUT, len(summary)))

    peaks = build_peaks(summary)
    write_csv(PEAK_OUT, peaks)
    print("wrote %s (%d seasons)" % (PEAK_OUT, len(peaks)))

    write_report(summary, peaks, len(raw))
    print("wrote %s" % REPORT_OUT)

    scored = [r for r in peaks if r["scored_final"] and r["scored_asof"]]
    shifted = [r for r in scored if r["peak_shifted"]]
    print("SUMMARY epiweeks=%d scored_seasons=%d peak_shifted=%d"
          % (len(summary), len(scored), len(shifted)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
