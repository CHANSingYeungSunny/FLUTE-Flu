"""
train_regional_baseline.py — GPT4TS Baseline (Regional, Unimodal)
==================================================================
US-Region: 10 HHS regions, T=20, htext=None (no text prompt).
Metrics: RMSE/PCC on DE-NORMALIZED data (Section V-B).
Reference: Table IV, Table VI, Section V-B, V-C.
"""

import torch, torch.nn as nn, numpy as np, pandas as pd, os, sys, time
from datetime import datetime
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(__file__))
from miflu_model import MIFlu

# ── Config (Table IV: Regional) ────────────────────────────────────────────
CONFIG = {
    "T": 20, "L_list": [2, 3, 5, 10, 13, 15, 20], "N": 10,
    "Lp": 4, "S": 2, "K": 4, "lora_r": 4, "D": 768,
    "batch_size": 32, "learning_rate": 0.0005, "epochs": 50,
    "num_repetitions": 10,
}

HHS_COLS = [f"HHS{i}" for i in range(1, 11)]

BASE_DIR = os.path.dirname(__file__)
LOG_PATH = os.path.join(BASE_DIR, "data", "training_regional_baseline_log.txt")
RESULTS_PATH = os.path.join(BASE_DIR, "data", "results_regional_baseline.csv")
DATA_PATH = os.path.join(BASE_DIR, "data", "us_region_raw.csv")

_log_file = None

def log_init(path):
    global _log_file
    os.makedirs(os.path.dirname(path), exist_ok=True)
    _log_file = open(path, "w", encoding="utf-8", buffering=1)

def log(msg=""):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    if _log_file: _log_file.write(line + "\n")

def log_close():
    if _log_file: _log_file.close()

# ── Data ────────────────────────────────────────────────────────────────────

def load_and_normalize():
    df = pd.read_csv(DATA_PATH)
    df = df[(df['epiweek'] >= 199740) & (df['epiweek'] <= 202018)]
    data = df[HHS_COLS].values.astype(np.float32)
    n = len(data)
    t_end, v_end = int(n * 0.50), int(n * 0.50) + int(n * 0.10)
    train_mean = data[:t_end].mean(axis=0, keepdims=True)
    train_std  = data[:t_end].std(axis=0, keepdims=True) + 1e-8
    data_norm = (data - train_mean) / train_std

    # Build windows
    X_all, Y_all, splits = [], [], []
    for L in CONFIG["L_list"]:
        T = CONFIG["T"]
        nw = n - T - L + 1
        X = np.zeros((nw, CONFIG["N"], T), dtype=np.float32)
        Y = np.zeros((nw, CONFIG["N"], L), dtype=np.float32)
        sp = np.zeros(nw, dtype=np.int8)
        for i in range(nw):
            X[i] = data_norm[i:i+T].T
            Y[i] = data_norm[i+T:i+T+L].T
            sp[i] = 0 if (i+T) < t_end else (1 if (i+T) < v_end else 2)
        X_all.append(X); Y_all.append(Y); splits.append(sp)

    log(f"Data: {n} total | Train={t_end} | Val={v_end-t_end} | Test={n-v_end}")
    return {"X_all": X_all, "Y_all": Y_all, "splits": splits,
            "L_list": CONFIG["L_list"],
            "train_mean": train_mean, "train_std": train_std}

# ── Training ────────────────────────────────────────────────────────────────

def train_epoch(model, loader, opt, crit, dev):
    model.train()
    loss_sum = 0.0
    for bx, by in loader:
        bx, by = bx.to(dev), by.to(dev)
        opt.zero_grad()
        yh, _, _ = model(bx, htext=None)
        L = crit(yh, by); L.backward(); opt.step()
        loss_sum += L.item() * bx.size(0)
    return loss_sum / len(loader.dataset)

@torch.no_grad()
def evaluate_regional(model, loader, dev, train_mean, train_std):
    """RMSE/PCC on DE-NORMALIZED data (Section V-B)."""
    model.eval()
    all_preds, all_targets = [], []
    for bx, by in loader:
        bx = bx.to(dev)
        yh, _, _ = model(bx, htext=None)
        all_preds.append(yh.cpu().numpy())
        all_targets.append(by.numpy())
    p_norm = np.concatenate(all_preds)    # (samples, N, L)
    t_norm = np.concatenate(all_targets)  # (samples, N, L)

    # De-normalize: reshape to (1, N, 1) for broadcasting with (B, N, L)
    N = p_norm.shape[1]
    mean = train_mean.reshape(1, N, 1)
    std  = train_std.reshape(1, N, 1)
    p_raw = p_norm * std + mean
    t_raw = t_norm * std + mean

    # RMSE: per Eq.(5), average over all elements
    rmse = np.sqrt(np.mean((p_raw - t_raw) ** 2))
    # PCC: per Eq.(6), flatten to 1D vectors
    p_flat = p_raw.reshape(-1)
    t_flat = t_raw.reshape(-1)
    p_mean, t_mean = p_flat.mean(), t_flat.mean()
    numerator = np.sum((p_flat - p_mean) * (t_flat - t_mean))
    denominator = np.sqrt(np.sum((p_flat - p_mean)**2) * np.sum((t_flat - t_mean)**2))
    pcc = numerator / (denominator + 1e-8)
    return rmse, pcc

def train_L(data_dict, L_idx, config, device):
    L = config["L_list"][L_idx]
    X = data_dict["X_all"][L_idx]
    Y = data_dict["Y_all"][L_idx]
    sp = data_dict["splits"][L_idx]
    Xt, Yt = X[sp==0], Y[sp==0]
    Xv, Yv = X[sp==1], Y[sp==1]
    Xte, Yte = X[sp==2], Y[sp==2]

    log(f"  L={L}: train={len(Xt)} val={len(Xv)} test={len(Xte)} windows")

    tl = DataLoader(TensorDataset(torch.from_numpy(Xt), torch.from_numpy(Yt)),
                    batch_size=config["batch_size"], shuffle=True)
    vl = DataLoader(TensorDataset(torch.from_numpy(Xv), torch.from_numpy(Yv)),
                    batch_size=config["batch_size"], shuffle=False)
    el = DataLoader(TensorDataset(torch.from_numpy(Xte), torch.from_numpy(Yte)),
                    batch_size=config["batch_size"], shuffle=False)

    model = MIFlu(N=config["N"], T=config["T"], L=L, Lp=config["Lp"],
                  S=config["S"], K=config["K"], lora_r=config["lora_r"], device=device)
    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad],
                           lr=config["learning_rate"])
    crit = nn.MSELoss()
    for ep in range(config["epochs"]):  # Fixed 50 epochs per Table IV — no early stopping
        t0 = time.time()
        tl_loss = train_epoch(model, tl, opt, crit, device)
        v_rmse, v_pcc = evaluate_regional(model, vl, device,
                                          data_dict["train_mean"], data_dict["train_std"])
        dt = time.time() - t0
        log(f"    ep {ep+1:2d}/{config['epochs']} | train_loss={tl_loss:.6f} | val_rmse={v_rmse:.1f} val_pcc={v_pcc:.4f} | {dt:.1f}s | GPU={torch.cuda.memory_allocated()/1e9:.2f}GB" if device=="cuda" else f"    ep {ep+1:2d} | loss={tl_loss:.6f} | rmse={v_rmse:.1f} pcc={v_pcc:.4f}")
    t_rmse, t_pcc = evaluate_regional(model, el, device,
                                      data_dict["train_mean"], data_dict["train_std"])
    log(f"  L={L} DONE: RMSE={t_rmse:.1f} PCC={t_pcc:.4f}")
    del model; torch.cuda.empty_cache() if device=="cuda" else None
    return {"L": L, "test_rmse": t_rmse, "test_pcc": t_pcc}

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    log_init(LOG_PATH)
    log("=" * 60)
    log("  MIFlu Regional ILI Training (US-Region)")
    log("=" * 60)
    log(f"  Device: {device} {'(' + torch.cuda.get_device_name(0) + ')' if device=='cuda' else ''}")
    log(f"  Config: T={CONFIG['T']}, L={CONFIG['L_list']}, N={CONFIG['N']}")
    log(f"          K={CONFIG['K']}, Lp={CONFIG['Lp']}, S={CONFIG['S']}, lora_r={CONFIG['lora_r']}")
    log(f"          batch={CONFIG['batch_size']}, lr={CONFIG['learning_rate']}, epochs={CONFIG['epochs']}, reps={CONFIG['num_repetitions']}")
    log()

    data_dict = load_and_normalize(); log()
    all_rows, t_start = [], time.time()

    for L_idx in range(len(CONFIG["L_list"])):
        L = CONFIG["L_list"][L_idx]
        log(f"{'─'*50}"); log(f"  HORIZON L={L}"); log(f"{'─'*50}")
        L_reps = []
        for rep in range(CONFIG["num_repetitions"]):
            log(f"  [L={L}] Rep {rep+1}/{CONFIG['num_repetitions']} ...")
            r = train_L(data_dict, L_idx, CONFIG, device); L_reps.append(r)
            all_rows.append({"L": L, "rep": rep+1, "rmse": r["test_rmse"], "pcc": r["test_pcc"]})
            pd.DataFrame(all_rows).to_csv(RESULTS_PATH, index=False)
        avg_rmse = np.mean([r["test_rmse"] for r in L_reps])
        avg_pcc = np.mean([r["test_pcc"] for r in L_reps])
        log(f"  [L={L}] FINAL: RMSE={avg_rmse:.1f}+-{np.std([r['test_rmse'] for r in L_reps]):.1f}  PCC={avg_pcc:.4f}"); log()

    df = pd.DataFrame(all_rows)
    summary = df.groupby("L").agg(rmse=("rmse","mean"), pcc=("pcc","mean"))
    log("=" * 60); log("  FINAL RESULTS (10-rep average)"); log("=" * 60)
    log(f"  {'L':>6s}  {'RMSE':>10s}  {'PCC':>10s}"); log("  " + "-" * 30)
    for L in CONFIG["L_list"]:
        r = summary.loc[L]; log(f"  {L:>6d}  {r['rmse']:>10.1f}  {r['pcc']:>10.4f}")
    log("=" * 60)
    log(f"  Total time: {(time.time()-t_start)/60:.1f} min"); log(f"  Results: {RESULTS_PATH}")
    log_close()
    return summary

if __name__ == "__main__":
    main()
