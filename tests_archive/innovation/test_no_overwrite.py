"""Artifacts: create-only run dirs and append-only registry."""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402

from innovation import run_artifacts as ART  # noqa: E402


def test_create_only_run_dir():
    tmp = tempfile.mkdtemp(prefix="innov_runs_")
    old = ART.RUNS_ROOT
    ART.RUNS_ROOT = tmp
    try:
        d = ART.create_run_dir("r1")
        assert os.path.isdir(os.path.join(d, "checkpoints"))
        assert os.path.isdir(os.path.join(d, "predictions"))
        try:
            ART.create_run_dir("r1")
            raise AssertionError("second create must refuse to overwrite")
        except FileExistsError:
            pass
    finally:
        ART.RUNS_ROOT = old


def test_registry_is_append_only():
    tmp = tempfile.mkdtemp(prefix="innov_reg_")
    old = ART.REGISTRY_PATH
    ART.REGISTRY_PATH = os.path.join(tmp, "registry.csv")
    try:
        ART.append_registry({"run_id": "a", "status": "ok"})
        ART.append_registry({"run_id": "b", "status": "failed"})
        rows = ART.read_registry()
        assert [r["run_id"] for r in rows] == ["a", "b"], rows
        with open(ART.REGISTRY_PATH, encoding="utf-8") as f:
            assert f.read().count("run_id,") == 1, "header must appear once"
    finally:
        ART.REGISTRY_PATH = old


if __name__ == "__main__":
    test_create_only_run_dir()
    test_registry_is_append_only()
    print("[test_no_overwrite] OK")
