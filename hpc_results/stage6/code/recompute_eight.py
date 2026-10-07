#!/usr/bin/env python3
"""Stage 6 — INDEPENDENT recomputation of the eight-model primary metric.

Same discipline as the A2 verifier: this script imports NO training or scoring
model code. It reads only the per-(model, L, seed) prediction NPZs, the
Test-origin manifest and the train-only scaler, and rebuilds

    mse_all(model, L, seed) = mean over (origins x leads x 7 variables) of
                               (pred - target)^2  in standardized space
    average_MSE_4L(model)    = mean over seeds, then equal-weight mean over L

It then compares cell by cell against the scoring entry's own tables. Missing
artefacts, a Test target block outside [773, 966), a wrong origin count, or any
disagreement is a hard failure.

The eight-model plan is 8 models x 4 L x 3 seeds = 96 learned fits. The A2 `notext`
control (12 fits) is scored by the same entry point and is excluded from the
eight-model table. Together with the two deterministic baselines (8 records) the
artefact directory must hold exactly 116 records.
"""
import argparse, glob, json, os, sys
import numpy as np
import pandas as pd

TOL = 1e-9
EIGHT = ["nlinear", "dlinear", "patchtst", "itransformer",
         "miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
CONTROL = ["notext"]                      # mechanism ablation, reported separately
BASELINES = ["last_value_naive", "seasonal_naive"]
EXPECTED_TEST = {24: 170, 36: 158, 48: 146, 60: 134}
SEEDS = (42, 43, 44)
# The comparison itself is 8 models x 4 L x 3 seeds = 96 learned fits. The A2
# `notext` control is scored by the same entry point and therefore also lands in
# the artefact directory, so the total is 96 + 12 control + 8 naive = 116.
EXPECTED_LEARNED = 8 * 4 * 3                    # 96, the eight-model table
EXPECTED_CONTROL = len(CONTROL) * 4 * 3         # 12, reported apart
EXPECTED_RECORDS = EXPECTED_LEARNED + EXPECTED_CONTROL + 8   # 116


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scoring", default="results/stage6/scoring")
    ap.add_argument("--tol", type=float, default=TOL)
    a = ap.parse_args()
    d = os.path.join(a.scoring, "predictions")
    files = sorted(glob.glob(os.path.join(d, "pred_*.npz")))
    print(f"[recompute8] {len(files)} prediction artefacts in {d}")
    if len(files) != EXPECTED_RECORDS:
        print(f"[recompute8] FAIL: expected {EXPECTED_RECORDS} "
              f"(96 eight-model + 12 notext control + 8 baselines), found {len(files)}",
              file=sys.stderr)
        sys.exit(3)

    scaler = json.load(open(os.path.join(d, "scaler_train_only.json")))
    man = pd.read_csv(os.path.join(d, "test_manifest.csv"))
    print(f"[recompute8] scaler fitted on {scaler['fit_on']}; "
          f"vars={len(scaler['var_cols'])}; manifest rows={len(man)}")

    recs = []
    for f in files:
        z = np.load(f, allow_pickle=False)
        model = str(z["model"]); L = int(z["L"]); seed = int(z["seed"])
        pred, tgt = z["pred"], z["target"]
        tsr = z["target_start_row"]
        if str(z["space"]) != "standardized_train_fit_z":
            print(f"[recompute8] FAIL: {f} space={z['space']}", file=sys.stderr); sys.exit(3)
        if list(z["var_cols"]) != list(scaler["var_cols"]):
            print(f"[recompute8] FAIL: {f} variable order mismatch", file=sys.stderr); sys.exit(3)
        if tsr.min() < 773 or (tsr + L).max() > 966:
            print(f"[recompute8] FAIL: {f} Test targets outside [773,966)",
                  file=sys.stderr); sys.exit(3)
        if len(tsr) != EXPECTED_TEST[L] or pred.shape != tgt.shape or pred.shape[0] != len(tsr):
            print(f"[recompute8] FAIL: {f} shape/origin mismatch", file=sys.stderr); sys.exit(3)
        recs.append({"model": model, "L": L, "seed": seed,
                     "mse_all": float(np.mean((pred - tgt) ** 2)),
                     "mae_all": float(np.mean(np.abs(pred - tgt))),
                     "n_origins": len(tsr), "artefact": os.path.basename(f)})
    rec = pd.DataFrame(recs).sort_values(["model", "L", "seed"]).reset_index(drop=True)
    rec.to_csv(os.path.join(a.scoring, "recomputed_score_matrix.csv"), index=False)

    sm = pd.read_csv(os.path.join(a.scoring, "score_matrix.csv"))
    mg = sm.merge(rec, on=["model", "L", "seed"], how="outer",
                  suffixes=("_entry", "_re"), indicator=True)
    if (mg["_merge"] != "both").any():
        print("[recompute8] FAIL: score_matrix rows not matched by artefacts:\n"
              + mg[mg["_merge"] != "both"][["model", "L", "seed", "_merge"]].to_string(index=False),
              file=sys.stderr); sys.exit(3)
    md = float(np.max(np.abs(mg["mse_all_entry"] - mg["mse_all_re"])))
    da = float(np.max(np.abs(mg["mae_all_entry"] - mg["mae_all_re"])))
    print(f"[recompute8] max |mse_all diff| = {md:.3e}  max |mae_all diff| = {da:.3e}")
    if md > a.tol or da > a.tol:
        print("[recompute8] FAIL: recomputed metrics disagree with score_matrix.csv",
              file=sys.stderr); sys.exit(3)

    for m in EIGHT + CONTROL:
        for L in EXPECTED_TEST:
            for s in SEEDS:
                n = len(rec[(rec.model == m) & (rec.L == L) & (rec.seed == s)])
                if n != 1:
                    print(f"[recompute8] FAIL: {m} L={L} seed={s} present {n} times "
                          f"(expected 1)", file=sys.stderr); sys.exit(3)
    for b in BASELINES:
        for L in EXPECTED_TEST:
            if len(rec[(rec.model == b) & (rec.L == L)]) != 1:
                print(f"[recompute8] FAIL: baseline {b} L={L} not present exactly once",
                      file=sys.stderr); sys.exit(3)
    print(f"[recompute8] coverage OK: {EXPECTED_LEARNED} eight-model fits + "
          f"{EXPECTED_CONTROL} notext control + 8 baselines")

    per = (rec.groupby(["model", "L"])["mse_all"]
             .agg(["mean", "std", "count"]).reset_index())
    per.to_csv(os.path.join(a.scoring, "recomputed_score_summary.csv"), index=False)
    rows = []
    for grp, label in ((EIGHT, "eight-model"), (CONTROL, "mechanism-control"),
                       (BASELINES, "baseline")):
        sub = per[per.model.isin(grp)]
        g = (sub.groupby("model")["mean"].mean()
                .rename("average_MSE_4L").reset_index().sort_values("average_MSE_4L"))
        g["group"] = label
        rows.append(g)
    avg = pd.concat(rows, ignore_index=True)
    avg.to_csv(os.path.join(a.scoring, "recomputed_average_mse_4L.csv"), index=False)
    print("\n=== average_MSE_4L recomputed from artefacts (7-var z-space MSE) ===")
    for label in ("eight-model", "mechanism-control", "baseline"):
        print(f"-- {label}")
        for _, r in avg[avg.group == label].iterrows():
            print(f"   {r['model']:18s} {r['average_MSE_4L']:.6f}")

    # LLM vs non-LLM is a 4-vs-4 split of a FIXED list, not a random sample of
    # "all LLMs". Report it descriptively and say so.
    nl = avg[(avg.group == "eight-model") & avg.model.isin(
        ["nlinear", "dlinear", "patchtst", "itransformer"])]["average_MSE_4L"]
    ll = avg[(avg.group == "eight-model") & avg.model.isin(
        ["miflu", "qwen_time_llm", "calf_llm", "timecma_llm"])]["average_MSE_4L"]
    print(f"\n[recompute8] non-LLM mean average_MSE_4L = {nl.mean():.6f} (n={len(nl)})")
    print(f"[recompute8] LLM     mean average_MSE_4L = {ll.mean():.6f} (n={len(ll)})")
    print("[recompute8] NOTE: these are 4 fixed implementations chosen in advance,")
    print("             NOT a random sample of 'all LLMs'. This is a descriptive")
    print("             comparison of two named sets and carries no inferential")
    print("             claim about LLM forecasters in general.")
    print("\n[recompute8] PASS — eight-model primary metric independently reproduced")


if __name__ == "__main__":
    main()
