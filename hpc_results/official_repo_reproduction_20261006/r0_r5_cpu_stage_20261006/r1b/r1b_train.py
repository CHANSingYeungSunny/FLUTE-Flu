#!/usr/bin/env python3
"""
r1b_train.py — R1-B reproduction trainer.

Built ON the author's released code (imported, never modified). Implements the
corrections that cannot live in the model:

  B-1  seven-channel windows        (R1BDataset overrides the released loader's
                                     single-channel slice AND its Test-only use
                                     of feature 0)
  B-3  PEFT=1                       (the author's own LoRA branch; the caller
                                     must NOT pass --target_modules)
  B-5  validation-only selection    (the released rule selects on Test)
  B-6  persisted predictions        (the released np.save calls are commented out)
  B-7  declared configuration       (epochs 20 / lr 5e-4 / batch 16 are
                                     PAPER_EXPLICIT via Table IV)

B-2 (text prefix + readout) and B-4 (effective freeze) live in r1b_model.py.

CPU-runnable. `--device cpu` for acceptance tests; `--device cuda` for the pilot.

Usage:
  python r1b_train.py --horizon 24 --repetition 0 --device cpu \
      --code-root <author repo> --out <dir> [--epochs 2 --smoke]
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
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

DATA_SHA_EXPECT = "2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5"
N_VARS = 7
T = 104
SPLIT = (676, 97, 193)          # author integer rule on 966 rows; PAPER_EXPLICIT 70:10:20


def sha256_file(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
class R1BDataset(Dataset):
    """B-1: multivariate windows over ALL seven channels.

    The released `Dataset_Custom.__getitem__` slices `feat_id:feat_id+1` (one
    channel) and its `__len__` omits the `* enc_in` factor for Test, so Test
    only ever covers channel 0. This replaces both with a seven-channel window.
    Target containment: the whole target block [o+1, o+L] must lie inside the
    split (the strict rule), so no target crosses a boundary.
    """

    def __init__(self, data, T, L, lo, hi):
        """`o` is the LAST INPUT index. Input = [o-T+1, o]; target = [o+1, o+L].

        The strict rule is TARGET containment: the whole target block must lie
        inside [lo, hi). The input window MAY cross an earlier split boundary --
        that is normal rolling-origin forecasting, and the recovery plan states it
        explicitly ("historical input context crossing an earlier split boundary
        is permitted; future targets crossing a boundary are not").

        CORRECTED 2026-10-06. The first version used
            origins = [lo, hi-L-1] with x = data[o : o+T]
        which ignored T entirely: the target slice ran past the end of the array
        (RuntimeError: "stack expects each tensor to be equal size, but got
        [24,7] ... and [23,7]"), which failed the L=24 pilot job 607969.

        The corrected form reproduces the recorded A2/R1-B origin counts EXACTLY:
            L=24 -> 549 / 74 / 170      L=36 -> 537 / 62 / 158
            L=48 -> 525 / 50 / 146      L=60 -> 513 / 38 / 134
        which is independent confirmation that this is the intended contract.
        """
        self.data = data.astype(np.float32)
        self.T, self.L, self.lo, self.hi = T, L, lo, hi
        first_o = max(lo - 1, T - 1)          # need a full input window, and o+1 >= lo
        last_o = hi - L - 1                   # need o+L <= hi-1
        self.origins = np.arange(first_o, last_o + 1) if last_o >= first_o             else np.arange(0)

    def __len__(self):
        return len(self.origins)

    def __getitem__(self, i):
        o = int(self.origins[i])
        x = self.data[o - self.T + 1:o + 1, :]        # (T, 7)
        y = self.data[o + 1:o + 1 + self.L, :]        # (L, 7)
        assert x.shape[0] == self.T and y.shape[0] == self.L,             f"window out of range at o={o}: x{x.shape} y{y.shape}"
        return torch.from_numpy(x), torch.from_numpy(y), o


def load_data(code_root, data_path):
    import pandas as pd
    df = pd.read_csv(data_path)
    cols = [c for c in df.columns if c not in ("epiweek", "release_date", "date")]
    if len(cols) != N_VARS:
        raise SystemExit(f"[r1b] ABORT: expected {N_VARS} numeric columns, got {len(cols)}: {cols}")
    X = df[cols].to_numpy(np.float64)
    tr_end = int(len(X) * 0.70)                       # 676
    te_n = int(len(X) * 0.20)                         # 193
    va_end = len(X) - te_n                            # 773
    mu = X[:tr_end].mean(0)
    sd = X[:tr_end].std(0) + 1e-8                     # scaler on TRAIN ROWS ONLY
    return (X - mu) / sd, tr_end, va_end, cols


def build_prompt_embeddings(code_root, L, df_path, n_tokens=17):
    """Prompt embeddings for the paper's prompt template.

    The released repo ships precomputed GPT-2 embeddings for a 317-token prompt
    (`text_emb_label_0507_<L>.txt`). R1-B uses that SAME asset: it is the
    author's own text representation for this horizon, so using it keeps the
    textual input on the author's basis rather than inventing one.
    Returns (T_text, 768) or None.
    """
    cands = [os.path.join(code_root, "dataset", "illness", "text_emb",
                          f"text_emb_label_0507_{L}.txt"),
             os.path.join(os.path.dirname(df_path), "text_emb",
                          f"text_emb_label_0507_{L}.txt")]
    for c in cands:
        if os.path.exists(c):
            a = np.loadtxt(c).astype(np.float32)
            return a, c
    return None, None


# ─────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code-root", required=True)
    ap.add_argument("--data", default=None)
    ap.add_argument("--horizon", type=int, required=True, choices=(24, 36, 48, 60))
    ap.add_argument("--repetition", type=int, default=0)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--epochs", type=int, default=20)        # B-7: PAPER_EXPLICIT (Table IV)
    ap.add_argument("--lr", type=float, default=5e-4)        # B-7: PAPER_EXPLICIT (Table IV)
    ap.add_argument("--batch", type=int, default=16)         # B-7: PAPER_EXPLICIT (Table IV)
    ap.add_argument("--peft", type=int, default=1)           # B-3
    ap.add_argument("--no-text", action="store_true", help="matched no-text control")
    ap.add_argument("--out", required=True)
    ap.add_argument("--smoke", action="store_true", help="1 epoch, tiny subset")
    a = ap.parse_args()

    if socket.gethostname().lower().startswith("hpclogin"):
        print("[r1b] REFUSING to run on a login node"); return 3

    sys.path.insert(0, os.path.join(a.code_root, "scripts"))
    sys.path.insert(0, os.path.join(a.code_root))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from r1b_model import R1BCorrectedMIFlu

    data_path = a.data or os.path.join(a.code_root, "dataset", "illness",
                                       "national_illness.csv")
    got = sha256_file(data_path)
    if got != DATA_SHA_EXPECT:
        print(f"[r1b] ABORT: dataset sha256 {got} != {DATA_SHA_EXPECT}"); return 4

    os.makedirs(a.out, exist_ok=True)
    L, dev = a.horizon, torch.device(a.device)
    data, tr_end, va_end, cols = load_data(a.code_root, data_path)

    text, text_path = (None, None) if a.no_text else build_prompt_embeddings(
        a.code_root, L, data_path)

    # ---- B-1 windows, strict containment --------------------------------
    ds_tr = R1BDataset(data, T, L, 0, tr_end)
    ds_va = R1BDataset(data, T, L, tr_end, va_end)
    ds_te = R1BDataset(data, T, L, va_end, len(data))
    dl_tr = DataLoader(ds_tr, batch_size=a.batch, shuffle=True, drop_last=False)
    dl_va = DataLoader(ds_va, batch_size=a.batch, shuffle=False, drop_last=False)
    dl_te = DataLoader(ds_te, batch_size=a.batch, shuffle=False, drop_last=False)

    import argparse as _ap
    configs = _ap.Namespace(
        model_id="r1b", checkpoints=a.out, multimodal=0 if a.no_text else 1,
        root_path=os.path.dirname(data_path), data_path=os.path.basename(data_path),
        data="custom", features="M", freq=0, target="OT", embed="timeF", percent=100,
        lora_r=4, target_modules=["c_attn"],          # the author's LIST default - do not override
        PEFT=a.peft, seq_len=T, pred_len=L, label_len=18, decay_fac=0.75,
        learning_rate=a.lr, batch_size=a.batch, num_workers=0,
        train_epochs=a.epochs, lradj="type1", patience=3, gpt_layers=6,
        backbone="gpt2", textmodel="gpt2", e_layers=3, d_model=768, n_heads=4,
        d_ff=768, dropout=0.2, enc_in=N_VARS, c_out=N_VARS, patch_size=24,
        kernel_size=25, loss_func="mse", pretrain=1, freeze=1, model="model",
        stride=2, max_len=-1, hid_dim=16, tmax=10, itr=1, cos=0)

    torch.manual_seed(1000 + a.repetition)
    np.random.seed(1000 + a.repetition)
    model = R1BCorrectedMIFlu(configs, dev, text_embeddings=text).to(dev)

    tot = sum(p.numel() for p in model.parameters())
    trn = sum(p.numel() for p in model.parameters() if p.requires_grad)
    n_lora = sum(1 for n, p in model.named_parameters() if "lora_" in n)

    man = {
        "track": "R1-B", "horizon": L, "repetition": a.repetition,
        "device": str(dev), "host": socket.gethostname(),
        "python": sys.version.split()[0], "torch": torch.__version__,
        "dataset": data_path, "dataset_sha256": got,
        "split": {"train_end": tr_end, "val_end": va_end, "test_n": len(data) - va_end},
        "n_vars": N_VARS, "T": T, "L": L,
        "origins_per_split": {"train": len(ds_tr), "val": len(ds_va), "test": len(ds_te)},
        "epochs": a.epochs, "learning_rate": a.lr, "batch_size": a.batch,
        "epochs_provenance": "PAPER_EXPLICIT via Table IV (national = 20)",
        "lr_provenance": "PAPER_EXPLICIT via Table IV (national = 0.0005)",
        "batch_provenance": "PAPER_EXPLICIT via Table IV (national = 16)",
        "peft": a.peft, "lora_tensors": n_lora,
        "text_mode": "none (matched no-text control)" if a.no_text else "prefixed",
        "text_asset": text_path,
        "total_parameters": int(tot), "trainable_parameters": int(trn),
        "trainable_fraction": round(trn / tot, 6),
        "freeze_report": model.freeze_report,
        "corrections": model.corrections,
        "checkpoint_selection": "best VALIDATION mse_all (B-5)",
        "test_access_during_fit": False,
        "pooling_axes": "mean over (origins x leads x 7 variables), z-space",
    }
    print(f"[r1b] L={L} rep={a.repetition} total={tot:,} trainable={trn:,} "
          f"({100*trn/tot:.2f}%) lora_tensors={n_lora} text={man['text_mode']}")
    print(f"[r1b] origins train/val/test = {len(ds_tr)}/{len(ds_va)}/{len(ds_te)}")

    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=a.lr)
    crit = nn.MSELoss()
    epochs = 1 if a.smoke else a.epochs

    best = {"val": float("inf"), "state": None, "epoch": -1}
    for ep in range(epochs):
        model.train(); tl = n = 0.0
        for xb, yb, _ in dl_tr:
            xb, yb = xb.to(dev), yb.to(dev)
            opt.zero_grad()
            out = model(xb)
            loss = crit(out, yb)
            loss.backward(); opt.step()
            tl += float(loss) * xb.shape[0]; n += xb.shape[0]
        # B-5: validation only - Test is never touched here
        model.eval(); vl = m = 0.0
        with torch.no_grad():
            for xb, yb, _ in dl_va:
                xb, yb = xb.to(dev), yb.to(dev)
                vl += float(crit(model(xb), yb)) * xb.shape[0]; m += xb.shape[0]
        v = vl / max(m, 1)
        print(f"[r1b] epoch {ep+1}/{epochs} train={tl/max(n,1):.6f} val={v:.6f}")
        if v < best["val"]:
            best = {"val": v, "epoch": ep + 1,
                    "state": {k: t.detach().cpu().clone() for k, t in model.state_dict().items()}}
    man["best_val_mse"] = best["val"]; man["best_epoch"] = best["epoch"]

    # ---- B-5: restore the validation-selected checkpoint ----------------
    if best["state"] is not None:
        model.load_state_dict(best["state"])

    # ---- B-6: evaluate Test ONCE and persist predictions + targets ------
    model.eval()
    P, Y, O = [], [], []
    with torch.no_grad():
        for xb, yb, ob in dl_te:
            P.append(model(xb.to(dev)).cpu().numpy())
            Y.append(yb.numpy()); O.append(np.asarray(ob))
    pred = np.concatenate(P); targ = np.concatenate(Y); orig = np.concatenate(O)
    err = pred - targ
    man["test_mse_all"] = float(np.mean(err ** 2))
    man["test_mae_all"] = float(np.mean(np.abs(err)))
    man["n_test_origins"] = int(pred.shape[0])

    tag = f"r1b__L{L}__rep{a.repetition}"
    np.savez_compressed(os.path.join(a.out, f"pred_{tag}.npz"),
                        pred=pred.astype(np.float32), target=targ.astype(np.float32),
                        target_start_row=orig.astype(np.int32),
                        L=np.int32(L), seed=np.int32(a.repetition),
                        var_cols=np.array(cols), model=np.array("r1b_miflu"),
                        profile=np.array("author_966"), containment=np.array("strict"),
                        space=np.array("standardized_train_fit_z"),
                        checkpoint_selection=np.array("best_validation_mse"),
                        track=np.array("R1-B"))
    # ── LOCKED CHECKPOINT PATH (mandatory) ────────────────────────────────
    # The authorization forbids saving the full 331 MB state_dict per fit and
    # requires the locked path only: store the TRAINABLE tensors and write a
    # sidecar naming the frozen keys. The frozen backbone is bit-identically
    # reconstructible from the pinned 'gpt2' snapshot, and the sidecar lets the
    # reload be PROVEN rather than trusted. Saves ~329 MB per fit.
    frozen = sorted(n for n, prm in model.named_parameters() if not prm.requires_grad)
    keep = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()
            if k not in set(frozen)}
    ck_path = os.path.join(a.out, f"ckpt_{tag}.pth")
    side_path = os.path.join(a.out, f"ckpt_{tag}.frozen_keys.json")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "..", "storage"))
        import storage_guard as SG
        ck_bytes = SG.atomic_save_torch(ck_path, keep)
        _atomic = True
    except Exception as e:
        print(f"[r1b] storage_guard unavailable ({e}); falling back to torch.save")
        torch.save(keep, ck_path); ck_bytes = os.path.getsize(ck_path); _atomic = False
    json.dump({"frozen_keys": frozen, "n_stored_tensors": len(keep),
               "n_frozen_tensors": len(frozen),
               "asset": "gpt2 (the pinned snapshot the author's code uses)",
               "note": "frozen backbone tensors are reconstructed from the pretrained "
                       "snapshot and intentionally not stored"},
              open(side_path, "w"), indent=2)
    man["checkpoint_bytes"] = ck_bytes
    man["checkpoint_path"] = os.path.relpath(ck_path)
    man["frozen_keys_sidecar"] = os.path.relpath(side_path)
    man["n_stored_tensors"] = len(keep)
    man["n_frozen_tensors"] = len(frozen)
    man["atomic_write_used"] = _atomic
    print(f"[r1b] locked checkpoint: {ck_bytes:,} bytes "
          f"({len(keep)} stored / {len(frozen)} frozen) atomic={_atomic}")
    # ── reload verification: the locked checkpoint must reproduce predictions ─
    try:
        m2 = R1BCorrectedMIFlu(configs, dev, text_embeddings=text).to(dev)
        m2.load_state_dict(keep, strict=False)
        m2.eval()
        with torch.no_grad():
            for xb, _yb, _ob in dl_te:
                y2 = m2(xb.to(dev)).cpu().numpy(); break
        reload_max = float(np.abs(y2 - pred[:y2.shape[0]]).max())
        man["checkpoint_reload_max_abs_diff"] = reload_max
        man["checkpoint_reload_ok"] = bool(reload_max < 1e-6)
        print(f"[r1b] locked-checkpoint reload max|d| = {reload_max:.3e} "
              f"-> {'OK' if reload_max < 1e-6 else 'MISMATCH'}")
    except Exception as e:
        man["checkpoint_reload_ok"] = False
        man["checkpoint_reload_error"] = str(e)
        print(f"[r1b] reload verification failed: {e}")
    json.dump(man, open(os.path.join(a.out, f"manifest_{tag}.json"), "w"), indent=2)
    print(f"[r1b] test mse_all={man['test_mse_all']:.6f} mae_all={man['test_mae_all']:.6f} "
          f"origins={pred.shape[0]}")
    print(f"[r1b] wrote {a.out}/pred_{tag}.npz + ckpt + manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())