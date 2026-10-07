"""test_runner_import_path.py — reproduces the EXACT Gate 568972 root cause.

Model-free: no weights, no dataset, no network, no Torch/CUDA. The test copies
the real `scripts/` tree into an EMPTY temporary deployment root and runs the
real `clean_runner.py` as a subprocess with a cleared PYTHONPATH — precisely the
layout that failed in Gate 568972.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUNNER_REL = Path("scripts") / "innovation" / "clean_runner.py"


def _fake_deployment_root(tmp_path: Path) -> Path:
    root = tmp_path / "deploy_root"
    root.mkdir()
    shutil.copytree(REPO / "scripts", root / "scripts")
    return root


def _run(root: Path, run_key: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items()
           if k not in ("PYTHONPATH", "PYTHONHOME")}
    env["INNOVATION_DEPLOYMENT_ROOT"] = str(root)
    return subprocess.run(
        [sys.executable, str(root / RUNNER_REL), "--run-key", run_key],
        cwd=str(root), env=env, capture_output=True, text=True, timeout=300)


def test_runner_imports_when_parent_is_only_the_deployment_root(tmp_path):
    """The regression: importing must NOT fail from a bare deployment root."""
    root = _fake_deployment_root(tmp_path)
    p = _run(root, "primary__nlinear__L24__seed42__w1")
    combined = (p.stdout or "") + (p.stderr or "")
    assert "ModuleNotFoundError" not in combined, combined[-800:]
    assert "No module named 'innovation'" not in combined, combined[-800:]


def test_runner_reaches_spec_resolution_not_import_failure(tmp_path):
    """With no registry deployed the runner must fail LATER (registry lookup),
    which proves the import path itself is sound."""
    root = _fake_deployment_root(tmp_path)
    p = _run(root, "primary__nlinear__L24__seed42__w1")
    combined = (p.stdout or "") + (p.stderr or "")
    assert "frozen spec registry not found" in combined, combined[-800:]
    assert p.returncode != 0


def test_scripts_root_is_what_gets_added_to_sys_path():
    """Direct check of the corrected path contract."""
    src = (REPO / RUNNER_REL).read_text(encoding="utf-8")
    assert "_SCRIPTS_ROOT = os.path.dirname(_HERE)" in src
    assert "for _p in (_SCRIPTS_ROOT, _ROOT):" in src
    # the old, broken single-insert form must be gone
    assert "if _ROOT not in sys.path:\n    sys.path.insert(0, _ROOT)" not in src


def test_innovation_package_parent_layout_is_as_assumed():
    """Guard the assumption behind the fix: the package parent is scripts/."""
    assert (REPO / "scripts" / "innovation" / "__init__.py").exists()
    assert (REPO / "scripts" / "innovation" / "clean_runner.py").exists()
    assert (REPO / "scripts" / "innovation" / "clean_metrics.py").exists()
    # textual_embedder lives beside the package, so scripts/ must be importable
    assert (REPO / "scripts" / "textual_embedder.py").exists()


def test_repair_evidence_recorded(tmp_path):
    import json
    sc = REPO / "results" / "v3_clean" / "preregistration"
    pre = json.loads((sc / "d8_pre_repair_manifest.json").read_text(
        encoding="utf-8"))
    rec = json.loads((sc / "d8_repair_record.json").read_text(encoding="utf-8"))
    assert pre["failure_signature"]["exception"] == "ModuleNotFoundError"
    assert pre["failure_signature"]["failing_line"] == 41
    assert pre["failure_signature"]["shared_by_all_18_paths"] is True
    assert rec["classification"] == \
        "BEHAVIOR_NEUTRAL_RUNTIME_PATH_RESOLUTION_FIX"
    assert rec["scientific_parameters_changed"] == 0
    assert rec["pre_repair_sha256"] != rec["post_repair_sha256"]
    assert (sc / "d8_repair.diff").exists()
