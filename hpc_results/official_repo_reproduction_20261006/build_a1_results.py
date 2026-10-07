#!/usr/bin/env python3
"""Build the A1 result tables from the artefacts the author's own entry point
wrote on the HPC.

Reads the per-epoch CSVs the released code produces (./results/<setting>.csv)
and the per-run provenance.txt, then emits:

    a1_results_per_epoch.csv      every epoch of every A1 run
    a1_results_per_run.csv        the headline number per (horizon, repetition)
    a1_results_aggregate.csv      mean over the runs that exist
    a1_gpu_ledger.csv             the GPU charge recorded by the sbatch script

CRITICAL CAVEAT, restated in every table: the released entry point scores
**feature 0 only** and selects its checkpoint by **Test MSE**, so these numbers
are NOT comparable to the paper's Table V or to A2's seven-variable
validation-selected scores. They are the A1 track's own, differently-defined
quantity.
"""
import csv
import glob
import io
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "hpc_a1")
RUNS = os.path.join(HERE, "hpc_a1_runs")

CAVEAT = ("released entry point scores FEATURE 0 ONLY and selects the checkpoint "
          "by TEST MSE; not comparable to Table V or to A2")


def parse_provenance(path):
    d = {}
    for line in io.open(path, encoding="utf-8", errors="replace"):
        if "=" in line:
            k, v = line.strip().split("=", 1)
            d[k] = v
    return d


def load_run(csvpath, provpath):
    rows = list(csv.DictReader(io.open(csvpath, encoding="utf-8")))
    if not rows:
        return None, []
    ep = [{
        "horizon": None, "repetition": int(r["iteration"]), "epoch": int(r["epoch"]),
        "mse": float(r["mse"]), "mae": float(r["mae"]),
    } for r in rows]
    prov = parse_provenance(provpath) if os.path.exists(provpath) else {}
    return ep, prov


def main():
    os.makedirs(RUNS, exist_ok=True)
    # collect every L*/ dir produced on the HPC (L24 is under hpc_a1, others in
    # hpc_a1_runs once downloaded)
    search = []
    for base in (SRC, RUNS):
        search += glob.glob(os.path.join(base, "**", "*.csv"), recursive=True)

    per_epoch, per_run = [], []
    for csvpath in sorted(search):
        if os.path.basename(csvpath) == "a1_results_per_epoch.csv":
            continue
        d = os.path.dirname(csvpath)
        prov = os.path.join(d, "provenance.txt")
        m = re.search(r"_pl(\d+)_", os.path.basename(csvpath))
        L = int(m.group(1)) if m else None
        ep, pv = load_run(csvpath, prov)
        if not ep:
            continue
        for e in ep:
            e["horizon"] = L
            e["source_csv"] = os.path.relpath(csvpath, HERE)
            per_epoch.append(e)

        best = min(ep, key=lambda x: x["mse"])
        final = ep[-1]
        per_run.append({
            "track": "A1_reconstructed_paper_config",
            "horizon": L,
            "repetition": pv.get("itr_provenance", "") and 0,
            "itr": pv.get("slurm_job", "").split("_")[-1] or "",
            "slurm_job": pv.get("slurm_job", ""),
            "epochs": 20,
            "epochs_provenance": "RECONSTRUCTED (paper discloses no value)",
            "learning_rate": "5e-4",
            "lr_provenance": "RECONSTRUCTED (paper discloses no value)",
            "lr_schedule": "type1 exponential decay, decay_fac=0.75 (released default, MEASURED active)",
            "batch_size": 16,
            "multimodal": 1,
            "PEFT": 1,
            "lora_r": 4,
            "wall_seconds": pv.get("wall_seconds", ""),
            "author_exit_code": pv.get("author_exit_code", ""),
            "best_epoch": best["epoch"],
            "mse_best_epoch": f"{best['mse']:.6f}",
            "mae_best_epoch": f"{best['mae']:.6f}",
            "mse_final_epoch": f"{final['mse']:.6f}",
            "mae_final_epoch": f"{final['mae']:.6f}",
            "mse_mean_over_epochs": f"{sum(e['mse'] for e in ep) / len(ep):.6f}",
            "metric_caveat": CAVEAT,
            "known_defects_kept": "Test-selects-checkpoint; early_stopping commented out; freeze is a no-op",
            "checkpoint_sha256": pv.get("checkpoint_sha256", "not computed"),
        })

    def w(name, rows):
        if not rows:
            print(f"  (skip {name})")
            return
        p = os.path.join(HERE, name)
        with io.open(p, "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), extrasaction="ignore")
            wr.writeheader()
            wr.writerows(rows)
        print(f"  wrote {name} ({len(rows)} rows)")

    w("a1_results_per_epoch.csv", per_epoch)
    w("a1_results_per_run.csv", per_run)

    # aggregate per horizon (mean over the repetitions that exist)
    byL = defaultdict(list)
    for r in per_run:
        byL[r["horizon"]].append(r)
    agg = []
    for L in sorted(byL, key=lambda x: (x is None, x)):
        rs = byL[L]
        agg.append({
            "track": "A1_reconstructed_paper_config",
            "horizon": L,
            "n_repetitions_completed": len(rs),
            "n_repetitions_paper": 10,
            "mse_mean_over_epochs": f"{sum(float(r['mse_mean_over_epochs']) for r in rs) / len(rs):.6f}",
            "mse_best_epoch_mean": f"{sum(float(r['mse_best_epoch']) for r in rs) / len(rs):.6f}",
            "mae_best_epoch_mean": f"{sum(float(r['mae_best_epoch']) for r in rs) / len(rs):.6f}",
            "status": "PARTIAL - 1 of the paper's 10 repetitions",
            "metric_caveat": CAVEAT,
        })
    w("a1_results_aggregate.csv", agg)

    # GPU ledger produced by the sbatch script itself
    led = os.path.join(HERE, "hpc_a1_ledger.tsv")
    if os.path.exists(led):
        rows = []
        for line in io.open(led, encoding="utf-8"):
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 6:
                rows.append({"tag": parts[0], "slurm_job": parts[1], "horizon": parts[2],
                             "itr": parts[3], "elapsed": parts[4], "author_rc": parts[5]})
        w("a1_gpu_ledger.csv", rows)

    print("\nA1 summary")
    for r in agg:
        print(f"  L={r['horizon']:>2}  n_rep={r['n_repetitions_completed']}  "
              f"mse_mean_over_epochs={r['mse_mean_over_epochs']}  "
              f"best_epoch_mse={r['mse_best_epoch_mean']}")
    print(f"\n  CAVEAT: {CAVEAT}")


if __name__ == "__main__":
    main()