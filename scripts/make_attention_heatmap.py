#!/usr/bin/env python
"""make_attention_heatmap.py — Figure 2: cross-modal attention heatmap.
=========================================================================
Visualises the *gated cross-modal injection* introduced by the `gated_inject`
variant. The `ModalityAligner` performs a cross-attention in which the
time-series patches are the QUERIES and the textual prompt tokens are the
KEYS/VALUES::

    aligned, _ = cross_attn(query=htime, key=htext, value=htext)

`ModalityAligner.forward` deliberately discards the attention weights (it only
needs the fused tensor), so recovering them requires a forward hook. This
script:

  1. rebuilds the trained `gated_inject` model and loads `rep_01`'s checkpoint;
  2. computes the REAL text embedding from the same prompt used in training;
  3. feeds a REAL test window (the first forecast window of the test split,
     i.e. rows [val_end - T : val_end] of the train-only-scaled data);
  4. captures the cross-attention weights on the forward pass;
  5. plots time-patch (query) x text-token (key) attention.

Because the weights come from a genuine forward pass on held-out data with the
trained weights, the figure evidences that cross-modal activation actually
occurs inside the aligner (as opposed to the `full` variant, where text is
merely concatenated as a prefix).

Usage:
    python scripts/make_attention_heatmap.py
"""
from __future__ import annotations

import os
import sys

import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from configs import CONFIG, VAR_COLS, N_HEADS, set_seed   # noqa: E402
from miflu_model import MIFlu                              # noqa: E402
from textual_embedder import TextualInputEmbedder           # noqa: E402
from train_ablation import load_and_normalize, build_prompt  # noqa: E402

CKPT = os.path.join(
    PROJECT_ROOT, "results", "ili", "journal_evidence",
    "gated_inject", "reps_1_to_10", "rep_01", "checkpoints", "best_model.pt",
)
OUT_PATH = os.path.join(
    PROJECT_ROOT, "results", "ili", "figures", "fig_attention_heatmap.png",
)

# gated_inject variant flags (identical to train_ablation.py's variant table)
GATED = dict(use_text_ln=True, use_lora=True,
             gated_inject=True, unfreeze_first_k=2)


def capture_attention(model, x, htext):
    """Run a forward pass and capture the ModalityAligner cross-attention."""
    aligner = model.forecasting_llm.modality_aligner
    if aligner is None:
        raise RuntimeError(
            "checkpoint has no ModalityAligner — is this really gated_inject?"
        )

    captured = {}

    def _hook(module, args, output):
        # nn.MultiheadAttention returns (attn_output, attn_weights) when
        # need_weights=True (the default used by ModalityAligner.forward).
        if isinstance(output, tuple) and len(output) == 2 and output[1] is not None:
            captured["w"] = output[1].detach()

    handle = aligner.cross_attn.register_forward_hook(_hook)
    try:
        with torch.no_grad():
            model(x, htext)
    finally:
        handle.remove()

    if "w" not in captured:
        raise RuntimeError(
            "no attention weights captured — need_weights may be disabled"
        )
    return captured["w"]


def to_2d(weights: torch.Tensor) -> np.ndarray:
    """Collapse attention weights to (num_queries, num_keys)."""
    w = weights
    if w.dim() == 4:                      # (batch, heads, q, k)
        w = w.mean(dim=1)
    elif w.dim() == 3:                    # (batch, q, k)
        pass
    else:
        raise ValueError(f"unexpected attention shape {tuple(w.shape)}")
    return w[0].float().cpu().numpy()     # first (only) batch element


def main() -> int:
    set_seed(42)
    device = "cpu"
    L = CONFIG["L_list"][0]      # 24 — the reported horizon
    T = CONFIG["T"]              # 104 — look-back window

    print("[attn] loading data (train-only scaler, full 1025-row window)...")
    data = load_and_normalize()
    data_norm = data["data_norm"]
    val_end = data["val_end"]

    # ── REAL test window: first forecast window of the test split ──
    # Window k feeds rows [k : k+T] and forecasts [k+T : k+T+L]; the first
    # window whose target lies entirely in TEST is k = val_end - T.
    k = val_end - T
    window = data_norm[k:val_end]                       # (T, N)
    x = torch.from_numpy(np.ascontiguousarray(window.T))[None]  # (1, N, T)
    print(f"[attn] test window rows [{k}:{val_end}] -> x shape {tuple(x.shape)}")

    # ── REAL text embedding (same prompt the variant was trained with) ──
    print("[attn] building prompt embedding...")
    prompt = build_prompt(data["train_df"], T=T, L=L)
    embedder = TextualInputEmbedder(device=device)
    htext = embedder(prompt)
    print(f"[attn] htext shape {tuple(htext.shape)}")

    # ── Rebuild the trained model ──
    print("[attn] rebuilding gated_inject model...")
    model = MIFlu(N=CONFIG["N"], T=T, L=L, Lp=CONFIG["Lp"], S=CONFIG["S"],
                  K=CONFIG["K"], lora_r=CONFIG["lora_r"], device=device,
                  **GATED)
    # NOTE: `attn.bias` / `attn.masked_bias` are legacy causal-mask buffers.
    # Depending on the transformers version they are registered persistent or
    # not, so a checkpoint written on the cluster can omit them. They are
    # recomputed inside GPT2Attention.forward, so ignoring them is safe — but
    # we use strict=False WITH a guard so no genuine weight can silently skip.
    BENIGN_SUFFIX = ("attn.bias", "attn.masked_bias")
    state = torch.load(CKPT, map_location=device)
    result = model.load_state_dict(state, strict=False)
    missing = [k for k in result.missing_keys
               if not k.endswith(BENIGN_SUFFIX)]
    unexpected = list(result.unexpected_keys)
    if missing or unexpected:
        raise RuntimeError(
            f"checkpoint/model mismatch beyond known buffers. "
            f"missing={missing[:10]} unexpected={unexpected[:10]}"
        )
    if result.missing_keys:
        print(f"[attn] ignored {len(result.missing_keys)} legacy causal-mask "
              f"buffers (recomputed at forward time)")
    model.eval()
    print(f"[attn] loaded checkpoint: {CKPT}")

    # ── Capture cross-attention on a real forward pass ──
    att = to_2d(capture_attention(model, x, htext))
    n_q, n_k = att.shape
    print(f"[attn] attention matrix: {n_q} time-patches x {n_k} text tokens")
    print(f"[attn] attn stats: min={att.min():.5f} max={att.max():.5f} "
          f"mean={att.mean():.5f} std={att.std():.5f}")

    # ── Plot ──
    n_vars = CONFIG["N"]
    per_var = n_q // n_vars          # patches contributed by each variable
    fig, ax = plt.subplots(figsize=(11.0, 7.0))
    im = ax.imshow(att, aspect="auto", cmap="viridis", interpolation="nearest")

    # Separators + labels for the 7 input variables
    for i in range(1, n_vars):
        ax.axhline(i * per_var - 0.5, color="white", lw=0.8, alpha=0.65)
    ax.set_yticks([(i + 0.5) * per_var for i in range(n_vars)])
    ax.set_yticklabels(VAR_COLS, fontsize=8)

    ax.set_xlabel("Text token index (prompt keys/values)", fontsize=11)
    ax.set_ylabel("Time-series patch (query) — grouped by variable", fontsize=11)
    ax.set_title(
        "Figure 2 — Gated cross-modal injection: how time patches attend to text\n"
        f"gated_inject (rep_01) | ModalityAligner cross-attention, {N_HEADS} heads averaged"
        f" | test window rows [{k}:{val_end}]",
        fontsize=12,
    )
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("Attention weight", fontsize=10)

    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    fig.savefig(OUT_PATH, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[attn] wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
