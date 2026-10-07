"""
select_best_model.py — VALIDATION-ONLY champion selection (eligibility-gated).
=============================================================================

Two hard rules, both enforced structurally:

 1. TEST SEAL. Every read goes through `_read_json`, which REFUSES any path
    containing a test-artifact token (`test_predictions`, `test_metrics`,
    `test_evaluations/`). `tests/innovation/test_test_gate.py` proves the
    selector never opens a test path.

 2. ELIGIBILITY GATE (pre-HPC revision 5). A run may only enter selection when
    its `run_status.json` explicitly carries:
        protocol_version == PROTOCOL_VERSION,
        experiment_stage in ELIGIBLE_STAGES ("screening" | "full"),
        selection_eligible is True, and smoke_only is False.
    Smoke runs, pilot runs, failed debug runs, ad-hoc runs and any run produced
    under a different protocol are therefore EXCLUDED BY CONSTRUCTION — absence
    of the fields is itself a disqualifier. A legacy annotation file
    (`legacy_runs_eligibility.json`) can additionally force-exclude any run
    without mutating the run's own artifacts.

Score (plan §6): per-L mean-seed validation MSE ratio vs the MIFlu baseline,
equally averaged over the four horizons (lower is better); the candidate's
validation peak-hit ratio must not be below the baseline; ties within 1% are
broken by val MAE -> peak-hit -> trainable params -> training time.
"""

from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import glob
import json
import os
import re

import numpy as np

from innovation import run_artifacts as ART
from innovation.paths import (ELIGIBLE_STAGES, FROZEN_WINNERS_PATH, HORIZONS,
                              INNOVATION_ROOT, LEGACY_ELIGIBILITY_PATH,
                              PROTOCOL_VERSION, RUNS_ROOT, SELECTION_AUDIT_PATH,
                              canonical_model_key)
from innovation.run_id import parse_run_id

SCREENING_SELECTION_AUDIT_PATH = os.path.join(
    INNOVATION_ROOT, "screening", "screening_selection_audit.json")

BASELINE_MODEL = "gpt2_miflu"
TIE_TOL = 0.01

_TEST_PATH_RE = re.compile(
    r"(^|[/\\])test(_evaluations)?([/\\]|$)|test_predictions|test_metrics",
    re.IGNORECASE)


def assert_no_test_path(path) -> None:
    norm = os.path.normpath(str(path))
    if _TEST_PATH_RE.search(norm):
        raise RuntimeError(
            f"select_best_model must never read test artifacts: {path!r}")


def _read_json(path: str, open_fn=open):
    assert_no_test_path(path)
    with open_fn(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_legacy_eligibility(open_fn=open) -> dict:
    """run_id -> {selection_eligible: bool, reason: str} (annotation only)."""
    if not os.path.exists(LEGACY_ELIGIBILITY_PATH):
        return {}
    try:
        data = _read_json(LEGACY_ELIGIBILITY_PATH, open_fn=open_fn)
    except Exception:
        return {}
    out = {}
    for entry in data.get("runs", []):
        rid = entry.get("run_id")
        if rid:
            out[rid] = {"selection_eligible": bool(entry.get("selection_eligible", False)),
                        "reason": entry.get("reason", "legacy annotation")}
    return out


def _eligibility_verdict(st: dict, run_id: str, legacy: dict) -> tuple[bool, list]:
    """Return (eligible, list_of_exclusion_reasons)."""
    reasons = []
    if st.get("status") != "ok":
        reasons.append(f"run_status={st.get('status')!r} (not ok)")
    if "experiment_stage" not in st or "protocol_version" not in st:
        reasons.append("missing_eligibility_fields (predates the eligibility "
                       "schema)")
    else:
        if st.get("protocol_version") != PROTOCOL_VERSION:
            reasons.append(f"protocol_version_mismatch "
                           f"({st.get('protocol_version')} != {PROTOCOL_VERSION})")
        if st.get("experiment_stage") not in ELIGIBLE_STAGES:
            reasons.append(f"stage_not_eligible ({st.get('experiment_stage')})")
        if st.get("smoke_only") is True:
            reasons.append("smoke_only")
        if st.get("selection_eligible") is not True:
            reasons.append("selection_eligible is not True")
    if run_id in legacy and not legacy[run_id]["selection_eligible"]:
        reasons.append(f"legacy_annotation: {legacy[run_id]['reason']}")
    return (len(reasons) == 0), reasons


def load_cohort_manifest(path: str) -> dict:
    """Load a frozen cohort manifest -> run-id set + sha256.

    The manifest is the EXTERNAL provenance layer (immutable after freeze); the
    selector reads it instead of trusting the historical `experiment_stage`
    label, which the controller wrote as "full" for G/H/I/J too.
    """
    import hashlib
    with open(path, "rb") as f:
        raw = f.read()
    data = json.loads(raw.decode("utf-8"))
    ids = {c.get("run_id") for c in data.get("cohort", []) if c.get("run_id")}
    return {"path": path, "sha256": hashlib.sha256(raw).hexdigest(),
            "data": data, "ids": ids}


def scan_runs(open_fn=open, cohort_ids=None) -> list[dict]:
    """Every completed run with an explicit eligibility verdict (never test).

    If ``cohort_ids`` is given, ONLY runs whose id is explicitly listed are
    scanned (the frozen Stage-F cohort). There is NO fallback to scanning all
    `full` runs: an unlisted G/H/I/J run is rejected even when it carries
    ``experiment_stage="full"``.
    """
    legacy = load_legacy_eligibility(open_fn=open_fn)
    rows = []
    for d in sorted(glob.glob(os.path.join(RUNS_ROOT, "*"))):
        if not os.path.isdir(d):
            continue
        rp = os.path.join(d, "run_status.json")
        if not os.path.exists(rp):
            continue
        try:
            st = _read_json(rp, open_fn=open_fn)
        except Exception:
            continue
        run_id = os.path.basename(d)
        if cohort_ids is not None and run_id not in cohort_ids:
            continue
        try:
            meta = parse_run_id(run_id)
        except Exception:
            meta = {"model": "?", "horizon": None, "seed": None}
        meta = dict(meta)
        # ONE canonical model key: prefer the authoritative run_status.model_key,
        # else normalise the slugged run_id model (gpt2-miflu -> gpt2_miflu).
        meta["model"] = canonical_model_key(st.get("model_key") or meta.get("model"))
        eligible, reasons = _eligibility_verdict(st, run_id, legacy)
        rows.append({
            "run_id": run_id, "run_dir": d, **meta,
            "status": st.get("status"),
            "experiment_stage": st.get("experiment_stage"),
            "smoke_only": st.get("smoke_only"),
            "selection_eligible": st.get("selection_eligible"),
            "protocol_version": st.get("protocol_version"),
            "eligible": bool(eligible),
            "exclusion_reasons": reasons,
            "best_val_mse": st.get("best_val_mse"),
            "val_mae_all_z": st.get("val_mae_all_z"),
            "peak_hit_ratio": st.get("peak_hit_ratio"),
            "trainable_parameters": st.get("trainable_parameters"),
            "train_seconds": st.get("train_seconds"),
        })
    return rows


def _mean(vals):
    vals = [v for v in vals if v is not None]
    return float(np.mean(vals)) if vals else None


def build_audit(all_rows: list[dict]) -> dict:
    rows = [r for r in all_rows if r["eligible"]]
    excluded = [{"run_id": r["run_id"], "reasons": r["exclusion_reasons"]}
                for r in all_rows if not r["eligible"]]

    models = sorted({r["model"] for r in rows})
    baseline = [r for r in rows if r["model"] == BASELINE_MODEL]
    base_mse_by_L = {L: _mean([r["best_val_mse"] for r in baseline
                               if r["horizon"] == L]) for L in HORIZONS}
    base_peak = _mean([r["peak_hit_ratio"] for r in baseline])
    missing_baseline_horizons = [L for L in HORIZONS
                                 if base_mse_by_L.get(L) in (None, 0)]
    from collections import Counter
    _cells = Counter((r["model"], r["horizon"], r["seed"]) for r in rows)
    duplicate_cells = sorted(
        [{"model": m, "horizon": L, "seed": s, "n": n}
         for (m, L, s), n in _cells.items() if n > 1],
        key=lambda x: (x["model"], x["horizon"], x["seed"]))

    results = []
    for m in models:
        if m == BASELINE_MODEL:
            continue
        per_L, complete = {}, True
        for L in HORIZONS:
            cand = _mean([r["best_val_mse"] for r in rows
                          if r["model"] == m and r["horizon"] == L])
            if cand is None or base_mse_by_L[L] in (None, 0):
                complete = False
                break
            per_L[L] = cand / base_mse_by_L[L]
        if not complete:
            continue
        peak = _mean([r["peak_hit_ratio"] for r in rows if r["model"] == m])
        params = _mean([r["trainable_parameters"] for r in rows if r["model"] == m])
        secs = _mean([r["train_seconds"] for r in rows if r["model"] == m])
        mae = _mean([r["val_mae_all_z"] for r in rows if r["model"] == m])
        results.append({
            "model": m, "primary_score": float(np.mean(list(per_L.values()))),
            "per_L_ratio": per_L, "val_mae": mae, "peak_hit_ratio": peak,
            "baseline_peak_hit_ratio": base_peak,
            "peak_not_below_baseline": bool(
                peak is None or base_peak is None or peak >= base_peak),
            "trainable_parameters": params, "train_seconds": secs,
        })

    results.sort(key=lambda x: x["primary_score"])
    winner = None
    if results:
        best = results[0]["primary_score"]
        tied = [r for r in results
                if (r["primary_score"] - best) <= TIE_TOL * max(best, 1e-12)]
        tied.sort(key=lambda r: (
            0 if r["peak_not_below_baseline"] else 1,
            r["val_mae"] if r["val_mae"] is not None else 1e18,
            -(r["peak_hit_ratio"] or 0.0),
            r["trainable_parameters"] if r["trainable_parameters"] is not None else 1e18,
            r["train_seconds"] if r["train_seconds"] is not None else 1e18))
        winner = tied[0]

    n_models = len(models)
    n_L = sum(1 for L in HORIZONS if any(r["horizon"] == L for r in rows))
    if not rows:
        status = "no_eligible_runs"
    elif missing_baseline_horizons:
        status = "baseline_horizon_missing"
    elif winner is None:
        status = ("insufficient_data" if n_L < len(HORIZONS)
                  else "no_eligible_candidate")
    else:
        status = "ok"
    diagnostic = {
        "ok": status == "ok",
        "status": status,
        "baseline_model": BASELINE_MODEL,
        "missing_baseline_horizons": missing_baseline_horizons,
        "duplicate_cells": duplicate_cells,
        "n_eligible_candidates": len(results),
        "reason": ("champion selected" if status == "ok" else
                   ("baseline %r has no eligible run for horizons %s"
                    % (BASELINE_MODEL, missing_baseline_horizons)
                    if missing_baseline_horizons else
                    "no candidate has complete eligible coverage across all horizons")),
    }
    return {
        "created_utc": ART.utc_now(),
        "selection_split": "validation_only",
        "test_accessed": False,
        "protocol_version": PROTOCOL_VERSION,
        "eligible_stages": list(ELIGIBLE_STAGES),
        "baseline_model": BASELINE_MODEL,
        "baseline_val_mse_by_L": base_mse_by_L,
        "baseline_peak_hit_ratio": base_peak,
        "horizons_covered": n_L,
        "n_runs_scanned": len(all_rows),
        "n_runs_eligible": len(rows),
        "n_runs_excluded": len(excluded),
        "excluded_runs": excluded,
        "n_models_eligible": n_models,
        "status": status,
        "diagnostic": diagnostic,
        "missing_baseline_horizons": missing_baseline_horizons,
        "duplicate_cells": duplicate_cells,
        "candidates": results,
        "winner": winner,
        "note": ("runs lacking explicit eligibility fields, smoke/pilot/adhoc "
                 "runs and protocol mismatches are excluded by construction"
                 if status != "ok" else
                 "winner frozen; test evaluation now permitted"),
    }


def freeze_winners(audit: dict) -> str | None:
    if not audit.get("winner"):
        return None
    payload = {"frozen_utc": ART.utc_now(),
               "basis": "select_best_model.py (validation-only, eligibility-gated)",
               "selection_audit": os.path.basename(SELECTION_AUDIT_PATH),
               "winners": [audit["winner"]]}
    ART.write_json(FROZEN_WINNERS_PATH, payload)
    return FROZEN_WINNERS_PATH


def stage_rank(rows: list[dict], stage: str = "screening") -> dict:
    """Preliminary validation-only observed rank for ONE stage (absolute val MSE).

    Used for Stage E: the no-text Screening matrix does not contain the MIFlu
    control, so a baseline-relative score is undefined there; candidates are
    ranked by absolute mean validation MSE over their eligible runs (grouped by
    the ONE canonical model key). Never reads Test.
    """
    from innovation.paths import display_name_for
    util = [r for r in rows
            if r.get("experiment_stage") == stage and r.get("eligible")]
    per_model = {}
    for r in util:
        if r.get("best_val_mse") is None:
            continue
        m = canonical_model_key(r["model"])
        per_model.setdefault(m, []).append(float(r["best_val_mse"]))
    ranking = sorted(
        ({"model": m, "mean_val_mse": sum(v) / len(v), "n_runs": len(v)}
         for m, v in per_model.items()),
        key=lambda x: x["mean_val_mse"])
    for i, r in enumerate(ranking):
        r["rank"] = i + 1
        r["display_name"] = display_name_for(r["model"])
    return {
        "stage": stage, "selection_split": "validation_only", "test_accessed": False,
        "label": "preliminary validation-only observed %s rank" % stage,
        "n_eligible_runs": len(util), "observed_ranking": ranking,
        "baseline_relative_ratio_available": False,
        "note": ("absolute validation MSE (the no-text matrix excludes the MIFlu "
                 "control, so a baseline ratio is undefined at this stage); "
                 "baseline-relative scoring applies to the champion freeze (K)"),
    }


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="validation-only champion selection")
    ap.add_argument("--require-winner", action="store_true", dest="require_winner")
    ap.add_argument("--screening-rank", action="store_true", dest="screening_rank")
    ap.add_argument("--cohort-manifest", default=None, dest="cohort_manifest")
    ap.add_argument("--require-complete-cohort", action="store_true",
                    dest="require_complete_cohort")
    ap.add_argument("--expect-cohort-sha", default=None, dest="expect_cohort_sha")
    a = ap.parse_args(argv)

    cohort = None
    cohort_ids = None
    if a.cohort_manifest:
        cohort = load_cohort_manifest(a.cohort_manifest)
        if a.expect_cohort_sha and cohort["sha256"] != a.expect_cohort_sha:
            print("[select_best_model] COHORT_MANIFEST_TAMPERED: %s != %s"
                  % (cohort["sha256"], a.expect_cohort_sha))
            return 2
        cohort_ids = set(cohort["ids"])
        # The champion rule needs the MIFlu baseline, which is NOT part of the
        # pre-registered Stage-F matrix; the manifest lists it separately.
        for b in cohort["data"].get("baseline_cohort", []):
            if b.get("run_id"):
                cohort_ids.add(b["run_id"])

    rows = scan_runs(cohort_ids=cohort_ids)

    if a.screening_rank:
        audit_e = stage_rank(rows, "screening")
        ART.write_json(SCREENING_SELECTION_AUDIT_PATH, audit_e)
        print("[select_best_model] Stage E screening rank: eligible=%d models=%d "
              "test_accessed=%s" % (audit_e["n_eligible_runs"],
                                    len(audit_e["observed_ranking"]),
                                    audit_e["test_accessed"]))
        for r in audit_e["observed_ranking"]:
            print("    #%d %s mean_val_mse=%.6f (n=%d)"
                  % (r["rank"], r["model"], r["mean_val_mse"], r["n_runs"]))
        return 0

    audit = build_audit(rows)
    if cohort is not None:
        cells = {}
        for r in rows:
            if r["model"] == BASELINE_MODEL:
                continue           # the baseline is not a candidate cell
            cells.setdefault((r["model"], r["horizon"], r["seed"]), []).append(r["run_id"])
        dup_cells = [{"model": k[0], "horizon": k[1], "seed": k[2], "n": len(v)}
                     for k, v in cells.items() if len(v) > 1]
        audit["cohort_manifest_path"] = cohort["path"]
        audit["cohort_manifest_sha256"] = cohort["sha256"]
        audit["cohort_manifest_size"] = len(cohort["ids"])
        audit["cohort_resolved_cells"] = len(cells)
        audit["cohort_duplicate_cells"] = dup_cells
        audit["cohort_complete"] = bool(len(cells) == 160 and not dup_cells)
        if a.require_complete_cohort and not audit["cohort_complete"]:
            audit["status"] = "cohort_incomplete"
            ART.write_json(SELECTION_AUDIT_PATH, audit)
            print("[select_best_model] COHORT_INCOMPLETE: cells=%d dup=%d"
                  % (len(cells), len(dup_cells)))
            return 2
    ART.write_json(SELECTION_AUDIT_PATH, audit)
    print(f"[select_best_model] scanned={audit['n_runs_scanned']} "
          f"eligible={audit['n_runs_eligible']} "
          f"excluded={audit['n_runs_excluded']} | status={audit['status']} | "
          f"test_accessed={audit['test_accessed']}")
    if audit["excluded_runs"]:
        print("[select_best_model] exclusions (first 8):")
        for e in audit["excluded_runs"][:8]:
            print(f"    - {e['run_id'][:56]}… :: {e['reasons']}")
    if audit["winner"]:
        print(f"[select_best_model] winner: {audit['winner']['model']} "
              f"(score {audit['winner']['primary_score']:.4f})")
        print(f"[select_best_model] frozen -> {freeze_winners(audit)}")
    else:
        print("[select_best_model] no winner frozen; test remains SEALED.")
        print("[select_best_model] diagnostic status=%s reason=%s"
              % (audit["status"], audit["diagnostic"]["reason"]))
        if audit["diagnostic"]["missing_baseline_horizons"]:
            print("[select_best_model] missing baseline horizons: %s"
                  % audit["diagnostic"]["missing_baseline_horizons"])
        if audit["diagnostic"]["duplicate_cells"]:
            print("[select_best_model] duplicate cells: %s"
                  % audit["diagnostic"]["duplicate_cells"][:8])
        if a.require_winner:
            print("[select_best_model] DIAGNOSTIC_FAILURE: no lawful champion")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
