"""
Autonomous controller tests (innov-v2.5)
=======================================

Tests the pure orchestration logic of ``hpc_scripts/autonomous/state.py`` and the
controller's 12 hard requirements, per-stage budgeting, the one-time Test gate, the
stage ceiling, and crash-free resume (no duplicate submission).

The controller module lives OUTSIDE the frozen runtime hash, so importing it here does
not change the snapshot aggregate.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

import pytest

_HERE = os.path.abspath(__file__)
# tests/innovation/<file>.py -> project root is parents[2]
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
_AUTON = os.path.join(_ROOT, "hpc_scripts", "autonomous")
sys.path.insert(0, _AUTON)

import state  # noqa: E402

PY = sys.executable


def _plan(tmp, ceiling="K", stages=None):
    if stages is None:
        stages = [
            {"key": "A", "name": "verify_gate", "submit_mode": "local",
             "jobs": []},
            {"key": "B", "name": "four_pilots", "submit_mode": "slurm",
             "jobs": [
                 {"model": "gpt2_miflu", "text_encoder": "gpt2",
                  "fusion": "concat_projection", "horizon": 24, "seed": 42,
                  "epochs": 20, "stage": "pilot"},
                 {"model": "dlinear", "text_encoder": "none",
                  "fusion": "identity", "horizon": 24, "seed": 42,
                  "epochs": 20, "stage": "pilot"},
             ]},
            {"key": "D", "name": "screening", "submit_mode": "slurm",
             "expand": {"models": ["dlinear", "nlinear"], "text_encoders": ["none"],
                        "fusions": ["identity"], "horizons": [24, 60],
                        "seeds": [42, 43, 44], "epochs": 20, "stage": "screening"}},
            {"key": "L", "name": "test", "submit_mode": "slurm", "gated": True,
             "jobs": []},
        ]
    p = {
        "protocol_version": "innov-v2.0",
        "implementation_source_version": "innov-v2.5",
        "authorization_ceiling": ceiling,
        "stages": stages,
    }
    path = os.path.join(tmp, "stage_plan.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(p, f)
    return path


# ── requirements 10 / ceiling ───────────────────────────────────────────────────
def test_stage_within_ceiling():
    assert state.stage_within_ceiling("A", "K")
    assert state.stage_within_ceiling("K", "K")
    assert not state.stage_within_ceiling("L", "K")     # Test excluded by ceiling
    assert not state.stage_within_ceiling("N", "K")
    assert state.stage_within_ceiling("L", "L")
    assert not state.stage_within_ceiling("Z", "K")      # unknown stage


# ── job identity / expansion ─────────────────────────────────────────────────
def test_job_key_and_run_id():
    job = {"model": "gpt2_miflu", "text_encoder": "gpt2",
           "fusion": "concat_projection", "horizon": 24, "seed": 42}
    assert state.job_key("B", job) == "B|gpt2_miflu|gpt2|concat_projection|L24|s42"
    assert state.run_id_for(job) == "national_ili__gpt2_miflu__gpt2__concat_projection__L24__s42"


def test_generate_stage_jobs_explicit_and_expand():
    plan = state.load_stage_plan(_plan(tempfile.mkdtemp()))
    b = state.get_stage(plan, "B")
    assert len(state.generate_stage_jobs(b)) == 2
    d = state.get_stage(plan, "D")
    jobs = state.generate_stage_jobs(d)
    # 2 models x 1 enc x 1 fusion x 2 horizons x 3 seeds = 12
    assert len(jobs) == 12
    assert all(j["stage"] == "screening" for j in jobs)
    # a LOCAL gate stage with no explicit jobs yields ONE synthetic step so the
    # controller executes it in order instead of silently skipping it
    a = state.get_stage(plan, "A")
    a_jobs = state.generate_stage_jobs(a)
    assert len(a_jobs) == 1 and a_jobs[0].get("local") is True
    assert state.job_key("A", a_jobs[0]) == "A|local"
    assert state.run_id_for(a_jobs[0]) == "local__verify_gate"


# ── requirement 9: resume without duplicate submission ─────────────────────────
def test_resume_does_not_duplicate():
    tmp = tempfile.mkdtemp()
    plan = _plan(tmp)
    ledger = os.path.join(tmp, "job_ledger.csv")
    # the FIRST pending step is the LOCAL verify gate A (local stages are run,
    # not skipped), then the first B pilot job
    nxt = state.next_pending_job(state.load_stage_plan(plan), [], "K")
    assert nxt["stage_key"] == "A" and nxt["job_key"] == "A|local"
    state.append_ledger_row(ledger, {"job_id": "LOCAL-A", "stage": "A",
                                     "model_key": "local", "horizon": "na",
                                     "seed": "na", "submitted_utc": "t",
                                     "state": "COMPLETED", "exit_code": "0:0",
                                     "node": "", "run_id": "local__verify_gate",
                                     "notes": "KEY=A|local"})
    rows = state.load_ledger(ledger)
    nxt = state.next_pending_job(state.load_stage_plan(plan), rows, "K")
    assert nxt["stage_key"] == "B"
    first_key = nxt["job_key"]
    # record it as COMPLETED in the ledger
    state.append_ledger_row(ledger, {"job_id": "123", "stage": "B",
                                     "model_key": "gpt2_miflu", "horizon": 24,
                                     "seed": 42, "submitted_utc": "t",
                                     "state": "COMPLETED", "exit_code": "0:0",
                                     "node": "n", "run_id": "r",
                                     "notes": "KEY=" + first_key})
    rows = state.load_ledger(ledger)
    # next pending must skip the completed job and return the second B job
    nxt2 = state.next_pending_job(state.load_stage_plan(plan), rows, "K")
    assert nxt2["job_key"] != first_key
    # after marking ALL B jobs done, next is D (still within ceiling)
    for j in state.generate_stage_jobs(state.get_stage(state.load_stage_plan(plan), "B")):
        state.append_ledger_row(ledger, {"job_id": "x", "stage": "B",
                                         "model_key": j["model"], "horizon": j["horizon"],
                                         "seed": j["seed"], "submitted_utc": "t",
                                         "state": "COMPLETED", "exit_code": "0:0",
                                         "node": "n", "run_id": "r",
                                         "notes": "KEY=" + state.job_key("B", j)})
    rows = state.load_ledger(ledger)
    nxt3 = state.next_pending_job(state.load_stage_plan(plan), rows, "K")
    assert nxt3["stage_key"] == "D"
    # L (Test) is beyond ceiling K -> never returned
    assert nxt3["stage_key"] != "L"


def test_append_ledger_is_append_only():
    tmp = tempfile.mkdtemp()
    ledger = os.path.join(tmp, "job_ledger.csv")
    state.append_ledger_row(ledger, {"job_id": "1", "stage": "B", "model_key": "m",
                                     "horizon": 24, "seed": 42, "submitted_utc": "t",
                                     "state": "PD", "exit_code": "", "node": "",
                                     "run_id": "r", "notes": "KEY=k"})
    state.append_ledger_row(ledger, {"job_id": "2", "stage": "B", "model_key": "m",
                                     "horizon": 24, "seed": 42, "submitted_utc": "t",
                                     "state": "COMPLETED", "exit_code": "0:0", "node": "n",
                                     "run_id": "r", "notes": "KEY=k"})
    rows = state.load_ledger(ledger)
    assert len(rows) == 2
    assert rows[0]["job_id"] == "1" and rows[1]["job_id"] == "2"


# ── requirement 5/6: artifact validation triggers ──────────────────────────────
def _run_dir(tmp, **over):
    rd = os.path.join(tmp, "runs", "national_ili__m__none__identity__L24__s42")
    os.makedirs(os.path.join(rd, "checkpoints"), exist_ok=True)
    status = {"status": "ok", "test_artifacts_written": False,
              "test_access_allowed": False,
              "source_snapshot_sha256": "abc", "experiment_stage": "pilot"}
    status.update(over)
    with open(os.path.join(rd, "run_status.json"), "w", encoding="utf-8") as f:
        json.dump(status, f)
    with open(os.path.join(rd, "checkpoints", "checkpoint_manifest.json"),
              "w", encoding="utf-8") as f:
        json.dump({"ok": True}, f)
    return rd


def test_validate_run_ok():
    tmp = tempfile.mkdtemp()
    rd = _run_dir(tmp)
    res = state.validate_run(run_dir=rd, manifest_aggregate="abc",
                             expected_stage="pilot")
    assert res["ok"] is True


def test_validate_run_failures():
    tmp = tempfile.mkdtemp()
    # missing run_status
    res = state.validate_run(run_dir=os.path.join(tmp, "missing"),
                             manifest_aggregate="abc", expected_stage="pilot")
    assert res["ok"] is False and res["reason"] == "missing_run_status"
    # status not ok
    rd = _run_dir(tmp, status="failed")
    res = state.validate_run(run_dir=rd, manifest_aggregate="abc",
                             expected_stage="pilot")
    assert res["ok"] is False and res["reason"] == "status_not_ok"
    # test artifact leak
    rd = _run_dir(tmp, test_artifacts_written=True)
    res = state.validate_run(run_dir=rd, manifest_aggregate="abc",
                             expected_stage="pilot")
    assert res["ok"] is False and res["reason"] == "test_artifact_leak"
    # test access violation
    rd = _run_dir(tmp, test_access_allowed=True)
    res = state.validate_run(run_dir=rd, manifest_aggregate="abc",
                             expected_stage="pilot")
    assert res["ok"] is False and res["reason"] == "test_access_violation"
    # source mismatch
    rd = _run_dir(tmp)
    res = state.validate_run(run_dir=rd, manifest_aggregate="DIFFERENT",
                             expected_stage="pilot")
    assert res["ok"] is False and res["reason"] == "source_mismatch"
    # stage mismatch
    rd = _run_dir(tmp)
    res = state.validate_run(run_dir=rd, manifest_aggregate="abc",
                             expected_stage="screening")
    assert res["ok"] is False and res["reason"] == "stage_mismatch"
    # missing checkpoint manifest
    rd = _run_dir(tmp)
    os.remove(os.path.join(rd, "checkpoints", "checkpoint_manifest.json"))
    res = state.validate_run(run_dir=rd, manifest_aggregate="abc",
                             expected_stage="pilot")
    assert res["ok"] is False and res["reason"] == "missing_checkpoint_manifest"


# ── per-stage budgeting ────────────────────────────────────────────────────────
def test_compute_budget_within_and_over():
    ok = state.compute_budget(job_count=4, avg_minutes=30, storage_gb_free=100.0,
                              queue_pending_ok=True, source_version="innov-v2.5",
                              required_source_version="innov-v2.5", deps_ok=True,
                              repair_cascades_used=0, max_repair_cascades=4,
                              protocol_amendments_used=0, max_protocol_amendments=1)
    assert ok["within_limits"] is True
    assert ok["gpu_hours_estimate"] == 2.0
    # source version mismatch -> over limits
    bad = state.compute_budget(job_count=4, avg_minutes=30, storage_gb_free=100.0,
                               queue_pending_ok=True, source_version="innov-v2.4",
                               required_source_version="innov-v2.5", deps_ok=True,
                               repair_cascades_used=0, max_repair_cascades=4,
                               protocol_amendments_used=0, max_protocol_amendments=1)
    assert bad["within_limits"] is False and bad["source_ok"] is False
    # too many repair cascades -> over limits
    bad2 = state.compute_budget(job_count=4, avg_minutes=30, storage_gb_free=100.0,
                                queue_pending_ok=True, source_version="innov-v2.5",
                                required_source_version="innov-v2.5", deps_ok=True,
                                repair_cascades_used=5, max_repair_cascades=4,
                                protocol_amendments_used=0, max_protocol_amendments=1)
    assert bad2["within_limits"] is False
    assert state.budget_ok(ok) is True
    assert state.budget_ok(bad) is False


# ── one-time Test gate (requirement: never on time remaining) ──────────────────
def test_test_gate_closed_until_resolved():
    cm = {"all_mandatory_resolved": False,
          "mandatory_items": [{"id": "x", "resolved": False}]}
    assert state.test_gate_open(cm, {"passed": True}) is False
    cm2 = {"all_mandatory_resolved": True,
           "mandatory_items": [{"id": "x", "resolved": True}]}
    assert state.test_gate_open(cm2, {"passed": True}) is True
    # freeze audit not passed -> closed even if matrix resolved
    assert state.test_gate_open(cm2, {"passed": False}) is False
    # no completion matrix -> closed
    assert state.test_gate_open(None, {"passed": True}) is False


# ── CLI subcommands (key=value, no jq) ─────────────────────────────────────────
def _cli(args):
    return subprocess.run([PY, os.path.join(_AUTON, "state.py"), *args],
                          capture_output=True, text=True)


def test_cli_budget_and_ceiling_and_gate():
    r = _cli(["ceiling", "--stage", "L", "--ceiling", "K"])
    assert "WITHIN=no" in r.stdout
    r = _cli(["ceiling", "--stage", "B", "--ceiling", "K"])
    assert "WITHIN=yes" in r.stdout

    r = _cli(["budget", "--job-count", "4", "--avg-min", "30", "--storage-gb", "100",
              "--queue-ok", "1", "--source-ver", "innov-v2.5", "--req-ver", "innov-v2.5",
              "--deps-ok", "1", "--repair-used", "0", "--repair-max", "4",
              "--amend-used", "0", "--amend-max", "1"])
    assert "WITHIN_LIMITS=yes" in r.stdout

    cm = os.path.join(tempfile.mkdtemp(), "completion_matrix.json")
    with open(cm, "w", encoding="utf-8") as f:
        json.dump({"all_mandatory_resolved": False, "mandatory_items": []}, f)
    fa = os.path.join(tempfile.mkdtemp(), "freeze_audit.json")
    with open(fa, "w", encoding="utf-8") as f:
        json.dump({"passed": False}, f)
    r = _cli(["gate", "--completion", cm, "--freeze-audit", fa])
    assert "GATE=closed" in r.stdout


def test_cli_plan_sequence_and_validate_run():
    tmp = tempfile.mkdtemp()
    plan = _plan(tmp)
    r = _cli(["plan-sequence", "--plan", plan, "--ceiling", "K"])
    assert r.returncode == 0
    # 2 pilot jobs + 12 screening jobs = 14 lines, all PENDING (no ledger)
    seqs = [l for l in r.stdout.splitlines() if l.startswith("SEQ|")]
    # 1 local verify gate (A) + 2 pilot jobs (B) + 12 screening jobs (D) = 15
    assert len(seqs) == 15
    assert any(l.startswith("SEQ|A|local|") for l in seqs)
    # Test (L) must NOT appear because ceiling=K
    assert not any("|L|" in l for l in seqs)

    rd = _run_dir(tmp)
    r = _cli(["validate-run", "--run-dir", rd, "--manifest-aggregate", "abc",
              "--expected-stage", "pilot"])
    assert "OK=yes" in r.stdout


def test_cli_next_job_resume():
    tmp = tempfile.mkdtemp()
    plan = _plan(tmp)
    ledger = os.path.join(tmp, "job_ledger.csv")
    # the LOCAL verify gate A is the first step (local stages are not skipped)
    r = _cli(["next-job", "--plan", plan, "--ledger", ledger, "--ceiling", "K"])
    assert "STAGE_KEY=A" in r.stdout and "STAGE_MODE=local" in r.stdout
    # mark A completed -> the first B pilot job becomes next
    state.append_ledger_row(ledger, {"job_id": "LOCAL-A", "stage": "A",
                                     "model_key": "local", "horizon": "na",
                                     "seed": "na", "submitted_utc": "t",
                                     "state": "COMPLETED", "exit_code": "0:0",
                                     "node": "", "run_id": "local__verify_gate",
                                     "notes": "KEY=A|local"})
    r = _cli(["next-job", "--plan", plan, "--ledger", ledger, "--ceiling", "K"])
    assert "STAGE_KEY=B" in r.stdout and "RESULT=PENDING" in r.stdout
    # mark the first B job COMPLETED, then next-job must skip it
    nxt = state.next_pending_job(state.load_stage_plan(plan),
                                 state.load_ledger(ledger), "K")
    state.append_ledger_row(ledger, {"job_id": "1", "stage": "B",
                                     "model_key": "gpt2_miflu", "horizon": 24,
                                     "seed": 42, "submitted_utc": "t",
                                     "state": "COMPLETED", "exit_code": "0:0",
                                     "node": "n", "run_id": "r",
                                     "notes": "KEY=" + nxt["job_key"]})
    r = _cli(["next-job", "--plan", plan, "--ledger", ledger, "--ceiling", "K"])
    assert "KEY=B|gpt2_miflu" not in r.stdout


# ── requirement 1: single-instance lock (flock semantics) ───────────────────────
def test_single_instance_lock():
    fcntl = pytest.importorskip("fcntl")  # Unix-only; controller uses flock on Linux
    tmp = tempfile.mkdtemp()
    lock = os.path.join(tmp, ".controller.lock")
    fd1 = open(lock, "w")
    fd2 = open(lock, "w")
    try:
        fcntl.flock(fd1, fcntl.LOCK_EX | fcntl.LOCK_NB)  # acquire
        # second holder must fail (non-blocking)
        with pytest.raises(OSError):
            fcntl.flock(fd2, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        fcntl.flock(fd1, fcntl.LOCK_UN)
        fd1.close(); fd2.close()


if __name__ == "__main__":
    test_stage_within_ceiling()
    test_job_key_and_run_id()
    test_generate_stage_jobs_explicit_and_expand()
    test_resume_does_not_duplicate()
    test_append_ledger_is_append_only()
    test_validate_run_ok()
    test_validate_run_failures()
    test_compute_budget_within_and_over()
    test_test_gate_closed_until_resolved()
    test_cli_budget_and_ceiling_and_gate()
    test_cli_plan_sequence_and_validate_run()
    test_cli_next_job_resume()
    test_single_instance_lock()
    print("[test_autonomous_controller] OK")
