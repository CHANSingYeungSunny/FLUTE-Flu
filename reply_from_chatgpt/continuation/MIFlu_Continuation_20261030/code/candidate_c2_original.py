#!/usr/bin/env python3
"""
C2 schedule-alignment extension. NOT RUN. Original source SHA256: 0c8d8012d18e99b11b7657af927842a9b03c928f57786f5f93ecbf5908d17a7c

IDENTICAL to the frozen R1-B configuration except for ONE change: the released
author learning-rate schedule (utils/tools.py:26-27) is applied.

    lr(epoch) = 5e-4                      if epoch <  3
              = 5e-4 * 0.9 ** (epoch-3)   if epoch >= 3

R1-B declares lradj="type1" but never calls adjust_learning_rate, so it trains
all 20 epochs at a constant 5e-4. This is the only setting where R1-B silently
differs from a RECOVERED released default without that difference being a
declared repair of a released defect. See R1C_DOCUMENTARY_EVIDENCE.md.

This is Track R work. It does NOT touch Track C and does not change the
championship.

NOT a paper reproduction (that is Track R, verdict PARTIAL_REPRODUCTION).
This is the MIFlu slot of the eight-model Test championship.

CONTRACT
  dataset   author national_illness.csv, 966 rows, sha 2a96dfed…ebfe5
  split     train [0,676) · validation [676,773) · test [773,966)
  T         104, N=7
  strict    o = last input index; input = data[o-T+1 : o+1]; target = data[o+1 : o+L]
            origins = [max(lo-1, T-1), hi-L-1]   (target fully inside its split)
            counts 549/74/170 · 537/62/158 · 525/50/146 · 513/38/134
  keys      forecast_origin = o · target_start_row = o+1 · target_end_row = o+L
  policy    Validation selects the checkpoint; Test read ONCE afterwards
  config    20 epochs, batch 16, lr 5e-4   (PAPER_EXPLICIT via Table IV)
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

DATA_SHA_EXPECT = "2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5"
T, N_VARS = 104, 7
SPLITS = {"train": (0, 676), "validation": (676, 773), "test": (773, 966)}
FEATURE_NAMES = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
                 "ILITOTAL", "NUM. OF PROVIDERS", "OT"]
EXPECTED = {24: (549, 74, 170), 36: (537, 62, 158),
            48: (525, 50, 146), 60: (513, 38, 134)}


def sha256_file(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


class Strict966Dataset(Dataset):
    """Strict containment: the whole target block must lie inside the split."""

    def __init__(self, data, L, lo, hi):
        self.data = data.astype(np.float32)
        self.L = int(L)
        first = max(lo - 1, T - 1)
        last = hi - L - 1
        self.origins = np.arange(first, last + 1) if last >= first else np.arange(0)
        assert np.all(self.origins + 1 >= lo)
        assert np.all(self.origins + L <= hi - 1)

    def __len__(self):
        return len(self.origins)

    def __getitem__(self, k):
        o = int(self.origins[k])
        x = self.data[o - T + 1:o + 1]        # (T, N)
        y = self.data[o + 1:o + 1 + self.L]   # (L, N)
        assert x.shape[0] == T and y.shape[0] == self.L
        return torch.from_numpy(x), torch.from_numpy(y), o


def load_966(path):
    df = pd.read_csv(path)
    if len(df) != 966:
        raise SystemExit(f"[strict966] ABORT expected 966 rows, got {len(df)}")
    cols = [c for c in df.columns if c not in ("epiweek", "release_date", "date")]
    if len(cols) != N_VARS:
        raise SystemExit(f"[strict966] ABORT expected {N_VARS} cols, got {cols}")
    X = df[cols].to_numpy(np.float64)
    tr_end, te_n = int(len(X) * 0.70), int(len(X) * 0.20)
    va_end = len(X) - te_n
    mu, sd = X[:tr_end].mean(0), X[:tr_end].std(0) + 1e-8
    return (X - mu) / sd, tr_end, va_end, cols


def build_text(code_root, L):
    p = os.path.join(code_root, "dataset", "illness", "text_emb",
                     f"text_emb_label_0507_{L}.txt")
    return (np.loadtxt(p).astype(np.float32), p) if os.path.exists(p) else (None, None)


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
    ap.add_argument("--out", required=True)
    ap.add_argument("--lr-schedule", default="r1c_type1",
                    choices=("constant", "r1c_type1"),
                    help="constant = R1-B; r1c_type1 = the released 0.9 decay")
    a = ap.parse_args()

    if socket.gethostname().lower().startswith("hpclogin"):
        print("[strict966] REFUSING login node"); return 3
    sys.path.insert(0, a.r1b)
    from r1b_model import R1BCorrectedMIFlu

    got = sha256_file(a.data)
    if got != DATA_SHA_EXPECT:
        print(f"[strict966] ABORT dataset sha {got}"); return 4

    os.makedirs(a.out, exist_ok=True)
    L, dev = a.horizon, torch.device(a.device)
    data, tr_end, va_end, cols = load_966(a.data)
    assert (tr_end, va_end) == (676, 773), (tr_end, va_end)
    text, text_path = build_text(a.code_root, L)

    ds = {k: Strict966Dataset(data, L, lo, hi) for k, (lo, hi) in SPLITS.items()}
    counts = (len(ds["train"]), len(ds["validation"]), len(ds["test"]))
    if counts != EXPECTED[L]:
        print(f"[strict966] ABORT counts {counts} != {EXPECTED[L]}"); return 6
    dls = {k: DataLoader(d, batch_size=a.batch, shuffle=(k == "train"),
                         drop_last=False) for k, d in ds.items()}

    import argparse as _ap
    configs = _ap.Namespace(
        model_id="r1c_c1", checkpoints=a.out, multimodal=1,
        root_path=os.path.dirname(a.data), data_path=os.path.basename(a.data),
        data="custom", features="M", freq=0, target="OT", embed="timeF",
        percent=100, lora_r=4, target_modules=["c_attn"], PEFT=1, seq_len=T,
        pred_len=L, label_len=18, decay_fac=0.75, learning_rate=a.lr,
        batch_size=a.batch, num_workers=0, train_epochs=a.epochs, lradj="type1",
        patience=3, gpt_layers=6, backbone="gpt2", textmodel="gpt2", e_layers=3,
        d_model=768, n_heads=4, d_ff=768, dropout=0.2, enc_in=N_VARS,
        c_out=N_VARS, patch_size=24, kernel_size=25, loss_func="mse",
        pretrain=1, freeze=1, model="model", stride=2, max_len=-1, hid_dim=16,
        tmax=10, itr=1, cos=0)

    torch.manual_seed(a.seed); np.random.seed(a.seed)
    model = R1BCorrectedMIFlu(configs, dev, text_embeddings=text).to(dev)
    tot = sum(p.numel() for p in model.parameters())
    trn = sum(p.numel() for p in model.parameters() if p.requires_grad)
    n_lora = sum(1 for n, _ in model.named_parameters() if "lora_" in n)
    print(f"[strict966] L={L} seed={a.seed} windows tr/va/te={counts} "
          f"total={tot:,} trainable={trn:,} ({100*trn/tot:.2f}%) lora={n_lora}")

    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=a.lr)
    crit = nn.MSELoss()
    best = {"val": float("inf"), "state": None, "epoch": -1}
    t0 = time.time()
    for ep in range(a.epochs):
        # C2: match the released END-of-epoch schedule at the start
        # of the NEXT epoch. This repairs the one-epoch shift in packaged C1.
        if a.lr_schedule == "r1c_type1":
            # Match the author's END-of-previous-epoch update exactly.
            # ep is zero-based: training epoch 4 still uses the epoch-3 update.
            e_previous = ep
            cur = a.lr if e_previous < 3 else a.lr * (0.9 ** (e_previous - 3))
            for g in opt.param_groups:
                g["lr"] = cur
        model.train(); tl = n = 0.0
        for xb, yb, _ in dls["train"]:
            xb, yb = xb.to(dev), yb.to(dev)
            opt.zero_grad(); loss = crit(model(xb), yb); loss.backward(); opt.step()
            tl += float(loss) * xb.shape[0]; n += xb.shape[0]
        model.eval(); vl = m = 0.0
        with torch.no_grad():
            for xb, yb, _ in dls["validation"]:
                xb, yb = xb.to(dev), yb.to(dev)
                vl += float(crit(model(xb), yb)) * xb.shape[0]; m += xb.shape[0]
        v = vl / max(m, 1)
        print(f"[strict966] epoch {ep+1}/{a.epochs} train={tl/max(n,1):.6f} val={v:.6f}")
        if v < best["val"]:
            best = {"val": v, "epoch": ep + 1,
                    "state": {k: t.detach().cpu().clone()
                              for k, t in model.state_dict().items()}}
    if best["state"] is not None:
        model.load_state_dict(best["state"])
    model.eval()

    def frame(split):
        rows = []
        with torch.no_grad():
            for xb, yb, ob in dls[split]:
                xb = xb.to(dev)
                pred = model(xb).cpu().numpy()   # (B, L, N)
                true = yb.numpy()                # (B, L, N)
                for i in range(pred.shape[0]):
                    o = int(ob[i])
                    for fi in range(N_VARS):
                        for k in range(L):
                            rows.append({
                                "dataset_hash": got, "seed": a.seed,
                                "horizon": L, "split": split,
                                "forecast_origin": o,
                                "target_start_row": o + 1,
                                "target_end_row": o + L,
                                "forecast_lead": k + 1,
                                "feature_index": fi,
                                "corrected_feature_name": FEATURE_NAMES[fi],
                                "model_key": "miflu_official_strict966",
                                "y_true_z": float(true[i, k, fi]),
                                "y_pred_z": float(pred[i, k, fi]),
                            })
        return pd.DataFrame(rows)

    vdf, tdf = frame("validation"), frame("test")

    def mm(d):
        e = d.y_pred_z.values - d.y_true_z.values
        return float(np.mean(e ** 2)), float(np.mean(np.abs(e)))
    v_mse, v_mae = mm(vdf); t_mse, t_mae = mm(tdf)

    tag = f"r1c_c2_endmatch__L{L}__seed{a.seed}"
    vdf.to_csv(os.path.join(a.out, f"validation_predictions_{tag}.csv"), index=False)
    tdf.to_csv(os.path.join(a.out, f"test_predictions_{tag}.csv"), index=False)

    frozen = sorted(n_ for n_, p in model.named_parameters() if not p.requires_grad)
    keep = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()
            if k not in set(frozen)}
    torch.save(keep, os.path.join(a.out, f"ckpt_{tag}.pth"))
    json.dump({"frozen_keys": frozen, "n_stored_tensors": len(keep),
               "n_frozen_tensors": len(frozen)},
              open(os.path.join(a.out, f"ckpt_{tag}.frozen_keys.json"), "w"), indent=2)

    json.dump({
        "label": "official-repository-based corrected MIFlu, author-966 strict championship slot",
        "NOT": "a paper reproduction (Track R holds that verdict)",
        "track": "C", "horizon": L, "seed": a.seed, "device": str(dev),
        "dataset": a.data, "dataset_sha256": got,
        "splits": {k: list(v) for k, v in SPLITS.items()},
        "window_rule": "strict containment (target fully inside its split)",
        "window_counts": {"train": counts[0], "validation": counts[1], "test": counts[2]},
        "T": T, "N": N_VARS, "feature_names": FEATURE_NAMES,
        "epochs": a.epochs, "lr": a.lr, "batch": a.batch,
        "lr_schedule": a.lr_schedule,
        "lr_schedule_evidence": ("utils/tools.py:26-27 (released type1)" if
                                 a.lr_schedule == "r1c_type1" else "constant 5e-4"),
        "r1c_candidate": "C2_end_of_epoch_matched_scheduler",
        "best_val_mse": best["val"], "best_epoch": best["epoch"],
        "val_mse_z": v_mse, "val_mae_z": v_mae, "n_val": int(len(vdf)),
        "test_mse_z": t_mse, "test_mae_z": t_mae, "n_test": int(len(tdf)),
        "total_parameters": int(tot), "trainable_parameters": int(trn),
        "trainable_fraction": round(trn / tot, 6), "lora_tensors": n_lora,
        "text_asset": text_path,
        "checkpoint_selection": "best VALIDATION mse (Test read once, after freeze)",
        "test_access_during_fit": False,
        "wall_seconds": round(time.time() - t0, 1),
    }, open(os.path.join(a.out, f"manifest_{tag}.json"), "w"), indent=2)

    print(f"[strict966] val mse={v_mse:.6f} n={len(vdf)} | "
          f"test mse={t_mse:.6f} mae={t_mae:.6f} n={len(tdf)} best_ep={best['epoch']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())