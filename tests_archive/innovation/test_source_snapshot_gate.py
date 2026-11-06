"""
Deployment-root source verification tests (implementation source version v2.1)
=============================================================================

Proves the explicit-deployment-root contract of `verify_source_snapshot` and
closes the nested-snapshot false-positive path.

Mandated cases:
  1 correct explicit root passes
  2 incorrect deployment root fails
  3 nested source_snapshot root is rejected
  4 runtime source modification fails
  5 CRITICAL: intact nested snapshot + modified runtime source => FAILS
  6 missing runtime file fails
  7 controlled-scope extra file fails
  8 missing manifest fails
  9 incorrect expected aggregate hash fails
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402

from innovation import run_artifacts as ART  # noqa: E402
from innovation import source_snapshot as SS  # noqa: E402
from innovation import verify_source_snapshot as V  # noqa: E402
from innovation.paths import (PROJECT_ROOT, SOURCE_SNAPSHOT_DIR,  # noqa: E402
                              SOURCE_SNAPSHOT_MANIFEST)

_BUILT = {"done": False}
NESTED_REL = os.path.join("results", "innovation", "source_snapshot")


def _ensure_snapshot():
    """Rebuild the snapshot so the manifest is current for THIS source state."""
    if not _BUILT["done"]:
        SS.build(rebuild=True)
        _BUILT["done"] = True


def _manifest():
    _ensure_snapshot()
    with open(SOURCE_SNAPSHOT_MANIFEST, "r", encoding="utf-8") as f:
        return json.load(f)


def _materialise(root: str, nested: bool = False) -> str:
    """Copy the frozen file set into `root` (optionally also as a nested copy)."""
    man = _manifest()
    for f in man["files"]:
        for base in ([root] + ([os.path.join(root, NESTED_REL)] if nested else [])):
            dst = os.path.join(base, f["path"])
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(PROJECT_ROOT, f["path"]), dst)
    return root


def _tmp(prefix="innov_deploy_"):
    return tempfile.mkdtemp(prefix=prefix)


# 1 ─────────────────────────────────────────────────────────────────────────
def test_correct_explicit_root_passes():
    _ensure_snapshot()
    res = V.verify(SOURCE_SNAPSHOT_MANIFEST, deployment_root=PROJECT_ROOT)
    assert res["ok"] is True, res
    assert res["verification_mode"] == "explicit_root", res
    assert res["exit_status"] == 0, res
    assert res["actual_aggregate_sha256"] == res["expected_aggregate_sha256"], res


# 2 ─────────────────────────────────────────────────────────────────────────
def test_incorrect_deployment_root_fails():
    _ensure_snapshot()
    res = V.verify(SOURCE_SNAPSHOT_MANIFEST, deployment_root=_tmp())
    assert res["ok"] is False and res["exit_status"] != 0, res
    assert res["missing_files"], res


# 3 ─────────────────────────────────────────────────────────────────────────
def test_nested_snapshot_root_rejected():
    _ensure_snapshot()
    root = _materialise(_tmp(), nested=True)
    res = V.verify(SOURCE_SNAPSHOT_MANIFEST,
                   deployment_root=os.path.join(root, NESTED_REL))
    assert res["ok"] is False and res["exit_status"] != 0, res
    assert res["reason"] == "INVALID_NESTED_SNAPSHOT_ROOT", res
    assert res["verification_mode"] == "rejected_nested_root", res


# 4 ─────────────────────────────────────────────────────────────────────────
def test_runtime_modification_fails():
    _ensure_snapshot()
    root = _materialise(_tmp())
    victim = os.path.join(root, "scripts", "innovation", "runner.py")
    with open(victim, "a", encoding="utf-8") as f:
        f.write("\n# tampered\n")
    res = V.verify(SOURCE_SNAPSHOT_MANIFEST, deployment_root=root)
    assert res["ok"] is False and res["exit_status"] != 0, res
    assert any(m["path"].endswith("scripts/innovation/runner.py")
               for m in res["mismatched_files"]), res


# 5 ─────────────────────────────────────────────────────────────────────────
def test_intact_nested_snapshot_cannot_hide_modified_runtime():
    """CRITICAL anti-false-positive: the nested copy is intact, the runtime
    source is modified -> verification MUST fail."""
    man = _manifest()
    root = _materialise(_tmp(), nested=True)

    # nested snapshot copy stays INTACT (hash equals the manifest value)
    nested_victim = os.path.join(root, NESTED_REL, "scripts", "innovation", "runner.py")
    rec = next(f for f in man["files"]
               if f["path"] == "scripts/innovation/runner.py")
    assert ART.sha256_file(nested_victim) == rec["sha256"], "nested copy must be intact"

    # ACTUAL runtime source IS modified
    runtime_victim = os.path.join(root, "scripts", "innovation", "runner.py")
    with open(runtime_victim, "a", encoding="utf-8") as f:
        f.write("\n# runtime tampered\n")

    res = V.verify(SOURCE_SNAPSHOT_MANIFEST, deployment_root=root)
    assert res["ok"] is False, res
    assert res["exit_status"] != 0, res
    assert any(m["path"] == "scripts/innovation/runner.py"
               for m in res["mismatched_files"]), res

    # and the nested root itself is still REJECTED (cannot be used to self-verify)
    res2 = V.verify(SOURCE_SNAPSHOT_MANIFEST,
                    deployment_root=os.path.join(root, NESTED_REL))
    assert res2["reason"] == "INVALID_NESTED_SNAPSHOT_ROOT", res2


# 6 ─────────────────────────────────────────────────────────────────────────
def test_missing_runtime_file_fails():
    _ensure_snapshot()
    root = _materialise(_tmp())
    os.remove(os.path.join(root, "scripts", "innovation", "metrics.py"))
    res = V.verify(SOURCE_SNAPSHOT_MANIFEST, deployment_root=root)
    assert res["ok"] is False and res["exit_status"] != 0, res
    assert "scripts/innovation/metrics.py" in res["missing_files"], res


# 7 ─────────────────────────────────────────────────────────────────────────
def test_controlled_scope_extra_fails():
    _ensure_snapshot()
    root = _materialise(_tmp())
    extra = os.path.join(root, "scripts", "innovation", "zz_extra_probe.py")
    with open(extra, "w", encoding="utf-8") as f:
        f.write("# not in the frozen manifest\n")
    res = V.verify(SOURCE_SNAPSHOT_MANIFEST, deployment_root=root)
    assert res["ok"] is False and res["exit_status"] != 0, res
    assert "scripts/innovation/zz_extra_probe.py" in \
        res["unexpected_files_in_controlled_scope"], res


# 8 ─────────────────────────────────────────────────────────────────────────
def test_missing_manifest_fails():
    res = V.verify(os.path.join(_tmp(), "nope.json"), deployment_root=PROJECT_ROOT)
    assert res["ok"] is False and res["exit_status"] != 0, res
    assert "not found" in (res["reason"] or ""), res


# 9 ─────────────────────────────────────────────────────────────────────────
def test_incorrect_expected_aggregate_fails():
    _ensure_snapshot()
    res = V.verify(SOURCE_SNAPSHOT_MANIFEST, deployment_root=PROJECT_ROOT,
                   expect="0" * 64)
    assert res["ok"] is False and res["exit_status"] != 0, res
    assert res["reason"] == "aggregate_sha256_mismatch", res


# extra guards ──────────────────────────────────────────────────────────────
def test_project_root_is_not_a_nested_root():
    assert V._is_nested_root(os.path.realpath(PROJECT_ROOT)) is False
    assert V._is_nested_root(os.path.realpath(SOURCE_SNAPSHOT_DIR)) is True


if __name__ == "__main__":
    test_correct_explicit_root_passes()
    test_incorrect_deployment_root_fails()
    test_nested_snapshot_root_rejected()
    test_runtime_modification_fails()
    test_intact_nested_snapshot_cannot_hide_modified_runtime()
    test_missing_runtime_file_fails()
    test_controlled_scope_extra_fails()
    test_missing_manifest_fails()
    test_incorrect_expected_aggregate_fails()
    test_project_root_is_not_a_nested_root()
    print("[test_source_snapshot_gate] OK")
