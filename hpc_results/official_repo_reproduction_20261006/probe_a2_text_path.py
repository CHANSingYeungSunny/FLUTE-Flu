#!/usr/bin/env python3
"""Does text actually reach the forecast in the A2 model we benchmarked?

The P0 investigation proved the AUTHOR's released code discards text. That says
nothing about A2, which is the implementation whose numbers the LLM-vs-non-LLM
benchmark reports. A2 prefixes the text and reads the trailing patch positions
(miflu_model.py lines 375-376 and 407), which is the direction that SHOULD make
text reachable. This script checks it empirically rather than by reading code.

Same method as the released-code probe: fixed weights, eval mode, and a
SAME-SHAPE different-content text swap, so sequence length (and therefore any
dropout RNG consumption) is identical.

Run locally (CPU is fine, the model is small):
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python probe_a2_text_path.py
"""
import glob
import io
import json
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(PROJ, "scripts"))

TOL = 1e-6


def pick_checkpoint():
    cands = [
        os.path.join(PROJ, "hpc_results", "checkpoints", "best_miflu_L24.pth"),
        os.path.join(PROJ, "results", "ili", "journal_evidence", "full",
                     "checkpoints", "best_model_L24.pt"),
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    hits = glob.glob(os.path.join(PROJ, "**", "*miflu*L24*.pth"), recursive=True)
    return hits[0] if hits else None


def main():
    out = {}
    import miflu_model as MM

    ckpt_path = pick_checkpoint()
    print(f"[a2probe] checkpoint = {ckpt_path}")
    if not ckpt_path:
        print("[a2probe] ABORT: no A2 checkpoint found")
        return 2

    model = MM.MIFlu(N=7, T=104, L=24, device="cpu")
    sd = torch.load(ckpt_path, map_location="cpu")
    sd = sd.get("state_dict", sd.get("model", sd)) if isinstance(sd, dict) else sd
    missing, unexpected = model.load_state_dict(sd, strict=False)
    print(f"[a2probe] loaded: missing={len(missing)} unexpected={len(unexpected)}")
    model.eval()
    out["checkpoint"] = ckpt_path
    out["missing_keys"] = len(missing)
    out["unexpected_keys"] = len(unexpected)
    out["model_eval_mode"] = not model.training
    out["dropout_training"] = [m.training for m in model.modules()
                               if isinstance(m, torch.nn.Dropout)]

    # ---- a real prompt via the project's own builder ----------------------
    import pandas as pd
    csv = os.path.join(PROJ, "data", "raw", "national_illness_raw_paper_exact.csv")
    df = pd.read_csv(csv)
    df = df.iloc[:676]                       # training rows only
    prompt24 = MM.build_prompt(df, T=104, L=24) if hasattr(MM, "build_prompt") else None
    import textual_embedder as TE
    prompt24 = TE.build_prompt(df, T=104, L=24)
    prompt60 = TE.build_prompt(df, T=104, L=60)
    print(f"[a2probe] prompt chars: L24={len(prompt24)} L60={len(prompt60)}")

    emb = TE.TextualInputEmbedder(device="cpu")
    with torch.no_grad():
        E24 = emb(prompt24)
        E60 = emb(prompt60)
    if isinstance(E24, dict):
        E24 = E24.get("embeddings", E24)
    if isinstance(E60, dict):
        E60 = E60.get("embeddings", E60)
    if E24.dim() == 2:
        E24 = E24.unsqueeze(0)
    if E60.dim() == 2:
        E60 = E60.unsqueeze(0)
    print(f"[a2probe] embedding shapes: L24={tuple(E24.shape)} L60={tuple(E60.shape)}")
    out["text_shape_L24"] = list(E24.shape)
    out["text_shape_L60"] = list(E60.shape)
    out["equal_length_available"] = bool(E24.shape == E60.shape)

    # ---- build the three text variants, all the SAME shape ----------------
    T_tok = E24.shape[1]
    variants = {"original": E24}
    if E24.shape == E60.shape:
        variants["different_prompt_same_length"] = E60
    else:
        # fall back to a truncation/pad of the longer prompt so the swap is
        # still equal-length; disclosed as such
        L60 = E60
        if L60.shape[1] >= T_tok:
            variants["different_prompt_truncated"] = L60[:, :T_tok, :]
        else:
            pad = torch.zeros(1, T_tok - L60.shape[1], L60.shape[2])
            variants["different_prompt_padded"] = torch.cat([L60, pad], dim=1)
    g = torch.Generator().manual_seed(0)
    perm = torch.randperm(T_tok, generator=g)
    variants["row_permuted_same_multiset"] = E24[:, perm, :]

    out["variants"] = {k: list(v.shape) for k, v in variants.items()}
    out["same_shape_all_variants"] = len({tuple(v.shape) for v in variants.values()}) == 1

    # ---- fixed time-series input -----------------------------------------
    NUMCOLS = [c for c in df.columns if c not in ("epiweek", "release_date", "date")]
    X = df[NUMCOLS].to_numpy(dtype=np.float32)
    X = X[:676][-104:]                       # last 104 training steps
    N = min(7, X.shape[1])
    # MIFlu.forward expects (batch, N, T)
    x = torch.tensor(X[:, :N].T[None, :, :], dtype=torch.float32)
    out["input_shape"] = list(x.shape)

    # ---- prediction difference across equal-length contents ---------------
    preds = {}
    for name, E in variants.items():
        with torch.no_grad():
            y = model(x, E)
        if isinstance(y, (tuple, list)):
            y = y[0]
        preds[name] = y.detach()
    base = preds["original"]
    diffs = {}
    for name, p in preds.items():
        if name == "original":
            continue
        d = (p - base).abs()
        diffs[name] = {"max_abs_prediction_difference": float(d.max()),
                       "mean_abs_prediction_difference": float(d.mean()),
                       "n_differing_elements": int((d > 0).sum()),
                       "n_elements": int(d.numel())}
    out["prediction_differences"] = diffs

    # ---- gradient of the forecasting loss wrt the text embeddings ---------
    E = variants["original"].clone().requires_grad_(True)
    y = model(x, E)
    if isinstance(y, (tuple, list)):
        y = y[0]
    loss = (y ** 2).mean()
    loss.backward()
    out["gradients"] = {
        "loss": float(loss.item()),
        "text_embedding_grad_norm": float(E.grad.detach().norm().item()) if E.grad is not None else None,
        "text_embedding_grad_max_abs": float(E.grad.detach().abs().max().item()) if E.grad is not None else None,
    }

    maxd = max(d["max_abs_prediction_difference"] for d in diffs.values())
    gt = out["gradients"]["text_embedding_grad_norm"]
    out["tolerance"] = TOL
    out["verdict"] = "text_active" if (maxd > TOL or (gt or 0) > 0) else "text_inert"
    out["verdict_reason"] = (f"max|Δpred| over equal-length text swaps = {maxd:.6e} "
                             f"(tol {TOL:.1e}); |grad_text| = {gt}")
    out["scope"] = ("A2 corrected reconstruction (miflu_model.py), which is the "
                    "implementation the LLM-vs-non-LLM benchmark reports. This is "
                    "NOT the author's released code - see TEXT_PATH_RESOLUTION.md "
                    "for that, where the verdict was text_inert.")

    p = os.path.join(HERE, "a2_text_path_probe.json")
    io.open(p, "w", encoding="utf-8").write(json.dumps(out, indent=2))

    print(f"\n[a2probe] equal-shape variants: {out['same_shape_all_variants']}")
    for k, v in diffs.items():
        print(f"[a2probe]   {k:34s} max|Δ|={v['max_abs_prediction_difference']:.6e} "
              f"({v['n_differing_elements']}/{v['n_elements']} elements differ)")
    print(f"[a2probe] |grad_text| = {gt}")
    print(f"[a2probe] VERDICT = {out['verdict']} :: {out['verdict_reason']}")
    print(f"[a2probe] wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())