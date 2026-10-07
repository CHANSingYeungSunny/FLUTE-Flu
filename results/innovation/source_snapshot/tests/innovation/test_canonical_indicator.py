"""
Canonical indicator tests (innov-v2.3)
======================================

The adopted script is PROSPECTIVE: its exact hash is pinned and it must
reproduce the accepted reproduction metrics. No claim of pre-incident byte
identity is made anywhere.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402

from innovation.paths import (CANONICAL_INDICATOR_REL,  # noqa: E402
                              GOVERNANCE_DIR, PROJECT_ROOT)

ADOPTION = os.path.join(GOVERNANCE_DIR, "canonical_indicator_adoption.json")
REGRESSION = os.path.join(GOVERNANCE_DIR, "canonical_indicator_regression.json")
COPY = os.path.join(GOVERNANCE_DIR, "canonical_indicator_script.py")
SHA_FILE = os.path.join(GOVERNANCE_DIR, "canonical_indicator_script.sha256")


def _sha256(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _require(path: str) -> dict:
    assert os.path.exists(path), f"missing governance artifact: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_adoption_record_exists_and_is_honest():
    d = _require(ADOPTION)
    assert d["repository_relative_path"] == CANONICAL_INDICATOR_REL
    assert len(d["sha256"]) == 64
    assert d["implementation_source_version_before_adoption"] == "innov-v2.2"
    assert d["historical_integrity_status"] == "UNRESOLVED"
    assert ("could not be established" in d["historical_integrity_statement"])
    assert d["no_preincident_byte_identity_claim"] is True
    assert "No claim is made that it is byte-identical" in d["declaration"]
    assert "must not be represented as proven identical" in \
        d["prohibited_interpretation"]


def test_canonical_copy_hash_matches():
    d = _require(ADOPTION)
    live = _sha256(os.path.join(
        PROJECT_ROOT, CANONICAL_INDICATOR_REL.replace("/", os.sep)))
    assert live == d["sha256"], "adopted file changed after adoption"
    assert _sha256(COPY) == d["sha256"], "canonical copy does not match record"
    with open(SHA_FILE, "r", encoding="utf-8") as f:
        assert f.read().split()[0] == d["sha256"]
    assert d["canonical_copy_verified"] is True
    assert d["matches_local_working_copy"] is True


def test_regression_passed_and_used_trusted_predictions():
    d = _require(REGRESSION)
    assert d["trained_any_model"] is False
    assert d["innovation_test_artifacts_created"] is False
    assert d["stop_code"] is None, d["stop_code"]
    assert d["canonical_indicator_regression_passed"] is True
    files = d["trustworthy_prediction_files"]
    assert files and all(f["sha256"] and f["predates_incident"]
                         and f["eligible_for_regression_check"] for f in files)
    assert d["reference_sources"], "no reference provenance recorded"
    for row in d["comparisons"]:
        assert row["pass_fail"] in ("PASS", "REFERENCE_UNAVAILABLE"), row
        if row["pass_fail"] == "PASS":
            assert row["reference_provenance"]


def test_only_the_literature_peak_criterion_is_used():
    a = _require(ADOPTION)
    r = _require(REGRESSION)
    assert a["peak_criterion"]["criterion"] == "PTE <= 1 week AND PIE <= 25%"
    assert a["peak_criterion"]["pte_max_weeks"] == 1.0
    assert a["peak_criterion"]["pie_max_pct"] == 25.0
    assert "PTE <= 1.0 week AND PIE <= 25.0%" in r["peak_criterion"]


if __name__ == "__main__":
    test_adoption_record_exists_and_is_honest()
    test_canonical_copy_hash_matches()
    test_regression_passed_and_used_trusted_predictions()
    test_only_the_literature_peak_criterion_is_used()
    print("[test_canonical_indicator] OK")
