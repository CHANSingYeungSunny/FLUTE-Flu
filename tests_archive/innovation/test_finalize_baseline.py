"""test_finalize_baseline.py — D15 regression tests.

Reproduces the exact Wave-1 fail-stop: finalize job 572650 died with
    FileNotFoundError: .../baseline__last_value_naive__L24__seedna__w1/
                         checkpoints/best_val_mse.pt
because the finalize driver assumed every row carries a checkpoint, while
deterministic baselines are FROZEN to `checkpoint_applicable=false`.

These tests are MODEL-FREE: no model is built, no weights are loaded. The
checkpoint entry points (export_compact / restore_and_compare) are monkey-
patched to RAISE, proving the baseline branch never calls them.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from innovation import baseline_finalize as BF               # noqa: E402
from innovation import compact_checkpoint as CC              # noqa: E402
from innovation import finalize_row as FR                    # noqa: E402
from innovation import storage_verification as SV            # noqa: E402

REG = json.loads((REPO / "results" / "v3_clean" / "runs"
                  / "complete_specs_598.json").read_text(encoding="utf-8"))
BASELINE_SPECS = [s for s in REG["specs"] if s.get("arm") == "baseline"]
assert len(BASELINE_SPECS) == 8, "frozen matrix must carry 8 baseline rows"

ROW321 = "baseline__last_value_naive__L24__seedna__w1"       # the D15 row
ORIGINAL_JOB = "572649"                                     # its training job


@pytest.fixture(autouse=True)
def _deployment_root(monkeypatch):
    monkeypatch.setenv("INNOVATION_DEPLOYMENT_ROOT", str(REPO))


@pytest.fixture(autouse=True)
def _checkpoint_functions_must_not_run(monkeypatch):
    """Prove the baseline branch NEVER touches the checkpoint machinery."""
    def _boom(*a, **k):                                      # noqa: ANN001
        raise AssertionError("checkpoint function called on a baseline row")
    monkeypatch.setattr(CC, "export_compact", _boom)
    monkeypatch.setattr(CC, "restore_and_compare", _boom)


def _make_run(tmp_path: Path, spec: dict, *, checkpoints="empty",
              drop=(), mutate=None) -> Path:
    """Build a synthetic but structurally faithful baseline run directory."""
    d = tmp_path / "runs" / spec["run_key"]
    (d / "predictions").mkdir(parents=True)
    (d / "metrics").mkdir()
    (d / "logs").mkdir()
    if checkpoints == "empty":
        (d / "checkpoints").mkdir()
    elif checkpoints == "absent":
        pass
    elif checkpoints == "unexpected":
        (d / "checkpoints").mkdir()
        (d / "checkpoints" / "best_val_mse.pt").write_bytes(b"pt")

    files = {
        "run_status.json": {
            "run_key": spec["run_key"], "state": "COMPLETED",
            "spec": {"arm": "baseline", "model": spec["model"],
                     "parent_model": spec["parent_model"],
                     "horizon": spec["horizon"], "seed": "n/a",
                     "wave": 1, "control": ""},
            "stochastic_seed_applicable": False,
            "checkpoint_applicable": False, "elapsed_seconds": 3.9},
        "resource_usage.json": {
            "stochastic_seed_applicable": False,
            "checkpoint_applicable": False, "train_seconds": 0.0,
            "gpu_hours": 0.0, "peak_gpu_memory_bytes": None},
        "source_manifest.json": {"version": "innov-v3.19-test"},
        "split_manifest.json": {"train": 717, "val": 102, "test": 206},
        "scaler_metadata.json": {"fit_on": "train"},
        "prompt_statistics_metadata.json": {"fit_on": "train"},
        "config_resolved.yaml": "# frozen config\n",
        "environment.txt": "python=3.9 torch=2\n",
        # clean_runner writes git_commit.txt EMPTY in a frozen (non-git) root
        "git_commit.txt": "",
        "predictions/validation_predictions.csv": "y_hat\n0.1\n",
        "metrics/paper_aligned_full_output_metrics.json": {"mse": 1.0},
        "metrics/ilitotal_fixed_step_metrics.json": {"steps": [0, 1, 2, 3]},
        "metrics/ilitotal_full_horizon_metrics.json": {"mse": 1.0},
        "metrics/pte_pie_metrics.json": {"pte": 1, "pie": 0.25},
    }
    for r in drop:
        files.pop(r, None)
    if mutate:
        mutate(files)
    for r, content in files.items():
        p = d / r
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(content) if r.endswith(".json")
                     else str(content), encoding="utf-8")
    return d


def _run_finalize(tmp_path: Path, spec: dict, run_dir: Path,
                  durable_name: str = "durable") -> dict:
    durable_root = tmp_path / durable_name
    out = tmp_path / durable_name / f"{spec['run_key']}.storage_verification.json"
    # a deployment root mirroring the real isolated one: the registry is
    # resolved through INNOVATION_DEPLOYMENT_ROOT (the autouse fixture), so
    # this only feeds the isolation probe — which must see NO test_evaluations
    # (the local repo DOES carry the older innovation line's test_evaluations,
    # and the probe correctly fails closed on it).
    fake_root = tmp_path / "deployment_root"
    fake_root.mkdir(exist_ok=True)
    rc = FR.main([
        "--run-key", spec["run_key"],
        "--deployment-root", str(fake_root),
        "--run-dir", str(run_dir),
        "--durable-root", str(durable_root),
        "--out", str(out),
        "--original-job-id", ORIGINAL_JOB,
    ])
    rec = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else {}
    return {"rc": rc, "record": rec, "durable": durable_root / spec["run_key"],
            "out": out}


def _spec_for(run_key: str) -> dict:
    return next(s for s in BASELINE_SPECS if s["run_key"] == run_key)


# ── the frozen authority ─────────────────────────────────────────────────
def test_spec_authority_is_the_frozen_arm():
    """checkpoint_applicable is derived from the frozen spec's arm."""
    for s in BASELINE_SPECS:
        info = CC.resolve_run_key(s["run_key"])
        assert FR.spec_checkpoint_applicable(info) is False
    for arm in ("primary", "ablation", "negative_control"):
        info = {"arm": arm}
        assert FR.spec_checkpoint_applicable(info) is True


def test_both_models_all_four_horizons_are_covered():
    assert {s["model"] for s in BASELINE_SPECS} == \
        {"last_value_naive", "seasonal_naive"}
    assert sorted({s["horizon"] for s in BASELINE_SPECS}) == [24, 36, 48, 60]


# ── the exact D15 row: happy path (empty checkpoints dir) ────────────────
def test_row_321_last_value_naive_empty_checkpoints_dir_accepts(tmp_path):
    spec = _spec_for(ROW321)
    run = _make_run(tmp_path, spec, checkpoints="empty")
    r = _run_finalize(tmp_path, spec, run)
    assert r["rc"] == 0, r["record"].get("detail")
    assert r["record"]["passed"] is True
    assert r["record"]["arm"] == "baseline"
    assert r["record"]["reason"] == BF.BASELINE_REASON
    # checkpoint checks are EXPLICITLY not_applicable — present, not missing
    for c in SV.CHECKPOINT_ONLY_CHECKS:
        assert r["record"]["checks"][c] == SV.NOT_APPLICABLE
    # the non-checkpoint checks are all literally True
    for c in SV.COMMON_CHECKS:
        assert r["record"]["checks"][c] is True
    for c in SV.BASELINE_ONLY_CHECKS:
        assert r["record"]["checks"][c] is True
    # evidence retains the original training job identity
    assert r["record"]["evidence"]["source_job_id"] == ORIGINAL_JOB
    assert r["record"]["evidence"]["reason"] == BF.BASELINE_REASON
    assert r["record"]["evidence"]["checkpoint_applicable"] is False
    assert r["record"]["evidence"]["stochastic_seed_applicable"] is False
    for e in SV.CHECKPOINT_ONLY_EVIDENCE:
        assert r["record"]["evidence"][e] == SV.NOT_APPLICABLE


def test_empty_git_commit_is_legitimate_provenance(tmp_path):
    """clean_runner writes git_commit.txt EMPTY in a frozen (non-git) root:
    presence is the correct requirement, and an empty file must still accept."""
    spec = _spec_for(ROW321)
    run = _make_run(tmp_path, spec, checkpoints="empty")   # fixture: empty git
    assert (run / "git_commit.txt").read_text(encoding="utf-8") == ""
    r = _run_finalize(tmp_path, spec, run)
    assert r["rc"] == 0, r["record"].get("detail")
    assert r["record"]["checks"]["provenance_complete"] is True


def test_row_321_absent_checkpoints_dir_also_accepts(tmp_path):
    spec = _spec_for(ROW321)
    run = _make_run(tmp_path, spec, checkpoints="absent")
    r = _run_finalize(tmp_path, spec, run)
    assert r["rc"] == 0, r["record"].get("detail")
    assert r["record"]["passed"] is True


@pytest.mark.parametrize("run_key",
                         [s["run_key"] for s in BASELINE_SPECS])
def test_every_baseline_row_accepts(tmp_path, run_key):
    spec = _spec_for(run_key)
    run = _make_run(tmp_path, spec, checkpoints="empty")
    r = _run_finalize(tmp_path, spec, run)
    assert r["rc"] == 0, r["record"].get("detail")
    assert r["record"]["passed"] is True


# ── fail-closed scenarios ────────────────────────────────────────────────
def test_unexpected_checkpoint_fails_closed_and_is_recorded(tmp_path):
    spec = _spec_for(ROW321)
    run = _make_run(tmp_path, spec, checkpoints="unexpected")
    r = _run_finalize(tmp_path, spec, run)
    assert r["rc"] == 1
    assert r["record"]["passed"] is False
    assert r["record"]["checks"]["no_unexpected_checkpoint"] is False
    assert r["record"]["unexpected_checkpoint_entries"] == \
        ["checkpoints/best_val_mse.pt"]
    # nothing published
    assert not r["durable"].exists()


def test_missing_prediction_fails_closed(tmp_path):
    spec = _spec_for(ROW321)
    run = _make_run(tmp_path, spec,
                    drop=("predictions/validation_predictions.csv",))
    r = _run_finalize(tmp_path, spec, run)
    assert r["rc"] == 1
    assert r["record"]["checks"]["artifact_completeness"] is False
    assert not r["durable"].exists()


@pytest.mark.parametrize("metric", BF.BASELINE_METRICS)
def test_missing_each_metric_fails_closed(tmp_path, metric):
    spec = _spec_for(ROW321)
    run = _make_run(tmp_path, spec, drop=(f"metrics/{metric}",))
    r = _run_finalize(tmp_path, spec, run)
    assert r["rc"] == 1
    assert r["record"]["checks"]["artifact_completeness"] is False


@pytest.mark.parametrize("prov",
                         ["source_manifest.json", "split_manifest.json",
                          "scaler_metadata.json",
                          "prompt_statistics_metadata.json",
                          "config_resolved.yaml", "environment.txt",
                          "git_commit.txt"])
def test_missing_each_provenance_fails_closed(tmp_path, prov):
    spec = _spec_for(ROW321)
    run = _make_run(tmp_path, spec, drop=(prov,))
    r = _run_finalize(tmp_path, spec, run)
    assert r["rc"] == 1
    assert r["record"]["checks"]["provenance_complete"] is False


@pytest.mark.parametrize("mutate,check", [
    (lambda f: f.__setitem__("resource_usage.json", "not-json"),
     "resource_usage_semantics_ok"),
    (lambda f: f["resource_usage.json"].__setitem__("checkpoint_applicable",
                                                    True),
     "checkpoint_applicable_false"),
    (lambda f: f["resource_usage.json"].__setitem__(
        "stochastic_seed_applicable", True),
     "stochastic_seed_applicable_false"),
    (lambda f: f["resource_usage.json"].__setitem__("train_seconds", 12.5),
     "resource_usage_semantics_ok"),
    (lambda f: f["resource_usage.json"].__setitem__("gpu_hours", 0.01),
     "resource_usage_semantics_ok"),
    (lambda f: f["resource_usage.json"].pop("train_seconds"),
     "resource_usage_semantics_ok"),
    (lambda f: f["run_status.json"].__setitem__("state", "FAILED"),
     "run_status_completed"),
    (lambda f: f["run_status.json"].__setitem__("checkpoint_applicable",
                                                True),
     "checkpoint_applicable_false"),
])
def test_malformed_evidence_fails_closed(tmp_path, mutate, check):
    spec = _spec_for(ROW321)
    run = _make_run(tmp_path, spec, mutate=mutate)
    r = _run_finalize(tmp_path, spec, run)
    assert r["rc"] == 1, f"{check} should have failed closed"
    assert r["record"]["checks"][check] is False
    assert not r["durable"].exists()


# ── atomic publication + content ─────────────────────────────────────────
def test_atomic_publication_manifest_last_and_content_match(tmp_path):
    spec = _spec_for(ROW321)
    run = _make_run(tmp_path, spec, checkpoints="empty")
    r = _run_finalize(tmp_path, spec, run)
    assert r["rc"] == 0
    dur = r["durable"]
    assert (dur / BF.MANIFEST_NAME).is_file()
    # no staging or publish leftovers
    assert not Path(str(dur) + ".staging").exists()
    assert not Path(str(dur) + ".publish").exists()
    # the durable package carries the evidence, not a checkpoint
    assert not (dur / "compact.safetensors").exists()
    assert not (dur / "checkpoints").exists()
    m = json.loads((dur / BF.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert m["run_key"] == spec["run_key"]
    assert m["reason"] == BF.BASELINE_REASON
    assert m["checkpoint_applicable"] is False
    assert m["checkpoint_file_sha256"] == "not_applicable"
    assert m["checkpoint_canonical_tensor_sha256"] == "not_applicable"
    assert m["original_job_id"] == ORIGINAL_JOB
    for rel in BF.BASELINE_REQUIRED:
        assert (dur / rel).is_file(), rel
    for rel in BF.BASELINE_METRICS:
        assert (dur / "metrics" / rel).is_file(), rel
    # content is byte-identical to the source evidence
    src_csv = (run / "predictions" / "validation_predictions.csv").read_bytes()
    assert (dur / "predictions" / "validation_predictions.csv"
            ).read_bytes() == src_csv


def test_source_run_dir_is_never_mutated_by_the_baseline_branch(tmp_path):
    """No checkpoint deletion, no source mutation: the scratch evidence of
    job 572649 must survive the repair-finalize untouched."""
    spec = _spec_for(ROW321)
    run = _make_run(tmp_path, spec, checkpoints="empty")
    before = sorted(str(p.relative_to(run)) for p in run.rglob("*"))
    r = _run_finalize(tmp_path, spec, run)
    assert r["rc"] == 0
    after = sorted(str(p.relative_to(run)) for p in run.rglob("*"))
    assert before == after


# ── stale staging is quarantined, never reused ───────────────────────────
def test_stale_staging_is_quarantined_not_reused(tmp_path):
    spec = _spec_for(ROW321)
    run = _make_run(tmp_path, spec, checkpoints="empty")
    durable_root = tmp_path / "durable"
    stale = durable_root / (spec["run_key"] + ".staging")
    stale.mkdir(parents=True)
    sentinel = stale / "POISON.txt"
    sentinel.write_text("stale", encoding="utf-8")

    out = durable_root / f"{spec['run_key']}.storage_verification.json"
    fake_root = tmp_path / "deployment_root"
    fake_root.mkdir(exist_ok=True)
    rc = FR.main(["--run-key", spec["run_key"],
                  "--deployment-root", str(fake_root),
                  "--run-dir", str(run),
                  "--durable-root", str(durable_root),
                  "--out", str(out),
                  "--original-job-id", ORIGINAL_JOB])
    assert rc == 0
    rec = json.loads(out.read_text(encoding="utf-8"))
    assert rec["passed"] is True
    # the stale staging was moved aside and its content preserved
    assert rec["quarantined_stale_staging"]
    q = Path(rec["quarantined_stale_staging"])
    assert (q / "POISON.txt").read_text(encoding="utf-8") == "stale"
    assert ".stale_staging" in str(q)
    # the published package does NOT contain the poison
    dur = durable_root / spec["run_key"]
    assert not (dur / "POISON.txt").exists()
    assert not stale.exists()


# ── idempotent repair-finalize ──────────────────────────────────────────
def test_repair_finalize_is_idempotent(tmp_path):
    spec = _spec_for(ROW321)
    run = _make_run(tmp_path, spec, checkpoints="empty")
    r1 = _run_finalize(tmp_path, spec, run, durable_name="d1")
    assert r1["rc"] == 0
    manifest_before = (r1["durable"] / BF.MANIFEST_NAME).read_bytes()

    # second run over the SAME source and durable root must succeed WITHOUT
    # republishing (verify-only) and leave the published bytes untouched
    out2 = tmp_path / "d1" / "rec2.json"
    fake_root = tmp_path / "deployment_root"
    fake_root.mkdir(exist_ok=True)
    rc2 = FR.main(["--run-key", spec["run_key"],
                   "--deployment-root", str(fake_root),
                   "--run-dir", str(run),
                   "--durable-root", str(tmp_path / "d1"),
                   "--out", str(out2),
                   "--original-job-id", ORIGINAL_JOB])
    assert rc2 == 0
    rec2 = json.loads(out2.read_text(encoding="utf-8"))
    assert rec2["passed"] is True
    assert rec2.get("idempotent") is True
    assert (r1["durable"] / BF.MANIFEST_NAME).read_bytes() == manifest_before


# ── storage-verification schema semantics ────────────────────────────────
def _baseline_checks(**over):
    c = {k: True for k in SV.COMMON_CHECKS + SV.BASELINE_ONLY_CHECKS}
    c.update({k: SV.NOT_APPLICABLE for k in SV.CHECKPOINT_ONLY_CHECKS})
    c.update(over)
    return c


def _baseline_evidence(**over):
    e = {"run_key": "k", "model": "last_value_naive", "horizon": 24,
         "source_run_key": "k", "source_job_id": "572649",
         "source_training_attempt": 1,
         "export_implementation_version": "t", "comparison_mode":
         "baseline_no_checkpoint",
         "file_sha256": SV.NOT_APPLICABLE,
         "canonical_tensor_sha256": SV.NOT_APPLICABLE,
         "source_full_checkpoint_sha256": SV.NOT_APPLICABLE,
         "canonical_hash_schema": SV.NOT_APPLICABLE,
         "reason": BF.BASELINE_REASON, "checkpoint_applicable": False,
         "stochastic_seed_applicable": False}
    e.update(over)
    return e


def test_schema_baseline_record_passes():
    sv = SV.StorageVerification(_baseline_checks(), _baseline_evidence(),
                                arm="baseline", reason=BF.BASELINE_REASON)
    assert sv.passed is True


def test_schema_missing_checkpoint_check_is_a_hard_fail():
    c = _baseline_checks()
    del c["compact_file_present"]        # must be present, even as sentinel
    sv = SV.StorageVerification(c, _baseline_evidence(), arm="baseline",
                                reason=BF.BASELINE_REASON)
    assert sv.passed is False
    assert sv.verdict()[1] == SV.MISSING


def test_schema_baseline_claiming_checkpoint_true_fails():
    c = _baseline_checks(compact_file_present=True)
    sv = SV.StorageVerification(c, _baseline_evidence(), arm="baseline",
                                reason=BF.BASELINE_REASON)
    assert sv.passed is False


def test_schema_baseline_missing_noncheckpoint_true_fails():
    c = _baseline_checks(artifact_completeness=False)
    sv = SV.StorageVerification(c, _baseline_evidence(), arm="baseline",
                                reason=BF.BASELINE_REASON)
    assert sv.passed is False


def test_schema_baseline_wrong_reason_rejected():
    with pytest.raises(SV.StorageVerificationError):
        SV.StorageVerification(_baseline_checks(), _baseline_evidence(),
                               arm="baseline", reason="some_other_reason")


def test_schema_baseline_evidence_checkpoint_hash_must_be_sentinel():
    e = _baseline_evidence(file_sha256="abc123")
    sv = SV.StorageVerification(_baseline_checks(), e, arm="baseline",
                                reason=BF.BASELINE_REASON)
    assert sv.passed is False


def test_schema_stochastic_sentinels_mirror():
    c = {k: True for k in SV.COMMON_CHECKS + SV.CHECKPOINT_ONLY_CHECKS}
    c.update({k: SV.NOT_APPLICABLE for k in SV.BASELINE_ONLY_CHECKS})
    e = {"run_key": "k", "model": "nlinear", "horizon": 24,
         "source_run_key": "k", "source_job_id": "1",
         "source_training_attempt": 1,
         "export_implementation_version": "t", "comparison_mode": "same_source",
         "file_sha256": "a" * 64, "canonical_tensor_sha256": "b" * 64,
         "source_full_checkpoint_sha256": "c" * 64,
         "canonical_hash_schema": "canonical-v1",
         "reason": SV.NOT_APPLICABLE, "checkpoint_applicable":
         SV.NOT_APPLICABLE, "stochastic_seed_applicable": SV.NOT_APPLICABLE}
    sv = SV.StorageVerification(c, e, arm="primary")
    assert sv.passed is True
    # a stochastic row claiming a baseline-only check True is inconsistent
    c2 = dict(c, no_unexpected_checkpoint=True)
    sv2 = SV.StorageVerification(c2, e, arm="primary")
    assert sv2.passed is False


def test_schema_legacy_records_still_validate():
    """Backward compatibility: the 320 accepted v3.18 records (13 checks,
    arm absent) must keep validating under the extended schema."""
    c = {k: True for k in SV.LEGACY_REQUIRED_CHECKS}
    e = {"run_key": "k", "model": "nlinear", "horizon": 24,
         "file_sha256": "a" * 64, "canonical_tensor_sha256": "b" * 64,
         "source_full_checkpoint_sha256": "c" * 64,
         "canonical_hash_schema": "canonical-v1",
         "source_run_key": "k", "source_job_id": "1",
         "source_training_attempt": 1,
         "export_implementation_version": "t", "comparison_mode": "same_source"}
    sv = SV.StorageVerification(c, e)
    assert sv.passed is True
    # and a legacy missing check still fails closed
    c2 = dict(c)
    del c2["restoration_exact"]
    assert SV.StorageVerification(c2, e).passed is False


def test_storage_verdict_dict_roundtrip():
    sv = SV.StorageVerification(_baseline_checks(), _baseline_evidence(),
                                arm="baseline", reason=BF.BASELINE_REASON)
    assert SV.storage_verdict(sv.to_dict()) is True
    assert SV.storage_verdict({"checks": {}}) is False


# ── source-level guards on the driver ───────────────────────────────────
def test_driver_never_references_the_checkpoint_file_in_the_baseline_path():
    src = (REPO / "scripts" / "innovation" / "finalize_row.py"
           ).read_text(encoding="utf-8")
    i = src.index("def finalize_baseline(")
    j = src.index("def finalize_stochastic(")
    baseline_body = src[i:j]
    assert "best_val_mse.pt" not in baseline_body
    assert "export_compact" not in baseline_body
    assert "restore_and_compare" not in baseline_body
    # the sentinel reason is wired through
    assert BF.BASELINE_REASON in baseline_body


def test_driver_branches_on_spec_checkpoint_applicability():
    src = (REPO / "scripts" / "innovation" / "finalize_row.py"
           ).read_text(encoding="utf-8")
    assert "spec_checkpoint_applicable(info)" in src
    i = src.index("def main(")
    tail = src[i:]
    assert "finalize_stochastic(" in tail and "finalize_baseline(" in tail
