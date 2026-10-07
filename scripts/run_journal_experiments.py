#!/usr/bin/env python
"""
run_journal_experiments.py — Orchestrate the journal-reproducibility HPC runs
=============================================================================

Runs the Table VIII ablation variants + the training-recipe sweep + the
peak-aware early-stopping study as a SEQUENCE of independent jobs, each writing
to its own directory under `hpc_results/journal_evidence/<exp>/reps_1_to_10/`.

WHY SEQUENTIAL
--------------
The `stingy` partition allows only ONE job at a time, with a 4h wall limit.
`train_ablation.py` already supports per-experiment resume, so a single job that
overruns can simply be re-submitted and it will skip completed (L, rep) pairs.

WHAT IT RUNS (priority subset, per the advisor's approved scope)
---------------------------------------------------------------
  A. Table VIII variants × L=24 × 10 reps:
       full, no_multi, no_lora, no_lora_multi
  B. Training-recipe sweep on `full` × L=24 × 10 reps:
       adamw_cosine, huber_clip
  C. Early stopping on validation loss, on `full` × L=24 × 10 reps:
       --early-stop --patience 5

Each experiment is invoked exactly like a manual run, e.g.:
  python scripts/train_ablation.py --variant full --horizon 24 --reps 10 \
      --epochs 20 --batch 16 --export-dir <out>/reps_1_to_10

Usage:
  python scripts/run_journal_experiments.py            # run everything
  python scripts/run_journal_experiments.py --only full
  python scripts/run_journal_experiments.py --dry-run  # print commands only
  python scripts/run_journal_experiments.py --full-l   # also sweep L=24,36,48,60
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
OUT_ROOT = os.path.join(PROJECT_ROOT, "hpc_results", "journal_evidence")

# (name, [extra args])  --export-dir is appended automatically.
BASE_VARIANTS = [
    ("full",         ["--variant", "full"]),
    ("no_multi",     ["--variant", "no_multi"]),
    ("no_lora",      ["--variant", "no_lora"]),
    ("no_lora_multi",["--variant", "no_lora_multi"]),
]
RECIPE_SWEEP = [
    ("full__adamw_cosine", ["--variant", "full", "--recipe", "adamw_cosine"]),
    ("full__huber_clip",   ["--variant", "full", "--recipe", "huber_clip"]),
]
EARLYSTOP = [
    ("full__earlystop", ["--variant", "full", "--early-stop",
                         "--patience", "5"]),
]

DEFAULT_ARGS = ["--horizon", "24", "--reps", "10", "--epochs", "20",
                "--batch", "16", "--seed", "42"]


def build_experiments(full_l: bool):
    exps = BASE_VARIANTS + RECIPE_SWEEP + EARLYSTOP
    if full_l:
        # Expand each into the 4 horizons (Table VIII full sweep).
        expanded = []
        for name, args in exps:
            for L in (24, 36, 48, 60):
                expanded.append((f"{name}_L{L}", args + ["--horizon", str(L)]))
        return expanded
    return exps


def run_one(name: str, args: list, dry_run: bool):
    out_dir = os.path.join(OUT_ROOT, name, "reps_1_to_10")
    cmd = [sys.executable, os.path.join(HERE, "train_ablation.py"),
           *args, *DEFAULT_ARGS, "--export-dir", out_dir]
    print("\n" + "=" * 72)
    print(f"  EXPERIMENT: {name}")
    print(f"  OUT       : {out_dir}")
    print(f"  CMD       : {' '.join(cmd)}")
    print("=" * 72)
    if dry_run:
        return 0
    os.makedirs(out_dir, exist_ok=True)
    # Stream output live; return code propagates so a failure stops the chain.
    rc = subprocess.call(cmd)
    return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=str, default=None,
                    help="Run only the experiment whose name contains this substring.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--full-l", action="store_true",
                    help="Also sweep L=24,36,48,60 (full Table VIII).")
    args = ap.parse_args()

    exps = build_experiments(args.full_l)
    if args.only:
        exps = [(n, a) for n, a in exps if args.only in n]
        if not exps:
            print(f"[ERROR] --only {args.only!r} matched no experiment.")
            return 2

    print(f"[plan] {len(exps)} experiment(s) to run sequentially under "
          f"{OUT_ROOT}")
    failures = []
    for name, a in exps:
        rc = run_one(name, a, args.dry_run)
        if rc != 0:
            failures.append((name, rc))
            print(f"[FAIL] {name} exited with code {rc} — STOPPING chain.")
            break
    if failures:
        print(f"\n[SUMMARY] {len(failures)} experiment(s) failed: {failures}")
        return 1
    print("\n[SUMMARY] all experiments completed (or dry-run finished).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
