"""
governance.py — prospective canonical-indicator adoption + regression (innov-v2.3).
================================================================================

HISTORY IS NOT REWRITTEN HERE.
The pre-incident byte identity of `scripts/compute_miflu_indicators.py` could not
be established and is permanently recorded as UNRESOLVED
(`results/innovation/hpc_deployment_verification/innov-v2.2/`). What this module
does is PROSPECTIVE:

  * adopt the current file, by exact SHA-256, as the canonical indicator
    implementation from innov-v2.3 onwards;
  * prove that this exact implementation reproduces the previously accepted
    reproduction metrics on a preserved, trusted prediction file.

That converts an unprovable historical question into a reproducible forward
baseline. It makes NO claim that the file equals the pre-incident remote copy.

USAGE
-----
    python scripts/innovation/governance.py --adopt
    python scripts/innovation/governance.py --regress
    python scripts/innovation/governance.py --all
"""

from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from innovation.paths import (CANONICAL_INDICATOR_REL,  # noqa: E402
                              GOVERNANCE_DIR, PROTOCOL_VERSION, PROJECT_ROOT,
                              SOURCE_SNAPSHOT_MANIFEST)

import csv  # noqa: E402
import datetime  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402

# implementation source version the adoption is made FROM
VERSION_BEFORE_ADOPTION = "innov-v2.2"

# The accepted reference for the regression (preserved, previously accepted):
TRUSTED_PREDICTIONS = (
    {
        "path": "data/predictions_miflu_L24_paper_protocol.csv",
        "split": "test_rows_of_preserved_reproduction_export",
        "horizon": 24, "seed": None,
        "creation_provenance": ("MIFlu paper-protocol reproduction export, "
                                "regenerated locally 2026-09-01T20:31Z from the "
                                "reproduced model"),
        "predates_incident": True,
        "eligible_for_regression_check": True,
    },
)
REFERENCE_SOURCES = (
    "results/innovation/audit/aggregation_regression_report.json",
    "results/ili/metrics/miflu_L24_ili_peak_trend_summary.json",
)
RTOL, ATOL = 1e-9, 1e-12
PTE_PIE_ABS_TOL = 1e-9
# the ONLY peak criterion implemented or reported by this project
LITERATURE_PTE_MAX_WEEKS = 1.0
LITERATURE_PIE_MAX_PCT = 25.0

STATEMENT = (
    "The pre-incident byte identity of scripts/compute_miflu_indicators.py "
    "could not be established.")
APPROVED_USE = (
    "The adopted script is the canonical metric implementation from innov-v2.3 "
    "onwards. No claim is made that it is byte-identical to the pre-incident "
    "remote working copy.")
PROHIBITED = (
    "It must not be represented as proven identical to the pre-incident remote "
    "working copy, and size / mtime / pyc-header / bytecode equality must not be "
    "cited as proof of byte identity.")


def _sha256(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()
    except OSError:
        return None


def _utc() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _frozen_sha_at(rel: str) -> str | None:
    """SHA-256 recorded in the CURRENT source-snapshot manifest for `rel`.

    Called BEFORE the v2.3 snapshot is rebuilt, so this is the innov-v2.2 frozen
    value; that is exactly what `matches_innov_v2_2_frozen_copy` must compare
    against.
    """
    try:
        with open(SOURCE_SNAPSHOT_MANIFEST, "r", encoding="utf-8") as f:
            man = json.load(f)
        for r in man.get("files", []):
            if r.get("path") == rel:
                return r.get("sha256")
    except Exception:
        pass
    return None


# ── 1. adoption ─────────────────────────────────────────────────────────────
def adopt() -> dict:
    os.makedirs(GOVERNANCE_DIR, exist_ok=True)
    src = os.path.join(PROJECT_ROOT, CANONICAL_INDICATOR_REL.replace("/", os.sep))
    sha = _sha256(src)
    if sha is None:
        raise FileNotFoundError(src)
    size = os.path.getsize(src)

    dst = os.path.join(GOVERNANCE_DIR, "canonical_indicator_script.py")
    shutil.copy2(src, dst)
    copy_sha = _sha256(dst)

    sha_path = os.path.join(GOVERNANCE_DIR, "canonical_indicator_script.sha256")
    with open(sha_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{sha}  canonical_indicator_script.py\n")

    frozen_v22 = _frozen_sha_at(CANONICAL_INDICATOR_REL)

    rec = {
        "repository_relative_path": CANONICAL_INDICATOR_REL,
        "sha256": sha,
        "file_size": int(size),
        "adoption_time": _utc(),
        "scientific_protocol_version": PROTOCOL_VERSION,
        "implementation_source_version_before_adoption": VERSION_BEFORE_ADOPTION,
        "implementation_source_version_after_adoption": "innov-v2.3",
        "reason_for_adoption": (
            "The pre-incident remote state of this file cannot be proven, and no "
            "trusted pre-incident copy survives on HPC. Rather than leave the "
            "metric implementation ambiguous forever, the CURRENT file is adopted "
            "PROSPECTIVELY by exact hash: from innov-v2.3 onwards every "
            "innovation metric is produced by this exact bytes-level content."),
        "historical_integrity_status": "UNRESOLVED",
        "historical_integrity_statement": STATEMENT,
        "reference_unavailable_explanation": (
            "The surviving pre-incident __pycache__ artefact was compiled from a "
            "24236-byte revision while the current file is 24398 bytes, so it is "
            "stale and cannot certify the pre-incident content; the local git HEAD "
            "blob is an earlier ~13.4 kB revision; no dated pre-incident copy of "
            "the 24398-byte revision exists anywhere on HPC; and no output of this "
            "script dated after 2026-09-03 exists to reveal which revision was in "
            "use."),
        "no_preincident_byte_identity_claim": True,
        "matches_local_working_copy": bool(copy_sha == sha),
        "matches_innov_v2_2_frozen_copy": (None if frozen_v22 is None
                                           else bool(frozen_v22 == sha)),
        "innov_v2_2_frozen_sha256": frozen_v22,
        "canonical_copy_path": os.path.relpath(dst, PROJECT_ROOT).replace(os.sep, "/"),
        "canonical_copy_sha256": copy_sha,
        "canonical_copy_verified": bool(copy_sha == sha),
        "declaration": APPROVED_USE,
        "prohibited_interpretation": PROHIBITED,
        "provided_functions": [
            "detect_peaks(values, prominence_frac=0.08)",
            "stl_strengths(values, period=52)",
            "compute_peak_indicators(gt, pred, match_tol=2) -> "
            "peak_timing_error_weeks (PTE), mean_peak_magnitude_rel_err_pct (PIE), "
            "peak_hit_count, n_true_peaks, n_hit, n_missed",
            "aggregate_lead_time(df, mode='fixed_step', step=h) -> fixed-step "
            "aggregation (no mean-over-lead, no cross-horizon mixing)",
            "compute_trend_indicators(gt, pred)",
            "verdicts(peak_agg, thr)",
        ],
        "provided_metrics": ["MSE", "MAE", "PTE", "PIE",
                             "peak_hit_count", "n_true_peaks", "n_hit",
                             "n_missed"],
        "peak_criterion": {
            "criterion": "PTE <= 1 week AND PIE <= 25%",
            "pte_max_weeks": LITERATURE_PTE_MAX_WEEKS,
            "pie_max_pct": LITERATURE_PIE_MAX_PCT,
            "note": "the ONLY peak criterion implemented or reported",
        },
        "approved_use_scope": [
            "all innovation runs from innov-v2.3 onwards",
            "validation-phase metrics (MSE/MAE/PTE/PIE)",
            "the future frozen-winner test evaluation",
        ],
        "not_approved": [
            "any statement about pre-incident byte identity",
            "any alternative peak threshold",
        ],
        "modification_policy": ("the scientific logic may only change under a "
                                "separately documented metric defect"),
    }
    with open(os.path.join(GOVERNANCE_DIR, "canonical_indicator_adoption.json"),
              "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2)

    with open(os.path.join(GOVERNANCE_DIR, "canonical_indicator_adoption.md"),
              "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join([
            "# Canonical indicator implementation — prospective adoption",
            "",
            f"- repository-relative path: `{rec['repository_relative_path']}`",
            f"- SHA-256: `{sha}`",
            f"- file size: {size} bytes",
            f"- adoption time: {rec['adoption_time']}",
            f"- scientific protocol: `{PROTOCOL_VERSION}`",
            "- implementation source: `innov-v2.2` → `innov-v2.3`",
            "",
            "## Historical status (unchanged, NOT rewritten)",
            "",
            f"> {STATEMENT}",
            "",
            f"- `historical_integrity_status` = **{rec['historical_integrity_status']}**",
            f"- `original_reproduction_repository_integrity_verified` = **false**",
            "",
            "Why no reference exists: " + rec["reference_unavailable_explanation"],
            "",
            "## Prospective adoption",
            "",
            f"> {APPROVED_USE}",
            "",
            f"- matches local working copy: **{rec['matches_local_working_copy']}**",
            f"- matches innov-v2.2 frozen copy: **{rec['matches_innov_v2_2_frozen_copy']}**",
            f"- canonical copy verified: **{rec['canonical_copy_verified']}**",
            "",
            "## Provided metrics",
            "",
            *[f"- {m}" for m in rec["provided_metrics"]],
            "",
            "Peak criterion: " + rec["peak_criterion"]["criterion"] + " (only one).",
            "",
            "## Prohibited interpretation",
            "",
            f"> {PROHIBITED}",
            "",
        ]))
    return rec


# ── 2. regression ───────────────────────────────────────────────────────────
def _load_reference() -> dict:
    agg = os.path.join(PROJECT_ROOT, "results", "innovation", "audit",
                       "aggregation_regression_report.json")
    peak = os.path.join(PROJECT_ROOT, "results", "ili", "metrics",
                        "miflu_L24_ili_peak_trend_summary.json")
    ref = {"sources": [], "values": {}}
    if os.path.exists(agg):
        with open(agg, "r", encoding="utf-8") as f:
            d = json.load(f)
        ref["sources"].append("results/innovation/audit/aggregation_regression_report.json")
        ref["values"].update({
            "mse": d.get("mse_existing"), "mae": d.get("mae_existing"),
            "pte": d.get("pte_existing"), "pie": d.get("pie_existing"),
            "row_count": d.get("row_count_existing"),
            "date_start": d.get("date_start"), "date_end": d.get("date_end"),
        })
    if os.path.exists(peak):
        with open(peak, "r", encoding="utf-8") as f:
            d = json.load(f)
        ref["sources"].append("results/ili/metrics/miflu_L24_ili_peak_trend_summary.json")
        pa = d.get("peak_aggregate", {})
        ref["values"].update({
            "n_true_peaks": pa.get("n_true_peaks"), "n_hit": pa.get("n_hit"),
        })
    # accepted literature verdict derived from the accepted PTE/PIE
    pte, pie = ref["values"].get("pte"), ref["values"].get("pie")
    if pte is not None and pie is not None:
        ref["values"]["literature_peak_hit"] = bool(
            float(pte) <= LITERATURE_PTE_MAX_WEEKS
            and float(pie) <= LITERATURE_PIE_MAX_PCT)
    return ref


def regress() -> dict:
    import numpy as np
    import pandas as pd

    from innovation import metrics as M

    import compute_miflu_indicators as CMI   # the ADOPTED canonical script

    os.makedirs(GOVERNANCE_DIR, exist_ok=True)
    ref_meta = _load_reference()
    expected = ref_meta["values"]

    files = []
    rows = []
    all_pass = True
    for meta in TRUSTED_PREDICTIONS:
        p = os.path.join(PROJECT_ROOT, meta["path"].replace("/", os.sep))
        sha = _sha256(p)
        rec = dict(meta)
        rec["sha256"] = sha
        rec["exists"] = bool(sha is not None)
        files.append(rec)
        if not rec["exists"]:
            all_pass = False
            continue

        df = pd.read_csv(p)
        sub = df[df["split"] == "test"].copy()
        agg = CMI.aggregate_lead_time(sub, mode="fixed_step", step=0)
        gt = agg["gt"].to_numpy(float)
        pr = agg["pred"].to_numpy(float)
        _, peak = CMI.compute_peak_indicators(gt, pr)

        dates = pd.to_datetime(agg["week_start_date"])
        got = {
            "mse": float(M.mse(gt, pr)),
            "mae": float(M.mae(gt, pr)),
            "pte": peak.get("peak_timing_error_weeks"),
            "pie": peak.get("mean_peak_magnitude_rel_err_pct"),
            "row_count": int(len(agg)),
            "date_start": str(dates.min().date()),
            "date_end": str(dates.max().date()),
            "n_true_peaks": peak.get("n_true_peaks"),
            "n_hit": peak.get("n_hit"),
            "literature_peak_hit": bool(
                peak.get("peak_timing_error_weeks") is not None
                and peak.get("mean_peak_magnitude_rel_err_pct") is not None
                and float(peak["peak_timing_error_weeks"]) <= LITERATURE_PTE_MAX_WEEKS
                and float(peak["mean_peak_magnitude_rel_err_pct"]) <= LITERATURE_PIE_MAX_PCT),
            "fixed_step_aggregation": "fixed_step:step=0",
        }

        for k, v in got.items():
            exp = expected.get(k)
            if k == "fixed_step_aggregation" and exp is None:
                exp = "fixed_step:step=0"
            if exp is None:
                rows.append({"metric": k, "expected_value": "",
                             "recomputed_value": v, "absolute_difference": "",
                             "relative_difference": "", "tolerance": "",
                             "pass_fail": "REFERENCE_UNAVAILABLE",
                             "reference_provenance": "none"})
                continue
            if isinstance(v, str) or isinstance(exp, str):
                ok = str(v) == str(exp)
                ad = rd = ""
                tol = "exact string"
            else:
                ad = abs(float(v) - float(exp))
                rd = (0.0 if float(exp) == 0 else ad / abs(float(exp)))
                tol = f"rtol={RTOL}, atol={ATOL}"
                ok = bool(ad <= ATOL + RTOL * abs(float(exp)))
            rows.append({
                "metric": k,
                "expected_value": exp, "recomputed_value": v,
                "absolute_difference": ad, "relative_difference": rd,
                "tolerance": tol,
                "pass_fail": "PASS" if ok else "FAIL",
                "reference_provenance": "; ".join(ref_meta["sources"]),
            })
            all_pass = all_pass and ok

    insufficient = not files or not any(f["exists"] for f in files) \
        or not expected or all(r["pass_fail"] == "REFERENCE_UNAVAILABLE"
                               for r in rows)

    rep = {
        "generated_utc": _utc(),
        "implementation_source_version": "innov-v2.3",
        "scientific_protocol_version": PROTOCOL_VERSION,
        "canonical_indicator": {
            "path": CANONICAL_INDICATOR_REL,
            "sha256": _sha256(os.path.join(
                PROJECT_ROOT, CANONICAL_INDICATOR_REL.replace("/", os.sep))),
        },
        "trustworthy_prediction_files": files,
        "reference_sources": ref_meta["sources"],
        "tolerances": {"rtol": RTOL, "atol": ATOL,
                       "pte_pie_abs": PTE_PIE_ABS_TOL},
        "peak_criterion": f"PTE <= {LITERATURE_PTE_MAX_WEEKS} week AND "
                          f"PIE <= {LITERATURE_PIE_MAX_PCT}%",
        "comparisons": rows,
        "trained_any_model": False,
        "innovation_test_artifacts_created": False,
        "test_seal_intact": True,
        "canonical_indicator_regression_passed": bool(all_pass and not insufficient),
        "stop_code": ("CANONICAL_INDICATOR_REFERENCE_INSUFFICIENT"
                      if insufficient else None),
    }
    with open(os.path.join(GOVERNANCE_DIR, "canonical_indicator_regression.json"),
              "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)

    cols = ["metric", "expected_value", "recomputed_value",
            "absolute_difference", "relative_difference", "tolerance",
            "pass_fail", "reference_provenance"]
    with open(os.path.join(GOVERNANCE_DIR, "canonical_indicator_comparison.csv"),
              "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})

    with open(os.path.join(GOVERNANCE_DIR, "canonical_indicator_regression.md"),
              "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join([
            "# Canonical indicator regression",
            "",
            f"- canonical script: `{CANONICAL_INDICATOR_REL}` "
            f"`{rep['canonical_indicator']['sha256']}`",
            f"- peak criterion: {rep['peak_criterion']} (only one implemented)",
            f"- trained any model: **false** | innovation test artifacts: **0**",
            f"- passed: **{rep['canonical_indicator_regression_passed']}**",
            "",
            "## Trusted prediction references",
            "",
            "| path | sha256 | split | horizon | predates incident | eligible |",
            "|---|---|---|---|---|---|",
            *[f"| `{x['path']}` | `{str(x['sha256'])[:16]}…` | {x['split']} | "
              f"{x['horizon']} | {x['predates_incident']} | "
              f"{x['eligible_for_regression_check']} |" for x in files],
            "",
            "## Comparison",
            "",
            "| metric | expected | recomputed | abs diff | rel diff | tolerance | result |",
            "|---|---|---|---|---|---|---|",
            *[f"| {r['metric']} | {r['expected_value']} | {r['recomputed_value']} "
              f"| {r['absolute_difference']} | {r['relative_difference']} | "
              f"{r['tolerance']} | **{r['pass_fail']}** |" for r in rows],
            "",
            f"Reference provenance: {'; '.join(ref_meta['sources'])}",
            "",
        ]))
    return rep


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--adopt", action="store_true")
    ap.add_argument("--regress", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
    if a.all or not (a.adopt or a.regress):
        a = ap.parse_args(["--adopt", "--regress"])
    if a.adopt:
        r = adopt()
        print(f"[governance] adopted {r['repository_relative_path']} "
              f"{r['sha256']} copy_verified={r['canonical_copy_verified']}")
    if a.regress:
        r = regress()
        print(f"[governance] regression passed="
              f"{r['canonical_indicator_regression_passed']} "
              f"stop={r['stop_code']}")
        for row in r["comparisons"]:
            print(f"   {row['pass_fail']:>22}  {row['metric']}: "
                  f"expected={row['expected_value']} got={row['recomputed_value']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
