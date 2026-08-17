"""
train_miflu.py — Full MIFlu (Multimodal)
==========================================
Full MIFlu with text prompt embeddings via GPT2 text embedder.
This is the main model from the paper — Table V.

Reference: MIFlu paper, Section IV-A, IV-C, Table V.
"""

import torch, torch.nn as nn, numpy as np, pandas as pd, os, sys, time, argparse
from datetime import datetime
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(__file__))
from miflu_model import MIFlu
from textual_embedder import TextualInputEmbedder, build_prompt

# ── Authoritative hyperparameters (match the essay / Table IV) ──────────────────
# Paper protocol (MIFlu_paper.md): T=104, L ∈ {24,36,48,60} evaluated
# SEPARATELY as four independent runs (NOT a single rolling L=52 walk-forward).
# Each L is trained independently with `num_repetitions` repeats; the checkpoint
# and result table are stored per L. The L=52 walk-forward path is isolated under
# scripts/chattime_variant/ and is NOT the default MIFlu deliverable.
CONFIG = {
    "T": 104, "L_list": [24, 36, 48, 60], "N": 7,
    "Lp": 24, "S": 2, "K": 6, "lora_r": 4, "D": 768,
    "batch_size": 16, "learning_rate": 0.0005, "epochs": 20,
    "num_repetitions": 10,
}

# N=7 channel list (RESTORED per ChatTime-protocol restructure).
# Channel order matches the MIFlu paper Table X template.
#   OT = num_patients（CDC 总就诊人次/分母，全量未缩放）.
#   NOTE: 论文 Table X 仅称 "'OT' feature for long-term forecasting task"，未给公式、
#   未称黑箱。OT=num_patients（全量）是基于 Fig 2(a) 图表量级反推出的实现选择，
#   非论文明文定义；训练代码从未做 /100 缩放；StandardScaler 使常数缩放不影响训练。
VAR_COLS = [
    "% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
    "ILITOTAL", "NUM. OF PROVIDERS", "OT",
]

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(BASE_DIR)
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_PATH = os.path.join(PROJECT_ROOT, "data", f"training_miflu_log_{TS}.txt")
# Paper-protocol output naming: per-horizon results use the explicit suffix
# `_paper_protocol` so they can never be confused with the L=52 walk-forward
# variant (scripts/chattime_variant/ -> results_chattime_walkforward_L52.csv).
RESULTS_PATH = os.path.join(PROJECT_ROOT, "data",
                            f"results_miflu_paper_protocol_{TS}.csv")
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "national_illness_raw.csv")
CKPT_DIR = os.path.join(PROJECT_ROOT, "checkpoints")

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
    return {"data_norm": data_norm, "train_end": t_end, "val_end": v_end,
            "train_df": df.iloc[:t_end], "train_mean": train_mean, "train_std": train_std}

def build_windows(data_norm, T, L, train_end, val_end):
    """Build sliding train/val/test windows with explicit split labels.

    Returns (X_train, Y_train, X_val, Y_val, X_test, Y_test, split_info) where
    `split_info` is a dict carrying the per-window target-start index and its
    split label (0=train,1=val,2=test). The test set's target-start indices are
    guaranteed to begin strictly AFTER `val_end` so no test target was ever seen
    during fitting (see docs/leakage_audit_report.md). This metadata is also used
    to attach a `split` column to the prediction output CSV.
    """
    total = data_norm.shape[0]
    nw = total - T - L + 1
    X = np.zeros((nw, CONFIG["N"], T), dtype=np.float32)
    Y = np.zeros((nw, CONFIG["N"], L), dtype=np.float32)
    splits = np.zeros(nw, dtype=np.int8)
    target_starts = np.arange(nw) + T  # absolute index of the first target week
    for i in range(nw):
        X[i] = data_norm[i:i+T].T
        Y[i] = data_norm[i+T:i+T+L].T
        # Target-based split: a window is assigned to train/val/test according to
        # the START INDEX of its TARGET (i+T), not its input history. The lower
        # boundary is INCLUSIVE so that a window whose target starts exactly at
        # `val_end` is assigned to VAL, never to TEST. Consequently every TEST
        # window's target start is STRICTLY > val_end, guaranteeing no test target
        # week was ever visible during fitting. (Sliding-window inputs may span the
        # train/val or val/test boundary — this is standard time-series CV and
        # does NOT leak the target, which lives in the assigned split only.)
        target_start = i + T
        splits[i] = 0 if target_start < train_end else (1 if target_start <= val_end else 2)
    split_info = {
        "target_starts": target_starts,
        "splits": splits,
        "train_end": train_end,
        "val_end": val_end,
        "train_idx": np.where(splits == 0)[0],
        "val_idx": np.where(splits == 1)[0],
        "test_idx": np.where(splits == 2)[0],
    }
    return (X[splits==0], Y[splits==0], X[splits==1], Y[splits==1],
            X[splits==2], Y[splits==2], split_info)

def train_epoch(model, loader, opt, crit, dev, prompt_cache, train_mean, train_std, clip=1.0):
    model.train()
    loss_sum = 0.0
    for bx, by in loader:
        bx, by = bx.to(dev), by.to(dev)
        bsz = bx.size(0)
        ht = prompt_cache.expand(bsz, -1, -1) if prompt_cache.shape[0] == 1 else prompt_cache[:bsz]
        opt.zero_grad()
        # yh_rev: StandardScaler space (metrics/loss) ; yh_phys: physical (unused in train)
        yh_rev, _, _, _ = model(bx, htext=ht, train_mean=train_mean, train_std=train_std)
        L = crit(yh_rev, by)
        if not torch.isfinite(L):
            log("    [WARN] non-finite loss — skipping this batch (NaN-rep discipline)")
            opt.zero_grad()
            continue
        L.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
        opt.step()
        loss_sum += L.item() * bsz
    return loss_sum / len(loader.dataset)

@torch.no_grad()
def evaluate(model, loader, crit, dev, prompt_cache, train_mean, train_std, diag=False):
    model.eval()
    preds, targets = [], []
    for i, (bx, by) in enumerate(loader):
        bx = bx.to(dev)
        bsz = bx.size(0)
        ht = prompt_cache.expand(bsz, -1, -1) if prompt_cache.shape[0] == 1 else prompt_cache[:bsz]
        # Metrics MUST be in StandardScaler space (Section V-B): yh_rev vs Y (StdScaler target)
        yh_rev, _, _, _ = model(bx, htext=ht, train_mean=train_mean, train_std=train_std)
        preds.append(yh_rev.cpu().numpy()); targets.append(by.numpy())
        if diag and i == 0:
            yy = yh_rev.cpu().numpy(); tt = by.numpy()
            log(f"    [DIAG] y_pred(StdScaler): mean={yy.mean():.4f} std={yy.std():.4f} min={yy.min():.4f} max={yy.max():.4f}")
            log(f"    [DIAG] y_true(StdScaler): mean={tt.mean():.4f} std={tt.std():.4f} min={tt.min():.4f} max={tt.max():.4f}")
    p = np.concatenate(preds); t = np.concatenate(targets)
    mse_all = np.mean((p-t)**2); mae_all = np.mean(np.abs(p-t))
    mse_ili = np.mean((p[:,4,:]-t[:,4,:])**2); mae_ili = np.mean(np.abs(p[:,4,:]-t[:,4,:]))
    # Pearson correlation on ILITOTAL (channel 4) across all test windows.
    gt_ili = t[:, 4, :].reshape(-1)
    pr_ili = p[:, 4, :].reshape(-1)
    if np.std(gt_ili) > 0 and np.std(pr_ili) > 0:
        pcc_ili = float(np.corrcoef(gt_ili, pr_ili)[0, 1])
    else:
        pcc_ili = float("nan")
    if diag:
        log(f"    [DIAG] MSE_AllVars={mse_all:.6f} MSE_ILITotal={mse_ili:.6f} PCC_ILI={pcc_ili:.4f}")
    # Return raw ILITOTAL (channel 4) series for the per-horizon prediction CSV.
    # Shapes: (n_windows, L) — caller assigns the correct `split` label.
    return mse_all, mae_all, mse_ili, mae_ili, pcc_ili, t[:, 4, :], p[:, 4, :]

def train_L(data_dict, L, config, device, prompt_cache, seed=42):
    """Train ONE repetition for horizon L. Returns metrics + the per-rep checkpoint
    path + the minimum validation MSE observed across epochs (for best-rep selection)."""
    torch.manual_seed(seed + L)   # reproducible per-horizon init
    np.random.seed(seed + L)
    tm = torch.from_numpy(data_dict["train_mean"].astype(np.float32))
    ts = torch.from_numpy(data_dict["train_std"].astype(np.float32))
    Xt, Yt, Xv, Yv, Xte, Yte, split_info = build_windows(
        data_dict["data_norm"], config["T"], L,
        data_dict["train_end"], data_dict["val_end"])
    log(f"  L={L}: train={len(Xt)} val={len(Xv)} test={len(Xte)} windows")
    # Leakage guard: every test window's target-start index must exceed val_end,
    # i.e. no test target was visible during fit. Asserted here and in the test
    # suite (tests/test_leakage_audit.py).
    test_target_starts = split_info["target_starts"][split_info["test_idx"]]
    assert int(test_target_starts.min()) > data_dict["val_end"], (
        f"LEAKAGE GUARD FAILED: test target starts at "
        f"{int(test_target_starts.min())} but val_end={data_dict['val_end']}")
    log(f"  L={L}: leakage guard OK — min test target-start index "
        f"= {int(test_target_starts.min())} > val_end={data_dict['val_end']}")
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
    best_val = float('inf')
    for ep in range(config["epochs"]):  # Fixed 20 epochs per Table IV — no early stopping
        t0 = time.time()
        tl_loss = train_epoch(model, tl, opt, crit, device, prompt_cache, tm, ts, clip=1.0)
        v_mse_all, v_mae_all, v_mse_ili, v_mae_ili, _, _, _ = evaluate(model, vl, crit, device, prompt_cache, tm, ts)
        dt = time.time() - t0
        best_val = min(best_val, v_mse_all)
        log(f"    ep {ep+1:2d}/{config['epochs']} | train_loss={tl_loss:.6f} | val_mse={v_mse_all:.6f}(All) {v_mse_ili:.4f}(ILI) | val_mae={v_mae_all:.6f} | {dt:.1f}s | GPU={torch.cuda.memory_allocated()/1e9:.2f}GB" if device=="cuda" else f"    ep {ep+1:2d}/{config['epochs']} | train_loss={tl_loss:.6f} | val_mse={v_mse_all:.6f}(All) {v_mse_ili:.4f}(ILI) | val_mae={v_mae_all:.6f} | {dt:.1f}s")
    t_mse_all, t_mae_all, t_mse_ili, t_mae_ili, t_pcc_ili, t_gt_ili, t_pr_ili = evaluate(model, el, crit, device, prompt_cache, tm, ts, diag=(L==CONFIG["L_list"][0]))
    # ── NaN-rep discipline: discard reps whose test prediction is non-finite ──
    if not (np.isfinite(t_mse_all) and np.isfinite(t_mse_ili) and np.isfinite(t_pcc_ili)):
        log(f"  [WARN] L={L} rep seed={seed} produced non-finite metrics — DISCARDED (NaN-rep)")
        del model; torch.cuda.empty_cache() if device=="cuda" else None
        return {"L": L, "test_mse_all": np.nan, "test_mae_all": np.nan,
                "test_mse_ili": np.nan, "test_mae_ili": np.nan, "test_pcc_ili": np.nan,
                "rep_ckpt": None, "best_val": np.nan, "seed": seed, "discarded": True}
    log(f"  L={L} DONE: test_mse={t_mse_all:.6f}(All) {t_mse_ili:.4f}(ILI) test_mae={t_mae_all:.6f} pcc={t_pcc_ili:.4f}")
    # per-rep temp checkpoint; main() keeps only the best-val-loss rep as best_miflu_L{L}.pth
    os.makedirs(CKPT_DIR, exist_ok=True)
    rep_ckpt = os.path.join(CKPT_DIR, f"_rep_miflu_L{L}_seed{seed}.pth")
    torch.save(model.state_dict(), rep_ckpt)
    del model; torch.cuda.empty_cache() if device=="cuda" else None
    return {"L": L, "test_mse_all": t_mse_all, "test_mae_all": t_mae_all,
            "test_mse_ili": t_mse_ili, "test_mae_ili": t_mae_ili, "test_pcc_ili": t_pcc_ili,
            "test_gt_ili": t_gt_ili, "test_pr_ili": t_pr_ili,
            "rep_ckpt": rep_ckpt, "best_val": best_val, "seed": seed, "discarded": False}


def export_prediction_csv(data_dict, L, config, device, prompt_cache,
                           best_rep, out_dir):
    """Write a per-horizon prediction CSV with an explicit `split` column.

    The CSV is produced from the BEST-VAL-LOSS rep checkpoint so the plotted
    curve matches the reported metrics. Every row carries its split label
    (train/val/test) and the absolute week index `abs_week` so figure scripts
    can align predictions to ground truth in time. Figure scripts MUST filter
    to `split == 'test'` only (asserted in code).

    Columns: split, abs_week, step (0..L-1), ground_truth_ili, prediction_ili
    """
    import torch.utils.data as _td
    tm = torch.from_numpy(data_dict["train_mean"].astype(np.float32))
    ts = torch.from_numpy(data_dict["train_std"].astype(np.float32))
    # Rebuild windows to retrieve the global split layout.
    Xt, Yt, Xv, Yv, Xte, Yte, sinfo = build_windows(
        data_dict["data_norm"], config["T"], L,
        data_dict["train_end"], data_dict["val_end"])
    # Map each target-start index -> split label (target_starts[k] is the global
    # target start of window k; train/val/test_idx are window indices).
    split_of_idx = {int(sinfo["target_starts"][k]): "train" for k in sinfo["train_idx"]}
    split_of_idx.update({int(sinfo["target_starts"][k]): "val" for k in sinfo["val_idx"]})
    split_of_idx.update({int(sinfo["target_starts"][k]): "test" for k in sinfo["test_idx"]})
    # Global window index i -> target weeks start at i+T.
    model = MIFlu(N=config["N"], T=config["T"], L=L, Lp=config["Lp"],
                  S=config["S"], K=config["K"], lora_r=config["lora_r"], device=device)
    model.load_state_dict(torch.load(best_rep["rep_ckpt"], map_location=device))
    model.eval()

    def _collect(X, Y, global_start):
        nw = X.shape[0]
        dl = _td.DataLoader(_td.TensorDataset(torch.from_numpy(X), torch.from_numpy(Y)),
                             batch_size=config["batch_size"], shuffle=False)
        rows = []
        # Local window offset within this split's DataLoader.
        local_to_global = {local: int(sinfo["target_starts"][global_start + local])
                           for local in range(nw)}
        with torch.no_grad():
            for bi, (bx, by) in enumerate(dl):
                bx = bx.to(device)
                bsz = bx.size(0)
                ht = prompt_cache.expand(bsz, -1, -1) if prompt_cache.shape[0] == 1 else prompt_cache[:bsz]
                yh_rev, _, _, _ = model(bx, htext=ht, train_mean=tm, train_std=ts)
                gt = by.cpu().numpy()[:, 4, :]
                pr = yh_rev.cpu().numpy()[:, 4, :]
                for r in range(bsz):
                    gi = local_to_global[bi * config["batch_size"] + r]
                    lbl = split_of_idx[gi]
                    for s in range(L):
                        rows.append((lbl, gi + s, s,
                                     float(gt[r, s]), float(pr[r, s])))
        return rows

    rows = (_collect(Xt, Yt, 0)
            + _collect(Xv, Yv, len(sinfo["train_idx"]))
            + _collect(Xte, Yte, len(sinfo["train_idx"]) + len(sinfo["val_idx"])))
    out_df = pd.DataFrame(rows, columns=[
        "split", "abs_week", "step", "ground_truth_ili", "prediction_ili"])
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"predictions_miflu_L{L}_paper_protocol.csv")
    out_df.to_csv(out_path, index=False)
    n_train = (out_df["split"] == "train").sum()
    n_val = (out_df["split"] == "val").sum()
    n_test = (out_df["split"] == "test").sum()
    log(f"  [CSV] L={L}: predictions written -> {out_path} "
        f"(train={n_train}, val={n_val}, test={n_test} rows)")
    return out_path


def main():
    # ── CLI (defaults are the authoritative essay config; overrides for HPC convenience) ──
    ap = argparse.ArgumentParser(description="MIFlu National training (authoritative config).")
    ap.add_argument("--horizon", type=int, default=None,
                    help="Train a single horizon L (e.g. 24). Default: full sweep [24,36,48,60].")
    ap.add_argument("--reps", type=int, default=CONFIG["num_repetitions"],
                    help="Number of repetitions (default 10, per essay).")
    ap.add_argument("--epochs", type=int, default=CONFIG["epochs"],
                    help="Training epochs (default 20, per essay Table IV).")
    ap.add_argument("--batch", type=int, default=CONFIG["batch_size"],
                    help="Batch size (default 16, per essay Table IV). Lower (e.g. 8) if OOM on HPC.")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    args = ap.parse_args()

    # Build effective config (batch/lr/T/K/Lp/S/lora_r fixed to the essay)
    eff = dict(CONFIG)
    eff["num_repetitions"] = args.reps
    eff["epochs"] = args.epochs
    eff["batch_size"] = args.batch
    L_list = [args.horizon] if args.horizon is not None else CONFIG["L_list"]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    log_init(LOG_PATH)
    log("=" * 60)
    log("  MIFlu — FULL MULTIMODAL (text prompt + time-series)")
    log("  PAPER PROTOCOL (MIFlu_paper.md)")
    log("=" * 60)
    log(f"  Evaluation protocol: paper protocol (NOT L=52 walk-forward)")
    log(f"  Device: {device} {'(' + torch.cuda.get_device_name(0) + ')' if device=='cuda' else ''}")
    log(f"  Config: T={eff['T']}, L={L_list} (each L trained INDEPENDENTLY)")
    log(f"          K={eff['K']}, Lp={eff['Lp']}, S={eff['S']}, lora_r={eff['lora_r']}")
    log(f"          Split: static 70:10:20 (shuffle=False)")
    log(f"          Normalization: StandardScaler fit on TRAIN only")
    log(f"          batch={eff['batch_size']}, lr={eff['learning_rate']}, epochs={eff['epochs']}, reps={eff['num_repetitions']}, seed={args.seed}")
    log()
    data_dict = load_and_normalize(); log()

    # ── Build text embedder once (shared across L) ──
    log("Loading GPT2 text embedder...")
    text_embedder = TextualInputEmbedder(device=device)
    log()

    all_rows, t_start, saved_ckpts, best_rep_info = [], time.time(), [], {}
    for L in L_list:
        # ── Build L-specific prompt (each L has different task instruction) ──
        prompt = build_prompt(data_dict["train_df"], T=eff["T"], L=L)
        prompt_cache = text_embedder(prompt)  # (1, 367, 768)
        log(f"  Prompt built for L={L}: {prompt_cache.shape[1]} tokens")
        log(f"{'─'*50}"); log(f"  HORIZON L={L}"); log(f"{'─'*50}")
        L_reps = []
        best_rep, best_val = None, float('inf')
        for rep in range(eff["num_repetitions"]):
            log(f"  [L={L}] Rep {rep+1}/{eff['num_repetitions']} ...")
            r = train_L(data_dict, L, eff, device, prompt_cache, seed=args.seed + rep); L_reps.append(r)
            all_rows.append({"L": L, "rep": rep+1,
                "mse_ili": r["test_mse_ili"], "mae_ili": r["test_mae_ili"]})
            pd.DataFrame(all_rows).to_csv(RESULTS_PATH, index=False)
            # track best-validation-loss rep for checkpoint (skip discarded NaN reps)
            if not r.get("discarded") and np.isfinite(r["best_val"]) and r["best_val"] < best_val:
                best_val, best_rep = r["best_val"], r
        # Keep only the best-val-loss rep's checkpoint as the canonical one
        final_ckpt = os.path.join(CKPT_DIR, f"best_miflu_L{L}.pth")
        if best_rep is not None:
            os.replace(best_rep["rep_ckpt"], final_ckpt)
            best_rep["rep_ckpt"] = final_ckpt  # update dict to the renamed file so downstream loaders use the correct path
            best_rep_info[L] = {"seed": best_rep["seed"], "best_val": best_val,
                                 "test_mse_ili": best_rep["test_mse_ili"]}
            saved_ckpts.append(final_ckpt)
            log(f"  [CKPT] L={L}: kept rep seed={best_rep['seed']} (best val_mse={best_val:.6f}) -> {final_ckpt}")
            # Export per-horizon prediction CSV with explicit `split` column.
            pred_csv = export_prediction_csv(
                data_dict, L, eff, device, prompt_cache, best_rep,
                os.path.join(PROJECT_ROOT, "data"))
            best_rep_info[L]["pred_csv"] = pred_csv
        else:
            log(f"  [WARN] L={L}: ALL reps discarded (non-finite) — no checkpoint saved!")
        # clean up any leftover temp rep checkpoints
        for r in L_reps:
            if r["rep_ckpt"] and os.path.exists(r["rep_ckpt"]) and r is not best_rep:
                try: os.remove(r["rep_ckpt"])
                except OSError: pass
        avg_mse_all = np.mean([r["test_mse_all"] for r in L_reps])
        avg_mse_ili = np.mean([r["test_mse_ili"] for r in L_reps])
        log(f"  [L={L}] FINAL: MSE_AllVars={avg_mse_all:.6f} MSE_ILITotal={avg_mse_ili:.6f}"); log()

    df = pd.DataFrame(all_rows)
    # Per-horizon summary: mean ± std over the 10 repetitions (paper reports the
    # mean of 10 runs). RMSE derived from MSE; PCC is the mean Pearson correlation.
    summary = df.groupby("L").agg(
        mse_ili_mean=("mse_ili", "mean"), mse_ili_std=("mse_ili", "std"),
        mae_ili_mean=("mae_ili", "mean"), mae_ili_std=("mae_ili", "std"))
    # Also persist a tidy per-horizon result table (English headers).
    result_table = summary.reset_index().rename(columns={
        "L": "Horizon",
        "mse_ili_mean": "MSE_ILI_mean", "mse_ili_std": "MSE_ILI_std",
        "mae_ili_mean": "MAE_ILI_mean", "mae_ili_std": "MAE_ILI_std"})
    table_path = os.path.join(PROJECT_ROOT, "data",
                               f"results_miflu_paper_protocol_table_{TS}.csv")
    result_table.to_csv(table_path, index=False)

    log("=" * 60)
    log("  FINAL RESULTS — ILITOTAL (paper protocol, mean ± std over 10 reps)")
    log("=" * 60)
    header = f"  {'L':>4s}  {'MSE':>12s}  {'MAE':>12s}"
    log(header)
    log("  " + "-" * 32)
    for L in L_list:
        r = summary.loc[L]
        log(f"  {L:>4d}  {r['mse_ili_mean']:>10.4f}±{r['mse_ili_std']:<5.4f}  "
            f"{r['mae_ili_mean']:>10.4f}±{r['mae_ili_std']:<5.4f}")
    log("=" * 60)
    log("  BEST-VAL CHECKPOINTS (one per horizon, rep with lowest val MSE):")
    for L, info in best_rep_info.items():
        log(f"    - L={L}: seed={info['seed']}  best_val_mse={info['best_val']:.6f}  test_mse_ili={info['test_mse_ili']:.6f}")
    log("=" * 60)
    log(f"  Total time: {(time.time()-t_start)/60:.1f} min")
    log(f"  Raw per-rep results : {RESULTS_PATH}")
    log(f"  Tidy result table   : {table_path}")
    log_close()
    return summary

if __name__ == "__main__":
    main()
