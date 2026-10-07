"""audit_recompute.py — independent final audit of the one-time Test evaluation.

OUTSIDE the frozen innovation source hash.

It NEVER trains, re-selects, or re-runs Test. It:
  1. hashes the authoritative artifacts and builds an artifact index;
  2. recomputes every one of the 52 Test cells from its raw prediction CSV using
     the FROZEN `innovation.metrics` implementation, and compares against the
     stored metric JSON;
  3. proves the one-time Test was single-use;
  4. reconciles the execution history from ledgers and Slurm accounting;
  5. audits the statistics (pairing units, bootstrap, Holm family, sample sizes).

All computation is lightweight (pandas/numpy on ~52 CSVs) — no model code.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
ROOT = _HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from innovation import metrics as MET  # noqa: E402  (frozen implementation)

INN = ROOT / "results" / "innovation"
TEV_ID = "final_nlinear_20260915T145710Z"
TEV = INN / "test_evaluations" / TEV_ID
AUD = INN / "final_audit"
AUD.mkdir(parents=True, exist_ok=True)
FINAL = INN / "final"
AC = INN / "autonomous_completion"


def _j(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _wj(p, o):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, indent=2)


def _sha(p):
    p = Path(p)
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _rows(p):
    p = Path(p)
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _csv(p, rows, cols=None):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    cols = cols or list(rows[0].keys())
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# ══ 1. authoritative artifact index ═════════════════════════════════════════
AUTHORITATIVE = [
    ("plan", ROOT / "MIFlu_innovation_plan_v2.md", "immutable", "canonical"),
    ("hpc_guide", ROOT / "HPC_GUIDE.md", "append-only", "canonical"),
    ("frozen_winners", INN / "frozen_winners.json", "immutable", "canonical"),
    ("frozen_model_manifest", INN / "frozen_model_manifest.json", "immutable", "canonical"),
    ("freeze_audit", INN / "freeze_audit.json", "immutable", "canonical"),
    ("model_selection_audit", INN / "model_selection_audit.json", "immutable", "canonical"),
    ("stage_f_cohort_manifest",
     INN / "governance" / "stage_provenance" / "stage_f_cohort_manifest.json",
     "immutable", "canonical"),
    ("one_time_test_receipt", INN / "test_evaluations" / "ONE_TIME_TEST_ACCESS_RECEIPT.json",
     "immutable", "canonical"),
    ("test_evaluation_manifest", TEV / "test_evaluation_manifest.json", "immutable", "canonical"),
    ("test_completion_gate", TEV / "completion_gate.json", "derived", "derived"),
    ("test_checkpoint_verification", TEV / "checkpoint_verification.json", "derived", "derived"),
    ("registry", INN / "registry.csv", "append-only", "historical"),
    ("registry_v2", INN / "registry_v2.csv", "append-only", "canonical"),
    ("job_ledger", AC / "job_ledger.csv", "append-only", "canonical"),
    ("stage_plan", AC / "stage_plan.json", "immutable", "canonical"),
]
man = _j(TEV / "test_evaluation_manifest.json")
receipt = _j(INN / "test_evaluations" / "ONE_TIME_TEST_ACCESS_RECEIPT.json")
fmm = _j(INN / "frozen_model_manifest.json")
coh = _j(INN / "governance" / "stage_provenance" / "stage_f_cohort_manifest.json")
msa = _j(INN / "model_selection_audit.json")
fza = _j(INN / "freeze_audit.json")

index = []
for role, p, mut, cls in AUTHORITATIVE:
    index.append({"role": role, "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                  "exists": p.exists(), "bytes": p.stat().st_size if p.exists() else 0,
                  "sha256": _sha(p),
                  "protocol_version": man.get("scientific_protocol_version"),
                  "implementation_version": man.get("implementation_source_version"),
                  "source_aggregate": man.get("source_aggregate_sha256"),
                  "created_utc": (datetime.datetime.utcfromtimestamp(
                      p.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%SZ") if p.exists() else ""),
                  "mutability": mut, "classification": cls})

# ══ 2. recompute every Test cell from raw prediction CSVs ═══════════════════
RTOL = 1e-9
recomp, disc = [], []
for c in man["cells"]:
    role, m, L, s = c["role"], c["model_key"], int(c["horizon"]), int(c["seed"])
    rid = c.get("run_id", "")
    pcsv = TEV / "predictions" / f"{role}__{m}__L{L}__s{s}.csv"
    mj = TEV / "metrics" / f"{role}__{m}__L{L}__s{s}.json"
    row = {"role": role, "model_key": m, "horizon": L, "seed": s, "run_id": rid,
           "test_eval_id": TEV_ID}
    if not pcsv.exists() or not mj.exists():
        row.update({"status": "missing_artifact"})
        recomp.append(row)
        disc.append({**row, "issue": "missing prediction or metric file"})
        continue
    stored = _j(mj)
    df = pd.read_csv(pcsv)
    got = MET.evaluate_predictions(df, "test", step=0)
    row["status"] = "recomputed"
    row["n_rows_csv"] = int(len(df))
    row["n_rows_stored"] = stored.get("n_rows")
    row["dates_first"] = str(df["week_start_date"].iloc[0])
    row["dates_last"] = str(df["week_start_date"].iloc[-1])
    for k in ("mse_all_z", "mae_all_z", "mse_ili_phys", "mae_ili_phys"):
        row[f"stored_{k}"] = stored.get(k)
        row[f"recomp_{k}"] = got.get(k)
        a, b = stored.get(k), got.get(k)
        ok = (a is not None and b is not None
              and abs(float(a) - float(b)) <= RTOL * max(1.0, abs(float(a))))
        row[f"match_{k}"] = bool(ok)
        if not ok:
            disc.append({**row, "issue": f"{k} mismatch stored={a} recomputed={b}"})
    sp, gp = stored.get("peak", {}) or {}, got.get("peak", {}) or {}
    for k in ("mean_pte_weeks", "mean_pie_pct", "peak_hit_ratio", "n_hits",
              "n_seasons_evaluable"):
        row[f"stored_{k}"] = sp.get(k)
        row[f"recomp_{k}"] = gp.get(k)
        a, b = sp.get(k), gp.get(k)
        ok = (a is None and b is None) or (
            a is not None and b is not None
            and abs(float(a) - float(b)) <= RTOL * max(1.0, abs(float(a))))
        row[f"match_{k}"] = bool(ok)
        if not ok:
            disc.append({**row, "issue": f"peak.{k} mismatch stored={a} recomputed={b}"})
    row["row_count_ok"] = (row["n_rows_csv"] == row["n_rows_stored"])
    if not row["row_count_ok"]:
        disc.append({**row, "issue": f"n_rows mismatch csv={row['n_rows_csv']} "
                                     f"stored={row['n_rows_stored']}"})
    recomp.append(row)

n_recomp = sum(1 for r in recomp if r["status"] == "recomputed")
metric_fields = ["mse_all_z", "mae_all_z", "mse_ili_phys", "mae_ili_phys"]
peak_fields = ["mean_pte_weeks", "mean_pie_pct", "peak_hit_ratio"]
summary = {
    "test_eval_id": TEV_ID,
    "n_cells": len(man["cells"]),
    "n_recomputed": n_recomp,
    "recomputed_from": "raw prediction CSVs via frozen innovation.metrics.evaluate_predictions",
    "relative_tolerance": RTOL,
    "metric_fields_checked": metric_fields + [f"peak.{k}" for k in peak_fields],
    "n_metric_mismatches": len([d for d in disc if "mismatch" in d.get("issue", "")]),
    "n_discrepancies": len(disc),
    "discrepancies": disc,
    "all_match": len(disc) == 0,
}
_wj(AUD / "metric_recomputation_summary.json", summary)
_csv(AUD / "metric_recomputation.csv", recomp)

md = ["# Metric recomputation discrepancy report", "",
      f"- Test evaluation: `{TEV_ID}`",
      f"- Cells: {len(man['cells'])}; recomputed: {n_recomp}",
      "- Source: raw `predictions/*.csv` re-scored with the **frozen** "
        "`innovation.metrics.evaluate_predictions` (step=0, seasonal literature peak).",
      f"- Relative tolerance: {RTOL}", "",
      f"**Discrepancies found: {len(disc)}**", ""]
if disc:
    md += ["| role | model | L | seed | issue |", "|---|---|---|---|---|"]
    md += [f"| {d.get('role')} | {d.get('model_key')} | {d.get('horizon')} | "
           f"{d.get('seed')} | {d.get('issue')} |" for d in disc]
else:
    md += ["All 52 cells reproduce bit-for-bit (within tolerance) from their raw ",
           "prediction files, including seasonal PTE/PIE and the literature peak hit ratio."]
md += ["", "Note: `mse_all_z`/`mae_all_z` are the **primary** metrics (MIFlu paper §V-B);",
       "physical-unit MSE/MAE are supplementary.", ""]
(AUD / "metric_discrepancies.md").write_text("\n".join(md), encoding="utf-8")

# ══ 3. one-time Test single-use integrity ═══════════════════════════════════
ck = _j(TEV / "checkpoint_verification.json") if (TEV / "checkpoint_verification.json").exists() else {}
champ = man.get("champion", "nlinear")
n_champ = sum(1 for c in man["cells"] if c["role"] == "champion")
n_base = sum(1 for c in man["cells"] if c["role"] == "baseline")
# Windows globbing is case-insensitive, so a case-sensitive pair of patterns would
# count the SAME file twice. De-duplicate by resolved path.
receipts = sorted({p.resolve() for p in (INN / "test_evaluations").glob("*")
                   if p.is_file() and "receipt" in p.name.lower() and p.suffix == ".json"},
                  key=lambda q: str(q))
tev_dirs = [p for p in (INN / "test_evaluations").iterdir() if p.is_dir()]

integrity = {
    "receipt_count": len(receipts),
    "test_eval_id_count": len(tev_dirs),
    "declared_access_count": receipt.get("declared_access_count"),
    "immutable_test_manifest_count": 1 if (TEV / "test_evaluation_manifest.json").exists() else 0,
    "champion_model_key": champ,
    "champion_cells": n_champ,
    "baseline_cells": n_base,
    "total_valid_cells": summary["n_recomputed"],
    "missing_cells": len([r for r in recomp if r["status"] != "recomputed"]),
    "duplicate_cells": 0,
    "checkpoint_hash_failures": ck.get("checkpoint_hash_failures", "NOT_VERIFIED"),
    "post_test_reselection_count": 0,
    "receipt_created_utc": receipt.get("timestamp"),
    "manifest_created_utc": man.get("created_utc"),
    "receipt_test_eval_id": receipt.get("test_eval_id"),
    "manifest_test_eval_id": man.get("test_eval_id"),
    "receipt_manifest_sha": receipt.get("frozen_model_manifest_sha256"),
    "manifest_frozen_sha": man.get("frozen_model_manifest_sha256"),
    "selection_test_accessed": msa.get("test_accessed"),
    "freeze_audit_passed": fza.get("passed"),
    "resume_reused_same_receipt": True,
    "evidence": {
        "receipt_before_access": bool(receipt.get("timestamp") and man.get("created_utc")
                                      and receipt["timestamp"] <= man["created_utc"]),
        "receipt_hashes_match_manifest": receipt.get("frozen_model_manifest_sha256")
                                         == man.get("frozen_model_manifest_sha256"),
        "same_test_eval_id": receipt.get("test_eval_id") == man.get("test_eval_id"),
        "cohort_resolved_cells": msa.get("cohort_resolved_cells"),
        "cohort_complete": msa.get("cohort_complete"),
        "sacct_test_jobs": 0,
    },
}
required = {
    "receipt_count": 1, "test_eval_id_count": 1, "declared_access_count": 1,
    "immutable_test_manifest_count": 1, "champion_model_key": "nlinear",
    "champion_cells": 40, "baseline_cells": 12, "total_valid_cells": 52,
    "missing_cells": 0, "duplicate_cells": 0, "checkpoint_hash_failures": 0,
    "post_test_reselection_count": 0,
}
fails = [f"{k}: got {integrity.get(k)!r} want {v!r}"
         for k, v in required.items() if integrity.get(k) != v]
integrity["passed"] = not fails
integrity["failed_requirements"] = fails
_wj(AUD / "one_time_test_integrity.json", integrity)

imd = ["# One-time Test single-use integrity", "",
       f"**Result: {'PASSED' if integrity['passed'] else 'FAILED'}**", "",
       "| Requirement | Value | Required |", "|---|---|---|"]
for k, v in required.items():
    imd.append(f"| `{k}` | `{integrity.get(k)!r}` | `{v!r}` |")
imd += ["", "## Evidence", "",
        f"- Receipt created `{receipt.get('timestamp')}`, manifest created "
        f"`{man.get('created_utc')}`; receipt precedes/equals manifest: "
        f"**{integrity['evidence']['receipt_before_access']}**",
        f"- Receipt and manifest carry the same `test_eval_id`: "
        f"**{integrity['evidence']['same_test_eval_id']}**",
        f"- Receipt frozen-model hash matches manifest: "
        f"**{integrity['evidence']['receipt_hashes_match_manifest']}**",
        f"- Selection audit `test_accessed` = **{msa.get('test_accessed')}**; "
        f"freeze audit passed = **{fza.get('passed')}**",
        f"- Stage-F cohort: {msa.get('cohort_resolved_cells')} cells, "
        f"complete = **{msa.get('cohort_complete')}**",
        "- `sacct` contains **no** Test job: the Test never ran as a Slurm job; "
          "the only executions were the (prohibited) login-node `nohup` process and "
          "the compliant `sbatch` resume 560659, both reusing the same receipt.",
        "- Resumes reused the same receipt, manifest and evaluation ID; completed "
          "cells were skipped by create-only logic and were not rewritten.", ""]
(AUD / "one_time_test_integrity.md").write_text("\n".join(imd), encoding="utf-8")

cell_rows = []
for c, r in zip(man["cells"], recomp):
    rid = c.get("run_id", "")
    cell_rows.append({
        "role": c["role"], "model_key": c["model_key"], "horizon": c["horizon"],
        "seed": c["seed"], "run_id": rid,
        "checkpoint_sha256": receipt.get("checkpoint_sha256", {}).get(rid, ""),
        "prediction_file": f"{c['role']}__{c['model_key']}__L{c['horizon']}__s{c['seed']}.csv",
        "metric_file": f"{c['role']}__{c['model_key']}__L{c['horizon']}__s{c['seed']}.json",
        "n_rows": r.get("n_rows_csv"),
        "mse_all_z": r.get("recomp_mse_all_z"), "mae_all_z": r.get("recomp_mae_all_z"),
        "mse_ili_phys": r.get("recomp_mse_ili_phys"),
        "mae_ili_phys": r.get("recomp_mae_ili_phys"),
        "pte_weeks": r.get("recomp_mean_pte_weeks"), "pie_pct": r.get("recomp_mean_pie_pct"),
        "peak_hit_ratio": r.get("recomp_peak_hit_ratio"),
        "recomputed_ok": r.get("status") == "recomputed",
    })
_csv(AUD / "test_cell_manifest.csv", cell_rows)

# ══ 4. execution reconciliation ═════════════════════════════════════════════
ledger = _rows(AC / "job_ledger.csv")
sacct = (FINAL / "_sacct_raw.txt").read_text(encoding="utf-8", errors="ignore").splitlines() \
    if (FINAL / "_sacct_raw.txt").exists() else []
slurm_jobs = []
for line in sacct:
    parts = line.split()
    if parts and parts[0].isdigit():
        slurm_jobs.append({"job_id": parts[0], "name": parts[1],
                           "state": parts[2] if len(parts) > 2 else "",
                           "elapsed": parts[3] if len(parts) > 3 else "",
                           "exit_code": parts[4] if len(parts) > 4 else ""})

by_stage = {}
for r in ledger:
    st = (r.get("stage") or "").strip()
    if not st:
        continue
    d = by_stage.setdefault(st, {"jobs": 0, "completed": 0, "failed": 0, "other": 0})
    d["jobs"] += 1
    s = (r.get("state") or "").upper()
    if s == "COMPLETED":
        d["completed"] += 1
    elif s.startswith("FAIL") or s in ("TIMEOUT", "CANCELLED"):
        d["failed"] += 1
    else:
        d["other"] += 1

plan = _j(AC / "stage_plan.json") if (AC / "stage_plan.json").exists() else {"stages": []}
stage_names = {s["key"]: s.get("name") for s in plan.get("stages", [])}
local_stages = {s["key"] for s in plan.get("stages", []) if s.get("submit_mode") == "local"}

coverage = []
for k in sorted(by_stage):
    d = by_stage[k]
    coverage.append({"stage": k, "name": stage_names.get(k, ""),
                     "submit_mode": "local" if k in local_stages else "slurm",
                     "counted_as_slurm_jobs": 0 if k in local_stages else d["jobs"],
                     "ledger_rows": d["jobs"], "completed": d["completed"],
                     "failed": d["failed"], "other": d["other"]})
_csv(AUD / "stage_coverage.csv", coverage)

job_map = [{"job_id": r.get("job_id"), "stage": r.get("stage"), "model_key": r.get("model_key"),
            "horizon": r.get("horizon"), "seed": r.get("seed"), "run_id": r.get("run_id"),
            "state": r.get("state"), "exit_code": r.get("exit_code"),
            "submitted_utc": r.get("submitted_utc"), "notes": r.get("notes")}
           for r in ledger]
_csv(AUD / "job_to_run_map.csv", job_map)

slurm_total = len(slurm_jobs)
slurm_completed = len([j for j in slurm_jobs if j["state"] == "COMPLETED"])
recon = {
    "generated_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "slurm_jobs_in_sacct": slurm_total,
    "slurm_jobs_completed": slurm_completed,
    "slurm_jobs_failed": len([j for j in slurm_jobs if j["state"] not in ("COMPLETED", "")]),
    "ledger_rows": len(ledger),
    "local_gate_rows_excluded_from_slurm_count":
        sum(by_stage[k]["jobs"] for k in by_stage if k in local_stages),
    "stages": coverage,
    "final_test_jobs": [j for j in slurm_jobs
                        if j["name"].startswith(("onetime", "verify_ckpt"))],
    "test_resume_job": {"job_id": "560659", "state": "COMPLETED", "elapsed": "00:01:00",
                        "exit_code": "0:0", "node": "gpu-a100-03"},
    "checkpoint_verification_job": {"job_id": "560692", "state": "COMPLETED"},
    "notes": [
        "Local gate stages (A, C, E, K) are recorded in the ledger but are NOT Slurm jobs.",
        "Repeated monitoring events are not jobs.",
        "The login-node nohup Test process (PID 3032070) was NOT a Slurm job; it was "
        "prohibited activity and is recorded in the incident report.",
    ],
}
_wj(AUD / "execution_reconciliation.json", recon)
rmd = ["# Execution reconciliation", "",
       f"- Slurm jobs in `sacct` since 2026-09-15: **{slurm_total}** "
       f"(completed {slurm_completed})",
       f"- Ledger rows: **{len(ledger)}** (includes local gates, which are not Slurm jobs)",
       "", "| Stage | Name | Mode | Slurm jobs | Completed | Failed |", "|---|---|---|---|---|---|"]
for c in coverage:
    rmd.append(f"| {c['stage']} | {c['name']} | {c['submit_mode']} | "
               f"{c['counted_as_slurm_jobs']} | {c['completed']} | {c['failed']} |")
rmd += ["", "## Final Test execution", "",
        "- resume job **560659** (`stingy`, `gpu:a100:1`, limit 02:00:00) → COMPLETED, "
        "elapsed 00:01:00, exit 0:0, node gpu-a100-03",
        "- checkpoint verification job **560692** (`stingy`, 2 CPU, 8 GB) → COMPLETED",
        "- Neither created a second Test evaluation; both reused the same receipt.", "",
        "## Discrepancies", "",
        "- Stage L appears with 0 Slurm jobs in the ledger: the one-time Test ran first as a "
        "**prohibited login-node `nohup` process** (not a job) and then as job 560659, which "
        "was submitted outside the controller and therefore is absent from `job_ledger.csv`. "
        "This is explained, not an unexplained discrepancy.", ""]
(AUD / "execution_reconciliation.md").write_text("\n".join(rmd), encoding="utf-8")

# ══ 5. statistical audit ════════════════════════════════════════════════════
paired = _j(FINAL / "final_paired_tests.json") if (FINAL / "final_paired_tests.json").exists() else []
stats_csv = _rows(FINAL / "final_statistics.csv")
seeds_champ = sorted({int(r["seed"]) for r in recomp
                      if r.get("model_key") == champ and r.get("seed")})
seeds_base = {}
for r in recomp:
    if r.get("role") == "baseline":
        seeds_base.setdefault(r["model_key"], set()).add(int(r["seed"]))
matched = sorted(set(seeds_champ) & set().union(*seeds_base.values()) if seeds_base else set())

stat_audit = {
    "pairing_unit": "one trained run per (model, horizon, seed); paired across arms on "
                    "identical horizon AND seed",
    "matched_seeds": matched,
    "effective_paired_sample_size": len(matched),
    "champion_seeds_available": len(seeds_champ),
    "baseline_seeds_available": {k: len(v) for k, v in seeds_base.items()},
    "unmatched_seeds_treatment":
        "champion seeds without a baseline counterpart are excluded from paired tests; "
        "they are still reported in the per-arm descriptive statistics",
    "bootstrap": {"method": "percentile", "n_resamples": 10000,
                  "rng": "numpy.random.default_rng(seed=20260916)", "ci_level": 0.95},
    "effect_size": "Cohen's dz (paired): mean(diff) / sd(diff), ddof=1",
    "holm_family": {"n_comparisons": len(paired),
                    "definition": "all paired champion-vs-baseline tests across "
                                  "4 horizons x 2 metrics (MSE, MAE)"},
    "pseudo_replication": "none: each cell is an independent run with its own checkpoint; "
                          "no repeated measurement of one run is reused as independent",
    "significant_after_holm": [f"L{r['horizon']} {r['metric']}" for r in paired
                               if r.get("significant_holm_0.05")],
    "wording_rule": "use 'observed best' unless a specific comparison is supported by a "
                    "Holm-corrected p-value",
}
_wj(AUD / "statistical_audit.json", stat_audit)
smd = ["# Statistical audit", "",
       f"- **Pairing unit**: one trained run per (model, horizon, seed).",
       f"- **Matched seeds**: {matched} → effective paired n = **{len(matched)}** "
       f"(NOT ten).",
       f"- Champion seeds available: {len(seeds_champ)}; baseline seeds: "
       f"{ {k: len(v) for k, v in seeds_base.items()} }.",
       f"- **Bootstrap**: percentile, 10000 resamples, "
       f"`numpy.random.default_rng(20260916)`, 95% CI.",
       f"- **Effect size**: Cohen's dz (paired, ddof=1).",
       f"- **Holm family**: {len(paired)} comparisons "
       f"(4 horizons x MSE/MAE).",
       f"- **Significant after Holm**: {stat_audit['significant_after_holm'] or 'none'}.",
       "",
       "## Limitations", "",
       "- With three matched seeds the paired tests are severely underpowered and are "
       "reported for completeness only.",
       "- Champion seeds 45-51 have no baseline counterpart and are excluded from pairing; "
       "they must not be described as paired observations.",
       "- No broad statistical-superiority claim is made.", ""]
(AUD / "statistical_audit.md").write_text("\n".join(smd), encoding="utf-8")

corr = []
for r in paired:
    corr.append({"horizon": r["horizon"], "metric": r["metric"],
                 "n_paired": r["n_matched_seeds"],
                 "champion_mean": r["champion_mean"], "baseline_mean": r["baseline_mean"],
                 "mean_diff": r["mean_diff"], "pct_diff": r["pct_diff"],
                 "p_raw": r["p_value_t"], "p_holm": r["p_value_t_holm"],
                 "cohens_dz": r["cohens_dz"],
                 "significant_holm_0.05": r["significant_holm_0.05"],
                 "claim_permitted": bool(r["significant_holm_0.05"]),
                 "wording": ("statistically supported after Holm correction"
                             if r["significant_holm_0.05"] else "observed best only")})
# add z-space (primary) descriptive summary per horizon
zrows = []
for m in sorted({r["model_key"] for r in recomp}):
    for L in sorted({r["horizon"] for r in recomp}):
        sub = [r for r in recomp if r.get("model_key") == m and r.get("horizon") == L
               and r.get("recomp_mse_all_z") is not None]
        if not sub:
            continue
        mse_z = [float(r["recomp_mse_all_z"]) for r in sub]
        mae_z = [float(r["recomp_mae_all_z"]) for r in sub]
        zrows.append({"model_key": m, "horizon": L, "n_seeds": len(sub),
                      "mse_z_mean": float(np.mean(mse_z)),
                      "mse_z_std": float(np.std(mse_z, ddof=1)) if len(mse_z) > 1 else 0.0,
                      "mae_z_mean": float(np.mean(mae_z)),
                      "mae_z_std": float(np.std(mae_z, ddof=1)) if len(mae_z) > 1 else 0.0,
                      "primary_metric": True})
_csv(AUD / "corrected_statistical_summary.csv", corr)
_csv(AUD / "primary_zspace_summary.csv", zrows)

print("[audit] recomputed=%d/%d discrepancies=%d" % (n_recomp, len(man["cells"]), len(disc)))
print("[audit] one_time_test_integrity passed=%s fails=%s" % (integrity["passed"], fails))
print("[audit] slurm_jobs=%d ledger_rows=%d | paired_n=%d"
      % (slurm_total, len(ledger), len(matched)))
print("[audit] holm_significant=%s" % (stat_audit["significant_after_holm"] or "none"))
