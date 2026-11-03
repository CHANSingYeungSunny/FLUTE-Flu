"""storage_policy.py — v3.13 pure-Python storage safety policy.

NO torch, no model code, no filesystem mutation here: only parsing, projection
and path-safety decisions. It is imported by the pure-Bash controller (through
small helper invocations) and by the model-free tests.

Responsibilities:
  * parse `mmlsquota` output into machine-readable numbers
  * project final/peak home and scratch footprints for the remaining rows
  * enforce the mandatory safety margins
  * decide whether a durable-copy target path is contained and safe
  * decide whether a deletion candidate is acceptable (refuse by default)
"""
from __future__ import annotations

import os
import re

GIB = 1024 ** 3
MIB = 1024 ** 2

# ---- mandatory safety margins (frozen by the task) ------------------------
HOME_HARD_LIMIT_GIB = 100.0
HOME_SOFT_QUOTA_GIB = 50.0
HOME_TARGET_MAX_GIB = 80.0        # projected final AND peak including staging
HOME_RESERVE_GIB = 20.0           # must stay below the 100 GiB hard limit
SCRATCH_SOFT_QUOTA_GIB = 300.0
SCRATCH_HARD_QUOTA_GIB = 1000.0
SCRATCH_TARGET_MAX_GIB = 280.0

# ---- observed compact durable sizes (measured on compute nodes, v3.13) ----
COMPACT_BYTES_BY_SCHEMA = {
    "nlinear": 10224, "dlinear": 20480, "patchtst": 351704,
    "itransformer": 305376, "gpt2_miflu": 4135503,
    "qwen_time_llm": 1482128, "calf_llm": 7927320, "timecma_llm": 5564776,
    "baseline": 2048,
}
# non-checkpoint artifacts (predictions/metrics/logs/provenance) per row
NON_CHECKPOINT_BYTES = 24 * MIB
# worst-case multiplier for the shared base models that must remain available
SHARED_BASE_BYTES = 14 * GIB


def parse_quota(text: str) -> dict:
    """Parse `mmlsquota` output.

    Expected rows look like:
      home     USR  104855648  52428800  104857600  0  5 days | 82916 0 0 0 none
      scratch  USR  351222560  314572800 1073741824 0 10 days| 23320 0 0 0 none
    Numbers are in KB.
    """
    out = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 6 or parts[0] not in ("home", "scratch"):
            continue
        try:
            used_kb = int(parts[2]); quota_kb = int(parts[3]); limit_kb = int(parts[4])
        except (ValueError, IndexError):
            continue
        out[parts[0]] = {
            "used_kb": used_kb, "quota_kb": quota_kb, "limit_kb": limit_kb,
            "used_bytes": used_kb * 1024, "quota_bytes": quota_kb * 1024,
            "limit_bytes": limit_kb * 1024,
            "used_gib": round(used_kb / 1048576, 3),
            "quota_gib": round(quota_kb / 1048576, 3),
            "limit_gib": round(limit_kb / 1048576, 3),
        }
    return out


def projected_row_bytes(schema: str) -> int:
    """Worst-case durable bytes for ONE row (compact + artifacts)."""
    base = COMPACT_BYTES_BY_SCHEMA.get(schema)
    if base is None:
        # unknown schema: refuse to guess, assume the largest known compact size
        base = max(COMPACT_BYTES_BY_SCHEMA.values())
    return base + NON_CHECKPOINT_BYTES


def capacity_projection(quota: dict, remaining_by_schema: dict,
                        accepted_rows_durable_bytes: int,
                        wave1_rows_durable_bytes: int,
                        scratch_now_bytes: int,
                        staged_rows: int = 1) -> dict:
    """Conservative capacity proof. Returns pass/fail plus every input used."""
    home_now = int(quota.get("home", {}).get("used_bytes", 0))
    home_limit = int(quota.get("home", {}).get("limit_bytes",
                                               HOME_HARD_LIMIT_GIB * GIB))

    remaining_bytes = sum(projected_row_bytes(s) * n
                          for s, n in remaining_by_schema.items())
    # the 205 already-submitted durable rows will be compacted: model BOTH the
    # current footprint and the post-compaction footprint conservatively.
    post_compaction_wave1 = int(wave1_rows_durable_bytes)
    per_row_compact = max(1, post_compaction_wave1 // max(1, 205))
    compaction_saving = max(0, wave1_rows_durable_bytes - 205 * per_row_compact)

    projected_final = home_now - compaction_saving + remaining_bytes
    # peak = final + one atomic staging directory for the next row
    max_next = max([projected_row_bytes(s)
                    for s in remaining_by_schema] or [24 * MIB])
    projected_peak = projected_final + max_next * staged_rows

    projected_final_gib = round(projected_final / GIB, 2)
    projected_peak_gib = round(projected_peak / GIB, 2)
    headroom_gib = round((home_limit - projected_peak) / GIB, 2)

    return {
        "home_now_gib": round(home_now / GIB, 2),
        "home_hard_limit_gib": round(home_limit / GIB, 2),
        "remaining_rows": int(sum(remaining_by_schema.values())),
        "remaining_by_schema": dict(remaining_by_schema),
        "remaining_bytes": int(remaining_bytes),
        "remaining_gib": round(remaining_bytes / GIB, 2),
        "expected_compaction_saving_bytes": int(compaction_saving),
        "expected_compaction_saving_gib": round(compaction_saving / GIB, 2),
        "projected_final_bytes": int(projected_final),
        "projected_final_gib": projected_final_gib,
        "projected_peak_bytes": int(projected_peak),
        "projected_peak_gib": projected_peak_gib,
        "headroom_gib": headroom_gib,
        "limits": {"final_max_gib": HOME_TARGET_MAX_GIB,
                   "peak_max_gib": HOME_TARGET_MAX_GIB,
                   "reserve_gib": HOME_RESERVE_GIB},
        "final_ok": projected_final_gib <= HOME_TARGET_MAX_GIB,
        "peak_ok": projected_peak_gib <= HOME_TARGET_MAX_GIB,
        "reserve_ok": headroom_gib >= HOME_RESERVE_GIB,
        "scratch_now_gib": round(scratch_now_bytes / GIB, 2),
        "scratch_target_max_gib": SCRATCH_TARGET_MAX_GIB,
        "scratch_hard_limit_gib": SCRATCH_HARD_QUOTA_GIB,
        "scratch_ok": (scratch_now_bytes / GIB) < SCRATCH_HARD_QUOTA_GIB,
        "shared_base_bytes": int(SHARED_BASE_BYTES),
        "passed": bool(projected_final_gib <= HOME_TARGET_MAX_GIB
                       and projected_peak_gib <= HOME_TARGET_MAX_GIB
                       and headroom_gib >= HOME_RESERVE_GIB
                       and (scratch_now_bytes / GIB) < SCRATCH_HARD_QUOTA_GIB),
    }


def is_contained(path: str, allowed_root: str) -> bool:
    """Canonical containment check: symlink-free and strictly inside the root."""
    if not path or not allowed_root:
        return False
    root = os.path.realpath(allowed_root)
    target = os.path.realpath(path)
    if target == root:
        return False                      # the root itself is not a target
    if not target.startswith(root + os.sep):
        return False
    rel = os.path.relpath(target, root)
    if rel.startswith("..") or os.path.isabs(rel):
        return False
    for part in rel.split(os.sep):
        if part in ("", ".", ".."):
            return False
        if ".." in part:
            return False
    return True


def deletion_allowed(path: str, allowed_root: str, classification: str,
                     has_manifest: bool, is_symlink: bool,
                     owner_ok: bool) -> tuple:
    """Default-DENY. Returns (allowed, reason)."""
    if not owner_ok:
        return False, "owner-not-verified"
    if is_symlink:
        return False, "symlink"
    if not is_contained(path, allowed_root):
        return False, "outside-allowed-root"
    if classification not in ("H_PARTIAL_FAILED_COPY",
                              "E_SUPERSEDED_MIFLU_BULK_REGENERABLE",
                              "I_CACHE_REGENERABLE"):
        return False, f"classification-not-eligible:{classification}"
    if not has_manifest:
        return False, "no-manifest-record"
    return True, "eligible"


SAFE_STAGING_RE = re.compile(r"^[A-Za-z0-9._-]+\.staging\.[0-9]+$")


def is_valid_staging_name(name: str) -> bool:
    return bool(SAFE_STAGING_RE.match(name))


def staging_path(final_path: str, job_id: str) -> str:
    base = os.path.basename(final_path.rstrip(os.sep))
    return os.path.join(os.path.dirname(final_path),
                        f"{base}.staging.{job_id}")
