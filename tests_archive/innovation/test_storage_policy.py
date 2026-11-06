"""test_storage_policy.py — model-free tests for the v3.13 storage policy.

No torch, no model loading, no filesystem mutation: only parsing, projection,
containment and default-deny deletion logic.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from innovation import storage_policy as SP        # noqa: E402

QUOTA_TEXT = (
    "                         Block Limits                                "
    "    |     File Limits\n"
    "Filesystem type             KB      quota      limit   in_doubt    "
    "grace |    files   quota    limit in_doubt    grace  Remarks\n"
    "home       USR       104855648   52428800  104857600          0   "
    "5 days |    82916       0        0        0     none\n"
    "scratch    USR       351222560  314572800 1073741824          0  "
    "10 days |    23320       0        0        0     none\n"
)


# ── quota parsing ─────────────────────────────────────────────────────────
def test_parse_quota_reads_both_filesystems():
    q = SP.parse_quota(QUOTA_TEXT)
    assert set(q) == {"home", "scratch"}
    assert q["home"]["used_kb"] == 104855648
    assert q["home"]["quota_kb"] == 52428800
    assert q["home"]["limit_kb"] == 104857600
    assert q["scratch"]["limit_kb"] == 1073741824


def test_parse_quota_gib_conversions():
    q = SP.parse_quota(QUOTA_TEXT)
    assert round(q["home"]["limit_gib"], 1) == 100.0
    assert round(q["home"]["quota_gib"], 1) == 50.0
    # 1073741824 KB == 1024 GiB (== 1 TiB), not 1000
    assert round(q["scratch"]["limit_gib"], 1) == 1024.0


def test_parse_quota_ignores_unknown_lines():
    assert SP.parse_quota("garbage\nlines\n") == {}


# ── capacity projection ───────────────────────────────────────────────────
def _remaining():
    return {"qwen_time_llm": 35, "calf_llm": 40, "timecma_llm": 40,
            "gpt2_miflu": 252, "baseline": 8}


def test_projection_within_limits_passes():
    q = SP.parse_quota(QUOTA_TEXT)
    # after the D13 cleanup home is ~49 GiB
    q["home"]["used_bytes"] = int(49 * SP.GIB)
    q["home"]["used_gib"] = 49.0
    proj = SP.capacity_projection(q, _remaining(),
                                  accepted_rows_durable_bytes=0,
                                  wave1_rows_durable_bytes=int(41 * SP.GIB),
                                  scratch_now_bytes=int(403 * SP.GIB))
    assert proj["passed"] is True
    assert proj["final_ok"] and proj["peak_ok"] and proj["reserve_ok"]
    assert proj["projected_final_gib"] <= SP.HOME_TARGET_MAX_GIB
    assert proj["projected_peak_gib"] <= SP.HOME_TARGET_MAX_GIB
    assert proj["headroom_gib"] >= SP.HOME_RESERVE_GIB


def test_projection_detects_overrun():
    q = SP.parse_quota(QUOTA_TEXT)
    q["home"]["used_bytes"] = int(95 * SP.GIB)
    proj = SP.capacity_projection(q, _remaining(), 0, int(41 * SP.GIB),
                                  int(403 * SP.GIB))
    assert proj["passed"] is False
    assert proj["headroom_gib"] < SP.HOME_RESERVE_GIB


def test_projection_unknown_schema_uses_worst_case():
    worst = max(SP.COMPACT_BYTES_BY_SCHEMA.values()) + SP.NON_CHECKPOINT_BYTES
    assert SP.projected_row_bytes("does_not_exist") == worst


def test_projection_reports_remaining_rows():
    q = SP.parse_quota(QUOTA_TEXT)
    q["home"]["used_bytes"] = int(49 * SP.GIB)
    proj = SP.capacity_projection(q, _remaining(), 0, int(41 * SP.GIB),
                                  int(403 * SP.GIB))
    assert proj["remaining_rows"] == 375


def test_scratch_beyond_hard_limit_fails():
    q = SP.parse_quota(QUOTA_TEXT)
    q["home"]["used_bytes"] = int(49 * SP.GIB)
    proj = SP.capacity_projection(q, _remaining(), 0, int(41 * SP.GIB),
                                  int(1100 * SP.GIB))
    assert proj["scratch_ok"] is False
    assert proj["passed"] is False


# ── containment / traversal / symlink ─────────────────────────────────────
def test_containment_accepts_direct_child(tmp_path):
    root = tmp_path / "durable"
    root.mkdir()
    child = root / "row"
    child.mkdir()
    assert SP.is_contained(str(child), str(root)) is True


def test_containment_rejects_parent_and_sibling(tmp_path):
    root = tmp_path / "durable"
    root.mkdir()
    (tmp_path / "outside").mkdir()
    assert SP.is_contained(str(tmp_path), str(root)) is False
    assert SP.is_contained(str(tmp_path / "outside"), str(root)) is False
    assert SP.is_contained(str(root), str(root)) is False


def test_containment_rejects_traversal(tmp_path):
    root = tmp_path / "durable"
    root.mkdir()
    assert SP.is_contained(str(root / ".." / ".." / "etc"), str(root)) is False


def test_containment_rejects_empty_or_relative(tmp_path):
    root = tmp_path / "durable"
    root.mkdir()
    assert SP.is_contained("", str(root)) is False
    assert SP.is_contained("relative/path", str(root)) is False


@pytest.mark.skipif(os.name == "nt" and not os.environ.get("CI"),
                    reason="symlink needs privileges on Windows")
def test_containment_rejects_symlink_escape(tmp_path):
    root = tmp_path / "durable"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = root / "row"
    try:
        os.symlink(str(outside), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("symlink unsupported")
    assert SP.is_contained(str(link), str(root)) is False


# ── deletion is default-deny ──────────────────────────────────────────────
def test_deletion_allowed_for_eligible_partial_copy(tmp_path):
    root = tmp_path / "durable"
    root.mkdir()
    p = root / "row"
    p.mkdir()
    ok, why = SP.deletion_allowed(str(p), str(root), "H_PARTIAL_FAILED_COPY",
                                  has_manifest=True, is_symlink=False,
                                  owner_ok=True)
    assert ok and why == "eligible"


@pytest.mark.parametrize("cls", [
    "A_ACTIVE_CURRENT_WAVE1_REQUIRED",
    "B_CURRENT_WAVE1_ACCEPTED_DURABLE_EVIDENCE",
    "D_SUPERSEDED_MIFLU_EVIDENCE_REQUIRED_FOR_AUDIT",
    "G_SYSTEM_SHARED_OR_UNKNOWN",
    "SOMETHING_UNCLASSIFIED",
])
def test_deletion_refused_for_non_eligible_classes(tmp_path, cls):
    root = tmp_path / "durable"
    root.mkdir()
    p = root / "row"
    p.mkdir()
    ok, why = SP.deletion_allowed(str(p), str(root), cls, has_manifest=True,
                                  is_symlink=False, owner_ok=True)
    assert ok is False and "not-eligible" in why


def test_deletion_refused_when_owner_unverified(tmp_path):
    root = tmp_path / "durable"
    root.mkdir()
    p = root / "row"
    p.mkdir()
    ok, why = SP.deletion_allowed(str(p), str(root), "H_PARTIAL_FAILED_COPY",
                                  has_manifest=True, is_symlink=False,
                                  owner_ok=False)
    assert ok is False and why == "owner-not-verified"


def test_deletion_refused_for_symlink(tmp_path):
    root = tmp_path / "durable"
    root.mkdir()
    ok, why = SP.deletion_allowed(str(root / "row"), str(root),
                                  "H_PARTIAL_FAILED_COPY", has_manifest=True,
                                  is_symlink=True, owner_ok=True)
    assert ok is False and why == "symlink"


def test_deletion_refused_outside_root(tmp_path):
    root = tmp_path / "durable"
    root.mkdir()
    (tmp_path / "outside").mkdir()
    ok, why = SP.deletion_allowed(str(tmp_path / "outside"), str(root),
                                  "H_PARTIAL_FAILED_COPY", has_manifest=True,
                                  is_symlink=False, owner_ok=True)
    assert ok is False and why == "outside-allowed-root"


def test_deletion_refused_without_manifest(tmp_path):
    root = tmp_path / "durable"
    root.mkdir()
    p = root / "row"
    p.mkdir()
    ok, why = SP.deletion_allowed(str(p), str(root), "H_PARTIAL_FAILED_COPY",
                                  has_manifest=False, is_symlink=False,
                                  owner_ok=True)
    assert ok is False and why == "no-manifest-record"


# ── atomic staging ────────────────────────────────────────────────────────
def test_staging_path_is_a_sibling_with_job_id():
    final = os.path.join(os.sep + "durable", "root", "row__w1")
    st = SP.staging_path(final, "571472")
    assert st == os.path.join(os.sep + "durable", "root",
                              "row__w1.staging.571472")


def test_staging_name_validation():
    assert SP.is_valid_staging_name("row__w1.staging.571472") is True
    assert SP.is_valid_staging_name("row__w1") is False
    assert SP.is_valid_staging_name("row__w1.staging") is False
    assert SP.is_valid_staging_name("../evil.staging.1") is False


def test_staging_is_contained_in_the_durable_root(tmp_path):
    root = tmp_path / "durable"
    root.mkdir()
    st = SP.staging_path(str(root / "row__w1"), "1")
    assert SP.is_contained(st, str(root)) is True
