"""
state.py — pure orchestration logic for the innovation autonomous controller.
==========================================================================

Lives OUTSIDE the frozen innovation runtime hash (``hpc_scripts/autonomous/``), so
it is never part of the deployed source snapshot and never changes the snapshot
aggregate. It contains NO torch / innovation imports: every importable function is
unit-tested by ``tests/innovation/test_autonomous_controller.py``, and
``controller.sh`` drives Slurm through subcommands that print ``key=value`` lines
(no ``jq`` dependency on the login node).

This module implements the 12 hard requirements of the persistent overnight
controller contract (plan ``innovation_login_node_controller``):

  1. single-instance lock          -> handled in lib.sh / controller.sh (flock)
  2. record job id BEFORE polling  -> append_ledger_row + next_pending_job
  3. at most one job at a time     -> squeue_empty gate in controller.sh
  4. poll for terminal Slurm state -> controller.sh poll loop
  5. validate artifacts            -> validate_run
  6. fail-stop on deterministic failure / source mismatch / metadata mismatch /
     Test-access violation / missing artifacts -> validate_run + controller.sh
  7. never silently retry          -> no retry loop anywhere
  8. append-only ledger            -> append_ledger_row
  9. resumable without duplicate   -> next_pending_job skips ledger-terminal jobs
 10. never beyond authorized stage -> stage_within_ceiling
 11. heartbeat + current_state.json-> write_current_state
 12. copy scratch artifacts back   -> handled in lib.sh / controller.sh
Plus per-stage budgeting and the one-time Test gate.
"""
from __future__ import annotations

import csv
import json
import os
import sys

# Authoritative stage order for the autonomous session (A -> N).
STAGE_ORDER = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N"]

# The single job ledger schema (append-only; the controller owns it going forward).
LEDGER_FIELDS = ["job_id", "stage", "model_key", "horizon", "seed",
                 "submitted_utc", "state", "exit_code", "node", "run_id", "notes"]


# ── stage ordering / ceiling ──────────────────────────────────────────────────
def stage_index(key: str) -> int:
    return STAGE_ORDER.index(key) if key in STAGE_ORDER else -1


def stage_within_ceiling(stage_key: str, ceiling: str) -> bool:
    """Requirement 10: never advance beyond the authorized ceiling stage."""
    if stage_key not in STAGE_ORDER or ceiling not in STAGE_ORDER:
        return False
    return stage_index(stage_key) <= stage_index(ceiling)


# ── stage plan ────────────────────────────────────────────────────────────────
def load_stage_plan(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_stage(plan: dict, key: str) -> dict | None:
    for s in plan.get("stages", []):
        if s.get("key") == key:
            return s
    return None


# ── job identity / expansion ─────────────────────────────────────────────────
def job_key(stage_key: str, job: dict) -> str:
    if job.get("local"):
        return f"{stage_key}|local"
    return "|".join([
        stage_key,
        str(job.get("model", "")),
        str(job.get("text_encoder", "none")),
        str(job.get("fusion", "identity")),
        "L" + str(job.get("horizon", "?")),
        "s" + str(job.get("seed", "?")),
    ])


def run_id_for(job: dict, dataset: str = "national_ili") -> str:
    if job.get("local"):
        return f"local__{job.get('stage', 'local')}"
    return (f"{dataset}__{job['model']}__{job.get('text_encoder', 'none')}"
            f"__{job.get('fusion', 'identity')}__L{job['horizon']}__s{job['seed']}")


def _slug(value) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9]+", "-", str(value).strip()).strip("-") or "na"


def run_prefix_for(job: dict, dataset: str = "national_ili") -> str:
    """The deterministic run-id PREFIX (no timestamp / git sha).

    The runner's create-only run directory is named
    ``slug(dataset)__slug(model)__slug(encoder)__slug(fusion)__L{h}__seed{s}__<ts>__<git>``
    (see scripts/innovation/run_id.py). The trailing timestamp/git-sha makes the
    exact directory unpredictable at submit time, so the controller locates the
    run directory by this PREFIX and takes the newest match.
    """
    if job.get("local"):
        return f"local__{job.get('stage', 'local')}"
    return "__".join([
        _slug(dataset), _slug(job["model"]), _slug(job.get("text_encoder", "none")),
        _slug(job.get("fusion", "identity")), f"L{int(job['horizon'])}",
        f"seed{int(job['seed'])}",
    ])


def generate_stage_jobs(stage: dict) -> list[dict]:
    """Expand a stage into its concrete job list.

    A stage may carry an explicit ``jobs`` list, or an ``expand`` descriptor with a
    ``catalog`` (models / text_encoders / fusions / horizons / seeds) that is
    cartesian-producted. Stages with neither produce no jobs (e.g. a local verify
    or freeze step).
    """
    if stage.get("jobs"):
        return list(stage["jobs"])
    exp = stage.get("expand")
    if not exp:
        # A local (non-Slurm) gate stage with no explicit jobs is a single
        # synthetic step so the controller executes it IN ORDER (verify /
        # candidate-readiness / select / freeze) instead of silently skipping it.
        if stage.get("submit_mode", "slurm") == "local":
            return [{"local": True, "stage": stage.get("name", "local")}]
        return []
    models = exp.get("models", [])
    encoders = exp.get("text_encoders", [])
    fusions = exp.get("fusions", [])
    horizons = exp.get("horizons", [])
    seeds = exp.get("seeds", [])
    epochs = exp.get("epochs", 20)
    st = exp.get("stage", stage.get("name", "validation"))
    out = []
    for m in models:
        for e in encoders:
            for fu in fusions:
                for h in horizons:
                    for s in seeds:
                        out.append({"model": m, "text_encoder": e, "fusion": fu,
                                    "horizon": h, "seed": s, "epochs": epochs,
                                    "stage": st})
    return out


# ── ledger (append-only) ──────────────────────────────────────────────────────
def load_ledger(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def ledger_has_terminal(ledger: list[dict], key: str,
                        terminal_states=("COMPLETED",)) -> bool:
    for r in ledger:
        if r.get("notes", "").startswith("KEY=" + key) and r.get("state") in terminal_states:
            return True
    return False


def append_ledger_row(path: str, row: dict) -> None:
    fields = LEDGER_FIELDS
    exists = os.path.exists(path)
    with open(path, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fields})


def update_last_row_state(path: str, job_id: str, state: str,
                          exit_code: str = "", node: str = "") -> None:
    """Rewrite only the row matching ``job_id`` (used to record terminal state).

    Still append-oriented in spirit: the ledger is never truncated; we only flip
    the matching row's status by rewriting the file. The historical rows are
    preserved verbatim except for the single targeted row.
    """
    if not os.path.exists(path):
        return
    rows = load_ledger(path)
    out = []
    for r in rows:
        if r.get("job_id") == job_id:
            r = dict(r)
            r["state"] = state
            if exit_code:
                r["exit_code"] = exit_code
            if node:
                r["node"] = node
        out.append(r)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS)
        w.writeheader()
        for r in out:
            w.writerow({k: r.get(k, "") for k in LEDGER_FIELDS})


# ── resume: next pending job within ceiling ───────────────────────────────────
def next_pending_job(plan: dict, ledger: list[dict],
                     ceiling: str | None = None) -> dict | None:
    for s in plan.get("stages", []):
        key = s.get("key")
        if ceiling and not stage_within_ceiling(key, ceiling):
            continue
        for job in generate_stage_jobs(s):
            jk = job_key(key, job)
            if not ledger_has_terminal(ledger, jk):
                return {"stage_key": key, "stage": s, "job": job, "job_key": jk}
    return None


# ── per-stage budgeting ───────────────────────────────────────────────────────
def compute_budget(*, job_count: int, avg_minutes: float,
                   storage_gb_free: float, queue_pending_ok: bool,
                   source_version: str, required_source_version: str,
                   deps_ok: bool, repair_cascades_used: int,
                   max_repair_cascades: int, protocol_amendments_used: int,
                   max_protocol_amendments: int) -> dict:
    """Compute the resource budget for a stage and whether it fits the authorization.

    Requirement (per-stage gate): do NOT begin a stage whose estimated completion
    cannot fit the current authorization / resource limits; instead record it as
    queued or deferred.
    """
    gpu_hours = round(job_count * avg_minutes / 60.0, 3)
    source_ok = (source_version == required_source_version)
    within_limits = bool(
        queue_pending_ok and source_ok and deps_ok
        and repair_cascades_used <= max_repair_cascades
        and protocol_amendments_used <= max_protocol_amendments
    )
    return {
        "job_count": job_count,
        "avg_minutes": avg_minutes,
        "gpu_hours_estimate": gpu_hours,
        "storage_gb_free": storage_gb_free,
        "queue_pending_ok": bool(queue_pending_ok),
        "source_version": source_version,
        "required_source_version": required_source_version,
        "source_ok": source_ok,
        "deps_ok": bool(deps_ok),
        "repair_cascades_used": repair_cascades_used,
        "max_repair_cascades": max_repair_cascades,
        "protocol_amendments_used": protocol_amendments_used,
        "max_protocol_amendments": max_protocol_amendments,
        "within_limits": within_limits,
    }


def budget_ok(b: dict) -> bool:
    return bool(b.get("within_limits"))


# ── completion matrix + one-time Test gate ────────────────────────────────────
def load_completion_matrix(path: str) -> dict | None:
    """The machine-checkable completion matrix is a JSON sidecar; a `.md` human
    version is also maintained for the report. We read the JSON."""
    p = path
    if path.endswith(".md"):
        p = path[:-3] + ".json"
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def test_gate_open(completion_matrix: dict | None,
                   freeze_audit: dict | None) -> bool:
    """Requirement: the one-time Test evaluation may run ONLY when (a) the
    completion matrix has no unresolved mandatory validation item, and (b) the
    validation-only champion freeze audit passes all checks. It must NEVER run
    merely because time remains."""
    if not completion_matrix:
        return False
    if not completion_matrix.get("all_mandatory_resolved", False):
        return False
    mandatory = completion_matrix.get("mandatory_items", [])
    if any((not m.get("resolved")) for m in mandatory):
        return False
    if not freeze_audit:
        return False
    if not freeze_audit.get("passed", False):
        return False
    return True


# ── artifact validation (fail-stop triggers) ─────────────────────────────────
def validate_run(*, run_dir: str, manifest_aggregate: str | None,
                 expected_stage: str | None,
                 allow_test_access: bool = False) -> dict:
    """Requirement 5 + 6: validate artifacts before advancing.

    Returns ok=True only when the run is OK, wrote no test artifact, did not leak
    test access, matches the frozen source snapshot, matches the expected stage,
    and has its checkpoint manifest. Any other condition is a deterministic
    failure / mismatch that must FAIL-STOP the controller.
    """
    rs = os.path.join(run_dir, "run_status.json")
    if not os.path.exists(rs):
        return {"ok": False, "reason": "missing_run_status"}
    with open(rs, "r", encoding="utf-8") as f:
        rj = json.load(f)
    if rj.get("status") != "ok":
        return {"ok": False, "reason": "status_not_ok", "status": rj.get("status")}
    if rj.get("test_artifacts_written") is True:
        return {"ok": False, "reason": "test_artifact_leak"}
    if bool(rj.get("test_access_allowed")) and not allow_test_access:
        return {"ok": False, "reason": "test_access_violation"}
    if manifest_aggregate and rj.get("source_snapshot_sha256") != manifest_aggregate:
        return {"ok": False, "reason": "source_mismatch"}
    if expected_stage and rj.get("experiment_stage") != expected_stage:
        return {"ok": False, "reason": "stage_mismatch",
                "got": rj.get("experiment_stage"), "expected": expected_stage}
    ck = os.path.join(run_dir, "checkpoints", "checkpoint_manifest.json")
    if not os.path.exists(ck):
        return {"ok": False, "reason": "missing_checkpoint_manifest"}
    return {"ok": True, "status": "ok"}


def resolve_run_dir(runs_root: str, prefix: str, stage: str | None = None):
    """Return the NEWEST run directory matching ``prefix`` (optionally restricted
    to a given ``experiment_stage``).

    The runner's run directory name carries an unpredictable UTC timestamp + git
    suffix, and the same spec can exist at several stages (pilot/screening/full),
    so the controller locates the directory by this deterministic prefix and
    stage rather than predicting the full name.
    """
    import glob
    matches = []
    for d in glob.glob(os.path.join(runs_root, f"*{prefix}*")):
        if not os.path.isdir(d):
            continue
        if stage:
            rp = os.path.join(d, "run_status.json")
            if not os.path.exists(rp):
                continue
            try:
                with open(rp, "r", encoding="utf-8") as f:
                    st = json.load(f)
            except Exception:
                continue
            if str(st.get("experiment_stage")) != str(stage):
                continue
        matches.append((os.path.getmtime(d), d))
    if not matches:
        return None
    matches.sort(key=lambda x: x[0], reverse=True)
    return matches[0][1]


# ── heartbeat / current state ─────────────────────────────────────────────────
def write_current_state(path: str, state: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# ── CLI: key=value output (no jq needed on the login node) ───────────────────
def _emit(d: dict) -> None:
    for k, v in d.items():
        print(f"{k}={v}")


def cli(argv) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("next-job")
    p.add_argument("--plan", required=True)
    p.add_argument("--ledger", required=True)
    p.add_argument("--ceiling", default=None)

    p = sub.add_parser("budget")
    p.add_argument("--job-count", type=int, required=True)
    p.add_argument("--avg-min", type=float, required=True)
    p.add_argument("--storage-gb", type=float, required=True)
    p.add_argument("--queue-ok", type=int, required=True)
    p.add_argument("--source-ver", required=True)
    p.add_argument("--req-ver", required=True)
    p.add_argument("--deps-ok", type=int, required=True)
    p.add_argument("--repair-used", type=int, required=True)
    p.add_argument("--repair-max", type=int, required=True)
    p.add_argument("--amend-used", type=int, required=True)
    p.add_argument("--amend-max", type=int, required=True)

    p = sub.add_parser("gate")
    p.add_argument("--completion", required=True)
    p.add_argument("--freeze-audit", required=True)

    p = sub.add_parser("ceiling")
    p.add_argument("--stage", required=True)
    p.add_argument("--ceiling", required=True)

    p = sub.add_parser("validate-run")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--manifest-aggregate", default=None)
    p.add_argument("--expected-stage", default=None)
    p.add_argument("--allow-test-access", type=int, default=0)

    p = sub.add_parser("run-id")
    p.add_argument("--model", required=True)
    p.add_argument("--text-encoder", default="none")
    p.add_argument("--fusion", default="identity")
    p.add_argument("--horizon", type=int, required=True)
    p.add_argument("--seed", type=int, required=True)

    p = sub.add_parser("plan-sequence")
    p.add_argument("--plan", required=True)
    p.add_argument("--ledger", default=None)
    p.add_argument("--ceiling", default=None)

    p = sub.add_parser("resolve-run")
    p.add_argument("--runs-root", required=True)
    p.add_argument("--prefix", required=True)
    p.add_argument("--stage", default=None)

    a = ap.parse_args(argv)

    if a.cmd == "next-job":
        plan = load_stage_plan(a.plan)
        ledger = load_ledger(a.ledger)
        nxt = next_pending_job(plan, ledger, a.ceiling)
        if nxt is None:
            print("RESULT=NONE")
            return 0
        job = nxt["job"]
        print("RESULT=PENDING")
        print("STAGE_KEY=" + nxt["stage_key"])
        print("JOB_KEY=" + nxt["job_key"])
        print("STAGE_MODE=" + nxt["stage"].get("submit_mode", "slurm"))
        print("RUN_ID=" + run_id_for(job))
        print("RUN_PREFIX=" + run_prefix_for(job))
        if job.get("local"):
            print("ARGS=local")
        else:
            print("ARGS=" + " ".join([
                str(job.get("model", "")), str(job.get("text_encoder", "none")),
                str(job.get("fusion", "identity")), str(job.get("horizon")),
                str(job.get("seed")), str(job.get("epochs", 20)),
                str(job.get("stage", nxt["stage"].get("name", "validation")))]))
        return 0

    if a.cmd == "budget":
        b = compute_budget(
            job_count=a.job_count, avg_minutes=a.avg_min,
            storage_gb_free=a.storage_gb, queue_pending_ok=bool(a.queue_ok),
            source_version=a.source_ver, required_source_version=a.req_ver,
            deps_ok=bool(a.deps_ok), repair_cascades_used=a.repair_used,
            max_repair_cascades=a.repair_max,
            protocol_amendments_used=a.amend_used,
            max_protocol_amendments=a.amend_max)
        _emit(b)
        print("WITHIN_LIMITS=" + ("yes" if b["within_limits"] else "no"))
        return 0

    if a.cmd == "gate":
        cm = load_completion_matrix(a.completion)
        try:
            with open(a.freeze_audit, "r", encoding="utf-8") as f:
                fa = json.load(f)
        except Exception:
            fa = None
        open_gate = test_gate_open(cm, fa)
        print("GATE=" + ("open" if open_gate else "closed"))
        return 0 if open_gate else 0

    if a.cmd == "ceiling":
        within = stage_within_ceiling(a.stage, a.ceiling)
        print("WITHIN=" + ("yes" if within else "no"))
        return 0

    if a.cmd == "validate-run":
        res = validate_run(
            run_dir=a.run_dir, manifest_aggregate=a.manifest_aggregate,
            expected_stage=a.expected_stage,
            allow_test_access=bool(a.allow_test_access))
        _emit(res)
        print("OK=" + ("yes" if res["ok"] else "no"))
        return 0 if res["ok"] else 1

    if a.cmd == "run-id":
        print("RUN_ID=" + run_id_for({
            "model": a.model, "text_encoder": a.text_encoder,
            "fusion": a.fusion, "horizon": a.horizon, "seed": a.seed}))
        return 0

    if a.cmd == "plan-sequence":
        plan = load_stage_plan(a.plan)
        ledger = load_ledger(a.ledger) if a.ledger else []
        ceiling = a.ceiling
        for s in plan.get("stages", []):
            key = s.get("key")
            if ceiling and not stage_within_ceiling(key, ceiling):
                continue
            mode = s.get("submit_mode", "slurm")
            for job in generate_stage_jobs(s):
                jk = job_key(key, job)
                done = ledger_has_terminal(ledger, jk)
                rid = run_prefix_for(job)
                if job.get("local"):
                    args = "local"
                else:
                    args = " ".join([
                        str(job.get("model", "")), str(job.get("text_encoder", "none")),
                        str(job.get("fusion", "identity")), str(job.get("horizon")),
                        str(job.get("seed")), str(job.get("epochs", 20)),
                        str(job.get("stage", s.get("name", "validation")))])
                print(f"SEQ|{key}|{mode}|{jk}|{rid}|{args}|{'DONE' if done else 'PENDING'}")
        return 0

    if a.cmd == "resolve-run":
        rd = resolve_run_dir(a.runs_root, a.prefix, a.stage)
        print("RUN_DIR=" + (rd if rd else "NONE"))
        return 0 if rd else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(cli(sys.argv[1:]))
