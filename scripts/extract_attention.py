#!/usr/bin/env python
"""extract_attention.py — load gated_inject rep_01 checkpoint, hook
ModalityAligner.cross_attn, run one forward pass, and record the mean/peak
attention weight assigned to TEXT tokens as hard evidence that gated_inject
actually routes time->text attention."""
import os
import sys
import csv
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from configs import CONFIG, set_seed                       # noqa: E402
from miflu_model import MIFlu                              # noqa: E402
from textual_embedder import TextualInputEmbedder          # noqa: E402
from train_ablation import load_and_normalize, build_prompt  # noqa: E402

CKPT = os.path.join(
    PROJECT_ROOT, "results", "ili", "journal_evidence",
    "gated_inject", "reps_1_to_10", "rep_01", "checkpoints", "best_model.pt")
OUT = os.path.join(PROJECT_ROOT, "results", "ili", "metrics",
                   "attention_evidence.csv")

GATED = dict(use_text_ln=True, use_lora=True,
             gated_inject=True, unfreeze_first_k=2)


def capture_attention(model, x, htext):
    aligner = model.forecasting_llm.modality_aligner
    if aligner is None:
        raise RuntimeError("no ModalityAligner — not gated_inject")
    captured = {}

    def _hook(module, args, output):
        if isinstance(output, tuple) and len(output) == 2 and output[1] is not None:
            captured["w"] = output[1].detach()

    handle = aligner.cross_attn.register_forward_hook(_hook)
    try:
        with torch.no_grad():
            model(x, htext)
    finally:
        handle.remove()
    return captured["w"]


def main():
    set_seed(42)
    device = "cpu"
    L = CONFIG["L_list"][0]      # 24
    T = CONFIG["T"]              # 104
    data = load_and_normalize()
    data_norm = data["data_norm"]
    val_end = data["val_end"]
    k = val_end - T
    window = data_norm[k:val_end]                              # (T, N)
    x = torch.from_numpy(np.ascontiguousarray(window.T))[None]  # (1, N, T)
    prompt = build_prompt(data["train_df"], T=T, L=L)
    htext = TextualInputEmbedder(device=device)(prompt)

    model = MIFlu(N=CONFIG["N"], T=T, L=L, Lp=CONFIG["Lp"], S=CONFIG["S"],
                  K=CONFIG["K"], lora_r=CONFIG["lora_r"], device=device, **GATED)
    BENIGN = ("attn.bias", "attn.masked_bias")
    state = torch.load(CKPT, map_location=device)
    res = model.load_state_dict(state, strict=False)
    missing = [kk for kk in res.missing_keys if not kk.endswith(BENIGN)]
    assert not missing and not res.unexpected_keys, \
        f"ckpt mismatch: missing={missing[:5]} unexpected={res.unexpected_keys[:5]}"
    model.eval()

    w = capture_attention(model, x, htext)
    if w.dim() == 4:
        w = w.mean(dim=1)
    w = w[0].float().cpu().numpy()          # (n_q time-patches, n_k text-tokens)
    n_q, n_k = w.shape
    uniform = 1.0 / n_k
    mean_text = float(w.mean())
    peak_text = float(w.max(axis=1).mean())
    ratio = peak_text / uniform

    rows = [
        ("n_time_patches", n_q),
        ("n_text_tokens", n_k),
        ("uniform_attention", round(uniform, 8)),
        ("mean_text_attention", round(mean_text, 8)),
        ("peak_text_attention", round(peak_text, 8)),
        ("peak_over_uniform_ratio", round(ratio, 4)),
    ]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as f:
        wcsv = csv.writer(f)
        wcsv.writerow(["metric", "value"])
        for kk, vv in rows:
            wcsv.writerow([kk, vv])
    print(f"[attn] wrote {OUT}")
    for kk, vv in rows:
        print(f"  {kk}: {vv}")


if __name__ == "__main__":
    main()
