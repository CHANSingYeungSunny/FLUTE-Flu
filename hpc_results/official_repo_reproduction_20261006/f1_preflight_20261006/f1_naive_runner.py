#!/usr/bin/env python3
"""
f1_naive_runner.py — CPU-only, deterministic naive references for F1, emitting
the SAME prediction artefact schema as the trained models so that ONE scorer
handles all six arms.

Difference from `scripts/train_naive_966.py` (which is NOT modified):

  1. It uses the LEAKAGE-SAFE seasonal definition from `naive_leakage_safe.py`.
     The original computes `ref = ts + s - 52`, which for L=60 references rows
     `ts+0 .. ts+7` - actual target rows inside the forecast window. Verified:
     that is leakage at 8 leads. The corrected form is `ref = ts-52+(s mod 52)`,
     which is <= origin for every lead.
  2. It SAVES predictions and targets as NPZ, so the independent scorer can
     recompute the metrics. The original writes only a metrics CSV.

Requires NO GPU. Writes NO output to scratch. Refuses to run on a login node.

Usage:
  python f1_naive_runner.py --name last_value_naive --horizon 60 \
      --export-dir <dir> --profile author_966 --containment strict
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(PROJ, "scripts"))
sys.path.insert(0, HERE)

import naive_leakage_safe as NLS          # noqa: E402


def refuse_on_login_node():
    h = socket.gethostname().lower()
    if h.startswith("hpclogin") or "login" in h:
        print(f"[f1naive] REFUSING to run on a login node ({h})")
        sys.exit(3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True,
                    choices=("last_value_naive", "seasonal_naive"))
    ap.add_argument("--horizon", type=int, required=True, choices=(24, 36, 48, 60))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--profile", default="author_966",
                    choices=("project_1025", "author_966"))
    ap.add_argument("--containment", default="strict",
                    choices=("start", "strict"))
    ap.add_argument("--export-dir", required=True)
    ap.add_argument("--insufficient-history-policy", default="invalid",
                    choices=("invalid", "clamp_first"))
    args = ap.parse_args()

    refuse_on_login_node()
    if args.containment != "strict":
        raise SystemExit("[f1naive] F1 requires --containment strict")

    # reuse the project's own window construction so the forecast keys are
    # IDENTICAL to the trained arms' keys
    import train_naive_966 as TN
    from configs import CONFIG, VAR_COLS

    dd = TN.load_and_normalize(args.profile)
    T, N = CONFIG["T"], CONFIG["N"]
    L = args.horizon

    ts_all, splits = TN.window_index(dd["data_norm"], T, L, dd["train_end"],
                                     dd["val_end"], containment=args.containment)
    test_mask = (splits == 2)

    pred, target, valid, n_invalid = NLS.build_naive(
        dd["data_norm"], ts_all, test_mask, L, args.name,
        policy=args.insufficient_history_policy)

    # invalid leads must NOT be silently scored: mark them with a mask array and
    # report the count. The scorer treats a missing mask as "all valid".
    os.makedirs(args.export_dir, exist_ok=True)
    ts_test = ts_all[test_mask]
    # the scaler is a ScalerBundle; expose mean/scale in the same shape the
    # trained arms record (1, N)
    tm = np.asarray(dd["scaler"].mean_, np.float32).reshape(1, N)
    tsd = np.asarray(dd["scaler"].scale_, np.float32).reshape(1, N)

    out = os.path.join(args.export_dir,
                       f"pred_{args.name}_L{L}_s{args.seed}.npz")
    np.savez_compressed(
        out,
        pred=pred.astype(np.float32), target=target.astype(np.float32),
        target_start_row=ts_test.astype(np.int32),
        L=np.int32(L), seed=np.int32(args.seed),
        var_cols=np.array(VAR_COLS), train_mean=tm, train_std=tsd,
        model=args.name, profile=args.profile, containment=args.containment,
        space="standardized_train_fit_z",
        valid_lead_mask=valid,
        checkpoint_selection="deterministic - no checkpoint",
        stochastic_seed_applicable=False,
        seasonal_lag_rows=NLS.SEASONAL_LAG_ROWS,
        insufficient_history_policy=args.insufficient_history_policy,
        n_invalid_leads=np.int32(n_invalid))

    # honest per-cell metrics, excluding invalid leads when a mask is present
    # valid is (n_win, L); broadcast over variables as (n_win, 1, L)
    m = valid[:, None, :].astype(np.float64)
    err = (pred - target)
    mse = float(np.sum((err ** 2) * m) / max(np.sum(m) * N, 1))
    mae = float(np.sum(np.abs(err) * m) / max(np.sum(m) * N, 1))

    prov = {
        "name": args.name, "horizon": L, "seed": args.seed,
        "profile": args.profile, "containment": args.containment,
        "n_test_windows": int(pred.shape[0]),
        "mse_all_masked": mse, "mae_all_masked": mae,
        "n_invalid_leads": int(n_invalid),
        "leakage_safe": True,
        "seasonal_lag_rows": NLS.SEASONAL_LAG_ROWS,
        "uses_gpu": False,
        "artifact": os.path.relpath(out),
    }
    with open(os.path.join(args.export_dir,
                           f"provenance_{args.name}_L{L}_s{args.seed}.json"), "w") as fh:
        json.dump(prov, fh, indent=2)

    print(f"[f1naive] {args.name} L={L} windows={pred.shape[0]} "
          f"mse={mse:.6f} mae={mae:.6f} invalid_leads={n_invalid}")
    print(f"[f1naive] wrote {out}")
    print("[f1naive] LEAKAGE_SAFE=True  GPU_REQUIRED=False")


if __name__ == "__main__":
    main()