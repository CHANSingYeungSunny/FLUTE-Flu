#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_table_ix.py — Table IX (training time) from the Table VI regional cells.

WHY THIS FILE EXISTS
--------------------
`docs/WORK_BREAKDOWN.md` §13.D corrected an earlier claim: **Table IX is the
training time of the REGIONAL models**, so it depends on the Table VI
configuration (`T=20`, `L ∈ {2,3,5,10,13,15,20}`, `K=4`, 50 epochs, batch 32)
having actually been run and timed. A national timing table is a different table
and must never be labelled IX.

`scripts/train_regional.py` now writes, in every cell manifest, the measured
`wall_seconds` plus the rule-12 hardware block (GPU name, partition, node, job
id). This script aggregates exactly those fields — it does **not** re-time
anything and it does **not** invent a number: a cell with no measured
`wall_seconds`, or one flagged `probe_only`, is excluded and reported.

Output
------
    paper_tables/TABLE_IX_REGIONAL_TRAINING_TIME.csv
        one row per (model, L, seed) cell: wall_seconds, minutes, GPU, partition,
        node, job id, n_params, n_train_windows, plus the cell's manifest path.
    paper_tables/TABLE_IX_REGIONAL_TRAINING_TIME_MEANS.csv
        mean ± sd minutes per (model, L) over seeds — the table's body.

Usage
-----
    python scripts/build_table_ix.py --check          # what is available?
    python scripts/build_table_ix.py                  # write both CSVs

Gate (the queue's Table IX row): the row only becomes `TODO` once the Table VI
cells it needs are `DONE`; `--check` exits 3 when there is nothing measured yet,
which is what the queue's success criterion should key on.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGIONAL_ROOT = os.path.join(PROJECT_ROOT, "hpc_results", "regional")
OUT_DIR = os.path.join(PROJECT_ROOT, "paper_tables")
OUT_CELLS = os.path.join(OUT_DIR, "TABLE_IX_REGIONAL_TRAINING_TIME.csv")
OUT_MEANS = os.path.join(OUT_DIR, "TABLE_IX_REGIONAL_TRAINING_TIME_MEANS.csv")


def find_manifests(root: str = REGIONAL_ROOT) -> list:
    """Every `manifest_*.json` under the regional tree (one per Table VI cell)."""
    return sorted(glob.glob(os.path.join(root, "**", "manifest_*.json"),
                            recursive=True))


def collect(root: str = REGIONAL_ROOT) -> tuple:
    """Return `(rows, skipped)` from the regional manifests.

    A row is emitted only when the manifest carries a measured `wall_seconds`;
    `skipped` records why a manifest was not usable, so the report can say
    "3 cells are still probe-only" instead of silently shrinking the table.
    """
    rows, skipped = [], []
    for path in find_manifests(root):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                m = json.load(fh)
        except Exception as exc:                    # noqa: BLE001
            skipped.append((path, f"unreadable: {type(exc).__name__}: {exc}"))
            continue
        wall = m.get("wall_seconds")
        if wall is None:
            skipped.append((path, "no measured wall_seconds"))
            continue
        if m.get("probe_only"):
            skipped.append((path, "probe_only=True (rule 13(b))"))
            continue
        hw = m.get("hardware") or {}
        slurm = m.get("slurm") or {}
        cfg = m.get("config") or {}
        params = cfg.get("params")
        if not isinstance(params, dict):        # older manifests stringified it
            params = {}
        rows.append({
            "model": m.get("model"), "region": m.get("region"),
            "L": m.get("L"), "seed": m.get("seed"),
            "wall_seconds": round(float(wall), 3),
            "minutes": round(float(wall) / 60.0, 3),
            "gpu": hw.get("gpu_name"), "run_device": hw.get("run_device"),
            "partition": slurm.get("SLURM_JOB_PARTITION"),
            "node": slurm.get("SLURM_NODELIST"),
            "job_id": slurm.get("SLURM_JOB_ID"),
            "epochs": cfg.get("epochs"), "batch": cfg.get("batch"),
            "K": cfg.get("K"), "n_vars": m.get("n_vars"),
            "n_train_windows": cfg.get("n_train_windows"),
            "trainable_parameters": params.get("trainable_parameters"),
            "manifest": os.path.relpath(path, PROJECT_ROOT),
        })
    return rows, skipped


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    """Mean ± sd minutes per (model, L) over seeds — the published Table IX body."""
    if df.empty:
        return df
    g = df.groupby(["model", "L"], as_index=False).agg(
        n_seeds=("seed", "nunique"),
        minutes_mean=("minutes", "mean"),
        minutes_sd=("minutes", "std"),
        gpu=("gpu", "first"),
        partition=("partition", "first"))
    return g.sort_values(["model", "L"]).reset_index(drop=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Aggregate Table IX (regional training time) from the Table VI "
                    "cell manifests. Nothing is re-timed.")
    ap.add_argument("--root", default=REGIONAL_ROOT)
    ap.add_argument("--check", action="store_true",
                    help="Report what is available; exit 3 if nothing measured.")
    ap.add_argument("--out-dir", default=OUT_DIR)
    a = ap.parse_args(argv)

    rows, skipped = collect(a.root)
    print(f"[table-ix] manifests found: {len(find_manifests(a.root))} "
          f"usable: {len(rows)} skipped: {len(skipped)}")
    for path, why in skipped[:10]:
        print(f"  skip {os.path.relpath(path, PROJECT_ROOT)}: {why}")
    if not rows:
        print("[table-ix] NOTHING MEASURED YET — Table IX stays blocked until the "
              "Table VI cells are DONE (WORK_BREAKDOWN §13.D)")
        return 3

    df = pd.DataFrame(rows).sort_values(["model", "L", "seed"])
    means = summarise(df)
    print(df[["model", "L", "seed", "minutes", "gpu", "partition"]]
          .to_string(index=False))
    print("\nmean minutes per (model, L):")
    print(means.to_string(index=False))

    # Rule 12: a timing table must name its hardware, and must not mix GPUs.
    gpus = sorted({str(g) for g in df["gpu"] if g})
    print(f"\n[table-ix] hardware = {gpus or 'CPU only'}, "
          f"partitions = {sorted({str(p) for p in df['partition'] if p})}")
    if len(gpus) > 1:
        print("[table-ix][WARN] more than one GPU model in this table: no timing "
              "claim may cross it (AGENTS.md rule 12)")

    if a.check:
        return 0
    os.makedirs(a.out_dir, exist_ok=True)
    cells = os.path.join(a.out_dir, os.path.basename(OUT_CELLS))
    means_path = os.path.join(a.out_dir, os.path.basename(OUT_MEANS))
    df.to_csv(cells, index=False)
    means.to_csv(means_path, index=False)
    print(f"[table-ix] wrote {cells}\n[table-ix] wrote {means_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
