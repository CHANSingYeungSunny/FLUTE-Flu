#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""train_classical_966.py — expanded benchmark, classical ML arms (non-LLM).

Why a separate runner
---------------------
Decision Tree / Random Forest / Gradient Boosting / SVR / KNN are not
gradient-trained torch modules, so they cannot go through the Adam/epochs
engine in `train_backbone_966.py`. This runner imports the **A2 protocol
functions verbatim** from `train_nlinear_966` —

    load_and_normalize()  -> identical scaler (train-only fit), identical split
    build_windows()       -> identical T=104 windows, identical strict containment

so protocol identity with MIFlu / DLinear / the other backbones is by
construction, not by re-implementation. Only the estimator differs.

Convention
----------
Channel-agnostic shared model: every (window, variable) pair is stacked into
one design matrix, so a single estimator maps T -> L for all 7 variables.
This mirrors `DLinear(individual=False)`, the project's chosen linear
convention. It is recorded in the metrics JSON as `channel_agnostic=True`.

Outputs
-------
  <export-dir>/metrics.json                      summary + provenance
  <export-dir>/pred_<model>_L<L>_s<seed>.npz     same schema as stage-6 npz,
                                                 so the analysis/plotting
                                                 scripts consume it unchanged.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from configs import CONFIG, VAR_COLS, set_seed, resolve_profile   # noqa: E402
from train_nlinear_966 import (build_windows,           # noqa: E402
                               load_and_normalize)
import walk_forward                                     # noqa: E402

ILI_CHANNEL = 4

MODELS = {
    "decision_tree":     "DecisionTreeRegressor(max_depth=None, random_state=seed)",
    "random_forest":     "RandomForestRegressor(n_estimators=200, random_state=seed, n_jobs=-1)",
    "gradient_boosting": "GradientBoostingRegressor(n_estimators=200, random_state=seed) via MultiOutputRegressor",
    "svr":               "SVR(C=1.0, epsilon=0.1) via MultiOutputRegressor",
    "knn":               "KNeighborsRegressor(n_neighbors=10, weights='distance')",
}


def make_estimator(name, seed):
    from sklearn.tree import DecisionTreeRegressor
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.svm import SVR
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.multioutput import MultiOutputRegressor

    if name == "decision_tree":
        return DecisionTreeRegressor(max_depth=None, random_state=seed), "native"
    if name == "random_forest":
        return RandomForestRegressor(n_estimators=200, random_state=seed,
                                     n_jobs=-1), "native"
    if name == "gradient_boosting":
        # Classic GradientBoostingRegressor was 428 s per cell even at 100 trees /
        # depth 3 (7 separate models in MultiOutputRegressor), which cannot fit a
        # 120-cell sweep. HistGradientBoostingRegressor is sklearn's histogram-based
        # gradient booster: same algorithm family, ~1-2 orders of magnitude faster
        # on 3.8k x 104 inputs. n_estimators -> max_iter in that API.
        from sklearn.ensemble import HistGradientBoostingRegressor
        return MultiOutputRegressor(
            HistGradientBoostingRegressor(max_iter=100, max_depth=3,
                                          random_state=seed)), "MultiOutput"
    if name == "svr":
        return MultiOutputRegressor(SVR(C=1.0, epsilon=0.1)), "MultiOutput"
    if name == "knn":
        return KNeighborsRegressor(n_neighbors=10, weights="distance"), "native"
    raise KeyError(f"unknown classical model {name!r}")


def _flat(X):
    """(n, N, T) -> (n*N, T): stack channels so one shared model sees them all."""
    n, N, T = X.shape
    return X.reshape(n * N, T)


def _flat_y(Y):
    n, N, L = Y.shape
    return Y.reshape(n * N, L)


def _mse(p, t):
    mse_all = float(np.mean((p - t) ** 2))
    mae_all = float(np.mean(np.abs(p - t)))
    mse_ili = float(np.mean((p[:, ILI_CHANNEL, :] - t[:, ILI_CHANNEL, :]) ** 2))
    mae_ili = float(np.mean(np.abs(p[:, ILI_CHANNEL, :] - t[:, ILI_CHANNEL, :])))
    return mse_all, mae_all, mse_ili, mae_ili


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=sorted(MODELS))
    ap.add_argument("--horizon", type=int, required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--profile", default="author_966")
    ap.add_argument("--containment", choices=["start", "strict"], default="strict")
    ap.add_argument("--export-dir", required=True)
    # Rolling origin (additive; 0 = the existing fixed split, unchanged).
    walk_forward.add_fold_argument(ap)
    a = ap.parse_args()

    set_seed(a.seed + a.horizon)
    L, T, N = a.horizon, CONFIG["T"], CONFIG["N"]
    fold = None
    fold_split = None
    if a.fold:
        _n = int(resolve_profile(a.profile)["n_rows"])
        _te, _ve, fold = walk_forward.fold_from_args(a, _n, a.profile,
                                                     horizon=a.horizon)
        fold_split = (fold.train_end, fold.val_end)
        print(f"[{a.model}] rolling-origin fold {fold.label}: "
              f"train_end={fold.train_end} val_end={fold.val_end} "
              f"test_end={fold.test_end}")
    dd = load_and_normalize(a.profile, split=fold_split)
    if fold is not None:
        dd = walk_forward.restrict_data(dd, fold)
    Xt, Yt, Xv, Yv, Xte, Yte, sinfo = build_windows(
        dd["data_norm"], T, L, dd["train_end"], dd["val_end"],
        containment=a.containment)
    print(f"[{a.model}] L={L} seed={a.seed} profile={a.profile} "
          f"train={len(Xt)} val={len(Xv)} test={len(Xte)} windows "
          f"(containment={a.containment}, fold={a.fold})")

    est, multi = make_estimator(a.model, a.seed)
    est.fit(_flat(Xt), _flat_y(Yt))            # TRAIN ONLY — no val leakage

    pv = est.predict(_flat(Xv)).reshape(len(Xv), N, L)
    pt = est.predict(_flat(Xte)).reshape(len(Xte), N, L)
    v_mse, v_mae, _, _ = _mse(pv, Yv)
    t_mse, t_mae, t_mse_ili, t_mae_ili = _mse(pt, Yte)
    print(f"[{a.model}] val_mse={v_mse:.6f}  test_mse={t_mse:.6f} "
          f"(ILITOTAL {t_mse_ili:.6f})  test_mae={t_mae:.6f}")

    os.makedirs(a.export_dir, exist_ok=True)
    scaler = dd["scaler"]
    mean = np.asarray(scaler.mean_).reshape(1, -1)
    scale = np.asarray(scaler.scale_).reshape(1, -1)
    tsr = np.asarray(sinfo["target_starts"])[np.asarray(sinfo["splits"]) == 2]
    npz = os.path.join(a.export_dir, f"pred_{a.model}_L{L}_s{a.seed}.npz")
    np.savez_compressed(
        npz, pred=pt.astype(np.float32), target=Yte.astype(np.float32),
        target_start_row=tsr.astype(np.int32), L=np.int32(L),
        seed=np.int32(a.seed), var_cols=np.array(VAR_COLS),
        train_mean=mean.astype(np.float32), train_std=scale.astype(np.float32),
        model=np.array(a.model), profile=np.array(a.profile),
        containment=np.array(a.containment),
        space=np.array("standardized_train_fit_z"),
        **({"fold": np.int32(fold.index), "fold_test_end": np.int32(fold.test_end)}
           if fold is not None else {}))

    metrics = {
        "model": a.model, "L": L, "seed": a.seed, "profile": a.profile,
        "containment": a.containment, "fold": a.fold,
        "split_source": dd.get("split_source", "profile"),
        "train_end": dd["train_end"], "val_end": dd["val_end"],
        "channel_agnostic": True, "trainable_parameters": None,
        "estimator": MODELS[a.model], "multioutput_wrapper": multi,
        "n_train_windows": int(len(Xt)), "n_val_windows": int(len(Xv)),
        "n_test_windows": int(len(Xte)),
        "val_mse_7var_z": v_mse, "val_mae_7var_z": v_mae,
        "test_mse_7var_z": t_mse, "test_mae_7var_z": t_mae,
        "test_mse_ilitotal_z": t_mse_ili, "test_mae_ilitotal_z": t_mae_ili,
        "selection": "none (sklearn estimator fitted on TRAIN only; val reported, not used to select)",
        "protocol_source": "train_nlinear_966.build_windows / load_and_normalize (imported verbatim)",
        "prediction_file": os.path.basename(npz),
    }
    with open(os.path.join(a.export_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"[{a.model}] wrote {npz}")


if __name__ == "__main__":
    main()
