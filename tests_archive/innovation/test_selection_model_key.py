"""Tests for the innov-v2.9 model-key normalisation repair (select_best_model).

Covers the 10 behaviours required by the v2.9 repair prompt. The selection logic
lives in the frozen source set, so these tests are part of the v2.9 cascade.
"""
from __future__ import annotations

import os
import sys

import pytest

_HERE = os.path.abspath(__file__)
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from innovation.paths import canonical_model_key  # noqa: E402
import innovation.select_best_model as S  # noqa: E402


def _row(model, horizon, seed, mse, stage="screening", eligible=True, peak=0.0,
         mae=1.0, params=1000.0, secs=1.0):
    return {"run_id": "r__%s__none__identity__L%s__seed%s" % (model, horizon, seed),
            "run_dir": "/x", "model": model, "horizon": horizon, "seed": seed,
            "experiment_stage": stage, "eligible": eligible,
            "exclusion_reasons": [] if eligible else ["x"],
            "best_val_mse": mse, "val_mae_all_z": mae, "peak_hit_ratio": peak,
            "trainable_parameters": params, "train_seconds": secs}


# 1. one canonical key for every spelling
def test_canonical_key_equivalence():
    assert canonical_model_key("gpt2-miflu") == "gpt2_miflu"
    assert canonical_model_key("gpt2_miflu") == "gpt2_miflu"
    assert canonical_model_key("gpt2-miflu") == canonical_model_key("gpt2_miflu")
    assert canonical_model_key("Some_New-Model") == "Some-New-Model"  # stable slug


# 2. baseline validation MSE found for every required horizon
def test_baseline_found_every_horizon():
    rows = []
    for L in (24, 36, 48, 60):
        rows.append(_row("gpt2_miflu", L, 42, 1.0, stage="full"))
        rows.append(_row("dlinear", L, 42, 0.5, stage="full"))
    audit = S.build_audit(rows)
    for L in (24, 36, 48, 60):
        assert audit["baseline_val_mse_by_L"][L] is not None
    assert audit["status"] == "ok"
    assert audit["winner"]["model"] == "dlinear"


# 3. grouping does not split underscore / hyphen spellings
def test_grouping_not_split_by_spelling():
    rows = [_row("gpt2-miflu", 24, 42, 1.0, stage="screening"),
            _row("gpt2_miflu", 24, 43, 1.2, stage="screening")]
    a = S.stage_rank(rows, "screening")
    assert len(a["observed_ranking"]) == 1     # ONE canonical model
    assert a["observed_ranking"][0]["n_runs"] == 2


# 4. legacy / ineligible runs fail closed
def test_legacy_ineligible_fails_closed():
    st = {"status": "ok", "experiment_stage": "full",
          "protocol_version": S.PROTOCOL_VERSION, "selection_eligible": False}
    ok, reasons = S._eligibility_verdict(st, "rid", {})
    assert ok is False and reasons


# 5. screening / full / later eligible runs stay distinct by stage
def test_stages_distinct():
    rows = [_row("dlinear", 24, 42, 0.5, stage="screening"),
            _row("dlinear", 24, 42, 0.4, stage="full")]
    assert S.stage_rank(rows, "screening")["n_eligible_runs"] == 1
    assert S.stage_rank(rows, "full")["n_eligible_runs"] == 1


# 6. selector reads validation artifacts only
def test_selector_reads_validation_only():
    S.assert_no_test_path("/data/predictions/validation_predictions.csv")  # ok
    with pytest.raises(RuntimeError):
        S.assert_no_test_path("/data/test_predictions.csv")


# 7. any attempted Test read fails
def test_test_read_fails():
    with pytest.raises(RuntimeError):
        S._read_json("/runs/x/metrics/test_metrics.json")
    with pytest.raises(RuntimeError):
        S._read_json("/runs/test_evaluations/y.json")


# 8. missing baseline horizon fails explicitly
def test_missing_baseline_horizon_explicit():
    rows = [_row("gpt2_miflu", 24, 42, 1.0, stage="full"),
            _row("dlinear", 24, 42, 0.5, stage="full")]
    audit = S.build_audit(rows)
    assert audit["status"] == "baseline_horizon_missing"
    assert set(audit["diagnostic"]["missing_baseline_horizons"]) == {36, 48, 60}


# 9. duplicate cells fail explicitly
def test_duplicate_cells_explicit():
    rows = [_row("gpt2_miflu", L, 42, 1.0, stage="full") for L in (24, 36, 48, 60)]
    rows += [_row("gpt2_miflu", 24, 42, 1.1, stage="full")]      # duplicate cell
    rows += [_row("dlinear", L, 42, 0.5, stage="full") for L in (24, 36, 48, 60)]
    audit = S.build_audit(rows)
    assert any(d["model"] == "gpt2_miflu" and d["horizon"] == 24 and d["seed"] == 42
               for d in audit["diagnostic"]["duplicate_cells"])


# 10. no eligible candidate -> diagnostic failure (non-zero), not empty success
def test_no_candidate_diagnostic_failure(tmp_path, monkeypatch):
    rows = [_row("gpt2_miflu", L, 42, 1.0, stage="full") for L in (24, 36, 48, 60)]
    monkeypatch.setattr(S, "scan_runs", lambda open_fn=open, cohort_ids=None: rows)
    monkeypatch.setattr(S, "SELECTION_AUDIT_PATH", str(tmp_path / "sel.json"))
    assert S.main(["--require-winner"]) == 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
