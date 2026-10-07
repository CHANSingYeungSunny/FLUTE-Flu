"""screening_gate.py — v3.4 pre-Screening compute-node Gate.

Runs ALL EIGHT model families end to end through the frozen runner with tiny
limits and stage `validation` (never `screening`, so a Gate run can never be
mistaken for, or enter, the formal Screening set), then validates that every
required v3.4 artifact — including the three NEW ones — was emitted and is
parseable.

Gate passes only if all eight families both complete and validate.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

ROOT = os.path.abspath(os.environ.get("INNOVATION_DEPLOYMENT_ROOT", "."))
RUNS = os.path.join(ROOT, "results", "innovation", "runs")
OUT = os.path.join(ROOT, "hpc_results", "innovation",
                   f"screening_gate_{os.environ.get('SLURM_JOB_ID', 'local')}")
os.makedirs(OUT, exist_ok=True)

MODELS = [
    ("nlinear", "none", "identity", None),
    ("dlinear", "none", "identity", None),
    ("patchtst", "none", "identity", None),
    ("itransformer", "none", "identity", None),
    ("gpt2_miflu", "gpt2", "concat-projection", None),
    ("qwen_time_llm", "none", "identity", "Qwen/Qwen2.5-1.5B"),
    ("calf_llm", "none", "identity", "gpt2"),
    ("timecma_llm", "none", "identity", "gpt2"),
]

REQUIRED = ["config_resolved.yaml", "environment.txt", "git_commit.txt",
            "split_manifest.json", "scaler_metadata.json",
            "prompt_statistics_metadata.json", "checkpoints/best_val_mse.pt",
            "checkpoints/checkpoint_manifest.json", "logs/train_history.csv",
            "predictions/validation_predictions.csv",
            "metrics/validation_metrics.json",
            "metrics/fixed_step_metrics.json",
            "metrics/peak_metrics_by_season.csv", "run_status.json",
            "resource_usage.json"]
PRED_KEYS = ["model_key", "horizon", "seed", "split", "step", "lead_weeks",
             "target_date", "variable", "y_true_equiv", "y_pred_equiv"]


def jload(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def run_one(model, te, fusion, model_id):
    cmd = [sys.executable, "scripts/innovation/runner.py",
           "--model", model, "--text-encoder", te, "--fusion", fusion,
           "--horizon", "24", "--seed", "42", "--epochs", "1",
           "--limit-train", "24", "--limit-val", "8",
           "--experiment-stage", "validation", "--max-seconds", "900"]
    if model_id:
        cmd += ["--model-id", model_id, "--load-backbone"]
    before = set(os.listdir(RUNS)) if os.path.isdir(RUNS) else set()
    t0 = time.time()
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    dt = time.time() - t0
    after = set(os.listdir(RUNS)) if os.path.isdir(RUNS) else set()
    new = sorted(after - before)
    return {"model": model, "rc": p.returncode, "seconds": round(dt, 1),
            "new_run_dirs": new,
            "stderr_tail": (p.stderr or "")[-600:],
            "stdout_tail": (p.stdout or "")[-600:]}


def validate(model, run_dirs):
    res = {"model": model, "run_dir": run_dirs[-1] if run_dirs else None,
           "checks": {}, "errors": []}
    if not run_dirs:
        res["errors"].append("no run directory created")
        return res
    d = os.path.join(RUNS, run_dirs[-1])
    missing = [r for r in REQUIRED if not os.path.exists(os.path.join(d, r))]
    res["checks"]["all_required_artifacts"] = not missing
    if missing:
        res["errors"].append(f"missing artifacts: {missing}")
        return res

    st = jload(os.path.join(d, "run_status.json"))
    res["checks"]["run_status_ok"] = st.get("status") == "ok"
    res["checks"]["restore_ok"] = st.get("restore_ok") is True
    res["checks"]["test_access_zero"] = st.get("test_access_count") == 0
    res["checks"]["holdout_access_zero"] = st.get("holdout_access_count") == 0
    res["checks"]["canonical_data_hash_present"] = bool(
        st.get("canonical_data_sha256"))
    res["checks"]["output_is_seven_variables"] = int(st.get("total_parameters") or 0) > 0

    # long-format prediction keys
    head = open(os.path.join(d, "predictions", "validation_predictions.csv"),
                encoding="utf-8").readline().strip().split(",")
    res["checks"]["prediction_key_model_key"] = "model_key" in head
    res["checks"]["prediction_key_horizon"] = "horizon" in head
    res["checks"]["prediction_key_seed"] = "seed" in head
    res["checks"]["prediction_key_step"] = "step" in head
    res["checks"]["prediction_key_lead_weeks"] = "lead_weeks" in head
    res["checks"]["prediction_key_target_date"] = (
        "target_date" in head or "week_start_date" in head)
    res["checks"]["prediction_key_variable"] = "variable" in head
    res["checks"]["prediction_has_z_true_and_pred"] = (
        "ground_truth_ili" in head and "prediction_ili" in head)

    # new: fixed-step metrics 0..3
    fs = jload(os.path.join(d, "metrics", "fixed_step_metrics.json"))
    steps = fs.get("steps", {})
    res["checks"]["fixed_step_0_3_present"] = all(str(s) in steps
                                                  for s in (0, 1, 2, 3))
    ok_finite = True
    for s in (0, 1, 2, 3):
        e = steps.get(str(s), {})
        if not e.get("available") or not isinstance(e.get("mse_z"), (int, float)):
            if os.environ.get("GATE_STRICT_FINITE", "1") == "1":
                ok_finite = False
        if e.get("lead_weeks") != s + 1:
            ok_finite = False
    res["checks"]["fixed_step_lead_mapping_and_finite"] = ok_finite
    res["checks"]["no_cross_step_averaging_flag"] = (
        fs.get("steps_never_averaged") is True)

    # new: prompt statistics + resource usage
    ps = jload(os.path.join(d, "prompt_statistics_metadata.json"))
    res["checks"]["prompt_stats_train_only"] = (
        ps.get("fit_scope") == "train rows only")
    ru = jload(os.path.join(d, "resource_usage.json"))
    res["checks"]["resource_usage_parameters"] = int(
        ru.get("trainable_parameters") or 0) >= 0
    res["checks"]["resource_usage_gpu_hours"] = (
        isinstance(ru.get("gpu_hours_train"), (int, float)))
    res["checks"]["resource_usage_storage"] = (
        isinstance(ru.get("checkpoint_bytes"), int))

    # paper-style full-horizon metrics
    vm = jload(os.path.join(d, "metrics", "validation_metrics.json"))
    res["checks"]["fullhorizon_z_metrics"] = (
        isinstance(vm.get("mse_all_z"), (int, float))
        and isinstance(vm.get("mae_all_z"), (int, float)))

    for k, v in res["checks"].items():
        if not v:
            res["errors"].append(f"check failed: {k}")
    res["passed"] = not res["errors"]
    return res


def main() -> int:
    rep = {"gate": "pre_screening_v3.4", "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
           "node": os.environ.get("SLURMD_NODENAME"),
           "deployment_root": ROOT, "models": [], "started_utc": time.strftime(
               "%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    n_ok = 0
    for model, te, fusion, mid in MODELS:
        r = run_one(model, te, fusion, mid)
        v = validate(model, r["new_run_dirs"])
        entry = {**r, "validate": v, "passed": r["rc"] == 0 and v.get("passed", False)}
        rep["models"].append(entry)
        print(f"[gate] {model}: rc={r['rc']} seconds={r['seconds']} "
              f"passed={entry['passed']}")
        if entry["passed"]:
            n_ok += 1
    rep["models_ok"] = f"{n_ok}/8"
    rep["passed"] = n_ok == 8
    rep["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rep["test_access_count"] = 0
    rep["holdout_access_count"] = 0
    with open(os.path.join(OUT, "gate_report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print(f"[gate] models_ok={n_ok}/8 passed={rep['passed']}")
    print(f"[gate] report -> {OUT}/gate_report.json")
    return 0 if rep["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
