"""test_deployment_completeness.py — items 8-9.

Unpacks the COMPLETE bundle into an EMPTY temporary root and proves that a run
can start there: the registry sits exactly where clean_runner reads it, the row
counts are right, all 580 scripts are findable, clean_runner can resolve
representative specs WITHOUT instantiating a model, the 18 deferred rows are
refused, every recorded hash matches, and the archive / Test / holdout are not
discoverable.

Model-free: no weights, no dataset reading, no network, no Torch/CUDA.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from innovation import clean_runner as CR  # noqa: E402

BUNDLE = REPO / "results" / "v3_clean" / "implementation" / "bundle_a.zip"
DEPLOY_MANIFEST = (REPO / "results" / "v3_clean" / "implementation"
                   / "deployment_manifest.json")
GIT_BASH = Path(r"C:\Program Files\Git\bin\bash.exe")


@pytest.fixture(scope="module")
def deployed(tmp_path_factory):
    if not BUNDLE.exists():
        pytest.skip("bundle not built yet")
    root = tmp_path_factory.mktemp("empty_deploy_root")
    assert not any(root.iterdir()), "test must start from an EMPTY root"
    with zipfile.ZipFile(BUNDLE) as z:
        z.extractall(root)
    return root


def test_empty_root_receives_every_manifest_member(deployed):
    man = json.loads(DEPLOY_MANIFEST.read_text(encoding="utf-8"))
    missing = [m["path"] for m in man["members"]
               if not (deployed / m["path"]).exists()]
    assert not missing, missing[:10]


def test_all_recorded_hashes_match(deployed):
    man = json.loads(DEPLOY_MANIFEST.read_text(encoding="utf-8"))
    import hashlib
    bad = []
    for m in man["members"]:
        p = deployed / m["path"]
        if not p.exists():
            bad.append((m["path"], "missing"))
            continue
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        if h.hexdigest() != m["sha256"]:
            bad.append((m["path"], "hash"))
    assert not bad, bad[:10]


def test_spec_registry_is_at_the_path_clean_runner_reads(deployed):
    reg = CR.load_registry(str(deployed))
    assert reg["n_specs"] == 598
    assert len(reg["specs"]) == 598


def test_row_counts_598_580_18(deployed):
    reg = CR.load_registry(str(deployed))
    w1 = [s for s in reg["specs"] if s["wave"] == 1]
    w2 = [s for s in reg["specs"] if s["wave"] == 2]
    assert len(w1) == 580
    assert len(w2) == 18
    assert reg["n_executable_bindings"] == 580


def test_all_580_executable_scripts_are_findable(deployed):
    reg = CR.load_registry(str(deployed))
    missing = []
    for s in reg["specs"]:
        if not s.get("executable_binding"):
            continue
        p = deployed / "hpc_scripts" / "v3_clean" / f"{s['run_key']}.sh"
        if not p.exists():
            missing.append(s["run_key"])
    assert not missing, missing[:10]
    assert len(list((deployed / "hpc_scripts" / "v3_clean").glob("*.sh"))) == 581


def test_clean_runner_and_gate_are_deployed(deployed):
    assert (deployed / "scripts" / "innovation" / "clean_runner.py").exists()
    assert (deployed / "scripts" / "innovation" / "clean_gate.py").exists()
    assert (deployed / "hpc_scripts" / "v3_clean" / "clean_gate.sh").exists()


def test_canonical_raw_data_and_scaler_are_deployed(deployed):
    # load_raw_df() reads data/raw/national_illness_raw.csv
    assert (deployed / "data" / "raw" / "national_illness_raw.csv").exists()
    assert (deployed / "data" / "scaler_miflu_national.json").exists()


def test_asset_descriptors_and_bootstrap_metadata_deployed(deployed):
    base = deployed / "results" / "v3_clean" / "implementation"
    assert (base / "asset_descriptors.json").exists()
    assert (base / "environment_bootstrap.json").exists()
    env = json.loads((base / "environment_bootstrap.json").read_text(
        encoding="utf-8"))
    assert env["slurm"]["exclude"] == "gpu-a100-05"
    assert env["slurm"]["gres"] == "gpu:a100:1"
    assert env["slurm"]["partition"] == "stingy"
    assets = json.loads((base / "asset_descriptors.json").read_text(
        encoding="utf-8"))
    assert "weights are" in assets["policy"]


def test_clean_runner_resolves_representative_specs_without_models(deployed):
    reg = CR.load_registry(str(deployed))
    picks = []
    for arm in ("primary", "baseline", "ablation", "negative_control"):
        cand = [s for s in reg["specs"] if s["arm"] == arm and s["wave"] == 1]
        assert cand, arm
        picks.append(cand[0])
    for s in picks:
        got = CR.resolve_spec(reg, s["run_key"])
        assert got["model"] == s["model"]
        assert got["horizon"] == s["horizon"]


def test_all_18_deferred_rows_refused_in_the_deployed_root(deployed):
    reg = CR.load_registry(str(deployed))
    deferred = [s for s in reg["specs"] if s["wave"] == 2]
    assert len(deferred) == 18
    for s in deferred:
        with pytest.raises(SystemExit):
            CR.resolve_spec(reg, s["run_key"])


def test_archive_and_test_paths_not_discoverable(deployed):
    assert not (deployed / "results" / "v3").exists()
    assert not (deployed / "results" / "v3_superseded_archive").exists()
    assert not (deployed / "results" / "innovation" / "test_evaluations").exists()
    blob = " ".join(str(p) for p in deployed.rglob("*")).lower()
    assert "test_predictions" not in blob
    assert "test_metrics" not in blob
    assert "holdout" not in blob


def test_no_crlf_in_any_deployed_file(deployed):
    bad = []
    for p in deployed.rglob("*"):
        if p.is_file() and p.suffix in (".sh", ".py", ".csv", ".json"):
            if b"\r" in p.read_bytes():
                bad.append(str(p.relative_to(deployed)))
    assert not bad, bad[:10]


def test_every_shell_script_passes_bash_n(deployed):
    if not GIT_BASH.exists():
        pytest.skip("Git Bash not available for syntax checking")
    scripts = sorted((deployed / "hpc_scripts" / "v3_clean").glob("*.sh"))
    assert len(scripts) == 581
    bad = []
    for p in scripts:
        r = subprocess.run([str(GIT_BASH), "-n", str(p)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            bad.append((p.name, r.stderr.strip()[:120]))
    assert not bad, bad[:5]


def test_bundle_excludes_forbidden_content():
    with zipfile.ZipFile(BUNDLE) as z:
        names = z.namelist()
    for forbidden in ("v3_superseded_archive", "test_evaluations",
                      "test_predictions", "test_metrics", "holdout"):
        assert not any(forbidden in n.lower() for n in names), forbidden
    assert not any(n.endswith((".pt", ".pth", ".bin", ".safetensors"))
                   for n in names)
