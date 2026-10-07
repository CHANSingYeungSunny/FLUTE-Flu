"""
Metadata chain tests (innov-v2.3)
=================================

Covers: five-layer presence/agreement, fail-closed defaults, test-access rules,
legacy registry immutability, selector exclusion, registry_v2 append-only and
duplicate-run_id rejection.
"""

from __future__ import annotations

import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402

from innovation import run_artifacts as ART  # noqa: E402
from innovation import select_best_model as SBM  # noqa: E402
from innovation.paths import (FAIL_CLOSED_FALSE_FIELDS,  # noqa: E402
                              IMPLEMENTATION_SOURCE_VERSION,
                              INNOVATION_ROOT, PROJECT_ROOT, PROTOCOL_VERSION,
                              REQUIRED_METADATA_FIELDS, STAGE_PURPOSE,
                              assert_test_access_gate, fail_closed_bool,
                              governance_fields)

PILOT_SPECS = os.path.join(PROJECT_ROOT, "hpc_scripts", "pilot_specs.json")
LEGACY_REGISTRY = os.path.join(INNOVATION_ROOT, "registry.csv")


# 1-2 ────────────────────────────────────────────────────────────────────────
def test_governance_fields_pilot_values():
    g = governance_fields(stage="pilot", model_key="dlinear")
    for f in REQUIRED_METADATA_FIELDS:
        assert f in g, f"missing governance field {f}"
    assert g["experiment_stage"] == "pilot"
    assert g["purpose"] == "infrastructure_verification_only"
    assert g["selection_eligible"] is False
    assert g["paper_result_eligible"] is False
    assert g["test_access_allowed"] is False
    assert g["protocol_version"] == PROTOCOL_VERSION == "innov-v2.0"
    assert g["implementation_source_version"] == IMPLEMENTATION_SOURCE_VERSION
    assert g["model_key"] == "dlinear"


def test_smoke_and_screening_defaults():
    s = governance_fields(stage="smoke", model_key="dlinear")
    assert s["purpose"] == STAGE_PURPOSE["smoke"]
    assert s["selection_eligible"] is False
    assert s["paper_result_eligible"] is False
    assert s["test_access_allowed"] is False
    f = governance_fields(stage="full", model_key="dlinear")
    assert f["selection_eligible"] is True and f["paper_result_eligible"] is True
    assert f["test_access_allowed"] is False


# 3-5 ────────────────────────────────────────────────────────────────────────
def test_pilot_specs_carry_every_governance_field():
    with open(PILOT_SPECS, "r", encoding="utf-8") as f:
        d = json.load(f)
    assert len(d["specs"]) == 4
    assert [s["model"] for s in d["specs"]] == [
        "gpt2_miflu", "dlinear", "patchtst", "itransformer"]
    for s in d["specs"]:
        for fld in REQUIRED_METADATA_FIELDS:
            assert fld in s, f"spec {s['model']} missing {fld}"
        assert s["experiment_stage"] == "pilot"
        assert s["purpose"] == "infrastructure_verification_only"
        assert s["selection_eligible"] is False
        assert s["paper_result_eligible"] is False
        assert s["test_access_allowed"] is False
        assert s["protocol_version"] == "innov-v2.0"
        assert s["implementation_source_version"] == IMPLEMENTATION_SOURCE_VERSION
        assert s["source_snapshot_sha256"], "source snapshot hash must be filled"
        assert s["authoritative_plan_sha256"].startswith("aa4ab1c8")
        assert s["display_name"] and s["architecture_fidelity"]


# 6 ──────────────────────────────────────────────────────────────────────────
def test_missing_governance_fields_fail_closed():
    empty = {}
    for f in FAIL_CLOSED_FALSE_FIELDS:
        assert fail_closed_bool(empty, f) is False, f
    assert fail_closed_bool({"selection_eligible": None}, "selection_eligible") is False
    assert fail_closed_bool({"selection_eligible": "True"}, "selection_eligible") is True
    assert fail_closed_bool({"test_access_allowed": "false"},
                            "test_access_allowed") is False


# 7-9 ────────────────────────────────────────────────────────────────────────
def test_test_access_rejected_for_non_test_stages():
    for stage in ("pilot", "smoke", "screening", "full", "adhoc", "validation"):
        try:
            governance_fields(stage=stage, model_key="dlinear",
                              test_access_allowed=True)
        except ValueError as e:
            assert "INVALID_TEST_ACCESS_FOR_EXPERIMENT_STAGE" in str(e), e
        else:
            raise AssertionError(f"{stage} must reject test access")


# 10 ─────────────────────────────────────────────────────────────────────────
def test_test_access_without_frozen_winner_fails():
    for kw in ({"frozen_winner_manifest_exists": False,
                "checkpoint_hash_matches": True,
                "explicit_test_gate_authorized": True},
               {"frozen_winner_manifest_exists": True,
                "checkpoint_hash_matches": False,
                "explicit_test_gate_authorized": True},
               {"frozen_winner_manifest_exists": True,
                "checkpoint_hash_matches": True,
                "explicit_test_gate_authorized": False}):
        try:
            assert_test_access_gate(**kw)
        except RuntimeError as e:
            assert "TEST_GATE_NOT_AUTHORIZED" in str(e)
        else:
            raise AssertionError(f"gate must fail for {kw}")
    assert_test_access_gate(frozen_winner_manifest_exists=True,
                            checkpoint_hash_matches=True,
                            explicit_test_gate_authorized=True)


# 11 ─────────────────────────────────────────────────────────────────────────
def test_legacy_registry_rows_unchanged_and_ineligible():
    with open(LEGACY_REGISTRY, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 14, f"legacy registry must keep 14 rows, got {len(rows)}"
    cols = list(rows[0].keys())
    assert cols == ART.REGISTRY_COLUMNS, "legacy schema must not be widened"
    for r in rows:
        for f in ("experiment_stage", "selection_eligible",
                  "paper_result_eligible", "test_access_allowed"):
            assert f not in cols, "legacy rows must not gain governance columns"


# 12 ─────────────────────────────────────────────────────────────────────────
def test_selector_excludes_smoke_and_pilot():
    rows = SBM.scan_runs()
    eligible = {r["run_id"] for r in rows if r["eligible"]}
    assert eligible == set(), f"no run may be eligible yet: {eligible}"
    audit = SBM.build_audit(rows)
    assert audit["test_accessed"] is False
    joined = " ".join(" ".join(e["reasons"]) for e in audit["excluded_runs"])
    for token in ("stage_not_eligible", "smoke_only", "selection_eligible"):
        assert token in joined, (token, joined)


# 19-20 ──────────────────────────────────────────────────────────────────────
def test_ordinary_runs_create_no_test_artifacts_and_seal_holds():
    runs_root = os.path.join(INNOVATION_ROOT, "runs")
    hits = []
    for root, _dirs, files in os.walk(runs_root):
        for fn in files:
            if fn.startswith("test_") or fn in ("test_metrics.json",
                                                "test_predictions.csv"):
                hits.append(os.path.join(root, fn))
    assert not hits, hits
    assert not os.path.exists(os.path.join(INNOVATION_ROOT,
                                           "frozen_winners.json"))
    tev = os.path.join(INNOVATION_ROOT, "test_evaluations")
    assert (not os.path.isdir(tev)) or not os.listdir(tev)


# 21-22 ──────────────────────────────────────────────────────────────────────
def test_registry_v2_append_only_and_rejects_duplicates():
    path = ART.REGISTRY_V2_PATH
    if not os.path.exists(path):
        print("[skip] registry_v2.csv not created yet")
        return
    with open(path, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ids = [r["run_id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate run_id in registry_v2"
    for r in rows:
        for fld in REQUIRED_METADATA_FIELDS:
            assert fld in r, f"registry_v2 missing column {fld}"
        assert fail_closed_bool(r, "test_access_allowed") is False
        if r.get("experiment_stage") in ("pilot", "smoke"):
            assert fail_closed_bool(r, "selection_eligible") is False
            assert fail_closed_bool(r, "paper_result_eligible") is False


# 1-2 (five layers) ──────────────────────────────────────────────────────────
def test_five_layer_chain_report_is_complete():
    rep = os.path.join(INNOVATION_ROOT, "audit",
                       "runtime_metadata_chain_report.json")
    if not os.path.exists(rep):
        print("[skip] runtime_metadata_chain_report.json not generated yet")
        return
    with open(rep, "r", encoding="utf-8") as f:
        d = json.load(f)
    assert d["runtime_metadata_chain_complete"] is True, [
        (e["field"], e["layers_missing"], e["distinct_values"])
        for e in d["fields"] if not e["agree"]]
    assert len(d["fields"]) == len(REQUIRED_METADATA_FIELDS)


if __name__ == "__main__":
    test_governance_fields_pilot_values()
    test_smoke_and_screening_defaults()
    test_pilot_specs_carry_every_governance_field()
    test_missing_governance_fields_fail_closed()
    test_test_access_rejected_for_non_test_stages()
    test_test_access_without_frozen_winner_fails()
    test_legacy_registry_rows_unchanged_and_ineligible()
    test_selector_excludes_smoke_and_pilot()
    test_ordinary_runs_create_no_test_artifacts_and_seal_holds()
    test_registry_v2_append_only_and_rejects_duplicates()
    test_five_layer_chain_report_is_complete()
    print("[test_metadata_chain] OK")
