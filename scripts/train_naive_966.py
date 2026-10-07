"""
train_naive_966.py — deterministic forecast floors for the A2 author-966 task.
==============================================================================

Two deterministic references, computed in the SAME train-fitted z-space as the
learned A2 fits so `mse_all` (7-variable, full-horizon, z-space) is directly
comparable:

  * last_value_naive : repeat the last observed INPUT value over the whole
                       horizon, per variable (persistence floor).
  * seasonal_naive   : value 52 ROWS before each target week, per variable.
                       On the 966-row author data this is 52 calendar weeks
                       (dense, no gap), so lag-by-row == lag-by-calendar. A
                       reference that would fall before row 0 is clamped to the
                       first row and recorded as `seasonal_reference_clamped`.

Both are deterministic: `stochastic_seed_applicable=false`. The seed is accepted
for matrix bookkeeping (mapped to seed cells) but does not affect the result.

No future observation is ever read — including leads 53..60 (the seasonal
reference `ts + s - 52` is always strictly before the target row `ts + s`).

Usage:
  python scripts/train_naive_966.py --name last_value_naive --horizon 24 --profile author_966
  python scripts/train_naive_966.py --name seasonal_naive --horizon 24 --profile author_966
  python scripts/train_naive_966.py --self-check
  python scripts/train_naive_966.py --preflight
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from configs import (CONFIG, VAR_COLS, resolve_profile, split_for_profile,
                     verify_profile_hash)
from scaler_utils import ScalerBundle

ILI_CHANNEL = 4
SEASONAL_LAG = 52


def load_and_normalize(profile):
    p = resolve_profile(profile)
    verify_profile_hash(profile)
    df = pd.read_csv(p["data_path"])
    data = df[VAR_COLS].values.astype(np.float32)
    n = len(data)
    t_end, v_end = split_for_profile(profile, n)
    bundle = ScalerBundle.fit_from_train(df, VAR_COLS, train_end=t_end,
                                         val_end=v_end)
    mean = bundle.mean_.reshape(1, -1).astype(np.float32)
    std = bundle.scale_.reshape(1, -1).astype(np.float32)
    data_norm = (data - mean) / std
    return {"data_norm": data_norm, "train_end": t_end, "val_end": v_end,
            "n": n, "scaler": bundle, "profile": p}


def window_index(data_norm, T, L, train_end, val_end, containment="start"):
    """Return (target_starts, splits) for all stride-1 windows (no X/Y copies).

    `containment="strict"` applies the Stage 5 rule: the WHOLE target block must
    lie inside its split, so baselines share the learned models' origin set.
    """
    total = data_norm.shape[0]
    nw = total - T - L + 1
    splits = np.zeros(nw, dtype=np.int8)
    target_starts = np.arange(nw) + T
    for i in range(nw):
        ts = i + T
        if containment == "strict":
            if ts + L <= train_end:
                splits[i] = 0
            elif ts >= train_end and ts + L <= val_end:
                splits[i] = 1
            elif ts >= val_end and ts + L <= total:
                splits[i] = 2
            else:
                splits[i] = -1
        else:
            splits[i] = 0 if ts < train_end else (1 if ts <= val_end else 2)
    return target_starts, splits


def naive_predictions(data_norm, target_starts, mask, L, name):
    """Deterministic naive forecasts for the selected windows (test = mask==2).

    Returns (pred, target, clamped_count). `pred`/`target` have shape (n_win, N, L).
    """
    N = data_norm.shape[1]
    idx = np.where(mask)[0]
    ts_all = target_starts[idx]
    pred = np.zeros((len(idx), N, L), dtype=np.float32)
    target = np.zeros((len(idx), N, L), dtype=np.float32)
    clamped = 0
    for j, ts in enumerate(ts_all):
        target[j] = data_norm[ts:ts + L].T
        if name == "last_value_naive":
            last = data_norm[ts - 1]            # last observed INPUT value
            pred[j] = np.repeat(last[:, None], L, axis=1)
        elif name == "seasonal_naive":
            for s in range(L):
                ref = ts + s - SEASONAL_LAG      # 52 rows before target week
                assert ref < ts + s, "seasonal naive must never read the future"
                if ref < 0:
                    ref = 0
                    clamped += 1
                pred[j, :, s] = data_norm[ref]
        else:
            raise ValueError(f"unknown naive name {name!r}")
    return pred, target, clamped


def evaluate(pred, target):
    mse_all = float(np.mean((pred - target) ** 2))
    mae_all = float(np.mean(np.abs(pred - target)))
    mse_ili = float(np.mean((pred[:, ILI_CHANNEL, :] - target[:, ILI_CHANNEL, :]) ** 2))
    mae_ili = float(np.mean(np.abs(pred[:, ILI_CHANNEL, :] - target[:, ILI_CHANNEL, :])))
    return mse_all, mae_all, mse_ili, mae_ili


def self_check():
    rng = np.random.RandomState(0)
    data = rng.randn(300, 7).astype(np.float32)
    ts = np.array([104, 105, 106])
    for name in ("last_value_naive", "seasonal_naive"):
        pred, target, clamped = naive_predictions(data, ts, np.ones(3, bool), 24, name)
        assert pred.shape == (3, 7, 24) and target.shape == (3, 7, 24)
        if name == "last_value_naive":
            # every step equals the last input value
            assert np.allclose(pred[:, :, 0], data[[103, 104, 105]])
            assert np.allclose(pred[:, :, -1], data[[103, 104, 105]])
        else:
            # step s equals data[ts+s-52]
            assert np.allclose(pred[0, :, 0], data[52])
            assert np.allclose(pred[0, :, 23], data[75])
        assert clamped == 0
    print("[naive] self-check OK: last_value & seasonal_naive shapes + formulas")
    return True


def preflight(profile, horizon, name, containment="start"):
    # Runs on the VALIDATION split only — never the Test split — so this is a
    # development check, not a new Test score.
    dd = load_and_normalize(profile)
    T, N, L = CONFIG["T"], CONFIG["N"], horizon
    ts_all, splits = window_index(dd["data_norm"], T, L, dd["train_end"],
                                  dd["val_end"], containment=containment)
    val_mask = splits == 1
    pred, target, clamped = naive_predictions(dd["data_norm"], ts_all,
                                              val_mask, L, name)
    assert pred.shape == target.shape == (int(val_mask.sum()), N, L)
    # Future-leak guard (any split): seasonal reference index < target index
    # for EVERY lead s in 0..L-1, including leads 53..60 (L=60).
    if name == "seasonal_naive":
        idx = np.where(val_mask)[0]
        for j, ts in enumerate(ts_all[idx]):
            for s in range(L):
                assert ts + s - SEASONAL_LAG < ts + s
    mse_all, _, mse_ili, _ = evaluate(pred, target)
    print("[naive] preflight OK (VALIDATION split only, no Test scoring)")
    print(f"  profile={profile} name={name} L={L} "
          f"val_windows={int(val_mask.sum())}")
    print(f"  scaler train-only fit OK (train_end={dd['scaler'].train_end})")
    print(f"  future-leak guard OK (seasonal ref < target for every lead 0..{L-1})")
    print(f"  clamped references={clamped} (expect 0 on dense author data)")
    print(f"  val mse_all={mse_all:.6f} mse_ili={mse_ili:.6f} "
          f"(development only, not a frozen result)")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", type=str, default=None,
                    choices=("last_value_naive", "seasonal_naive"))
    ap.add_argument("--horizon", type=int, default=None)
    ap.add_argument("--seed", type=int, default=42,
                    help="bookkeeping only (deterministic; "
                         "stochastic_seed_applicable=false)")
    ap.add_argument("--profile", type=str, default="author_966",
                    choices=("project_1025", "author_966"))
    ap.add_argument("--export-dir", default=None)
    ap.add_argument("--containment", choices=["start", "strict"], default="start",
                    help="target-split rule: 'start' = legacy (target start), "
                         "'strict' = Stage 5 (whole target inside its split)")
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--preflight", action="store_true")
    args = ap.parse_args()
    # ---- Stage 5 A2 guard: containment must be explicit and strict ----
    import os as _os
    _req = _os.environ.get("A2_REQUIRE_STRICT") == "1"
    if _req and getattr(args, "containment", "start") != "strict":
        raise SystemExit("[A2] A2_REQUIRE_STRICT=1 requires --containment strict, got %r"
                         % getattr(args, "containment", None))
    print("[A2] run_config containment=%s profile=%s horizon=%s seed=%s"
          % (getattr(args, "containment", "start"), getattr(args, "profile", None),
             getattr(args, "horizon", None), getattr(args, "seed", None)))


    if args.self_check:
        self_check()
        return
    if args.preflight:
        if args.name is None:
            raise SystemExit("--name is required with --preflight")
        preflight(args.profile, args.horizon or 24, args.name, args.containment)
        return
    if args.name is None:
        raise SystemExit("--name is required (last_value_naive | seasonal_naive)")

    export_dir = args.export_dir or os.path.join(
        "results", "stage3_a2", "author_966", "naive")
    os.makedirs(export_dir, exist_ok=True)
    metrics_path = os.path.join(export_dir, "metrics.csv")

    dd = load_and_normalize(args.profile)
    T, N = CONFIG["T"], CONFIG["N"]
    L_list = [args.horizon] if args.horizon is not None else CONFIG["L_list"]

    rows = []
    if os.path.exists(metrics_path):
        try:
            rows = pd.read_csv(metrics_path).to_dict("records")
        except Exception:
            rows = []
    done = {(str(r["name"]), int(r["L"])) for r in rows}

    for L in L_list:
        if (args.name, L) in done:
            continue
        ts_all, splits = window_index(dd["data_norm"], T, L, dd["train_end"],
                                      dd["val_end"], containment=args.containment)
        # Report on the TEST split (the A2 estimand); val split is supplementary.
        pred_test, target_test, clamped = naive_predictions(
            dd["data_norm"], ts_all, splits == 2, L, args.name)
        mse_all, mae_all, mse_ili, mae_ili = evaluate(pred_test, target_test)
        rows = [x for x in rows if (str(x["name"]), int(x["L"])) != (args.name, L)]
        rows.append({
            "name": args.name, "L": L, "seed": args.seed,
            "stochastic_seed_applicable": False,
            "mse_all": mse_all, "mae_all": mae_all,
            "mse_ili": mse_ili, "mae_ili": mae_ili,
            "seasonal_reference_clamped": int(clamped),
            "n_test_windows": int(pred_test.shape[0]),
        })
        pd.DataFrame(rows).to_csv(metrics_path, index=False)
        print(f"[naive] {args.name} L={L} mse_all={mse_all:.6f} "
              f"mse_ili={mse_ili:.6f} clamped={clamped}")

    print(f"[naive] DONE -> {metrics_path}")


if __name__ == "__main__":
    main()
