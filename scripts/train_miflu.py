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
from scaler_utils import ScalerBundle, DEFAULT_SCALER_PATH
from cdc_calendar import attach_calendar

# ── Authoritative hyperparameters (match the essay / Table IV) ──────────────────
# Paper protocol (MIFlu_paper.md): T=104, L ∈ {24,36,48,60} evaluated
# SEPARATELY as four independent runs (NOT a single rolling L=52 walk-forward).
# Each L is trained independently with `num_repetitions` repeats; the checkpoint
# and result table are stored per L. The L=52 walk-forward path is isolated under
# scripts/chattime_variant/ and is NOT the default MIFlu deliverable.
# Hyper-parameters, the N=7 channel list and the deterministic `set_seed()`
# all come from configs.py (single source of truth). Values are IDENTICAL to
# the literals that used to live here, so published numbers are unaffected.
#
# N=7 channel list (RESTORED per ChatTime-protocol restructure).
# Channel order matches the MIFlu paper Table X template.
#   OT = num_patients（CDC 总就诊人次/分母，全量未缩放）.
#   NOTE: 论文 Table X 仅称 "'OT' feature for long-term forecasting task"，未给公式、
#   未称黑箱。OT=num_patients（全量）是基于 Fig 2(a) 图表量级反推出的实现选择，
#   非论文明文定义；训练代码从未做 /100 缩放；StandardScaler 使常数缩放不影响训练。
from configs import (CONFIG, VAR_COLS, set_seed,
                     resolve_profile, split_for_profile, verify_profile_hash)

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(BASE_DIR)
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_PATH = os.path.join(PROJECT_ROOT, "data", f"training_miflu_log_{TS}.txt")
# Paper-protocol output naming: per-horizon results use the explicit suffix
# `_paper_protocol` so they can never be confused with the L=52 walk-forward
# variant (scripts/chattime_variant/ -> results_chattime_walkforward_L52.csv).
# NOTE: RESULTS_PATH / LOG_PATH are moved into EXPORT_DIR inside main() when a
# non-default --export-dir is given, so smoke tests / journal-evidence runs
# never clobber the published data/ artifacts.
RESULTS_PATH = os.path.join(PROJECT_ROOT, "data",
                            f"results_miflu_paper_protocol_{TS}.csv")
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "national_illness_raw.csv")
CKPT_DIR = os.path.join(PROJECT_ROOT, "checkpoints")
ACTIVE_PROFILE = "project_1025"           # overridden from --profile in main()
SCALER_PATH = DEFAULT_SCALER_PATH         # overridden from the profile in main()

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
    """Fit the StandardScaler on the TRAIN split only and persist it.

    ADVISOR Q3: the scaler's mean_/scale_ are written to
    `data/scaler_miflu_national.json` so that any later TEST-time / plotting /
    figure process can invert predictions back to patient counts WITHOUT
    re-deriving the split (which is the classic source of train/test leakage
    and of "the figure doesn't match the table" bugs).

    The numerics are unchanged from the original implementation (float32 array,
    population std, +1e-8 epsilon) so previously published MSE/MAE remain valid.
    """
    df = pd.read_csv(DATA_PATH)
    # Full 2002-2021 data — distribution shift makes text embeddings valuable
    data = df[VAR_COLS].values.astype(np.float32)
    n = len(data)
    # Profile-aware split: project_1025 -> 717/819, author_966 -> 676/773.
    t_end, v_end = split_for_profile(ACTIVE_PROFILE, n)

    bundle = ScalerBundle.fit_from_train(df, VAR_COLS, train_end=t_end, val_end=v_end)
    bundle.save_json(SCALER_PATH)
    log(f"Scaler persisted -> {SCALER_PATH} "
        f"(train_end={bundle.train_end}, val_end={bundle.val_end})")

    train_mean = bundle.mean_.reshape(1, -1).astype(np.float32)
    train_std = bundle.scale_.reshape(1, -1).astype(np.float32)
    data_norm = (data - train_mean) / train_std
    log(f"Data: {n} total | Train={t_end} | Val={v_end-t_end} | Test={n-v_end}")
    return {"data_norm": data_norm, "train_end": t_end, "val_end": v_end,
            "train_df": df.iloc[:t_end], "train_mean": train_mean, "train_std": train_std,
            "scaler": bundle}

def build_windows(data_norm, T, L, train_end, val_end, containment="start"):
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
        if containment == "strict":
            # Stage 5 section 2.2: the WHOLE target block must lie inside its split.
            if target_start + L <= train_end:
                splits[i] = 0
            elif target_start >= train_end and target_start + L <= val_end:
                splits[i] = 1
            elif target_start >= val_end and target_start + L <= total:
                splits[i] = 2
            else:
                splits[i] = -1   # target straddles a split boundary -> not assignable
        else:
            splits[i] = 0 if target_start < train_end else (1 if target_start <= val_end else 2)
    keep = np.where(splits >= 0)[0]
    X, Y, splits, target_starts = X[keep], Y[keep], splits[keep], target_starts[keep]
    split_info = {
        "target_starts": target_starts,
        "splits": splits,
        "train_end": train_end,
        "val_end": val_end,
        "containment": containment,
        "dropped_straddling": int(np.sum(splits < 0)) if False else int((len(keep)) * 0),
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
    """Dual-track evaluation.

    PRIMARY track (z / StandardScaler space) — this is what MIFlu §V-B
    prescribes for National ILI and what Table V reports. `train_mean` /
    `train_std` are the scaler statistics.

    SUPPLEMENTARY track (physical / patient counts) — de-normalised with the
    SAME scaler, reported alongside for interpretability. Never replaces the
    primary numbers (see docs/scaler_convention_supplement.md).
    """
    model.eval()
    preds, targets = [], []
    preds_phys, targets_phys = [], []
    # (1, N, 1) -> broadcast over (B, N, L)
    tm = train_mean.view(1, -1, 1).to(dev)
    ts = train_std.view(1, -1, 1).to(dev)
    for i, (bx, by) in enumerate(loader):
        bx = bx.to(dev)
        bsz = bx.size(0)
        ht = prompt_cache.expand(bsz, -1, -1) if prompt_cache.shape[0] == 1 else prompt_cache[:bsz]
        # Metrics MUST be in StandardScaler space (Section V-B): yh_rev vs Y (StdScaler target)
        yh_rev, yh_phys, _, _ = model(bx, htext=ht, train_mean=train_mean, train_std=train_std)
        preds.append(yh_rev.cpu().numpy()); targets.append(by.numpy())
        # Physical track: prediction comes from the model; target is inverted here.
        preds_phys.append(yh_phys.cpu().numpy())
        targets_phys.append((by.to(dev) * ts + tm).cpu().numpy())
        if diag and i == 0:
            yy = yh_rev.cpu().numpy(); tt = by.numpy()
            log(f"    [DIAG] y_pred(StdScaler): mean={yy.mean():.4f} std={yy.std():.4f} min={yy.min():.4f} max={yy.max():.4f}")
            log(f"    [DIAG] y_true(StdScaler): mean={tt.mean():.4f} std={tt.std():.4f} min={tt.min():.4f} max={tt.max():.4f}")
    p = np.concatenate(preds); t = np.concatenate(targets)
    mse_all = np.mean((p-t)**2); mae_all = np.mean(np.abs(p-t))
    mse_ili = np.mean((p[:,4,:]-t[:,4,:])**2); mae_ili = np.mean(np.abs(p[:,4,:]-t[:,4,:]))
    # ---- SUPPLEMENTARY: physical-unit (patient-count) metrics ----
    pp = np.concatenate(preds_phys); tt_p = np.concatenate(targets_phys)
    mse_ili_phys = float(np.mean((pp[:, 4, :] - tt_p[:, 4, :]) ** 2))
    mae_ili_phys = float(np.mean(np.abs(pp[:, 4, :] - tt_p[:, 4, :])))
    # Pearson correlation on ILITOTAL (channel 4) across all test windows.
    gt_ili = t[:, 4, :].reshape(-1)
    pr_ili = p[:, 4, :].reshape(-1)
    if np.std(gt_ili) > 0 and np.std(pr_ili) > 0:
        pcc_ili = float(np.corrcoef(gt_ili, pr_ili)[0, 1])
    else:
        pcc_ili = float("nan")
    if diag:
        log(f"    [DIAG] MSE_AllVars={mse_all:.6f} MSE_ILITotal={mse_ili:.6f} PCC_ILI={pcc_ili:.4f}")
        log(f"    [DIAG] SUPPLEMENTARY physical units: MSE_ILITotal={mse_ili_phys:.1f} "
            f"patients^2  MAE_ILITotal={mae_ili_phys:.1f} patients")
    # Return raw ILITOTAL (channel 4) series for the per-horizon prediction CSV.
    # Shapes: (n_windows, L) — caller assigns the correct `split` label.
    return (mse_all, mae_all, mse_ili, mae_ili, pcc_ili,
            t[:, 4, :], p[:, 4, :], mse_ili_phys, mae_ili_phys)

def train_L(data_dict, L, config, device, prompt_cache, seed=42, containment="start"):
    """Train ONE repetition for horizon L. Returns metrics + the per-rep checkpoint
    path + the minimum validation MSE observed across epochs (for best-rep selection)."""
    set_seed(seed + L)   # deterministic: random / numpy / torch / cuda / cuDNN
    np.random.seed(seed + L)
    tm = torch.from_numpy(data_dict["train_mean"].astype(np.float32))
    ts = torch.from_numpy(data_dict["train_std"].astype(np.float32))
    Xt, Yt, Xv, Yv, Xte, Yte, split_info = build_windows(
        data_dict["data_norm"], config["T"], L,
        data_dict["train_end"], data_dict["val_end"], containment=containment)
    log(f"  L={L}: train={len(Xt)} val={len(Xv)} test={len(Xte)} windows "
        f"(containment={containment})")
    # Leakage guard. Under 'start' the test target-start index must exceed
    # val_end; under 'strict' the FIRST test target index equals val_end (the
    # first row of the test segment) and the whole target must stay inside it.
    test_target_starts = split_info["target_starts"][split_info["test_idx"]]
    if containment == "strict":
        assert int(test_target_starts.min()) >= data_dict["val_end"], (
            f"LEAKAGE GUARD FAILED (strict): first test target="
            f"{int(test_target_starts.min())} < val_end={data_dict['val_end']}")
        _n_rows = int(data_dict["data_norm"].shape[0])
        assert int(test_target_starts.max()) + L <= _n_rows, (
            f"LEAKAGE GUARD FAILED (strict): last test target end="
            f"{int(test_target_starts.max()) + L} > n={_n_rows}")
    else:
        assert int(test_target_starts.min()) > data_dict["val_end"], (
            f"LEAKAGE GUARD FAILED: test target starts at "
            f"{int(test_target_starts.min())} but val_end={data_dict['val_end']}")
    log(f"  L={L}: leakage guard OK — min test target-start index "
        f"= {int(test_target_starts.min())}, containment={containment}")
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
    best_state = None
    best_epoch = -1
    for ep in range(config["epochs"]):  # Fixed 20 epochs per Table IV — no early stopping
        t0 = time.time()
        tl_loss = train_epoch(model, tl, opt, crit, device, prompt_cache, tm, ts, clip=1.0)
        v_mse_all, v_mae_all, v_mse_ili, v_mae_ili, _, _, _, _, _ = evaluate(model, vl, crit, device, prompt_cache, tm, ts)
        dt = time.time() - t0
        if v_mse_all < best_val:
            best_val = v_mse_all
            best_epoch = ep
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        log(f"    ep {ep+1:2d}/{config['epochs']} | train_loss={tl_loss:.6f} | val_mse={v_mse_all:.6f}(All) {v_mse_ili:.4f}(ILI) | val_mae={v_mae_all:.6f} | {dt:.1f}s | GPU={torch.cuda.memory_allocated()/1e9:.2f}GB" if device=="cuda" else f"    ep {ep+1:2d}/{config['epochs']} | train_loss={tl_loss:.6f} | val_mse={v_mse_all:.6f}(All) {v_mse_ili:.4f}(ILI) | val_mae={v_mae_all:.6f} | {dt:.1f}s")
    # ---- Stage 5 test-isolation gate ----
    # Test scoring happens ONCE from the separate scoring entry, after every
    # scheduled checkpoint has been selected and locked. While DEFER_TEST=1 the
    # Test loader is never evaluated, so no Test number exists yet.
    if os.environ.get("DEFER_TEST") == "1":
        log("  L=%s rep seed=%s: DEFER_TEST=1 - Test NOT evaluated (validation-only fit)"
            % (L, seed))
        os.makedirs(CKPT_DIR, exist_ok=True)
        # Stage 5 A2: persist the BEST-VALIDATION-EPOCH weights under a per-seed
        # name so the later locked-batch scoring can select/specify each
        # (model, L, seed) checkpoint independently.
        if best_state is not None:
            model.load_state_dict(best_state)
        rep_ckpt = os.path.join(CKPT_DIR, "best_miflu_L%s_seed%s.pth" % (L, seed))
        torch.save(model.state_dict(), rep_ckpt)
        del model
        torch.cuda.empty_cache() if device == "cuda" else None
        return {"L": L, "test_mse_all": None, "test_mae_all": None,
                "test_mse_ili": None, "test_mae_ili": None, "test_pcc_ili": None,
                "test_mse_ili_phys": None, "test_mae_ili_phys": None,
                "test_gt_ili": None, "test_pr_ili": None,
                "rep_ckpt": rep_ckpt, "best_val": best_val,
                "best_epoch": best_epoch, "seed": seed,
                "discarded": False, "test_deferred": True}

    (t_mse_all, t_mae_all, t_mse_ili, t_mae_ili, t_pcc_ili, t_gt_ili, t_pr_ili,
     t_mse_ili_phys, t_mae_ili_phys) = evaluate(
        model, el, crit, device, prompt_cache, tm, ts,
        diag=(L == CONFIG["L_list"][0]))
    # ── NaN-rep discipline: discard reps whose test prediction is non-finite ──
    if not (np.isfinite(t_mse_all) and np.isfinite(t_mse_ili) and np.isfinite(t_pcc_ili)):
        log(f"  [WARN] L={L} rep seed={seed} produced non-finite metrics — DISCARDED (NaN-rep)")
        del model; torch.cuda.empty_cache() if device=="cuda" else None
        return {"L": L, "test_mse_all": np.nan, "test_mae_all": np.nan,
                "test_mse_ili": np.nan, "test_mae_ili": np.nan, "test_pcc_ili": np.nan,
                "test_mse_ili_phys": np.nan, "test_mae_ili_phys": np.nan,
                "rep_ckpt": None, "best_val": np.nan, "seed": seed, "discarded": True}
    log(f"  L={L} DONE: test_mse={t_mse_all:.6f}(All) {t_mse_ili:.4f}(ILI) test_mae={t_mae_all:.6f} pcc={t_pcc_ili:.4f}")
    # per-rep temp checkpoint; main() keeps only the best-val-loss rep as best_miflu_L{L}.pth
    os.makedirs(CKPT_DIR, exist_ok=True)
    rep_ckpt = os.path.join(CKPT_DIR, f"_rep_miflu_L{L}_seed{seed}.pth")
    torch.save(model.state_dict(), rep_ckpt)
    del model; torch.cuda.empty_cache() if device=="cuda" else None
    return {"L": L, "test_mse_all": t_mse_all, "test_mae_all": t_mae_all,
            "test_mse_ili": t_mse_ili, "test_mae_ili": t_mae_ili, "test_pcc_ili": t_pcc_ili,
            "test_mse_ili_phys": t_mse_ili_phys, "test_mae_ili_phys": t_mae_ili_phys,
            "test_gt_ili": t_gt_ili, "test_pr_ili": t_pr_ili,
            "rep_ckpt": rep_ckpt, "best_val": best_val, "seed": seed, "discarded": False}


def export_prediction_csv(data_dict, L, config, device, prompt_cache,
                           best_rep, out_dir, containment="start"):
    """Write a per-horizon prediction CSV with an explicit `split` column.

    The CSV is produced from the BEST-VAL-LOSS rep checkpoint so the plotted
    curve matches the reported metrics. Every row carries its split label
    (train/val/test) and the absolute week index `abs_week` so figure scripts
    can align predictions to ground truth in time. Figure scripts MUST filter
    to `split == 'test'` only (asserted in code).

    ADVISOR Q1/Q2/Q3 — columns written (backward compatible: only ADDED):
      split, abs_week, step, epiweek, week_start_date,
      ground_truth_ili, prediction_ili,               <- z-space (PRIMARY)
      ground_truth_ili_phys, prediction_ili_phys      <- patient counts (FIGURES)

    `epiweek` / `week_start_date` come from `cdc_calendar`, which uses the raw
    CDC epiweek labels instead of assuming a regular weekly grid. The old
    synthetic mapping (2002w01 + i weeks) drifted ~19 weeks by row 820 because
    the CDC file is missing 2002 weeks 21-39.
    """
    import torch.utils.data as _td
    tm = torch.from_numpy(data_dict["train_mean"].astype(np.float32))
    ts = torch.from_numpy(data_dict["train_std"].astype(np.float32))
    tm_np = np.asarray(data_dict["train_mean"]).ravel()
    ts_np = np.asarray(data_dict["train_std"]).ravel()
    # Rebuild windows to retrieve the global split layout.
    Xt, Yt, Xv, Yv, Xte, Yte, sinfo = build_windows(
        data_dict["data_norm"], config["T"], L,
        data_dict["train_end"], data_dict["val_end"], containment=containment)
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
                yh_rev, yh_phys, _, _ = model(bx, htext=ht, train_mean=tm, train_std=ts)
                gt = by.cpu().numpy()[:, 4, :]
                pr = yh_rev.cpu().numpy()[:, 4, :]
                # Physical track (patient counts) — used by every figure.
                gt_p = gt * float(ts_np[4]) + float(tm_np[4])
                pr_p = yh_phys.cpu().numpy()[:, 4, :]
                for r in range(bsz):
                    gi = local_to_global[bi * config["batch_size"] + r]
                    lbl = split_of_idx[gi]
                    for s in range(L):
                        rows.append((lbl, gi + s, s,
                                     float(gt[r, s]), float(pr[r, s]),
                                     float(gt_p[r, s]), float(pr_p[r, s])))
        return rows

    rows = (_collect(Xt, Yt, 0)
            + _collect(Xv, Yv, len(sinfo["train_idx"]))
            + _collect(Xte, Yte, len(sinfo["train_idx"]) + len(sinfo["val_idx"])))
    out_df = pd.DataFrame(rows, columns=[
        "split", "abs_week", "step",
        "ground_truth_ili", "prediction_ili",
        "ground_truth_ili_phys", "prediction_ili_phys"])
    # Attach the REAL CDC calendar (epiweek + week_start_date). This replaces the
    # buggy synthetic `2002w01 + abs_week weeks` mapping, which drifted ~19 weeks.
    # raw_csv follows the active profile so abs_week indices map to the RIGHT
    # calendar (author 966-row file vs project 1025-row file).
    out_df = attach_calendar(out_df, abs_week_col="abs_week", raw_csv=DATA_PATH)
    out_df = out_df[["split", "abs_week", "step", "epiweek", "week_start_date",
                     "ground_truth_ili", "prediction_ili",
                     "ground_truth_ili_phys", "prediction_ili_phys"]]
    # Alignment invariant (ADVISOR Q2b): ground truth and prediction must refer
    # to the SAME calendar week. All windows covering a week must agree on GT.
    gt_spread = (out_df.groupby("abs_week")["ground_truth_ili"].max()
                 - out_df.groupby("abs_week")["ground_truth_ili"].min()).max()
    assert float(gt_spread) < 1e-4, (
        f"GT disagrees across overlapping windows (max spread {gt_spread}) — "
        "off-by-one alignment bug")
    log(f"  [CSV] L={L}: alignment check OK (max GT spread across overlapping "
        f"windows = {float(gt_spread):.2e})")
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
    ap.add_argument("--containment", choices=["start", "strict"], default="start",
                    help="target-split rule: 'start' = legacy (target start), "
                         "'strict' = Stage 5 (whole target inside its split)")
    ap.add_argument("--profile", default="project_1025",
                    choices=sorted(("project_1025", "author_966")),
                    help="Immutable dataset profile (project 1025-row snapshot "
                         "or author 966-row vintage).")
    ap.add_argument("--export-dir", default=None,
                    help="Where the per-horizon prediction CSVs are written "
                         "(default: <project>/data). Smoke tests and the "
                         "journal-evidence runs point this at a scratch dir so "
                         "published artifacts are never clobbered.")
    ap.add_argument("--ckpt-dir", default=None,
                    help="Checkpoint directory (default: <project>/checkpoints).")
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


    # ── Deterministic execution: seed every RNG before touching any data ──
    set_seed(args.seed)

    # ── Profile selection: hash-verified data path + split rule + scaler path ──
    global DATA_PATH, ACTIVE_PROFILE, SCALER_PATH
    ACTIVE_PROFILE = args.profile
    _prof = resolve_profile(args.profile)
    verify_profile_hash(args.profile)
    DATA_PATH = _prof["data_path"]
    SCALER_PATH = _prof["scaler_path"]

    # Module-level output dirs are consumed by train_L()/export_prediction_csv().
    global CKPT_DIR
    if args.ckpt_dir:
        CKPT_DIR = args.ckpt_dir
        os.makedirs(CKPT_DIR, exist_ok=True)
    EXPORT_DIR = args.export_dir or os.path.join(PROJECT_ROOT, "data")
    # Route the other per-run artifacts into EXPORT_DIR too, so a scratch run
    # never overwrites data/results_miflu_paper_protocol_*.csv / logs.
    global RESULTS_PATH, LOG_PATH
    if args.export_dir:
        _stem = os.path.splitext(os.path.basename(RESULTS_PATH))[0]
        RESULTS_PATH = os.path.join(EXPORT_DIR, os.path.basename(RESULTS_PATH))
        LOG_PATH = os.path.join(EXPORT_DIR, f"training_miflu_log_{TS}.txt")

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
        prompt = build_prompt(data_dict["train_df"], T=eff["T"], L=L,
                              date_range_string=_prof["date_range_string"])
        prompt_cache = text_embedder(prompt)  # (1, 367, 768)
        log(f"  Prompt built for L={L}: {prompt_cache.shape[1]} tokens")
        log(f"{'─'*50}"); log(f"  HORIZON L={L}"); log(f"{'─'*50}")
        L_reps = []
        best_rep, best_val = None, float('inf')
        for rep in range(eff["num_repetitions"]):
            log(f"  [L={L}] Rep {rep+1}/{eff['num_repetitions']} ...")
            r = train_L(data_dict, L, eff, device, prompt_cache, seed=args.seed + rep,
                        containment=args.containment); L_reps.append(r)
            all_rows.append({"L": L, "rep": rep+1,
                "mse_ili": r["test_mse_ili"] if r.get("test_mse_ili") is not None else np.nan, "mae_ili": r["test_mae_ili"] if r.get("test_mae_ili") is not None else np.nan,
                # SUPPLEMENTARY physical-unit track (patient counts)
                "mse_ili_phys": r["test_mse_ili_phys"],
                "mae_ili_phys": r["test_mae_ili_phys"]})
            pd.DataFrame(all_rows).to_csv(RESULTS_PATH, index=False)
            # track best-validation-loss rep for checkpoint (skip discarded NaN reps)
            if not r.get("discarded") and np.isfinite(r["best_val"]) and r["best_val"] < best_val:
                best_val, best_rep = r["best_val"], r
        # Keep the best-val-loss checkpoint as canonical. Under Stage 5 A2 the
        # checkpoint already carries its seed (best_miflu_L{L}_seed{seed}.pth),
        # so it must NOT be renamed to a seed-less name (which would overwrite
        # the other seeds).
        if best_rep is not None:
            if os.environ.get("DEFER_TEST") == "1":
                final_ckpt = best_rep["rep_ckpt"]
                log(f"  [CKPT] L={L}: kept per-seed best-epoch ckpt seed={best_rep['seed']} "
                    f"(best val_mse={best_val:.6f}, best_epoch={best_rep.get('best_epoch')}) -> {final_ckpt}")
            else:
                final_ckpt = os.path.join(CKPT_DIR, f"best_miflu_L{L}.pth")
                os.replace(best_rep["rep_ckpt"], final_ckpt)
                log(f"  [CKPT] L={L}: kept rep seed={best_rep['seed']} (best val_mse={best_val:.6f}) -> {final_ckpt}")
            best_rep["rep_ckpt"] = final_ckpt  # update dict to the renamed file so downstream loaders use the correct path
            best_rep_info[L] = {"seed": best_rep["seed"], "best_val": best_val,
                                 "best_epoch": best_rep.get("best_epoch"),
                                 "test_mse_ili": best_rep["test_mse_ili"]}
            saved_ckpts.append(final_ckpt)
            # Export per-horizon prediction CSV with explicit `split` column.
            if os.environ.get("DEFER_TEST") == "1":
                pred_csv = None
                log("  [DEFER_TEST] prediction export skipped (locked-batch step)")
            else:
                pred_csv = export_prediction_csv(
                data_dict, L, eff, device, prompt_cache, best_rep, EXPORT_DIR,
                containment=args.containment)
            best_rep_info[L]["pred_csv"] = pred_csv
        else:
            log(f"  [WARN] L={L}: ALL reps discarded (non-finite) — no checkpoint saved!")
        # clean up any leftover temp rep checkpoints
        for r in L_reps:
            if r["rep_ckpt"] and os.path.exists(r["rep_ckpt"]) and r is not best_rep:
                try: os.remove(r["rep_ckpt"])
                except OSError: pass
        if any(r.get("test_deferred") for r in L_reps):
            log(f"  [L={L}] FINAL: TEST DEFERRED - no Test numbers produced (locked-batch step); "
                f"best val={best_val:.6f}")
        else:
            avg_mse_all = np.mean([r["test_mse_all"] for r in L_reps])
            avg_mse_ili = np.mean([r["test_mse_ili"] for r in L_reps])
            log(f"  [L={L}] FINAL: MSE_AllVars={avg_mse_all:.6f} MSE_ILITotal={avg_mse_ili:.6f}")
        log()

    df = pd.DataFrame(all_rows)
    # Per-horizon summary: mean ± std over the 10 repetitions (paper reports the
    # mean of 10 runs). RMSE derived from MSE; PCC is the mean Pearson correlation.
    summary = df.groupby("L").agg(
        mse_ili_mean=("mse_ili", "mean"), mse_ili_std=("mse_ili", "std"),
        mae_ili_mean=("mae_ili", "mean"), mae_ili_std=("mae_ili", "std"),
        mse_ili_phys_mean=("mse_ili_phys", "mean"),
        mse_ili_phys_std=("mse_ili_phys", "std"),
        mae_ili_phys_mean=("mae_ili_phys", "mean"),
        mae_ili_phys_std=("mae_ili_phys", "std"))
    # Also persist a tidy per-horizon result table (English headers).
    result_table = summary.reset_index().rename(columns={
        "L": "Horizon",
        "mse_ili_mean": "MSE_ILI_mean", "mse_ili_std": "MSE_ILI_std",
        "mae_ili_mean": "MAE_ILI_mean", "mae_ili_std": "MAE_ILI_std",
        "mse_ili_phys_mean": "MSE_ILI_phys_mean",
        "mse_ili_phys_std": "MSE_ILI_phys_std",
        "mae_ili_phys_mean": "MAE_ILI_phys_mean",
        "mae_ili_phys_std": "MAE_ILI_phys_std"})
    table_path = os.path.join(EXPORT_DIR,
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
    log("  SUPPLEMENTARY — de-normalised (patient counts). NOT the paper's")
    log("  Table V metric: MIFlu §V-B de-normalises only for the REGIONAL task.")
    log("  Reported for interpretability of the figures only.")
    log("  " + "-" * 62)
    for L in L_list:
        r = summary.loc[L]
        log(f"  {L:>4d}  MSE={r['mse_ili_phys_mean']:>14.1f}±{r['mse_ili_phys_std']:<9.1f} "
            f"patients^2   MAE={r['mae_ili_phys_mean']:>9.1f}±{r['mae_ili_phys_std']:<7.1f} patients")
    log("=" * 60)
    log("  BEST-VAL CHECKPOINTS (one per horizon, rep with lowest val MSE):")
    for L, info in best_rep_info.items():
        if info.get("test_mse_ili") is None:
            log(f"    - L={L}: seed={info['seed']}  best_val_mse={info['best_val']:.6f}  test=DEFERRED")
        else:
            log(f"    - L={L}: seed={info['seed']}  best_val_mse={info['best_val']:.6f}  test_mse_ili={info['test_mse_ili']:.6f}")
    log("=" * 60)
    log(f"  Total time: {(time.time()-t_start)/60:.1f} min")
    log(f"  Raw per-rep results : {RESULTS_PATH}")
    log(f"  Tidy result table   : {table_path}")
    log_close()
    return summary

if __name__ == "__main__":
    main()
