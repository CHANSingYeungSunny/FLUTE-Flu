#!/usr/bin/env python3
"""
miflu_transfer_train.py
=======================
official-repository-based MIFlu transferred to the historical comparison contract.

This is NOT a paper reproduction and must never be labelled one. It takes the
FROZEN corrected R1-B architecture (the official repository's GPT4TS-derived
MIFlu with corrections B-1..B-6) and runs it under the HISTORICAL 1025-row
comparison contract, so that exactly one slot of the historical 4-vs-4 changes.

HISTORICAL CONTRACT (recovered, not invented)
---------------------------------------------
  dataset        data/raw/national_illness_raw.csv, 1025 rows
  sha256         c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d
  split          717 / 102 / 206   (hard-coded constant in clean_runner.py)
  window rule    stride 1; split by TARGET START:
                 train if ts < 717, val if ts <= 819, else test        (ts = i + T)
  T              104
  N              7, VAR_COLS order (ILITOTAL at index 4)
  scaler         per-column mean/std, float32, fitted on data[:717] ONLY
  z-space        (x - mean) / std
  horizons       24 / 36 / 48 / 60
  seeds          42 .. 51
  selection      best VALIDATION MSE  (historical rule: best_val_mse.pt, patience 7)
  config         epochs 20, batch 16, lr 5e-4

DELIBERATE DEVIATIONS FROM THE OLD SELF-BUILT MIFlu (declared)
--------------------------------------------------------------
  D1 architecture  -> the official repository's MIFlu (this is the intervention)
  D2 text asset    -> the author's text_emb_label_0507_<L>.txt (the official
                      repository's own horizon prompt embedding), instead of the
                      project-built prompt statistics encoder
  D3 window labels -> VAR_COLS names emitted truthfully; the OLD artefacts carry
                      variable labels shifted by two (see HISTORICAL_CONTRACT.md)
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

# The frozen Wave-1 / 4-vs-4 track is the v3_clean lineage, whose copy is LF.
# (The older v3_4/v3_5 roots hold a CRLF copy of the SAME content, sha
#  c2b983af...; identical after normalisation. The transfer must use the
#  v3_clean variant so the contract matches the frozen comparison exactly.)
DATA_SHA_EXPECT = "0a0648000066e12fe499f98693885b88ed3bc29fc8daca7f3af171b1bac86088"
T = 104
N_VARS = 7
TRAIN_END = 717
VAL_END = 819
VAR_COLS = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
            "ILITOTAL", "NUM. OF PROVIDERS", "OT"]
ILI_CHANNEL = 4
SCALER_MEAN = [1.755405306816101, 1.7133967876434326, 2658.326416015625,
               3699.761474609375, 9368.2890625, 1320.093505859375,
               491997.59375]
SCALER_STD = [1.2095322608947754, 1.1299502849578857, 2113.183837890625,
              4152.29541015625, 8853.4345703125, 504.9544982910156,
              234443.296875]


def sha256_file(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


class HistoricalWindowDataset(Dataset):
    """Historical window rule: stride 1, split decided by TARGET START week.

    X[i] = data[i : i+T].T   -> (N, T)
    Y[i] = data[i+T : i+T+L].T -> (N, L)
    split: train if (i+T) < 717 ; val if (i+T) <= 819 ; else test
    """

    def __init__(self, data_norm, L, split):
        self.data = data_norm.astype(np.float32)
        self.L = int(L)
        total = self.data.shape[0]
        nw = total - T - self.L + 1
        ts = np.arange(nw) + T
        keep = {"train": ts < TRAIN_END,
                "val": (ts >= TRAIN_END) & (ts <= VAL_END),
                "test": ts > VAL_END}[split]
        self.idx = np.where(keep)[0]

    def __len__(self):
        return len(self.idx)

    def __getitem__(self, k):
        # The official-repository model consumes (seq, channels), exactly as the
        # author's loader produces it. The historical pipeline's own models used
        # (N, T); the transpose is applied HERE so the architecture is untouched.
        i = int(self.idx[k])
        x = self.data[i:i + T]                   # (T, N)
        y = self.data[i + T:i + T + self.L]      # (L, N)
        # KEY IDENTITY: the historical `forecast_origin` is the WINDOW INDEX i,
        # not the target start. Verified against the frozen durable artefact:
        # primary__gpt2_miflu__L24__seed42__w1 has forecast_origin 613..715,
        # and 613 + T = 717 = its first validation target row.
        return torch.from_numpy(x), torch.from_numpy(y), i


def load_historical(code_root, data_path):
    df = pd.read_csv(data_path)
    if len(df) != 1025:
        raise SystemExit(f"[transfer] ABORT: expected 1025 rows, got {len(df)}")
    for c in VAR_COLS:
        if c not in df.columns:
            raise SystemExit(f"[transfer] ABORT: missing column {c}")
    arr = df[VAR_COLS].values.astype(np.float32)
    mean = np.asarray(SCALER_MEAN, dtype=np.float32).reshape(1, -1)
    std = np.asarray(SCALER_STD, dtype=np.float32).reshape(1, -1)
    return ((arr - mean) / std).astype(np.float32), df


def build_text(code_root, L):
    cands = [os.path.join(code_root, "dataset", "illness", "text_emb",
                          f"text_emb_label_0507_{L}.txt")]
    for c in cands:
        if os.path.exists(c):
            return np.loadtxt(c).astype(np.float32), c
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code-root", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--r1b", required=True)
    ap.add_argument("--horizon", type=int, required=True, choices=(24, 36, 48, 60))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--patience", type=int, default=7)
    ap.add_argument("--out", required=True)
    ap.add_argument("--smoke", action="store_true",
                    help="cap training batches per epoch (shape/path validation)")
    ap.add_argument("--smoke-steps", type=int, default=4)
    a = ap.parse_args()

    if socket.gethostname().lower().startswith("hpclogin"):
        print("[transfer] REFUSING to run on a login node"); return 3

    sys.path.insert(0, a.r1b)
    from r1b_model import R1BCorrectedMIFlu

    got = sha256_file(a.data)
    if got != DATA_SHA_EXPECT:
        print(f"[transfer] ABORT: dataset sha256 {got} != {DATA_SHA_EXPECT}"); return 4

    os.makedirs(a.out, exist_ok=True)
    L, dev = a.horizon, torch.device(a.device)
    data, df = load_historical(a.code_root, a.data)
    text, text_path = build_text(a.code_root, L)

    ds_tr = HistoricalWindowDataset(data, L, "train")
    ds_va = HistoricalWindowDataset(data, L, "val")
    ds_te = HistoricalWindowDataset(data, L, "test")
    dl_tr = DataLoader(ds_tr, batch_size=a.batch, shuffle=True, drop_last=False)
    dl_va = DataLoader(ds_va, batch_size=a.batch, shuffle=False, drop_last=False)
    dl_te = DataLoader(ds_te, batch_size=a.batch, shuffle=False, drop_last=False)

    import argparse as _ap
    configs = _ap.Namespace(
        model_id="miflu_transfer", checkpoints=a.out, multimodal=1,
        root_path=os.path.dirname(a.data), data_path=os.path.basename(a.data),
        data="custom", features="M", freq=0, target="OT", embed="timeF",
        percent=100, lora_r=4, target_modules=["c_attn"], PEFT=1, seq_len=T,
        pred_len=L, label_len=18, decay_fac=0.75, learning_rate=a.lr,
        batch_size=a.batch, num_workers=0, train_epochs=a.epochs,
        lradj="type1", patience=a.patience, gpt_layers=6, backbone="gpt2",
        textmodel="gpt2", e_layers=3, d_model=768, n_heads=4, d_ff=768,
        dropout=0.2, enc_in=N_VARS, c_out=N_VARS, patch_size=24, kernel_size=25,
        loss_func="mse", pretrain=1, freeze=1, model="model", stride=2,
        max_len=-1, hid_dim=16, tmax=10, itr=1, cos=0)

    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    model = R1BCorrectedMIFlu(configs, dev, text_embeddings=text).to(dev)
    tot = sum(p.numel() for p in model.parameters())
    trn = sum(p.numel() for p in model.parameters() if p.requires_grad)
    n_lora = sum(1 for n, _ in model.named_parameters() if "lora_" in n)

    print(f"[transfer] L={L} seed={a.seed} train/val/test windows = "
          f"{len(ds_tr)}/{len(ds_va)}/{len(ds_te)}")
    print(f"[transfer] total={tot:,} trainable={trn:,} ({100*trn/tot:.2f}%) "
          f"lora_tensors={n_lora} text={text_path}")

    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad],
                           lr=a.lr)
    crit = nn.MSELoss()
    best = {"val": float("inf"), "state": None, "epoch": -1}
    bad = 0
    t0 = time.time()
    for ep in range(a.epochs):
        model.train(); tl = n = 0.0
        for si, (xb, yb, _) in enumerate(dl_tr):
            if a.smoke and si >= a.smoke_steps:
                break
            xb, yb = xb.to(dev), yb.to(dev)
            opt.zero_grad()
            out = model(xb)
            loss = crit(out, yb)
            loss.backward(); opt.step()
            tl += float(loss) * xb.shape[0]; n += xb.shape[0]
        model.eval(); vl = m = 0.0
        with torch.no_grad():
            for vi_, (xb, yb, _) in enumerate(dl_va):
                if a.smoke and vi_ >= a.smoke_steps:
                    break
                xb, yb = xb.to(dev), yb.to(dev)
                vl += float(crit(model(xb), yb)) * xb.shape[0]; m += xb.shape[0]
        v = vl / max(m, 1)
        print(f"[transfer] epoch {ep+1}/{a.epochs} train={tl/max(n,1):.6f} val={v:.6f}")
        if v < best["val"]:
            best = {"val": v, "epoch": ep + 1,
                    "state": {k: t.detach().cpu().clone()
                              for k, t in model.state_dict().items()}}
            bad = 0
        else:
            bad += 1
            if bad >= a.patience:
                print(f"[transfer] early stop at epoch {ep+1} (patience {a.patience})")
                break

    if best["state"] is not None:
        model.load_state_dict(best["state"])
    model.eval()

    # ── Predictions for BOTH splits, in the historical prediction schema ──
    # The historical champion selector (average_MSE_4L) is computed on
    # VALIDATION, so validation predictions are mandatory, not optional.
    mean_v = np.asarray(SCALER_MEAN, dtype=np.float64)
    std_v = np.asarray(SCALER_STD, dtype=np.float64)

    def predict_frame(loader, split_name):
        rows, P_all, Y_all = [], [], []
        with torch.no_grad():
            for bi, (xb, yb, ts) in enumerate(loader):
                if a.smoke and bi >= a.smoke_steps:
                    break
                xb = xb.to(dev)
                pred = model(xb).cpu().numpy()      # (B, L, N), z-space
                true = yb.numpy()                    # (B, L, N), z-space
                P_all.append(pred); Y_all.append(true)
                for i in range(pred.shape[0]):
                    origin = int(ts[i])
                    for vi in range(N_VARS):
                        for k in range(L):
                            tz = float(true[i, k, vi]); pz = float(pred[i, k, vi])
                            rows.append({
                                "model_key": "miflu_official_transferred",
                                "horizon": L, "seed_or_rep": a.seed,
                                "split": split_name,
                                "forecast_origin": origin, "target_date": None,
                                "step": k, "lead_weeks": k + 1,
                                "variable": VAR_COLS[vi], "variable_index": vi,
                                "y_true_z": tz, "y_pred_z": pz,
                                "y_true_physical": float(tz * std_v[vi] + mean_v[vi]),
                                "y_pred_physical": float(pz * std_v[vi] + mean_v[vi]),
                            })
        return pd.DataFrame(rows), P_all, Y_all

    vdf, _, _ = predict_frame(dl_va, "val")
    pdf, P_all, Y_all = predict_frame(dl_te, "test")

    def _m(e):
        e = e.y_pred_z.values - e.y_true_z.values
        return float(np.mean(e ** 2)), float(np.mean(np.abs(e)))

    val_mse, val_mae = _m(vdf)
    mse, mae = _m(pdf)

    tag = f"miflu_transfer__L{L}__seed{a.seed}"
    vdf.to_csv(os.path.join(a.out, f"validation_predictions_{tag}.csv"), index=False)
    pdf.to_csv(os.path.join(a.out, f"test_predictions_{tag}.csv"), index=False)
    np.savez_compressed(
        os.path.join(a.out, f"pred_{tag}.npz"),
        pred=np.concatenate(P_all).astype(np.float32),      # (n, L, N)
        target=np.concatenate(Y_all).astype(np.float32),    # (n, L, N)
        origin=np.concatenate([ts.numpy() for _, _, ts in dl_te]).astype(np.int32),
        horizon=np.int32(L), seed=np.int32(a.seed),
        model=np.array("miflu_official_transferred"),
        space=np.array("standardized_train_fit_z"))

    frozen = sorted(n_ for n_, p in model.named_parameters() if not p.requires_grad)
    keep = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()
            if k not in set(frozen)}
    ck = os.path.join(a.out, f"ckpt_{tag}.pth")
    torch.save(keep, ck)
    json.dump({"frozen_keys": frozen, "n_stored_tensors": len(keep),
               "n_frozen_tensors": len(frozen)},
              open(os.path.join(a.out, f"ckpt_{tag}.frozen_keys.json"), "w"), indent=2)

    man = {
        "label": "official-repository-based MIFlu transferred to the historical comparison contract",
        "NOT": "a paper reproduction",
        "horizon": L, "seed": a.seed, "device": str(dev),
        "host": socket.gethostname(),
        "dataset": a.data, "dataset_sha256": got,
        "split": {"train": TRAIN_END, "validation": VAL_END - TRAIN_END,
                  "test": 1025 - VAL_END},
        "window_rule": "stride 1, split by target start (historical)",
        "windows": {"train": len(ds_tr), "val": len(ds_va), "test": len(ds_te)},
        "T": T, "N": N_VARS, "var_cols": VAR_COLS,
        "epochs": a.epochs, "lr": a.lr, "batch": a.batch, "patience": a.patience,
        "best_val_mse": best["val"], "best_epoch": best["epoch"],
        "val_mse_all_7vars_full_horizon_z": val_mse,
        "val_mae_all_7vars_full_horizon_z": val_mae,
        "n_val_elements": int(len(vdf)),
        "test_mse_all_7vars_full_horizon_z": mse,
        "test_mae_all_7vars_full_horizon_z": mae,
        "n_elements": int(len(pdf)),
        "total_parameters": int(tot), "trainable_parameters": int(trn),
        "trainable_fraction": round(trn / tot, 6), "lora_tensors": n_lora,
        "text_asset": text_path,
        "checkpoint_selection": "best VALIDATION mse (historical rule)",
        "test_access_during_fit": False,
        "wall_seconds": round(time.time() - t0, 1),
        "deviations_from_old_selfbuilt": [
            "D1 architecture: official repository MIFlu (the intervention)",
            "D2 text asset: author text_emb_label_0507_<L>.txt",
            "D3 variable labels emitted truthfully (old files are shifted by 2)",
        ],
    }
    json.dump(man, open(os.path.join(a.out, f"manifest_{tag}.json"), "w"), indent=2)
    print(f"[transfer] val mse_all7={val_mse:.6f} mae_all7={val_mae:.6f} "
          f"n={len(vdf)} | test mse_all7={mse:.6f} mae_all7={mae:.6f} "
          f"n={len(pdf)} best_epoch={best['epoch']}")
    print(f"[transfer] wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())