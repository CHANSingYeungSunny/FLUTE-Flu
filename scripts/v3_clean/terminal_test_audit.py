"""terminal_test_audit.py — 21-item terminal-state audit for the one-time
Test/Holdout phase.

Runs on the HPC login node AFTER the serial driver reaches ALL_DONE. It reads
ONLY metadata (keys file, ledger, sacct, result-dir manifests, file presence,
structural target-date columns). It NEVER reads a Test ILI target/prediction
VALUE into an audit conclusion — leakage/overlap checks are structural.

Fail-stop: any failed check exits non-zero.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

BASE = "/scratch/sychan552/_test_phase"
KEYS_FILE = os.path.join(BASE, "test_eval_keys.txt")
LEDGER = os.path.join(BASE, "test_eval_ledger.jsonl")
RESULTS = os.path.join(BASE, "results")
DRIVER_LOG = os.path.join(BASE, "test_eval_driver.log")
DEPLOY = "/scratch/sychan552/innovation_deploy_root_v3_clean14"
TEST_EVAL_PY = os.path.join(DEPLOY, "scripts", "innovation", "test_eval.py")
FROZEN_TEST_EVAL_SHA = "93a1338bfac30096a95448830bb2867d9966e3625df9a51c91453b86ae7dae0b"

METRIC_FILES = (
    "paper_aligned_full_output_metrics.json",
    "ilitotal_fixed_step_metrics.json",
    "ilitotal_full_horizon_metrics.json",
    "pte_pie_metrics.json",
)
VAL_END = 819          # first test target abs_week must be 820 (= VAL_END + 1)
T = 104

CHECKS: list = []
FAILED = False


def check(name, ok, detail=""):
    global FAILED
    CHECKS.append({"name": name, "passed": bool(ok), "detail": str(detail)})
    if not ok:
        FAILED = True
        print(f"  [FAIL] {name}: {detail}")


def sha256_file(p):
    if not os.path.isfile(p):
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sacct_dump():
    r = subprocess.run(
        ["sacct", "-X", "-u", "sychan552", "--starttime", "2026-09-21T00:00",
         "--format=JobID,JobName,State,ExitCode", "-n"],
        capture_output=True, text=True)
    rows = []
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[1] == "te_eval":
            rows.append({"job_id": parts[0], "jobname": parts[1],
                         "state": parts[2], "exit": parts[3]})
    return rows


def main():
    # --- authorized keys ---
    keys = [k.strip() for k in open(KEYS_FILE) if k.strip()]
    check("01_keys_84", len(keys) == 84, f"n={len(keys)}")
    check("02_keys_unique", len(set(keys)) == 84, f"unique={len(set(keys))}")

    fam = {"gpt2_miflu": 0, "nlinear": 0, "seasonal_naive": 0}
    for k in keys:
        for m in fam:
            if f"__{m}__" in k:
                fam[m] += 1
    check("03_family_composition_40_40_4",
          fam["gpt2_miflu"] == 40 and fam["nlinear"] == 40
          and fam["seasonal_naive"] == 4, str(fam))
    check("04_no_unauthorized_comparator",
          all(any(f"__{m}__" in k for m in fam) for k in keys))

    # --- ledger ---
    ledger = [json.loads(l) for l in open(LEDGER) if l.strip()]
    lk = [e["run_key"] for e in ledger]
    check("05_ledger_84", len(ledger) == 84, f"n={len(ledger)}")
    check("06_ledger_keys_match_authorized", set(lk) == set(keys),
          f"ledger={len(set(lk))} keys={len(set(keys))}")
    check("07_ledger_keys_unique", len(set(lk)) == 84)
    n_sub = len(ledger)
    n_cmp = sum(1 for e in ledger if e.get("state") == "COMPLETED")
    n_suc = sum(1 for e in ledger if e.get("exit") == "0:0")
    check("08_counts_84_84_84", n_sub == 84 and n_cmp == 84 and n_suc == 84,
          f"sub={n_sub} cmp={n_cmp} suc={n_suc}")

    # --- sacct (Slurm ground truth) ---
    sac = sacct_dump()
    check("09_no_85th_job", len(sac) == 84, f"sacct_te_eval={len(sac)}")
    check("10_slurm_all_completed", all(r["state"] == "COMPLETED" for r in sac),
          str(sorted({r["state"] for r in sac})))
    check("11_slurm_all_exit_0_0", all(r["exit"] == "0:0" for r in sac),
          str(sorted({r["exit"] for r in sac})))

    # --- result dirs + artifacts ---
    dirs = sorted(d for d in os.listdir(RESULTS)
                  if os.path.isdir(os.path.join(RESULTS, d)))
    check("12_result_dirs_84", len(dirs) == 84, f"n={len(dirs)}")
    check("13_result_dirs_match_keys", set(dirs) == set(keys),
          f"dirs={len(set(dirs))} keys={len(set(keys))}")

    n_manifest = n_pred = n_metric_ok = n_status_ok = 0
    n_restore_ok = 0
    first_target_min = None
    first_target_max = None
    target_overlap_bad = 0
    for k in keys:
        rd = os.path.join(RESULTS, k)
        mf = os.path.join(rd, "test_manifest.json")
        if os.path.isfile(mf):
            n_manifest += 1
            try:
                m = json.load(open(mf))
            except Exception as e:
                m = {}
                check(f"manifest_json_{k}", False, str(e))
            # restoration evidence / provenance fields
            if m.get("arm") == "baseline":
                if m.get("checkpoint_applicable") is False and \
                   m.get("stochastic_seed_applicable") is False and \
                   m.get("compact_sha256") == "not_applicable":
                    n_restore_ok += 1
            else:
                need = ("compact_sha256", "canonical_tensor_sha256",
                        "canonical_hash_schema", "restoration")
                if all(m.get(x) for x in need) and \
                   m.get("restoration", {}).get("strict_load_ok") is True and \
                   m.get("restoration", {}).get("missing_keys") == [] and \
                   m.get("restoration", {}).get("unexpected_keys") == []:
                    n_restore_ok += 1
            tmin = m.get("test_target_abs_week_min")
            tmax = m.get("test_target_abs_week_max")
            if tmin is not None:
                first_target_min = tmin if first_target_min is None else \
                    min(first_target_min, tmin)
            if tmax is not None:
                first_target_max = tmax if first_target_max is None else \
                    max(first_target_max, tmax)
            if tmin is not None and tmin < VAL_END + 1:
                target_overlap_bad += 1
        p = os.path.join(rd, "predictions", "test_predictions.csv")
        if os.path.isfile(p) and os.path.getsize(p) > 0:
            n_pred += 1
        if all(os.path.isfile(os.path.join(rd, "metrics", f))
               for f in METRIC_FILES):
            n_metric_ok += 1
        st = os.path.join(rd, "test_status.json")
        if os.path.isfile(st):
            try:
                if json.load(open(st)).get("state") == "COMPLETED":
                    n_status_ok += 1
            except Exception:
                pass

    check("14_manifests_84", n_manifest == 84, f"n={n_manifest}")
    check("15_predictions_84_nonempty", n_pred == 84, f"n={n_pred}")
    check("16_metrics_4_each_84", n_metric_ok == 84, f"n={n_metric_ok}")
    check("17_status_completed_84", n_status_ok == 84, f"n={n_status_ok}")
    check("18_restoration_evidence_84", n_restore_ok == 84, f"n={n_restore_ok}")

    # --- structural leakage (no ILI value read) ---
    check("19_first_test_target_abs_week_820",
          first_target_min == VAL_END + 1,
          f"min={first_target_min} (want {VAL_END + 1})")
    check("20_no_target_overlap_with_validation",
          target_overlap_bad == 0, f"overlap={target_overlap_bad}")
    check("21_test_target_max_consistent",
          first_target_max == 1024, f"max={first_target_max} (want 1024)")

    # --- frozen script hash (no post-Test change) ---
    check("22_test_eval_py_hash_frozen",
          sha256_file(TEST_EVAL_PY) == FROZEN_TEST_EVAL_SHA,
          sha256_file(TEST_EVAL_PY)[:16])

    # --- driver / lock / queue ---
    all_done = "ALL_DONE" in open(DRIVER_LOG).read() if os.path.isfile(DRIVER_LOG) else False
    check("23_driver_normal_exit", all_done, "ALL_DONE present in driver log")
    locks = [f for f in os.listdir(BASE) if f.endswith(".lock")]
    check("24_lock_released", len(locks) == 0, str(locks))
    q = subprocess.run(["squeue", "-u", "sychan552", "-h", "-o", "%j"],
                       capture_output=True, text=True).stdout
    check("25_queue_no_residual_test_job", "te_eval" not in q, q.strip())

    out = {
        "audit": "terminal_test_audit",
        "passed": not FAILED,
        "n_checks": len(CHECKS),
        "n_failed": sum(1 for c in CHECKS if not c["passed"]),
        "family_composition": fam,
        "sacct_te_eval_jobs": len(sac),
        "checks": CHECKS,
    }
    with open(os.path.join(BASE, "terminal_test_audit.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"TERMINAL_AUDIT {'PASSED' if not FAILED else 'FAILED'} "
          f"({sum(1 for c in CHECKS if c['passed'])}/{len(CHECKS)})")
    for c in CHECKS:
        if not c["passed"]:
            print(f"  [FAIL] {c['name']}: {c['detail']}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
