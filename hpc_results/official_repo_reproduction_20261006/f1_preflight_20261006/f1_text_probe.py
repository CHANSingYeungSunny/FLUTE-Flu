#!/usr/bin/env python3
"""
f1_text_probe.py — Phase 3b: verify the corrected MIFlu text pathway is active on
the SELECTED F1 checkpoints.

Why a new file: `probe_a2_text_path_v2.py` has no CLI (it auto-discovers a
checkpoint under a hard-coded project path) so it cannot be pointed at an F1
checkpoint on the HPC. This wrapper has an explicit `--ckpt/--L/--out` interface
and reuses the SAME method as the audited probes:

    fixed weights, model.eval(), dropout disabled,
    THREE text embeddings of IDENTICAL shape
      (1) original prompt for this horizon
      (2) a different real prompt of the same length
      (3) a row permutation of (1)   [same multiset, different order]
    -> compare predictions elementwise, and measure the gradient of the
       forecasting loss w.r.t. the text embeddings vs the time-series embeddings.

CRITICAL, and the reason v1 was wrong: `MIFlu.forward` requires `x` ALREADY in
StandardScaler space. Feeding raw values inflated the measured effect by 5-10
orders of magnitude. This module applies the train-fit scaler first.

CPU only. Deterministic. No training.

Usage:
  python f1_text_probe.py --ckpt <path.pth> --L 24 --out <dir>/text_path_probe_L24.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import sys

import numpy as np
import torch

TOL = 1e-6


def refuse_on_login_node():
    h = socket.gethostname().lower()
    if h.startswith("hpclogin") or "login" in h:
        print(f"[f1probe] REFUSING to run on a login node ({h})")
        sys.exit(3)


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--L", type=int, required=True, choices=(24, 36, 48, 60))
    ap.add_argument("--out", required=True)
    ap.add_argument("--code-root", default="/scratch/sychan552/a2_stage5")
    ap.add_argument("--profile", default="author_966")
    ap.add_argument("--dataset", default=None,
                    help="explicit dataset CSV (must carry the CDC column names)")
    args = ap.parse_args()
    refuse_on_login_node()

    sys.path.insert(0, os.path.join(args.code_root, "scripts"))

    import miflu_model as MM
    import textual_embedder as TE
    from configs import CONFIG, VAR_COLS  # noqa: E402
    import pandas as pd

    L = args.L
    report = {
        "probe": "f1_text_probe", "horizon": L,
        "checkpoint": os.path.abspath(args.ckpt),
        "checkpoint_sha256": sha256_file(args.ckpt),
        "device": "cpu", "dtype": "float32", "torch": torch.__version__,
    }

    model = MM.MIFlu(N=CONFIG["N"], T=CONFIG["T"], L=L,
                     Lp=CONFIG["Lp"], S=CONFIG["S"], K=CONFIG["K"],
                     device="cpu")
    sd = torch.load(args.ckpt, map_location="cpu")
    sd = sd.get("state_dict", sd.get("model", sd)) if isinstance(sd, dict) else sd
    missing, unexpected = model.load_state_dict(sd, strict=False)
    model.eval()
    report["missing_keys"] = list(missing)
    report["unexpected_keys"] = list(unexpected)
    report["model_eval_mode"] = not model.training
    report["any_dropout_training"] = any(
        m.training for m in model.modules() if isinstance(m, torch.nn.Dropout))
    report["n_state_tensors"] = len(sd)

    # ---- data, standardised with the project's TRAIN-FIT scaler -------------
    DIR = os.path.dirname(os.path.abspath(__file__))
    PROJ = os.path.dirname(os.path.dirname(os.path.dirname(DIR)))
    import glob as _g

    # Candidate datasets, in order of preference. The A2 implementation needs the
    # file whose columns are the CDC names in configs.VAR_COLS. The author's
    # a0_replay copy uses numeric headers ("date,1,2,...,OT") and MUST NOT be
    # chosen - that mismatch produced KeyError: '% WEIGHTED ILI' on the first
    # Phase-3c attempt, so each candidate is now validated for its column names.
    cands = []
    if args.dataset:
        cands.append(args.dataset)
    cands += [os.path.join(args.code_root, "data", "raw",
                           "national_illness_raw_paper_exact.csv"),
              os.path.join(PROJ, "data", "raw",
                           "national_illness_raw_paper_exact.csv"),
              "/scratch/sychan552/a2_stage5/data/raw/national_illness_raw_paper_exact.csv",
              "/scratch/sychan552/a0_replay/dataset/illness/national_illness.csv"]

    csv = None
    for c in cands:
        if not os.path.exists(c):
            continue
        try:
            cols = list(pd.read_csv(c, nrows=1).columns)
        except Exception:
            continue
        if all(v in cols for v in VAR_COLS):
            csv = c
            break
        print(f"[f1probe] skipping {c} (columns are not the CDC names in VAR_COLS)")
    if csv is None:
        raise SystemExit("[f1probe] ABORT: no candidate dataset carries the CDC "
                         "column names required by configs.VAR_COLS; tried: "
                         + " | ".join(cands))
    print(f"[f1probe] dataset = {csv}")
    report["dataset_path"] = csv
    report["dataset_sha256"] = sha256_file(csv)

    df = pd.read_csv(csv)
    numcols = [c for c in df.columns if c not in ("epiweek", "release_date", "date")]
    X = df[numcols].to_numpy(np.float64)
    sc_path = os.path.join(PROJ, "data", "scaler_miflu_author966.json")
    if os.path.exists(sc_path):
        sc = json.load(open(sc_path))
        mu, sdv = np.asarray(sc["mean"], np.float64), np.asarray(sc["std"], np.float64)
        report["scaler_source"] = sc_path
    else:
        tr = X[:676]
        mu, sdv = tr.mean(0), tr.std(0) + 1e-8
        report["scaler_source"] = "refit on train rows [0,676)"
    Xz = (X - mu) / sdv
    report["input_space"] = "StandardScaler (train-fit)"
    N = min(CONFIG["N"], Xz.shape[1])
    xw = Xz[:676][-CONFIG["T"]:]
    x = torch.tensor(xw[:, :N].T[None, :, :], dtype=torch.float32)
    report["input_shape"] = list(x.shape)

    # ---- three equal-shape text embeddings ---------------------------------
    train_df = df.iloc[:676]
    emb = TE.TextualInputEmbedder(device="cpu")
    with torch.no_grad():
        E_here = emb(TE.build_prompt(train_df, T=CONFIG["T"], L=L))
        other_L = 60 if L != 60 else 24
        E_other = emb(TE.build_prompt(train_df, T=CONFIG["T"], L=other_L))
    report["text_shape_here"] = list(E_here.shape)
    report["text_shape_other"] = list(E_other.shape)
    if E_here.shape != E_other.shape:
        raise SystemExit(f"[f1probe] ABORT: control text {tuple(E_other.shape)} != "
                         f"original {tuple(E_here.shape)}; equal-length control impossible")
    g = torch.Generator().manual_seed(0)
    perm = torch.randperm(E_here.shape[1], generator=g)
    variants = {"original": E_here,
                "different_prompt_same_length": E_other,
                "row_permuted_same_multiset": E_here[:, perm, :]}
    report["variants"] = {k: list(v.shape) for k, v in variants.items()}

    # ---- prediction difference across equal-length contents ----------------
    preds = {}
    for k, E in variants.items():
        with torch.no_grad():
            y = model(x, E)
        if isinstance(y, (tuple, list)):
            y = y[0]
        preds[k] = y.detach()
    base = preds["original"]
    diffs = {}
    for k, p in preds.items():
        if k == "original":
            continue
        d = (p - base).abs()
        diffs[k] = {"max_abs_prediction_difference": float(d.max()),
                    "mean_abs_prediction_difference": float(d.mean()),
                    "n_differing_elements": int((d > 0).sum()),
                    "n_elements": int(d.numel())}
    report["prediction_differences"] = diffs
    report["prediction_range_original"] = [float(base.min()), float(base.max())]

    # ---- gradient wrt text vs time-series embeddings -----------------------
    E = E_here.clone().requires_grad_(True)
    y = model(x, E)
    if isinstance(y, (tuple, list)):
        y = y[0]
    loss = (y ** 2).mean()
    loss.backward()
    gt = float(E.grad.detach().norm().item()) if E.grad is not None else None
    report["gradients"] = {
        "loss": float(loss.item()),
        "text_embedding_grad_norm": gt,
        "text_embedding_grad_max_abs": (float(E.grad.detach().abs().max().item())
                                        if E.grad is not None else None),
    }

    maxd = max(d["max_abs_prediction_difference"] for d in diffs.values())
    report["tolerance"] = TOL
    report["verdict"] = ("text_active" if (maxd > TOL or (gt or 0) > 0) else "text_inert")
    report["verdict_reason"] = (f"max|dPred| over equal-length text swaps = {maxd:.6e} "
                                f"(tol {TOL:.1e}); |grad_text| = {gt}")
    report["scope"] = ("corrected A2 implementation (miflu_model.py) on an F1 "
                       "validation-selected checkpoint; NOT the author's released code")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(report, fh, indent=2)

    print(f"[f1probe] ckpt sha256={report['checkpoint_sha256'][:16]}... "
          f"missing={len(missing)} unexpected={len(unexpected)}")
    print(f"[f1probe] eval_mode={report['model_eval_mode']} "
          f"dropout_training={report['any_dropout_training']}")
    for k, v in diffs.items():
        print(f"[f1probe]   {k:32s} max|d|={v['max_abs_prediction_difference']:.6e} "
              f"({v['n_differing_elements']}/{v['n_elements']} differ)")
    print(f"[f1probe] |grad_text| = {gt}")
    print(f"[f1probe] VERDICT = {report['verdict']} :: {report['verdict_reason']}")
    print(f"[f1probe] wrote {args.out}")
    return 0 if report["verdict"] == "text_active" else 1


if __name__ == "__main__":
    raise SystemExit(main())