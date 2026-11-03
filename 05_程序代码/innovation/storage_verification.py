"""storage_verification.py — v3.19 authoritative storage-verification schema.

WHY (D16): the v3.16 Gate wrote `canonical_invariant_vs_durable` into the
storage result (`res`) while `storage_verdict(rep, rest, ...)` read the
restoration result (`rest`). The field was therefore absent, and the verdict
used `rest.get("canonical_invariant_vs_durable", True)` — a MISSING FIELD
DEFAULTED TO PASS, so the check was never actually enforced.

WHY (D15): the schema was checkpoint-only. Deterministic baselines are FROZEN
to carry no checkpoint (`checkpoint_applicable=false`), so a baseline record
can never provide `compact_file_present` & friends as True — and silently
omitting them would recreate exactly the D16 "missing defaults to pass" bug.
The fix: an EXPLICIT `not_applicable` sentinel. A checkpoint-only check on a
baseline row must be present AND carry the sentinel; anything missing is a
hard fail, and the sentinel is only ever accepted on the arm-appropriate side.

This module removes that whole failure class:
  * ONE versioned, strongly-typed result object
  * `verdict()` reads ONLY that object
  * EVERY required check must be present; a missing key is a HARD FAIL that
    reports `MISSING_REQUIRED_STORAGE_CHECK`
  * a check counts as passed only when its value is literally `True`, or when
    it is the `not_applicable` sentinel on the arm-appropriate side
  * there is no `.get(name, True)` anywhere in the verdict path
  * `arm=None` keeps the exact LEGACY contract (the 13 checkpoint-era checks),
    so the 320 already-accepted records still validate unchanged
"""
from __future__ import annotations

import json

SCHEMA = "storage-verification-v1"

# The explicit, non-boolean marker for a check that provably does not apply.
NOT_APPLICABLE = "not_applicable"
BASELINE_REASON = "deterministic_baseline_no_checkpoint"
STOCHASTIC_ARMS = ("primary", "ablation", "negative_control")
BASELINE_ARM = "baseline"
VALID_ARMS = (None,) + STOCHASTIC_ARMS + (BASELINE_ARM,)

# ---- arm-independent checks -------------------------------------------
COMMON_CHECKS = (
    "artifact_completeness",
    "run_status_completed",
    "atomic_publish_ok",
    "contained",
)
# True for stochastic rows; NOT_APPLICABLE for deterministic baselines.
CHECKPOINT_ONLY_CHECKS = (
    "compact_file_present",
    "compact_file_sha256_matches_manifest",
    "canonical_tensor_sha256_present",
    "reconstruction_exact",
    "restoration_exact",
    "strict_missing_keys_zero",
    "strict_unexpected_keys_zero",
    "no_frozen_backbone_duplication",
    "same_source_invariant_ok",
)
# True for deterministic baselines; NOT_APPLICABLE for stochastic rows.
BASELINE_ONLY_CHECKS = (
    "no_unexpected_checkpoint",
    "checkpoint_applicable_false",
    "stochastic_seed_applicable_false",
    "resource_usage_semantics_ok",
    "provenance_complete",
)

LEGACY_REQUIRED_CHECKS = COMMON_CHECKS + CHECKPOINT_ONLY_CHECKS
REQUIRED_CHECKS = COMMON_CHECKS + CHECKPOINT_ONLY_CHECKS + BASELINE_ONLY_CHECKS

# ---- evidence ----------------------------------------------------------
COMMON_EVIDENCE = (
    "run_key", "model", "horizon",
    "source_run_key", "source_job_id", "source_training_attempt",
    "export_implementation_version", "comparison_mode",
)
CHECKPOINT_ONLY_EVIDENCE = (
    "file_sha256", "canonical_tensor_sha256",
    "source_full_checkpoint_sha256", "canonical_hash_schema",
)
BASELINE_ONLY_EVIDENCE = (
    "reason", "checkpoint_applicable", "stochastic_seed_applicable",
)
LEGACY_REQUIRED_EVIDENCE = COMMON_EVIDENCE + CHECKPOINT_ONLY_EVIDENCE
REQUIRED_EVIDENCE = (COMMON_EVIDENCE + CHECKPOINT_ONLY_EVIDENCE
                     + BASELINE_ONLY_EVIDENCE)

MISSING = "MISSING_REQUIRED_STORAGE_CHECK"
FAILED = "FAILED_STORAGE_CHECK"
OK = "OK"


class StorageVerificationError(ValueError):
    """Raised when a result is constructed with an unusable shape."""


def _sentinel_side(arm):
    """Which check family carries `not_applicable` for this arm."""
    if arm == BASELINE_ARM:
        return CHECKPOINT_ONLY_CHECKS
    return BASELINE_ONLY_CHECKS          # stochastic arms


class StorageVerification:
    """The ONLY structure `storage_verdict` is allowed to read."""

    __slots__ = ("checks", "evidence", "schema", "arm", "reason")

    def __init__(self, checks: dict, evidence: dict,
                 arm: str | None = None, reason: str | None = None):
        if not isinstance(checks, dict) or not isinstance(evidence, dict):
            raise StorageVerificationError("checks and evidence must be dicts")
        if arm not in VALID_ARMS:
            raise StorageVerificationError(f"unknown arm: {arm!r}")
        if arm == BASELINE_ARM and reason != BASELINE_REASON:
            raise StorageVerificationError(
                f"baseline arm requires reason={BASELINE_REASON!r}")
        extra = sorted(set(checks) - set(REQUIRED_CHECKS))
        if extra:
            raise StorageVerificationError(f"unknown check ids: {extra}")
        sentinel_side = _sentinel_side(arm)
        # values must be real booleans (or the explicit sentinel on the
        # arm-appropriate side) -> no truthy coercion, no None, no defaults
        for k, v in checks.items():
            if isinstance(v, bool):
                continue
            if v == NOT_APPLICABLE and arm is not None and k in sentinel_side:
                continue
            raise StorageVerificationError(
                f"non-boolean check value for {k!r}: {v!r}")
        self.schema = SCHEMA
        self.checks = dict(checks)
        self.evidence = dict(evidence)
        self.arm = arm
        self.reason = reason

    # ---- the single authoritative verdict -------------------------------
    def verdict(self) -> tuple:
        """(passed, code, detail) — fails CLOSED on anything missing."""
        if self.arm is None:
            required = LEGACY_REQUIRED_CHECKS
        else:
            required = REQUIRED_CHECKS
        missing = [c for c in required if c not in self.checks]
        if missing:
            return False, MISSING, ",".join(missing)
        required_ev = (LEGACY_REQUIRED_EVIDENCE if self.arm is None
                       else REQUIRED_EVIDENCE)
        missing_ev = [e for e in required_ev if e not in self.evidence]
        if missing_ev:
            return False, MISSING, "evidence:" + ",".join(missing_ev)
        if self.arm == BASELINE_ARM:
            if self.evidence.get("reason") != BASELINE_REASON:
                return False, FAILED, "evidence:reason"
            if self.evidence.get("checkpoint_applicable") is not False:
                return False, FAILED, "evidence:checkpoint_applicable"
            if self.evidence.get("stochastic_seed_applicable") is not False:
                return False, FAILED, "evidence:stochastic_seed_applicable"
            for e in CHECKPOINT_ONLY_EVIDENCE:
                if self.evidence.get(e) != NOT_APPLICABLE:
                    return False, FAILED, f"evidence:{e}:not_applicable"
        elif self.arm is not None:
            for e in CHECKPOINT_ONLY_EVIDENCE:
                v = self.evidence.get(e)
                if not isinstance(v, str) or not v or v == NOT_APPLICABLE:
                    return False, FAILED, f"evidence:{e}"
            for e in BASELINE_ONLY_EVIDENCE:
                if self.evidence.get(e) != NOT_APPLICABLE:
                    return False, FAILED, f"evidence:{e}:not_applicable"
        sentinel_side = _sentinel_side(self.arm) if self.arm is not None else ()
        failed = []
        for c in required:
            v = self.checks[c]
            if self.arm is None:
                if v is not True:
                    failed.append(c)
            elif c in sentinel_side:
                # must be EXACTLY the sentinel — True here would be an
                # inconsistent claim (e.g. a baseline asserting
                # compact_file_present)
                if v != NOT_APPLICABLE:
                    failed.append(c)
            elif v is not True:
                failed.append(c)
        if failed:
            return False, FAILED, ",".join(failed)
        return True, OK, ""

    @property
    def passed(self) -> bool:
        return self.verdict()[0]

    def to_dict(self) -> dict:
        passed, code, detail = self.verdict()
        return {"schema": self.schema, "passed": passed, "code": code,
                "detail": detail, "arm": self.arm, "reason": self.reason,
                "checks": dict(self.checks), "evidence": dict(self.evidence)}


def storage_verdict(result) -> bool:
    """v3.17+: the ONLY entry point. Accepts a StorageVerification (or its
    serialized dict). Anything else — including a plain dict missing fields —
    fails closed. No default-to-pass behaviour exists."""
    if isinstance(result, StorageVerification):
        return result.passed
    if isinstance(result, dict):
        try:
            return StorageVerification(result.get("checks"),
                                       result.get("evidence"),
                                       arm=result.get("arm"),
                                       reason=result.get("reason")).passed
        except Exception:                                      # noqa: BLE001
            return False
    return False


def load_result(path: str):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return StorageVerification(d["checks"], d["evidence"],
                               arm=d.get("arm"), reason=d.get("reason"))
