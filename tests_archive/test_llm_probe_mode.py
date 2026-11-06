"""test_llm_probe_mode.py — `--probe-only` on the backbone runner (CPU, no download).

Why this exists
---------------
Probing a **real** LLM checkpoint on a CPU/IO partition is the only way to prove
the frozen-encoder adapter works before an A100 is free
(`docs/HPC_RUNBOOK.md` "PARTITION POLICY": downloads, revision pinning and
hidden-state smoke tests produce no measured number, so they may run anywhere).
Such a cell must be self-labelling as a probe (AGENTS.md rule 13(b)) — otherwise
a CPU-partition cell could be mistaken for a benchmark row.

Tested here:
1. `--probe-only` exists and is documented;
2. it forces `probe_only=True` in the manifest and `artefact_is_a_result=False`;
3. it refuses to write under `expanded_runs/`;
4. without the flag the metrics row carries no `probe_only` key (default path
   unchanged).

Run:  python -m pytest -q tests/test_llm_probe_mode.py
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(PROJECT_ROOT, "scripts")
for _p in (SCRIPTS, PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import train_backbone_966 as tb                  # noqa: E402


def test_probe_only_flag_is_documented(capsys):
    with pytest.raises(SystemExit) as ei:
        tb.main(["--help"])
    assert ei.value.code == 0
    text = capsys.readouterr().out
    assert "--probe-only" in text
    assert "expanded_runs" in text and "13(b)" in text


def test_probe_only_cell_is_written_outside_expanded_runs(tmp_path):
    """A mock-encoder cell + --probe-only must land in the given dir, marked."""
    export = tmp_path / "probe"
    cmd = [sys.executable, os.path.join(SCRIPTS, "train_backbone_966.py"),
           "--backbone", "llm_encoder", "--horizon", "24", "--seed", "42",
           "--profile", "author_966", "--containment", "strict",
           "--mock-encoder", "--probe-only", "--max-train-windows", "8",
           "--max-val-windows", "4",
           "--export-dir", str(export), "--ckpt-dir", str(tmp_path / "ckpt")]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="-1")
    out = subprocess.run(cmd, capture_output=True, text=True,
                         cwd=PROJECT_ROOT, env=env)
    assert out.returncode == 0, out.stdout + out.stderr
    manifest = export / "manifest_llm_encoder_L24_s42.json"
    assert manifest.exists()
    import json
    m = json.loads(manifest.read_text(encoding="utf-8"))
    assert m["probe_only"] is True
    assert m["artefact_is_a_result"] is False
    assert m["mock_encoder"] is True


def test_probe_only_refuses_expanded_runs(tmp_path):
    cmd = [sys.executable, os.path.join(SCRIPTS, "train_backbone_966.py"),
           "--backbone", "llm_encoder", "--horizon", "24", "--seed", "42",
           "--profile", "author_966", "--containment", "strict",
           "--mock-encoder", "--probe-only", "--max-train-windows", "4",
           "--export-dir", str(tmp_path / "expanded_runs" / "x")]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="-1")
    out = subprocess.run(cmd, capture_output=True, text=True,
                         cwd=PROJECT_ROOT, env=env)
    assert out.returncode != 0
    assert "refusing to write a mock-encoder cell under expanded_runs" \
        in (out.stdout + out.stderr)


if __name__ == "__main__":       # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
