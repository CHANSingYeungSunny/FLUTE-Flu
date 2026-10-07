#!/usr/bin/env python3
"""Stage 5 A2 — INDEPENDENT recomputation of the primary metric from artefacts.

This script deliberately does NOT import the training or scoring model code.
It reads only the per-(model, L, seed) prediction NPZ files, the Test-origin
manifest and the train-only scaler that the scoring step wrote, and rebuilds

    mse_all(model, L, seed) = mean over (origins x leads x 7 variables) of
                               (pred - target)^2   in standardized space
    average_MSE_4L(model)    = mean over seeds, then equal-weight mean over L

It then compares, cell by cell, against the numbers the scoring entry wrote to
score_matrix.csv / score_summary.csv / average_mse_4L.csv. Any mismatch, any
missing Test origin, or any origin that is not inside the frozen Test interval
is a hard failure (exit code 3).
"""
import argparse, glob, json, os, sys
import numpy as np
import pandas as pd

TOL = 1e-9
LEARNED = ("miflu", "notext", "nlinear")
BASELINES = ("last_value_naive", "seasonal_naive")
EXPECTED_TEST = {24: 170, 36: 158, 48: 146, 60: 134}
EXPECTED_NPZ = 44


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scoring", default="results/stage5/scoring")
    ap.add_argument("--tol", type=float, default=TOL)
    a = ap.parse_args()

    d = os.path.join(a.scoring, "predictions")
    files = sorted(glob.glob(os.path.join(d, "pred_*.npz")))
    print(f"[recompute] {len(files)} prediction artefacts found in {d}")
    if len(files) != EXPECTED_NPZ:
        print(f"[recompute] FAIL: expected {EXPECTED_NPZ} artefacts, found {len(files)}",
              file=sys.stderr)
        sys.exit(3)

    scaler = json.load(open(os.path.join(d, "scaler_train_only.json")))
    man = pd.read_csv(os.path.join(d, "test_manifest.csv"))
    print(f"[recompute] scaler fitted on {scaler['fit_on']}; "
          f"vars={len(scaler['var_cols'])}; manifest rows={len(man)}")

    recs = []
    for f in files:
        z = np.load(f, allow_pickle=False)
        model = str(z["model"]); L = int(z["L"]); seed = int(z["seed"])
        pred, tgt = z["pred"], z["target"]
        tsr = z["target_start_row"]
        if str(z["space"]) != "standardized_train_fit_z":
            print(f"[recompute] FAIL: {f} space={z['space']}", file=sys.stderr); sys.exit(3)
        if list(z["var_cols"]) != list(scaler["var_cols"]):
            print(f"[recompute] FAIL: {f} variable order mismatch", file=sys.stderr); sys.exit(3)
        # frozen Test containment: target block must lie wholly inside the Test split
        lo, hi = 773, 966
        if tsr.min() < lo or (tsr + L).max() > hi:
            print(f"[recompute] FAIL: {f} has Test targets outside [{lo},{hi})",
                  file=sys.stderr); sys.exit(3)
        if len(tsr) != EXPECTED_TEST[L] or pred.shape != tgt.shape or pred.shape[0] != len(tsr):
            print(f"[recompute] FAIL: {f} shape/origin-count mismatch "
                  f"{pred.shape} vs {len(tsr)} vs {EXPECTED_TEST[L]}", file=sys.stderr)
            sys.exit(3)
        mse_all = float(np.mean((pred - tgt) ** 2))
        mae_all = float(np.mean(np.abs(pred - tgt)))
        recs.append({"model": model, "L": L, "seed": seed,
                     "mse_all_recomputed": mse_all, "mae_all_recomputed": mae_all,
                     "n_origins": len(tsr), "artefact": os.path.basename(f)})
    rec = pd.DataFrame(recs).sort_values(["model", "L", "seed"]).reset_index(drop=True)
    rec.to_csv(os.path.join(a.scoring, "recomputed_score_matrix.csv"), index=False)

    # ---- compare with the scoring entry's own numbers -------------------
    sm = pd.read_csv(os.path.join(a.scoring, "score_matrix.csv"))
    mg = sm.merge(rec, on=["model", "L", "seed"], how="outer", indicator=True)
    if (mg["_merge"] != "both").any():
        bad = mg[mg["_merge"] != "both"][["model", "L", "seed", "_merge"]]
        print("[recompute] FAIL: score_matrix rows not matched by artefacts:\n"
              + bad.to_string(index=False), file=sys.stderr)
        sys.exit(3)
    md = float(np.max(np.abs(mg["mse_all"] - mg["mse_all_recomputed"])))
    da = float(np.max(np.abs(mg["mae_all"] - mg["mae_all_recomputed"])))
    print(f"[recompute] max |mse_all diff| = {md:.3e}   max |mae_all diff| = {da:.3e}")
    if md > a.tol or da > a.tol:
        print("[recompute] FAIL: recomputed metrics disagree with score_matrix.csv",
              file=sys.stderr)
        sys.exit(3)

    # ---- coverage of the planned matrix --------------------------------
    for m in LEARNED:
        for L in EXPECTED_TEST:
            for s in (42, 43, 44):
                sub = rec[(rec.model == m) & (rec.L == L) & (rec.seed == s)]
                if len(sub) != 1:
                    print(f"[recompute] FAIL: {m} L={L} seed={s} not present exactly once",
                          file=sys.stderr); sys.exit(3)
    for b in BASELINES:
        for L in EXPECTED_TEST:
            sub = rec[(rec.model == b) & (rec.L == L)]
            if len(sub) != 1:
                print(f"[recompute] FAIL: baseline {b} L={L} not present exactly once",
                      file=sys.stderr); sys.exit(3)
    print("[recompute] coverage OK: 36 learned fits + 8 deterministic baselines")

    # ---- average_MSE_4L ------------------------------------------------
    per = (rec[rec.model.isin(LEARNED + BASELINES)]
           .groupby(["model", "L"])["mse_all_recomputed"].agg(["mean", "std", "count"])
           .reset_index())
    per.to_csv(os.path.join(a.scoring, "recomputed_score_summary.csv"), index=False)
    avg = (per[per["model"].isin(LEARNED)]
           .groupby("model")["mean"].mean()
           .rename("average_MSE_4L").reset_index().sort_values("average_MSE_4L"))
    base = (per[per["model"].isin(BASELINES)]
            .groupby("model")["mean"].mean()
            .rename("average_MSE_4L").reset_index().sort_values("average_MSE_4L"))
    avg = pd.concat([avg, base], ignore_index=True)
    avg.to_csv(os.path.join(a.scoring, "recomputed_average_mse_4L.csv"), index=False)
    print("\n=== average_MSE_4L recomputed from artefacts (7-var z-space MSE) ===")
    for _, r in avg.iterrows():
        print(f"  {r['model']:18s} {r['average_MSE_4L']:.6f}")

    ref = os.path.join(a.scoring, "average_mse_4L.csv")
    if os.path.exists(ref):
        r2 = pd.read_csv(ref)
        j = avg.merge(r2, on="model", suffixes=("_recomputed", "_entry"))
        dm = float(np.max(np.abs(j["average_MSE_4L_recomputed"] - j["average_MSE_4L_entry"])))
        print(f"\n[recompute] max |average_MSE_4L diff| vs scoring entry = {dm:.3e}")
        if dm > 1e-8:
            print("[recompute] FAIL: average_MSE_4L mismatch", file=sys.stderr); sys.exit(3)
    print("\n[recompute] PASS — primary metric independently reproduced from artefacts")


if __name__ == "__main__":
    main()
