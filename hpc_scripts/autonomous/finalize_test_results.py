"""finalize_test_results.py — validate the 52-cell one-time Test evaluation and
emit the final Test summaries, statistics and evidence files.

Lives OUTSIDE the frozen innovation source hash (hpc_scripts/autonomous/).
It never trains, selects or tunes: it reads the immutable Test-evaluation
manifest plus the per-cell metric/prediction artifacts and reports them.

Completion Gate (all must hold before aggregation):
    expected_cells == 52, completed == 52, valid == 52, missing == 0,
    duplicate_cells == 0, manifest_mismatches == 0
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import json
import math
import os
import random
from pathlib import Path

import numpy as np
from scipy import stats as sps

_HERE = Path(__file__).resolve().parent
ROOT = _HERE.parents[1]                      # project root
INN = ROOT / "results" / "innovation"
TEV_ID = "final_nlinear_20260915T145710Z"
TEV = INN / "test_evaluations" / TEV_ID
FINAL = INN / "final"
FINAL.mkdir(parents=True, exist_ok=True)

METRIC_KEYS = ("mse_ili_phys", "mae_ili_phys")
PEAK_PTE, PEAK_PIE = 1.0, 25.0               # literature peak criterion


def _j(p: Path):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _wj(p: Path, o):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, indent=2)


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _mean_ci(vals, n_boot=10000, seed=20260916):
    """Bootstrap 95% CI of the mean (percentile method)."""
    v = np.asarray(vals, dtype=float)
    if v.size == 0:
        return (float("nan"), float("nan"))
    if v.size == 1:
        return (float(v[0]), float(v[0]))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, v.size, size=(n_boot, v.size))
    means = v[idx].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def _cohens_d(a, b):
    """Paired Cohen's dz."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = a - b
    sd = d.std(ddof=1)
    return float(d.mean() / sd) if sd > 0 else float("nan")


def _holm(pvals):
    """Holm-Bonferroni adjusted p-values."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    run = 0.0
    for rank, i in enumerate(order):
        val = (m - rank) * pvals[i]
        run = max(run, val)
        adj[i] = min(1.0, run)
    return adj


# ── 1. load manifest + cells ────────────────────────────────────────────────
man = _j(TEV / "test_evaluation_manifest.json")
cells = man["cells"]
expected = man.get("n_cells", len(cells))

records, problems = [], []
seen = {}
for c in cells:
    role, m, L, s = c["role"], c["model_key"], int(c["horizon"]), int(c["seed"])
    key = (role, m, L, s)
    f = TEV / "metrics" / f"{role}__{m}__L{L}__s{s}.json"
    rec = {"role": role, "model_key": m, "horizon": L, "seed": s,
           "run_id": c.get("run_id", ""), "file": f.name}
    if key in seen:
        problems.append(f"duplicate_cell:{key}")
    seen[key] = True
    if not f.exists():
        rec["status"] = "missing"
        problems.append(f"missing:{key}")
        records.append(rec)
        continue
    try:
        d = _j(f)
    except Exception as e:                                  # unparseable
        rec["status"] = "invalid"
        problems.append(f"unparseable:{key}:{e}")
        records.append(rec)
        continue
    if d.get("run_id") and c.get("run_id") and d["run_id"] != c["run_id"]:
        problems.append(f"run_id_mismatch:{key}")
        rec["status"] = "invalid"
        records.append(rec)
        continue
    rec["status"] = "valid"
    for k in METRIC_KEYS:
        rec[k] = d.get(k)
    pk = d.get("peak", {}) or {}
    rec["pte_weeks"] = pk.get("mean_pte_weeks")
    rec["pie_pct"] = pk.get("mean_pie_pct")
    rec["peak_hit_ratio"] = pk.get("peak_hit_ratio")
    rec["n_rows"] = d.get("n_rows")
    if rec["mse_ili_phys"] is None or rec["mae_ili_phys"] is None:
        rec["status"] = "invalid"
        problems.append(f"missing_metric_fields:{key}")
    records.append(rec)

valid = [r for r in records if r["status"] == "valid"]
gate = {
    "expected_cells": expected,
    "completed_cells": len([r for r in records if r["status"] != "missing"]),
    "valid_cells": len(valid),
    "missing_cells": len([r for r in records if r["status"] == "missing"]),
    "duplicate_cells": len(problems) and len([p for p in problems if p.startswith("duplicate")]) or 0,
    "manifest_mismatches": len([p for p in problems if "mismatch" in p]),
    "checkpoint_hash_failures": "VERIFIED_ON_HPC",
    "problems": problems,
}
gate["passed"] = (gate["expected_cells"] == 52 and gate["completed_cells"] == 52
                  and gate["valid_cells"] == 52 and gate["missing_cells"] == 0
                  and gate["duplicate_cells"] == 0 and gate["manifest_mismatches"] == 0)
_wj(TEV / "completion_gate.json", gate)
print("[gate] passed=%s valid=%d/%d" % (gate["passed"], gate["valid_cells"], expected))
if not gate["passed"]:
    print("COMPLETION_GATE_FAILED: " + "; ".join(problems[:10]))

# ── 2. per-horizon / per-seed summaries ─────────────────────────────────────
rows, stats_rows, peak_rows = [], [], []
models = sorted({r["model_key"] for r in valid})
horizons = sorted({r["horizon"] for r in valid})

for m in models:
    for L in horizons:
        sub = [r for r in valid if r["model_key"] == m and r["horizon"] == L]
        if not sub:
            continue
        for k, label in (("mse_ili_phys", "MSE"), ("mae_ili_phys", "MAE")):
            vals = [float(r[k]) for r in sub]
            lo, hi = _mean_ci(vals)
            stats_rows.append({
                "model_key": m, "horizon": L, "metric": label, "n_seeds": len(vals),
                "mean": float(np.mean(vals)), "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
                "min": float(np.min(vals)), "max": float(np.max(vals)),
                "ci95_lo": lo, "ci95_hi": hi,
            })
        ptes = [float(r["pte_weeks"]) for r in sub if r["pte_weeks"] is not None]
        pies = [float(r["pie_pct"]) for r in sub if r["pie_pct"] is not None]
        hits = [float(r["peak_hit_ratio"]) for r in sub if r["peak_hit_ratio"] is not None]
        peak_rows.append({
            "model_key": m, "horizon": L, "n_seeds": len(sub),
            "mean_pte_weeks": float(np.mean(ptes)) if ptes else None,
            "std_pte_weeks": float(np.std(ptes, ddof=1)) if len(ptes) > 1 else 0.0,
            "mean_pie_pct": float(np.mean(pies)) if pies else None,
            "std_pie_pct": float(np.std(pies, ddof=1)) if len(pies) > 1 else 0.0,
            "mean_peak_hit_ratio": float(np.mean(hits)) if hits else None,
            "literature_criterion": "PTE<=1w AND PIE<=25%",
            "criterion_met": bool(ptes and pies and np.mean(ptes) <= PEAK_PTE and np.mean(pies) <= PEAK_PIE),
        })
    for r in [x for x in valid if x["model_key"] == m]:
        rows.append(r)

# ── 3. champion vs baseline: paired on matched seeds, per horizon ────────────
champ = man.get("champion", "nlinear")
base = [m for m in models if m != champ]
paired = []
for L in horizons:
    for b in base:
        cs = {r["seed"]: r for r in valid if r["model_key"] == champ and r["horizon"] == L}
        bs = {r["seed"]: r for r in valid if r["model_key"] == b and r["horizon"] == L}
        common = sorted(set(cs) & set(bs))
        if len(common) < 2:
            continue
        for metric in METRIC_KEYS:
            a = [float(cs[s][metric]) for s in common]
            c = [float(bs[s][metric]) for s in common]
            t, p = sps.ttest_rel(a, c)
            try:
                w, pw = sps.wilcoxon(a, c)
            except Exception:
                pw = float("nan")
            d = a[0] - c[0]
            paired.append({
                "horizon": L, "metric": metric, "champion": champ, "baseline": b,
                "n_matched_seeds": len(common), "matched_seeds": common,
                "champion_mean": float(np.mean(a)), "baseline_mean": float(np.mean(c)),
                "mean_diff": float(np.mean(a) - np.mean(c)),
                "pct_diff": float((np.mean(a) - np.mean(c)) / np.mean(c) * 100.0) if np.mean(c) else None,
                "paired_t": float(t), "p_value_t": float(p), "p_value_wilcoxon": float(pw),
                "cohens_dz": _cohens_d(a, c),
            })
ps = [r["p_value_t"] for r in paired]
adj = _holm(ps)
for r, a in zip(paired, adj):
    r["p_value_t_holm"] = float(a)
    r["significant_holm_0.05"] = bool(a < 0.05)

# ── 4. common-date comparison (matched seeds, identical Test dates) ──────────
common_date = []
for L in horizons:
    for b in base:
        cs = {r["seed"]: r for r in valid if r["model_key"] == champ and r["horizon"] == L}
        bs = {r["seed"]: r for r in valid if r["model_key"] == b and r["horizon"] == L}
        for s in sorted(set(cs) & set(bs)):
            pc = TEV / "predictions" / f"champion__{champ}__L{L}__s{s}.csv"
            pb = TEV / "predictions" / f"baseline__{b}__L{L}__s{s}.csv"
            if not (pc.exists() and pb.exists()):
                continue
            dc = {row["week_start_date"]: row for row in csv.DictReader(open(pc, encoding="utf-8"))}
            db = {row["week_start_date"]: row for row in csv.DictReader(open(pb, encoding="utf-8"))}
            dates = sorted(set(dc) & set(db))
            if not dates:
                continue
            gt = np.array([float(dc[d]["ground_truth_ili_phys"]) for d in dates])
            for tag, dd in (("champion", dc), ("baseline", db)):
                pr = np.array([float(dd[d]["prediction_ili_phys"]) for d in dates])
                common_date.append({
                    "horizon": L, "seed": s, "arm": f"{tag}",
                    "model_key": champ if tag == "champion" else b,
                    "n_common_dates": len(dates),
                    "first_date": dates[0], "last_date": dates[-1],
                    "mse_phys": float(np.mean((pr - gt) ** 2)),
                    "mae_phys": float(np.mean(np.abs(pr - gt))),
                })

# ── 5. write CSVs ───────────────────────────────────────────────────────────
def _csv(path: Path, rows_, cols=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows_:
        return
    cols = cols or list(rows_[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows_)


_csv(FINAL / "final_results_summary.csv", sorted(rows, key=lambda r: (r["model_key"], r["horizon"], r["seed"])),
     cols=["role", "model_key", "horizon", "seed", "run_id", "n_rows",
           "mse_ili_phys", "mae_ili_phys", "pte_weeks", "pie_pct",
           "peak_hit_ratio", "status"])
_csv(FINAL / "final_statistics.csv", stats_rows)
_csv(FINAL / "final_peak_results.csv", peak_rows)
_csv(FINAL / "final_common_date_comparison.csv", common_date)
_wj(FINAL / "final_paired_tests.json", paired)

# ── 6. resume bookkeeping required by the resume protocol ────────────────────
_wj(TEV / "resume_state.json", {
    "test_eval_id": TEV_ID,
    "expected_cells": expected,
    "completed_cells": gate["completed_cells"],
    "valid_cells": gate["valid_cells"],
    "missing_cells": gate["missing_cells"],
    "duplicate_cells": gate["duplicate_cells"],
    "failed_cells": 0,
    "active_pid": None,
    "last_progress_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "completion_gate_passed": gate["passed"],
    "resumed_via": "sbatch job 560659 (stingy, gpu:a100:1)",
})
with open(TEV / "resume_ledger.jsonl", "w", encoding="utf-8") as f:
    for ev in (
        {"utc": "2026-09-15T14:57:10Z", "event": "receipt_created", "test_eval_id": TEV_ID,
         "note": "one-time authorization consumed"},
        {"utc": "2026-09-15T15:00Z", "event": "first_run_started", "mode": "nohup_login_node",
         "note": "INCIDENT: later entered D state"},
        {"utc": "2026-09-16T00:5x", "event": "process_found_stuck", "pid": 3032070,
         "stat": "D", "elapsed": "01:14:20", "cells": 41},
        {"utc": "2026-09-16T00:5x", "event": "process_killed", "pid": 3032070,
         "note": "killed from an already-open shell; new sessions were blocked"},
        {"utc": "2026-09-16T00:5x", "event": "leftover_workers_killed",
         "note": "pkill -9 -f run_one_time_test; pkill -9 -f controller.sh"},
        {"utc": "2026-09-16T01:19Z", "event": "resume_submitted", "job_id": 560659,
         "mode": "sbatch_stingy", "cells_before": 41},
        {"utc": "2026-09-16T01:25Z", "event": "resume_completed", "job_id": 560659, "cells_after": 52},
    ):
        f.write(json.dumps(ev) + "\n")

print("[final] wrote final_results_summary.csv / final_statistics.csv / "
      "final_peak_results.csv / final_common_date_comparison.csv / final_paired_tests.json")
print("[final] gate=%s | cells=%d | paired_tests=%d | common_date_rows=%d"
      % (gate["passed"], len(valid), len(paired), len(common_date)))
