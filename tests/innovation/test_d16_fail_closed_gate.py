"""test_d16_fail_closed_gate.py — D16 regression tests.

The defect: the Gate wrote `canonical_invariant_vs_durable` into the storage
result while `storage_verdict` read the restoration result, and the missing
field defaulted to PASS. These tests prove the fail-closed contract and that
independent-training comparisons can never be labelled same_source.

v3.19 update: the schema is now ARM-AWARE (D15). Every check in the full
`REQUIRED_CHECKS` set must still be present — a missing check is a hard fail —
but the checkpoint-only checks carry an explicit `not_applicable` sentinel on a
deterministic baseline, and the baseline-only checks carry the same sentinel on
a stochastic row. The record below is a STOCHASTIC one (arm="primary"): common
and checkpoint-only checks are True, baseline-only checks are `not_applicable`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from innovation import storage_verification as SV        # noqa: E402
from innovation import same_source_invariant as SSI      # noqa: E402


def _checks(**over):
    c = {k: True for k in SV.COMMON_CHECKS + SV.CHECKPOINT_ONLY_CHECKS}
    c.update({k: SV.NOT_APPLICABLE for k in SV.BASELINE_ONLY_CHECKS})
    c.update(over)
    return c


def _evidence(**over):
    e = {"run_key": "k", "model": "nlinear", "horizon": 24,
         "file_sha256": "a" * 64, "canonical_tensor_sha256": "b" * 64,
         "canonical_hash_schema": "canonical-tensor-v1",
         "source_full_checkpoint_sha256": "c" * 64,
         "source_run_key": "k", "source_job_id": "1",
         "source_training_attempt": 1,
         "export_implementation_version": "v",
         "comparison_mode": "same_source",
         "reason": SV.NOT_APPLICABLE,
         "checkpoint_applicable": SV.NOT_APPLICABLE,
         "stochastic_seed_applicable": SV.NOT_APPLICABLE}
    e.update(over)
    return e


def _make(**ckw):
    arm = ckw.pop("arm", "primary")
    reason = ckw.pop("reason", None)
    return SV.StorageVerification(_checks(), _evidence(), arm=arm,
                                  reason=reason)


# ── the fail-closed contract ─────────────────────────────────────────────
def test_all_required_present_and_true_passes():
    sv = SV.StorageVerification(_checks(), _evidence(), arm="primary")
    assert sv.verdict() == (True, SV.OK, "")
    assert sv.passed is True


@pytest.mark.parametrize("missing", SV.REQUIRED_CHECKS)
def test_missing_required_check_fails_closed(missing):
    c = _checks()
    del c[missing]
    ok, code, detail = SV.StorageVerification(
        c, _evidence(), arm="primary").verdict()
    assert ok is False
    assert code == SV.MISSING
    assert "MISSING_REQUIRED_STORAGE_CHECK" == SV.MISSING
    assert missing in detail


def test_missing_required_evidence_fails_closed():
    e = _evidence()
    del e["source_job_id"]
    ok, code, detail = SV.StorageVerification(
        _checks(), e, arm="primary").verdict()
    assert ok is False and code == SV.MISSING and "source_job_id" in detail


@pytest.mark.parametrize("name", SV.REQUIRED_CHECKS)
def test_required_check_false_fails(name):
    ok, code, detail = SV.StorageVerification(
        _checks(**{name: False}), _evidence(), arm="primary").verdict()
    assert ok is False and code == SV.FAILED and name in detail


def test_unknown_check_id_is_rejected():
    with pytest.raises(SV.StorageVerificationError):
        SV.StorageVerification(_checks() | {"bogus_check": True},
                               _evidence(), arm="primary")


def test_non_boolean_check_values_are_rejected():
    with pytest.raises(SV.StorageVerificationError):
        SV.StorageVerification(_checks(**{"contained": 1}), _evidence(),
                               arm="primary")
    with pytest.raises(SV.StorageVerificationError):
        SV.StorageVerification(_checks(**{"contained": None}), _evidence(),
                               arm="primary")


def test_sentinel_out_of_place_is_rejected():
    """The `not_applicable` sentinel is only valid on the arm-appropriate
    side; a stochastic row cannot mark a COMMON check not_applicable."""
    with pytest.raises(SV.StorageVerificationError):
        SV.StorageVerification(_checks(**{"contained": SV.NOT_APPLICABLE}),
                               _evidence(), arm="primary")


def test_the_exact_d16_scenario_now_fails():
    """The old code put the canonical flag in `res` and read it from `rest`,
    defaulting to True. With the typed result the flag is a REQUIRED check, so
    omitting it fails instead of silently passing."""
    c = _checks()
    del c["same_source_invariant_ok"]          # as if written to the wrong dict
    ok, code, detail = SV.StorageVerification(c, _evidence(),
                                              arm="primary").verdict()
    assert ok is False and code == SV.MISSING


def test_verdict_accepts_only_the_authoritative_structure():
    assert SV.storage_verdict(
        SV.StorageVerification(_checks(), _evidence(), arm="primary")) is True
    # a serialized typed result still works
    assert SV.storage_verdict(
        SV.StorageVerification(_checks(), _evidence(),
                               arm="primary").to_dict()) is True
    # a "restoration-result-like" dict must NOT pass
    assert SV.storage_verdict({"restoration_exact": True,
                               "missing_keys": [], "unexpected_keys": []}) \
        is False
    assert SV.storage_verdict({}) is False
    assert SV.storage_verdict(None) is False


# ── no default-to-pass anywhere in the verdict path ──────────────────────
def test_no_default_true_lookup_in_verdict_path():
    src = (REPO / "scripts" / "innovation"
           / "storage_verification.py").read_text(encoding="utf-8")
    body = src.split("def verdict")[1].split("def ")[0]
    # no `.get(<name>, True)`-style default-to-pass may exist in the verdict
    has_default_true = ".get(" in body and ", True)" in body
    assert not has_default_true
    assert "MISSING_REQUIRED_STORAGE_CHECK" in src


def test_gate_delegates_to_the_typed_result():
    src = (REPO / "scripts" / "innovation" / "clean_gate.py").read_text(
        encoding="utf-8")
    assert "StorageVerification(" in src
    # the old unwired call must be gone
    assert "AC.storage_verdict(" not in src


# ── same-source identity enforcement ─────────────────────────────────────
def test_identity_mismatch_is_rejected_not_marked_same_source():
    pre = {"source_run_key": "k", "source_full_checkpoint_sha256": "aa",
           "source_job_id": "1", "source_training_attempt": 1,
           "export_implementation_version": "v-pre"}
    post = dict(pre, source_full_checkpoint_sha256="bb")
    out = SSI.same_source_compare("/nonexistent", "/nonexistent", "nlinear", 24,
                                  "/tmp", pre, post)
    assert out["comparison_mode"] == SSI.REJECTED
    assert out["passed"] is False
    assert out["comparison_mode"] != SSI.COMPARISON_MODE


def test_different_run_key_is_rejected():
    pre = {"source_run_key": "k1", "source_full_checkpoint_sha256": "aa",
           "source_job_id": "1", "source_training_attempt": 1,
           "export_implementation_version": "v"}
    post = dict(pre, source_run_key="k2")
    out = SSI.same_source_compare("/x", "/x", "nlinear", 24, "/tmp", pre, post)
    assert out["comparison_mode"] == SSI.REJECTED


def test_incomplete_identity_is_refused():
    out = SSI.same_source_compare("/x", "/x", "nlinear", 24, "/tmp", {}, {})
    assert out["comparison_mode"] == SSI.MISSING_SOURCE
    assert out["passed"] is False


def test_same_source_mode_is_declared_only_for_matching_identity():
    assert SSI.COMPARISON_MODE == "same_source"
    assert SSI.REJECTED != SSI.COMPARISON_MODE


def test_required_identity_fields_are_enforced():
    for k in ("source_full_checkpoint_sha256", "source_run_key",
              "source_job_id", "source_training_attempt",
              "export_implementation_version"):
        assert k in SSI._REQUIRED_IDENTITY


def test_same_source_module_documents_the_independent_training_ban():
    src = (REPO / "scripts" / "innovation"
           / "same_source_invariant.py").read_text(encoding="utf-8")
    assert "independent training" in src.lower()
    assert "REJECTED_INDEPENDENT_TRAINING" in src


# ── legacy backward compatibility (the 320 already-accepted records) ─────
def test_legacy_13_check_record_still_validates():
    c = {k: True for k in SV.LEGACY_REQUIRED_CHECKS}
    e = {"run_key": "k", "model": "nlinear", "horizon": 24,
         "file_sha256": "a" * 64, "canonical_tensor_sha256": "b" * 64,
         "canonical_hash_schema": "canonical-tensor-v1",
         "source_full_checkpoint_sha256": "c" * 64,
         "source_run_key": "k", "source_job_id": "1",
         "source_training_attempt": 1,
         "export_implementation_version": "v",
         "comparison_mode": "same_source"}
    assert SV.StorageVerification(c, e).passed is True
