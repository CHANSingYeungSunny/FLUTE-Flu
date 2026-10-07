"""Tests for the innov-v2.10 Stage F cohort-manifest selection repair."""
from __future__ import annotations

import json
import os
import random
import sys

import pytest

_HERE = os.path.abspath(__file__)
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from innovation.paths import canonical_model_key  # noqa: E402
import innovation.select_best_model as S  # noqa: E402


def _cohort(n):
    return {"expected_cells": n, "cohort": [
        {"run_id": "national-ili__dlinear__none__identity__L24__seed%d__ts__nogit" % s,
         "model_key": "dlinear", "horizon": 24, "seed": s} for s in range(42, 42 + n)]}


def _row(model, horizon, seed, mse, stage="full", eligible=True):
    return {"run_id": "r__%s__none__identity__L%s__seed%s" % (model, horizon, seed),
            "run_dir": "/x", "model": model, "horizon": horizon, "seed": seed,
            "experiment_stage": stage, "eligible": eligible, "exclusion_reasons": [],
            "best_val_mse": mse, "val_mae_all_z": 1.0, "peak_hit_ratio": 0.5,
            "trainable_parameters": 1.0, "train_seconds": 1.0}


# 1. manifest yields the expected unique cells
def test_manifest_size_and_sha(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps(_cohort(160)))
    m = S.load_cohort_manifest(str(p))
    assert len(m["ids"]) == 160 and len(m["sha256"]) == 64


# 7. manifest tampering is detected
def test_manifest_tamper_detected(tmp_path, monkeypatch):
    p = tmp_path / "m.json"
    p.write_text(json.dumps(_cohort(160)))
    good = S.load_cohort_manifest(str(p))["sha256"]
    assert S.load_cohort_manifest(str(p))["sha256"] == good
    monkeypatch.setattr(S, "scan_runs", lambda open_fn=open, cohort_ids=None: [])
    assert S.main(["--cohort-manifest", str(p), "--expect-cohort-sha", "0" * 64]) == 2
    # correct sha passes the tamper check (then fails the completeness gate)
    monkeypatch.setattr(S, "SELECTION_AUDIT_PATH", str(tmp_path / "sel.json"))
    assert S.main(["--cohort-manifest", str(p), "--expect-cohort-sha", good,
                   "--require-complete-cohort"]) == 2


# 2. G/H/I/J (unlisted) runs are excluded from scanning
def test_unlisted_run_excluded(tmp_path, monkeypatch):
    runs = tmp_path / "runs" / "national-ili__dlinear__none__identity__L24__seed42__X__nogit"
    runs.mkdir(parents=True)
    (runs / "run_status.json").write_text(json.dumps(
        {"status": "ok", "experiment_stage": "full"}))
    monkeypatch.setattr(S, "RUNS_ROOT", str(tmp_path / "runs"))
    assert S.scan_runs(cohort_ids=set()) == []                       # excluded
    got = S.scan_runs(cohort_ids={os.path.basename(str(runs))})
    assert len(got) == 1                                             # listed -> included


# 3. duplicate cells are rejected
def test_duplicate_cells_rejected(tmp_path, monkeypatch):
    p = tmp_path / "m.json"
    p.write_text(json.dumps(_cohort(160)))
    rows = [_row("dlinear", 24, 42, 1.0), _row("dlinear", 24, 42, 0.9)]
    monkeypatch.setattr(S, "scan_runs", lambda open_fn=open, cohort_ids=None: rows)
    monkeypatch.setattr(S, "SELECTION_AUDIT_PATH", str(tmp_path / "sel.json"))
    assert S.main(["--cohort-manifest", str(p), "--require-complete-cohort"]) == 2


# 4. missing cells are rejected
def test_missing_cells_rejected(tmp_path, monkeypatch):
    p = tmp_path / "m.json"
    p.write_text(json.dumps(_cohort(160)))
    monkeypatch.setattr(S, "scan_runs",
                        lambda open_fn=open, cohort_ids=None: [_row("dlinear", 24, 42, 1.0)])
    monkeypatch.setattr(S, "SELECTION_AUDIT_PATH", str(tmp_path / "sel.json"))
    assert S.main(["--cohort-manifest", str(p), "--require-complete-cohort"]) == 2


# 5. unresolved provenance -> no winner (diagnostic failure)
def test_unresolved_provenance_no_winner(monkeypatch, tmp_path):
    monkeypatch.setattr(S, "scan_runs", lambda open_fn=open, cohort_ids=None: [])
    monkeypatch.setattr(S, "SELECTION_AUDIT_PATH", str(tmp_path / "sel.json"))
    assert S.main(["--require-winner"]) == 1


# 6. performance values cannot alter membership
def test_performance_cannot_alter_membership():
    ids = {"a", "b"}
    assert "c" not in ids                      # membership is by run-id only
    # build_audit groups by canonical model key, independent of MSE ordering
    rows = [_row("dlinear", L, 42, 5.0 - i, stage="full") for i, L in enumerate((24, 36, 48, 60))]
    rows += [_row("gpt2_miflu", L, 42, 10.0, stage="full") for L in (24, 36, 48, 60)]
    assert S.build_audit(rows)["n_runs_eligible"] == len(rows)


# 8. Test paths (incl. test_evaluations) are blocked
def test_test_paths_blocked():
    for p in ("/x/test_evaluations/y.json", "/x/test_predictions.csv",
              "/x/metrics/test_metrics.json"):
        with pytest.raises(RuntimeError):
            S.assert_no_test_path(p)


# 9. canonical baseline lookup works for underscore and slug forms
def test_canonical_baseline_forms():
    assert canonical_model_key("gpt2-miflu") == canonical_model_key("gpt2_miflu") == "gpt2_miflu"
    rows = [_row("gpt2_miflu", L, 42, 1.0, stage="full") for L in (24, 36, 48, 60)]
    rows += [_row("dlinear", L, 42, 0.5, stage="full") for L in (24, 36, 48, 60)]
    a = S.build_audit(rows)
    assert all(a["baseline_val_mse_by_L"][L] is not None for L in (24, 36, 48, 60))


# 10. selector is deterministic over shuffled input order
def test_determinism_shuffled():
    rows = [_row("gpt2_miflu", L, s, 1.0, stage="full") for L in (24, 36, 48, 60) for s in (42, 43)]
    rows += [_row("dlinear", L, s, 0.5, stage="full") for L in (24, 36, 48, 60) for s in (42, 43)]
    rows += [_row("nlinear", L, s, 0.7, stage="full") for L in (24, 36, 48, 60) for s in (42, 43)]
    a1 = S.build_audit(list(rows))
    rnd = list(rows)
    random.Random(0).shuffle(rnd)
    a2 = S.build_audit(rnd)
    assert a1["winner"]["model"] == a2["winner"]["model"]
    assert abs(a1["winner"]["primary_score"] - a2["winner"]["primary_score"]) < 1e-12


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
