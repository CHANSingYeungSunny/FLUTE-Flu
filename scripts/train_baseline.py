"""
train_baseline.py — GPT4TS Baseline (Unimodal)
================================================
GPT4TS: same architecture as MIFlu but WITHOUT text prompt embeddings.
Used as baseline in Table V and as "MIFlu w/o multimodality" in Table VIII.

Reference: MIFlu paper, Table V, Table VIII. GPT4TS paper [9].
"""

import torch, torch.nn as nn, numpy as np, pandas as pd, os, sys, time
from datetime import datetime
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(__file__))
from miflu_model import MIFlu

CONFIG = {
    "T": 104, "L_list": [24, 36, 48, 60], "N": 7,
    "Lp": 24, "S": 2, "K": 6, "lora_r": 4, "D": 768,
    "batch_size": 16, "learning_rate": 0.0005, "epochs": 20,
    "num_repetitions": 10,
}

VAR_COLS = [
    "% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
    "ILITOTAL", "NUM. OF PROVIDERS", "OT",
]

BASE_DIR = os.path.dirname(__file__)
LOG_PATH = os.path.join(BASE_DIR, "data", "training_baseline_log.txt")
RESULTS_PATH = os.path.join(BASE_DIR, "data", "results_baseline.csv")
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "raw", "national_illness_raw.csv")

_log_file = None

def log_init(path):
    global _log_file
    os.makedirs(os.path.dirname(path), exist_ok=True)
    _log_file = open(path, "w", encoding="utf-8", buffering=1)

def log(msg=""):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    if _log_file:
        _log_file.write(line + "\n")

def log_close():
    if _log_file:
        _log_file.close()

def load_and_normalize():
    df = pd.read_csv(DATA_PATH)
    # Full 2002-2021 data — distribution shift makes text embeddings valuable
    data = df[VAR_COLS].values.astype(np.float32)
    n = len(data)
    t_end, v_end = int(n * 0.70), int(n * 0.70) + int(n * 0.10)
    train_mean = data[:t_end].mean(axis=0, keepdims=True)
    train_std  = data[:t_end].std(axis=0, keepdims=True) + 1e-8
    data_norm = (data - train_mean) / train_std
    log(f"Data: {n} total | Train={t_end} | Val={v_end-t_end} | Test={n-v_end}")
    return {"data_norm": data_norm, "train_end": t_end, "val_end": v_end}

def build_windows(data_norm, T, L, train_end, val_end):
    total = data_norm.shape[0]
    nw = total - T - L + 1
    X = np.zeros((nw, CONFIG["N"], T), dtype=np.float32)
    Y = np.zeros((nw, CONFIG["N"], L), dtype=np.float32)
    splits = np.zeros(nw, dtype=np.int8)
    for i in range(nw):
        X[i] = data_norm[i:i+T].T
        Y[i] = data_norm[i+T:i+T+L].T
        splits[i] = 0 if (i+T) < train_end else (1 if (i+T) < val_end else 2)
    return (X[splits==0], Y[splits==0], X[splits==1], Y[splits==1], X[splits==2], Y[splits==2])

def train_epoch(model, loader, opt, crit, dev):
    model.train()
    loss_sum = 0.0
    for bx, by in loader:
        bx, by = bx.to(dev), by.to(dev)
        opt.zero_grad()
        yh, _, _ = model(bx, htext=None)
        L = crit(yh, by)
        L.backward()
        opt.step()
        loss_sum += L.item() * bx.size(0)
    return loss_sum / len(loader.dataset)

@torch.no_grad()
def evaluate(model, loader, crit, dev, diag=False):
    model.eval()
    preds, targets = [], []
    for i, (bx, by) in enumerate(loader):
        bx = bx.to(dev)
        yh, _, _ = model(bx, htext=None)
        preds.append(yh.cpu().numpy())
        targets.append(by.numpy())
        if diag and i == 0:
            # Diagnostic: first batch stats
            yy = yh.cpu().numpy()
            tt = by.numpy()
            log(f"    [DIAG] y_pred: mean={yy.mean():.4f} std={yy.std():.4f} min={yy.min():.4f} max={yy.max():.4f}")
            log(f"    [DIAG] y_true: mean={tt.mean():.4f} std={tt.std():.4f} min={tt.min():.4f} max={tt.max():.4f}")
    p = np.concatenate(preds); t = np.concatenate(targets)
    # Shape: (samples, N=7, L)
    # MSE_AllVars: average across all 7 variables and all L time steps (Table VIII)
    mse_all = np.mean((p-t)**2)
    mae_all = np.mean(np.abs(p-t))
    # MSE_ILITotal: only Var 5 (ILITOTAL, index 4) — comparable to Table V
    mse_ili = np.mean((p[:,4,:]-t[:,4,:])**2)
    mae_ili = np.mean(np.abs(p[:,4,:]-t[:,4,:]))
    if diag:
        log(f"    [DIAG] MSE_AllVars={mse_all:.6f} MSE_ILITotal={mse_ili:.6f}")
    return mse_all, mae_all, mse_ili, mae_ili

def train_L(data_dict, L, config, device):
    Xt, Yt, Xv, Yv, Xte, Yte = build_windows(
        data_dict["data_norm"], config["T"], L,
        data_dict["train_end"], data_dict["val_end"])
    log(f"  L={L}: train={len(Xt)} val={len(Xv)} test={len(Xte)} windows")
    tl = DataLoader(TensorDataset(torch.from_numpy(Xt), torch.from_numpy(Yt)),
                    batch_size=config["batch_size"], shuffle=True)
    vl = DataLoader(TensorDataset(torch.from_numpy(Xv), torch.from_numpy(Yv)),
                    batch_size=config["batch_size"], shuffle=False)
    el = DataLoader(TensorDataset(torch.from_numpy(Xte), torch.from_numpy(Yte)),
                    batch_size=config["batch_size"], shuffle=False)
    model = MIFlu(N=config["N"], T=config["T"], L=L, Lp=config["Lp"],
                  S=config["S"], K=config["K"], lora_r=config["lora_r"], device=device)
    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=config["learning_rate"])
    crit = nn.MSELoss()
    for ep in range(config["epochs"]):  # Fixed 20 epochs per Table IV — no early stopping
        t0 = time.time()
        tl_loss = train_epoch(model, tl, opt, crit, device)
        v_mse_all, v_mae_all, v_mse_ili, v_mae_ili = evaluate(model, vl, crit, device)
        dt = time.time() - t0
        log(f"    ep {ep+1:2d}/{config['epochs']} | train_loss={tl_loss:.6f} | val_mse={v_mse_all:.6f}(All) {v_mse_ili:.4f}(ILI) | val_mae={v_mae_all:.6f} | {dt:.1f}s | GPU={torch.cuda.memory_allocated()/1e9:.2f}GB" if device=="cuda" else f"    ep {ep+1:2d}/{config['epochs']} | train_loss={tl_loss:.6f} | val_mse={v_mse_all:.6f}(All) {v_mse_ili:.4f}(ILI) | val_mae={v_mae_all:.6f} | {dt:.1f}s")
    t_mse_all, t_mae_all, t_mse_ili, t_mae_ili = evaluate(model, el, crit, device, diag=(L==CONFIG["L_list"][0]))
    # Split test into pre-COVID (first half) vs COVID (second half) for diagnosis
    el_pre = DataLoader(TensorDataset(torch.from_numpy(Xte[:len(Xte)//2]), torch.from_numpy(Yte[:len(Yte)//2])),
                        batch_size=config["batch_size"], shuffle=False)
    t_mse_pre, _, _, _ = evaluate(model, el_pre, crit, device)
    log(f"  L={L} DONE: test_mse={t_mse_all:.6f}(All) {t_mse_ili:.4f}(ILI) preCOVID_mse={t_mse_pre:.6f} test_mae={t_mae_all:.6f}")
    del model; torch.cuda.empty_cache() if device=="cuda" else None
    return {"L": L, "test_mse_all": t_mse_all, "test_mae_all": t_mae_all,
            "test_mse_ili": t_mse_ili, "test_mae_ili": t_mae_ili}

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    log_init(LOG_PATH)
    log("=" * 60)
    log("  GPT4TS Baseline — Unimodal (no text prompt)")
    log("=" * 60)
    log(f"  Device: {device} {'(' + torch.cuda.get_device_name(0) + ')' if device=='cuda' else ''}")
    log(f"  Config: T={CONFIG['T']}, L={CONFIG['L_list']}")
    log(f"          K={CONFIG['K']}, Lp={CONFIG['Lp']}, S={CONFIG['S']}, lora_r={CONFIG['lora_r']}")
    log(f"          batch={CONFIG['batch_size']}, lr={CONFIG['learning_rate']}, epochs={CONFIG['epochs']}, reps={CONFIG['num_repetitions']}")
    log()
    data_dict = load_and_normalize(); log()
    all_rows, t_start = [], time.time()
    for L in CONFIG["L_list"]:
        log(f"{'─'*50}"); log(f"  HORIZON L={L}"); log(f"{'─'*50}")
        L_reps = []
        for rep in range(CONFIG["num_repetitions"]):
            log(f"  [L={L}] Rep {rep+1}/{CONFIG['num_repetitions']} ...")
            r = train_L(data_dict, L, CONFIG, device); L_reps.append(r)
            all_rows.append({"L": L, "rep": rep+1,
                "mse_all": r["test_mse_all"], "mae_all": r["test_mae_all"],
                "mse_ili": r["test_mse_ili"], "mae_ili": r["test_mae_ili"]})
            pd.DataFrame(all_rows).to_csv(RESULTS_PATH, index=False)
        avg_mse_all = np.mean([r["test_mse_all"] for r in L_reps])
        avg_mse_ili = np.mean([r["test_mse_ili"] for r in L_reps])
        log(f"  [L={L}] FINAL: MSE_AllVars={avg_mse_all:.6f} MSE_ILITotal={avg_mse_ili:.6f}"); log()
    df = pd.DataFrame(all_rows)
    summary = df.groupby("L").agg(
        mse_all=("mse_all","mean"), mse_ili=("mse_ili","mean"),
        mae_all=("mae_all","mean"), mae_ili=("mae_ili","mean"))
    log("=" * 60); log("  FINAL RESULTS (10-rep average)"); log("=" * 60)
    log(f"  {'L':>6s}  {'MSE_All':>10s}  {'MSE_ILI':>10s}  {'MAE_All':>10s}")
    log("  " + "-" * 46)
    for L in CONFIG["L_list"]:
        r = summary.loc[L]; log(f"  {L:>6d}  {r['mse_all']:>10.6f}  {r['mse_ili']:>10.6f}  {r['mae_all']:>10.6f}")
    log(f"  {'avg':>6s}  {summary['mse_all'].mean():>10.6f}  {summary['mse_ili'].mean():>10.6f}  {summary['mae_all'].mean():>10.6f}")
    log(f"  → MSE_AllVars (Table VIII ablation): {summary['mse_all'].mean():.4f}")
    log(f"  → MSE_ILITotal (Table V GPT4TS):    {summary['mse_ili'].mean():.4f}")
    log("=" * 60)
    log(f"  Total time: {(time.time()-t_start)/60:.1f} min"); log(f"  Results: {RESULTS_PATH}")
    log_close()
    return summary

if __name__ == "__main__":
    main()
