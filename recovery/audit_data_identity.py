# -*- coding: utf-8 -*-
"""Stage 1 data identity audit (CPU only, read-only).

Verifies the author CSVs against the recovery-plan claims and compares the
author snapshot with the project's July-2026 FluView snapshot.

Outputs (all under recovery/):
  dataset_manifest.json      byte+semantic hashes, rows, cols, dtypes, ranges
  feature_mapping.csv        author column -> FluView field -> project column
  coverage_audit.csv         per-source week coverage, gaps, duplicates
  overlap_differences.csv    row-level joined differences
  data_identity_report.md    narrative + classification
"""
from __future__ import annotations
import csv
import datetime
import hashlib
import json
import os

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECOVERY = os.path.join(PROJECT, "recovery")
AUTHOR = os.path.join(PROJECT, "recovery", "author_repo", "dataset", "illness")

VAR7 = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
        "ILITOTAL", "NUM. OF PROVIDERS", "OT"]
AUTH_COL_TO_NAME = {"1": "% WEIGHTED ILI", "2": "% UNWEIGHTED ILI",
                    "3": "AGE 0-4", "4": "AGE 5-24", "5": "ILITOTAL",
                    "6": "NUM. OF PROVIDERS", "OT": "OT"}
NAME_TO_AUTH_COL = {"% WEIGHTED ILI": "1", "% UNWEIGHTED ILI": "2",
                    "AGE 0-4": "3", "AGE 5-24": "4", "ILITOTAL": "5",
                    "NUM. OF PROVIDERS": "6", "OT": "OT"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def load_rows(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_date(v):
    v = v.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(v, fmt)
        except ValueError:
            pass
    return None


def main():
    auth_p = os.path.join(AUTHOR, "national_illness.csv")
    auth_o = os.path.join(AUTHOR, "national_illness_orig.csv")
    proj_p = os.path.join(PROJECT, "data", "raw", "national_illness_raw.csv")
    pex_p = os.path.join(PROJECT, "data", "raw",
                         "national_illness_raw_paper_exact.csv")

    auth = load_rows(auth_p)
    auth_orig = load_rows(auth_o)
    proj = load_rows(proj_p)
    pex = load_rows(pex_p)

    manifest = {"sources": {}, "checks": {}}
    for tag, p, rows in [("author_processed", auth_p, auth),
                         ("author_orig", auth_o, auth_orig),
                         ("project_raw", proj_p, proj),
                         ("paper_exact", pex_p, pex)]:
        m = {"path": os.path.relpath(p, PROJECT).replace(os.sep, "/"),
             "sha256": sha256(p),
             "size_bytes": os.path.getsize(p),
             "n_rows": len(rows),
             "columns": list(rows[0].keys()) if rows else []}
        manifest["sources"][tag] = m

    # ---- author identity: 966 rows, identical parsed numeric values ----
    assert len(auth) == len(auth_orig) == 966, (len(auth), len(auth_orig))
    n_diff = 0
    maxdiff = 0.0
    for a, o in zip(auth, auth_orig):
        for col in VAR7:
            ac = AUTH_COL_TO_NAME if col in AUTH_COL_TO_NAME else None
        for aname, oname in [("1", "% WEIGHTED ILI"), ("2", "%UNWEIGHTED ILI"),
                             ("3", "AGE 0-4"), ("4", "AGE 5-24"),
                             ("5", "ILITOTAL"), ("6", "NUM. OF PROVIDERS"),
                             ("OT", "OT")]:
            va, vo = num(a[aname]), num(o[oname])
            if va != vo:
                n_diff += 1
                maxdiff = max(maxdiff, abs(va - vo))
    manifest["checks"]["author_966_parsed_identity"] = {
        "n_rows": len(auth),
        "numeric_cell_diffs": n_diff,
        "max_abs_diff": maxdiff,
        "identical": n_diff == 0,
    }

    # ---- author date labels ----
    dates = [parse_date(r["date"]) for r in auth]
    first, last = dates[0], dates[-1]
    deltas = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
    manifest["checks"]["author_dates"] = {
        "first": str(first), "last": str(last),
        "n_rows": len(auth),
        "all_7day_cadence": all(d == 7 for d in deltas),
        "distinct_deltas": sorted(set(deltas)),
    }

    # ---- paper_exact vs author: value identity (ignoring epiweek/header) ----
    pex_vals = [[num(r[c]) for c in VAR7] for r in pex]
    auth_vals = [[num(r[NAME_TO_AUTH_COL[c]]) for c in VAR7] for r in auth]
    diffs = 0
    for i in range(966):
        for j in range(7):
            if pex_vals[i][j] != auth_vals[i][j]:
                diffs += 1
    manifest["checks"]["paper_exact_equals_author_values"] = {
        "cell_diffs": diffs, "identical": diffs == 0}

    # ---- paper_exact epiweek encoding vs project epiweek encoding ----
    pex_ew = [int(r["epiweek"]) for r in pex]
    proj_ew = [int(r["epiweek"]) for r in proj]
    manifest["checks"]["paper_exact_epiweeks"] = {
        "first": pex_ew[0], "last": pex_ew[-1], "n": len(pex_ew),
        "strictly_increasing": all(pex_ew[i] < pex_ew[i + 1]
                                   for i in range(len(pex_ew) - 1)),
    }
    manifest["checks"]["project_epiweeks"] = {
        "first": proj_ew[0], "last": proj_ew[-1], "n": len(proj_ew),
        "strictly_increasing": all(proj_ew[i] < proj_ew[i + 1]
                                   for i in range(len(proj_ew) - 1)),
    }

    # ---- coverage: set comparison ----
    proj_set = set(proj_ew)
    pex_set = set(pex_ew)
    manifest["checks"]["coverage"] = {
        "project_unique": len(proj_set), "project_n": len(proj_ew),
        "project_duplicates": len(proj_ew) - len(proj_set),
        "pex_unique": len(pex_set), "pex_n": len(pex_ew),
        "pex_duplicates": len(pex_ew) - len(pex_set),
        "pex_minus_proj": sorted(pex_set - proj_set)[:20],
        "proj_extra_at_start": sorted(proj_set - pex_set)[:50],
        "proj_extra_at_end": sorted(proj_set - pex_set)[-50:],
    }

    # ---- overlap join on epiweek ----
    proj_by_ew = {r["epiweek"]: r for r in proj}
    ov = []
    for i, r in enumerate(pex):
        ew = r["epiweek"]
        pr = proj_by_ew.get(ew)
        if pr is None:
            continue
        for c in VAR7:
            va = num(r[c])
            vp = num(pr[c])
            if va is None or vp is None:
                continue
            d = vp - va
            rel = d / va if abs(va) > 1e-9 else None
            ov.append({"epiweek": ew, "author_date": pex[i]["release_date"],
                       "variable": c, "author_value": va,
                       "project_value": vp, "abs_diff": d,
                       "rel_diff": rel})

    # write overlap_differences.csv
    with open(os.path.join(RECOVERY, "overlap_differences.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(ov[0].keys()))
        w.writeheader()
        for r in ov:
            w.writerow(r)

    # ---- per-variable summary ----
    from collections import defaultdict
    pervar = defaultdict(list)
    for r in ov:
        pervar[r["variable"]].append(r)
    var_summary = {}
    for c, rows in pervar.items():
        exact = sum(1 for r in rows if r["project_value"] == r["author_value"])
        absd = sorted(r["abs_diff"] for r in rows)
        var_summary[c] = {
            "n_overlap": len(rows), "exact_matches": exact,
            "max_abs_diff": absd[-1], "median_abs_diff": absd[len(absd)//2],
            "n_rounding_only": sum(1 for r in rows
                                   if abs(r["abs_diff"]) <= 1e-5),
            "n_nontrivial": sum(1 for r in rows
                                if abs(r["abs_diff"]) > 1e-4),
            "first_diff_row": next((r["epiweek"] for r in rows
                                    if abs(r["abs_diff"]) > 1e-4), None),
        }
    manifest["checks"]["overlap_per_variable"] = var_summary

    # ---- denominator identity: 100 * ILITOTAL / OT == %UNWEIGHTED ILI ----
    resid = []
    for r in auth:
        ili = num(r["5"]); ot = num(r["OT"]); un = num(r["2"])
        if ot and ili is not None:
            resid.append(abs(100.0 * ili / ot - un))
    manifest["checks"]["unweighted_denominator_identity"] = {
        "n": len(resid), "max_resid": max(resid),
        "median_resid": sorted(resid)[len(resid)//2],
    }

    # ---- feature mapping ----
    with open(os.path.join(RECOVERY, "feature_mapping.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["author_column", "author_orig_header", "fluview_field",
                    "project_column", "interpretation"])
        w.writerow(["1", "% WEIGHTED ILI", "wili", "% WEIGHTED ILI",
                    "percentage of visits, population-weighted"])
        w.writerow(["2", "%UNWEIGHTED ILI", "ili", "% UNWEIGHTED ILI",
                    "percentage of visits, unweighted"])
        w.writerow(["3", "AGE 0-4", "num_age_0", "AGE 0-4",
                    "ILI visit count, ages 0-4"])
        w.writerow(["4", "AGE 5-24", "num_age_1", "AGE 5-24",
                    "ILI visit count, ages 5-24"])
        w.writerow(["5", "ILITOTAL", "num_ili", "ILITOTAL",
                    "total ILI visit count"])
        w.writerow(["6", "NUM. OF PROVIDERS", "num_providers",
                    "NUM. OF PROVIDERS", "reporting provider count"])
        w.writerow(["OT", "OT", "num_patients", "OT",
                    "total patient visits (denominator)"])

    # ---- coverage audit csv ----
    with open(os.path.join(RECOVERY, "coverage_audit.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source", "n_rows", "first_week", "last_week",
                    "first_label", "last_label"])
        w.writerow(["author", 966, pex_ew[0], pex_ew[-1],
                    pex[0]["release_date"], pex[-1]["release_date"]])
        w.writerow(["project_raw", 1025, proj_ew[0], proj_ew[-1],
                    proj[0]["release_date"], proj[-1]["release_date"]])

    with open(os.path.join(RECOVERY, "dataset_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)

    print(json.dumps(manifest["checks"], indent=2, default=str))


if __name__ == "__main__":
    main()
