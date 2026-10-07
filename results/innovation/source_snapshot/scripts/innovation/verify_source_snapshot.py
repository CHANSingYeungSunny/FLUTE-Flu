"""
verify_source_snapshot.py — deployment-root source verification.
================================================================

Verifies the ACTUAL DEPLOYED RUNTIME ROOT (not a nested snapshot copy) against
`source_snapshot_manifest.json`. Implements the explicit deployment-root
contract:

  * `collect_paths(root)` is parameterised, so present / missing / extra / hash
    checks ALL use the explicit root — nothing falls back to a module-level
    PROJECT_ROOT once a root has been supplied;
  * `--deployment-root <path>` is an explicit CLI argument, and the resolved
    root is recorded in the report;
  * a root that IS the nested `results/innovation/source_snapshot` directory (or
    lies inside it, or ENDS WITH that path) is REJECTED with
    `INVALID_NESTED_SNAPSHOT_ROOT` — closing the false-positive path where an
    intact nested snapshot copy could vouch for a modified runtime tree;
  * any missing file, hash mismatch, controlled-scope extra file, invalid root
    or aggregate-hash difference returns NON-ZERO.

USAGE (as the first step of every pilot job / deployment check):
    python scripts/innovation/verify_source_snapshot.py \
        --deployment-root /path/to/runtime/root \
        --manifest results/innovation/source_snapshot_manifest.json \
        [--expect <sha256>] [--report <out.json>]

Exit codes: 0 = verified, non-zero = abort.
"""

from __future__ import annotations

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import os

from innovation import run_artifacts as ART
from innovation.paths import PROJECT_ROOT, SOURCE_SNAPSHOT_DIR, SOURCE_SNAPSHOT_MANIFEST
from innovation.source_snapshot import _aggregate, collect_paths

_NESTED_SUFFIX = "/results/innovation/source_snapshot"


def _is_within(child: str, parent: str) -> bool:
    child = os.path.realpath(child)
    parent = os.path.realpath(parent)
    return child == parent or child.startswith(parent + os.sep)


def _is_nested_root(resolved: str) -> bool:
    """True if `resolved` IS the nested snapshot dir, lies inside it, or ENDS
    with its canonical suffix (covers running the verifier FROM the nested copy,
    where PROJECT_ROOT would resolve to the snapshot directory itself)."""
    if _is_within(resolved, SOURCE_SNAPSHOT_DIR):
        return True
    norm = os.path.normpath(resolved).replace("\\", "/")
    return norm.endswith(_NESTED_SUFFIX)


def verify(manifest_path: str = SOURCE_SNAPSHOT_MANIFEST,
           deployment_root: str | None = None,
           expect: str | None = None,
           script_path: str | None = None) -> dict:
    manifest_path = os.path.abspath(manifest_path)
    script_path = os.path.abspath(script_path or __file__)

    given_root = deployment_root
    resolved = os.path.realpath(deployment_root) if deployment_root \
        else os.path.realpath(PROJECT_ROOT)
    mode = "explicit_root" if deployment_root else "module_root_fallback"

    base = {
        "deployment_root": given_root,
        "resolved_deployment_root": resolved,
        "manifest": manifest_path,
        "script_path": script_path,
        "verification_mode": mode,
    }

    # ── guard: never vouch for the nested snapshot copy ──────────────────────
    if _is_nested_root(resolved):
        return {**base, "ok": False, "abort": True, "exit_status": 1,
                "reason": "INVALID_NESTED_SNAPSHOT_ROOT",
                "verification_mode": "rejected_nested_root",
                "expected_file_count": 0, "verified_file_count": 0,
                "missing_files": [], "mismatched_files": [],
                "unexpected_files_in_controlled_scope": [],
                "expected_aggregate_sha256": None,
                "actual_aggregate_sha256": None,
                "checked_utc": ART.utc_now()}

    if not os.path.exists(manifest_path):
        return {**base, "ok": False, "abort": True, "exit_status": 1,
                "reason": f"manifest not found: {manifest_path}",
                "expected_file_count": 0, "verified_file_count": 0,
                "missing_files": [], "mismatched_files": [],
                "unexpected_files_in_controlled_scope": [],
                "expected_aggregate_sha256": None,
                "actual_aggregate_sha256": None,
                "checked_utc": ART.utc_now()}

    with open(manifest_path, "r", encoding="utf-8") as f:
        man = json.load(f)

    expected_files = {f["path"]: f for f in man.get("files", [])}
    present = collect_paths(resolved)                      # EXPLICIT root
    missing = sorted(set(expected_files) - set(present))
    extra = sorted(set(present) - set(expected_files))

    mismatched = []
    deployed = []
    for rel, rec in sorted(expected_files.items()):
        p = os.path.join(resolved, rel)
        if not os.path.exists(p):
            continue
        sha = ART.sha256_file(p)
        deployed.append({"path": rel, "size": os.path.getsize(p), "sha256": sha})
        if sha != rec["sha256"]:
            mismatched.append({"path": rel, "expected": rec["sha256"],
                               "deployed": sha})

    actual = _aggregate(deployed) if deployed else ""
    ok = (not missing) and (not mismatched) and (not extra) \
        and actual == man.get("aggregate_sha256") \
        and (expect is None or actual == expect)

    return {
        **base,
        "ok": bool(ok), "abort": not bool(ok),
        "exit_status": 0 if ok else 1,
        "reason": None if ok else (
            "missing_files" if missing else
            "mismatched_files" if mismatched else
            "unexpected_files_in_controlled_scope" if extra else
            "aggregate_sha256_mismatch"),
        "expected_file_count": len(expected_files),
        "verified_file_count": len(deployed),
        "missing_files": missing[:50],
        "mismatched_files": mismatched[:50],
        "unexpected_files_in_controlled_scope": extra[:50],
        "expected_aggregate_sha256": man.get("aggregate_sha256"),
        "actual_aggregate_sha256": actual,
        "scientific_protocol_version": (man.get("scientific_protocol_version")
                                        or man.get("protocol_version")),
        "implementation_source_version": man.get("implementation_source_version"),
        "repository_head_short": man.get("repository_head_short"),
        "expect_argument": expect,
        "checked_utc": ART.utc_now(),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deployment-root", default=None, dest="deployment_root",
                    help="explicit runtime/deployment root to verify")
    ap.add_argument("--manifest", default=SOURCE_SNAPSHOT_MANIFEST)
    ap.add_argument("--expect", default=None)
    ap.add_argument("--report", default=None)
    a = ap.parse_args(argv)
    res = verify(a.manifest, a.deployment_root, a.expect)
    if a.report:
        ART.write_json(a.report, res)
    print("[verify_source_snapshot]")
    for k in ("deployment_root", "resolved_deployment_root", "manifest",
              "script_path", "verification_mode", "expected_file_count",
              "verified_file_count", "expected_aggregate_sha256",
              "actual_aggregate_sha256", "exit_status"):
        print(f"   {k} = {res.get(k)}")
    for k in ("missing_files", "mismatched_files",
              "unexpected_files_in_controlled_scope"):
        if res.get(k):
            print(f"   [ABORT] {k}: {res[k]}")
    if res.get("reason"):
        print(f"   [ABORT] reason = {res['reason']}")
    return int(res.get("exit_status", 1))


if __name__ == "__main__":
    raise SystemExit(main())
