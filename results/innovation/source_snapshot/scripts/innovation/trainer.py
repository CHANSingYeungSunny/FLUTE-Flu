"""
trainer.py — one unified training loop: val-MSE early stopping + best restore.
=============================================================================

Early-stopping audit (revision 2)
---------------------------------
`early_stopping.EarlyStopping` was AUDITED before reuse: its `improved` test is
`val_loss < best - min_delta` and its `stop` test is
`num_bad_epochs >= patience` — both depend EXCLUSIVELY on validation loss, with
no peak / PTE / PIE / other indicator anywhere. It is therefore REUSED here
(full audit: `results/innovation/audit/early_stopping_audit.md`).

The trainer monitors validation MSE (z-space, all channels — the main protocol
metric), keeps the best-epoch weights, and RESTORES them at the end. PTE/PIE
never influence stopping or checkpoint selection.
"""

from __future__ import annotations

import os
import time

import numpy as np
import pandas as pd
import torch

from cdc_calendar import attach_calendar  # noqa: E402
from early_stopping import EarlyStopping  # noqa: E402
from innovation.data_pipeline import make_loaders  # noqa: E402

ILI = 4


def _ctx(ctx_fn, bsz, device):
    return ctx_fn(bsz) if ctx_fn is not None else None


def train_epoch(model, loader, opt, crit, device, ctx_fn=None) -> float:
    model.train()
    tot, n = 0.0, 0
    for bx, by in loader:
        bx, by = bx.to(device), by.to(device)
        opt.zero_grad()
        yh = model(bx, _ctx(ctx_fn, bx.size(0), device))
        loss = crit(yh, by)
        if hasattr(model, "auxiliary_loss"):
            loss = loss + model.auxiliary_loss()
        if not torch.isfinite(loss):
            opt.zero_grad()
            continue
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        tot += float(loss.item()) * bx.size(0)
        n += bx.size(0)
    return tot / max(n, 1)


@torch.no_grad()
def evaluate_z(model, loader, device, ctx_fn=None) -> dict:
    model.eval()
    ps, ts = [], []
    for bx, by in loader:
        bx = bx.to(device)
        ps.append(model(bx, _ctx(ctx_fn, bx.size(0), device)).cpu().numpy())
        ts.append(by.numpy())
    p = np.concatenate(ps)
    t = np.concatenate(ts)
    return {"mse_all": float(np.mean((p - t) ** 2)),
            "mae_all": float(np.mean(np.abs(p - t))),
            "mse_ili": float(np.mean((p[:, ILI, :] - t[:, ILI, :]) ** 2))}


@torch.no_grad()
def predict_frame(model, X, Y, idx, T, L, scaler, split_label, device,
                  batch_size: int = 16, ctx_fn=None) -> pd.DataFrame:
    """Per-step predictions (dual-track: z-space + physical) with real dates."""
    model.eval()
    rows = []
    scale_ili = float(scaler.scale_[ILI])
    mean_ili = float(scaler.mean_[ILI])
    for s in range(0, len(X), batch_size):
        bx = torch.from_numpy(X[s:s + batch_size]).to(device)
        yh = model(bx, _ctx(ctx_fn, bx.size(0), device)).cpu().numpy()
        by = Y[s:s + batch_size]
        gt_z, pr_z = by[:, ILI, :], yh[:, ILI, :]
        gt_p = gt_z * scale_ili + mean_ili
        pr_p = pr_z * scale_ili + mean_ili
        for r in range(bx.size(0)):
            base = int(idx[s + r]) + int(T)
            for step in range(L):
                rows.append((split_label, base + step, step,
                             float(gt_z[r, step]), float(pr_z[r, step]),
                             float(gt_p[r, step]), float(pr_p[r, step])))
    df = pd.DataFrame(rows, columns=[
        "split", "abs_week", "step", "ground_truth_ili", "prediction_ili",
        "ground_truth_ili_phys", "prediction_ili_phys"])
    df = attach_calendar(df, abs_week_col="abs_week")
    return df[["split", "abs_week", "step", "epiweek", "week_start_date",
               "ground_truth_ili", "prediction_ili",
               "ground_truth_ili_phys", "prediction_ili_phys"]]


def train_model(model, windows, cfg, run_dir, device="cpu", patience=7,
                epochs=20, batch_size=16, lr=5e-4, ctx_fn=None,
                max_seconds=None):
    """Train one model, early-stop on val MSE, restore the best checkpoint.

    `max_seconds` implements the timeout/resume requirement (revision 8): when
    the wall-clock budget is exceeded the loop stops early, but the best
    checkpoint seen so far is still restored and recorded (truncated=True).
    """
    tr = make_loaders(windows, "train", batch_size, True)
    va = make_loaders(windows, "val", batch_size, False)
    opt = torch.optim.Adam(model.parameters(), lr=float(lr))
    crit = torch.nn.MSELoss()
    ckpt_dir = os.path.join(run_dir, "checkpoints")
    stopper = EarlyStopping(patience=int(patience), save_dir=ckpt_dir,
                            filename="best_val_mse.pt")
    history = []
    truncated = False
    _t0 = time.time()
    for ep in range(1, int(epochs) + 1):
        if max_seconds is not None and (time.time() - _t0) > float(max_seconds):
            truncated = True
            print(f"    [time-limit] {max_seconds}s exceeded — stop at ep {ep}")
            break
        tr_loss = train_epoch(model, tr, opt, crit, device, ctx_fn)
        v = evaluate_z(model, va, device, ctx_fn)
        res = stopper(v["mse_all"], model, epoch=ep)
        history.append({"epoch": ep, "train_loss": tr_loss,
                        "val_mse": v["mse_all"], "val_mae": v["mae_all"],
                        "val_mse_ili": v["mse_ili"],
                        "improved": res["improved"], "saved": res["saved"],
                        "best_epoch": res["best_epoch"] if res["best_epoch"] else ep,
                        "stop": res["stop"]})
        print(f"    ep {ep:>3}/{epochs} | train={tr_loss:.4f} "
              f"val_mse={v['mse_all']:.4f} | "
              f"{'SAVED' if res['saved'] else res['reason'][:40]}"
              f"{' | STOP' if res['stop'] else ''}")
        if res["stop"]:
            break

    ckpt_path = os.path.join(ckpt_dir, "best_val_mse.pt")
    if os.path.exists(ckpt_path):
        model.load_state_dict(
            torch.load(ckpt_path, map_location=device, weights_only=True),
            strict=True)
    history_df = pd.DataFrame(history)
    history_df.attrs["truncated"] = bool(truncated)
    return history_df, stopper, ckpt_path
