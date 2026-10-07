"""
Pilot script safety tests (innov-v2.4)
======================================

Closes `FORBIDDEN_CD_TARGET_IN_GENERATED_SCRIPTS`: every generated Pilot /
Worker / Submit script must run from an EXPLICIT isolated deployment root, must
never `cd` into (or import from) the original reproduction repository, and the
submit driver must be serial, `afterok`-chained and fail-stop.

The forbidden string may appear only as a comparison CONSTANT. Any executable
`cd`, python path, runner working directory or import path using it must fail.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402

from innovation import runtime_guard as RG  # noqa: E402
from innovation.paths import (BANNED_RUNTIME_ROOT,  # noqa: E402
                              IMPLEMENTATION_SOURCE_VERSION, PROJECT_ROOT)

HPC = os.path.join(PROJECT_ROOT, "hpc_scripts")
PILOTS = [os.path.join(HPC, "pilot_gpt2_miflu_L24_seed42.sh"),
          os.path.join(HPC, "pilot_dlinear_L24_seed42.sh"),
          os.path.join(HPC, "pilot_patchtst_L24_seed42.sh"),
          os.path.join(HPC, "pilot_itransformer_L24_seed42.sh")]
WORKER = os.path.join(HPC, "innovation_worker.sh")
SUBMIT = os.path.join(HPC, "submit_innovation_pilot.sh")
BASH = r"C:\Program Files\Git\bin\bash.exe"

BANNED = BANNED_RUNTIME_ROOT
BANNED_TAIL = "CHATTIME/Chattime"

# executable usages that are never allowed
_BAD_CD = re.compile(r"^\s*cd\s+[^\n]*" + re.escape(BANNED_TAIL), re.M)
_BAD_PY = re.compile(r"python[^\n]*" + re.escape(BANNED_TAIL))
_BAD_FALLBACK = re.compile(r"INNOVATION_DEPLOYMENT_ROOT:-\$\(pwd\)")


def _read(p: str) -> str:
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


# 1-3 ────────────────────────────────────────────────────────────────────────
def test_no_forbidden_cd_target_in_pilots_worker_submit():
    for p in PILOTS + [WORKER, SUBMIT]:
        txt = _read(p)
        assert not _BAD_CD.search(txt), f"forbidden cd target in {p}"
        assert not _BAD_PY.search(txt), f"forbidden python path in {p}"


# 4 ──────────────────────────────────────────────────────────────────────────
def test_scripts_require_explicit_deployment_root():
    for p in PILOTS + [WORKER, SUBMIT]:
        txt = _read(p)
        assert ': "${INNOVATION_DEPLOYMENT_ROOT:?' in txt, \
            f"{os.path.basename(p)} must fail-closed when the root is unset"
        assert not _BAD_FALLBACK.search(txt), \
            f"{os.path.basename(p)} must not use a silent $(pwd) fallback"


# 6-7 ────────────────────────────────────────────────────────────────────────
def test_banned_root_and_subdir_are_rejected():
    assert RG.is_banned(BANNED) is True
    assert RG.is_banned(BANNED + "/scripts") is True
    assert RG.is_banned(BANNED + "/scripts/miflu_model.py") is True


# 8 ──────────────────────────────────────────────────────────────────────────
def test_legal_isolated_root_passes():
    assert RG.is_banned(
        "/home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/"
        "innov-v2.4_deadbeef") is False
    res = RG.check(deployment_root=PROJECT_ROOT)
    assert res["ok"] is True, res["violations"]


# 5 ──────────────────────────────────────────────────────────────────────────
def test_missing_deployment_root_fails_closed():
    if not os.path.exists(BASH):
        print("[skip] git bash not available")
        return
    env = dict(os.environ)
    env.pop("INNOVATION_DEPLOYMENT_ROOT", None)
    env["CONFIRM_INNOVATION_SUBMIT"] = "YES"
    r = subprocess.run([BASH, SUBMIT], cwd=PROJECT_ROOT, env=env,
                       capture_output=True, text=True)
    # must fail BEFORE reaching any sbatch
    assert r.returncode != 0, "missing deployment root must fail closed"
    assert "INNOVATION_DEPLOYMENT_ROOT" in (r.stdout + r.stderr)


def test_guard_blocks_without_confirmation():
    if not os.path.exists(BASH):
        print("[skip] git bash not available")
        return
    env = dict(os.environ)
    env.pop("CONFIRM_INNOVATION_SUBMIT", None)
    env["INNOVATION_DEPLOYMENT_ROOT"] = PROJECT_ROOT
    r = subprocess.run([BASH, SUBMIT], cwd=PROJECT_ROOT, env=env,
                       capture_output=True, text=True)
    assert "submission_attempted=false" in (r.stdout + r.stderr)


# 9-12 ───────────────────────────────────────────────────────────────────────
def test_each_pilot_calls_runner_once_and_runs_all_startup_checks():
    for p in PILOTS:
        txt = _read(p)
        assert txt.count("scripts/innovation/runner.py") == 1, \
            f"{os.path.basename(p)} must call the runner exactly once"
        assert "scripts/innovation/runtime_guard.py" in txt
        assert "--deployment-root \"$DEPLOYMENT_ROOT\"" in txt
        assert "scripts/innovation/verify_source_snapshot.py" in txt
        assert "expected_aggregate_sha256" in txt, "must compare the v2.4 hash"
        assert "test_access_allowed" in txt, "must assert test access is false"


def test_worker_constraints():
    txt = _read(WORKER)
    # an EXECUTABLE sbatch (start of a command, or command substitution) is
    # forbidden; the word must not even appear as a usage instruction
    assert not re.search(r"(^|;|\|\||&&|\$\()\s*sbatch\b", txt), \
        "worker must never invoke sbatch"
    assert "sbatch" not in txt, "worker must not mention sbatch at all"
    assert "scripts/innovation/runtime_guard.py" in txt
    assert "scripts/innovation/verify_source_snapshot.py" in txt
    assert txt.count("scripts/innovation/runner.py") == 1


# 13-17 ──────────────────────────────────────────────────────────────────────
def test_submit_references_only_the_four_pilots():
    txt = _read(SUBMIT)
    for n in ("pilot_gpt2_miflu_L24_seed42.sh", "pilot_dlinear_L24_seed42.sh",
              "pilot_patchtst_L24_seed42.sh", "pilot_itransformer_L24_seed42.sh"):
        assert n in txt, f"submit must reference {n}"
    for bad in ("submit_innovation_screening", "submit_innovation_full",
                "submit_innovation_smoke", "test_evaluation", "frozen_winner",
                "innovation_worker.sh"):
        assert bad not in txt, f"submit must not reference {bad}"
    assert "submit_innovation_pilot.sh" not in txt, "no self-recursion"
    assert "afterok" in txt and "afterany" not in txt
    # executable retry constructs only (the word alone may appear in prose)
    for retry in ("--requeue", "while true", "until sbatch", "for i in 1 2 3"):
        assert retry not in txt.lower(), f"no silent retry ({retry})"


# 18 ─────────────────────────────────────────────────────────────────────────
def test_fail_stop_simulation():
    """With fake sbatch/sacct on PATH, a FAILED predecessor must stop the chain."""
    if not os.path.exists(BASH):
        print("[skip] git bash not available")
        return
    tmp = tempfile.mkdtemp(prefix="innov_chain_")
    bindir = os.path.join(tmp, "bin")
    os.makedirs(bindir, exist_ok=True)
    log = os.path.join(tmp, "sbatch.log").replace("\\", "/")
    with open(os.path.join(bindir, "sbatch"), "w", newline="\n") as f:
        f.write("#!/bin/bash\necho call >> " + log + "\necho 900001\n")
    with open(os.path.join(bindir, "sacct"), "w", newline="\n") as f:
        f.write("#!/bin/bash\nlast=\"\"\nfor a in \"$@\"; do last=\"$a\"; done\n"
                "case \"$last\" in\n  State) echo \"$FAKE_SACCT_STATE\" ;;\n"
                "  ExitCode) echo \"$FAKE_SACCT_EXIT\" ;;\n  *) echo \"\" ;;\nesac\n")
    root = PROJECT_ROOT.replace("\\", "/")
    root = "/" + root[0].lower() + root[2:] if len(root) > 1 and root[1] == ":" else root

    def _run(state, exit_code):
        if os.path.exists(log):
            os.remove(log)
        env = dict(os.environ)
        env["PATH"] = "/" + bindir.replace("\\", "/").replace(":", "") + \
            ":" + env.get("PATH", "")
        env["PATH"] = bindir.replace("\\", "/") + ":" + env.get("PATH", "")
        env["CONFIRM_INNOVATION_SUBMIT"] = "YES"
        env["INNOVATION_DEPLOYMENT_ROOT"] = root
        env["FAKE_SACCT_STATE"] = state
        env["FAKE_SACCT_EXIT"] = exit_code
        return subprocess.run([BASH, SUBMIT], cwd=PROJECT_ROOT, env=env,
                              capture_output=True, text=True), \
            (sum(1 for _ in open(log, encoding="utf-8"))
             if os.path.exists(log) else 0)

    r_ok, n_ok = _run("COMPLETED", "0:0")
    assert n_ok == 8, f"success scenario must submit all eight pilots, got {n_ok}"
    assert r_ok.returncode == 0, r_ok.stdout + r_ok.stderr

    r_bad, n_bad = _run("FAILED", "1:0")
    assert n_bad == 1, f"fail-stop must submit only the first pilot, got {n_bad}"
    assert r_bad.returncode != 0
    assert "FAIL-STOP" in (r_bad.stdout + r_bad.stderr)


# 20-23 ──────────────────────────────────────────────────────────────────────
def test_eight_pilots_remain_ineligible():
    with open(os.path.join(HPC, "pilot_specs.json"), "r", encoding="utf-8") as f:
        d = json.load(f)
    assert len(d["specs"]) == 8
    for s in d["specs"]:
        assert s["selection_eligible"] is False
        assert s["paper_result_eligible"] is False
        assert s["test_access_allowed"] is False
        assert s["experiment_stage"] == "pilot"
        assert s["purpose"] == "infrastructure_verification_only"
        assert s["implementation_source_version"] == IMPLEMENTATION_SOURCE_VERSION
        assert s["source_snapshot_sha256"]


def test_spec_hash_matches_manifest():
    man_p = os.path.join(PROJECT_ROOT, "results", "innovation",
                         "source_snapshot_manifest.json")
    with open(man_p, "r", encoding="utf-8") as f:
        agg = json.load(f)["aggregate_sha256"]
    with open(os.path.join(HPC, "pilot_specs.json"), "r", encoding="utf-8") as f:
        d = json.load(f)
    assert d["source_snapshot_sha256"] == agg
    for s in d["specs"]:
        assert s["source_snapshot_sha256"] == agg


def test_test_seal_holds():
    inv = os.path.join(PROJECT_ROOT, "results", "innovation")
    # v2 frozen-winner history is immutable; v3 must not create a champion.
    assert os.path.exists(os.path.join(inv, "frozen_winners.json"))
    assert not os.path.exists(os.path.join(PROJECT_ROOT, "results", "v3", "champion.json"))
    # Existing v2 Test artifacts are immutable history; only the v3 path is sealed.
    assert not os.path.isdir(os.path.join(PROJECT_ROOT, "results", "v3", "test_evaluations"))
    hits = []
    for root, _d, files in os.walk(os.path.join(PROJECT_ROOT, "results", "v3", "runs")):
        for fn in files:
            if fn.startswith("test_"):
                hits.append(os.path.join(root, fn))
    assert not hits, hits


# 24 ─────────────────────────────────────────────────────────────────────────
def test_bash_n_on_pilots_worker_submit():
    if not os.path.exists(BASH):
        print("[skip] git bash not available")
        return
    for p in PILOTS + [WORKER, SUBMIT]:
        r = subprocess.run([BASH, "-n", p], capture_output=True, text=True)
        assert r.returncode == 0, f"bash -n failed for {p}: {r.stderr}"


if __name__ == "__main__":
    test_no_forbidden_cd_target_in_pilots_worker_submit()
    test_scripts_require_explicit_deployment_root()
    test_banned_root_and_subdir_are_rejected()
    test_legal_isolated_root_passes()
    test_missing_deployment_root_fails_closed()
    test_guard_blocks_without_confirmation()
    test_each_pilot_calls_runner_once_and_runs_all_startup_checks()
    test_worker_constraints()
    test_submit_references_only_the_four_pilots()
    test_fail_stop_simulation()
    test_four_pilots_remain_ineligible()
    test_spec_hash_matches_manifest()
    test_test_seal_holds()
    test_bash_n_on_pilots_worker_submit()
    print("[test_script_safety] OK")
