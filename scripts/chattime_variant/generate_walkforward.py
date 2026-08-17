#!/usr/bin/env python
"""
generate_walkforward.py — [ISOLATED / NON-DEFAULT PATH]
=======================================================

⚠️  THIS IS THE CHATTIME-STYLE WALK-FORWARD VARIANT, NOT THE MIFLU PAPER PROTOCOL.

It is kept here (scripts/chattime_variant/) ONLY for the Phase 2 ChatTime-backbone
comparison. It is NOT part of the MIFlu reproduction deliverable. The authoritative
MIFlu pipeline is `scripts/train_miflu.py` with L ∈ {24,36,48,60} evaluated
independently under the paper protocol (see docs/leakage_audit_report.md).

Protocol (mirrors ChatTime run_ili_walkforward.py):
  * N = 7 channels (OT RESTORED as 7th channel = num_patients / denominator;
    our own implementation choice — paper Table X only calls it "'OT' feature for
    long-term forecasting", no formula given, NOT a black box; StandardScaler-neutralized scale).
  * ILITOTAL is the ONLY target / ground truth (channel index 4).
  * Hist window T = 104, Pred window = 52, stride = 52 (NON-OVERLAPPING).
  * Chronological 70:10:20 split (train:val:test). Test starts at
    test_start = round(L_total * (1 - test_frac)), test_frac = 0.20.
  * Every TEST window is inferred once; the final window is truncated to
    min(pred_len, remaining) so no padding / boundary fabrication occurs.
  * Predictions are concatenated in time order to form the continuous series.

Output (kept under results/ili with an explicit walk-forward suffix so it can
never be confused with the paper-protocol tables):
    results/ili/miflu_fulltest_walkforward.csv
    columns: date, ground_truth, prediction

This script requires a GPU/CPU torch run with the N=7 L=52 checkpoint
produced by the HPC retrain job (best_miflu_L52.pth).

Usage:
  python scripts/chattime_variant/generate_walkforward.py --ckpt checkpoints/best_miflu_L52.pth
  python scripts/chattime_variant/generate_walkforward.py   # auto-finds checkpoints/best_miflu_L52.pth
"""
import os
import sys
import argparse
import numpy as np
import pandas as pd
import torch

# Resolve project layout: this file lives in scripts/chattime_variant/, so the
# sibling `scripts/` directory (holding miflu_model / textual_embedder) must be
# added to sys.path explicitly.
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(HERE)          # scripts/
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)  # MLFlu/
sys.path.insert(0, SCRIPTS_DIR)

from miflu_model import MIFlu
from textual_embedder import TextualInputEmbedder, build_prompt

# ── N=7 channel configuration (OT RESTORED) ─────────────────────────────────
# OT = num_patients (total outpatient volume / denominator).
# NOTE: OT ≈ 总门诊量/分母 — our own implementation choice; the paper Table X only
# labels it "'OT' feature for long-term forecasting" (no formula, not a black box).
# StandardScaler neutralizes the constant-scale difference.
VAR_COLS = [
    "% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
    "ILITOTAL", "NUM. OF PROVIDERS", "OT",
]
ILI_IDX = 4          # ILITOTAL channel in the 7-var array
N = 7
T = 104              # fixed history window (per paper + ChatTime)
L = 52               # prediction horizon (single, mirrors ChatTime)
Lp, S, K, lora_r, D = 24, 2, 6, 4, 768

TRAIN_FRAC, VAL_FRAC, TEST_FRAC = 0.70, 0.10, 0.20
STRIDE = L          # non-overlapping walk-forward
PRED_LEN = L

DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "national_illness_raw.csv")
FIG_ROOT = os.path.join(PROJECT_ROOT, "results", "ili")
DEFAULT_CKPT = os.path.join(PROJECT_ROOT, "checkpoints", "best_miflu_L52.pth")


def load_normalize(df):
    data = df[VAR_COLS].values.astype(np.float32)
    n = len(data)
    t_end = int(round(n * TRAIN_FRAC))
    v_end = t_end + int(round(n * VAL_FRAC))
    train_mean = data[:t_end].mean(0, keepdims=True)
    train_std = data[:t_end].std(0, keepdims=True) + 1e-8
    data_norm = (data - train_mean) / train_std
    return data_norm, train_mean, train_std, t_end, v_end, n


def walk_forward_windows(y, hist_len, pred_len, stride, test_start):
    """Mirror ChatTime run_ili_walkforward.walk_forward_windows exactly.

    Yields (hist, truth, start, length) for each non-overlapping test window.
    The final window is truncated to min(pred_len, remaining).
    """
    L_total = len(y)
    i = max(hist_len, test_start)
    while i < L_total:
        hist = y[i - hist_len:i]
        length = min(pred_len, L_total - i)
        if length <= 0:
            break
        truth = y[i:i + length]
        yield hist, truth, i, length
        i += stride


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=DEFAULT_CKPT,
                    help="Path to N=7 L=52 checkpoint (best_miflu_L52.pth).")
    ap.add_argument("--out_dir", default=FIG_ROOT)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    if not os.path.exists(args.ckpt):
        print(f"[BLOCKER] checkpoint not found: {args.ckpt}")
        sys.exit(3)

    df = pd.read_csv(DATA_PATH)
    data_norm, train_mean, train_std, t_end, v_end, n = load_normalize(df)

    # Test region (70:10:20) — only windows whose prediction target falls in test.
    test_start = int(round(n * (1 - TEST_FRAC)))

    # Build 7-var prompt from TRAIN portion (includes OT stats).
    train_df = df.iloc[:t_end]
    text_embedder = TextualInputEmbedder(device=args.device)

    prompt = build_prompt(train_df, T=T, L=L)
    ht = text_embedder(prompt).to(args.device)   # (1, tokens, 768)

    model = MIFlu(N=N, T=T, L=L, Lp=Lp, S=S, K=K, lora_r=lora_r, D=D,
                  device=args.device)
    model.load_state_dict(torch.load(args.ckpt, map_location=args.device))
    model.eval()

    tm = torch.from_numpy(train_mean.astype(np.float32)).to(args.device)
    ts = torch.from_numpy(train_std.astype(np.float32)).to(args.device)

    # Index helpers over the normalized array (channels last).
    # data_norm[i] is a (N,) row; we need windows shaped (N, T) / (N, L).
    gt_rows, pred_rows, date_rows = [], [], []
    with torch.no_grad():
        for hist, truth, start, length in walk_forward_windows(
                data_norm, T, PRED_LEN, STRIDE, test_start):
            # hist: (T, N) ; need (1, N, T)
            xb = torch.from_numpy(hist.T[np.newaxis].astype(np.float32)).to(args.device)
            yh_rev, yh_phys, _, _ = model(xb, htext=ht, train_mean=tm, train_std=ts)
            # ground truth (physical ILITOTAL) via inverse StandardScaler
            gt_phys = truth[:, ILI_IDX] * train_std[0, ILI_IDX] + train_mean[0, ILI_IDX]
            pred_phys = yh_phys.cpu().numpy()[0][ILI_IDX]  # length == PRED_LEN, clip to `length`
            # dates: forecast weeks (epiweek), truncated to actual length
            wk = df["epiweek"].iloc[start: start + length].values.astype(int)
            for j in range(length):
                date_rows.append(str(int(wk[j])))
                gt_rows.append(float(gt_phys[j]))
                pred_rows.append(float(np.clip(pred_phys[j], 0.0, None)))

    out = pd.DataFrame({
        "date": date_rows,
        "ground_truth": gt_rows,
        "prediction": pred_rows,
    })
    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, "miflu_fulltest_walkforward.csv")
    out.to_csv(out_path, index=False)
    print(f"[SAVED] {out_path}  ({len(out)} weeks, "
          f"test_start={test_start}, stride={STRIDE}, pred={PRED_LEN})")
    print("[NOTE] This is the ChatTime-style L=52 walk-forward variant, NOT the "
          "MIFlu paper protocol. See scripts/train_miflu.py for the authoritative runs.")


if __name__ == "__main__":
    main()
