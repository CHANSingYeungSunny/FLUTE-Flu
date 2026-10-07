#!/usr/bin/env python3
"""
independent_scorer_r1b.py — gate C12.

Recomputes the R1-B Test metrics from the persisted prediction NPZs using
arithmetic written independently of the training code's metric path, and
compares against the values the trainer reported in its manifests.

Also checks the structural claims the contract depends on:
  * prediction / target shapes are (n_origins, L, 7)
  * target_start_row values are unique and ascending
  * the target block for each origin lies inside the Test split [773, 966)
"""
from __future__ import annotations

import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PREDS = os.path.join(HERE, "preds")

PAPER = {24: (1.542, 0.726), 36: (1.422, 0.779),
         48: (1.414, 0.757), 60: (1.364, 0.719)}
EXPECT_ORIGINS = {24: 170, 36: 158, 48: 146, 60: 134}
TEST_LO, TEST_HI = 773, 966
TOL_MSE, TOL_MAE, TOL_MEAN = 0.10, 0.05, 0.08

REPORTED = {24: (2.1334972381591797, 0.929780900478363),
            36: (2.022707939147949, 0.9976677894592285),
            48: (1.8413366079330444, 0.8957162499427795),
            60: (1.7933106422424316, 0.9115838408470154)}


def main():
    rows, out = [], {}
    print(f"{'L':>3} {'n':>4} {'MSE(indep)':>12} {'MSE(reported)':>14} "
          f"{'d':>10} {'MAE(indep)':>12} {'MAE(reported)':>14} {'d':>10}")
    all_ok = True
    for L in (24, 36, 48, 60):
        p = os.path.join(PREDS, f"pred_r1b__L{L}__rep0.npz")
        z = np.load(p, allow_pickle=False)
        pred, targ, orig = z["pred"], z["target"], z["target_start_row"]
        struct_ok = (pred.shape == targ.shape
                     and pred.ndim == 3 and pred.shape[2] == 7
                     and pred.shape[1] == L)
        unique_asc = bool(np.all(np.diff(orig) > 0))
        # target block [o+1, o+L] must sit inside the Test split
        contained = bool(np.all(orig + 1 >= TEST_LO) and np.all(orig + L <= TEST_HI - 1))
        err = pred.astype(np.float64) - targ.astype(np.float64)
        mse = float((err ** 2).mean())
        mae = float(np.abs(err).mean())
        r_mse, r_mae = REPORTED[L]
        d_mse, d_mae = mse - r_mse, mae - r_mae
        pm, pa = PAPER[L]
        out[L] = {
            "n_origins": int(pred.shape[0]),
            "mse_independent": mse, "mae_independent": mae,
            "mse_reported": r_mse, "mae_reported": r_mae,
            "mse_reproduced_minus_reported": d_mse,
            "mae_reproduced_minus_reported": d_mae,
            "paper_mse": pm, "paper_mae": pa,
            "mse_minus_paper": mse - pm, "mae_minus_paper": mae - pa,
            "rel_mse_vs_paper_pct": 100 * (mse - pm) / pm,
            "inside_mse_tolerance": abs(mse - pm) <= TOL_MSE,
            "inside_mae_tolerance": abs(mae - pa) <= TOL_MAE,
            "shape ok": struct_ok, "origins unique+ascending": unique_asc,
            "targets contained in test split": contained,
            "origin_count matches contract": int(pred.shape[0]) == EXPECT_ORIGINS[L],
        }
        print(f"{L:>3} {pred.shape[0]:>4} {mse:>12.6f} {r_mse:>14.6f} {d_mse:>10.2e} "
              f"{mae:>12.6f} {r_mae:>14.6f} {d_mae:>10.2e}")
        all_ok &= struct_ok and unique_asc and contained

    mse_mean = float(np.mean([out[L]["mse_independent"] for L in out]))
    mae_mean = float(np.mean([out[L]["mae_independent"] for L in out]))
    paper_mean_mse = float(np.mean([PAPER[L][0] for L in PAPER]))
    paper_mean_mae = float(np.mean([PAPER[L][1] for L in PAPER]))

    print()
    print(f"four-horizon mean MSE : independent {mse_mean:.6f}  "
          f"paper {paper_mean_mse:.6f}  diff {mse_mean - paper_mean_mse:+.6f}  "
          f"(tol +/-{TOL_MEAN})")
    print(f"four-horizon mean MAE : independent {mae_mean:.6f}  "
          f"paper {paper_mean_mae:.6f}  diff {mae_mean - paper_mean_mae:+.6f}")
    print()
    print("structural checks all pass:", all_ok)
    print("horizons inside MSE tolerance:",
          sum(1 for L in out if out[L]["inside_mse_tolerance"]), "/ 4")

    summary = {
        "per_horizon": {str(k): v for k, v in out.items()},
        "four_horizon_mean": {
            "mse_independent": mse_mean, "mae_independent": mae_mean,
            "paper_mse": paper_mean_mse, "paper_mae": paper_mean_mae,
            "mse_diff": mse_mean - paper_mean_mse,
            "mae_diff": mae_mean - paper_mean_mae,
            "inside_mean_tolerance": abs(mse_mean - paper_mean_mse) <= TOL_MEAN,
        },
        "tolerances": {"mse_per_horizon": TOL_MSE, "mae_per_horizon": TOL_MAE,
                       "mse_four_horizon_mean": TOL_MEAN},
        "horizons_inside_mse_tolerance": sum(
            1 for L in out if out[L]["inside_mse_tolerance"]),
        "max_abs_scorer_disagreement": max(
            max(abs(out[L]["mse_reproduced_minus_reported"]),
                abs(out[L]["mae_reproduced_minus_reported"])) for L in out),
    }
    with open(os.path.join(HERE, "R1B_INDEPENDENT_SCORING.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print("\nwrote R1B_INDEPENDENT_SCORING.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())