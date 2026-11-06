#!/usr/bin/env python3
"""Re-aggregate the legacy 5-fold walk-forward panel from RAW prediction NPZ.

Created 2026-11-06 for HANDOFF_20261105/v8 TASK 1. The original producer script
was not present in the repository; this one reproduces its output exactly on the
802 previously-valid cells (verified against final/WF_RECOMPUTED.csv).

Metric: MSE = mean over (origins x 7 standardized channels x L leads) of
(pred - target)^2, read directly from the NPZ. No metrics.csv is trusted.

Grid: 5 folds (f1..f5) x 17 models x 4 lengths (24/36/48/60) x 3 legacy seeds
(42/43/44) = 1020 cells. This is the LEGACY N=3 walk-forward protocol, NOT the
new 28-arm national 10-seed (2021-2030) protocol.

Artifact resolution (both layouts exist on disk):
  1. <root>/<fold>/<model>_L<L>_s<seed>/pred_<model>_L<L>_s<seed>.npz
  2. <root>/<fold>/L<L>_s<seed>/pred_miflu_L<L>_seed<seed>.npz   (miflu only)
  3. any pred_*.npz inside the directories above (rerun outputs)

MUST be run via sbatch on a compute node (numpy load of ~1000 NPZ), never on the
Burgundy login node.
"""
import argparse
import csv
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

FOLDS = ["f1", "f2", "f3", "f4", "f5"]
MODELS = ["calf_llm", "cnn", "decision_tree", "dnn", "gradient_boosting", "gru",
          "itransformer", "knn", "lstm", "miflu", "nlinear", "patchtst",
          "qwen_time_llm", "random_forest", "rnn", "svr", "timecma_llm"]
LS = [24, 36, 48, 60]
SEEDS = [42, 43, 44]
EXPECTED_SPACE = "standardized_train_fit_z"


def candidates(root, fold, model, L, seed):
    d_model = os.path.join(root, fold, f"{model}_L{L}_s{seed}")
    d_bare = os.path.join(root, fold, f"L{L}_s{seed}")
    exact = os.path.join(d_model, f"pred_{model}_L{L}_s{seed}.npz")
    miflu = os.path.join(d_bare, f"pred_miflu_L{L}_seed{seed}.npz")
    out = [exact]
    if model == "miflu":
        out.append(miflu)
    for d in (d_model, d_bare):
        out.extend(sorted(glob.glob(os.path.join(d, "pred_*.npz"))))
    seen, uniq = set(), []
    for p in out:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def score(path, fold, model, L, seed):
    """Return (mse, status, detail)."""
    if not os.path.exists(path):
        return "", "no_npz", "file-absent"
    try:
        z = np.load(path, allow_pickle=False)
        missing = {"pred", "target"} - set(z.files)
        if missing:
            return "", "invalid", "missing-keys:" + ",".join(sorted(missing))
        if "space" in z.files and str(z["space"]) != EXPECTED_SPACE:
            return "", "invalid", "space=" + str(z["space"])
        if "fold" in z.files and int(z["fold"]) != int(fold[1:]):
            return "", "invalid", "fold-mismatch=" + str(z["fold"])
        pred = np.asarray(z["pred"], dtype=np.float64)
        tgt = np.asarray(z["target"], dtype=np.float64)
        if pred.shape != tgt.shape:
            return "", "invalid", f"shape {pred.shape} != {tgt.shape}"
        if pred.ndim != 3 or pred.shape[1] != 7 or pred.shape[2] != L:
            return "", "invalid", f"bad-shape {pred.shape} for L={L}"
        if not (np.isfinite(pred).all() and np.isfinite(tgt).all()):
            return "", "invalid", "nonfinite"
        mse = float(np.mean((pred - tgt) ** 2))
        if not np.isfinite(mse):
            return "", "invalid", "nonfinite-mse"
        return f"{mse:.9f}", "ok", os.path.relpath(path, os.path.dirname(os.path.dirname(path)))
    except Exception as e:
        return "", "invalid", "exception:" + type(e).__name__ + ":" + str(e)[:120]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wf-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--baseline", default="", help="optional frozen WF_RECOMPUTED.csv to diff")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    rows, details = [], []
    for fold in FOLDS:
        for model in MODELS:
            for L in LS:
                for seed in SEEDS:
                    paths = candidates(a.wf_root, fold, model, L, seed)
                    mse, status, detail = "", "no_npz", "no-candidate"
                    for p in paths:
                        mse, status, detail = score(p, fold, model, L, seed)
                        if status == "ok":
                            detail = os.path.relpath(p, a.wf_root)
                            break
                    rows.append({"fold": fold, "model": model, "L": L, "seed": seed,
                                 "mse": mse, "status": status})
                    details.append({"fold": fold, "model": model, "L": L, "seed": seed,
                                    "status": status, "npz": detail})
    # cells CSV
    with open(os.path.join(a.out_dir, "WF_RECOMPUTED.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["fold", "model", "L", "seed", "mse", "status"])
        w.writeheader()
        w.writerows(rows)
    # means CSV: fold x model, n valid, mean mse
    groups = defaultdict(list)
    for r in rows:
        if r["status"] == "ok":
            groups[(r["fold"], r["model"])].append(float(r["mse"]))
    with open(os.path.join(a.out_dir, "WF_RECOMPUTED_MEANS.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["fold", "model", "n", "mse"])
        for fold in FOLDS:
            for model in MODELS:
                v = groups[(fold, model)]
                if v:
                    w.writerow([fold, model, len(v), f"{np.mean(v):.9f}"])
    # provenance detail
    with open(os.path.join(a.out_dir, "WF_RECOMPUTED_DETAIL.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["fold", "model", "L", "seed", "status", "npz"])
        w.writeheader()
        w.writerows(details)
    # diff against frozen baseline if supplied
    report = {
        "grid_cells": len(rows),
        "status_counts": {},
        "baseline_diff": None,
    }
    report["status_counts"] = {s: sum(1 for r in rows if r["status"] == s)
                               for s in sorted({r["status"] for r in rows})}
    if a.baseline and os.path.exists(a.baseline):
        old = {(r["fold"], r["model"], r["L"], r["seed"]): r
               for r in csv.DictReader(open(a.baseline, encoding="utf-8"))}
        new = {(r["fold"], r["model"], r["L"], r["seed"]): r for r in rows}
        recovered, changed, still_missing, lost = [], [], [], []
        for k, o in old.items():
            n = new.get(k)
            if not n:
                continue
            if o["status"] == "no_npz" and n["status"] == "ok":
                recovered.append(k)
            elif o["status"] == "ok" and n["status"] != "ok":
                lost.append((k, o["status"], n["status"]))
            elif o["status"] == "ok" and n["status"] == "ok":
                if abs(float(o["mse"]) - float(n["mse"])) > 1e-6:
                    changed.append((k, o["mse"], n["mse"]))
            elif n["status"] != "ok":
                still_missing.append((k, n["status"]))
        report["baseline_diff"] = {
            "recovered_218_count": len(recovered),
            "changed_existing_ok_values": len(changed),
            "changed_examples": changed[:10],
            "lost_existing_ok": len(lost),
            "lost_examples": lost[:10],
            "still_missing": len(still_missing),
            "still_missing_examples": still_missing[:10],
        }
    with open(os.path.join(a.out_dir, "WF_RECOMPUTE_REPORT.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
