#!/usr/bin/env python3
"""Aggregate Track B core cells from logs/results into one CSV (partial ok)."""
import csv, glob, json, os, re, sys

B = "/gpfs1/scratch/sychan552/trackB_20261104/core"
rows = []
for cell in sorted(glob.glob(os.path.join(B, "export", "*", "L*_s*"))):
    model = os.path.basename(os.path.dirname(cell))
    L, seed = re.match(r"L(\d+)_s(\d+)", os.path.basename(cell)).groups()
    res = sorted(glob.glob(os.path.join(cell, "results_*.csv")))
    logs = sorted(glob.glob(os.path.join(cell, "training_*log_*.txt")))
    if not res:
        continue
    txt = ""
    for lg in logs:
        txt += open(lg, errors="ignore").read()
    def grab(pat, default=""):
        m = re.findall(pat, txt)
        return m[-1] if m else default
    mse_all = grab(r"MSE_AllVars=([0-9.]+)") or grab(r"test_mse=([0-9.]+)\(All\)")
    mae_all = grab(r"test_mae=([0-9.]+)")
    mse_ili = grab(r"MSE_ILITotal=([0-9.]+)") or grab(r"test_mse=[0-9.]+\(All\) ([0-9.]+)\(ILI\)")
    mse_wili = grab(r"test_mse=[0-9.]+\(All\) [0-9.]+\(ILI\) ([0-9.]+)\(WILI\)")
    pcc = grab(r"pcc=([0-9.]+)")
    wall = grab(r"wall_seconds[\"=: ]+([0-9.]+)")
    gpu = grab(r"gpu_name[\"=: ]+([^\"\\n,]+)")
    # fallback from results CSV
    if not mse_ili:
        with open(res[-1]) as fh:
            rr = list(csv.DictReader(fh))
        if rr:
            mse_ili = rr[0].get("mse_ili", "")
            mse_wili = rr[0].get("mse_wili", "")
            mae_all = mae_all or rr[0].get("mae_ili", "")
    rows.append(dict(model=model, L=L, seed=seed,
                     mse_all=mse_all, mae_all=mae_all,
                     mse_ili=mse_ili, mse_wili=mse_wili, pcc=pcc,
                     wall_s=wall, gpu=gpu,
                     results=os.path.relpath(res[-1], B),
                     pred=(os.path.relpath(sorted(glob.glob(os.path.join(cell,"predictions_*.csv")))[-1], B)
                           if glob.glob(os.path.join(cell,"predictions_*.csv")) else "")))

out = os.path.join(B, "TRACKB_CORE_PARTIAL.csv")
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else
                       ["model","L","seed","mse_all","mae_all","mse_ili","mse_wili","pcc","wall_s","gpu","results","pred"])
    w.writeheader(); w.writerows(rows)
print("cells", len(rows), "->", out)
if rows:
    print("models", sorted({r["model"] for r in rows}))
