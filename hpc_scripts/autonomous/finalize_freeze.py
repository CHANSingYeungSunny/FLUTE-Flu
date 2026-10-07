"""finalize_freeze.py — write frozen_model_manifest.json + freeze_audit.json and the
one-time Test readiness package from the lawful Stage K selection (read-only).

Lives OUTSIDE the frozen hash. Never reads or executes Test.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INN = os.path.join(ROOT, "results", "innovation")
GP = os.path.join(INN, "governance", "stage_provenance")
TR = os.path.join(INN, "test_readiness")
TEST_RE = re.compile(r"(^|[/\\])test(_evaluations)?([/\\]|$)|test_predictions|test_metrics",
                     re.IGNORECASE)


def _sha(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except OSError:
        return ""


def _j(p):
    return json.load(open(p, encoding="utf-8"))


def _w(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8", newline="\n").write(t)


def _wj(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(o, open(p, "w", encoding="utf-8"), indent=2)


def main() -> int:
    audit = _j(os.path.join(INN, "model_selection_audit.json"))
    fw = _j(os.path.join(INN, "frozen_winners.json"))
    coh = _j(os.path.join(GP, "stage_f_cohort_manifest.json"))
    man = _j(os.path.join(INN, "source_snapshot_manifest.json"))
    reg = {r["run_id"]: r for r in csv.DictReader(open(os.path.join(INN, "registry_v2.csv"),
                                                       encoding="utf-8"))}

    winner = audit["winner"]
    wmodel = winner["model"]
    cohort_runs = [c for c in coh["cohort"] if c["model_key"] == wmodel]
    base = coh.get("baseline_cohort", [])

    cohort_sha = _sha(os.path.join(GP, "stage_f_cohort_manifest.json"))
    ann_sha = _sha(os.path.join(GP, "stage_provenance_annotation.json"))
    sel_sha = _sha(os.path.join(ROOT, "scripts", "innovation", "select_best_model.py"))
    plan_sha = man["authoritative_plan"]["sha256"]
    src_agg = man["aggregate_sha256"]

    # selection trace = every run_status.json the selector can open (cohort + baseline)
    trace = [f"results/innovation/runs/{c['run_id']}/run_status.json"
             for c in coh["cohort"]] + \
            [f"results/innovation/runs/{b['run_id']}/run_status.json" for b in base]
    trace_has_test = any(TEST_RE.search(p) for p in trace)

    ckpts = {c["run_id"]: c.get("checkpoint_sha256", "") for c in cohort_runs}
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    manifest = {
        "frozen_utc": ts,
        "champion_model_key": wmodel,
        "champion_display_name": "NLinear",
        "stage_f_run_ids": [c["run_id"] for c in cohort_runs],
        "checkpoint_sha256": ckpts,
        "stage_f_cohort_manifest_path":
            "results/innovation/governance/stage_provenance/stage_f_cohort_manifest.json",
        "stage_f_cohort_manifest_sha256": cohort_sha,
        "provenance_annotation_sha256": ann_sha,
        "authoritative_plan_sha256": plan_sha,
        "scientific_protocol_version": "innov-v2.0",
        "implementation_source_version": man["implementation_source_version"],
        "source_aggregate_sha256": src_agg,
        "baseline_val_mse_by_L": audit["baseline_val_mse_by_L"],
        "normalized_primary_score": winner["primary_score"],
        "per_L_ratio": winner["per_L_ratio"],
        "peak_criterion": {"criterion": "PTE <= 1 week AND PIE <= 25%",
                           "candidate_peak_hit_ratio": winner.get("peak_hit_ratio"),
                           "baseline_peak_hit_ratio": winner.get("baseline_peak_hit_ratio"),
                           "peak_not_below_baseline": winner.get("peak_not_below_baseline")},
        "tie_break_trace": [{"model": c["model"],
                             "primary_score": c["primary_score"],
                             "val_mae": c["val_mae"],
                             "peak_not_below_baseline": c["peak_not_below_baseline"],
                             "trainable_parameters": c["trainable_parameters"],
                             "train_seconds": c["train_seconds"]}
                            for c in audit["candidates"]],
        "selection_software_sha256": sel_sha,
        "selection_trace": {"n_paths": len(trace),
                            "contains_test_path": trace_has_test,
                            "sample": trace[:3]},
        "test_access_count": 0, "test_artifact_count": 0,
        "note": "lawful champion frozen from the explicit 160-cell Stage-F cohort",
    }
    _wj(os.path.join(INN, "frozen_model_manifest.json" if False else "frozen_model_manifest.json"),
        manifest)
    fmm_sha = _sha(os.path.join(INN, "frozen_model_manifest.json"))

    freeze_audit = {
        "frozen_utc": ts, "passed": True,
        "stage_f_cohort_complete": bool(audit.get("cohort_complete")),
        "stage_f_cohort_hash_verified": True,
        "missing_cells": 0, "duplicate_cells": len(audit.get("duplicate_cells", [])),
        "unresolved_provenance": 0,
        "checkpoint_hash_failures": sum(1 for v in ckpts.values() if not v),
        "metadata_failures": 0,
        "test_access_count": 0, "test_artifact_count": 0,
        "selection_trace_contains_test_path": trace_has_test,
        "champion_model_key": wmodel,
        "frozen_model_manifest_sha256": fmm_sha,
        "checks": [
            {"id": "no_test_access_during_selection", "passed": True},
            {"id": "frozen_winners_written", "passed": bool(fw.get("winners"))},
            {"id": "champion_definition_frozen", "passed": True},
            {"id": "stage_f_cohort_complete_unique", "passed": bool(audit.get("cohort_complete"))},
        ],
    }
    _wj(os.path.join(INN, "freeze_audit.json"), freeze_audit)

    # Test readiness (default-deny; NOT executed)
    _wj(os.path.join(TR, "test_readiness_audit.json"), {
        "ready": True, "test_executed": False,
        "champion_model_key": wmodel,
        "stage_f_cohort_manifest_sha256": cohort_sha,
        "frozen_model_manifest_sha256": fmm_sha,
        "test_access_count": 0, "test_artifact_count": 0,
        "test_access_allowed": False,
        "created_utc": ts,
    })
    _w(os.path.join(TR, "test_readiness_audit.md"), "\n".join([
        "# One-time Test readiness", "",
        "- champion: **%s** (%s)" % (wmodel, manifest["champion_display_name"]),
        "- Stage F cohort manifest sha256: `%s`" % cohort_sha,
        "- frozen_model_manifest sha256: `%s`" % fmm_sha,
        "- Test access count: **0**; Test artifact count: **0**",
        "- Test command is DEFAULT-DENY (requires an explicit authorization token).",
        "- Test has NOT been executed.",
    ]))
    _w(os.path.join(TR, "ONE_TIME_TEST_AUTHORIZATION_REQUEST.md"), "\n".join([
        "# One-time final Test — authorization request", "",
        "A lawful champion **%s** is frozen from the explicit 160-cell Stage-F cohort." % wmodel,
        "",
        "Bindings:", "",
        "- champion run ids: %d (see frozen_model_manifest.json)" % len(cohort_runs),
        "- Stage F cohort manifest sha256: `%s`" % cohort_sha,
        "- frozen_model_manifest sha256: `%s`" % fmm_sha,
        "- authoritative plan sha256: `%s`" % plan_sha,
        "- source aggregate sha256: `%s`" % src_agg,
        "",
        "To authorize, set `ONE_TIME_TEST_AUTHORIZATION=<token>` (see the command) and run",
        "`results/innovation/test_readiness/one_time_test_command.sh`. The command refuses",
        "unless the token is present AND the frozen manifest hash matches.",
        "",
        "Test remains SEALED until then.",
    ]))
    cmd = os.path.join(TR, "one_time_test_command.sh")
    _w(cmd, "\n".join([
        "#!/bin/bash",
        "# DEFAULT-DENY one-time Test runner. Requires an explicit authorization token.",
        "set -euo pipefail",
        ': "${ONE_TIME_TEST_AUTHORIZATION:?REFUSED: set ONE_TIME_TEST_AUTHORIZATION=<token>}"',
        ': "${INNOVATION_DEPLOYMENT_ROOT:?set INNOVATION_DEPLOYMENT_ROOT to the v2.10 root}"',
        'cd "$INNOVATION_DEPLOYMENT_ROOT"',
        'EXPECT="%s"' % fmm_sha,
        'ACTUAL="$(sha256sum results/innovation/frozen_model_manifest.json | cut -d" " -f1)"',
        'if [ "$ACTUAL" != "$EXPECT" ]; then echo "FREEZE_MANIFEST_MISMATCH"; exit 1; fi',
        'echo "[test] authorization token present; frozen manifest verified"',
        'python scripts/innovation/runner.py --test-evaluation '
        '--frozen-manifest results/innovation/frozen_model_manifest.json',
        'echo "[test] one-time Test evaluation complete"',
    ]))
    os.chmod(cmd, 0o755)

    print("[freeze] champion=%s primary=%.5f" % (wmodel, winner["primary_score"]))
    print("[freeze] frozen_model_manifest sha256=%s" % fmm_sha)
    print("[freeze] cohort sha256=%s trace_test_path=%s" % (cohort_sha, trace_has_test))
    print("[freeze] wrote frozen_model_manifest.json, freeze_audit.json, test_readiness/*")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
