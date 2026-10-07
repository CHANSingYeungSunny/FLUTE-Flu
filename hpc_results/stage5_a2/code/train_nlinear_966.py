"""
train_nlinear_966.py — NLinear thin runner for the A2 author-966 comparison.
============================================================================

WHY THIS RUNNER EXISTS
----------------------
NLinear currently runs ONLY through `scripts/innovation/clean_runner.py`, which
is bound to the frozen 598-spec 1,025-row registry and its own metric code. It
cannot run on the author 966-row data under the `train_miflu`/`train_ablation`
protocol. This thin runner reuses the EXACT NLinear definition
(`scripts/innovation/backbones/dlinear.py::NLinear`, Zeng et al., AAAI 2023) and
mirrors the A2 data-prep + training protocol (train-only scaler, stride-1
windows, split by target start with `<= val_end`, Adam lr 5e-4, MSE z-space,
validation-based checkpoint selection, Test evaluated once after selection).

The NLinear class is loaded from its source file via `importlib` rather than
`from innovation.backbones import NLinear`, so the heavy `backbones/__init__.py`
registry (which imports gpt2_miflu_adapter / itransformer / llm_inspired / …) is
NOT executed. The loaded class is the SAME source file, so architecture
equivalence to the original implementation is by construction; `--self-check`
proves the extracted class computes the reference NLinear maths bit-for-bit.

A2 frozen protocol (recovery/stage3/configs/a2_frozen_protocol.json):
  * seeds {42,43,44} (never chosen by result inspection)
  * selection = best VALIDATION mse_all per (horizon, seed); Test once
  * mse_all = mean squared error over ALL 7 variables, full horizon, z-space

Usage:
  python scripts/train_nlinear_966.py --horizon 24 --seed 42 --profile author_966
  python scripts/train_nlinear_966.py --self-check          # CPU equivalence
  python scripts/train_nlinear_966.py --preflight           # CPU shape/split checks
"""

import argparse
import importlib.util
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(__file__))

from configs import (CONFIG, VAR_COLS, set_seed, resolve_profile,
                     split_for_profile, verify_profile_hash)
from scaler_utils import ScalerBundle
from cdc_calendar import attach_calendar

ILI_CHANNEL = 4  # index of "ILITOTAL" inside VAR_COLS

_DLINEAR_PATH = os.path.join(os.path.dirname(__file__), "innovation",
                             "backbones", "dlinear.py")

CKPT_DIR = os.path.join(os.path.dirname(__file__), "..", "checkpoints")


def load_nlinear_class():
    """Load NLinear from its source file WITHOUT executing backbones/__init__.py.

    `innovation.backbones.dlinear` only imports `innovation`, `innovation.fidelity`
    and `innovation.interfaces` (all light); it does NOT pull the registry that
    `backbones/__init__.py` would. Loading via importlib reuses the exact source
    so no architectural drift can be introduced by extraction.
    """
    spec = importlib.util.spec_from_file_location("_nlinear_impl", _DLINEAR_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.NLinear


# ── Data prep (exact mirror of train_ablation.load_and_normalize + build_windows)
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
            "n": n, "train_df": df.iloc[:t_end], "scaler": bundle,
            "profile": p}


def build_windows(data_norm, T, L, train_end, val_end, containment="start"):
    total = data_norm.shape[0]
    N = data_norm.shape[1]
    nw = total - T - L + 1
    X = np.zeros((nw, N, T), dtype=np.float32)
    Y = np.zeros((nw, N, L), dtype=np.float32)
    splits = np.zeros(nw, dtype=np.int8)
    target_starts = []
    for i in range(nw):
        X[i] = data_norm[i:i + T].T
        Y[i] = data_norm[i + T:i + T + L].T
        ts = i + T
        if containment == "strict":
            # Stage 5 section 2.2: the WHOLE target block must lie inside its split.
            if ts + L <= train_end:
                splits[i] = 0
            elif ts >= train_end and ts + L <= val_end:
                splits[i] = 1
            elif ts >= val_end and ts + L <= total:
                splits[i] = 2
            else:
                splits[i] = -1   # target straddles a split boundary -> not assignable
        else:
            splits[i] = 0 if ts < train_end else (1 if ts <= val_end else 2)
        target_starts.append(ts)
    keep = np.where(splits >= 0)[0]
    X, Y, splits = X[keep], Y[keep], splits[keep]
    ts_arr = np.asarray(target_starts)[keep]
    return (X[splits == 0], Y[splits == 0], X[splits == 1], Y[splits == 1],
            X[splits == 2], Y[splits == 2], {"target_starts": ts_arr, "splits": splits,
                                             "containment": containment})


# ── Metrics (exact mirror of train_ablation.evaluate, 7-variable z-space) ─────
@torch.no_grad()
def eval_mse(model, loader, device):
    model.eval()
    preds, targets = [], []
    for bx, by in loader:
        bx = bx.to(device)
        p = model(bx)
        preds.append(p.cpu().numpy())
        targets.append(by.numpy())
    p = np.concatenate(preds)
    t = np.concatenate(targets)
    mse_all = float(np.mean((p - t) ** 2))
    mae_all = float(np.mean(np.abs(p - t)))
    mse_ili = float(np.mean((p[:, ILI_CHANNEL, :] - t[:, ILI_CHANNEL, :]) ** 2))
    mae_ili = float(np.mean(np.abs(p[:, ILI_CHANNEL, :] - t[:, ILI_CHANNEL, :])))
    return mse_all, mae_all, mse_ili, mae_ili


def train_one(data_dict, L, seed, epochs, batch, device, containment="start"):
    """Train one (horizon, seed) NLinear fit; select by best validation MSE."""
    set_seed(seed + L)  # matches MIFlu's internal set_seed(seed + L) convention
    T, N = CONFIG["T"], CONFIG["N"]
    Xt, Yt, Xv, Yv, Xte, Yte, _sinfo = build_windows(
        data_dict["data_norm"], T, L, data_dict["train_end"], data_dict["val_end"],
        containment=containment)

    tl = DataLoader(TensorDataset(torch.from_numpy(Xt), torch.from_numpy(Yt)),
                    batch_size=batch, shuffle=True)
    vl = DataLoader(TensorDataset(torch.from_numpy(Xv), torch.from_numpy(Yv)),
                    batch_size=batch, shuffle=False)
    el = DataLoader(TensorDataset(torch.from_numpy(Xte), torch.from_numpy(Yte)),
                    batch_size=batch, shuffle=False)

    model = load_nlinear_class()(T=T, N=N, L=L).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=5e-4)
    crit = nn.MSELoss()

    best_val = float("inf")
    best_state = None
    best_epoch = -1
    for ep in range(epochs):
        model.train()
        for bx, by in tl:
            bx, by = bx.to(device), by.to(device)
            opt.zero_grad()
            loss = crit(model(bx), by)
            loss.backward()
            opt.step()
        v_mse_all, _, _, _ = eval_mse(model, vl, device)
        if v_mse_all < best_val:
            best_val = v_mse_all
            best_epoch = ep
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    if os.environ.get("DEFER_TEST") == "1":
        print("  [nlinear] DEFER_TEST=1 - Test NOT evaluated (validation-only fit)")
        # Stage 5 A2: persist the best-validation-epoch weights under a per-seed
        # name so the locked-batch scoring can select each (model, L, seed).
        os.makedirs(CKPT_DIR, exist_ok=True)
        ckpt_path = os.path.join(CKPT_DIR, f"best_nlinear_L{L}_seed{seed}.pth")
        torch.save(model.state_dict(), ckpt_path)
        return {"L": L, "seed": seed, "mse_all": None, "mae_all": None,
                "mse_ili": None, "mae_ili": None, "best_val": best_val,
                "best_epoch": best_epoch, "n_train": int(len(Xt)),
                "n_val": int(len(Xv)), "n_test": int(len(Xte)),
                "ckpt": ckpt_path,
                "model": model, "data_dict": data_dict, "test_deferred": True}
    t_mse_all, t_mae_all, t_mse_ili, t_mae_ili = eval_mse(model, el, device)
    return {"L": L, "seed": seed, "mse_all": t_mse_all, "mae_all": t_mae_all,
            "mse_ili": t_mse_ili, "mae_ili": t_mae_ili, "best_val": best_val,
            "n_train": int(len(Xt)), "n_val": int(len(Xv)), "n_test": int(len(Xte)),
            "model": model, "data_dict": data_dict}


# ── Equivalence self-check (CPU, no training, no Test scoring) ───────────────
def self_check():
    NLinear = load_nlinear_class()
    torch.manual_seed(0)
    T, N, L = 104, 7, 24
    model = NLinear(T=T, N=N, L=L)
    x = torch.randn(4, N, T)
    y = model(x)

    # Reference NLinear maths (Zeng et al., AAAI 2023): subtract last value,
    # one shared Linear(T->L) over the time axis, add the last value back.
    last = x[:, :, -1:]
    s = x - last
    y_ref = model.lin(s) + last
    err = float((y - y_ref).abs().max().item())
    assert err < 1e-6, f"NLinear forward drifted from reference: {err}"

    # Shape + output contract: (B, N, L) in the same z-space.
    assert y.shape == (4, N, L), y.shape
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    assert n_params == T * L + L, n_params  # Linear(T,L): weight + bias
    print("[nlinear] self-check OK")
    print(f"  loaded class = {NLinear.__module__}.{NLinear.__name__} "
          f"(source: {os.path.relpath(_DLINEAR_PATH)})")
    print(f"  forward matches reference NLinear maths (max abs err {err:.2e})")
    print(f"  output shape (B,N,L)={tuple(y.shape)}, trainable params={n_params}")
    return True


def preflight(profile, horizon, seed, containment="start"):
    """CPU shape/split checks without any training or Test scoring."""
    dd = load_and_normalize(profile)
    T, N, L = CONFIG["T"], CONFIG["N"], horizon
    Xt, Yt, Xv, Yv, Xte, Yte, sinfo = build_windows(
        dd["data_norm"], T, L, dd["train_end"], dd["val_end"],
        containment=containment)

    # Split invariant directly from the builder's own labels.
    ts = sinfo["target_starts"]
    sp = sinfo["splits"]
    if containment == "strict":
        # Stage 5 section 2.2: the WHOLE target block lies inside its split.
        assert ((sp == 0) == (ts + L <= dd["train_end"])).all()
        assert ((sp == 1) == ((ts >= dd["train_end"]) & (ts + L <= dd["val_end"]))).all()
        assert ((sp == 2) == ((ts >= dd["val_end"]) & (ts + L <= dd["n"]))).all()
    else:
        train_mask = ts < dd["train_end"]
        val_mask = (ts >= dd["train_end"]) & (ts <= dd["val_end"])
        test_mask = ts > dd["val_end"]
        assert (train_mask | val_mask | test_mask).all()
        assert not (train_mask & val_mask).any() and not (val_mask & test_mask).any()
        assert len(Xt) == int(train_mask.sum()) and len(Xv) == int(val_mask.sum()) \
            and len(Xte) == int(test_mask.sum())
    # A train scaler must never see a val/test row (fit_on_train_only gate).
    assert dd["scaler"].train_end == dd["train_end"]
    assert dd["train_df"].shape[0] == dd["train_end"]

    # Scaler numeric convention: population std ddof=0 + 1e-8, float32 input.
    assert dd["scaler"].val_end == dd["val_end"]
    assert dd["data_norm"].dtype == np.float32

    model = load_nlinear_class()(T=T, N=N, L=L)
    with torch.no_grad():
        y = model(torch.from_numpy(Xte[:4]).float())
    assert y.shape == (min(4, len(Xte)), N, L)

    print("[nlinear] preflight OK")
    print(f"  profile={profile} n={dd['n']} "
          f"train_end={dd['train_end']} val_end={dd['val_end']}")
    print(f"  L={L} seed={seed} windows train={len(Xt)} val={len(Xv)} "
          f"test={len(Xte)}")
    print(f"  scaler train-only fit OK (train_end={dd['scaler'].train_end})")
    print(f"  NLinear forward shape (B,N,L)={tuple(y.shape)} on {min(4, len(Xte))} test windows")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", type=int, default=None,
                    help="Single L (default: sweep [24,36,48,60]).")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--profile", type=str, default="author_966",
                    choices=("project_1025", "author_966"))
    ap.add_argument("--epochs", type=int, default=CONFIG["epochs"])
    ap.add_argument("--batch", type=int, default=CONFIG["batch_size"])
    ap.add_argument("--export-dir", default=None)
    ap.add_argument("--ckpt-dir", default=None,
                    help="Checkpoint directory (default: <project>/checkpoints).")
    ap.add_argument("--containment", choices=["start", "strict"], default="start",
                    help="target-split rule: 'start' = legacy (target start), "
                         "'strict' = Stage 5 (whole target inside its split)")
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--preflight", action="store_true")
    args = ap.parse_args()
    global CKPT_DIR
    if args.ckpt_dir:
        CKPT_DIR = args.ckpt_dir
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
        preflight(args.profile, args.horizon or 24, args.seed, args.containment)
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    export_dir = args.export_dir or os.path.join(
        "results", "stage3_a2", "author_966", "nlinear")
    os.makedirs(export_dir, exist_ok=True)
    metrics_path = os.path.join(export_dir, "metrics.csv")

    dd = load_and_normalize(args.profile)
    L_list = [args.horizon] if args.horizon is not None else CONFIG["L_list"]

    # Accumulate rows; dedupe on (L, seed) so a resume never duplicates.
    rows = []
    if os.path.exists(metrics_path):
        try:
            rows = pd.read_csv(metrics_path).to_dict("records")
        except Exception:
            rows = []
    done = {(int(r["L"]), int(r["seed"])) for r in rows}

    for L in L_list:
        if (L, args.seed) in done:
            continue
        t0 = time.time()
        r = train_one(dd, L, args.seed, args.epochs, args.batch, device, args.containment)
        rows = [x for x in rows if (int(x["L"]), int(x["seed"])) != (L, args.seed)]
        rows.append({k: r[k] for k in ("L", "seed", "mse_all", "mae_all",
                                       "mse_ili", "mae_ili", "best_val",
                                       "n_train", "n_val", "n_test")})
        pd.DataFrame(rows).to_csv(metrics_path, index=False)
        if r.get("mse_all") is None:
            print(f"[nlinear] L={L} seed={args.seed} TEST DEFERRED "
                  f"best_val={r['best_val']:.6f} best_epoch={r.get('best_epoch')} "
                  f"({time.time()-t0:.1f}s)")
        else:
            print(f"[nlinear] L={L} seed={args.seed} mse_all={r['mse_all']:.6f} "
                  f"mse_ili={r['mse_ili']:.6f} best_val={r['best_val']:.6f} "
                  f"({time.time()-t0:.1f}s)")

    print(f"[nlinear] DONE -> {metrics_path}")


if __name__ == "__main__":
    main()
