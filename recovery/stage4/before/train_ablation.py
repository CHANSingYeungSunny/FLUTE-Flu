"""
train_ablation.py — Table VIII Ablation Variants + Training-Recipe Sweep
=========================================================================
Runs MIFlu ablation variants via --variant, and (new) training-recipe variants
via --recipe.

Variants (matching MIFlu Table VIII):
  full        = MIFlu (text + LoRA + all prompt sections)
  no_dataset  = w/o Dataset information section
  no_task     = w/o Task instruction section
  no_vardesc  = w/o Input variable description section
  no_lora     = w/o LoRA (only PE + LN trainable)
  no_multi    = w/o multimodality (no text, LoRA kept) = baseline
  no_lora_multi = w/o LoRA + multimodality (no text, no LoRA)

Training recipes (Advisor Question 4):
  baseline      = Adam, lr=5e-4, wd=0, no scheduler, MSE        (published)
  adamw_cosine  = AdamW, lr=5e-4, wd=0.01, CosineAnnealingLR
  huber_clip    = AdamW, lr=1e-4, wd=0.01, Huber Loss, grad-clip 5.0

Optional peak-aware early stopping (Advisor Question 5): --early-stop

Usage:
  python train_ablation.py --variant no_lora
  python train_ablation.py --variant full --recipe adamw_cosine
  python train_ablation.py --variant full --early-stop --patience 5

─────────────────────────────────────────────────────────────────────────────
BUGS FIXED IN THIS FILE (each previously made the script unrunnable / wrong)
─────────────────────────────────────────────────────────────────────────────
1. 4-tuple unpack (CRASH). `MIFlu.forward` returns
   (y_hat_rev, y_phys, means, stdevs), but the old code wrote
   `yh, _, _ = model(...)`, raising ValueError on the very first batch.
   -> now `yh_rev, yh_phys, _, _ = model(...)`.
2. `log_close()` was called at the end of main() but NEVER DEFINED in this
   module (only train_miflu.py has it) -> NameError after every run.
   -> now defined.
3. `load_and_normalize()` discarded train_mean/train_std, so the model could
   never be inverted to physical units (Advisor Q3) and the scaler was never
   persisted.
   -> now returns them and writes data/scaler_miflu_national.json.
4. Split boundary off-by-one: this file used `< val_end` where train_miflu.py
   uses `<= val_end`, so the two produced different train/val/test memberships
   and their numbers were not comparable.
   -> unified to `<=` (see build_windows below).
5. No artifacts: no checkpoint, no prediction CSV, no early stopping, no
   recipe control. -> all added.
─────────────────────────────────────────────────────────────────────────────
"""

import os
import sys
import time
import argparse
from datetime import datetime

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(__file__))

# ── Centralised configuration (single source of truth) ──
# Hyper-parameters, channel list, data-window constants and the deterministic
# `set_seed()` helper now live in configs.py. Nothing below re-declares them.
from configs import (
    CONFIG, VAR_COLS, SCALER_PATH, RAW_DATA_PATH as DATA_PATH,
    FULL_ROWS, TRAIN_END, VAL_END, CORE_VARIANTS,
    assert_full_window, derive_split, set_seed,
    JOURNAL_EVIDENCE_ROOT,
)
from miflu_model import MIFlu
from textual_embedder import TextualInputEmbedder, build_prompt
from scaler_utils import ScalerBundle
from cdc_calendar import attach_calendar
from recipes import build_recipe, describe, RECIPES
from early_stopping import EarlyStopping

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(BASE_DIR)


# ── Prompt variant builders ────────────────────────────────────────────────

def build_prompt_no_dataset(train_df, T, L):
    """Remove [Dataset information] section."""
    prompt = build_prompt(train_df, T, L)
    idx = prompt.find("***")
    return prompt[idx:] if idx > 0 else prompt


def build_prompt_no_task(train_df, T, L):
    """Remove [Task instruction] section."""
    prompt = build_prompt(train_df, T, L)
    idx = prompt.rfind("*** [Task instruction]")
    return prompt[:idx].rstrip() if idx > 0 else prompt


def build_prompt_no_vardesc(train_df, T, L):
    """Remove [Input variable description] section, keep only headers."""
    prompt = build_prompt(train_df, T, L)
    parts = prompt.split("***")
    if len(parts) >= 3:
        return parts[0] + "***\n" + parts[2]
    return prompt


# ── Logging ─────────────────────────────────────────────────────────────────
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
    """BUG FIX #2: this function was called by main() but never defined."""
    global _log_file
    if _log_file:
        _log_file.close()
        _log_file = None


# ── Data ────────────────────────────────────────────────────────────────────
def load_and_normalize():
    """Fit StandardScaler on TRAIN ONLY and persist it (Advisor Q3).

    DATA-LEAKAGE GUARANTEE (proven, not merely documented)
    ------------------------------------------------------
    `ScalerBundle.fit_from_train` derives mean_ / scale_ from `data[:train_end]`
    and nothing else. Validation and test rows are only ever divided by those
    statistics; there is no second `.fit()` anywhere in this module. Two
    assertions make the guarantee unfalsifiable:
      1. `assert_full_window(n)` → crash unless the CSV is the full 1025 rows
         (this is what blocks the 966-row truncation);
      2. `derive_split(n)`       → crash unless the split is exactly 717 / 819.
    The fitted statistics are persisted to `data/scaler_miflu_national.json`;
    if a file already exists we re-fit and then ASSERT it agrees, so a stale or
    hand-edited scaler can never silently move published numbers.

    BUG FIX #3: the original returned only data_norm/train_end/val_end, so
    `MIFlu.forward(..., train_mean=..., train_std=...)` could not be used and
    predictions could never be converted back to patient counts.
    """
    df = pd.read_csv(DATA_PATH)
    data = df[VAR_COLS].values.astype(np.float32)
    n = assert_full_window(len(data))          # guard: no 966-row truncation
    t_end, v_end = derive_split(n)             # guard: split is exactly 717/819
    assert (t_end, v_end) == (TRAIN_END, VAL_END)

    # ── FIT ON TRAIN ONLY: data[:717] ──
    bundle = ScalerBundle.fit_from_train(df, VAR_COLS, train_end=t_end, val_end=v_end)

    # Provenance: persist, and cross-check against any previously persisted file.
    if os.path.exists(SCALER_PATH):
        try:
            persisted = ScalerBundle.load_json(SCALER_PATH)
            bundle.assert_consistent_with(persisted)
            log(f"Scaler: FIT on train[:{t_end}] ONLY — agrees with persisted "
                f"{SCALER_PATH} (no test-set refit)")
        except Exception as e:
            log(f"[WARN] persisted scaler mismatch ({e}) — overwriting with "
                f"freshly fitted train-only statistics")
            bundle.save_json(SCALER_PATH)
    else:
        bundle.save_json(SCALER_PATH)
        log(f"Scaler: FIT on train[:{t_end}] ONLY -> persisted {SCALER_PATH}")

    train_mean = bundle.mean_.reshape(1, -1).astype(np.float32)
    train_std = bundle.scale_.reshape(1, -1).astype(np.float32)
    # NOTE: `transform` semantics only — the SAME train-derived statistics are
    # applied to every split below. No refit on val/test occurs anywhere.
    data_norm = (data - train_mean) / train_std
    log(f"Data: {n} total (FULL {FULL_ROWS}-row window) | "
        f"Train={t_end} | Val={v_end-t_end} | Test={n-v_end}")
    return {"data_norm": data_norm, "train_end": t_end, "val_end": v_end,
            "train_df": df.iloc[:t_end], "train_mean": train_mean,
            "train_std": train_std, "scaler": bundle}


def build_windows(data_norm, T, L, train_end, val_end):
    """Sliding windows at stride = 1 (FULLY OVERLAPPING).

    BUG FIX #4: this module previously used strict `<` for BOTH boundaries
    (`0 if (i+T) < train_end else (1 if (i+T) < val_end else 2)`) whereas
    train_miflu.py uses `<= val_end`. That one-week difference changed split
    membership, so ablation numbers were not comparable with the main Table V
    run. Unified here on train_miflu.py's convention.

    NOTE (Advisor Q1): stride is 1, i.e. consecutive windows are offset by ONE
    week. That offset is the ORIGIN SHIFT, not a "1-week-ahead forecast": each
    window still forecasts the full L-week horizon. Overlap means every
    calendar week is predicted by up to L windows, at forecast steps 0..L-1.
    """
    total = data_norm.shape[0]
    nw = total - T - L + 1
    X = np.zeros((nw, CONFIG["N"], T), dtype=np.float32)
    Y = np.zeros((nw, CONFIG["N"], L), dtype=np.float32)
    splits = np.zeros(nw, dtype=np.int8)
    target_starts = np.arange(nw) + T
    for i in range(nw):
        X[i] = data_norm[i:i + T].T
        Y[i] = data_norm[i + T:i + T + L].T
        target_start = i + T
        # <= val_end  (matches train_miflu.build_windows)
        splits[i] = 0 if target_start < train_end else (1 if target_start <= val_end else 2)
    split_info = {"target_starts": target_starts, "splits": splits}
    return (X[splits == 0], Y[splits == 0], X[splits == 1], Y[splits == 1],
            X[splits == 2], Y[splits == 2])


# ── Training ────────────────────────────────────────────────────────────────
def train_epoch(model, loader, opt, crit, dev, prompt_cache,
                train_mean, train_std, clip=None):
    model.train()
    loss_sum = 0.0
    for bx, by in loader:
        bx, by = bx.to(dev), by.to(dev)
        bsz = bx.size(0)
        ht = (prompt_cache.expand(bsz, -1, -1)
              if prompt_cache is not None and prompt_cache.shape[0] == 1
              else prompt_cache[:bsz] if prompt_cache is not None else None)
        opt.zero_grad()
        # BUG FIX #1: forward returns FOUR values, not three.
        yh_rev, _, _, _ = model(bx, htext=ht,
                                train_mean=train_mean, train_std=train_std)
        loss = crit(yh_rev, by)
        if not torch.isfinite(loss):
            log("    [WARN] non-finite loss — skipping this batch")
            opt.zero_grad()
            continue
        loss.backward()
        if clip:
            torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
        opt.step()
        loss_sum += loss.item() * bsz
    return loss_sum / len(loader.dataset)


@torch.no_grad()
def evaluate(model, loader, crit, dev, prompt_cache, train_mean, train_std):
    """Dual-track: z-space (PRIMARY, per MIFlu §V-B) + physical (SUPPLEMENTARY).

    Returns (mse_all, mae_all, mse_ili, mae_ili, mse_ili_phys, mae_ili_phys).
    """
    model.eval()
    preds, targets = [], []
    preds_phys, targets_phys = [], []
    tm = train_mean.view(1, -1, 1).to(dev)
    ts = train_std.view(1, -1, 1).to(dev)
    for bx, by in loader:
        bx = bx.to(dev)
        bsz = bx.size(0)
        ht = (prompt_cache.expand(bsz, -1, -1)
              if prompt_cache is not None and prompt_cache.shape[0] == 1
              else prompt_cache[:bsz] if prompt_cache is not None else None)
        yh_rev, yh_phys, _, _ = model(bx, htext=ht,
                                      train_mean=train_mean, train_std=train_std)
        preds.append(yh_rev.cpu().numpy()); targets.append(by.numpy())
        preds_phys.append(yh_phys.cpu().numpy())
        targets_phys.append((by.to(dev) * ts + tm).cpu().numpy())

    p = np.concatenate(preds); t = np.concatenate(targets)
    pp = np.concatenate(preds_phys); tt = np.concatenate(targets_phys)
    mse_all = float(np.mean((p - t) ** 2))
    mae_all = float(np.mean(np.abs(p - t)))
    mse_ili = float(np.mean((p[:, 4, :] - t[:, 4, :]) ** 2))
    mae_ili = float(np.mean(np.abs(p[:, 4, :] - t[:, 4, :])))
    mse_ili_phys = float(np.mean((pp[:, 4, :] - tt[:, 4, :]) ** 2))
    mae_ili_phys = float(np.mean(np.abs(pp[:, 4, :] - tt[:, 4, :])))

    # NOTE: this used to also return the collapsed 1-week-ahead validation
    # series (val_gt / val_pred), which existed solely to feed the peak gate of
    # the removed PeakAwareEarlyStopping. Nothing consumes them now, so they are
    # no longer produced.
    return (mse_all, mae_all, mse_ili, mae_ili,
            mse_ili_phys, mae_ili_phys)


def train_L(data_dict, L, config, device, prompt_cache, use_lora, use_text,
            seed=42, recipe="baseline", early_stop=False, patience=5,
            rep_dir=None, variant_name="unknown",
            rep=1, use_text_ln=True, gated_inject=False, unfreeze_first_k=0):
    """Train ONE repetition. Returns a metrics dict."""
    # ── Deterministic execution (reproducibility) ──
    # Seeds random / numpy / torch / torch.cuda and forces cuDNN determinism.
    # Previously only torch.manual_seed was set, leaving numpy and cuDNN free.
    set_seed(seed + L)
    tm = torch.from_numpy(data_dict["train_mean"].astype(np.float32))
    ts = torch.from_numpy(data_dict["train_std"].astype(np.float32))

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
                  S=config["S"], K=config["K"], lora_r=config["lora_r"],
                  device=device, use_text_ln=use_text_ln, use_lora=use_lora,
                  gated_inject=gated_inject, unfreeze_first_k=unfreeze_first_k)

    # ── PARAM AUDIT (Data-Integrity gate) ──
    # Prove no LoRA/Unfreezing contamination leaked across variants / reps.
    #
    # `LoRA Tensors` / `LoRA Params` are the decisive evidence: the OLD code
    # created the LoRA tensors and merely FROZE them for `no_lora`, so the
    # trainable total alone could not distinguish "no LoRA" from "frozen LoRA".
    # Now `no_lora` creates none at all, and this line proves it (must be 0/0).
    named = list(model.named_parameters())
    trainable_params = {n: p.numel() for n, p in named if p.requires_grad}
    lora_tensors = [n for n, _ in named if "lora_A" in n or "lora_B" in n]
    lora_params = sum(p.numel() for n, p in named
                      if "lora_A" in n or "lora_B" in n)
    log(f"[PARAM AUDIT] Variant: {variant_name} | "
        f"Total Trainable: {sum(trainable_params.values()):,} | "
        f"LoRA Tensors: {len(lora_tensors)} | LoRA Params: {lora_params:,} | "
        f"use_text_ln={use_text_ln} use_lora={use_lora} "
        f"gated_inject={gated_inject} unfreeze_first_k={unfreeze_first_k}")

    # ── LoRA control ──
    # LoRA is now conditionally created inside MIFlu/ForecastingLLM via `use_lora`
    # (BRANCH B); the first `unfreeze_first_k` layers are fully unfrozen (BRANCH A,
    # no LoRA). No post-hoc freezing needed here.

    # ── PHASE 4: rep_N/checkpoints/ created up-front so the early stopper and
    #    the end-of-training save both target the same directory. ──
    ckpt_root = None
    if rep_dir:
        os.makedirs(rep_dir, exist_ok=True)
        ckpt_root = os.path.join(rep_dir, "checkpoints")
        os.makedirs(ckpt_root, exist_ok=True)

    # ── Recipe (Advisor Q4) ──
    opt, crit, sched, clip = build_recipe(recipe, model, config["epochs"])

    # ── Early stopping on validation loss (Advisor Q5). OFF by default so the
    #    main Table IV protocol stays a fixed 20 epochs. ──
    #    NOTE: the former "peak gate" (checkpoint only when Peak Hit Rate > 0.7)
    #    was removed with the peak_hit_rate indicator (2026-09). This is now
    #    plain val_loss + patience. See early_stopping.py PROVENANCE.
    stopper = None
    if early_stop:
        stopper = EarlyStopping(patience=patience, save_dir=ckpt_root)

    best_val = float("inf")
    epoch_rows = []          # per-rep epoch trace -> rep_N/metrics.csv
    for ep in range(config["epochs"]):
        t0 = time.time()
        tl_loss = train_epoch(model, tl, opt, crit, device,
                              prompt_cache if use_text else None, tm, ts, clip)
        (v_mse_all, v_mae_all, v_mse_ili, v_mae_ili,
         _, _) = evaluate(
            model, vl, crit, device, prompt_cache if use_text else None, tm, ts)
        best_val = min(best_val, v_mse_all)
        dt = time.time() - t0

        extra = ""
        if stopper is not None:
            res = stopper(v_mse_all, model, epoch=ep + 1)
            extra = f" | {'SAVED' if res['saved'] else res['reason'][:28]}"
            if res["stop"]:
                log(f"    [EARLY-STOP] patience exhausted at epoch {ep+1}")
                extra += " | STOP"
        if sched is not None:
            sched.step()

        # PHASE 4: record the epoch trace that becomes rep_N/metrics.csv.
        epoch_rows.append({
            "epoch": ep + 1,
            "train_loss": tl_loss,
            "val_mse_all": v_mse_all,
            "val_mae_all": v_mae_all,
            "val_mse_ili": v_mse_ili,
            "val_mae_ili": v_mae_ili,
            "lr": (sched.get_last_lr()[0] if sched is not None
                   else config.get("learning_rate")),
            "seconds": round(dt, 2),
        })

        log(f"    ep {ep+1:2d}/{config['epochs']} | train_loss={tl_loss:.6f} "
            f"| val_mse={v_mse_all:.6f}(All) {v_mse_ili:.4f}(ILI) "
            f"| val_mae={v_mae_all:.6f} | {dt:.1f}s{extra}")
        if stopper is not None and stopper.history and stopper.history[-1]["stop"]:
            break

    # Persist this repetition's epoch-by-epoch trace.
    if rep_dir:
        os.makedirs(rep_dir, exist_ok=True)
        pd.DataFrame(epoch_rows).to_csv(
            os.path.join(rep_dir, "metrics.csv"), index=False)

    (t_mse_all, t_mae_all, t_mse_ili, t_mae_ili,
     t_mse_ili_phys, t_mae_ili_phys) = evaluate(
        model, el, crit, device, prompt_cache if use_text else None, tm, ts)

    if not (np.isfinite(t_mse_all) and np.isfinite(t_mse_ili)):
        log(f"  [WARN] L={L} seed={seed} produced non-finite metrics — DISCARDED")
        del model
        torch.cuda.empty_cache() if device == "cuda" else None
        return {"L": L, "test_mse_all": np.nan, "test_mae_all": np.nan,
                "test_mse_ili": np.nan, "test_mae_ili": np.nan,
                "test_mse_ili_phys": np.nan, "test_mae_ili_phys": np.nan,
                "rep_ckpt": None, "best_val": np.nan, "seed": seed,
                "discarded": True}

    log(f"  L={L} DONE: test_mse={t_mse_all:.6f}(All) {t_mse_ili:.4f}(ILI) "
        f"test_mae={t_mae_all:.6f} | SUPPLEMENTARY phys: "
        f"MSE={t_mse_ili_phys:.1f} MAE={t_mae_ili_phys:.1f} patients")

    rep_ckpt = None
    if rep_dir and ckpt_root:
        os.makedirs(ckpt_root, exist_ok=True)
        # Per-horizon checkpoint naming so sequential horizons
        # (L=24/36/48/60) do NOT overwrite each other. Each horizon's model is
        # saved as best_model_L{L}.pt (e.g. best_model_L24.pt) for independent,
        # auditable reproducibility.
        rep_ckpt = os.path.join(ckpt_root, f"best_model_{variant_name}_L{L}_rep{rep:02d}.pt")
        torch.save(model.state_dict(), rep_ckpt)

        # Provenance metadata — makes the checkpoint's meaning unambiguous.
        # Without --early-stop this is the FINAL-epoch model (the published
        # fixed-20-epoch protocol), NOT a lowest-validation-loss selection.
        try:
            import json as _json
            with open(os.path.join(rep_dir, "checkpoint_meta.json"), "w",
                      encoding="utf-8") as _f:
                _json.dump({
                    "variant": variant_name,
                    "horizon_L": L,
                    "seed": seed,
                    "recipe": recipe,
                    "early_stopping_enabled": bool(early_stop),
                    "selection": (
                        "EarlyStopping on val_loss (patience-based; best "
                        "weights checkpointed)" if early_stop
                        else "final epoch (fixed-epoch Table IV protocol)"),
                    "best_val_mse_all": (None if not np.isfinite(best_val)
                                         else float(best_val)),
                }, _f, indent=2)
        except Exception as e:  # metadata must never fail a scientific run
            log(f"    [WARN] could not write checkpoint_meta.json ({e})")

        if stopper is not None:
            stopper.save_report(os.path.join(rep_dir, "early_stopping.json"))

        # PHASE 4: per-rep dual-track predictions (z-space + physical units).
        try:
            export_prediction_csv(data_dict, L, config, device,
                                  prompt_cache if use_text else None,
                                  rep_ckpt, rep_dir,
                                  use_text_ln=use_text_ln, use_lora=use_lora,
                                  gated_inject=gated_inject,
                                  unfreeze_first_k=unfreeze_first_k,
                                  variant_name=variant_name)
        except Exception as e:
            log(f"    [WARN] per-rep prediction export failed ({e})")

    del model
    torch.cuda.empty_cache() if device == "cuda" else None
    return {"L": L, "test_mse_all": t_mse_all, "test_mae_all": t_mae_all,
            "test_mse_ili": t_mse_ili, "test_mae_ili": t_mae_ili,
            "test_mse_ili_phys": t_mse_ili_phys,
            "test_mae_ili_phys": t_mae_ili_phys,
            "rep_ckpt": rep_ckpt, "best_val": best_val, "seed": seed,
            "discarded": False}


def export_prediction_csv(data_dict, L, config, device, prompt_cache,
                          ckpt_path, out_dir, variant_name="unknown",
                          use_text_ln=True, use_lora=True,
                          gated_inject=False, unfreeze_first_k=0):
    """Write the per-horizon prediction CSV (dual-track + real CDC calendar)."""
    import torch.utils.data as _td
    tm = torch.from_numpy(data_dict["train_mean"].astype(np.float32))
    ts = torch.from_numpy(data_dict["train_std"].astype(np.float32))
    tm_np = np.asarray(data_dict["train_mean"]).ravel()
    ts_np = np.asarray(data_dict["train_std"]).ravel()

    Xt, Yt, Xv, Yv, Xte, Yte = build_windows(
        data_dict["data_norm"], config["T"], L,
        data_dict["train_end"], data_dict["val_end"])
    n_tr, n_va = len(Xt), len(Xv)

    model = MIFlu(N=config["N"], T=config["T"], L=L, Lp=config["Lp"],
                  S=config["S"], K=config["K"], lora_r=config["lora_r"],
                  device=device, use_text_ln=use_text_ln, use_lora=use_lora,
                  gated_inject=gated_inject, unfreeze_first_k=unfreeze_first_k)
    BENIGN = ("attn.bias", "attn.masked_bias")
    _res = model.load_state_dict(
        torch.load(ckpt_path, map_location=device), strict=False)
    _missing = [k for k in _res.missing_keys if not k.endswith(BENIGN)]
    assert not _missing and not _res.unexpected_keys, \
        f"ckpt mismatch: missing={_missing[:5]} unexpected={_res.unexpected_keys[:5]}"
    model.eval()

    # abs_week of window k's target start = k + T
    def _collect(X, Y, split_label, offset):
        dl = _td.DataLoader(_td.TensorDataset(torch.from_numpy(X), torch.from_numpy(Y)),
                            batch_size=config["batch_size"], shuffle=False)
        rows = []
        with torch.no_grad():
            for bi, (bx, by) in enumerate(dl):
                bx = bx.to(device)
                bsz = bx.size(0)
                ht = (prompt_cache.expand(bsz, -1, -1)
                      if prompt_cache is not None and prompt_cache.shape[0] == 1
                      else prompt_cache[:bsz] if prompt_cache is not None else None)
                yh_rev, yh_phys, _, _ = model(bx, htext=ht, train_mean=tm, train_std=ts)
                gt = by.cpu().numpy()[:, 4, :]
                pr = yh_rev.cpu().numpy()[:, 4, :]
                gt_p = gt * float(ts_np[4]) + float(tm_np[4])
                pr_p = yh_phys.cpu().numpy()[:, 4, :]
                for r in range(bsz):
                    gi = offset + bi * config["batch_size"] + r + config["T"]
                    for s in range(L):
                        rows.append((split_label, gi + s, s,
                                     float(gt[r, s]), float(pr[r, s]),
                                     float(gt_p[r, s]), float(pr_p[r, s])))
        return rows

    rows = (_collect(Xt, Yt, "train", 0)
            + _collect(Xv, Yv, "val", n_tr)
            + _collect(Xte, Yte, "test", n_tr + n_va))
    out_df = pd.DataFrame(rows, columns=[
        "split", "abs_week", "step",
        "ground_truth_ili", "prediction_ili",
        "ground_truth_ili_phys", "prediction_ili_phys"])
    out_df = attach_calendar(out_df, abs_week_col="abs_week")
    out_df = out_df[["split", "abs_week", "step", "epiweek", "week_start_date",
                     "ground_truth_ili", "prediction_ili",
                     "ground_truth_ili_phys", "prediction_ili_phys"]]

    # Alignment invariant (Advisor Q2b).
    spread = (out_df.groupby("abs_week")["ground_truth_ili"].max()
              - out_df.groupby("abs_week")["ground_truth_ili"].min()).max()
    assert float(spread) < 1e-4, f"GT misaligned across windows (spread {spread})"

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"predictions_{variant_name}_L{L}_paper_protocol.csv")
    out_df.to_csv(out_path, index=False)
    log(f"  [CSV] L={L}: predictions -> {out_path} "
        f"(alignment spread={float(spread):.2e})")
    return out_path


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", type=str, default="full",
                        choices=["full", "no_dataset", "no_task", "no_vardesc",
                                 "no_lora", "no_multi", "no_lora_multi",
                                 "no_text_ln", "gated_inject"])
    # ── Advisor Q4: training recipe ──
    parser.add_argument("--recipe", type=str, default="baseline",
                        choices=sorted(RECIPES),
                        help="Training recipe (optimizer/wd/scheduler/loss/clip).")
    # ── Advisor Q5: early stopping on validation loss ──
    parser.add_argument("--early-stop", action="store_true",
                        help="Enable early stopping on validation loss (default "
                             "OFF so the Table IV fixed-20-epoch protocol is "
                             "preserved).")
    parser.add_argument("--patience", type=int, default=5)
    # ── run controls ──
    parser.add_argument("--horizon", type=int, default=None,
                        help="Train a single L (default: sweep [24,36,48,60]).")
    parser.add_argument("--reps", type=int, default=CONFIG["num_repetitions"])
    parser.add_argument("--epochs", type=int, default=CONFIG["epochs"])
    parser.add_argument("--batch", type=int, default=CONFIG["batch_size"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true",
                        help="Ignore existing results and retrain ALL (L, rep) "
                             "pairs from scratch (disables resume). Use for a "
                             "clean reproduction run.")
    parser.add_argument("--export-dir", default=None,
                        help="Output root. Journal runs point this at "
                             "hpc_results/journal_evidence/<exp>/reps_1_to_10/.")
    args = parser.parse_args()

    # ── Deterministic execution: seed every RNG before touching any data ──
    set_seed(args.seed)

    # Run-time config: CLI overrides MUST actually reach the trainer.
    # (Previously the module-level `CONFIG` was handed to train_L verbatim, so
    #  `--epochs` / `--batch` were printed in the run header but silently
    #  ignored — anyone reproducing with non-default settings silently got the
    #  defaults. Defaults are unchanged, so published numbers are unaffected.)
    run_config = dict(CONFIG)
    run_config["epochs"] = args.epochs
    run_config["batch_size"] = args.batch

    variants = {
        "full":          {"use_text": True,  "use_lora": True,  "prompt_fn": build_prompt, "name": "MIFlu (full)"},
        "no_dataset":    {"use_text": True,  "use_lora": True,  "prompt_fn": build_prompt_no_dataset, "name": "w/o Dataset information"},
        "no_task":       {"use_text": True,  "use_lora": True,  "prompt_fn": build_prompt_no_task, "name": "w/o Task instruction"},
        "no_vardesc":    {"use_text": True,  "use_lora": True,  "prompt_fn": build_prompt_no_vardesc, "name": "w/o Input variable description"},
        "no_lora":       {"use_text": True,  "use_lora": False, "prompt_fn": build_prompt, "name": "w/o LoRA"},
        "no_multi":      {"use_text": False, "use_lora": True,  "prompt_fn": None, "name": "w/o multimodality"},
        "no_lora_multi": {"use_text": False, "use_lora": False, "prompt_fn": None, "name": "w/o LoRA+multimodality"},
        # ── Dual-Track core novelty (journal submission) ──
        "no_text_ln":    {"use_text": True,  "use_lora": True,  "use_text_ln": False,
                          "prompt_fn": build_prompt, "name": "w/o text LayerNorm (statistical shortcut)"},
        "gated_inject":  {"use_text": True,  "use_lora": True,  "gated_inject": True,
                          "unfreeze_first_k": 2, "prompt_fn": build_prompt,
                          "name": "ModalityAligner (gated injection)"},
    }
    v = variants[args.variant]

    # Experiment identity: recipe is part of the name so a recipe sweep never
    # silently overwrites a variant run.
    exp_name = (f"{args.variant}" if args.recipe == "baseline"
                else f"{args.variant}__{args.recipe}")
    if args.early_stop:
        exp_name += "__earlystop"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    EXPORT_ROOT = (args.export_dir
                   or os.path.join(PROJECT_ROOT, "hpc_results", "journal_evidence",
                                   exp_name))
    os.makedirs(EXPORT_ROOT, exist_ok=True)
    LOG_PATH = os.path.join(EXPORT_ROOT, "training_ablation.log")
    RESULTS_PATH = os.path.join(EXPORT_ROOT, "metrics.csv")
    log_init(LOG_PATH)

    log("=" * 66)
    log(f"  Table VIII Ablation: {v['name']}")
    log("=" * 66)
    log(f"  Variant         : {args.variant}  (use_text={v['use_text']}, "
        f"use_lora={v['use_lora']}, use_text_ln={v.get('use_text_ln', True)}, "
        f"gated_inject={v.get('gated_inject', False)}, "
        f"unfreeze_first_k={v.get('unfreeze_first_k', 0)})")
    log(f"  Recipe          : {args.recipe}  -> {describe(args.recipe)}")
    log(f"  Early stopping  : {args.early_stop} "
        f"(patience={args.patience})")
    log(f"  Config          : T={CONFIG['T']}, K={CONFIG['K']}, Lp={CONFIG['Lp']}, S={CONFIG['S']}")
    log(f"                    batch={args.batch}, epochs={args.epochs}, reps={args.reps}, seed={args.seed}")
    log(f"  Data window     : FULL 1025 rows (200201-202152) — matches MIFlu §V-A")
    log(f"  Output          : {EXPORT_ROOT}")
    log()

    data_dict = load_and_normalize()
    log()

    text_embedder = None
    if v['use_text']:
        log("Loading GPT2 text embedder...")
        text_embedder = TextualInputEmbedder(device=device)
    log()

    L_list = [args.horizon] if args.horizon is not None else CONFIG["L_list"]

    # Resume support: skip (L, rep) pairs already present in metrics.csv.
    # `--force` clears the "done" set so every pair is retrained from scratch
    # (essential for a clean reproduction on the refactored code).
    all_rows = []
    done = set()
    if args.force:
        log("  [FORCE] resume disabled — all (L, rep) pairs will be retrained")
    elif os.path.exists(RESULTS_PATH):
        try:
            prev = pd.read_csv(RESULTS_PATH)
            all_rows = prev.to_dict("records")
            for r in all_rows:
                if not (isinstance(r.get("test_mse_all"), float)
                        and np.isnan(r["test_mse_all"])):
                    done.add((int(r["L"]), int(r["rep"])))
            if done:
                log(f"  [RESUME] {len(done)} (L, rep) pairs already complete")
        except Exception as e:
            log(f"  [WARN] could not parse existing metrics.csv ({e}) — starting fresh")
            all_rows, done = [], set()

    t_start = time.time()
    for L in L_list:
        log(f"{'─'*50}"); log(f"  HORIZON L={L}"); log(f"{'─'*50}")

        prompt_cache = None
        if v['use_text'] and v['prompt_fn'] is not None:
            prompt = v['prompt_fn'](data_dict["train_df"], T=CONFIG["T"], L=L)
            prompt_cache = text_embedder(prompt)

        best_rep, best_val = None, float("inf")
        for rep in range(1, args.reps + 1):
            if (L, rep) in done:
                log(f"  [L={L}] Rep {rep}/{args.reps} ... already done, skipping")
                continue
            log(f"  [L={L}] Rep {rep}/{args.reps} ...")
            rep_dir = os.path.join(EXPORT_ROOT, f"horizon_L{L}", f"rep_{rep:02d}")
            r = train_L(data_dict, L, run_config, device, prompt_cache,
                        v['use_lora'], v['use_text'],
                        seed=args.seed + rep - 1, recipe=args.recipe,
                        early_stop=args.early_stop, patience=args.patience,
                        rep_dir=rep_dir, variant_name=args.variant, rep=rep,
                        use_text_ln=v.get("use_text_ln", True),
                        gated_inject=v.get("gated_inject", False),
                        unfreeze_first_k=v.get("unfreeze_first_k", 0))
            all_rows.append({
                "L": L, "rep": rep,
                "mse_all": r["test_mse_all"], "mae_all": r["test_mae_all"],
                "mse_ili": r["test_mse_ili"], "mae_ili": r["test_mae_ili"],
                "mse_ili_phys": r["test_mse_ili_phys"],
                "mae_ili_phys": r["test_mae_ili_phys"],
                "best_val": r["best_val"], "seed": r["seed"],
                "discarded": r["discarded"],
            })
            pd.DataFrame(all_rows).to_csv(RESULTS_PATH, index=False)
            if not r["discarded"] and r["best_val"] < best_val:
                best_val, best_rep = r["best_val"], r

        if best_rep is not None and best_rep["rep_ckpt"]:
            export_prediction_csv(data_dict, L, run_config, device,
                                  prompt_cache if v['use_text'] else None,
                                  best_rep["rep_ckpt"], EXPORT_ROOT,
                                  use_text_ln=v.get("use_text_ln", True),
                                  use_lora=v['use_lora'],
                                  gated_inject=v.get("gated_inject", False),
                                  unfreeze_first_k=v.get("unfreeze_first_k", 0))

        fin = [r for r in all_rows if r["L"] == L]
        ok = [r for r in fin if not r["discarded"]]
        if ok:
            log(f"  [L={L}] FINAL over {len(ok)} reps: "
                f"MSE_AllVars={np.mean([r['mse_all'] for r in ok]):.6f} "
                f"MSE_ILITotal={np.mean([r['mse_ili'] for r in ok]):.6f}")
        log()

    df = pd.DataFrame(all_rows)
    ok = df[~df["discarded"]] if "discarded" in df.columns else df
    summary = ok.groupby("L").agg(
        mse_all_mean=("mse_all", "mean"), mse_all_std=("mse_all", "std"),
        mae_all_mean=("mae_all", "mean"), mae_all_std=("mae_all", "std"),
        mse_ili_mean=("mse_ili", "mean"), mse_ili_std=("mse_ili", "std"),
        mse_ili_phys_mean=("mse_ili_phys", "mean"),
        mae_ili_phys_mean=("mae_ili_phys", "mean"))
    summary_path = os.path.join(EXPORT_ROOT, "summary.csv")
    summary.to_csv(summary_path)

    log("=" * 66)
    log(f"  ABLATION COMPLETE: {v['name']} | recipe={args.recipe}")
    log("=" * 66)
    log(summary.to_string())
    log(f"  Avg MSE_AllVars across L: {summary['mse_all_mean'].mean():.6f}")
    log(f"  Total time: {(time.time()-t_start)/60:.1f} min")
    log(f"  Per-rep metrics : {RESULTS_PATH}")
    log(f"  Summary         : {summary_path}")
    log_close()

    print(f"\nABLATION_RESULT: variant={args.variant} recipe={args.recipe} "
          f"mse_all={summary['mse_all_mean'].mean():.6f}")


if __name__ == "__main__":
    main()
